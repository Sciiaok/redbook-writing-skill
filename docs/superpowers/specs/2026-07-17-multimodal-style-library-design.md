# 小红书爆款风格学习与生成闭环设计

## 目标

升级 `redbook-writing` Skill，让类目研究同时学习高表现笔记的视觉、文字和内容载体；生成稿必须引用可追溯的风格原型与对照样本。没有匹配风格证据时，Skill 停在 `needs_style_research`，不得凭“小红书风”想象出一套规整 PPT。

第一版只覆盖图文与轮播。视频只记录封面、标题、正文与基础表现，不做逐镜风格建模。

## 问题诊断

现有研究已经保存标题、互动、hook、逐页任务和 `cover_mechanism`，但没有保存以下对象：

- 每一页实际画面及其哈希；
- 可观察的布局、文字密度、素材、颜色与装饰；
- 图片内文字和正文之间的分工；
- 句长、换行、标点、人称、语域与叙事推进；
- 高表现样本与同账号普通/低表现样本的风格差异；
- 生成稿实际使用了哪些风格规则和参考样本。

因此 `draft` 只能从“轮播、聊天记录、封面方向”等抽象词自由发挥。常见结果是渐变背景、均匀卡片、图标矩阵、统一圆角与阴影、每页结构完全相同。这些设计整齐，但缺少小红书常见的真实素材感、信息节奏和局部不规则性。

## 设计原则

1. **先观察，再归纳。** 原始记录只写看见的事实；“低饱和日记型”等风格名称属于跨样本归纳。
2. **爆款不是绝对高赞。** 优先使用同账号近期可比基线和异常倍数，保留账号规模、投放、热点与发布时间等混杂。
3. **只看高表现不够。** 每个可复用风格原型同时保留普通/低表现或质疑样本，用于区分常见装饰和可能有用的差异。
4. **一次只选一个主风格。** 生成稿绑定一个 primary archetype；可选一个 secondary archetype 补充单一技巧，不混成“风格大杂烩”。
5. **学习语法，不复制作品。** 不复刻原帖人物、原图、原句、独特插画或完整构图；输出保留来源 ID 与有意偏离项。
6. **原图本地保存。** 第三方截图不提交公开仓库，不写入 SQLite BLOB；数据库只保存本地路径、哈希、来源与特征。
7. **结构门和审美门分开。** 机器验证引用、状态和完整性；视觉自然度仍需要基于样本的 creative review。

## 范围

### 第一版包含

- 全站高表现图文/轮播风格池；
- 当前类目高表现图文/轮播风格池；
- 同账号普通/低表现对照；
- 逐页图片、OCR、视觉特征、文字特征与载体逻辑；
- 本地 SQLite 长期风格库；
- 风格原型的建立、查询、状态升级和退役；
- `draft` 的风格检索、引用合同和 anti-PPT 审校；
- 样本不足时的停止状态；
- 结构验证、单元测试、集成测试与高风险前向评测。

### 第一版不包含

- 无人值守批量爬虫、登录绕过、验证码处理或反风控；
- 视频逐镜抽取与视频生成；
- 独立设计软件、Figma 插件或完整图片渲染器；
- 根据视觉特征推导平台因果或稳定爆款率；
- 将第三方原图、完整正文或评论语料提交到公开仓库；
- 模仿单一创作者的可识别个人风格；
- 自动发布、点赞、评论或私信。

## 备选方案与选择

### 方案 A：只扩充 Prompt 和 Markdown 参考

在 `draft-quality.md` 增加版式、配色、语气提示。改动最小，但无法保证每次研究都采集风格，也不能验证生成稿是否真的引用了样本。

结论：不采用。

### 方案 B：SQLite 风格库 + Skill 硬门 + 检索合同

保留现有 run 目录和 CSV 审计链，增加本地 SQLite 风格库、逐页特征、风格原型和 draft 引用。验证器检查结构，creative review 检查视觉自然度。

结论：采用。它解决当前问题，又不把 Skill 变成独立设计产品。

### 方案 C：同时开发模板与图片渲染引擎

除方案 B 外，再实现 HTML/Canvas/Figma 等渲染系统。可控性更高，但会把本次工作扩成设计工具项目，且模板仍可能固化成另一种 PPT。

