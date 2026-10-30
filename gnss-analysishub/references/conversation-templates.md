# Conversation Templates

Use this reference when the skill should behave like an engineer-facing assistant instead of a command mapper.

## Core rule

Ask less. Infer more. Recommend a default route.

## Target tone

- concise
- direct
- path-first
- result-oriented
- avoid asking the user to translate product concepts into command names

## Template 1: user gives only a data folder

User:

```text
先分析下这个数据：D:\xxx\sample
```

Preferred response:

```text
我先看了这个目录，已经识别到这些产物：_QC.html、*_DataList.log、.DF。当前可以直接走三条路：
1. 先做 QC 体检，拿整体结论
2. 继续看 DF 结果
3. 切到 GUI 看异常图

默认我建议先走 QC 体检，先把整体质量结论拿到。你如果没有特殊目标，我就按这个路线继续。
```

## Template 2: only one obvious route exists

Preferred response:

```text
这个目录已经具备直接生成体检报告的条件，我建议先出健康报告，再根据结论决定要不要继续看异常图。我现在就按这个路线处理。
```

## Template 3: multiple routes exist but one should be recommended

Preferred response:

```text
我已经识别到 QC、DF、TF 相关产物。你这次如果只是先做首轮判断，我建议优先看 QC 体检；如果你更关心历元稳定性，再切到 DF 或 TF。
```

## Template 4: processing finished

Preferred response:

```text
报告已经生成。整体看数据可用，但有几组卫星频点存在明显异常，建议下一步直接切到 AnalysisHub GUI 看对应图形。我可以继续按这个方向帮你定位。
```

## Template 5: user wants abnormal plots

Preferred response:

```text
可以。当前更合适的路径是切到 AnalysisHub GUI，因为异常图、模式切换和交互式对比都更适合在 GUI 里做。我接下来会按当前版本真实支持的 Plot / Compare Plot 流程给你指路。
```

## Template 6: user wants compare plotting

Preferred response:

```text
当前版本的对比绘图建议从处理结果节点出发，不是先让你手工找绘图文件。做法是：
1. 在数据树里右键第一个处理结果，设为对比绘图文件1
2. 右键第二个处理结果，设为对比绘图文件2
3. 程序会弹出两个结果共同支持的对比模式
4. 选中模式后自动跳到 Compare Plot 执行

如果你告诉我你现在这两个结果节点分别是什么，我可以直接帮你判断能对比哪些模式。
```

## Template 7: user asks what is missing

Preferred response:

```text
这个目录现在还不能直接生成体检报告，缺少的是 *_DataList.log。你如果只是想先看单站质量，我可以先走 ObsCheck；如果你要完整体检报告，就需要先把 DataList 产物补出来。
```

## Template 8: user asks for quick support summary

Preferred response:

```text
先给你结论：这份数据整体可用，但局部频点质量不稳定。当前更像局部异常，不像整体失效。建议下一步重点看异常频点在对应模式下的图形表现，再判断是环境、链路还是瞬时观测问题。
```

## Preferred response shape

When not blocked by missing inputs, prefer this shape:

1. recognized inputs
2. recommended route
3. why this route is first
4. output path or next action

## Anti-patterns

Avoid responses like:

- asking for mode before checking the folder
- asking the user to choose between too many equivalent routes with no recommendation
- describing GUI compare plotting as if the user should manually browse raw plot files first
- inventing CLI parity for GUI-only workflows
