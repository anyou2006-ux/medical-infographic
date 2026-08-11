---
name: medical-infographic
description: 将医疗信息化、智慧医院、HIS、EMR、医疗 AI、医院运营、临床业务流程等内容制作成经过事实与隐私检查的 GPT 直出信息图。默认让 GPT 根据完整提示词一次生成整页成图，支持微信公众号长图、小红书 3:4 多页卡片、电脑或 PPT 16:9 信息图，以及架构图、流程图、时间轴、对比矩阵、驾驶舱和场景解剖图。Use when creating healthcare IT infographics from text, Markdown, documents, or structured data. Do not use for patient diagnosis, treatment advice, or unredacted patient records.
---

# 医疗信息化信息图

默认使用 GPT 图像生成完整页面，包括中文、模块、连接关系、图表和视觉风格。先锁定事实层和逐页提示词，再逐页生成、逐字检查和定向重试。仅在 GPT 图像工具不可用或用户显式要求可编辑矢量时使用 SVG 降级路径。

## 工作流程

1. 读取输入，确定主题、目标受众和交付渠道。
2. 接受显式参数；未指定时使用：`render_mode: gpt-only`、`layout: auto`、`density: standard`、`theme: medical-blue`、`pages: auto`、`evidence_mode: balanced`。
3. 读取 [evidence-policy.md](references/evidence-policy.md)，检查患者隐私、数字、政策、排名、临床效果和产品参数。
4. 遇到患者隐私或缺少来源的高风险事实时停止最终出图，说明需要删除或补充的内容。
5. 读取 [layouts.md](references/layouts.md)，选择一种版式。只有无法可靠判断时才询问版式偏好。
6. 读取 [channels.md](references/channels.md)，确定画布、页数、文字上限和来源区。
7. 按 [output-schema.md](references/output-schema.md) 创建 `infographic-spec.json`。
8. 运行 `scripts/validate_content.py --spec <spec.json>`。状态为 `blocked` 时停止；状态为 `warning` 时只能标记为预览版。
9. 读取 [gpt-rendering.md](references/gpt-rendering.md)，运行 `scripts/build_gpt_prompt.py <spec.json> --output-dir <dir>`，生成逐页 `gpt-prompt-*.txt`。
10. 使用内置图像生成工具，逐页提交对应提示词；每次只生成一页。保存为 `page-*.png`，不要用 SVG 重新排版或覆盖 GPT 成图。
11. 使用图像查看工具检查每一页，对照规格逐字核验标题、模块、数字、单位、来源、箭头和页码。发现问题时只针对该页进行一次单变量重试；最多重试两轮。
12. 运行 `scripts/check_output.py <spec.json> <page.png...> --content-report <report.json> --visual-reviewed --output <quality-report.json>`。只有状态为 `pass` 才称为最终版。
13. GPT 图像工具不可用或连续两轮仍不合格时，读取 [hybrid-rendering.md](references/hybrid-rendering.md)，生成 SVG 降级版并明确标注，不得静默切换。

## 渠道参数

- `channel: wechat-long`：微信公众号长图。
- `channel: xhs-cards`：小红书 3:4 多页卡片。
- `channel: presentation`：电脑或 PPT 16:9 页面。

必须要求或推断 `channel`。当同一请求需要多个渠道时，复用同一事实层并分别渲染，不重新改写数字。

## 输出要求

交付以下可用文件：

- `infographic-spec.json`
- 一份或多份 `gpt-prompt-*.txt`
- 一张或多张 GPT 直出的 `page-*.png`
- `quality-report.json`
- `sources.md`，仅在存在外部来源时生成

仅在降级模式额外交付 `page-*.svg`。

在最终回复中说明渠道、版式、核验状态、文件位置和任何降级情况。

## 修改已有信息图

修改配色、密度、版式、页数或渠道时，先编辑现有 `infographic-spec.json`，重新生成提示词并调用 GPT。修改事实、数字或来源时重新运行内容验证。不要使用脚本在最终 PNG 上覆盖关键文字。
