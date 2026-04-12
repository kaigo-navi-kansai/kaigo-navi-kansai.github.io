"""毎週月曜9時に launchd から呼ばれるメインエントリ。

- 実行日の週(1-4)に応じてテーマを決定
  week1: 補助金 / week2: AI活用 / week3: 職員研修 / week4: 介護経営
- カイポケコラムの構造ヒントを取得(本文は転載しない)
- テーマごとの情報源収集(補助金は府県庁スクレイピング)
- Claude に Kaipoke 風 JSON を生成させる
- articles.json 先頭に追加し、個別HTMLを articles/ へ出力
- git add/commit/push

CLI:
  python weekly_post.py                      # 本番(自動判定)
  python weekly_post.py --dry-run            # git push しない
  python weekly_post.py --theme subsidy      # テーマ強制
  python weekly_post.py --no-push            # 生成のみ
"""
from __future__ import annotations

import argparse
import hashlib
import logging
import os
import random
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path

from common import (
    ARTICLES_HTML_DIR, JST, load_articles, save_articles, upsert_article,
    load_env, call_claude_json, today_iso_date, make_slug, unique_slug,
    SUBSIDIES_JSON, load_json,
)
from article_template import write_article, CAT_NAMES
import kaipoke_style

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = Path(os.environ.get("KAIGO_NAVI_LOG", Path.home() / "logs" / "kaigo-navi.log"))

THEME_BY_WEEK = {1: "subsidy", 2: "ai-tips", 3: "training", 4: "management"}

AI_TOPICS = [
    "ChatGPTで介護記録の申し送りを要約する実践手順",
    "AI音声入力で夜勤記録の記入時間を減らす方法",
    "介護ロボット導入時に現場抵抗を下げる3ステップ",
    "AIで家族向け連絡文のテンプレートを自動生成する",
    "ICT導入による夜間巡視の省力化と安全性両立",
    "介護記録AIの個人情報取り扱いリスクと対策",
    "AIによる勤怠・シフト最適化の導入効果を測る方法",
    "タブレット一つで変わる事務作業の棚卸し",
]
TRAINING_TOPICS = [
    "新人介護職員の定着率を上げる3ヶ月研修ロードマップ",
    "ユニットリーダー育成のためのリーダーシップ研修",
    "認知症ケア実践研修を施設全体で運用する",
    "ハラスメント防止研修をロールプレイで定着させる",
    "感染症BCP研修を形骸化させない年間サイクル",
    "看取りケア研修で家族対応の質を上げる",
    "接遇研修と介護技術研修を連動させる設計",
    "外国人介護職員の教育とチーム統合のコツ",
]
MANAGEMENT_TOPICS = [
    "特養の入居待機者対応を広報から見直す",
    "稼働率とレセプト管理の勘所",
    "人事評価制度を介護現場にフィットさせる方法",
    "運営指導(実地指導)で指摘されやすい10項目",
    "事故・ヒヤリハットを構造的に減らす仕組みづくり",
    "医療連携を深化させる在宅支援診療所との関係構築",
    "管理者のメンタルヘルスと休む技術",
    "中規模法人のガバナンス強化ロードマップ",
]

SYSTEM_PROMPT = """あなたは介護業界の編集者です。関西の介護施設管理者(特養施設長・グループホーム管理者・デイサービス責任者)向けに、
「介護ポータルサイトのコラム記事」風のスタイルで Web 記事を執筆します。

厳守事項:
- 他サイトの文章をコピーしない。構造・文体トーンのみ参考にし、内容は自身の言葉で書く
- 個人情報・実在施設名は書かない
- 数字・期限・手順など具体性を重視
- 断定しすぎず、自施設に合わせて調整するトーン
- 関西6府県の事情に触れられる箇所では触れる(大阪・兵庫・京都・滋賀・奈良・和歌山)

HTML記法の厳守:
- 見出しは <h2 class="h2" id="secN"> ... </h2> と <h3 class="h3"> ... </h3> のみ使用
- 本文 <p>、リスト <ul>/<ol>/<li> を基本構成に使う
- ポイント強調ボックスは <div class="point-box"><div class="point-title">タイトル</div> ... </div>
- 注意喚起は <div class="callout"><div class="callout-title">タイトル</div> 本文 </div> (情報系は callout-info クラスを追加)
- 強調枠は <div class="highlight-box"><div class="highlight-lead">計算式や結論</div><div class="highlight-sub">補足</div></div>
- ステップは <ol class="flow"><li><h4>見出し</h4><p>本文</p></li>...</ol>
- 比較は <table class="comp-table"><thead>...</thead><tbody>...</tbody></table>

出力は次のJSON形式のみ、前後に説明を付けない:
{
  "title": "40〜60文字のタイトル",
  "excerpt": "検索結果用 100〜140字の要約",
  "lead": "<p>冒頭リード2〜3文(強調して書き出す)</p>",
  "reading_time_min": 5〜10の整数,
  "toc": [{"id":"sec1","title":"1. ..."}, {"id":"sec2","title":"2. ..."}, ...],
  "body_html": "<h2 class=\\"h2\\" id=\\"sec1\\">1. ...</h2>...<h2 class=\\"h2\\" id=\\"sec2\\">2. ...</h2>...",
  "tags": ["タグ1", "タグ2", "タグ3", "タグ4"]
}"""


