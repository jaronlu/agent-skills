#!/usr/bin/env python3
"""Compare prompt variants from a JSONL evaluation run.

Input: one JSON object per line, one line per case per variant. If a case has
several trials, add a `trial` field; the script aggregates them to one
case-level outcome by majority (ties fail).

Required keys: case_id, variant, passed (bool, 0/1, true/false, pass/fail, yes/no).
Optional keys: trial, stratum (missing/null -> "unset"), score (0..1),
format_ok (bool), tokens, latency_ms, failure_class.

Usage:
    python3 scripts/compare.py results.jsonl --baseline baseline
    python3 scripts/compare.py results.jsonl --baseline baseline --markdown

Exit codes: 0 success, 2 invalid input.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path
from typing import cast

TRUE_VALUES = {"true", "1", "pass", "passed", "yes", "correct"}
FALSE_VALUES = {"false", "0", "fail", "failed", "no", "incorrect"}
ADJUST_METHODS = ("holm", "bonferroni", "none")


def parse_passed(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and value in (0, 1):
        return bool(value)
    if isinstance(value, str):
        token = value.strip().lower()
        if token in TRUE_VALUES:
            return True
        if token in FALSE_VALUES:
            return False
    raise ValueError(
        f"passed must be bool/0/1/true/false/pass/fail, got {value!r}"
    )


def parse_optional_flag(value):
    if value is None:
        return None
    return parse_passed(value)


def normalize_stratum(value):
    """Coerce missing, null, numeric, or blank strata to a printable label."""
    if value is None:
        return "unset"
    text = " ".join(str(value).split())
    return text or "unset"


def parse_number(value):
    """Accept numbers or numeric strings; ignore booleans and non-finite values."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        try:
            number = float(value)
        except OverflowError:
            return None
    elif isinstance(value, str):
        try:
            number = float(value.strip())
        except (ValueError, OverflowError):
            return None
    else:
        return None
    return number if math.isfinite(number) else None


def parse_score(value):
    number = parse_number(value)
    if number is None:
        return None
    if not 0 <= number <= 1:
        raise ValueError(f"score must be between 0 and 1, got {value!r}")
    return number


def trial_sort_key(value: str):
    try:
        return (0, float(value))
    except (TypeError, ValueError):
        return (1, value)


def wilson(passes: int, n: int, z: float):
    if n == 0:
        return (0.0, 0.0)
    p = passes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return (max(0.0, center - half), min(1.0, center + half))


def mcnemar_exact(b: int, c: int) -> float:
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(math.comb(n, k) for k in range(0, min(b, c) + 1)) / (2 ** n)
    return min(1.0, 2 * tail)


def bootstrap_delta(pairs, iterations: int, alpha: float = 0.05):
    if not pairs:
        return (0.0, 0.0)
    if iterations < 100:
        raise ValueError("bootstrap iterations must be at least 100")
    if not 0 < alpha < 1:
        raise ValueError("alpha must be between 0 and 1")
    rng = random.Random(42)
    n = len(pairs)
    deltas = []
    for _ in range(iterations):
        idx = [rng.randrange(n) for _ in range(n)]
        delta = sum(pairs[i][1] - pairs[i][0] for i in idx) / n
        deltas.append(delta)
    deltas.sort()
    lo = deltas[int((alpha / 2) * (iterations - 1))]
    hi = deltas[int((1 - alpha / 2) * (iterations - 1))]
    return (lo, hi)


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def pp(x: float) -> str:
    return f"{x * 100:+.1f} pp"


def fmt_ci(lo: float, hi: float) -> str:
    return f"{pct(lo)}–{pct(hi)}"


def stratum_cell(n: int, passes: int) -> str:
    return "- (0)" if n == 0 else f"{pct(passes / n)} ({n})"


def md_escape(value) -> str:
    return str(value).replace("|", "\\|").replace("\n", " ")


