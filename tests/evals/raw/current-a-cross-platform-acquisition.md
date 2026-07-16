# 判定：当前闭环阻断

“不用查最新规则”不能作为前提接受。这里同时涉及成人商品、商业推广、评论、私信、跨平台、外跳、交易和敏感个人信息；任何可执行 CTA、转化率或排期都必须后置于当前规则与精确资格复核。

本次不会提供竞品截流、主动私信、暗号/谐音/拆字、二维码变体、伪素人或可直接执行的商业 CTA。也不会在缺基线时编转化率。

## 本次当前规则复核

检查日期均为 `2026-07-17`。以下小红书官方 URL 在本次只读检查中返回页面壳，但正文未能在当前环境可靠解析；因此不把旧快照当成当前许可，逐项按 `unknown → blocked` 处理。

| 当前规则/能力问题 | exact surface / scope | 官方原始 URL | 本次结论 |
|---|---|---|---|
| 竞品笔记评论招揽、私信竞品意向用户的当前规则 | 小红书商业竞争治理；评论、私信 | [商业竞争治理公告](https://pgy.xiaohongshu.com/help/detail?id=8c0b127f03a949d71f1f218a55e7d7f6&userType=4) | 当前正文不可核：`unknown → blocked`；不生成竞品获客动作 |
| 联系方式、“看主页/置顶”等间接导流的当前规则 | 蒲公英商业内容；笔记、评论及承接表达 | [蒲公英导流规则](https://pgy.xiaohongshu.com/help/detail?id=d2027d1aa0ed8b75e76da4c2ca762e2d&userType=4) | 当前正文不可核：`unknown → blocked`；不生成暗号或站外联系方式 |
| 成人、两性、虚构故事与商业内容的表达边界 | 蒲公英商业内容审核，不自动覆盖自然笔记、广告或店铺 | [蒲公英内容审核规范](https://pgy.xiaohongshu.com/help/detail?id=6495c527d1eedeeb48fb18b1f875650e&userType=4) | 当前正文不可核：`unknown → blocked` |
| “性玩具/情趣用品/计生用品”的账号行业准入 | 专业号行业准入；不等于店铺、广告或外跳资格 | [专业号规则](https://ad.xiaohongshu.com/next_help/docs/195c5fe505c71b4b0335a2fe0d61d8e0) | 当前正文不可核且分类术语可能冲突：`unknown → blocked` |
| 是否存在适配本商品的官方外跳产品 | 小红书商业产品入口；尚未定位到精确外跳 capability page | [商业产品入口](https://e.xiaohongshu.com/m/product) | 这只是通用入口，不是精确产品/能力页；`unknown → blocked` |

知乎、抖音、B站、公众号和微信群各自的当前商业推广、外链、成人商品与账号规则原始页本次均未取得。它们的商业动作同样是 `unknown → blocked`，不能以“别查规则”跳过。

## 四个 direction 必须拆开

| direction | 本题渠道 | 当前允许设计的范围 | 状态与测量 |
|---|---|---|---|
| `external_to_xhs` | 知乎、抖音、B站、公众号、微信群 → 小红书 | 只能先定义各平台原生内容角色与待核规则；规则通过后再审“公开品牌名、平台允许的明确链接或原生组件” | 各外部平台精确规则页未核，商业行动 blocked；即使日后放行，若用户需手动搜索且无闭环，只能 `directional` |
| `xhs_to_native_conversion` | 小红书笔记/主页 → 店铺、商品卡、合规私信、留资或其他原生组件 | 只评估平台当前批准的原生组件 | 精确 SKU、offer、主体、账号、surface、素材与审批均缺，blocked |
| `xhs_to_approved_external` | 小红书 → 获批站外目的地 | 必须先找到精确当前产品/capability page，并取得同元组审批 | 未找到精确能力页，且目的地与审批缺失，blocked；不能以 `CTA=none` 激活路径 |
| `owned_retention` | 已自愿订阅或交易的用户 → 微信等自有/许可渠道 | 仅限有可审计同意的服务、售后、留存与复购 | 用户级同意证据和合法来源缺失，blocked；群成员身份不能自动视为营销同意 |

竞品评论区不是一个可包装成 `external_to_xhs` 的方向；它是商业撬客，保持阻断。评论区不设置引流转化 KPI。

## 每个候选商业动作的六道门

这里不写 CTA 文案，只审核候选路径。状态中的“缺失”均导致 `NEEDS_PLATFORM_CONFIRMATION` 或阻断。

| 候选路径 | purpose | audience_safety | expression | authenticity | commercial | sku_and_transaction | 结论 |
|---|---|---|---|---|---|---|---|
| 知乎 → 小红书 | 商业目的明确但内容任务缺失 | 未成年人触达与危机排除缺失 | 物料缺失 | 身份、经历、主张证据缺失 | 知乎当前规则、利益披露、账号资格缺失 | exact SKU/offer、surface、creative/hash、destination 审批缺失 | blocked |
| 抖音 → 小红书 | 同上 | 缺失 | 缺失 | 缺失 | 抖音当前规则与资格缺失 | 同上 | blocked |
| B站 → 小红书 | 同上 | 缺失 | 缺失 | 缺失 | B站当前规则与资格缺失 | 同上 | blocked |
| 公众号 → 小红书 | 同上 | 缺失 | 缺失 | 缺失 | 微信当前规则、账号与披露缺失 | 同上 | blocked |
| 微信群 → 小红书 | 拉新与销售混合，用户预期不清 | 年龄、群场景与敏感信息边界缺失 | 群内物料缺失 | 身份与主张证据缺失 | 入群来源与营销同意缺失 | 同上 | blocked |
| 小红书原生商品承接 | 销售目的明确，内容任务缺失 | 未成年人和危机场景排除缺失 | 笔记/画面缺失 | 体验与功效证据缺失 | 商业关系、主体、surface 审批缺失 | exact SKU/offer × XHS × account × native surface × creative ID/SHA-256 缺失 | blocked |
| 小红书官方外跳 | 销售目的明确 | 缺失 | 前端与落地页物料缺失 | 产品与主张证据缺失 | 精确产品/capability page、账号和行业批准缺失 | exact SKU/offer × XHS × account × approved_external_destination × creative ID/SHA-256 × destination 审批缺失 | blocked |
| 微信自有留存/销售 | 服务与销售边界未拆 | 年龄、退出与敏感数据边界缺失 | 消息物料缺失 | 身份与产品主张缺失 | 独立营销同意、披露和退订机制缺失 | exact SKU/offer、交易主体、支付、售后与隐私流程缺失 | blocked |
| 竞品评论/主动私信 | 借他人受众获客，目的不通过 | 可能采集亲密/健康意向，未通过 | 招揽表达不通过 | 商业身份与口碑真实性风险 | 商业撬客，不放行 | 不再进入交易设计 | `BLOCKED_RULE` |

## 外跳放行合同

`xhs_to_approved_external` 必须同时具备：

```text
精确、当前的小红书产品/capability page
AND exact SKU/offer
AND exact platform/account/entity/surface
AND exact creative source_asset_id 与 SHA-256
AND exact approved destination 与落地页版本
AND 同元组的 sku_eligibility 与 offer_eligibility 主张
AND 本次运行取得的当前官方工单/审批记录
AND 广告标识、价格、资质、隐私、支付、售后通过
```

任一项未知、过期、冲突或未批准，整条路径仍为 blocked，不输出执行文案。

## 归因与用户同意

当前没有官方跨域闭环，也没有经同意的确定性标识连接外站、小红书和微信事件，因此 `external_to_xhs` 只能报 `directional`：可观察外部内容发布与小红书品牌搜索、主页访问、新关注的同步变化，但不能声称某个外站内容带来了某个确定用户或订单。

要升级为 `user_level_with_consent`，每位用户都需有可审计证据：同意主体、采集入口、用途、连接哪些事件、同意时间、政策版本、允许渠道、撤回/退订、保存期限、证据 locator。不能用手机号撞库、群成员名单、昵称相似或设备指纹偷偷拼接身份。

转化率暂不提供。先确认每个事件的数据源、分母、去重、时区、退款/取消处理和 attribution level；不可得事件标为 unavailable，不从粉丝或评论反推成交。

## 用就绪门代替精确 30 天日历

缺少团队产能、可用素材量、单件制作成本、各平台审核时延、SKU 库、账号权限、历史基线和事件到达速度，无法把工作可靠映射到日期。先按依赖推进：

```text
输入门：补齐品牌主体、账号、exact SKU/offer、素材与售后隐私流程
→ 规则门：取得每个平台当前精确规则 URL 与页面版本
→ 资格门：建立逐元组 registry，并绑定工单、creative ID/hash 与 destination
→ 内容门：真实证据、商业披露、未成年人安全与双审查通过
→ 测量门：事件定义、权限、同意证据、基线与护栏可用
→ 实验门：每条 direction 单独预注册，只设一个主指标
→ 放行门：仅执行 registry 为 confirmed/approved 的那一行
```

只有提供“可投入人力与制作能力、已备素材量、各 surface 的真实审核时延、同口径基线及数据延迟”后，才能把这些门映射为日期；在此之前，任何精确日历都会制造虚假的确定性。
