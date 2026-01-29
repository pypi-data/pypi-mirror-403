from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional, Dict, Any

import requests

from .errors import AuthError, NotFoundError, RateLimitError, ApiError
from .types import GistSpec, PullResult, JsonDict

logger = logging.getLogger("gistflow")


class GistFlow:
    """
    Minimal v1 client:
      - create private gist
      - push JSON (overwrite file content)
      - pull JSON with ETag (returns 304 as changed=False)
      - watch(callback, interval)
      - rotate (creates new gist with same content)
    """

    def __init__(self, token: str, spec: GistSpec):
        self.token = token
        self.spec = spec

    @staticmethod
    def from_env(env: Dict[str, str]) -> "GistFlow":
        token = env["GITHUB_TOKEN"]
        gist_id = env["GIST_ID"]
        filename = env.get("GIST_FILE", "state.json")
        return GistFlow(token=token, spec=GistSpec(gist_id=gist_id, filename=filename))

    @classmethod
    def from_os_env(cls) -> "GistFlow":
        return cls.from_env(dict(os.environ))

    # ---------- low-level helpers ----------

    def _headers(self, extra: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        h = {
            "Authorization": f"Bearer {self.token}",  # never log this
            "Accept": "application/vnd.github+json",
            "User-Agent": "gistflow/0.1.0",
        }
        if extra:
            h.update(extra)
        return h

    def _handle_common_errors(self, r: requests.Response) -> None:
        msg = r.text
        try:
            j = r.json()
            if isinstance(j, dict) and "message" in j:
                msg = j["message"]
        except Exception:
            pass

        # Best-effort request context (may not exist on mocked responses)
        method = getattr(getattr(r, "request", None), "method", "?")
        url = getattr(r, "url", "?")

        logger.error(
            "GitHub API error: %s %s (status=%s) message=%r",
            method,
            url,
            r.status_code,
            msg,
        )

        if r.status_code in (401, 403):
            raise AuthError(f"{r.status_code} {r.reason}: {msg}")
        if r.status_code == 404:
            raise NotFoundError(f"404 Not Found: {msg}")
        if r.status_code == 429 or (r.status_code == 403 and "rate limit" in str(msg).lower()):
            raise RateLimitError(f"{r.status_code} {r.reason}: {msg}")
        if r.status_code >= 400:
            raise ApiError(f"{r.status_code} {r.reason}: {msg}")

    # ---------- gist lifecycle ----------

    @classmethod
    def create_private_gist(
        cls,
        token: str,
        filename: str,
        initial: Dict[str, Any],
        description: str = "gistflow state",
    ) -> GistSpec:
        payload = {
            "description": description,
            "public": False,
            "files": {filename: {"content": json.dumps(initial)}},
        }

        logger.info("Creating private gist (filename=%s)", filename)

        r = requests.post(
            "https://api.github.com/gists",
            headers={
                "Authorization": f"Bearer {token}",  # never log this
                "Accept": "application/vnd.github+json",
                "User-Agent": "gistflow/0.1.0",
            },
            json=payload,
            timeout=15,
        )

        if r.status_code >= 400:
            msg = r.text
            try:
                j = r.json()
                if isinstance(j, dict) and "message" in j:
                    msg = j["message"]
            except Exception:
                pass

            logger.error(
                "GitHub API error: POST /gists (status=%s) message=%r",
                r.status_code,
                msg,
            )

            if r.status_code in (401, 403):
                raise AuthError(f"{r.status_code} {r.reason}: {msg}")
            raise ApiError(f"{r.status_code} {r.reason}: {msg}")

        gist_id = r.json()["id"]
        logger.info("Created private gist (gist_id=%s)", gist_id)
        return GistSpec(gist_id=gist_id, filename=filename)

    # ---------- state operations ----------

    def push_json(self, data: JsonDict) -> None:
        payload = {"files": {self.spec.filename: {"content": json.dumps(data)}}}

        logger.info("Pushing JSON (gist_id=%s file=%s)", self.spec.gist_id, self.spec.filename)
        if isinstance(data, dict):
            logger.debug("Push payload keys=%s", list(data.keys()))
        else:
            logger.debug("Push payload type=%s", type(data).__name__)

        r = requests.patch(
            f"https://api.github.com/gists/{self.spec.gist_id}",
            headers=self._headers(),
            json=payload,
            timeout=15,
        )

        logger.debug("Push response status=%s", r.status_code)

        if r.status_code >= 400:
            self._handle_common_errors(r)

    def pull_json(self, etag: Optional[str] = None) -> PullResult:
        extra: Dict[str, str] = {}
        if etag:
            extra["If-None-Match"] = etag

        logger.debug(
            "Pulling JSON (gist_id=%s file=%s etag=%r)",
            self.spec.gist_id,
            self.spec.filename,
            etag,
        )

        r = requests.get(
            f"https://api.github.com/gists/{self.spec.gist_id}",
            headers=self._headers(extra),
            timeout=15,
        )

        if r.status_code == 304:
            logger.debug("Pull not modified (304) (gist_id=%s)", self.spec.gist_id)
            return PullResult(changed=False, etag=etag, data=None)

        if r.status_code >= 400:
            self._handle_common_errors(r)

        new_etag = r.headers.get("ETag")
        logger.debug("Pull response status=%s new_etag=%r", r.status_code, new_etag)

        j = r.json()

        try:
            content = j["files"][self.spec.filename]["content"]
        except KeyError:
            raise NotFoundError(f"File '{self.spec.filename}' not found in gist {self.spec.gist_id}")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            raise ApiError(f"Invalid JSON in gist file '{self.spec.filename}': {e}")

        logger.info("Pulled JSON changed=True (gist_id=%s file=%s)", self.spec.gist_id, self.spec.filename)
        return PullResult(changed=True, etag=new_etag, data=data)

    def watch(self, callback, interval: float = 60.0, *, run_immediately: bool = True) -> None:
        """
        Poll forever. Calls callback(data) only when the remote state changes.

        Uses ETag to avoid downloading content when unchanged.
        """
        logger.info(
            "Starting watch (gist_id=%s file=%s interval=%ss run_immediately=%s)",
            self.spec.gist_id,
            self.spec.filename,
            interval,
            run_immediately,
        )

        etag: Optional[str] = None

        if run_immediately:
            res = self.pull_json(etag=None)
            if res.changed and res.data is not None:
                callback(res.data)
            etag = res.etag

        while True:
            time.sleep(interval)
            res = self.pull_json(etag=etag)
            if res.changed and res.data is not None:
                callback(res.data)
                etag = res.etag

    def rotate(self, delete_old: bool = False, description: str = "gistflow rotated state") -> GistSpec:
        """
        Create a new private gist containing the current state file, returning the new GistSpec.
        NOTE: Workers must be updated manually with the new gist id (v1 design).

        Current v1 behavior rotates ONLY the configured file, not all files in the gist.
        """
        logger.info("Rotating gist (old_gist_id=%s delete_old=%s)", self.spec.gist_id, delete_old)

        # Fetch latest data (force)
        res = self.pull_json(etag=None)
        current = res.data if res.data is not None else {}

        new_spec = GistFlow.create_private_gist(
            token=self.token,
            filename=self.spec.filename,
            initial=current,
            description=description,
        )

        logger.info("Rotated gist created (new_gist_id=%s)", new_spec.gist_id)

        if delete_old:
            logger.info("Deleting old gist (old_gist_id=%s)", self.spec.gist_id)

            r = requests.delete(
                f"https://api.github.com/gists/{self.spec.gist_id}",
                headers=self._headers(),
                timeout=15,
            )

            logger.debug("Delete old gist response status=%s", r.status_code)

            if r.status_code >= 400:
                self._handle_common_errors(r)

        return new_spec