结论：本期不做。风格学习闭环稳定后再单独评估。

## 总体流程

```text
查询树与候选笔记
        ↓
全站高表现 + 当前类目高表现 + 同账号对照
        ↓
逐页保存图片 / OCR / 正文 / 表现 / 账号基线
        ↓
visual observations + copy observations
        ↓
跨账号归纳 style archetype + counterexamples
        ↓
draft 按 category × carrier × primary_job × constraints 检索
        ↓
风格选择合同 + 逐页内容/视觉 brief + 文字稿
        ↓
相似度检查 + anti-PPT review + compliance review
        ↓
ready / needs_style_research / needs_revision
```

## 存储架构

### 仓库内

仓库提交：

```text
redbook-writing/
├── assets/style-library-schema.sql
├── references/style-research-and-generation.md
└── scripts/style_library.py
```

仓库只保存 Schema、方法、脚本、空模板和合成测试 fixture，不保存第三方帖子原图或完整文案。

### 用户工作区

运行时创建：

```text
research/xiaohongshu/_style_library/
├── style-library.sqlite
├── raw/                         # 本地原图，默认 gitignored
│   └── <sha256>.<ext>
├── derived/                     # OCR、缩略图或安全派生物
│   └── <sha256>.json
└── exports/                     # 可读风格卡和查询结果
```

SQLite 不存图片 BLOB。每个 asset 保存来源 URL、采集时间、本地相对路径、SHA-256、宽高、访问状态和授权/版权备注。

每次 run 继续保存 `accounts.csv`、`posts.csv`、`topics.csv` 和 draft。Run 文件通过 ID 指向长期风格库，避免另建一套互不相认的数据源。

新 discovery/refresh run 另存 `style-samples.csv`，它不是第二份特征库，而是本轮“哪些入选帖子已经完成逐页风格采集”的审计清单：

```text
style_sample_id,post_id,query_ids,performance_tier,carrier,primary_job_scope,slide_count_visible,slide_count_captured,visual_observation_ids,copy_observation_ids,archetype_ids,evidence_role,capture_status,limitations
```

- `capture_status` 只允许 `complete | partial | blocked | excluded`；
- `evidence_role` 只允许 `support | counterexample | boundary | unassigned`；
- 每个被 `query-log.csv.selected_post_ids` 选中的图文/轮播高表现样本和同账号对照，必须有且只有一行 manifest；
- `complete` 必须能在 SQLite 中解析到帖子、所有可见页以及所需 visual/copy observation；
- `partial/blocked` 必须写真实限制，不能被用于升级原型或放行 ready draft；
- `query-log.csv` 追加 `selected_style_sample_ids,new_style_patterns,style_capture_result`，以便区分“发现了帖子”和“完成了风格学习”；旧 run 不追溯补造。

### 数据所有权与同步

- Run CSV 是“这次为什么选择这些样本”的审计原件；
- `style-samples.csv` 是“这次入选样本是否完成逐页采集”的审计 manifest；
- SQLite 是跨 run 复用的风格观察与原型库；
- `post_id`、`account_id`、`query_id` 沿用 run 中的稳定 ID，不在 SQLite 另造同义 ID；
- 导入 SQLite 时保存 `run_id` 和原始 CSV SHA-256；后续数据变化追加 observation，不覆盖历史表现；
- draft 同时在 frontmatter 和 `draft_style_bindings` 保存风格引用，二者不一致时验证失败；
- Schema 使用 `PRAGMA user_version` 迁移，观察记录保存 `taxonomy_version`，旧记录不会静默套用新分类。

## SQLite 数据模型

### `style_assets`

一行代表一份本地原始或安全派生资产；数据库不接受二进制内容：

```text
asset_id PK
source_url
asset_path
asset_sha256 UNIQUE
mime_type
width
height
collected_at
access_status
observation_method
copyright_notes
```

`asset_path` 必须是风格库目录下的相对路径，且只能指向 `raw/` 或 `derived/`。Schema 与 CLI 都拒绝 BLOB、目录穿越和库外绝对路径。

### `style_posts`

一行代表一篇内容身份；互动表现不写在此表：

```text
post_id PK
note_id
url
account_id
category
published_at
format
caption_text
caption_sha256
status
```