def load(path: Path):
    records = []
    errors = []
    seen = set()
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeDecodeError) as exc:
        return [], [f"cannot read {path}: {exc}"]
    for lineno, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"line {lineno}: invalid JSON ({exc})")
            continue
        if not isinstance(row, dict):
            errors.append(f"line {lineno}: expected an object")
            continue
        missing = [k for k in ("case_id", "variant", "passed") if k not in row]
        if missing:
            errors.append(f"line {lineno}: missing {', '.join(missing)}")
            continue
        try:
            row["passed"] = parse_passed(row["passed"])
            row["score"] = parse_score(row.get("score"))
            row["format_ok"] = parse_optional_flag(row.get("format_ok"))
        except ValueError as exc:
            errors.append(f"line {lineno}: {exc}")
            continue
        case_id = str(row["case_id"]).strip()
        variant = str(row["variant"]).strip()
        if not case_id:
            errors.append(f"line {lineno}: case_id must not be empty")
            continue
        if not variant:
            errors.append(f"line {lineno}: variant must not be empty")
            continue
        raw_trial = row.get("trial")
        trial = None if raw_trial is None else str(raw_trial).strip() or None
        key = (case_id, variant, trial)
        if key in seen:
            errors.append(
                f"line {lineno}: duplicate case/variant/trial {key} "
                "(trials must have distinct `trial` values)"
            )
            continue
        seen.add(key)
        row["case_id"] = case_id
        row["variant"] = variant
        row["trial"] = trial
        row["stratum"] = normalize_stratum(row.get("stratum"))
        row["tokens"] = parse_number(row.get("tokens"))
        row["latency_ms"] = parse_number(row.get("latency_ms"))
        records.append(row)
    return records, errors


def _aggregate_case(group):
    trials = [row["trial"] for row in group]
    if len(group) > 1 and any(trial is None for trial in trials):
        raise ValueError(
            f"{group[0]['case_id']}/{group[0]['variant']}: "
            "mixed trial and non-trial rows"
        )
    strata = {row["stratum"] for row in group}
    if len(strata) > 1:
        raise ValueError(
            f"{group[0]['case_id']}/{group[0]['variant']}: "
            f"stratum differs across trials ({sorted(strata)})"
        )

    pass_rate = sum(1 for row in group if row["passed"]) / len(group)
    scores = [row["score"] for row in group if row["score"] is not None]
    formats = [row["format_ok"] for row in group if row["format_ok"] is not None]
    tokens = [row["tokens"] for row in group if row["tokens"] is not None]
    latency = [row["latency_ms"] for row in group if row["latency_ms"] is not None]

    return {
        "case_id": group[0]["case_id"],
        "variant": group[0]["variant"],
        "stratum": group[0]["stratum"],
        "passed": pass_rate > 0.5,  # majority; ties fail
        "trial_pass_rate": pass_rate,
        "trials": len(group),
        "score": statistics.mean(scores) if scores else None,
        "format_rate": statistics.mean(formats) if formats else None,
        "format_ok": all(formats) if formats else None,
        "tokens": statistics.mean(tokens) if tokens else None,
        "latency": statistics.mean(latency) if latency else None,
        "failure_class": next(
            (row.get("failure_class") for row in group if row.get("failure_class")),
            None,
        ),
    }


def summarize(records):
    case_strata = {}
    for row in records:
        case_id = row["case_id"]
        stratum = row["stratum"]
        if case_id in case_strata and case_strata[case_id] != stratum:
            raise ValueError(
                f"{case_id}: stratum differs across variants "
                f"({case_strata[case_id]!r} vs {stratum!r})"
            )
        case_strata[case_id] = stratum

    by_variant = defaultdict(list)
    for row in records:
        by_variant[row["variant"]].append(row)

    stats = {}
    for variant, rows in by_variant.items():
        groups = defaultdict(list)
        for row in rows:
            groups[row["case_id"]].append(row)
        cases = [_aggregate_case(group) for group in groups.values()]

        n = len(cases)
        passes = sum(1 for case in cases if case["passed"])
        scores = [case["score"] for case in cases if case["score"] is not None]
        formats = [case["format_rate"] for case in cases if case["format_rate"] is not None]
        tokens = [case["tokens"] for case in cases if case["tokens"] is not None]
        latency = [case["latency"] for case in cases if case["latency"] is not None]

        trial_values = sorted(
            {row["trial"] for row in rows if row["trial"] is not None},
            key=trial_sort_key,
        )
        trial_rates = []
        for trial in trial_values:
            subset = [row for row in rows if row["trial"] == trial]
            if subset:
                trial_rates.append(
                    sum(1 for row in subset if row["passed"]) / len(subset)
                )

        stats[variant] = {
            "n": n,
            "cases": n,
            "passes": passes,
            "rate": passes / n if n else 0.0,
            "tokens": statistics.mean(tokens) if tokens else None,
            "latency": statistics.mean(latency) if latency else None,
            "score": statistics.mean(scores) if scores else None,
            "format": statistics.mean(formats) if formats else None,
            "format_n": len(formats),
            "trials": max((cast(int, case["trials"]) for case in cases), default=1),
            "trial_rates": trial_rates,
            "trial_spread": (
                (min(trial_rates), max(trial_rates))
                if len(trial_rates) > 1
                else None
            ),
            "rows": cases,
        }
    return stats


