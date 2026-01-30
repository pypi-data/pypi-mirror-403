Project Management
==================

The API Reference provides a comprehensive set of tools for managing projects within your organization. You can perform the following actions:
* Create project: Creates a new project within your organization.
* Get project data: Retrieves detailed information about a specific project using its Id.
* Delete project: Deletes an existing project.
* List projects: Retrieves a list of all projects within your organization. You can choose to retrieve a summary or detailed information for each project.
* Update project: Updates the name and description of an existing project.
* Add project member: Sends an invitation email to add a user to a project with specific roles (supports individual and batch invitations).

List projects
~~~~~~~~~~~~~~

Lists existing projects within an organization using `PyGEA </pygeai>`_. You can choose to display a summary or the full project information.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_


Command line
^^^^^^^^^^^^

You can list projects using the following command-line options:


List projects with summary details (default)
############################################

You can list the projects without additional options, as follows:

.. code-block:: shell

    geai org list-projects


List projects with full details
###############################

Use the optional flag "-d" to indicate "full" detail. The default is summary.

.. code-block:: shell

    geai org list-projects -d full


If we need to work with a different API key, we can indicate an alias. Let's suppose we have an 'admin' alias with an
organization API key.

List projects using a different API token (alias)
#################################################

.. code-block:: shell

    geai --alias <alias_name> org list-projects

Replace `<alias_name>` with the actual alias for your `GEAI_API_KEY` (e.g., "admin").

**Note**: Each alias defines a profile with a specific access level. Based on the profile's access level, you will need to use SAIA_ORGANIZATION_APITOKEN or SAIA_PROJECT_APITOKEN as GEAI_API_KEY.


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to list projects with the desired detail level:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    client = OrganizationClient()
    project_list = client.get_project_list(detail="full")  # Use "summary" for less detail
    print(project_list)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippets to list projects using the high-level service layer:

List projects with default details
##################################

You can get the list of projects by calling the "get_project_list" method from the OrganizationManager manager class.


.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()

    response = manager.get_project_list()
    print(f"response: {response}")


List projects with full details and a specific alias
####################################################

Also, you can indicate the alias for the desired environment to use.

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager(alias="sdkorg")

    response = manager.get_project_list("full")
    print(f"response: {response}")



Create project
~~~~~~~~~~~~~~

Creates a new project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_ using `PyGEA </pygeai>`_, providing the project name and the administrator's email address. Optionally, you can add a project description and set `usage limits <https://wiki.genexus.com/enterprise-ai/wiki?802,Usage+Limits+API#:~:text=Managing%20quotas%20per%20project>`_.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

The simplest way to create a project is using the command line:

1. Open your terminal or command prompt.
2. Run the following command, replacing the placeholders with your desired values:

.. code-block:: shell

    geai org create-project \
      -n "Project Name" \
      -e "admin@example.com"  \
      -d "Project Description"

Where:

- `n`: Name of your project.
- `e`: Email address of the project administrator.
- `d`: Optional description for your project.


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

For more control, you can use the low-level service layer. To do so:

1.  Import the necessary modules.
2.  Create an instance of the `OrganizationClient` class.
3.  Call the `create_project` method, providing the required information.

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    name="Project Name"
    description="Project Description"
    email="admin@example.com"

    client = OrganizationClient()
    new_project = client.create_project(name=name, email=email, description=description)
    print(new_project)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

The high-level service layer offers a more structured approach:

1. Import the necessary modules.
2. Create an instance of the `OrganizationManager` class.
3. Define the project's usage limits (optional).
4. Create a `Project` object with the necessary information.
5. Call the `create_project` method of the `OrganizationManager` to create the project.

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.models import UsageLimit, Project

    manager = OrganizationManager()

    usage_limit = UsageLimit(
        subscription_type="Monthly",  # Options: Freemium, Daily, Weekly, Monthly
        usage_unit="Requests",        # Options: Requests, Cost
        soft_limit=500.0,             # Recommended usage limit
        hard_limit=1000.0,            # Maximum allowed usage
        renewal_status="Renewable"    # Options: Renewable, NonRenewable
    )

    project = Project(
        name="Project Name",
        description="Project Description",
        email="admin@example.com",
        usage_limit=usage_limit
    )


    created_project = manager.create_project(project)


Update project
~~~~~~~~~~~~~~

Updates an existing project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_  using `PyGEA </pygeai>`_. You can modify a project's name and description by providing its Id and updated information.

