---
name: medical-infographic
description: 将医疗信息化、智慧医院、HIS、EMR、医疗 AI、医院运营、临床业务流程等内容制作成经过事实与隐私检查的混合信息图。用于微信公众号长图、小红书 3:4 多页卡片、电脑或 PPT 16:9 信息图，以及医疗系统架构图、流程图、时间轴、对比矩阵、驾驶舱和场景解剖图。Use when creating healthcare IT infographics from text, Markdown, documents, or structured data. Do not use for patient diagnosis, treatment advice, or unredacted patient records.
---

# 医疗信息化信息图

将图像生成用于无文字视觉素材，将 SVG 用于中文、数字、图表、箭头和来源。任何工具不可用时保留可编辑 SVG，不编造内容以填补缺失信息。

## 工作流程

1. 读取输入，确定主题、目标受众和交付渠道。
2. 接受显式参数；未指定时使用：`layout: auto`、`density: standard`、`theme: medical-blue`、`pages: auto`、`evidence_mode: balanced`。
3. 读取 [evidence-policy.md](references/evidence-policy.md)，检查患者隐私、数字、政策、排名、临床效果和产品参数。
4. 遇到患者隐私或缺少来源的高风险事实时停止最终出图，说明需要删除或补充的内容。
5. 读取 [layouts.md](references/layouts.md)，选择一种版式。只有无法可靠判断时才询问版式偏好。
6. 读取 [channels.md](references/channels.md)，确定画布、页数、文字上限和来源区。
7. 按 [output-schema.md](references/output-schema.md) 创建 `infographic-spec.json`。
8. 运行 `scripts/validate_content.py --spec <spec.json>`。状态为 `blocked` 时停止；状态为 `warning` 时只能标记为预览版。
9. 桌面端存在图像生成工具时，按 [hybrid-rendering.md](references/hybrid-rendering.md) 生成无文字或少文字的背景/插画。不得让图像模型绘制表格、长段中文或关键数值。
10. 运行 `scripts/render_svg.py <spec.json> --output-dir <dir>` 生成可编辑 SVG。
11. 存在 Node.js 与 `sharp` 时，运行 `node scripts/render_png.cjs <input.svg> <output.png>`。缺少依赖时交付 SVG 并说明 PNG 未生成。
12. 运行 `scripts/check_output.py` 生成 `quality-report.json`。仅当状态为 `pass` 时称为最终版。
13. 视觉检查代表页；发现裁切、重叠、错字或连接关系错误时先修复再交付。

## 渠道参数

- `channel: wechat-long`：微信公众号长图。
- `channel: xhs-cards`：小红书 3:4 多页卡片。
- `channel: presentation`：电脑或 PPT 16:9 页面。

必须要求或推断 `channel`。当同一请求需要多个渠道时，复用同一事实层并分别渲染，不重新改写数字。

## 输出要求

交付以下可用文件：

- `infographic-spec.json`
- 一张或多张 `page-*.svg`
- 能够转换时生成对应 `page-*.png`
- `quality-report.json`
- `sources.md`，仅在存在外部来源时生成

在最终回复中说明渠道、版式、核验状态、文件位置和任何降级情况。

## 修改已有信息图

修改配色、密度、版式、页数或渠道时，优先编辑现有 `infographic-spec.json` 后重新渲染。修改事实、数字或来源时重新运行内容验证。不要直接在最终 PNG 上覆盖关键文字。

