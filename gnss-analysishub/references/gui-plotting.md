# GUI Plotting

Use this reference when the user asks how to draw plots in the current `AnalysisHub` GUI.

This file is intentionally strict about verified behavior from the current source-backed GUI path.

## Verified GUI Entry Names

- `Data -> Import Rover File...`
- `Data -> Import Base File...`
- `Plot` dock / panel
- `Compare Plot` dock / panel
- `Plot File:`
- `Browse`
- `Parse`
- chart types in the regular plot dock:
  - `Observation Series`
  - `Time Series (LCT/CN0/Doppler/Elev)`
  - `Obs-Slip Timeline`
  - `Sky Plot`
- observation-series toggle:
  - `Carrier`
  - `Pseudorange`

## Important Boundary

- Importing an observation file into the GUI is not the same thing as opening a plot-data file for rendering.
- In the current source-backed GUI path, plotting is driven by plot-data files such as:
  - `*_DataList.log`
  - `.DD`
  - `.DF`
  - `.TF`
  - `.MP`
  - `.GF`
  - `.MW`
  - `.PsrCompare`
- Do not promise that arbitrary raw observation files can be plotted directly unless that running build was explicitly verified.
- If the adjacent `Sourcefile_<input completeBaseName>` already contains matching plot artifacts, use station settings to restore them instead of rerunning QC. RINEX import exposes station settings only when that history folder is detected; an already imported file can use `Current Station Settings...` from its Data Manager context menu.

## Plot-Capable Files In A Processed Output Directory

When the user gives a processed directory, classify files like this:

- `*_DataList.log`
  - main GUI plotting source
  - supports:
    - `Observation Series`
    - `Time Series (LCT/CN0/Doppler/Elev)`
    - `Obs-Slip Timeline`
    - `Sky Plot`
- `.MP`
  - multipath-related plots
- `.GF`
  - GF combination plot
- `.MW`
  - MW combination plot
- `.PsrCompare`
  - pseudorange-compare style plot
- `.DD`
  - zero-baseline residual plot
- `.DF`
  - diff-epoch residual plot
- `.TF`
  - triple-epoch residual plot
- `_QC.html`
  - report only
  - not the main `Plot` parser input

## Regular Plot Workflow

### A. `*_DataList.log`

1. Open `AnalysisHub.exe`.
2. In the `Plot` dock, choose `Browse`.
3. Select `*_DataList.log`.
4. Click `Parse`.
5. Choose one of these chart types:
   - `Observation Series`
   - `Time Series (LCT/CN0/Doppler/Elev)`
   - `Obs-Slip Timeline`
   - `Sky Plot`
6. Choose system or frequency selector.
7. Click `Plot`.

Use this mapping:

- observation-sequence plots by system:
  - choose `Observation Series`
  - select `ALL / GPS / BDS / GLO / GAL / QZS`
  - optionally switch `Carrier / Pseudorange`
- system-frequency time series:
  - choose `Time Series (LCT/CN0/Doppler/Elev)`
  - select `GPS_L1`, `BDS_B1I`, `GAL_E1`, and similar selectors
- slip timeline:
  - choose `Obs-Slip Timeline`
- sky plot:
  - choose `Sky Plot`

Current interaction note:

- for `_DataList.log` observation-sequence plotting, the current build supports clicking a plotted point to inspect `CN0` and elevation

### B. `.MP`

1. Open `AnalysisHub.exe`.
2. In the `Plot` dock, choose `Browse`.
3. Select `.MP`.
4. Click `Parse`.
5. Select the target system or frequency if needed.
6. Click `Plot`.

Expected subplots include:

- pseudorange multipath
- carrier multipath
- CN0

### C. `.GF` / `.MW` / `.PsrCompare`

1. Open `AnalysisHub.exe`.
2. In the `Plot` dock, choose `Browse`.
3. Select `.GF`, `.MW`, or `.PsrCompare`.
4. Click `Parse`.
5. Select system or frequency if needed.
6. Click `Plot`.

Expected meaning:

- `.GF`
  - GF combination
- `.MW`
  - MW combination
- `.PsrCompare`
  - pseudorange-compare style values

### D. `.DD` / `.DF` / `.TF`

1. Open `AnalysisHub.exe`.
2. In the `Plot` dock, choose `Browse`.
3. Select `.DD`, `.DF`, or `.TF`.
4. Click `Parse`.
5. Select a system-frequency entry such as `GPS_L1`.
6. Click `Plot`.

Use this mapping:

- `.DD`
  - zero-baseline residual
