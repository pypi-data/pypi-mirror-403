from pygeai import logger
from pygeai.admin.clients import AdminClient
from pygeai.core.common.exceptions import APIError
from pygeai.organization.endpoints import GET_ASSISTANT_LIST_V1, GET_PROJECT_LIST_V1, GET_PROJECT_V1, \
    CREATE_PROJECT_V1, UPDATE_PROJECT_V1, DELETE_PROJECT_V1, GET_PROJECT_TOKENS_V1, GET_REQUEST_DATA_V1, \
    GET_MEMBERSHIPS_V2, GET_PROJECT_MEMBERSHIPS_V2, GET_PROJECT_ROLES_V2, GET_PROJECT_MEMBERS_V2, \
    GET_ORGANIZATION_MEMBERS_V2, GET_PLUGIN_RUNTIME_POLICIES_V2, ADD_PROJECT_MEMBER_V2, CREATE_ORGANIZATION_V2, \
    GET_ORGANIZATION_LIST_V2, DELETE_ORGANIZATION_V2
from pygeai.core.base.clients import BaseClient
from pygeai.core.utils.validators import validate_status_code
from pygeai.core.utils.parsers import parse_json_response


class OrganizationClient(BaseClient):

    def _get_token_information(self):
        return AdminClient(self.api_service.token, base_url=self.api_service.base_url).validate_api_token()

    def _get_project_id(self):
        response = None
        try:
            response = self._get_token_information()
            return response.get("projectId")
        except Exception as e:
            logger.error(f"Error retrieving project_id from GEAI. Response: {response}: {e}")
            raise APIError(f"Error retrieving project_id from GEAI: {e}")

    def _get_organization_id(self):
        response = None
        try:
            response = self._get_token_information()
            return response.get("organizationId")
        except Exception as e:
            logger.error(f"Error retrieving organization_id from GEAI. Response: {response}: {e}")
            raise APIError(f"Error retrieving organization_id from GEAI: {e}")

    def get_assistant_list(
            self,
            detail: str = "summary"
    ) -> dict:
        """
        Retrieves a list of assistants with the specified level of detail.

        :param detail: str - The level of detail to include in the response. Possible values:
            - "summary": Provides a summarized list of assistants. (Default)
            - "full": Provides a detailed list of assistants. (Optional)
        :return: AssistantListResponse - The API response containing the list of assistants and the project.
        """
        response = self.api_service.get(endpoint=GET_ASSISTANT_LIST_V1, params={"detail": detail})
        validate_status_code(response)
        return parse_json_response(response, "get assistant list")

    def get_project_list(
            self,
            detail: str = "summary",
            name: str = None
    ) -> dict:
        """
        Retrieves a list of projects based on the specified level of detail and optional project name.

        :param detail: str - The level of detail to include in the response. Possible values:
            - "summary": Provides a summarized list of projects. (Default)
            - "full": Provides a detailed list of projects. (Optional)
        :param name: str - (Optional) Filters the project list by an exact project name match.
        :return: dict - The API response containing the list of projects in JSON format.
        """
        if detail and name:
            response = self.api_service.get(
                endpoint=GET_PROJECT_LIST_V1,
                params={
                    "detail": detail,
                    "name": name
                }
            )
        else:
            response = self.api_service.get(
                endpoint=GET_PROJECT_LIST_V1,
                params={
                    "detail": detail
                }
            )
        validate_status_code(response)
        return parse_json_response(response, "get project list")

    def get_project_data(
            self,
            project_id: str
    ) -> dict:
        """
        Retrieves detailed information about a specific project based on its unique project ID.

        :param project_id: str - The GUID of the project (required).
        :return: dict - The API response containing the project details in JSON format.
        """
        endpoint = GET_PROJECT_V1.format(id=project_id)
        response = self.api_service.get(
            endpoint=endpoint
        )
        validate_status_code(response)
        return parse_json_response(response, "get project data for ID", project_id=project_id)

    def create_project(
            self,
            name: str,
            email: str,
            description: str = None,
            usage_limit: dict = None
    ) -> dict:
        """
        Creates a new project with the provided details. Optionally, a usage limit can be specified.

        :param name: str - The name of the new project (required).
        :param email: str - The email address of the project administrator (required).
        :param description: str - A description of the new project (optional).
        :param usage_limit: dict - A dictionary specifying the usage limits for the project. If provided, it must include usage type and thresholds (optional).
        :return: dict - The API response with details of the created project in JSON format.
        """
        if usage_limit and any(usage_limit):
            response = self.api_service.post(
                endpoint=CREATE_PROJECT_V1,
                data={
                    "name": name,
                    "administratorUserEmail": email,
                    "description": description,
                    "usageLimit": usage_limit
                }
            )
        else:
            response = self.api_service.post(
                endpoint=CREATE_PROJECT_V1,
                data={
                    "name": name,
                    "administratorUserEmail": email,
                    "description": description
                }
            )
        validate_status_code(response)
        return parse_json_response(response, "create project with name", name=name)

    def update_project(
            self,
            project_id: str,
            name: str,
            description: str = None
    ) -> dict:
        """
        Updates an existing project with the provided details.

        :param project_id: str - The unique identifier (GUID) of the project to update (required).
        :param name: str - The new name for the project (required).
        :param description: str - A new description for the project (optional).
        :return: dict - The API response containing the updated project details in JSON format.
        """
        endpoint = UPDATE_PROJECT_V1.format(id=project_id)
        response = self.api_service.put(
            endpoint=endpoint,
            data={
                "name": name,
                "description": description
            }
        )
        validate_status_code(response)
        return parse_json_response(response, "update project with ID", project_id=project_id)

    def delete_project(
            self,
            project_id
    ) -> dict:
        """
        Deletes an existing project using its unique identifier.

        :param project_id: str - The unique identifier (GUID) of the project to delete (required).
        :return: dict - The API response confirming the deletion of the project, in JSON format.
        """
        endpoint = DELETE_PROJECT_V1.format(id=project_id)
        response = self.api_service.delete(endpoint=endpoint)
        validate_status_code(response)
        return parse_json_response(response, "delete project with ID", project_id=project_id)

    def get_project_tokens(
            self,
            project_id
    ) -> dict:
        """
        Retrieves the tokens associated with a specific project using its unique identifier.

        :param project_id: str - The unique identifier (GUID) of the project (required).
        :return: dict - The API response containing the tokens associated with the project, in JSON format.
        """
        endpoint = GET_PROJECT_TOKENS_V1.format(id=project_id)
        response = self.api_service.get(endpoint=endpoint)
        validate_status_code(response)
        return parse_json_response(response, "get tokens for project with ID", project_id=project_id)

    def export_request_data(
            self,
            assistant_name: str = None,
            status: str = None,
            skip: int = 0,
            count: int = 0
    ) -> dict:
        """
        Exports request data based on the specified filters such as assistant name, status, and pagination parameters.

        :param assistant_name: str - The name of the assistant to filter the request data by (optional).
        :param status: str - The status to filter the request data by (optional).
        :param skip: int - The number of entries to skip in the response (default is 0).
        :param count: int - The number of entries to retrieve in the response (default is 0).
        :return: dict - The API response containing the requested data, in JSON format.
        """
        response = self.api_service.get(
            endpoint=GET_REQUEST_DATA_V1,
            params={
                "assistantName": assistant_name,
                "status": status,
                "skip": skip,
                "count": count
            }
        )
        validate_status_code(response)
        return parse_json_response(response, "export request data")

    def get_memberships(
            self,
            email: str = None,
            start_page: int = 1,
            page_size: int = 20,
            order_key: str = None,
            order_direction: str = "desc",
            role_types: str = None
    ) -> dict:
        """
        Retrieves a list of Organizations and Projects a user belongs to with their Roles.

        :param email: str - The email address of the user to search for (optional, case-insensitive).
        :param start_page: int - The page number for pagination (default is 1).
        :param page_size: int - The number of items per page (default is 20).
        :param order_key: str - Field for sorting. Only 'organizationName' is supported (optional).
        :param order_direction: str - Sort direction: 'asc' or 'desc' (default is 'desc').
        :param role_types: str - Comma-separated list of role types: 'backend', 'frontend' (optional, case-insensitive).
        :return: dict - The API response containing the list of organizations and projects with roles, in JSON format.
        """
        params = {
            "startPage": start_page,
            "pageSize": page_size,
            "orderDirection": order_direction
        }
        if email:
            params["email"] = email
        if order_key:
            params["orderKey"] = order_key
        if role_types:
            params["roleTypes"] = role_types

        response = self.api_service.get(endpoint=GET_MEMBERSHIPS_V2, params=params)
        validate_status_code(response)
        return parse_json_response(response, "get memberships")

    def get_project_memberships(
            self,
            email: str = None,
            start_page: int = 1,
            page_size: int = 20,
            order_key: str = None,
            order_direction: str = "desc",
            role_types: str = None
    ) -> dict:
        """
        Retrieves a list of Projects and Roles for a user within a specific Organization.

        :param email: str - The email address of the user to search for (optional, case-insensitive).
        :param start_page: int - The page number for pagination (default is 1).
        :param page_size: int - The number of items per page (default is 20).
        :param order_key: str - Field for sorting. Only 'projectName' is supported (optional).
        :param order_direction: str - Sort direction: 'asc' or 'desc' (default is 'desc').
        :param role_types: str - Comma-separated list of role types: 'backend', 'frontend' (optional, case-insensitive).
        :return: dict - The API response containing the list of projects with roles, in JSON format.
        """
        params = {
            "startPage": start_page,
            "pageSize": page_size,
            "orderDirection": order_direction
        }
        if email:
            params["userEmail"] = email
        if order_key:
            params["orderKey"] = order_key
        if role_types:
            params["roleTypes"] = role_types

        organization_id = self._get_organization_id()
        headers = {"organization-id": organization_id}

        response = self.api_service.get(endpoint=GET_PROJECT_MEMBERSHIPS_V2, params=params, headers=headers)
        validate_status_code(response)
        return parse_json_response(response, "get project memberships")

    def get_project_roles(
            self,
            project_id: str,
            start_page: int = 1,
            page_size: int = 20,
            order_key: str = None,
            order_direction: str = "desc",
            role_types: str = None
    ) -> dict:
        """
        Retrieves all Roles supported by a specific Project.

        :param project_id: str - The unique identifier (GUID) of the project (required).
        :param start_page: int - The page number for pagination (default is 1).
        :param page_size: int - The number of items per page (default is 20).
        :param order_key: str - Field for sorting. Only 'name' is supported (optional).
        :param order_direction: str - Sort direction: 'asc' or 'desc' (default is 'desc').
        :param role_types: str - Comma-separated list of role types: 'backend', 'frontend' (optional, case-insensitive).
        :return: dict - The API response containing the list of roles for the project, in JSON format.
        """
        params = {
            "startPage": start_page,
            "pageSize": page_size,
            "orderDirection": order_direction
        }
        if order_key:
            params["orderKey"] = order_key
        if role_types:
            params["roleTypes"] = role_types

        headers = {"project-id": project_id}
        response = self.api_service.get(endpoint=GET_PROJECT_ROLES_V2, params=params, headers=headers)
        validate_status_code(response)
        return parse_json_response(response, "get project roles for project", project_id=project_id)

    def get_project_members(
            self,
            project_id: str,
            start_page: int = 1,
            page_size: int = 20,
            order_key: str = None,
            order_direction: str = "desc",
            role_types: str = None
    ) -> dict:
        """
        Retrieves all members and their Roles for a specific Project.

        :param project_id: str - The unique identifier (GUID) of the project (required).
        :param start_page: int - The page number for pagination (default is 1).
        :param page_size: int - The number of items per page (default is 20).
        :param order_key: str - Field for sorting. Only 'name' is supported (optional).
        :param order_direction: str - Sort direction: 'asc' or 'desc' (default is 'desc').
        :param role_types: str - Comma-separated list of role types: 'backend', 'frontend' (optional, case-insensitive).
        :return: dict - The API response containing the list of members with their roles, in JSON format.
        """
        params = {
            "startPage": start_page,
            "pageSize": page_size,
            "orderDirection": order_direction
        }
        if order_key:
            params["orderKey"] = order_key
        if role_types:
            params["roleTypes"] = role_types

        headers = {"project-id": project_id}
        response = self.api_service.get(endpoint=GET_PROJECT_MEMBERS_V2, params=params, headers=headers)
        validate_status_code(response)
        return parse_json_response(response, "get project members for project", project_id=project_id)

    def get_organization_members(
            self,
            organization_id: str,
            start_page: int = 1,
            page_size: int = 20,
            order_key: str = None,
            order_direction: str = "desc",
            role_types: str = None
    ) -> dict:
        """
        Retrieves all members and their Roles for a specific Organization.

        :param organization_id: str - The unique identifier (GUID) of the organization (required).
        :param start_page: int - The page number for pagination (default is 1).
        :param page_size: int - The number of items per page (default is 20).
        :param order_key: str - Field for sorting. Only 'email' is supported (optional).
        :param order_direction: str - Sort direction: 'asc' or 'desc' (default is 'desc').
        :param role_types: str - Comma-separated list of role types. Only 'backend' is supported for organizations (optional, case-insensitive).
        :return: dict - The API response containing the list of members with their roles, in JSON format.
        """
        params = {
            "organizationId": organization_id,
            "startPage": start_page,
            "pageSize": page_size,
            "orderDirection": order_direction
        }
        if order_key:
            params["orderKey"] = order_key
        if role_types:
            params["roleTypes"] = role_types

        response = self.api_service.get(endpoint=GET_ORGANIZATION_MEMBERS_V2, params=params)
        validate_status_code(response)
        return parse_json_response(response, "get organization members for organization", organization_id=organization_id)

    def get_runtime_policies(
            self,
            organization_id: str = None
    ) -> dict:
        """
        Retrieves the plugin runtime policies defined for a given organization.

        If no policies are defined, the response indicates that individual policies will apply.

        :param organization_id: str - The unique identifier (GUID) of the organization (optional, defaults to token's organization).
        :return: dict - The API response containing plugin runtime policies or a message indicating no policies are defined, in JSON format.
        """
        if not organization_id:
            organization_id = self._get_organization_id()
        headers = {"organization-id": organization_id}
        response = self.api_service.get(endpoint=GET_PLUGIN_RUNTIME_POLICIES_V2, headers=headers)
        validate_status_code(response)
        return parse_json_response(response, "get plugin runtime policies for organization", organization_id=organization_id)

    def add_project_member(
            self,
            project_id: str,
            user_email: str,
            roles: list
    ) -> dict:
        """
        Adds a user to a project by sending an invitation with the specified roles.

        :param project_id: str - The unique identifier (GUID) of the project (required). Will be sent as header.
        :param user_email: str - The email address of the user to invite (required).
        :param roles: list - A list of role names or GUIDs to assign to the user (required).
        :return: dict - The API response confirming the invitation was sent, in JSON format.
        """
        headers = {"project-id": project_id}
        data = {
            "userEmail": user_email,
            "roles": roles
        }
        response = self.api_service.post(
            endpoint=ADD_PROJECT_MEMBER_V2,
            data=data,
            headers=headers
        )
        validate_status_code(response)
        return parse_json_response(response, "add project member", user_email=user_email)

    def create_organization(
            self,
            name: str,
            administrator_user_email: str
    ) -> dict:
        """
        Creates a new organization with the provided details.

        This endpoint requires an OAuth access token from the System Administrator role.

        :param name: str - The name of the new organization (required).
        :param administrator_user_email: str - The email address of the organization administrator (required).
        :return: dict - The API response with details of the created organization in JSON format.
        """
        response = self.api_service.post(
            endpoint=CREATE_ORGANIZATION_V2,
            data={
                "name": name,
                "administratorUserEmail": administrator_user_email
            }
        )
        validate_status_code(response)
        return parse_json_response(response, "create organization with name", name=name)

    def get_organization_list(
            self,
            start_page: int = None,
            page_size: int = None,
            order_key: str = None,
            order_direction: str = "desc",
            filter_key: str = None,
            filter_value: str = None
    ) -> dict:
        """
        Retrieves a list of organizations based on the specified search criteria.

        This endpoint requires an OAuth access token from the System Administrator role.

        :param start_page: int - The page number for pagination (optional).
        :param page_size: int - The number of items per page (optional).
        :param order_key: str - Field for sorting. Only 'name' is supported (optional).
        :param order_direction: str - Sort direction: 'asc' or 'desc' (default is 'desc').
        :param filter_key: str - Field for filtering. Only 'name' is supported (optional).
        :param filter_value: str - Value to filter by (optional).
        :return: dict - The API response containing the list of organizations in JSON format.
        """
        params = {
            "orderDirection": order_direction
        }
        if start_page is not None:
            params["startPage"] = start_page
        if page_size is not None:
            params["pageSize"] = page_size
        if order_key:
            params["orderKey"] = order_key
        if filter_key:
            params["filterKey"] = filter_key
        if filter_value:
            params["filterValue"] = filter_value

        response = self.api_service.get(endpoint=GET_ORGANIZATION_LIST_V2, params=params)
        validate_status_code(response)
        return parse_json_response(response, "get organization list")

    def delete_organization(
            self,
            organization_id: str
    ) -> dict:
        """
        Deletes an existing organization using its unique identifier.

        This endpoint requires an OAuth access token from the System Administrator role.

        :param organization_id: str - The unique identifier (GUID) of the organization to delete (required).
        :return: dict - The API response confirming the deletion of the organization, in JSON format.
        """
        endpoint = DELETE_ORGANIZATION_V2.format(organizationId=organization_id)
        response = self.api_service.delete(endpoint=endpoint)
        validate_status_code(response)
        return parse_json_response(response, "delete organization with ID", organization_id=organization_id)
