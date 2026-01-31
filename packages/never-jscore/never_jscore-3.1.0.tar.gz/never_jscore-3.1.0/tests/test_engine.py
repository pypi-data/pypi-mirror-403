"""
never-jscore 多进程 + 多线程并发测试

测试场景：
1. 多进程并行（每个进程独立的 V8 平台）
2. 每个进程内多线程并行（每个线程独立的 Context）
3. JSEngine Worker Pool 测试（跨线程任务分发）

验证目标：
- 进程正常退出（不卡住）
- 线程安全
- 资源正确释放
- 结果正确性
"""

import never_jscore
import threading
import multiprocessing
import time
import os
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import List, Tuple

# ============================================
# 测试用 JavaScript 代码
# ============================================

JS_CODE = """
// 简单的加密函数用于测试
function encrypt(data, key) {
    // 简单的 XOR 加密模拟
    let result = '';
    for (let i = 0; i < data.length; i++) {
        result += String.fromCharCode(data.charCodeAt(i) ^ (key % 256));
    }
    return btoa(result);
}

function decrypt(encoded, key) {
    let data = atob(encoded);
    let result = '';
    for (let i = 0; i < data.length; i++) {
        result += String.fromCharCode(data.charCodeAt(i) ^ (key % 256));
    }
    return result;
}

function calculate(a, b, op) {
    switch(op) {
        case 'add': return a + b;
        case 'sub': return a - b;
        case 'mul': return a * b;
        case 'div': return b !== 0 ? a / b : 0;
        default: return 0;
    }
}

function asyncTask(delay, value) {
    return new Promise(resolve => {
        setTimeout(() => resolve(value * 2), delay);
    });
}

// 测试函数：返回进程和线程信息
function getInfo() {
    return {
        timestamp: Date.now(),
        random: Math.random()
    };
}
"""

# ============================================
# 单线程 Context 测试
# ============================================

def test_single_thread_context(thread_id: int, iterations: int) -> Tuple[int, int, float]:
    """
    单线程内使用 Context 执行多次操作

    Returns:
        (thread_id, success_count, elapsed_time)
    """
    success = 0
    start = time.perf_counter()

    # 每个线程创建独立的 Context
    ctx = never_jscore.Context(enable_extensions=True)
    ctx.compile(JS_CODE)

    for i in range(iterations):
        try:
            # 测试函数调用
            result = ctx.call("calculate", [i, thread_id, "add"])
            expected = i + thread_id
            if result == expected:
                success += 1

            # 测试加密解密
            text = f"hello_{thread_id}_{i}"
            key = (thread_id * 100 + i) % 256
            encrypted = ctx.call("encrypt", [text, key])
            decrypted = ctx.call("decrypt", [encrypted, key])
            if decrypted == text:
                success += 1
            else:
                print(f"[Thread {thread_id}] Decrypt mismatch: {text} != {decrypted}")

        except Exception as e:
            print(f"[Thread {thread_id}] Error at iteration {i}: {e}")

    # 显式删除 Context
    del ctx

    elapsed = time.perf_counter() - start
    return (thread_id, success, elapsed)


def test_multithreading_context(num_threads: int, iterations_per_thread: int):
    """
    多线程测试：每个线程独立 Context
    """
    print(f"\n{'='*60}")
    print(f"多线程 Context 测试")
    print(f"线程数: {num_threads}, 每线程迭代: {iterations_per_thread}")
    print(f"{'='*60}")

    start = time.perf_counter()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = [
            executor.submit(test_single_thread_context, tid, iterations_per_thread)
            for tid in range(num_threads)
        ]

        results = [f.result() for f in futures]

    total_time = time.perf_counter() - start

    # 统计结果
    total_success = sum(r[1] for r in results)
    expected_total = num_threads * iterations_per_thread * 2  # 每次迭代 2 个测试

    print(f"\n结果统计:")
    for tid, success, elapsed in results:
        print(f"  Thread {tid}: {success} 成功, 耗时 {elapsed:.3f}s")

    print(f"\n总计: {total_success}/{expected_total} 成功")
    print(f"总耗时: {total_time:.3f}s")
    print(f"吞吐量: {total_success/total_time:.1f} ops/s")

    return total_success == expected_total


