import argparse
import json
import os
import sys
from typing import Any, Dict

from .client import GistFlow
from .types import GistSpec


def _env() -> Dict[str, str]:
    # minimal env loader (no python-dotenv dependency)
    return dict(os.environ)


def cmd_init(args) -> int:
    spec = GistFlow.create_private_gist(
        token=_env()["GITHUB_TOKEN"],
        filename=args.filename,
        initial=json.loads(args.initial_json),
        description=args.description,
    )
    print("GIST_ID=", spec.gist_id, sep="")
    print("GIST_FILE=", spec.filename, sep="")
    return 0


def cmd_push(args) -> int:
    env = _env()
    client = GistFlow(token=env["GITHUB_TOKEN"], spec=GistSpec(env["GIST_ID"], env.get("GIST_FILE", "state.json")))
    data = json.loads(args.json)
    client.push_json(data)
    return 0


def cmd_pull(args) -> int:
    env = _env()
    client = GistFlow(token=env["GITHUB_TOKEN"], spec=GistSpec(env["GIST_ID"], env.get("GIST_FILE", "state.json")))
    res = client.pull_json(etag=None)
    if res.data is None:
        print("null")
    else:
        print(json.dumps(res.data))
    return 0


def cmd_watch(args) -> int:
    env = _env()
    client = GistFlow(token=env["GITHUB_TOKEN"], spec=GistSpec(env["GIST_ID"], env.get("GIST_FILE", "state.json")))

    def cb(data: Any):
        print(json.dumps(data), flush=True)

    client.watch(cb, interval=args.interval, run_immediately=True)
    return 0


def cmd_rotate(args) -> int:
    env = _env()
    client = GistFlow(token=env["GITHUB_TOKEN"], spec=GistSpec(env["GIST_ID"], env.get("GIST_FILE", "state.json")))
    new_spec = client.rotate(delete_old=args.delete_old)
    print("NEW_GIST_ID=", new_spec.gist_id, sep="")
    print("Update workers with: export GIST_ID=" + new_spec.gist_id)
    return 0


def main() -> None:
    p = argparse.ArgumentParser(prog="gistflow")
    sub = p.add_subparsers(dest="cmd", required=True)

    p_init = sub.add_parser("init", help="Create a new private gist and print env vars.")
    p_init.add_argument("--filename", default="state.json")
    p_init.add_argument("--description", default="gistflow state")
    p_init.add_argument("--initial-json", default='{"status":"ok","ts":0}')
    p_init.set_defaults(fn=cmd_init)

    p_push = sub.add_parser("push", help="Push JSON to the configured gist.")
    p_push.add_argument("json", help='JSON string, e.g. \'{"k":"v"}\'')
    p_push.set_defaults(fn=cmd_push)

    p_pull = sub.add_parser("pull", help="Pull JSON from the configured gist.")
    p_pull.set_defaults(fn=cmd_pull)

    p_watch = sub.add_parser("watch", help="Poll and print JSON whenever it changes.")
    p_watch.add_argument("--interval", type=float, default=60.0)
    p_watch.set_defaults(fn=cmd_watch)

    p_rotate = sub.add_parser("rotate", help="Create a new gist with the current state (manual worker update required).")
    p_rotate.add_argument("--delete-old", action="store_true")
    p_rotate.set_defaults(fn=cmd_rotate)

    args = p.parse_args()
    rc = args.fn(args)
    sys.exit(rc)
