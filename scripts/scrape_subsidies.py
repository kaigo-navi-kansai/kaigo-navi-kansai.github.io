"""県庁・厚労省の介護関連ページを巡回し、テキスト抽出して data/subsidies.json に保存する。

注意: robots.txt を尊重し、1秒以上のリクエスト間隔・UA明示で実行する。
"""
from __future__ import annotations

import sys
import time
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from common import (
    SUBSIDIES_JSON, USER_AGENT, load_json, save_json, now_iso,
)

TIMEOUT = 20
REQUEST_INTERVAL_SEC = 1.2
MAX_TEXT_CHARS = 20000  # 1ページあたりの保存上限


def check_robots(url: str) -> bool:
    """robots.txt を確認し、UAが該当URLを取得可か返す。取得失敗時は安全側に True。"""
    try:
        parsed = urlparse(url)
        robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"
        rp = RobotFileParser()
        rp.set_url(robots_url)
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception as e:
        print(f"  [warn] robots.txt check failed: {e}", file=sys.stderr)
        return True


def fetch_text(url: str) -> str:
    """URLを取得してHTMLから本文テキストを抽出する。"""
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,*/*;q=0.8",
        "Accept-Language": "ja,en;q=0.8",
    }
    r = requests.get(url, headers=headers, timeout=TIMEOUT)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding
    soup = BeautifulSoup(r.text, "lxml")

    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "form"]):
        tag.decompose()

    main = (
        soup.find("main")
        or soup.find(id="content")
        or soup.find(id="contents")
        or soup.find("article")
        or soup.body
        or soup
    )

    text = main.get_text(separator="\n", strip=True)
    lines = [ln for ln in (l.strip() for l in text.splitlines()) if ln]
    cleaned = "\n".join(lines)
    return cleaned[:MAX_TEXT_CHARS]


def main() -> int:
    data = load_json(SUBSIDIES_JSON)
    if not data:
        print("subsidies.json が見つかりません", file=sys.stderr)
        return 1

    sources = data.get("sources", {})
    if not sources:
        print("sources が空です", file=sys.stderr)
        return 1

    success = 0
    failures = []
    keys = list(sources.keys())

    for i, key in enumerate(keys):
        src = sources[key]
        url = src.get("url")
        print(f"[{i+1}/{len(keys)}] {key}: {url}")

        if not url:
            print("  [skip] URLなし")
            continue

        if not check_robots(url):
            print("  [skip] robots.txt で不許可")
            failures.append((key, "robots disallowed"))
            continue

        try:
            text = fetch_text(url)
            src["raw_text"] = text
            src["fetched"] = now_iso()
            print(f"  [ok] {len(text)} chars")
            success += 1
        except Exception as e:
            print(f"  [error] {e}", file=sys.stderr)
            failures.append((key, str(e)))

        if i < len(keys) - 1:
            time.sleep(REQUEST_INTERVAL_SEC)

    data["sources"] = sources
    data["updated"] = now_iso()
    save_json(SUBSIDIES_JSON, data)

    print(f"\n完了: 成功 {success}/{len(keys)} 件")
    if failures:
        print("失敗:")
        for k, reason in failures:
            print(f"  - {k}: {reason}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