def setup_logging() -> None:
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(LOG_FILE, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )


def current_week_theme() -> str:
    day = datetime.now(JST).day
    week = min(4, (day - 1) // 7 + 1)
    return THEME_BY_WEEK[week]


def pick_unused(pool: list[str], used_titles: set[str]) -> str:
    unused = [t for t in pool if t not in used_titles]
    return random.choice(unused or pool)


def build_subsidy_user_prompt(subs: dict, style_hint: str) -> str:
    snippets = []
    for pref_key, pref_name in [
        ("osaka", "大阪府"), ("hyogo", "兵庫県"), ("kyoto", "京都府"),
        ("shiga", "滋賀県"), ("nara", "奈良県"), ("wakayama", "和歌山県"),
        ("mhlw", "厚生労働省"),
    ]:
        src = subs.get("sources", {}).get(pref_key, {})
        text = (src.get("raw_text") or "")[:2500]
        url = src.get("url", "")
        if text:
            snippets.append(f"# {pref_name} ({url})\n{text}")
    sources_block = "\n\n".join(snippets) if snippets else "(今週は有効な取得結果なし)"
    return f"""関西6府県の介護施設管理者向けに「補助金・助成金」テーマの記事を書いてください。
以下の府県庁・厚労省ページから取得した原文抜粋を参考情報として使い、最新動向や管理者が活用できる視点をまとめてください。
※ 原文の文言はコピーせず、必ず要約・構造化して書くこと。

# 参考情報
{sources_block}

# 編集スタイルの参考
{style_hint}

# 指示
- タイトルは関西または特定府県の最新動向を感じさせるものに
- toc は 5〜7項目
- body_html には必ず point-box / callout / comp-table のいずれかを含める
- 指定JSON形式で出力"""


def build_generic_user_prompt(theme: str, topic_title: str, style_hint: str) -> str:
    theme_label = CAT_NAMES.get(theme, theme)
    return f"""関西圏の介護施設管理者向けに「{theme_label}」カテゴリの記事を書いてください。

# 今回のテーマ
{topic_title}

# 編集スタイルの参考
{style_hint}

# 指示
- 導入リードで「どんな管理者に役立つ記事か」を示す
- toc は 5〜6項目
- 実践手順は flow(STEP形式)で表現
- 効果を測る数値指標を1セクション設ける
- body_html には point-box / callout / flow のいずれかを2つ以上含める
- 指定JSON形式で出力"""


def gather_subsidy_context() -> dict:
    """補助金テーマのため府県庁HPを最新取得。scrape_subsidies.py を呼び出す。"""
    logging.info("府県庁ページをスクレイピング中…")
    try:
        subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "scrape_subsidies.py")],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        logging.warning(f"スクレイプ失敗(続行): {e}")
    return load_json(SUBSIDIES_JSON) or {}


def auto_related(articles: list[dict], category: str, exclude_slug: str, n: int = 3) -> list[dict]:
    same = [a for a in articles if a.get("category") == category and a.get("slug") != exclude_slug]
    same.sort(key=lambda a: a.get("published", ""), reverse=True)
    return [
        {"title": a["title"], "url": f'/articles/{a["slug"]}.html'}
        for a in same[:n]
    ]


def theme_image(theme: str) -> str:
    imgs = {
        "subsidy":    "https://images.unsplash.com/photo-1554224155-6726b3ff858f?auto=format&fit=crop&w=800&q=80",
        "ai-tips":    "https://images.unsplash.com/photo-1677442136019-21780ecad995?auto=format&fit=crop&w=800&q=80",
        "training":   "https://images.unsplash.com/photo-1524178232363-1fb2b075b655?auto=format&fit=crop&w=800&q=80",
        "management": "https://images.unsplash.com/photo-1552664730-d307ca884978?auto=format&fit=crop&w=800&q=80",
    }
    return imgs.get(theme, "")


