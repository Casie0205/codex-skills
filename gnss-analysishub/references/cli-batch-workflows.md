# CLI Batch Workflows

Use this reference when the user asks how to batch `AnalysisHub-cli` commands across many folders, scenes, or countries.

## Core Idea

Do not describe batch work as one large shell loop.

Treat it as five layers:

1. leaf CLI command
2. scene scanner and candidate filter
3. per-scene output contract
4. root-level archive or summary
5. delivery bundle or index page

In the current workspace, the repo-level helper scripts already follow this split:

- observation-quality compare flow:
  - `batch_obs_quality_compare.py`
  - `aggregate_obs_quality_reports.py`
  - `package_obs_quality_bundle.py`
- SSR-style flow:
  - `batch_run_ssr_csm_compare.py`
  - `build_ssr_root_index.py`
  - `build_ssr_grand_summary.py`
  - `archive_ssr_reports.py`

The important skill behavior is to explain both levels:

- the real leaf command the CLI executes
- the script-level orchestration that makes it usable at folder scale

## Leaf Commands That Batch Well

The current CLI families that fit this pattern are:

- `AnalysisHub-cli qc obscheck <file> [options]`
- `AnalysisHub-cli qc diff-epoch <file> [options]`
- `AnalysisHub-cli qc triple-epoch <file> [options]`
- `AnalysisHub-cli qc residual <base-file> <rover-file> [options]`
- `AnalysisHub-cli qc short-residual <base-file> <rover-file> [options]`
- `AnalysisHub-cli qc merge-reports ...`
- `AnalysisHub-cli ctclib auto <rover_or_raw_file> [options]`
- `AnalysisHub-cli report auto-combined [options]`
- `AnalysisHub-cli iono <rover_file> [options]`
- `AnalysisHub-cli ssr <log_file> [options]`
- `AnalysisHub-cli report health <qc_html> <datalist> [options]`
- `AnalysisHub-cli report rtk <qc_html> <datalist> [options]`
- `AnalysisHub-cli report obs-compare <datalist...> [options]`

Batching should not hide these leaf commands.

When the skill proposes a batch workflow, it should still name the underlying CLI entrypoints explicitly.

## Common Batch Responsibilities

No matter which leaf command is used, the script layer usually owns these jobs:

- accept a root folder instead of one file
- scan recursively or non-recursively
- skip generated directories such as report folders, archive folders, and `Sourcefile_*`
- filter candidate files by suffix, regex, size, or naming rule
- normalize filenames first when the scene naming is inconsistent
- decide whether to reuse existing outputs or force a rerun
- place per-scene outputs into stable subdirectories
- collect per-scene artifacts into a root-level archive
- generate a root HTML or CSV summary for quick review
- optionally package the archive into a standalone deliverable

This is the main difference between a usable batch workflow and a raw CLI surface.

## Recommended Batch Shape

When the user asks for a new batch flow, prefer this sequence:

1. define the batch unit
2. define the candidate rule
3. define the leaf CLI command
4. define the rerun rule
5. define the per-scene output contract
6. define the root-level archive or summary
7. define the delivery bundle if the results must be shared

Typical batch units:

- one raw log file
- one rover/base pair
- one scene folder
- one processed report folder
- one country root

Typical output levels:

- scene-local outputs beside the raw data
- root-level archive for centralized browsing
- final bundle or index for sharing

## Observation-Quality Compare Pattern

The current workspace has the clearest example here.

### Stage 1: Per-log QC

Use `qc obscheck` as the leaf step.

Typical responsibilities:

- scan `.log` files under a root
- skip generated report folders
- keep only the intended participant files
- reuse existing `_QC.html` and `_DataList.log` unless the user wants rerun
- allow a `force` mode for regeneration

Important current details from the existing script practice:

- `--obsqcmp-mp` is part of the current compare-oriented QC path
- stale compare outputs such as `summary.csv`, `dimensions.csv`, and `observation_quality_compare_report.html` may need to be removed before rerun

### Stage 2: Per-scene compare report

