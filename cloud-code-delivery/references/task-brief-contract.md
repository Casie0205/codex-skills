# Cloud Code Task Brief Contract


状态：active | 更新日期：2026-11-12

## 目录

- [1. 用途](#1-用途)
- [2. 必填章节](#2-必填章节)
- [3. 字段规则](#3-字段规则)
- [4. 完整示例](#4-完整示例)
- [5. 校验与停止规则](#5-校验与停止规则)

## 1. 用途

任务单是本地电脑向离线云电脑传递开发意图的唯一契约。它必须让一个能力有限、无法
联网、无法访问本地对话历史的模型，在不猜测的情况下判断：做什么、改哪里、如何验证、
何时停止、结果放在哪里。

任务单只描述一个任务。两个独立目标应拆成两份任务单。

## 2. 必填章节

任务单必须包含一个 H1 标题和以下 8 个编号 `##` 章节，标题文字保持稳定：

```text
1. 任务标识
2. 仓库与环境
3. 目标
4. 范围
5. 上下文
6. 验收
7. 验证
8. 回传
```

缺少任一章、章节为空、关键路径仍含 `{{...}}` 占位符时，云电脑必须停止。

## 3. 字段规则

| 字段 | 要求 |
| --- | --- |
| `task_id` | 唯一、稳定，仅使用字母、数字、下划线和连字符 |
| `local_input_root` | 本地只读挂载根目录，必须明确标记禁止写入 |
| `local_drive_mapping` | 固定写为 `C: -> O:, D: -> P:`，本地上下文路径使用云电脑映射盘 |
| `repo_path` | 云电脑上的代码仓库绝对路径 |
| `branch` | 预期分支；不匹配时停止 |
| `build_root` | 云电脑上可写的构建输出目录；位于仓库内时必须被 Git 忽略，否则必须使用外部独立目录 |
| `project` | 云电脑项目标识，例如 `ctclib` |
| `project_context_paths` | 云电脑可读取的本地项目上下文文档绝对路径 |
| `target` | 用户可观察的结果，不写实现方案 |
| `non_goals` | 明确排除项，防止范围扩张 |
| `allowed_paths` | 允许修改的文件或目录 |
| `forbidden_paths` | 禁止修改的文件或目录 |
| `acceptance` | 可逐项判断真假的验收条件 |
| `verify_commands` | 可复制执行的完整命令 |
| `server_build_targets` | solution/project, configuration, and platform metadata. For `windows-cpp-build` MCP tasks, `platform` is always `x86`; every listed target must be rebuilt before completion. |
| `output_path` | 云电脑内结果目录，不得位于本地只读挂载 |
| `network` | 固定为 `forbidden` |
| `doc_authority` | 固定为 `cloud-code-first` |
| `commit_policy` | 提交信息前缀和允许暂存的路径 |
| `screenshot_report_skill` | 固定为 `cloud-dev-result-report` |

路径应使用目标操作系统的格式。Windows 路径在 Markdown 代码块中保留反斜杠。
`server_build_targets.solution` 可以是 `.sln` 或 `.vcxproj` 绝对路径；`project` 写实际
构建目标名。

## 4. 完整示例

[task-brief-example.md](task-brief-example.md) 是一个无占位符、可按检查清单逐项核对的
完整任务实例。复制本地模板后，应逐字段替换并保持章节顺序不变。

示例用于说明字段粒度，不代表真实项目路径、分支或构建命令。

## 5. 校验与停止规则

逐项确认：

- [ ] 8 个必需编号 `##` 章节全部存在；
- [ ] 每个章节都有实际内容；
- [ ] `task_id`、`local_input_root`、`repo_path`、`branch`、`output_path`、
  `build_root`、`network`、`project`、`project_context_paths`、`doc_authority` 和
  `commit_policy` 已填写；
- [ ] `local_drive_mapping` 和 `screenshot_report_skill` 已填写；
- [ ] `allowed_paths`、`forbidden_paths`、`non_goals`、验收条件和验证命令均已填写；
- [ ] `server_build_targets` 已填写，且 `verify_commands` 包含对应目标的完整重建命令；
- [ ] `network` 的值严格为 `forbidden`；
- [ ] 全文没有 `{{...}}` 占位符；
- [ ] 允许修改路径没有覆盖整个磁盘或整个仓库；
- [ ] 输出目录不在本地只读挂载中；
- [ ] 每条验证命令可独立执行；
- [ ] 验收条件可逐项判断真假。

结构完整不代表路径、版本或验收标准正确。模型还必须核对仓库当前分支、任务文件是否
存在、未提交修改是否与目标重叠。任何事实冲突均优先于任务单中的预期值，并以
`BLOCKED` 结束。

涉及新增源文件、共享来源或 `.vcxproj` 修改时，任务单还应注明消费者项目和实现文件的
覆盖检查命令。不得只列一个便于本地运行的 app target。
