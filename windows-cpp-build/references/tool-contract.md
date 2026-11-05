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
{}
```

Output:

- `vswhere_path`
- `installations[]`, including `installation_path`, `display_name`, `installation_version`, `msbuild_path`, and `vcvars_path`
- `errors[]`

### `build_solution`

Input:

```json
{
  "solution_path": "D:\\project\\app.sln",
  "configuration": "Debug",
  "platform": "x64",
  "restore": true,
  "clean": false,
  "timeout_seconds": 1800,
  "extra_properties": {}
}
```

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
- `timed_out`
- `duration_seconds`
- `target_path`
- `configuration`
- `platform`
- `command[]`
- `log_path`
- `errors[]`
- `warnings[]`
- `diagnostic_summary`
- `stdout_tail[]`

`solution_path`, `project_path`, and `log_path` must be absolute paths. `log_root` must also be absolute when supplied.

`success` is the primary completion field. It is true only when `exit_code == 0` and `timed_out == false`.

`diagnostic_summary` includes `total`, `errors`, `warnings`, `fatal`, and per-category counts.

## 4. Diagnostic categories

- `missing_include`: missing header or include path, typically `C1083`
- `source_file`: a missing or misplaced source or generated file
- `compile`: compiler semantic or syntax failure
- `link`: linker failure such as `LNK2019`
- `project_or_build`: MSBuild, project, toolset, or configuration failure
- `toolchain`: missing compiler, toolset, Windows SDK, or Visual Studio component, including `MSB8020` and `MSB8036`
- `project_or_build`: project configuration or general MSBuild failure
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
