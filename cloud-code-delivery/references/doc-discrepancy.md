# Document Discrepancy

状态：active | 更新日期：2026-11-11

## 目录

- [1. 用途](#1-用途)
- [2. 优先级](#2-优先级)
- [3. 记录格式](#3-记录格式)
- [4. 处理规则](#4-处理规则)

## 1. 用途

云电脑开发时，本地项目文档可能落后于源码。本文件规定如何把差异反馈给本地知识库，
同时不违反本地只读边界。

## 2. 优先级

1. 云电脑当前源码和实际运行结果；
2. 任务单明确的用户要求；
3. 本地项目上下文文档；
4. 推断和旧笔记。

本地文档冲突不能阻止符合任务目标的源码修改，但必须记录差异。若冲突导致需求本身
无法判断，停止并输出 `BLOCKED`。

## 3. 记录格式

每条差异包含：

```text
DOC-DISCREPANCY
LOCAL-DOC: <path and section>
LOCAL-CLAIM: <what the local document says>
CODE-EVIDENCE:
- file: <repo-relative path>
- symbol: <function/type/macro>
- lines: <line number or stable anchor>
- snippet: <minimal supporting code excerpt or none>
OBSERVED: <what the code actually does>
CORRECTION: <short replacement statement>
STATUS: confirmed | corrected | open
```

没有差异时输出：

```text
DOC-DISCREPANCY: none
```

## 4. 处理规则

- 不写入 `local_input_root`。
- 不修改任务单之外的项目文档。
- 不把未核对内容写成 `confirmed`。
- 多个文档复制同一旧结论时，只记录权威位置一次，并指出其他受影响文档。
- 无法确认的差异标为 `open`，保留给本地后续审查。
