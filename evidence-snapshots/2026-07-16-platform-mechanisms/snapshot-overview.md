# 小红书平台机制研究档案

本目录保存 2026-07-16 这一轮全网研究的可追溯资料。任何总结都不能代替原始链接账本；来源失效或结论被反驳时保留记录并更新状态，不静默删除。

## 文件导航

| 文件 | 用途 |
|---|---|
| `run.yaml` | 本轮目标、状态、来源层、采集与证据政策 |
| `research-plan.md` | 研究问题、检索范围、停止条件 |
| `source-log.csv` | 所有去重来源的元数据、链接、检索词、访问状态、证据形式和等级 |
| `query-log.csv` | 实际执行的查询、平台、结果与缺口 |
| `claim-ledger.csv` | 规范化主张、支持/反证、作用域、状态、局限和 Skill 使用规则 |
| `xhs-post-samples.csv` | 本轮能够核验到字段的笔记级样本；缺原帖链接或指标时明确留空 |
| `xhs-comment-search-samples.csv` | 登录态搜索“评论区截流”得到的20张搜索卡与1条详情核验；不冒充效果或头部榜单 |
| `acquisition-channels.csv` | 外部获客、站内承接与批准外跳的渠道角色、CTA、指标、归因和SKU状态 |
| `sku-registry.csv` | 具体SKU × 平台 × surface 的独立资格、规则/工单、时间与素材限制；当前为待补SKU的阻断模板 |
| `offer-registry.csv` | 非SKU的编辑内容、自有站入口、订阅留存、创作者合作和线下活动资格 |
| `notes/official-and-academic.md` | 官方规则、算法备案、工程论文和学术材料摘要 |
| `notes/xhs-creator-posts.md` | 小红书站内创作者帖、可见数据、经验主张和局限 |
| `notes/industry-web.md` | 公众号、知乎、行业媒体与报告的逐条摘要 |
| `notes/industry-evidence-matrix.md` | 行业资料横向证据矩阵与冲突审计 |
| `notes/comment-section-acquisition.md` | 评论参与、评论截流、商业撬客、效果证据与三色规则 |
| `notes/cross-platform-acquisition.md` | external→XHS、站内转化、自有资产、渠道矩阵与敏感经营门槛 |
| `synthesis.md` | 跨来源综合判断；只引用账本中已有来源 |

## 证据与状态

- `A`：官方原文、法规、论文原文、公开技术资料或可复核的平台产品事实。
- `B`：方法和样本口径较清楚的独立数据或多案例研究。
- `C`：有后台截图、连续实验或具体样本的从业者复盘。
- `D`：单一经验、观点、转述或找不到原始依据的算法传言。

主张状态只使用 `confirmed`、`supported_experience`、`hypothesis`、`contradicted`、`unknown`。证据等级与结论状态不是一回事：例如两篇 D 级文章互相冲突，只能证明传言不可靠，不能证明其中一套公式正确。

## 保存原则

1. 保存元数据、原始链接、结构化转述和必要的短证据，不整页复制受版权保护的文章。
2. 同一来源被多个查询命中时聚合发现路径，不重复计数。
3. 论文、规则和经验必须注明时间与产品模块，不能外推为当前全站固定算法。
4. 小红书站内数据只记录公开可见口径；无法拆分的互动量不伪造成点赞/收藏。
5. 不点赞、关注、评论、发布，不导出 Cookie，也不绕过登录或风控。
6. 一个SKU/offer在一个surface通过，不自动放行其他surface；外跳缺精确官方证据时保持blocked。
