import unittest
import tempfile
import os

from pygeai.core.common.config import SettingsManager, get_settings, reset_settings


class TestSettingsManager(unittest.TestCase):
    """
    Tests for SettingsManager configuration file operations.
    
    python -m unittest pygeai.tests.auth.test_config_manager.TestSettingsManager
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

    def test_creates_empty_credentials_file_if_not_exists(self):
        """Test that SettingsManager creates empty credentials file if it doesn't exist"""
        os.unlink(self.temp_creds_file.name)
        
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        self.assertTrue(os.path.exists(self.temp_creds_file.name))

    def test_set_and_get_api_key(self):
        """Test setting and getting API key for an alias"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_api_key("test_api_key", alias="test")
        api_key = settings.get_api_key(alias="test")
        
        self.assertEqual(api_key, "test_api_key")

    def test_set_and_get_base_url(self):
        """Test setting and getting base URL for an alias"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_base_url("https://test.example.com", alias="test")
        base_url = settings.get_base_url(alias="test")
        
        self.assertEqual(base_url, "https://test.example.com")

    def test_set_and_get_access_token(self):
        """Test setting and getting OAuth access token"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_access_token("oauth_token_123", alias="test")
        access_token = settings.get_access_token(alias="test")
        
        self.assertEqual(access_token, "oauth_token_123")

    def test_set_and_get_project_id(self):
        """Test setting and getting project ID"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_project_id("project-456", alias="test")
        project_id = settings.get_project_id(alias="test")
        
        self.assertEqual(project_id, "project-456")

    def test_set_and_get_organization_id(self):
        """Test setting and getting organization ID"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_organization_id("org-789", alias="test")
        org_id = settings.get_organization_id(alias="test")
        
        self.assertEqual(org_id, "org-789")

    def test_set_and_get_eval_url(self):
        """Test setting and getting eval URL"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_eval_url("https://eval.example.com", alias="test")
        eval_url = settings.get_eval_url(alias="test")
        
        self.assertEqual(eval_url, "https://eval.example.com")

    def test_multiple_aliases(self):
        """Test that multiple aliases can be managed independently"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_api_key("dev_key", alias="dev")
        settings.set_base_url("https://dev.example.com", alias="dev")
        
        settings.set_api_key("prod_key", alias="prod")
        settings.set_base_url("https://prod.example.com", alias="prod")
        
        self.assertEqual(settings.get_api_key(alias="dev"), "dev_key")
        self.assertEqual(settings.get_base_url(alias="dev"), "https://dev.example.com")
        
        self.assertEqual(settings.get_api_key(alias="prod"), "prod_key")
        self.assertEqual(settings.get_base_url(alias="prod"), "https://prod.example.com")

    def test_list_aliases(self):
        """Test listing all configured aliases"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_base_url("https://dev.example.com", alias="dev")
        settings.set_base_url("https://staging.example.com", alias="staging")
        settings.set_base_url("https://prod.example.com", alias="prod")
        
        aliases = settings.list_aliases()
        
        self.assertEqual(len(aliases), 3)
        self.assertIn("dev", aliases)
        self.assertIn("staging", aliases)
        self.assertIn("prod", aliases)
        self.assertEqual(aliases["dev"], "https://dev.example.com")

    def test_has_value_returns_true_for_existing(self):
        """Test has_value returns True for existing setting"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_api_key("test_key", alias="test")
        
        self.assertTrue(settings.has_value("GEAI_API_KEY", "test"))

    def test_has_value_returns_false_for_missing(self):
        """Test has_value returns False for missing setting"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_api_key("test_key", alias="test")
        
        self.assertFalse(settings.has_value("GEAI_API_BASE_URL", "test"))

    def test_has_value_returns_false_for_missing_alias(self):
        """Test has_value returns False for non-existent alias"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        self.assertFalse(settings.has_value("GEAI_API_KEY", "nonexistent"))

    def test_get_setting_value_returns_empty_for_missing_alias(self):
        """Test get_setting_value returns None and logs warning for missing alias"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        value = settings.get_setting_value("GEAI_API_KEY", "nonexistent")
        
        self.assertIsNone(value)

    def test_auto_adds_eval_url_when_missing(self):
        """Test that eval_url is auto-added when requested but missing"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_api_key("test_key", alias="test")
        settings.set_base_url("https://test.example.com", alias="test")
        
        eval_url = settings.get_setting_value("GEAI_API_EVAL_URL", "test")
        
        self.assertEqual(eval_url, "")
        self.assertTrue(settings.has_value("GEAI_API_EVAL_URL", "test"))

    def test_auto_adds_oauth_vars_when_access_token_present(self):
        """Test that OAuth vars are auto-added when access_token is present"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        settings.set_access_token("oauth_token_123", alias="test")
        
        project_id = settings.get_setting_value("GEAI_PROJECT_ID", "test")
        org_id = settings.get_setting_value("GEAI_ORGANIZATION_ID", "test")
        
        self.assertEqual(project_id, "")
        self.assertEqual(org_id, "")
        self.assertTrue(settings.has_value("GEAI_PROJECT_ID", "test"))
        self.assertTrue(settings.has_value("GEAI_ORGANIZATION_ID", "test"))


