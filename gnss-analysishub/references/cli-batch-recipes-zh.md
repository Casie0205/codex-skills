# CLI 批处理话术

当用户不是在问单条命令，而是在问“这件事怎么批量做、怎么稳定做、怎么交付结果”时，使用这份中文参考。

目标不是把用户教成命令行专家。

目标是把当前已经落地的 CLI 能力，加上脚本层编排经验，讲成一套容易复用的工作流。

## 一句话原则

讲批处理时，不要只给一串命令。

要同时讲清楚四层：

1. 批处理对象是什么
2. 底层 CLI 叶子命令是什么
3. 脚本层怎么扫描、复跑、归档
4. 最后怎么把结果交付出去

## 推荐回答骨架

遇到批处理问题，优先按这个结构回答：

- `批处理目标`
- `批处理单元`
- `底层 CLI`
- `编排思路`
- `输出目录`
- `汇总 / 归档`
- `交付方式`
- `当前不是原生命令的部分`

## 场景 1：批量单站质检

用户常见问法：

```text
我想把一个目录下面的原始 log 全部跑一遍质检，怎么做比较稳？
```

推荐回答：

```text
可以按“扫描目录 -> 逐文件跑 ObsCheck -> 复用已有结果或按需强制重跑 -> 每个场景各自落地输出”这条链路来做。
底层叶子命令还是 `AnalysisHub-cli qc obscheck <file>`，但真正稳定的批处理重点不在命令本身，而在外层编排：
1. 先定义哪些 `.log` 算候选输入
2. 跳过已经生成的报告目录和 `Sourcefile_*`
3. 决定是复用已有 `_QC.html` / `_DataList.log`，还是强制重跑
4. 把每个场景的输出固定放在源数据旁边，后面才方便汇总
如果只是“整批先跑一轮 QC”，这就是最小可用方案。
```

底层说明：

- 叶子命令：`AnalysisHub-cli qc obscheck <file> [options]`
- 典型脚本思路：扫描 `.log`、过滤候选、判断是否已有输出、按场景落输出

不要承诺：

- 不要把“批量扫描目录”说成当前 CLI 自带的单条原生命令

## 场景 2：批量观测量对比

用户常见问法：

```text
如果我要做批量质检 + 观测量对比 + 总表，应该怎么把 AnalysisHub-cli 编排起来？
```

推荐回答：

```text
这类需求建议拆成三段，而不是试图一条命令做完。
第一段是逐文件 QC，底层走 `AnalysisHub-cli qc obscheck <raw.log>`。
第二段是每个场景收集多份 `DataList.log`，再走 `AnalysisHub-cli report obs-compare <datalist...>` 生成单场景对比结果。
第三段再把所有场景的 `summary.csv`、`dimensions.csv` 和 HTML 报表统一归档，生成总表和索引页。
也就是说，CLI 负责叶子分析，脚本负责批量扫描、结果复用、统一归档和总表交付。
```

底层说明：

- 叶子命令 1：`AnalysisHub-cli qc obscheck <file> --obsqcmp-mp`
- 叶子命令 2：`AnalysisHub-cli report obs-compare <datalist1> <datalist2> ...`
- 对应现有脚本链路：
  - `scripts/batch_obs_quality_compare.py`
  - `scripts/aggregate_obs_quality_reports.py`
  - `scripts/package_obs_quality_bundle.py`

补充话术：

```text
这里关键的不只是“能不能跑起来”，而是“结果目录是不是稳定、后续总表是不是还能自动接上”。现在这套脚本实践已经把这件事做出来了，所以更适合按标准链路解释。
```

不要承诺：

- 不要把归档总表这一步说成 `AnalysisHub-cli report obs-compare` 原生自带

## 场景 3：批量一键流程

用户常见问法：

```text
我想把很多固定坐标场景都按一键流程跑掉，CLI 怎么组织？
```

推荐回答：

```text
这类需求适合把 `AnalysisHub-cli ctclib auto <rover_or_raw_file> [options]` 当成叶子命令，再在脚本层补齐场景扫描、坐标绑定、结果复用和归档。
如果是原始单文件，就按单文件 auto 路线；如果是 rover + base，则脚本层先把文件配对好，再统一下发 `--base`、`--coord`、`--base-coord` 等参数。
如果希望质检链路与 GUI 的 ObsQc MP 模式对齐，就在 auto 流程里带上 `--obsqcmp-mp`。
```

叶子命令：

- `AnalysisHub-cli ctclib auto <rover_or_raw_file> [options]`

脚本层职责：

- 识别一条场景的 rover/base 输入
- 绑定真值坐标和基站坐标
- 判断已有 `_QC.html` / `_DataList.log` / `.arlog` / `.pos` 是否可复用
- 保持场景输出目录稳定，方便后续追踪

典型输出：

