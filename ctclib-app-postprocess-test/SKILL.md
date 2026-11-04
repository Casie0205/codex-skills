---
name: ctclib-app-postprocess-test
description: Run and maintain ctclib_app post-processing tests with copied CTCCFG configurations, controlled parameter changes, explicit output directories, and result validation.
---

# ctclib_app Post-process Test

Use this skill for CTCLib post-processing runs whose entrypoint is `ctclib_app.exe`
with a `.ctccfg` configuration.

## Executable Resolution

Resolve the executable in this order:

1. `$env:CTCLIB_APP_EXE`, when set.
2. `D:\Code\ctclib_test\ctclib_app.exe` on the current computer.
3. `D:\Code\ctclib-nav\exe\ctclib_app\Release32\ctclib_app.exe`.
4. `D:\Code\ctclib-nav\exe\ctclib_app\Debug64\ctclib_app.exe` only when the user
   explicitly requests the Debug build.

If none exists, stop and ask for the executable path. Do not silently switch versions.

## Workflow

1. Locate the run data directory, source configuration, and input observation file.
2. Read the source config before changing it. Identify the active section, exact key,
   current value, output mode, and input path.
3. Read [references/config-editing.md](references/config-editing.md) before creating or
   modifying a configuration copy.
4. Default to no parameter change when the user only asks to rerun.
5. For parameter tests, copy the source config into `forpost_list`, use a descriptive
   filename, set explicit absolute paths, and keep the original config unchanged.
6. Run the selected config with the resolved executable. Read
   [references/run-and-validation.md](references/run-and-validation.md) before execution.
7. Verify the configured output directory and expected result files.
8. Report the executable, config, input data, output directory, elapsed time, and every
   missing or failed artifact.

## Hard Rules

- Use `Release32` equivalent by default; use Debug only on explicit request.
- Use absolute paths for `file_input_obs_rover` and `dir_output`.
- Keep every modified config under `forpost_list`.
- Keep the original config unchanged.
- Do not invent parameter names or sections. Verify them against the active config or
  the full-version `ctclib.ctccfg`.
- When `selfoutput=1`, account for a time-named output directory. To force the configured
  `dir_output`, verify whether `selfoutput` must be `0`.
- Chinese comments must be trailing comments on parameter lines or omitted. Do not leave
  a Chinese-only comment line.
- Need a rebuild after source changes: stop and ask the user to rebuild. Do not compile.
- Never claim success without checking output files.

## References

- [references/config-editing.md](references/config-editing.md): path rules, config-copy
  conventions, output naming, comment rules, and parameter examples.
- [references/run-and-validation.md](references/run-and-validation.md): run commands,
  expected outputs, test scenarios, failure handling, and final report.
