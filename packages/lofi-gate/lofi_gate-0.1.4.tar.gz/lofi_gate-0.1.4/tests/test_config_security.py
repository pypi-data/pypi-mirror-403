
import os
import unittest
import toml
from unittest.mock import patch, MagicMock
# load_config is not exported in __init__ so we import from logic
from lofi_gate.logic import run_checks, load_config

class TestConfigurableSecurity(unittest.TestCase):
    def setUp(self):
        # Create a mock lofi.toml
        self.config_file = "lofi.toml"
        self.package_json = "package.json"
        
        # Create mock package.json to trigger npm check
        with open(self.package_json, "w") as f:
            f.write('{"scripts": {}}')

    def tearDown(self):
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        if os.path.exists(self.package_json):
            os.remove(self.package_json)

    @patch('lofi_gate.logic.run_command')
    def test_security_check_fail_on_error_true(self, mock_run):
        # Mock npm audit to FAIL
        mock_run.return_value = (1, "Vulnerabilities found", 0.5, "npm audit")
        
        # Config: Fail on error = True
        config = {
            "gate": {
                "security_check": True,
                "security_fail_on_error": True
            }
        }
        with open(self.config_file, "w") as f:
            toml.dump(config, f)
            
        # Run checks - should exit with 1
        result = run_checks(parallel=False)
        self.assertEqual(result, 1)

    @patch('lofi_gate.logic.run_command')
    def test_security_check_fail_on_error_false(self, mock_run):
        # Define side effect to handle different commands
        def command_side_effect(cmd, label=None):
            if "npm audit" in cmd:
                return 1, "Vulnerabilities found", 0.5, cmd
            return 0, "Success", 0.1, cmd
            
        mock_run.side_effect = command_side_effect
        
        # Config: Fail on error = False
        config = {
            "gate": {
                "security_check": True,
                "security_fail_on_error": False
            }
        }
        with open(self.config_file, "w") as f:
            toml.dump(config, f)
            
        # Run checks - should exit with 0 (pass)
        result = run_checks(parallel=False)
        self.assertEqual(result, 0)

        
    @patch('lofi_gate.logic.run_command')
    def test_security_check_disabled(self, mock_run):
        # Define side effect: Security fails (if called), others pass
        def command_side_effect(cmd, label=None):
            if "npm audit" in cmd:
                return 1, "Vulnerabilities found", 0.5, cmd
            return 0, "Success", 0.1, cmd
        mock_run.side_effect = command_side_effect

        # Config: Security check disabled
        config = {
            "gate": {
                "security_check": False
            }
        }
        with open(self.config_file, "w") as f:
            toml.dump(config, f)
            
        # Run checks - should exit with 0 (pass) because Security is skipped
        result = run_checks(parallel=False)
        self.assertEqual(result, 0)
        
        # Ensure npm audit was NOT called
        audit_called = False
        for call in mock_run.call_args_list:
            # call[0] are args, call[0][0] is the command string
            if call.args and "npm audit" in call.args[0]:
                audit_called = True
        self.assertFalse(audit_called, "npm audit should not be called when security_check is False")

if __name__ == '__main__':
    unittest.main()
