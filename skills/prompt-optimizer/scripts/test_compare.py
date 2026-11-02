"""Tests for compare.py.

Run from the repository root:
    python3 -m unittest discover -s skills/prompt-optimizer/scripts -p "test_*.py"
"""

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import compare  # pyright: ignore[reportImplicitRelativeImport]


class TestStatistics(unittest.TestCase):
    def test_wilson_bounds(self):
        lo, hi = compare.wilson(35, 50, 1.96)
        self.assertAlmostEqual(lo, 0.562, places=3)
        self.assertAlmostEqual(hi, 0.809, places=3)
        self.assertEqual(compare.wilson(0, 0, 1.96), (0.0, 0.0))

    def test_mcnemar_exact(self):
        self.assertAlmostEqual(compare.mcnemar_exact(2, 9), 0.0654, places=3)
        self.assertEqual(compare.mcnemar_exact(0, 0), 1.0)
        self.assertAlmostEqual(compare.mcnemar_exact(0, 5), 0.0625, places=4)

    def test_bootstrap_is_deterministic_and_brackets_delta(self):
        pairs = [(1, 0)] * 2 + [(0, 1)] * 9 + [(1, 1)] * 30 + [(0, 0)] * 9
        lo1, hi1 = compare.bootstrap_delta(pairs, 2000)
        lo2, hi2 = compare.bootstrap_delta(pairs, 2000)
        self.assertEqual((lo1, hi1), (lo2, hi2))
        self.assertLess(lo1, 7 / 50)
        self.assertGreater(hi1, 7 / 50)

    def test_alpha_controls_interval_width(self):
        pairs = [(1, 0)] * 2 + [(0, 1)] * 9 + [(1, 1)] * 30 + [(0, 0)] * 9
        lo90, hi90 = compare.bootstrap_delta(pairs, 2000, 0.10)
        lo95, hi95 = compare.bootstrap_delta(pairs, 2000, 0.05)
        self.assertGreaterEqual(hi95 - lo95, hi90 - lo90)


class TestLoad(unittest.TestCase):
    def write(self, lines):
        tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding="utf-8")
        tmp.write("\n".join(lines))
        tmp.close()
        return Path(tmp.name)

    def test_load_valid_and_errors(self):
        path = self.write(
            [
                json.dumps({"case_id": "c1", "variant": "baseline", "passed": True}),
                json.dumps({"case_id": "c2", "variant": "baseline", "passed": 0}),
                "not json",
                json.dumps({"case_id": "c3", "variant": "A"}),
                json.dumps({"case_id": "c1", "variant": "baseline", "passed": False}),
            ]
        )
        records, errors = compare.load(path)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(errors), 3)
        self.assertTrue(records[0]["passed"])
        self.assertFalse(records[1]["passed"])
        path.unlink()

    def test_missing_baseline(self):
        path = self.write([json.dumps({"case_id": "c1", "variant": "A", "passed": True})])
        stats = compare.summarize(compare.load(path)[0])
        self.assertEqual(compare.compare(stats, "baseline", 0.05, 100, "holm"), [])
        path.unlink()