def adjust_pvalues(results, method: str):
    if not results:
        return
    m = len(results)
    if method == "none":
        for result in results:
            result["p_adj"] = result["p"]
        return
    if method == "bonferroni":
        for result in results:
            result["p_adj"] = min(1.0, result["p"] * m)
        return

    order = sorted(range(m), key=lambda i: results[i]["p"])
    running = 0.0
    for rank, index in enumerate(order):
        adjusted = min(1.0, (m - rank) * results[index]["p"])
        running = max(running, adjusted)
        results[index]["p_adj"] = running


def compare(
    stats, baseline: str, alpha: float, iterations: int, adjust: str, min_n: int = 50
):
    if baseline not in stats:
        return []
    base = {row["case_id"]: row["passed"] for row in stats[baseline]["rows"]}
    results = []
    for variant, data in stats.items():
        if variant == baseline:
            continue
        cand = {row["case_id"]: row["passed"] for row in data["rows"]}
        shared = sorted(set(base) & set(cand))
        pairs = [(int(base[cid]), int(cand[cid])) for cid in shared]
        b = sum(1 for base_p, cand_p in pairs if base_p == 1 and cand_p == 0)
        c = sum(1 for base_p, cand_p in pairs if base_p == 0 and cand_p == 1)
        delta = (
            sum(cand_p - base_p for base_p, cand_p in pairs) / len(pairs)
            if pairs
            else 0.0
        )
        lo, hi = bootstrap_delta(pairs, iterations, alpha)
        results.append(
            {
                "variant": variant,
                "pairs": len(pairs),
                "b": b,
                "c": c,
                "delta": delta,
                "delta_ci": (lo, hi),
                "p": mcnemar_exact(b, c),
                "missing_in_candidate": len(set(base) - set(cand)),
                "missing_in_baseline": len(set(cand) - set(base)),
                "insufficient_pairs": len(pairs) < min_n,
            }
        )
    adjust_pvalues(results, adjust)
    for result in results:
        result["significant"] = (
            not result["insufficient_pairs"]
            and result["p_adj"] < alpha
            and result["delta"] > 0
            and result["delta_ci"][0] > 0
        )
    return results


def strata_table(stats, baseline: str):
    variants = [baseline] + sorted(v for v in stats if v != baseline)
    strata = sorted({row["stratum"] for data in stats.values() for row in data["rows"]})
    table: dict[str, dict[str, tuple[int, int, float]]] = {}
    for stratum in strata:
        table[stratum] = {}
        for variant in variants:
            rows = [row for row in stats[variant]["rows"] if row["stratum"] == stratum]
            passes = sum(1 for row in rows if row["passed"])
            table[stratum][variant] = (
                len(rows),
                passes,
                passes / len(rows) if rows else 0.0,
            )
    return variants, table


