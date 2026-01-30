Migration Guide
===============

Overview
--------

The GEAI SDK provides powerful migration capabilities that allow you to clone and migrate projects and their resources between different GEAI instances or within the same instance. This feature is essential for:

- **Environment promotion**: Moving projects from development to staging to production
- **Backup and disaster recovery**: Creating copies of projects for safety
- **Multi-tenant deployments**: Replicating project setups across different organizations
- **Testing and experimentation**: Creating isolated copies for testing changes

The migration feature supports migrating the following resource types:

- **Agents**: AI agents with their configurations and prompts
- **Tools**: Custom tools and integrations
- **Agentic Processes**: Multi-step agentic workflows
- **Tasks**: Individual task definitions
- **Usage Limits**: Resource usage constraints and quotas
- **RAG Assistants**: Retrieval-Augmented Generation assistants
- **Files**: Project files and attachments
- **Secrets**: Secure credentials and sensitive configuration values

Key Features
------------

**Selective Migration**
  Migrate specific resources by ID or migrate all resources of a given type using the ``all`` keyword.

**Bulk Migration**
  Use the ``--all`` flag to migrate every available resource type in a single command.

**Cross-Instance Migration**
  Migrate projects between different GEAI instances with different API credentials.

**Same-Instance Cloning**
  Clone projects within the same instance for testing or backup purposes.

**Automatic Resource Discovery**
  When using ``all``, the migration tool automatically discovers and migrates all existing resources.

**Flexible Destination**
  Migrate to a new project or to an existing project in the same or different instance.

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

Before migrating, you need:

1. **Source credentials**: API key and instance URL for the source project
2. **Destination credentials**: API key and instance URL (can be the same as source)
3. **Project identifiers**: Source project ID
4. **Admin email**: Required when creating a new destination project

API Token Scopes
~~~~~~~~~~~~~~~~~

Different migration operations require different API token scopes:

**Organization Scope Tokens**
  Required for operations that create or manage projects and organization-level resources:
  
  - **Project Creation**: Creating new projects requires organization scope API keys (``--from-org-key`` and ``--to-org-key``)
  - **Usage Limit Migration**: Managing usage limits requires organization scope API keys
  
  For more information, see the `Organization API Documentation <https://docs.globant.ai/en/wiki?22,Organization+API>`_ and `Usage Limits API Documentation <https://docs.globant.ai/en/wiki?802,Usage+Limits+API>`_.

**Project Scope Tokens**
  Required for operations within a project:
  
  - **Agent Migration**: Migrating agents within projects
  - **Tool Migration**: Migrating tools within projects
  - **Agentic Process Migration**: Migrating agentic processes
  - **Task Migration**: Migrating tasks
  - **RAG Assistant Migration**: Migrating RAG assistants
  - **File Migration**: Migrating files within projects
  - **Secret Migration**: Migrating secrets within projects

Migration Scenarios and Required Keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The required API keys depend on whether you're creating a new project or migrating to an existing one:

**Scenario 1: Creating a New Project**
  When using ``--to-project-name`` and ``--admin-email``:
  
  - ``--from-api-key``: **Project scope** token for reading source resources
  - ``--from-org-key``: **Organization scope** token (REQUIRED for project creation)
  - ``--to-org-key``: **Organization scope** token for destination instance (REQUIRED, or use ``--from-org-key`` for same instance)
  - ``--to-api-key``: OPTIONAL - If not provided, a project scope API key will be automatically created for the new project
  
  The migration tool will:
  
  1. Create the new project using organization scope keys
  2. Automatically generate a project scope API key for the new project
  3. Use the generated key to migrate all resources

**Scenario 2: Migrating to an Existing Project**
  When using ``--to-project-id``:
  
  - ``--from-api-key``: **Project scope** token for reading source resources (REQUIRED)
  - ``--to-api-key``: **Project scope** token for writing to destination project (REQUIRED)
  - Organization scope keys are NOT needed for resource migration
  
.. warning::
   When migrating to an existing project (using ``--to-project-id``), you MUST provide ``--to-api-key``. This is a project scope token that has write access to the destination project.

Interactive Mode
----------------

The migration tool provides an **interactive mode** that guides you through the migration process with step-by-step prompts. This mode is ideal when:

- You're new to the migration tool and want guidance
- You don't know the exact IDs of resources to migrate
- You want to browse and select resources interactively
- You prefer a wizard-style interface over command-line arguments

Invoking Interactive Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~

