import sys
import os
import pytest
from unittest.mock import MagicMock, patch

# Import from the installed package
from lofi_gate import logic

def test_determine_test_command_pytest():
    scripts = {}
    with patch("os.path.exists", return_value=True): # Simulates pyproject.toml existing
        cmd = logic.determine_test_command(scripts)
        assert "pytest" in cmd

def test_estimate_tokens():
    text = "1234"
    assert logic.estimate_tokens(text) == 1
    
    text = "12345678"
    assert logic.estimate_tokens(text) == 2
