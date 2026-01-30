import unittest
from json import JSONDecodeError
from unittest.mock import patch

from pygeai.organization.clients import OrganizationClient
from pygeai.core.common.exceptions import InvalidAPIResponseException
from pygeai.organization.endpoints import GET_ASSISTANT_LIST_V1, GET_PROJECT_LIST_V1, GET_PROJECT_V1, CREATE_PROJECT_V1, \
    UPDATE_PROJECT_V1, DELETE_PROJECT_V1, GET_PROJECT_TOKENS_V1, GET_REQUEST_DATA_V1, GET_MEMBERSHIPS_V2, \
    GET_PROJECT_MEMBERSHIPS_V2, GET_PROJECT_ROLES_V2, GET_PROJECT_MEMBERS_V2, GET_ORGANIZATION_MEMBERS_V2, \
    ADD_PROJECT_MEMBER_V2, CREATE_ORGANIZATION_V2, GET_ORGANIZATION_LIST_V2, DELETE_ORGANIZATION_V2


class TestOrganizationClient(unittest.TestCase):
    """
    python -m unittest pygeai.tests.organization.test_clients.TestOrganizationClient
    """

    def setUp(self):
        self.client = OrganizationClient()

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_assistant_list_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"assistants": [{"name": "assistant1"}, {"name": "assistant2"}]}
        mock_response.status_code = 200

        result = self.client.get_assistant_list(detail="summary")

        mock_get.assert_called_once_with(endpoint=GET_ASSISTANT_LIST_V1, params={"detail": "summary"})
        self.assertIsNotNone(result)
        self.assertEqual(len(result['assistants']), 2)
        self.assertEqual(result['assistants'][0]['name'], "assistant1")
        self.assertEqual(result['assistants'][1]['name'], "assistant2")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_assistant_list_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_assistant_list(detail="full")

        mock_get.assert_called_once_with(endpoint=GET_ASSISTANT_LIST_V1, params={"detail": "full"})
        self.assertEqual(str(context.exception), "Unable to get assistant list: Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_list_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"projects": [{"name": "project1"}, {"name": "project2"}]}
        mock_response.status_code = 200

        result = self.client.get_project_list(detail="summary")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_LIST_V1, params={"detail": "summary"})
        self.assertIsNotNone(result)
        self.assertEqual(len(result['projects']), 2)
        self.assertEqual(result['projects'][0]['name'], "project1")
        self.assertEqual(result['projects'][1]['name'], "project2")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_list_with_name(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"projects": [{"name": "specific_project"}]}
        mock_response.status_code = 200

        result = self.client.get_project_list(detail="full", name="specific_project")

        mock_get.assert_called_once_with(
            endpoint=GET_PROJECT_LIST_V1,
            params={"detail": "full", "name": "specific_project"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['projects']), 1)
        self.assertEqual(result['projects'][0]['name'], "specific_project")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_list_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_list(detail="full")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_LIST_V1, params={"detail": "full"})
        self.assertEqual(str(context.exception), "Unable to get project list: Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_data_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "project1"}}
        mock_response.status_code = 200

        result = self.client.get_project_data(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_V1.format(id="123"))
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "project1")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_data_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_data(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_V1.format(id="123"))
        self.assertEqual(str(context.exception), "Unable to get project data for ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_create_project_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "project1"}}
        mock_response.status_code = 200

        result = self.client.create_project(name="project1", email="admin@example.com", description="A test project")

        mock_post.assert_called_once_with(
            endpoint=CREATE_PROJECT_V1,
            data={
                "name": "project1",
                "administratorUserEmail": "admin@example.com",
                "description": "A test project"
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "project1")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_create_project_with_usage_limit(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "project1"}}
        mock_response.status_code = 200

        usage_limit = {"type": "Requests", "threshold": 1000}
        result = self.client.create_project(
            name="project1", email="admin@example.com", description="A test project", usage_limit=usage_limit
        )

        mock_post.assert_called_once_with(
            endpoint=CREATE_PROJECT_V1,
            data={
                "name": "project1",
                "administratorUserEmail": "admin@example.com",
                "description": "A test project",
                "usageLimit": usage_limit
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "project1")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_create_project_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_project(name="project1", email="admin@example.com")

        mock_post.assert_called_once_with(
            endpoint=CREATE_PROJECT_V1,
            data={
                "name": "project1",
                "administratorUserEmail": "admin@example.com",
                "description": None
            }
        )
        self.assertEqual(str(context.exception), "Unable to create project with name 'project1': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.put")
    def test_update_project_success(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.json.return_value = {"project": {"id": "123", "name": "updated_project"}}
        mock_response.status_code = 200

        result = self.client.update_project(project_id="123", name="updated_project", description="Updated description")

        mock_put.assert_called_once_with(
            endpoint=UPDATE_PROJECT_V1.format(id="123"),
            data={"name": "updated_project", "description": "Updated description"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['project']['name'], "updated_project")

    @patch("pygeai.core.services.rest.GEAIApiService.put")
    def test_update_project_json_decode_error(self, mock_put):
        mock_response = mock_put.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.update_project(project_id="123", name="updated_project")

        mock_put.assert_called_once_with(
            endpoint=UPDATE_PROJECT_V1.format(id="123"),
            data={"name": "updated_project", "description": None}
        )
        self.assertEqual(str(context.exception), "Unable to update project with ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.delete")
    def test_delete_project_success(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.json.return_value = {"status": "deleted"}
        mock_response.status_code = 200

        result = self.client.delete_project(project_id="123")

        mock_delete.assert_called_once_with(endpoint=DELETE_PROJECT_V1.format(id="123"))
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], "deleted")

    @patch("pygeai.core.services.rest.GEAIApiService.delete")
    def test_delete_project_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_project(project_id="123")

        mock_delete.assert_called_once_with(endpoint=DELETE_PROJECT_V1.format(id="123"))
        self.assertEqual(str(context.exception), "Unable to delete project with ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_tokens_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"tokens": ["token1", "token2"]}
        mock_response.status_code = 200

        result = self.client.get_project_tokens(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_TOKENS_V1.format(id="123"))
        self.assertIsNotNone(result)
        self.assertEqual(len(result['tokens']), 2)
        self.assertEqual(result['tokens'][0], "token1")
        self.assertEqual(result['tokens'][1], "token2")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_tokens_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_tokens(project_id="123")

        mock_get.assert_called_once_with(endpoint=GET_PROJECT_TOKENS_V1.format(id="123"))
        self.assertEqual(str(context.exception), "Unable to get tokens for project with ID '123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_export_request_data_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"requests": [{"id": "1", "status": "pending"}]}
        mock_response.status_code = 200

        result = self.client.export_request_data()

        mock_get.assert_called_once_with(
            endpoint=GET_REQUEST_DATA_V1,
            params={"assistantName": None, "status": None, "skip": 0, "count": 0}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['requests']), 1)
        self.assertEqual(result['requests'][0]['status'], "pending")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_export_request_data_with_params(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"requests": [{"id": "1", "status": "completed"}]}
        mock_response.status_code = 200

        result = self.client.export_request_data(assistant_name="assistant1", status="completed", skip=10, count=5)

        mock_get.assert_called_once_with(
            endpoint=GET_REQUEST_DATA_V1,
            params={"assistantName": "assistant1", "status": "completed", "skip": 10, "count": 5}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['requests']), 1)
        self.assertEqual(result['requests'][0]['status'], "completed")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_export_request_data_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.export_request_data(assistant_name="assistant1")

        mock_get.assert_called_once_with(
            endpoint=GET_REQUEST_DATA_V1,
            params={"assistantName": "assistant1", "status": None, "skip": 0, "count": 0}
        )
        self.assertEqual(str(context.exception), "Unable to export request data: Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_memberships_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
        
            "count": 1,
            "pages": 1,
            "organizationsMemberships": [
                {
                    "organizationId": "org-123",
                    "organizationName": "Test Org",
                    "projectsMemberships": []
                }
            ]
        }
        mock_response.status_code = 200

        result = self.client.get_memberships()

        mock_get.assert_called_once_with(
            endpoint=GET_MEMBERSHIPS_V2,
            params={"startPage": 1, "pageSize": 20, "orderDirection": "desc"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['count'], 1)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_memberships_with_params(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"count": 0, "pages": 0, "organizationsMemberships": []}
        mock_response.status_code = 200

        result = self.client.get_memberships(
            email="test@example.com",
            start_page=2,
            page_size=10,
            order_key="organizationName",
            order_direction="asc",
            role_types="backend,frontend"
        )

        mock_get.assert_called_once_with(
            endpoint=GET_MEMBERSHIPS_V2,
            params={
                "email": "test@example.com",
                "startPage": 2,
                "pageSize": 10,
                "orderKey": "organizationName",
                "orderDirection": "asc",
                "roleTypes": "backend,frontend"
            }
        )
        self.assertIsNotNone(result)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_memberships_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_memberships()

        self.assertEqual(str(context.exception), "Unable to get memberships: Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_memberships_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.side_effect = [
            {"organizationId": "org-123"},
            {
                "count": 1,
                "pages": 1,
                "projectsMemberships": [
                    {
                        "organizationId": "org-123",
                        "organizationName": "Test Org",
                        "projectId": "proj-456",
                        "projectName": "Test Project",
                        "roles": []
                    }
                ]
            }
        ]
        mock_response.status_code = 200

        result = self.client.get_project_memberships()

        self.assertEqual(mock_get.call_count, 2)
        mock_get.assert_called_with(
            endpoint=GET_PROJECT_MEMBERSHIPS_V2,
            params={"startPage": 1, "pageSize": 20, "orderDirection": "desc"},
            headers={"organization-id": "org-123"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['count'], 1)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_memberships_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            {"organizationId": "org-123"},
            JSONDecodeError("Invalid JSON", "", 0)
        ]
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_memberships()

        self.assertEqual(str(context.exception), "Unable to get project memberships: Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_roles_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
        
            "roles": [
                {"id": "role-1", "name": "Admin", "externalId": "admin-ext", "type": "backend", "origin": "system"}
            ]
        }
        mock_response.status_code = 200

        result = self.client.get_project_roles(project_id="proj-123")

        mock_get.assert_called_once_with(
            endpoint=GET_PROJECT_ROLES_V2,
            params={"startPage": 1, "pageSize": 20, "orderDirection": "desc"},
            headers={"project-id": "proj-123"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['roles']), 1)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_roles_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_roles(project_id="proj-123")

        self.assertEqual(str(context.exception), "Unable to get project roles for project 'proj-123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_members_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
        
            "members": [
                {"email": "user@example.com", "roles": []}
            ]
        }
        mock_response.status_code = 200

        result = self.client.get_project_members(project_id="proj-123")

        mock_get.assert_called_once_with(
            endpoint=GET_PROJECT_MEMBERS_V2,
            params={"startPage": 1, "pageSize": 20, "orderDirection": "desc"},
            headers={"project-id": "proj-123"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['members']), 1)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_project_members_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_project_members(project_id="proj-123")

        self.assertEqual(str(context.exception), "Unable to get project members for project 'proj-123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_organization_members_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
        
            "members": [
                {"email": "user@example.com", "roles": []}
            ]
        }
        mock_response.status_code = 200

        result = self.client.get_organization_members(organization_id="org-123")

        mock_get.assert_called_once_with(
            endpoint=GET_ORGANIZATION_MEMBERS_V2,
            params={"organizationId": "org-123", "startPage": 1, "pageSize": 20, "orderDirection": "desc"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(len(result['members']), 1)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_organization_members_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_organization_members(organization_id="org-123")

        self.assertEqual(str(context.exception), "Unable to get organization members for organization 'org-123': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_add_project_member_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "invitation sent"}
        mock_response.status_code = 201

        result = self.client.add_project_member(
            project_id="proj-123",
            user_email="newuser@example.com",
            roles=["Project member", "Project administrator"]
        )

        mock_post.assert_called_once_with(
            endpoint=ADD_PROJECT_MEMBER_V2,
            data={
                "userEmail": "newuser@example.com",
                "roles": ["Project member", "Project administrator"]
            },
            headers={"project-id": "proj-123"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], "invitation sent")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_add_project_member_with_role_guids(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"status": "invitation sent"}
        mock_response.status_code = 201

        result = self.client.add_project_member(
            project_id="proj-123",
            user_email="newuser@example.com",
            roles=["guid-1", "guid-2"]
        )

        mock_post.assert_called_once_with(
            endpoint=ADD_PROJECT_MEMBER_V2,
            data={
                "userEmail": "newuser@example.com",
                "roles": ["guid-1", "guid-2"]
            },
            headers={"project-id": "proj-123"}
        )
        self.assertIsNotNone(result)

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_add_project_member_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 201
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.add_project_member(
                project_id="proj-123",
                user_email="newuser@example.com",
                roles=["Project member"]
            )

        self.assertEqual(str(context.exception), "Unable to add project member 'newuser@example.com': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_create_organization_success(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.json.return_value = {"organizationId": "org-123", "organizationName": "Test Org"}
        mock_response.status_code = 201

        result = self.client.create_organization(name="Test Org", administrator_user_email="admin@example.com")

        mock_post.assert_called_once_with(
            endpoint=CREATE_ORGANIZATION_V2,
            data={
                "name": "Test Org",
                "administratorUserEmail": "admin@example.com"
            }
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['organizationName'], "Test Org")

    @patch("pygeai.core.services.rest.GEAIApiService.post")
    def test_create_organization_json_decode_error(self, mock_post):
        mock_response = mock_post.return_value
        mock_response.status_code = 201
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.create_organization(name="Test Org", administrator_user_email="admin@example.com")

        self.assertEqual(str(context.exception), "Unable to create organization with name 'Test Org': Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_organization_list_success(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {
            "count": 2,
            "pages": 1,
            "organizations": [
                {"organizationId": "org-1", "organizationName": "Org 1"},
                {"organizationId": "org-2", "organizationName": "Org 2"}
            ]
        }
        mock_response.status_code = 200

        result = self.client.get_organization_list()

        mock_get.assert_called_once_with(
            endpoint=GET_ORGANIZATION_LIST_V2,
            params={"orderDirection": "desc"}
        )
        self.assertIsNotNone(result)
        self.assertEqual(result['count'], 2)
        self.assertEqual(len(result['organizations']), 2)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_organization_list_with_filters(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.json.return_value = {"count": 1, "pages": 1, "organizations": [{"organizationId": "org-1", "organizationName": "Test"}]}
        mock_response.status_code = 200

        result = self.client.get_organization_list(
            start_page=1,
            page_size=10,
            order_key="name",
            order_direction="asc",
            filter_key="name",
            filter_value="Test"
        )

        mock_get.assert_called_once_with(
            endpoint=GET_ORGANIZATION_LIST_V2,
            params={
                "startPage": 1,
                "pageSize": 10,
                "orderKey": "name",
                "orderDirection": "asc",
                "filterKey": "name",
                "filterValue": "Test"
            }
        )
        self.assertIsNotNone(result)

    @patch("pygeai.core.services.rest.GEAIApiService.get")
    def test_get_organization_list_json_decode_error(self, mock_get):
        mock_response = mock_get.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.get_organization_list()

        self.assertEqual(str(context.exception), "Unable to get organization list: Invalid JSON response")

    @patch("pygeai.core.services.rest.GEAIApiService.delete")
    def test_delete_organization_success(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.json.return_value = {"status": "deleted"}
        mock_response.status_code = 200

        result = self.client.delete_organization(organization_id="org-123")

        mock_delete.assert_called_once_with(endpoint=DELETE_ORGANIZATION_V2.format(organizationId="org-123"))
        self.assertIsNotNone(result)
        self.assertEqual(result['status'], "deleted")

    @patch("pygeai.core.services.rest.GEAIApiService.delete")
    def test_delete_organization_json_decode_error(self, mock_delete):
        mock_response = mock_delete.return_value
        mock_response.status_code = 200
        mock_response.json.side_effect = JSONDecodeError("Invalid JSON", "", 0)
        mock_response.text = "Invalid JSON response"

        with self.assertRaises(InvalidAPIResponseException) as context:
            self.client.delete_organization(organization_id="org-123")

        self.assertEqual(str(context.exception), "Unable to delete organization with ID 'org-123': Invalid JSON response")

