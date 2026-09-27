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
import measure_pickle_gate
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

    def test_isolated_measurement_remains_bounded_and_preserves_trial_identity(self):
        for count, detail in ((500, "summary"), (1000, "full")):
            request = json.loads(measure_local.payload(count, sample_cap=1000, detail=detail))
            self.assertEqual(request["response_detail"], detail)
            self.assertEqual(request["input"]["simulation"]["trial_count"], count)
            ids = [event["event_id"] for trial in request["input"]["trials"]
                   for event in trial["occurrences"]]
            self.assertEqual(len(set(ids)), count)
        with self.assertRaises(ValueError):
            measure_local.payload(1001, sample_cap=1000)
        with self.assertRaises(ValueError):
            measure_local.payload(101)

    def test_pickle_probe_rejects_unreviewed_sample_before_starting_child(self):
        with self.assertRaisesRegex(ValueError, "fixed reviewed samples"):
            measure_pickle_gate.sample(Path("unused-python"), 10001)
        self.assertEqual(measure_pickle_gate.MAX_SECONDS, 30)
        self.assertEqual(measure_pickle_gate.MAX_PEAK_BYTES, 800 * 1024 * 1024)

    def test_trial_limit_generator_remains_inside_input_byte_guard(self):
        request = json.loads(measure_local.payload(10000, sample_cap=10000, detail="full"))
        self.assertEqual(request["input"]["simulation"]["trial_count"], 10000)
        self.assertEqual(len(request["input"]["trials"]), 10000)
        self.assertEqual(request["input"]["trials"][-1]["occurrences"][0]["event_id"], "T10000-E1")
        self.assertLess(len(measure_local.payload(10000, sample_cap=10000, detail="full")), 12 * 1024 * 1024)

    def test_row_limit_fixture_has_25000_unique_events_below_25_mib(self):
        raw = measure_local.payload(10000, sample_cap=10000, detail="full", total_occurrences=25000)
        self.assertLess(len(raw), 25 * 1024 * 1024)
        request = json.loads(raw)
        trials = request["input"]["trials"]
        self.assertEqual(sum(len(trial["occurrences"]) for trial in trials), 25000)
        ids = [event["event_id"] for trial in trials for event in trial["occurrences"]]
        self.assertEqual(len(set(ids)), len(ids))
        for trial in (trials[0], trials[4999], trials[5000], trials[-1]):
            self.assertEqual([e["event_sequence"] for e in trial["occurrences"]],
                             list(range(1, len(trial["occurrences"]) + 1)))
            self.assertTrue(all(e["event_id"] == e["loss_basis"]["occurrence_id"]
                                for e in trial["occurrences"]))

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
