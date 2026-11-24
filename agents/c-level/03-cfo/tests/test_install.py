"""Installer isolation/credential regression tests with disposable profile roots."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[4]
sys.path.insert(0,str(ROOT/'hermes-agent'))
import yaml
from hermes_cli import profiles

spec=importlib.util.spec_from_file_location('finance_installer',ROOT/'agents/c-level/03-cfo/install.py')
installer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(installer)


class InstallerIsolationTests(unittest.TestCase):
    def test_only_finance_profiles_created_without_copying_secrets_or_touching_coo(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            (root/'config.yaml').write_text(yaml.safe_dump({'model':{'provider':'fixture','default':'fixture-model',
                'base_url':'http://fixture.local','api_key':'fixture-do-not-copy'}}),encoding='utf-8')
            (root/'.env').write_text('FIXTURE_SECRET=fixture-do-not-copy\n',encoding='utf-8')
            skill=root/'skills/mars-cfo-agent';skill.mkdir(parents=True)
            (skill/'SKILL.md').write_text('# Fixture Skill\n',encoding='utf-8')
            coo=root/'profiles/mars-coo';coo.mkdir(parents=True)
            (coo/'config.yaml').write_text('keep-coo',encoding='utf-8')
            created=[]
            def create(name,**kwargs):
                self.assertTrue(kwargs['no_alias'] and kwargs['no_skills'])
                path=root/'profiles'/name;path.mkdir(parents=True);created.append(name)
                return path
            with patch.object(installer,'ROOT',root), patch.object(profiles,'get_profile_dir',lambda name:root/'profiles'/name), patch.object(profiles,'create_profile',create):
                installer.install_profiles()
            self.assertEqual(set(created),set(installer.PROFILE_TOOLS))
            self.assertEqual((coo/'config.yaml').read_text(),'keep-coo')
            for name in created:
                path=root/'profiles'/name
                config=yaml.safe_load((path/'config.yaml').read_text(encoding='utf-8'))
                self.assertNotIn('api_key',config['model'])
                self.assertNotIn(str(root),config['mcp_servers']['mars_lms']['command'])
                self.assertEqual(config['mcp_servers']['mars_lms']['tools']['include'],installer.PROFILE_TOOLS[name])
                self.assertFalse((path/'.env').exists())
                self.assertFalse((path/'auth.json').exists())

    def test_existing_finance_profile_prevents_any_partial_install_or_overwrite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);target=root/'profiles/debt-collector';target.mkdir(parents=True)
            (target/'SOUL.md').write_text('keep-existing',encoding='utf-8')
            with patch.object(installer,'ROOT',root),patch.object(profiles,'get_profile_dir',lambda name:root/'profiles'/name),patch.object(profiles,'create_profile') as create:
                with self.assertRaises(SystemExit):installer.install_profiles()
                create.assert_not_called()
            self.assertEqual((target/'SOUL.md').read_text(),'keep-existing')
            self.assertEqual([p.name for p in (root/'profiles').iterdir()],['debt-collector'])


if __name__=='__main__':unittest.main()
