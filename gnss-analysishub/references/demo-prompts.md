# Demo Prompts

Use these prompts for internal demos and share sessions. They are written to match the current `AnalysisHub` / `AnalysisHub-cli` implementation, not an imagined future version.

## Folder recognition

```text
先识别这个目录里有哪些 GNSS 分析产物，告诉我能走哪些 AnalysisHub / AnalysisHub-cli 流程。
```

```text
帮我判断这个目录是只有 QC，还是同时具备 DF / TF 体检分析条件。
```

## QC and health report

```text
基于这个 _QC.html 和 DataList.log，生成数据体检报表，并总结最主要的异常项。
```

```text
请用 AnalysisHub-cli 的能力解释这份 QC 体检报表，告诉我结论、关键异常、重点时间窗和下一步排查建议。
```

## DF / TF mode explanation

```text
如果我切到 DF 模式再点体检报表，现在工具会走什么逻辑？和 CLI 的 report health 有什么区别？
```

```text
请说明当前 GUI 下 DF / TF 体检报表能输出哪些异常汇总表，尤其是伪距和载波精度异常卫星频点。
```

## Plotting

```text
把这个 DF 文件按 GPS、频点 1 画残差图，告诉我对应的 CLI 命令应该怎么写。
```

```text
针对这个 DataList 文件，给我生成一个 CN0 图的 CLI 命令，并说明输出 PNG 会放到哪里。
```

## Batch workflows

```text
把这个目录下所有 QC HTML 合并成一张汇总表，并告诉我最适合先看的系统和频点。
```

```text
如果我要做批量质检 + 汇总 + 体检报表，应该怎么把 AnalysisHub-cli 编排成一个稳定流程？
```

## Support-facing summary

```text
请把这次 GNSS 分析结果整理成一段市场支持可直接转发的摘要，不要讲命令，只讲结论和建议。
```

```text
请把这份体检结论压缩成 4 句话，适合放在周会汇报里。
```
