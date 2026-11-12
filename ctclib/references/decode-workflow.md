# CTCLib 原始数据解码

## 目录

- [命令契约](#命令契约)
- [主要输出](#主要输出)
- [成功判定](#成功判定)
- [IMU 快速检查](#imu-快速检查)
- [常见提示](#常见提示)

## 命令契约

已验证的命令形式：

```powershell
& "<resolved-ctclib_decode.exe>" -b "<absolute-input-path>"
```

`<resolved-ctclib_decode.exe>` 必须由 skill 的路径解析流程从
`D:\Code\ctclib_exe` 下自动定位，不能写死版本子目录。

- `-b` 表示批次处理。
- 输入路径使用绝对路径。实测相对路径 `.\\file.bin` 会直接失败。
- 不加 `-b` 时，程序提示 `>> input file name:`。
- `--help` 不是帮助参数，会被当成输入文件名。
- 输出目录位于输入文件旁：
  `<input-dir>\<input-stem>_ctclibdec`

包装脚本会先在工作区创建输入硬链接或副本，因此输出仍位于 `D:\Output`。
数据专用输出布局为：

```text
D:\Output\<dataset-root>\
  ctclib\
    README.md
    output-index.json
    decode_<timestamp>\
      source\<input-stem>_ctclibdec\
      _run\
```

`-NoStage` 时，输出目录直接位于原始输入文件旁。

每次解码完成后会自动刷新数据集 `ctclib` 根目录下的 `README.md` 和
`output-index.json`。它们列出当前输出目录、运行状态和清理分类；不要手动编辑。

不要新建 `D:\Output\ctclib` 下的输出目录。`Workspace` 必须显式传入，
并使用数据集专用根目录，例如：

```text
D:\Output\M720_20261109_160537\ctclib\decode_20261109_193000
```

## 主要输出

| 文件 | 含义 |
| --- | --- |
| `ctclibdec_imu.txt` | `IMU,` 记录以及 `INSSETTING`、`INSSTATICCALIB` 记录 |
| `ctclibdec_imu_navplot\imu_*.navplot` | 按时间分段的 NavPlot 格式 IMU 数据 |
| `ctclibdec_vio.prodef` | 首行为 VIO 字段定义，后续为 `VIO,` 数据 |
| `ctclibdec_forpost.ctccfg` | 可直接交给 `ctclib_app.exe` 的后处理配置 |
| `ctclibdec_log.txt` | 解码日志和逐历元状态 |
| `ctclibdec_rtkplot_origin.navplot` | 原始定位轨迹数据 |

空的 RTCM、NovAtel、GGA 文件不一定表示解码失败。应按输入数据类型判断哪些输出应存在。

## 成功判定

1. 检查退出码。
2. 检查 `_ctclibdec` 目录存在。
3. 检查 `ctclibdec_forpost.ctccfg` 长度大于零。
4. 检查至少一个提取数据文件长度大于零；只有非空日志不算解码成功。
5. 输入含 IMU 时，对 `ctclibdec_imu.txt` 统计 `IMU,` 行数和时间范围。
6. 输入含 VIO 时，对 `ctclibdec_vio.prodef` 检查是否存在 `VIO,` 数据行。

不要用单一控制台提示替代以上检查。

复用已有 `_ctclibdec` 目录必须显式传入 `-Force`。包装脚本会比较运行前后的文件，
只有本次新增或修改的配置与数据文件计入成功判定。

## IMU 快速检查

Mova 样例的 `IMU,` 行字段顺序：

```text
IMU,时间,gyro_x,gyro_y,gyro_z,acc_x,acc_y,acc_z,...
```

该样例中加速度模长约等于 1，数据按 `g` 量纲输出。

整段统计的标准差主要反映车辆运动。评估零偏稳定性、随机游走或振动噪声时，应使用静止段或 Allan 方差。

## 常见提示

```text
ERROR! CSM has not been decrypted yet!
```

该提示在 Mova 样例中可重复出现，但 IMU 和 VIO 输出仍有效。它属于内部格式提示，不能单独作为失败依据。
