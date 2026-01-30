from pygeai.analytics.responses import (
    AgentsCreatedAndModifiedResponse, AgentsCreatedAndModifiedPerDayResponse, AgentActivityPerDayItem,
    FlowsCreatedAndModifiedResponse, FlowsCreatedAndModifiedPerDayResponse, FlowActivityPerDayItem,
    ProcessesCreatedAndModifiedResponse, AgentUsagePerUserResponse, AgentUsagePerUserItem,
    AverageCostPerRequestResponse, AverageCostPerUserResponse, AverageCostPerUserPerDateResponse,
    CostPerUserPerDateItem, AverageRequestTimeResponse, AverageRequestsPerDayResponse,
    AverageRequestsPerUserResponse, AverageRequestsPerUserPerDateResponse, RequestsPerUserPerDateItem,
    AverageTokensPerRequestResponse, AverageUsersPerAgentResponse, UsersPerAgentItem,
    AverageUsersPerProjectResponse, UsersPerProjectItem, NumberOfTokensResponse,
    NumberOfTokensPerAgentResponse, TokensPerAgentItem, NumberOfTokensPerDayResponse, TokensPerDayItem,
    OverallErrorRateResponse, Top10AgentsByRequestsResponse, AgentByRequestsItem,
    Top10AgentsByTokensResponse, AgentByTokensItem, Top10UsersByCostResponse, UserByCostItem,
    Top10UsersByRequestsResponse, UserByRequestsItem, TotalActiveAgentsResponse,
    TotalActiveProjectsResponse, TotalActiveUsersResponse, TotalCostResponse,
    TotalCostPerDayResponse, CostPerDayItem, TotalRequestTimeResponse, TotalRequestsResponse,
    TotalRequestsPerDayResponse, RequestsPerDayItem, TotalRequestsWithErrorResponse, TotalTokensResponse
)


