# 安装与调用验收检查表

本检查表用于验证 GitHub 安装、显式调用、隐式调用和三种渠道交付。确定性验收由脚本执行；Skill 选择行为需要在安装后的新 Codex 任务中检查。

## 1. 安装检查

```text
使用 $skill-installer 安装：
https://github.com/anyou2006-ux/medical-infographic/tree/main/skills/medical-infographic
```

```powershell
python scripts/verify_install.py --source skills/medical-infographic
```

通过条件：状态为 `pass`，`skill_name` 为 `medical-infographic`，15 个必需文件均存在，`source_match` 为 `true`。

## 2. 自动验收

```powershell
python scripts/run_acceptance.py --output artifacts/acceptance
```

通过条件：`total` 和 `passed` 均为 9，`failed` 为 0。每个案例目录应包含 SVG、`content-report.json` 和 `quality-report.json`。

9 个案例覆盖：

- 微信公众号、小红书、电脑/PPT 三种渠道。
- 结构、流程、决策三类内容。
- 架构图、流程图、时间轴、对比矩阵、驾驶舱和场景解剖图六种版式。
- 5 个显式调用和 4 个隐式调用提示词。

## 3. 新任务中的显式调用

新建 Codex 任务，依次提交：

```text
使用 $medical-infographic，把 HIS 核心模块关系制作成 16:9 医疗信息化架构图，用于 PPT 展示。
```

```text
使用 $medical-infographic，把门诊预约、签到、诊疗、检查、缴费和随访流程制作成 6 页小红书卡片。
```

```text
使用 $medical-infographic，把医院数据治理内容制作成微信公众号长图。
```

通过条件：任务读取 Skill，要求或形成结构化规范，并进入内容校验和成图流程。

## 4. 新任务中的隐式调用

新建 Codex 任务，不写 Skill 名称，提交：

```text
把智慧病房的终端、网络、平台和服务内容制作成 5 页小红书医疗信息图。
```

通过条件：Codex 自动选择 `medical-infographic`。隐式选择依赖 Skill 描述和当前技能数量，因此需要记录是否触发，不能只检查最终文本。

## 5. 不应触发的请求

以下请求不应调用该 Skill：

```text
根据患者症状给出诊断和用药建议。
```

```text
修复 Python 项目中的单元测试失败。
```

如误触发，应调整 `SKILL.md` 的 `description`，并重新执行本检查表。
