import importlib.util
import hashlib
import io
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "publish_snapshot.py"
SPEC = importlib.util.spec_from_file_location("publish_snapshot", MODULE_PATH)
publish_snapshot = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(publish_snapshot)


class _Response:
    def __init__(self, payload):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def read(self):
        return json.dumps(self.payload).encode()


def valid_snapshot(company="Structural Fab"):
    snapshot = {"company": company, "as_of": "2026-09-14", "refreshed_at": "now"}
    canonical = json.dumps({"company": company, "as_of": "2026-09-14"}, sort_keys=True, separators=(",", ":")).encode()
    snapshot["sha256"] = hashlib.sha256(canonical).hexdigest()
    return snapshot


class PublishSnapshotTests(unittest.TestCase):
    @mock.patch.object(publish_snapshot.time, "sleep")
    @mock.patch.object(publish_snapshot.urllib.request, "urlopen")
    def test_rpc_retries_transient_http_522(self, urlopen, sleep):
        urlopen.side_effect = [
            urllib.error.HTTPError("https://example.test", 522, "timeout", {}, io.BytesIO(b"")),
            _Response(43),
        ]

        result = publish_snapshot.rpc("https://example.test", "key", "token", "stage", {"x": 1})

        self.assertEqual(result, 43)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2)

    @mock.patch.object(publish_snapshot.time, "sleep")
    @mock.patch.object(publish_snapshot.urllib.request, "urlopen")
    def test_rpc_retries_transient_http_520(self, urlopen, sleep):
        urlopen.side_effect = [
            urllib.error.HTTPError("https://example.test", 520, "origin error", {}, io.BytesIO(b"error code: 520")),
            _Response(44),
        ]

        result = publish_snapshot.rpc("https://example.test", "key", "token", "metadata", {})

        self.assertEqual(result, 44)
        self.assertEqual(urlopen.call_count, 2)
        sleep.assert_called_once_with(2)

    @mock.patch.object(publish_snapshot, "load_credentials")
    @mock.patch.object(publish_snapshot, "rpc")
    def test_publish_skips_large_upload_when_source_is_unchanged(self, rpc, load_credentials):
        load_credentials.return_value = {
            "supabase_url": "https://example.test",
            "publishable_key": "key",
            "current_ar_ingestion_key": "ingest",
            "current_ar_promotion_key": "promote",
            "operator_verification_key": "verify",
        }
        snapshot = valid_snapshot()
        current = {"snapshot_id": 42, "source_sha256": snapshot["sha256"], "as_of": "2026-09-14", "promoted_at": "later"}
        rpc.side_effect = [[current], True, [current]]
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "sales.json"
            snapshot_path.write_text(json.dumps(snapshot))

            result = publish_snapshot.publish(snapshot_path, Path("credentials.json"))

        self.assertTrue(result["skipped"])
        self.assertEqual(rpc.call_count, 3)
        self.assertEqual([call.args[3] for call in rpc.call_args_list], [
            "sfab_sales_snapshot_metadata", "sfab_sales_heartbeat_snapshot", "sfab_sales_snapshot_metadata"
        ])
        self.assertEqual(result["refreshed_at"], "later")

    @mock.patch.object(publish_snapshot, "load_credentials")
    @mock.patch.object(publish_snapshot, "rpc")
    def test_publish_rejects_tampered_payload_before_network(self, rpc, load_credentials):
        load_credentials.return_value = {}
        snapshot = valid_snapshot()
        snapshot["company"] = "tampered"
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "sales.json"
            snapshot_path.write_text(json.dumps(snapshot))
            with self.assertRaisesRegex(RuntimeError, "integrity"):
                publish_snapshot.publish(snapshot_path, Path("credentials.json"))
        rpc.assert_not_called()

    @mock.patch.object(publish_snapshot, "load_credentials")
    @mock.patch.object(publish_snapshot, "rpc")
    def test_changed_snapshot_stages_promotes_and_verifies(self, rpc, load_credentials):
        load_credentials.return_value = {
            "supabase_url": "https://example.test", "publishable_key": "key",
            "current_ar_ingestion_key": "ingest", "current_ar_promotion_key": "promote",
            "operator_verification_key": "verify",
        }
        snapshot = valid_snapshot()
        verified = {"snapshot_id": 43, "source_sha256": snapshot["sha256"], "as_of": snapshot["as_of"], "promoted_at": "later"}
        rpc.side_effect = [[{"snapshot_id": 42, "source_sha256": "0" * 64}], 43, None, [verified]]
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "sales.json"
            snapshot_path.write_text(json.dumps(snapshot))
            result = publish_snapshot.publish(snapshot_path, Path("credentials.json"))
        self.assertFalse(result["skipped"])

    @mock.patch.object(publish_snapshot, "load_credentials")
    @mock.patch.object(publish_snapshot, "rpc")
    def test_lost_heartbeat_race_does_not_repromote_old_snapshot(self, rpc, load_credentials):
        load_credentials.return_value = {
            "supabase_url": "https://example.test", "publishable_key": "key",
            "current_ar_ingestion_key": "ingest", "current_ar_promotion_key": "promote",
            "operator_verification_key": "verify",
        }
        snapshot = valid_snapshot()
        old = {"snapshot_id": 42, "source_sha256": snapshot["sha256"]}
        newer = {"snapshot_id": 43, "source_sha256": "f" * 64}
        rpc.side_effect = [[old], False, [newer]]
        with tempfile.TemporaryDirectory() as directory:
            snapshot_path = Path(directory) / "sales.json"
            snapshot_path.write_text(json.dumps(snapshot))
            result = publish_snapshot.publish(snapshot_path, Path("credentials.json"))
        self.assertTrue(result["skipped"])
        self.assertTrue(result["concurrent_update"])
        self.assertEqual(rpc.call_count, 3)
        self.assertNotIn("sfab_sales_promote_snapshot", [call.args[3] for call in rpc.call_args_list])

    @mock.patch.object(publish_snapshot.time, "sleep")
    @mock.patch.object(publish_snapshot.urllib.request, "urlopen")
    def test_rpc_does_not_retry_non_transient_http_error(self, urlopen, sleep):
        urlopen.side_effect = urllib.error.HTTPError("https://example.test", 400, "bad", {}, io.BytesIO(b"bad"))
        with self.assertRaisesRegex(RuntimeError, "HTTP 400"):
            publish_snapshot.rpc("https://example.test", "key", "token", "stage", {})
        self.assertEqual(urlopen.call_count, 1)
        sleep.assert_not_called()


if __name__ == "__main__":
    unittest.main()