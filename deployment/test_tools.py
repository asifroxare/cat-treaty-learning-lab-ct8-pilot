"""Dependency-free tests for deployment evidence integrity."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import probe
import prepare_pages
import verify_goldens
import measure_local
import isolated_execution
import staging_acceptance


class DeploymentEvidenceTests(unittest.TestCase):
    def test_request_id_is_only_allowed_normalization(self):
        original = {"api": {"request_id": "a", "completion_status": "complete"},
                    "post_capacity": {"gross_contractual_recovery": 10,
                                      "reinstatement_premium_payable": 3,
                                      "net_cash_settlement": 7},
                    "exclusion_reasons": ["outside_window"]}
        variant = json.loads(json.dumps(original))
        variant["api"]["request_id"] = "b"
        digest = lambda obj: probe.fixture_digest(obj, [("api", "request_id")])
        self.assertEqual(digest(original), digest(variant))
        for path, value in (("gross_contractual_recovery", 11),
                            ("reinstatement_premium_payable", 4),
                            ("net_cash_settlement", 6)):
            changed = json.loads(json.dumps(variant))
            changed["post_capacity"][path] = value
            self.assertNotEqual(digest(original), digest(changed))
        variant["exclusion_reasons"][0] = "other"
        self.assertNotEqual(digest(original), digest(variant))

    def test_staging_rejects_unreviewed_origin_before_network(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "manifest.json"
            path.write_text(json.dumps({"api_origin": "https://wrong.example",
                                        "frontend_origin": "https://front.example", "fixtures": []}))
            with patch("sys.argv", ["staging_acceptance", "--frontend", "https://front.example",
                                    "--api", "https://api.example", "--manifest", str(path)]):
                with self.assertRaisesRegex(RuntimeError, "manifest origins"):
                    staging_acceptance.main()

    def test_pages_policy_is_exact_and_keeps_missing_assets_out_of_spa(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "index.html").write_text("<html></html>")
            (root / "assets").mkdir()
            (root / "assets" / "app.js").write_text("const api='https://api.example';")
            prepare_pages.prepare(root, "https://api.example")
            headers = (root / "_headers").read_text()
            redirects = (root / "_redirects").read_text()
            self.assertIn("connect-src 'self' https://api.example", headers)
            self.assertIn("script-src 'self'", headers)
            self.assertIn("/hours-clause /index.html 200", redirects)
            self.assertNotIn("/assets/", redirects)
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                prepare_pages.prepare(root, "http://localhost:8000")

    def test_manifest_rejects_tampered_request(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            (root / "approved-catalogue.json").write_bytes(b'{}')
            (root / "approved-hours-clause.json").write_bytes(b'{}')
            entries = [{"route": route, "request_file": f"approved-{route}.json",
                        "request_sha256": "0" * 64, "response_sha256": "1" * 64}
                       for route in ("catalogue", "hours-clause")]
            (root / "baseline-candidates.json").write_text(json.dumps({
                "source_commit": verify_goldens.BASELINE,
                "normalization": ["api.request_id"], "fixtures": entries}))
            with self.assertRaisesRegex(ValueError, "bytes do not match"):
                verify_goldens.verify_manifest(root)

    def test_synthetic_trials_preserve_ct6_global_event_id_contract(self):
        for count in (1, 10, 100):
            request = json.loads(measure_local.payload(count))
            self.assertEqual(request["input"]["simulation"]["trial_count"], count)
            ids = [event["event_id"] for trial in request["input"]["trials"]
                   for event in trial["occurrences"]]
            self.assertEqual(len(ids), len(set(ids)))
            self.assertTrue(all(event["event_id"] == event["loss_basis"]["occurrence_id"]
                for trial in request["input"]["trials"] for event in trial["occurrences"]))

    def test_disposable_process_returns_complete_value_or_ends_on_deadline(self):
        answer = isolated_execution.execute("isolation_fixtures", "square", 7, timeout_seconds=10)
        self.assertEqual(answer.value, 49)
        with self.assertRaises(isolated_execution.ExecutionExpired):
            isolated_execution.execute("isolation_fixtures", "wait_forever", None, timeout_seconds=0.1)
        with self.assertRaises(isolated_execution.ExecutionFailed):
            isolated_execution.execute("isolation_fixtures", "crash", None, timeout_seconds=10)

    def test_request_digest_changes_on_input_mutation(self):
        raw = b'{"trial_count":1}\n'
        changed = b'{"trial_count":2}\n'
        self.assertNotEqual(hashlib.sha256(raw).hexdigest(), hashlib.sha256(changed).hexdigest())


if __name__ == "__main__":
    unittest.main()
