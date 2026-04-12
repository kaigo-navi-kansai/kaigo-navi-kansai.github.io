"""subsidies.json の raw_text を Claude で要約・記事化し、articles.json に追記する。

府県ごとに1本、最新動向を示す記事を生成。既存記事(同slug)は上書き更新。
"""
from __future__ import annotations

import sys

from common import (
    SUBSIDIES_JSON, load_env, load_json,
    load_articles, save_articles, upsert_article,
    call_claude_json, today_iso_date, make_slug, unique_slug,
)

PREF_NAMES = {
    "osaka": "大阪府", "hyogo": "兵庫県", "kyoto": "京都府",
    "shiga": "滋賀県", "nara": "奈良県", "wakayama": "和歌山県",
}

SYSTEM_PROMPT = """あなたは介護業界に詳しい編集者です。行政ページから取得した原文を元に、
関西圏の介護施設管理者（特養施設長・グループホーム管理者・デイサービス責任者）向けに
読みやすい日本語の記事を執筆します。

厳守事項:
- 原文の著作権に配慮し、要約・再構成して自身の言葉で書く（コピーしない）
- 不確実な情報は「○○府の情報によれば」「詳細は公式ページ参照」と明記
- 金額・要件・締切は原文記載がある場合のみ書く。なければ触れない
- 冒頭で「どんな管理者に役立つか」を一文で示す
- 実務で使える視点（申請しやすさ・必要書類の目安・注意点）を含める
- 断定しすぎない。「○○の可能性があります」等のトーンを保つ

出力は必ず次のJSON形式のみ、前後に説明を付けない:
{
  "title": "40文字以内のタイトル",
  "excerpt": "100文字以内の要約",
  "body_html": "<p>...</p> 形式の本文。h2/h3/ul/ol/blockquoteを適宜使用。800〜1400文字。",
  "tags": ["タグ1", "タグ2", "タグ3"]
}"""


def build_user_prompt(pref_key: str, pref_name: str, url: str, raw_text: str) -> str:
    snippet = (raw_text or "").strip()[:8000]
    return f"""以下は {pref_name} の介護担当課 公式ページから取得した原文抜粋です。
この内容を元に、{pref_name}の介護施設管理者向けの記事を作成してください。

# 情報源
- 公式ページ: {url}
- 府県: {pref_name}

# 原文抜粋
{snippet}

# 指示
- 上記原文から、補助金・助成金・最新制度・通知など「管理者が知りたい情報」を抽出
- 原文が情報薄い場合は、一般的な{pref_name}の介護施策の傾向を踏まえた解説記事にする
- 記事末尾に「詳細は公式ページをご確認ください: {url}」の一文を含める
- 指定JSON形式で出力"""


def main() -> int:
    load_env()

    subs = load_json(SUBSIDIES_JSON)
    if not subs:
        print("subsidies.json が見つかりません", file=sys.stderr)
        return 1

    articles_data = load_articles()
    today = today_iso_date()
    created = 0

    for pref_key, pref_name in PREF_NAMES.items():
        src = subs.get("sources", {}).get(pref_key)
        if not src:
            print(f"[skip] {pref_key}: source 情報なし")
            continue

        url = src.get("url", "")
        raw_text = src.get("raw_text", "") or ""
        print(f"[{pref_key}] 記事生成中…")

        try:
            user_prompt = build_user_prompt(pref_key, pref_name, url, raw_text)
            result = call_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=3000)
        except Exception as e:
            print(f"  [error] {e}", file=sys.stderr)
            continue

        slug_base = make_slug("subsidy", f"{pref_key}-{today}")
        slug = unique_slug(articles_data["articles"], slug_base)

        article = {
            "slug": slug,
            "title": result["title"],
            "category": "subsidy",
            "prefecture": pref_key,
            "excerpt": result["excerpt"],
            "body_html": result["body_html"],
            "tags": result.get("tags", []),
            "published": today,
            "source_url": url,
            "image": f"https://images.unsplash.com/photo-1454165804606-c3d57bc86b40?auto=format&fit=crop&w=800&q=80",
            "featured": False,
            "popular": False,
        }
        upsert_article(articles_data, article)
        created += 1
        print(f"  [ok] {article['title']}")

    save_articles(articles_data)
    print(f"\n完了: {created} 件の補助金記事を更新しました")
    return 0


if __name__ == "__main__":
    sys.exit(main())
