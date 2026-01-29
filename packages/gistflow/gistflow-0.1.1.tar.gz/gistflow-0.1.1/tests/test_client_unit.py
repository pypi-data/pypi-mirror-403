import unittest
from unittest.mock import patch, Mock
import os

from gistflow import GistFlow, GistSpec
from gistflow.errors import AuthError, NotFoundError, ApiError


class TestGistFlowPush(unittest.TestCase):
    def test_push_json_calls_patch_with_expected_payload(self):
        client = GistFlow(token="t", spec=GistSpec("gid", "state.json"))

        r = Mock()
        r.status_code = 200

        with patch("requests.patch", return_value=r) as mock_patch:
            client.push_json({"a": 1})

            mock_patch.assert_called_once()
            args, kwargs = mock_patch.call_args

            # URL
            self.assertIn("/gists/gid", args[0])

            # Headers include auth
            self.assertIn("Authorization", kwargs["headers"])

            # Payload shape
            self.assertEqual(
                kwargs["json"],
                {"files": {"state.json": {"content": '{"a": 1}'}}}
            )


class TestGistFlowPullErrors(unittest.TestCase):
    def test_pull_json_missing_file_raises_notfound(self):
        client = GistFlow(token="t", spec=GistSpec("gid", "state.json"))

        r = Mock()
        r.status_code = 200
        r.headers = {"ETag": '"new"'}
        r.json.return_value = {"files": {"other.json": {"content": '{"x":1}'}}}

        with patch("requests.get", return_value=r):
            with self.assertRaises(NotFoundError):
                client.pull_json()

    def test_pull_json_invalid_json_raises_apierror(self):
        client = GistFlow(token="t", spec=GistSpec("gid", "state.json"))

        r = Mock()
        r.status_code = 200
        r.headers = {"ETag": '"new"'}
        r.json.return_value = {"files": {"state.json": {"content": "{not valid json"}}}

        with patch("requests.get", return_value=r):
            with self.assertRaises(ApiError):
                client.pull_json()

    def test_pull_json_sends_if_none_match_header(self):
        client = GistFlow(token="t", spec=GistSpec("gid", "state.json"))

        r = Mock()
        r.status_code = 304
        r.headers = {}

        with patch("requests.get", return_value=r) as mock_get:
            client.pull_json(etag='"abc"')
            _, kwargs = mock_get.call_args
            self.assertEqual(kwargs["headers"]["If-None-Match"], '"abc"')


class TestErrorMessageParsing(unittest.TestCase):
    def test_handle_common_errors_uses_message_field_when_json(self):
        client = GistFlow(token="t", spec=GistSpec("gid", "state.json"))

        r = Mock()
        r.status_code = 403
        r.reason = "Forbidden"
        r.text = '{"message":"Resource not accessible by personal access token"}'
        r.json.return_value = {"message": "Resource not accessible by personal access token"}

        with self.assertRaises(AuthError) as ctx:
            client._handle_common_errors(r)

        self.assertIn("Resource not accessible", str(ctx.exception))


class TestRotate(unittest.TestCase):
    def test_rotate_creates_new_gist_and_returns_new_spec(self):
        client = GistFlow(token="t", spec=GistSpec("oldid", "state.json"))

        # pull_json() returns current state
        with patch.object(client, "pull_json") as mock_pull:
            mock_pull.return_value = Mock(changed=True, etag='"e"', data={"x": 1})

            # create_private_gist returns new spec
            with patch.object(GistFlow, "create_private_gist") as mock_create:
                mock_create.return_value = GistSpec("newid", "state.json")

                new_spec = client.rotate(delete_old=False)

                self.assertEqual(new_spec.gist_id, "newid")
                self.assertEqual(new_spec.filename, "state.json")
                mock_create.assert_called_once()

    def test_rotate_delete_old_calls_delete(self):
        client = GistFlow(token="t", spec=GistSpec("oldid", "state.json"))

        with patch.object(client, "pull_json") as mock_pull:
            mock_pull.return_value = Mock(changed=True, etag='"e"', data={"x": 1})

            with patch.object(GistFlow, "create_private_gist") as mock_create:
                mock_create.return_value = GistSpec("newid", "state.json")

                r_del = Mock()
                r_del.status_code = 204

                with patch("requests.delete", return_value=r_del) as mock_delete:
                    client.rotate(delete_old=True)
                    mock_delete.assert_called_once()
                    args, _ = mock_delete.call_args
                    self.assertIn("/gists/oldid", args[0])


class TestFromEnv(unittest.TestCase):
    def test_from_os_env_reads_expected_vars(self):
        old = dict(os.environ)
        try:
            os.environ["GITHUB_TOKEN"] = "tok"
            os.environ["GIST_ID"] = "gid"
            os.environ["GIST_FILE"] = "f.json"

            c = GistFlow.from_os_env()
            self.assertEqual(c.token, "tok")
            self.assertEqual(c.spec.gist_id, "gid")
            self.assertEqual(c.spec.filename, "f.json")
        finally:
            os.environ.clear()
            os.environ.update(old)
