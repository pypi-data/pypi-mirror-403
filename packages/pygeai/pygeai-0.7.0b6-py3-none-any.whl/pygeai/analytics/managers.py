from pygeai import logger
from pygeai.core.handlers import ErrorHandler
from pygeai.core.common.exceptions import APIError
from pygeai.analytics.clients import AnalyticsClient
from pygeai.analytics.mappers import AnalyticsResponseMapper
from pygeai.analytics.responses import (
    AgentsCreatedAndModifiedResponse, AgentsCreatedAndModifiedPerDayResponse,
    FlowsCreatedAndModifiedResponse, FlowsCreatedAndModifiedPerDayResponse,
    ProcessesCreatedAndModifiedResponse, AgentUsagePerUserResponse,
    AverageCostPerRequestResponse, AverageCostPerUserResponse, AverageCostPerUserPerDateResponse,
    AverageRequestTimeResponse, AverageRequestsPerDayResponse, AverageRequestsPerUserResponse,
    AverageRequestsPerUserPerDateResponse, AverageTokensPerRequestResponse,
    AverageUsersPerAgentResponse, AverageUsersPerProjectResponse, NumberOfTokensResponse,
    NumberOfTokensPerAgentResponse, NumberOfTokensPerDayResponse, OverallErrorRateResponse,
    Top10AgentsByRequestsResponse, Top10AgentsByTokensResponse, Top10UsersByCostResponse,
    Top10UsersByRequestsResponse, TotalActiveAgentsResponse, TotalActiveProjectsResponse,
    TotalActiveUsersResponse, TotalCostResponse, TotalCostPerDayResponse,
    TotalRequestTimeResponse, TotalRequestsResponse, TotalRequestsPerDayResponse,
    TotalRequestsWithErrorResponse, TotalTokensResponse
)


