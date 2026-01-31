// Node.js bootstrap initialization extension for never-jscore
// Must be loaded BEFORE deno_node to create __bootstrap.ext_node_* objects
//
// This fixes the error: "Cannot read properties of undefined (reading 'nodeGlobals')"
// which occurs because deno_node's 00_globals.js runs during JsRuntime::new()
// and expects __bootstrap.ext_node_nodeGlobals to already exist.

use std::rc::Rc;
use deno_core::v8;
use deno_core::Extension;

// Re-export GlobalsStorage from deno_node for compatibility
pub use deno_node::GlobalsStorage;

/// Middleware that creates __bootstrap.ext_node_nodeGlobals and ext_node_denoGlobals
/// This must run BEFORE deno_node's ESM modules are loaded
pub fn bootstrap_global_object_middleware<'s>(
    scope: &mut v8::PinScope<'s, '_>,
    global: v8::Local<'s, v8::Object>,
) {
    // Create __bootstrap if it doesn't exist
    let bootstrap_key = v8::String::new(scope, "__bootstrap").unwrap();
    let bootstrap = match global.get(scope, bootstrap_key.into()) {
        Some(value) if value.is_object() => value.to_object(scope).unwrap(),
        _ => {
            let null = v8::null(scope);
            let obj = v8::Object::with_prototype_and_properties(scope, null.into(), &[], &[]);
            global.set(scope, bootstrap_key.into(), obj.into());
            obj
        }
    };

    // Create ext_node_denoGlobals
    let deno_globals_key = v8::String::new(scope, "ext_node_denoGlobals").unwrap();
    let deno_globals = match bootstrap.get(scope, deno_globals_key.into()) {
        Some(value) if value.is_object() => value,
        _ => {
            let null = v8::null(scope);
            let obj: v8::Local<v8::Value> = v8::Object::with_prototype_and_properties(scope, null.into(), &[], &[]).into();
            bootstrap.set(scope, deno_globals_key.into(), obj);
            obj
        }
    };
    let deno_globals_obj: v8::Local<v8::Object> = deno_globals.try_into().unwrap();
    let deno_globals = v8::Global::new(scope, deno_globals_obj);

    // Create ext_node_nodeGlobals
    let node_globals_key = v8::String::new(scope, "ext_node_nodeGlobals").unwrap();
    let node_globals = match bootstrap.get(scope, node_globals_key.into()) {
        Some(value) if value.is_object() => value,
        _ => {
            let null = v8::null(scope);
            let obj: v8::Local<v8::Value> = v8::Object::with_prototype_and_properties(scope, null.into(), &[], &[]).into();
            bootstrap.set(scope, node_globals_key.into(), obj);
            obj
        }
    };
    let node_globals_obj: v8::Local<v8::Object> = node_globals.try_into().unwrap();
    let node_globals = v8::Global::new(scope, node_globals_obj);

    // Store in context slot for deno_node's property handlers to access
    let storage = GlobalsStorage::new(deno_globals, node_globals);
    scope.get_current_context().set_slot(Rc::new(storage));
}

deno_core::extension!(
    never_jscore_node_bootstrap,
    global_object_middleware = bootstrap_global_object_middleware,
);

pub fn init() -> Extension {
    never_jscore_node_bootstrap::init()
}