def git_commit_and_push(slug: str, theme: str) -> None:
    logging.info("git add/commit/push 開始")
    subprocess.run(["git", "add", "articles/", "data/articles.json", "data/subsidies.json"], cwd=ROOT, check=True)
    status = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=ROOT)
    if status.returncode == 0:
        logging.info("変更なし。コミットをスキップ")
        return
    msg = f"post: weekly_post {theme} {slug} ({today_iso_date()})"
    subprocess.run(["git", "commit", "-m", msg], cwd=ROOT, check=True)
    subprocess.run(["git", "push"], cwd=ROOT, check=True)
    logging.info("push 完了")


def run(args: argparse.Namespace) -> int:
    setup_logging()
    logging.info("=== weekly_post 開始 ===")
    load_env()

    theme = args.theme or current_week_theme()
    logging.info(f"テーマ: {theme}")

    style_hint = kaipoke_style.build_style_hints()
    logging.info(f"スタイルヒント取得 ({len(style_hint)} chars)")

    articles_data = load_articles()
    articles = articles_data["articles"]

    if theme == "subsidy":
        subs = gather_subsidy_context()
        user_prompt = build_subsidy_user_prompt(subs, style_hint)
        topic_title = f"subsidy-weekly-{today_iso_date()}"
    else:
        if theme == "ai-tips":
            pool = AI_TOPICS
        elif theme == "training":
            pool = TRAINING_TOPICS
        else:
            pool = MANAGEMENT_TOPICS
        used = {a.get("title", "") for a in articles if a.get("category") == theme}
        topic_title = pick_unused(pool, used)
        logging.info(f"選定トピック: {topic_title}")
        user_prompt = build_generic_user_prompt(theme, topic_title, style_hint)

    logging.info("Claude 呼び出し中…")
    try:
        result = call_claude_json(SYSTEM_PROMPT, user_prompt, max_tokens=8000, temperature=0.5)
    except Exception as e:
        logging.error(f"Claude 呼び出し失敗: {e}")
        return 1

    # slug: {category}-YYYY-MM-DD-{6桁hash} 形式(タイトル由来で衝突回避)
    title_for_hash = (result.get("title") or topic_title).encode("utf-8")
    hash_suffix = hashlib.sha1(title_for_hash).hexdigest()[:6]
    slug = unique_slug(articles, f"{theme}-{today_iso_date()}-{hash_suffix}")

    article = {
        "slug": slug,
        "title": result["title"],
        "category": theme,
        "prefecture": None,
        "excerpt": result["excerpt"],
        "lead": result.get("lead", ""),
        "body_html": result.get("body_html", ""),
        "reading_time_min": int(result.get("reading_time_min") or 7),
        "toc": result.get("toc") or [],
        "tags": result.get("tags") or [],
        "published": today_iso_date(),
        "source_url": None,
        "image": theme_image(theme),
        "featured": True,
        "popular": False,
        "custom_html": True,
    }
    article["related"] = auto_related(articles, theme, slug, n=3)

    write_article(article, ARTICLES_HTML_DIR)
    logging.info(f"HTML 出力: articles/{slug}.html")

    upsert_article(articles_data, article)
    # 新着先頭に出すため、末尾に追加された最新を先頭へ移動
    lst = articles_data["articles"]
    moved = [a for a in lst if a["slug"] == slug]
    rest = [a for a in lst if a["slug"] != slug]
    articles_data["articles"] = moved + rest
    save_articles(articles_data)
    logging.info(f"articles.json 更新: {slug}")

    if args.dry_run or args.no_push:
        logging.info("push スキップ(dry-run または --no-push)")
    else:
        try:
            git_commit_and_push(slug, theme)
        except subprocess.CalledProcessError as e:
            logging.error(f"git 失敗: {e}")
            return 2

    logging.info("=== weekly_post 正常終了 ===")
    return 0


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="関西介護ナビ 週次自動投稿")
    p.add_argument("--theme", choices=["subsidy", "ai-tips", "training", "management"],
                   help="週テーマ自動判定を上書き")
    p.add_argument("--dry-run", action="store_true", help="生成のみで git push しない")
    p.add_argument("--no-push", action="store_true", help="dry-run の別名")
    return p.parse_args()


def main() -> int:
    try:
        return run(parse_args())
    except Exception:
        logging.error("予期せぬ例外\n" + traceback.format_exc())
        return 9


if __name__ == "__main__":
    sys.exit(main())
