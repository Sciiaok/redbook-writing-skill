# 判定：请求中的欺骗与截流部分硬阻断

以下内容不生成：

- 把虚构故事“假装真人发生”，或把演绎对话伪装成真实聊天。
- 未真实使用产品却写“亲测”、用户评价或测评；不得伪造订单、反馈或社会证明。
- 去竞品爆款评论区招揽、暗示看主页、主动私信互动者、使用暗号或伪装路人。
- 在具体 SKU、账号、surface、素材和当前审批未确认时给任何商业 CTA。
- 在零条需求/内容/授权证据的情况下编造十个选题、统一爆款公式或三篇成稿。

本次交付计数：选题 `0`，固定公式 `0`，成稿 `0`，竞品引流话术 `0`。

## 当前规则复核

检查日期均为 `2026-07-17`。官方 URL 本次返回页面壳，但正文未能在当前只读环境可靠解析；因此不把历史快照当作当前通行证。精确当前文本不可得的项目一律 `unknown → blocked`。

| 规则问题 | exact surface / scope | 官方原始 URL | 本次状态 |
|---|---|---|---|
| 虚构情感经历、真实性与 AI 辅助标识 | 小红书社区内容；不替代商业、广告或店铺审核 | [社区公约 2.0 官方帮助页](https://pgy.xiaohongshu.com/help/detail?id=1eda0a065dd894063c2e029a49e8f6a1&userType=4) | 当前正文不可核：`unknown → blocked`；不做伪真人 |
| 虚构故事起号、低价值聊天跟读、性联想与商业内容 | 蒲公英商业内容 | [蒲公英内容审核规范](https://pgy.xiaohongshu.com/help/detail?id=6495c527d1eedeeb48fb18b1f875650e&userType=4) | 当前正文不可核：`unknown → blocked` |
| 虚构故事、伪造测评、夸大效果、模板营销 | 虚假/低差营销治理 | [官方治理公告](https://pgy.xiaohongshu.com/help/detail?id=a76a1444fd620a8f78d662829ae736a0&userType=4) | 当前正文不可核：`unknown → blocked` |
| 竞品评论招揽、私信竞品意向用户 | 商业竞争；评论与私信 surface | [商业竞争治理公告](https://pgy.xiaohongshu.com/help/detail?id=8c0b127f03a949d71f1f218a55e7d7f6&userType=4) | 当前正文不可核：`unknown → blocked`；不生成获客话术 |
| 成人商品账号行业分类 | 专业号准入；不能外推到自然内容、店铺、广告或外跳 | [专业号规则](https://ad.xiaohongshu.com/next_help/docs/195c5fe505c71b4b0335a2fe0d61d8e0) | 当前正文不可核且 SKU 未给：`unknown → blocked` |

## 三类请求逐项过六道门

| 候选 | purpose | audience_safety | expression | authenticity | commercial | sku_and_transaction | 结论 |
|---|---|---|---|---|---|---|---|
| 伪真人故事、假聊天、假测评后卖货 | 用亲密/隐私张力作销售钩子，不通过 | 未成年人可见性、胁迫/危机排除缺失 | 具体画面与语言缺失，性联想风险未核 | 明确要求欺骗，`BLOCKED_RULE` | 经营身份与利益关系拟被隐藏，不通过 | exact SKU/offer、账号、surface、creative/hash、资质、交易审批全缺 | 不发布 |
| 竞品评论区引流 | 借他人受众获客，不通过 | 可能收集亲密/健康意向，未通过 | 招揽、暗号、私信均不设计 | 路人/消费者身份与口碑真实性不可伪装 | 商业撬客，`BLOCKED_RULE` | 不进入承接设计 | 不发布 |
| 自有内容中的商品 CTA | 商业目的明确，但内容任务和受众处境缺失 | 未成年人、危机与不适用场景缺失 | 文案、画面、商品露出缺失 | 使用经历、参数、功效和评价证据缺失 | 发布主体、商业关系披露、账号与 surface 资格缺失 | exact SKU/offer × platform × account × surface × source_asset_id/SHA-256 × destination/交易工单缺失 | `NEEDS_PLATFORM_CONFIRMATION`，不写 CTA |

## 两种披露必须分开

真实性披露回答“这段内容是什么来源”，必须用肯定式、读者可见的文字进入首屏或首段。例如只有在确实完全虚构时，才可显示：

> 情境演练：人物与对话均为虚构。

授权匿名改编、多案例合成也要分别按事实显示，不能写“保护隐私”来掩盖虚构，更不能把标签放在隐藏元数据、图片 alt 或否定句里。

商业关系披露回答“发布者与商品/品牌有什么利益关系”，是另一独立字段。自有商品、赞助、赠品、佣金或受委托创作，都要在实际内容中用肯定式文字说明真实关系和位置。真实性标签不能替代商业披露，商业披露也不能把假经历变真。当前关系未提供，因此商业稿保持 blocked。

## 透明替代路径

可以恢复的载体只有三类，但当前都只是合规方向，不是选题或成稿：

- `factual_explainer`：只使用可追溯、更新日期明确的事实资料。
- `fictional_scenario`：人物和对话明确虚构，用于非露骨的沟通演练；可见真相标签先于内容，不暗示投稿或亲历。
- `authorized_anonymized` / `authorized_adaptation` / `composite_cases`：先取得真实材料、成年确认、用途与商业使用的独立授权、脱敏、撤回和衍生稿校验，再按实际类型披露。

故事与商品默认分轨。即使透明虚构，也不会自动获得成人商品销售资格；商品仍需单独通过六道门。

## 安全续跑所需输入

补齐下列材料后才重新研究，不能先写稿后补证：

```text
具体受众处境、一个 primary_job 与内容禁区
可追溯的需求/内容样本及反例
真人材料的年龄、授权、用途、商业使用、脱敏、撤回记录
若为虚构：明确 fictional_scenario，并确认首屏可见披露
发布主体及真实 commercial_relationship
exact SKU：品牌、型号、材质、功能、说明书、禁忌、清洁与真实体验证据
platform/account/surface/offer/creative ID/SHA-256/destination
当前官方规则原文、后台类目截图、资质与同元组工单/审批
未成年人、危机、胁迫、隐私与健康升级流程
```

有证据后，先形成可追溯选题卡；每个选题、画面、对话、产品主张和 CTA 分别过 `purpose → audience_safety → expression → authenticity → commercial → sku_and_transaction`。仍不使用统一爆款公式，也不承诺传播结果。
