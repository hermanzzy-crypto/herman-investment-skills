"""Offline regressions: period drift, missing data, matching and scoring boundaries."""
import contextlib
from datetime import date, datetime
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / (name + ".py"))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


snapshot = module("pull_stock_snapshot")
scorecard = module("herman_scorecard")


class ResearchToolsTest(unittest.TestCase):
    def test_periods_roll_across_year_and_exclude_future_report_period(self):
        df = pd.DataFrame({"REPORT_DATE": ["2025-12-31", "2026-09-30", "2026-06-30",
                                            "2026-03-31", "2027-03-31"]})
        rows = snapshot.report_rows(df, date(2027, 1, 3))
        self.assertEqual(rows.iloc[0]["_d"], "2026-09-30")
        self.assertEqual(set(rows["_d"]), set(df["REPORT_DATE"]) - {"2027-03-31"})

    def test_calendar_uses_available_trade_dates_and_lag_window(self):
        dates = list(pd.bdate_range("2026-12-01", "2027-01-05"))
        calendar = pd.DataFrame({"trade_date": dates})
        result = snapshot.margin_dates(calendar, date(2027, 1, 3))
        self.assertEqual(result[0], "20270101")  # synthetic calendar, no weekday guess
        self.assertEqual(len(result), 6)
        self.assertTrue(all(x <= "20270103" for x in result))
        self.assertEqual(len(set(result)), len(result))

    def test_stale_or_empty_calendar_cannot_produce_current_margin_dates(self):
        for days in [[], ["2025-12-31"]]:
            with self.assertRaises(ValueError):
                snapshot.margin_dates(pd.DataFrame({"trade_date": days}), date(2027, 1, 3))

    def test_margin_matches_named_code_column_exactly(self):
        df = pd.DataFrame({"名称": ["002463假匹配", "目标", "其他"],
                           "证券代码": [24630, 2463, 246300], "融资余额": [1, 200000000, 3]})
        result = snapshot.filter_margin(df, "002463")
        self.assertEqual(list(result["融资余额"]), [200000000])
        self.assertTrue(snapshot.filter_margin(df, "600000").empty)
        with self.assertRaises(ValueError):
            snapshot.filter_margin(pd.DataFrame({"名称": ["002463"]}), "002463")

    def test_weighted_score_and_sentiment_independence(self):
        item = {"scores": dict(zip(scorecard.WEIGHTS, [4.5, 4, 3, 4.5, 3])),
                "sentiment": "偏弱"}
        self.assertEqual(scorecard.score_one(item)["composite"], 76.5)
        item["sentiment"] = "极热"
        self.assertEqual(scorecard.score_one(item)["composite"], 76.5)

    def test_missing_or_invalid_scores_do_not_become_ranking(self):
        with self.assertRaises(SystemExit):
            scorecard.score_one({"scores": {"business": 5}})
        for value in [0, 6, True, None, float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(SystemExit):
                scorecard.score_one({"scores": {key: value for key in scorecard.WEIGHTS}})

    def test_snapshot_handles_missing_margin_and_zero_cashflow_offline(self):
        class FrozenDateTime(datetime):
            @classmethod
            def now(cls, tz=None):
                return cls(2027, 1, 3, 12, tzinfo=tz)

        def statement(**kwargs):
            return pd.DataFrame([{"REPORT_DATE": "2026-09-30", "TOTAL_OPERATE_INCOME": 1e8,
                                  "PARENT_NETPROFIT": 1e7, "OPERATE_COST": 0,
                                  "TOTAL_ASSETS": 2e8, "TOTAL_LIABILITIES": 0,
                                  "TOTAL_PARENT_EQUITY": 2e8, "NETCASH_OPERATE": 0}])

        margin = Mock(return_value=pd.DataFrame({"证券代码": ["600000"], "融资余额": [1e8]}))
        holders = Mock(return_value=pd.DataFrame({"股东名称": ["香港中央结算"],
                                                 "占总流通股本持股比例": [1.0]}))
        api = SimpleNamespace(
            stock_comment_em=lambda: pd.DataFrame({"代码": ["002463"], "最新价": [100]}),
            stock_profit_sheet_by_report_em=statement,
            stock_balance_sheet_by_report_em=statement,
            stock_cash_flow_sheet_by_report_em=statement,
            stock_zh_a_gdhs_detail_em=lambda **kw: pd.DataFrame({"股东户数统计截止日": ["2026-09-30"]}),
            tool_trade_date_hist_sina=lambda: pd.DataFrame({"trade_date": ["2026-12-31"]}),
            stock_margin_detail_szse=margin,
            stock_lhb_stock_detail_date_em=lambda **kw: pd.DataFrame({"交易日": ["2026-12-31"]}),
            stock_gdfx_free_top_10_em=holders,
            stock_research_report_em=lambda **kw: pd.DataFrame({"日期": ["2026-12-31"],
                                                               "2027-每股收益": [5.0]}))
        output = io.StringIO()
        with patch.dict("sys.modules", {"akshare": api}), patch.object(snapshot, "datetime", FrozenDateTime), contextlib.redirect_stdout(output):
            snapshot.main("002463")
        margin.assert_called_once_with(date="20261231")
        holders.assert_called_once_with(symbol="sz002463", date="20260930")
        text = output.getvalue()
        self.assertNotIn("ERR", text)
        self.assertNotIn("融资余额=0.00", text)
        self.assertIn("MISSING", text)
        row = next(line for line in text.splitlines() if line.strip().startswith("2026-09-30"))
        numbers = row.split()[1:]
        self.assertEqual(float(numbers[2]), 100.0)  # zero cost => 100% gross margin
        self.assertEqual(float(numbers[-1]), 0.0)   # zero cashflow is real data, not missing
        self.assertIn("2027-每股收益", text)


if __name__ == "__main__":
    unittest.main()
