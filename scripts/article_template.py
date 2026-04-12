"""カイポケ風コラム記事 HTML のレンダラ。

Claude が生成する JSON を受け取り、サイトの共通 CSS(column.css) を使って
個別記事HTMLページを出力する。
"""
from __future__ import annotations

import html
from datetime import datetime
from pathlib import Path

CAT_NAMES = {
    "subsidy": "補助金・助成金",
    "ai-tips": "AI・ICT活用",
    "training": "職員研修",
    "management": "介護経営tips",
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


def _e(s: str) -> str:
    return html.escape(str(s or ""))


def _format_date(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso).strftime("%Y年%m月%d日")
    except Exception:
        return iso


def _toc_html(toc: list[dict]) -> str:
    if not toc:
        return ""
    items = "".join(
        f'<li><a href="#{_e(t.get("id",""))}">{_e(t.get("title",""))}</a></li>'
        for t in toc
    )
    return f'<nav class="toc" aria-label="目次"><div class="toc-title">目次</div><ol>{items}</ol></nav>'


def _tags_html(tags: list[str]) -> str:
    if not tags:
        return ""
    return '<div class="tag-row">' + "".join(
        f'<span class="tag">#{_e(t)}</span>' for t in tags
    ) + "</div>"


def _related_html(related: list[dict]) -> str:
    if not related:
        return ""
    cards = "".join(
        f'<a href="{_e(r.get("url","#"))}">{_e(r.get("title",""))}</a>'
        for r in related
    )
    return f'<section class="related-section"><h3>関連記事</h3><div class="related-list">{cards}</div></section>'


def render(article: dict) -> str:
    """article dict から HTML 文字列を生成。

    期待する article 構造:
      title, excerpt, lead(本文冒頭リード), body_html(整形済み本文),
      category, prefecture, published, reading_time_min,
      toc (list of {id, title}), tags (list), related (list of {title, url}),
      image (URL), source_url, cta_text (optional)
    """
    title = _e(article.get("title"))
    excerpt = _e(article.get("excerpt"))
    category = article.get("category", "")
    cat_name = CAT_NAMES.get(category, category)
    cat_link = CAT_PAGE.get(category, "/")
    prefecture = article.get("prefecture")
    pref_name = PREF_NAMES.get(prefecture, "") if prefecture else ""
    published = article.get("published", "")
    published_disp = _format_date(published)
    reading_min = article.get("reading_time_min") or 0
    lead = article.get("lead", "")
    body_html = article.get("body_html", "")
    image = article.get("image") or ""
    source_url = article.get("source_url") or ""
    cta_text = article.get("cta_text") or "補助金情報をもっと見る"

    reading_html = (
        f'<span class="reading-time">約{int(reading_min)}分で読めます</span>'
        if reading_min else ""
    )
    pref_disp = f' / {_e(pref_name)}' if pref_name else ""
    hero_img = (
        f'<img src="{_e(image)}" alt="" style="width:100%;border-radius:8px;margin:4px 0 24px;" loading="lazy">'
        if image else ""
    )
    source_block = (
        f'<p class="source-note">情報源: <a href="{_e(source_url)}" target="_blank" rel="noopener">{_e(source_url)}</a></p>'
        if source_url else ""
    )
    breadcrumb_pref = (
        f' › <a href="/pages/prefectures/{prefecture}.html">{_e(pref_name)}</a>'
        if prefecture and pref_name else ""
    )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | 関西介護ナビ</title>
<meta name="description" content="{excerpt}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{excerpt}">
<meta property="og:type" content="article">
<link rel="stylesheet" href="../css/style.css">
<link rel="stylesheet" href="../css/responsive.css">
<link rel="stylesheet" href="../css/column.css">
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

    <article class="column-wrap">
      <div class="column-meta">
        <span class="badge cat-{_e(category)}">{cat_name}{pref_disp}</span>
        <span>公開: {published_disp}</span>
        {reading_html}
      </div>

      <h1>{title}</h1>

      <div class="column-lead">{lead}</div>

      {_toc_html(article.get("toc") or [])}

      {hero_img}

      {body_html}

      {_tags_html(article.get("tags") or [])}

      {_related_html(article.get("related") or [])}

      {source_block}

      <div class="cta-box">
        <h3>関西介護ナビは毎週月曜に最新情報を更新</h3>
        <p>補助金・AI活用・職員研修・介護経営tipsを、関西6府県の介護施設管理者向けにお届けします。</p>
        <a href="{cat_link}">{_e(cta_text)} →</a>
      </div>

      <div class="ad-slot" data-slot="article-bottom" style="margin-top:24px;"><span class="ad-label">広告</span></div>
    </article>

    <div style="margin-top:24px;"><a href="{cat_link}" class="btn btn-outline">← {cat_name} 一覧へ戻る</a></div>
  </div>

  <aside class="sidebar">
    <div class="ad-slot ad-slot-sidebar" data-slot="sidebar-top"><span class="ad-label">広告</span></div>
    <div class="sidebar-box">
      <h3>関連カテゴリ</h3>
      <ul>
        <li><a href="/pages/subsidy.html">補助金・助成金</a></li>
        <li><a href="/pages/ai-tips.html">AI・ICT活用</a></li>
        <li><a href="/pages/training.html">職員研修</a></li>
        <li><a href="/pages/management.html">介護経営tips</a></li>
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
      <li><a href="/pages/management.html">介護経営tips</a></li>
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


def write_article(article: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'{article["slug"]}.html'
    path.write_text(render(article), encoding="utf-8")
    return path
