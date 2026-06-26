# 数据源 playbook（akshare 接口 / 方法）

图例：✅ 已实测可抓 | 🟡 高把握未实测 | ⚠️ 能抓但有坑。基准日以拉取当天为准，绝不靠记忆。

## 称重机（五维）核心数据

| 维度 | 要什么 | akshare 接口 / 方法 |
|---|---|---|
| 行情/市值/PE | 现价、市值、52周、换手 | finance-analyst `query.py <code>`；`stock_comment_em`（含换手/PE/主力成本） ✅ |
| 财务三表 | 营收/净利/毛利/净利率/ROE/负债/现金流 | `stock_profit_sheet_by_report_em`、`stock_balance_sheet_by_report_em`、`stock_cash_flow_sheet_by_report_em`（symbol=SH/SZ+code）✅ |
| 营运资本 | 应收/存货/合同负债/货币资金 | `stock_balance_sheet_by_report_em`（ACCOUNTS_RECE / INVENTORY / CONTRACT_LIAB / MONETARYFUNDS）✅ |
| 前瞻PE/评级 | 一致预期PE、买入占比 | `stock_research_report_em`（含 2026/2027 盈利预测-市盈率、东财评级）✅ |
| 十大流通股东 | 实控人/北向/社保/QFII | `stock_gdfx_free_top_10_em`（symbol=sz/sh+code, date=季末）✅ |

> 现金含量 = NETCASH_OPERATE / PARENT_NETPROFIT；毛利率 = 1 − OPERATE_COST/TOTAL_OPERATE_INCOME；ROE = PARENT_NETPROFIT/TOTAL_PARENT_EQUITY；负债率 = TOTAL_LIABILITIES/TOTAL_ASSETS。

## 投票机·维度一：概念火不火（热度/关注度）

| 指标 | 衡量什么 | 数据源 | 解读阈值 |
|---|---|---|---|
| 概念板块涨幅/排名 | 概念相对大盘超额、是否领涨 | `stock_board_concept_name_em` + `_hist_em` 🟡 | 跑赢沪深300、居涨幅榜前列＝火 |
| 换手率 | 博弈激烈度 | `stock_zh_a_hist`（含换手率列）/ `stock_comment_em` ✅ | 日换手 >10%＝高度博弈；>20%＝过热 |
| 东财人气榜排名 | 散户关注度 | `stock_hot_rank_em` 🟡 | 进前50/快速上升＝散户涌入 |
| 千股千评·关注指数 | 市场参与意愿 | `stock_comment_em` 🟡 | 关注指数/参与度上行 |
| 近一月研报数 | 卖方关注激增 | `stock_research_report_em` ✅ | 月研报数环比翻倍＝机构在喊 |
| 机构调研次数 | 机构关注 | `stock_jgdy_detail_em` 🟡 | 调研机构数激增 |
| 舆论/搜索热度 | 散户舆论温度 | WebSearch 新闻数 / 百度指数 ✅ | 新闻量、搜索量陡增 |

## 投票机·维度二：是否足够多人相信（共识/参与广度）

| 指标 | 衡量什么 | 数据源 | 解读 |
|---|---|---|---|
| 股东户数变化 | 参与广度 | `stock_zh_a_gdhs_detail_em` ✅ | 温和增＝信仰扩散；**暴增＝接盘已发生（反指！）** |
| 融资余额/买入占比 | 杠杆信仰 | `stock_margin_detail_szse` ✅ | 融资余额/流通市值上行＝杠杆在信 |
| 研报"买入"占比 | 卖方共识 | `stock_research_report_em` ✅ | 买入占比>80%＝高度一致（也＝拥挤） |
| 公募持仓家数变化 | 机构信仰 | `stock_fund_stock_holder` 🟡 | 持有基金家数上升 |
| 北向/社保/QFII（季度） | 聪明钱信仰 | `stock_gdfx_free_top_10_em` ✅ | 香港中央结算/社保季度增持 |
| 估值分位(PE/PB) | 信仰已 price-in 多少 | 研报前瞻PE ✅ | 越高＝越拥挤＝接盘空间越小 |

## 投票机·维度三：是否有资金流入（真金白银）