### `style_post_observations`

一行代表某次采集时的表现与入口快照：

```text
post_observation_id PK
post_id FK
run_id
source_csv_sha256
collected_at
visible_engagement
account_baseline_multiple
performance_tier
queries_matched
search_surface
sort_or_filter
known_confounds
```

`performance_tier` 只允许 `high | ordinary | low | unknown`。它是本次研究的比较标签，不是平台官方等级。没有可比基线时可保留 `unknown` 或候选高表现，不得用绝对互动直接升级风格证据。同一帖子重新采集时追加 observation，不改写旧快照。

### `style_slides`

一行代表一页轮播或一张封面：

```text
slide_id PK
post_id FK
slide_index
slide_role
asset_id FK
ocr_text
ocr_confidence
access_status
observation_method
taxonomy_version
```

`slide_role` 使用 `cover | scene | context | evidence | comparison | step | boundary | transition | summary | cta | other`。缺页必须记录 `access_status=missing/partial`，不能根据相邻页补写。

### `visual_observations`

每页只记录可观察特征：

```text
visual_observation_id PK
slide_id FK
composition
dominant_material
background_type
subject_presence
crop_and_subject_ratio
layout_structure
text_zones
text_density
hierarchy_levels
alignment
spacing_pattern
palette
font_feel
decoration_types
annotation_style
imperfection_signals
image_text_relationship
evidence_level
taxonomy_version
notes
```

第一版不要求计算机视觉模型。Agent 必须打开图片后记录；OCR 或自动颜色提取只作为辅助，`observation_method` 与置信度必须外显。

### `copy_observations`

按帖子或页面记录文字风格：

```text
observation_id PK
post_id FK
slide_id nullable FK
text_surface
point_of_view
audience_address
register
sentence_length_pattern
line_break_pattern
punctuation_pattern
emoji_pattern
diction_markers
hook_move
narrative_moves
evidence_move
payoff_move
cta_move
image_caption_division
quoted_fragments_hash
evidence_level
taxonomy_version
notes
```

`quoted_fragments_hash` 用于检测不当复用，不在公开导出中保存长段原文。评论只提取匿名化语言模式和需求类型，不存无关身份信息。

### `style_archetypes`

一行代表可复用风格原型：

```text
archetype_id PK
name
category_scope
carrier
primary_job_scope
audience_state
description
cover_rules_json
slide_rhythm_json
visual_rules_json
copy_rules_json
material_requirements_json
anti_patterns_json
production_cost
confidence
status
created_at
updated_at
taxonomy_version
```

`status` 只允许：

- `candidate`：单一或不足以泛化的样本；
- `supported`：至少两个独立账号的高表现样本，并有独立对照/反例；
- `reusable`：至少三个独立账号、两个查询/排序环境重复出现，且无重大未解释冲突；
- `stale`：时间窗已过或近期证据不足；
- `deprecated`：反例、规则或效果学习表明不再使用。

这些数量是 Skill 的研究门槛，不是平台规律。

### `style_archetype_evidence`

连接风格原型与证据：

```text
archetype_evidence_id PK
archetype_id FK
post_id FK
slide_id nullable FK
evidence_role
observed_feature
account_id
query_id
performance_tier
account_baseline_multiple
limitations
```

`evidence_role` 只允许 `support | counterexample | boundary`。同一 post/slide 不能同时充当支持与反例。

### `draft_style_bindings`

保存生成稿实际使用的风格：

```text
draft_binding_id PK
draft_id
archetype_id
binding_role
reference_post_ids
counterexample_post_ids
visual_rules_used_json
copy_rules_used_json
material_plan_json
intentional_deviations_json
anti_patterns_checked_json
retrieved_at
review_status
```

`binding_role` 只允许 `primary | secondary`。每份 draft 必须恰好一个 primary；secondary 最多一个，且只能补充一个明确技巧。

## 爆款与对照样本选择

样本池由三部分组成：

1. 全站高表现样本：学习当前平台常见视觉与载体；
2. 当前类目高表现样本：学习目标人群、素材和语言；
3. 同账号普通/低表现对照：排除账号体量和个人风格混杂。

优先级：

```text
同账号可比异常倍数
→ 同类目、同载体、同时间窗的相对高表现
→ 只有绝对互动的候选样本
```

