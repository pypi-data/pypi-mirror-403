import os
import time
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool, get_context

import never_jscore
from loguru import logger

# 读取 JS 代码
with open('defind_rcc.js', encoding='utf8') as f:
    jscode = f.read()


def process_worker(process_id):
    """单个进程执行的函数"""
    pid = os.getpid()
    logger.info(f"进程 {process_id} 启动 (PID: {pid})")

    # 每个进程创建独立的 JSEngine（不能跨进程共享）
    engine = never_jscore.JSEngine(jscode, workers=2, enable_node_compat=True)

    results = []

    def thread_worker(task_id):
        """线程任务"""
        try:
            key = '04a26b4dcb2dbf92977f3df2e440fa71ee7cc2cfbe659f27188af7529e8d9b7017f144c6f71cd5cb74b44a902f305430e8654e0e6ccad3e7d589fe61f3071705e3'
            rand_str = "cqvY1QwplQaAdvujwrlUsp45aaOGNOC7"
            user = 'sssss'
            password = '1111'
            value = engine.call('genery_ecc', [user, password, key, rand_str])
            logger.info(f"进程[{pid}] 任务[{task_id}] 成功: {value[:50] if value else None}...")
            return value
        except Exception as e:
            logger.error(f"进程[{pid}] 任务[{task_id}] 失败: {e}")
            return None

            # 启动线程池执行固定数量的任务
    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(thread_worker, i) for i in range(10)]
        results = [f.result() for f in futures]

        # 显式删除 engine
    del engine

    success_count = sum(1 for r in results if r is not None)
    logger.info(f"进程 {process_id} 完成: {success_count}/10 成功")
    return success_count


if __name__ == "__main__":
    start_time = time.time()

    # 使用 spawn 方式（Windows 兼容）
    ctx = get_context('spawn')

    with ctx.Pool(processes=2) as pool:
        results = pool.map(process_worker, range(2))

    total_success = sum(results)
    elapsed = time.time() - start_time

    logger.info(f"总计: {total_success}/20 成功, 耗时: {elapsed:.2f}s")