To update usage limits, refer to `Managing quotas per project <https://wiki.genexus.com/enterprise-ai/wiki?71,Managing+quotas+per+project>`_.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to update a project:


.. code-block:: shell

    geai org update-project \
      -id <project_id> \
      --name "<new_project_name>" \
      --description "<new_project_description>"

Replace the placeholders with the actual values:

* `<project_id>`: Id of the project you want to update.
* `<new_project_name>`: New name for the project.
* `<new_project_description>`: New description for the project.

For example:

.. code-block:: shell
    geai org update-project \
      --id 12345678-90ab-cdef-1234-567890abcdef \
      --name "Updated Project Name" \
      --description "This is the updated project description"


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to update a project using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_iid="<project_id>"
    name="<new_project_name>"
    description="<new_project_description>"

    client = OrganizationClient()
    new_project = client.update_project(
        project_id=project_id,
        name=name,
        description=description
    )
    print(new_project)

Replace the placeholders with the actual values for your project.


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to update a project using the high-level service layer:


.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.models import UsageLimit, Project

    client = OrganizationManager()

    project = Project(
        id="<project_id>",
        name="<new_project_name>",
        description="<new_project_description>",
    )


    project = client.update_project(project)
    print(f"project: {project}")


Replace the placeholders with the actual values for your project.


Delete project
~~~~~~~~~~~~~~

Deletes an existing project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_ using `PyGEA </pygeai>`_. You can delete a project by providing its project Id.

A successful deletion results in an empty response. If the project doesn't exist or if you lack the necessary permissions, an error occurs.

To delete a project, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to delete a project:

.. code-block:: shell

    geai org delete-project \
      --id <project_id>

Replace <`project_id`> with the actual project Id. For example:

.. code-block:: shell
    geai org delete-project \
      --id 12345678-90ab-cdef-1234-567890abcdef


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to delete a project using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "<project_id>"
    client = OrganizationClient()
    deleted_project = client.delete_project(project_id=project_id)
    print(deleted_project)

Replace <`project_id`> with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id="12345678-90ab-cdef-1234-567890abcdef"
    client = OrganizationClient()
    deleted_project = client.delete_project(project_id=project_id)
    print(deleted_project)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to delete a project using the high-level service layer:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()

    response = manager.delete_project("<project_id>")
    print(f"response: {response}")

Replace <`project_id`> with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()
    response = manager.delete_project("12345678-90ab-cdef-1234-567890abcdef")
    print(f"response: {response}")


Get project data
~~~~~~~~~~~~~~~~

Retrieves project data using `PyGEA </pygeai>`_. You can fetch project details by providing the project Id.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_


Command line
^^^^^^^^^^^^

Use the following command to retrieve the project:

.. code-block:: shell

    geai org get-project \
    --id <project_id>

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: shell

    geai org get-project \
    --id 12345678-90ab-cdef-1234-567890abcdef


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project data using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_iid="<project_id>"
    client = OrganizationClient()
    project_data = client.get_project_data(project_id=project_id)
    print(project_data)

Replace `<project_id>` with the actual project Id. For example:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id="12345678-90ab-cdef-1234-567890abcdef"
    client = OrganizationClient()
    project_data = client.get_project_data(project_id=project_id)
    print(project_data)


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project data using the high-level service layer:


.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager(alias="sdkorg")

    project = manager.get_project_data(project_iid="<project_id>")
    print(f"project: {project}")


Replace `<project_id>` with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager(alias="sdkorg")
    project = manager.get_project_data(project_id="12345678-90ab-cdef-1234-567890abcdef")
    print(f"project: {project}")


Member Management
=================
You can manage project members to control access and permissions within your projects.

* Add Project Member: Sends an invitation email to add a user to a project with specific roles.

Add Project Member
~~~~~~~~~~~~~~~~~~

Sends an invitation email to add a user to a project in `Globant Enterprise AI <https://wiki.genexus.com/enterprise-ai/wiki?8,Table+of+contents%3AEnterprise+AI>`_ using `PyGEA </pygeai>`_. You can add individual users or process multiple invitations via a CSV file (batch mode).

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Add a single user to a project
###############################

Use the following command to invite a user to a project:

.. code-block:: shell

    geai org add-project-member \
      --project-id <project_id> \
      --email <user_email> \
      --roles "<role1>,<role2>"

Replace the placeholders with the actual values:

