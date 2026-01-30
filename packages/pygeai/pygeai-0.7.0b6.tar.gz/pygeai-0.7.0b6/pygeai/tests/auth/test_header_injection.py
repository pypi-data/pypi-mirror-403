import unittest
from unittest.mock import patch, MagicMock

from pygeai.core.base.clients import BaseClient
from pygeai.core.services.rest import GEAIApiService


class TestHeaderInjection(unittest.TestCase):
    """
    Tests for proper header injection in API requests.
    
    python -m unittest pygeai.tests.auth.test_header_injection.TestHeaderInjection
    """

    def test_api_key_auth_header_format(self):
        """Test that API key is formatted as Bearer token"""
        client = BaseClient(
            api_key="test_api_key_123",
            base_url="https://api.test.com"
        )
        
        headers = client.api_service._add_token_to_headers({})
        
        self.assertEqual(headers['Authorization'], 'Bearer test_api_key_123')

    def test_oauth_auth_header_format(self):
        """Test that OAuth access token is formatted as Bearer token"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_access_token_123",
            project_id="project-456"
        )
        
        headers = client.api_service._add_token_to_headers({})
        
        self.assertEqual(headers['Authorization'], 'Bearer oauth_access_token_123')

    def test_oauth_project_id_header_added(self):
        """Test that ProjectId header is added for OAuth"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        headers = client.api_service._add_oauth_context_to_headers({})
        
        self.assertEqual(headers['ProjectId'], 'project-456')

    def test_oauth_organization_id_header_added(self):
        """Test that OrganizationId header is added when provided"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456",
            organization_id="org-789"
        )
        
        headers = client.api_service._add_oauth_context_to_headers({})
        
        self.assertEqual(headers['ProjectId'], 'project-456')
        self.assertEqual(headers['OrganizationId'], 'org-789')

    def test_api_key_no_project_id_header(self):
        """Test that ProjectId header is not added for API key auth without project_id"""
        client = BaseClient(
            api_key="api_key_123",
            base_url="https://api.test.com"
        )
        
        headers = client.api_service._add_token_to_headers({})
        headers = client.api_service._add_oauth_context_to_headers(headers)
        
        self.assertNotIn('ProjectId', headers)
        self.assertNotIn('OrganizationId', headers)

    def test_headers_preserved_when_adding_auth(self):
        """Test that existing headers are preserved when adding auth headers"""
        client = BaseClient(
            base_url="https://api.test.com",
            access_token="oauth_token_123",
            project_id="project-456"
        )
        
        existing_headers = {
            'Content-Type': 'application/json',
            'X-Custom-Header': 'custom_value'
        }
        
        headers = client.api_service._add_token_to_headers(existing_headers.copy())
        headers = client.api_service._add_oauth_context_to_headers(headers)
        
        self.assertEqual(headers['Authorization'], 'Bearer oauth_token_123')
        self.assertEqual(headers['ProjectId'], 'project-456')
        self.assertEqual(headers['Content-Type'], 'application/json')
        self.assertEqual(headers['X-Custom-Header'], 'custom_value')

    def test_authorization_header_not_duplicated(self):
        """Test that Authorization header is not duplicated if already present"""
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token_123"
        )
        
        existing_headers = {'Authorization': 'Bearer existing_token'}
        
        headers = service._add_token_to_headers(existing_headers.copy())
        
        self.assertEqual(headers['Authorization'], 'Bearer existing_token')

    def test_project_id_header_case_sensitivity(self):
        """Test that ProjectId header checks for both case variations"""
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123"
        )
        
        headers_lower = {'project-id': 'existing-project'}
        result_lower = service._add_oauth_context_to_headers(headers_lower.copy())
        
        self.assertEqual(result_lower['project-id'], 'existing-project')
        self.assertNotIn('ProjectId', result_lower)

    def test_project_id_header_capital_case(self):
        """Test that ProjectId header is not duplicated with capital case"""
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123"
        )
        
        headers_capital = {'ProjectId': 'existing-project'}
        result_capital = service._add_oauth_context_to_headers(headers_capital.copy())
        
        self.assertEqual(result_capital['ProjectId'], 'existing-project')

    def test_organization_id_header_case_sensitivity(self):
        """Test that OrganizationId header checks for both case variations"""
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123",
            organization_id="org-456"
        )
        
        headers_lower = {'organization-id': 'existing-org'}
        result_lower = service._add_oauth_context_to_headers(headers_lower.copy())
        
        self.assertEqual(result_lower['organization-id'], 'existing-org')
        self.assertNotIn('OrganizationId', result_lower)

    def test_empty_headers_dict_created_if_none(self):
        """Test that empty headers dict is created if None is passed"""
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123"
        )
        
        headers = service._add_oauth_context_to_headers(None)
        
        self.assertIsInstance(headers, dict)
        self.assertEqual(headers['ProjectId'], 'project-123')

    def test_no_project_id_no_header_added(self):
        """Test that no ProjectId header is added when project_id is None"""
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token"
        )
        
        headers = service._add_oauth_context_to_headers({})
        
        self.assertNotIn('ProjectId', headers)
        self.assertNotIn('project-id', headers)

    def test_api_key_with_project_id_adds_header(self):
        """Test that ProjectId header is added even with API key auth if project_id is set"""
        client = BaseClient(
            api_key="api_key_123",
            base_url="https://api.test.com",
            project_id="project-456"
        )
        
        headers = client.api_service._add_oauth_context_to_headers({})
        
        self.assertEqual(headers['ProjectId'], 'project-456')


class TestGEAIApiServiceHeaderPropagation(unittest.TestCase):
    """
    Tests that headers are properly propagated in all HTTP methods.
    
    python -m unittest pygeai.tests.auth.test_header_injection.TestGEAIApiServiceHeaderPropagation
    """

    @patch('pygeai.core.services.rest.req.Session')
    def test_get_request_includes_oauth_headers(self, mock_session_class):
        """Test that GET requests include OAuth headers"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.url = "https://api.test.com/endpoint"
        mock_session.get.return_value = mock_response
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123",
            organization_id="org-456"
        )
        
        service.get("endpoint")
        
        call_args = mock_session.get.call_args
        headers = call_args[1]['headers']
        
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['ProjectId'], 'project-123')
        self.assertEqual(headers['OrganizationId'], 'org-456')

    @patch('pygeai.core.services.rest.req.Session')
    def test_post_request_includes_oauth_headers(self, mock_session_class):
        """Test that POST requests include OAuth headers"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.url = "https://api.test.com/endpoint"
        mock_session.post.return_value = mock_response
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123"
        )
        
        service.post("endpoint", data={"key": "value"})
        
        call_args = mock_session.post.call_args
        headers = call_args[1]['headers']
        
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['ProjectId'], 'project-123')

    @patch('pygeai.core.services.rest.req.Session')
    def test_put_request_includes_oauth_headers(self, mock_session_class):
        """Test that PUT requests include OAuth headers"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.url = "https://api.test.com/endpoint"
        mock_session.put.return_value = mock_response
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123"
        )
        
        service.put("endpoint", data={"key": "value"})
        
        call_args = mock_session.put.call_args
        headers = call_args[1]['headers']
        
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['ProjectId'], 'project-123')

    @patch('pygeai.core.services.rest.req.Session')
    def test_delete_request_includes_oauth_headers(self, mock_session_class):
        """Test that DELETE requests include OAuth headers"""
        mock_session = MagicMock()
        mock_response = MagicMock()
        mock_response.url = "https://api.test.com/endpoint"
        mock_session.delete.return_value = mock_response
        mock_session_class.return_value.__enter__.return_value = mock_session
        
        service = GEAIApiService(
            base_url="https://api.test.com",
            token="test_token",
            project_id="project-123"
        )
        
        service.delete("endpoint")
        
        call_args = mock_session.delete.call_args
        headers = call_args[1]['headers']
        
        self.assertIn('Authorization', headers)
        self.assertEqual(headers['ProjectId'], 'project-123')


if __name__ == '__main__':
    unittest.main()