def stratum_diagnostics(table, baseline, variants, min_stratum_n):
    warnings = []
    for stratum, row in table.items():
        base_n = row[baseline][0]
        base_rate = row[baseline][2]
        for variant in variants:
            if variant == baseline:
                continue
            cand_n = row[variant][0]
            cand_rate = row[variant][2]
            if base_n == 0 or cand_n == 0:
                continue
            drop = cand_rate - base_rate
            if min(base_n, cand_n) < min_stratum_n:
                if drop < -0.05:
                    warnings.append(
                        f"{variant}/{stratum}: small stratum "
                        f"(n={base_n}/{cand_n}) dropped {pp(drop)}; not gated"
                    )
            elif drop < -0.05:
                warnings.append(
                    f"{variant}/{stratum}: dropped {pp(drop)} "
                    f"({pct(base_rate)} -> {pct(cand_rate)})"
                )
    return warnings


def build_warnings(
    stats,
    comparisons,
    baseline,
    variants,
    table,
    min_n,
    min_stratum_n,
    alpha,
    adjust,
):
    warnings = []
    for variant, data in stats.items():
        if data["n"] < min_n:
            warnings.append(
                f"{variant}: n={data['n']} < {min_n}; treat as directional"
            )
        if data["trials"] > 1:
            warnings.append(
                f"{variant}: {data['trials']} trials aggregated by majority "
                "(ties fail); n counts cases"
            )
        if data["format_n"] < data["n"]:
            warnings.append(
                f"{variant}: format coverage {data['format_n']}/{data['n']}; "
                "compliance is incomplete"
            )
        if data["format"] is not None and data["format"] < 1:
            warnings.append(
                f"{variant}: format compliance {pct(data['format'])} < 100%"
            )
    for comparison in comparisons:
        if comparison["insufficient_pairs"]:
            warnings.append(
                f"{comparison['variant']}: paired n={comparison['pairs']} < "
                f"{min_n}; significance is not assessed"
            )
        if comparison["p_adj"] >= alpha:
            warnings.append(
                f"{comparison['variant']}: not significant after {adjust} "
                f"adjustment (p_adj={comparison['p_adj']:.3f}); "
                "directional or canary only"
            )
        if comparison["delta_ci"][0] <= 0:
            warnings.append(
                f"{comparison['variant']}: delta CI includes zero "
                f"({pp(comparison['delta_ci'][0])}–{pp(comparison['delta_ci'][1])})"
            )
        if comparison["delta"] < 0:
            warnings.append(
                f"{comparison['variant']}: candidate is worse "
                f"({pp(comparison['delta'])})"
            )
        if comparison["missing_in_candidate"] or comparison["missing_in_baseline"]:
            warnings.append(
                f"{comparison['variant']}: unpaired cases "
                f"(missing in candidate {comparison['missing_in_candidate']}, "
                f"in baseline {comparison['missing_in_baseline']})"
            )
    warnings += stratum_diagnostics(table, baseline, variants, min_stratum_n)
    return warnings


def _quality_rows(stats, baseline):
    variants = [baseline] + sorted(v for v in stats if v != baseline)
    for variant in variants:
        data = stats[variant]
        score = f"{data['score']:.2f}" if data["score"] is not None else "-"
        fmt = (
            f"{pct(data['format'])} ({data['format_n']}/{data['n']})"
            if data["format"] is not None
            else f"- (0/{data['n']})"
        )
        spread = (
            f"{pct(data['trial_spread'][0])}–{pct(data['trial_spread'][1])}"
            if data["trial_spread"]
            else "-"
        )
        yield variant, score, fmt, str(data["trials"]), spread