* `<project_id>`: Id of the project.
* `<user_email>`: Email address of the user to invite.
* `<role1>,<role2>`: Comma-separated list of roles (e.g., "Project member,Project administrator").

For example:

.. code-block:: shell

    geai org add-project-member \
      --project-id 1956c032-3c66-4435-acb8-6a06e52f819f \
      --email user@example.com \
      --roles "Project member,Project administrator"

You can also use the short alias:

.. code-block:: shell

    geai org apm \
      --project-id 1956c032-3c66-4435-acb8-6a06e52f819f \
      --email user@example.com \
      --roles "Project member"


Add multiple users via CSV file (batch mode)
#############################################

Use the `-b` or `--batch` flag to process multiple invitations from a CSV file:

.. code-block:: shell

    geai org add-project-member --batch <path_to_csv_file>

The CSV file format should be:

.. code-block:: text

    project_id,email,role1,role2,...
    1956c032-3c66-4435-acb8-6a06e52f819f,user1@example.com,Project member
    1956c032-3c66-4435-acb8-6a06e52f819f,user2@example.com,Project member,Project administrator

For example:

.. code-block:: shell

    geai org add-project-member --batch project_members.csv

The command will process each line and report successful and failed invitations.


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to invite a user to a project using the low-level service layer:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "<project_id>"
    email = "<user_email>"
    roles = ["Project member", "Project administrator"]

    client = OrganizationClient()
    result = client.add_project_member(project_id=project_id, email=email, roles=roles)
    print(result)

Replace the placeholders with the actual values. For example:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "1956c032-3c66-4435-acb8-6a06e52f819f"
    email = "user@example.com"
    roles = ["Project member", "Project administrator"]

    client = OrganizationClient()
    result = client.add_project_member(project_id=project_id, email=email, roles=roles)
    print(result)

For batch processing, you can use:

.. code-block:: python

    import csv
    from pygeai.organization.clients import OrganizationClient

    client = OrganizationClient()

    with open('project_members.csv', 'r') as file:
        csv_reader = csv.reader(file)
        for row in csv_reader:
            if len(row) >= 3:
                project_id = row[0]
                email = row[1]
                roles = row[2:]
                try:
                    result = client.add_project_member(
                        project_id=project_id,
                        email=email,
                        roles=roles
                    )
                    print(f"✓ Invited {email} to project {project_id}")
                except Exception as e:
                    print(f"✗ Failed to invite {email}: {e}")


High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to invite a user to a project using the high-level service layer:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()

    project_id = "<project_id>"
    email = "<user_email>"
    roles = ["Project member", "Project administrator"]

    response = manager.add_project_member(
        project_id=project_id,
        email=email,
        roles=roles
    )
    print(f"response: {response}")

Replace the placeholders with the actual values. For example:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager

    manager = OrganizationManager()

    project_id = "1956c032-3c66-4435-acb8-6a06e52f819f"
    email = "user@example.com"
    roles = ["Project member", "Project administrator"]

    response = manager.add_project_member(
        project_id=project_id,
        email=email,
        roles=roles
    )
    print(f"response: {response}")


Token Management
================
You can manage project tokens, which are essential for authentication and authorization when interacting with specific projects.

* Get Project Tokens: Retrieves the tokens associated with a specific project.

Get Project Tokens
~~~~~~~~~~~~~~~~~~

Retrieves the tokens associated with a specific project using PyGEA. You can fetch these tokens by providing the project Id.

