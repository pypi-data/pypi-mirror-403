import unittest
from unittest.mock import patch
from pygeai.core.common.exceptions import APIError
from pygeai.core.handlers import ErrorHandler
from pygeai.analytics.managers import AnalyticsManager
from pygeai.analytics.mappers import AnalyticsResponseMapper
from pygeai.analytics.responses import (
    AgentsCreatedAndModifiedResponse, TotalRequestsPerDayResponse,
    AverageCostPerRequestResponse, NumberOfTokensResponse
)


class TestAnalyticsManager(unittest.TestCase):

    def setUp(self):
        self.manager = AnalyticsManager()
        self.error_response = {"errors": [{"id": 404, "description": "Not found"}]}

    @patch("pygeai.analytics.clients.AnalyticsClient.get_agents_created_and_modified")
    def test_get_agents_created_and_modified(self, mock_get_agents):
        mock_response = AgentsCreatedAndModifiedResponse(createdAgents=10, modifiedAgents=5)
        mock_get_agents.return_value = {"createdAgents": 10, "modifiedAgents": 5}

        with patch.object(AnalyticsResponseMapper, 'map_to_agents_created_and_modified_response', return_value=mock_response):
            response = self.manager.get_agents_created_and_modified("2024-01-01", "2024-01-31")

        self.assertIsInstance(response, AgentsCreatedAndModifiedResponse)
        self.assertEqual(response.createdAgents, 10)
        self.assertEqual(response.modifiedAgents, 5)
        mock_get_agents.assert_called_once_with(start_date="2024-01-01", end_date="2024-01-31")

    @patch("pygeai.analytics.clients.AnalyticsClient.get_agents_created_and_modified")
    def test_get_agents_created_and_modified_error(self, mock_get_agents):
        mock_get_agents.return_value = self.error_response

        with patch.object(ErrorHandler, 'has_errors', return_value=True):
            with patch.object(ErrorHandler, 'extract_error', return_value="Not found"):
                with self.assertRaises(APIError) as context:
                    self.manager.get_agents_created_and_modified("2024-01-01", "2024-01-31")

        self.assertIn("Error received while retrieving agents created and modified", str(context.exception))
        mock_get_agents.assert_called_once_with(start_date="2024-01-01", end_date="2024-01-31")

    @patch("pygeai.analytics.clients.AnalyticsClient.get_total_requests_per_day")
    def test_get_total_requests_per_day(self, mock_get_requests):
        mock_response = TotalRequestsPerDayResponse(requestsPerDay=[])
        mock_get_requests.return_value = {"requestsPerDay": []}

        with patch.object(AnalyticsResponseMapper, 'map_to_total_requests_per_day_response', return_value=mock_response):
            response = self.manager.get_total_requests_per_day("2024-01-01", "2024-01-31")

        self.assertIsInstance(response, TotalRequestsPerDayResponse)
        mock_get_requests.assert_called_once_with(start_date="2024-01-01", end_date="2024-01-31", agent_name=None)

    @patch("pygeai.analytics.clients.AnalyticsClient.get_total_requests_per_day")
    def test_get_total_requests_per_day_with_agent_name(self, mock_get_requests):
        mock_response = TotalRequestsPerDayResponse(requestsPerDay=[])
        mock_get_requests.return_value = {"requestsPerDay": []}

        with patch.object(AnalyticsResponseMapper, 'map_to_total_requests_per_day_response', return_value=mock_response):
            response = self.manager.get_total_requests_per_day("2024-01-01", "2024-01-31", agent_name="TestAgent")

        self.assertIsInstance(response, TotalRequestsPerDayResponse)
        mock_get_requests.assert_called_once_with(start_date="2024-01-01", end_date="2024-01-31", agent_name="TestAgent")

    @patch("pygeai.analytics.clients.AnalyticsClient.get_average_cost_per_request")
    def test_get_average_cost_per_request(self, mock_get_cost):
        mock_response = AverageCostPerRequestResponse(averageCost=2.50)
        mock_get_cost.return_value = {"averageCost": 2.50}

        with patch.object(AnalyticsResponseMapper, 'map_to_average_cost_per_request_response', return_value=mock_response):
            response = self.manager.get_average_cost_per_request("2024-01-01", "2024-01-31")

        self.assertIsInstance(response, AverageCostPerRequestResponse)
        self.assertEqual(response.averageCost, 2.50)

    @patch("pygeai.analytics.clients.AnalyticsClient.get_total_tokens")
    def test_get_total_tokens(self, mock_get_tokens):
        mock_response = NumberOfTokensResponse(totalInputTokens=5000, totalOutputTokens=3000, totalTokens=8000)
        mock_get_tokens.return_value = {
            "totalInputTokens": 5000,
            "totalOutputTokens": 3000,
            "totalTokens": 8000
        }

        with patch.object(AnalyticsResponseMapper, 'map_to_total_tokens_response', return_value=mock_response):
            response = self.manager.get_total_tokens("2024-01-01", "2024-01-31")

        self.assertIsInstance(response, NumberOfTokensResponse)
        self.assertEqual(response.totalTokens, 8000)


if __name__ == '__main__':
    unittest.main()
