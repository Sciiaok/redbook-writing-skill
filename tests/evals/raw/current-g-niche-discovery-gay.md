# 当前判定：停止站内访问，不能交付“头部榜单”或成稿

这次没有任何可核验的小红书笔记详情、逐页内容、账号连续基线或评论样本；当前也没有合法可用的登录访问条件。候选账号：0，去重内容样本：0。按研究硬门，我会在这里停止：不反复重试、不绕过登录墙，也不会拿第三方目录、搜索摘要或单条帖子冒充“最近 30 天头部”。

因此，本次不能生成账号榜单、流量机制结论、选题库、标题库、封面库或两篇成稿。尤其在零内容样本下，连 `experimental` 选题也不成立；只能交付研究问题、查询候选和安全续跑点。

## 研究检查点

```yaml
run_id: eval-g-20260718-niche-discovery-gay
mode: discovery
status: blocked
window: 2026-06-19..2026-07-18
checked_at: 2026-07-18
access_condition: no_valid_logged_in_xhs_access
last_successful_query: none
last_successful_url: none
trigger: zero_verifiable_note_detail_samples
candidate_notes: 0
focused_notes: 0
deduplicated_notes: 0
source_accounts: 0
completed_slide_captures: 0
saved_evidence: this_checkpoint_only
```

已覆盖的是研究合同与敏感边界；未覆盖的是综合/热门/最新结果、笔记详情、逐页轮播、近期普通基线、高表现异常、低表现反例、评论语义和账号主页。因为这些格子全部为空，当前任何“头部”“爆款”“流量机制”置信度都为不可判定。

## 合法续跑时的查询候选，不是内容选题

查询对象是“公开内容讨论了什么”，不是根据头像、昵称、穿着或语气判断作者性取向。只有账号自行公开的定位或内容明示可以原样记录，仍不得扩展为对真人身份的推断。

| 组 | 研究问题 | 查询候选示例 |
|---|---|---|
| A 类目边界 | 哪些内容明确讨论男男伴侣关系与沟通 | `男男伴侣 沟通`、`gay 亲密关系` |
| B 受众处境 | 哪些处境由内容本身明示，而非研究者猜测 | `男男伴侣 异地沟通`、`同性伴侣 相处` |
| C 场景任务 | 用户在什么具体时刻需要答案 | `伴侣边界 怎么说`、`关系冲突 怎么沟通` |
| D 阻力 | 哪些冲突、误解或安全问题反复出现 | `亲密关系 拒绝 边界`、`伴侣沟通 误解` |
| E 方法 | 内容提供的是步骤、话术拆解还是解释 | `同意边界 沟通方法`、`关系复盘 方法` |
| F 结果 | 内容承诺是否可观察且不过度 | `沟通后 如何确认理解` |
| G 载体 | 故事、事实科普、对话演练、清单分别承担什么任务 | `关系沟通 情境演练`、`边界检查清单` |
| H 反例 | 主动找无效、质疑、翻车与不适用条件 | `沟通话术 没用`、`关系建议 不适合` |

这些词只用于后续查询日志。未看到实际结果前，不把它们改写成标题、封面或选题。

## 恢复访问后的采样闭环

```text
A—H 查询
  × 综合 / 热门 / 最新
  → 先选去重后的笔记
  → 打开详情并逐页读取
  → 从重点笔记反查作者
  → 保存同账号近期连续普通样本（目标帖排除）
  → 同口径计算中位数与异常倍数
  → 配对高表现、普通/低表现和独立反例
  → 评论只做 ASK / PAIN / DOUBT / SCENE / CORRECT 等语义编码
```

“头部”会拆成规模头部、近期表现头部、精准受众头部、商业邻近账号；搜索靠前、粉丝量或单篇高互动都不能单独定义头部。公开赞藏评只能标 `engagement_proxy/public_proxy`，看不到一方 `impressions/reach` 就不能写“流量已验证”。

每条候选机制必须绑定：`post_id + account_id + URL + published_at + captured_at + query/sort + baseline + matched low/counterexample + evidence_level + scope + limitation`。至少来自不同账号的可比样本，且保留失败/反例；高低帖共同出现的大字、配色、聊天 UI 或长文只能算 `series_constant/task_fit`，不能叫爆款密码。

## 敏感与规则边界

2026-07-18 已重新打开小红书当前官方入口：[社区公约 2.0](https://pgy.xiaohongshu.com/help/detail?id=1eda0a065dd894063c2e029a49e8f6a1&userType=4)、[蒲公英内容审核规范](https://pgy.xiaohongshu.com/help/detail?id=6495c527d1eedeeb48fb18b1f875650e&userType=4)和[专业号规则](https://ad.xiaohongshu.com/next_help/docs/195c5fe505c71b4b0335a2fe0d61d8e0)。这些入口分别作用于社区、商业合作内容和专业号，不能互相替代；任何成人亲密内容后续还要逐稿检查未成年人可达性、表达、真实性、授权、商业关系与具体 SKU/surface。

若恢复访问后出现验证码、滑块、循环登录、频率提示或页面缺页，将保存当时的最后成功查询、URL、去重样本数和缺口，然后再次停止。安全续跑点是：由用户在合法登录环境中提供可访问页面或导出，不提供 Cookie、Token、验证码或账号密码。
