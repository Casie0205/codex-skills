---
name: ctclib
description: Use when the user wants to decode CTCLib raw GNSS/INS data with ctclib_decode.exe, run navigation post-processing with ctclib_app.exe, or inspect the resulting CTCLib outputs.
---

# CTCLib

Status: verified on Windows on 2026-11-12.

## Contents

- [Purpose](#purpose)
- [Locate executables](#locate-executables)
- [Choose the workflow](#choose-the-workflow)
- [Decode raw data](#decode-raw-data)
- [Run navigation](#run-navigation)
- [Output layout](#output-layout)
- [Validate results](#validate-results)
- [Required rules](#required-rules)

## Purpose

This skill wraps exactly two executables:

- `ctclib_decode.exe`: analyze receiver raw data, extract IMU/VIO/RTCM/NovAtel
  content, and generate a post-processing config.
- `ctclib_app.exe`: read a `.ctccfg` file and run GNSS/INS navigation
  post-processing.

Prefer the packaged scripts over rebuilding ad hoc command lines.

## Locate executables

Resolve the installation directory in this order:

1. `-CtclibHome`.
2. Environment variable `CTCLIB_HOME`.
3. Default installation root `D:\Code\ctclib_exe`.

The supplied directory may be either:

- the installation root containing one or more version directories; or
- an exact directory that directly contains the executables.

When given a root, search recursively for directories that contain all required
files. If several complete installations exist, select the one with the highest
numeric version directory. Pass an exact executable directory in `-CtclibHome`
or `CTCLIB_HOME` when a specific build must be used.

Each resolved installation directory must contain:

```text
ctclib_decode.exe
ctclib_app.exe
Decrypter.dll
```

Do not assume a fixed release subdirectory under `D:\Code\ctclib_exe`; package
layouts can change between releases.

`ctclib_app.exe` cannot start without `Decrypter.dll`. Registration is stored
under:

```text
HKEY_CURRENT_USER\SOFTWARE\WOW6432Node\CTCLib4.0\Decrypt
```

## Choose the workflow

- Raw-data analysis, IMU/VIO inspection, or decode-generated config: use the
  decode workflow.
- Existing `.ctccfg` and requested INS/GNSS result: use the navigation
  workflow.
- Raw input plus requested navigation result: decode first, then run
  navigation with the generated `ctclibdec_forpost.ctccfg`.

## Decode raw data

Run:

```powershell
& "<skill-root>\scripts\run-decode.ps1" `
  -InputFile "<raw-file>" `
  -Workspace "D:\Output\<dataset-root>\ctclib\decode_<timestamp>"
```

The script:

- resolves the input to an absolute path;
- hard-links or copies it into the workspace;
- runs `ctclib_decode.exe -b`;
- writes decoded output to
  `<workspace>\source\<input-stem>_ctclibdec`;
- writes command, console, and JSON summaries under `<workspace>\_run`.

Use `-PlanOnly` to inspect paths without execution. Use `-NoStage` only when
the user explicitly permits decoding beside the source data.
`-TimeoutSeconds` defaults to 900; increase it for unusually large inputs.

Read [references/decode-workflow.md](references/decode-workflow.md) before
interpreting decoded outputs or the `CSM has not been decrypted` message.

## Run navigation

Run:

```powershell
& "<skill-root>\scripts\run-solve.ps1" `
  -ConfigFile "<config.ctccfg>" `
  -OutputDir "D:\Output\<dataset-root>\ctclib\<run-name>"
```

The script:

- preserves the source config;
- writes `ctclib.derived.ctccfg` under the run directory;
- converts `file_input_obs_rover` to an absolute path;
- sets `selfoutput=0` and the requested `dir_output`;
- runs `ctclib_app.exe` with the derived config.

If the CTCLib registration is missing, the script exits with
`license_required` before launching the application. A bounded process timeout
also prevents an unexpected registration prompt from waiting forever.

Use `-UseConfigOutput` only when the source config's output location must be
preserved. Use `-Force` only after explicit approval to reuse a non-empty
output directory.
`-TimeoutSeconds` defaults to 900 and bounds the application process.

Read [references/navigation-workflow.md](references/navigation-workflow.md)
before building or interpreting a navigation config.

## Output layout

Never create new ctclib outputs under the generic `D:\Output\ctclib` root.
Use a dataset-specific output folder instead:

```text
D:\Output\<dataset-root>\
  ctclib\
    decode_<timestamp>\
    <run-name>\
    runs\
```

Example:

```text
D:\Output\M720_20261109_160537\ctclib\decode_20261109_193000
```

Use the raw dataset folder name as `<dataset-root>`. The packaged scripts
reject paths below `D:\Output\ctclib` and require an explicit dataset-specific
workspace or output directory.

## Validate results

After decoding, verify:

- exit code is `0`;
- the `_ctclibdec` directory exists and is non-empty;
- `ctclibdec_forpost.ctccfg` exists and is non-zero;
- at least one non-zero extracted data output exists; a log alone is not enough;
- for IMU-bearing inputs, `ctclibdec_imu.txt` has `IMU,` rows;
- for VIO-bearing inputs, `ctclibdec_vio.prodef` has `VIO,` rows.

After navigation, verify:

- exit code is `0`;
- the output directory contains `ins_novatel.ASC` or the current build's
  equivalent primary result;
- `ctclib.ctccfg`, when present, confirms the actual input and output paths;
- GNSS interruption checks use measured status transitions in
  `ins_novatel.ASC`, not only the config text.

Do not determine success from console text or exit code alone.

## Required rules

- Use absolute paths for inputs, configs, and outputs.
- Do not overwrite existing decode or navigation results without explicit
  user approval.
- Reusing an existing decode output requires `-Force`, and only newly created
  or changed config/data files count as success.
- Reusing a non-empty navigation output directory requires `-Force`, and only
  newly created or changed primary files count as success.
- Treat `ERROR! CSM has not been decrypted yet!` as a possible normal internal
  format message; validate the output files and data rows.
- Do not interpret standard deviations as truth-referenced errors.
- Do not apply `ins_insplot.txt` column definitions to `ins_novatel.ASC`, or
  the reverse.
