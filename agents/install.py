"""Sync project-local profiles; preserve model/auth/history and unrelated settings."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'agents/c-level'
os.environ['HERMES_HOME']=str(ROOT)
sys.path.insert(0,str(ROOT/'hermes-agent'))
import yaml
from hermes_cli.profiles import create_profile,get_profile_dir

def catalog():
    data=json.loads((SOURCE/'registry.json').read_text(encoding='utf-8'))
    roles={r['id']:dict(r) for r in data['roles']}
    roles['mars-ceo']['tools']=sorted({t for r in roles.values() for t in r['tools']}|{'c_level_delegation_plan'})
    for r in data['specialists']:
        if r.get('standalone'):roles[r['id']]=dict(r,children=[],mission='MARS scoped leaf specialist')
    return roles

def finance_module():
    spec=importlib.util.spec_from_file_location('finance_source',SOURCE/'03-cfo/install.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module

def render_soul(role):
    path=SOURCE/role['folder'];agent=path/'agents.md'
    if not agent.exists():agent=path/'agent.md'
    runtime=(SOURCE/'runtime.md').read_text(encoding='utf-8')
    result=(path/'soul.md').read_text(encoding='utf-8')+'\n\n'+agent.read_text(encoding='utf-8')+'\n\n'+runtime
    if role['id']=='mars-ceo':
        result+='\n\n## Department Routing\n\n'+json.dumps([{k:r[k] for k in ['id','title','contact','owner']} for r in catalog().values() if r['id'] in role['children']],ensure_ascii=False)
    if role['id']=='mars-cfo':
        result+='\n\n## Native Finance Delegation Arguments\n\n'+json.dumps({'tasks':finance_module().delegation_tasks('USER_CONFIRMED_MONTH')},ensure_ascii=False)
    if role['id'] in ['debt-collector','cashier-reporter','budget-planner']:
        result=finance_module().render_soul(role['id'])+'\n\n'+runtime
    if len(result)>18000:raise ValueError(f"SOUL budget exceeded: {role['id']} ({len(result)})")
    return result,agent

def sync(role,*,check=False,overwrite=False):
    target=get_profile_dir(role['id']);soul,agent=render_soul(role)
    if check:
        cfg=yaml.safe_load((target/'config.yaml').read_text(encoding='utf-8')) if (target/'config.yaml').exists() else {}
        actual=(cfg or {}).get('mcp_servers',{}).get('mars_lms',{}).get('tools',{}).get('include')
        valid=(target/'SOUL.md').exists() and (target/'SOUL.md').read_text(encoding='utf-8')==soul and actual==role['tools']
        return {'profile':role['id'],'installed':valid,'tools':len(role['tools'])}
    exists=target.exists()
    if exists and not overwrite:raise ValueError('Existing profile requires --sync: '+role['id'])
    if not exists:target=create_profile(role['id'],no_alias=True,no_skills=True,description=role['mission'])
    file=target/'config.yaml';config=yaml.safe_load(file.read_text(encoding='utf-8')) if file.exists() else {};config=config or {}
    if not exists:
        model=(yaml.safe_load((ROOT/'config.yaml').read_text(encoding='utf-8')) or {}).get('model') or {}
        config['model']={k:model[k] for k in ['provider','default','base_url'] if k in model}
    servers=config.setdefault('mcp_servers',{});servers.pop('mars-lms',None)
    executable='Scripts/python.exe' if os.name=='nt' else 'bin/python'
    servers['mars_lms']={'command':'${PYTHONPATH}/../mcp-servers/mars_lms/.venv/'+executable,
      'args':['${PYTHONPATH}/../mcp-servers/mars_lms/server.py'],
      'env':{'PYTHONIOENCODING':'utf-8','PYTHONUNBUFFERED':'1'},
      'tools':{'include':role['tools'],'prompts':False,'resources':False},'timeout':180,'connect_timeout':60}
    config['platform_toolsets']={'cli':(['delegation'] if role['children'] else [])+['mars_lms']}
    config['delegation']={'max_concurrent_children':3,'max_spawn_depth':2 if role['id']=='mars-ceo' else 1,'orchestrator_enabled':False}
    file.write_text(yaml.safe_dump(config,sort_keys=False,allow_unicode=True),encoding='utf-8')
    (target/'SOUL.md').write_text(soul,encoding='utf-8');(target/'AGENTS.md').write_bytes(agent.read_bytes())
    skill_source=SOURCE/role['folder']/'SKILL.md'
    skill_name=role.get('skill')
    if role['id']=='mars-cfo':
        skill_source=ROOT/'skills/mars-cfo-agent/SKILL.md';skill_name='mars-cfo-agent'
    elif role['id']=='mars-coo':
        skill_name='mars-coo-operations'
    if skill_source.exists() and skill_name:
        skill=target/'skills'/skill_name;skill.mkdir(parents=True,exist_ok=True)
        (skill/'SKILL.md').write_bytes(skill_source.read_bytes())
    return {'profile':role['id'],'installed':True,'tools':len(role['tools']),'soul_chars':len(soul),'credentials_copied':False}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile',nargs='?',default='all');parser.add_argument('--check',action='store_true');parser.add_argument('--sync',action='store_true')
    args=parser.parse_args();roles=catalog();name=args.profile
    if name not in roles and 'mars-'+name in roles:name='mars-'+name
    if name!='all' and name not in roles:parser.error('Unknown profile: '+name)
    selected=list(roles.values()) if name=='all' else [roles[name]]
    for role in selected:render_soul(role)
    if not args.check and not args.sync and any(get_profile_dir(r['id']).exists() for r in selected):parser.error('Existing targets require --sync; no changes made')
    results=[sync(role,check=args.check,overwrite=args.sync) for role in selected]
    print(json.dumps(results,ensure_ascii=True,indent=2))
    if args.check and not all(r['installed'] for r in results):raise SystemExit(1)
if __name__=='__main__':main()