# ============================================
# JSEngine Worker Pool 测试
# ============================================

def test_jsengine_worker_pool(num_workers: int, total_tasks: int):
    """
    JSEngine Worker Pool 测试
    """
    print(f"\n{'='*60}")
    print(f"JSEngine Worker Pool 测试")
    print(f"Worker 数: {num_workers}, 总任务数: {total_tasks}")
    print(f"{'='*60}")

    start = time.perf_counter()

    # 创建 JSEngine（JS 代码只加载一次）
    engine = never_jscore.JSEngine(
        JS_CODE,
        workers=num_workers,
        enable_extensions=True
    )

    print(f"Engine 创建完成: {engine}")

    success = 0
    errors = []

    def submit_task(task_id):
        try:
            # 测试计算
            result = engine.call("calculate", [task_id, 10, "mul"])
            if result == task_id * 10:
                return True
            else:
                return False
        except Exception as e:
            return str(e)

    # 多线程提交任务到 Worker Pool
    with ThreadPoolExecutor(max_workers=num_workers * 2) as executor:
        futures = [executor.submit(submit_task, i) for i in range(total_tasks)]
        results = [f.result() for f in futures]

    success = sum(1 for r in results if r is True)
    errors = [r for r in results if r is not True and r is not False]

    elapsed = time.perf_counter() - start

    print(f"\n结果统计:")
    print(f"  成功: {success}/{total_tasks}")
    print(f"  失败: {total_tasks - success}")
    if errors:
        print(f"  错误样例: {errors[:3]}")
    print(f"  耗时: {elapsed:.3f}s")
    print(f"  吞吐量: {total_tasks/elapsed:.1f} tasks/s")

    # 显式删除 Engine
    del engine

    return success == total_tasks


# ============================================
# 单进程测试函数（供多进程调用）
# ============================================

def process_worker(process_id: int, num_threads: int, iterations: int) -> dict:
    """
    单个进程内的测试工作
    """
    pid = os.getpid()
    print(f"[Process {process_id}] Started (PID: {pid})")

    results = {
        'process_id': process_id,
        'pid': pid,
        'thread_results': [],
        'success': True
    }

    try:
        # 在进程内运行多线程测试
        start = time.perf_counter()

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [
                executor.submit(test_single_thread_context, tid, iterations)
                for tid in range(num_threads)
            ]

            thread_results = [f.result() for f in futures]

        elapsed = time.perf_counter() - start

        results['thread_results'] = thread_results
        results['elapsed'] = elapsed
        results['total_success'] = sum(r[1] for r in thread_results)
        results['expected'] = num_threads * iterations * 2

        print(f"[Process {process_id}] Completed: {results['total_success']}/{results['expected']} in {elapsed:.3f}s")

    except Exception as e:
        results['success'] = False
        results['error'] = str(e)
        print(f"[Process {process_id}] Error: {e}")

    return results


