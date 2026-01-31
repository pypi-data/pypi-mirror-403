"""
never_jscore - 基于 Deno Core 的高性能 JavaScript 运行时

High-performance Python JavaScript execution engine based on Deno Core (V8)
with full Promise/async support.

Features:
- Full Deno Web API support (fetch, URL, crypto, etc.)
- Node.js compatibility mode (require, npm packages)
- Deterministic random number generation
- Hook interception ($terminate, $return)
- Worker pool architecture for 10-20x performance improvement (v3.0)

v3.0 Architecture:
- JSEngine (NEW): Recommended for multi-threaded scenarios, JS code loaded only once
- Context (LEGACY): Backward compatible API
"""

from .never_jscore import Context, JSEngine

__version__ = "2.5.2"
__all__ = ["Context", "JSEngine"]
