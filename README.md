# redbook-writing

小红书研究、写作与审校的 evidence-first Codex Skill。

这个项目从一个很具体的不满开始：很多“小红书方法论”经不起第二句追问。CES 的出处在哪？所谓 200 初始流量看的是曝光还是浏览？一篇笔记比账号平时高多少，分母是什么？评论区里出现三次“求链接”，能不能代表需求？

`redbook-writing` 不急着给答案。它先建一次可审计的 run，把查询、原始来源、平台主张、账号基线、笔记样本、反例、选题和成稿串起来。最终交付包含成稿，也会交代这篇为什么能写、哪里仍然未知、发出去之后看哪个指标。

适合以下工作：

- 调研一个新类目，找近期可学的账号与内容模式；
- 拆 CES、冷启动、限流、搜索承接等机制说法；
- 从已有证据生成选题、标题、封面、轮播或聊天记录成稿；
- 更新旧研究，只补最近一段时间的变化；
- 审核真人材料、敏感内容、评论参与、商品 CTA 和跨平台承接。

安装入口是 [`redbook-writing/`](redbook-writing/)，方法总览见 [`SKILL.md`](redbook-writing/SKILL.md)。

## 快速开始

```bash
git clone https://github.com/Sciiaok/redbook-writing-skill.git
cp -R redbook-writing ~/.codex/skills/redbook-writing
```

然后把一个真实问题交给它。下面故意用成人亲密关系这个高风险场景举例，因为它会同时触发调研、真实性、敏感规则和商业边界；换成家居、旅行、美妆或职场类目，输入合同不变。

```text
使用 redbook-writing，做一次 discovery。

类目：成人亲密关系
目标读者：第一次和伴侣讨论边界、隐私和安全感的成年人
这次要回答：哪些具体问题值得做成长期栏目
可用材料：公开笔记和评论；没有后台数据
生产条件：不出镜，可以做轮播和透明标注的情境对话
商业目标：暂不卖货
禁区：伪真人、假聊天、未授权截图、竞品评论截流

先建立查询树、停止条件和落库目录。样本不够时不要生成选题。
```

这类输入比“给我十个爆款选题”有用得多。Skill 知道要研究什么，也知道什么时候应该停。

## 它如何看待小红书运营里的黑话

### CES、流量池、冷启动

精确 CES 权重和“每篇固定先给 200 流量”在当前证据里是 `unknown`，不是可以拿来算分的规则。公开工程材料能说明特定推荐入口存在 item cold-start，也能说明内容与行为信号会参与排序，但不能推出全站统一权重，更不能推出创作者侧的固定晋级池。

所以机制分析不用一个总分解释一切，而是拆开看：

```text
曝光 → 点击 → 消费深度 → 赞/藏/评/分享 → 主页/关注 → 合规后链路
```

这些事件的分母不同。收藏高不等于成交近，评论多也不等于账号权重高。

### 限流、养号、垂类标签

80 浏览不能直接推出“被限流”。诊断会先检查页面是否有规则提示，再看内容资格、搜索收录与竞争、需求强度、封面点击、正文承接和主页定位。没有平台提示和可比基线时，统一的 7 天、15 天、30 天恢复倒计时没有意义。

“养号”“互赞互粉”“互动群喂标签”不会被写进方案。这些动作会污染自然基线，也缺少能支持创作者这样操作的一手机制证据。

### 爆款、头部账号、账号基线

“头部”不是一个标签。Schema 分开记录四种 head type：

- `scale`：当前可见体量；
- `recent_performance`：近期连续内容的稳定表现与异常值；
- `audience_precision`：议题和评论是否贴近目标读者；
- `commercial_adjacent`：离实际决策或交易有多近。

单篇爆文、搜索靠前、旧置顶都不能独立定义头部。重点账号先取近期同类、非置顶内容的中位数 `M_recent`，再计算 max / median 的 `outlier_multiple`。少于可比样本门槛时只报告范围，不硬造稳定基线。

### 搜索承接、推荐触达、关系建立、商业转化

每篇内容只能选一个 `primary_job`：

