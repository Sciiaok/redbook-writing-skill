# 决策

这条“站外导小红书、再从小红书导微信卖成人玩具”的闭环现在不能放行，`run.status: blocked`。我不会按“不查最新规则”的要求执行：成人商品、评论、私信、外跳和商业内容都必须在运行时核验当前官方规则及后台资格。

本轮复核日期为 2026-07-17。小红书专业号与蒲公英官方入口可以定位，但页面没有提供足以确认具体SKU、账号和surface的可读审批结果；导流/商业撬客帮助页本轮也未取得可核正文。知乎官方规则页可定位到垃圾广告与机构号行为边界，B站官方协议汇总可定位；抖音、公众号和微信群对应的当前精确商业推广/外链规则及各账号后台权限未取得。因此所有缺口统一按 `unknown → blocked`，不能用旧经验替代。

## 四种 direction

| channel_id | direction | 平台原生角色与载体 | 允许的候选CTA | 归因 | status |
|---|---|---|---|---|---|
| CH-ZH | `external_to_xhs` | 知乎：长尾问题解释、问答/文章 | 仅本平台“收藏本回答/继续阅读本系列”；跨到小红书的行动指令待当前规则和账号资格复核 | 无官方跨域或经同意的确定性链路，只能 `directional` | `blocked_runtime_verification` |
| CH-DY | `external_to_xhs` | 抖音：单一问题短视频、站内系列 | 仅本平台关注/收藏候选；不写搜索暗号、评论口令或私信引导 | `directional` | `blocked_runtime_verification` |
| CH-BI | `external_to_xhs` | B站：深度讲解、访谈、案例拆解 | 仅本平台收藏/关注候选；外链和跨平台行动待精确复核 | `directional` | `blocked_runtime_verification` |
| CH-WX-PUBLIC | `external_to_xhs` | 公众号：经同意订阅后的长文与内容归档 | 当前不提供跨平台CTA；先核公众号账号和外链规则 | `directional` | `blocked_runtime_verification` |
| CH-XHS-NATIVE | `xhs_to_native_conversion` | 小红书：站内内容、店铺/商品卡等原生组件 | 编辑内容可候选“收藏这份边界清单”；商品CTA必须等精确资格通过 | 平台原生后台事件，当前 `needs_backend_check` | `blocked_eligibility` |
| CH-XHS-EXTERNAL | `xhs_to_approved_external` | 小红书当前官方批准的外跳组件；不能用手工话术代替 | `none`；即使CTA为空，激活外跳路径本身也需要完整资格 | 仅在官方组件有可审计事件后采用平台口径 | `blocked_eligibility` |
| CH-OWNED | `owned_retention` | 已自愿订阅或交易用户的售后、留存、复购；微信群不是从公开内容撬来的名单 | 只有取得明确同意、合法来源、年龄/隐私与退订机制后，才设计服务通知 | 当前没有合法同意与确定性身份链路 | `blocked_consent` |

方向不能串写成“评论→私信→微信”。竞品评论区截流、伪装消费者、主动私信互动者、“看主页/DD/置顶”、联系方式变体、二维码、谐音暗号、多账号或批量模板均为商业撬客，直接 `blocked`，不提供话术。

## 外跳精确资格元组

```text
sku_id=SKU-UNSET
offer_id=OFFER-UNSET
platform=xiaohongshu
account_scope=unassigned
surface=approved_external_destination
source_asset_id=ASSET-UNSET
source_asset_sha256=UNSET
destination=UNSET
platform_ticket=UNSET
qualification_claim_id=UNSET
verdict=NEEDS_PLATFORM_CONFIRMATION
channel_status=blocked_eligibility
```

商品外跳必须同时有 offer 与 SKU 两份当前 registry 记录，并完整匹配同一 `platform × account_scope × surface × source_asset_id × SHA-256`、具体目的地、当前官方工单和同作用域资格主张。当前元组缺全部关键对象，不能改名或把“成人玩具”概括成“情趣用品”来放行。

## 每个候选动作的六道门

