---
draft_id: DRAFT-001
topic_id: TOPIC-001
platform: xiaohongshu
account_scope: none
primary_job: feed_stop
lifecycle: evergreen_search
style_contract_version: 2
business_objective: traffic_first
style_requirement: both
style_library_path: ../_style_library/style-library.sqlite
style_taxonomy_version: 2
style_query_category: "待填写"
style_query_carrier: text_card
style_query_primary_job: feed_stop
style_query_required_constraint_codes: none
style_query_active_constraint_codes: none
style_query_available_material_codes: text_only
style_query_active_contraindication_codes: none
style_binding_source: none
style_binding_status: needs_style_research
primary_style_archetype_id: none
secondary_style_archetype_id: none
performance_rule_claim_kind: series_constant
style_feature_contrast: invariant
performance_evidence_scope: not_performance_evidence
performance_visibility_scope: public_proxy
traffic_stage: feed_stop
traffic_primary_metric: engagement_proxy
traffic_verdict: not_applicable
job_primary_metric: unavailable
job_metric_event_definition: "当前没有一方任务指标；发布前按 primary_job 定义事件与分母"
job_metric_denominator: unavailable
job_metric_data_scope: unavailable
job_metric_verdict: unavailable
visual_delivery_requirement: brief
visual_delivery_status: brief_only
truth_label: factual_explainer
truth_disclosure_text: 事实说明
truth_disclosure_location: 首屏
authorization_ids: none
source_material_ids: none
commercial_relationship: none
disclosure_text: none
disclosure_location: none
answer_location: "待填写：第几页/第几段"
cta_type: none
eligibility_ids: ""
surfaces: ""
status: needs_review
---

> 事实说明

# 成稿标题（工作名）

## 证据与目标用户

- 目标用户此刻的处境：
- 读完获得：
- Source / Claim / Account / Post IDs：
- 代表样本与反例：
- 本稿独有材料：
- 不能补写的未知项：

## 标题版本

1. 
2. 
3. 

选定版本与理由：不使用“保证点击/爆款”作为理由。

## 封面版本

1. 文案 / 画面 / 与正文的答案关系：
2. 文案 / 画面 / 与正文的答案关系：
3. 文案 / 画面 / 与正文的答案关系：

## 风格检索与规则合同

- 当前状态：`needs_style_research` 不得写成 ready。若下方列出至少 2 个 task-fit `traffic_mechanism_ids`、1 个 `counterexample_id`，且真实性/授权/事实/商业门通过，可交付显著标注的 `candidate_only / needs_review` 候选稿和探索 brief；否则只交付证据缺口与补采计划。
- `series_constant` / `task_fit` 只说明系列识别或任务适配，必须保持 `not_performance_evidence`。
- 公开竞品只有 `engagement_proxy`，`traffic_verdict` 必须为 `not_applicable`。
- starter 当前发布门禁未完成，不得绑定或包装成爆款公式。

## 成稿

写完整正文或逐页/逐镜分镜。每页只承担一个任务；标题、封面和开头的承诺必须在 `answer_location` 兑现。

若 `commercial_relationship != none`，必须把与 frontmatter 完全一致的肯定式 `disclosure_text` 写在这段实际发布文案里：明确自有/自营、广告/品牌合作、获赠、佣金/返佣、受委托或其他利益关系，不能写“不是广告/没有合作”来否认已声明的关系。若位置填 `首屏/第一页/首段/开头/标题下`，披露应在成稿前部直接可见；若填 `CTA前/正文CTA前`，先写披露，再原样写下方合同中的 `cta_copy`。不要把披露只放在元数据、合同块、HTML 注释、图片 alt 或链接地址中。视频口播与字幕需另做人工可见性复核，当前 Markdown 校验不自动放行。

## 关键词与话题

- 主查询/主意图：
- 同义表达与长尾：
- 标题/封面/正文/话题如何自然对齐：
- 不使用的无关热门词：

## 事实与证明

| 主张 | 类型（事实/观察/推断/虚构） | 证据ID/原件 | 适用范围 | 未知/修改 |
|---|---|---|---|---|
|  |  |  |  |  |

产品/功效另列真实体验、说明书、适用/不适用、利益关系、SKU与surface资格。

## CTA 与披露

```text
cta_type: none
cta_copy: none
commercial_relationship: none
disclosure_text: none
disclosure_location: none
eligibility_ids: none
platform: xiaohongshu
account_scope: none
surfaces: none
```

以上机器字段必须与 frontmatter 完全一致。若 `cta_type=none`，正文、画面和评论承接也不得出现购买或站外动作；审校者需要阅读实际成稿确认，不能只看元数据。

## 合规审校

review_status: pending

完成审校后把 `pending` 改为 `PASS | PARTIAL | FAIL` 之一。

- 致命：
- 重要：
- 次要：
- 六道门：purpose / audience_safety / expression / authenticity / commercial / sku_and_transaction
- 修订与复检：

## 创意审校

review_status: pending

完成审校后把 `pending` 改为 `PASS | PARTIAL | FAIL` 之一。

- 两秒内是否知道“在说我什么”：
- 标题/封面/开头/答案是否兑现同一承诺：
- 细节、节奏、人物差异与用户语气：
- 是否有营销号腔、AI套话或空泛总结：
- 载体与制作条件是否匹配：
- 修订与复检：

## 观测计划

- 流量阶段：`feed_stop | read_through | save_share | comment_cocreation | profile_follow`
- Primary job：
- Exposure primary：只用 impressions；平台只给 reach 时固定用 reach。
- Job primary metric / event / denominator：与 primary job 对应，不能拿点赞或后链路顶替。
- 可用代理及其局限：
- 观察窗口：
- 生命周期：
- 失败层级：
- 下一轮只改一个变量：
- 混杂因素：
- 结果：`pending | win | loss | inconclusive`

## 逐页视觉 QA

- 若 `visual_delivery_requirement=rendered`，不能以 `brief_only` 交付。
- 最终图片未实际生成、打开和逐页复核时，只能写 `rendered_needs_review`，不能写 `rendered_pass`。
- 成人敏感商品 CTA 仅在显式写 `cta_product_scope: adult_product` 时触发精确生产门禁；关系教育本身不产生商品资格。
