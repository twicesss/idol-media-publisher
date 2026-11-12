"""Poll configured X accounts for recent posts using the official X API.

This first-stage monitor only reads public post metadata and media attachment
metadata. It deliberately does not download media or publish to YouTube.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "accounts.json"
STATE_PATH = ROOT / "data" / "seen_posts.json"
REPORT_PATH = ROOT / "data" / "latest_report.json"
X_API = "https://api.x.com/2"


def load_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    with temp.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
    temp.replace(path)


def api_get(path: str, token: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    response = requests.get(
        f"{X_API}{path}",
        headers={"Authorization": f"Bearer {token}"},
        params=params,
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def get_user_id(handle: str, token: str, user_cache: dict[str, str]) -> str:
    if handle in user_cache:
        return user_cache[handle]
    result = api_get(f"/users/by/username/{handle}", token, {
        "user.fields": "id,username,name,protected"
    })
    user = result.get("data")
    if not user or user.get("protected"):
        raise RuntimeError(f"Account @{handle} is unavailable or protected.")
    user_id = user["id"]
    user_cache[handle] = user_id
    return user_id


def fetch_recent_posts(user_id: str, token: str) -> list[dict[str, Any]]:
    result = api_get(
        f"/users/{user_id}/tweets",
        token,
        {
            "max_results": 10,
            "exclude": "retweets",
            "tweet.fields": "id,text,created_at,attachments,referenced_tweets",
            "expansions": "attachments.media_keys",
            "media.fields": "media_key,type,url,preview_image_url,duration_ms,variants",
        },
    )
    posts = result.get("data", [])
    media = result.get("includes", {}).get("media", [])
    media_by_key = {item["media_key"]: item for item in media}
    for post in posts:
        keys = post.get("attachments", {}).get("media_keys", [])
        post["media"] = [media_by_key[key] for key in keys if key in media_by_key]
    return posts


def main() -> int:
    token = os.environ.get("X_BEARER_TOKEN", "").strip()
    if not token:
        print("ERROR: X_BEARER_TOKEN secret is not configured.", file=sys.stderr)
        return 2

    config = load_json(CONFIG_PATH, {})
    accounts = config.get("accounts", [])
    if not isinstance(accounts, list) or not accounts:
        print("ERROR: config/accounts.json must contain at least one account.")
        return 2

    state = load_json(STATE_PATH, {"seen_post_ids": []})
    seen = set(state.get("seen_post_ids", []))
    user_cache: dict[str, str] = {}
    discovered: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for raw_handle in accounts:
        handle = str(raw_handle).strip().lstrip("@")
        if not handle:
            continue
        try:
            user_id = get_user_id(handle, token, user_cache)
            posts = fetch_recent_posts(user_id, token)
            for post in posts:
                post_id = post.get("id")
                if not post_id or post_id in seen:
                    continue
                attachments = post.get("media", [])
                media_types = sorted({m.get("type", "unknown") for m in attachments})
                discovered.append({
                    "source_handle": handle,
                    "post_id": post_id,
                    "text": post.get("text", ""),
                    "created_at": post.get("created_at"),
                    "post_url": f"https://x.com/{handle}/status/{post_id}",
                    "media_types": media_types,
                    "media_metadata": attachments,
                    "status": "discovered_metadata_only",
                })
                seen.add(post_id)
        except requests.HTTPError as exc:
            failures.append({"handle": handle, "error": str(exc)})
        except (requests.RequestException, KeyError, ValueError, RuntimeError) as exc:
            failures.append({"handle": handle, "error": str(exc)})

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "accounts_configured": len(accounts),
        "new_posts": discovered,
        "failures": failures,
        "note": "Metadata discovery only. Media retrieval and publishing are intentionally disabled.",
    }
    save_json(REPORT_PATH, report)
    save_json(STATE_PATH, {"seen_post_ids": sorted(seen)})

    print(json.dumps({
        "accounts_checked": len(accounts),
        "new_posts": len(discovered),
        "failures": len(failures),
        "report": str(REPORT_PATH.relative_to(ROOT)),
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
