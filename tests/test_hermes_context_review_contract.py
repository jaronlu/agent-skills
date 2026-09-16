from __future__ import annotations

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "skills" / "hermes-context-review"


class HermesContextReviewContractTests(unittest.TestCase):
    """Guard the entry-point routes and safety contracts, not runtime Hermes behavior."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (PACKAGE / "SKILL.md").read_text(encoding="utf-8")

    def reference(self, name: str) -> str:
        return (PACKAGE / "references" / name).read_text(encoding="utf-8")

    def test_every_reference_is_directly_routed(self) -> None:
        """SKILL.md must link each reference it defers to, with no nested chain."""
        references = sorted(p.name for p in (PACKAGE / "references").glob("*.md"))
        self.assertTrue(references, "the skill must keep its references")
        for name in references:
            self.assertIn(f"references/{name}", self.skill, f"{name} is not routed from SKILL.md")
        # no nested reference chains inside the references themselves
        for p in (PACKAGE / "references").glob("*.md"):
            self.assertEqual(re.findall(r"\]\((references/[^)]+)\)", p.read_text(encoding="utf-8")), [])

    def test_entry_retains_read_only_and_evidence_boundaries(self) -> None:
        for contract in ("Read-only review", "Never expose secrets", "index is authoritative", "stop without a verdict", "runtime-session evidence"):
            self.assertIn(contract, self.skill)
        for verdict in ("VERDICT: BLOCK", "VERDICT: WARN", "VERDICT: PASS"):
            self.assertIn(verdict, self.skill)
        self.assertRegex(self.skill, r"VERDICT: WARN.*critical verification gap")

    def test_staged_review_covers_both_rename_sides(self) -> None:
        text = self.reference("review-workflow.md")
        for contract in ("git diff --cached --name-status", "HEAD:<old-path>", ":<new-path>", "no HEAD", "unmerged"):
            self.assertIn(contract, text)

    def test_memory_defaults_and_runtime_count_are_explicit(self) -> None:
        text = self.reference("memory-checks.md")
        for contract in ("missing key", "is not a configuration error", "drop empty entries", 'len("\\n§\\n".join(entries))',
                         "max(0, actual - limit)", "90%", "not a Hermes runtime limit", "not an invalid format"):
            self.assertIn(contract, text)
        self.assertNotIn("hard limit 2,200", self.reference("hermes-conventions.md"))

    def test_runtime_review_does_not_claim_disk_means_loaded(self) -> None:
        text = self.reference("runtime-checks.md")
        for contract in ("A file existing", "loaded in the current session", "user_profile_enabled", "skills.external_dirs",
                         "skills.create_dir", "mutate distribution databases", "actual prompt unverified"):
            self.assertIn(contract, text)


if __name__ == "__main__":
    unittest.main()
