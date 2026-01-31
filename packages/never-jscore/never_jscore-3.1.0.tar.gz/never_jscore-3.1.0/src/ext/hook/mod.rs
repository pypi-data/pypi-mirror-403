use deno_core::{extension, Extension, OpState};
use super::ExtensionTrait;

use crate::storage::{save_hook_data, save_hook_data_for_worker, WorkerId};

/// Op: Save Hook intercepted data to global storage (new version, used with terminate_execution)
///
/// Save data before calling op_terminate_execution.
/// Data is saved to global static HashMap, keyed by worker_id for thread safety.
#[deno_core::op2]
#[string]
pub fn op_save_hook_data(state: &mut OpState, #[string] data: String) -> String {
    // 尝试从 OpState 获取 WorkerId（Worker Pool 场景）
    if let Some(worker_id) = state.try_borrow::<WorkerId>() {
        // Worker Pool 场景：使用 worker_id 作为 key
        save_hook_data_for_worker(worker_id.0, data.clone());
    } else {
        // Context 场景：使用默认的 worker_id = 0
        save_hook_data(data.clone());
    }
    data
}

/// Op: Terminate JavaScript execution
///
/// Calls V8's terminate_execution(), which cannot be caught by try-catch.
/// Must be used with op_save_hook_data - save data first, then terminate.
///
/// ⚠️ Note: This op requires access to V8 IsolateHandle,
/// which must be stored during Context initialization.
#[deno_core::op2(fast)]
pub fn op_terminate_execution(state: &mut OpState) {
    // Get IsolateHandle from OpState
    if let Some(handle) = state.try_borrow_mut::<deno_core::v8::IsolateHandle>() {
        handle.terminate_execution();
    }
}

// Hook extension - provides JavaScript termination and data interception
extension!(
    init_hook,
    ops = [op_terminate_execution, op_save_hook_data]
);

impl ExtensionTrait<()> for init_hook {
    fn init(_: ()) -> Extension {
        init_hook::init()
    }
}

/// Get the JavaScript initialization code for hook functions
pub fn get_init_js() -> &'static str {
    include_str!("init_hook.js")
}

/// Build hook extensions
pub fn extensions(_options: (), is_snapshot: bool) -> Vec<Extension> {
    vec![init_hook::build((), is_snapshot)]
}

// Re-export hook utility functions for use in context.rs
pub use crate::storage::{get_hook_data as get_hook_data_storage, clear_hook_data as clear_hook_data_storage};
