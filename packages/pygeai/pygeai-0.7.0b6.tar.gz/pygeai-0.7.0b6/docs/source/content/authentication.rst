Authentication
==============

The PyGEAI SDK supports two authentication methods: **API Key** authentication and **OAuth 2.0** authentication. Both methods provide secure access to Globant Enterprise AI services, with OAuth offering enhanced security through token-based authentication and project-level access control.

API Key Authentication
----------------------

API Key authentication is the traditional method that uses a project-specific API token. This is the simplest authentication method and is suitable for most use cases.

Configuration
~~~~~~~~~~~~~

You can configure API Key authentication using the CLI:

.. code-block:: shell

    geai configure

When prompted, enter your API key and base URL:

.. code-block:: shell

    -> Select an alias (Leave empty to use 'default'): default
    -> Insert your GEAI_API_KEY: your_api_key_here
    GEAI API KEY for alias 'default' saved successfully!
    -> Insert your GEAI API BASE URL: https://api.saia.ai
    GEAI API BASE URL for alias 'default' saved successfully!

The ``geai configure`` command creates or updates the credentials file at ``~/.geai/credentials`` with the specified alias profile.

Usage in Code
~~~~~~~~~~~~~

**Using Configured Credentials:**

.. code-block:: python

    from pygeai.lab.clients import AILabClient
    
    # Uses credentials from configuration file
    client = AILabClient()

**Explicit API Key:**

.. code-block:: python

    from pygeai.lab.clients import AILabClient
    
    client = AILabClient(
        api_key="your_api_key_here",
        base_url="https://api.saia.ai"
    )

**With Project ID:**

.. code-block:: python

    from pygeai.lab.clients import AILabClient
    
    client = AILabClient(
        api_key="your_api_key_here",
        base_url="https://api.saia.ai",
        project_id="your-project-id"
    )

OAuth 2.0 Authentication
------------------------

OAuth 2.0 provides enhanced security by using temporary access tokens instead of long-lived API keys. This method requires both an ``access_token`` and a ``project_id``.

Prerequisites
~~~~~~~~~~~~~

Before using OAuth authentication, you need to:

1. Obtain OAuth credentials (client ID, username, password)
2. Get an access token
3. Know your project ID

Getting an Access Token
~~~~~~~~~~~~~~~~~~~~~~~

Use the Auth client to obtain an OAuth 2.0 access token:

.. code-block:: python

    from pygeai.auth.clients import AuthClient
    
    auth_client = AuthClient()
    
    # Get OAuth 2.0 access token
    response = auth_client.get_oauth2_access_token(
        client_id="your-client-id",
        username="your-username",
        password="your-password"
    )
    
    access_token = response["access_token"]
    project_id = "your-project-id"

Usage in Code
~~~~~~~~~~~~~

**Basic OAuth Authentication:**

.. code-block:: python

    from pygeai.lab.clients import AILabClient
    
    client = AILabClient(
        base_url="https://api.saia.ai",
        access_token="your_oauth_access_token",
        project_id="your-project-id"
    )

**With Other Clients:**

.. code-block:: python

    from pygeai.core.secrets.clients import SecretClient
    from pygeai.evaluation.clients import EvaluationClient
    
    # Secret Client with OAuth
    secret_client = SecretClient(
        base_url="https://api.saia.ai",
        access_token="your_oauth_access_token",
        project_id="your-project-id"
    )
    
    # Evaluation Client with OAuth
    eval_client = EvaluationClient(
        base_url="https://api.saia.ai",
        eval_url="https://eval.saia.ai",
        access_token="your_oauth_access_token",
        project_id="your-project-id"
    )

