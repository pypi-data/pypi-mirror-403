from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.options import DETAIL_OPTION, PROJECT_NAME_OPTION, PROJECT_ID_OPTION, SUBSCRIPTION_TYPE_OPTION, \
    USAGE_LIMIT_USAGE_UNIT_OPTION, USAGE_LIMIT_SOFT_LIMIT_OPTION, USAGE_LIMIT_HARD_LIMIT_OPTION, \
    USAGE_LIMIT_RENEWAL_STATUS_OPTION, PROJECT_DESCRIPTION_OPTION
from pygeai.cli.texts.help import ORGANIZATION_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.plugins.clients import PluginClient
from pygeai.core.utils.console import Console
from pygeai.organization.clients import OrganizationClient


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(organization_commands, ORGANIZATION_HELP_TEXT)
    Console.write_stdout(help_text)


def list_assistants(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    organization_id = opts.get("organization_id")
    project_id = opts.get("project_id")

    if not organization_id and project_id:
        raise MissingRequirementException("Organization ID and Project ID are required.")

    client = PluginClient()
    result = client.list_assistants(organization_id=organization_id, project_id=project_id)

    Console.write_stdout(f"Assistant list: \n{result}")


assistants_list_options = [
    Option(
        "organization_id",
        ["--organization-id", "--oid"],
        "UUID of the organization",
        True
    ),
    Option(
        "project_id",
        ["--project-id", "--pid"],
        "UUID of the project",
        True
    ),
]


def get_project_list(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    detail = opts.get("detail", "summary")
    name = opts.get("name")

    client = OrganizationClient()
    result = client.get_project_list(detail, name)
    Console.write_stdout(f"Project list: \n{result}")


project_list_options = [
    DETAIL_OPTION,
    PROJECT_NAME_OPTION,
]


def get_project_detail(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")

    if not project_id:
        raise MissingRequirementException("Cannot retrieve project detail without project-id")

    client = OrganizationClient()
    result = client.get_project_data(project_id=project_id)
    Console.write_stdout(f"Project detail: \n{result}")


project_detail_options = [
    PROJECT_ID_OPTION,
]


def create_project(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    name = opts.get("name")
    email = opts.get("admin_email")
    description = opts.get("description")
    subscription_type = opts.get("subscription_type")
    usage_unit = opts.get("usage_unit")
    soft_limit = opts.get("soft_limit")
    hard_limit = opts.get("hard_limit")
    renewal_status = opts.get("renewal_status")
    
    usage_limit = {}
    if subscription_type or usage_unit or soft_limit or hard_limit or renewal_status:
        usage_limit.update({
            "subscriptionType": subscription_type,
            "usageUnit": usage_unit,
            "softLimit": soft_limit,
            "hardLimit": hard_limit,
            "renewalStatus": renewal_status
        })

    if not (name and email):
        raise MissingRequirementException("Cannot create project without name and administrator's email")

    client = OrganizationClient()
    result = client.create_project(name, email, description)
    Console.write_stdout(f"New project: \n{result}")


create_project_options = [
    Option(
        "name",
        ["--name", "-n"],
        "Name of the new project",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "Description of the new project",
        True
    ),
    Option(
        "admin_email",
        ["--email", "-e"],
        "Project administrator's email",
        True
    ),
    SUBSCRIPTION_TYPE_OPTION,
    USAGE_LIMIT_USAGE_UNIT_OPTION,
    USAGE_LIMIT_SOFT_LIMIT_OPTION,
    USAGE_LIMIT_HARD_LIMIT_OPTION,
    USAGE_LIMIT_RENEWAL_STATUS_OPTION
]


def update_project(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")
    name = opts.get("name")
    description = opts.get("description")

    if not (project_id and name):
        raise MissingRequirementException("Cannot update project without project-id and/or name")

    client = OrganizationClient()
    result = client.update_project(project_id, name, description)
    Console.write_stdout(f"Updated project: \n{result}")


update_project_options = [
    PROJECT_ID_OPTION,
    PROJECT_NAME_OPTION,
    PROJECT_DESCRIPTION_OPTION,
]


def delete_project(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")

    if not project_id:
        raise MissingRequirementException("Cannot delete project without project-id")

    client = OrganizationClient()
    result = client.delete_project(project_id)
    Console.write_stdout(f"Deleted project: \n{result}")


delete_project_options = [
    PROJECT_ID_OPTION,
]


def get_project_tokens(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")

    if not project_id:
        raise MissingRequirementException("Cannot retrieve project tokens without project-id")

    client = OrganizationClient()
    result = client.get_project_tokens(project_id)
    Console.write_stdout(f"Project tokens: \n{result}")


get_project_tokens_options = [
    PROJECT_ID_OPTION,
]


def export_request_data(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    assistant_name = opts.get("assistant_name")
    status = opts.get("status")
    skip = opts.get("skip", 0)
    count = opts.get("count", 0)

    client = OrganizationClient()
    result = client.export_request_data(assistant_name, status, skip, count)
    Console.write_stdout(f"Request data: \n{result}")


export_request_data_options = [
    Option(
        "assistant_name",
        ["--assistant-name"],
        "string: Assistant name (optional)",
        True
    ),
    Option(
        "status",
        ["--status"],
        "string: Status (optional)",
        True
    ),
    Option(
        "skip",
        ["--skip"],
        "integer: Number of entries to skip",
        True
    ),
    Option(
        "count",
        ["--count"],
        "integer: Number of entries to retrieve",
        True
    )
]


def get_memberships(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    email = opts.get("email")
    start_page = int(opts.get("start_page", 1))
    page_size = int(opts.get("page_size", 20))
    order_key = opts.get("order_key")
    order_direction = opts.get("order_direction", "desc")
    role_types = opts.get("role_types")

    client = OrganizationClient()
    result = client.get_memberships(email, start_page, page_size, order_key, order_direction, role_types)
    Console.write_stdout(f"Memberships: \n{result}")


get_memberships_options = [
    Option(
        "email",
        ["--email", "-e"],
        "Email address of the user (optional, case-insensitive)",
        True
    ),
    Option(
        "start_page",
        ["--start-page"],
        "Page number for pagination (default: 1)",
        True
    ),
    Option(
        "page_size",
        ["--page-size"],
        "Number of items per page (default: 20)",
        True
    ),
    Option(
        "order_key",
        ["--order-key"],
        "Field for sorting (only 'organizationName' supported)",
        True
    ),
    Option(
        "order_direction",
        ["--order-direction"],
        "Sort direction: asc or desc (default: desc)",
        True
    ),
    Option(
        "role_types",
        ["--role-types"],
        "Comma-separated list: backend, frontend (optional, case-insensitive)",
        True
    ),
]


def get_project_memberships(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    email = opts.get("email")
    start_page = int(opts.get("start_page", 1))
    page_size = int(opts.get("page_size", 20))
    order_key = opts.get("order_key")
    order_direction = opts.get("order_direction", "desc")
    role_types = opts.get("role_types")

    client = OrganizationClient()
    result = client.get_project_memberships(email, start_page, page_size, order_key, order_direction, role_types)
    Console.write_stdout(f"Project memberships: \n{result}")


get_project_memberships_options = [
    Option(
        "email",
        ["--email", "-e"],
        "Email address of the user (optional, case-insensitive)",
        True
    ),
    Option(
        "start_page",
        ["--start-page"],
        "Page number for pagination (default: 1)",
        True
    ),
    Option(
        "page_size",
        ["--page-size"],
        "Number of items per page (default: 20)",
        True
    ),
    Option(
        "order_key",
        ["--order-key"],
        "Field for sorting (only 'projectName' supported)",
        True
    ),
    Option(
        "order_direction",
        ["--order-direction"],
        "Sort direction: asc or desc (default: desc)",
        True
    ),
    Option(
        "role_types",
        ["--role-types"],
        "Comma-separated list: backend, frontend (optional, case-insensitive)",
        True
    ),
]


def get_project_roles(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")
    start_page = int(opts.get("start_page", 1))
    page_size = int(opts.get("page_size", 20))
    order_key = opts.get("order_key")
    order_direction = opts.get("order_direction", "desc")
    role_types = opts.get("role_types")

    if not project_id:
        raise MissingRequirementException("Cannot retrieve project roles without project-id")

    client = OrganizationClient()
    result = client.get_project_roles(project_id, start_page, page_size, order_key, order_direction, role_types)
    Console.write_stdout(f"Project roles: \n{result}")


get_project_roles_options = [
    PROJECT_ID_OPTION,
    Option(
        "start_page",
        ["--start-page"],
        "Page number for pagination (default: 1)",
        True
    ),
    Option(
        "page_size",
        ["--page-size"],
        "Number of items per page (default: 20)",
        True
    ),
    Option(
        "order_key",
        ["--order-key"],
        "Field for sorting (only 'name' supported)",
        True
    ),
    Option(
        "order_direction",
        ["--order-direction"],
        "Sort direction: asc or desc (default: desc)",
        True
    ),
    Option(
        "role_types",
        ["--role-types"],
        "Comma-separated list: backend, frontend (optional, case-insensitive)",
        True
    ),
]


def get_project_members(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")
    start_page = int(opts.get("start_page", 1))
    page_size = int(opts.get("page_size", 20))
    order_key = opts.get("order_key")
    order_direction = opts.get("order_direction", "desc")
    role_types = opts.get("role_types")

    if not project_id:
        raise MissingRequirementException("Cannot retrieve project members without project-id")

    client = OrganizationClient()
    result = client.get_project_members(project_id, start_page, page_size, order_key, order_direction, role_types)
    Console.write_stdout(f"Project members: \n{result}")


get_project_members_options = [
    PROJECT_ID_OPTION,
    Option(
        "start_page",
        ["--start-page"],
        "Page number for pagination (default: 1)",
        True
    ),
    Option(
        "page_size",
        ["--page-size"],
        "Number of items per page (default: 20)",
        True
    ),
    Option(
        "order_key",
        ["--order-key"],
        "Field for sorting (only 'name' supported)",
        True
    ),
    Option(
        "order_direction",
        ["--order-direction"],
        "Sort direction: asc or desc (default: desc)",
        True
    ),
    Option(
        "role_types",
        ["--role-types"],
        "Comma-separated list: backend, frontend (optional, case-insensitive)",
        True
    ),
]


def get_organization_members(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    organization_id = opts.get("organization_id")
    start_page = int(opts.get("start_page", 1))
    page_size = int(opts.get("page_size", 20))
    order_key = opts.get("order_key")
    order_direction = opts.get("order_direction", "desc")
    role_types = opts.get("role_types")

    if not organization_id:
        raise MissingRequirementException("Cannot retrieve organization members without organization-id")

    client = OrganizationClient()
    result = client.get_organization_members(organization_id, start_page, page_size, order_key, order_direction, role_types)
    Console.write_stdout(f"Organization members: \n{result}")


get_organization_members_options = [
    Option(
        "organization_id",
        ["--organization-id", "--oid"],
        "GUID of the organization (required)",
        True
    ),
    Option(
        "start_page",
        ["--start-page"],
        "Page number for pagination (default: 1)",
        True
    ),
    Option(
        "page_size",
        ["--page-size"],
        "Number of items per page (default: 20)",
        True
    ),
    Option(
        "order_key",
        ["--order-key"],
        "Field for sorting (only 'email' supported)",
        True
    ),
    Option(
        "order_direction",
        ["--order-direction"],
        "Sort direction: asc or desc (default: desc)",
        True
    ),
    Option(
        "role_types",
        ["--role-types"],
        "Comma-separated list: backend (only for organizations, case-insensitive)",
        True
    ),
]


def get_runtime_policies(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    organization_id = opts.get("organization_id")

    client = OrganizationClient()
    result = client.get_runtime_policies(organization_id)
    Console.write_stdout(f"Plugin runtime policies: \n{result}")


get_runtime_policies_options = [
    Option(
        "organization_id",
        ["--organization-id", "--oid"],
        "GUID of the organization (optional, defaults to token's organization)",
        True
    ),
]


def add_project_member(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    project_id = opts.get("project_id")
    user_email = opts.get("user_email")
    batch_file = opts.get("batch_file")
    
    roles = []
    roles_arg = opts.get("roles")
    if roles_arg:
        roles = [r.strip() for r in roles_arg.split(",")]

    client = OrganizationClient()

    if batch_file:
        add_project_member_in_batch(client, batch_file)
    else:
        if not (project_id and user_email and roles):
            raise MissingRequirementException("Cannot add project member without project-id, user email, and roles")
        result = client.add_project_member(project_id, user_email, roles)
        Console.write_stdout(f"User invitation sent: \n{result}")


def add_project_member_in_batch(client: OrganizationClient, batch_file: str):
    import csv
    import os

    if not os.path.exists(batch_file):
        raise MissingRequirementException(f"Batch file not found: {batch_file}")

    successful = 0
    failed = 0
    errors = []

    try:
        with open(batch_file, 'r') as f:
            csv_reader = csv.reader(f)
            for line_num, row in enumerate(csv_reader, start=1):
                if len(row) < 3:
                    error_msg = f"Line {line_num}: Invalid format - expected at least 3 columns (project_id, email, role1, ...)"
                    errors.append(error_msg)
                    failed += 1
                    continue

                project_id = row[0].strip()
                email = row[1].strip()
                roles = [r.strip() for r in row[2:] if r.strip()]

                if not (project_id and email and roles):
                    error_msg = f"Line {line_num}: Missing required fields (project_id={project_id}, email={email}, roles={roles})"
                    errors.append(error_msg)
                    failed += 1
                    continue

                try:
                    client.add_project_member(project_id, email, roles)
                    successful += 1
                except Exception as e:
                    error_msg = f"Line {line_num}: Failed to add {email} to project {project_id}: {str(e)}"
                    errors.append(error_msg)
                    failed += 1

        Console.write_stdout(f"Batch processing complete: {successful} successful, {failed} failed")
        if errors:
            Console.write_stdout("\nErrors:")
            for error in errors:
                Console.write_stdout(f"  - {error}")
    except Exception as e:
        raise MissingRequirementException(f"Failed to read batch file: {str(e)}")


add_project_member_options = [
    Option(
        "project_id",
        ["--project-id", "--pid"],
        "GUID of the project (required unless --batch is used)",
        True
    ),
    Option(
        "user_email",
        ["--email", "-e"],
        "Email address of the user to invite (required unless --batch is used)",
        True
    ),
    Option(
        "roles",
        ["--roles", "-r"],
        "Comma-separated list of role names or GUIDs (e.g., 'Project member,Project administrator') (required unless --batch is used)",
        True
    ),
    Option(
        "batch_file",
        ["--batch", "-b"],
        "Path to CSV file with format: project_id,email,role1,role2,... (one invitation per line)",
        True
    ),
]


def create_organization(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    name = opts.get("name")
    email = opts.get("admin_email")

    if not (name and email):
        raise MissingRequirementException("Cannot create organization without name and administrator's email")

    client = OrganizationClient()
    result = client.create_organization(name, email)
    Console.write_stdout(f"New organization: \\n{result}")


create_organization_options = [
    Option(
        "name",
        ["--name", "-n"],
        "Name of the new organization",
        True
    ),
    Option(
        "admin_email",
        ["--email", "-e"],
        "Organization administrator's email",
        True
    ),
]


def get_organization_list(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    order_direction = opts.get("order_direction", "desc")
    
    start_page = None
    start_page_arg = opts.get("start_page")
    if start_page_arg:
        start_page = int(start_page_arg)
    
    page_size = None
    page_size_arg = opts.get("page_size")
    if page_size_arg:
        page_size = int(page_size_arg)
    
    order_key = opts.get("order_key")
    filter_key = opts.get("filter_key")
    filter_value = opts.get("filter_value")

    client = OrganizationClient()
    result = client.get_organization_list(start_page, page_size, order_key, order_direction, filter_key, filter_value)
    Console.write_stdout(f"Organization list: \\n{result}")


get_organization_list_options = [
    Option(
        "start_page",
        ["--start-page"],
        "Page number for pagination",
        True
    ),
    Option(
        "page_size",
        ["--page-size"],
        "Number of items per page",
        True
    ),
    Option(
        "order_key",
        ["--order-key"],
        "Field for sorting (only 'name' supported)",
        True
    ),
    Option(
        "order_direction",
        ["--order-direction"],
        "Sort direction: asc or desc (default: desc)",
        True
    ),
    Option(
        "filter_key",
        ["--filter-key"],
        "Field for filtering (only 'name' supported)",
        True
    ),
    Option(
        "filter_value",
        ["--filter-value"],
        "Value to filter by",
        True
    ),
]


def delete_organization(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    organization_id = opts.get("organization_id")

    if not organization_id:
        raise MissingRequirementException("Cannot delete organization without organization-id")

    client = OrganizationClient()
    result = client.delete_organization(organization_id)
    Console.write_stdout(f"Deleted organization: \\n{result}")


delete_organization_options = [
    Option(
        "organization_id",
        ["--organization-id", "--oid"],
        "GUID of the organization (required)",
        True
    ),
]

organization_commands = [
    Command(
        "help",
        ["help", "h"],
        "Display help text",
        show_help,
        ArgumentsEnum.NOT_AVAILABLE,
        [],
        []
    ),
    Command(
        "assistants_list",
        ["list-assistants"],
        "List assistant information",
        list_assistants,
        ArgumentsEnum.OPTIONAL,
        [],
        assistants_list_options
    ),
    Command(
        "project_list",
        ["list-projects"],
        "List project information",
        get_project_list,
        ArgumentsEnum.OPTIONAL,
        [],
        project_list_options
    ),
    Command(
        "project_detail",
        ["get-project"],
        "Get project information",
        get_project_detail,
        ArgumentsEnum.REQUIRED,
        [],
        project_detail_options
    ),
    Command(
        "create_project",
        ["create-project"],
        "Create new project",
        create_project,
        ArgumentsEnum.REQUIRED,
        [],
        create_project_options
    ),
    Command(
        "update_project",
        ["update-project"],
        "Update existing project",
        update_project,
        ArgumentsEnum.REQUIRED,
        [],
        update_project_options
    ),
    Command(
        "delete_project",
        ["delete-project"],
        "Delete existing project",
        delete_project,
        ArgumentsEnum.REQUIRED,
        [],
        delete_project_options
    ),
    Command(
        "get_project_tokens",
        ["get-tokens"],
        "Get project tokens",
        get_project_tokens,
        ArgumentsEnum.REQUIRED,
        [],
        get_project_tokens_options
    ),
    Command(
        "export_request_data",
        ["export-request"],
        "Export request data",
        export_request_data,
        ArgumentsEnum.OPTIONAL,
        [],
        export_request_data_options
    ),
    Command(
        "get_memberships",
        ["get-memberships"],
        "Get user memberships across organizations and projects",
        get_memberships,
        ArgumentsEnum.OPTIONAL,
        [],
        get_memberships_options
    ),
    Command(
        "get_project_memberships",
        ["get-project-memberships"],
        "Get user project memberships within an organization",
        get_project_memberships,
        ArgumentsEnum.OPTIONAL,
        [],
        get_project_memberships_options
    ),
    Command(
        "get_project_roles",
        ["get-project-roles"],
        "Get all roles supported by a project",
        get_project_roles,
        ArgumentsEnum.REQUIRED,
        [],
        get_project_roles_options
    ),
    Command(
        "get_project_members",
        ["get-project-members"],
        "Get all members and their roles for a project",
        get_project_members,
        ArgumentsEnum.REQUIRED,
        [],
        get_project_members_options
    ),
    Command(
        "get_organization_members",
        ["get-organization-members"],
        "Get all members and their roles for an organization",
        get_organization_members,
        ArgumentsEnum.REQUIRED,
        [],
        get_organization_members_options
    ),
    Command(
        "get_runtime_policies",
        ["get-runtime-policies"],
        "Get runtime policies for a plugin",
        get_runtime_policies,
        ArgumentsEnum.OPTIONAL,
        [],
        get_runtime_policies_options
    ),
    Command(
        "add_project_member",
        ["add-project-member"],
        "Add a member to a project (single or batch)",
        add_project_member,
        ArgumentsEnum.OPTIONAL,
        [],
        add_project_member_options
    ),
    Command(
        "create_organization",
        ["create-organization"],
        "Create new organization",
        create_organization,
        ArgumentsEnum.REQUIRED,
        [],
        create_organization_options
    ),
    Command(
        "get_organization_list",
        ["get-organization-list"],
        "Get organization list",
        get_organization_list,
        ArgumentsEnum.OPTIONAL,
        [],
        get_organization_list_options
    ),
    Command(
        "delete_organization",
        ["delete-organization"],
        "Delete organization",
        delete_organization,
        ArgumentsEnum.REQUIRED,
        [],
        delete_organization_options
    ),
]
