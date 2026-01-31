//! JSEngine - Python友好的JavaScript引擎
//!
//! 提供简洁的API用于多线程JavaScript执行
//! 核心优势：JS代码只加载一次，多线程复用

use pyo3::prelude::*;
use pyo3::types::PyList;
use std::cell::OnceCell;
use std::sync::Arc;
use tokio::sync::oneshot;

use crate::worker_pool::{WorkerPool, WorkerPoolConfig, Task, TaskType};
use crate::convert::{json_to_python, python_to_json};
use crate::storage::{get_hook_data_for_worker, clear_hook_data_for_worker};

#[cfg(feature = "node_compat")]
use crate::node_compat::NodeCompatOptions;

/// Thread-local Tokio Runtime for JSEngine
///
/// 避免每次调用都创建新的 Runtime，显著提升性能（~80-150μs/调用）
thread_local! {
    static ENGINE_RUNTIME: OnceCell<tokio::runtime::Runtime> = OnceCell::new();
}

/// 使用 thread-local Runtime 执行异步操作
fn run_with_engine_runtime<F, R>(f: F) -> R
where
    F: std::future::Future<Output = R>,
{
    ENGINE_RUNTIME.with(|cell| {
        let rt = cell.get_or_init(|| {
            tokio::runtime::Builder::new_current_thread()
                .enable_all()
                .build()
                .expect("Failed to create tokio runtime for JSEngine")
        });
        rt.block_on(f)
    })
}

/// JavaScript引擎
///
/// v3.0新增API，推荐用于多线程场景
///
/// 核心特性：
/// - JS代码只在Worker初始化时加载一次
/// - Worker持久化，重复使用
/// - 自动管理Worker池
/// - 支持并行处理
///
/// # Example
///
/// ```python
/// # 创建引擎，JS代码只加载一次
/// engine = JSEngine("""
///     function encrypt(data) {
///         return btoa(JSON.stringify(data));
///     }
/// """, workers=4)
///
/// # 多线程调用，无需重复加载
/// results = [engine.call("encrypt", [data]) for data in data_list]
/// ```
#[pyclass]
pub struct JSEngine {
    pool: Arc<WorkerPool>,
}

