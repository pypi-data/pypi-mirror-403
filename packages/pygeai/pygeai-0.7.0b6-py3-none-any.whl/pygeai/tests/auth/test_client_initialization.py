import unittest
import tempfile
import os
import logging
import io

from pygeai.core.base.clients import BaseClient
from pygeai.core.base.session import reset_session, get_session
from pygeai.core.common.config import reset_settings, get_settings
from pygeai.core.common.constants import AuthType
from pygeai.core.common.exceptions import MissingRequirementException, MixedAuthenticationException


class TestBaseClientInitialization(unittest.TestCase):
    """
    Tests for BaseClient initialization with different authentication methods.
    
    python -m unittest pygeai.tests.auth.test_client_initialization.TestBaseClientInitialization
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()
        reset_settings()
        
        from pygeai.core.base.clients import BaseClient
        BaseClient._logged_session_config = None

    def tearDown(self):
        """Clean up test fixtures"""
        from pygeai.core.base.clients import BaseClient
        BaseClient._logged_session_config = None
        
        reset_session()
        reset_settings()

    def test_init_with_api_key_direct(self):
        """Test BaseClient initialization with direct API key"""
        client = BaseClient(
            api_key="test_api_key",
            base_url="https://api.test.com"
        )
        
        self.assertEqual(client.session.api_key, "test_api_key")
        self.assertEqual(client.session.base_url, "https://api.test.com")
        self.assertEqual(client.session.auth_type, AuthType.API_KEY)
        self.assertEqual(client.api_service.token, "test_api_key")

    def test_init_with_oauth_direct(self):
        """Test BaseClient initialization with direct OAuth credentials"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(client.session.access_token, "oauth_token_123")
        self.assertEqual(client.session.project_id, "project-456")
        self.assertEqual(client.session.auth_type, AuthType.OAUTH_TOKEN)
        self.assertEqual(client.api_service.token, "oauth_token_123")
        self.assertEqual(client.api_service.project_id, "project-456")

    def test_init_with_alias_loads_from_config(self):
        """Test BaseClient initialization with alias loads from config"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[staging]\n')
            f.write('GEAI_API_KEY = staging_api_key\n')
            f.write('GEAI_API_BASE_URL = https://staging.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            reset_session()
            
            client = BaseClient(alias="staging")
            
            self.assertEqual(client.session.api_key, "staging_api_key")
            self.assertEqual(client.session.base_url, "https://staging.example.com")
        finally:
            os.unlink(creds_file)

    def test_init_with_nonexistent_alias_raises_error(self):
        """Test that using non-existent alias raises MissingRequirementException"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = default_key\n')
            f.write('GEAI_API_BASE_URL = https://default.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            reset_session()
            
            with self.assertRaises(MissingRequirementException):
                BaseClient(alias="nonexistent")
        finally:
            os.unlink(creds_file)

    def test_init_oauth_without_project_id_raises_error(self):
        """Test that OAuth without project_id raises MissingRequirementException"""
        with self.assertRaises(MissingRequirementException) as context:
            BaseClient(
                base_url="https://api.test.com",
                access_token="oauth_token_123"
            )
        
        self.assertIn("project_id is required", str(context.exception))

    def test_init_mixed_auth_without_allow_raises_error(self):
        """Test that mixed auth without allow_mixed_auth raises MixedAuthenticationException"""
        with self.assertRaises(MixedAuthenticationException) as context:
            BaseClient(
                api_key="api_key_123",
                base_url="https://api.test.com",
                access_token="oauth_token_123",
                project_id="project-456",
                allow_mixed_auth=False
            )
        
        self.assertIn("Cannot specify both", str(context.exception))

    def test_init_mixed_auth_with_allow_succeeds(self):
        """Test that mixed auth with allow_mixed_auth=True succeeds"""
        client = BaseClient(
            api_key="api_key_123",
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456",
            allow_mixed_auth=True
        )
        
        self.assertEqual(client.session.auth_type, AuthType.OAUTH_TOKEN)
        self.assertEqual(client.api_service.token, "oauth_token_123")

    def test_init_with_organization_id(self):
        """Test BaseClient initialization with organization_id"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456",
            organization_id="org-789"
        )
        
        self.assertEqual(client.session.organization_id, "org-789")
        self.assertEqual(client.api_service.organization_id, "org-789")

    def test_init_mutates_singleton_session(self):
        """Test that direct credential initialization mutates the singleton session"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = config_key\n')
            f.write('GEAI_API_BASE_URL = https://config.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            reset_session()
            
            session_before = get_session()
            self.assertEqual(session_before.api_key, "config_key")
            
            client = BaseClient(
                api_key="new_key",
                base_url="https://new.example.com"
            )
            
            session_after = get_session()
            self.assertEqual(session_after.api_key, "new_key")
            self.assertIs(session_before, session_after)
        finally:
            os.unlink(creds_file)

    def test_init_default_uses_default_session(self):
        """Test that initialization without params uses default session"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = default_key\n')
            f.write('GEAI_API_BASE_URL = https://default.example.com\n')
        
        try:
            reset_settings()
            get_settings(credentials_file=creds_file)
            reset_session()
            
            client = BaseClient()
            
            self.assertEqual(client.session.api_key, "default_key")
            self.assertEqual(client.session.base_url, "https://default.example.com")
        finally:
            os.unlink(creds_file)


class TestBaseClientAuthenticationLogging(unittest.TestCase):
    """
    Tests for authentication logging behavior in BaseClient.
    
    python -m unittest pygeai.tests.auth.test_client_initialization.TestBaseClientAuthenticationLogging
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()
        reset_settings()
        
        from pygeai.core.base.clients import BaseClient
        BaseClient._logged_session_config = None
        
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.INFO)
        
        self.geai_logger = logging.getLogger('geai')
        self._original_handlers = self.geai_logger.handlers.copy()
        self._original_level = self.geai_logger.level
        
        self.geai_logger.handlers = []
        self.geai_logger.addHandler(self.handler)
        self.geai_logger.setLevel(logging.INFO)
        self.geai_logger.propagate = False

    def tearDown(self):
        """Clean up test fixtures"""
        self.geai_logger.handlers = self._original_handlers
        self.geai_logger.level = self._original_level
        
        from pygeai.core.base.clients import BaseClient
        BaseClient._logged_session_config = None
        
        reset_session()
        reset_settings()

    def test_logs_api_key_authentication(self):
        """Test that API key authentication is logged"""
        BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        log_output = self.log_capture.getvalue()
        
        self.assertIn("Using API Key authentication", log_output)

    def test_logs_oauth_authentication(self):
        """Test that OAuth authentication is logged"""
        BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token",
            project_id="project-123"
        )
        
        log_output = self.log_capture.getvalue()
        
        self.assertIn("Using OAuth 2.0 authentication", log_output)
        self.assertIn("Project ID: project-123", log_output)

    def test_logs_organization_id_when_present(self):
        """Test that organization ID is logged when present"""
        BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token",
            project_id="project-123",
            organization_id="org-456"
        )
        
        log_output = self.log_capture.getvalue()
        
        self.assertIn("Organization ID: org-456", log_output)

    def test_logs_base_url_and_alias(self):
        """Test that base URL and alias are logged"""
        BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        log_output = self.log_capture.getvalue()
        
        self.assertIn("Base URL: https://api.test.com", log_output)
        self.assertIn("Alias: default", log_output)

    def test_authentication_logged_only_once_for_same_config(self):
        """Test that authentication is logged only once for the same configuration"""
        BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        first_log = self.log_capture.getvalue()
        auth_count_first = first_log.count("Using API Key authentication")
        self.assertEqual(auth_count_first, 1)
        
        self.log_capture.truncate(0)
        self.log_capture.seek(0)
        
        BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        second_log = self.log_capture.getvalue()
        auth_count_second = second_log.count("Using API Key authentication")
        self.assertEqual(auth_count_second, 0)

    def test_authentication_logged_again_for_different_config(self):
        """Test that authentication is logged again when configuration changes"""
        BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        first_log = self.log_capture.getvalue()
        self.assertIn("Using API Key authentication", first_log)
        
        self.log_capture.truncate(0)
        self.log_capture.seek(0)
        
        from pygeai.core.base.clients import BaseClient as BC
        BC._logged_session_config = None
        reset_session()
        
        BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token",
            project_id="project-123"
        )
        
        second_log = self.log_capture.getvalue()
        self.assertIn("Using OAuth 2.0 authentication", second_log)