绝对高赞、搜索靠前、首页推荐、明星账号、旧置顶、投放、抽奖或热点事件不能独立定义爆款风格证据。每个判断继续保留采集入口、时间、可见指标与限制。

### 查询到入库的完成条件

一次搜索不以“看过结果页”为完成。对于写入 `selected_post_ids` 的图文/轮播样本，必须依次完成：

```text
posts.csv 内容身份与表现快照
→ style-samples.csv manifest
→ 原图/页面访问状态与哈希
→ 可见页 slide 记录
→ visual/copy observations
→ support/counterexample/boundary 角色
→ query-log.csv style_capture_result
```

`style_capture_result` 只允许 `complete | partial | blocked | not_required`。选中样本存在但 manifest 或 SQLite 引用缺失时只能写 `partial/blocked`，该查询不能计入风格饱和停止条件。

## 风格抽取方法

### 视觉层

逐页回答：

- 这页用什么真实素材承载信息；
- 第一眼先看到什么，第二层是什么；
- 文字占多少、落在哪些区、层级差如何建立；
- 是否使用整齐网格，哪些地方故意不齐；
- 背景是照片、纸张、截图、纯色、纹理还是界面；
- 人物、手部、物品和环境如何出现；
- 圈画、箭头、贴纸、马赛克、手写或系统 UI 是否有信息作用；
- 这一页与前后页如何形成节奏。

不使用“高级、松弛、氛围感”作为唯一描述。主观词必须落到可观察特征。

### 文字层

分别观察标题、图片内文字和正文：

- 谁在说话，对谁说；
- 开头是命名场景、提出矛盾、直接给答案还是展示证据；
- 句子长短、换行、标点和 emoji 如何变化；
- 使用生活口语、行业词、解释语还是销售语；
- 每一段如何推进，而不是只统计关键词；
- 事实、经历、判断和建议如何区分；
- 图片内文字承担信息，正文补充什么；
- 结尾如何收束，是否存在强行互动或导流。

### 内容载体层

风格原型必须带 `carrier`，至少区分：

- 实拍日记；
- 实拍加注释；
- 截图圈画；
- 聊天/对话演绎；
- 文字卡；
- 清单/步骤；
- 对比/避坑；
- 拼贴/手账；
- 单图提醒。

载体由信息任务和可用素材决定，不因某一载体曾高表现就迁移到所有题目。

## 生成时的检索合同

`draft` 开始前，按以下键查询：

```text
category
carrier
primary_job
audience_state
production_constraints
available_materials
```

检索优先级：

```text
当前类目 × 同载体 × 同 primary_job
→ 当前类目 × 同载体
→ 全站 × 同载体 × 同 primary_job
→ 无合格结果：needs_style_research
```

只允许 `supported` 或 `reusable` 作为 primary archetype。`candidate` 可提示补采，不能放行 ready 稿。

生成前必须输出并落库：

```text
style_archetype_id
style_reference_post_ids
style_counterexample_post_ids
visual_rules_used
copy_rules_used
material_plan
slide_map
intentional_deviations
anti_patterns
```

缺少任一核心引用时，生成内容可以保持 `needs_style_research`，不得写 `ready` 或“可直接发布”。

### Run 与 draft 字段

`run.yaml` 增加：

```yaml
style_requirement: both  # none | copy | visual | both
style_library_path: ../_style_library/style-library.sqlite
style_taxonomy_version: 1
```

所有相对路径统一相对 run 目录解析，避免依赖调用脚本时的当前工作目录。`mechanism` 默认 `none`；新 discovery/refresh 默认 `both`；只交付标题/正文的 draft 为 `copy`；封面、轮播或图片交付使用 `visual` 或 `both`。旧 run 缺字段按 legacy 处理，但一旦修改为 complete/ready 就必须迁移。

Draft frontmatter 增加：

```yaml
style_requirement: both
style_library_path: ../_style_library/style-library.sqlite
style_taxonomy_version: 1
primary_style_archetype_id: STYLE-001
secondary_style_archetype_id: none
style_reference_post_ids: POST-001;POST-002
style_counterexample_post_ids: POST-003
style_binding_status: grounded
```