| 指标 | 衡量什么 | 数据源 | 解读 |
|---|---|---|---|
| 龙虎榜净买入+游资席位 | 游资点火 | `stock_lhb_stock_detail_em` / `_yyb_detail_em` / `_date_em` ✅ | 知名游资席位净买入＝点火 |
| 融资余额净增 | 杠杆流入 | `stock_margin_detail_szse` ✅ | 单日/单周融资净增 |
| 全市场北向净流入 | 北向情绪(大盘) | `stock_hsgt_fund_flow_summary_em` ✅ | 个股日度已停，只能看全市场 |
| 港股南向(CCASS) | 南向加减仓(港股) | 自建 `ccass-tracker/ccass_daily.py` ✅ | A00003/04(ChinaClear) 持股日变化 |
| 主力/超大单净流入 | 资金流(推断) | `stock_individual_fund_flow` ⚠️ | 推断非真身，仅作情绪参考 |
| 大宗交易折溢价 | 机构进出 | `stock_dzjy_mrtj_em` 🟡 | 折价大＝机构出货 |
| 量能 | 资金活跃度 | `stock_zh_a_hist`（成交额）✅ | 成交额阶梯放大＝资金进场 |

## ⚠️ 6 个数据陷阱（不懂会被误导）

1. **"主力资金流向"是按单子大小推断的伪身份**——量化/游资拆单都会混进"大单"，≠真机构。
2. **北向个股日度持股 2024-08-16 已停**，只剩全市场日度净流入 + 季度香港中央结算；港股南向才有 CCASS 日度。
3. **股东户数暴增常是反指**——它说"散户已接盘"，不是"还会涨"。
4. **全是滞后指标**（户数/北向/持仓多为季度）——你看到的是"已发生"。
5. **反身性双向**——指标向上自我强化，信号一裂同样猛地反向。
6. **"主力成本"是弱信号、勿当真身**——它是 `stock_comment_em` 按"近期换手加权成交均价 / 筹码成本模型"**算出来的估算值**，**不是真实已知的某主力成本**；各平台(东财/同花顺/通达信)给的值都不一样，和"主力资金流向"同属"推断非真身"。**只能当"近期进场资金大致成本带"的软参考（证据=弱）**：价格在其下方 ≈ 近期买盘多浮亏（可能抛压、也可能支撑），别当事实。判断成本/筹码请优先用下方附录的"真身"数据。

## 附录：判断"谁在什么价位 / 成本"用哪些数据（按可靠度）

| 信号 | 可靠度 | 为什么硬 | akshare 接口 |
|---|---|---|---|
| 龙虎榜席位买入额/价 | 🟢强（仅上榜日）| 真实成交席位，看得到游资/机构具体买卖 | `stock_lhb_stock_detail_em` / `_yyb_detail_em` |
| 大宗交易价格 | 🟢强 | 真实成交价 + 折溢价 | `stock_dzjy_mrtj_em` |
| 定增/配股价 | 🟢强 | 参与方的真实成本 | 巨潮公告 / `stock_qbzf_em` |
| 股东户数变化（季度）| 🟢强 | 真实，反映散户进出 | `stock_zh_a_gdhs_detail_em` |
| 北向/机构持仓（季度）| 🟢强 | 真实持股变化（虽无成本）| `stock_gdfx_free_top_10_em` |
| 筹码分布（平均成本/获利比例/成本集中度）| 🟡中 | 比"主力成本"透明，但**仍是同一类模型估算** | `stock_cyq_em` |
| **主力成本 / 主力资金流向** | 🔴弱 | **算法推断、非真身、各平台不一** | `stock_comment_em` / `stock_individual_fund_flow` |

> **铁律**：判断"谁在什么价位/成本"，优先信 **龙虎榜席位、大宗交易、定增价、股东户数、北向机构持仓** 这些"真身"数据；**"主力成本 / 主力资金"只作弱参考，绝不当事实下结论。**

## 环境坑速记
- 港股报价 akshare 偶发 `RemoteDisconnected`，重试一次或改 WebSearch。
- `stock_a_indicator_lg` 在部分 akshare 版本不存在；估值用 `stock_comment_em` 的 PE 或研报前瞻 PE。
- A股 EM 三表 symbol 格式：`SH`/`SZ` + 代码（6开头=SH，其余=SZ）。
- 千股千评 PE 在公司刚暴雷/亏损时会失真（TTM 基数极小），需结合前瞻 PE 判断。