Complete OAuth Flow Example
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from pygeai.auth.clients import AuthClient
    from pygeai.lab.clients import AILabClient
    from pygeai.lab.agents.clients import AgentClient
    
    # Step 1: Obtain OAuth access token
    auth_client = AuthClient()
    token_response = auth_client.get_oauth2_access_token(
        client_id="your-client-id",
        username="user@example.com",
        password="your-password"
    )
    
    access_token = token_response["access_token"]
    project_id = "your-project-id"
    
    # Step 2: Use OAuth token with clients
    lab_client = AILabClient(
        base_url="https://api.saia.ai",
        access_token=access_token,
        project_id=project_id
    )
    
    # Step 3: Use the client
    agents = lab_client.list_agents()
    print(f"Found {len(agents)} agents")

Authentication Comparison
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 30 35 35

   * - Feature
     - API Key
     - OAuth 2.0
   * - **Security**
     - Long-lived key
     - Temporary access token
   * - **Setup Complexity**
     - Simple
     - Moderate
   * - **Project Isolation**
     - Optional
     - Required
   * - **Token Expiration**
     - Never (until revoked)
     - Yes (requires refresh)
   * - **Header Format**
     - ``Bearer {api_key}``
     - ``Bearer {access_token}``
   * - **Additional Headers**
     - None (ProjectId optional)
     - ``ProjectId`` header required
   * - **Use Case**
     - Development, testing
     - Production, multi-project

Implementation Details
----------------------

Header Injection
~~~~~~~~~~~~~~~~

The SDK automatically injects authentication headers:

**API Key:**

.. code-block:: python

    Authorization: Bearer your_api_key_here

**OAuth 2.0:**

.. code-block:: python

    Authorization: Bearer your_oauth_access_token
    ProjectId: your-project-id

Backward Compatibility
~~~~~~~~~~~~~~~~~~~~~~

OAuth parameters (``access_token`` and ``project_id``) are **keyword-only** parameters to maintain backward compatibility with existing code:

.. code-block:: python

    # Correct - keyword arguments
    client = AILabClient(
        base_url="https://api.saia.ai",
        access_token="token",
        project_id="project-123"
    )
    
    # Error - cannot pass as positional
    client = AILabClient("https://api.saia.ai", "token", "project-123")

Validation
~~~~~~~~~~

The SDK validates authentication parameters:

- **Missing OAuth parameters**: If ``access_token`` is provided without ``project_id``, a ``MissingRequirementException`` is raised.
- **Complete OAuth**: Both ``access_token`` and ``project_id`` must be provided together.

.. code-block:: python

    # Raises MissingRequirementException
    client = AILabClient(
        base_url="https://api.saia.ai",
        access_token="token_without_project"
    )
    
    # Correct
    client = AILabClient(
        base_url="https://api.saia.ai",
        access_token="token",
        project_id="project-123"
    )

Advanced Features
-----------------

Mixed Authentication
~~~~~~~~~~~~~~~~~~~~

The SDK supports using both API Key and OAuth 2.0 authentication simultaneously through the ``allow_mixed_auth`` parameter. When both are provided, OAuth takes precedence.

.. code-block:: python

    from pygeai.lab.clients import AILabClient
    
    client = AILabClient(
        api_key="your_api_key",
        base_url="https://api.saia.ai",
        access_token="your_oauth_token",
        project_id="your-project-id",
        allow_mixed_auth=True  # Required when providing both
    )
    # OAuth authentication will be used (takes precedence)

**Validation:**

- If both ``api_key`` and ``access_token`` are provided without ``allow_mixed_auth=True``, a ``MixedAuthenticationException`` is raised.
- When mixed auth is allowed, OAuth 2.0 (``access_token``) takes precedence over the API key.

Organization ID
~~~~~~~~~~~~~~~

The optional ``organization_id`` parameter provides organization-level context for API requests:

.. code-block:: python

    client = AILabClient(
        base_url="https://api.saia.ai",
        access_token="your_oauth_token",
        project_id="your-project-id",
        organization_id="your-org-id"
    )

When provided, the SDK automatically includes the ``OrganizationId`` header in API requests.

Environment Variables
~~~~~~~~~~~~~~~~~~~~~

All authentication parameters can be configured via environment variables:

**API Key Authentication:**

