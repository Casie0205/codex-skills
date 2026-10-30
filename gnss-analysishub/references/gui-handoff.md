# GUI Handoff

Use this reference for interactive report review, plotting, station settings, existing-result recovery, and GUI-only analysis pages.

## Prefer The GUI When

- the user wants to inspect abnormal plots interactively;
- the active `QC / DF / TF` context matters;
- two processed results should be compared visually;
- the user wants PPP-SSR chart review or the combined residual/ionosphere tool;
- an existing `Sourcefile_<stem>` result set should be restored without rerunning QC;
- a current observation's station settings need to be changed.

## Resume Existing QC Results

The expected history directory is adjacent to the original observation file:

```text
Sourcefile_<input completeBaseName>
```

At import time, select this checkbox in station settings:

```text
Load existing QC results and plot options from the adjacent Sourcefile_ folder
```

The GUI then restores matching reports and plot artifacts and does not run QC again. Directory detection alone is not success; a matching recognized artifact must also exist.

RINEX has a deliberate exception:

- matching adjacent history exists: import opens station settings so the user can select history loading;
- no matching history: import remains fast and does not open station settings;
- already imported: right-click the observation in Data Manager, choose `Current Station Settings...`, select history loading, and confirm.

This recovery path can restore `_QC.html`, `_DataList.log`, `.MPresult/.MP`, `.DF/.TF` and their reports, plus other matching plot artifacts. See [file-patterns.md](file-patterns.md) for the exact recognized set.

## Current GUI Entries

- `Analysis -> Residual / Ionosphere...`
- `Analysis -> GNSS Accuracy Tool...`
- `Analysis -> GNSS Accuracy Advanced...` is a retained Pro label path, but the current source-backed build has no verified separate action wiring; do not promise it as a production workflow.
- `Analysis -> PPP-SSR...`
- `Tools -> Survey Points...`
- `Tools -> Data Conversion...`
- `Tools -> ADR Compare...`
- `Tools -> RAWIMUXA...`

Current boundaries:

- `Residual / Ionosphere...` is one combined tool, not two menu entries.
- `PPP-SSR...` opens the integrated SSR analysis dialog.
- `GNSS Accuracy Tool...` is available for GUI use; do not claim unverified CLI parity.
- `Survey Points...` and `ADR Compare...` are still placeholders. `RAWIMUXA...` parses ASCII logs and plots converted IMU values; treat its integrated yaw as relative rather than absolute heading.

## Plot Handoff

For verified controls and file types, read [gui-plotting.md](gui-plotting.md).

- Observation import is not the same as parsing a plot-data file.
- Derived files such as `*_DataList.log`, `.DF`, `.TF`, `.MP`, `.GF`, `.MW`, and `.PsrCompare` drive the verified plotting path.
- For compare plotting from processed results, prefer the Data Manager right-click flow that assigns compare file 1 and file 2.
- Do not promise direct plotting of arbitrary raw observations unless it was verified on the running build.

## Edition Behavior

After a user enters Pro and completes authorization, later launches default to Pro while that authorization remains valid. When it expires, startup falls back to the regular edition. Avoid promising a fixed validity duration unless it is shown by the current authorization policy.

## Launch Boundary

There is no verified bundled launcher script in this skill. Do not claim that the GUI opened a particular file unless it was actually launched and verified. When handing off manually, state which observation or derived artifact the user should select and which exact menu or dock to use.

Typical source-tree release executable locations include:

```text
build_vs2022_qt51212\src\gui\Release\AnalysisHub.exe
```

For the Pro variant, resolve the executable inside that variant's own build output; do not assume the regular and Pro paths are interchangeable.
