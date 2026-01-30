from pygeai import logger
from pygeai.admin.clients import AdminClient
from pygeai.analytics.endpoints import (
    GET_AGENTS_CREATED_AND_MODIFIED_V1, GET_AGENTS_CREATED_AND_MODIFIED_PER_DAY_V1,
    GET_FLOWS_CREATED_AND_MODIFIED_V1, GET_FLOWS_CREATED_AND_MODIFIED_PER_DAY_V1,
    GET_PROCESSES_CREATED_AND_MODIFIED_V1, GET_AGENT_USAGE_PER_USER_V1,
    GET_AVERAGE_COST_PER_REQUEST_V1, GET_AVERAGE_COST_PER_USER_V1,
    GET_AVERAGE_COST_PER_USER_PER_DATE_V1, GET_AVERAGE_REQUEST_TIME_V1,
    GET_AVERAGE_REQUESTS_PER_DAY_V1, GET_AVERAGE_REQUESTS_PER_USER_V1,
    GET_AVERAGE_REQUESTS_PER_USER_PER_DATE_V1, GET_AVERAGE_TOKENS_PER_REQUEST_V1,
    GET_AVERAGE_USERS_PER_AGENT_V1, GET_AVERAGE_USERS_PER_PROJECT_V1,
    GET_NUMBER_OF_TOKENS_V1, GET_NUMBER_OF_TOKENS_PER_AGENT_V1,
    GET_NUMBER_OF_TOKENS_PER_DAY_V1, GET_OVERALL_ERROR_RATE_V1,
    GET_TOP_10_AGENTS_BY_REQUESTS_V1, GET_TOP_10_AGENTS_BY_TOKENS_V1,
    GET_TOP_10_USERS_BY_COST_V1, GET_TOP_10_USERS_BY_REQUESTS_V1,
    GET_TOTAL_ACTIVE_AGENTS_V1, GET_TOTAL_ACTIVE_PROJECTS_V1,
    GET_TOTAL_ACTIVE_USERS_V1, GET_TOTAL_COST_V1, GET_TOTAL_COST_PER_DAY_V1,
    GET_TOTAL_REQUEST_TIME_V1, GET_TOTAL_REQUESTS_V1, GET_TOTAL_REQUESTS_PER_DAY_V1,
    GET_TOTAL_REQUESTS_WITH_ERROR_V1, GET_TOTAL_TOKENS_V1
)
from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import APIError
from pygeai.core.utils.validators import validate_status_code
from pygeai.core.utils.parsers import parse_json_response


