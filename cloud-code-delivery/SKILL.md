---
name: cloud-code-delivery
description: Execute one code-development task on an offline cloud computer that can read a locally mounted task brief but cannot write back to the local computer. Use for implementing features, fixing bugs, refactoring, adding tests, or repairing builds when the task brief defines the repository, scope, acceptance criteria, and verification commands.
---

# Cloud Code Delivery

状态：active | 适用：离线云电脑 | 调用前缀：`clou` | 更新日期：2026-11-11

## 目录

- [1. 目标](#1-目标)
- [2. 读取顺序](#2-读取顺序)
- [3. 环境契约](#3-环境契约)
- [4. 硬性规则](#4-硬性规则)
- [5. 执行流程](#5-执行流程)
- [6. 停止条件](#6-停止条件)
- [7. 交付物](#7-交付物)
- [8. 完成汇报](#8-完成汇报)
- [9. 参考文件](#9-参考文件)

## 1. 目标

在一个云电脑工作区内完成一个边界明确的代码任务，并通过真实构建或测试证据证明
结果。任务输入来自本地电脑的单向只读文档，代码和输出只写入云电脑工作区。

本技能不负责多项任务并行、只读代码审查、联网调研、生产部署、密钥操作或跨机器自动
回传。

## 2. 读取顺序

严格按以下顺序读取：

1. 任务单本身。
2. [task-brief-contract.md](references/task-brief-contract.md)。
3. 任务单中的 `project_context_paths`。
4. 仓库根目录最近的 `AGENTS.md`，不存在时读取 `README.md`。
5. 任务单指定的项目文档、构建说明和测试说明。
6. [execution-gates.md](references/execution-gates.md)。
7. [result-contract.md](references/result-contract.md)。

任务单缺少必需章节、路径不存在或仓库与任务单不一致时，停止修改并报告
`BLOCKED`。不要通过猜测补全任务单。

## 3. 环境契约

- 本地挂载目录只读。任务单中的 `local_input_root` 及其所有子目录禁止写入。
- 所有修改只允许发生在任务单指定的 `repo_path`、`build_root` 和 `output_path` 内。
- 默认输出目录为 `D:\Output\cloud-code-delivery\<task_id>`；任务单可覆盖。
- 默认禁止联网。依赖必须来自仓库、云电脑缓存或任务单列出的本地离线目录。
- 构建、测试、格式化和静态检查必须使用任务单给出的完整命令。命令缺失时停止，不自行
  猜测或改用未授权入口。
- 本地项目上下文是只读输入，不是当前源码的替代品。实际源码、构建和运行结果优先。
- 不读取、复制、打印或提交密钥、令牌、证书、个人凭据和无关用户数据。

## 4. 硬性规则

- 一次只做一个任务。发现第二个独立需求时，记录但不实施。
- 先读代码再改代码。不得只凭函数名、搜索结果或旧文档推断行为。
- 优先复用仓库现有模块、命名、测试和构建方式；不得另起一套并行实现。
- 主入口保持薄层。新行为放入职责单一的模块；主文件只做解析、调度和连接。
- 修改已有功能时，检查旧分支、旧参数和旧路径是否应删除。不得长期保留两套可切换
  实现，除非任务单明确要求兼容。
- 本地文档与源码冲突时，不得静默沿用错误描述。必须在结果中记录
  `DOC-DISCREPANCY`，给出源码证据和建议修正。
- 不得执行 `git reset --hard`、`git clean`、强制推送、批量回滚或删除未知文件。
- 不得使用 `git add -A` 或 `git add .`。只按显式路径暂存本任务修改的文件。
- 开工前记录 `git status --short`、`git diff --cached --name-only` 和
  `git ls-files --others --exclude-standard`。索引必须为空；已有修改或未跟踪文件属于
  用户，不得覆盖或混入本任务提交。
- 禁止编造构建结果、测试结果、文件路径、版本号或完成状态。
- 每次可验证的逻辑修改完成后提交一次 Git 提交。提交前至少完成与之对应的构建、
  测试或静态检查；无法检查时不得标记为 `DONE`。

## 5. 执行流程

### 5.1 输入门禁

检查任务单是否包含任务标识、仓库路径、目标、非目标、允许修改范围、验收标准、
验证命令和输出路径。逐项确认：

- 8 个必需编号 `##` 章节全部存在且非空；
- `task_id`、`local_input_root`、`repo_path`、`branch`、`output_path`、
  `build_root`、`network`、`project`、`project_context_paths`、`doc_authority` 和
  `commit_policy` 已填写；
- `allowed_paths`、`forbidden_paths`、`non_goals`、验收条件和验证命令均已填写；
- 文件中没有 `{{...}}` 占位符；
- `local_input_root` 与所有云电脑可写路径分离；`build_root` 必须在 `repo_path` 内，或是
  任务单明确授权的独立可写构建目录。
- `build_root` 位于 `repo_path` 内时，先运行 `git check-ignore -q -- "<build_root>"`。
  未被 Git 忽略时停止，要求任务单改为仓库外的构建目录或已有忽略目录。

任一项不满足时停止。

### 5.2 仓库定位

记录：

- 当前分支和提交；
- `git status --short`；
- `git diff --cached --name-only`；
- `git ls-files --others --exclude-standard`；
- 入口文件、目标模块、相邻实现和测试；
- 实际构建根、配置文件、生成目录和已有失败基线。
- 项目上下文文档存在且可读；发现与源码冲突时记录，不在本地写回。

索引非空时立即停止。现有未提交修改或未跟踪文件只要与允许修改路径重叠，立即停止并
报告重叠文件。

### 5.3 最小计划

开始编辑前写出不超过 5 步的计划，每步必须包含：

1. 要回答的问题；
2. 要读取或修改的精确路径；
3. 成功判据；
4. 失败时的下一步。

计划中不得出现“优化相关代码”这类无边界动作。

### 5.4 实现

- 文字搜索只用于定位候选；C/C++ 符号、重载、宏、模板和包含关系必须结合语言服务、
  编译数据库或实际编译确认。
- 先修改最小根因，再处理由其直接导致的问题。
- 新功能或独立流程必须拆成独立模块；不得继续扩张最大的现有文件。
- 只修改任务范围内的文件。发现无关缺陷时记录到结果中，不顺便修复。

### 5.5 调试

遇到构建或测试失败时：

1. 完整阅读第一条根因错误；
2. 复现同一命令；
3. 对照最近修改和正确实现；
4. 一次只验证一个假设；
5. 修复后重新运行同一命令。

同类根因连续 3 次尝试仍未解决时停止，报告已尝试的假设和证据。

### 5.6 验证与审查

必须执行任务单中的全部验收命令，并保存完整输出。随后检查：

```powershell
git diff --check
git diff --stat
git diff --name-only
git status --short
git ls-files --others --exclude-standard
```

逐项检查改动是否满足任务单，是否引入旧流程残留、重复入口、无边界参数、缺失测试或
无关格式化。新建文件必须出现在 `git status --short` 或未跟踪文件清单中。审查发现的
问题先修复，再重新验证。

列出本地项目文档与源码的已确认差异；没有差异时明确写 `DOC-DISCREPANCY: none`。

### 5.7 提交与回传

只暂存本任务修改的文件：

```powershell
git add -- <file1> <file2>
git diff --cached --name-only
git diff --cached --check
git commit -m "<type>: <summary>"
git status --short
git ls-files --others --exclude-standard
git show --stat --oneline <result_commit>
```

提交前确认暂存清单只含任务允许路径内的文件。出现任何无关文件时不要提交，输出
`BLOCKED` 并保留现场。提交成功后从 `<base_commit>..<result_commit>` 生成补丁和结果包，
写入 `output_path`。任何本任务新建源码文件或未被忽略的构建产物只要仍出现在未跟踪
清单中，就不得标记 `DONE`；应先补做验证和提交。不得尝试写入本地挂载目录。

## 6. 停止条件

出现任一项时停止，不继续猜测：

- 任务单缺失、占位符未替换或路径不存在；
- 仓库、分支或目标文件与任务单不一致；
- Git 索引非空；
- 已有修改或未跟踪文件与允许修改路径重叠；
- 需要联网、权限提升、密钥或生产环境；
- 需要执行不可恢复的 Git 或文件操作；
- 验收标准无法观测；
- 构建环境缺失且任务单没有替代验证方式；
- 同类根因连续 3 次修复失败；
- 任务实际包含两个以上独立目标。

停止时保留现场，输出 `BLOCKED`，写明已确认事实、缺失输入和最小下一步。

## 7. 交付物

`DONE` 且 `change_set: code` 时生成：

```text
result.md
changed-files.txt
verification.log
cloud-code.patch
```

`DONE` 且 `change_set: none` 时生成：

```text
result.md
changed-files.txt
verification.log
```

后者的 `changed-files.txt` 写 `NONE`，不要求提交或补丁。

文件格式和字段见 [result-contract.md](references/result-contract.md)。输出目录不可写
时不得声称回传完成。若代码修改已经提交，但结果文件无法写入，使用 `PARTIAL`；若仍
存在未提交代码、缺失输入或其他不安全状态，使用 `BLOCKED`。两种情况都只做最终回复，
并在其中写出完整原因、已确认事实和最小下一步。

## 8. 完成汇报

最终回复使用以下字段，不添加空泛评价：

```text
STATUS: DONE | PARTIAL | BLOCKED
TASK: <task_id>
COMMIT: <base..result or none>
FILES: <changed paths>
VERIFIED: <command and observed result>
NOT VERIFIED: <items or none>
RISK: <remaining risk or none>
NEXT: <one concrete action or none>
OUTPUT: <cloud output path>
DOC-DISCREPANCY: none | <STATUS: confirmed | corrected | open; document; claim; source evidence; correction>
```

状态判定：

- `DONE`：全部验收通过，没有本任务未跟踪文件。代码有修改时必须已提交并生成补丁；
  确认无需修改时 `change_set` 为 `none`，不要求提交或补丁。
- `PARTIAL`：本任务代码修改已全部提交，但验收未全部通过，或结果包无法写入。
- `BLOCKED`：缺少输入、环境或安全检查失败，或仍有本任务代码未提交。已有部分提交
  不改变该判定。

其他状态的文件要求见 [result-contract.md](references/result-contract.md)。

## 9. 参考文件

- [task-brief-contract.md](references/task-brief-contract.md)：任务单字段、示例和缺失判定。
- [task-brief-example.md](references/task-brief-example.md)：只用于理解字段粒度的示例，不得执行其中的示例路径或命令。
- [execution-gates.md](references/execution-gates.md)：阶段门禁、Git 安全、模块边界和低能力模型约束。
- [result-contract.md](references/result-contract.md)：输出文件、补丁格式和回传检查。
- [doc-discrepancy.md](references/doc-discrepancy.md)：本地文档与云电脑源码冲突时的记录格式。