| primary_job | 这篇内容真正要完成的事 |
| --- | --- |
| `recommendation_reach` | 在推荐入口里让正确的人点进来 |
| `search_capture` | 回答一个明确查询，并让答案可被找到 |
| `relationship_building` | 让读者理解账号会持续提供什么 |
| `commercial_conversion` | 在资格已确认的路径里降低决策阻力 |

主指标跟着 job 走。拿不到后链路时可以用代理指标，但必须标 `proxy_only`；公开互动不能反推 CTR、完读、订单或退款。

## 一次 run 里到底保存什么

Prompt 只是入口，Skill 靠一套引用合同工作。默认运行目录如下：

```text
research/xiaohongshu/<YYYY-MM-DD>-<category>/
├── run.yaml
├── research.md
├── query-log.csv
├── source-log.csv
├── claim-ledger.csv
├── accounts.csv
├── posts.csv
├── topics.csv
├── acquisition-channels.csv
├── sku-registry.csv
├── offer-registry.csv
├── authorization-log.csv
└── drafts/
    └── <draft-id>.md
```

`run.yaml` 只接受 `in_progress`、`blocked`、`complete` 三种状态。资料没采完就是 `in_progress`；登录、授权或资格卡住了就是 `blocked`。不能发明一个“基本完成”绕过完成门。

证据在这些对象之间流动：

```mermaid
flowchart LR
    Q["query"] --> S["source"]
    S --> C["claim"]
    Q --> P["post"]
    P --> A["account baseline"]
    P --> T["topic"]
    A --> T
    C --> T
    T --> D["draft"]
    AU["authorization"] --> D
    SKU["SKU / offer eligibility"] --> D
    D --> CH["channel"]
```

每个 ID 都要能回指上游。`TOPIC-` 找不到帖子或需求样本，不能进入 active；`DRAFT-` 没有完成真实性、商业关系和审校合同，也不能写 ready。

字段定义与引用关系在 [`schemas.md`](redbook-writing/references/schemas.md)。项目附了 13 份可复制模板，不需要从空 CSV 开始搭表。

## Reference 不是附录

`SKILL.md` 负责识别任务、选择模式和决定何时停止。真正影响研究与成稿判断的细节，放在七份 reference 里。截至当前版本共 2,006 行：

| 文件 | 它负责的判断 | 已写进去的具体内容 |
| --- | --- | --- |
| [`research-method.md`](redbook-writing/references/research-method.md) · 396 行 | 怎么搜、怎么取样、什么时候算研究完成 | 四种模式、八组关键词、四轮查询、notes-first、近期中位数、高低位与反例、评论编码、去重和停止条件 |
| [`platform-mechanisms.md`](redbook-writing/references/platform-mechanisms.md) · 180 行 | 哪些流量说法有一手依据 | 算法备案、推荐与搜索工程、图文冷启动、查询理解、相关性、重排、榜单和限流的模块边界 |
| [`experience-hypotheses.md`](redbook-writing/references/experience-hypotheses.md) · 166 行 | 公众号、知乎、服务商和操盘复盘该信多少 | 分母/样本/入口/反例四问，B/C/D 经验分级，玄学黑名单，条件性经验和自然准实验 |
| [`current-rules.md`](redbook-writing/references/current-rules.md) · 184 行 | 敏感题材、真实性和商业资格能否继续 | 运行时官方复核、六道门、AI/改编披露、未成年人、成人 SKU、利益关系、导流和隐私信息 |
| [`draft-quality.md`](redbook-writing/references/draft-quality.md) · 399 行 | 有证据以后怎样写出一篇完整内容 | 写作输入合同、载体选择、故事/聊天/轮播门槛、标题封面承诺、proof ledger、双审校和内容生命周期 |
| [`acquisition-and-comments.md`](redbook-writing/references/acquisition-and-comments.md) · 404 行 | 评论、商品承接和跨平台路径能不能做 | 四类 direction、绿黄红评论门、商业撬客阻断、SKU/offer 资格、归因层级、实验预注册和敏感投稿 |
| [`schemas.md`](redbook-writing/references/schemas.md) · 277 行 | 怎样让上述方法可以被机器检查 | run、query、source、claim、account、post、topic、channel、SKU、offer、授权和 draft 的字段、枚举与外键 |