To achieve this, you have three options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_
* `High-Level Service Layer </docs/source/content/api_reference.rst#high-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve project tokens:

.. code-block:: shell
    geai org get-tokens --id <project_id>

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: shell
    geai org get-tokens --id 12345678-90ab-cdef-1234-567890abcdef


Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project tokens using the low-level service layer:


.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "<project_id>"

    client = OrganizationClient()
    tokens = client.get_project_tokens(project_id=project_id)
    print(tokens)

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "12345678-90ab-cdef-1234-567890abcdef"

    client = OrganizationClient()
    tokens = client.get_project_tokens(project_id=project_id)
    print(tokens)

High level service layer
^^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project tokens using the high-level service layer:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.base.models import ProjectTokensResponse

    client = OrganizationManager()
    project_id = "<project_id>"

    tokens: ProjectTokensResponse = client.get_project_tokens(project_id=project_id)
    print(f"tokens: {tokens}")

Replace `<project_id>` with the actual project Id. For example:

.. code-block:: python

    from pygeai.organization.managers import OrganizationManager
    from pygeai.core.models import ProjectTokensResponse

    client = OrganizationManager()

    project_id = "12345678-90ab-cdef-1234-567890abcdef"

    tokens: ProjectTokensResponse = client.get_project_tokens(project_id=project_id)
    print(f"tokens: {tokens}")


Access Control
==============
The Access Control API provides tools to manage memberships, roles, and members across organizations and projects.

* Get Memberships: Retrieves organizations where you are a member.
* Get Project Memberships: Retrieves projects where a user is a member.
* Get Project Roles: Retrieves all roles supported by a specific project.
* Get Project Members: Retrieves all members and their roles for a specific project.
* Get Organization Members: Retrieves all members and their roles for a specific organization.
* Get Plugin Runtime Policies: Retrieves plugin runtime policies defined for an organization.

Get Memberships
~~~~~~~~~~~~~~~

Retrieves all organizations where you are a member using `PyGEA </pygeai>`_. Supports pagination and filtering options.

To achieve this, you have two options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve your organization memberships:

.. code-block:: shell

    geai org get-memberships

With optional pagination parameters:

.. code-block:: shell

    geai org get-memberships \
      --start-page 1 \
      --page-size 10 \
      --order-direction asc

Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve memberships:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    client = OrganizationClient()
    result = client.get_memberships(
        start_page=1,
        page_size=10,
        order_direction="asc"
    )
    print(result)


Get Project Memberships
~~~~~~~~~~~~~~~~~~~~~~~

Retrieves projects where a specific user is a member using `PyGEA </pygeai>`_. Supports pagination, sorting, and filtering by email.

To achieve this, you have two options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve project memberships for a specific user:

.. code-block:: shell

    geai org get-project-memberships \
      --email user@example.com \
      --start-page 1 \
      --page-size 10

With optional sorting and filtering:

.. code-block:: shell

    geai org get-project-memberships \
      --email user@example.com \
      --start-page 1 \
      --page-size 10 \
      --order-key name \
      --order-direction desc \
      --role-types backend,frontend

Where:

* `--email`: User email address to filter by (required).
* `--start-page`: Page number for pagination (optional, default: 1).
* `--page-size`: Number of items per page (optional, default: 20).
* `--order-key`: Field for sorting (only 'name' supported, optional).
* `--order-direction`: Sort direction: 'asc' or 'desc' (optional, default: 'desc').
* `--role-types`: Comma-separated list of role types (optional, case-insensitive).

Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project memberships:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    client = OrganizationClient()
    result = client.get_project_memberships(
        email="user@example.com",
        start_page=1,
        page_size=10,
        order_key="name",
        order_direction="desc",
        role_types="backend,frontend"
    )
    print(result)


Get Project Roles
~~~~~~~~~~~~~~~~~

Retrieves all roles supported by a specific project using `PyGEA </pygeai>`_. Supports pagination, sorting, and filtering by role types.

To achieve this, you have two options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve project roles:

.. code-block:: shell

    geai org get-project-roles \
      --project-id <project_id>

With optional pagination and filtering:

.. code-block:: shell

    geai org get-project-roles \
      --project-id 12345678-90ab-cdef-1234-567890abcdef \
      --start-page 1 \
      --page-size 10 \
      --order-key name \
      --order-direction asc \
      --role-types backend

Where:

* `--project-id`: The unique identifier (GUID) of the project (required).
* `--start-page`: Page number for pagination (optional, default: 1).
* `--page-size`: Number of items per page (optional, default: 20).
* `--order-key`: Field for sorting (only 'name' supported, optional).
* `--order-direction`: Sort direction: 'asc' or 'desc' (optional, default: 'desc').
* `--role-types`: Comma-separated list of role types: 'backend', 'frontend' (optional, case-insensitive).

Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project roles:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "12345678-90ab-cdef-1234-567890abcdef"

    client = OrganizationClient()
    result = client.get_project_roles(
        project_id=project_id,
        start_page=1,
        page_size=10,
        order_key="name",
        order_direction="asc",
        role_types="backend"
    )
    print(result)


Get Project Members
~~~~~~~~~~~~~~~~~~~

Retrieves all members and their roles for a specific project using `PyGEA </pygeai>`_. Supports pagination, sorting, and filtering by role types.

To achieve this, you have two options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve project members:

.. code-block:: shell

    geai org get-project-members \
      --project-id <project_id>

With optional pagination and filtering:

.. code-block:: shell

    geai org get-project-members \
      --project-id 12345678-90ab-cdef-1234-567890abcdef \
      --start-page 1 \
      --page-size 10 \
      --order-key name \
      --order-direction desc \
      --role-types backend,frontend

Where:

* `--project-id`: The unique identifier (GUID) of the project (required).
* `--start-page`: Page number for pagination (optional, default: 1).
* `--page-size`: Number of items per page (optional, default: 20).
* `--order-key`: Field for sorting (only 'name' supported, optional).
* `--order-direction`: Sort direction: 'asc' or 'desc' (optional, default: 'desc').
* `--role-types`: Comma-separated list of role types: 'backend', 'frontend' (optional, case-insensitive).

Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve project members:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    project_id = "12345678-90ab-cdef-1234-567890abcdef"

    client = OrganizationClient()
    result = client.get_project_members(
        project_id=project_id,
        start_page=1,
        page_size=10,
        order_key="name",
        order_direction="desc",
        role_types="backend,frontend"
    )
    print(result)


Get Organization Members
~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves all members and their roles for a specific organization using `PyGEA </pygeai>`_. Supports pagination, sorting, and filtering by role types.

To achieve this, you have two options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve organization members:

.. code-block:: shell

    geai org get-organization-members \
      --organization-id <organization_id>

With optional pagination and filtering:

.. code-block:: shell

    geai org get-organization-members \
      --organization-id 12345678-90ab-cdef-1234-567890abcdef \
      --start-page 1 \
      --page-size 10 \
      --order-key email \
      --order-direction asc \
      --role-types backend

Where:

* `--organization-id` or `--oid`: The unique identifier (GUID) of the organization (required).
* `--start-page`: Page number for pagination (optional, default: 1).
* `--page-size`: Number of items per page (optional, default: 20).
* `--order-key`: Field for sorting (only 'email' supported, optional).
* `--order-direction`: Sort direction: 'asc' or 'desc' (optional, default: 'desc').
* `--role-types`: Comma-separated list of role types. Only 'backend' is supported for organizations (optional, case-insensitive).

Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve organization members:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    organization_id = "12345678-90ab-cdef-1234-567890abcdef"

    client = OrganizationClient()
    result = client.get_organization_members(
        organization_id=organization_id,
        start_page=1,
        page_size=10,
        order_key="email",
        order_direction="asc",
        role_types="backend"
    )
    print(result)


Get Plugin Runtime Policies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Retrieves the plugin runtime policies defined for a given organization using `PyGEA </pygeai>`_. If no policies are defined, the response indicates that individual policies will apply.

Plugin runtime policies control permissions for organization agents at The Station, including chat sharing and external execution permissions.

To achieve this, you have two options:

* `Command Line </docs/source/content/api_reference.rst#command-line>`_
* `Low-Level Service Layer </docs/source/content/api_reference.rst#low-level-service-layer>`_

