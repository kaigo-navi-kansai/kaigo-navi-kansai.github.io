(function () {
  'use strict';

  const ROOT = (function () {
    const path = location.pathname;
    const depth = path.replace(/\/[^/]*$/, '').split('/').filter(Boolean).length;
    return depth === 0 ? '' : '../'.repeat(depth);
  })();

  const DATA_URL = ROOT + 'data/articles.json';

  const CAT_NAMES = {
    subsidy: '補助金・助成金',
    'ai-tips': 'AI・ICT活用',
    training: '職員研修',
    management: '管理者tips',
  };
  const CAT_CLASS = {
    subsidy: 'cat-subsidy',
    'ai-tips': 'cat-ai',
    training: 'cat-training',
    management: 'cat-management',
  };
  const PREF_NAMES = {
    osaka: '大阪府', hyogo: '兵庫県', kyoto: '京都府',
    shiga: '滋賀県', nara: '奈良県', wakayama: '和歌山県',
  };

  function formatDate(iso) {
    try {
      const d = new Date(iso);
      return d.toLocaleDateString('ja-JP', { year: 'numeric', month: 'long', day: 'numeric' });
    } catch (e) { return iso || ''; }
  }

  function escapeHtml(s) {
    return String(s || '').replace(/[&<>"']/g, (c) => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[c]));
  }

  function articleUrl(article) {
    return ROOT + 'articles/' + article.slug + '.html';
  }

  function renderCard(article) {
    const catClass = CAT_CLASS[article.category] || '';
    const catName = CAT_NAMES[article.category] || article.category;
    const thumb = article.image
      ? `<img src="${escapeHtml(article.image)}" alt="" loading="lazy">`
      : (article.title || '').charAt(0);
    return `
      <article class="article-card">
        <a href="${articleUrl(article)}" class="thumb">${thumb}</a>
        <div class="body">
          <span class="cat ${catClass}">${escapeHtml(catName)}</span>
          <h3><a href="${articleUrl(article)}">${escapeHtml(article.title)}</a></h3>
          <p class="excerpt">${escapeHtml(article.excerpt || '')}</p>
          <div class="meta">
            <time datetime="${escapeHtml(article.published)}">${formatDate(article.published)}</time>
            ${article.prefecture ? `<span>${escapeHtml(PREF_NAMES[article.prefecture] || '')}</span>` : ''}
          </div>
        </div>
      </article>
    `;
  }

  function renderList(container, items) {
    if (!items.length) {
      container.innerHTML = '<p class="empty">記事はまだありません。週次更新でまもなく掲載します。</p>';
      return;
    }
    container.innerHTML = items.map(renderCard).join('');
  }

  function renderPopular(container, items) {
    if (!items.length) { container.innerHTML = '<li class="empty">準備中</li>'; return; }
    container.innerHTML = items.map((a) =>
      `<li><a href="${articleUrl(a)}">${escapeHtml(a.title)}</a></li>`
    ).join('');
  }

  function filterArticles(articles, mode, limit) {
    const sorted = [...articles].sort((a, b) => (b.published || '').localeCompare(a.published || ''));
    let out = sorted;
    if (mode === 'latest') out = sorted;
    else if (mode === 'featured') out = sorted.filter((a) => a.featured);
    else if (mode === 'popular') out = sorted.filter((a) => a.popular);
    return limit ? out.slice(0, limit) : out;
  }

  function getQueryParams() {
    const params = {};
    location.search.slice(1).split('&').forEach((p) => {
      if (!p) return;
      const [k, v] = p.split('=').map(decodeURIComponent);
      params[k] = v;
    });
    return params;
  }

  function renderFiltered(container, articles) {
    const category = container.dataset.category;
    const prefecture = container.dataset.prefecture;
    const params = getQueryParams();
    let list = [...articles];
    if (category) list = list.filter((a) => a.category === category);
    if (prefecture) list = list.filter((a) => a.prefecture === prefecture);
    if (params.cat) list = list.filter((a) => a.category === params.cat);
    list.sort((a, b) => (b.published || '').localeCompare(a.published || ''));
    renderList(container, list);
    // Category filter UI
    const catSelect = document.getElementById('filter-category');
    if (catSelect) {
      catSelect.addEventListener('change', () => {
        const v = catSelect.value;
        const next = v ? articles.filter((a) => a.category === v) : articles;
        renderList(container, next);
      });
    }
  }

  async function load() {
    try {
      const res = await fetch(DATA_URL, { cache: 'no-cache' });
      if (!res.ok) throw new Error('fetch failed');
      const data = await res.json();
      const articles = Array.isArray(data.articles) ? data.articles : [];

      document.querySelectorAll('[data-load]').forEach((el) => {
        const mode = el.dataset.load;
        const limit = parseInt(el.dataset.limit || '0', 10) || 0;
        if (mode === 'popular') {
          renderPopular(el, filterArticles(articles, 'popular', limit));
        } else if (mode === 'latest' || mode === 'featured') {
          renderList(el, filterArticles(articles, mode, limit));
        } else if (mode === 'category' || mode === 'prefecture' || mode === 'all') {
          renderFiltered(el, articles);
        }
      });
    } catch (err) {
      console.error('articles load error', err);
      document.querySelectorAll('[data-load] .loading').forEach((el) => {
        el.textContent = '記事の読み込みに失敗しました。';
      });
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', load);
  } else {
    load();
  }
})();
