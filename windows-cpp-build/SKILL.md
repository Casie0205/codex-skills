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
3. Do not pass a `platform` argument. The MCP always builds with MSBuild `/p:Platform=x86`; an explicit platform override is rejected.
4. Build the unchanged baseline when practical, so existing failures are not attributed to the new edit.
5. Read the reported errors and warnings. Fix one root cause at a time.
6. Rebuild the same target after every source or project-file change.
7. Report the exact target, configuration, fixed platform `x86`, exit code, and log path.

## Build Completion

The MCP does not impose a build-duration timeout. It waits for the MSBuild process to
exit and then returns parsed diagnostics for either success or failure.

When the client supplies `_meta.progressToken`, the MCP emits
`notifications/progress` immediately after starting MSBuild and for each non-empty
output line. A start notification means the build is active; continue waiting for the
final tool result instead of retrying or treating the call as unresponsive.

Codex still applies a client-side request timeout. Configure a 24-hour transport safety
limit so a normal long build is not cut off:

```toml
[mcp_servers.windows_cpp_build]
command = 'python'
args = ['-m', 'windows_cpp_build_mcp']
env = { PYTHONPATH = 'D:\Code\windows-cpp-build-mcp\src' }
tool_timeout_sec = 86400
```

Treat the client setting as a hung-request guard, not as a build policy. Do not stop or
duplicate a build based only on elapsed time while the MCP call is still running.

## Error Handling

- Treat `C1083` as a real file-resolution failure. When the message names an include file, find which include is missing, which file requested it, and whether the correct directory or package belongs in the project configuration. When it names a source file, check the project item path, generated-file step, and file existence.
- Do not add broad include directories to silence a missing-header error until the owning dependency and required include root are understood.
- Treat `LNK2019` and related link errors as ownership/definition/import-library problems, not as reasons to add arbitrary source files.
- When the build output is incomplete, call `parse_build_log` on the saved log instead of relying on the console tail.
- If no Visual Studio or MSBuild installation is found, report that environment blocker. Do not claim compilation succeeded.
- Do not silently fall back to Visual Studio 2022 or the `v143` toolset when the project requires Visual Studio 2019.

## Tool Contract

Read [references/tool-contract.md](references/tool-contract.md) when configuring the MCP, interpreting its results, or extending the server.