- `.DF`
  - diff-epoch residual
- `.TF`
  - triple-epoch residual

## Compare Plot Workflow

Use this when the user wants to overlay the same type of information from multiple files onto the same subplot.

### Supported compare families

The dedicated `Compare Plot` dock currently supports:

- `.DD`
- `.DF`
- `.TF`
- `.GF`
- `.MW`
- `.PsrCompare`
- `.MP`
- `_DataList.log`

### A. Compare residual / GF / MW / MP / PsrCompare files

1. Open `AnalysisHub.exe`.
2. Switch to the `Compare Plot` dock.
3. Choose `Browse`.
4. Select two or more files from the same plot family.
5. Click `Parse`.
6. Use the satellite checkbox area to control which satellites are drawn.
7. Click `Plot`.

Expected behavior:

- the same observable is overlaid on one subplot
- colors distinguish files or frequency series depending on the mode
- this path is intended for quick cross-file anomaly comparison

### B. Compare `_DataList.log`

1. Open `AnalysisHub.exe`.
2. Switch to the `Compare Plot` dock.
3. Choose `Browse`.
4. Select two `_DataList.log` files.
5. Click `Parse`.
6. Choose the compare mode for observation sequence or CN0 comparison.
7. Click `Plot`.

Current verified behavior:

- only the first two selected files are used
- observation-sequence compare shows observations that exist in file 2 but not in file 1 at the same epoch
- common observations are hidden
- frequency colors are used for the plotted observation points
- clicking a point shows `CN0` and elevation
- do not describe other `_DataList.log` compare modes unless they are re-verified

## Preferred Compare Plot Workflow In The Current GUI

When the user is already working from processed data nodes in the main file tree, prefer this path first instead of asking them to manually browse compare files:

1. In `Data Manager`, right-click the first processed result node.
2. Choose `Set As Compare Plot File 1`.
3. Right-click the second processed result node.
4. Choose `Set As Compare Plot File 2`.
5. Wait for the shared compare-mode dialog.
6. Choose one shared mode.
7. Let the GUI switch into `Compare Plot`.

Current verified behavior:

- the GUI derives compare-capable plot files from the processed result nodes
- the dialog shows only modes shared by both selected results
- the current GUI keeps only two compare slots by default
- `_DataList.log` may lead to:
  - `Observation Compare [Carrier]`
  - `Observation Compare [Pseudorange]`
  - `CN0 Compare`
- other families depend on whether both results can derive:
  - `.DD`
  - `.DF`
  - `.TF`
  - `.MP`
  - `.GF`
  - `.MW`
  - `.PsrCompare`

## Fastest Verified Workflows

### 1. Observation series by system

1. Open `AnalysisHub.exe`.
2. In the `Plot` dock, choose `Browse`.
3. Select `*_DataList.log`.
4. Click `Parse`.
5. Set chart type to `Observation Series`.
6. Select `ALL`, `GPS`, `BDS`, `GLO`, `GAL`, or `QZS`.
7. If needed, switch `Carrier` or `Pseudorange`.
8. Click `Plot`.

### 2. Time series by system and frequency

1. Open `AnalysisHub.exe`.
2. In the `Plot` dock, choose `Browse`.
3. Select `*_DataList.log`.
4. Click `Parse`.
5. Set chart type to `Time Series (LCT/CN0/Doppler/Elev)`.
6. Select a frequency entry such as:
   - `GPS_L1`
   - `GPS_L2C`
   - `GPS_L5`
   - `BDS_B1I`
   - `BDS_B2I`
   - `GAL_E1`
7. Click `Plot`.

### 3. Compare two processed outputs

1. Open `AnalysisHub.exe`.
2. In `Data Manager`, right-click one processed result and set it as compare plot file 1.
3. Right-click another processed result and set it as compare plot file 2.
4. In the shared-mode dialog, choose the target compare mode.
5. Let the GUI jump to `Compare Plot`.
6. Adjust satellites or selectors if needed.
7. Click `Plot`.

## What To Say About QC

- If `*_DataList.log` already exists, plotting does not require re-running QC.
- If it is inside the matching adjacent `Sourcefile_<stem>` directory, select `Load existing QC results and plot options from the adjacent Sourcefile_ folder` in station settings to register the existing report and plot files.
- If the user only has a raw observation file and no derived plot-data artifact, the current verified source-backed path is:
  - import the file
  - run the needed processing to produce `*_DataList.log`
  - then plot from `Plot` or `Compare Plot`
- If the user wants a compare overlay, first ensure the needed derived files already exist for both inputs.
