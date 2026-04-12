#!/usr/bin/env bash
# 関西介護ナビ 週次自動投稿 launchd アンインストーラ
set -euo pipefail

LAUNCH_DIR="$HOME/Library/LaunchAgents"
LABEL="com.kaigo-navi.weekly"
PLIST_PATH="$LAUNCH_DIR/$LABEL.plist"

if [ -f "$PLIST_PATH" ]; then
  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  rm -f "$PLIST_PATH"
  echo "✅ 削除完了: $PLIST_PATH"
else
  echo "インストールされていません: $PLIST_PATH"
fi
echo "ログファイルは保持します($HOME/logs/)"
