"""
Test JSEngine hook with worker-isolated storage
"""

import sys
import os

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import never_jscore
import json
from concurrent.futures import ThreadPoolExecutor


def test_hook_with_worker_id():
    """Test basic hook with worker_id isolation"""
    print("\n=== Test 1: Basic Hook with Worker ID ===")

    engine = never_jscore.JSEngine("""
        function hookTest(data) {
            $terminate({message: data, timestamp: Date.now()});
        }
    """, workers=2, enable_extensions=True)

    # Call hook function
    result = engine.call("hookTest", ["test data"])

    print(f"Result: {result}")

    # Check if it's a hook result
    assert isinstance(result, dict)
    assert result.get("__hook__") == True
    assert "worker_id" in result
    assert "data" in result

    worker_id = result["worker_id"]
    print(f"Hook detected, worker_id: {worker_id}")

    # Extract hook data directly from result
    hook_data = result["data"]
    print(f"Hook data: {hook_data}")

    assert hook_data["message"] == "test data"
    assert "timestamp" in hook_data

    print("✓ Basic hook test passed")


def test_concurrent_hooks():
    """Test concurrent hooks with multiple workers"""
    print("\n=== Test 2: Concurrent Hooks ===")

    engine = never_jscore.JSEngine("""
        function processWithHook(id) {
            $terminate({
                taskId: id,
                squared: id * id,
                message: 'Task ' + id + ' completed'
            });
        }
    """, workers=4, enable_extensions=True)

    def worker_task(task_id):
        result = engine.call("processWithHook", [task_id])

        if isinstance(result, dict) and result.get("__hook__"):
            # Extract data directly from result
            hook_data = result.get("data")
            if hook_data:
                return task_id, hook_data, True

        return task_id, None, False

    # Run 20 concurrent hook tasks
    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(worker_task, range(20)))

    # Verify all tasks got correct data
    success_count = 0
    for task_id, hook_data, success in results:
        if success and hook_data:
            assert hook_data["taskId"] == task_id, f"Data mismatch: expected {task_id}, got {hook_data['taskId']}"
            assert hook_data["squared"] == task_id * task_id
            success_count += 1

    print(f"Success: {success_count}/20 tasks")
    assert success_count == 20, f"Expected 20 successes, got {success_count}"

    print("✓ Concurrent hook test passed")


def test_mixed_normal_and_hook():
    """Test mixing normal calls and hook calls"""
    print("\n=== Test 3: Mixed Normal and Hook Calls ===")

    engine = never_jscore.JSEngine("""
        function normalFunc(x) {
            return {type: 'normal', value: x * 2};
        }

        function hookFunc(x) {
            $terminate({type: 'hook', value: x * 3});
        }
    """, workers=4, enable_extensions=True)

    def process_task(args):
        task_id, use_hook = args

        if use_hook:
            result = engine.call("hookFunc", [task_id])
            if isinstance(result, dict) and result.get("__hook__"):
                # Extract data directly from result
                hook_data = result.get("data")
                if hook_data:
                    return task_id, hook_data["value"], "hook"
        else:
            result = engine.call("normalFunc", [task_id])
            return task_id, result["value"], "normal"

        return task_id, None, "error"

    # Mix of normal and hook calls
    tasks = [(i, i % 3 == 0) for i in range(30)]

    with ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_task, tasks))

    # Verify results
    for task_id, value, call_type in results:
        if call_type == "hook":
            assert value == task_id * 3
        elif call_type == "normal":
            assert value == task_id * 2
        else:
            assert False, f"Task {task_id} failed"

    print(f"Processed {len(results)} mixed calls")
    print("✓ Mixed call test passed")


def test_worker_recovery():
    """Test worker can continue after hook"""
    print("\n=== Test 4: Worker Recovery After Hook ===")

    engine = never_jscore.JSEngine("""
        function normalFunc(x) {
            return x + 100;
        }

        function hookFunc(x) {
            $terminate({hooked: x});
        }
    """, workers=1, enable_extensions=True)

    # Normal call
    result1 = engine.call("normalFunc", [1])
    assert result1 == 101
    print("Call 1 (normal): OK")

    # Hook call
    result2 = engine.call("hookFunc", [2])
    assert result2.get("__hook__") == True
    hook_data = result2.get("data")
    assert hook_data["hooked"] == 2
    print("Call 2 (hook): OK")

    # Normal call again - worker should be recovered
    result3 = engine.call("normalFunc", [3])
    assert result3 == 103
    print("Call 3 (normal after hook): OK")

    print("✓ Worker recovery test passed")


def main():
    print("=" * 70)
    print("  JSEngine Hook Tests - Worker-Isolated Storage")
    print("=" * 70)

    test_hook_with_worker_id()
    test_concurrent_hooks()
    test_mixed_normal_and_hook()
    test_worker_recovery()

    print("\n" + "=" * 70)
    print("✅ All hook tests passed!")
    print("=" * 70)
    print("\nKey improvements:")
    print("  ✓ Each worker has isolated hook data storage")
    print("  ✓ No data race between workers")
    print("  ✓ Hook data returned directly in result")
    print("  ✓ Workers recover correctly after hook")
    print("=" * 70)


if __name__ == "__main__":
    main()
