"""共通ユーティリティ: Claude APIクライアント、記事データI/O、日付処理"""
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
ARTICLES_JSON = DATA_DIR / "articles.json"
SUBSIDIES_JSON = DATA_DIR / "subsidies.json"
ARTICLES_HTML_DIR = ROOT / "articles"

JST = timezone(timedelta(hours=9))
USER_AGENT = "kaigo-navi-kansai-bot/1.0 (+https://kaigo-navi-kansai.github.io/)"

# --- env loading ------------------------------------------------------------

def load_env() -> None:
    """ローカル実行時は ../.env を読む。CI は既に環境変数設定済みのためスキップ。"""
    env_path = ROOT / ".env"
    if env_path.exists():
        load_dotenv(env_path)


# --- JSON I/O ---------------------------------------------------------------

def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def load_articles() -> dict:
    data = load_json(ARTICLES_JSON)
    if not data:
        data = {"version": "1.0", "updated": None, "articles": []}
    data.setdefault("articles", [])
    return data


def save_articles(data: dict) -> None:
    data["updated"] = datetime.now(JST).isoformat()
    save_json(ARTICLES_JSON, data)


def upsert_article(data: dict, article: dict) -> None:
    """slug 一致で既存記事を上書き、なければ追加。"""
    articles = data["articles"]
    for i, a in enumerate(articles):
        if a.get("slug") == article.get("slug"):
            articles[i] = article
            return
    articles.append(article)


# --- helpers ----------------------------------------------------------------

def now_iso() -> str:
    return datetime.now(JST).isoformat()


def today_iso_date() -> str:
    return datetime.now(JST).strftime("%Y-%m-%d")


_slug_re = re.compile(r"[^a-z0-9\-]+")


def make_slug(prefix: str, key: str) -> str:
    """英数字とハイフン以外を除去した slug を生成。"""
    base = re.sub(r"[^a-zA-Z0-9]+", "-", key.lower()).strip("-")
    return f"{prefix}-{base}" if prefix else base


def unique_slug(articles: list[dict], candidate: str) -> str:
    existing = {a.get("slug") for a in articles}
    if candidate not in existing:
        return candidate
    i = 2
    while f"{candidate}-{i}" in existing:
        i += 1
    return f"{candidate}-{i}"


# --- Claude API -------------------------------------------------------------

def get_anthropic_client():
    """anthropic.Anthropic を返す。キー未設定時は明示エラー。"""
    import anthropic
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY が設定されていません。.env または GitHub Secrets を確認してください。"
        )
    return anthropic.Anthropic(api_key=key)


MODEL_DEFAULT = "claude-sonnet-4-6"


def call_claude(
    system: str,
    user: str,
    *,
    model: str = MODEL_DEFAULT,
    max_tokens: int = 4000,
    temperature: float = 0.4,
) -> str:
    """Claude に依頼してテキスト応答を返す。system プロンプトはキャッシュ対象。"""
    client = get_anthropic_client()
    resp = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        temperature=temperature,
        system=[{"type": "text", "text": system, "cache_control": {"type": "ephemeral"}}],
        messages=[{"role": "user", "content": user}],
    )
    parts = []
    for block in resp.content:
        if getattr(block, "type", None) == "text":
            parts.append(block.text)
    return "".join(parts).strip()


def call_claude_json(
    system: str,
    user: str,
    *,
    model: str = MODEL_DEFAULT,
    max_tokens: int = 4000,
    temperature: float = 0.3,
) -> Any:
    """Claude 応答を JSON として解釈して返す。```json``` フェンスは除去。"""
    text = call_claude(system, user, model=model, max_tokens=max_tokens, temperature=temperature)
    text = text.strip()
    m = re.search(r"```(?:json)?\s*(.*?)\s*```", text, re.DOTALL)
    if m:
        text = m.group(1)
    return json.loads(text)
