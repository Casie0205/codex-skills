# Windows C++ Build MCP Contract

## 目录

- [1. Purpose](#1-purpose)
- [2. Tools](#2-tools)
- [3. Result fields](#3-result-fields)
- [4. Diagnostic categories](#4-diagnostic-categories)
- [5. Output locations](#5-output-locations)
- [6. Configuration](#6-configuration)

## 1. Purpose

The MCP provides a deterministic Windows build loop for C++ projects. It does not automate the Visual Studio UI. It discovers Visual Studio, invokes MSBuild, saves the full build log, parses compiler and linker diagnostics, and returns machine-readable evidence.

## 2. Tools

### `discover_visual_studio`

Input:

```json
{"version": "2019"}
```

Output:

- `vswhere_path`
- `requested_version`
- `installations[]`, including `installation_path`, `display_name`, `installation_version`, `msbuild_path`, and `vcvars_path`
- `errors[]`

### `build_solution`

Input:

```json
{
  "solution_path": "D:\\project\\app.sln",
  "configuration": "Debug",
  "visual_studio_version": "2019",
  "restore": true,
  "clean": false,
  "extra_properties": {}
}
```

The MCP always passes MSBuild `/p:Platform=x86`. `build_solution` and `build_project`
do not expose a `platform` argument; passing one is rejected instead of being silently
ignored. `extra_properties` rejects `Platform` and `PlatformTarget`, property names
outside the supported identifier format, and values containing property separators,
shell metacharacters, quotes, or control characters so callers cannot inject another
property. `extra_properties` therefore supports scalar values only, not semicolon-list
properties such as `PreprocessorDefinitions=FOO;BAR`.

The build call is synchronous. It waits until MSBuild exits, then returns the actual
process exit code and parsed diagnostics. There is no `timeout_seconds` argument and no
server-side build-duration cutoff.

Before invoking MSBuild, the MCP derives `vcvarsall.bat` from the selected Visual Studio
installation, runs it for `x86`, captures the resulting environment, and passes that
environment to the MSBuild process. This supplies `INCLUDE`, `LIB`, `PATH`, and related
Visual C++ variables while keeping the build command itself as a direct process call.

When the request includes `_meta.progressToken`, the server emits
`notifications/progress` immediately after starting MSBuild, for each non-empty output line,
and once when the process exits. Progress messages are live status only; the final tool
result remains authoritative.

### `build_project`

Uses the same input shape as `build_solution`, with `project_path` replacing `solution_path`.

### `parse_build_log`

Input:

```json
{
  "log_path": "D:\\Output\\windows-cpp-build-mcp\\build-logs\\app\\20261105-120000\\build.log"
}
```

## 3. Result fields

Build tools return:

- `success`
- `exit_code`
- `duration_seconds`
- `target_path`
- `configuration`
- `platform` (always `x86`)
- `vcvars_path`
- `environment_initialized`
- `environment_error`
- `visual_studio_version`
- `command[]`
- `log_path`
- `errors[]`
- `warnings[]`
- `diagnostic_summary`
- `stdout_tail[]`

`solution_path`, `project_path`, and `log_path` must be absolute paths. `log_root` must also be absolute when supplied.

`success` is the primary completion field. It is true only when `exit_code == 0`.

`diagnostic_summary` includes `total`, `errors`, `warnings`, `fatal`, and per-category counts.

## 4. Diagnostic categories

- `missing_include`: missing header or include path, typically `C1083`
- `source_file`: a missing or misplaced source or generated file
- `compile`: compiler semantic or syntax failure
- `link`: linker failure such as `LNK2019`
- `project_or_build`: MSBuild, project, toolset, or configuration failure
- `toolchain`: missing compiler, toolset, Windows SDK, or Visual Studio component, including `MSB8020` and `MSB8036`
- `other`: a diagnostic that does not match a known code

## 5. Output locations

Build logs default to:

```text
D:\Output\windows-cpp-build-mcp\build-logs\<target-name>\<timestamp>\
```

Set `WINDOWS_CPP_BUILD_LOG_ROOT` to override the root. Each build directory contains `build.log`.

## 6. Configuration

The server uses these discovery paths unless `msbuild_path` is supplied:

1. `WINDOWS_CPP_MSBUILD`
2. Visual Studio installations reported by `vswhere.exe`
3. `PATH`

Use an explicit MSBuild path when multiple toolchains are installed and the project requires a specific one.

`vcvarsall.bat` resolution order:

1. `WINDOWS_CPP_VCVARS`
2. Visual Studio installation derived from the selected `MSBuild.exe`
3. Visual Studio installations reported by `vswhere.exe`

A `vcvarsall.bat` path containing `^` or `%` is rejected because it cannot be passed
safely through `cmd.exe`; use the normal Visual Studio installation path.

For Visual Studio 2019, set `WINDOWS_CPP_VS_VERSION` to `[16.0,17.0)` or pass `visual_studio_version: "2019"` to the build tools. Keep the project on `PlatformToolset=v142`; do not let it fall through to the v143 toolset from Visual Studio 2022.

The MCP waits for MSBuild to finish regardless of build duration. Set the Codex MCP
client timeout to a transport safety limit of 24 hours:

```toml
[mcp_servers.windows_cpp_build]
command = 'python'
args = ['-m', 'windows_cpp_build_mcp']
env = { PYTHONPATH = 'D:\Code\windows-cpp-build-mcp\src' }
tool_timeout_sec = 86400
```
