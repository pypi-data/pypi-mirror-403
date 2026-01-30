import os
import sys
import tempfile
import unittest
from pathlib import Path


class TestCLIConfigureWithAlias(unittest.TestCase):
    """
    Test configure command with --alias flag
    """

    def setUp(self):
        """Reset settings and session before each test"""
        from pygeai.core.common.config import reset_settings
        from pygeai.core.base.session import reset_session
        self._original_sys_argv = sys.argv.copy()
        reset_settings()
        reset_session()

    def tearDown(self):
        """Reset settings and session after each test"""
        from pygeai.core.common.config import reset_settings
        from pygeai.core.base.session import reset_session
        sys.argv = self._original_sys_argv
        reset_settings()
        reset_session()

    def test_configure_with_default_alias(self):
        """Test configure command with default alias"""
        from pygeai.cli.geai import CLIDriver

        sys.argv = ['geai', 'configure']
        driver = CLIDriver()

        self.assertEqual(driver.session.alias, 'default')

    def test_configure_with_custom_alias(self):
        """Test configure command with custom alias"""
        from pygeai.cli.geai import CLIDriver

        # Create credentials file with custom alias
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            custom_creds = f.name
            f.write('[prod]\n')
            f.write('GEAI_API_KEY = prod_key_123\n')
            f.write('GEAI_API_BASE_URL = https://prod.example.com\n')

        try:
            sys.argv = ['geai', '--credentials', custom_creds, '--alias', 'prod', 'configure']
            driver = CLIDriver()

            self.assertEqual(driver.session.alias, 'prod')
            self.assertEqual(driver.session.api_key, 'prod_key_123')
            self.assertEqual(driver.session.base_url, 'https://prod.example.com')
        finally:
            os.unlink(custom_creds)


class TestCLICommandsUseCorrectProfile(unittest.TestCase):
    """
    Test that CLI commands use the session with the correct alias/profile.
    
    These tests verify that when commands are invoked with --alias flag,
    they use the correct profile from the credentials file.
    
    NOTE: These tests pass when run individually but fail when run as part of the full suite
    due to persistent singleton state from other tests. Run individually with:
      python -m unittest pygeai.tests.cli.test_credentials_flag.TestCLICommandsUseCorrectProfile.test_driver_session_uses_correct_alias_dev
    """

    def setUp(self):
        """Set up test fixtures"""
        import sys
        from pygeai.core.common.config import reset_settings
        from pygeai.core.base.session import reset_session
        
        # Save original sys.argv
        self._original_sys_argv = sys.argv.copy()
        
        # Reset singletons
        reset_settings()
        reset_session()
        
        # Create test credentials file with multiple profiles
        self.creds_file = tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False)
        self.creds_file.write('[default]\n')
        self.creds_file.write('GEAI_API_KEY = default_key\n')
        self.creds_file.write('GEAI_API_BASE_URL = https://default.example.com\n')
        self.creds_file.write('\n')
        self.creds_file.write('[dev]\n')
        self.creds_file.write('GEAI_API_KEY = dev_key_456\n')
        self.creds_file.write('GEAI_API_BASE_URL = https://dev.example.com\n')
        self.creds_file.write('\n')
        self.creds_file.write('[prod]\n')
        self.creds_file.write('GEAI_API_KEY = prod_key_789\n')
        self.creds_file.write('GEAI_API_BASE_URL = https://prod.example.com\n')
        self.creds_file.close()

    def tearDown(self):
        """Clean up test fixtures"""
        import sys
        from pygeai.core.common.config import reset_settings
        from pygeai.core.base.session import reset_session
        
        # Restore sys.argv
        sys.argv = self._original_sys_argv
        
        # Clean up credentials file
        if hasattr(self, 'creds_file') and os.path.exists(self.creds_file.name):
            os.unlink(self.creds_file.name)
        
        # Reset singletons
        reset_settings()
        reset_session()

    def test_driver_session_uses_correct_alias_dev(self):
        """Test that CLIDriver session uses the correct alias - dev profile"""
        from pygeai.cli.geai import CLIDriver
        from pygeai.core.common.config import reset_settings, get_settings
        from pygeai.core.base.session import reset_session
        
        # Reset and initialize with custom credentials
        reset_settings()
        reset_session()
        get_settings(credentials_file=self.creds_file.name)
        
        # Test with 'dev' alias
        sys.argv = ['geai', '--credentials', self.creds_file.name, '--alias', 'dev', 'chat']
        driver = CLIDriver()
        
        # Verify driver session has correct profile
        self.assertEqual(driver.session.alias, 'dev')
        self.assertEqual(driver.session.api_key, 'dev_key_456')
        self.assertEqual(driver.session.base_url, 'https://dev.example.com')

    def test_driver_session_uses_correct_alias_prod(self):
        """Test that CLIDriver session uses the correct alias - prod profile"""
        from pygeai.cli.geai import CLIDriver
        from pygeai.core.common.config import reset_settings, get_settings
        from pygeai.core.base.session import reset_session
        
        # Reset and initialize with custom credentials
        reset_settings()
        reset_session()
        get_settings(credentials_file=self.creds_file.name)
        
        # Test with 'prod' alias
        sys.argv = ['geai', '--credentials', self.creds_file.name, '--alias', 'prod', 'llm']
        driver = CLIDriver()
        
        # Verify driver session has correct profile
        self.assertEqual(driver.session.alias, 'prod')
        self.assertEqual(driver.session.api_key, 'prod_key_789')
        self.assertEqual(driver.session.base_url, 'https://prod.example.com')

    def test_driver_session_uses_default_when_no_alias(self):
        """Test that CLIDriver uses default alias when no --alias flag provided"""
        from pygeai.cli.geai import CLIDriver
        from pygeai.core.common.config import reset_settings, get_settings
        from pygeai.core.base.session import reset_session
        
        # Reset and initialize with custom credentials
        reset_settings()
        reset_session()
        get_settings(credentials_file=self.creds_file.name)
        
        # No --alias flag, should use 'default'
        sys.argv = ['geai', '--credentials', self.creds_file.name, 'chat']
        driver = CLIDriver()
        
        # Verify driver session uses default
        self.assertEqual(driver.session.alias, 'default')
        self.assertEqual(driver.session.api_key, 'default_key')
        self.assertEqual(driver.session.base_url, 'https://default.example.com')

    def test_driver_session_with_alias_shorthand(self):
        """Test that -a shorthand works for --alias"""
        from pygeai.cli.geai import CLIDriver
        from pygeai.core.common.config import reset_settings, get_settings
        from pygeai.core.base.session import reset_session
        
        # Reset and initialize with custom credentials
        reset_settings()
        reset_session()
        get_settings(credentials_file=self.creds_file.name)
        
        # Use -a instead of --alias
        sys.argv = ['geai', '--credentials', self.creds_file.name, '-a', 'prod', 'chat']
        driver = CLIDriver()
        
        self.assertEqual(driver.session.alias, 'prod')
        self.assertEqual(driver.session.api_key, 'prod_key_789')
        self.assertEqual(driver.session.base_url, 'https://prod.example.com')


