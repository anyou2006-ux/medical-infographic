# 输出规格

规范文件位于 `assets/infographic-spec.schema.json`。脚本使用标准库执行核心校验，不依赖第三方 JSON Schema 包。

最小示例：

```json
{
  "title": "医院数据治理架构",
  "render_mode": "gpt-only",
  "channel": "presentation",
  "layout": "architecture",
  "density": "standard",
  "theme": "medical-blue",
  "evidence_mode": "balanced",
  "language": "zh-CN",
  "pages": 1,
  "sections": [
    {"title": "数据源", "items": ["HIS", "EMR", "LIS"]},
    {"title": "治理平台", "items": ["主数据", "质量规则"]}
  ],
  "sources": [
    {"title": "项目输入材料", "url": "", "date": "2026-08-11"}
  ]
}
```

`visual_asset` 为可选本地图片路径。不要把二进制图片写入 JSON。

`render_mode` 可取：

- `gpt-only`：默认。GPT 根据完整提示词直接生成整页 PNG。
- `hybrid`：显式降级。AI 视觉背景加 SVG 信息层。
- `svg`：显式降级。纯 SVG 输出。
