# HERMAN INVESTMENT skill

> 一个把投资 Agent 变成"五维 + 情绪"个股研究员的 [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) ——
> 先用"**称重机**"判断生意值多少钱，再用"**投票机**"判断有没有人接盘，每个结论都标证据强度。
> **仅研究支持，非投资建议。**

A personal investment-research skill for Claude / Agent-Skills-compatible clients. It analyzes a single A-share / HK-share stock across **five value dimensions + three sentiment dimensions**, scores it, and tells you both *what the business is worth* and *whether there's anyone left to take the shares higher* — with every claim graded by evidence strength.

---

## 核心心法（5 条铁律）

1. **先称重机、后投票机**：用价值（五维）选标的，用情绪/资金（投资信仰三维）看时点——绝不反过来。
2. **证据分级**：每个当前结论标 **强**（财报/公告/订单）/ **中**（媒体/研报）/ **弱**（传闻）；绝不靠记忆下当前市场判断。
3. **稀缺 ≠ 便宜，好公司 ≠ 好投资**：卡点真实、公司优秀，贵了仍是差投资。
4. **必须可证伪**：每个判断写下"什么情况说明这个判断错了"。
5. **散户户数暴增 = 反指**（接盘已发生），不是继续涨的信号。

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
- 危险信号：户数暴增 / 北向机构减持 / 放量滞涨 / 融资见顶 / 估值极值 → 任意 2-3 个出现即警惕。

## 评分

五维各 1-5 分，加权合成 0-100：**商业模式 25% / 卡点 15% / 财务健康 25% / 价值 20% / 估值 15%**；情绪是独立择时列、不计入价值分。

---

## 目录结构

```
SKILL.md                       # 可触发的执行协议
references/
  framework.md                 # 五维框架清单
  data-sources.md              # 三维博弈指标表 + akshare 接口 + 5 个数据陷阱
scripts/
  herman_scorecard.py          # 五维加权打分（输入 JSON → 0-100 分 + 排序表）
  pull_stock_snapshot.py       # 一键拉单票实时快照（行情/三表/户数/两融/龙虎榜/北向/研报）
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

脚本也可独立调用：
```bash
# 拉某只票的实时快照
python3 scripts/pull_stock_snapshot.py 002463

# 五维打分排序
echo '[{"name":"沪电股份","code":"002463","scores":{"business":4,"chokepoint":4,"financial_health":5,"value":5,"valuation":3}}]' \
  | python3 scripts/herman_scorecard.py - --format md
```

## 依赖

- **[akshare](https://github.com/akfamily/akshare)**（实时行情/财报/资金面，免费）：`pip install akshare`
- **[serenity-skill](https://github.com/muxuuu/serenity-skill)**（②产业链卡点维度调用；未装则手动走卡点逻辑）
- 注意：北向个股日度持股自 **2024-08-16 已停**（只剩全市场日度 + 季度香港中央结算）。

## ⚠️ 免责声明

本项目仅提供**研究方法、推理框架与优先级排序**，**不构成任何投资建议、要约或买卖指令**。评分含主观判断，数据可能滞后。市场有风险，投资需谨慎，决策与盈亏由使用者本人承担。

## License

MIT © hermanzzy-crypto（与 Claude 共建）
