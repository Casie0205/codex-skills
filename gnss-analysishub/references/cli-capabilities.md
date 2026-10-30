# CLI Capabilities

This reference captures the current `AnalysisHub-cli` surface from the implementation in this workspace.

## Contents

- [Binary](#binary)
- [Top-level commands](#top-level-commands)
- [Global options](#global-options)
- [Data conversion](#data-conversion)
- [QC subcommands](#qc-subcommands)
- [`ctclib` subcommands](#ctclib-subcommands)
- [Report subcommands](#report-subcommands)
- [`iono` command](#iono-command)
- [`ssr` command](#ssr-command)
- [Plot command](#plot-command)
- [Recommended tool choice](#recommended-tool-choice)

## Binary

Typical build outputs in this workspace:

- `build_vs2022_qt51212\src\cli\RelWithDebInfo\AnalysisHub-cli.exe`
- `build_vs2022_qt51212\src\cli\Release\AnalysisHub-cli.exe`

## Top-level commands

- `qc`
- `report`
- `ctclib`
- `iono`
- `ssr`
- `convert`
- `accuracy`
- `survey`
- `tool`
- `plot`

Current implementation status:

- `qc`, `report`, `ctclib`, `iono`, `ssr`, `convert`, and `plot` are executable command families.
- `accuracy`, `survey`, and `tool` currently return reserved/help text only.

## Global options

The top-level parser currently accepts:

- `-j`, `--json`
- `--verbose`
- `--config <file>`
- `--output-dir <dir>`
- `--external-dir <dir>`

Current implementation notes:

- `--output-dir` and `--external-dir` are active in the current command surface.
- `--config` is parsed at the top level, but current subcommands mainly rely on explicit command-line options instead of an external config file; do not treat `--config` as a primary documented workflow without re-verifying the target command.

## Data conversion

Use the conversion CLI in two phases: pre-analyze each input, then run conversion with message names or exact selection keys.

### Pre-analyze message types and counts

```powershell
AnalysisHub-cli.exe convert analyze <input...> [options]
```

Options:

- `--vendor chc|un|nv|km` (default: `chc`)
- `--input-dir <dir>`
- `--pattern <patterns>` with comma-separated file patterns (default: `*`)
- `--recursive`
- `--json`

The text result reports `Message Type | Protocol | Format | Count | Unit | Key`. The exact `Key` is accepted by `convert run --include-key`; use it when a name has both ASCII and binary variants or when selecting only one `UNKNOWN` format.

Typical pre-analysis:

```powershell
AnalysisHub-cli.exe convert analyze E:\scene\m7xx.dat

AnalysisHub-cli.exe convert analyze `
  --input-dir E:\batch `
  --pattern "*.dat,*.log" `
  --recursive
```

### Run batch conversion

```powershell
AnalysisHub-cli.exe convert run <input...> [options]
```

Output targets:

- `--to ascii` converts selected messages to ASCII and is the default.
- `--to binary` converts selected messages to binary.
- `--to rinex --rinex-version <version>` converts to RINEX.
- RINEX versions: `2.11`, `3.01`, `3.02`, `3.03`, `3.04`, `4.00`.

Message selection:

- `--message <name>` selects one message name and may be repeated.
- `--messages <a,b,c>` selects comma-separated message names.
- `--message-file <file>` reads a UTF-8 list; lines may contain comma-separated names and `#` comments.
- `--include-key <key>` selects one exact key emitted by `convert analyze` and may be repeated.
- `--skip-missing-messages` lets each file continue when some requested names or keys are absent.
- If no message name or key is supplied, every selectable message detected in that file is converted.

Common options:

- `--vendor chc|un|nv|km` (default: `chc`)
- `--input-type auto|raw-ascii|raw-binary|rtcm3|rtcm2|hrcx|rinex|nmea`
- `--input-dir <dir>`
- `--pattern <patterns>`
- `--recursive`
- `--jobs <1..6>` (default: available CPU count, capped at 6)
- `--output-dir <dir>`
- `--json`

Output rules:

- Without `--output-dir`, each file writes outputs beside its source file.
- With `--output-dir`, all files use the shared output directory.
- Analysis and conversion progress is written per file to stderr.
- Batch exit code is `0` when all files succeed, `2` on partial success, `3` when every file fails, and `1` for argument or setup errors.
- JSON output uses `convert.analyze` or `convert.run` with per-file results, selected keys, missing selections, output files, and a summary.

Batch selected messages to ASCII:

```powershell
AnalysisHub-cli.exe convert run `
  --input-dir E:\batch `
  --pattern "*.dat,*.log" `
  --recursive `
  --to ascii `
  --messages "GNSSOBSCMP,GPSEPH,BD2EPH" `
  --skip-missing-messages `
  --jobs 4
```

Use a message list file for a stable batch profile:

```powershell
AnalysisHub-cli.exe convert run E:\batch\a.dat E:\batch\b.dat `
  --to ascii `
  --message-file E:\profiles\ascii_messages.txt `
  --skip-missing-messages
```

Select only ASCII `UNKNOWN` bytes rather than both `UNKNOWN` variants:

```powershell
AnalysisHub-cli.exe convert run E:\scene\m7xx.dat `
  --to ascii `
  --include-key UNKNOWN:ASCII:0
```

Convert to RINEX 3.04:

```powershell
AnalysisHub-cli.exe convert run E:\scene\m7xx.dat `
  --input-type auto `
  --to rinex `
  --rinex-version 3.04
```

Current implementation notes:

- `--message UNKNOWN` selects every detected `UNKNOWN` variant with that name; use `--include-key UNKNOWN:ASCII:0` or `UNKNOWN:BINARY:0` for one exact format.
- For heterogeneous files, combine explicit selections with `--skip-missing-messages`; otherwise one missing requested message makes that file fail preflight.
- For RINEX, omit message filters unless the user deliberately wants to restrict source message types.
- The CLI conversion flow and GUI `Tools -> Data Conversion...` use the same message-conversion service.

## QC subcommands

### ObsCheck

```powershell
AnalysisHub-cli.exe qc obscheck <file> [options]
```

### Diff epoch

```powershell
AnalysisHub-cli.exe qc diff-epoch <file> [options]
```

### Triple epoch

```powershell
AnalysisHub-cli.exe qc triple-epoch <file> [options]
```

### Zero baseline residual

```powershell
AnalysisHub-cli.exe qc residual <base-file> <rover-file> [options]
```

### Short baseline residual

```powershell
AnalysisHub-cli.exe qc short-residual <base-file> <rover-file> [options]
```

### Merge QC HTML reports

```powershell
AnalysisHub-cli.exe qc merge-reports --dir <dir> [-o <output.xlsx>]
AnalysisHub-cli.exe qc merge-reports --dir <dir> --recurse [-o <output.xlsx>]
AnalysisHub-cli.exe qc merge-reports file1.html file2.html ...
```

## Shared QC options

- `--ele-deg <deg>`
- `--interval <sec>`
- `--sys <systems>` such as `G,R,E,C`
- `--out-dir <dir>`
- `--data-type <n>`
- `--ban-prn <list>`
- `--start-time <time>`
- `--end-time <time>`
- `--ctclib-slip`
- `--doppler`
- `--dynamic`
- `--obsqcmp-mp`

Current implementation notes:

- The current CLI surface exposes elevation mask, interval, system set, output directory, data type, banned PRNs, start/end time, CTCLib slip enable, Doppler analysis, and dynamic-data marking.
- The current CLI surface also exposes `--obsqcmp-mp`, which matches the GUI `ObsQc MP mode` and routes QC execution to `CHCQC2.0_obsqcmp.exe`.
- The current `GnssConfig::defaults()` seed enables CTCLib slip check by default.
- `--ctclib-slip` is still accepted as an explicit CLI switch, but it now matches the default seed.
- There is no dedicated CLI flag in the current surface to force a legacy raw slip-detection mode off the default CTCLib path.

## `ctclib` subcommands

### Fixed-coordinate residual

```powershell
AnalysisHub-cli.exe ctclib app <rover_file> [options]
```

Options:

- `--coord x,y,z`
- `--base <file>`
- `--base-coord x,y,z`
- `--ref-gps <prn>`
- `--ref-bds <prn>`
- `--ref-glo <prn>`
- `--ref-gal <prn>`
- `--truth <file>`
- `--time <w1,s1,w2,s2>`

### Post-processing

```powershell
AnalysisHub-cli.exe ctclib post <rover_file> [options]
```

Options:

- `--base <file>`
- `--base-coord x,y,z`
- `--mode rtk|spp|rtd`
- `--sys <mask>`
- `--elmin <deg>`
- `--excluded-sats <list>`
- `--scene <mode>`

### One-click auto process + combined report

```powershell
AnalysisHub-cli.exe ctclib auto <rover_or_raw_file> [options]
```

Use this when the user wants the CLI equivalent of the GUI one-click chain.

Current implementation notes:

- This command runs fixed-coordinate residual first, then runs ObsCheck, then generates the combined report automatically.
- For single-file raw auto mode, omit `--base`. The same raw file is QC'd twice:
  - rover pass uses `ANT-1`
  - base pass uses `Baseobs`
- For rover+base RINEX mode, provide `--base <file>`.
- The combined output merges:
  - rover observation-score report
  - optional base observation-score report
  - fixed-coordinate residual report
- Default combined report file name is `<stem>_auto_process_report.html`.
- The QC side of the current auto-process path uses the CTCLib slip-check default.
- `--obsqcmp-mp` is valid here because `ctclib auto` builds its QC stage from the same `GnssConfig` and switches the QC executable to `CHCQC2.0_obsqcmp.exe`.
- When the scene artifacts already exist and only the report needs refresh, do not rerun `ctclib auto`; use `report auto-combined` instead.

`ctclib auto` accepts:

- all `ctclib app` options listed above
- the shared QC options listed earlier in this file

Typical outputs beside the selected output root or source folder include:

- `*_QC.html`
- `*_DataList.log`
- sibling `.MP` / `.MPresult` when generated by the QC stage
- `.arlog`
- `.pos`
- `<stem>_auto_process_report.html`

## Report subcommands

### Combined one-click report rebuild

```powershell
AnalysisHub-cli.exe report auto-combined --rover-datalist <file> --arlog <file> [options]
```

Primary options:

- `--rover-datalist <file>`
- `--base-datalist <file>`
- `--rover-qc <file>`
- `--base-qc <file>`
- `--rover-mp <file>`
- `--rover-mpresult <file>`
- `--base-mp <file>`
- `--base-mpresult <file>`
- `--arlog <file>`
- `--pos <file>`
- `--coord x,y,z`
- `--rover-title <text>`
- `--base-title <text>`
- `--fixed-title <text>`
- `--out-dir <dir>`
- `-o, --output <file>`

Current implementation notes:

- This command rebuilds the fixed-coordinate report plus the one-click combined report from existing artifacts.
- It requires at least:
  - `--rover-datalist`
  - `--arlog`
- `--base-datalist` is optional. If it is omitted, the combined report contains the rover observation-score section plus the fixed-coordinate section.
- If `--rover-qc`, `--rover-mp`, `--rover-mpresult`, `--base-qc`, `--base-mp`, or `--base-mpresult` are omitted, the command tries to derive sibling files from the `DataList` stem.
- If `--pos` is provided, the fixed-coordinate report can reuse the existing position file.
- If `--coord` is provided, the fixed report uses it as the reference ECEF coordinate.
- The implementation also regenerates fixed-report homepage detail charts from the selected satellite rows.
- Use this command after template, threshold, or report-layout changes when the upstream QC / CTCLib artifacts are already available.

### Health report

```powershell
AnalysisHub-cli.exe report health <qc_html> <datalist> [options]
```

Options:

- `--obs-file <file>`
- `--out-dir <dir>`
- `--gf-only`

Current implementation notes:

- CLI `report health` is suitable for QC-style health generation from existing `_QC.html + _DataList.log`.
- Current GUI logic still owns the mode-following `QC / DF / TF` workflow and the interactive follow-up path.

### RTK report

```powershell
AnalysisHub-cli.exe report rtk <qc_html> <datalist> [options]
```

Options are the same as `report health`.

### Ionosphere HTML report

```powershell
AnalysisHub-cli.exe report iono <IonosphereIndex_Ant0.txt|IonosphereIndex_Ant0.log|Ionosatinfodatalist.log|Ionosatinfodatalist.txt> [--out-dir <dir>] [-o <output.html>]
```

Current implementation notes:

- Accepts either the direct ionosphere result file or the parsed datalist-style intermediate file.
- If `-o` / `--output` is not specified, the default output file is written beside the input file.
- The default output name is `<input_stem>_iono_report.html`.
- `--out-dir` can redirect the default output directory without forcing an explicit file name.

### Observation-quality compare report

```powershell
AnalysisHub-cli.exe report obs-compare <datalist1> <datalist2> [datalistN...] [--out-dir <dir>]
```

Current implementation notes:

- This command needs at least two `DataList.log` inputs.
- It generates one HTML compare report plus CSV outputs.
- The current implementation tries to derive sibling `.MPresult`, `.MP`, and `_QC.html` files from each `DataList.log` stem when they exist.

## `iono` command

```powershell
AnalysisHub-cli.exe iono <input> [options]
```

Options:

- `--base <file>`
- `--coord x,y,z`
- `--rover-coord x,y,z`
- `--base-coord x,y,z`
- `--ref-gps <prn>`
- `--ref-bds <prn>`
- `--ref-glo <prn>`
- `--ref-gal <prn>`
- `--truth <file>`
- `--iono-mode auto|brdc|estimate|off`
- `--time <w1,s1,w2,s2>`
- `--rtcm-time <str>`

Current implementation notes:

- The same command covers both rover+base RINEX and single-file raw input.
- Provide `--base <file>` for rover+base RINEX mode.
- Omit `--base` for single-file raw / decoder-style mode.
- `--coord` and `--rover-coord` are aliases for rover fixed XYZ.
- Reference satellites are optional; `0` means auto-selection.
- `--truth <file>` enables the truth/reference coordinate file flow.
- Output may include:
  - ionosphere result log/index path
  - plot-data path such as `Ionosatinfodatalist.log`
  - HTML report path when report generation succeeds
- `auto` is the current default ionosphere mode.

## `ssr` command

```powershell
AnalysisHub-cli.exe ssr <log_file> [options]
```

Options:

- `--mode csm|upbeat`
- `--sub-mode C0|C1`
- `--decrypted <file>`

Current implementation notes:

- Default mode is `csm`.
- `--sub-mode` is meaningful for `csm` and defaults to `C0`.
- Output is a loss report text file plus structured loss items per packet type.

## Plot command

```powershell
AnalysisHub-cli.exe plot <file> [options]
```

Options:

- `-t, --type <type>`: `residual|cn0|elevation|skyplot|mp|gfmw|scatter`
- `-o, --output <file>`
- `-s, --system <sys>`: `ALL|GPS|BDS|GLO|GAL|QZS`
- `-f, --freq <idx>`
- `--width <px>`
- `--height <px>`

Current implementation notes:

- Auto-detection maps `DD / DF / TF` to `residual`
- `DataList` maps to `cn0`
- `MP` maps to `mp`
- `GF / MW / PsrCompare` map to the GF/MW-style path
- `skyplot` in CLI currently falls back to `cn0`

## Recommended tool choice

- Batch message conversion, QC, one-click auto process, combined-report rebuild, ionosphere, SSR loss analysis, merge, and plot export: use CLI
- Interactive per-file message selection: use GUI `Tools -> Data Conversion...`
- Health report from `_QC.html + _DataList.log`: CLI is fine
- Ionosphere report from existing `IonosphereIndex_Ant0.txt` or `Ionosatinfodatalist.log`: use CLI `report iono`
- Observation-quality compare from multiple `DataList.log`: use CLI `report obs-compare`
- Refreshing one-click reports after report-template changes: use CLI `report auto-combined`
- Health behavior that must follow active GUI mode `QC / DF / TF`: use GUI
- Interactive compare plotting: use GUI
- Interactive PPP-SSR chart review: use GUI `PPP-SSR...`
- Interactive residual/ionosphere page switching: use GUI `Residual / Ionosphere...`
- `accuracy`, `survey`, and `tool` topics currently need GUI or future implementation, not the current CLI

## Long-running demo hint

For large single-file QC jobs, the CLI may stay silent until completion. For demos, prefer the bundled progress wrapper:

```powershell
invoke_obscheck_with_progress.ps1 -InputFile <file> -OutputDir <dir> -DataType <n> -EleDeg <deg>
```
