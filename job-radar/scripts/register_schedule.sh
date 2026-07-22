#!/usr/bin/env bash
# job-radar collector.py를 매일 09:00(KST)에 자동 실행하도록 등록한다.
# OS를 감지해서 macOS는 launchd(plist), Linux는 crontab을 사용한다.
#
# 시스템의 로컬 타임존이 KST(Asia/Seoul)가 아니어도 정확히 KST 09:00에 실행되도록
# python3로 "KST 09:00"에 해당하는 시스템 로컬 시(時)/분(分)을 계산해서 등록한다.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="$(command -v python3)"

# KST 09:00 -> 시스템 로컬 시간 기준 "분 시" 계산
read -r MINUTE HOUR <<< "$("$PYTHON_BIN" - <<'EOF'
import datetime
try:
    from zoneinfo import ZoneInfo
    seoul = ZoneInfo("Asia/Seoul")
except Exception:
    seoul = None

today = datetime.date.today()
if seoul:
    target_seoul = datetime.datetime.combine(today, datetime.time(9, 0), tzinfo=seoul)
    target_local = target_seoul.astimezone()
else:
    # zoneinfo 사용 불가 시 UTC+9 고정 오프셋으로 근사 계산
    target_seoul = datetime.datetime.combine(today, datetime.time(9, 0), tzinfo=datetime.timezone(datetime.timedelta(hours=9)))
    target_local = target_seoul.astimezone()
print(target_local.minute, target_local.hour)
EOF
)"

echo "[register_schedule] 프로젝트 경로: $PROJECT_DIR"
echo "[register_schedule] KST 09:00 == 이 시스템 로컬 시간 기준 ${HOUR}:$(printf '%02d' "$MINUTE")"

OS_NAME="$(uname -s)"

if [[ "$OS_NAME" == "Darwin" ]]; then
  PLIST_DIR="$HOME/Library/LaunchAgents"
  PLIST_PATH="$PLIST_DIR/com.jobradar.collector.plist"
  mkdir -p "$PLIST_DIR"

  cat > "$PLIST_PATH" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobradar.collector</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_BIN</string>
        <string>$PROJECT_DIR/collector.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>$HOUR</integer>
        <key>Minute</key>
        <integer>$MINUTE</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/launchd.out.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/launchd.err.log</string>
</dict>
</plist>
EOF

  echo "[register_schedule] launchd plist 작성: $PLIST_PATH"
  launchctl unload "$PLIST_PATH" 2>/dev/null || true
  launchctl load -w "$PLIST_PATH"
  echo "[register_schedule] 등록 완료. 확인: launchctl list | grep com.jobradar.collector"
  echo "[register_schedule] 해제하려면: launchctl unload $PLIST_PATH"

elif [[ "$OS_NAME" == "Linux" ]]; then
  if ! command -v crontab >/dev/null 2>&1; then
    echo "[register_schedule] crontab 명령을 찾을 수 없습니다. 설치 후 다시 실행하세요."
    echo "  Debian/Ubuntu: sudo apt-get install -y cron && sudo service cron start"
    exit 1
  fi

  CRON_MARKER="# job-radar-collector"
  CRON_LINE="$MINUTE $HOUR * * * cd $PROJECT_DIR && $PYTHON_BIN collector.py >> $PROJECT_DIR/logs/cron.log 2>&1 $CRON_MARKER"

  ( crontab -l 2>/dev/null | grep -v "$CRON_MARKER" || true ; echo "$CRON_LINE" ) | crontab -

  echo "[register_schedule] crontab 등록 완료:"
  crontab -l | grep "$CRON_MARKER"
  echo "[register_schedule] 확인: crontab -l"
  echo "[register_schedule] 해제하려면: crontab -l | grep -v '$CRON_MARKER' | crontab -"

else
  echo "[register_schedule] 지원하지 않는 OS: $OS_NAME (macOS 또는 Linux에서 실행하세요)"
  exit 1
fi
