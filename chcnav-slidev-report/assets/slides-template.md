---
theme: ./theme
layout: cover
title: 报告标题
subtitle: 用一句明确结论概括本次汇报的主要发现
metaLeftLabel: 汇报人：
metaLeftValue: 填写姓名
metaRightLabel: 时间：
metaRightValue: 2099.01
author: 填写姓名
date: 2099-01
canvasWidth: 1280
aspectRatio: 16/9
highlighter: shiki
lineNumbers: false
mdc: true
transition: fade
colorSchema: light
fonts:
  sans: Microsoft YaHei
  mono: Cascadia Code
  provider: none
defaults:
  layout: default
---

---
title: 报告概述
subtitle: 用一句明确结论概括本页最重要的事实
---

<div class="lead-grid">
  <section class="lead-item">
    <div class="lead-index">01</div>
    <h2>背景与问题</h2>
    <p>填写研究背景、业务问题或需要回答的核心问题。</p>
  </section>
  <section class="lead-item">
    <div class="lead-index">02</div>
    <h2>主要结果</h2>
    <p>填写最重要的结果、数据范围或验证结论。</p>
  </section>
  <section class="lead-item">
    <div class="lead-index">03</div>
    <h2>边界与下一步</h2>
    <p>填写证据边界、仍需验证的问题和后续工作。</p>
  </section>
</div>

---
layout: toc
title: 汇报结构
---

<div class="toc-list">
  <section class="toc-item">
    <span class="toc-part">Part 1</span>
    <h2>背景与目标</h2>
    <p>填写第一部分说明。</p>
  </section>
  <section class="toc-item">
    <span class="toc-part">Part 2</span>
    <h2>方法与结果</h2>
    <p>填写第二部分说明。</p>
  </section>
  <section class="toc-item">
    <span class="toc-part">Part 3</span>
    <h2>分析与讨论</h2>
    <p>填写第三部分说明。</p>
  </section>
  <section class="toc-item">
    <span class="toc-part">Part 4</span>
    <h2>结论与下一步</h2>
    <p>填写第四部分说明。</p>
  </section>
</div>

---
layout: section
sectionNumber: "01"
title: 背景与目标
---

在这里写明本章节要回答的问题、范围或假设。

---
title: 内容页标题
subtitle: 写出本页数据能够直接支持的明确结论
---

<div class="setup-grid">
  <div class="setup-list">
    <section class="setup-item">
      <span class="label">要点一</span>
      <strong>填写核心事实或参数</strong>
      <p>填写解释、来源或约束。</p>
    </section>
    <section class="setup-item">
      <span class="label">要点二</span>
      <strong>填写核心事实或参数</strong>
      <p>填写解释、来源或约束。</p>
    </section>
    <section class="setup-item">
      <span class="label">要点三</span>
      <strong>填写核心事实或参数</strong>
      <p>填写解释、来源或约束。</p>
    </section>
  </div>
  <div class="metric-stack">
    <section class="metric-item">
      <strong>指标</strong>
      <div>
        <h3>指标名称</h3>
        <p>填写指标定义和取值。</p>
      </div>
    </section>
    <section class="metric-item">
      <strong>结果</strong>
      <div>
        <h3>结果名称</h3>
        <p>填写结果和解释边界。</p>
      </div>
    </section>
  </div>
</div>

---
layout: split
split: figure-left
title: 图表页标题
subtitle: 写出图中最重要的明确结论
---

::left::

<figure class="figure-block">
  <div class="figure-placeholder">替换为图 1 或删除本页</div>
  <figcaption>图 1　图表标题</figcaption>
</figure>

::right::

<div class="rule-list">
  <section class="rule-item">
    <strong>观察</strong>
    <div>
      <h3>填写第一条观察</h3>
      <p>填写图中能够直接支持的结论。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>说明</strong>
    <div>
      <h3>填写第二条说明</h3>
      <p>填写口径、样本量或限制条件。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>注意</strong>
    <div>
      <h3>填写解释边界</h3>
      <p>填写不能从当前图表推出的结论。</p>
    </div>
  </section>
</div>

---
layout: split
split: wide-left
title: 公式页标题
subtitle: 写出公式揭示的明确结论，不要只描述公式
---

