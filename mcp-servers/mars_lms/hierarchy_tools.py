"""Prepare bounded native delegation contexts from canonical role sources."""
import json
from pathlib import Path
SOURCE=Path(__file__).resolve().parents[2]/'agents/c-level'

def delegation_plan(parent_id,child_ids,task,parameters=None):
    def error(message):return {'success':False,'status_code':400,'error':message}
    registry=json.loads((SOURCE/'registry.json').read_text(encoding='utf-8'))
    roles={r['id']:r for r in registry['roles']+registry['specialists']}
    parent=roles.get(parent_id)
    if not parent:return error('Unknown parent role')
    if not task or not task.strip():return error('A concrete task is required')
    if not child_ids or len(child_ids)>3 or len(set(child_ids))!=len(child_ids):return error('Select one to three distinct direct children')
    if any(child not in parent.get('children',[]) for child in child_ids):return error('Only registered direct children may be delegated')
    parameters=parameters or {};serialized=json.dumps(parameters,ensure_ascii=False)
    if len(serialized)>6000 or len(task)>4000:return error('Task/parameter context exceeds bounded input budget')
    if any(word in serialized.lower() for word in ['password','access_token','refresh_token','api_key','authorization','bearer ']):return error('Do not put credentials or tokens in delegated parameters')
    tasks=[]
    for child in child_ids:
        role=roles[child];path=(SOURCE/role['folder']).resolve()
        if not path.is_relative_to(SOURCE.resolve()):return error('Invalid role source path')
        agent=path/('agents.md' if child in {r['id'] for r in registry['roles']} else 'agent.md')
        packet={'role_id':child,'reports_to':parent_id,'task':task,'parameters':parameters,
          'soul':(path/'soul.md').read_text(encoding='utf-8'),'agent':agent.read_text(encoding='utf-8'),
          'runtime':(SOURCE/'runtime.md').read_text(encoding='utf-8'),'assigned_tools':role['tools'],
          'boundary':'Use assigned MCP capabilities. Tool access is inherited, not technically isolated per role. Return actual evidence, unknowns and human actions. Never send messages or disclose private contacts.'}
        tasks.append({'goal':f'Act as {child}; {task}','context':json.dumps(packet,ensure_ascii=False)})
    return {'success':True,'status_code':200,'data':{'parent_id':parent_id,'dispatch_performed':False,'delegate_task_arguments':{'tasks':tasks},'limitations':['Prepares contexts only; does not execute agents or establish role authorization.']}}

def register_hierarchy_tools(mcp,result):
    @mcp.tool()
    async def c_level_delegation_plan(parent_id:str,child_ids:list[str],task:str,parameters:dict|None=None):
        """Prepare actual canonical child identities/contracts for native delegate_task. Direct children only, max three. Does not dispatch or send messages. Do not include credentials in task or parameters."""
        return result(delegation_plan(parent_id,child_ids,task,parameters))