#[pymethods]
impl JSEngine {
    /// 创建JavaScript引擎
    ///
    /// Args:
    ///     code: JavaScript代码（只在初始化时加载一次）
    ///     workers: Worker数量（默认为CPU核心数）
    ///     enable_extensions: 启用Web API扩展（默认True）
    ///     enable_node_compat: 启用Node.js兼容（默认False）
    ///     enable_logging: 启用调试日志（默认False）
    ///     random_seed: 随机数种子（默认None）
    ///     fast_return: 快速返回模式，函数return后立即返回不等待定时器（默认False）
    ///
    /// Returns:
    ///     JSEngine实例
    #[new]
    #[pyo3(signature = (
        code,
        workers=None,
        enable_extensions=true,
        enable_node_compat=false,
        enable_logging=false,
        random_seed=None,
        fast_return=false
    ))]
    fn new(
        code: String,
        workers: Option<usize>,
        enable_extensions: bool,
        enable_node_compat: bool,
        enable_logging: bool,
        random_seed: Option<u32>,
        fast_return: bool,
    ) -> PyResult<Self> {
        let worker_count = workers.unwrap_or_else(|| {
            std::thread::available_parallelism()
                .map(|n| n.get())
                .unwrap_or(4)
        });

        let mut config = WorkerPoolConfig {
            worker_count,
            init_code: Some(code),
            enable_extensions,
            enable_logging,
            random_seed,
            enable_node_compat,
            fast_return,
            #[cfg(feature = "node_compat")]
            node_compat_options: None,
        };

        // 如果启用Node兼容，设置默认选项
        #[cfg(feature = "node_compat")]
        if enable_node_compat {
            config.node_compat_options = Some(NodeCompatOptions::default());
        }

        let pool = WorkerPool::new(config)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;

        Ok(JSEngine {
            pool: Arc::new(pool),
        })
    }

    /// 调用JavaScript函数
    ///
    /// Args:
    ///     func_name: 函数名
    ///     args: 参数列表
    ///
    /// Returns:
    ///     函数返回值
    ///
    /// Example:
    ///     ```python
    ///     result = engine.call("encrypt", ["hello"])
    ///     ```
    fn call(&self, py: Python, func_name: String, args: &Bound<PyList>) -> PyResult<Py<PyAny>> {
        // 转换参数为JSON
        let json_args: Vec<serde_json::Value> = args
            .iter()
            .map(|item| python_to_json(&item))
            .collect::<PyResult<Vec<_>>>()?;

        // 创建任务
        let (tx, rx) = oneshot::channel();
        let task = Task {
            task_type: TaskType::Call {
                func_name,
                args: json_args,
            },
            tx,
        };

        // 提交任务
        self.pool
            .submit(task)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;

        // 释放GIL并等待结果
        let json_result = py.allow_threads(|| {
            let rx_result = run_with_engine_runtime(async { rx.await });

            rx_result
                .map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Worker died before returning result")
                })?
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyException, _>(e))
        })?;

        // 转换结果为Python对象
        let bound = json_to_python(py, &json_result)?;
        Ok(bound.unbind())
    }

    /// 执行JavaScript代码
    ///
    /// Args:
    ///     code: JavaScript代码
    ///
    /// Returns:
    ///     执行结果
    ///
    /// Example:
    ///     ```python
    ///     result = engine.execute("Math.sqrt(16)")
    ///     ```
    fn execute(&self, py: Python, code: String) -> PyResult<Py<PyAny>> {
        // 创建任务
        let (tx, rx) = oneshot::channel();
        let task = Task {
            task_type: TaskType::Execute { code },
            tx,
        };

        // 提交任务
        self.pool
            .submit(task)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e))?;

        // 释放GIL并等待结果
        let json_result = py.allow_threads(|| {
            let rx_result = run_with_engine_runtime(async { rx.await });

            rx_result
                .map_err(|_| {
                    PyErr::new::<pyo3::exceptions::PyRuntimeError, _>("Worker died before returning result")
                })?
                .map_err(|e| PyErr::new::<pyo3::exceptions::PyException, _>(e))
        })?;

        // 转换结果为Python对象
        let bound = json_to_python(py, &json_result)?;
        Ok(bound.unbind())
    }

    /// 获取Worker数量
    #[getter]
    fn workers(&self) -> usize {
        self.pool.worker_count()
    }

    /// 获取指定Worker的Hook数据
    ///
    /// 当调用返回 `{"__hook__": true, "worker_id": N}` 时，
    /// 使用此方法获取实际的hook数据
    ///
    /// Args:
    ///     worker_id: Worker的ID（从返回结果中获取）
    ///
    /// Returns:
    ///     Hook数据的JSON字符串，如果没有数据则返回None
    ///
    /// Example:
    ///     ```python
    ///     result = engine.call("hookFunc", [data])
    ///     if isinstance(result, dict) and result.get("__hook__"):
    ///         worker_id = result["worker_id"]
    ///         hook_data = engine.get_hook_data(worker_id)
    ///         if hook_data:
    ///             import json
    ///             data = json.loads(hook_data)
    ///     ```
    fn get_hook_data(&self, worker_id: usize) -> Option<String> {
        get_hook_data_for_worker(worker_id)
    }

    /// 清空指定Worker的Hook数据
    ///
    /// Args:
    ///     worker_id: Worker的ID
    ///
    /// Example:
    ///     ```python
    ///     engine.clear_hook_data(worker_id)
    ///     ```
    fn clear_hook_data(&self, worker_id: usize) {
        clear_hook_data_for_worker(worker_id);
    }

    /// 上下文管理器支持 - __enter__
    fn __enter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    /// 上下文管理器支持 - __exit__
    fn __exit__(
        &self,
        _exc_type: &Bound<PyAny>,
        _exc_value: &Bound<PyAny>,
        _traceback: &Bound<PyAny>,
    ) -> PyResult<bool> {
        // 返回False表示不抑制异常
        Ok(false)
    }

    /// 字符串表示
    fn __repr__(&self) -> String {
        format!("JSEngine(workers={})", self.pool.worker_count())
    }
}