::left::

$$
e_k = \hat{x}_k - x_k
$$

$$
\mathrm{metric} = f(e_k, P_k)
$$

**变量定义：** $x_k$ 为真实值，$\hat{x}_k$ 为估计值，$P_k$ 为协方差。

::right::

<div class="rule-list">
  <section class="rule-item">
    <strong>≈1</strong>
    <div>
      <h3>理想值</h3>
      <p>填写理想值及其含义。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>&gt;1</strong>
    <div>
      <h3>偏高</h3>
      <p>填写偏高的常见原因。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>&lt;1</strong>
    <div>
      <h3>偏低</h3>
      <p>填写偏低的常见原因。</p>
    </div>
  </section>
</div>

---
title: 表格页标题
subtitle: 写出表格比较后得到的明确结论
---

<table class="flat-table">
  <thead>
    <tr><th>路径或类别</th><th>指标 A</th><th>指标 B</th><th>指标 C</th><th>结论</th></tr>
  </thead>
  <tbody>
    <tr><td><strong>对象 1</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
    <tr><td><strong>对象 2</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
    <tr><td><strong>对象 3</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
  </tbody>
</table>

<div class="callout spaced">
  <p>填写表格解读、适用范围或不能推出的结论。</p>
</div>

---
title: 全局误差评价
subtitle: 用一句明确结论概括一致性与绝对导航精度
---

<div class="global-error-eval">
  <section class="global-error-panel">
    <h2>状态组 ANEES / NRC</h2>
    <table class="flat-table">
      <thead>
        <tr><th>路径</th><th>位置</th><th>速度</th><th>姿态</th><th>NRC</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>路径 1</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
        <tr><td><strong>路径 2</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
        <tr><td><strong>路径 3</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
      </tbody>
    </table>
  </section>

  <section class="global-error-panel">
    <h2>位置误差 RMS</h2>
    <table class="flat-table">
      <thead>
        <tr><th>路径</th><th>E</th><th>N</th><th>U</th><th>水平</th><th>3D RMS</th><th>3D max</th></tr>
      </thead>
      <tbody>
        <tr><td><strong>路径 1</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
        <tr><td><strong>路径 2</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
        <tr><td><strong>路径 3</strong></td><td>填写</td><td>填写</td><td>填写</td><td>填写</td><td>填写</td><td>填写</td></tr>
      </tbody>
    </table>
  </section>

  <div class="global-error-note">
    <p><strong>填写评价时刻数量。</strong>填写一致性与速度、姿态差异的解释边界。</p>
    <p>填写绝对精度结果的结构优势、限制和不能外推的范围。</p>
  </div>
</div>

---
layout: section
sectionNumber: "02"
title: 方法与结果
---

说明本章节的方法、数据、验证过程和主要结果。

---
title: 对比页标题
subtitle: 写出比较后得到的明确结论
---

<div class="two-col-list">
  <div>
    <h2>对象 A</h2>
    <ul>
      <li>填写参数或现象。</li>
      <li>填写结果和限制。</li>
      <li>填写证据来源。</li>
    </ul>
  </div>
  <div>
    <h2>对象 B</h2>
    <ul>
      <li>填写参数或现象。</li>
      <li>填写结果和限制。</li>
      <li>填写证据来源。</li>
    </ul>
  </div>
</div>

---
title: 关键差异
subtitle: 写出影响最终判断的明确差异
---

<div class="rule-list">
  <section class="rule-item">
    <strong>01</strong>
    <div>
      <h3>填写第一条差异</h3>
      <p>填写数值、条件和解释。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>02</strong>
    <div>
      <h3>填写第二条差异</h3>
      <p>填写数值、条件和解释。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>03</strong>
    <div>
      <h3>填写第三条差异</h3>
      <p>填写数值、条件和解释。</p>
    </div>
  </section>
</div>

<p class="table-note">填写样本量、单位、方法或统计口径。</p>

---
layout: split
split: figure-left
title: 结果图表页
subtitle: 写出图表支持的明确结论
---

::left::

<figure class="figure-block tall">
  <div class="figure-placeholder">替换为图 2 或删除本页</div>
  <figcaption>图 2　图表标题</figcaption>