class TestSettingsManagerEnvironmentVariables(unittest.TestCase):
    """
    Tests for environment variable precedence in SettingsManager.
    
    python -m unittest pygeai.tests.auth.test_config_manager.TestSettingsManagerEnvironmentVariables
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_settings()
        self.temp_creds_file = tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False)
        self.temp_creds_file.close()
        
        self.original_env = {}
        for key in ['GEAI_API_KEY', 'GEAI_API_BASE_URL', 'GEAI_OAUTH_ACCESS_TOKEN', 
                    'GEAI_PROJECT_ID', 'GEAI_ORGANIZATION_ID', 'GEAI_API_EVAL_URL']:
            self.original_env[key] = os.environ.get(key)
            if key in os.environ:
                del os.environ[key]

    def tearDown(self):
        """Clean up test fixtures"""
        for key, value in self.original_env.items():
            if value is not None:
                os.environ[key] = value
            elif key in os.environ:
                del os.environ[key]
        
        if os.path.exists(self.temp_creds_file.name):
            os.unlink(self.temp_creds_file.name)
        reset_settings()

    def test_env_var_overrides_config_for_default_alias(self):
        """Test that environment variable overrides config file for default alias"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        settings.set_api_key("config_key", alias="default")
        
        os.environ['GEAI_API_KEY'] = "env_key"
        
        api_key = settings.get_api_key(alias="default")
        
        self.assertEqual(api_key, "env_key")

    def test_env_var_does_not_override_non_default_alias(self):
        """Test that environment variable doesn't override non-default alias"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        settings.set_api_key("config_key", alias="staging")
        
        os.environ['GEAI_API_KEY'] = "env_key"
        
        api_key = settings.get_api_key(alias="staging")
        
        self.assertEqual(api_key, "config_key")

    def test_env_var_used_when_no_config_for_default(self):
        """Test that environment variable is used when no config exists for default"""
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        os.environ['GEAI_API_KEY'] = "env_key"
        
        api_key = settings.get_api_key(alias="default")
        
        self.assertEqual(api_key, "env_key")

    def test_all_env_vars_work_for_default_alias(self):
        """Test that all supported environment variables work"""
        os.environ['GEAI_API_KEY'] = "env_api_key"
        os.environ['GEAI_API_BASE_URL'] = "https://env.example.com"
        os.environ['GEAI_OAUTH_ACCESS_TOKEN'] = "env_oauth_token"
        os.environ['GEAI_PROJECT_ID'] = "env_project_id"
        os.environ['GEAI_ORGANIZATION_ID'] = "env_org_id"
        os.environ['GEAI_API_EVAL_URL'] = "https://env.eval.example.com"
        
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        self.assertEqual(settings.get_api_key(), "env_api_key")
        self.assertEqual(settings.get_base_url(), "https://env.example.com")
        self.assertEqual(settings.get_access_token(), "env_oauth_token")
        self.assertEqual(settings.get_project_id(), "env_project_id")
        self.assertEqual(settings.get_organization_id(), "env_org_id")
        self.assertEqual(settings.get_eval_url(), "https://env.eval.example.com")

    def test_env_var_only_applies_to_default_alias_query(self):
        """Test that env vars only apply when querying default or no alias"""
        os.environ['GEAI_API_KEY'] = "env_key"
        
        settings = SettingsManager(credentials_file=self.temp_creds_file.name)
        
        default_key = settings.get_api_key()
        self.assertEqual(default_key, "env_key")
        
        explicit_default_key = settings.get_api_key(alias="default")
        self.assertEqual(explicit_default_key, "env_key")


class TestGetSettingsSingleton(unittest.TestCase):
    """
    Tests for get_settings singleton behavior.
    
    python -m unittest pygeai.tests.auth.test_config_manager.TestGetSettingsSingleton
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_settings()

    def tearDown(self):
        """Clean up test fixtures"""
        reset_settings()

    def test_get_settings_returns_singleton(self):
        """Test that get_settings returns the same instance"""
        settings1 = get_settings()
        settings2 = get_settings()
        
        self.assertIs(settings1, settings2)

    def test_reset_settings_clears_singleton(self):
        """Test that reset_settings clears the singleton"""
        settings1 = get_settings()
        reset_settings()
        settings2 = get_settings()
        
        self.assertIsNot(settings1, settings2)


if __name__ == '__main__':
    unittest.main()
