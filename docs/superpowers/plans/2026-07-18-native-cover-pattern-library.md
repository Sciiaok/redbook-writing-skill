# 小红书原生封面模式库实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把可追溯的小红书封面样本沉淀成跨类目可检索的模式库，并为文字型内容提供优先、可复现、不会伪造中文的确定性字卡渲染器。

**Architecture:** 证据层保存本次四张本地样本和新增站内样本的可观察特征、公开互动代理与局限；模式层把封面分成文字优先与画面优先两条路由，记录任务、素材门、反例和生产参数；执行层用选择器返回 `matched / needs_materials / needs_research`，字卡族再交给 Pillow 渲染器生成 1080×1440 PNG。封面模式只承担载体与任务适配，不能冒充流量因果或绕过现有 style binding 发布门。

**Tech Stack:** Python 3、Pillow、JSON、pytest、Markdown、现有 redbook-writing 资产合同。

## Global Constraints

- 文字型 `feed_stop / explain / authority_statement / relationship_build` 在无强视觉证据时优先字卡；真实画面本身构成证据时优先实拍、结果对照或截图。
- 本次截图中的用户名、头像、具体文案和完整构图只作观察证据，不复制为模板。
- 公开点赞、收藏、评论、分享只记录为 `public_proxy_observation`，不推断封面导致流量。
- 没有 exact published style binding 时，输出上限仍是 `prototype_only`。
- 中文文字必须由确定性排版渲染；生成模型不得承担最终文字拼写。
- 所有新增脚本先写失败测试，再做最小实现；最终运行完整测试与 Skill validator。

---

### Task 1: 建立封面证据合同与模式资产

**Files:**
- Create: `docs/research/2026-07-18-native-cover-patterns.md`
- Create: `docs/research/2026-07-18-native-cover-patterns.json`
- Create: `redbook-writing/assets/cover-patterns-v1.json`
- Create: `tests/test_cover_patterns.py`

**Interfaces:**
- Consumes: 四张本地截图、站内只读观察、公开运营资料。
- Produces: `cover-patterns-v1.json`，字段包含 `pattern_id`、`family`、`priority_policy`、`jobs`、`carriers`、`required_materials_any`、`contraindications`、`design_contract`、`evidence_refs`、`claim_ceiling`。

- [ ] **Step 1: 写失败测试**

```python
def test_text_card_is_prioritized_only_for_text_first_jobs():
    asset = load_asset()
    text_card = by_id(asset, "CP01")
    assert text_card["priority_policy"]["default_when"]
    assert "real_scene_is_primary_evidence" in text_card["contraindications"]
    assert text_card["claim_ceiling"] == "task_fit"
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python3 -m pytest tests/test_cover_patterns.py -q`

Expected: FAIL because `cover-patterns-v1.json` does not exist.

- [ ] **Step 3: 采集并落库**

记录四张本地截图的字卡变体；再补充站内跨类目封面类型。每条 observation 保留入口、日期、可见互动、视觉结构、任务推断、混杂与 `public_proxy_observation` 标签。

- [ ] **Step 4: 写最小模式资产**

至少包含：黑底强调字卡、轻纸张/梗图字卡、荧光便签字卡、实拍主体+稀疏标题、结果前后对照、截图批注、清单/表格、PLOG/拼贴、产品/质感特写。每个模式必须有正向适用条件与防误用反例。

- [ ] **Step 5: 运行资产测试**

Run: `python3 -m pytest tests/test_cover_patterns.py -q`

Expected: PASS.

### Task 2: 精确选择封面模式

**Files:**
- Create: `redbook-writing/scripts/select_cover_pattern.py`
- Create: `tests/test_select_cover_pattern.py`

**Interfaces:**
- Consumes: `--job`、`--carrier`、`--materials`、`--visual-evidence-role`、可选 `--pattern-id`。
- Produces: JSON receipt with `status`, `selected_pattern`, `rejected_patterns`, `missing_materials`, `claim_ceiling`.

- [ ] **Step 1: 写失败测试**

```python
def test_real_scene_evidence_routes_away_from_text_card():
    result = select(job="decision_support", carrier="comparison_warning", materials={"owned_or_authorized_before_after"}, visual_evidence_role="primary")
    assert result["selected_pattern"]["pattern_id"] == "CP05"

def test_text_first_without_visual_evidence_prefers_text_card():
    result = select(job="feed_stop", carrier="text_card", materials={"truthful_serious_premise"}, visual_evidence_role="none")
    assert result["selected_pattern"]["family"] == "text_dominant_native_card"
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python3 -m pytest tests/test_select_cover_pattern.py -q`

Expected: FAIL because selector is missing.

- [ ] **Step 3: 实现最小选择器**

按硬门顺序执行：job/carrier exact match → contraindication → material gate → visual evidence role → priority rank。不得为了命中字卡而改写用户 job、carrier 或素材状态。

