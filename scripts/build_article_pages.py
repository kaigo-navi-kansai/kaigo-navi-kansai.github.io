"""articles.json の各記事を /articles/{slug}.html として出力する静的ジェネレータ。"""
from __future__ import annotations

import html
import sys
from datetime import datetime

from common import ARTICLES_HTML_DIR, load_articles

CAT_NAMES = {
    "subsidy": "補助金・助成金",
    "ai-tips": "AI・ICT活用",
    "training": "職員研修",
    "management": "管理者tips",
}
CAT_CLASS = {
    "subsidy": "cat-subsidy",
    "ai-tips": "cat-ai",
    "training": "cat-training",
    "management": "cat-management",
}
CAT_PAGE = {
    "subsidy": "/pages/subsidy.html",
    "ai-tips": "/pages/ai-tips.html",
    "training": "/pages/training.html",
    "management": "/pages/management.html",
}
PREF_NAMES = {
    "osaka": "大阪府", "hyogo": "兵庫県", "kyoto": "京都府",
    "shiga": "滋賀県", "nara": "奈良県", "wakayama": "和歌山県",
}


def format_date(iso: str) -> str:
    try:
        d = datetime.fromisoformat(iso)
    except Exception:
        return iso
    return d.strftime("%Y年%m月%d日")


