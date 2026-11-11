# Result Contract

状态：active | 更新日期：2026-11-11

## 目录

- [1. 输出位置](#1-输出位置)
- [2. 必需文件](#2-必需文件)
- [3. 内容格式](#3-内容格式)
- [4. 补丁生成](#4-补丁生成)
- [5. 回传检查](#5-回传检查)

## 1. 输出位置

默认目录：

```text
D:\Output\cloud-code-delivery\<task_id>\
```

任务单可指定其他云电脑本地目录，但不得指向 `local_input_root` 或任何只读挂载路径。
目录创建或写入失败时，只能做最终回复并说明 `OUTPUT: unavailable`：

- 本任务代码修改已经全部提交时使用 `PARTIAL`；
- 仍有本任务代码未提交、缺少输入或存在其他不安全状态时使用 `BLOCKED`。

不得声称结果文件已经生成。

## 2. 必需文件

文件要求随状态变化：

| 状态 | 必需文件 | 补丁要求 |
| --- | --- | --- |
| `DONE` | `result.md`、`changed-files.txt`、`verification.log`、`cloud-code.patch` | 必须有提交和可应用补丁 |
| `PARTIAL` | 可写时生成 `result.md`、`changed-files.txt`、`verification.log`；不可写时只做最终回复 | 有代码提交时必须生成补丁 |
| `BLOCKED` | 可写时生成 `result.md`；不可写时只做最终回复 | 不要求补丁 |

任何状态都不得创建空文件或伪造内容。无修改时 `changed-files.txt` 写一行 `NONE`。
若输出 `verification.log` 但未执行验证，则写 `NOT RUN: <reason>`；`BLOCKED` 且输出目录
可写但没有生成日志时，必须在 `result.md` 写明未运行原因。输出目录不可写时只在最终
回复中说明。

只要存在未提交的代码修改，状态必须是 `BLOCKED`，不得使用 `PARTIAL`。`PARTIAL` 中的
代码修改必须已经提交。

可选文件：

```text
review.md
test-details.log
```

不得把构建中间目录、缓存、依赖包或大型二进制文件复制进结果目录。

## 3. 内容格式

`result.md` 必须包含：

```markdown
# Cloud Code Result: <task_id>

## 状态

- status: DONE | PARTIAL | BLOCKED
- task_id:
- repository:
- branch:
- change_set: code | none
- base_commit:
- result_commit:
- commit_count:
- finished_at:

## 目标与结果

- requested:
- implemented:

## 修改

- files:
- module_boundaries:
- removed_obsolete_paths:

## 验证

- commands:
  - command:
    exit_code:
    key_output:
- not_verified:

## 风险与后续

- risks:
- unresolved:
- next_action:
```

`changed-files.txt` 每行一个仓库相对路径，或仅写 `NONE`。`verification.log` 保存原始
命令、退出码和关键输出，不手工改成成功状态。`cloud-code.patch` 必须能从任务基线提交
应用。

## 4. 补丁生成

`DONE` 或存在代码提交的 `PARTIAL` 使用完整提交范围生成补丁：

```powershell
git diff --binary --output="<output_path>\cloud-code.patch" <base_commit>..<result_commit>
```

提交失败或仍有本任务代码未提交时，不得生成完成补丁或使用 `DONE`。保留现场并将状态
设为 `BLOCKED`。本任务代码已全部提交但验收或结果包不完整时使用 `PARTIAL`。

生成后检查文件非空：

```powershell
Get-Item "<output_path>\cloud-code.patch" | Select-Object Length
```

补丁为空或 Git 报错时不得声称存在可回传修改。

变更清单也由 Git 直接写出，避免文本编码改变内容：

```powershell
git diff --name-only --output="<output_path>\changed-files.txt" <base_commit>..<result_commit>
```

## 5. 回传检查

- [ ] 结果文件与 `DONE`、`PARTIAL` 或 `BLOCKED` 的状态矩阵一致；
- [ ] 输出目录不可写时只使用最终回复，不冒充已生成结果文件；
- [ ] `result.md` 的状态与验证证据一致；
- [ ] 有修改时 `changed-files.txt` 与实际提交范围一致，无修改时明确写 `NONE`；
- [ ] 执行过命令时 `verification.log` 含实际命令和退出码；
- [ ] `DONE` 的 `cloud-code.patch` 覆盖全部本任务提交且非空；
- [ ] 输出路径不在本地只读挂载内；
- [ ] 未包含密钥、凭据、缓存和无关文件；
- [ ] 最终回复列出提交范围、验证结果和残余风险。