Command line
^^^^^^^^^^^^

Use the following command to retrieve plugin runtime policies:

.. code-block:: shell

    geai org get-plugin-runtime-policies \
      --organization-id <organization_id>

Replace `<organization_id>` with the actual organization GUID. For example:

.. code-block:: shell

    geai org get-plugin-runtime-policies \
      --organization-id 12345678-90ab-cdef-1234-567890abcdef

You can also use the short alias:

.. code-block:: shell

    geai org get-plugin-runtime-policies --oid 12345678-90ab-cdef-1234-567890abcdef

**Response Examples:**

1. **Organizations without policies:**

   .. code-block:: json

       {
         "messages": {
           "description": "Organization plugin runtime policies not defined. Individual policy will apply."
         }
       }

2. **Organizations with policies:**

   .. code-block:: json

       {
         "policies": {
           "chatSharingPermissions": "project",
           "externalExecutionPermissions": "organization"
         }
       }

   Where:

   - `chatSharingPermissions`: Maximum execution permissions for organization Agents. Values: "none", "project", "organization".
   - `externalExecutionPermissions`: Allows sharing conversation by anonymous users. Values: "none", "project", "organization".

Low level service layer
^^^^^^^^^^^^^^^^^^^^^^^

Use the following code snippet to retrieve plugin runtime policies:

.. code-block:: python

    from pygeai.organization.clients import OrganizationClient

    organization_id = "12345678-90ab-cdef-1234-567890abcdef"

    client = OrganizationClient()
    result = client.get_plugin_runtime_policies(organization_id=organization_id)
    print(result)
