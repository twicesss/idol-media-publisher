"""Read public media RSS feeds for configured X profiles via FxEmbed.

This optional third-party feed integration reads metadata only. It does not
download media or publish to YouTube. Monitoring is disabled by default.
"""
from __future__ import annotations

import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote
import xml.etree.ElementTree as ET

import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "accounts.json"
STATE_PATH = ROOT / "data" / "seen_posts.json"
REPORT_PATH = ROOT / "data" / "latest_report.json"
FEED_BASE = "https://fxtwitter.com"
USER_AGENT = "IdolMediaPublisher/0.1 (public RSS reader)"
MAX_SEEN_PER_ACCOUNT = 5000


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


def clean_html(value: str) -> str:
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"</p\s*>", "\n", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(value)).strip()


def classify_media(url: str, media_type: str) -> str:
    media_type = (media_type or "").lower()
    path = url.lower().split("?", 1)[0]
    if "video" in media_type or path.endswith((".mp4", ".m4v", ".mov")):
        return "video"
    if "image" in media_type or path.endswith((".jpg", ".jpeg", ".png", ".webp", ".gif")):
        return "photo"
    return "unknown"


def parse_feed(xml_text: str, handle: str) -> list[dict[str, Any]]:
    root = ET.fromstring(xml_text)
    items = root.findall("./channel/item")
    parsed: list[dict[str, Any]] = []

    for item in items:
        guid = (item.findtext("guid") or item.findtext("link") or "").strip()
        link = (item.findtext("link") or guid).strip()
        title = clean_html(item.findtext("title") or "")
        description = clean_html(item.findtext("description") or "")
        published = (item.findtext("pubDate") or "").strip()
        media: list[dict[str, str]] = []

        enclosure = item.find("enclosure")
        if enclosure is not None:
            url = (enclosure.attrib.get("url") or "").strip()
            kind = classify_media(url, enclosure.attrib.get("type", ""))
            if url:
                media.append({"url": url, "type": kind})

        for element in item.iter():
            if element.tag.endswith("content") or element.tag.endswith("thumbnail"):
                url = (element.attrib.get("url") or "").strip()
                kind = classify_media(url, element.attrib.get("type", ""))
                if url and all(existing["url"] != url for existing in media):
                    media.append({"url": url, "type": kind})

        if not guid:
            continue
        post_id_match = re.search(r"/status/(\d+)", link or guid)
        parsed.append({
            "source_handle": handle,
            "post_id": post_id_match.group(1) if post_id_match else guid,
            "guid": guid,
            "post_url": link,
            "title": title,
            "text": description or title,
            "published": published,
            "media": media,
            "media_types": sorted({entry["type"] for entry in media}),
            "status": "discovered_metadata_only",
        })
    return parsed


def fetch_media_feed(handle: str, count: int) -> list[dict[str, Any]]:
    encoded_handle = quote(handle.lstrip("@"), safe="")
    url = f"{FEED_BASE}/{encoded_handle}/media.xml"
    response = requests.get(
        url,
        params={"count": max(1, min(count, 100))},
        headers={"User-Agent": USER_AGENT, "Accept": "application/rss+xml, application/xml"},
        timeout=30,
    )
    response.raise_for_status()
    return parse_feed(response.text, handle)


def main() -> int:
    config = load_json(CONFIG_PATH, {})
    if not config.get("monitoring_enabled", False):
        print("Monitoring is disabled in config/accounts.json; no feed requests were made.")
        return 0
    if config.get("feed_provider") != "fxembed":
        print("ERROR: unsupported feed_provider; expected fxembed.")
        return 2

    accounts = config.get("accounts", [])
    if not isinstance(accounts, list) or not accounts:
        print("ERROR: config/accounts.json must contain at least one account.")
        return 2

    feed_count = int(config.get("feed_count", 100))
    state = load_json(STATE_PATH, {"seen_by_account": {}})
    seen_by_account = state.setdefault("seen_by_account", {})
    newly_discovered: list[dict[str, Any]] = []
    baseline: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []

    for raw_handle in accounts:
        handle = str(raw_handle).strip().lstrip("@")
        if not handle:
            continue
        try:
            posts = fetch_media_feed(handle, feed_count)
            known_ids = set(seen_by_account.get(handle, []))
            if handle not in seen_by_account:
                seen_by_account[handle] = [post["guid"] for post in posts][-MAX_SEEN_PER_ACCOUNT:]
                baseline.append({"handle": handle, "baseline_posts": len(posts)})
                continue

            fresh = [post for post in posts if post["guid"] not in known_ids]
            newly_discovered.extend(reversed(fresh))
            updated_ids = [post["guid"] for post in posts] + list(known_ids)
            seen_by_account[handle] = list(dict.fromkeys(updated_ids))[:MAX_SEEN_PER_ACCOUNT]
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            failures.append({"handle": handle, "error": str(exc)})

    report = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "feed_provider": "FxEmbed public RSS",
        "accounts_configured": len(accounts),
        "baseline": baseline,
        "new_media_posts": newly_discovered,
        "failures": failures,
        "note": "Metadata only. No media downloaded and no YouTube publishing performed.",
    }
    save_json(REPORT_PATH, report)
    save_json(STATE_PATH, seen_by_account)
    print(json.dumps({
        "accounts_checked": len(accounts),
        "baseline_accounts": len(baseline),
        "new_media_posts": len(newly_discovered),
        "failures": len(failures),
        "report": str(REPORT_PATH.relative_to(ROOT)),
    }, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