class TestInputNormalization(unittest.TestCase):
    def test_null_stratum_becomes_unset(self):
        record = {"case_id": "c1", "variant": "baseline", "passed": True, "stratum": None}
        path = _write_jsonl([record])
        records, errors = compare.load(path)
        self.assertEqual(errors, [])
        self.assertEqual(records[0]["stratum"], "unset")
        path.unlink()

    def test_numeric_strings_and_bom(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "passed": "true", "tokens": "210", "latency_ms": "900"},
            {"case_id": "c1", "variant": "A", "passed": "FALSE", "tokens": 470, "latency_ms": 1400},
        ]
        path = _write_jsonl(rows, encoding="utf-8-sig")
        records, errors = compare.load(path)
        self.assertEqual(errors, [])
        self.assertTrue(records[0]["passed"])
        self.assertFalse(records[1]["passed"])
        self.assertEqual(records[0]["tokens"], 210.0)
        self.assertEqual(records[0]["stratum"], "unset")
        path.unlink()

    def test_pass_fail_words_and_trimmed_ids(self):
        rows = [
            {"case_id": " c1 ", "variant": " baseline ", "passed": "pass"},
            {"case_id": "c1", "variant": "A", "passed": "fail"},
            {"case_id": "", "variant": "A", "passed": True},
        ]
        records, errors = compare.load(_write_jsonl(rows))
        self.assertEqual(len(records), 2)
        self.assertEqual(len(errors), 1)
        self.assertEqual(records[0]["case_id"], "c1")
        self.assertEqual(records[0]["variant"], "baseline")
        self.assertTrue(records[0]["passed"])
        self.assertFalse(records[1]["passed"])

    def test_strata_mismatch_across_variants_is_rejected(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "passed": True, "stratum": "typical"},
            {"case_id": "c1", "variant": "A", "passed": True, "stratum": "edge"},
        ]
        records, errors = compare.load(_write_jsonl(rows))
        self.assertEqual(errors, [])
        with self.assertRaisesRegex(ValueError, "stratum differs across variants"):
            compare.summarize(records)


def _write_jsonl(rows, encoding="utf-8"):
    tmp = tempfile.NamedTemporaryFile("w", suffix=".jsonl", delete=False, encoding=encoding)
    tmp.write("\n".join(json.dumps(r) for r in rows))
    tmp.close()
    return Path(tmp.name)


def _normalized_record(case_id, variant, passed, stratum="unset", format_ok=None):
    return {
        "case_id": case_id,
        "variant": variant,
        "passed": passed,
        "trial": None,
        "stratum": stratum,
        "score": None,
        "format_ok": format_ok,
        "tokens": None,
        "latency_ms": None,
    }


def _run_main_capture(args):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = compare.main(args)
    return code, out.getvalue(), err.getvalue()


def _run_main(args):
    return _run_main_capture(args)[0]


class TestTrials(unittest.TestCase):
    def test_majority_and_tie(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "trial": 1, "passed": True},
            {"case_id": "c1", "variant": "baseline", "trial": 2, "passed": True},
            {"case_id": "c1", "variant": "baseline", "trial": 3, "passed": False},
            {"case_id": "c2", "variant": "baseline", "trial": 1, "passed": False},
            {"case_id": "c2", "variant": "baseline", "trial": 2, "passed": False},
            {"case_id": "c2", "variant": "baseline", "trial": 3, "passed": True},
            {"case_id": "c3", "variant": "baseline", "trial": 1, "passed": True},
            {"case_id": "c3", "variant": "baseline", "trial": 2, "passed": False},
        ]
        stats = compare.summarize(compare.load(_write_jsonl(rows))[0])["baseline"]
        cases = {row["case_id"]: row for row in stats["rows"]}
        self.assertEqual(stats["n"], 3)
        self.assertEqual(stats["passes"], 1)
        self.assertEqual(stats["trials"], 3)
        self.assertTrue(cases["c1"]["passed"])   # 2/3
        self.assertFalse(cases["c2"]["passed"])  # 1/3
        self.assertFalse(cases["c3"]["passed"])  # 1/2 tie fails
        self.assertEqual(len(stats["trial_rates"]), 3)
        self.assertIsNotNone(stats["trial_spread"])

    def test_mixed_trial_rows_rejected(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "passed": True},
            {"case_id": "c1", "variant": "baseline", "trial": 1, "passed": True},
        ]
        with self.assertRaises(ValueError):
            compare.summarize(compare.load(_write_jsonl(rows))[0])

    def test_duplicate_trial_rejected(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "trial": 1, "passed": True},
            {"case_id": "c1", "variant": "baseline", "trial": 1, "passed": False},
        ]
        records, errors = compare.load(_write_jsonl(rows))
        self.assertEqual(len(records), 1)
        self.assertEqual(len(errors), 1)


