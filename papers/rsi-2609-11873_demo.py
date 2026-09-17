#!/usr/bin/env python3
"""
Minimal executable demo for arXiv:2609.11873
"The Last AI Built by Humans: Toward Genuine Recursive Self-Improvement"

Two pieces, both faithful to the paper:

  Part A — Headroom-Closed Index (HCI), Eq.(2):
        H_mbh = 100 * (s_mbh - F_b0) / (100 - F_b0)
     where F_b0 = 90th-percentile score of the benchmark's *entry year*.
     H = 0  -> entry-year frontier
     H = 100 -> perfect score

  Part B — The RSI improvement loop:
        experience -> propose modification -> evaluate under acceptance rule
        -> retain accepted change -> successor inherits and loops.
     We contrast:
        L1: humans prescribe *which* intervention to try (fixed strategy).
        L2: AI diagnoses failures and *chooses* the intervention itself.
     The acceptance rule is a held-out validation set with a no-regression
     gate (regression testing), matching the paper's "protected evaluation".

Pure stdlib, deterministic seed. Run:  python3 rsi_demo.py
"""
import itertools
import random

# ============================================================
# Part A — HCI (Eq. 2)
# ============================================================
def hci(score, entry_year_frontier):
    """Normalize a raw benchmark score into Headroom-Closed Index [0,100]."""
    return 100.0 * (score - entry_year_frontier) / (100.0 - entry_year_frontier)


# ============================================================
# Part B — Toy RSI improvement loop on a synthetic concept
# ============================================================
# Hidden target over 4 interpretable integer features.
def feats(x):
    return {"odd": x % 2 == 1, "div3": x % 3 == 0,
            "div5": x % 5 == 0, "big": x > 100}

def hidden_label(x):
    f = feats(x)
    return 1 if ((f["odd"] and f["div3"]) or (f["div5"] and f["big"])) else 0

# The system's *persistent state* = a set of conjunctive rules + default pred.
# Accepted changes to this object survive into the next round (the "successor").
class Policy:
    def __init__(self):
        self.rules = []      # list of frozensets-of-feature-names -> predict 1
        self.default = 0
    def predict(self, x):
        f = feats(x)
        for r in self.rules:
            if all(f[k] for k in r):
                return 1
        return self.default
    def clone(self):
        p = Policy(); p.rules = list(self.rules); p.default = self.default
        return p

def accuracy(policy, data):
    ok = sum(policy.predict(x) == y for x, y in data)
    return ok / len(data)

def errors(policy, data):
    fn = [x for x, y in data if policy.predict(x) == 0 and y == 1]  # missed positives
    fp = [x for x, y in data if policy.predict(x) == 1 and y == 0]  # false alarms
    return fn, fp

# --- Candidate proposal (the "improver") ----------------------
def mine_positive_rule(examples, max_size=3):
    """From mislabeled-positive examples, propose a conjunctive feature rule
    that covers them. Purely from *experience* (training set), not validation."""
    if not examples:
        return None
    fnames = list(feats(examples[0]).keys())
    best, best_cov = None, 0
    for size in (2, 3):
        for combo in itertools.combinations(fnames, size):
            cov = sum(1 for x in examples if all(feats(x)[k] for k in combo))
            if cov > best_cov:
                best, best_cov = frozenset(combo), cov
    return best if best_cov > 0 else None

def propose_L1(policy, train):
    """L1: a FIXED human-prescribed intervention -> always mine a positive rule
    from false negatives. (Humans decide *what* and *how*; AI only executes.)"""
    fn, _ = errors(policy, train)
    rule = mine_positive_rule(fn)
    return ("add-positive-rule", rule) if rule else ("no-op", None)

def propose_L2(policy, train):
    """L2: AI DIAGNOSES failures and picks the intervention strategy.
    If false negatives dominate -> add a positive rule.
    If false positives dominate -> flip default toward negative (prune bias)."""
    fn, fp = errors(policy, train)
    if len(fn) >= len(fp) and fn:
        return ("add-positive-rule", mine_positive_rule(fn))
    elif fp:
        return ("flip-default-to-negative", None)
    return ("no-op", None)

def apply_candidate(policy, kind, payload):
    cand = policy.clone()
    if kind == "add-positive-rule" and payload is not None and payload not in cand.rules:
        cand.rules.append(payload)
    elif kind == "flip-default-to-negative":
        cand.default = 0
    return cand

# --- Improvement loop with protected acceptance rule ----------
def improvement_loop(policy, train, val, rounds, proposer, label):
    print(f"\n=== {label} ===")
    print(f"{'r':>2} {'strategy':<26} {'val_before':>10} {'val_after':>9} {'verdict':<9} {'rules':>5}")
    for r in range(1, rounds + 1):
        before = accuracy(policy, val)
        kind, payload = proposer(policy, train)          # propose from experience
        candidate = apply_candidate(policy, kind, payload)
        after = accuracy(candidate, val)
        # Acceptance rule: held-out validation with a no-regression gate.
        accepted = kind != "no-op" and after >= before
        if accepted:
            policy = candidate                          # successor inherits the change
        print(f"{r:>2} {kind:<26} {before:>10.3f} {after:>9.3f} "
              f"{'ACCEPT' if accepted else 'reject':<9} {len(policy.rules):>5}")
    return policy

# ============================================================
# Run
# ============================================================
def main():
    # ---- Part A: HCI illustration ----
    print("Part A: HCI normalization (paper Eq. 2)")
    # Paper's illustrative 2026 domain values; F0 = synthetic entry-year frontier.
    demo = [("Tool agents (raw acc)", 39.9, 10.0),
            ("Software engineering", 52.6, 15.0),
            ("Graduate science",     85.8, 20.0)]
    print(f"{'domain':<24}{'raw':>8}{'F0':>7}{'HCI':>9}")
    for name, raw, f0 in demo:
        print(f"{name:<24}{raw:>8.1f}{f0:>7.1f}{hci(raw, f0):>9.1f}")

    # ---- Part B: improvement loop ----
    random.seed(7)
    data = [(x, hidden_label(x)) for x in range(0, 300)]
    random.shuffle(data)
    train = data[:200]
    val   = data[200:]

    p1 = Policy()
    p1 = improvement_loop(p1, train, val, 12, propose_L1,
                     "L1 — fixed human-prescribed intervention")

    p2 = Policy()
    p2 = improvement_loop(p2, train, val, 12, propose_L2,
                     "L2 — AI diagnoses & chooses the intervention")

    # ---- Map final skill onto HCI ----
    f0 = accuracy(Policy(), val) * 100          # entry-year = initial (untuned) policy
    final1, final2 = accuracy(p1, val) * 100, accuracy(p2, val) * 100
    print("\nPart B result (validation accuracy -> HCI, entry-year = initial policy):")
    print(f"  initial HCI = 0.0  (by construction)")
    print(f"  L1 final: val_acc={accuracy(p1,val):.3f}  HCI={hci(final1, f0):.1f}")
    print(f"  L2 final: val_acc={accuracy(p2,val):.3f}  HCI={hci(final2, f0):.1f}")
    print("Note: candidates are chosen from *training* experience; the held-out")
    print("validation set is the protected acceptance rule (no-regression gate).")

if __name__ == "__main__":
    main()
