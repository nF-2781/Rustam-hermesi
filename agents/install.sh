#!/usr/bin/env bash
# Mars C-level agentlarini Hermes profiliga aylantiradi.
#   soul.md + agents.md  ->  ~/.hermes/profiles/mars-<role>/SOUL.md
#
#   bash agents/install.sh            # 6 profilni yaratadi/yangilaydi
#   bash agents/install.sh --check    # faqat holatni ko'rsatadi
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

ROLES=(ceo coo cfo cto cmo cpo hr)
declare -A DESC=(
  [ceo]="Rahbariyat boshlig'i: filial holatini yig'ib, C-level ga topshiriq beradi va yakuniy qaror tavsiya qiladi."
  [coo]="Operatsion direktor: davomat, uy vazifasi, jadval, xona va tasdiqlar oqimi."
  [cfo]="Moliya direktori: tushum, qarzdorlik, xarajat, qoldiq va to'lov dinamikasi."
  [cto]="Texnika direktori: mars_lms MCP, backend integratsiyasi, dashboard, agentlar infratuzilmasi."
  [cmo]="Marketing direktori: murojaatlar voronkasi, yangi o'quvchi konversiyasi, retention."
  [cpo]="Mahsulot direktori: o'quvchi/ota-ona tajribasi, mahsulot sifati va takliflar oqimi."
  [hr]="HR direktori: mentor yuklamasi va sifati, onboarding, kadr ehtiyoji."
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

printf '%-10s %-12s %-8s %s\n' "AGENT" "PROFIL" "SOUL.md" "HOLAT"
for role in "${ROLES[@]}"; do
  name="mars-$role"
  src_soul="$SELF_DIR/$role/soul.md"
  src_agents="$SELF_DIR/$role/agents.md"
  [ -f "$src_soul" ] && [ -f "$src_agents" ] || { echo "✗ $role: soul.md/agents.md yo'q"; exit 1; }

  if [ "$CHECK" = "1" ]; then
    dir="$(profile_dir "$name")" || { printf '%-10s %-12s %-8s %s\n' "$role" "$name" "-" "yo'q"; continue; }
    size="$(wc -c < "$dir/SOUL.md" 2>/dev/null || echo 0)"
    printf '%-10s %-12s %-8s %s\n' "$role" "$name" "${size}b" "tayyor"
    continue
  fi

  if ! profile_exists "$name"; then
    "${HERMES[@]}" profile create "$name" --clone --description "${DESC[$role]}" >/dev/null
  fi
  dir="$(profile_dir "$name")" || { echo "✗ $name profili yaratilmadi"; exit 1; }

  {
    echo "<!-- mars-$role: soul.md + agents.md dan avtomatik yig'ildi (agents/install.sh) -->"
    cat "$src_soul"
    echo
    echo "---"
    echo
    cat "$src_agents"
  } > "$dir/SOUL.md"

  "${HERMES[@]}" -p "$name" config set terminal.cwd "$ROOT" >/dev/null 2>&1 || true
  printf '%-10s %-12s %-8s %s\n' "$role" "$name" "$(wc -c < "$dir/SOUL.md")b" "o'rnatildi"
done

[ "$CHECK" = "1" ] && exit 0
echo
echo "Tekshirish:  hermes profile list"
echo "Suhbat:      hermes -p mars-cfo chat"
