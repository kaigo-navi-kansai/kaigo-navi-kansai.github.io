"""AI・ICT活用tips記事を週1本、Claude に生成させて articles.json に追記する。

トピックプールから未使用テーマを選び、管理者向けの実践記事を書く。
"""
from __future__ import annotations

import random
import sys

from common import (
    load_env, load_articles, save_articles, upsert_article,
    call_claude_json, today_iso_date, make_slug, unique_slug,
)

TOPIC_POOL = [
    ("chatgpt-kaigo-kiroku", "ChatGPTで介護記録を時短する方法"),
    ("ai-shift-sakusei", "AIで介護シフト作成を効率化する方法"),
    ("ict-ritsyoku-bousi", "ICTツール導入で離職防止につなげる方法"),
    ("chatgpt-kensyu-shiryou", "ChatGPTで職員研修資料を自動作成する方法"),
    ("kaigo-dx-hojokin", "介護施設でのDX推進・補助金活用ガイド"),
    ("ai-yoka-scheduling", "AIで利用者の余暇活動スケジュールを最適化する方法"),
    ("chatgpt-kazoku-renraku", "ChatGPTでご家族向け連絡文を時短する方法"),
    ("ict-miorisei", "ICT見守りセンサーの導入効果を現場指標で測る"),
    ("ai-nyuyoku-kaigi", "AI議事録で入浴介助カンファレンスを効率化"),
    ("chatgpt-manual", "ChatGPTで施設マニュアルを更新する実践手順"),
]

SYSTEM_PROMPT = """あなたは介護現場に詳しく、AI・ICT活用にも明るい編集者です。
関西圏の介護施設管理者(特養施設長・グループホーム管理者・デイサービス責任者)向けに、
業務改善の観点から実践的な記事を書きます。

厳守事項:
- 現場で明日から試せる具体的な手順を1つ以上含める
- ChatGPT・Geminiなど具体的なツール名を出してよいが、特定商品への誘導は避ける
- 個人情報をプロンプトに入れないなどリスクへの注意も一文入れる
- 断定しすぎず、現場に合わせて調整するトーン
- 体裁: 導入(どんな管理者に役立つか)→実践手順→効果指標→注意点

出力は必ず次のJSON形式のみ、前後に説明を付けない:
{
  "title": "40文字以内のタイトル",
  "excerpt": "100文字以内の要約",
  "body_html": "<p>...</p> 形式の本文。h2/h3/ul/ol/blockquoteを適宜使用。1000〜1600文字。",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4"]
}"""


def pick_topic(articles: list[dict]) -> tuple[str, str]:
    """既存記事にないトピックを優先して選ぶ。"""
    used_slugs = {a.get("slug", "") for a in articles if a.get("category") == "ai-tips"}
    candidates = [t for t in TOPIC_POOL if not any(t[0] in s for s in used_slugs)]
    if not candidates:
        candidates = TOPIC_POOL
    return random.choice(candidates)


def generate_article(topic_key: str, topic_title: str) -> dict:
    user_prompt = f"""以下のテーマで記事を書いてください。

# テーマ
{topic_title}

# 対象読者
関西圏の特養施設長・グループホーム管理者・デイサービス責任者

# 要件
- 導入1段落で「この記事は○○に役立ちます」と明示
- 実践手順を3〜5ステップで具体的に書く
- 効果測定の指標例を2つ以上含める
- 注意点・限界も1セクション設ける
- 指定JSON形式で出力"""
    return call_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=3500)


def main() -> int:
    load_env()
    data = load_articles()
    articles = data["articles"]

    topic_key, topic_title = pick_topic(articles)
    print(f"選定トピック: {topic_title}")

    try:
        result = generate_article(topic_key, topic_title)
    except Exception as e:
        print(f"記事生成エラー: {e}", file=sys.stderr)
        return 1

    today = today_iso_date()
    slug_base = make_slug("ai", f"{topic_key}-{today}")
    slug = unique_slug(articles, slug_base)

    article = {
        "slug": slug,
        "title": result["title"],
        "category": "ai-tips",
        "prefecture": None,
        "excerpt": result["excerpt"],
        "body_html": result["body_html"],
        "tags": result.get("tags", []),
        "published": today,
        "source_url": None,
        "image": "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=800&q=80",
        "featured": False,
        "popular": False,
    }
    upsert_article(data, article)
    save_articles(data)
    print(f"[ok] {article['title']} を追加しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
