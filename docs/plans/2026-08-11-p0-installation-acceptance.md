# P0 安装与验收实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 验证公开仓库可被 Codex 安装，并用 9 个代表性提示词重复验证三种渠道的内容校验、SVG 生成和质量检查。

**Architecture:** 使用官方 `skill-installer` 完成用户级安装。仓库内保存提示词、预期参数和固定规范，验收运行器不调用模型，而是验证提示词契约后使用固定规范执行确定性流水线；Codex 显式及隐式触发另由新任务检查表验证。

**Tech Stack:** Python 3.11、`unittest`、JSON、现有 SVG 渲染与质量检查脚本、GitHub Actions。

---

### Task 1: 定义 9 个验收案例

**Files:**
- Create: `evals/acceptance-cases.json`
- Create: `tests/test_acceptance.py`

**Step 1:** 写失败测试，要求案例数为 9，覆盖 3 个渠道和 3 类内容，并同时包含显式及隐式调用。

**Step 2:** 运行 `python -m unittest tests.test_acceptance -v`，预期因案例文件不存在而失败。

**Step 3:** 创建案例清单，每个案例包含提示词、调用方式、预期渠道、预期版式、规范文件和预期状态。

**Step 4:** 再次运行测试，预期通过。

### Task 2: 实现端到端验收运行器

**Files:**
- Create: `scripts/run_acceptance.py`
- Modify: `tests/test_acceptance.py`
- Modify: `.gitignore`

**Step 1:** 写失败测试，要求运行器为每个案例生成 SVG、内容报告和质量报告，并汇总通过率。

**Step 2:** 运行测试，预期因运行器不存在而失败。

**Step 3:** 实现最小运行器，复用现有三个脚本，不复制校验规则。

**Step 4:** 运行 `python scripts/run_acceptance.py --output artifacts/acceptance`，预期 9/9 通过。

### Task 3: 实现安装检查

**Files:**
- Create: `scripts/verify_install.py`
- Modify: `tests/test_acceptance.py`

**Step 1:** 写失败测试，要求检查已安装 Skill 的 `SKILL.md`、脚本、参考文档和元数据。

**Step 2:** 使用官方安装器从 `anyou2006-ux/medical-infographic` 安装 `skills/medical-infographic`。

**Step 3:** 实现安装检查器并对真实安装目录运行。

### Task 4: 补充使用文档

**Files:**
- Create: `docs/acceptance-checklist.md`
- Create: `docs/acceptance-report.md`
- Modify: `README.md`

**Step 1:** 记录 9 个案例的执行命令和通过条件。

**Step 2:** 记录新 Codex 任务中的显式调用、隐式调用和不应触发案例。

**Step 3:** 在 README 增加安装命令、验收命令和报告链接。

### Task 5: 发布验证

**Files:**
- Modify: `.github/workflows/test.yml`

**Step 1:** 将 9 案例验收加入 GitHub Actions。

**Step 2:** 运行完整单元测试、官方 Skill/Plugin 校验及验收运行器。

**Step 3:** 提交功能分支，合并到 `main`，推送并等待 GitHub Actions 通过。
