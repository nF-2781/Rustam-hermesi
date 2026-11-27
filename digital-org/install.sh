#!/usr/bin/env bash
# Digital Organization agentlarini Hermes profiliga aylantiradi.
#   soul.md + agents.md + workflow.md  ->  profiles/mars-ai-<slug>/SOUL.md
#
#   bash digital-org/install.sh            # 9 profilni yaratadi/yangilaydi
#   bash digital-org/install.sh --check    # faqat holatni ko'rsatadi
#
# Diqqat: bu `agents/install.sh` (7 kishilik jamoa, mars-<rol>) dan mustaqil.
set -euo pipefail

SELF_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SELF_DIR/.." && pwd)"
if git -C "$ROOT" rev-parse --show-toplevel >/dev/null 2>&1; then
  ROOT="$(git -C "$ROOT" rev-parse --show-toplevel)"
fi
export HERMES_HOME="$ROOT"
export PYTHONPATH="$ROOT/hermes-agent"

PY="$ROOT/hermes-agent/.venv/Scripts/python.exe"
[ -x "$PY" ] || PY="$ROOT/hermes-agent/.venv/bin/python"
[ -x "$PY" ] || { echo "✗ Python venv topilmadi: $ROOT/hermes-agent/.venv"; exit 1; }
HERMES=("$PY" -m hermes_cli.main)

DIRS=(00-orchestrator 01-ceo-strategist 02-academic-manager 03-branch-manager \
      04-finance-payroll 05-auditor-security 06-mentor-assistant 07-tutor-intern \
      08-student-parent)
declare -A SLUG=(
  [00-orchestrator]=orchestrator
  [01-ceo-strategist]=ceo
  [02-academic-manager]=academic
  [03-branch-manager]=branch
  [04-finance-payroll]=finance
  [05-auditor-security]=auditor
  [06-mentor-assistant]=mentor
  [07-tutor-intern]=tutor
  [08-student-parent]=student
)
declare -A DESC=(
  [00-orchestrator]="AI OS markazi: so'rovni yo'naltiradi, kontekst yig'adi, A2A zanjirni kuzatadi."
  [01-ceo-strategist]="Strategiya: KPI, filial foydasi, yangi yo'nalish qarorlari."
  [02-academic-manager]="O'quv sifati: talab, waitlist, mentor tanlash, metodika."
  [03-branch-manager]="Filial operatsiyasi: guruh, xona, transfer, zamena, akustika."
  [04-finance-payroll]="Moliya: tushum, xarajat, kassa, qarzdorlik, oylik loyihasi."
  [05-auditor-security]="Nazorat: audit log, davomat nizosi, RBAC/ABAC, observability."
  [06-mentor-assistant]="Mentor yordamchisi: dars, davomat, uy vazifasi, kod tekshiruvi."
  [07-tutor-intern]="Tutor bronlari va intern dasturi (topshiriq, davomat, Space)."
  [08-student-parent]="O'quvchi portali va ota-ona kabineti, xabarnomalar."
)

profile_dir() {
  local name="$1" base
  for base in "$ROOT/profiles" "$HOME/.hermes/profiles"; do
    [ -d "$base/$name" ] && { printf '%s\n' "$base/$name"; return 0; }
  done
  return 1
}

profile_exists() {
  "${HERMES[@]}" profile list 2>/dev/null | grep -qE "(^| )$1( |$)"
}

CHECK=0
[ "${1:-}" = "--check" ] && CHECK=1

printf '%-22s %-24s %-8s %s\n' "AGENT" "PROFIL" "SOUL.md" "HOLAT"
for dir in "${DIRS[@]}"; do
  slug="${SLUG[$dir]}"
  name="mars-ai-$slug"
  for f in soul.md agents.md workflow.md; do
    [ -f "$SELF_DIR/agents/$dir/$f" ] || { echo "✗ $dir: $f yo'q"; exit 1; }
  done

  if [ "$CHECK" = "1" ]; then
    pdir="$(profile_dir "$name")" || { printf '%-22s %-24s %-8s %s\n' "$dir" "$name" "-" "yo'q"; continue; }
    size="$(wc -c < "$pdir/SOUL.md" 2>/dev/null || echo 0)"
    printf '%-22s %-24s %-8s %s\n' "$dir" "$name" "${size}b" "tayyor"
    continue
  fi

  if ! profile_exists "$name"; then
    "${HERMES[@]}" profile create "$name" --clone --description "${DESC[$dir]}" >/dev/null
  fi
  pdir="$(profile_dir "$name")" || { echo "✗ $name profili yaratilmadi"; exit 1; }

  {
    echo "<!-- mars-ai-$slug: soul.md + agents.md + workflow.md dan yig'ildi (digital-org/install.sh) -->"
    cat "$SELF_DIR/agents/$dir/soul.md"
    echo
    echo "---"
    echo
    cat "$SELF_DIR/agents/$dir/agents.md"
    echo
    echo "---"
    echo
    cat "$SELF_DIR/agents/$dir/workflow.md"
  } > "$pdir/SOUL.md"

  "${HERMES[@]}" -p "$name" config set terminal.cwd "$ROOT" >/dev/null 2>&1 || true
  printf '%-22s %-24s %-8s %s\n' "$dir" "$name" "$(wc -c < "$pdir/SOUL.md")b" "o'rnatildi"
done

[ "$CHECK" = "1" ] && exit 0
echo
echo "Tekshirish:  hermes profile list | grep mars-ai-"
echo "Suhbat:      hermes -p mars-ai-finance chat"
