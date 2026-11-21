#!/usr/bin/env bash
# Mars loyihasi uchun Hermes dashboardni bitta buyruqda ko'taradi.
# Yo'llar repo ildizidan olinadi — jamoada repo qayerda klonlangan bo'lsa ham ishlaydi.
#
#   bash skills/hermes_mars_dashboard/run_mars_dashboard.sh [start|status|stop]
#
# Windows'da dashboard hermes-2.bat orqali ALOHIDA oynada ishga tushadi:
# terminal yopilsa ham jarayon o'lmaydi.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF_DIR/../.." && pwd)"
if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi

export HERMES_HOME="$ROOT"
export PYTHONPATH="$ROOT/hermes-agent"

PY="$ROOT/hermes-agent/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY="$ROOT/hermes-agent/.venv/bin/python"
BAT="$ROOT/hermes-2.bat"

LOG="$ROOT/logs/dashboard-mars.log"
PIDFILE="$ROOT/logs/.mars-dashboard.pid"
PORTFILE="$ROOT/logs/.mars-dashboard.port"
mkdir -p "$ROOT/logs"

case "$(uname -s)" in
  MINGW*|MSYS*|CYGWIN*) IS_WIN=1 ;;
  *) IS_WIN=0 ;;
esac

CANDIDATES="${CANDIDATES:-9120 9121 9122 9123 9124 9130}"

port_busy() { netstat -ano 2>/dev/null | grep -q ":$1 .*LISTENING"; }
http_ok()   { [ "$(curl -s -o /dev/null -w '%{http_code}' --max-time 2 "http://127.0.0.1:$1/")" = "200" ]; }
api_ok()    { curl -s --max-time 2 "http://127.0.0.1:$1/api/status" | grep -q '"version"'; }

port_pid() { netstat -ano 2>/dev/null | grep ":$1 .*LISTENING" | head -1 | awk '{print $NF}'; }

report() {
  echo "✓ Dashboard tayyor: http://127.0.0.1:$1"
  curl -s --max-time 3 "http://127.0.0.1:$1/api/status" | head -c 160; echo
  echo "  log: $LOG"
}

running_port() {
  for p in $CANDIDATES; do
    if http_ok "$p" && api_ok "$p"; then echo "$p"; return 0; fi
  done
  if [ -f "$PORTFILE" ]; then
    p="$(cat "$PORTFILE")"
    if http_ok "$p" && api_ok "$p"; then echo "$p"; return 0; fi
  fi
  return 1
}

case "${1:-start}" in
  status)
    if p="$(running_port)"; then report "$p"; else echo "✗ Mars dashboard ishlamayapti"; exit 1; fi
    ;;

  stop)
    port=""; [ -f "$PORTFILE" ] && port="$(cat "$PORTFILE")"
    killed=0
    # faqat shu portlardagi tinglovchilarni o'chiramiz (gateway'ning 9119 ga tegmaymiz).
    # Windows'da `kill -0` MSYS bo'lmagan PID'lar uchun ishonchsiz — to'g'ridan-to'g'ri taskkill.
    for p in ${port:-} $CANDIDATES; do
      [ -n "$p" ] || continue
      pid="$(port_pid "$p")"
      [ -n "$pid" ] || continue
      if [ "$IS_WIN" = "1" ]; then
        if taskkill //PID "$pid" //T //F >/dev/null 2>&1; then
          echo "✓ To'xtatildi (port $p, PID $pid)"; killed=1
        fi
      else
        if kill "$pid" 2>/dev/null; then echo "✓ To'xtatildi (port $p, PID $pid)"; killed=1; fi
      fi
    done
    rm -f "$PIDFILE" "$PORTFILE"
    [ "$killed" = "1" ] || echo "— Mars dashboard jarayoni topilmadi (allaqachon o'chgan)"
    ;;

  start)
    if p="$(running_port)"; then
      echo "— Allaqachon ishlayapti (qayta ko'tarilmadi)"; report "$p"; exit 0
    fi

    BUILD_FLAG=""
    [ -d "$ROOT/hermes-agent/hermes_cli/web_dist" ] && BUILD_FLAG="--skip-build"

    PORT=""
    for p in $CANDIDATES; do port_busy "$p" || { PORT="$p"; break; }; done
    if [ -z "$PORT" ]; then
      PORT=0
      echo "→ Barcha standart portlar band, OS bo'sh port beradi (--port 0)"
    fi

    if [ "$IS_WIN" = "1" ] && [ -f "$BAT" ]; then
      # hermes-2.bat: HERMES_HOME/PYTHONPATH ni %~dp0 dan oladi + alohida oyna
      WINROOT="$(cygpath -w "$ROOT" 2>/dev/null || echo "$ROOT")"
      WINBAT="$(cygpath -w "$BAT" 2>/dev/null || echo "$BAT")"
      WINLOG="$(cygpath -w "$LOG" 2>/dev/null || echo "$LOG")"
      WINLAUNCHER="$ROOT/logs/.mars-dashboard-launch.cmd"
      WINLAUNCHER_W="$(cygpath -w "$WINLAUNCHER" 2>/dev/null || echo "$WINLAUNCHER")"
      {
        echo "@echo off"
        echo "cd /d \"$WINROOT\""
        echo "call \"$WINBAT\" dashboard --port $PORT --no-open $BUILD_FLAG > \"$WINLOG\" 2>&1"
      } > "$WINLAUNCHER"
      # stdio uziladi: alohida oyna chaqiruvchi terminalni bloklamaydi
      cmd //c start "Hermes Mars Dashboard" //min cmd //c "$WINLAUNCHER_W" </dev/null >/dev/null 2>&1
      echo "→ hermes-2.bat alohida oynada ishga tushdi (port $PORT); tayyor bo'lishini kutaman..."
    elif [ -x "$PY" ]; then
      nohup "$PY" -m hermes_cli.main dashboard --port "$PORT" --no-open $BUILD_FLAG >"$LOG" 2>&1 &
      echo $! > "$PIDFILE"
      echo "→ Ko'tarilmoqda... PID $(cat "$PIDFILE"), port $PORT"
    else
      echo "✗ Python venv ham, hermes-2.bat ham topilmadi ($ROOT)"; exit 1
    fi

    for _ in $(seq 1 120); do
      sleep 1
      if [ "$PORT" = "0" ]; then
        PORT="$(grep -o 'HERMES_DASHBOARD_READY port=[0-9]*' "$LOG" 2>/dev/null | tail -1 | cut -d= -f2 || true)"
        [ -n "${PORT:-}" ] || continue
      fi
      if http_ok "$PORT" && api_ok "$PORT"; then
        echo "$PORT" > "$PORTFILE"
        pid="$(port_pid "$PORT")"; [ -n "$pid" ] && echo "$pid" > "$PIDFILE"
        report "$PORT"; exit 0
      fi
      if grep -q "BACKEND_PORT_IN_USE" "$LOG" 2>/dev/null; then
        echo "✗ Port band bo'lib qoldi:"; tail -5 "$LOG"; exit 1
      fi
    done
    echo "✗ 120s ichida javob bermadi. Log:"; tail -20 "$LOG"; exit 1
    ;;

  *)
    echo "Ishlatish: $0 [start|status|stop]"; exit 2
    ;;
esac