</figure>

::right::

<div class="rule-list">
  <section class="rule-item">
    <strong>结果</strong>
    <div>
      <h3>填写直接观察</h3>
      <p>只写图表或数据能够直接支持的内容。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>解释</strong>
    <div>
      <h3>填写合理推断</h3>
      <p>明确标注为推断，并写出依据。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>边界</strong>
    <div>
      <h3>填写限制</h3>
      <p>写出样本、方法或模型带来的限制。</p>
    </div>
  </section>
</div>

---
layout: section
sectionNumber: "03"
title: 分析与讨论
---

区分直接证据、合理推断和尚不能下结论的内容。

---
title: 证据分级
subtitle: 写出当前证据能够确认的明确结论
---

<div class="evidence-grid">
  <section class="evidence-col">
    <h2>已确认证据</h2>
    <ul>
      <li>填写直接观测或已验证结果。</li>
      <li>填写数据范围、样本量或实验条件。</li>
      <li>填写可复现的检查结果。</li>
    </ul>
  </section>
  <section class="evidence-col">
    <h2>合理推断</h2>
    <ul>
      <li>填写与当前证据一致的推断。</li>
      <li>写明推断依赖的条件。</li>
      <li>避免把相关性写成因果关系。</li>
    </ul>
  </section>
  <section class="evidence-col">
    <h2>尚不能下结论</h2>
    <ul>
      <li>填写仍需验证的问题。</li>
      <li>填写不能外推的范围。</li>
      <li>填写下一步需要补充的实验或数据。</li>
    </ul>
  </section>
</div>

---
layout: split
title: 限制与下一步
subtitle: 写出当前结论的适用范围和已确定的后续动作
---

::left::

<div class="rule-list">
  <section class="rule-item">
    <strong>限制 01</strong>
    <div>
      <h3>数据范围</h3>
      <p>填写样本、场景或 realization 的限制。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>限制 02</strong>
    <div>
      <h3>方法边界</h3>
      <p>填写模型、假设或参数口径的限制。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>限制 03</strong>
    <div>
      <h3>证据缺口</h3>
      <p>填写尚未完成的分析。</p>
    </div>
  </section>
</div>

::right::

<div class="rule-list">
  <section class="rule-item">
    <strong>下一步 01</strong>
    <div>
      <h3>补充验证</h3>
      <p>填写需要的实验、seed 或数据。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>下一步 02</strong>
    <div>
      <h3>细化分析</h3>
      <p>填写需要进一步分解的指标或节点。</p>
    </div>
  </section>
  <section class="rule-item">
    <strong>下一步 03</strong>
    <div>
      <h3>决定事项</h3>
      <p>填写需要团队确认的下一步。</p>
    </div>
  </section>
</div>

---
title: 复现入口
subtitle: 结果、脚本和数据均可按下列路径复现
---

<div class="path-list">
  <div class="path-row">
    <span>输入数据</span>
    <code>填写路径</code>
  </div>
  <div class="path-row">
    <span>运行结果</span>
    <code>填写路径</code>
  </div>
  <div class="path-row">
    <span>分析脚本</span>
    <code>填写路径</code>
  </div>
  <div class="path-row">
    <span>报告正文</span>
    <code>填写路径</code>
  </div>
</div>

<div class="command-row">
  <div class="command-item">
    <span>本地预览</span>
    <code>在 VS Code 中打开 Slidev 预览</code>
  </div>
  <div class="command-item">
    <span>输出约定</span>
    <code>默认仅维护 Markdown</code>
  </div>
</div>

<p class="table-note">默认不导出 PPTX、PDF 或 HTML；如需其他格式，由用户明确指定。</p>

---
layout: end
title: 感谢观看！
---

<div class="closing-summary">
  <h2>核心结论</h2>
  <p>填写本次汇报最重要的结论、适用范围和下一步。</p>
  <div class="closing-metrics">
    <div><strong>填写</strong><span>关键数据</span></div>
    <div><strong>填写</strong><span>关键数据</span></div>
    <div><strong>填写</strong><span>关键数据</span></div>
  </div>
</div>
