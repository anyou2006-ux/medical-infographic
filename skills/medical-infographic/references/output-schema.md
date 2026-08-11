# 输出规格

规范文件位于 `assets/infographic-spec.schema.json`。脚本使用标准库执行核心校验，不依赖第三方 JSON Schema 包。

最小示例：

```json
{
  "title": "医院数据治理架构",
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

