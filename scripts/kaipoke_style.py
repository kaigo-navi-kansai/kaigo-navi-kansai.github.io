"""カイポケコラムから構造パターンだけを抽出するヘルパー。

ここで取得するのは「記事タイトル」「H2見出しテキスト」などのメタ構造のみ。
本文テキストは保存・再配布しない(著作権配慮)。
取得に失敗した場合は空を返し、呼び出し側は組み込みテンプレートへフォールバック。
"""
from __future__ import annotations

import time
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests
from bs4 import BeautifulSoup

from common import USER_AGENT

INDEX_URL = "https://ads.kaipoke.biz/column/"
DELAY_SEC = 2.0
TIMEOUT = 15


def _robots_ok(url: str) -> bool:
    try:
        p = urlparse(url)
        rp = RobotFileParser()
        rp.set_url(f"{p.scheme}://{p.netloc}/robots.txt")
        rp.read()
        return rp.can_fetch(USER_AGENT, url)
    except Exception:
        return True


def _fetch(url: str) -> str | None:
    if not _robots_ok(url):
        return None
    try:
        r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
        r.raise_for_status()
        r.encoding = r.apparent_encoding or r.encoding
        return r.text
    except Exception:
        return None


def fetch_column_titles(limit: int = 12) -> list[dict]:
    """コラム一覧ページからタイトルとURLのみ抽出。"""
    html = _fetch(INDEX_URL)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    out: list[dict] = []
    seen: set[str] = set()
    for a in soup.select("a"):
        href = a.get("href", "") or ""
        text = a.get_text(strip=True)
        if not href or not text:
            continue
        if "/column/" not in href:
            continue
        if not (12 <= len(text) <= 90):
            continue
        full = urljoin(INDEX_URL, href)
        if full in seen:
            continue
        seen.add(full)
        out.append({"title": text, "url": full})
        if len(out) >= limit:
            break
    return out


def fetch_outline(url: str) -> list[str]:
    """単一記事ページから H2 見出しテキストのみ抽出(本文は取得しない)。"""
    time.sleep(DELAY_SEC)
    html = _fetch(url)
    if not html:
        return []
    soup = BeautifulSoup(html, "lxml")
    headings: list[str] = []
    for h in soup.find_all("h2"):
        t = h.get_text(strip=True)
        if t and len(t) <= 80:
            headings.append(t)
    return headings[:12]


def build_style_hints() -> str:
    """Claude に渡す文体・構成ヒントを組み立てる。取得失敗時は既定テンプレ。"""
    default_hint = (
        "記事構造の参考: 冒頭リード(問いかけ/結論)→目次→番号付きH2見出し(5〜6本)→"
        "各H2下にH3サブ見出し→ポイントボックス/表/ステップ一覧を適宜→まとめ/CTA。"
        "読者が現場で実行できる具体性(数字・手順・期限)を重視。"
    )
    try:
        titles = fetch_column_titles(limit=10)
    except Exception:
        return default_hint
    if not titles:
        return default_hint
    outlines: list[str] = []
    for t in titles[:2]:  # 参照記事は2本まで(リクエスト節度)
        try:
            outline = fetch_outline(t["url"])
        except Exception:
            outline = []
        if outline:
            outlines.append(f"- 参考記事「{t['title']}」の見出し構造: " + " / ".join(outline[:6]))
    hint = default_hint
    if outlines:
        hint += "\n\n実在する介護系コラムの構造パターン例(文体模倣のため、本文は転載しない):\n" + "\n".join(outlines)
    titles_line = " / ".join(t["title"] for t in titles[:8])
    hint += f"\n\n最近のコラム題材傾向: {titles_line}"
    return hint
