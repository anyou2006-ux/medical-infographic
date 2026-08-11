# Medical Infographic Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a GitHub-ready Codex Skill and Plugin that turns healthcare IT content into verified, channel-specific hybrid infographics.

**Architecture:** Keep orchestration and safety rules in a concise `SKILL.md`. Use Python standard-library scripts for deterministic spec validation, privacy checks, SVG generation, and quality reports; call Codex image generation only as an optional visual layer. Store detailed channel, layout, evidence, and example guidance in one-level references.

**Tech Stack:** Codex Skill/Plugin manifests, Python 3.11 standard library, JSON Schema document, SVG 1.1, `unittest`, optional Codex image generation.

---

### Task 1: Scaffold the Plugin and Skill

**Files:**
- Create: `.codex-plugin/plugin.json`
- Create: `skills/medical-infographic/SKILL.md`
- Create: `skills/medical-infographic/agents/openai.yaml`

**Steps:**
1. Run the official Plugin scaffold into `E:/codexfile` with `--with-skills --with-scripts --with-assets`.
2. Run the official Skill initializer into the Plugin `skills/` directory with `scripts,references,assets` resources.
3. Replace placeholders with final metadata.
4. Run Plugin and Skill validators and record expected initial failures for unfinished resources.

### Task 2: Define the Data Contract

**Files:**
- Create: `skills/medical-infographic/references/output-schema.md`
- Create: `skills/medical-infographic/assets/infographic-spec.schema.json`
- Test: `tests/test_validate_spec.py`

**Steps:**
1. Write failing tests for valid channels, layouts, evidence modes, dimensions, sections, sources, and pages.
2. Run `python -m unittest tests.test_validate_spec -v`; expect failures because the validator does not exist.
3. Implement schema and validation rules.
4. Run the focused test; expect pass.

### Task 3: Implement Privacy and Evidence Validation

**Files:**
- Create: `skills/medical-infographic/scripts/validate_content.py`
- Test: `tests/test_validate_content.py`

**Steps:**
1. Add tests for names paired with patient fields, Chinese ID numbers, phone numbers, medical record numbers, unsupported channel values, missing sources, and illustrative data.
2. Verify tests fail.
3. Implement deterministic checks and JSON output with `status`, `errors`, and `warnings`.
4. Verify all focused tests pass.

### Task 4: Implement Channel-Aware SVG Rendering

**Files:**
- Create: `skills/medical-infographic/scripts/render_svg.py`
- Create: `skills/medical-infographic/assets/themes/*.json`
- Test: `tests/test_render_svg.py`

**Steps:**
1. Add tests for 1080 × 6000, 1080 × 1440, and 1920 × 1080 output dimensions.
2. Add tests for XML escaping, title wrapping, section positioning, page output, source footer, and embedded visual image paths.
3. Verify tests fail.
4. Implement the minimal standard-library SVG renderer.
5. Verify tests pass and generated SVG parses as XML.

### Task 5: Implement Quality Reporting

**Files:**
- Create: `skills/medical-infographic/scripts/check_output.py`
- Test: `tests/test_check_output.py`

**Steps:**
1. Add tests for missing sources, privacy flags, invalid dimensions, overflow markers, and render modes.
2. Verify tests fail.
3. Implement `quality-report.json` generation.
4. Verify tests pass.

### Task 6: Author Skill References and Examples

**Files:**
- Create: `skills/medical-infographic/references/channels.md`
- Create: `skills/medical-infographic/references/layouts.md`
- Create: `skills/medical-infographic/references/evidence-policy.md`
- Create: `skills/medical-infographic/references/hybrid-rendering.md`
- Create: `skills/medical-infographic/references/examples.md`
- Create: `tests/fixtures/*.json`

**Steps:**
1. Document the three channel adapters and six layout selectors.
2. Document strict, balanced, and source-only evidence behavior.
3. Add 12 sanitized examples and test summaries.
4. Keep all reference links one level below `SKILL.md`.

### Task 7: Finalize Skill and Plugin Metadata

**Files:**
- Modify: `skills/medical-infographic/SKILL.md`
- Modify: `skills/medical-infographic/agents/openai.yaml`
- Modify: `.codex-plugin/plugin.json`
- Create: `README.md`
- Create: `LICENSE`

**Steps:**
1. Write concise imperative workflow instructions and trigger-rich metadata.
2. Configure UI metadata and default prompt.
3. Add GitHub-facing installation, usage, limitations, and contribution notes at repository root, not inside the Skill folder.
4. Use a neutral contributor copyright notice under the MIT license.

### Task 8: Verify and Package

**Files:**
- Create: `tests/test_examples.py`
- Create: `examples/generated/*`

**Steps:**
1. Run `python -m unittest discover -s tests -v`; expect all tests to pass.
2. Generate representative outputs for all three channels.
3. Parse every SVG as XML and inspect representative PNG/SVG output visually where supported.
4. Run `quick_validate.py` on the Skill.
5. Run `validate_plugin.py` on the Plugin.
6. Run `git status --short`, review all tracked files, and create the initial local commit.

