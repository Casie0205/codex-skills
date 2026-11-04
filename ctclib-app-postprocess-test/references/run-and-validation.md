# CTCLib 后处理运行与验证

> 状态：可用 | 更新日期：2026-11-04 | 入口：`ctclib-app-postprocess-test`

## 目录

- [1. 可执行文件](#1-可执行文件)
- [2. 运行前检查](#2-运行前检查)
- [3. 运行命令](#3-运行命令)
- [4. 输出文件](#4-输出文件)
- [5. 测试场景](#5-测试场景)
- [6. 编译边界](#6-编译边界)
- [7. 失败处理](#7-失败处理)
- [8. 完成汇报](#8-完成汇报)

## 1. 可执行文件

按顺序解析：

```text
$env:CTCLIB_APP_EXE
D:\Code\ctclib_test\ctclib_app.exe
D:\Code\ctclib-nav\exe\ctclib_app\Release32\ctclib_app.exe
```

仅当用户明确要求 Debug 时，才使用：

```text
D:\Code\ctclib-nav\exe\ctclib_app\Debug64\ctclib_app.exe
```

当前电脑已验证存在：

```text
D:\Code\ctclib_test\ctclib_app.exe
```

不要静默切换到其他版本。

## 2. 运行前检查

检查：

- 可执行文件存在；
- `.ctccfg` 存在且可读；
- `file_input_obs_rover` 是绝对路径且文件存在；
- `dir_output` 是绝对路径；
- 是否需要将 `selfoutput` 改为 `0`；
- 参数 section 和参数名称正确；
- 输出目录是否需要新建；
- 是否允许覆盖已有结果。

## 3. 运行命令

工作目录切换到配置文件所在的数据目录：

```powershell
$exe = "D:\Code\ctclib_test\ctclib_app.exe"
$config = "D:\Dataset\<dataset>\forpost_list\<config-name>.ctccfg"
$workdir = Split-Path -Parent $config

Push-Location $workdir
try {
    & $exe $config
    $exitCode = $LASTEXITCODE
} finally {
    Pop-Location
}

if ($exitCode -ne 0) {
    throw "ctclib_app failed with exit code $exitCode"
}
```

如果使用截图中的 Release32 版本，将 `$exe` 替换为：

```text
D:\Code\ctclib-nav\exe\ctclib_app\Release32\ctclib_app.exe
```

## 4. 输出文件

检查配置对应的输出目录。常见结果文件：

```text
gnss_rtkplot.txt
ins_fastsol.txt
ahrssol.txt
ins_log.ctclog
```

检查：

- 输出目录存在；
- 至少存在一个关键结果文件；
- 结果文件非空；
- `ins_log.ctclog` 中没有致命错误；
- 运行时间合理；
- 实际输出目录与配置一致。

不同版本可能不生成全部文件。缺失文件必须报告，不能自行宣称成功。

## 5. 测试场景

### 5.1 单次默认测试

- 使用原始配置或用户指定配置；
- 不修改参数；
- 使用默认 Release32 等价版本；
- 运行并检查输出。

### 5.2 参数对照测试

1. 在 `forpost_list` 中建立两个配置副本；
2. 每个副本只改变需要对照的参数；
3. 使用不同绝对输出目录；
4. 依次运行，不并行竞争资源；
5. 检查两组输出都生成；
6. 对比结果时说明参数差异和输出路径。

例如：

```text
hcnav_forpost_gimode0_loosely.ctccfg
hcnav_forpost_gimode1_tightly.ctccfg
```

### 5.3 重复运行

- 使用原配置或已有配置副本；
- 不创建新的参数副本；
- 在用户允许时覆盖原输出；
- 检查覆盖后的文件更新时间。

## 6. 编译边界

如果用户修改了 CTCLib 源码：

- AI 不负责执行编译；
- 提示用户先重新构建对应版本；
- 确认使用新生成的 exe 后再测试；
- 不得用旧 exe 的运行结果冒充新代码结果。

## 7. 失败处理

失败时：

- 保留配置副本；
- 保留实际输出目录和日志；
- 报告退出码和错误原文；
- 报告缺失的输入或输出文件；
- 不自动删除失败结果；
- 不切换到未授权的 Debug 版本；
- 不通过猜测参数绕过启动失败。

## 8. 完成汇报

```text
执行程序：
使用版本：
配置文件：
输入数据：
实际输出目录：
运行时间：
退出码：
生成文件：
缺失文件：
参数改动：
验证结果：
未解决问题：
```

只有实际检查输出目录和关键结果文件后，才能写“运行成功”。
