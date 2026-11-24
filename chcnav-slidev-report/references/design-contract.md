# CHCNAV Slidev Design Contract

## 目录

- [Source](#source)
- [Canvas and Typography](#canvas-and-typography)
- [Page Geometry](#page-geometry)
- [Assets](#assets)
- [Output Policy](#output-policy)

## Source

The theme is derived from `D:\DOC\PPTinternally.pptx`.

The PowerPoint master is rasterized once into the background files under `assets/theme/assets/`. PPTX is not needed for Slidev preview or Markdown authoring.

## Canvas and Typography

| Parameter | Value |
|---|---|
| Canvas | `1280 × 720 px`, 16:9 |
| Font | 微软雅黑 |
| Primary orange | `#FF7F32` |
| Deep orange | `#E95D00` |
| Body dark | `#1F1F1F` |
| Secondary gray | `#3F3F3F` |
| Body font-size | `18 pt` (24 px in browser); tables, captions, paths, and footnotes may be smaller |
| Body line-height | `1.5` |
| Field label | `16 pt`, bold, primary orange `#FF7F32` |
| Content title | 36 pt at `x=99.91, y=41.24, w=901.93, h=57.8` |
| Content subtitle | 18 pt (24 px) at `x=99.91, y=101, w=901.99, h=72`, maximum two lines |
| Section number | 220 pt |
| Section title | 40 pt |
| Closing title | 66 pt |

## Page Geometry

### Cover

- Title: `x=132.67, y=149.33, w=1014.67, h=170.17`
- Subtitle: `x=272.67, y=345.34, w=734.67, h=49.83`
- Divider: `x=222.67, y=319.51, w=834.67`
- Metadata boxes: `x=361.33` and `x=655.21`, both `y=455.51`, `w=263.45`

### Contents

- `Contents` label: `x=121.33, y=311.33, w=286.67`
- Topic grid: starts at `x=601.33, y=145`, width `621.07`

### Section

- Number: `x=62.01, y=221.75, w=386.92, h=285.22`
- Copy: `x=440.64, y=248.53, w=681.91`
- Body: starts 151 px below the section title

### Content

- Safe content area: `x=100, y=176, w=1080, h=484`
- Split layouts use `wide-left`, `wide-right`, `figure-left`, or `figure-right`

### Closing

- Title: `x=50.67, y=169.33, w=643.8, h=139.17`
- Copy: `x=736.78, y=173.68, w=491.22, h=430.82`

## Assets

Preserve these files:

```text
assets/theme/assets/template_cover.png
assets/theme/assets/template_toc.png
assets/theme/assets/template_section.png
assets/theme/assets/template_content.png
assets/theme/assets/template_closing.png
assets/theme/assets/chcnav-logo.png
assets/theme/assets/chcnav-logo-white.png
```

The background assets contain the orange title marker and decorative elements. Orange cover and closing pages keep their native white logo; section pages keep their native dark logo. White content, split, and contents pages render transparent `chcnav-logo.png`. `chcnav-logo-white.png` is reserved for explicit recoloring or alternate orange layouts.

## Output Policy

The default deliverables are:

```text
slides.md
theme/
assets/
```

Do not create PPTX, PDF, HTML, PNG, or similar files unless the user explicitly requests them. A preview server may be used for inspection because it does not persist an exported artifact.