行数只说明范围，不代表这些判断天然正确。因此 reference 里同时保留日期、作用域、原始链接、不可外推部分和冲突来源；规则型文件还要求运行时重新打开官方页面。

七份文件也不会在每次任务里全部灌进上下文。类目调研只加载研究方法和 Schema；解释 CES 时再加载机制与经验审计；碰到成人内容、商品或外跳，才追加现行规则与渠道合同；要成稿时才读写作质量。这样既保留方法深度，也避免不相关的规则挤掉当前样本。

## 这些方法吃了哪些输入

仓库没有把一批文章读完后压成一篇“行业共识”。2026-07-16 的研究快照逐条保存了 59 个查询、130 个去重来源和 75 个可审计 claim。来源结构是：

| 来源层 | 数量 | 主要输入 | 在 Skill 里的用途 |
| --- | ---: | --- | --- |
| 官方 / 规则 / 法律 | 41 | 算法备案、社区规范、蒲公英审核、专业号与商品准入、广告与隐私规则 | 确认当前边界；只在原文对应的产品和 surface 内生效 |
| 工程 / 学术 | 14 | 推荐与搜索生产论文、查询理解、文本图像表示、图文冷启动、多样性重排 | 解释公开可见的系统模块；不还原全站黑箱或精确互动权重 |
| 行业 / 媒体 / 案例 | 73 | 公众号、知乎、行业媒体、数据工具、MCN 与创作者复盘 | 提取用户语言、候选规律和失败模式；逐条保留方法、样本、利益关系与局限 |
| 站内创作者 / 第三方账号 | 2 | 可核验的站内创作者材料与账号来源 | 作为局部观察，不冒充全平台代表样本 |

行业输入不是随手摘几句。单独的证据矩阵复核了 37 篇原文，每一行都记录“方法/样本、能支持什么、主要局限、证据级别”。研究目录还保存了 11 条既有笔记字段样本、20 张“评论区截流”登录态搜索卡、11 条渠道矩阵、11 条 SKU-surface 资格记录和 8 条非 SKU offer 记录。

这里有个刻意保留的难看数字：20 张搜索卡只打开并核验了 1 条详情。它足以证明“评论区截流教程很多”，远远不够证明这种做法有效。因此这部分在综合报告中明确写成缺口，没有包装成评论获客研究，更没有拿来生成头部账号榜单。

### 来源多，不等于多数票通过

每条来源先分 A/B/C/D，再判断它支持的 claim 处于什么状态：`confirmed`、`supported_experience`、`hypothesis`、`contradicted` 或 `unknown`。

| 等级 | 常见材料 | 能做到哪一步 |
| --- | --- | --- |
| A | 当前官方原文、监管材料、原始工程或学术论文 | 只确认原文写明的时期、模块和作用域 |
| B | 方法和样本清楚的独立报告，或多个账号后台且限制明确 | 写“该样本观察到”，不能改写为平台因果 |
| C | 单账号后台、访谈、工具商案例、抽样不完整 | 生成条件性假设，并主动补反例 |
| D | 无原始链接、无分母、只给口诀、收入或涨粉结果 | 留作 rumor / `unknown`，不进入默认策略 |

两条 D 级文章不会合成一个 A 级结论；一篇论文的 A 级也不会自动覆盖论文里转述的二手数字。`claim-ledger.csv` 分开保存支持来源和反证来源，验证器还会阻止 C/D 来源把主张标成 `confirmed`。

### 看看这些输入怎样改变结论

**CES / 流量池：** 两套流传口诀给出不同权重，却都找不到可核的一手技术来源；公开工程材料只能支持特定推荐/搜索模块使用内容和行为信号。最终结论保留为 `unknown`，生产侧改看“曝光 → 点击 → 消费深度 → 互动 → 后链路”。

