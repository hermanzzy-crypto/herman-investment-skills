#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HERMAN INVESTMENT 五维评分卡（可复现打分 + 排序）

五维(各打 1-5 分, 5 最好) 加权合成综合分(0-100):
  business(商业模式) 25 | chokepoint(产业链卡点) 15 | financial_health(财务健康) 25
  | value(未来潜力/价值) 20 | valuation(估值安全边际, 便宜=高分) 15
sentiment(情绪/择时) 与 evidence(证据强度) 仅作标注, 不计入综合分。

用法:
  python herman_scorecard.py --template            # 打印单只 JSON 模板
  python herman_scorecard.py stocks.json           # 单只或数组, 输出 JSON
  python herman_scorecard.py stocks.json --format md   # 输出 markdown 排序表
  cat stocks.json | python herman_scorecard.py - --format both
"""
from __future__ import annotations
import argparse, json, math, sys

WEIGHTS = {"business": 25, "chokepoint": 15, "financial_health": 25, "value": 20, "valuation": 15}
LABELS = {"business": "商业模式", "chokepoint": "卡点", "financial_health": "财务健康",
          "value": "价值潜力", "valuation": "估值"}

TEMPLATE = {
    "name": "示例公司", "code": "000000",
    "scores": {k: 3 for k in WEIGHTS},          # 1-5
    "sentiment": "健康/偏热/极热/危险",            # 择时位置, 不计分
    "evidence": "强/中/弱",                        # 证据强度, 不计分
    "note": "一句话点评（卡住的环节/排序原因/主要风险）",
}


def _n(v, label):
    try:
        x = float(v)
    except (TypeError, ValueError):
        raise SystemExit(f"{label} 必须是 1-5 的数字, 收到 {v!r}")
    if isinstance(v, bool) or not math.isfinite(x) or not 1 <= x <= 5:
        raise SystemExit(f"{label} 必须在 1-5 之间且为有限数字, 收到 {v!r}")
    return x


def score_one(d: dict) -> dict:
    if not isinstance(d, dict):
        raise SystemExit("每只公司的输入必须是 JSON 对象")
    s = d.get("scores", {})
    if not isinstance(s, dict) or any(k not in s for k in WEIGHTS):
        raise SystemExit("五维评分必须完整；资料不足请暂不评分，不以0或中性分补齐")
    total = 0.0
    detail = {}
    for k, w in WEIGHTS.items():
        r = _n(s[k], f"scores.{k}")
        pts = r / 5.0 * w
        detail[k] = {"score": r, "weight": w, "points": round(pts, 2)}
        total += pts
    total = round(total, 1)
    verdict = ("核心研究优先" if total >= 75 else "值得跟踪" if total >= 60
               else "谨慎/观察" if total >= 45 else "低优先/回避")
    return {"name": d.get("name", ""), "code": d.get("code", ""),
            "composite": total, "verdict": verdict,
            "sentiment": d.get("sentiment", ""), "evidence": d.get("evidence", ""),
            "note": d.get("note", ""), "detail": detail}


def to_md(results: list) -> str:
    results = sorted(results, key=lambda r: r["composite"], reverse=True)
    head = "| 排名 | 公司 | 代码 | " + " | ".join(LABELS.values()) + " | **综合分** | 情绪 | 证据 | 一句话 |"
    sep = "|" + "---|" * (4 + len(LABELS) + 3)
    lines = ["# HERMAN INVESTMENT 五维评分排序", "",
             f"> 权重：商业模式25% / 卡点15% / 财务健康25% / 价值20% / 估值15%；情绪与证据仅标注。", "",
             head, sep]
    for i, r in enumerate(results, 1):
        cells = [f"{r['detail'][k]['score']:g}" for k in WEIGHTS]
        lines.append(f"| {i} | {r['name']} | {r['code']} | " + " | ".join(cells) +
                     f" | **{r['composite']}** | {r['sentiment']} | {r['evidence']} | {r['note']} |")
    lines += ["", "> 研究优先级排序，非投资建议；评分含主观判断、数据有滞后。"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser(description="HERMAN INVESTMENT 五维评分卡")
    ap.add_argument("input", nargs="?", help="JSON 文件或 '-' 读 stdin (单只对象或数组)")
    ap.add_argument("--template", action="store_true")
    ap.add_argument("--format", choices=["json", "md", "both"], default="json")
    a = ap.parse_args()
    if a.template:
        print(json.dumps(TEMPLATE, ensure_ascii=False, indent=2)); return
    if not a.input:
        ap.error("需要输入文件或 --template")
    raw = sys.stdin.read() if a.input == "-" else open(a.input, encoding="utf-8").read()
    data = json.loads(raw)
    items = data if isinstance(data, list) else [data]
    results = [score_one(x) for x in items]
    if a.format in ("json", "both"):
        print(json.dumps(sorted(results, key=lambda r: r["composite"], reverse=True),
                         ensure_ascii=False, indent=2))
    if a.format == "both":
        print("\n---\n")
    if a.format in ("md", "both"):
        print(to_md(results))


if __name__ == "__main__":
    main()