class AnalyticsResponseMapper:

    @classmethod
    def map_to_agents_created_and_modified_response(cls, data: dict) -> AgentsCreatedAndModifiedResponse:
        return AgentsCreatedAndModifiedResponse(
            createdAgents=data.get("createdAgents", 0),
            modifiedAgents=data.get("modifiedAgents", 0)
        )

    @classmethod
    def map_to_agents_created_and_modified_per_day_response(cls, data: dict) -> AgentsCreatedAndModifiedPerDayResponse:
        items_data = data.get("agentsCreatedAndModifiedPerDay", [])
        items = [AgentActivityPerDayItem.model_validate(item) for item in items_data]
        return AgentsCreatedAndModifiedPerDayResponse(agentsCreatedAndModifiedPerDay=items)

    @classmethod
    def map_to_flows_created_and_modified_response(cls, data: dict) -> FlowsCreatedAndModifiedResponse:
        return FlowsCreatedAndModifiedResponse(
            createdFlows=data.get("createdFlows", 0),
            modifiedFlows=data.get("modifiedFlows", 0)
        )

    @classmethod
    def map_to_flows_created_and_modified_per_day_response(cls, data: dict) -> FlowsCreatedAndModifiedPerDayResponse:
        items_data = data.get("flowsCreatedAndModifiedPerDay", [])
        items = [FlowActivityPerDayItem.model_validate(item) for item in items_data]
        return FlowsCreatedAndModifiedPerDayResponse(flowsCreatedAndModifiedPerDay=items)

    @classmethod
    def map_to_processes_created_and_modified_response(cls, data: dict) -> ProcessesCreatedAndModifiedResponse:
        return ProcessesCreatedAndModifiedResponse(
            createdProcesses=data.get("createdProcesses", 0),
            modifiedProcesses=data.get("modifiedProcesses", 0)
        )

    @classmethod
    def map_to_agent_usage_per_user_response(cls, data: dict) -> AgentUsagePerUserResponse:
        items_data = data.get("agentUsagePerUser", [])
        items = [AgentUsagePerUserItem.model_validate(item) for item in items_data]
        return AgentUsagePerUserResponse(agentUsagePerUser=items)

    @classmethod
    def map_to_average_cost_per_request_response(cls, data: dict) -> AverageCostPerRequestResponse:
        return AverageCostPerRequestResponse(averageCost=data.get("averageCost", 0.0))

    @classmethod
    def map_to_average_cost_per_user_response(cls, data: dict) -> AverageCostPerUserResponse:
        return AverageCostPerUserResponse(averageCost=data.get("averageCost", 0.0))

    @classmethod
    def map_to_average_cost_per_user_per_date_response(cls, data: dict) -> AverageCostPerUserPerDateResponse:
        items_data = data.get("averageCostPerUserPerDate", [])
        items = [CostPerUserPerDateItem.model_validate(item) for item in items_data]
        return AverageCostPerUserPerDateResponse(averageCostPerUserPerDate=items)

    @classmethod
    def map_to_average_request_time_response(cls, data: dict) -> AverageRequestTimeResponse:
        return AverageRequestTimeResponse(averageTime=data.get("averageTime", 0.0))

    @classmethod
    def map_to_average_requests_per_day_response(cls, data: dict) -> AverageRequestsPerDayResponse:
        return AverageRequestsPerDayResponse(averageRequests=data.get("averageRequests", 0.0))

    @classmethod
    def map_to_average_requests_per_user_response(cls, data: dict) -> AverageRequestsPerUserResponse:
        return AverageRequestsPerUserResponse(averageRequests=data.get("averageRequests", 0.0))

    @classmethod
    def map_to_average_requests_per_user_per_date_response(cls, data: dict) -> AverageRequestsPerUserPerDateResponse:
        items_data = data.get("averageRequestsPerUserPerDate", [])
        items = [RequestsPerUserPerDateItem.model_validate(item) for item in items_data]
        return AverageRequestsPerUserPerDateResponse(averageRequestsPerUserPerDate=items)

    @classmethod
    def map_to_average_tokens_per_request_response(cls, data: dict) -> AverageTokensPerRequestResponse:
        return AverageTokensPerRequestResponse(
            averageInputTokens=data.get("averageInputTokens", 0.0),
            averageOutputTokens=data.get("averageOutputTokens", 0.0),
            averageTotalTokens=data.get("averageTotalTokens", 0.0)
        )

    @classmethod
    def map_to_average_users_per_agent_response(cls, data: dict) -> AverageUsersPerAgentResponse:
        items_data = data.get("averageUsersPerAgent", [])
        items = [UsersPerAgentItem.model_validate(item) for item in items_data]
        return AverageUsersPerAgentResponse(averageUsersPerAgent=items)

    @classmethod
    def map_to_average_users_per_project_response(cls, data: dict) -> AverageUsersPerProjectResponse:
        items_data = data.get("averageUsersPerProject", [])
        items = [UsersPerProjectItem.model_validate(item) for item in items_data]
        return AverageUsersPerProjectResponse(averageUsersPerProject=items)

    @classmethod
    def map_to_number_of_tokens_response(cls, data: dict) -> NumberOfTokensResponse:
        return NumberOfTokensResponse(
            totalInputTokens=data.get("totalInputTokens", 0),
            totalOutputTokens=data.get("totalOutputTokens", 0),
            totalTokens=data.get("totalTokens", 0)
        )

    @classmethod
    def map_to_number_of_tokens_per_agent_response(cls, data: dict) -> NumberOfTokensPerAgentResponse:
        items_data = data.get("tokensPerAgent", [])
        items = [TokensPerAgentItem.model_validate(item) for item in items_data]
        return NumberOfTokensPerAgentResponse(tokensPerAgent=items)

    @classmethod
    def map_to_number_of_tokens_per_day_response(cls, data: dict) -> NumberOfTokensPerDayResponse:
        items_data = data.get("tokensPerDay", [])
        items = [TokensPerDayItem.model_validate(item) for item in items_data]
        return NumberOfTokensPerDayResponse(tokensPerDay=items)

    @classmethod
    def map_to_overall_error_rate_response(cls, data: dict) -> OverallErrorRateResponse:
        return OverallErrorRateResponse(errorRate=data.get("errorRate", 0.0))

    @classmethod
    def map_to_top_10_agents_by_requests_response(cls, data: dict) -> Top10AgentsByRequestsResponse:
        items_data = data.get("topAgents", [])
        items = [AgentByRequestsItem.model_validate(item) for item in items_data]
        return Top10AgentsByRequestsResponse(topAgents=items)

    @classmethod
    def map_to_top_10_agents_by_tokens_response(cls, data: dict) -> Top10AgentsByTokensResponse:
        items_data = data.get("topAgents", [])
        items = [AgentByTokensItem.model_validate(item) for item in items_data]
        return Top10AgentsByTokensResponse(topAgents=items)

    @classmethod
    def map_to_top_10_users_by_cost_response(cls, data: dict) -> Top10UsersByCostResponse:
        items_data = data.get("topUsers", [])
        items = [UserByCostItem.model_validate(item) for item in items_data]
        return Top10UsersByCostResponse(topUsers=items)

    @classmethod
    def map_to_top_10_users_by_requests_response(cls, data: dict) -> Top10UsersByRequestsResponse:
        items_data = data.get("topUsers", [])
        items = [UserByRequestsItem.model_validate(item) for item in items_data]
        return Top10UsersByRequestsResponse(topUsers=items)

    @classmethod
    def map_to_total_active_agents_response(cls, data: dict) -> TotalActiveAgentsResponse:
        return TotalActiveAgentsResponse(totalActiveAgents=data.get("totalActiveAgents", 0))

    @classmethod
    def map_to_total_active_projects_response(cls, data: dict) -> TotalActiveProjectsResponse:
        return TotalActiveProjectsResponse(totalActiveProjects=data.get("totalActiveProjects", 0))

    @classmethod
    def map_to_total_active_users_response(cls, data: dict) -> TotalActiveUsersResponse:
        return TotalActiveUsersResponse(totalActiveUsers=data.get("totalActiveUsers", 0))

    @classmethod
    def map_to_total_cost_response(cls, data: dict) -> TotalCostResponse:
        return TotalCostResponse(totalCost=data.get("totalCost", 0.0))

    @classmethod
    def map_to_total_cost_per_day_response(cls, data: dict) -> TotalCostPerDayResponse:
        items_data = data.get("costPerDay", [])
        items = [CostPerDayItem.model_validate(item) for item in items_data]
        return TotalCostPerDayResponse(costPerDay=items)

    @classmethod
    def map_to_total_request_time_response(cls, data: dict) -> TotalRequestTimeResponse:
        return TotalRequestTimeResponse(totalTime=data.get("totalTime", 0.0))

    @classmethod
    def map_to_total_requests_response(cls, data: dict) -> TotalRequestsResponse:
        return TotalRequestsResponse(totalRequests=data.get("totalRequests", 0))

    @classmethod
    def map_to_total_requests_per_day_response(cls, data: dict) -> TotalRequestsPerDayResponse:
        items_data = data.get("requestsPerDay", [])
        items = [RequestsPerDayItem.model_validate(item) for item in items_data]
        return TotalRequestsPerDayResponse(requestsPerDay=items)

    @classmethod
    def map_to_total_requests_with_error_response(cls, data: dict) -> TotalRequestsWithErrorResponse:
        return TotalRequestsWithErrorResponse(totalRequestsWithError=data.get("totalRequestsWithError", 0))

    @classmethod
    def map_to_total_tokens_response(cls, data: dict) -> TotalTokensResponse:
        return TotalTokensResponse(
            totalInputTokens=data.get("totalInputTokens", 0),
            totalOutputTokens=data.get("totalOutputTokens", 0),
            totalTokens=data.get("totalTokens", 0)
        )