def render_article(article: dict) -> str:
    title = html.escape(article.get("title", ""))
    excerpt = html.escape(article.get("excerpt", ""))
    category = article.get("category", "")
    cat_name = CAT_NAMES.get(category, category)
    cat_class = CAT_CLASS.get(category, "")
    cat_link = CAT_PAGE.get(category, "/")
    prefecture = article.get("prefecture")
    pref_name = PREF_NAMES.get(prefecture, "")
    pref_link = f"/pages/prefectures/{prefecture}.html" if prefecture else None
    published_display = format_date(article.get("published", ""))
    body_html = article.get("body_html", "")
    source_url = article.get("source_url", "")
    image = article.get("image", "")
    tags = article.get("tags", []) or []
    tags_html = "".join(f'<span class="tag">#{html.escape(t)}</span>' for t in tags)

    breadcrumb_pref = (
        f' › <a href="{pref_link}">{pref_name}</a>' if pref_link and pref_name else ""
    )
    source_block = (
        f'<p class="form-note">情報源: <a href="{html.escape(source_url)}" target="_blank" rel="noopener">{html.escape(source_url)}</a></p>'
        if source_url
        else ""
    )
    hero_img = (
        f'<img src="{html.escape(image)}" alt="" style="width:100%;border-radius:8px;margin-bottom:24px;" loading="lazy">'
        if image
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 関西介護ナビ</title>
<meta name="description" content="{excerpt}">
<link rel="stylesheet" href="../css/style.css">
<link rel="stylesheet" href="../css/responsive.css">
</head>
<body>
<header class="site-header">
  <div class="container header-inner">
    <a href="/" class="logo"><span class="logo-mark">関</span><span class="logo-text">関西介護ナビ</span></a>
    <button class="nav-toggle" aria-label="メニュー" aria-expanded="false"><span></span><span></span><span></span></button>
    <nav class="site-nav"><ul>
      <li><a href="/pages/subsidy.html">補助金・助成金</a></li>
      <li><a href="/pages/ai-tips.html">AI・ICT活用</a></li>
      <li><a href="/pages/training.html">職員研修</a></li>
      <li><a href="/pages/management.html">管理者tips</a></li>
      <li class="has-dropdown"><a href="#">府県別 ▾</a><ul class="dropdown">
        <li><a href="/pages/prefectures/osaka.html">大阪府</a></li>
        <li><a href="/pages/prefectures/hyogo.html">兵庫県</a></li>
        <li><a href="/pages/prefectures/kyoto.html">京都府</a></li>
        <li><a href="/pages/prefectures/shiga.html">滋賀県</a></li>
        <li><a href="/pages/prefectures/nara.html">奈良県</a></li>
        <li><a href="/pages/prefectures/wakayama.html">和歌山県</a></li>
      </ul></li>
      <li><a href="/pages/contact.html">お問い合わせ</a></li>
    </ul></nav>
  </div>
</header>

<main class="container main-layout" style="padding-top:32px;">
  <div class="main-content">
    <nav class="breadcrumb">
      <a href="/">ホーム</a> › <a href="{cat_link}">{cat_name}</a>{breadcrumb_pref} › 記事
    </nav>
    <article class="article-body">
      <span class="cat {cat_class}" style="display:inline-block;background:#1e5ba8;color:#fff;padding:3px 10px;border-radius:12px;font-size:12px;margin-bottom:12px;">{cat_name}{(' / ' + pref_name) if pref_name else ''}</span>
      <h1>{title}</h1>
      <div class="article-meta">
        公開: {published_display}
      </div>
      {hero_img}
      {body_html}
      <div class="tag-list">{tags_html}</div>
      {source_block}

      <div class="ad-slot" data-slot="article-bottom" style="margin-top:32px;"><span class="ad-label">広告</span></div>
    </article>

    <div style="margin-top:24px;"><a href="{cat_link}" class="btn btn-outline">← {cat_name}一覧へ</a></div>
  </div>

  <aside class="sidebar">
    <div class="ad-slot ad-slot-sidebar" data-slot="sidebar-top"><span class="ad-label">広告</span></div>
    <div class="sidebar-box">
      <h3>関連カテゴリ</h3>
      <ul>
        <li><a href="/pages/subsidy.html">補助金・助成金</a></li>
        <li><a href="/pages/ai-tips.html">AI・ICT活用</a></li>
        <li><a href="/pages/training.html">職員研修</a></li>
        <li><a href="/pages/management.html">管理者tips</a></li>
      </ul>
    </div>
    <div class="ad-slot ad-slot-sidebar" data-slot="sidebar-bottom"><span class="ad-label">広告</span></div>
  </aside>
</main>

<footer class="site-footer">
  <div class="container footer-inner">
    <div class="footer-brand">
      <div class="logo"><span class="logo-mark">関</span><span class="logo-text">関西介護ナビ</span></div>
      <p>関西圏介護施設管理者向け情報サイト</p>
    </div>
    <div class="footer-nav"><h4>カテゴリ</h4><ul>
      <li><a href="/pages/subsidy.html">補助金・助成金</a></li>
      <li><a href="/pages/ai-tips.html">AI・ICT活用</a></li>
      <li><a href="/pages/training.html">職員研修</a></li>
      <li><a href="/pages/management.html">管理者tips</a></li>
    </ul></div>
    <div class="footer-nav"><h4>府県別</h4><ul>
      <li><a href="/pages/prefectures/osaka.html">大阪府</a></li>
      <li><a href="/pages/prefectures/hyogo.html">兵庫県</a></li>
      <li><a href="/pages/prefectures/kyoto.html">京都府</a></li>
      <li><a href="/pages/prefectures/shiga.html">滋賀県</a></li>
      <li><a href="/pages/prefectures/nara.html">奈良県</a></li>
      <li><a href="/pages/prefectures/wakayama.html">和歌山県</a></li>
    </ul></div>
    <div class="footer-nav"><h4>サイト情報</h4><ul>
      <li><a href="/pages/contact.html">お問い合わせ</a></li>
    </ul></div>
  </div>
  <div class="footer-copy"><div class="container"><small>© <span id="year"></span> 関西介護ナビ. All rights reserved.</small></div></div>
</footer>

<script src="../js/main.js"></script>
</body>
</html>
"""


def main() -> int:
    data = load_articles()
    articles = data.get("articles", [])
    ARTICLES_HTML_DIR.mkdir(parents=True, exist_ok=True)

    written = 0
    for a in articles:
        slug = a.get("slug")
        if not slug:
            continue
        out = ARTICLES_HTML_DIR / f"{slug}.html"
        out.write_text(render_article(a), encoding="utf-8")
        written += 1

    print(f"完了: {written} 件の記事ページを生成しました -> {ARTICLES_HTML_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
