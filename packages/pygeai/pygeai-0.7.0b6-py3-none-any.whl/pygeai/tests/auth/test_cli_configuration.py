import unittest
import tempfile
import os
from io import StringIO
from unittest.mock import patch

from pygeai.cli.commands.configuration import configure
from pygeai.cli.commands import Option
from pygeai.core.common.config import reset_settings, get_settings


class TestCLIConfigurationWarnings(unittest.TestCase):
    """
    Tests for CLI configuration warnings and validation.
    
    python -m unittest pygeai.tests.auth.test_cli_configuration.TestCLIConfigurationWarnings
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_settings()
        self.temp_creds_file = tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False)
        self.temp_creds_file.close()

    def tearDown(self):
        """Clean up test fixtures"""
        if os.path.exists(self.temp_creds_file.name):
            os.unlink(self.temp_creds_file.name)
        reset_settings()

    @patch('sys.stdout', new_callable=StringIO)
    def test_warns_about_mixed_auth_in_same_profile(self, mock_stdout):
        """Test that CLI warns when both API key and OAuth are set for same profile"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("api_key", ["--key"], "Set API key", True), "test_api_key"),
            (Option("access_token", ["--access-token"], "Set access token", True), "test_oauth_token"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("WARNING", output)
        self.assertIn("2 different types of authentication", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_no_warning_for_single_auth_type(self, mock_stdout):
        """Test that no warning is issued when only one auth type is set"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("api_key", ["--key"], "Set API key", True), "test_api_key"),
            (Option("base_url", ["--url"], "Set base URL", True), "https://test.example.com"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertNotIn("WARNING", output)
        self.assertNotIn("2 different types of authentication", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_api_key_configuration_success_message(self, mock_stdout):
        """Test that API key configuration shows success message"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("api_key", ["--key"], "Set API key", True), "test_api_key"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("GEAI API KEY for alias 'test' saved successfully!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_base_url_configuration_success_message(self, mock_stdout):
        """Test that base URL configuration shows success message"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("base_url", ["--url"], "Set base URL", True), "https://test.example.com"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("GEAI API BASE URL for alias 'test' saved successfully!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_oauth_configuration_success_messages(self, mock_stdout):
        """Test that OAuth configuration shows success messages"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("access_token", ["--access-token"], "Set access token", True), "oauth_token_123"),
            (Option("project_id", ["--project-id"], "Set project ID", True), "project-456"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "oauth_profile")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("GEAI OAUTH2 ACCESS TOKEN for alias 'oauth_profile' saved successfully!", output)
        self.assertIn("GEAI PROJECT ID for alias 'oauth_profile' saved successfully!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_organization_id_configuration_success_message(self, mock_stdout):
        """Test that organization ID configuration shows success message"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("organization_id", ["--organization-id"], "Set org ID", True), "org-789"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("GEAI ORGANIZATION ID for alias 'test' saved successfully!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_eval_url_configuration_success_message(self, mock_stdout):
        """Test that eval URL configuration shows success message"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("eval_url", ["--eval-url"], "Set eval URL", True), "https://eval.test.example.com"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("GEAI API EVAL URL for alias 'test' saved successfully!", output)

    @patch('sys.stdout', new_callable=StringIO)
    def test_list_aliases_displays_configured_profiles(self, mock_stdout):
        """Test that --list flag displays all configured profiles"""
        reset_settings()
        settings = get_settings(credentials_file=self.temp_creds_file.name)
        
        settings.set_base_url("https://dev.example.com", alias="dev")
        settings.set_base_url("https://prod.example.com", alias="prod")
        
        option_list = [
            (Option("list", ["--list"], "List aliases", False), None)
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("Alias: dev -> Base URL: https://dev.example.com", output)
        self.assertIn("Alias: prod -> Base URL: https://prod.example.com", output)

    @patch('builtins.input', return_value='n')
    @patch('sys.stdout', new_callable=StringIO)
    def test_remove_alias_cancellation(self, mock_stdout, mock_input):
        """Test that alias removal can be cancelled"""
        reset_settings()
        settings = get_settings(credentials_file=self.temp_creds_file.name)
        settings.set_api_key("test_key", alias="test")
        settings.set_base_url("https://test.example.com", alias="test")
        
        option_list = [
            (Option("remove_alias", ["--remove-alias"], "Remove alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("kept in configuration file", output)
        self.assertIn("test", settings.list_aliases())

    @patch('builtins.input', return_value='y')
    @patch('sys.stdout', new_callable=StringIO)
    def test_remove_alias_confirmation(self, mock_stdout, mock_input):
        """Test that alias can be removed with confirmation"""
        reset_settings()
        settings = get_settings(credentials_file=self.temp_creds_file.name)
        settings.set_api_key("test_key", alias="test")
        settings.set_base_url("https://test.example.com", alias="test")
        
        option_list = [
            (Option("remove_alias", ["--remove-alias"], "Remove alias", True), "test")
        ]
        
        configure(option_list)
        
        output = mock_stdout.getvalue()
        
        self.assertIn("removed from configuration file", output)
        self.assertNotIn("test", settings.list_aliases())

    def test_configuration_persists_to_file(self):
        """Test that configuration is persisted to credentials file"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("api_key", ["--key"], "Set API key", True), "persisted_key"),
            (Option("base_url", ["--url"], "Set base URL", True), "https://persisted.example.com"),
            (Option("profile_alias", ["--profile-alias"], "Set alias", True), "persist")
        ]
        
        configure(option_list)
        
        reset_settings()
        new_settings = get_settings(credentials_file=self.temp_creds_file.name)
        
        self.assertEqual(new_settings.get_api_key(alias="persist"), "persisted_key")
        self.assertEqual(new_settings.get_base_url(alias="persist"), "https://persisted.example.com")

    def test_default_alias_used_when_not_specified(self):
        """Test that 'default' alias is used when profile_alias is not specified"""
        reset_settings()
        get_settings(credentials_file=self.temp_creds_file.name)
        
        option_list = [
            (Option("api_key", ["--key"], "Set API key", True), "default_key"),
        ]
        
        configure(option_list)
        
        settings = get_settings()
        
        self.assertEqual(settings.get_api_key(alias="default"), "default_key")


if __name__ == '__main__':
    unittest.main()
