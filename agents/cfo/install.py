"""Install/check only the CFO and its three specialists using native Hermes profiles."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import sys

SOURCE = Path(__file__).resolve().parent
ROOT = SOURCE.parents[1]
PROFILE_TOOLS = {
    'mars-cfo': ['lms_login', 'lms_context', 'get_debts', 'debt_control_agent',
                 'daily_finance_report', 'get_finance_report', 'get_payments', 'list_students'],
    'debt-collector': ['lms_login', 'get_debts', 'debt_control_agent'],
    'cashier-reporter': ['lms_login', 'daily_finance_report', 'get_payments'],
    'budget-planner': ['lms_login', 'get_finance_report', 'daily_finance_report', 'lms_context'],
}
SPECIALISTS = {
    'debt-collector': ('01-debt-collector', 'debt_control_agent', {'month': 'USER_CONFIRMED_MONTH'}),
    'cashier-reporter': ('02-cashier-reporter', 'daily_finance_report', {'month': 'USER_CONFIRMED_MONTH', 'compare': True}),
    'budget-planner': ('03-budget-planner', 'get_finance_report', {'month': 'USER_CONFIRMED_MONTH'}),
}


def delegation_tasks(month: str):
    tasks = []
    for role, (folder, tool, arguments) in SPECIALISTS.items():
        path = SOURCE/'sub-agents'/folder
        args = {key: month if value == 'USER_CONFIRMED_MONTH' else value for key, value in arguments.items()}
        packet = {'role_id': role, 'reports_to': 'mars-cfo', 'month': month,
                  'soul': (path/'soul.md').read_text(encoding='utf-8'),
                  'agent': (path/'agent.md').read_text(encoding='utf-8'),
                  'assigned_tools': PROFILE_TOOLS[role], 'primary_tool': tool, 'arguments': args,
                  'boundary': 'Use the shared read-only finance MCP. lms_login() loads private credentials if needed. Check error fields, disclose period/coverage limits, use only student IDs in outputs, never send messages, change records or redelegate. daily_finance_report compares months; cash balance is not physically reconciled. Budget target is required for a projection.'}
        tasks.append({'goal': f'Act as {role}; perform the assigned branch finance audit and report evidence and limitations to mars-cfo.',
                      'context': json.dumps(packet, ensure_ascii=False)})
    return tasks


def render_soul(name):
    contract = (SOURCE/'runtime.md').read_text(encoding='utf-8')
    if name == 'mars-cfo':
        # Exclude static money examples from the runtime prompt; preserve them in
        # the imported source document, explicitly marked illustrative there.
        original = (SOURCE/'soul.md').read_text(encoding='utf-8')
        identity = original.split('---', 1)[0]
        # Preserve the source identity/tone, while keeping numeric scenarios and
        # unverified tool capability examples out of the loaded runtime prompt.
        if '## 2.' in original:
            identity += '\n\n## 2.'+original.split('## 2.',1)[1].split('## 3.',1)[0]
        packet = json.dumps({'tasks': delegation_tasks('USER_CONFIRMED_MONTH')}, ensure_ascii=False, indent=2)
        result = contract+'\n\n## CFO Identity\n\n'+identity+'\n\n## Native Delegation Arguments\n\n```json\n'+packet+'\n```\n'
    else:
        folder = SPECIALISTS[name][0]
        path = SOURCE/'sub-agents'/folder
        api_contract = contract.split('Ask for the reporting month',1)[1].split('## Native Three-Specialist Delegation',1)[0]
        output_contract = contract.split('## Output and Boundaries',1)[1]
        result = ('# Finance Specialist Runtime\n\n'
                  f'You are {name}, a leaf finance specialist reporting to mars-cfo (Islom). '
                  'Use only your assigned profile tools: '+', '.join(PROFILE_TOOLS[name])+'. '
                  'Do not delegate further. Check error/status_code before using details; login() is named lms_login for these finance tools and reads private .env credentials.\n\n'
                  +'## Actual API Evidence\n\nAsk for the reporting month'+api_contract
                  +'\n\n## Output and Boundaries\n'+output_contract
                  +'\n\n## Assigned Specialist\n\n'
                  +(path/'soul.md').read_text(encoding='utf-8')+'\n\n'
                  +(path/'agent.md').read_text(encoding='utf-8'))
    if len(result) > 18_000:
        raise ValueError('Generated identity exceeds the checked native context-file budget')
    return result


def install_profiles(check=False):
    os.environ['HERMES_HOME'] = str(ROOT)
    sys.path.insert(0, str(ROOT/'hermes-agent'))
    import yaml
    from hermes_cli.profiles import create_profile, get_profile_dir

    if check:
        results=[]
        for name in PROFILE_TOOLS:
            target=get_profile_dir(name)
            valid=target.is_dir() and (target/'config.yaml').exists() and (target/'SOUL.md').exists()
            results.append({'profile':name,'installed':valid})
        print(json.dumps(results))
        return results
    targets={name:get_profile_dir(name) for name in PROFILE_TOOLS}
    if any(path.exists() for path in targets.values()):
        raise SystemExit('A CFO target profile already exists; no profile changes made. Use --check to inspect.')
    # Validate all source material before creating any target.
    souls={name:render_soul(name) for name in PROFILE_TOOLS}
    skill_source=ROOT/'skills/mars-cfo-agent/SKILL.md'
    if not skill_source.is_file():
        raise SystemExit('CFO skill source is missing; no profile changes made.')
    root_config=yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8')) or {}
    model=root_config.get('model') or {}
    selected={key:model[key] for key in ['provider','default','base_url'] if key in model}
    executable='Scripts/python.exe' if os.name=='nt' else 'bin/python'
    for name,tools in PROFILE_TOOLS.items():
        target=create_profile(name,no_alias=True,no_skills=True,
            description='MARS CFO — Islom and finance specialists' if name=='mars-cfo' else f'MARS CFO finance specialist: {name}')
        config={'mcp_servers':{'mars_lms':{
            'command':'${PYTHONPATH}/../mcp-servers/mars_lms/.venv/'+executable,
            'args':['${PYTHONPATH}/../mcp-servers/mars_lms/server.py'],
            'tools':{'include':tools,'prompts':False,'resources':False},
            'env':{'PYTHONIOENCODING':'utf-8','PYTHONUNBUFFERED':'1'},
            'timeout':180,'connect_timeout':60}},
            'platform_toolsets':{'cli':['delegation','mars_lms'] if name=='mars-cfo' else ['mars_lms']}}
        if name=='mars-cfo':
            config['delegation']={'max_concurrent_children':3,'max_spawn_depth':1,'orchestrator_enabled':False}
        if selected:config['model']=dict(selected)
        (target/'config.yaml').write_text(yaml.safe_dump(config,sort_keys=False,allow_unicode=True),encoding='utf-8')
        (target/'SOUL.md').write_text(souls[name],encoding='utf-8')
        src=SOURCE/'agents.md' if name=='mars-cfo' else SOURCE/'sub-agents'/SPECIALISTS[name][0]/'agent.md'
        shutil.copyfile(src,target/'AGENTS.md')
        if name=='mars-cfo':
            skill=target/'skills/mars-cfo-agent';skill.mkdir(parents=True,exist_ok=True)
            shutil.copyfile(skill_source,skill/'SKILL.md')
        print(json.dumps({'profile':name,'tools':tools,'soul_chars':len(souls[name]),'credentials_copied':False}))
    return list(targets)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true')
    install_profiles(check=parser.parse_args().check)
