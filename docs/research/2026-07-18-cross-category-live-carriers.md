# 跨类目原生载体研究：安全续跑检查点

> 状态：`blocked_access`
> 研究日期：2026-07-18
> 研究模式：`refresh`（补足跨类目真实高/常态/低表现载体对照）
> 证据边界：公开互动仅记为 `public engagement proxy`，不可写成曝光、推荐或流量。

## 本轮问题

在不复用 `2026-07-17-live-xhs-style-observations` 的前提下，补足当前真实小红书图文/轮播的跨类目载体原型，并为每个候选寻找同账号、相近阶段、同 carrier、同 `primary_job` 的普通或低表现对照。优先覆盖：

1. 真实场景体验；
2. 前后改造；
3. 统一协议比较；
4. 截图/证据教程；
5. 关系/成长档案；
6. 纯文字代理/IP 卡。

## 访问检查点

- `run_id`：`RUN-20260718-CROSS-CATEGORY-LIVE-CARRIERS`
- `checked_at`：`2026-07-18T02:17:35+08:00`
- `mode`：`refresh`
- `round`：浏览器连接检查，尚未开始查询轮次
- `last_successful_query`：无
- `last_successful_url`：无
- `current_query`：无；准备接入主任务已经登录的小红书内置浏览器
- `trigger_signal`：子代理隔离环境返回 `Browser is not available: iab`；按故障文档检查一次后，可用浏览器列表仍为空
- `candidate_count`：0
- `focus_count`：0
- `deduplicated_new_sample_count`：0
- `saved_evidence`：本文件与同名 JSONL；未保存任何登录凭据或会话信息

## 已覆盖与缺口

- 已完成：读取研究方法、落库合同和既有 2026-07-17/18 样本索引；确认旧库已经覆盖聊天、截图教程、前后变化、关系档案和文字卡等线索，因此它们不能冒充本轮新增样本。
- 未覆盖：六类载体的新候选、高/常态/低对照、主页连续基线、逐页观察、发布日期与页面年龄、评论语义、跨账号复现。
- 置信度影响：本轮没有新增 observed 记录，不能形成任何视觉风格或表现关联结论。

## 证据来源分层

| 来源层 | 本文件实际收到什么 | 能支持什么 | 不能支持什么 |
| --- | --- | --- | --- |
| `root_task_context` | 研究目标、六类载体、只读约束，以及根任务存在已登录浏览器的运行上下文 | 定义本轮研究问题与安全边界 | 不是帖子证据；没有任何目标帖、对照帖、逐页记录或指标可以归因给根代理 |
| `old_local_observation` | `O-XHS-004/006/008/010/011/012` 及其 2026-07-18 审计文件 | 说明哪些旧线索已出现、哪些字段缺失、下一轮需去重什么 | 不能冒充 2026-07-18 本轮新增采集，不能刷新发布日期、互动、页面或账号基线 |
| `current_subagent_live_capture` | 0 条；尚未开始查询即遇到浏览器不可用 | 只支持访问状态检查点 | 不支持任何内容、审美或表现主张 |
| `derived_gap_audit` | 下表对旧记录的字段完整性判断 | 支持续跑优先级与 fail-closed 决策 | 不是新的站内观察，也不能提升旧证据等级 |

因此，本文件的新增信息只有“证据完整性审查”和“续跑合同”，没有新增小红书样本。

## 六类载体证据完整性审查