def render_text(
    stats,
    comparisons,
    baseline,
    alpha,
    min_n,
    min_stratum_n,
    adjust,
    warnings,
):
    z = statistics.NormalDist().inv_cdf(1 - alpha / 2)
    confidence = int((1 - alpha) * 100)
    lines = [f"Prompt evaluation — baseline: {baseline}", ""]
    lines.append(
        f"{'variant':<14}{'n':>4}{'pass':>6}{'rate':>8}   {confidence}% CI"
        f"{'':<14}{'tokens':>8}{'latency':>10}"
    )
    for variant in [baseline] + sorted(v for v in stats if v != baseline):
        data = stats[variant]
        lo, hi = wilson(data["passes"], data["n"], z)
        tokens = f"{data['tokens']:.0f}" if data["tokens"] is not None else "-"
        latency = f"{data['latency']:.0f}ms" if data["latency"] is not None else "-"
        lines.append(
            f"{variant:<14}{data['n']:>4}{data['passes']:>6}"
            f"{data['rate'] * 100:>7.1f}%   {fmt_ci(lo, hi):<20}"
            f"{tokens:>8}{latency:>10}"
        )

    lines += ["", "Quality and trials", ""]
    lines.append(f"{'variant':<14}{'score':>7}{'format':>8}{'trials':>7}   spread")
    for variant, score, fmt, trials, spread in _quality_rows(stats, baseline):
        lines.append(f"{variant:<14}{score:>7}{fmt:>8}{trials:>7}   {spread}")

    if comparisons:
        lines += [
            "",
            f"Paired comparisons vs {baseline} "
            f"(McNemar exact, {confidence}% bootstrap delta CI, {adjust})",
            "",
        ]
        lines.append(
            f"{'variant':<14}{'pairs':>6}{'b':>4}{'c':>4}{'delta':>10}"
            f"   {'delta CI':<18}{'p':>7}{'p_adj':>8}{'sig':>4}"
        )
        for comparison in comparisons:
            lines.append(
                f"{comparison['variant']:<14}{comparison['pairs']:>6}"
                f"{comparison['b']:>4}{comparison['c']:>4}"
                f"{pp(comparison['delta']):>10}   "
                f"{pp(comparison['delta_ci'][0])}–{pp(comparison['delta_ci'][1]):<10}"
                f"{comparison['p']:>7.3f}{comparison['p_adj']:>8.3f}"
                f"{'*' if comparison['significant'] else '':>4}"
            )

    variants, table = strata_table(stats, baseline)
    lines += ["", "Per stratum", ""]
    lines.append(f"{'stratum':<14}" + "".join(f"{v:>14}" for v in variants))
    for stratum, row in table.items():
        lines.append(
            f"{stratum:<14}"
            + "".join(
                f"{stratum_cell(row[v][0], row[v][1]):>14}" for v in variants
            )
        )

    if warnings:
        lines += ["", "Warnings"]
        lines += [f"- {warning}" for warning in warnings]
    return "\n".join(lines)


