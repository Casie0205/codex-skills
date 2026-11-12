# Result Contract

状态：active | 更新日期：2026-11-12

## 目录

- [1. 输出位置](#1-输出位置)
- [2. 必需文件](#2-必需文件)
- [3. 内容格式](#3-内容格式)
  - [3.1 截图友好报告](#31-截图友好报告)
  - [3.2 服务器构建矩阵](#32-服务器构建矩阵)
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
| `DONE` + `change_set: code` | `result.md`、`changed-files.txt`、`verification.log`、`review.md`、`cloud-code.patch`、`development-result.json`、`development-result.html` | 必须有提交和可应用补丁 |
| `DONE` + `change_set: none` | `result.md`、`changed-files.txt`（`NONE`）、`verification.log`、`development-result.json`、`development-result.html` | 不要求提交或补丁 |
| `PARTIAL` | 可写时生成 `result.md`、`changed-files.txt`、`verification.log`、`development-result.json`、`development-result.html`；有代码提交时还必须生成 `review.md`；若报告渲染本身失败，允许缺少失败产物，但必须在 `result.md` 和 `NOT VERIFIED` 记录命令与错误；不可写时只做最终回复 | 有代码提交时必须生成补丁 |
| `BLOCKED` | 可写时生成 `result.md`；若存在代码修改，另生成 `review.md`；不可写时只做最终回复 | 不要求补丁 |

任何状态都不得创建空文件或伪造内容。无修改时 `changed-files.txt` 写一行 `NONE`。
若输出 `verification.log` 但未执行验证，则写 `NOT RUN: <reason>`；`BLOCKED` 且输出目录
可写但没有生成日志时，必须在 `result.md` 写明未运行原因。输出目录不可写时只在最终
回复中说明。

只要存在未提交的代码修改，状态必须是 `BLOCKED`，不得使用 `PARTIAL`。`PARTIAL` 中的
代码修改必须已经提交。

可选文件：

```text
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
- build_matrix:
  - solution:
    project:
    configuration:
    platform:
    exit_code:
    output:
- not_verified:

## 风险与后续

- risks:
- unresolved:
- next_action:

## 文档差异

- DOC-DISCREPANCY:
  - status: confirmed | corrected | open
  - local_document:
  - local_claim:
  - source_evidence:
  - observed_behavior:
  - suggested_correction:
```

`changed-files.txt` 每行一个仓库相对路径，或仅写 `NONE`。`verification.log` 保存原始
命令、退出码和关键输出，不手工改成成功状态。`cloud-code.patch` 必须能从任务基线提交
应用。没有文档差异时，`result.md` 写 `DOC-DISCREPANCY: none`。

### 3.1 截图友好报告

完成上述结果文件后，必须使用 `cloud-dev-result-report` 技能生成：

```text
development-result.json
development-result.html
```

报告以 `result.md`、`changed-files.txt`、`verification.log`、存在代码修改时的
`cloud-code.patch`、可用的 `review.md`、实际 Git 提交和测试输出为证据。HTML 必须
自包含、无外部资源依赖、状态与 `result.md` 一致，并适合用户直接浏览和截图。报告字段
和渲染命令见
`../../cloud-dev-result-report/SKILL.md` 与
`../../cloud-dev-result-report/references/report-schema.md`。

`DONE` 且输出目录可写时，缺少任一报告文件不得标记 `DONE`。`PARTIAL` 只有在报告渲染
本身失败时才能缺少对应报告产物，并必须写明缺失原因。

### 3.2 服务器构建矩阵

涉及共享来源、新增源文件或项目成员关系时，`result.md` 和
`development-result.json` 必须记录完整构建矩阵：

- 服务器实际 solution 和目标 project；
- 其他受影响的 production targets；
- 测试 target；
- 每项的 configuration、platform、exit code 和输出文件。

同时保存 `check_project_source_coverage.py` 的退出码和缺少实现文件的项目列表。
只记录一个 app target 的 build 不能证明 solution-level parity。

## 4. 补丁生成

`change_set: code` 的 `DONE`，或存在代码提交的 `PARTIAL`，使用完整提交范围生成补丁：

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
- [ ] 有代码修改时 `review.md` 记录实际审查方式、范围、发现和残余风险；
- [ ] `DONE` + `change_set: code` 的 `cloud-code.patch` 覆盖全部本任务提交且非空；
- [ ] `DONE` + `change_set: none` 的 `changed-files.txt` 为 `NONE` 且不伪造补丁；
- [ ] `DONE` 已生成非空 `development-result.json` 和 `development-result.html`；
  可写 `PARTIAL` 已生成报告，或已记录报告渲染失败原因和缺失产物；
- [ ] 报告状态与 `result.md` 一致，`DONE` 的验收和验证项全部为 `PASS + exit 0`；
- [ ] HTML 自包含，无外部 CSS、JavaScript、字体、图片或网络依赖；
- [ ] `server_build_targets` 中的每个目标都已按指定 configuration/platform 重建，且
  exit code 为 `0`；
- [ ] 共享来源覆盖检查通过，所有 consumer `.vcxproj` 都包含 required source；
- [ ] 每次任务都检查项目上下文，并记录 `DOC-DISCREPANCY` 或明确写 `none`；
- [ ] 非 `none` 的 `DOC-DISCREPANCY` 包含 `confirmed`、`corrected` 或 `open` 状态；
- [ ] 输出路径不在本地只读挂载内；
- [ ] 未包含密钥、凭据、缓存和无关文件；
- [ ] 最终回复列出提交范围、验证结果和残余风险。