**标题公式：** 同一账号 PPAN 的相似标题中，`4双鞋×一年三季` 有 1,399 赞，`6件T恤×夏天` 只有 137 赞。这个反例直接否掉了“数字 + 季节/场景就是爆款公式”的写法，标题结构只能作为待测变量。

**评论区截流：** 20 张站内卡片能证明它是活跃教程题材；官方材料同时把竞品评论招揽和私信竞品意向用户列入商业撬客。于是 reference 只保留真实、相关、无 CTA 的贡献型评论，并把截流方案设成硬阻断。

原始账本、专题笔记、证据矩阵和综合结论都在 [`evidence-snapshots/2026-07-16-platform-mechanisms/`](evidence-snapshots/2026-07-16-platform-mechanisms/)。想检查某个数字，不需要相信 README，可以直接沿 `query → source → claim` 往回查。

## 调研方法

### 查询不是只搜一个类目词

Discovery 把词拆成八组：类目、人群自述、场景任务、痛点障碍、方案动作、结果收益、内容形式、反例质疑。最多跑四轮：先建边界，再验证重复模式，然后从笔记反查账号，最后专门补低表现、质疑和最新样本。

综合、热门、最新分别记录。搜索位置只是当时入口和个性化环境下的 observation，不叫“全平台排名”。

### 先笔记，后账号

流程是 notes-first。先打开笔记，核验标题、正文、逐页内容、发布日期和可见指标；确认它值得研究后，再进主页读取近期连续内容。这样能少收一批“因为认识这个账号，所以觉得它是头部”的主观样本。

轮播要逐页记录任务，视频至少看开头、主要证据段和结尾动作。页面只显示合并互动时就原样保存，不能拆出一组看起来更完整的赞藏评。

### 爆文和反例一起留

每个模式都要同时保留普通、高位、低位和 counterexample。反例必须是独立样本，同一条证据换个 ID 不能两边都算。评论会按 `ASK / PAIN / DOUBT / SCENE / INTENT / ACTION / RESONANCE / CORRECT` 编码，但不会据此估算“多少用户都这样想”。

完整方法见 [`research-method.md`](redbook-writing/references/research-method.md)。

## 从选题到成稿

`experimental` 选题至少要绑定一条真实需求或内容样本。`active` 更严格：需要本窗口内至少两个不同账号的有效帖子，还要带可比表现字段和独立反例。零样本阶段只能存 `research_question` 或 `query_candidate`。

进入 draft 后，交付合同包含：

- 证据与不可外推部分；
- 2–3 个标题、封面表达方向；
- 完整正文或逐页分镜；
- 唯一的 `truth_label`；
- 独立的 `commercial_relationship` 与可见披露；
- 事实/功效证明；
- `compliance review` 和 `creative review`；
- 主指标、观察条件和下一次只改的变量。

聊天记录可以是真实记录、授权匿名改编或明确的 `fictional_scenario`。三种来源不能混用。把“情境演绎”藏在 alt、HTML 注释、折叠区或否定句里，验证器会拒绝。

细节在 [`draft-quality.md`](redbook-writing/references/draft-quality.md)。

## 敏感内容、商品与渠道

成人亲密关系、身体、健康或商品内容要逐项过六道门：

```text
purpose → audience_safety → expression → authenticity → commercial → sku_and_transaction
```

商品 CTA 需要精确匹配：

```text
SKU / offer
× platform
× account_scope
× surface
× source_asset_id
× source_asset_sha256
× destination
× platform_ticket
```

自然笔记能发，不代表店铺、广告、私信或官方外跳也能用。同一个 SKU 换了账号、surface 或素材字节，都要重新核验。`CTA=none` 不能激活一条原本没有获批的外跳路径。

跨平台会拆成四条方向，不用一条“全域闭环”含混带过：

```text
external_to_xhs
xhs_to_native_conversion
xhs_to_approved_external
owned_retention
```

没有用户级同意和可审计事件连接时，归因只能写 `directional`。评论区的贡献型参与可以研究；竞品截流、陌生私信、暗号、二维码变体和伪素人话术不会生成。

