"""
Tests for CLI functionality.
"""

import pytest
from click.testing import CliRunner
from mnemonic_encrypt.cli import cli
from mnemonic_encrypt import MnemonicEncryptor


class TestCLI:
    """Test cases for CLI commands."""
    
    @pytest.fixture
    def runner(self):
        """Create a CLI runner for testing."""
        return CliRunner()
    
    @pytest.fixture
    def valid_mnemonic(self):
        """Valid test mnemonic."""
        return "abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon abandon about"
    
    @pytest.fixture
    def test_password(self):
        """Test password."""
        return "test-password-123"
    
    def test_cli_help(self, runner):
        """Test CLI help command."""
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "MnemonicEncrypt" in result.output
    
    def test_cli_version(self, runner):
        """Test CLI version command."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
    
    def test_encrypt_command_help(self, runner):
        """Test encrypt command help."""
        result = runner.invoke(cli, ["encrypt", "--help"])
        assert result.exit_code == 0
        assert "encrypt" in result.output.lower()
    
    def test_decrypt_command_help(self, runner):
        """Test decrypt command help."""
        result = runner.invoke(cli, ["decrypt", "--help"])
        assert result.exit_code == 0
        assert "decrypt" in result.output.lower()
    
    def test_generate_command_help(self, runner):
        """Test generate command help."""
        result = runner.invoke(cli, ["generate", "--help"])
        assert result.exit_code == 0
        assert "generate" in result.output.lower()
    
    def test_verify_command_help(self, runner):
        """Test verify command help."""
        result = runner.invoke(cli, ["verify", "--help"])
        assert result.exit_code == 0
        assert "verify" in result.output.lower()
    
    def test_encrypt_with_options(self, runner, valid_mnemonic, test_password):
        """Test encrypt command with command-line options."""
        result = runner.invoke(cli, [
            "encrypt",
            "--mnemonic", valid_mnemonic,
            "--password", test_password
        ])
        assert result.exit_code == 0
        assert "成功" in result.output or "successful" in result.output.lower()
        assert "ME$v1$" in result.output
    
    def test_encrypt_decrypt_cycle(self, runner, valid_mnemonic, test_password):
        """Test full encrypt-decrypt cycle via CLI."""
        # Encrypt
        encrypt_result = runner.invoke(cli, [
            "encrypt",
            "--mnemonic", valid_mnemonic,
            "--password", test_password
        ])
        assert encrypt_result.exit_code == 0
        
        # Extract ciphertext from output
        output_lines = encrypt_result.output.split("\n")
        ciphertext = None
        for line in output_lines:
            if line.strip().startswith("ME$v1$"):
                ciphertext = line.strip()
                break
        
        assert ciphertext is not None
        
        # Decrypt
        decrypt_result = runner.invoke(cli, [
            "decrypt",
            "--ciphertext", ciphertext,
            "--password", test_password
        ])
        assert decrypt_result.exit_code == 0
        assert "成功" in decrypt_result.output or "successful" in decrypt_result.output.lower()
    
    def test_decrypt_wrong_password(self, runner, valid_mnemonic, test_password):
        """Test decrypt with wrong password."""
        # First encrypt
        encrypt_result = runner.invoke(cli, [
            "encrypt",
            "--mnemonic", valid_mnemonic,
            "--password", test_password
        ])
        
        # Extract ciphertext
        output_lines = encrypt_result.output.split("\n")
        ciphertext = None
        for line in output_lines:
            if line.strip().startswith("ME$v1$"):
                ciphertext = line.strip()
                break
        
        # Try to decrypt with wrong password
        decrypt_result = runner.invoke(cli, [
            "decrypt",
            "--ciphertext", ciphertext,
            "--password", "wrong-password"
        ])
        assert decrypt_result.exit_code != 0
        assert "失败" in decrypt_result.output or "failed" in decrypt_result.output.lower()
    
    def test_generate_default(self, runner):
        """Test generate command with default settings."""
        result = runner.invoke(cli, ["generate"])
        assert result.exit_code == 0
        assert "12" in result.output or "words" in result.output.lower()
    
    def test_generate_24_words(self, runner):
        """Test generating 24-word mnemonic."""
        result = runner.invoke(cli, ["generate", "--strength", "256"])
        assert result.exit_code == 0
        assert "24" in result.output
    
    def test_generate_show_all(self, runner):
        """Test generate command with --show-all flag."""
        result = runner.invoke(cli, ["generate", "--show-all"])
        assert result.exit_code == 0
        assert "128" in result.output
        assert "256" in result.output
    
    def test_verify_valid_mnemonic(self, runner, valid_mnemonic):
        """Test verify command with valid mnemonic."""
        result = runner.invoke(cli, ["verify", valid_mnemonic])
        assert result.exit_code == 0
        assert "有效" in result.output or "valid" in result.output.lower()
    
    def test_verify_invalid_mnemonic(self, runner):
        """Test verify command with invalid mnemonic."""
        result = runner.invoke(cli, ["verify", "invalid mnemonic phrase"])
        assert result.exit_code != 0
        assert "无效" in result.output or "invalid" in result.output.lower()
