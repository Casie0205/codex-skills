---
name: ctc-postprocess-test
description: Run and maintain ctclib_app post-processing tests with copied CTCCFG configurations, controlled parameter changes, explicit output directories, and result validation.
---

# ctclib_app Post-process Test

## Contents

- [Executable Resolution](#executable-resolution)
- [Workflow](#workflow)
- [Batch Test Layout](#batch-test-layout)
- [Configuration Requirements](#configuration-requirements)
- [Hard Rules](#hard-rules)
- [References](#references)

Use this skill for CTCLib post-processing runs whose entrypoint is `ctclib_app.exe`
with a `.ctccfg` configuration.

## Executable Resolution

Resolve the executable in this order:

1. `$env:CTCLIB_APP_EXE`, when set.
2. `D:\Code\ctclib-nav\exe\ctclib_app\Release32\ctclib_app.exe`.
3. `D:\Code\ctclib-nav\exe\ctclib_app\Debug64\ctclib_app.exe` only when the user
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
   filename, set explicit absolute paths, and keep the original config unchanged. For a
   batch test, use the layout in [Batch Test Layout](#batch-test-layout).
6. Run the selected config with the resolved executable. Read
   [references/run-and-validation.md](references/run-and-validation.md) before execution.
7. Verify the configured output directory and expected result files.
8. Report the executable, config, input data, output directory, elapsed time, and every
   missing or failed artifact.

## Batch Test Layout

For a set of configurations that belongs to one batch test:

1. Create a descriptive subdirectory under `<data-directory>\forpost_list`.
2. Copy every configuration used by that batch into the subdirectory.
3. Use descriptive configuration names and a separate absolute `dir_output` for each
   run.
4. Run the configurations sequentially unless the user explicitly permits otherwise.

Example:

```text
<data-directory>\forpost_list\<batch-name>\
|-- hcnav_forpost_gimode0_loosely.ctccfg
`-- hcnav_forpost_gimode1_tightly.ctccfg
```

## Configuration Requirements

- Do not leave a standalone line that contains only a Chinese comment in `.ctccfg`.
  Use a trailing Chinese comment on a parameter line or omit the comment.
- `gnss_interrupt_start_time` and `gnss_interrupt_end_time` take seconds of week only.
  Do not include a GPS week number or a full GPS week/time value.

## Hard Rules

- Use `Release32` equivalent by default; use Debug only on explicit request.
- Use absolute paths for `file_input_obs_rover` and `dir_output`.
- Keep every modified config under `forpost_list`.
- Keep each batch's configurations together under a batch subdirectory of
  `forpost_list`.
- Keep the original config unchanged.
- Do not invent parameter names or sections. Verify them against the active config or
  the full-version `ctclib.ctccfg`.
- When `selfoutput=1`, account for a time-named output directory. To force the configured
  `dir_output`, verify whether `selfoutput` must be `0`.
- Never write a standalone Chinese-only comment line in `.ctccfg`.
- Fill `gnss_interrupt_start_time` and `gnss_interrupt_end_time` with seconds of week
  only, without a GPS week number.
- Need a rebuild after source changes: stop and ask the user to rebuild. Do not compile.
- Never claim success without checking output files.

## References

- [references/config-editing.md](references/config-editing.md): path rules, config-copy
  conventions, output naming, comment rules, and parameter examples.
- [references/run-and-validation.md](references/run-and-validation.md): run commands,
  expected outputs, test scenarios, failure handling, and final report.
