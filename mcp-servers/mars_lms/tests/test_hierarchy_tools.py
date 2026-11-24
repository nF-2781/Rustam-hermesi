import json
from pathlib import Path
import sys
import unittest
from unittest.mock import AsyncMock, patch
from types import SimpleNamespace
sys.path.append(str(Path(__file__).resolve().parents[1]))
from hierarchy_tools import delegation_plan
from mcp.server.fastmcp import FastMCP
import profile_tools
from coo_register import register_coo

class LoginCompatibilityTests(unittest.IsolatedAsyncioTestCase):
    async def test_alias_uses_same_client_and_preserves_explicit_role_with_saved_credentials(self):
        api=SimpleNamespace(login=AsyncMock(return_value={'success':True,'status':200}))
        server=FastMCP('fixture')
        with patch.object(profile_tools,'LMSClient',return_value=api),patch.object(profile_tools,'read_settings',return_value={'MARS_PHONE':'fixture','MARS_PASSWORD':'fixture','MARS_ROLE':'saved-role'}):
            profile_tools.register_profile_tools(server)
            register_coo(server)
            login=server._tool_manager.get_tool('login').fn
            alias=server._tool_manager.get_tool('coo_login').fn
            self.assertIs(login,alias)
            await alias(role='explicit-role')
            api.login.assert_awaited_once_with('fixture','fixture','explicit-role')
        self.assertEqual(len(await server.list_tools()),21)

class HierarchyTests(unittest.TestCase):
    def test_direct_department_context_contains_real_identity_and_contract(self):
        reply=delegation_plan('mars-ceo',['mars-coo','mars-cfo','mars-cpo'],'Audit the confirmed branch')
        self.assertTrue(reply['success'])
        tasks=reply['data']['delegate_task_arguments']['tasks']
        self.assertEqual(len(tasks),3)
        for task in tasks:
            self.assertEqual(set(task),{'goal','context'})
            packet=json.loads(task['context'])
            self.assertIn(packet['role_id'],packet['soul'])
            self.assertIn('Agent Contract',packet['agent'])
            self.assertIn('runtime',packet)
        self.assertFalse(reply['data']['dispatch_performed'])

    def test_cannot_skip_hierarchy_exceed_batch_or_pass_secrets(self):
        cases=[('mars-ceo',['attendance-sentinel'],'Audit',{}),
               ('mars-ceo',['mars-coo','mars-cfo','mars-cpo','mars-cmo'],'Audit',{}),
               ('mars-ceo',['mars-coo','mars-coo'],'Audit',{}),
               ('mars-cpo',['student-progress-auditor'],'Audit',{'password':'fixture'}),
               ('../../outside',['mars-coo'],'Audit',{})]
        for args in cases:self.assertFalse(delegation_plan(*args)['success'])

    def test_cpo_keeps_both_keep_existing_specialists(self):
        for parent,child in [('mars-cpo','student-progress-auditor'),('mars-cpo','reception-request-router')]:
            reply=delegation_plan(parent,[child],'Review supplied evidence')
            self.assertTrue(reply['success'])
            self.assertIn(child,reply['data']['delegate_task_arguments']['tasks'][0]['goal'])
