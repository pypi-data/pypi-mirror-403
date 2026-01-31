"""
性能对比测试 - Context vs JSEngine

对比场景：
1. 单Context模式：每次调用都重新创建Context并加载JS代码
2. JSEngine多线程模式：JS代码只加载一次，多线程并发调用

测试用例：使用一个中等复杂度的加密算法
"""

import sys
import os

import never_jscore
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


# 测试用的JS加密算法（模拟真实场景）
JS_CRYPTO_CODE = """
// 简单的加密库实现
const CryptoLib = {
    // ROT13 + Base64 编码
    encrypt: function(text, key) {
        // Step 1: ROT cipher based on key
        let rotated = '';
        const shift = key.length % 26;
        for (let i = 0; i < text.length; i++) {
            let char = text[i];
            if (char.match(/[a-z]/i)) {
                const code = text.charCodeAt(i);
                const base = code >= 65 && code <= 90 ? 65 : 97;
                char = String.fromCharCode(((code - base + shift) % 26) + base);
            }
            rotated += char;
        }

        // Step 2: Add key signature
        const signed = key + '|' + rotated;

        // Step 3: Base64 encode
        return btoa(signed);
    },

    // 解密
    decrypt: function(encrypted, key) {
        // Step 1: Base64 decode
        const signed = atob(encrypted);

        // Step 2: Verify and remove signature
        const parts = signed.split('|');
        if (parts[0] !== key) {
            throw new Error('Invalid key');
        }
        const rotated = parts[1];

        // Step 3: Reverse ROT cipher
        let text = '';
        const shift = key.length % 26;
        for (let i = 0; i < rotated.length; i++) {
            let char = rotated[i];
            if (char.match(/[a-z]/i)) {
                const code = rotated.charCodeAt(i);
                const base = code >= 65 && code <= 90 ? 65 : 97;
                char = String.fromCharCode(((code - base - shift + 26) % 26) + base);
            }
            text += char;
        }

        return text;
    },

    // 计算简单哈希
    hash: function(text) {
        let hash = 0;
        for (let i = 0; i < text.length; i++) {
            const char = text.charCodeAt(i);
            hash = ((hash << 5) - hash) + char;
            hash = hash & hash; // Convert to 32bit integer
        }
        return Math.abs(hash).toString(16).padStart(8, '0');
    }
};

function processData(data, key) {
    const encrypted = CryptoLib.encrypt(data, key);
    const hash = CryptoLib.hash(encrypted);
    const decrypted = CryptoLib.decrypt(encrypted, key);

    return {
        original: data,
        encrypted: encrypted,
        hash: hash,
        decrypted: decrypted,
        verified: data === decrypted
    };
}
"""


def test_single_context_mode(iterations=1000):
    """
    测试1: 单Context模式
    每次调用都创建新的Context并加载JS代码（模拟v2.x的使用方式）
    """
    print("\n" + "=" * 70)
    print("【测试1】单Context模式 - 每次重新加载JS")
    print("=" * 70)

    test_data = [
        ("Hello World", "secret123"),
        ("Python JavaScript Bridge", "mykey456"),
        ("Performance Test Data", "testkey789"),
    ] * (iterations // 3)

    start_time = time.time()
    results = []

    for i, (data, key) in enumerate(test_data[:iterations]):
        # 每次都创建新的Context（模拟旧的使用方式）
        ctx = never_jscore.Context(enable_extensions=True)
        ctx.compile(JS_CRYPTO_CODE)

        result = ctx.call("processData", [data, key])
        results.append(result)

        del ctx  # 清理

        if (i + 1) % 100 == 0:
            print(f"  进度: {i + 1}/{iterations}")

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"\n结果:")
    print(f"  总调用次数: {iterations}")
    print(f"  总耗时: {elapsed:.2f}秒")
    print(f"  平均耗时: {elapsed * 1000 / iterations:.2f}ms/次")
    print(f"  吞吐量: {iterations / elapsed:.2f}次/秒")
    print(f"  验证: {sum(1 for r in results if r['verified'])}/{len(results)} 成功")

    return elapsed


def test_jsengine_single_thread(iterations=1000):
    """
    测试2: JSEngine单线程模式
    JS代码只加载一次，然后重复调用
    """
    print("\n" + "=" * 70)
    print("【测试2】JSEngine单线程模式 - JS只加载一次")
    print("=" * 70)

    test_data = [
        ("Hello World", "secret123"),
        ("Python JavaScript Bridge", "mykey456"),
        ("Performance Test Data", "testkey789"),
    ] * (iterations // 3)

    # 创建JSEngine，JS代码只加载一次
    engine = never_jscore.JSEngine(
        JS_CRYPTO_CODE,
        workers=1,  # 单线程模式
        enable_extensions=True
    )

    start_time = time.time()
    results = []

    for i, (data, key) in enumerate(test_data[:iterations]):
        result = engine.call("processData", [data, key])
        results.append(result)

        if (i + 1) % 100 == 0:
            print(f"  进度: {i + 1}/{iterations}")

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"\n结果:")
    print(f"  总调用次数: {iterations}")
    print(f"  总耗时: {elapsed:.2f}秒")
    print(f"  平均耗时: {elapsed * 1000 / iterations:.2f}ms/次")
    print(f"  吞吐量: {iterations / elapsed:.2f}次/秒")
    print(f"  验证: {sum(1 for r in results if r['verified'])}/{len(results)} 成功")

    return elapsed


