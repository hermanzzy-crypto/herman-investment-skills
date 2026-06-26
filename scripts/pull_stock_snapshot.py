#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HERMAN INVESTMENT — 单票实时快照（喂给五维框架的原始数据）

一次拉齐: 行情/估值(千股千评) + 多年财报(三表) + 股东户数趋势 + 两融 + 龙虎榜 + 北向季度 + 研报。
绝不靠记忆, 全部实时。基准日 = 运行当天。

用法:  python pull_stock_snapshot.py 002463
依赖:  akshare, pandas
注意:  北向个股日度 2024-08 已停, 这里取季度"香港中央结算"; 港股不适用(本脚本面向A股)。
"""
import sys, pandas as pd

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
    print(f"\n######## {code} 实时快照 ########")

    # 行情/估值/换手 (千股千评最稳)
    hr("行情 · 估值 · 换手 (维度①⑤ + 情绪一)")
    try:
        cm = ak.stock_comment_em()
        r = cm[cm["代码"].astype(str) == code]
        if len(r):
            r = r.iloc[0]
            for k in ["名称", "最新价", "涨跌幅", "换手率", "市盈率", "主力成本"]:
                if k in r: print(f"  {k}: {r[k]}")
    except Exception as e: print("  ERR", str(e)[:70])

    # 多年财报三表 (维度③④)
    hr("多年财报: 营收/净利/毛利/净利率/ROE/负债/现金含量 (维度③④)")
    try:
        sym = em(code)
        def ann(fn):
            df = getattr(ak, fn)(symbol=sym); df = df.copy()
            df["_d"] = df["REPORT_DATE"].astype(str).str[:10]
            a = df[df["_d"].str.endswith("12-31")].sort_values("_d", ascending=False).head(4)
            q = df[df["_d"] >= "2026-01-01"].sort_values("_d", ascending=False).head(1)
            return pd.concat([q, a]).drop_duplicates("_d")
        P, B, C = ann("stock_profit_sheet_by_report_em"), ann("stock_balance_sheet_by_report_em"), ann("stock_cash_flow_sheet_by_report_em")
        print(f"  {'期':9}{'营收亿':>8}{'净利亿':>8}{'毛利%':>7}{'净利%':>7}{'ROE%':>6}{'负债%':>7}{'现金含量':>8}")
        for _, p in P.iterrows():
            d = p["_d"]; rev = g(p, "TOTAL_OPERATE_INCOME"); npf = g(p, "PARENT_NETPROFIT"); cost = g(p, "OPERATE_COST")
            gm = (1 - float(cost) / float(rev)) * 100 if rev and cost else None
            nm = (float(npf) / float(rev)) * 100 if rev and npf else None
            br = B[B["_d"] == d]; roe = neg = None
            if len(br):
                br = br.iloc[0]; ta = g(br, "TOTAL_ASSETS"); tl = g(br, "TOTAL_LIABILITIES"); eq = g(br, "TOTAL_PARENT_EQUITY")
                neg = float(tl) / float(ta) * 100 if ta and tl else None
                roe = float(npf) / float(eq) * 100 if npf and eq else None
            cr = C[C["_d"] == d]; cc = None
            if len(cr):
                ocf = g(cr.iloc[0], "NETCASH_OPERATE"); cc = float(ocf) / float(npf) if ocf and npf and float(npf) != 0 else None
            f = lambda x, p=1: f"{x:.{p}f}" if isinstance(x, (int, float)) else "—"
            print(f"  {d[:7]:9}{str(yi(rev)):>8}{str(yi(npf)):>8}{f(gm):>7}{f(nm):>7}{f(roe):>6}{f(neg):>7}{f(cc,2):>8}")
    except Exception as e: print("  ERR", str(e)[:70])

    # 股东户数 (情绪二: 接盘信号)
    hr("股东户数趋势 (情绪二: 暴增=接盘已发生=反指)")
    try:
        gd = ak.stock_zh_a_gdhs_detail_em(symbol=code).sort_values("股东户数统计截止日")
        cols = [c for c in gd.columns if any(k in c for k in ["截止", "户数-本次", "增减比例", "户均持股市值"])]
        print(gd[cols].tail(6).to_string(index=False))
    except Exception as e: print("  ERR", str(e)[:70])

    # 两融 (情绪二三: 杠杆资金)
    hr("两融 融资余额 (情绪二三: 杠杆资金)")
    fn = "stock_margin_detail_szse" if code[0] != "6" else "stock_margin_detail_sse"
    for d in ["20260612", "20260512"]:
        try:
            m = getattr(ak, fn)(date=d)
            r = m[m.iloc[:, 0].astype(str).str.contains(code)]
            if len(r):
                col = [c for c in m.columns if "融资余额" in c][0]
                print(f"  {d}  融资余额={float(r.iloc[0][col])/1e8:.2f}亿")
        except Exception as e: print(f"  {d} ERR", str(e)[:45])

    # 龙虎榜 (情绪三: 游资)
    hr("龙虎榜上榜历史 (情绪三: 游资点火?)")
    try:
        l = ak.stock_lhb_stock_detail_date_em(symbol=code)
        print("  近5次上榜:", list(l["交易日"].tail(5)) if "交易日" in l.columns else "无")
    except Exception as e: print("  ERR(可能从未上榜)", str(e)[:50])

    # 北向季度 (情绪二: 聪明钱)
    hr("北向/社保/QFII 季度 (情绪二: 聪明钱进/出)")
    pfx = "sh" if code[0] == "6" else "sz"
    for d in ["20250930", "20251231", "20260331"]:
        try:
            t = ak.stock_gdfx_free_top_10_em(symbol=pfx + code, date=d)
            sb = t[t["股东名称"].astype(str).str.contains("香港中央结算|社保|QFII|GATES", na=False)]
            names = [f"{r['股东名称'][:8]}={r['占总流通股本持股比例']:.2f}%(Δ{r.get('变动比率','—')})" for _, r in sb.iterrows()]
            print(f"  {d}", " | ".join(names) if names else "前十大无北向/社保/QFII")
        except Exception as e: print(f"  {d} ERR", str(e)[:45])

    # 研报 (情绪一二 + 前瞻PE)
    hr("研报 数量/评级/前瞻PE (情绪一二 + 维度⑤)")
    try:
        rr = ak.stock_research_report_em(symbol=code)
        rcol = next((c for c in rr.columns if "评级" in c), None)
        fwd = next((c for c in rr.columns if "2026" in c and "市盈率" in c), None)
        pe26 = pd.to_numeric(rr[fwd], errors="coerce").replace(0, None).dropna().median() if fwd else None
        print(f"  研报数={len(rr)}  评级={rr[rcol].value_counts().to_dict() if rcol else '—'}  2026前瞻PE中位≈{round(pe26,1) if pe26 else '—'}")
    except Exception as e: print("  ERR", str(e)[:70])

    print("\n（北向个股日度 2024-08 已停, 上为季度口径；港股请用 ccass-tracker。数据基准=运行当天。）")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python pull_stock_snapshot.py <6位股票代码>  例: 002463"); sys.exit(1)
    main(sys.argv[1].strip())
