import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import Mock,patch
spec=importlib.util.spec_from_file_location('dashboard_lifecycle',Path(__file__).resolve().parents[2]/'skills/hermes_mars_dashboard/dashboard.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)

class OwnershipTests(unittest.TestCase):
    def record(self):return {'pid':123,'create_time':10,'port':9120,'executable':'fixture-python'}
    def process(self):
        return Mock(create_time=lambda:10,cwd=lambda:str(module.ROOT),cmdline=lambda:['fixture-python','-m','hermes_cli.main','dashboard','--port','9120'])
    def test_pid_reuse_wrong_cwd_or_wrong_command_cannot_terminate(self):
        for field,value in [('create_time',11),('cwd',str(module.ROOT.parent)),('cmdline',['unrelated-service'])]:
            process=self.process();setattr(process,field,lambda:value)
            with patch.object(module.psutil,'Process',return_value=process):self.assertFalse(module.stop_owned(self.record()))
            process.terminate.assert_not_called()
    def test_only_verified_process_is_terminated_without_port_scan_or_tree_kill(self):
        process=self.process()
        with patch.object(module.psutil,'Process',return_value=process):self.assertTrue(module.stop_owned(self.record()))
        process.terminate.assert_called_once();process.wait.assert_called_once_with(timeout=10)
        process.kill.assert_not_called();process.children.assert_not_called()
