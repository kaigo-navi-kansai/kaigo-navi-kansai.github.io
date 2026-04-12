#!/usr/bin/env bash
# 府県別ページを一括生成するスクリプト（ビルド時限定・本番不使用）
set -e
OUT_DIR="$(cd "$(dirname "$0")/.." && pwd)/pages/prefectures"
mkdir -p "$OUT_DIR"

gen() {
  local slug="$1" name="$2" gov_url="$3" gov_title="$4"
  cat > "$OUT_DIR/${slug}.html" <<HTML
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>${name}の介護施設向け情報 | 関西介護ナビ</title>
<meta name="description" content="${name}の介護施設管理者向け最新情報。補助金・助成金、管理者tips、AI活用、職員研修記事をまとめています。">
<link rel="stylesheet" href="../../css/style.css">
<link rel="stylesheet" href="../../css/responsive.css">
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

<section class="page-hero">
  <div class="container">
    <div class="breadcrumb"><a href="/">ホーム</a> › 府県別 › ${name}</div>
    <h1>${name}の介護施設向け情報</h1>
    <p>${name}の介護施設管理者向けの補助金・運営ノウハウを集約しています。</p>
  </div>
</section>

<main class="container main-layout">
  <div class="main-content">
    <div class="pref-info">
      <h3>${name} 行政リンク</h3>
      <dl>
        <dt>${gov_title}</dt>
        <dd><a href="${gov_url}" target="_blank" rel="noopener">${gov_url}</a></dd>
      </dl>
    </div>

    <section class="section">
      <div class="section-header"><h2>${name}の記事</h2></div>
      <div class="article-grid" data-load="prefecture" data-prefecture="${slug}">
        <p class="loading">読み込み中…</p>
      </div>
    </section>

    <div class="ad-slot" data-slot="content-bottom"><span class="ad-label">広告</span></div>
  </div>

  <aside class="sidebar">
    <div class="ad-slot ad-slot-sidebar" data-slot="sidebar-top"><span class="ad-label">広告</span></div>
    <div class="sidebar-box">
      <h3>他府県を見る</h3>
      <ul>
        <li><a href="osaka.html">大阪府</a></li>
        <li><a href="hyogo.html">兵庫県</a></li>
        <li><a href="kyoto.html">京都府</a></li>
        <li><a href="shiga.html">滋賀県</a></li>
        <li><a href="nara.html">奈良県</a></li>
        <li><a href="wakayama.html">和歌山県</a></li>
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

<script src="../../js/main.js"></script>
<script src="../../js/articles-loader.js"></script>
</body>
</html>
HTML
}

gen "osaka"    "大阪府"   "https://www.pref.osaka.lg.jp/kaigoshienka/"                           "大阪府 介護支援課"
gen "hyogo"    "兵庫県"   "https://web.pref.hyogo.lg.jp/kf17/index.html"                          "兵庫県 高齢政策課"
gen "kyoto"    "京都府"   "https://www.pref.kyoto.jp/kaigo/"                                      "京都府 介護・地域福祉課"
gen "shiga"    "滋賀県"   "https://www.pref.shiga.lg.jp/ippan/kenkouiryoufukushi/kaigo/"          "滋賀県 医療福祉推進課"
gen "nara"     "奈良県"   "https://www.pref.nara.jp/dd_aspx_menuid-10622.htm"                      "奈良県 介護保険課"
gen "wakayama" "和歌山県" "https://www.pref.wakayama.lg.jp/prefg/041300/"                          "和歌山県 長寿社会課"

echo "generated 6 prefecture pages"
