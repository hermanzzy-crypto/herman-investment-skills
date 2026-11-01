#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HERMAN INVESTMENT — 单票资料收集（喂给五维框架的原始数据）

尝试收集: 行情/估值(千股千评) + 多年财报(三表) + 股东户数趋势 + 两融 + 龙虎榜 + 季度持仓 + 研报。
仅为资料收集辅助；获取时间不等于报价/报告/持仓时点，不证明完成研究。

用法:  python pull_stock_snapshot.py 002463
依赖:  akshare, pandas
注意: 季度香港中央结算为托管披露，不是当前交易；港股不适用。
"""
import sys, pandas as pd
from datetime import date, datetime
from zoneinfo import ZoneInfo


def report_rows(df, today):
    df = df.copy()
    df["_d"] = df["REPORT_DATE"].astype(str).str[:10]
    df = df[df["_d"] <= today.isoformat()].sort_values("_d", ascending=False)
    annual = df[df["_d"].str.endswith("12-31")].head(4)
    return pd.concat([df.head(4), annual]).drop_duplicates("_d")


def margin_dates(calendar, today):
    days = sorted({str(d)[:10] for d in calendar["trade_date"]
                   if str(d)[:10] <= today.isoformat()})
    if not days or (today - date.fromisoformat(days[-1])).days > 15:
        raise ValueError("交易日历未覆盖近期，不能以旧日期冒充最新")
    return list(dict.fromkeys([d.replace("-", "") for d in reversed(days[-5:])]
                             + ([days[-21].replace("-", "")] if len(days) >= 21 else [])))


def filter_margin(df, code):
    col = next((c for c in ["证券代码", "股票代码", "标的证券代码", "代码"] if c in df), None)
    if col is None:
        raise ValueError("无可识别证券代码列")
    return df[df[col].astype(str).str.replace(r"\.0$", "", regex=True).str.zfill(6) == code]

def yi(x):
    try: return round(float(x) / 1e8, 2)
    except: return None

def em(c): return ("SH" if c[0] == "6" else "SZ") + c

def hr(t): print("\n" + "=" * 56 + f"\n {t}\n" + "=" * 56)

def g(r, *cs):
    for c in cs:
        if c in r and pd.notna(r[c]) and r[c] not in ("", "--"): return r[c]
    return None

def main(code):
    import akshare as ak
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    today = now.date()
    print(f"\n######## {code} 资料收集；获取于 {now.isoformat(timespec='seconds')} ########")
    print("各节时点不同；缺失不补0，关键字段须核对官方原文与行情时间戳。")
    periods = []

    # 聚合行情仅作线索，报价时点另核查
    hr("行情 · 估值 · 换手 (维度①⑤ + 情绪一)")
    try:
        cm = ak.stock_comment_em()
        r = cm[cm["代码"].astype(str) == code]
        if len(r):
            r = r.iloc[0]
            for k in ["名称", "最新价", "涨跌幅", "换手率", "市盈率"]:
                if k in r: print(f"  {k}: {r[k]}")
            print("  此处未核实报价时间，不能单独作为最新成交依据；PE须复核口径。")
        else:
            print("  MISSING: 未返回本证券行情")
    except Exception as e: print("  ERR", str(e)[:70])

    # 多年财报三表 (维度③④)
    hr("多年财报: 营收/净利/毛利/净利率/ROE/负债/现金含量 (维度③④)")
    try:
        sym = em(code)
        def ann(fn):
            return report_rows(getattr(ak, fn)(symbol=sym), today)
        P, B, C = ann("stock_profit_sheet_by_report_em"), ann("stock_balance_sheet_by_report_em"), ann("stock_cash_flow_sheet_by_report_em")
        periods = list(B["_d"].sort_values(ascending=False).head(3))
        print("  利润/现金流为累计值；简化ROE=归母净利/期末归母权益，非加权、未年化。")
        print("  报告期不是披露日，需核对原文与重述；非历史可得数据回测。")
        print(f"  {'报告期':11}{'营收亿':>8}{'净利亿':>8}{'毛利%':>7}{'净利%':>7}{'简化ROE%':>9}{'负债%':>7}{'现金含量':>8}")
        for _, p in P.iterrows():
            d = p["_d"]; rev = g(p, "TOTAL_OPERATE_INCOME"); npf = g(p, "PARENT_NETPROFIT"); cost = g(p, "OPERATE_COST")
            gm = (1 - float(cost) / float(rev)) * 100 if rev and cost is not None else None
            nm = (float(npf) / float(rev)) * 100 if rev and npf is not None else None
            br = B[B["_d"] == d]; roe = neg = None
            if len(br):
                br = br.iloc[0]; ta = g(br, "TOTAL_ASSETS"); tl = g(br, "TOTAL_LIABILITIES"); eq = g(br, "TOTAL_PARENT_EQUITY")
                neg = float(tl) / float(ta) * 100 if ta and tl is not None else None
                roe = float(npf) / float(eq) * 100 if npf is not None and eq else None
            cr = C[C["_d"] == d]; cc = None
            if len(cr):
                ocf = g(cr.iloc[0], "NETCASH_OPERATE"); cc = float(ocf) / float(npf) if ocf is not None and npf is not None and float(npf) > 0 else None
            f = lambda x, p=1: f"{x:.{p}f}" if isinstance(x, (int, float)) else "—"
            print(f"  {d:11}{str(yi(rev)):>8}{str(yi(npf)):>8}{f(gm):>7}{f(nm):>7}{f(roe):>9}{f(neg):>7}{f(cc,2):>8}")
    except Exception as e: print("  ERR", str(e)[:70])

    # 股东户数不能独立识别投资者身份
    hr("股东户数趋势 (参与广度线索，非投资者身份或涨跌预测)")
    try:
        gd = ak.stock_zh_a_gdhs_detail_em(symbol=code).sort_values("股东户数统计截止日")
        cols = [c for c in gd.columns if any(k in c for k in ["截止", "公告", "户数-本次", "增减比例", "户均持股市值"])]
        print(gd[cols].tail(6).to_string(index=False))
    except Exception as e: print("  ERR", str(e)[:70])

    # 两融 (情绪二三: 杠杆资金)
    hr("两融 融资余额 (情绪二三: 杠杆资金)")
    fn = "stock_margin_detail_szse" if code[0] != "6" else "stock_margin_detail_sse"
    try:
        dates = margin_dates(ak.tool_trade_date_hist_sina(), today)
    except Exception as e:
        dates = []
        print("  MISSING: 交易日历不可得", str(e)[:80])
    for d in dates:
        try:
            m = getattr(ak, fn)(date=d)
            r = filter_margin(m, code)
            if len(r):
                col = [c for c in m.columns if "融资余额" in c][0]
                print(f"  {d}  融资余额={float(r.iloc[0][col])/1e8:.2f}亿")
            else:
                print(f"  {d} MISSING: 未返回本证券记录，不补0")
        except Exception as e: print(f"  {d} ERR", str(e)[:45])

    # 龙虎榜 (情绪三: 游资)
    hr("龙虎榜上榜历史 (情绪三: 游资点火?)")
    try:
        l = ak.stock_lhb_stock_detail_date_em(symbol=code)
        col = next((c for c in ["交易日", "交易日期", "上榜日"] if c in l), None)
        print("  最近披露上榜日:", list(l[col].astype(str).sort_values(ascending=False).head(5)) if col else "MISSING: 日期字段不可识别")
    except Exception as e: print("  ERR（不等于从未上榜）", str(e)[:50])

    # 季度托管/股东披露，不能代表当日买卖
    hr("季度披露持仓 (托管口径非最终身份，非当前交易)")
    pfx = "sh" if code[0] == "6" else "sz"
    if not periods:
        print("  MISSING: 财报期不可得，不猜季度日期")
    for period in periods:
        d = period.replace("-", "")
        try:
            t = ak.stock_gdfx_free_top_10_em(symbol=pfx + code, date=d)
            sb = t[t["股东名称"].astype(str).str.contains("香港中央结算|社保|QFII|GATES", na=False)]
            names = [f"{r['股东名称'][:8]}={r['占总流通股本持股比例']:.2f}%(Δ{r.get('变动比率','—')})" for _, r in sb.iterrows()]
            print(f"  {d}", " | ".join(names) if names else "前十大无北向/社保/QFII")
        except Exception as e: print(f"  {d} ERR", str(e)[:45])

    # 研报 (情绪一二 + 前瞻PE)
    hr("研报署名预测样本 (非当前一致预期)")
    try:
        rr = ak.stock_research_report_em(symbol=code)
        dcol = next((c for c in ["日期", "报告日期", "发布日期"] if c in rr), None)
        if dcol is None:
            print("  MISSING: 无研报发布日期，不计算当前共识")
        else:
            rr = rr.sort_values(dcol, ascending=False)
            cols = [c for c in rr if c == dcol or any(k in c for k in ["机构", "评级", "每股收益", "净利润", "名称"])]
            print(rr[cols].head(5).to_string(index=False))
            print("  上为最新披露样本而非一致预期；按机构/日期/年份去重后，用已核实当前价÷EPS重算PE。")
    except Exception as e: print("  ERR", str(e)[:70])

    print("\n资料收集完成不等于研究完成；请逐节核查日期与缺口。港股使用HKEX等来源。")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] in ("-h", "--help"):
        print("用法: python3 pull_stock_snapshot.py <沪深A股6位代码>  例: 002463；资料收集非完整研究")
        sys.exit(0 if len(sys.argv) == 2 and sys.argv[1] in ("-h", "--help") else 1)
    if not (sys.argv[1].isdigit() and len(sys.argv[1]) == 6 and sys.argv[1][0] in "036"):
        sys.exit("仅支持沪深A股代码；港股与北交所请使用对应市场来源")
    main(sys.argv[1].strip())