`style_binding_status` 只允许 `grounded | needs_style_research | needs_revision`。Draft 状态为 `ready` 时必须是 `grounded`，且 SQLite 引用、frontmatter 与正文中的风格合同完全一致。

当 `style_binding_status=needs_style_research` 时，draft 顶层 `status` 必须是 `needs_review` 或 `blocked`；只输出缺口、补采查询与素材需求，不得附带看似可直接发布的完整视觉稿。该状态不是换个名字继续生成。

## Draft 生成行为

1. 先完成风格检索，再生成标题、正文和逐页方案。
2. 视觉指令必须逐页写素材、层级、排版、文字密度、与前后页关系；禁止只写“简洁高级、小红书风”。
3. 文案必须应用检索到的语气与节奏规则，同时保留事实、授权和商业披露合同。
4. 图片内文字与正文分别写，避免把同一段文字复制到两个表面。
5. 使用现有图片能力时，先用风格原型形成 prompt/brief；不得把单篇第三方帖子当成待复刻模板。
6. 文本密集页不得要求生成模型直接绘制长段中文；应生成素材/背景与可排版文字说明，实际工具允许时使用确定性排版。
7. 生成后记录有意偏离项，避免把跨帖子共性误写成必须全部照做。

## Anti-PPT 审校

Creative review 新增以下检查：

- 是否无依据地使用渐变背景、企业蓝紫色、发光效果或 3D 图标；
- 是否每页都是相同圆角卡片、相同居中标题和相同阴影；
- 是否用图标矩阵代替真实素材、截图、人物或场景；
- 是否所有元素过度对齐、过度等距，缺少参考样本中的自然密度变化；
- 是否把正文拆成“标题 + 三个要点 + 总结”式演示文稿；
- 是否页面之间没有节奏变化；
- 是否声称“小红书感”，却没有引用任何 visual/copy observation；
- 是否复制了单篇帖子独特构图、原句、人物或插画。

每项给出 `PASS | PARTIAL | FAIL` 与对应参考 ID。任一复制风险或无风格证据为 FAIL；明显 PPT 模式为 PARTIAL/FAIL，修订后重新审查。

## 抄袭与隐私边界

- 不在公开仓库提交第三方原图、完整正文、用户名、头像或无关评论身份；
- 不使用单篇帖子作为完整设计模板；
- 标题、正文和图片内文字与来源做连续词组/片段重合检查；
- 只保留短小、必要的观察片段或哈希，长文存本地受控材料；
- 生成稿不得复用独特人物、地点、订单、聊天身份或可识别经历；
- 参考来源仍需保留 URL、采集时间和用途。

## 状态与错误处理

| 情况 | 状态/动作 |
| --- | --- |
| 登录失效、验证码或频率限制 | 保存续跑点，停止访问，不重试绕过 |
| 轮播缺页 | slide 标 `partial/missing`，不补写缺失特征 |
| OCR 低置信度 | 保留原图路径，文字字段标 unknown，不推断 |
| 只有绝对高赞，没有账号基线 | 样本可进 candidate，不能单独升级原型 |
| 风格只来自一个账号 | archetype 保持 candidate |
| 没有匹配的 supported/reusable 原型 | draft 标 `needs_style_research` |
| SQLite 不可读或引用断裂 | fail closed；保留 run 日志和修复说明 |
| 风格规则与当前平台规则冲突 | 规则优先，原型 stale/deprecated |

## 兼容性

- `mechanism` 模式无需风格库；
- 旧 discovery/refresh run 仍可验证，但不会自动具备风格证据；
- 新 draft 若用户要求标题、正文、封面、轮播或图片，必须绑定风格原型；
- 纯事实机制回答不触发风格门；
- 旧 draft 可保持历史状态，修改为 ready 前必须迁移新合同。

## 文件改动范围

预计实施涉及：

- `redbook-writing/SKILL.md`
- `redbook-writing/references/research-method.md`
- `redbook-writing/references/draft-quality.md`
- `redbook-writing/references/schemas.md`
- 新增 `redbook-writing/references/style-research-and-generation.md`
- 新增 `redbook-writing/assets/style-library-schema.sql`
- 新增 `style-samples-template.csv`
- 更新 `query-log-template.csv`、`posts-template.csv`、`draft-template.md`、`run-template.yaml`
- 新增 `redbook-writing/scripts/style_library.py`
- 更新 `redbook-writing/scripts/validate_run.py`
- 新增/更新测试 fixture、单元测试与前向评测场景
- 更新 `.gitignore` 与 `README.md`

