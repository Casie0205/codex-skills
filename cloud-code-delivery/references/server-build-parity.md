# Server Build Parity

状态：active | 更新日期：2026-11-12

## 目录

- [1. Purpose](#1-purpose)
- [2. Identify the Required Targets](#2-identify-the-required-targets)
- [3. Check Source Membership](#3-check-source-membership)
- [4. Build the Full Matrix](#4-build-the-full-matrix)
- [5. Evidence and Status](#5-evidence-and-status)
- [6. CTCLib Example](#6-ctclib-example)

## 1. Purpose

Prevent a change from passing one cloud project while failing the solution or project
used by the server. A Visual Studio `.vcxproj` has its own source list. Adding a new
`.c` or `.cpp` file to one target does not add its object code to sibling targets that
compile the same shared translation unit.

## 2. Identify the Required Targets

Read `server_build_targets` from the task brief. Each target must name:

- solution or project path;
- target project;
- configuration;
- platform.

When a task changes project membership, a shared source, or a source consumed by
multiple applications, also inspect the server/deployment documentation and solution
tree. If the deployment target cannot be identified, report `BLOCKED`; do not infer
parity from a convenient local target.

## 3. Check Source Membership

For every new implementation file, find every project that compiles a translation unit
which calls or references it. Use:

Resolve `$PYTHON` and `$PYTHON_ARGS` with
[windows-shell-policy.md](windows-shell-policy.md) before running the commands.

```powershell
& $PYTHON @PYTHON_ARGS "<skill-root>\scripts\check_project_source_coverage.py" `
  --repo "<repo_path>" `
  --project-root "<repo_path>\proj" `
  --anchor-source "<repository-relative anchor source>" `
  --required-source "<repository-relative required source>" `
  --configuration "<server configuration>" `
  --platform "<server platform>"
```

Example: if `DataDecoder.c` calls `ImuTimeAlignment_*`, every project that compiles
`DataDecoder.c` must also compile `ImuTimeAlignment.c`.

The source must be present in each actual `.vcxproj`. A matching
`.vcxproj.filters` entry affects IDE presentation only and does not satisfy the linker.
After editing project XML, parse every changed `.vcxproj` and `.vcxproj.filters` with an
XML parser.

The checker counts only active `ClCompile` items. `ClInclude`, `None`,
`ExcludedFromBuild=true`, a nonmatching condition, or an unresolved MSBuild property does
not count as compiled source. Unsupported conditions or properties produce an
`INDETERMINATE` result instead of a false pass.

## 4. Build the Full Matrix

At minimum build:

1. the server/deployment solution and target, using the server configuration and
   platform;
2. every other production target affected by project-membership or shared-source
   changes;
3. the unit-test target.

Use rebuild rather than relying on stale objects when diagnosing source-membership
changes. A successful build of one app target does not prove that a sibling app or the
solution links successfully.

Coverage checking and building must use the same source tree and commit. If the repository
is mirrored or copied to a separate server/build tree, rerun the coverage checker against
that exact tree immediately before building.

Record for each item:

| Field | Meaning |
| --- | --- |
| solution | Absolute solution path |
| project | Built project name |
| configuration | Example: `Release` |
| platform | `x86`; fixed by the `windows-cpp-build` MCP |
| exit_code | Actual process exit code |
| output | Produced executable or library |
| evidence | Key compiler/linker summary |

## 5. Evidence and Status

- Unknown server target: `BLOCKED`.
- Source coverage checker finds a missing project: fix all listed projects before
  building.
- Server build fails after code is committed: use `PARTIAL` and include the linker or
  compiler evidence. Do not claim `DONE`.
- A successful server build does not replace unit, runtime, or end-to-end evidence; keep
  those checks independent.
- Include the complete build matrix in `verification.log` and the HTML result report.

## 6. CTCLib Example

The `windows-cpp-build` MCP has no platform argument and always passes
`/p:Platform=x86`. The source-coverage checker still accepts `--platform` because it
evaluates project conditions; use `x86` for parity with the build.

For the IMU time-alignment change:

```powershell
& $PYTHON @PYTHON_ARGS "<skill-root>\scripts\check_project_source_coverage.py" `
  --repo "D:\Code\ctclib-nav" `
  --project-root "D:\Code\ctclib-nav\proj" `
  --anchor-source "proj\ctclib_app\src\DataDecoder\DataDecoder.c" `
  --required-source "proj\ctclib_app\src\AppProcessor\RTKCore\ImuTimeAlignment.c" `
  --configuration "Release" `
  --platform "x86"
```

Then build the equivalent server target from the same tree:

```powershell
msbuild "D:\Code\ctclib-nav\CTCLIB-SURVEY.sln" `
  /t:ReBuild /p:Configuration=Release /p:Platform=x86
```

If the deployment tree is `D:\ctclib2.1\ctclib2.1-nav-windows\ctclib-nav`, rerun the
coverage command with `--repo` and `--project-root` pointing to that tree, then build its
`CTCLIB-SURVEY.sln`. Also build `ctclib_app_agri` and `UnitTest`. A prior Agri-only build
cannot justify marking the Survey task `DONE`.
