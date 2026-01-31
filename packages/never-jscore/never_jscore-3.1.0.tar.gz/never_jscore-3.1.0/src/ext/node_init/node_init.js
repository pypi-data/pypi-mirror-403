// Initialize Node.js globals for never-jscore
// This runs after deno_node is loaded to set up require() globally

import { internals, primordials } from "ext:core/mod.js";
import { createRequire } from "node:module";
import { op_fs_cwd } from "ext:core/ops";
import { nodeGlobals } from "ext:deno_node/00_globals.js";

// CRITICAL: Set up internals.nodeGlobals for CJS module wrapper
// This is normally done in Deno's 99_main.js but never-jscore doesn't use that
// The CJS module wrapper in 01_require.js uses Deno[Deno.internal].nodeGlobals
// We use the same object reference (not a copy) so it stays in sync with 02_init.js
internals.nodeGlobals = nodeGlobals;

// Get the requireImpl from internals (before it's deleted by initialize)
const requireImpl = internals.requireImpl;

// Set up that we're using local node_modules
if (requireImpl && typeof requireImpl.setUsesLocalNodeModulesDir === "function") {
  requireImpl.setUsesLocalNodeModulesDir();
}

// Initialize the Node.js runtime if available
// This sets up process, Buffer, setTimeout, etc.
if (internals.node && typeof internals.node.initialize === "function") {
  try {
    internals.node.initialize({
      usesLocalNodeModulesDir: true,  // We use local node_modules
      argv0: "never-jscore",
      runningOnMainThread: true,
      workerId: null,
      maybeWorkerMetadata: null,
      nodeDebug: "",
      warmup: false,
      moduleSpecifier: null,
    });
  } catch (e) {
    // Ignore initialization errors - we'll set up what we can manually
    // console.log("Node bootstrap error:", e.message);
  }
}

// Find the project root by searching for node_modules directory
// This ensures require() works correctly regardless of where the script is run from
function findProjectRoot(startDir) {
  const { statSync } = globalThis.__bootstrap?.nodeFs || {};
  let dir = startDir;
  let prev = null;

  while (dir && dir !== prev) {
    try {
      // Try to check if node_modules exists in this directory
      const nodeModulesPath = dir + "/node_modules";
      // Use a simple existence check via require.resolve or fs
      try {
        if (statSync) {
          const stat = statSync(nodeModulesPath);
          if (stat && stat.isDirectory()) {
            return dir;
          }
        }
      } catch (e) {
        // statSync not available, try alternative method
      }

      // Alternative: try to use Deno.statSync if available
      if (typeof Deno !== "undefined" && Deno.statSync) {
        try {
          const stat = Deno.statSync(nodeModulesPath);
          if (stat.isDirectory) {
            return dir;
          }
        } catch (e) {
          // Directory doesn't exist, continue searching
        }
      }
    } catch (e) {
      // Ignore errors and continue searching
    }

    prev = dir;
    // Go up one directory
    const lastSlash = Math.max(dir.lastIndexOf("/"), dir.lastIndexOf("\\"));
    if (lastSlash > 0) {
      dir = dir.substring(0, lastSlash);
    } else {
      break;
    }
  }

  // Fallback to start directory
  return startDir;
}

// Create a global require function based on project root (where node_modules is)
const cwd = op_fs_cwd();
const projectRoot = findProjectRoot(cwd);
const requireFromCwd = createRequire(projectRoot + "/");

// Expose require globally
globalThis.require = requireFromCwd;

// Also expose module for compatibility
globalThis.module = {
  exports: {},
  id: ".",
  path: cwd,
  filename: cwd + "/index.js",
  loaded: false,
  children: [],
  paths: requireFromCwd.resolve.paths(".") || [],
};

// Export __dirname and __filename based on CWD
globalThis.__dirname = cwd;
globalThis.__filename = cwd + "/index.js";