### `style_library.py` 命令接口

脚本只使用 Python 标准库 `sqlite3`，提供稳定的非交互命令：

```text
style_library.py init <db>
style_library.py ingest-run <db> <run-dir>
style_library.py upsert-slide <db> --record <json>
style_library.py upsert-visual <db> --record <json>
style_library.py upsert-copy <db> --record <json>
style_library.py upsert-archetype <db> --record <json>
style_library.py query <db> --category ... --carrier ... --primary-job ...
style_library.py bind-draft <db> --draft <path> --record <json>
style_library.py export-card <db> <archetype-id>
style_library.py validate <db>
```

所有写入接收 JSON 文件或标准输入，不把自由文本拼进 SQL。命令返回结构化 JSON 和非零错误码，便于 Skill 与测试复用。`query` 返回匹配理由、支持样本、反例、规则和限制，不只返回 style ID。

`ingest-run` 必须先校验 `style-samples.csv` 与 query/post 引用图，再在单个事务中写入；任何断链都回滚。重复导入同一 `run_id + source_csv_sha256` 为幂等操作；同一帖子后续重新采集则追加 observation，不覆盖历史快照。

## 验证策略

### 结构测试

- SQL Schema 可重复初始化；
- 外键、枚举、唯一约束和状态升级正确；
- 同一 evidence 不能同时支持与反证；
- raw asset 使用相对路径和 SHA-256，不接受 BLOB；
- query、post、style-sample、slide 与 observation 能双向对账；
- 重复 ingest 幂等，断链 ingest 整体回滚；
- draft 必须恰好一个 primary archetype；
- candidate archetype 不能放行 ready；
- 缺风格库、缺引用或断链时正确停止。

### 行为测试

新增前向场景：

1. 有充分样本的图文 draft：必须检索并引用风格原型；
2. 零风格样本 draft：必须返回 `needs_style_research`，不得给通用 PPT 方案；
3. 只有单账号高赞：原型保持 candidate；
4. 高表现与低表现对照：结论必须限定差异，不写平台因果；
5. 单篇原帖要求“照着做”：拒绝近似复刻，保留抽象规则；
6. anti-PPT：识别无证据的渐变、卡片矩阵和三段式页面；
7. 文风 grounded：必须引用 copy observations，不能杜撰口头禅。

### 人工视觉审查

机器测试不能证明“好看”。每个高风险视觉 fixture 还要按以下维度人工审查：

- 与目标载体是否匹配；
- 真实素材感是否成立；
- 信息层级和页面节奏是否接近参考原型；
- 图片内文字与正文是否分工；
- 是否出现 AI/PPT 常见模式；
- 是否与单一来源过度相似。

每项必须给具体页面和参考 ID，不能只给“更像小红书”的主观结论。

## 验收标准

1. Discovery/refresh 能把图文或轮播逐页写入本地风格库，并保留来源、哈希、观察方法和置信度。
2. 每个查询选中的高表现/对照样本都能通过 `query-log → posts → style-samples → SQLite` 对账；缺页和阻断可见且不冒充完成。
3. 风格库同时保存视觉、文风、内容载体、高表现证据和独立对照。
4. Draft 在生成前按类目、载体、primary job 与生产条件检索，且输出可追溯风格合同。
5. 没有 supported/reusable 风格原型时不能产出 ready 稿。
6. 每页视觉指令具体到素材、层级、排版、文字密度和页面节奏。
7. 文案应用有证据的句式、语域和叙事推进，不复用原句或杜撰口头禅。
8. Anti-PPT、近似复制和引用断裂会阻断发布状态。
9. 原始第三方图片与正文不会进入 Git 追踪文件。
10. 现有 84 项测试继续通过，新测试与前向评测全部通过。
11. README 能让用户理解风格如何采集、检索、生成和审校。

## 后续阶段

本设计完成后再评估两项独立工作：视频逐镜风格学习；基于稳定原型的确定性图片渲染。它们不进入本次实现。
