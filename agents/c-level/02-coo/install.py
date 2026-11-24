"""Install only mars-coo; map canonical lowercase definitions to native Hermes files."""
import json
import os
from pathlib import Path
import shutil
import sys

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[2]
os.environ['HERMES_HOME'] = str(ROOT)
sys.path.insert(0, str(ROOT/'hermes-agent'))
import yaml
from hermes_cli.profiles import create_profile, get_profile_dir

TOOLS = ['login', 'coo_branch_context', 'coo_delegation_plan',
         'coo_attendance_audit', 'coo_schedule_audit', 'coo_status_request_sla']


def install():
    if get_profile_dir('mars-coo').exists():
        raise SystemExit('mars-coo already exists; refusing to overwrite profile state.')
    target = create_profile('mars-coo', no_alias=True, no_skills=True,
        description='MARS COO coordinating attendance, room/schedule and status-request SLA specialists.')
    executable = 'Scripts/python.exe' if os.name == 'nt' else 'bin/python'
    config = {'mcp_servers': {'mars_lms': {
        'command': '${PYTHONPATH}/../mcp-servers/mars_lms/.venv/'+executable,
        'args': ['${PYTHONPATH}/../mcp-servers/mars_lms/server.py'],
        'env': {'MARS_API_URL': 'https://mars-backend-six.vercel.app'},
        'tools': {'include': TOOLS, 'prompts': False, 'resources': False}}},
        'platform_toolsets': {'cli': ['delegation', 'mars_lms']},
        'delegation': {'max_concurrent_children': 3, 'max_spawn_depth': 1, 'orchestrator_enabled': False}}
    # Copy model selection only; no provider secrets/auth stores or arbitrary config.
    root_config = yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8')) or {}
    model = root_config.get('model') or {}
    selected = {key: model[key] for key in ['provider', 'default', 'base_url'] if key in model}
    if selected:
        config['model'] = selected
    (target/'config.yaml').write_text(yaml.safe_dump(config, sort_keys=False), encoding='utf-8')
    # Hermes reads profile SOUL globally, but AGENTS only along the current CWD
    # chain. Embed the contract in SOUL so dashboard/root-CWD sessions also get it.
    identity = (SOURCE/'soul.md').read_text(encoding='utf-8')
    contract = (SOURCE/'agent.md').read_text(encoding='utf-8')
    contract = contract.replace('## ', '### ').replace('# MARS COO Agent', '## Agent Contract')
    (target/'SOUL.md').write_text(identity+'\n\n'+contract, encoding='utf-8')
    shutil.copyfile(SOURCE/'agent.md', target/'AGENTS.md')
    skill_dir = target/'skills/mars-coo-operations'
    skill_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SOURCE/'SKILL.md', skill_dir/'SKILL.md')
    print(json.dumps({'profile':'mars-coo', 'home':str(target), 'tools':TOOLS,
                      'credentials_copied':False, 'ceo_created':False}))


if __name__ == '__main__':
    install()