| Gap ID | 目标载体 / 旧类目线索 | 旧观察 | 旧页面覆盖 | 匹配普通/低帖 | 当前可保留角色 | 不可发布原因 | 当前状态 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `GAP-LIVE-01` | 真实场景体验 / 酒店→关系观点 | `O-XHS-010` | 单个 Live 首图；动态与完整素材未归档 | 无。旧 `BOUNDARY-O010-SAME-ACCOUNT-LOW` 没有可追溯 note ID，也没有同 carrier + 同 job 的逐页记录 | `task_fit`：真实场景只能作“在场/经历”锚点；标题、细节链和类比仍是待配对差异 | 缺账号 ID、29 条基线成员、目标排除收据、同 job 低帖、素材哈希、caption move 收据、分发状态 | `blocked_not_qualified` |
| `GAP-LIVE-02` | 前后改造 / 出租屋家居 | `O-XHS-008` | 仅 2/10 页 | 无可发布匹配。旧记录只称同系列多篇较低，没有保存低帖 note ID、日期、页面和 caption | `task_fit`：真实 before→过程/结果→成本；`anti_pattern`：AI 补造 before/after、只放精修结果 | 缺完整 10 页、28 条基线成员、相近阶段低帖、费用/过程位置、分发状态；跨约 7 个月窗口 | `blocked_not_qualified` |
| `GAP-LIVE-03` | 统一协议比较 / 智能家居 | `O-XHS-004` | 仅封面 1/? | 无。19 条账号基线只有中位数；没有成员、低帖 ID 或比较协议 | `task_fit`：比较任务可使用网格和明确比较轴；红黑、packshot、网格不是表现差异 | note ID 仅前缀、稳定 URL/账号 ID 缺失、内页未知、基线不可重算、没有 matched control | `blocked_not_qualified` |
| `GAP-LIVE-04` | 截图/证据教程 / iPhone 设置 | `O-XHS-006` | 仅 3/? 页 | 无。目标为 2025-12，主页基线主要来自 2026；没有低帖 ID | `task_fit`：一页一个路径、动作位置和结果；`anti_pattern`：红框和数量本身被写成流量按钮 | 缺末页、28 条基线成员、同周期低帖、系统版本/发布日期精度、页面哈希、分发状态 | `blocked_not_qualified` |
| `GAP-LIVE-05` | 关系/成长档案 / 周年关系 | `O-XHS-012` | 18/18 页完整观察，但无页面哈希 | 无匹配反例。17 页 PLOG `680fb4510000000023003a3c` 与目标 `primary_job` 不同，只能算 carrier boundary | `task_fit`：每页证明一个关系变化；`anti_pattern`：页数、白字、情侣照或统一滤镜被公式化 | 10 条基线缺成员 ID/日期；无同 job 低帖、独立账号、权利收据、评论语义和分发状态 | `blocked_not_qualified` |
| `GAP-LIVE-06` | 纯文字代理/IP 卡 / 成长关系随笔 | `O-XHS-011` | 高低 5 帖均为 1/1 单图；高低 caption move 未归档 | **唯一有可追溯同系列低帖 ID 的线索**：`6a548dad...`、`6a572b58...`、`6a3235ee...`；但缺高低正文差异收据和完整 28 条基线，仍不是可发布 matched contrast | `series_constant`：固定代理词、纯色字卡、长 caption；`contrastive_performance_hypothesis` 仅能候选为议题宽度、情绪后果、场景兑现 | 目标排除未证明、基线成员不全、caption 不能复核、无独立账号、曝光/分发/付费未知；公开互动不能变成流量结论 | `blocked_not_qualified` |

### 审查结论

- `qualified`：`0/6`。
- 有完整可追溯 matched control：`0/6`。
- 有 identifiable same-series low-post leads：仅 `GAP-LIVE-06`，但它仍缺“高低真正不同什么”的正文/叙事收据。
- 有完整逐页观察：仅 `GAP-LIVE-05`；完整页面不等于匹配反例或表现证据。
- 可作为生产问题使用的 `task_fit / series_constant / anti_pattern`：6/6 均可保留，但必须连同上表限制；不得进入 `qualified starter`、`performance rule` 或“爆款公式”。

## 可续跑字段 / 缺口表

下一次只补下列字段，旧值不得被覆盖；每条新记录先写 `capture_provenance=new_live_root_iab`，与 `old_local_observation` 分开。

