import unittest

from pygeai.lab.clients import AILabClient
from pygeai.evaluation.clients import EvaluationClient
from pygeai.core.secrets.clients import SecretClient
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import MissingRequirementException


class TestOAuthAuthentication(unittest.TestCase):
    """
    Tests for OAuth authentication support across all clients.
    
    python -m unittest pygeai.tests.auth.test_oauth.TestOAuthAuthentication
    """

    def test_base_client_oauth_initialization(self):
        """Test BaseClient accepts OAuth parameters"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(client.api_service.token, "oauth_token_123")
        self.assertEqual(client.api_service.project_id, "project-456")

    def test_base_client_api_key_initialization(self):
        """Test BaseClient backward compatibility with API key"""
        client = BaseClient(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        self.assertEqual(client.api_service.token, "api_key_123")
        self.assertIsNone(client.api_service.project_id)

    def test_base_client_incomplete_oauth_raises_error(self):
        """Test that providing only access_token without project_id raises error"""
        with self.assertRaises(MissingRequirementException) as context:
            BaseClient(
                base_url="https://api.test.com",
                access_token="oauth_token_123"
            )
        
        self.assertIn("project_id is required when using access_token", str(context.exception))

    def test_oauth_headers_are_added_correctly(self):
        """Test that OAuth headers are added correctly by _add_token_to_headers"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        headers = client.api_service._add_token_to_headers({})
        headers = client.api_service._add_oauth_context_to_headers(headers)
        
        self.assertEqual(headers.get('Authorization'), 'Bearer oauth_token_123')
        self.assertEqual(headers.get('ProjectId'), 'project-456')

    def test_api_key_headers_use_bearer(self):
        """Test that API key also uses Bearer format in Authorization header"""
        client = BaseClient(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        headers = client.api_service._add_token_to_headers({})
        
        self.assertEqual(headers.get('Authorization'), 'Bearer api_key_123')
        self.assertNotIn('ProjectId', headers)

    def test_oauth_headers_preserve_existing_headers(self):
        """Test that OAuth headers are added while preserving existing headers"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        existing_headers = {'Content-Type': 'application/json', 'Custom-Header': 'value'}
        headers = client.api_service._add_token_to_headers(existing_headers.copy())
        headers = client.api_service._add_oauth_context_to_headers(headers)
        
        self.assertEqual(headers.get('Authorization'), 'Bearer oauth_token_123')
        self.assertEqual(headers.get('ProjectId'), 'project-456')
        self.assertEqual(headers.get('Content-Type'), 'application/json')
        self.assertEqual(headers.get('Custom-Header'), 'value')

    def test_ailab_client_oauth_initialization(self):
        """Test AILabClient accepts OAuth parameters with project_id keyword-only"""
        client = AILabClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(client.api_service.token, "oauth_token_123")
        self.assertEqual(client.api_service.project_id, "project-456")
        self.assertEqual(client.project_id, "project-456")

    def test_ailab_client_api_key_with_project_id(self):
        """Test AILabClient with API key and project_id"""
        client = AILabClient(
            api_key="api_key_123",
            base_url="https://api.test.com",
            project_id="project-456"
        )
        
        self.assertEqual(client.api_service.token, "api_key_123")
        self.assertEqual(client.project_id, "project-456")

    def test_evaluation_client_oauth_initialization(self):
        """Test EvaluationClient accepts OAuth parameters"""
        client = EvaluationClient(
            base_url="https://api.test.com",
            eval_url="https://eval.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(client.api_service.token, "oauth_token_123")
        self.assertEqual(client.api_service.project_id, "project-456")

    def test_evaluation_client_api_key_backward_compatibility(self):
        """Test EvaluationClient backward compatibility with API key"""
        client = EvaluationClient(
            api_key="api_key_123",
            base_url="https://api.test.com",
            eval_url="https://eval.test.com"
        )
        
        self.assertEqual(client.api_service.token, "api_key_123")

    def test_secret_client_oauth_initialization(self):
        """Test SecretClient accepts OAuth parameters"""
        client = SecretClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        self.assertEqual(client.api_service.token, "oauth_token_123")
        self.assertEqual(client.api_service.project_id, "project-456")

    def test_secret_client_api_key_backward_compatibility(self):
        """Test SecretClient backward compatibility with API key"""
        client = SecretClient(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        self.assertEqual(client.api_service.token, "api_key_123")

    def test_oauth_token_used_over_api_key_in_headers(self):
        """Test that when OAuth token is used, it's properly formatted"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_wins",
            project_id="project-wins"
        )
        
        self.assertEqual(client.api_service.token, "oauth_token_wins")
        self.assertEqual(client.api_service.project_id, "project-wins")
        
        headers = client.api_service._add_token_to_headers({})
        headers = client.api_service._add_oauth_context_to_headers(headers)
        self.assertEqual(headers['Authorization'], 'Bearer oauth_token_wins')
        self.assertEqual(headers['ProjectId'], 'project-wins')


if __name__ == '__main__':
    unittest.main()