def test_jsengine_multithread(iterations=1000, workers=8, max_threads=20):
    """
    测试3: JSEngine多线程模式
    JS代码只加载一次，多个Python线程并发调用
    """
    print("\n" + "=" * 70)
    print(f"【测试3】JSEngine多线程模式 - {workers}个Worker, {max_threads}个Python线程")
    print("=" * 70)

    test_data = [
        ("Hello World", "secret123"),
        ("Python JavaScript Bridge", "mykey456"),
        ("Performance Test Data", "testkey789"),
    ] * (iterations // 3)

    # 创建JSEngine，JS代码只加载一次
    engine = never_jscore.JSEngine(
        JS_CRYPTO_CODE,
        workers=workers,
        enable_extensions=True
    )

    print(f"  JSEngine创建完成，Worker数量: {engine.workers}")

    def process_one(args):
        """单个任务处理函数"""
        idx, data, key = args
        result = engine.call("processData", [data, key])
        return idx, result

    # 准备任务
    tasks = [(i, data, key) for i, (data, key) in enumerate(test_data[:iterations])]

    start_time = time.time()
    results = [None] * iterations
    completed = 0

    # 使用线程池并发执行
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        futures = {executor.submit(process_one, task): task for task in tasks}

        for future in as_completed(futures):
            idx, result = future.result()
            results[idx] = result
            completed += 1

            if completed % 100 == 0:
                print(f"  进度: {completed}/{iterations}")

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"\n结果:")
    print(f"  总调用次数: {iterations}")
    print(f"  总耗时: {elapsed:.2f}秒")
    print(f"  平均耗时: {elapsed * 1000 / iterations:.2f}ms/次")
    print(f"  吞吐量: {iterations / elapsed:.2f}次/秒")
    print(f"  验证: {sum(1 for r in results if r and r['verified'])}/{len(results)} 成功")

    return elapsed


def main():
    print("=" * 70)
    print("         性能对比测试：Context vs JSEngine")
    print("=" * 70)
    print(f"\nJS代码大小: {len(JS_CRYPTO_CODE)} 字节")
    print("测试算法: 加密解密 + 哈希计算")
    print("测试次数: 1000次调用")

    # 先运行一次热身
    print("\n正在热身...")
    engine = never_jscore.JSEngine(JS_CRYPTO_CODE, workers=2, enable_extensions=True)
    for _ in range(10):
        engine.call("processData", ["warmup", "key"])
    print("热身完成！")

    # 测试1: 单Context模式（每次重新加载）
    time1 = test_single_context_mode(iterations=1000)

    # 测试2: JSEngine单线程模式（只加载一次）
    time2 = test_jsengine_single_thread(iterations=1000)

    # 测试3: JSEngine多线程模式
    time3 = test_jsengine_multithread(iterations=1000, workers=8, max_threads=20)

    # 性能对比总结
    print("\n" + "=" * 70)
    print("                      性能对比总结")
    print("=" * 70)

    print(f"\n1. 单Context模式（每次重新加载JS）:")
    print(f"   耗时: {time1:.2f}秒")
    print(f"   速度: {1000 / time1:.2f}次/秒")

    print(f"\n2. JSEngine单线程模式（JS只加载一次）:")
    print(f"   耗时: {time2:.2f}秒")
    print(f"   速度: {1000 / time2:.2f}次/秒")
    print(f"   性能提升: {time1 / time2:.2f}x 倍")

    print(f"\n3. JSEngine多线程模式（8 Workers + 20 Python线程）:")
    print(f"   耗时: {time3:.2f}秒")
    print(f"   速度: {1000 / time3:.2f}次/秒")
    print(f"   相比单Context: {time1 / time3:.2f}x 倍")
    print(f"   相比JSEngine单线程: {time2 / time3:.2f}x 倍")

    print("\n" + "=" * 70)
    print("核心优势:")
    print("=" * 70)
    print(f"✓ 避免重复加载JS: {time1 / time2:.1f}x 性能提升")
    print(f"✓ 多线程并发处理: {time1 / time3:.1f}x 性能提升")
    print(f"✓ Worker池复用: JS代码只加载{8}次（每个Worker一次）")
    print(f"✓ 完全脱离GIL: Python多线程真正并行执行")
    print("=" * 70)


if __name__ == "__main__":
    main()