To start the interactive migration wizard, use the ``--interactive`` or ``-i`` flag:

.. code-block:: shell

    geai migrate clone-project --interactive

or shorter:

.. code-block:: shell

    geai migrate clone-project -i

Interactive Mode Walkthrough
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When you launch interactive mode, the wizard will guide you through the following steps:

**Step 1: Migration Type Selection**

Choose whether you're migrating within the same instance or to a different instance:

.. code-block:: text

    ================================================================================
    PROJECT MIGRATION ASSISTANT
    ================================================================================

    Migration type (1=same instance, 2=cross instance):

- Option ``1``: Migrate within the same GEAI instance (destination instance will be same as source)
- Option ``2``: Migrate to a different GEAI instance (you'll provide separate destination credentials)

**Step 2: Source Configuration**

Provide your source project credentials:

.. code-block:: text

    --- Source Configuration ---
    Source API key: [enter your source API key]
    Source instance URL: [enter source instance URL, e.g., https://api.dev.example.ai]
    Source project ID: [enter source project ID]

The wizard will automatically retrieve your source organization ID from the API token.

**Step 3: Project Creation or Selection**

Decide whether to create a new destination project or use an existing one:

.. code-block:: text

    Create new destination project? (y/n):

- If you choose ``y`` (yes): You'll provide organization API keys, project name, and admin email to create a new project
- If you choose ``n`` (no): You'll provide an existing destination project ID

**For new project creation:**

.. code-block:: text

    Source organization API key: [enter organization scope API key]
    Destination organization API key: [same as source for same instance, or enter different key]
    New project name: [enter name for new project]
    Admin email: [enter admin email for project]

**For existing project:**

.. code-block:: text

    Destination project ID: [enter existing project ID]

**Step 4: Destination Configuration**

If you selected cross-instance migration (option 2) or using an existing project, provide destination details:

.. code-block:: text

    --- Destination Configuration ---
    Destination instance URL: [enter destination URL if cross-instance]
    Destination API key: [enter project API key for destination]

**Step 5: Resource Type Selection**

Select which types of resources you want to migrate:

.. code-block:: text

    --- Resource Type Selection ---
    Which resource types do you want to migrate?
      1. Agents
      2. Tools
      3. Agentic Processes
      4. Tasks
      5. RAG Assistants
      6. Files
      7. Usage Limits
      8. Secrets

    Select resource types (comma-separated numbers, or empty for all):

- Enter specific numbers (e.g., ``1,2,5`` for Agents, Tools, and RAG Assistants)
- Press Enter without typing anything to migrate **all** resource types

**Step 6: Resource Selection**

For each selected resource type, the wizard fetches available resources and displays an interactive menu:

.. code-block:: text

    --- Retrieving Available Resources ---

    Available agents:
      0. Cancel (don't migrate this resource type)
      1. Customer Support Agent (ID: agent-abc-123)
      2. Data Analysis Agent (ID: agent-def-456)
      3. Code Review Agent (ID: agent-ghi-789)

    Select agents (comma-separated numbers, or empty for all):

Selection options:

- Press **Enter** without typing: Migrate **all** resources of this type
- Enter **0**: Skip this resource type entirely
- Enter **specific numbers**: Migrate only selected resources (e.g., ``1,3`` to migrate items 1 and 3)

This process repeats for each resource type you selected in Step 5.

**Step 7: Migration Summary and Confirmation**

Review your migration configuration before execution:

.. code-block:: text

    --- Migration Summary ---
    Source: https://api.dev.example.ai / Project: source-project-123
    Destination: https://api.prod.example.ai / Project: Production Release
    Resources: agents, tools, rag_assistants

    Stop migration on first error? (Y/n):

- Enter ``Y`` or press Enter to stop migration if any resource fails
- Enter ``n`` to continue migrating remaining resources even if some fail

.. code-block:: text

    Proceed with migration? (y/n):

- Enter ``y`` to start the migration
- Enter ``n`` to cancel and exit without making changes

**Step 8: Migration Execution**

The migration proceeds with real-time progress updates:

.. code-block:: text

    ============================================================
    Migration Progress: 0/15 completed
    ============================================================

    [1/15] Migrating agent 'Customer Support Agent'...
    ✓ Successfully migrated agent 'Customer Support Agent'

    [2/15] Migrating agent 'Data Analysis Agent'...
    ✓ Successfully migrated agent 'Data Analysis Agent'

    [3/15] Migrating tool 'Database Query Tool'...
    ✓ Successfully migrated tool 'Database Query Tool'

    ...

    ============================================================
    Migration Complete: 15/15 successful
    ============================================================

Interactive Mode Benefits
~~~~~~~~~~~~~~~~~~~~~~~~~~

**1. No Need to Remember IDs**

   You don't need to know resource IDs beforehand. The wizard fetches and displays all available resources with their names and IDs.

**2. Visual Resource Selection**

   Browse resources in numbered menus and select exactly what you want to migrate.

**3. Guided Configuration**

   Step-by-step prompts ensure you provide all required information in the correct order.

**4. Input Validation**

   The wizard validates your input at each step and prompts you to retry if something is invalid.

**5. Pre-Migration Summary**

   Review all settings before execution with a clear summary of what will be migrated.

**6. Flexible Selection**

   Easily mix migration strategies: migrate all agents, specific tools, all RAG assistants, etc.

**7. Error Recovery**

   If you make a mistake during prompts, the wizard will ask again instead of failing the entire operation.

Interactive vs. CLI Mode Comparison
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

+----------------------------+---------------------------+---------------------------+
| Feature                    | Interactive Mode          | CLI Mode                  |
+============================+===========================+===========================+
| **Ease of Use**            | Beginner-friendly wizard  | Requires knowledge of     |
|                            |                           | all CLI arguments         |
+----------------------------+---------------------------+---------------------------+
| **Resource Discovery**     | Automatic with menus      | Manual (use API or docs)  |
+----------------------------+---------------------------+---------------------------+
| **Input Validation**       | Real-time with retry      | Fails if invalid args     |
+----------------------------+---------------------------+---------------------------+
| **Automation**             | Not scriptable            | Fully scriptable          |
+----------------------------+---------------------------+---------------------------+
| **Best For**               | One-time migrations,      | CI/CD pipelines,          |
|                            | exploration, learning     | automation, scripting     |
+----------------------------+---------------------------+---------------------------+

When to Use Interactive Mode
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

✅ **Use Interactive Mode when:**

- You're performing a one-time migration
- You're unsure of exact resource IDs or names
- You want to browse available resources before selecting
- You're learning how migration works
- You prefer guided prompts over memorizing command syntax

❌ **Use CLI Mode instead when:**

- You're automating migrations in scripts or CI/CD pipelines
- You already know exact resource IDs to migrate
- You need to run the same migration multiple times
- You want to version control migration commands

Example Interactive Session
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Here's a complete example of an interactive migration session:

.. code-block:: text

    $ geai migrate clone-project -i

    ================================================================================
    PROJECT MIGRATION ASSISTANT
    ================================================================================

    Migration type (1=same instance, 2=cross instance): 2

    --- Source Configuration ---
    Source API key: sk_dev_abc123...
    Source instance URL: https://api.dev.example.ai
    Source project ID: proj-dev-001

    Create new destination project? (y/n): y
    Source organization API key: sk_org_dev_xyz789...
    Destination organization API key: sk_org_prod_def456...
    New project name: Production Release v2.0
    Admin email: admin@example.com

    --- Destination Configuration ---
    Destination instance URL: https://api.prod.example.ai
    Destination API key: (will be created after project creation)

    --- Resource Type Selection ---
    Which resource types do you want to migrate?
      1. Agents
      2. Tools
      3. Agentic Processes
      4. Tasks
      5. RAG Assistants
      6. Files
      7. Usage Limits
      8. Secrets

    Select resource types (comma-separated numbers, or empty for all): 1,2,5

    --- Retrieving Available Resources ---

    Available agents:
      0. Cancel (don't migrate this resource type)
      1. Customer Support Agent (ID: agent-001)
      2. Sales Assistant (ID: agent-002)
      3. HR Onboarding Agent (ID: agent-003)

    Select agents (comma-separated numbers, or empty for all): 

    Available tools:
      0. Cancel (don't migrate this resource type)
      1. Database Query Tool (ID: tool-001)
      2. Email Sender (ID: tool-002)
      3. Calendar Integration (ID: tool-003)

    Select tools (comma-separated numbers, or empty for all): 1,3

    Available RAG assistants:
      0. Cancel (don't migrate this resource type)
      1. Documentation Assistant (ID: doc-assistant-001)
      2. Code Helper (ID: code-assistant-002)

    Select RAG assistants (comma-separated numbers, or empty for all): 

    --- Migration Summary ---
    Source: https://api.dev.example.ai / Project: proj-dev-001
    Destination: https://api.prod.example.ai / Project: Production Release v2.0
    Resources: agents, tools, rag_assistants

    Stop migration on first error? (Y/n): Y

    Proceed with migration? (y/n): y

    Creating new project 'Production Release v2.0'...
    Project 'Production Release v2.0' created successfully with ID: proj-prod-002
    Creating project API key for new project...
    Project API key created successfully

    ============================================================
    Migration Progress: 0/7 completed
    ============================================================

    [1/7] Migrating agent 'Customer Support Agent'...
    ✓ Successfully migrated agent 'Customer Support Agent'

    [2/7] Migrating agent 'Sales Assistant'...
    ✓ Successfully migrated agent 'Sales Assistant'

    [3/7] Migrating agent 'HR Onboarding Agent'...
    ✓ Successfully migrated agent 'HR Onboarding Agent'

    [4/7] Migrating tool 'Database Query Tool'...
    ✓ Successfully migrated tool 'Database Query Tool'

    [5/7] Migrating tool 'Calendar Integration'...
    ✓ Successfully migrated tool 'Calendar Integration'

    [6/7] Migrating RAG assistant 'Documentation Assistant'...
    ✓ Successfully migrated RAG assistant 'Documentation Assistant'

    [7/7] Migrating RAG assistant 'Code Helper'...
    ✓ Successfully migrated RAG assistant 'Code Helper'

    ============================================================
    Migration Complete: 7/7 successful
    ============================================================

    Migration completed: 7/7 successful

This example demonstrates:

- Cross-instance migration (dev to prod)
- New project creation
- Selective resource type migration (agents, tools, RAG assistants only)
- Mixed selection strategies (all agents, specific tools, all RAG assistants)
- Successful completion with progress tracking

Basic Usage
-----------

Migrate Everything
~~~~~~~~~~~~~~~~~~

The simplest and most common use case is to migrate an entire project with all its resources:

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "1a2b3c4d-5e6f-7g8h-9i0j-1k2l3m4n5o6p" \\
        --from-instance "https://api.source.example.ai" \\
        --to-project-name "Cloned Project" \\
        --admin-email "admin@example.com" \\
        --all

This command will:

1. Create a new project named "Cloned Project"
2. Discover all resources in the source project
3. Migrate all agents, tools, processes, tasks, usage limits, RAG assistants, files, and secrets
4. Display progress and results

Migrate to Different Instance
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To migrate between different GEAI instances, provide the destination instance details:

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.dev.example.ai" \\
        --to-api-key "destination_api_key_456" \\
        --to-project-name "Production Project" \\
        --to-instance "https://api.prod.example.ai" \\
        --to-organization-id "prod-org-id" \\
        --admin-email "prod-admin@example.com" \\
        --all

Selective Migration
-------------------

Migrate Specific Resource Types
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Instead of migrating everything, you can selectively migrate specific resource types:

**Migrate all agents only:**

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "Agents Only" \\
        --admin-email "admin@example.com" \\
        --agents all

**Migrate all tools only:**

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "Tools Only" \\
        --admin-email "admin@example.com" \\
        --tools all

**Migrate all RAG assistants only:**

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "RAG Assistants Only" \\
        --admin-email "admin@example.com" \\
        --rag-assistants all

**Migrate all secrets only:**

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "Secrets Only" \\
        --admin-email "admin@example.com" \\
        --secrets all

Migrate Specific Resources by ID
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For fine-grained control, specify comma-separated resource IDs:

**Migrate specific agents:**

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "Selected Agents" \\
        --admin-email "admin@example.com" \\
        --agents "agent-id-1,agent-id-2,agent-id-3"

**Migrate specific tools:**

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "Selected Tools" \\
        --admin-email "admin@example.com" \\
        --tools "tool-id-1,tool-id-2"

Mixed Migration Strategies
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Combine different migration strategies for maximum flexibility:

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "Mixed Migration" \\
        --admin-email "admin@example.com" \\
        --agents all \\
        --tools "tool-id-1,tool-id-2" \\
        --rag-assistants all \\
        --files all

This command migrates:

- **ALL** agents (auto-discovered)
- **SPECIFIC** tools (by ID)
- **ALL** RAG assistants (auto-discovered)
- **ALL** files (auto-discovered)

Advanced Usage
--------------

Migrate with Organization Context
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When migrating between organizations, specify organization IDs:

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-organization-id "source-org-id" \\
        --from-instance "https://api.example.ai" \\
        --to-api-key "destination_api_key_456" \\
        --to-project-name "Cross-Org Project" \\
        --to-organization-id "destination-org-id" \\
        --to-instance "https://api.example.ai" \\
        --admin-email "admin@example.com" \\
        --all

Migrate All AI Lab Resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To migrate all AI Lab-related resources (agents, tools, processes, tasks):

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_api_key_123" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-name "AI Lab Resources" \\
        --admin-email "admin@example.com" \\
        --agents all \\
        --tools all \\
        --agentic-processes all \\
        --tasks all

CLI Reference
-------------

Command: ``geai migrate clone-project``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Description:** Clone a project with selective or complete resource migration.

**Interactive Mode Flag:**

``--interactive`` or ``-i``
  Launch the interactive migration wizard with step-by-step prompts. When this flag is used, all other arguments are ignored and the wizard will prompt for all required information. See the :ref:`Interactive Mode` section for details.

**Required Arguments (CLI Mode):**

``--from-api-key <key>``
  Project scope API key for the source GEAI instance (for migrating resources)

``--from-project-id <id>``
  ID of the source project to migrate from

``--from-instance <url>``
  URL of the source GEAI instance

**Optional Arguments:**

``--from-org-key <key>``
  Organization scope API key for the source instance (REQUIRED when creating projects or migrating usage limits)

``--to-api-key <key>``
  Project scope API key for the destination instance. **REQUIRED** when using ``--to-project-id`` (existing project). OPTIONAL when creating a new project (auto-generated if not provided)

``--to-org-key <key>``
  Organization scope API key for the destination instance (REQUIRED when creating projects or migrating usage limits)

``--to-project-id <id>``
  Destination project ID (use this to migrate to an existing project). **REQUIRED**: ``--to-api-key`` must also be provided. **MUTUALLY EXCLUSIVE** with ``--to-project-name`` and ``--admin-email``

``--to-project-name <name>``
  Name for the new destination project (when specified with --admin-email, creates a new project). **MUTUALLY EXCLUSIVE** with ``--to-project-id``

``--admin-email <email>``
  Admin email for the new project (required when creating a new project with --to-project-name)

``--to-instance <url>``
  URL of the destination instance (defaults to source instance if omitted)

``--from-organization-id <id>``
  Organization ID in the source instance (required for usage limits and file migration)

``--to-organization-id <id>``
  Organization ID in the destination instance (required for usage limits and file migration)

**Migration Flags:**

``--all``
  Migrate all available resource types (agents, tools, processes, tasks, usage limits, RAG assistants, files, secrets)

``--agents <all|id1,id2,...>``
  Migrate all agents or specific agents by ID (comma-separated)

``--tools <all|id1,id2,...>``
  Migrate all tools or specific tools by ID (comma-separated)

``--agentic-processes <all|id1,id2,...>``
  Migrate all agentic processes or specific processes by ID (comma-separated)

``--tasks <all|id1,id2,...>``
  Migrate all tasks or specific tasks by ID (comma-separated)

``--usage-limits <all|id1,id2,...>``
  Migrate all usage limits or specific usage limits by ID (comma-separated)

``--rag-assistants <all|id1,id2,...>``
  Migrate all RAG assistants or specific assistants by ID (comma-separated)

``--files <all|id1,id2,...>``
  Migrate all files or specific files by ID (comma-separated)

``--secrets <all|id1,id2,...>``
  Migrate all secrets or specific secrets by ID (comma-separated)

``--stop-on-error <0|1>`` or ``--soe <0|1>``
  Control migration behavior on errors. Set to ``1`` (default) to stop migration on first error, or ``0`` to continue migrating remaining resources even if some fail

Migration Behavior
------------------

Resource Discovery
~~~~~~~~~~~~~~~~~~

When you use ``all`` for any resource type, the migration tool:

1. Connects to the source instance
2. Lists all available resources of that type
3. Filters resources with valid IDs/names
4. Creates migration strategies for each discovered resource
5. Displays the count of discovered resources

For example:

.. code-block:: shell

    geai migrate clone-project ... --agents all

Will output something like:

.. code-block:: text

    Discovered 15 agents
    Migrating agents...
    [Progress indicators]

Error Handling
~~~~~~~~~~~~~~

The migration process includes robust error handling:

- Invalid API keys or instances result in clear error messages
- Missing required parameters are detected before migration starts
- Individual resource migration failures are logged but don't stop the entire process by default (unless ``--stop-on-error 1`` is set)
- Final migration result includes success/failure status for each resource
- Use ``--stop-on-error 0`` to continue migrating all resources even if some fail, or ``--stop-on-error 1`` (default) to halt on first error

Best Practices
--------------

1. **Test First**: Always test migrations in a development environment before production
2. **Start with Interactive Mode**: If you're new to migrations or unsure about resource IDs, use ``--interactive`` mode for guided assistance
3. **Use --all for Complete Clones**: When creating backups or full clones, use ``--all``
4. **Verify Credentials**: Double-check API keys and instance URLs before running migrations
5. **Monitor Progress**: Watch the console output for discovery counts and migration status
6. **Check Results**: Review the migration result summary after completion
7. **Incremental Migration**: For large projects, consider migrating resource types incrementally
8. **Document Migrations**: Keep track of what was migrated and when
9. **Automate Repeated Migrations**: Once you know the exact resources and IDs, convert interactive sessions to CLI commands for repeatability

Common Use Cases
----------------

Development to Production Promotion (with new project creation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "dev_project_api_key" \\
        --from-org-key "dev_org_api_key" \\
        --from-project-id "dev-project-id" \\
        --from-instance "https://api.dev.example.ai" \\
        --to-api-key "prod_project_api_key" \\
        --to-org-key "prod_org_api_key" \\
        --to-project-name "Production Release v1.0" \\
        --to-instance "https://api.prod.example.ai" \\
        --admin-email "prod-admin@example.com" \\
        --all

Project Backup (with new project creation)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "project_api_key" \\
        --from-org-key "org_api_key" \\
        --from-project-id "main-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-org-key "org_api_key" \\
        --to-project-name "Main Project Backup $(date +%Y-%m-%d)" \\
        --admin-email "admin@example.com" \\
        --all

Migrate Resources to Existing Project (no org keys needed)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

When migrating to an existing project, you must provide both ``--to-project-id`` and ``--to-api-key``:

.. code-block:: shell

    geai migrate clone-project \\
        --from-api-key "source_project_api_key" \\
        --from-project-id "source-project-id" \\
        --from-instance "https://api.example.ai" \\
        --to-project-id "existing-project-id" \\
        --to-api-key "target_project_api_key" \\
        --agents all \\
        --tools all

This example migrates all agents and tools to an existing project without requiring organization scope API keys.

Troubleshooting
---------------

Migration Fails with Authentication Error
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``Error retrieving project_id from GEAI: Authentication failed``

**Solution**: Verify your API keys are correct and have necessary permissions:

- When creating a new project (``--to-project-name`` + ``--admin-email``): You MUST provide **organization scope** API keys via ``--from-org-key`` and ``--to-org-key``
- When migrating usage limits (``--usage-limits``): You MUST provide **organization scope** API keys via ``--from-org-key`` and ``--to-org-key``
- For other resource migrations: Use **project scope** API keys via ``--from-api-key`` and ``--to-api-key``

Missing Organization Scope API Keys
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``Source organization scope API key (--from-org-key) is required for project creation``

**Solution**: When creating a new project or migrating usage limits, you must explicitly provide organization scope API keys using ``--from-org-key`` and ``--to-org-key`` parameters. Project scope API keys cannot be used for these operations

Missing Destination Project API Key
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``Destination project API key (--to-api-key) is required when migrating to an existing project (--to-project-id)``

**Solution**: When migrating to an existing project using ``--to-project-id``, you MUST provide ``--to-api-key`` with a project scope API key that has write access to the destination project. This is required because the migration tool needs to create resources in the existing project.

**Note**: When creating a NEW project (using ``--to-project-name`` and ``--admin-email``), ``--to-api-key`` is optional and will be automatically generated if not provided.

Migration Discovers No Resources
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: ``Discovered 0 agents`` when you know resources exist

**Solution**: Check that the ``--from-project-id`` is correct and the API key has read access

Partial Migration Success
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Problem**: Some resources migrate successfully, others fail

**Solution**: Check the error log for specific resource failures and retry individual resources if needed

Limitations
-----------

- API rate limits may affect large migrations
- Some resource dependencies may require specific migration order
- Cross-instance migrations require network connectivity between instances
- Certain resource types may have instance-specific configurations

See Also
--------

- :doc:`cli` - General CLI usage
- :doc:`ai_lab` - AI Lab concepts and resources
- :doc:`quickstart` - Getting started with GEAI SDK
