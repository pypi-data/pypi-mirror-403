import unittest
from unittest.mock import patch, MagicMock
from pygeai.analytics.clients import AnalyticsClient


class TestAnalyticsClient(unittest.TestCase):

    def setUp(self):
        self.client = AnalyticsClient()

    @patch('pygeai.analytics.clients.AnalyticsClient.api_service')
    def test_get_agents_created_and_modified(self, mock_api_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"createdAgents": 10, "modifiedAgents": 5}
        mock_api_service.get.return_value = mock_response

        result = self.client.get_agents_created_and_modified("2024-01-01", "2024-01-31")

        self.assertEqual(result["createdAgents"], 10)
        self.assertEqual(result["modifiedAgents"], 5)
        mock_api_service.get.assert_called_once()

    @patch('pygeai.analytics.clients.AnalyticsClient.api_service')
    def test_get_total_requests_per_day(self, mock_api_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "requestsPerDay": [
                {"date": "2024-01-01", "totalRequests": 100, "totalRequestsWithError": 5}
            ]
        }
        mock_api_service.get.return_value = mock_response

        result = self.client.get_total_requests_per_day("2024-01-01", "2024-01-31")

        self.assertIn("requestsPerDay", result)
        mock_api_service.get.assert_called_once()

    @patch('pygeai.analytics.clients.AnalyticsClient.api_service')
    def test_get_total_requests_per_day_with_agent_name(self, mock_api_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "requestsPerDay": [
                {"date": "2024-01-01", "totalRequests": 50, "totalRequestsWithError": 2}
            ]
        }
        mock_api_service.get.return_value = mock_response

        result = self.client.get_total_requests_per_day("2024-01-01", "2024-01-31", agent_name="TestAgent")

        self.assertIn("requestsPerDay", result)
        mock_api_service.get.assert_called_once()

    @patch('pygeai.analytics.clients.AnalyticsClient.api_service')
    def test_get_average_cost_per_request(self, mock_api_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"averageCost": 2.50}
        mock_api_service.get.return_value = mock_response

        result = self.client.get_average_cost_per_request("2024-01-01", "2024-01-31")

        self.assertEqual(result["averageCost"], 2.50)
        mock_api_service.get.assert_called_once()

    @patch('pygeai.analytics.clients.AnalyticsClient.api_service')
    def test_get_total_tokens(self, mock_api_service):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "totalInputTokens": 5000,
            "totalOutputTokens": 3000,
            "totalTokens": 8000
        }
        mock_api_service.get.return_value = mock_response

        result = self.client.get_total_tokens("2024-01-01", "2024-01-31")

        self.assertEqual(result["totalTokens"], 8000)
        mock_api_service.get.assert_called_once()


if __name__ == '__main__':
    unittest.main()
