# 决策：原方案整体阻断，不能按要求生成

我不会把虚构内容伪装成真人经历、后台投稿或真实聊天，也不会生成假测评、统一“爆款公式”或去竞品评论区获客的话术。当前又没有可追溯需求样本、授权材料、具体 SKU 与 surface 资格，所以这轮不能诚实地产出 10 个选题、3 篇成稿、标题或封面；它们不能靠加一句免责声明变成可发布内容。

2026-07-18 运行时复核显示：小红书[内容审核规范](https://pgy.xiaohongshu.com/help/detail?id=6495c527d1eedeeb48fb18b1f875650e&userType=4)当前页面版本为 2026-07-15，作用域是蒲公英商业合作内容，其中明确列出聊天记录跟读、模板化故事营销、虚构故事起号、私密/性相关内容、间接导流和置顶评论配合等风险；[专业号行业准入规则](https://ad.xiaohongshu.com/next_help/docs/195c5fe505c71b4b0335a2fe0d61d8e0)同时出现“性玩具禁入”与“情趣用品、计生用品普通准入”的术语冲突。前者不能自动外推为所有自然内容规则，后者也绝不是文字改名即可获得许可；具体商品必须由平台按精确分类确认。

## 先拆成两条互不偷渡的轨道

| 轨道 | 可以继续研究的透明载体 | 当前不能做 |
|---|---|---|
| 编辑内容 | `factual_explainer` 事实科普；首屏明确写“情境演练：人物与对话均为虚构”的教育性对话；有当前授权记录的匿名整理/改编；非露骨的同意、边界、安全与求助信息 | 伪真人投稿、假聊天截图、情色或隐私尴尬作钩子、把个案写成普遍规律、借故事暗植商品 |
| 商业内容 | 只有精确 SKU、主体、账号、surface、素材版本、平台工单和披露全部通过后，才另开商业稿 | 在编辑故事里突然卖货；未确认商品却给购买、私信、站外或评论 CTA；用“体验分享”伪装广告 |

建议的透明聊天载体不是仿造真实截图，而是明确标注的情境演练：不用真人头像、昵称、时间戳或平台水印制造真实性；每轮只用于展示一种沟通选择及其边界。若以后使用真人材料，必须有年龄确认、用途/商业使用分开授权、聊天双方权利、脱敏、撤回和删除记录。

机制选择器也已按你指定的聊天载体运行：

```text
traffic_stage=read_through
primary_job=relationship_build
carrier=chat_dramatization
status=needs_materials
missing_material_codes=
  authorized_chat_original_or_fiction_disclosure,
  rights_clearance
```

它没有返回 `matched`，所以不能绑定三槽机制，更不能继续生成标题、封面或正文。即便补齐这两项，仍需真实需求样本、独立反例、敏感规则与商业门全部闭合。

## 六道门：对当前请求逐项判定

| 门 | 当前判定 | 原因与下一步 |
|---|---|---|
| `purpose` | `BLOCKED_RULE` | 目前把假真人故事作为吸睛和后续卖货钩子，教育目的不足以覆盖欺骗性设计；应先把单篇目标改成一个非商业关系任务 |
| `audience_safety` | `NEEDS_PLATFORM_CONFIRMATION` | 内容公开可被未成年人看到；“18+”标签不是年龄隔离。需要非露骨表达、未成年人投稿排除、危机/胁迫/暴力/健康求助升级流程；任何危机场景都不得承接商品 |
| `expression` | `NEEDS_PLATFORM_CONFIRMATION` | 尚无逐句文案和逐帧画面，无法审查性暗示、敏感部位、类生殖器、动作或打码/谐音；须按实际素材审核，不能假定处理后就会通过 |
| `authenticity` | `BLOCKED_RULE` | “假装真人发生”和伪聊天直接失败；只能改成首屏可见的 `fictional_scenario`，或取得当前有效授权后使用对应真实性标签 |
| `commercial` | `NEEDS_PLATFORM_CONFIRMATION` | 卖自有商品应单独标 `commercial_relationship=owned_product`，利益披露必须进入实际稿件；当前没有主张证明、商业稿件和审核 receipt |
| `sku_and_transaction` | `NEEDS_PLATFORM_CONFIRMATION` | 缺具体品牌/型号/形态/材质/功能/包装、资质、offer、账号主体、surface、素材 ID 与 SHA-256、落地页、当前平台工单；所有商业 CTA 保持 `blocked` |

允许商业 CTA 的资格元组必须逐项完整：

```text
exact SKU × exact offer × Xiaohongshu
× exact account_scope × exact surface
× source_asset_id × source_asset_sha256
× current platform ticket / qualification claim
```

`organic_content`、`professional_account`、`shop`、`pgy_commercial_content`、`ads`、`leadgen`、`dm_commercial`、`approved_external_destination` 要分别核验；一个 surface 通过不能扩展到另一个。当前所有行都是 `NEEDS_PLATFORM_CONFIRMATION → blocked`，不是“先发再看”。

## 评论边界

竞品评论获客属于商业撬客，硬阻断；不会生成任何主页跳转、私信招揽、置顶配合、站外暗号、多账号、伪素人、批量模板或自动评论方案。即使删掉直接 CTA，只要目标仍是借别人的笔记把意向用户转到自己的商业承接面，仍不合格。

可替代路径只有：

- 在自己的账号做有真实证据的搜索型关系教育内容；
- 评论仅在与原帖直接相关时提供一条独立有用的事实/边界补充，不提自己的商品、身份承接或去向，也不设获客 KPI；
- 商业增长改走获批的站内原生组件、官方投放或有披露的创作者合作，前提仍是精确 SKU 与素材审批通过。

## 关于“爆款”

不存在可交付的统一爆款公式、概率、CES 权重或固定互动阈值。后续每篇只能选一个 `primary_job`，用本账号一方 impressions/reach 看真实曝光，再用与任务对应的指标判断内容是否完成；公开赞藏评只能作为代理，不能证明流量或成交。

当前审查结论：

```text
Compliance：FAIL
阻断项：伪真人/假聊天、商业撬客、未确认成人 SKU 与 surface
Creative：FAIL
缺口：零需求样本、零授权材料、载体真实性条件未满足
最终状态：不发布；先补证并重构，不生成成稿
```
