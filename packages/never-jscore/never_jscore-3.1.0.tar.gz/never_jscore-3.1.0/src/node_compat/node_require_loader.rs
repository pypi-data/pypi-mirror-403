// Node.js require loader implementation for never-jscore

use deno_core::FastString;
use deno_core::url::Url;
use deno_error::JsErrorBox;
use deno_node::{NodeRequireLoader, NodeRequireLoaderRc};
use deno_permissions::PermissionsContainer;
use node_resolver::errors::PackageJsonLoadError;
use std::borrow::Cow;
use std::path::Path;
use std::rc::Rc;

/// Simple NodeRequireLoader implementation for never-jscore
pub struct NeverJsCoreRequireLoader;

impl NeverJsCoreRequireLoader {
    pub fn new_rc() -> NodeRequireLoaderRc {
        Rc::new(Self)
    }

    /// Find the nearest package.json and check its "type" field
    fn find_package_type(file_path: &Path) -> Option<String> {
        let mut current = file_path.parent();

        while let Some(dir) = current {
            let package_json = dir.join("package.json");
            if package_json.exists() {
                if let Ok(content) = std::fs::read_to_string(&package_json) {
                    if let Ok(pkg) = serde_json::from_str::<serde_json::Value>(&content) {
                        if let Some(pkg_type) = pkg.get("type").and_then(|t| t.as_str()) {
                            return Some(pkg_type.to_string());
                        }
                    }
                }
                // Found package.json but no "type" field means CJS (default)
                return None;
            }
            current = dir.parent();
        }
        None
    }
}

impl NodeRequireLoader for NeverJsCoreRequireLoader {
    fn ensure_read_permission<'a>(
        &self,
        _permissions: &mut PermissionsContainer,
        path: Cow<'a, Path>,
    ) -> Result<Cow<'a, Path>, JsErrorBox> {
        // For now, allow all read operations
        // In production, you might want to implement proper permission checks
        Ok(path)
    }

    fn load_text_file_lossy(&self, path: &Path) -> Result<FastString, JsErrorBox> {
        // Read file and convert to FastString
        let content = std::fs::read_to_string(path)
            .map_err(|e| JsErrorBox::from_err(e))?;
        Ok(FastString::from(content))
    }

    fn is_maybe_cjs(&self, specifier: &Url) -> Result<bool, PackageJsonLoadError> {
        // Convert URL to file path
        let file_path = match specifier.to_file_path() {
            Ok(p) => p,
            Err(_) => return Ok(true), // Default to CJS if can't get path
        };

        // Check file extension first
        if let Some(ext) = file_path.extension().and_then(|e| e.to_str()) {
            match ext {
                "cjs" => return Ok(true),   // Explicit CommonJS
                "mjs" => return Ok(false),  // Explicit ESM
                "json" => return Ok(false), // JSON is not CJS
                _ => {}
            }
        }

        // For .js files, check package.json "type" field
        match Self::find_package_type(&file_path) {
            Some(ref t) if t == "module" => Ok(false),  // ESM
            _ => Ok(true),  // CJS (default when no type or type="commonjs")
        }
    }
}
