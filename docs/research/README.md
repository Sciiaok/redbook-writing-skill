# 研究资产索引

这里保存 `redbook-writing` 的公开资料审计、站内观察和派生机制。它们不是“参考链接堆”；每一组都说明样本、来源激励、能支持什么、不能支持什么，并尽量提供机器可读副本。

读法：先从与你的问题最接近的一行进入，再回到原文件看来源与限制。不要把多个弱来源投票合成强结论，也不要把公开赞藏评改名为自然流量。

## 2026-07-18 深挖批次

| 资产 | 输入规模/形态 | 最适合回答 | 明确不能回答 | 机器副本 |
|---|---|---|---|---|
| [官方商家课笔记](2026-07-18-official-xhs-merchant-course-notes.md) | 小红书电商学习中心 4 节公开课，账号/标题封面/正文/评论全链路 | 平台在 2024 年怎样教商家生产笔记；推荐/搜索任务、承诺兑现、评论反馈和自账号样本库 | 2026 算法权重、固定分发时长、某版式必爆 | [JSON](2026-07-18-official-xhs-merchant-course-notes.json) |
| [运营课程与操盘复盘](2026-07-18-operator-course-playbooks.md) | 17 个公开来源、13 张 playbook、4 组冲突、6 个淘汰说法 | 服务商、数据机构、品牌复盘中重复出现的生产动作与失败边界 | 固定阈值、自然流量因果、盗版付费课内容 | [JSON](2026-07-18-operator-course-playbooks.json) |
| [品牌/代理项目](2026-07-18-brand-operator-case-playbooks.md) | 12 条来源、9 个项目、11 张 playbook | 选品、人群、内容、KFS/投放、搜索承接与复盘怎样连成项目 | 把预算、达人、选品和内容混合结果归因给标题/封面 | [JSON](2026-07-18-brand-operator-case-playbooks.json) |
| [隐藏生产物](2026-07-18-hidden-production-artifacts.md) | 23 个公开来源、9 组生产机制 | brief、母资产、创作者协作、话题供给、指标合同、AI 返工和版本血缘 | 这些流程本身会提高自然流量 | [JSON](2026-07-18-hidden-production-artifacts.json) |
| [学术多模态审计](2026-07-18-academic-multimodal-evidence.md) | 5 篇原始研究/公开数据，含标题、美妆商业帖、KOC 民族志、CHASM、RedNote-Vibe | 大样本变量的真实设计、偏差、AI/商业风险和可实验边界 | 字数、人脸、问号、发布时间、AI/人写的通用效果公式 | [JSON](2026-07-18-academic-multimodal-evidence.json) |
| [站内高低公开代理横截面](2026-07-18-live-public-proxy-contrast.md) | 宠物系列、租房改造、劳动仲裁、上海路线、敏感肌面霜 5 个任务包 | 反证“越美/越密/有真人/有文件就更高”，提出承诺—证据、工作物、变化等候选 | 曝光、CTR、自然流量因果、matched-control 结论 | [JSON](2026-07-18-live-public-proxy-contrast.json) |
| [跨类目载体 gap audit](2026-07-18-cross-category-live-carriers.md) | 当前公开载体审计，合格 matched control 为 0 | 哪些证据还缺、为什么不能把高赞样本做 starter | 高表现视觉规则晋级 | [JSONL](2026-07-18-cross-category-live-carriers.jsonl) |
| [原生实用载体审计](2026-07-18-native-traffic-utility.md) | 比较板、法律清单、截图教程、改造、正式解释 5 组既有观察 | 任务型载体的补采合同与 candidate mechanism | 红黑榜/红框/深蓝/前后图是爆款风格 | [JSONL](2026-07-18-native-traffic-utility.jsonl) |
| [原生 feed 证据审计](2026-07-18-native-traffic-feed.md) | 站内公开 feed 线索与缺口 | 哪些公开观察可保留为 research lead | 公开互动代理直接升级为流量 | [JSONL](2026-07-18-native-traffic-feed.jsonl) |

## 2026-07-17 基础批次

| 资产 | 用途 | 边界 |
|---|---|---|
| [生产级运营证据](2026-07-17-production-grade-xhs-operations-evidence.md) | 官方、工程、学术、行业和操盘经验的第一轮综合审计 | 按原文作用域使用，不把工程模块还原成全站权重 |
| [生产主张](2026-07-17-production-claims.json) | 机器读取的 claim 与状态 | 状态会随当前官方核验和新反证变化 |
| [站内逐页风格观察](2026-07-17-live-xhs-style-observations.md) | 真实页面的 carrier、视觉、文风与边界观察 | 多组仍缺完整 baseline/权利/逐页 receipt，不是 starter |
| [站内观察 journal](2026-07-17-live-xhs-style-observations.jsonl) | 机器重放的脱敏观察 | 不含第三方原图或完整正文 |

## 从研究资产进入 Skill

研究层的长文不会在每次写稿时整包塞进上下文。经过审计的跨来源结论先进入：

- `redbook-writing/assets/traffic-mechanisms-v1.json`：统一、可检索的机制卡；
- `redbook-writing/references/traffic-mechanism-library.md`：人工可读解释；
- `redbook-writing/assets/traffic-mechanism-candidates-template.jsonl`：后续运行追加候选；
- 本地 `_style_library/style-library.sqlite`：当前类目逐页 observation、对照、publication 与 draft binding。

晋级路径：

```text
公开课程/项目/研究/帖子
  → lead
  → production_hypothesis 或 task_fit
  → 合格高低对照下的 public_proxy_association
  → 本账号一方 exposure 复现后的 first_party_traffic_validated
```

任何一级都保留反例、失效条件、付费/自然范围和来源。不能因为资料很多就跳级。

