use std::cell::{Cell, RefCell};
use std::sync::{Arc, Mutex};
use std::collections::HashMap;
use once_cell::sync::Lazy;

/// Worker ID - 用于在 OpState 中标识当前 Worker
///
/// 在 Worker Pool 场景下，每个 Worker 在创建 JsRuntime 时会将自己的 ID
/// 存入 OpState，这样 hook op 就能知道是哪个 Worker 触发的 hook。
#[derive(Clone, Copy, Debug)]
pub struct WorkerId(pub usize);

/// 全局 Hook 数据存储 - 按Worker ID分别存储
///
/// 在调用 terminate_execution() 前保存 Hook 拦截的数据。
/// 使用全局静态HashMap，每个Worker有独立的存储空间，避免数据竞争。
static HOOK_DATA: Lazy<Arc<Mutex<HashMap<usize, String>>>> = Lazy::new(|| Arc::new(Mutex::new(HashMap::with_capacity(16))));

/// JavaScript 执行结果存储
///
/// 用于在 Rust 和 JavaScript 之间传递执行结果。
/// 通过 Deno Core 的 op 机制，JavaScript 可以将结果存储到这里。
///
/// 性能优化：使用 Cell<bool> 替代 RefCell<bool>，减少借用检查开销
pub struct ResultStorage {
    pub value: RefCell<Option<String>>,
    early_return: Cell<bool>,  // 标记是否是提前返回（用于Hook拦截）
    terminated: Cell<bool>,    // 标记是否应该终止runtime
}

impl ResultStorage {
    pub fn new() -> Self {
        Self {
            value: RefCell::new(None),
            early_return: Cell::new(false),
            terminated: Cell::new(false),
        }
    }

    pub fn clear(&self) {
        *self.value.borrow_mut() = None;
        self.early_return.set(false);
        self.terminated.set(false);
    }

    pub fn store(&self, value: String) {
        *self.value.borrow_mut() = Some(value);
    }

    pub fn take(&self) -> Option<String> {
        self.value.borrow_mut().take()
    }

    /// 检查是否有结果存储（不取出）
    pub fn has_result(&self) -> bool {
        self.value.borrow().is_some()
    }

    /// 标记为提前返回（Hook拦截）
    pub fn mark_early_return(&self) {
        self.early_return.set(true);
    }

    /// 检查是否是提前返回
    pub fn is_early_return(&self) -> bool {
        self.early_return.get()
    }

    /// 标记为已终止（强制停止runtime）
    pub fn mark_terminated(&self) {
        self.terminated.set(true);
    }

    /// 检查是否应该终止
    pub fn is_terminated(&self) -> bool {
        self.terminated.get()
    }
}

impl Default for ResultStorage {
    fn default() -> Self {
        Self::new()
    }
}

/// 保存 Hook 拦截的数据到全局存储
///
/// 这个函数在 JS 调用 __saveAndTerminate__() 时被调用，
/// 数据会保存到对应Worker ID的存储空间中，即使 V8 isolate 被终止也能访问。
///
/// # Arguments
/// * `worker_id` - Worker的唯一标识符
/// * `data` - 要保存的Hook数据（JSON字符串）
pub fn save_hook_data_for_worker(worker_id: usize, data: String) {
    let mut guard = HOOK_DATA.lock().unwrap();
    guard.insert(worker_id, data);
}

/// 获取指定Worker保存的 Hook 数据
///
/// 从全局存储中读取特定Worker保存的 Hook 数据。
/// 通常在 JS 被 terminate_execution() 终止后调用。
///
/// # Arguments
/// * `worker_id` - Worker的唯一标识符
pub fn get_hook_data_for_worker(worker_id: usize) -> Option<String> {
    let guard = HOOK_DATA.lock().unwrap();
    guard.get(&worker_id).cloned()
}

/// 清空指定Worker保存的 Hook 数据
///
/// 在开始新的 JS 执行前调用，避免读取到旧数据。
///
/// # Arguments
/// * `worker_id` - Worker的唯一标识符
pub fn clear_hook_data_for_worker(worker_id: usize) {
    let mut guard = HOOK_DATA.lock().unwrap();
    guard.remove(&worker_id);
}

/// 保存 Hook 拦截的数据到全局存储（Context API兼容）
///
/// 为了向后兼容Context API，使用特殊的worker_id = 0
pub fn save_hook_data(data: String) {
    save_hook_data_for_worker(0, data);
}

/// 获取保存的 Hook 数据（Context API兼容）
///
/// 为了向后兼容Context API，从worker_id = 0读取
pub fn get_hook_data() -> Option<String> {
    get_hook_data_for_worker(0)
}

/// 清空保存的 Hook 数据（Context API兼容）
///
/// 为了向后兼容Context API，清空worker_id = 0
pub fn clear_hook_data() {
    clear_hook_data_for_worker(0);
}