Use `report obs-compare` as the leaf compare step.

The script layer should:

- gather at least two `DataList.log` files per scene
- write the compare outputs into a stable scene-local folder such as `obs_quality_compare`
- keep the compare report close to the source scene for easier inspection

### Stage 3: Root archive

After scene-local compare reports exist, aggregate them into one centralized archive.

The current script pattern copies:

- report HTML
- `summary.csv`
- `dimensions.csv`

Then it generates root-level summary artifacts such as:

- scene overview CSV
- dimension summary CSV
- one region-level summary HTML

This stage is not a native CLI command.

It is script-level orchestration above `report obs-compare`.

### Stage 4: Shareable bundle

If results must be delivered to others, add one more packaging step:

- copy country archives into one bundle root
- rebuild the cross-country summary
- write one `index.html` entry page
- preserve relative links so the bundle can be opened offline

## One-Click Auto Process Pattern

Use `ctclib auto` when the user wants the full one-click chain per scene.

Typical fit:

- one raw log file in single-file mode
- one rover/base pair in RINEX mode
- one fixed reference coordinate per scene

The script layer should:

- normalize how rover/base files and coordinates are resolved
- decide whether to reuse an existing one-click output directory
- keep per-scene outputs stable so the generated report paths remain predictable
- pass `--obsqcmp-mp` when the GUI-equivalent ObsQc MP path is desired

Per-scene outputs normally include:

- `_QC.html`
- `*_DataList.log`
- `.MP` / `.MPresult`
- `.arlog`
- `.pos`
- `*_auto_process_report.html`

## Report Rebuild Pattern

Use `report auto-combined` when the scene has already finished QC / CTCLib processing and only the report must be rebuilt.

Typical reasons:

- the combined report template changed
- titles, thresholds, or explanation text changed
- the fixed-report detail charts need to be regenerated
- the user wants a faster rerun that avoids recomputing QC and CTCLib outputs

The script layer should:

- detect the existing rover `DataList.log`
- detect whether a base `DataList.log` also exists
- resolve sibling `_QC.html`, `.MP`, `.MPresult`, `.arlog`, and `.pos` files
- rebuild only when the artifact set is complete enough for the requested report
- keep the regenerated report in a stable path

This is a good batch leaf command when the expensive analysis already ran and only the reporting layer is still moving.

## Direct-Merge Pattern

If the user only wants to merge many QC HTML reports into one Excel workbook, do not over-design it.

Prefer the native CLI directly:

```powershell
AnalysisHub-cli.exe qc merge-reports --dir <dir> --recurse -o <merged.xlsx>
```

Use a heavier archive workflow only when the user also wants:

- scene ranking
- dimension summaries
- centralized HTML browsing
- bundle delivery

## SSR-Style Pattern

The same orchestration idea also appears in the current SSR scripts:

- run one leaf analysis per scene
- keep scene-local HTML and plots
- build a root index
- optionally build a grand summary page
- archive the final deliverables into one root folder

Important distinction:

- in the current workspace, some SSR helper pages are driven by `SSRAnalysis.exe --batch ...` style tooling rather than the current `AnalysisHub-cli ssr` entrypoint

Be explicit about that distinction.
Do not describe those helper scripts as native `AnalysisHub-cli` subcommands if they are not.

## Skill Response Template For Batch Questions

When the user asks how to batch a CLI workflow, answer in this structure:

- `Batch Goal`
- `Batch Unit`
- `Leaf CLI Command`
- `Scan Rule`
- `Resume Or Force Rule`
- `Scene Output Layout`
- `Root Summary Or Archive`
- `Delivery Or Packaging`
- `Current Gaps Or Non-CLI Parts`

This keeps the answer practical without pretending that everything is already one built-in command.

## Output Discipline

- Separate `CLI-supported leaf commands` from `script-level orchestration`.
- Name the exact generated folders when they are already established by practice.
- Say whether the archive step is current practice, not a native CLI feature.
- Prefer existing helper scripts when they already match the request.
- If the user only needs a small batch merge, recommend the smallest workable flow first.