class TestCLIDriverWithCredentialsFlag(unittest.TestCase):
    """
    Test suite for CLIDriver with --credentials/--creds flag.
    Run with: python -m unittest pygeai.tests.cli.test_credentials_flag.TestCLIDriverWithCredentialsFlag
    """

    def setUp(self):
        """Reset settings and session before each test"""
        import sys
        from pygeai.core.common.config import reset_settings
        from pygeai.core.base.session import reset_session
        # Save original sys.argv
        self._original_sys_argv = sys.argv.copy()
        reset_settings()
        reset_session()
    
    def tearDown(self):
        """Reset settings and session after each test"""
        import sys
        from pygeai.core.common.config import reset_settings
        from pygeai.core.base.session import reset_session
        # Restore original sys.argv
        sys.argv = self._original_sys_argv
        reset_settings()
        reset_session()

    def test_cli_driver_with_custom_credentials(self):
        """Test CLIDriver initialization with custom credentials file"""
        import sys
        from pygeai.cli.geai import CLIDriver
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            custom_creds = f.name
            f.write('[test_profile]\n')
            f.write('GEAI_API_KEY = cli_test_key\n')
            f.write('GEAI_API_BASE_URL = https://cli.test.com\n')
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['geai', '--credentials', custom_creds, 'version']
            
            driver = CLIDriver()
            
            # Verify that the custom credentials file is being used
            from pygeai.core.common.config import get_settings
            settings = get_settings()
            self.assertEqual(settings.GEAI_CREDS_FILE, Path(custom_creds))
        finally:
            sys.argv = original_argv
            os.unlink(custom_creds)

    def test_cli_driver_with_creds_shorthand(self):
        """Test CLIDriver initialization with --creds shorthand flag"""
        import sys
        from pygeai.cli.geai import CLIDriver
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            custom_creds = f.name
            f.write('[short_profile]\n')
            f.write('GEAI_API_KEY = short_key\n')
            f.write('GEAI_API_BASE_URL = https://short.test.com\n')
        
        original_argv = sys.argv.copy()
        try:
            sys.argv = ['geai', '--creds', custom_creds, 'version']
            
            driver = CLIDriver()
            
            from pygeai.core.common.config import get_settings
            settings = get_settings()
            self.assertEqual(settings.GEAI_CREDS_FILE, Path(custom_creds))
        finally:
            sys.argv = original_argv
            os.unlink(custom_creds)

    @unittest.skip("Test passes individually but fails in full suite due to test isolation issues - investigating")
    def test_cli_driver_with_credentials_and_alias(self):
        """Test CLIDriver with both --credentials and --alias flags"""
        import sys
        from pygeai.cli.geai import CLIDriver
        from pygeai.core.common.config import reset_settings, get_settings
        from pygeai.core.base.session import reset_session
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            custom_creds = f.name
            f.write('[custom_alias]\n')
            f.write('GEAI_API_KEY = custom_alias_key\n')
            f.write('GEAI_API_BASE_URL = https://custom.test.com\n')
        
        original_argv = sys.argv.copy()
        try:
            # Reset and immediately initialize with custom credentials to prevent race conditions
            reset_settings()
            reset_session()
            get_settings(credentials_file=custom_creds)
            
            sys.argv = ['geai', '--credentials', custom_creds, '--alias', 'custom_alias', 'version']
            
            driver = CLIDriver()
            
            # Verify both credentials file and alias are used
            from pygeai.core.common.config import get_settings
            settings = get_settings()
            self.assertEqual(settings.GEAI_CREDS_FILE, Path(custom_creds), 
                           f"Expected credentials file {custom_creds}, got {settings.GEAI_CREDS_FILE}")
            self.assertEqual(driver.session.alias, 'custom_alias',
                           f"Expected alias 'custom_alias', got '{driver.session.alias}'")
            self.assertEqual(driver.session.api_key, 'custom_alias_key')
            self.assertEqual(driver.session.base_url, 'https://custom.test.com')
        finally:
            sys.argv = original_argv
            os.unlink(custom_creds)


if __name__ == '__main__':
    unittest.main()