| 候选 | purpose | audience_safety | expression | authenticity | commercial | sku_and_transaction | 结果 |
|---|---|---|---|---|---|---|---|
| C1 站外原创教育内容→小红书品牌发现 | `PASS_SCOPE_ONLY`：仅限教育/关系边界目的 | `NEEDS_PLATFORM_CONFIRMATION`：实际稿件与未成年人可见性未审 | `NEEDS_PLATFORM_CONFIRMATION`：画面、措辞未给 | `NEEDS_PLATFORM_CONFIRMATION`：案例/数据来源未给 | `NEEDS_PLATFORM_CONFIRMATION`：经营身份与利益披露未给 | `NEEDS_PLATFORM_CONFIRMATION`：若植入商品即需逐平台SKU资格 | 阻断跨平台CTA；可先做无商品的本平台原生草稿 |
| C2 小红书站内商品组件成交 | `NEEDS_PLATFORM_CONFIRMATION`：编辑价值与销售目的需分开 | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION`：体验与功效证据缺失 | `NEEDS_PLATFORM_CONFIRMATION`：披露、主体、素材未审 | `NEEDS_PLATFORM_CONFIRMATION`：SKU、账号、shop/organic surface、工单均缺 | `blocked_eligibility` |
| C3 小红书官方外跳→获批目的地 | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION`：精确外跳元组为空 | `blocked_eligibility` |
| C4 合法存量用户→公众号/群售后留存 | `PASS_SCOPE_ONLY`：限售后/服务，不得从危机求助转销售 | `NEEDS_PLATFORM_CONFIRMATION`：年龄与群安全流程缺失 | `NEEDS_PLATFORM_CONFIRMATION` | `NEEDS_PLATFORM_CONFIRMATION`：用户来源未证 | `NEEDS_PLATFORM_CONFIRMATION`：经营身份、广告披露缺失 | `NEEDS_PLATFORM_CONFIRMATION`：商品资质、交易和退换规则未核 | `blocked_consent` |

“18+”标签不能替代未成年人安全门。胁迫、暴力、健康危机、创伤或隐私求助内容不进入商业链路。

## 可执行的前置依赖，而不是精确日历

```text
收集具体SKU、offer、主体和账号
  → 分平台、分surface复核当前官方规则与后台权限
  → 为每份素材生成ID和SHA-256
  → 取得同精确元组的官方工单与资格主张
  → 六道门逐素材复核
  → 先建立各平台自然基线
  → 每个渠道预注册唯一主指标与单一变量
  → 小规模人工发布/投放（只在获批surface）
  → 按预注册事件量判断继续、修改或停止
```

缺少生产产能、素材库存、平台审核时延和账号基线，所以不能把这些依赖包装成精确30天日历，也不能给固定跨平台转化率。

## 测量与预注册

- `external_to_xhs`：主要指标候选为品牌搜索、主页访问或新关注中的一个；无用户级闭环时只报告同期方向性关联，不声称某篇站外内容带来具体用户。
- `xhs_to_native_conversion`：只有后台权限确认后，才从商品点击、加购、支付、退款或有效留资中选一个主要指标，并写清去重和退款边界。
- `xhs_to_approved_external`：只有获批组件和落地页可审计时才测官方点击/订单；私下发链接不形成可靠归因。
- `owned_retention`：只有合法同意后才测订阅、服务完成、复购或退订；不得拼接未经同意的跨平台身份。

每个实验在执行前填写：假设、direction、资格元组、受众状态、唯一主指标、数据源、基线、测试窗口、最小事件量（由基线/成本推导）、混杂因素、停止条件与风险护栏。当前这些输入为空，因此方案停在资格与规则补证阶段。

## 本轮规则复核入口

- 小红书[专业号行业准入入口](https://ad.xiaohongshu.com/next_help/docs/195c5fe505c71b4b0335a2fe0d61d8e0)与[蒲公英内容审核入口](https://pgy.xiaohongshu.com/help/detail?id=6495c527d1eedeeb48fb18b1f875650e&userType=4)：2026-07-17定位；不足以确认当前精确SKU/账号/surface。
- 知乎[社区/账号行为规则入口](https://www.zhihu.com/term/credit)与[机构号使用规范](https://www.zhihu.com/org_use_norm)：2026-07-17定位；不能替代具体商业账号和外链资格。
- B站[协议汇总](https://www.bilibili.com/blackboard/topic/activity-cn8bxPLzz.html)：2026-07-17定位；具体账号、商业推广、成人商品与外链能力仍待后台/官方当前规则确认。
- 抖音、公众号、微信群：本轮未取得可审计的当前精确规则与后台资格，状态保持 `unknown → blocked`。