class TestAdjustment(unittest.TestCase):
    def test_holm_adjustment(self):
        results = [{"p": 0.01}, {"p": 0.04}, {"p": 0.03}]
        compare.adjust_pvalues(results, "holm")
        self.assertEqual([r["p_adj"] for r in results], [0.03, 0.06, 0.06])

    def test_bonferroni_and_none(self):
        results = [{"p": 0.01}, {"p": 0.04}]
        compare.adjust_pvalues(results, "bonferroni")
        self.assertEqual([r["p_adj"] for r in results], [0.02, 0.08])
        compare.adjust_pvalues(results, "none")
        self.assertEqual([r["p_adj"] for r in results], [0.01, 0.04])


class TestScoresAndFormat(unittest.TestCase):
    def test_score_and_format_aggregation(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "passed": True, "score": 0.5, "format_ok": True},
            {"case_id": "c2", "variant": "baseline", "passed": True, "score": 1.0, "format_ok": False},
        ]
        stats = compare.summarize(compare.load(_write_jsonl(rows))[0])["baseline"]
        self.assertEqual(stats["score"], 0.75)
        self.assertEqual(stats["format"], 0.5)

    def test_score_out_of_range_rejected(self):
        rows = [{"case_id": "c1", "variant": "baseline", "passed": True, "score": 1.5}]
        records, errors = compare.load(_write_jsonl(rows))
        self.assertEqual(records, [])
        self.assertEqual(len(errors), 1)

    def test_format_warning(self):
        rows = [
            {"case_id": "c1", "variant": "baseline", "passed": True, "format_ok": False},
        ]
        stats = compare.summarize(compare.load(_write_jsonl(rows))[0])
        variants, table = compare.strata_table(stats, "baseline")
        warnings = compare.build_warnings(
            stats, [], "baseline", variants, table, 50, 10, 0.05, "holm"
        )
        self.assertTrue(any("format compliance" in warning for warning in warnings))


class TestStratumDiagnostics(unittest.TestCase):
    def test_small_stratum_drop_is_flagged_not_gated(self):
        table = {
            "typical": {"baseline": (10, 8, 0.8), "A": (10, 6, 0.6)},
            "small": {"baseline": (4, 3, 0.75), "A": (4, 2, 0.5)},
        }
        warnings = compare.stratum_diagnostics(table, "baseline", ["baseline", "A"], 10)
        self.assertTrue(any("typical: dropped" in warning for warning in warnings))
        self.assertTrue(any("small stratum" in warning for warning in warnings))

    def test_strata_must_match_across_variants(self):
        rows = [
            _normalized_record("c1", "baseline", True, "typical"),
            _normalized_record("c1", "A", True, "boundary"),
        ]
        with self.assertRaisesRegex(ValueError, "stratum differs across variants"):
            compare.summarize(rows)