| 字段组 | 必填字段 | 通过条件 | 缺失时状态 |
| --- | --- | --- | --- |
| 身份与时间 | `note_id`、稳定 URL、`account_id`、账号名、`published_ui`、`collected_at`、页面年龄、置顶/合作可见状态 | ID 完整；时间保留页面原文与精度；不可见项写 unknown | `identity_incomplete` |
| 公开指标 | 赞/藏/评原始 UI 字符串、组件是否完整、指标截取时间 | 原样保存，不拆万级近似，不合成“流量” | `public_proxy_only` |
| 目标内容 | 从封面到末页逐页记录九字段：`page_role/material/composition/hierarchy/text_density/annotation/imperfection/image_text_division/copy_move` | 可见全部页；缺页明确 `n/?`，不得推断末页 | `page_sequence_incomplete` |
| 账号基线 | 目标排除后成员的 note ID、日期、指标、carrier、job、页数、置顶、可比性、排除理由 | 至少 5 条可比成员且可重算中位数；目标排除可证明 | `baseline_unrecomputable` |
| 匹配低帖 | 同账号、相近账号阶段、同 carrier、同 `primary_job` 的普通/低帖；完整逐页与 caption move | 先写 shared constants，再写真实 feature contrast | `matched_control_missing` |
| 特征角色 | 每个特征只标 `series_constant / task_fit / contrastive_performance_hypothesis / anti_pattern` 之一 | 高低共同项只能是 constant；不同 job 只能是 boundary | `role_overclaimed` |
| 混杂 | 内容年龄、热点、作者信任、人物/空间吸引力、付费、外部分发、搜索长尾、产品节点 | 不可见写 unknown；不得省略强混杂 | `confounders_unresolved` |
| 权利与复用 | `rights_basis_code`、可复用范围、素材/页面哈希（私有清单）、真人/档案/截图授权状态 | 默认 `reference_only_no_reuse`；未授权不复制图、原句、人物或独特版式 | `rights_reference_only` |
| 跨账号复现 | 第二个独立账号的目标、基线与 matched low | 同一候选机制在独立账号复现后仍只能叫 public-proxy association | `independent_replication_missing` |
| 流量判定 | 自有一方 impressions/reach、入口、CTR/停留等；竞品通常不可得 | 无一方数据时固定 `traffic_verdict=unavailable` | `traffic_unavailable` |

建议续跑顺序：先补 `GAP-LIVE-03/04` 的完整身份与页序列，再补 `GAP-LIVE-01/02/05` 的同 job 低帖，最后深读 `GAP-LIVE-06` 高低 caption；优先级来自“最短缺口”，不是对哪类载体更容易爆的判断。

## 硬边界

本轮未切换到外部搜索、未尝试提取 Cookie/Token、未绕过登录、未点赞、收藏、关注、评论、私信或发布。没有把旧样本换 ID 后计作新样本，也没有为凑六类载体补造链接、互动或逐页结构。

## 安全续跑点

在主任务可访问的已登录内置浏览器中继续，先从搜索结果找新笔记，再反查作者主页；每个载体至少保存：

- 目标帖 URL、note ID、账号、可判发布日期/页面年龄、原始公开互动字符串；
- 同账号排除目标后的连续普通样本成员，逐条保留 ID、日期、公开指标、carrier、`primary_job` 与可比性；
- 至少一条同 carrier、同 `primary_job`、相近阶段的普通/低表现对照；
- 从封面到末页的 `page_role / material / composition / hierarchy / text_density / annotation / imperfection / image_text_division / copy_move`；
- `series_constant / task_fit / contrastive_performance_hypothesis / anti_pattern` 分层；
- `paid_status / external_distribution / exposure` 不可见时一律写 unknown；公开互动不得升级为流量判定。

遇到登录墙、验证码、人机验证、频率提示或循环跳转，应在本文件追加最后成功查询、URL、样本数和触发原文后停止，不重试、不换入口。
