# 落库 Schema 与引用合同

本文件是运行目录的数据合同。字段名必须与 `scripts/validate_run.py` 一致；可以追加新字段，但不要改名、删必填字段或把多个概念塞进一个自由文本列。

导航：[目录与 ID](#目录结构) · [运行与证据账本](#runyaml) · [账号帖子选题](#accountscsv) · [渠道与资格](#acquisition-channelscsv) · [成稿合同](#draftsmd) · [引用图](#引用图)

## 目录结构

默认运行目录：`research/xiaohongshu/<YYYY-MM-DD>-<category>/`

```text
<run>/
├── run.yaml
├── research.md
├── query-log.csv
├── source-log.csv
├── claim-ledger.csv
├── accounts.csv                 # discovery / refresh
├── posts.csv                    # discovery / refresh
├── topics.csv                   # discovery / refresh / draft
├── acquisition-channels.csv     # 涉及渠道时
├── sku-registry.csv             # 涉及商品时
├── offer-registry.csv           # 涉及非SKU内容/服务/订阅时
├── authorization-log.csv        # 涉及真人、投稿、聊天或案例材料时
└── drafts/
    └── <draft-id>.md             # draft
```

`mechanism` 需要前五个公共文件；`discovery/refresh` 另需账号、帖子、选题；`draft` 另需选题和至少一篇成稿。即使复用历史证据，也把本次使用的来源/主张行复制或稳定引用到运行目录，使交付可独立审计。

## ID 与多值规则

- 推荐前缀：`RUN-`、`Q-`、`OFF-/TECH-/ACA-/IND-`、`CLM-`、`ACC-`、`POST-`、`TOPIC-`、`DRAFT-`、`CH-`、`SKU-`、`OFFER-`、`AUTH-`。
- ID 在同一文件内唯一；`eligibility_id` 在 SKU 与 offer 两个 registry 之间也全局唯一。
- 多值字段使用分号 `;`，不要用中文顿号或自由文本混合 ID。
- URL 使用稳定的 `http(s)` 原始页面。账号按主页 ID/URL 去重；笔记按 note ID/URL 去重。
- 同一笔记被多个搜索命中时合并到一行，把路径写入 `queries_matched`。
- 近重复不直接删除；使用 `duplicate_of` 或 `cluster_id` 关联。

## run.yaml

顶层至少包含：

```yaml
run_id: RUN-20260716-001
mode: discovery
status: in_progress
created_at: 2026-07-16
category: "类目"
target_audience: "目标用户与具体处境"
primary_goal: "本次要回答的问题"
commercial_goal: "none | 具体商业目标"
window_start: 2026-06-16
window_end: 2026-07-16
assumptions: []
limitations: []
```

允许模式：`mechanism | discovery | refresh | draft`。允许状态：`in_progress | complete | blocked`。只有公共数据集和该模式必需数据集均非空、成稿合同完整时才写 `complete`；权限或规则阻断写 `blocked`，未完成写 `in_progress`，不能用自定义近义词绕过完成门。`assumptions` 写模型采用的默认值，`limitations` 写登录、样本、日期、字段和后台不可见等真实缺口；二者不能省略。

验证器成功时分别输出 `VALID_IN_PROGRESS`、`VALID_BLOCKED` 或 `VALID_COMPLETE`；前两者只说明当前检查点内部一致，不能对外声称研究或成稿完成。

## query-log.csv

精确表头：

```text
query_id,platform,query,search_surface,sort_or_filter,run_at,result_count,selected_source_ids,selected_account_ids,selected_post_ids,new_valid_accounts,new_content_patterns,notes
```

- `search_surface`：web、notes、users、topics、comments、official_help 等。
- `sort_or_filter`：综合/热门/最新/图文/视频等，保留页面真实口径。
- `result_count` 不可见时留空，不估算。
- `new_valid_accounts` 与 `new_content_patterns` 用于停止条件；只有按统一定义判断后填写。
- 失败、登录墙、验证码、结果污染和个性化限制写入 `notes`，不要删除该查询。

## source-log.csv

```text
source_id,source_layer,platform,source_type,title,author_org,published_at,collected_at,url,query_id,access_status,evidence_form,evidence_grade,notes_file
```

- `source_layer`：official、engineering、academic、industry、creator_experience、rumor。
- `access_status`：full、partial、snippet_only、blocked、dead_link。
- `evidence_form`：official_page、pdf、paper、report、backend_screenshot、post、interview 等。
- `evidence_grade`：A/B/C/D；等级衡量证据，不衡量结论是否喜欢。
- `published_at` 接受 `YYYY`、`YYYY-MM` 或 `YYYY-MM-DD`，不明可空；不要补造日级精度。`collected_at` 必须为 `YYYY-MM-DD`。
- 页面失效或被弃用也保留，更新状态与笔记，避免以后重复踩坑。

## claim-ledger.csv

```text
claim_id,category,claim_text,source_ids,counter_source_ids,evidence_grade,claim_status,scope,confidence_reason,skill_action,last_verified_at,verification_class
```

- `claim_text` 写一个可判断真假的规范化主张，不写长段总结。
- `source_ids` 与 `counter_source_ids` 必须指向 source log。
- `claim_status`：`confirmed | supported_experience | hypothesis | contradicted | unknown`。
- `verification_class` 是强制枚举，不从自由文本 `category` 猜：`current_runtime | historical_research | mechanism_evidence | experience | hypothesis`。涉及当前平台规则、法律、资格、产品能力或政策变化时必须选 `current_runtime`；“本轮未确认某当前能力”的负向边界也属于 current_runtime/unknown。它强制本次运行日的可访问官方来源，不能借自由 category、否定前缀或 `experience` 规避。
- `scope` 精确到时间、产品模块、入口、内容/商业面；禁止只写“全平台”。
- 主张的 `evidence_grade` 不得高于其最佳支持来源；多条弱来源不会自动合成为 A 级。
- C/D 级来源不得把主张标为 `confirmed`；D 级不得升为 `supported_experience`。
- `skill_action` 写“允许怎样说/必须怎样测试/必须阻断”，不写流量承诺。
- `current_runtime` 主张每次运行复核 `last_verified_at`，且支持来源本次重新采集；历史论文不能单独确认当前规则。

## accounts.csv

```text
account_id,account_name,profile_url,head_type,follower_count,window_start,window_end,recent_sample_n,recent_median_visible_engagement,recent_max_visible_engagement,outlier_multiple,audience_evidence,commercial_distance,collected_at,source_ids,confidence,status
```

- `head_type`：scale、recent_performance、audience_precision、commercial_adjacent，可多值。
- `follower_count` 和公开互动不可见时留空；不要补零。但字段不可见时不能把该账号标为 `scale`。
- `recent_sample_n` 只计算窗口内连续可判日期样本。
- `outlier_multiple = recent_max / recent_median`；中位数为 0 或字段不可比时留空。
- `audience_evidence` 写简介、反复议题、评论问题等公开证据，不根据头像/姓名推断身份。
- `source_ids` 必须回指 source log；主页 URL 本身不能替代查询与采集证据。
- `commercial_distance`：far、adjacent、near、direct；与内容质量分开。
- `status`：candidate、focus、excluded、stale，并在研究文档解释排除原因。
- `focus` 或 `high` confidence 不能使用 0 条近期样本。`candidate/focus + recent_performance` 必须同时有正数 `recent_sample_n`、有限非负数 median/max/outlier，且 max 不得小于 median；指标不可比或中位数为 0 时移除 `recent_performance`，不要用空字段、NaN 或 Inf 完成“表现头部”调研。`outlier_multiple` 必须等于可比公开指标的 max/median。

## posts.csv

```text
post_id,note_id,title,url,account_id,published_at,date_confidence,collected_at,queries_matched,search_surface,sort_or_filter,rank_observed,format,visible_engagement,engagement_breakdown_available,account_baseline_multiple,hook,page_or_scene_structure,need_signal,cover_mechanism,evidence_level,confidence,duplicate_of,cluster_id,status
```

- `date_confidence`：high、medium、low、unknown。含混相对日期不得纳入严格 7/30 天结论。
- `rank_observed` 只是当时当前环境的位置，不叫平台排名。
- `visible_engagement` 原样保存页面显示；合并数不拆分。
- `account_baseline_multiple` 只在同账号、同一公开指标可比时计算。
- `active` 选题引用的 observed/calculated 帖子必须同时有可见互动记录和数值型 `account_baseline_multiple`；没有表现指标的需求材料只能支撑 `experimental`，不能冒充高表现证据。
- `page_or_scene_structure` 逐页/逐场景记录任务，不只抄正文摘要。
- `need_signal` 区分求方法、分享经历、反对质疑、询问商品、泛泛夸赞。
- `evidence_level`：observed、calculated、inferred、hypothesis。
- `status`：active、excluded、stale；排除不等于删除。

## topics.csv

```text
topic_id,topic,primary_job,entry_surface,target_audience,specific_scenario,core_promise_or_tension,evidence_ids,counterexamples,lifecycle,format,format_reason,commercial_distance,rule_scopes,measurement_plan,hypothesis_id,priority,status,last_seen_at
```

- `primary_job`：recommendation_reach、search_capture、relationship_building、commercial_conversion。
- `evidence_ids` 可以引用 source、claim、account、post；必须至少指向实际样本。
- `experimental` 至少引用一个可访问的需求/访谈/评论/内容样本；官方规则或机制来源本身不能生成选题。`active` 至少引用两个不同、可追溯账号在本次窗口内的 active observed/calculated 帖子；不足则保持 `experimental`。
- `counterexamples` 写独立反例 ID 与其否定的范围，不写“暂无”；同一 ID 不能同时出现在 `evidence_ids` 和反例中。
- `lifecycle`：hot、periodic、evergreen_search。
- `measurement_plan` 至少包括主指标、可用代理、观察窗口、失败层级、下一次单变量。
- `status`：experimental、active、deprecated；旧选题降级，不静默删除。

## acquisition-channels.csv

```text
channel_id,direction,platform,account_scope,audience_state,channel_role,native_format,source_asset_id,public_identity,eligibility_ids,surfaces,permitted_cta,prohibited_cta,landing_asset,primary_metric,metric_availability,data_source,event_definition,diagnostic_metrics,attribution_method,attribution_level,baseline_window,test_window,minimum_events,decision_rule,compliance_scope,evidence_ids,confidence,owner,status,source_asset_sha256,consent_ids
```

- `direction` 只能是 external_to_xhs、xhs_to_native_conversion、xhs_to_approved_external、owned_retention。
- 每行只表示一个原生 `platform` 与一个真实账户/主体 `account_scope`；`unassigned` 只能用于阻断态，不能放行 CTA。
- 每个渠道只有一个主要 `channel_role` 和一个 `primary_metric`。
- `eligibility_ids` 引用下面两个 registry；商业 CTA 不得留空。
- `surfaces` 必须与被引用 registry 行逐项一致。
- `metric_availability` 真实写 available/unavailable/needs_backend_check。
- `event_definition` 写去重、同意、退款等边界；不能只写“转化”。
- 无用户级闭环的 external_to_xhs 使用 `attribution_level=directional`。
- `source_asset_sha256` 锁定本行实际素材版本；`user_level_with_consent` 还必须用 `consent_ids` 引用当前有效、明确允许跨平台归因且绑定该素材的 AUTH 记录。
- 资格未全部通过时，`status` 必须以 blocked/draft/needs_ 开头。

## sku-registry.csv

```text
eligibility_id,sku_id,sku_name,platform,account_scope,surface,source_asset_id,status,evidence_ids,platform_ticket,verified_at,expires_at,material_limits,qualification_requirements,notes,source_asset_sha256,qualification_claim_id
```

一个 SKU 每个 `platform × account_scope × surface × source_asset_id` 各一行。`source_asset_id` 是本次审批覆盖的具体稿件/素材；成稿时等于 `draft_id`，渠道时等于该行的 `source_asset_id`。常见 surface：organic_content、professional_account、shop、pgy_commercial_content、ads、leadgen、dm_commercial、approved_external_destination。

允许放行状态只有 `confirmed | approved`，且 `platform`、`account_scope`、`surface`、`source_asset_id` 都必须指向一个具体对象，不能写 `multi_platform`、`all_*` 或 `unassigned`。`source_asset_sha256` 锁定获批素材的精确字节版本。`platform_ticket` 必须引用 `source-log.csv` 中本次采集、可访问的官方审批记录；`qualification_claim_id` 必须引用与完整元组和素材哈希一致的当前 `sku_eligibility` 主张，两者同时出现在 `evidence_ids`，不可只引用一般规则自填 `confirmed`。必须有不晚于本次运行的 `verified_at`；若无 `expires_at` 就在本次运行重新核验，有明确有效期时本次运行日不得晚于它。其余状态使用 needs_platform_confirmation、insufficient_sku_input、insufficient_official_evidence、expired、rejected、blocked 等。一个账户、素材或 surface 通过不能放行另一个。

最小 SKU 资格主张作用域示例（键名必须保持一致）：

```text
sku_id=SKU-001|platform=xiaohongshu|account_scope=acct-xhs-001|surface=shop|source_asset_id=DRAFT-001|source_asset_sha256=<64位SHA-256>
```

## offer-registry.csv

```text
eligibility_id,offer_id,offer_name,offer_type,platform,account_scope,surface,source_asset_id,status,evidence_ids,platform_ticket,verified_at,expires_at,permission_or_consent_requirements,prohibited_uses,notes,source_asset_sha256,qualification_claim_id
```

非 SKU 的编辑内容、订阅、咨询、合作、活动、投稿计划使用 offer registry。不能用 `multi_platform/public_content` 一行放行所有平台；按具体 `platform × account_scope × surface × source_asset_id × source_asset_sha256` 拆分，并用 `platform_ticket + offer_eligibility qualification_claim_id` 保留精确审批记录。若内容同时植入商品，还必须追加 SKU eligibility。

最小 offer 资格主张作用域示例：

```text
offer_id=OFFER-001|offer_type=subscription|platform=xiaohongshu|account_scope=acct-xhs-001|surface=shop|source_asset_id=DRAFT-001|source_asset_sha256=<64位SHA-256>
```

## authorization-log.csv

```text
authorization_id,subject_scope,source_asset_id,material_id,material_sha256,material_type,permission_scope,commercial_use,anonymization_requirements,granted_at,expires_at,withdrawal_process,evidence_locator,verified_by,verified_at,status,authorized_output_sha256
```

- 涉及真人投稿、访谈、聊天记录、案例、匿名改编或合成案例时使用；不要把身份证、联系方式、原始聊天等隐私原件直接放进研究库。
- `material_type`：`first_party | interview | submission | case_record | chat_record | other`。
- `source_asset_id` 指向获授权用途的具体稿件/渠道素材；`material_id + material_sha256` 锁定被授权原材料，`authorized_output_sha256` 锁定当事人/核验人实际审过的衍生稿或归因素材。任一字节变化都要重新审查并更新授权，禁止拿一份无关授权套另一案例。
- `permission_scope` 可用分号组合：`anonymized_publish | adaptation | composite | verbatim | cross_platform_attribution`。用途不能从“同意采访”自动扩张到公开、改编、跨平台用户级归因或商业使用。
- `first_person_documented` 必须在可见披露中明确“本人/我的亲历”；涉及他人材料时，每条 AUTH 还必须包含 `anonymized_publish` 或 `verbatim`，仅有归因同意不能发布内容。`composite_cases` 至少需要两个不同 `subject_scope`、`material_id` 和 `material_sha256`；换 ID 复制同一材料不算两个案例。
- `commercial_use`：`approved | prohibited`；有商业关系的案例稿必须获得对应商业用途许可。
- `evidence_locator` 只写受控原件的保管编号/私有库定位符；`verified_by` 与 `verified_at` 记录谁在何时核验。不要伪造授权编号。
- `status`：`approved | pending | withdrawn | expired`。无 `expires_at` 的 approved 记录需在本次运行复核；撤回后立即阻断关联稿件。

## drafts/*.md

Frontmatter 必填：

```yaml
---
draft_id: DRAFT-001
topic_id: TOPIC-001
platform: xiaohongshu
account_scope: none
primary_job: search_capture
lifecycle: evergreen_search
truth_label: factual_explainer
truth_disclosure_text: 事实说明
truth_disclosure_location: 首屏
authorization_ids: none
source_material_ids: none
commercial_relationship: none
disclosure_text: none
disclosure_location: none
answer_location: "第3页/正文第2段"
cta_type: none
eligibility_ids: ""
surfaces: ""
status: needs_review
---
```

`truth_label` 只允许：`first_person_documented | authorized_anonymized | authorized_adaptation | composite_cases | fictional_scenario | factual_explainer`。`truth_disclosure_text` 必须使用肯定式合同（如“本内容为明确虚构”“经授权匿名整理”“本人亲历记录”），并在 `truth_disclosure_location=首屏/第一页/首段/开头/标题下` 的实际可见正文里出现；“不是真实虚构”“未经授权”等否定冲突会阻断。HTML 注释、隐藏标签、图片 alt、链接 URL 或只存在元数据中的文字不算可见。`authorization_ids` 必须与标签一致：本人一手材料写 `self_only`；授权匿名/改编引用相应 AUTH；合成案例至少引用两个允许 composite 且对应不同 subject/material/hash 的 AUTH；明确虚构与纯事实解释写 `none`。`source_material_ids` 必须与关联 AUTH 的 `material_id` 完全一致。商业关系是独立维度，`commercial_relationship` 只允许：`none | owned_product | sponsored | gifted | affiliate | commissioned_creator | other_disclosed`；非 `none` 时披露文案必须真实、肯定地写入 `## 成稿`，并与关系类型对应：自有/自营、广告/品牌合作、获赠、佣金/返佣、受委托，或明确的其他利益关系。“不是广告/没有品牌合作”等否认句会阻断。机器可验证位置仅支持首屏/第一页/首段/开头/标题下，或 `CTA前/正文CTA前`；后两者要求同一成稿中披露确实早于精确 `cta_copy`。视频口播与字幕等无法由 Markdown 单独证明的位置先由人工审校，不得伪填成机器 PASS。

`cta_type` 只允许：`none | save | follow | comment_question | read_series | product_component | leadgen | approved_external | paid_offer`。后四种商业 CTA 不能把商业关系写成 `none`，并必须引用当前有效且与 `platform × account_scope × surface × draft_id/source_asset_id` 完全一致的 eligibility。

正文二级标题必须完整且名称固定：

```text
## 证据与目标用户
## 标题版本
## 封面版本
## 成稿
## 关键词与话题
## 事实与证明
## CTA 与披露
## 合规审校
## 创意审校
## 观测计划
```

商业 CTA 的 `eligibility_ids` 与 `surfaces` 必须对应且全部 approved/confirmed。`cta_type=none` 才可留空。验证器检查结构和引用，不会替代语义、创意、版权、医学或平台人工审核。

`## CTA 与披露` 中必须逐行写 `cta_type`、`cta_copy`、`commercial_relationship`、`disclosure_text`、`disclosure_location`、`eligibility_ids`、`platform`、`account_scope`、`surfaces`，并与 frontmatter 完全一致。验证器能发现两处自相矛盾，但仍需审校者通读成稿，确认正文或画面没有在 `cta_type=none` 时暗藏购买/站外动作。

成稿 `status` 只允许 `needs_review | ready | blocked`。`run.status=complete` 时，每篇成稿必须为 `ready`，且 `## 合规审校` 与 `## 创意审校` 都包含 `review_status: PASS`；PARTIAL/FAIL 不得靠把运行标完成来绕过。

## 引用图

```text
query ──发现──> source/account/post
source ──支持/反证──> claim
post + claim + account baseline ──约束──> topic
topic + rule scope + truth material ──生成──> draft
SKU/offer eligibility ──逐surface放行──> channel/draft CTA
```

任何箭头断裂都应报错或降级，不允许用总结文字替代底层行。