- [ ] **Step 4: 运行选择器测试**

Run: `python3 -m pytest tests/test_select_cover_pattern.py -q`

Expected: PASS.

### Task 3: 确定性字卡渲染器

**Files:**
- Create: `redbook-writing/scripts/render_text_card_cover.py`
- Create: `tests/test_render_text_card_cover.py`
- Create: `redbook-writing/assets/cover-render-examples/text-card-input.json`
- Create: `redbook-writing/assets/cover-render-examples/text-card-demo.png`

**Interfaces:**
- Consumes: JSON with `variant`, `headline`, `accent_terms`, `meta`, optional authorized `sticker_path`, `output_path`.
- Produces: valid 1080×1440 RGB PNG plus machine-readable layout receipt on stdout.

- [ ] **Step 1: 写失败测试**

```python
def test_renderer_outputs_decodable_xhs_portrait_png(tmp_path):
    output = tmp_path / "cover.png"
    run_renderer(output)
    with Image.open(output) as image:
        image.load()
        assert image.size == (1080, 1440)
        assert image.mode == "RGB"
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python3 -m pytest tests/test_render_text_card_cover.py -q`

Expected: FAIL because renderer is missing.

- [ ] **Step 3: 实现三种字卡变体**

实现 `black_accent_card`、`paper_meme_card`、`highlight_note_card`。共同保证安全区、缩略图字号、显式换行、一个强调色、最多两个强调词、真实文字渲染和素材缺失 fail closed。

- [ ] **Step 4: 运行测试并生成示例**

Run: `python3 -m pytest tests/test_render_text_card_cover.py -q && python3 redbook-writing/scripts/render_text_card_cover.py --input redbook-writing/assets/cover-render-examples/text-card-input.json`

Expected: PASS and `text-card-demo.png` is created.

- [ ] **Step 5: 视觉检查**

分别按信息流缩略图与全图检查：两秒可读、无孤字、无溢出、强调不超过两处、没有 PPT 式模块堆叠、没有复制样本账号元素。

### Task 4: 把模式库接入 Skill 路由与 README

**Files:**
- Modify: `redbook-writing/SKILL.md`
- Create: `redbook-writing/references/cover-pattern-library.md`
- Modify: `redbook-writing/references/draft-quality.md`
- Modify: `redbook-writing/references/style-research-and-generation.md`
- Modify: `README.md`
- Modify: `tests/test_asset_schemas.py`

**Interfaces:**
- Consumes: Task 1–3 的模式资产、选择器和渲染器。
- Produces: 封面请求的明确加载路由、选择顺序、生产命令、反例和状态上限。

- [ ] **Step 1: 写失败的路由断言**

```python
def test_skill_routes_cover_work_to_pattern_library_and_selector():
    skill = SKILL.read_text(encoding="utf-8")
    assert "cover-pattern-library.md" in skill
    assert "select_cover_pattern.py" in skill
    assert "render_text_card_cover.py" in skill
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `python3 -m pytest tests/test_asset_schemas.py -q`

Expected: FAIL on missing cover route.

- [ ] **Step 3: 写最小 Skill 补丁**

在 SKILL 只增加路由与硬门；完整分类、参数和反例放进 `cover-pattern-library.md`。README 增加“文字型默认字卡、视觉证据型不默认字卡”的用法和命令。

- [ ] **Step 4: 运行定向测试**

Run: `python3 -m pytest tests/test_cover_patterns.py tests/test_select_cover_pattern.py tests/test_render_text_card_cover.py tests/test_asset_schemas.py -q`

Expected: PASS.

### Task 5: 全量验证、自审与发布

**Files:**
- Modify: only files required by review findings.

**Interfaces:**
- Consumes: 完整 diff 和测试输出。
- Produces: 可安装 Skill、审查记录、Git commit、GitHub `main` 更新。

- [ ] **Step 1: 验证 Skill 结构**

Run: `python3 /Users/hermione/.codex/skills/.system/skill-creator/scripts/quick_validate.py redbook-writing`

Expected: validation succeeds.

- [ ] **Step 2: 运行完整测试**

Run: `python3 -m pytest -q`

Expected: all tests pass.

- [ ] **Step 3: 自审 diff**

检查四类问题：把代理互动写成因果、字卡全局默认、复制创作者识别元素、文档与机器资产不一致。修复后重跑相关测试。

- [ ] **Step 4: 提交并推送**

```bash
git add README.md docs redbook-writing tests
git commit -m "feat: add native cover pattern library"
git push origin main
```

Expected: remote `main` points to the new commit.

## 计划自审

- 需求覆盖：四张截图沉淀、补看其他封面、优先字卡、跨类目防误用、确定性生成、Skill 接入、测试、自审、GitHub 推送均有对应任务。
- 占位符检查：无 TBD/TODO/“之后补充”。
- 接口一致性：资产 ID、选择器输出、渲染器输入和文档路由使用同一命名。
