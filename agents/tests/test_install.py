"""Managed sync must preserve an existing model, private auth and history."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec=importlib.util.spec_from_file_location('managed_installer',Path(__file__).resolve().parents[1]/'install.py')
installer=importlib.util.module_from_spec(spec);spec.loader.exec_module(installer)
import yaml

class SyncTests(unittest.TestCase):
    def test_existing_profile_preserves_model_auth_and_unrelated_config(self):
        with tempfile.TemporaryDirectory() as folder:
            target=Path(folder)
            old={'model':{'provider':'fixture','default':'selected-model'},'custom':'keep',
                 'mcp_servers':{'other':{'command':'fixture'}}}
            (target/'config.yaml').write_text(yaml.safe_dump(old),encoding='utf-8')
            (target/'auth.json').write_text('fixture-private-auth')
            (target/'history.txt').write_text('fixture-history')
            with patch.object(installer,'get_profile_dir',lambda _:target):
                installer.sync(installer.catalog()['mars-coo'],overwrite=True)
            actual=yaml.safe_load((target/'config.yaml').read_text(encoding='utf-8'))
            self.assertEqual(actual['model'],old['model'])
            self.assertEqual(actual['custom'],'keep')
            self.assertEqual(actual['mcp_servers']['other'],old['mcp_servers']['other'])
            self.assertEqual((target/'auth.json').read_text(),'fixture-private-auth')
            self.assertEqual((target/'history.txt').read_text(),'fixture-history')

    def test_seven_roles_and_existing_specialists_have_bounded_runtime_prompts(self):
        roles=installer.catalog()
        self.assertEqual(len(roles),12)
        expected={'mars-ceo':'Rustam','mars-coo':'Kamollidin','mars-cfo':'Islom',
                  'mars-cto':'Saidabzal','mars-cmo':'Muhammadrizo','mars-cpo':'Muhammadsolih','mars-hr':'Muhammadali'}
        actual={name:role['owner'] for name,role in roles.items() if 'owner' in role}
        self.assertEqual(actual,expected)
        self.assertEqual(set(roles['mars-ceo']['children']),set(expected)-{'mars-ceo'})
        self.assertEqual(set(roles['mars-cpo']['children']),{'student-progress-auditor','reception-request-router'})
        for role in roles.values():
            soul,agent=installer.render_soul(role)
            self.assertTrue(agent.is_file())
            self.assertLess(len(soul),18001)
            self.assertIn('MCP',soul)
