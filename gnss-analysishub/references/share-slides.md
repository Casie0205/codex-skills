# 基于 AnalysisHub 与 AnalysisHub-CLI 的 GNSS 原始数据分析 Skill

副标题：把会用工具的个人经验，沉淀成所有人都能调用的分析能力

---

## 第 1 页：今天想解决什么问题

- GNSS 原始数据分析已经有成熟工具，但使用门槛仍然偏高
- GUI 适合人工探索，不适合标准化复用
- CLI 适合批处理，但命令和输入文件关系不够直观
- 结果文件很多，`QC.html`、`DF/TF.html`、`DataList.log`、`.DF/.TF` 容易混
- 结论解释高度依赖“熟手经验”

本次分享目标：

- 用现有 `AnalysisHub` 和 `AnalysisHub-cli` 做一个可复用 Skill
- 让 AI 负责识别场景、组织流程、解释结果

---

## 第 2 页：核心思路

- 不重做算法
- 不替代 AnalysisHub
- 不让大模型自己“算 GNSS”

而是做一层 AI Skill：

- 识别用户意图
- 识别目录中的分析产物
- 路由到正确的 GUI 或 CLI 能力
- 生成面向人类的结论和建议

一句话概括：

`算法没有变，变的是入口。`

---

## 第 3 页：现有工具能力基础

当前 `AnalysisHub-cli` 已支持：

- `qc obscheck`
- `qc diff-epoch`
- `qc triple-epoch`
- `qc residual`
- `qc short-residual`
- `qc merge-reports`
- `report health`
- `report rtk`
- `plot`

当前 GUI 还有一个重要优势：

- `体检报表` 可以跟随当前 `QC / DF / TF` 模式切换

---

## 第 4 页：为什么要做 Skill，而不是只讲 CLI

只给 CLI 文档，问题还是在：

- 用户不知道该用哪个子命令
- 用户不知道一个目录里哪些文件能组成完整流程
- 用户不清楚 GUI 和 CLI 的边界
- 用户即使跑完，也未必知道该怎么看结果

Skill 的价值是把这些经验显式化：

- 文件模式识别
- 工具路由
- 命令编排
- 结果解释

---

## 第 5 页：Skill 设计结构

Skill 目前拆成四部分：

- `SKILL.md`
  触发条件、路由规则、输出格式
- `file-patterns.md`
  文件识别规则
- `cli-capabilities.md`
  当前 CLI 的真实能力边界
- `analysis-playbook.md`
  分析和解释的标准输出方式

另外还有两个辅助能力：

- 演示提词
- 目录产物识别脚本
- 交互式反问流程
- GUI 拉起与人工接力入口

---

## 第 6 页：我希望 Skill 最终达到的体验

用户只给一句话：

`先分析下这个数据`

Skill 应该做到：

- 先识别这个路径里有什么产物
- 反问真正缺失的信息，例如：
  - 解码类型
  - 希望走 QC、DF 还是 TF
  - 只要快速判断，还是要完整体检报表
- 处理完以后默认给出：
  - 体检报表路径
  - AI 总结
  - 是否继续看异常图
- 用户如果要继续看图，就直接拉起 AnalysisHub GUI

这才更像一个分析助手，而不是命令说明书

---

## 第 7 页：Skill 的工作流程

标准流程分为 5 步：

1. 识别目录中的 GNSS 分析产物
2. 判断用户是要做 QC、DF/TF、体检报表、绘图还是批量汇总
3. 决定走 GUI 还是 CLI
4. 调用 `AnalysisHub` / `AnalysisHub-cli`
5. 输出结论、异常项、重点时间窗和下一步建议

这里最关键的是：

- 不是所有流程都强行走 CLI
- 要尊重“当前工具的真实实现”

---

## 第 8 页：GUI 与 CLI 的边界

当前建议的边界是：

CLI 适合：

- 批处理
- 单站质检
- 头less 出图
- QC 健康报表
- 汇总合并

GUI 适合：

- 依赖当前页面状态的分析
- 跟随当前 `QC / DF / TF` 模式的体检报表
- DF/TF 模式下的精度异常联动查看

这点很重要，因为 Skill 不能“假装能力存在”。

---

## 第 9 页：一个真实样例目录

样例目录：

`D:\市场问题\MARKET-322\Sourcefile_9999323_20260420165032`

目录中同时存在：

- `_QC.html`
- `_DF.html`
- `_TF.html`
- `DataList.log`
- `.DF`
- `.TF`

Skill 能识别出三类健康报表路径：

- `cli-qc-health`
- `gui-df-health`
- `gui-tf-health`

---

## 第 10 页：Demo 1，识别目录产物

演示问题：

`先识别这个目录里有哪些 GNSS 分析产物，告诉我能走哪些 AnalysisHub / AnalysisHub-cli 流程。`

期望展示：

- AI 不是直接开跑命令
- AI 先理解目录里有哪些分析入口
- AI 能明确说出哪些走 CLI，哪些走 GUI

这里展示的是 Skill 的“认路能力”。

---

## 第 11 页：Demo 2，生成 QC 体检报表

演示问题：

`基于这个 _QC.html 和 DataList.log，生成数据体检报表，并总结最主要的异常项。`

可以展示的点：

- CLI 能稳定生成体检报表
- 输出有 `health.html`、`health_report.html`、PNG、CSV
- AI 可以把报表压缩成短结论

这里展示的是 Skill 的“流程编排能力”。

---

## 第 12 页：Demo 3，说明 DF / TF 模式差异

演示问题：

`如果我切到 DF 模式再点体检报表，现在工具会走什么逻辑？和 CLI 的 report health 有什么区别？`

这里重点说明：

- GUI 会跟当前模式走
- DF / TF 下会带精度异常卫星频点表
- CLI 当前暴露的是 QC 风格健康报表入口

这里展示的是 Skill 的“边界意识”。

---

## 第 13 页：为什么这件事有业务价值

对研发：

- 流程更标准
- 经验更容易沉淀

对测试和支持：

- 少记命令
- 少猜文件关系
- 更快得到可转述结论

对组织：

- 个人经验变成可安装、可更新、可复用的 Skill

---

## 第 14 页：如何随发版更新

现在已经做成了可发布包：

- 源 Skill 独立维护
- `Release\codex-skills\gnss-analysishub` 负责分发
- `install-gnss-analysishub-skill.cmd` 负责安装和升级
- Skill 自带 `manifest.json` 做版本识别

更新流程：

1. 修改源 Skill
2. 发布到 `Release`
3. 用户执行安装脚本

---

## 第 15 页：今天的结论

- 我们不是在做一个新的 GNSS 算法
- 我们是在做一层 GNSS 分析能力的 AI 入口
- 这层入口基于现有 `AnalysisHub` / `AnalysisHub-cli`
- 价值在于让工具能力更容易被调用、更容易被解释、更容易被复用

最后一句：

`把会用 AnalysisHub 的个人经验，沉淀成所有人都能调用的 Skill。`
