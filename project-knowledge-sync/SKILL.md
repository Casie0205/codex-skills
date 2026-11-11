---
name: project-knowledge-sync
description: Maintain a local Markdown knowledge base for codebases that exist only on an external cloud computer. Use when merging user-returned cloud AI reviews, screenshots, architecture notes, pseudocode, source excerpts, or runtime evidence into project framework documents, resolving contradictions, updating knowledge gaps, and preserving evidence status. Do not use to execute code on the cloud computer or to invent facts not present in provided evidence.
---

# Project Knowledge Sync

状态：active | 调用前缀：`proj` | 更新日期：2026-11-11

## 目录

- [1. 目标](#1-目标)
- [2. 证据边界](#2-证据边界)
- [3. 工作流](#3-工作流)
- [4. 合并位置](#4-合并位置)
- [5. 状态与伪代码](#5-状态与伪代码)
- [6. 停止条件](#6-停止条件)
- [7. 验证](#7-验证)
- [8. 参考文件](#8-参考文件)

## 1. 目标

把用户从云电脑带回的审查结果和源码证据，合并为本地可导航、可追溯的项目知识库。
云电脑代码只存在于云电脑；本地只能处理用户提供的文本、截图、运行结果或明确摘要。

本技能不访问云电脑源码，不执行开发任务，也不把未提供的内容补全为事实。

## 2. 证据边界

读取顺序：

1. 项目入口，例如 `D:\DOC\cloud-dev\projects\ctclib\README.md`。
2. 项目权威文档入口，例如 `D:\DOC\ctclib\README.md`。
3. 目标文档及其引用章节。
4. 用户提供的原始云电脑回复、截图、源码片段或审查记录。

证据等级：

| 状态 | 使用条件 |
| --- | --- |
| `confirmed-cloud` | 有云电脑当前源码路径、符号和可核对证据（行号、稳定锚点或最小片段），或有可复现运行结果 |
| `confirmed-local` | 本地截图或既有文档明确显示，但尚未对照云电脑当前源码 |
| `inferred` | 根据接口、调用关系或通用原理推断，但没有直接实现证据 |
| `open` | 缺少必要源码、配置、日志或运行结果 |
| `superseded` | 已被更完整证据替代 |

截图可证明屏幕上可见的函数名、结构字段和调用关系，但不能自动补全未显示的函数体。
审查动作可以使用 `corrected`，但合并后的新结论仍按上述证据等级标记。

## 3. 工作流

1. 记录当前文档结构、目录、链接和证据状态。
2. 把原始云电脑回复拆成独立结论。每条结论只回答一个问题。
3. 按 `references/review-intake.md` 判断状态和证据是否足够。
4. 按 `references/knowledge-base-rules.md` 选择权威文档和章节位置。
5. 把原始记录保存在项目 `reviews` 目录，把综合修正合并到权威文档。
6. 更新项目索引、知识缺口、更新记录和跨文档链接。
7. 保留未解决冲突，不得用概括性文字掩盖。
8. 运行结构化 Markdown 严格审计。

## 4. 合并位置

- 架构和数据流总览合并到项目总览文档。
- 单入口、单阶段或单模块流程合并到对应流程文档。
- 结构体、字段、所有权和不变量合并到数据结构文档。
- 未确认问题合并到知识缺口或文档的待核实章节。
- 原始云电脑回复保存在 `reviews`，不直接充当综合框架正文。

同一事实只能有一个权威位置。其他文档使用链接和简短摘要，不复制长篇说明。

## 5. 状态与伪代码

- 不得把 `inferred` 或截图推断升级为 `confirmed-cloud`。
- 每条 `confirmed-cloud` 结论必须带云电脑仓库相对路径、符号和可核对证据；行号稳定时优先
  保留行号。
- 冲突结论不得同时写成事实。新结论优先时，旧结论标记 `superseded` 并链接新位置。
- 伪代码必须保留真实函数名、结构体名、条件方向和调用顺序。
- 伪代码标记为 `extracted` 或 `inferred`；推断部分必须附证据缺口。
- 不得根据函数名编造参数、返回值、异常分支或数学公式。

## 6. 停止条件

出现以下情况时保持当前文档不变，记录待处理原因：

- 只有口头结论，没有路径、符号或运行证据；
- 源码版本、分支或提交不明确，且结论依赖具体实现；
- 同一符号存在多个候选，无法确认是哪一个；
- 新证据与现有源码证据冲突且无法解释；
- 用户提供的截图缺少关键上下文；
- 结论需要读取本地无法访问的云电脑文件才能成立。

## 7. 验证

使用 `structured-md-docs` 的审计脚本检查：

- 标题、目录和锚点一致；
- 相对链接存在；
- 文档没有重复权威副本；
- 未确认项仍有明确状态；
- 原始记录与综合结论双向可追溯；
- 每个维护文档低于云电脑读取所需的字符上限。

## 8. 参考文件

- [review-intake.md](references/review-intake.md)：审查输入分类、证据提取和合并矩阵。
- [knowledge-base-rules.md](references/knowledge-base-rules.md)：权威位置、伪代码、冲突和索引规则。
