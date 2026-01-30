import unittest
import warnings
import logging
import io
import tempfile
import os

from pygeai.core.base.session import Session, get_session, reset_session, _validate_alias
from pygeai.core.common.config import reset_settings, get_settings
from pygeai.core.common.constants import AuthType
from pygeai.core.common.exceptions import MissingRequirementException, MixedAuthenticationException


class TestSessionValidation(unittest.TestCase):
    """
    Tests for Session validation, warnings, and error handling.
    
    python -m unittest pygeai.tests.auth.test_session_validation.TestSessionValidation
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()
        reset_settings()
        
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.WARNING)
        
        self.geai_logger = logging.getLogger('geai')
        self._original_handlers = self.geai_logger.handlers.copy()
        self._original_level = self.geai_logger.level
        
        self.geai_logger.handlers = []
        self.geai_logger.addHandler(self.handler)
        self.geai_logger.setLevel(logging.WARNING)
        self.geai_logger.propagate = False

    def tearDown(self):
        """Clean up test fixtures"""
        self.geai_logger.handlers = self._original_handlers
        self.geai_logger.level = self._original_level
        reset_session()
        reset_settings()

    def test_oauth_requires_project_id(self):
        """Test that OAuth access_token requires project_id"""
        with self.assertRaises(MissingRequirementException) as context:
            Session(
                base_url="https://api.test.com",
                access_token="oauth_token_123"
            )
        
        self.assertIn("project_id", str(context.exception).lower())

    def test_project_id_without_access_token_warns(self):
        """Test that project_id without access_token issues UserWarning"""
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            session = Session(
                api_key="api_key_123",
                base_url="https://api.test.com",
                project_id="project-123"
            )
            
            self.assertEqual(len(w), 1)
            self.assertTrue(issubclass(w[0].category, UserWarning))
            self.assertIn("project_id provided without access_token", str(w[0].message))

    def test_mixed_auth_without_allow_raises_error(self):
        """Test that both api_key and access_token without allow_mixed_auth raises MixedAuthenticationException"""
        with self.assertRaises(MixedAuthenticationException) as context:
            Session(
                api_key="api_key_123",
                base_url="https://api.test.com",
                access_token="oauth_token_123",
                project_id="project-456",
                allow_mixed_auth=False
            )
        
        self.assertIn("Cannot specify both", str(context.exception))

    def test_mixed_auth_with_allow_succeeds(self):
        """Test that mixed auth works when allow_mixed_auth=True"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456",
            allow_mixed_auth=True
        )
        
        self.assertEqual(session.api_key, "api_key_123")
        self.assertEqual(session.access_token, "oauth_token_123")
        self.assertEqual(session.project_id, "project-456")
        self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)

    def test_no_authentication_logs_warning(self):
        """Test that no authentication method logs warning"""
        Session(base_url="https://api.test.com")
        
        log_output = self.log_capture.getvalue()
        self.assertIn("No authentication method configured", log_output)

    def test_no_base_url_logs_warning(self):
        """Test that missing base_url logs warning"""
        Session(api_key="api_key_123")
        
        log_output = self.log_capture.getvalue()
        self.assertIn("Cannot instantiate session without base_url", log_output)

    def test_auth_type_api_key_only(self):
        """Test auth type is API_KEY when only api_key is provided"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        self.assertEqual(session.auth_type, AuthType.API_KEY)
        self.assertTrue(session.is_api_key())
        self.assertFalse(session.is_oauth())

    def test_auth_type_oauth_only(self):
        """Test auth type is OAUTH_TOKEN when OAuth credentials are provided"""
        session = Session(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)
        self.assertTrue(session.is_oauth())
        self.assertFalse(session.is_api_key())

    def test_auth_type_none(self):
        """Test auth type is NONE when no credentials are provided"""
        session = Session(base_url="https://api.test.com")
        
        self.assertEqual(session.auth_type, AuthType.NONE)
        self.assertFalse(session.is_oauth())
        self.assertFalse(session.is_api_key())

    def test_auth_type_oauth_takes_precedence(self):
        """Test that OAuth takes precedence over API key when both are present"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456",
            allow_mixed_auth=True
        )
        
        self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)

    def test_get_active_token_api_key(self):
        """Test get_active_token returns api_key when using API key auth"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        self.assertEqual(session.get_active_token(), "api_key_123")

    def test_get_active_token_oauth(self):
        """Test get_active_token returns access_token when using OAuth"""
        session = Session(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(session.get_active_token(), "oauth_token_123")

    def test_get_active_token_none(self):
        """Test get_active_token returns None when no auth is configured"""
        session = Session(base_url="https://api.test.com")
        
        self.assertIsNone(session.get_active_token())

    def test_setter_updates_auth_type_api_key(self):
        """Test that setting api_key updates auth type"""
        session = Session(base_url="https://api.test.com")
        self.assertEqual(session.auth_type, AuthType.NONE)
        
        session.api_key = "new_api_key"
        self.assertEqual(session.auth_type, AuthType.API_KEY)

    def test_setter_updates_auth_type_oauth(self):
        """Test that setting OAuth properties updates auth type"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        self.assertEqual(session.auth_type, AuthType.API_KEY)
        
        session.access_token = "oauth_token_123"
        session.project_id = "project-456"
        self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)

    def test_alias_defaults_to_default(self):
        """Test that alias defaults to 'default' when not provided"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        self.assertEqual(session.alias, "default")

    def test_alias_can_be_set(self):
        """Test that custom alias can be set"""
        session = Session(
            api_key="api_key_123",
            base_url="https://api.test.com",
            alias="production"
        )
        
        self.assertEqual(session.alias, "production")

    def test_organization_id_can_be_set(self):
        """Test that organization_id can be set and retrieved"""
        session = Session(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456",
            organization_id="org-789"
        )
        
        self.assertEqual(session.organization_id, "org-789")


class TestGetSession(unittest.TestCase):
    """
    Tests for get_session function and singleton behavior.
    
    python -m unittest pygeai.tests.auth.test_session_validation.TestGetSession
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()
        reset_settings()
        
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.WARNING)
        
        self.geai_logger = logging.getLogger('geai')
        self._original_handlers = self.geai_logger.handlers.copy()
        self._original_level = self.geai_logger.level
        
        self.geai_logger.handlers = []
        self.geai_logger.addHandler(self.handler)
        self.geai_logger.setLevel(logging.WARNING)
        self.geai_logger.propagate = False

    def tearDown(self):
        """Clean up test fixtures"""
        self.geai_logger.handlers = self._original_handlers
        self.geai_logger.level = self._original_level
        reset_session()
        reset_settings()

    def test_get_session_is_singleton(self):
        """Test that get_session returns the same instance"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = test_key\n')
            f.write('GEAI_API_BASE_URL = https://test.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            session1 = get_session()
            session2 = get_session()
            
            self.assertIs(session1, session2)
        finally:
            os.unlink(creds_file)

    def test_get_session_loads_from_config(self):
        """Test that get_session loads credentials from config file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = config_key_123\n')
            f.write('GEAI_API_BASE_URL = https://config.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            session = get_session()
            
            self.assertEqual(session.api_key, "config_key_123")
            self.assertEqual(session.base_url, "https://config.example.com")
        finally:
            os.unlink(creds_file)

    def test_get_session_loads_oauth_from_config(self):
        """Test that get_session loads OAuth credentials from config"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_OAUTH_ACCESS_TOKEN = oauth_token_123\n')
            f.write('GEAI_PROJECT_ID = project-456\n')
            f.write('GEAI_API_BASE_URL = https://oauth.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            session = get_session()
            
            self.assertEqual(session.access_token, "oauth_token_123")
            self.assertEqual(session.project_id, "project-456")
            self.assertEqual(session.auth_type, AuthType.OAUTH_TOKEN)
        finally:
            os.unlink(creds_file)

    def test_get_session_warns_about_mixed_auth(self):
        """Test that get_session warns when both API key and OAuth are configured"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = api_key_123\n')
            f.write('GEAI_OAUTH_ACCESS_TOKEN = oauth_token_123\n')
            f.write('GEAI_PROJECT_ID = project-456\n')
            f.write('GEAI_API_BASE_URL = https://mixed.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            session = get_session()
            
            log_output = self.log_capture.getvalue()
            self.assertIn("Both API key and OAuth token configured", log_output)
            self.assertIn("OAuth token will take precedence", log_output)
        finally:
            os.unlink(creds_file)

    def test_get_session_updates_existing_with_alias(self):
        """Test that get_session with alias updates existing session"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = default_key\n')
            f.write('GEAI_API_BASE_URL = https://default.example.com\n')
            f.write('\n')
            f.write('[staging]\n')
            f.write('GEAI_API_KEY = staging_key\n')
            f.write('GEAI_API_BASE_URL = https://staging.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            session1 = get_session('default')
            self.assertEqual(session1.api_key, "default_key")
            
            session2 = get_session('staging')
            self.assertEqual(session2.api_key, "staging_key")
            
            self.assertIs(session1, session2)
        finally:
            os.unlink(creds_file)

    def test_validate_alias_raises_for_missing(self):
        """Test that _validate_alias raises exception for non-existent alias"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = test_key\n')
            f.write('GEAI_API_BASE_URL = https://test.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            with self.assertRaises(MissingRequirementException) as context:
                _validate_alias('nonexistent', allow_missing_default=False)
            
            self.assertIn("doesn't exist", str(context.exception))
        finally:
            os.unlink(creds_file)

    def test_validate_alias_allows_missing_default(self):
        """Test that _validate_alias allows missing 'default' when flag is set"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[production]\n')
            f.write('GEAI_API_KEY = prod_key\n')
            f.write('GEAI_API_BASE_URL = https://prod.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            
            _validate_alias('default', allow_missing_default=True)
        finally:
            os.unlink(creds_file)


if __name__ == '__main__':
    unittest.main()
