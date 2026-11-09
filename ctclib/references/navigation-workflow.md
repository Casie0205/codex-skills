# CTCLib 导航后处理

## 目录

- [配置契约](#配置契约)
- [包装脚本行为](#包装脚本行为)
- [主要输出](#主要输出)
- [结果分析](#结果分析)
- [常见故障](#常见故障)

## 配置契约

最小顶层配置：

```text
> START_CTCCFG
[ctclib]
gimode = 1
file_input_obs_rover = <absolute-or-config-relative-input>
selfoutput = 0
dir_output = <absolute-output-directory>
realtime_mode = 0
[ctclib_core]
device_name = CGI220pro
[ctclib_ins]
imu_freq = 200
navsol_gnss_freq = 5
> END_CTCCFG
```

`gimode`：

| 值 | 模式 |
| ---: | --- |
| `0` | loosely |
| `1` | tightly |
| `2` | ins-align-tightly |
| `3` | ins |
| `4` | gnss |

`file_input_obs_rover` 可相对配置文件目录解析。包装脚本会把它改成绝对路径。

GNSS 中断配置：

```text
gnss_interrupt_start_time = 200395, 0, 0, 0
gnss_interrupt_end_time = 200405, 0, 0, 0
```

程序回写的完整配置可能把时间显示为 `2.004E+05`。不能只根据该显示判断中断未生效，应检查导航结果中的状态变化。

## 包装脚本行为

`run-solve.ps1`：

1. 解析源配置的 `[ctclib] file_input_obs_rover`。
2. 在运行目录生成 `ctclib.derived.ctccfg`。
3. 默认写入绝对输入路径、`selfoutput=0` 和新的 `dir_output`。
4. 启动前检查本机注册状态；未注册时返回 `license_required`，不启动程序。
5. 对程序设置运行超时，避免注册提示或其他交互无限等待。
6. 保存 `stdout.log`、`stderr.log`、`command.txt` 和 `summary.json`。

源配置保持不变。

使用 `-Force` 复用非空输出目录时，只有本次运行新增或修改的主结果文件才算成功；
旧的 `ins_novatel.ASC` 不会让空跑被误判为成功。

## 主要输出

| 文件 | 含义 |
| --- | --- |
| `ins_novatel.ASC` | INS 位置、速度、姿态、状态和标准差 |
| `gnss_novatel.ASC` | GNSS 导航结果 |
| `ctclib.ctccfg` | 程序实际使用的完整配置 |
| `dr_est.prodef` | DR 估计字段定义 |
| `dr_plot.prodef` | DR 绘图字段定义 |
| `ins_integsol.txt` | 完整性结果；关闭完整性监视时可为空 |

不同构建可能输出 `ins_insplot.txt`。不要把 NovAtel 字段顺序套用到该文件，或反向套用。

## 结果分析

`ins_novatel.ASC` 的主要记录是 `#INSPVAXA`：

- GPS 周和秒位于记录头。
- 解状态和位置位于分号后的正文。
- 常见状态为 `INS_RTKFIXED`、`INS_RTKFLOAT`、`INS_PSRDIFF`、`NONE`。

检查 GNSS 中断时：

1. 统计中断窗口内的记录数与状态分布。
2. 找到最后一个有效解、第一个 `NONE`、最后一个 `NONE` 和恢复后的第一个有效解。
3. 区分中断过程与全程初始未收敛产生的 `NONE`。
4. 只根据文件中的实际时间和状态下结论。

## 常见故障

- 缺少 `Decrypter.dll`：程序无法启动。
- 没有有效注册码：控制台出现 `Please send Serial Number`。
- 输出目录非空：包装脚本默认停止，避免混入旧结果。
- 配置中使用相对输入路径且衍生配置被移到其他目录：包装脚本会先转换为绝对路径。
