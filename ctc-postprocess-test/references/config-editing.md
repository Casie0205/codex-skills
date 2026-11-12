# CTCLib 后处理配置管理

> 状态：可用 | 更新日期：2026-11-05 | 入口：`ctc-postprocess-test`

## 目录

- [1. 配置定位](#1-配置定位)
- [2. 路径规则](#2-路径规则)
- [3. 配置副本](#3-配置副本)
  - [3.1 批量测试子目录](#31-批量测试子目录)
- [4. 输出目录](#4-输出目录)
- [5. 注释规范](#5-注释规范)
  - [5.1 GNSS 中断时间](#51-gnss-中断时间)
- [6. 参数修改示例](#6-参数修改示例)
- [7. 新增参数](#7-新增参数)
- [8. 禁止行为](#8-禁止行为)

## 1. 配置定位

优先使用运行数据目录中的 `hcnav_forpost.ctccfg`：

```text
<data-directory>\hcnav_forpost.ctccfg
```

该文件包含可运行的 `[ctclib]` 配置，以及带注释的完整参数参考。修改前必须确认：

- 当前实际生效的参数没有以 `#` 注释；
- 参数位于正确的 section；
- 参数名称与当前版本完全一致；
- 输入文件存在；
- 输出模式和输出路径明确。

## 2. 路径规则

以下两项必须使用绝对路径：

- `file_input_obs_rover`
- `dir_output`

错误示例：

```ini
file_input_obs_rover = ../data/rover.bin
dir_output = ./ctclib_post_solution
```

正确示例：

```ini
file_input_obs_rover = D:/Dataset/<dataset>/<rover-observation-file>
dir_output = D:/Dataset/<dataset>/ctclib_post_solution_gimode0_5xnoise
```

在 Windows 配置中优先使用正斜杠 `/`，避免反斜杠转义歧义。

运行前检查 `file_input_obs_rover` 指向的文件存在且大小非零。

## 3. 配置副本

需要改参数时：

1. 单次测试在数据目录下创建或检查 `forpost_list` 子目录；
2. 复制原始配置到该目录；
3. 使用能表达参数变化的文件名；
4. 修改副本，不修改原配置；
5. 记录原文件名、新文件名和改动项。

推荐命名：

```text
hcnav_forpost_gimode0_loosely.ctccfg
hcnav_forpost_gimode1_tightly.ctccfg
hcnav_forpost_arw10x.ctccfg
hcnav_forpost_vio_enabled.ctccfg
```

文件名不使用空格、点号或含糊缩写。

### 3.1 批量测试子目录

一组批量测试包含多份配置时，在 `forpost_list` 下建立该批次的子目录，并将该组
全部测试配置复制到子目录中：

```text
<data-directory>\forpost_list\<batch-name>\
|-- hcnav_forpost_gimode0_loosely.ctccfg
`-- hcnav_forpost_gimode1_tightly.ctccfg
```

批次目录名使用简短英文、数字和连字符，例如 `gio-compare` 或 `arw-10x`。不同批次
分别建立子目录，不把多组测试配置混放在 `forpost_list` 根目录。

每个配置仍使用独立的绝对 `dir_output`。批次目录只用于集中管理该组配置，不改变
输出目录规则。

## 4. 输出目录

每个参数对照测试使用独立输出目录，名称应反映配置：

```text
ctclib_post_solution_gimode0_loosely
ctclib_post_solution_gimode1_tightly
ctclib_post_solution_arw10x
ctclib_post_solution_vio_enabled
```

避免在目录名中使用 `0.5x` 之类的点号，可使用 `half`。

### 4.1 selfoutput

如果当前配置中存在：

```ini
selfoutput = 1
```

其含义是生成按时间命名的输出目录。若需要严格使用 `dir_output`，检查并设置：

```ini
selfoutput = 0
dir_output = D:/Dataset/<dataset>/ctclib_post_solution_<case>
```

修改后必须在运行结果中确认实际输出目录。

## 5. 注释规范

不要出现只有中文注释、没有参数的独立行：

```ini
# 错误
# 输出路径配置
dir_output = D:/Dataset/<dataset>/ctclib_post_solution
```

中文注释只能放在参数行尾：

```ini
# 正确
dir_output = D:/Dataset/<dataset>/ctclib_post_solution # 输出路径配置
```

如果必须写独立说明，使用英文注释。

### 5.1 GNSS 中断时间

`gnss_interrupt_start_time` 和 `gnss_interrupt_end_time` 的值只填写周内秒，不填写
GPS 周号，也不填写“周号 + 周内秒”的组合时间。

```ini
gnss_interrupt_start_time = <周内秒>
gnss_interrupt_end_time = <周内秒>
```

修改时保留当前配置中的数值格式，只替换等号后的周内秒。

## 6. 参数修改示例

### 6.1 松耦合

先确认当前配置里的紧耦合值：

```ini
gimode = 1 # [enum] 0:loosely, 1:tightly
```

改为：

```ini
gimode = 0 # 松耦合
```

### 6.2 IMU 噪声放大

参数名必须按当前配置核对。不同配置版本可能使用 `gyro_arw` 或 `gyo_arw`。
当前示例配置使用 `gyo_arw`。不要凭截图猜参数名。

确认原值后按用户要求修改，例如放大 10 倍：

```ini
gyo_arw = 15.0, 15.0, 15.0 # ARW 放大 10 倍
```

如果原值是 `0.15, 0.15, 0.15`，10 倍后才是 `1.5, 1.5, 1.5`。修改前必须读取
实际原值，不得套用其他配置的数值。

### 6.3 启用 VIO

先确认当前配置中存在 `method_vio`，且 section 正确。若存在并需要启用：

```ini
method_vio = 1 # 启用 VIO
```

如果当前配置没有该参数，按第 7 节要求查完整配置，不得直接插入猜测参数。

## 7. 新增参数

新增参数时：

1. 查阅运行输出目录中的完整版 `ctclib.ctccfg`；
2. 确认参数名称、section、值类型和格式；
3. 将参数放入正确 section；
4. 不覆盖已有同名参数；
5. 修改后重新读取配置检查语法；
6. 记录参数来源路径。

示例：如果完整配置把 `gnss_interrupt` 放在 `[ctclib]`，就放在同一 section，不得
直接放到 `[ctclib_gnss]`。

## 8. 禁止行为

- 直接修改原始配置；
- 使用相对输入或输出路径；
- 不读取原值就修改参数；
- 猜测参数名或 section；
- 复制多份配置却不命名变化内容；
- 把中文说明单独写成无参数注释行；
- 会修改源码却要求 AI 直接编译；
- 未确认输入文件存在就运行。