class AnalyticsClient(BaseClient):

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = None, *,
                 access_token: str = None, project_id: str = None, organization_id: str = None):
        super().__init__(api_key, base_url, alias, access_token=access_token, project_id=project_id)
        ids = self.__get_project_and_organization_ids(api_key, base_url, alias, project_id, organization_id)
        self.project_id = ids.get("projectId")
        self.organization_id = ids.get("organizationId")
        if self.project_id and not self.api_service.project_id:
            self.api_service.project_id = self.project_id

    def __get_project_and_organization_ids(self, api_key: str = None, base_url: str = None, alias: str = None,
                                           project_id: str = None, organization_id: str = None):
        if project_id and organization_id:
            return {"projectId": project_id, "organizationId": organization_id}
        
        response = None
        try:
            response = AdminClient(api_key=api_key, base_url=base_url, alias=alias).validate_api_token()
            return {
                "projectId": project_id if project_id else response.get("projectId"),
                "organizationId": organization_id if organization_id else response.get("organizationId")
            }
        except Exception as e:
            logger.error(f"Error retrieving project_id and organization_id from GEAI. Response: {response}: {e}")
            raise APIError(f"Error retrieving project_id and organization_id from GEAI: {e}")

    def __build_headers(self):
        return {
            "Authorization": f"Bearer {self.api_service.token}",
            "OrganizationId": self.organization_id,
            "ProjectId": self.project_id
        }

    def get_agents_created_and_modified(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AGENTS_CREATED_AND_MODIFIED_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get agents created and modified")

    def get_agents_created_and_modified_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AGENTS_CREATED_AND_MODIFIED_PER_DAY_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get agents created and modified per day")

    def get_flows_created_and_modified(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_FLOWS_CREATED_AND_MODIFIED_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get flows created and modified")

    def get_flows_created_and_modified_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_FLOWS_CREATED_AND_MODIFIED_PER_DAY_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get flows created and modified per day")

    def get_processes_created_and_modified(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_PROCESSES_CREATED_AND_MODIFIED_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get processes created and modified")

    def get_agent_usage_per_user(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AGENT_USAGE_PER_USER_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get agent usage per user")

    def get_average_cost_per_request(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_COST_PER_REQUEST_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average cost per request")

    def get_average_cost_per_user(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_COST_PER_USER_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average cost per user")

    def get_average_cost_per_user_per_date(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_COST_PER_USER_PER_DATE_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average cost per user per date")

    def get_average_request_time(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_REQUEST_TIME_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average request time")

    def get_average_requests_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_REQUESTS_PER_DAY_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average requests per day")

    def get_average_requests_per_user(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_REQUESTS_PER_USER_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average requests per user")

    def get_average_requests_per_user_per_date(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_REQUESTS_PER_USER_PER_DATE_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average requests per user per date")

    def get_average_tokens_per_request(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_TOKENS_PER_REQUEST_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average tokens per request")

    def get_average_users_per_agent(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_USERS_PER_AGENT_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average users per agent")

    def get_average_users_per_project(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_AVERAGE_USERS_PER_PROJECT_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get average users per project")

    def get_number_of_tokens(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_NUMBER_OF_TOKENS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get number of tokens")

    def get_number_of_tokens_per_agent(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_NUMBER_OF_TOKENS_PER_AGENT_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get number of tokens per agent")

    def get_number_of_tokens_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_NUMBER_OF_TOKENS_PER_DAY_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get number of tokens per day")

    def get_overall_error_rate(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_OVERALL_ERROR_RATE_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get overall error rate")

    def get_top_10_agents_by_requests(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOP_10_AGENTS_BY_REQUESTS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get top 10 agents by requests")

    def get_top_10_agents_by_tokens(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOP_10_AGENTS_BY_TOKENS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get top 10 agents by tokens")

    def get_top_10_users_by_cost(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOP_10_USERS_BY_COST_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get top 10 users by cost")

    def get_top_10_users_by_requests(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOP_10_USERS_BY_REQUESTS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get top 10 users by requests")

    def get_total_active_agents(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_ACTIVE_AGENTS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total active agents")

    def get_total_active_projects(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_ACTIVE_PROJECTS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total active projects")

    def get_total_active_users(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_ACTIVE_USERS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total active users")

    def get_total_cost(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_COST_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total cost")

    def get_total_cost_per_day(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_COST_PER_DAY_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total cost per day")

    def get_total_request_time(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_REQUEST_TIME_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total request time")

    def get_total_requests(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_REQUESTS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total requests")

    def get_total_requests_per_day(
            self,
            start_date: str,
            end_date: str,
            agent_name: str = None
    ) -> dict:
        params = {"startDate": start_date, "endDate": end_date}
        if agent_name:
            params["agentName"] = agent_name
        response = self.api_service.get(
            endpoint=GET_TOTAL_REQUESTS_PER_DAY_V1,
            headers=self.__build_headers(),
            params=params
        )
        validate_status_code(response)
        return parse_json_response(response, "get total requests per day")

    def get_total_requests_with_error(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_REQUESTS_WITH_ERROR_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total requests with error")

    def get_total_tokens(
            self,
            start_date: str,
            end_date: str
    ) -> dict:
        response = self.api_service.get(
            endpoint=GET_TOTAL_TOKENS_V1,
            headers=self.__build_headers(),
            params={"startDate": start_date, "endDate": end_date}
        )
        validate_status_code(response)
        return parse_json_response(response, "get total tokens")
