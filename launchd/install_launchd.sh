#!/usr/bin/env bash
# 関西介護ナビ 週次自動投稿 launchd インストーラ
# 毎週月曜 09:00 JST に weekly_post.py を実行する LaunchAgent を登録します。
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO="$(cd "$SCRIPT_DIR/.." && pwd)"
LAUNCH_DIR="$HOME/Library/LaunchAgents"
LOG_DIR="$HOME/logs"
LABEL="com.kaigo-navi.weekly"
PLIST_PATH="$LAUNCH_DIR/$LABEL.plist"
TEMPLATE="$SCRIPT_DIR/com.kaigo-navi.weekly.plist.template"

if [ ! -f "$TEMPLATE" ]; then
  echo "テンプレートが見つかりません: $TEMPLATE" >&2
  exit 1
fi

PYTHON_BIN="$(command -v python3 || true)"
if [ -z "$PYTHON_BIN" ]; then
  echo "python3 がPATHに見つかりません。インストール後に再実行してください。" >&2
  exit 1
fi

echo "==> 構成"
echo "  Repo       : $REPO"
echo "  Python     : $PYTHON_BIN"
echo "  LaunchAgent: $PLIST_PATH"
echo "  LogDir     : $LOG_DIR"

mkdir -p "$LAUNCH_DIR" "$LOG_DIR"
touch "$LOG_DIR/kaigo-navi.log" "$LOG_DIR/kaigo-navi.stdout.log" "$LOG_DIR/kaigo-navi.stderr.log"

echo "==> plist 生成"
sed \
  -e "s|@PYTHON@|$PYTHON_BIN|g" \
  -e "s|@REPO@|$REPO|g" \
  -e "s|@HOME@|$HOME|g" \
  -e "s|@LOG_DIR@|$LOG_DIR|g" \
  "$TEMPLATE" > "$PLIST_PATH"

echo "==> LaunchAgent 再登録"
launchctl unload "$PLIST_PATH" 2>/dev/null || true
launchctl load  "$PLIST_PATH"

echo "==> 登録内容の確認"
launchctl list | grep -i "kaigo-navi" || true
echo ""
echo "✅ インストール完了"
echo ""
echo "次回実行: 毎週月曜 09:00 JST"
echo "手動テスト(すぐに1回実行): launchctl start $LABEL"
echo "停止(次回以降実行しない): bash $SCRIPT_DIR/uninstall_launchd.sh"
echo "ログ: tail -f $LOG_DIR/kaigo-navi.log"