class TestBaseClientSessionInteraction(unittest.TestCase):
    """
    Tests for BaseClient interaction with Session singleton.
    
    python -m unittest pygeai.tests.auth.test_client_initialization.TestBaseClientSessionInteraction
    """

    def setUp(self):
        """Set up test fixtures"""
        reset_session()
        reset_settings()

    def tearDown(self):
        """Clean up test fixtures"""
        reset_session()
        reset_settings()

    def test_multiple_clients_share_session(self):
        """Test that multiple clients share the same session instance"""
        client1 = BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        client2 = BaseClient(
            api_key="test_key",
            base_url="https://api.test.com"
        )
        
        self.assertIs(client1.session, client2.session)

    def test_client_with_different_credentials_updates_session(self):
        """Test that creating client with different credentials updates shared session"""
        client1 = BaseClient(
            api_key="first_key",
            base_url="https://first.test.com"
        )
        
        self.assertEqual(client1.session.api_key, "first_key")
        
        client2 = BaseClient(
            api_key="second_key",
            base_url="https://second.test.com"
        )
        
        self.assertEqual(client1.session.api_key, "second_key")
        self.assertEqual(client2.session.api_key, "second_key")

    def test_api_service_uses_active_token(self):
        """Test that api_service uses the active token from session"""
        client = BaseClient(
            api_key="api_key_123",
            base_url="https://api.test.com",
            access_token="oauth_token_456",
            project_id="project-789",
            allow_mixed_auth=True
        )
        
        self.assertEqual(client.api_service.token, "oauth_token_456")

    def test_api_service_configured_with_session_properties(self):
        """Test that api_service is configured with session properties"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token",
            project_id="project-123",
            organization_id="org-456"
        )
        
        self.assertEqual(client.api_service.base_url, "https://api.test.com")
        self.assertEqual(client.api_service.token, "oauth_token")
        self.assertEqual(client.api_service.project_id, "project-123")
        self.assertEqual(client.api_service.organization_id, "org-456")


if __name__ == '__main__':
    unittest.main()
