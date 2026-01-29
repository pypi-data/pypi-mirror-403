import os
import time
import json
import unittest
from typing import Any, Dict, Optional

import requests

from gistflow import GistFlow, GistSpec


def _load_dotenv(path: str) -> None:
    """Minimal .env loader (no python-dotenv dependency)."""
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip('"').strip("'")
            os.environ.setdefault(k, v)


def _now() -> int:
    return int(time.time())


def _pretty(obj: Any, max_len: int = 500) -> str:
    """Pretty JSON with truncation for logs."""
    try:
        s = json.dumps(obj, sort_keys=True)
    except Exception:
        s = str(obj)
    return s if len(s) <= max_len else s[:max_len] + "...(truncated)"


def _log(msg: str) -> None:
    print(msg, flush=True)


@unittest.skipUnless(
    os.environ.get("GISTFLOW_INTEGRATION") == "1",
    "Integration test disabled. Run with GISTFLOW_INTEGRATION=1",
)
class TestIntegrationJourney(unittest.TestCase):
    """
    Real end-to-end test against GitHub Gists.

    Requires:
      - .env_test containing GITHUB_TOKEN (and optionally GIST_FILE)
      - or environment variables already set
      - GISTFLOW_INTEGRATION=1 to enable the test

    This test:
      1) creates a new private gist
      2) pulls initial JSON
      3) pushes updated JSON
      4) verifies ETag 304 behavior
      5) rotates to a new gist id
      6) pulls from rotated gist
      7) deletes created gists (best effort)
    """

    def setUp(self) -> None:
        _log("\n========== gistflow integration journey: SETUP ==========")

        _load_dotenv(".env_test")

        self.token = os.environ.get("GITHUB_TOKEN")
        self.filename = os.environ.get("GIST_FILE", "state.json")

        if not self.token:
            self.skipTest("GITHUB_TOKEN not set (use .env_test or env var)")

        # Keep track of created gists so we can cleanup.
        self._created_gist_ids = []

        initial = {"status": "init", "ts": _now()}

        _log(f"[setup] Creating private gist with file={self.filename}")
        _log(f"[setup] Initial content: {_pretty(initial)}")

        self.spec = GistFlow.create_private_gist(
            token=self.token,
            filename=self.filename,
            initial=initial,
            description="gistflow integration test (auto-cleanup)",
        )
        self._created_gist_ids.append(self.spec.gist_id)

        _log(f"[setup] Created gist_id={self.spec.gist_id}")

        self.client = GistFlow(token=self.token, spec=self.spec)
        _log("========== SETUP complete ==========\n")

    def tearDown(self) -> None:
        _log("\n========== gistflow integration journey: TEARDOWN ==========")
        # Best-effort cleanup
        for gid in list(dict.fromkeys(self._created_gist_ids)):
            _log(f"[teardown] Deleting gist_id={gid} ...")
            try:
                r = requests.delete(
                    f"https://api.github.com/gists/{gid}",
                    headers={
                        "Authorization": f"Bearer {self.token}",
                        "Accept": "application/vnd.github+json",
                        "User-Agent": "gistflow-test/0.1.0",
                    },
                    timeout=15,
                )
                _log(f"[teardown] Delete status={r.status_code}")
            except Exception as e:
                _log(f"[teardown] Delete failed for {gid}: {e}")

        _log("========== TEARDOWN complete ==========\n")

    def test_full_journey_create_push_pull_rotate(self) -> None:
        _log("\n========== TEST: full journey ==========")

        # 1) Pull initial
        with self.subTest("1) pull initial state"):
            _log("[1] Pull initial state from gist")
            res1 = self.client.pull_json()
            _log(f"[1] changed={res1.changed} etag={res1.etag}")
            _log(f"[1] data={_pretty(res1.data)}")

            self.assertTrue(res1.changed)
            self.assertIsNotNone(res1.data)
            self.assertEqual(res1.data.get("status"), "init")

        # 2) Push update
        with self.subTest("2) push updated state"):
            payload = {"status": "updated", "ts": _now(), "note": "integration-test"}
            _log("[2] Push updated state")
            _log(f"[2] payload={_pretty(payload)}")
            self.client.push_json(payload)
            _log("[2] push_json OK")

        # 3) Pull updated
        with self.subTest("3) pull updated state"):
            _log("[3] Pull updated state")
            res2 = self.client.pull_json()
            _log(f"[3] changed={res2.changed} etag={res2.etag}")
            _log(f"[3] data={_pretty(res2.data)}")

            self.assertTrue(res2.changed)
            self.assertIsNotNone(res2.data)
            self.assertEqual(res2.data.get("status"), "updated")

        # 4) Verify ETag -> 304
        with self.subTest("4) verify ETag no-change behavior (304)"):
            _log("[4] Pull with If-None-Match (should be 304/unchanged)")
            _log(f"[4] using etag={res2.etag}")
            res3 = self.client.pull_json(etag=res2.etag)
            _log(f"[4] changed={res3.changed} etag={res3.etag} data={_pretty(res3.data)}")

            self.assertFalse(res3.changed)
            self.assertIsNone(res3.data)

        # 5) Rotate
        with self.subTest("5) rotate gist (new gist id)"):
            _log("[5] Rotate gist (creates a new private gist with current content)")
            new_spec = self.client.rotate(delete_old=False, description="gistflow rotated integration test")
            _log(f"[5] rotated new gist_id={new_spec.gist_id} filename={new_spec.filename}")

            self.assertNotEqual(new_spec.gist_id, self.spec.gist_id)

            # track for cleanup
            self._created_gist_ids.append(new_spec.gist_id)

        # 6) Pull from rotated gist
        with self.subTest("6) pull from rotated gist"):
            _log("[6] Pull from rotated gist (should contain updated state)")
            rotated_client = GistFlow(token=self.token, spec=GistSpec(new_spec.gist_id, self.filename))
            res4 = rotated_client.pull_json()
            _log(f"[6] changed={res4.changed} etag={res4.etag}")
            _log(f"[6] data={_pretty(res4.data)}")

            self.assertTrue(res4.changed)
            self.assertIsNotNone(res4.data)
            self.assertEqual(res4.data.get("status"), "updated")

        _log("========== TEST complete ==========\n")
