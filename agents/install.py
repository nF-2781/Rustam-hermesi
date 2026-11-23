#!/usr/bin/env python3
"""Mars AI Agent Profiles Installer for Hermes-2 / Hermes Dashboard.

Installs or updates named profiles in `profiles/` from `agents/<role>/`
definitions, ensuring all C-level agents and sub-agents are ready in Hermes Dashboard.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AGENTS_DIR = ROOT / "agents"
PROFILES_DIR = ROOT / "profiles"

ROLES = {
    "ceo": "Rahbariyat boshlig'i: filial holatini yig'ib, C-level ga topshiriq beradi va yakuniy qaror tavsiya qiladi.",
    "coo": "Operatsion direktor: davomat, uy vazifasi, jadval, xona va tasdiqlar oqimi.",
    "cfo": "Moliya direktori: tushum, qarzdorlik, xarajat, qoldiq va to'lov dinamikasi.",
    "cto": "Texnika direktori: mars_lms MCP, backend integratsiyasi, dashboard, agentlar infratuzilmasi.",
    "cmo": "Marketing direktori: murojaatlar voronkasi, yangi o'quvchi konversiyasi, retention.",
    "cpo": "Mahsulot direktori: o'quvchi/ota-ona tajribasi, mahsulot sifati va takliflar oqimi.",
    "hr": "HR direktori: mentor yuklamasi va sifati, onboarding, kadr ehtiyoji.",
}

HR_SUB_AGENTS = {
    "hr-recruiter": ("01-hr-recruiter", "HR Rekruting sub-agenti: kadr ehtiyoji, vakansiyalar va nomzodlar saralash."),
    "hr-onboarding": ("02-hr-onboarding", "HR Onboarding sub-agenti: yangi mentor adaptatsiyasi va sinov muddati."),
    "hr-attendance": ("03-hr-attendance", "HR Davomat sub-agenti: mentorlar va xodimlar davomati va dars intizomi."),
    "hr-records": ("04-hr-records", "HR Hujjatlar sub-agenti: kadrlar hisobi, anketalar va eNPS tahlili."),
}

PYTHON_EXE = sys.executable.replace("\\", "/")
SERVER_PY = (ROOT / "mcp-servers" / "mars_lms" / "server.py").as_posix()

CONFIG_YAML_TEMPLATE = f"""mcp_servers:
  mars_lms:
    command: {PYTHON_EXE}
    args:
      - {SERVER_PY}
    env:
      PYTHONIOENCODING: utf-8
      PYTHONUNBUFFERED: '1'
    enabled: true
    timeout: 180
    connect_timeout: 60
platform_toolsets:
  cli:
  - skills
  - mars_lms
"""


def install_profile(name: str, desc: str, soul_content: str) -> None:
    target_dir = PROFILES_DIR / name
    target_dir.mkdir(parents=True, exist_ok=True)

    # profile.yaml
    profile_yaml = target_dir / "profile.yaml"
    profile_yaml.write_text(f'description: "{desc}"\ndescription_auto: false\n', encoding="utf-8")

    # config.yaml
    config_yaml = target_dir / "config.yaml"
    if not config_yaml.exists():
        config_yaml.write_text(CONFIG_YAML_TEMPLATE, encoding="utf-8")

    # SOUL.md
    soul_file = target_dir / "SOUL.md"
    soul_file.write_text(soul_content, encoding="utf-8")

    # .no-bundled-skills
    no_bundled = target_dir / ".no-bundled-skills"
    if not no_bundled.exists():
        no_bundled.write_text("", encoding="utf-8")

    # Link/copy specific skills if present
    if name == "mars-hr":
        hr_skill_src = ROOT / "skills" / "mars-hr-agent"
        if hr_skill_src.exists():
            import shutil
            hr_skill_dst = target_dir / "skills" / "mars-hr-agent"
            hr_skill_dst.parent.mkdir(parents=True, exist_ok=True)
            if not hr_skill_dst.exists():
                shutil.copytree(hr_skill_src, hr_skill_dst)

    size = len(soul_content.encode("utf-8"))
    print(f"  [+] Profil: {name:<20} SOUL: {size:>5}b  -> {target_dir.relative_to(ROOT)}")


def main() -> None:
    check_mode = "--check" in sys.argv
    print(f"=== Mars AI Agent Profiles Installer ({'CHECK' if check_mode else 'INSTALL'}) ===")
    print(f"Root: {ROOT}")
    print()

    # 1. C-Level Agents
    for role, desc in ROLES.items():
        name = f"mars-{role}"
        role_dir = AGENTS_DIR / role
        src_soul = role_dir / "soul.md"
        src_agents = role_dir / "agents.md"

        if not src_soul.exists() or not src_agents.exists():
            print(f"  [-] {name}: soul.md yoki agents.md topilmadi ({role_dir})")
            continue

        if check_mode:
            target_dir = PROFILES_DIR / name
            status = "tayyor" if (target_dir / "SOUL.md").exists() else "yo'q"
            print(f"  {role:<6} {name:<15} {status}")
            continue

        combined_soul = (
            f"<!-- {name}: soul.md + agents.md dan avtomatik yig'ildi (agents/install.py) -->\n\n"
            f"{src_soul.read_text(encoding='utf-8').strip()}\n\n"
            f"---\n\n"
            f"{src_agents.read_text(encoding='utf-8').strip()}\n"
        )
        install_profile(name, desc, combined_soul)

    # 2. HR Sub-Agents
    for sub_id, (sub_folder, desc) in HR_SUB_AGENTS.items():
        sub_dir = AGENTS_DIR / "hr" / "sub-agents" / sub_folder
        src_soul = sub_dir / "soul.md"
        src_agent = sub_dir / "agent.md"

        if not src_soul.exists() or not src_agent.exists():
            continue

        if check_mode:
            target_dir = PROFILES_DIR / sub_id
            status = "tayyor" if (target_dir / "SOUL.md").exists() else "yo'q"
            print(f"  sub    {sub_id:<15} {status}")
            continue

        combined_soul = (
            f"<!-- {sub_id}: soul.md + agent.md dan avtomatik yig'ildi -->\n\n"
            f"{src_soul.read_text(encoding='utf-8').strip()}\n\n"
            f"---\n\n"
            f"{src_agent.read_text(encoding='utf-8').strip()}\n"
        )
        install_profile(sub_id, desc, combined_soul)

    print()
    print("Muvaffaqiyatli yakunlandi.")


if __name__ == "__main__":
    main()
