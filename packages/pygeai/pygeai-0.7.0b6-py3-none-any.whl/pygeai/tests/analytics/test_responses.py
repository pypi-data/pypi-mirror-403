import unittest
from pygeai.analytics.responses import (
    AgentsCreatedAndModifiedResponse, AgentActivityPerDayItem, AgentsCreatedAndModifiedPerDayResponse,
    FlowsCreatedAndModifiedResponse, FlowActivityPerDayItem, FlowsCreatedAndModifiedPerDayResponse,
    ProcessesCreatedAndModifiedResponse, AgentUsagePerUserItem, AgentUsagePerUserResponse,
    AverageCostPerRequestResponse, AverageCostPerUserResponse, TotalRequestsPerDayResponse,
    RequestsPerDayItem
)


class TestAnalyticsResponses(unittest.TestCase):

    def test_agents_created_and_modified_response(self):
        response = AgentsCreatedAndModifiedResponse(createdAgents=10, modifiedAgents=5)
        self.assertEqual(response.createdAgents, 10)
        self.assertEqual(response.modifiedAgents, 5)

    def test_agents_created_and_modified_per_day_response(self):
        items = [
            AgentActivityPerDayItem(date="2024-01-01", createdAgents=5, modifiedAgents=2),
            AgentActivityPerDayItem(date="2024-01-02", createdAgents=3, modifiedAgents=1)
        ]
        response = AgentsCreatedAndModifiedPerDayResponse(agentsCreatedAndModifiedPerDay=items)
        self.assertEqual(len(response.agentsCreatedAndModifiedPerDay), 2)
        self.assertEqual(response.agentsCreatedAndModifiedPerDay[0].date, "2024-01-01")

    def test_flows_created_and_modified_response(self):
        response = FlowsCreatedAndModifiedResponse(createdFlows=8, modifiedFlows=3)
        self.assertEqual(response.createdFlows, 8)
        self.assertEqual(response.modifiedFlows, 3)

    def test_flows_created_and_modified_per_day_response(self):
        items = [
            FlowActivityPerDayItem(date="2024-01-01", createdFlows=4, modifiedFlows=1)
        ]
        response = FlowsCreatedAndModifiedPerDayResponse(flowsCreatedAndModifiedPerDay=items)
        self.assertEqual(len(response.flowsCreatedAndModifiedPerDay), 1)

    def test_processes_created_and_modified_response(self):
        response = ProcessesCreatedAndModifiedResponse(createdProcesses=12, modifiedProcesses=6)
        self.assertEqual(response.createdProcesses, 12)
        self.assertEqual(response.modifiedProcesses, 6)

    def test_agent_usage_per_user_response(self):
        items = [
            AgentUsagePerUserItem(userId="user1", userName="John Doe", totalCost=100.50, totalRequests=50, totalTokens=1000)
        ]
        response = AgentUsagePerUserResponse(agentUsagePerUser=items)
        self.assertEqual(len(response.agentUsagePerUser), 1)
        self.assertEqual(response.agentUsagePerUser[0].userId, "user1")
        self.assertEqual(response.agentUsagePerUser[0].totalCost, 100.50)

    def test_average_cost_per_request_response(self):
        response = AverageCostPerRequestResponse(averageCost=2.50)
        self.assertEqual(response.averageCost, 2.50)

    def test_average_cost_per_user_response(self):
        response = AverageCostPerUserResponse(averageCost=150.75)
        self.assertEqual(response.averageCost, 150.75)

    def test_total_requests_per_day_response(self):
        items = [
            RequestsPerDayItem(date="2024-01-01", totalRequests=100, totalRequestsWithError=5),
            RequestsPerDayItem(date="2024-01-02", totalRequests=120, totalRequestsWithError=3)
        ]
        response = TotalRequestsPerDayResponse(requestsPerDay=items)
        self.assertEqual(len(response.requestsPerDay), 2)
        self.assertEqual(response.requestsPerDay[0].totalRequests, 100)
        self.assertEqual(response.requestsPerDay[1].totalRequestsWithError, 3)


if __name__ == '__main__':
    unittest.main()