class TestComparisonCoverage(unittest.TestCase):
    def test_significance_is_not_reported_below_paired_case_threshold(self):
        rows = []
        for i in range(50):
            rows.append(_normalized_record(f"b{i}", "baseline", i >= 10))
            rows.append(_normalized_record(f"a{i}", "A", True))
        for i in range(10):
            rows.extend([
                _normalized_record(f"shared{i}", "baseline", False),
                _normalized_record(f"shared{i}", "A", True),
            ])
        stats = compare.summarize(rows)
        results = compare.compare(stats, "baseline", 0.05, 500, "holm")
        self.assertEqual(results[0]["pairs"], 10)
        self.assertFalse(results[0]["significant"])
        _, table = compare.strata_table(stats, "baseline")
        warnings = compare.build_warnings(
            stats, results, "baseline", ["baseline", "A"], table, 50, 10, 0.05, "holm"
        )
        self.assertTrue(any("paired n=10 < 50" in warning for warning in warnings))

    def test_format_compliance_reports_coverage(self):
        rows = [
            _normalized_record("c1", "baseline", True, format_ok=True),
            _normalized_record("c2", "baseline", True),
        ]
        stats = compare.summarize(rows)
        self.assertEqual(stats["baseline"]["format_n"], 1)
        self.assertEqual(stats["baseline"]["n"], 2)
        variants, _ = compare.strata_table(stats, "baseline")
        output = compare.render_markdown(stats, [], "baseline", 0.05, 50, 10, "holm", [])
        self.assertIn("100.0% (1/2)", output)
        warnings = compare.build_warnings(
            stats, [], "baseline", variants, {"unset": {"baseline": (2, 2, 1.0)}}, 50, 10, 0.05, "holm"
        )
        self.assertTrue(any("format coverage 1/2" in warning for warning in warnings))

    def test_json_report_exposes_format_coverage_count(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            path.write_text(
                "\n".join([
                    json.dumps({"case_id": "c1", "variant": "baseline", "passed": True, "format_ok": True}),
                    json.dumps({"case_id": "c2", "variant": "baseline", "passed": True}),
                ]),
                encoding="utf-8",
            )
            code, out, _ = _run_main_capture([str(path), "--json"])
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(payload["variants"]["baseline"]["format_n"], 1)


class TestCli(unittest.TestCase):
    def test_end_to_end_markdown(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            rows = []
            for i in range(25):
                rows.append({"case_id": f"c{i}", "variant": "baseline", "stratum": "typical", "passed": i < 17})
                rows.append({"case_id": f"c{i}", "variant": "A", "stratum": "typical", "passed": i < 22})
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            code = _run_main([str(path), "--baseline", "baseline", "--markdown"])
            self.assertEqual(code, 0)

    def test_invalid_alpha_rejected(self):
        path = _write_jsonl([{"case_id": "c1", "variant": "baseline", "passed": True}])
        self.assertEqual(_run_main([str(path), "--alpha", "0"]), 2)
        self.assertEqual(_run_main([str(path), "--alpha", "1"]), 2)
        path.unlink()

    def test_invalid_bootstrap_rejected(self):
        path = _write_jsonl([{"case_id": "c1", "variant": "baseline", "passed": True}])
        self.assertEqual(_run_main([str(path), "--bootstrap", "0"]), 2)
        path.unlink()

    def test_directory_input_is_friendly(self):
        self.assertEqual(_run_main(["."]), 2)

    def test_skip_invalid_rows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            path.write_text(
                json.dumps({"case_id": "c1", "variant": "baseline", "passed": True})
                + "\nnot json\n",
                encoding="utf-8",
            )
            self.assertEqual(_run_main([str(path)]), 2)
            code, _, err = _run_main_capture([str(path), "--skip-invalid"])
            self.assertEqual(code, 0)
            self.assertIn("skipped 1 invalid row", err)

    def test_default_min_n_is_fifty(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            rows = []
            for i in range(25):
                rows.append({"case_id": f"c{i}", "variant": "baseline", "passed": i < 17})
                rows.append({"case_id": f"c{i}", "variant": "A", "passed": i < 22})
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            _, out, _ = _run_main_capture([str(path), "--bootstrap", "100"])
            self.assertIn("n=25 < 50", out)
            _, out, _ = _run_main_capture(
                [str(path), "--bootstrap", "100", "--min-n", "20"]
            )
            self.assertNotIn("n=25 < 50", out)

    def test_json_output_includes_adjusted_p(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "r.jsonl"
            rows = []
            for i in range(25):
                rows.append({"case_id": f"c{i}", "variant": "baseline", "passed": i < 17})
                rows.append({"case_id": f"c{i}", "variant": "A", "passed": i < 22})
                rows.append({"case_id": f"c{i}", "variant": "B", "passed": i < 18})
            path.write_text("\n".join(json.dumps(r) for r in rows), encoding="utf-8")
            code, out, _ = _run_main_capture(
                [str(path), "--json", "--bootstrap", "100"]
            )
            self.assertEqual(code, 0)
            payload = json.loads(out)
            self.assertEqual(payload["adjust"], "holm")
            self.assertTrue(all("p_adj" in c for c in payload["comparisons"]))
            self.assertIn("strata", payload)
            self.assertIn("unset", payload["strata"])
            self.assertTrue(payload["warnings"])


if __name__ == "__main__":
    unittest.main()