相关合同在 [`current-rules.md`](redbook-writing/references/current-rules.md) 和 [`acquisition-and-comments.md`](redbook-writing/references/acquisition-and-comments.md)。

## 验证器不是摆设

```bash
python3 redbook-writing/scripts/validate_run.py <run-dir> --strict
```

除 CSV 表头以外，它还会检查引用、状态、资格和披露。现有测试覆盖了这类失败：

- D 级传言被标成 `confirmed`，或 claim 等级高于支持来源；
- 当前平台能力没有本次运行的官方复核，却写成已经开放；
- `recent_performance` 没有近期样本，max 小于 median，或数值出现 NaN / Inf；
- active 选题只来自一个账号，证据和反例复用了同一 ID；
- 商业 CTA 没有同时绑定 SKU、offer、账号、surface、素材哈希和工单；
- 虚构披露藏在 HTML 注释或图片 alt；
- 授权后的稿件又被改过，最终字节与 `authorized_output_sha256` 不一致；
- 外站到小红书没有同意证据，却声称做到了用户级归因。

成功输出也分状态：`VALID_IN_PROGRESS`、`VALID_BLOCKED`、`VALID_COMPLETE`。前两种只说明当前检查点内部一致，不等于研究已经完成。

## 这个仓库怎么验证自己

当前仓库有 84 项自动化测试。除此之外，高风险行为还跑了独立的前向评测：

- `mechanism-ces`
- `niche-discovery-gay`
- `sensitive-story-comments`
- `cross-platform-acquisition`

每个场景至少保留两次针对当前 Skill bundle、不同 execution ID、不同 raw hash 的通过结果。失败输出没有删除：错误使用 `contradicted`、发明 30 天日历、写非法状态枚举等结果仍留在历史中。这样可以看到 Skill 是怎么被打穿、又是在哪条合同上补住的。

评测原文和评分在 [`tests/evals/forward-results.json`](tests/evals/forward-results.json)，发布门在 [`test_eval_artifacts.py`](tests/test_eval_artifacts.py)。

```bash
python3 -m unittest discover -s tests -p 'test_*.py' -v
```

这些测试数量和证据条数描述的是仓库的可审计范围，不是运营效果、用户规模或“爆款率”。

## 四种模式

| mode | 适用问题 | 完成物 |
| --- | --- | --- |
| `mechanism` | 推荐、搜索、限流、规则、评论或准入说法是否成立 | source log + claim ledger |
| `discovery` | 新类目有哪些供给、需求、账号和内容模式 | accounts + posts + topics |
| `refresh` | 旧研究之后发生了什么变化 | 增量查询与状态更新，旧模式保留 |
| `draft` | 已有证据如何写成这篇具体内容 | 完整 draft 合同与两轮审校 |

模式可以依次衔接，但不会混在一次回答里假装都做完。想查机制时默认不写稿；想写稿但 topic 没有证据，就先补最小必要调研。

## 仓库结构

```text
redbook-writing/
├── SKILL.md
├── references/                  # 研究、机制、规则、成稿、渠道、Schema
├── assets/                      # 13 份运行与账本模板
├── scripts/validate_run.py
└── agents/openai.yaml
evidence-snapshots/              # 本次方法研究及来源快照
tests/                           # Validator、Schema 与前向评测
```

`redbook-writing/` 可以单独安装。`evidence-snapshots/` 和 `tests/` 留在仓库里，是为了让方法的来源和失败记录也能被检查。

## 明确不做的事

- 伪造真人故事、聊天、测评、订单、评价或账号数据；
- 用头像、昵称、穿着、语气或关注关系推断敏感身份；
- 绕过登录墙、验证码、滑块、频率限制或平台风控；
- 生成竞品评论截流、批量模板评论、陌生私信和站外暗号；
- 把“18+”当成未成年人安全隔离；
- 在 SKU、授权、平台资格或素材版本不清楚时写可执行商业 CTA。

这不是法律意见，也不替平台做审核决定。它负责把证据缺口和错误前提暴露出来，并把能做的部分写清楚。

## License

仓库目前没有开源许可证。团队复用或商业使用前，请先确认许可。
