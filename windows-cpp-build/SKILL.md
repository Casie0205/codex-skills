---
name: windows-cpp-build
description: Build, diagnose, and repair Windows C++ solutions or projects through the local `windows-cpp-build` MCP, using MSBuild diagnostics instead of guessing. Use for `.sln` or `.vcxproj` builds, missing headers, compiler or linker errors, and build-fix-rebuild loops.
---

# Windows C++ Build

## Contents

- [Required Workflow](#required-workflow)
- [Build Completion](#build-completion)
- [Error Handling](#error-handling)
- [Tool Contract](#tool-contract)

Use the local `windows-cpp-build` MCP whenever a Windows C++ change must be validated. A source edit is not complete until a fresh build reports `success: true` and `exit_code: 0`.

## Required Workflow

1. Locate the actual `.sln` or `.vcxproj`; do not assume the nearest project is the intended target.
2. Call `discover_visual_studio` once to find MSBuild, or use an explicitly configured `msbuild_path`. When the project requires Visual Studio 2019, pass `version: "2019"` and `visual_studio_version: "2019"`; keep the toolset on `v142`.
3. Let the MCP locate and initialize `vcvarsall.bat` for `x86` before invoking MSBuild. Use `WINDOWS_CPP_VCVARS` only when automatic discovery is insufficient.
4. Do not pass a `platform` argument. The MCP always builds with MSBuild `/p:Platform=x86`; explicit `Platform` or `PlatformTarget` overrides are rejected.
5. Use a single configuration and target name. Do not put semicolons or shell metacharacters in `configuration`, `target`, or `extra_properties` values.
6. Start the build with `start_build_solution` or `start_build_project` and retain its `job_id`.
7. Build the unchanged baseline when practical, so existing failures are not attributed to the new edit.
8. Call `wait_for_build` repeatedly with the same `job_id` and the returned `next_cursor` until status is `succeeded`, `failed`, or `error`.
9. Read the reported messages, errors, and warnings. Fix one root cause at a time.
10. Start a new job and repeat the wait loop after every source or project-file change.
11. Report the exact target, configuration, fixed platform `x86`, environment status, exit code, and log path.

## Build Completion

Builds are asynchronous. `start_build_solution` and `start_build_project` return
immediately. Use `wait_for_build` with a maximum 30-second wait per call:

```toml
[mcp_servers.windows_cpp_build]
command = 'python'
args = ['-m', 'windows_cpp_build_mcp']
env = { PYTHONPATH = 'D:\Code\windows-cpp-build-mcp\src' }
tool_timeout_sec = 120
```

Each wait returns immediately when new output arrives, otherwise it waits at most 30
seconds. Continue polling while status is `running`; do not start a duplicate build
because a single wait timed out. Use `get_build_status` only when an immediate snapshot
is needed.

## Error Handling

- Treat `C1083` as a real file-resolution failure. When the message names an include file, find which include is missing, which file requested it, and whether the correct directory or package belongs in the project configuration. When it names a source file, check the project item path, generated-file step, and file existence.
- Do not add broad include directories to silence a missing-header error until the owning dependency and required include root are understood.
- Treat `LNK2019` and related link errors as ownership/definition/import-library problems, not as reasons to add arbitrary source files.
- When the build output is incomplete, call `parse_build_log` on the saved log instead of relying on the console tail.
- If `environment_initialized` is false, inspect `environment_error` and `vcvars_path`. For `MSB8020`, `MSB8008`, `MSB8036`, or missing `cl.exe`/`link.exe`, configure `WINDOWS_CPP_VCVARS` to the matching Visual Studio installation instead of changing project source.
- If no Visual Studio or MSBuild installation is found, report that environment blocker. Do not claim compilation succeeded.
- Do not silently fall back to Visual Studio 2022 or the `v143` toolset when the project requires Visual Studio 2019.

## Tool Contract

Read [references/tool-contract.md](references/tool-contract.md) when configuring the MCP, interpreting its results, or extending the server.
