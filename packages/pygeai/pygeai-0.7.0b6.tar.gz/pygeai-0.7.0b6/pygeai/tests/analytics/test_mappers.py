import unittest
from pygeai.analytics.mappers import AnalyticsResponseMapper
from pygeai.analytics.responses import (
    AgentsCreatedAndModifiedResponse, AgentsCreatedAndModifiedPerDayResponse,
    FlowsCreatedAndModifiedResponse, AverageCostPerRequestResponse,
    TotalRequestsPerDayResponse, NumberOfTokensResponse
)


class TestAnalyticsResponseMapper(unittest.TestCase):

    def test_map_to_agents_created_and_modified_response(self):
        data = {
            "createdAgents": 15,
            "modifiedAgents": 8
        }
        response = AnalyticsResponseMapper.map_to_agents_created_and_modified_response(data)
        self.assertIsInstance(response, AgentsCreatedAndModifiedResponse)
        self.assertEqual(response.createdAgents, 15)
        self.assertEqual(response.modifiedAgents, 8)

    def test_map_to_agents_created_and_modified_per_day_response(self):
        data = {
            "agentsCreatedAndModifiedPerDay": [
                {"date": "2024-01-01", "createdAgents": 5, "modifiedAgents": 2},
                {"date": "2024-01-02", "createdAgents": 3, "modifiedAgents": 1}
            ]
        }
        response = AnalyticsResponseMapper.map_to_agents_created_and_modified_per_day_response(data)
        self.assertIsInstance(response, AgentsCreatedAndModifiedPerDayResponse)
        self.assertEqual(len(response.agentsCreatedAndModifiedPerDay), 2)
        self.assertEqual(response.agentsCreatedAndModifiedPerDay[0].date, "2024-01-01")

    def test_map_to_flows_created_and_modified_response(self):
        data = {
            "createdFlows": 10,
            "modifiedFlows": 5
        }
        response = AnalyticsResponseMapper.map_to_flows_created_and_modified_response(data)
        self.assertIsInstance(response, FlowsCreatedAndModifiedResponse)
        self.assertEqual(response.createdFlows, 10)
        self.assertEqual(response.modifiedFlows, 5)

    def test_map_to_average_cost_per_request_response(self):
        data = {
            "averageCost": 3.25
        }
        response = AnalyticsResponseMapper.map_to_average_cost_per_request_response(data)
        self.assertIsInstance(response, AverageCostPerRequestResponse)
        self.assertEqual(response.averageCost, 3.25)

    def test_map_to_total_requests_per_day_response(self):
        data = {
            "requestsPerDay": [
                {"date": "2024-01-01", "totalRequests": 150, "totalRequestsWithError": 10},
                {"date": "2024-01-02", "totalRequests": 200, "totalRequestsWithError": 5}
            ]
        }
        response = AnalyticsResponseMapper.map_to_total_requests_per_day_response(data)
        self.assertIsInstance(response, TotalRequestsPerDayResponse)
        self.assertEqual(len(response.requestsPerDay), 2)
        self.assertEqual(response.requestsPerDay[0].totalRequests, 150)

    def test_map_to_number_of_tokens_response(self):
        data = {
            "totalInputTokens": 5000,
            "totalOutputTokens": 3000,
            "totalTokens": 8000
        }
        response = AnalyticsResponseMapper.map_to_number_of_tokens_response(data)
        self.assertIsInstance(response, NumberOfTokensResponse)
        self.assertEqual(response.totalInputTokens, 5000)
        self.assertEqual(response.totalOutputTokens, 3000)
        self.assertEqual(response.totalTokens, 8000)

    def test_map_with_missing_fields(self):
        data = {}
        response = AnalyticsResponseMapper.map_to_agents_created_and_modified_response(data)
        self.assertEqual(response.createdAgents, 0)
        self.assertEqual(response.modifiedAgents, 0)


if __name__ == '__main__':
    unittest.main()
