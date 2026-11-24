"""Install the two project-local Hermes profiles without copying credentials."""
import argparse
import json
import os
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
os.environ['HERMES_HOME'] = str(ROOT)
sys.path.insert(0, str(ROOT / 'hermes-agent'))
import yaml
from hermes_cli.profiles import create_profile, get_profile_dir

AGENTS = {
    'student-progress-auditor': ('mars-student-progress-auditor',
        ['login', 'students', 'student_progress', 'attendance', 'homework', 'curriculum'],
        'Audit authorized student progress and propose mentor support plans.'),
    'reception-request-router': ('mars-reception-request-router',
        ['login', 'incoming_requests', 'reception_triage'],
        'Classify reception requests and draft routing/replies; general backend inbox is unavailable.'),
}

def install(name):
    skill, tools, description = AGENTS[name]
    target = get_profile_dir(name)
    if target.exists():
        raise SystemExit(f'Profile already exists; refusing to overwrite: {name}')
    target = create_profile(name, no_alias=True, no_skills=True, description=description)
    config_path = target / 'config.yaml'
    config = yaml.safe_load(config_path.read_text(encoding='utf-8')) if config_path.exists() else {}
    config = config or {}
    # PYTHONPATH is a global Hermes deployment variable even in profile multiplexing.
    # Root launchers set it to this checkout's hermes-agent directory.
    executable = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
    config['mcp_servers'] = {'mars-lms': {
        'command': '${PYTHONPATH}/../mcp-servers/mars_lms/.venv/' + executable,
        'args': ['${PYTHONPATH}/../mcp-servers/mars_lms/server.py'],
        'env': {'MARS_API_URL': 'https://mars-backend-six.vercel.app'},
        'tools': {'include': tools, 'prompts': False, 'resources': False},
    }}
    config['platform_toolsets'] = {'cli': ['skills', 'mars-lms']}
    config_path.write_text(yaml.safe_dump(config, sort_keys=False, allow_unicode=True), encoding='utf-8')
    template = ROOT / 'agents' / name
    shutil.copyfile(template / 'SOUL.md', target / 'SOUL.md')
    skill_dir = target / 'skills' / skill
    skill_dir.mkdir(parents=True)
    shutil.copyfile(template / 'SKILL.md', skill_dir / 'SKILL.md')
    print(json.dumps({'profile': name, 'home': str(target), 'skill': skill, 'tools': tools,
                      'credentials_copied': False}))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', choices=[*AGENTS, 'all'], default='all', nargs='?')
    args = parser.parse_args()
    names = list(AGENTS) if args.profile == 'all' else [args.profile]
    if any(get_profile_dir(name).exists() for name in names):
        raise SystemExit('A target profile already exists; no profile changes made.')
    for name in names:
        install(name)