def test_multiprocess_multithreading(
        num_processes: int,
        threads_per_process: int,
        iterations_per_thread: int
):
    """
    多进程 + 多线程测试
    """
    print(f"\n{'='*60}")
    print(f"多进程 + 多线程并发测试")
    print(f"进程数: {num_processes}")
    print(f"每进程线程数: {threads_per_process}")
    print(f"每线程迭代数: {iterations_per_thread}")
    print(f"总操作数: {num_processes * threads_per_process * iterations_per_thread * 2}")
    print(f"{'='*60}")

    start = time.perf_counter()

    # 使用 spawn 方式创建进程（Windows 兼容）
    ctx = multiprocessing.get_context('spawn')

    with ctx.Pool(processes=num_processes) as pool:
        # 提交所有进程任务
        async_results = [
            pool.apply_async(
                process_worker,
                (pid, threads_per_process, iterations_per_thread)
            )
            for pid in range(num_processes)
        ]

        # 等待所有结果
        results = [ar.get(timeout=120) for ar in async_results]

    total_time = time.perf_counter() - start

    # 统计总结果
    total_success = sum(r.get('total_success', 0) for r in results)
    total_expected = sum(r.get('expected', 0) for r in results)
    all_passed = all(r.get('success', False) for r in results)

    print(f"\n{'='*60}")
    print(f"总结果:")
    print(f"{'='*60}")

    for r in results:
        pid = r.get('process_id', '?')
        success = r.get('total_success', 0)
        expected = r.get('expected', 0)
        elapsed = r.get('elapsed', 0)
        status = "✓" if r.get('success', False) else "✗"
        print(f"  Process {pid}: {success}/{expected} {status} ({elapsed:.3f}s)")

    print(f"\n总计: {total_success}/{total_expected} 成功")
    print(f"总耗时: {total_time:.3f}s")
    print(f"吞吐量: {total_success/total_time:.1f} ops/s")
    print(f"状态: {'ALL PASSED ✓' if all_passed and total_success == total_expected else 'FAILED ✗'}")

    return all_passed and total_success == total_expected


# ============================================
# 进程退出测试
# ============================================

def test_process_exit():
    """
    测试进程是否能正常退出（不卡住）
    """
    print(f"\n{'='*60}")
    print(f"进程退出测试")
    print(f"{'='*60}")

    # 创建 Context
    ctx = never_jscore.Context(enable_extensions=True)
    ctx.compile(JS_CODE)

    # 执行一些操作
    for i in range(10):
        result = ctx.call("calculate", [i, 5, "add"])
        assert result == i + 5, f"Expected {i+5}, got {result}"

    print("  10 次计算完成")

    # 测试异步操作
    result = ctx.call("getInfo", [])
    print(f"  getInfo 返回: timestamp={result.get('timestamp')}")

    # 显式删除
    del ctx
    print("  Context 已删除")

    print("  进程退出测试通过 ✓")
    return True


# ============================================
# 主测试入口
# ============================================

def main():
    print(f"never-jscore 并发测试")
    print(f"Python {sys.version}")
    print(f"PID: {os.getpid()}")
    print(f"CPU 核心数: {os.cpu_count()}")

    all_passed = True

    # 1. 进程退出测试
    try:
        if not test_process_exit():
            all_passed = False
    except Exception as e:
        print(f"进程退出测试失败: {e}")
        all_passed = False

    # 2. 多线程 Context 测试
    try:
        if not test_multithreading_context(num_threads=4, iterations_per_thread=50):
            all_passed = False
    except Exception as e:
        print(f"多线程 Context 测试失败: {e}")
        all_passed = False

    # 3. JSEngine Worker Pool 测试
    try:
        if not test_jsengine_worker_pool(num_workers=4, total_tasks=100):
            all_passed = False
    except Exception as e:
        print(f"JSEngine 测试失败: {e}")
        all_passed = False

    # 4. 多进程 + 多线程测试
    try:
        if not test_multiprocess_multithreading(
                num_processes=2,
                threads_per_process=2,
                iterations_per_thread=20
        ):
            all_passed = False
    except Exception as e:
        print(f"多进程测试失败: {e}")
        import traceback
        traceback.print_exc()
        all_passed = False

    # 最终结果
    print(f"\n{'='*60}")
    if all_passed:
        print("所有测试通过 ✓")
    else:
        print("部分测试失败 ✗")
    print(f"{'='*60}")

    print("\n等待进程退出...")
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit_code = main()
    print(f"退出码: {exit_code}")
    sys.exit(exit_code)
