# Cloud Code Task Example: fix-config-default

状态：example | 更新日期：2026-11-11

> 仅用于说明字段粒度。不得把本文中的示例路径、分支或命令当作当前任务执行。

## 目录

- [1. 任务标识](#1-任务标识)
- [2. 仓库与环境](#2-仓库与环境)
- [3. 目标](#3-目标)
- [4. 范围](#4-范围)
- [5. 上下文](#5-上下文)
- [6. 验收](#6-验收)
- [7. 验证](#7-验证)
- [8. 回传](#8-回传)

## 1. 任务标识

- task_id: fix-config-default
- created_at: 2026-11-11 15:30
- requested_by: local-operator

## 2. 仓库与环境

- local_input_root: P:\DOC
- local_drive_mapping: C: -> O:, D: -> P:
- repo_path: D:\Code\demo
- branch: main
- project: demo
- project_context_paths:
  - P:\DOC\demo\README.md
- doc_authority: cloud-code-first
- os: Windows 11
- toolchain: Visual Studio 2019 / v142
- server_build_targets:
  - solution: D:\Output\cloud-code-build\fix-config-default\demo.sln
    project: demo_app
    configuration: Debug
    platform: x86
- build_root: D:\Output\cloud-code-build\fix-config-default
- output_path: D:\Output\cloud-code-delivery\fix-config-default
- network: forbidden

## 3. 目标

配置文件中缺少 `timeout_ms` 时，程序使用 5000 毫秒默认值，而不是崩溃。

## 4. 范围

- allowed_paths:
  - D:\Code\demo\src\config
  - D:\Code\demo\tests\config
- forbidden_paths:
  - D:\Code\demo\third_party
  - P:\DOC
- non_goals:
  - 不修改其他配置字段的默认值
  - 不重构配置解析器

## 5. 上下文

- entrypoints:
  - D:\Code\demo\src\config\ConfigParser.cpp：读取并校验配置
- related_docs:
  - P:\DOC\demo\config-format.md：字段定义
- current_behavior: 缺字段时返回空指针并导致后续解引用
- desired_behavior: 缺字段时生成默认值并记录一条警告
- known_constraints:
  - 保持现有 JSON 库和错误码

## 6. 验收

- [ ] 缺少 `timeout_ms` 时返回默认值 5000
- [ ] 原有非法类型测试仍通过
- [ ] 新增缺字段回归测试通过

## 7. 验证

```powershell
cmake -S "D:\Code\demo" -B "D:\Output\cloud-code-build\fix-config-default" -G "Visual Studio 16 2019" -A x86
cmake --build "D:\Output\cloud-code-build\fix-config-default" --config Debug
ctest --test-dir "D:\Output\cloud-code-build\fix-config-default" -C Debug --output-on-failure
```

## 8. 回传

- output_path: D:\Output\cloud-code-delivery\fix-config-default
- required_files:
  - result.md
  - changed-files.txt
  - verification.log
  - cloud-code.patch
  - development-result.json
  - development-result.html
- screenshot_report_skill: cloud-dev-result-report
- commit_policy: fix prefix; stage only src\config and tests\config files changed by this task
- doc_discrepancy_report: required
- cloud_result_transfer: manual-copy
- local_write_policy: forbidden