def render_markdown(
    stats,
    comparisons,
    baseline,
    alpha,
    min_n,
    min_stratum_n,
    adjust,
    warnings,
):
    z = statistics.NormalDist().inv_cdf(1 - alpha / 2)
    confidence = int((1 - alpha) * 100)
    lines = [
        f"| Variant | n | Pass | Rate | {confidence}% CI | Tokens | Latency |",
        "|---|---|---|---|---|---|---|",
    ]
    for variant in [baseline] + sorted(v for v in stats if v != baseline):
        data = stats[variant]
        lo, hi = wilson(data["passes"], data["n"], z)
        tokens = f"{data['tokens']:.0f}" if data["tokens"] is not None else "-"
        latency = f"{data['latency']:.0f}ms" if data["latency"] is not None else "-"
        lines.append(
            f"| {md_escape(variant)} | {data['n']} | {data['passes']} | "
            f"{pct(data['rate'])} | {fmt_ci(lo, hi)} | {tokens} | {latency} |"
        )

    lines += [
        "",
        "| Variant | Score | Format | Trials | Trial spread |",
        "|---|---|---|---|---|",
    ]
    for variant, score, fmt, trials, spread in _quality_rows(stats, baseline):
        lines.append(
            f"| {md_escape(variant)} | {score} | {fmt} | {trials} | {spread} |"
        )

    if comparisons:
        lines += [
            "",
            "| Candidate | Pairs | b | c | Δ | Δ CI | p | p_adj | Sig |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
        for comparison in comparisons:
            lines.append(
                f"| {md_escape(comparison['variant'])} | {comparison['pairs']} | "
                f"{comparison['b']} | {comparison['c']} | "
                f"{pp(comparison['delta'])} | "
                f"{pp(comparison['delta_ci'][0])}–{pp(comparison['delta_ci'][1])} | "
                f"{comparison['p']:.3f} | {comparison['p_adj']:.3f} | "
                f"{'yes' if comparison['significant'] else 'no'} |"
            )

    variants, table = strata_table(stats, baseline)
    lines += [
        "",
        "| Stratum | " + " | ".join(md_escape(v) for v in variants) + " |",
        "|---|" + "---|" * len(variants),
    ]
    for stratum, row in table.items():
        lines.append(
            f"| {md_escape(stratum)} | "
            + " | ".join(
                stratum_cell(row[v][0], row[v][1]) for v in variants
            )
            + " |"
        )

    if warnings:
        lines += ["", "Warnings: " + "; ".join(warnings)]
    return "\n".join(lines)


def build_parser():
    parser = argparse.ArgumentParser(
        description="Compare prompt variants from a JSONL evaluation run."
    )
    parser.add_argument("results", type=Path)
    parser.add_argument("--baseline", default="baseline")
    parser.add_argument("--alpha", type=float, default=0.05)
    parser.add_argument("--bootstrap", type=int, default=5000)
    parser.add_argument("--min-n", type=int, default=50)
    parser.add_argument("--min-stratum-n", type=int, default=10)
    parser.add_argument("--adjust", choices=ADJUST_METHODS, default="holm")
    parser.add_argument("--skip-invalid", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--json", action="store_true")
    return parser


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)

    if not 0 < args.alpha < 1:
        print("error: --alpha must be between 0 and 1 (exclusive)", file=sys.stderr)
        return 2
    if args.bootstrap < 100:
        print("error: --bootstrap must be at least 100", file=sys.stderr)
        return 2
    if args.min_n < 1:
        print("error: --min-n must be at least 1", file=sys.stderr)
        return 2
    if args.min_stratum_n < 1:
        print("error: --min-stratum-n must be at least 1", file=sys.stderr)
        return 2

    if not args.results.exists():
        print(f"error: {args.results} not found", file=sys.stderr)
        return 2

    records, errors = load(args.results)
    if errors and not args.skip_invalid:
        for error in errors:
            print(f"error: {error}", file=sys.stderr)
        return 2
    if errors:
        print(f"warning: skipped {len(errors)} invalid row(s)", file=sys.stderr)
        for error in errors[:5]:
            print(f"  {error}", file=sys.stderr)
    if not records:
        print("error: no valid records", file=sys.stderr)
        return 2

    try:
        stats = summarize(records)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    if args.baseline not in stats:
        print(f"error: baseline variant {args.baseline!r} not found", file=sys.stderr)
        return 2

    comparisons = compare(
        stats, args.baseline, args.alpha, args.bootstrap, args.adjust, args.min_n
    )
    variants, table = strata_table(stats, args.baseline)
    warnings = build_warnings(
        stats,
        comparisons,
        args.baseline,
        variants,
        table,
        args.min_n,
        args.min_stratum_n,
        args.alpha,
        args.adjust,
    )

    if args.json:
        payload = {
            "baseline": args.baseline,
            "alpha": args.alpha,
            "adjust": args.adjust,
            "variants": {
                variant: {
                    key: data[key]
                    for key in (
                        "n",
                        "passes",
                        "rate",
                        "tokens",
                        "latency",
                        "score",
                        "format",
                        "format_n",
                        "trials",
                        "trial_spread",
                    )
                }
                for variant, data in stats.items()
            },
            "comparisons": comparisons,
            "strata": {
                stratum: {
                    variant: {
                        "n": cells[variant][0],
                        "passes": cells[variant][1],
                        "rate": cells[variant][2],
                    }
                    for variant in cells
                }
                for stratum, cells in table.items()
            },
            "warnings": warnings,
        }
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    elif args.markdown:
        print(
            render_markdown(
                stats,
                comparisons,
                args.baseline,
                args.alpha,
                args.min_n,
                args.min_stratum_n,
                args.adjust,
                warnings,
            )
        )
    else:
        print(
            render_text(
                stats,
                comparisons,
                args.baseline,
                args.alpha,
                args.min_n,
                args.min_stratum_n,
                args.adjust,
                warnings,
            )
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