- ``GEAI_API_KEY`` - Your API key
- ``GEAI_API_BASE_URL`` - Base URL for the API
- ``GEAI_PROJECT_ID`` - (Optional) Project ID

**OAuth 2.0 Authentication:**

- ``GEAI_OAUTH_ACCESS_TOKEN`` - Your OAuth 2.0 access token
- ``GEAI_PROJECT_ID`` - Your project ID (required with OAuth)
- ``GEAI_API_BASE_URL`` - Base URL for the API
- ``GEAI_ORGANIZATION_ID`` - (Optional) Organization ID

**Example:**

.. code-block:: shell

    export GEAI_OAUTH_ACCESS_TOKEN="your_oauth_token"
    export GEAI_PROJECT_ID="your-project-id"
    export GEAI_API_BASE_URL="https://api.saia.ai"
    export GEAI_ORGANIZATION_ID="your-org-id"

Session Utilities
~~~~~~~~~~~~~~~~~

The SDK provides utility methods to inspect the current authentication state:

.. code-block:: python

    from pygeai.core.base.session import get_session
    from pygeai.core.common.constants import AuthType
    
    session = get_session()
    
    # Check authentication type
    if session.is_oauth():
        print("Using OAuth 2.0 authentication")
        print(f"Project ID: {session.project_id}")
    elif session.is_api_key():
        print("Using API Key authentication")
    
    # Get the active token
    active_token = session.get_active_token()
    
    # Check auth type enum
    if session.auth_type == AuthType.OAUTH_TOKEN:
        print("OAuth authentication active")
    elif session.auth_type == AuthType.API_KEY:
        print("API Key authentication active")
    elif session.auth_type == AuthType.NONE:
        print("No authentication configured")

Warning Behaviors
~~~~~~~~~~~~~~~~~

The SDK provides helpful warnings in the following scenarios:

1. **Project ID without OAuth token**: If ``project_id`` is provided without ``access_token``, a ``UserWarning`` is issued since project_id is only used with OAuth 2.0.

2. **No authentication configured**: If neither ``api_key`` nor ``access_token`` is provided, a warning is logged.

3. **Missing base URL**: If ``base_url`` is not configured, a warning is logged.

4. **Mixed authentication in config**: When loading credentials from a config file that contains both API key and OAuth parameters, a warning is logged indicating OAuth will take precedence.

Exception Reference
~~~~~~~~~~~~~~~~~~~

The SDK raises specific exceptions for authentication errors:

- ``MissingRequirementException``: Raised when OAuth ``access_token`` is provided without required ``project_id``.
- ``MixedAuthenticationException``: Raised when both ``api_key`` and ``access_token`` are provided without ``allow_mixed_auth=True``.
- ``APIResponseError``: Raised for API-level authentication failures (invalid tokens, expired tokens, etc.).

Best Practices
--------------

1. **Use OAuth for Production**: OAuth provides better security through temporary tokens and project isolation.

2. **Store Credentials Securely**: Never hardcode API keys or access tokens in your source code. Use environment variables or secure credential storage.

3. **Token Refresh**: Implement token refresh logic when using OAuth to handle token expiration.

4. **Project Isolation**: Use ``project_id`` to ensure requests are scoped to the correct project, even when using API keys.

5. **Error Handling**: Implement proper error handling for authentication failures:

.. code-block:: python

    from pygeai.core.common.exceptions import (
        MissingRequirementException, 
        MixedAuthenticationException,
        APIResponseError
    )
    
    try:
        client = AILabClient(
            base_url="https://api.saia.ai",
            access_token=access_token,
            project_id=project_id
        )
        agents = client.list_agents()
    except MissingRequirementException as e:
        print(f"Configuration error: {e}")
    except MixedAuthenticationException as e:
        print(f"Mixed authentication error: {e}")
    except APIResponseError as e:
        print(f"Authentication failed: {e}")

Related Resources
-----------------

- :doc:`quickstart` - Getting started with PyGEAI
- :doc:`api_reference/auth` - Auth client API reference
- :doc:`ai_lab` - AI Lab documentation
