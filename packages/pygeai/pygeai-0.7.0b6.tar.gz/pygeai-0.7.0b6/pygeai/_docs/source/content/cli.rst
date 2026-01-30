geai - CLI Reference
====================

In this section, you can find examples of commands using the geai utility to perform basic tasks in GEAI.

CLI Architecture
----------------

The PyGEAI CLI provides a comprehensive command-line interface with the following features:

- **Type-Safe**: Full type hints for better IDE support and error detection
- **Fuzzy Matching**: Suggests similar commands when typos are detected
- **Enhanced Validation**: Detailed error messages with examples and suggestions
- **Multi-Profile Support**: Manage multiple GEAI instances via ``--alias`` flag
- **Consistent Error Handling**: Standardized exit codes and error formats
- **Verbose Mode**: Detailed logging for debugging and troubleshooting

Error Handling
--------------

The CLI provides clear, actionable error messages:

Exit Codes
^^^^^^^^^^

- ``0``: Success
- ``1``: User input error (invalid command, option, or argument)
- ``2``: Missing required parameter
- ``3``: Service error (API or agent issues)
- ``130``: Keyboard interrupt (Ctrl+C)
- ``255``: Unexpected error

Error Message Format
^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    ERROR: <error description>
      → <suggestion for fixing>
      
      Example:
        <example of correct usage>
    
    Run 'geai help' for usage information.

Global Options
--------------

Verbose Mode
^^^^^^^^^^^^

Enable detailed logging output to debug issues or understand command execution flow:

.. code-block:: shell

    geai --verbose <command> [options]
    geai -v <command> [options]

Example output with verbose mode:

.. code-block:: text

    2026-01-13 09:45:04 - geai - DEBUG - Verbose mode enabled
    2026-01-13 09:45:04 - geai - DEBUG - Running geai with: geai help
    2026-01-13 09:45:04 - geai - DEBUG - Session: default
    2026-01-13 09:45:04 - geai - DEBUG - Identifying command for argument: help
    2026-01-13 09:45:04 - geai - DEBUG - Searching for command matching: help
    2026-01-13 09:45:04 - geai - DEBUG - Command found: help (identifiers: ['help', 'h'])
    2026-01-13 09:45:04 - geai - DEBUG - Command identified: help
    2026-01-13 09:45:04 - geai - DEBUG - Processing command: help, arguments: []

**When to use verbose mode:**

- Troubleshooting configuration issues
- Understanding which session/alias is being used
- Debugging command parsing or option validation
- Reporting issues to support with detailed context
- Tracking API calls and responses

Basic Usage
-----------

# Display help

.. code-block:: shell

    geai h

.. code-block:: shell

    geai org h

.. code-block:: shell

    geai ast h


.. code-block:: shell

    geai chat h


# Create project

.. code-block:: shell

    geai org create-project \
      -n "SDKTest2" \
      -e "geai-sdk@globant.com" \
      -d "Test project for SDK"

# Update project

.. code-block:: shell

     geai org update-project \
      --id 12345678-1234-1234-1234-123456789abc \
      --name "SDK Test 3" \
      --description "Test description"

# List projects

.. code-block:: shell

    geai org list-projects

.. code-block:: shell

    geai org list-projects -d full

# Get tokens from organization

.. code-block:: shell

    geai org get-tokens --id aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee

# List assistants

.. code-block:: shell

    geai org list-assistants

# Get assistant information

.. code-block:: shell

    geai ast get-assistant --id 11111111-2222-3333-4444-555555555555

# Chat with assistant

.. code-block:: shell

    geai ast chat \
      --name "Welcome data Assistant" \
      --msg '[{"role": "user", "content": "Translate the phrase free software is the software that protects users freedoms"}, {"role": "user", "content": "now translate to french"]'


# Create assistant

.. code-block:: shell

    geai ast create-assistant \
      --type chat \
      --name "Welcome data Assistant 3" \
      --prompt "Translate to French" \
      --wd-title "Assistant with WelcomeData" \
      --wd-description "It is to test WelcomeData" \
      --wd-feature '[{"title": "First Feature", "description": "First Feature Description"}, {"title": "Second Feature", "description": "Second Feature Description"}]' \
      --wd-example-prompt '{"title": "First Prompt Example", "description": "First Prompt Example Description", "prompt_text": "You are an assistant specialized in translating"}'


# Update assistant

.. code-block:: shell

    geai ast update-assistant \
      --assistant-id 99999999-8888-7777-6666-555555555555 \
      --action savePublishNewRevision \
      --prompt "translate the following text to Latin" \
      --provider-name "openai" \
      --model-name "gpt-3.5-turbo" \
      --temperature 0.0 \\n  --wd-title "Assistant with WelcomeData" \
      --wd-description "It is to test WelcomeData" \
      --wd-feature "Second Feature: Second Feature Description" \
      --wd-feature "First Feature: First Feature Description" \
      --wd-example-prompt "First Prompt Example: First Prompt Example Description: You are an assistant specialized in translating"

# Delete assistant

.. code-block:: shell

    geai ast delete-assistant --id 99999999-8888-7777-6666-555555555555


# Chat completion

.. code-block:: shell

    geai chat completion \
      --model "saia:assistant:Welcome data Assistant 3" \
      --msg '[{"role": "user", "content": "Translate the phrase free software is the software that protects users freedoms"}, {"role": "user", "content": "now translate to french and italian"}]' \
      --stream 0