- `_QC.html`
- `*_DataList.log`
- `.MP` / `.MPresult`
- `.arlog`
- `.pos`
- `*_auto_process_report.html`

## 场景 4：已有产物后，批量重建一键综合报表

用户常见问法：

```text
我前面的 QC 和残差都已经跑完了，现在只是报表模板改了，能不能批量重出综合报表？
```

推荐回答：

```text
这时不要重跑 `ctclib auto`，直接把 `AnalysisHub-cli report auto-combined` 当成叶子命令。
它适合消费现成的 `DataList/QC/MP/MPresult/arlog/pos` 产物，只重建固定坐标报表和一键综合报表。
这样速度快很多，也不会重复跑 CTCLib 和 QC。
```

底层说明：

- 叶子命令：`AnalysisHub-cli report auto-combined --rover-datalist <file> --arlog <file> [options]`
- 最少输入：
  - `--rover-datalist`
  - `--arlog`
- 常见补充输入：
  - `--base-datalist`
  - `--rover-qc`
  - `--base-qc`
  - `--rover-mp`
  - `--rover-mpresult`
  - `--base-mp`
  - `--base-mpresult`
  - `--pos`
  - `--coord`

脚本层职责：

- 自动从 `DataList` stem 推导兄弟 `_QC.html / .MP / .MPresult`
- 判断哪些场景的产物已经齐全，可以直接重建
- 统一把重建后的报表落到稳定目录

## 场景 5：批量合并 QC HTML

用户常见问法：

```text
我只是想把很多 QC HTML 合并成一个 Excel，总结一下先看什么系统和频点，有没有最简单的做法？
```

推荐回答：

```text
如果目标只是“合并很多 QC HTML”，那就先别上复杂编排，直接用最小工作流：
`AnalysisHub-cli qc merge-reports --dir <dir> --recurse -o <merged.xlsx>`

这条路适合快速汇总，不需要额外做场景归档和 HTML 总表。
只有在你还想要“单场景排名、维度汇总、统一浏览页、对外交付包”这些能力时，才需要再上多阶段脚本编排。
```

底层说明：

- 叶子命令：`AnalysisHub-cli qc merge-reports ...`
- 这是当前最适合“轻量批处理”的原生命令

## 场景 6：批量 SSR / CSM 对比页

用户常见问法：

```text
类似 SSR 这种分析，如果要批量生成每个场景的对比页，再做一个根目录索引，思路应该怎么讲？
```

推荐回答：

```text
这类问题可以沿用同一个编排模型：
1. 每个场景先跑一次叶子分析
2. 单场景生成自己的 HTML 和图片
3. 根目录生成索引页
4. 如果还要集中查看，再做 grand summary 或归档目录
重点是告诉用户：这里的“批处理体验”来自脚本层编排，不只是底层分析程序本身。
```

底层说明：

- 当前工作区这类例子主要由脚本和 `SSRAnalysis.exe --batch ...` 组合实现
- 相关脚本：
  - `scripts/batch_run_ssr_csm_compare.py`
  - `scripts/build_ssr_root_index.py`
  - `scripts/build_ssr_grand_summary.py`
  - `scripts/archive_ssr_reports.py`

不要承诺：

- 不要把这套 SSR 页面链路直接说成 `AnalysisHub-cli ssr` 已经完整内建

## 场景 7：对外交付一个可浏览的结果包

用户常见问法：

```text
我不只是要内部跑完，还想给别人一个可直接点开的汇总包，这种怎么讲比较清楚？
```

推荐回答：

```text
这种需求要单独加“交付层”。
前面的 CLI 和脚本负责把单场景结果跑出来；交付层负责把各国家或各场景的归档结果重新整理到一个 bundle 目录里，再补一个 `index.html` 作为统一入口。
这样拿到包的人不需要重新找原始目录结构，直接从入口页点进国家总表、场景总表、单场景报告就行。
```

底层说明：

- 现有对应实践：`scripts/package_obs_quality_bundle.py`
- 关键产物通常包括：
  - bundle 根目录
  - 入口 `index.html`
  - 各国家归档目录
  - 跨国家总表

## Skill 说法偏好

优先这样说：

- `CLI 负责叶子分析，脚本负责批量编排`
- `先把单场景结果稳定落地，再做统一归档和总表`
- `如果只是轻量汇总，优先用最小原生命令`
- `如果要交付，就再补一层 bundle/index`

尽量不要这样说：

- `这个功能 CLI 一条命令就能全做`
- `先随便写个 for 循环把目录跑完`
- `归档和总表只是附带工作`

## 推荐收尾句

当用户是在聊方案而不是立刻要执行时，优先用这种收尾：

```text
如果按现在这套实践来沉淀 skill，我建议把它定义成“叶子命令 + 编排脚本 + 归档交付”三层模型。这样后面不管是继续补新脚本，还是把其中一部分再收回 CLI 原生命令，用户的话术和心智模型都不用推倒重来。
```
