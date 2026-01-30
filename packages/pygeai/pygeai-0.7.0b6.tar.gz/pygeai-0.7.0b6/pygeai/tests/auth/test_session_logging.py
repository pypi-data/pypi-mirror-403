import unittest
import logging
import io
import tempfile
import os

from pygeai.core.base.session import reset_session, get_session
from pygeai.core.common.config import reset_settings, get_settings
from pygeai.chat.clients import ChatClient
from pygeai.core.llm.clients import LlmClient
from pygeai.core.embeddings.clients import EmbeddingsClient


class TestSessionAuthenticationLogging(unittest.TestCase):
    """
    Test that authentication method logging happens only when sessions are created or aliases change,
    not every time a client is instantiated.
    """

    def setUp(self):
        """Set up test fixtures"""
        self._original_geai_logger_handlers = logging.getLogger('geai').handlers.copy()
        self._original_geai_logger_level = logging.getLogger('geai').level
        
        # Set up log capture
        self.log_capture = io.StringIO()
        self.handler = logging.StreamHandler(self.log_capture)
        self.handler.setLevel(logging.INFO)
        
        # Configure logger
        geai_logger = logging.getLogger('geai')
        geai_logger.handlers = []
        geai_logger.addHandler(self.handler)
        geai_logger.setLevel(logging.INFO)
        geai_logger.propagate = False
        
        reset_settings()
        reset_session()

    def tearDown(self):
        """Clean up test fixtures"""
        # Restore logger
        geai_logger = logging.getLogger('geai')
        geai_logger.handlers = self._original_geai_logger_handlers
        geai_logger.level = self._original_geai_logger_level
        
        # Reset BaseClient logging flag
        from pygeai.core.base.clients import BaseClient
        BaseClient._logged_session_config = None
        
        reset_settings()
        reset_session()

    def test_authentication_logged_once_for_multiple_clients(self):
        """Test that authentication is logged only once when creating multiple clients"""
        # Create 5 different clients
        ChatClient()
        LlmClient()
        EmbeddingsClient()
        ChatClient()
        LlmClient()
        
        # Get log output
        log_output = self.log_capture.getvalue()
        
        # Count authentication log messages
        auth_count = log_output.count('Using API Key authentication') + \
                    log_output.count('Using OAuth 2.0 authentication')
        
        self.assertEqual(auth_count, 1, 
                        f"Expected 1 authentication log, got {auth_count}. Log:\n{log_output}")

    def test_authentication_logged_when_alias_changes(self):
        """Test that authentication is logged when switching between aliases"""
        # Create credentials file with multiple aliases
        with tempfile.NamedTemporaryFile(mode='w', suffix='_credentials', delete=False) as f:
            creds_file = f.name
            f.write('[default]\n')
            f.write('GEAI_API_KEY = default_key\n')
            f.write('GEAI_API_BASE_URL = https://default.example.com\n')
            f.write('\n')
            f.write('[staging]\n')
            f.write('GEAI_API_KEY = staging_key\n')
            f.write('GEAI_API_BASE_URL = https://staging.example.com\n')
            f.write('GEAI_OAUTH_ACCESS_TOKEN = staging_token\n')
            f.write('GEAI_PROJECT_ID = staging_project\n')
        
        try:
            reset_settings()
            reset_session()
            get_settings(credentials_file=creds_file)
            
            # Use default alias
            get_session('default')
            ChatClient()
            ChatClient()
            
            # Switch to staging alias
            get_session('staging')
            ChatClient()
            ChatClient()
            
            # Get log output
            log_output = self.log_capture.getvalue()
            
            # Should have logged API Key once for default, OAuth once for staging
            api_key_count = log_output.count('Using API Key authentication')
            oauth_count = log_output.count('Using OAuth 2.0 authentication')
            
            self.assertEqual(api_key_count, 1,
                           f"Expected 1 API Key log, got {api_key_count}")
            self.assertEqual(oauth_count, 1,
                           f"Expected 1 OAuth log, got {oauth_count}")
        finally:
            os.unlink(creds_file)


if __name__ == '__main__':
    unittest.main()
