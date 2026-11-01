# HERMAN INVESTMENT skill

> 一个把投资 Agent 变成"五维 + 情绪"个股研究员的 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) ——
> 先用"**称重机**"判断生意值多少钱，再用"**投票机**"判断有没有人接盘，每个结论都标证据强度。
> **仅研究支持，非投资建议。**

A personal investment-research skill for Claude / Agent-Skills-compatible clients. It analyzes a single A-share / HK-share stock across **five value dimensions + three sentiment dimensions**, scores it, and evaluates business quality, valuation assumptions and market participation — with every claim graded by evidence strength.

---

## 核心心法（5 条铁律）

1. **先称重机、后投票机**：用价值（五维）选标的，用情绪/资金（投资信仰三维）看时点——绝不反过来。
2. **证据分级**：每个当前结论标 **强**（财报/公告/订单）/ **中**（媒体/研报）/ **弱**（传闻）；绝不靠记忆下当前市场判断。
3. **稀缺 ≠ 便宜，好公司 ≠ 好投资**：卡点真实、公司优秀，贵了仍是差投资。
4. **必须可证伪**：每个判断写下"什么情况说明这个判断错了"。
5. **证据有边界**：户数、季度托管持仓和融资是观察线索，不独立识别投资者身份或预测涨跌；缺关键材料允许暂不评分。

## 五维框架（称重机）

| 维度 | 看什么 |
|---|---|
| ① 供求 / 商业模式 | 竞争对手/份额/壁垒、需求方国内外/订单、定价权（**1-3 年涨价测试**） |
| ② 产业链卡点 | 调用 [serenity-skill](https://github.com/muxuuu/serenity-skill)：先排层、再排公司，找最难扩产的稀缺层 |
| ③ 财务健康度（短期=会不会暴雷） | 现金含量、短债长投、营运资本、合同负债 |
| ④ 未来潜力 / 价值（长期=能不能复利） | ROE/ROIC、自由现金流、毛利净利、管理层 |
| ⑤ 估值安全边际 | PE/PB/PS/PEG、历史分位、前瞻 PE、AH 溢价、安全边际 |

## 投资信仰三维（投票机 · 择时）

- **概念火不火**（热度）、**多少人信**（共识广度）、**资金流入**（真金白银）
- 量化"会不会有人接盘"，**不是价值判断**——用价值选票、用它看时点。
- 危险信号：户数暴增 / 北向机构减持 / 放量滞涨 / 融资见顶 / 估值极值 → 结合日期、覆盖与基本面判断，不用信号数量推算涨跌概率。

## 评分

五维各 1-5 分，加权得分（满分100）：**商业模式 25% / 卡点 15% / 财务健康 25% / 价值 20% / 估值 15%**；情绪是独立择时列、不计入价值分。

---

## 怎样把研究做成可复用判断（v1.2）

| 研究问题 | 方法 |
|---|---|
| 增长是否真实、可持续 | 拆价格/销量/组合/并表与特殊收益，区分归母、扣非、正常化 |
| 利润为何没有现金 | 同期/TTM现金转换、平均余额周转、成长资本开支与债务期限交叉检查 |
| 现价要求兑现什么 | 同口径比较、当前价重算前瞻PE、情景/反向DCF，区分FCFF/FCFE |
| 多只基金是否分散 | 确认目标总额或新增资金，穿透持仓与共同风险，区分产品占比和股票敞口 |
| H股折价是否值得切换 | 新增选择与已有A股换H分开，核对佣金、税费、汇率和流动性 |
| 到了旧观察价是否就便宜 | 先回看盈利假设、确认/失效条件与新证据，修改条件保留理由 |
| 怎样避免越研究越散 | 聚焦能改变结论的证据，有限重试，明确缺口与复核时点 |

入口按场景读取参考文件；日常近况更新无需重复全套深研。只公开可复用方法与代码，不附个人持仓、账户费率、历史交易或日报数据。原有评分权重保留，分数用于研究优先级，不替代安全边际或仓位判断。

## 目录结构

```
SKILL.md                       # 可触发的执行协议
references/
  framework.md                 # 五维检查清单
  research-protocol.md         # 证据、财务口径、同业比较与估值
  portfolio-and-funds.md        # 基金穿透、风险预算、QDII与A/H
  monitoring-and-review.md      # 条件状态、公告/事件与复盘
  data-sources.md              # 接口、数据边界与回退
scripts/
  herman_scorecard.py          # 完整1-5评分加权计算，缺失/非法值报错
  pull_stock_snapshot.py       # 沪深A股资料收集，日期滚动/缺失显式提示
tests/
  test_research_tools.py        # 离线回归：跨年、缺失、匹配与评分
```

## 安装

**Claude Code（用户级）**
```bash
SKILL_DIR="$HOME/.claude/skills/herman-investment"
git clone https://github.com/hermanzzy-crypto/herman-investment-skills.git "$SKILL_DIR"
```

**Agent Skills 通用**：把 `SKILL.md` / `references/` / `scripts/` 放进对应客户端的 `herman-investment/` 目录即可。

## 使用

技能在你这样说时自动触发：
- "用 Herman 框架分析 中际旭创" / "研究一下 XX" / "XX 值不值得买"
- "XX 的 供求关系 / 财务健康度 / 议价能力 / 估值 / 接盘资金面"
- "给这几只股票打分排序"
- "复核这几个基金的组合重叠" / "A股和H股价差是否值得考虑"

脚本也可独立调用：
```bash
# 收集某只沪深A股资料（非完整研究，需核对各节时点）
python3 scripts/pull_stock_snapshot.py 002463

# 五维打分排序
echo '[{"name":"沪电股份","code":"002463","scores":{"business":4,"chokepoint":4,"financial_health":5,"value":5,"valuation":3}}]' \
  | python3 scripts/herman_scorecard.py - --format md
```

## 依赖

- **[akshare](https://github.com/akfamily/akshare)**（实时行情/财报/资金面，免费）：`pip install akshare`
- **[serenity-skill](https://github.com/muxuuu/serenity-skill)**（②产业链卡点维度调用；未装则手动走卡点逻辑）
- 互联互通数据按研究日核查披露制度；季度托管持仓不能代替个股当日交易。港股使用HKEX及可靠行情源，不依赖个人机器脚本。
- 快照工具的交易日期依赖本次交易日历响应，日历过旧则明确缺失；报价未核实时点时不承诺最新。不是历史时点回测器。

离线验证（需要akshare依赖中的pandas）：
```bash
python3 -m unittest discover -s tests -v
```
离线检查不证明当日第三方接口可用，实际研究仍需核查本次响应。

## ⚠️ 免责声明

本项目仅提供**研究方法、推理框架与优先级排序**，**不构成任何投资建议、要约或买卖指令**。评分含主观判断，数据可能滞后。市场有风险，投资需谨慎，决策与盈亏由使用者本人承担。

## License

MIT © hermanzzy-crypto（与 Claude 共建）
