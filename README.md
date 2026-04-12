# 関西介護ナビ

関西6府県（大阪・兵庫・京都・滋賀・奈良・和歌山）の介護施設管理者向け情報サイト。
補助金・助成金情報、AI・ICT活用tips、職員研修記事を週次で自動更新します。

## 公開URL

https://kaigo-navi-kansai.github.io/

## ディレクトリ構成

```
.
├── index.html                 トップページ
├── css/                       スタイルシート
├── js/                        クライアントJS（記事一覧の描画等）
├── images/                    画像アセット
├── pages/                     カテゴリ・府県別・お問い合わせ
│   └── prefectures/           府県別ページ（6府県）
├── articles/                  個別記事HTML（自動生成）
├── data/
│   ├── articles.json          記事メタデータ（一元管理）
│   └── subsidies.json         補助金スクレイピング結果
├── scripts/                   週次自動化スクリプト（Python）
│   ├── common.py              Claude API クライアント等
│   ├── scrape_subsidies.py    県庁HP巡回・テキスト抽出
│   ├── generate_subsidy_articles.py
│   ├── generate_ai_tips.py
│   ├── generate_training.py
│   └── build_article_pages.py 記事HTMLページ生成
└── .github/workflows/
    └── weekly-update.yml      毎週月曜9時(JST)実行
```

## ローカル開発

```bash
# 静的サイトのプレビュー（任意の静的サーバで可）
python3 -m http.server 8000
# → http://localhost:8000/
```

## 自動化スクリプトのセットアップ

```bash
cd scripts
pip install -r requirements.txt

# ローカル実行用に .env を作成
cp ../.env.example ../.env
# エディタで ANTHROPIC_API_KEY を設定

# 個別実行
python scrape_subsidies.py
python generate_subsidy_articles.py
python generate_ai_tips.py
python generate_training.py
python build_article_pages.py
```

## 週次自動投稿(ローカル launchd)

メインの週次自動投稿は、macOS の launchd で実行する `scripts/weekly_post.py` です。
Mac が起動している環境で、毎週月曜 09:00 JST に1記事を自動生成・公開します。

### 週替わりテーマ
| 週 | テーマ | カテゴリ |
|---|---|---|
| 第1週(1〜7日) | 補助金・助成金 | `subsidy` |
| 第2週(8〜14日) | AI・ICT活用 | `ai-tips` |
| 第3週(15〜21日) | 職員研修 | `training` |
| 第4週(22〜末日) | 介護経営tips | `management` |

### セットアップ

```bash
cd /Users/gotoushinya/claudecodecli/kaigo-navi-kansai
pip3 install --user -r scripts/requirements.txt
cp .env.example .env  # ANTHROPIC_API_KEY を設定
bash launchd/install_launchd.sh
```

インストール後は毎週月曜 09:00 に自動実行されます。

### 手動テスト実行
```bash
# ドライラン(git push なし、記事生成のみ)
python3 scripts/weekly_post.py --dry-run

# テーマを指定して即時生成
python3 scripts/weekly_post.py --theme subsidy

# launchd 経由で即時実行(本番相当)
launchctl start com.kaigo-navi.weekly

# ログ
tail -f ~/logs/kaigo-navi.log
```

### 停止 / アンインストール
```bash
bash launchd/uninstall_launchd.sh
```

### 処理概要
1. 週番号でテーマを選定
2. カイポケコラムから構造パターンを参照(タイトル・見出しのみ、本文は転載しない)
3. `subsidy` 週は府県庁HPも巡回(`scrape_subsidies.py` 呼び出し)
4. Claude API にカイポケ風コラムHTMLを生成させる
5. `articles/` に個別HTML書き出し、`articles.json` 先頭に追加
6. `git add/commit/push` で公開

## GitHub Actions の設定(バックアップ用)

メイン自動投稿はローカル launchd に一本化しました。GH Actions は `workflow_dispatch`(手動実行)でのバックアップ経路として残しています。



リポジトリの Settings → Secrets and variables → Actions で以下を登録:

| 名前 | 値 |
|------|-----|
| `ANTHROPIC_API_KEY` | `sk-ant-api03-...`（Anthropic のAPIキー） |

Settings → Pages で以下を設定:

- Source: **GitHub Actions** もしくは **Deploy from a branch (main / root)**

## コンテンツカテゴリ

- **補助金・助成金** (`subsidy`) - 府県別の最新補助金情報
- **AI・ICT活用** (`ai-tips`) - ChatGPT・AI・ICTツールの活用法
- **職員研修** (`training`) - 研修の設計と運用
- **管理者tips** (`management`) - 施設運営ノウハウ

## ライセンス・コンテンツポリシー

- 県庁サイトへのスクレイピングは robots.txt を尊重し、リクエスト間隔を1秒以上とします
- 取得したテキストは要約・二次著作物として記事化し、原文のコピーは行いません
- 記事内には情報源へのリンクを明記します
