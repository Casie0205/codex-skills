---
name: windows-cpp-build
description: Build, diagnose, and repair Windows C++ solutions or projects through the local `windows-cpp-build` MCP, using MSBuild diagnostics instead of guessing. Use for `.sln` or `.vcxproj` builds, missing headers, compiler or linker errors, and build-fix-rebuild loops.
---

# Windows C++ Build

## Contents

- [Required Workflow](#required-workflow)
- [Error Handling](#error-handling)
- [Tool Contract](#tool-contract)

Use the local `windows-cpp-build` MCP whenever a Windows C++ change must be validated. A source edit is not complete until a fresh build reports `success: true`, `exit_code: 0`, and `timed_out: false`.

## Required Workflow

1. Locate the actual `.sln` or `.vcxproj`; do not assume the nearest project is the intended target.
2. Call `discover_visual_studio` once to find MSBuild, or use an explicitly configured `msbuild_path`. When the project requires Visual Studio 2019, pass `version: "2019"` and `visual_studio_version: "2019"`; keep the toolset on `v142`.
3. Use the MCP default platform `x86` unless the task brief or project explicitly requires another platform. If the solution defines `Win32`, `x64`, or `ARM64`, pass that exact platform name.
4. Build the unchanged baseline when practical, so existing failures are not attributed to the new edit.
5. Read the reported errors and warnings. Fix one root cause at a time.
6. Rebuild the same target after every source or project-file change.
7. Report the exact target, configuration, platform, exit code, and log path.

## Error Handling

- Treat `C1083` as a real file-resolution failure. When the message names an include file, find which include is missing, which file requested it, and whether the correct directory or package belongs in the project configuration. When it names a source file, check the project item path, generated-file step, and file existence.
- Do not add broad include directories to silence a missing-header error until the owning dependency and required include root are understood.
- Treat `LNK2019` and related link errors as ownership/definition/import-library problems, not as reasons to add arbitrary source files.
- When the build output is incomplete, call `parse_build_log` on the saved log instead of relying on the console tail.
- If no Visual Studio or MSBuild installation is found, report that environment blocker. Do not claim compilation succeeded.
- Do not silently fall back to Visual Studio 2022 or the `v143` toolset when the project requires Visual Studio 2019.

## Tool Contract

Read [references/tool-contract.md](references/tool-contract.md) when configuring the MCP, interpreting its results, or extending the server.
