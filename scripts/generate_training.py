"""職員研修tips記事を週1本、Claude に生成させて articles.json に追記する。"""
from __future__ import annotations

import random
import sys

from common import (
    load_env, load_articles, save_articles, upsert_article,
    call_claude_json, today_iso_date, make_slug, unique_slug,
)

TOPIC_POOL = [
    ("kensyu-naze-hitsuyou", "なぜ介護施設に職員研修が必要なのか〜離職防止と質向上の関係〜"),
    ("shinjin-kensyu", "新人介護職員研修の目的と効果的な進め方"),
    ("leader-kensyu", "管理者向けリーダーシップ研修がチームを変える理由"),
    ("harassment-kensyu", "ハラスメント防止研修を施設全体で取り組む重要性"),
    ("gijutsu-setsugu", "介護技術研修と接遇研修を組み合わせる効果"),
    ("ninchisho-kensyu", "認知症ケア研修で現場の対応力を上げる方法"),
    ("kyokotai-kensyu", "虐待防止・身体拘束適正化研修の運営ポイント"),
    ("kansen-bcp-kensyu", "感染症BCP研修を年1回形骸化させない運営のコツ"),
    ("medical-renkei-kensyu", "医療連携研修で看取りケアの質を高める"),
    ("ojt-kensyu", "OJT・Off-JTを組み合わせた研修計画の立て方"),
]

SYSTEM_PROMPT = """あなたは介護業界の人材育成に詳しい編集者です。
関西圏の介護施設管理者(特養施設長・グループホーム管理者・デイサービス責任者)向けに、
研修の設計・運営・効果測定を実務目線で書きます。

厳守事項:
- 抽象論に終わらせず、具体的な研修メニュー例・進め方を示す
- 「離職防止」「質向上」「法令遵守」のどの観点で価値があるかを明示
- 現場の時間制約に配慮し、短時間でも実行できる案を1つ以上出す
- 研修後の振り返り・評価の仕組みに触れる
- 体裁: 導入→研修の目的→効果的な進め方→評価と振り返り→よくある失敗

出力は必ず次のJSON形式のみ、前後に説明を付けない:
{
  "title": "40文字以内のタイトル",
  "excerpt": "100文字以内の要約",
  "body_html": "<p>...</p> 形式の本文。h2/h3/ul/ol/blockquoteを適宜使用。1000〜1600文字。",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4"]
}"""


def pick_topic(articles: list[dict]) -> tuple[str, str]:
    used_slugs = {a.get("slug", "") for a in articles if a.get("category") == "training"}
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
- 導入1段落で「どんな課題を抱えている管理者に役立つか」を示す
- 研修の目的を「離職防止」「質向上」「法令遵守」の観点で整理
- 効果的な進め方を3〜5ステップで具体化
- 評価指標の例を2つ以上(例: アンケート・インシデント件数・定着率など)
- よくある失敗パターンと対策を1セクション
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
    slug_base = make_slug("training", f"{topic_key}-{today}")
    slug = unique_slug(articles, slug_base)

    article = {
        "slug": slug,
        "title": result["title"],
        "category": "training",
        "prefecture": None,
        "excerpt": result["excerpt"],
        "body_html": result["body_html"],
        "tags": result.get("tags", []),
        "published": today,
        "source_url": None,
        "image": "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=800&q=80",
        "featured": False,
        "popular": False,
    }
    upsert_article(data, article)
    save_articles(data)
    print(f"[ok] {article['title']} を追加しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