class AnalyticsManager:

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = None):
        self.__analytics_client = AnalyticsClient(api_key=api_key, base_url=base_url, alias=alias)

    def get_agents_created_and_modified(
            self,
            start_date: str,
            end_date: str
    ) -> AgentsCreatedAndModifiedResponse:
        response_data = self.__analytics_client.get_agents_created_and_modified(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving agents created and modified: {error}")
            raise APIError(f"Error received while retrieving agents created and modified: {error}")

        result = AnalyticsResponseMapper.map_to_agents_created_and_modified_response(response_data)
        return result

    def get_agents_created_and_modified_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> AgentsCreatedAndModifiedPerDayResponse:
        response_data = self.__analytics_client.get_agents_created_and_modified_per_day(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving agents created and modified per day: {error}")
            raise APIError(f"Error received while retrieving agents created and modified per day: {error}")

        result = AnalyticsResponseMapper.map_to_agents_created_and_modified_per_day_response(response_data)
        return result

    def get_flows_created_and_modified(
            self,
            start_date: str,
            end_date: str
    ) -> FlowsCreatedAndModifiedResponse:
        response_data = self.__analytics_client.get_flows_created_and_modified(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving flows created and modified: {error}")
            raise APIError(f"Error received while retrieving flows created and modified: {error}")

        result = AnalyticsResponseMapper.map_to_flows_created_and_modified_response(response_data)
        return result

    def get_flows_created_and_modified_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> FlowsCreatedAndModifiedPerDayResponse:
        response_data = self.__analytics_client.get_flows_created_and_modified_per_day(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving flows created and modified per day: {error}")
            raise APIError(f"Error received while retrieving flows created and modified per day: {error}")

        result = AnalyticsResponseMapper.map_to_flows_created_and_modified_per_day_response(response_data)
        return result

    def get_processes_created_and_modified(
            self,
            start_date: str,
            end_date: str
    ) -> ProcessesCreatedAndModifiedResponse:
        response_data = self.__analytics_client.get_processes_created_and_modified(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving processes created and modified: {error}")
            raise APIError(f"Error received while retrieving processes created and modified: {error}")

        result = AnalyticsResponseMapper.map_to_processes_created_and_modified_response(response_data)
        return result

    def get_agent_usage_per_user(
            self,
            start_date: str,
            end_date: str
    ) -> AgentUsagePerUserResponse:
        response_data = self.__analytics_client.get_agent_usage_per_user(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving agent usage per user: {error}")
            raise APIError(f"Error received while retrieving agent usage per user: {error}")

        result = AnalyticsResponseMapper.map_to_agent_usage_per_user_response(response_data)
        return result

    def get_average_cost_per_request(
            self,
            start_date: str,
            end_date: str
    ) -> AverageCostPerRequestResponse:
        response_data = self.__analytics_client.get_average_cost_per_request(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average cost per request: {error}")
            raise APIError(f"Error received while retrieving average cost per request: {error}")

        result = AnalyticsResponseMapper.map_to_average_cost_per_request_response(response_data)
        return result

    def get_average_cost_per_user(
            self,
            start_date: str,
            end_date: str
    ) -> AverageCostPerUserResponse:
        response_data = self.__analytics_client.get_average_cost_per_user(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average cost per user: {error}")
            raise APIError(f"Error received while retrieving average cost per user: {error}")

        result = AnalyticsResponseMapper.map_to_average_cost_per_user_response(response_data)
        return result

    def get_average_cost_per_user_per_date(
            self,
            start_date: str,
            end_date: str
    ) -> AverageCostPerUserPerDateResponse:
        response_data = self.__analytics_client.get_average_cost_per_user_per_date(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average cost per user per date: {error}")
            raise APIError(f"Error received while retrieving average cost per user per date: {error}")

        result = AnalyticsResponseMapper.map_to_average_cost_per_user_per_date_response(response_data)
        return result

    def get_average_request_time(
            self,
            start_date: str,
            end_date: str
    ) -> AverageRequestTimeResponse:
        response_data = self.__analytics_client.get_average_request_time(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average request time: {error}")
            raise APIError(f"Error received while retrieving average request time: {error}")

        result = AnalyticsResponseMapper.map_to_average_request_time_response(response_data)
        return result

    def get_average_requests_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> AverageRequestsPerDayResponse:
        response_data = self.__analytics_client.get_average_requests_per_day(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average requests per day: {error}")
            raise APIError(f"Error received while retrieving average requests per day: {error}")

        result = AnalyticsResponseMapper.map_to_average_requests_per_day_response(response_data)
        return result

    def get_average_requests_per_user(
            self,
            start_date: str,
            end_date: str
    ) -> AverageRequestsPerUserResponse:
        response_data = self.__analytics_client.get_average_requests_per_user(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average requests per user: {error}")
            raise APIError(f"Error received while retrieving average requests per user: {error}")

        result = AnalyticsResponseMapper.map_to_average_requests_per_user_response(response_data)
        return result

    def get_average_requests_per_user_per_date(
            self,
            start_date: str,
            end_date: str
    ) -> AverageRequestsPerUserPerDateResponse:
        response_data = self.__analytics_client.get_average_requests_per_user_per_date(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average requests per user per date: {error}")
            raise APIError(f"Error received while retrieving average requests per user per date: {error}")

        result = AnalyticsResponseMapper.map_to_average_requests_per_user_per_date_response(response_data)
        return result

    def get_average_tokens_per_request(
            self,
            start_date: str,
            end_date: str
    ) -> AverageTokensPerRequestResponse:
        response_data = self.__analytics_client.get_average_tokens_per_request(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average tokens per request: {error}")
            raise APIError(f"Error received while retrieving average tokens per request: {error}")

        result = AnalyticsResponseMapper.map_to_average_tokens_per_request_response(response_data)
        return result

    def get_average_users_per_agent(
            self,
            start_date: str,
            end_date: str
    ) -> AverageUsersPerAgentResponse:
        response_data = self.__analytics_client.get_average_users_per_agent(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average users per agent: {error}")
            raise APIError(f"Error received while retrieving average users per agent: {error}")

        result = AnalyticsResponseMapper.map_to_average_users_per_agent_response(response_data)
        return result

    def get_average_users_per_project(
            self,
            start_date: str,
            end_date: str
    ) -> AverageUsersPerProjectResponse:
        response_data = self.__analytics_client.get_average_users_per_project(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving average users per project: {error}")
            raise APIError(f"Error received while retrieving average users per project: {error}")

        result = AnalyticsResponseMapper.map_to_average_users_per_project_response(response_data)
        return result

    def get_number_of_tokens(
            self,
            start_date: str,
            end_date: str
    ) -> NumberOfTokensResponse:
        response_data = self.__analytics_client.get_number_of_tokens(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving number of tokens: {error}")
            raise APIError(f"Error received while retrieving number of tokens: {error}")

        result = AnalyticsResponseMapper.map_to_number_of_tokens_response(response_data)
        return result

    def get_number_of_tokens_per_agent(
            self,
            start_date: str,
            end_date: str
    ) -> NumberOfTokensPerAgentResponse:
        response_data = self.__analytics_client.get_number_of_tokens_per_agent(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving number of tokens per agent: {error}")
            raise APIError(f"Error received while retrieving number of tokens per agent: {error}")

        result = AnalyticsResponseMapper.map_to_number_of_tokens_per_agent_response(response_data)
        return result

    def get_number_of_tokens_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> NumberOfTokensPerDayResponse:
        response_data = self.__analytics_client.get_number_of_tokens_per_day(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving number of tokens per day: {error}")
            raise APIError(f"Error received while retrieving number of tokens per day: {error}")

        result = AnalyticsResponseMapper.map_to_number_of_tokens_per_day_response(response_data)
        return result

    def get_overall_error_rate(
            self,
            start_date: str,
            end_date: str
    ) -> OverallErrorRateResponse:
        response_data = self.__analytics_client.get_overall_error_rate(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving overall error rate: {error}")
            raise APIError(f"Error received while retrieving overall error rate: {error}")

        result = AnalyticsResponseMapper.map_to_overall_error_rate_response(response_data)
        return result

    def get_top_10_agents_by_requests(
            self,
            start_date: str,
            end_date: str
    ) -> Top10AgentsByRequestsResponse:
        response_data = self.__analytics_client.get_top_10_agents_by_requests(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving top 10 agents by requests: {error}")
            raise APIError(f"Error received while retrieving top 10 agents by requests: {error}")

        result = AnalyticsResponseMapper.map_to_top_10_agents_by_requests_response(response_data)
        return result

    def get_top_10_agents_by_tokens(
            self,
            start_date: str,
            end_date: str
    ) -> Top10AgentsByTokensResponse:
        response_data = self.__analytics_client.get_top_10_agents_by_tokens(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving top 10 agents by tokens: {error}")
            raise APIError(f"Error received while retrieving top 10 agents by tokens: {error}")

        result = AnalyticsResponseMapper.map_to_top_10_agents_by_tokens_response(response_data)
        return result

    def get_top_10_users_by_cost(
            self,
            start_date: str,
            end_date: str
    ) -> Top10UsersByCostResponse:
        response_data = self.__analytics_client.get_top_10_users_by_cost(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving top 10 users by cost: {error}")
            raise APIError(f"Error received while retrieving top 10 users by cost: {error}")

        result = AnalyticsResponseMapper.map_to_top_10_users_by_cost_response(response_data)
        return result

    def get_top_10_users_by_requests(
            self,
            start_date: str,
            end_date: str
    ) -> Top10UsersByRequestsResponse:
        response_data = self.__analytics_client.get_top_10_users_by_requests(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving top 10 users by requests: {error}")
            raise APIError(f"Error received while retrieving top 10 users by requests: {error}")

        result = AnalyticsResponseMapper.map_to_top_10_users_by_requests_response(response_data)
        return result

    def get_total_active_agents(
            self,
            start_date: str,
            end_date: str
    ) -> TotalActiveAgentsResponse:
        response_data = self.__analytics_client.get_total_active_agents(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total active agents: {error}")
            raise APIError(f"Error received while retrieving total active agents: {error}")

        result = AnalyticsResponseMapper.map_to_total_active_agents_response(response_data)
        return result

    def get_total_active_projects(
            self,
            start_date: str,
            end_date: str
    ) -> TotalActiveProjectsResponse:
        response_data = self.__analytics_client.get_total_active_projects(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total active projects: {error}")
            raise APIError(f"Error received while retrieving total active projects: {error}")

        result = AnalyticsResponseMapper.map_to_total_active_projects_response(response_data)
        return result

    def get_total_active_users(
            self,
            start_date: str,
            end_date: str
    ) -> TotalActiveUsersResponse:
        response_data = self.__analytics_client.get_total_active_users(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total active users: {error}")
            raise APIError(f"Error received while retrieving total active users: {error}")

        result = AnalyticsResponseMapper.map_to_total_active_users_response(response_data)
        return result

    def get_total_cost(
            self,
            start_date: str,
            end_date: str
    ) -> TotalCostResponse:
        response_data = self.__analytics_client.get_total_cost(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total cost: {error}")
            raise APIError(f"Error received while retrieving total cost: {error}")

        result = AnalyticsResponseMapper.map_to_total_cost_response(response_data)
        return result

    def get_total_cost_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> TotalCostPerDayResponse:
        response_data = self.__analytics_client.get_total_cost_per_day(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total cost per day: {error}")
            raise APIError(f"Error received while retrieving total cost per day: {error}")

        result = AnalyticsResponseMapper.map_to_total_cost_per_day_response(response_data)
        return result

    def get_total_request_time(
            self,
            start_date: str,
            end_date: str
    ) -> TotalRequestTimeResponse:
        response_data = self.__analytics_client.get_total_request_time(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total request time: {error}")
            raise APIError(f"Error received while retrieving total request time: {error}")

        result = AnalyticsResponseMapper.map_to_total_request_time_response(response_data)
        return result

    def get_total_requests(
            self,
            start_date: str,
            end_date: str
    ) -> TotalRequestsResponse:
        response_data = self.__analytics_client.get_total_requests(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total requests: {error}")
            raise APIError(f"Error received while retrieving total requests: {error}")

        result = AnalyticsResponseMapper.map_to_total_requests_response(response_data)
        return result

    def get_total_requests_per_day(
            self,
            start_date: str,
            end_date: str,
            agent_name: str = None
    ) -> TotalRequestsPerDayResponse:
        response_data = self.__analytics_client.get_total_requests_per_day(
            start_date=start_date,
            end_date=end_date,
            agent_name=agent_name
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total requests per day: {error}")
            raise APIError(f"Error received while retrieving total requests per day: {error}")

        result = AnalyticsResponseMapper.map_to_total_requests_per_day_response(response_data)
        return result

    def get_total_requests_with_error(
            self,
            start_date: str,
            end_date: str
    ) -> TotalRequestsWithErrorResponse:
        response_data = self.__analytics_client.get_total_requests_with_error(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total requests with error: {error}")
            raise APIError(f"Error received while retrieving total requests with error: {error}")

        result = AnalyticsResponseMapper.map_to_total_requests_with_error_response(response_data)
        return result

    def get_total_tokens(
            self,
            start_date: str,
            end_date: str
    ) -> TotalTokensResponse:
        response_data = self.__analytics_client.get_total_tokens(
            start_date=start_date,
            end_date=end_date
        )
        if ErrorHandler.has_errors(response_data):
            error = ErrorHandler.extract_error(response_data)
            logger.error(f"Error received while retrieving total tokens: {error}")
            raise APIError(f"Error received while retrieving total tokens: {error}")

        result = AnalyticsResponseMapper.map_to_total_tokens_response(response_data)
        return result
