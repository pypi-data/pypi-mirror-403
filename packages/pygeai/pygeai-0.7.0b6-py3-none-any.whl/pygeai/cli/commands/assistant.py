import json

from pygeai.assistant.clients import AssistantClient
from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.commands.common import get_llm_settings, get_welcome_data, get_messages, get_welcome_data_feature_list, \
    get_welcome_data_example_prompt
from pygeai.cli.texts.help import ASSISTANT_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(assistant_commands, ASSISTANT_HELP_TEXT)
    Console.write_stdout(help_text)


def get_assistant_detail(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    detail = opts.get("detail", "summary")
    assistant_id = opts.get("assistant_id")

    if not assistant_id:
        raise MissingRequirementException("Cannot retrieve assistant detail without assistant_id")

    client = AssistantClient()
    result = client.get_assistant_data(assistant_id, detail)
    Console.write_stdout(f"Assistant detail: \n{result}")


assistant_detail_options = [
    Option(
        "detail",
        ["--detail", "-d"],
        "Defines the level of detail required. The available options are summary (default) or full.",
        True
    ),
    Option(
        "assistant_id",
        ["--assistant-id", "--id"],
        "Assistant ID.",
        True
    ),
]


def create_assistant(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    assistant_type = opts.get("type", "text")
    name = opts.get("name")
    description = opts.get("description")
    prompt = opts.get("prompt")
    provider_name = opts.get("provider_name")
    model_name = opts.get("model_name")
    max_tokens = opts.get("max_tokens")
    welcome_data_title = opts.get("welcome_data_title")
    welcome_data_description = opts.get("welcome_data_description")
    
    temperature = None
    temp_arg = opts.get("temperature")
    if temp_arg:
        try:
            temperature = float(temp_arg)
        except Exception:
            raise WrongArgumentError("When defined, temperature must be a decimal numer. Example: 0.5")
    
    feature_list = []
    feature_arg = opts.get("welcome_data_feature")
    if feature_arg:
        feature_list = get_welcome_data_feature_list([], feature_arg)
    
    examples_prompt_list = []
    examples_arg = opts.get("welcome_data_example_prompt")
    if examples_arg:
        examples_prompt_list = get_welcome_data_example_prompt([], examples_arg)

    if not (assistant_type and name and prompt):
        raise MissingRequirementException("Cannot create new assistant without 'type', 'name' and 'prompt'")

    llm_settings = {}
    if provider_name or model_name or temperature or max_tokens:
        llm_settings = get_llm_settings(provider_name, model_name, temperature, max_tokens)

    welcome_data = {}
    if welcome_data_title or welcome_data_description:
        welcome_data = get_welcome_data(
            welcome_data_title,
            welcome_data_description,
            feature_list,
            examples_prompt_list
        )

    client = AssistantClient()
    result = client.create_assistant(
        assistant_type=assistant_type,
        name=name,
        prompt=prompt,
        description=description,
        llm_settings=llm_settings,
        welcome_data=welcome_data
    )
    Console.write_stdout(f"New assistant detail: \n{result}")


create_assistant_options = [
    Option(
        "type",
        ["--type", "-t"],
        'string: Type of assistant. Possible values: text, chat. (Required)',
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        'string: Name of the assistant (Required)',
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        'string: Description of the assistant.',
        True
    ),
    Option(
        "prompt",
        ["--prompt"],
        'string: Prompt for the assistant  (Required)',
        True
    ),
    Option(
        "provider_name",
        ["--provider-name", "--provider", "-p"],
        'string: provider to be used',
        True
    ),
    Option(
        "model_name",
        ["--model-name", "-m"],
        'string: name of model according to selected provider',
        True
    ),
    Option(
        "temperature",
        ["--temperature"],
        'decimal: Volatility of the assistant',
        True
    ),
    Option(
        "max_tokens",
        ["--max-tokens"],
        'integer: Max number of tokens',
        True
    ),
    Option(
        "welcome_data_title",
        ["--wd-title"],
        'Title for welcome data',
        True
    ),
    Option(
        "welcome_data_description",
        ["--wd-description"],
        'Description for welcome data',
        True
    ),
    Option(
        "welcome_data_feature",
        ["--wd-feature"],
        'Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and '
        '"description". Example: \'{"title": "title of feature", "description": "Description of feature"}\'',
        True
    ),
    Option(
        "welcome_data_example_prompt",
        ["--wd-example-prompt"],
        'Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description" '
        ' and "prompt_text". Example: \'{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}\'',
        True
    ),
]


def update_assistant(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    assistant_id = opts.get("assistant_id")
    name = opts.get("name")
    description = opts.get("description")
    status = opts.get("status", 1)
    action = opts.get("action", "saveNewRevision")
    revision_id = opts.get("revision_id")
    prompt = opts.get("prompt")
    provider_name = opts.get("provider_name")
    model_name = opts.get("model_name")
    max_tokens = opts.get("max_tokens")
    welcome_data_title = opts.get("welcome_data_title")
    welcome_data_description = opts.get("welcome_data_description")
    
    temperature = None
    temp_arg = opts.get("temperature")
    if temp_arg:
        try:
            temperature = float(temp_arg)
        except Exception:
            raise WrongArgumentError("When defined, temperature must be a decimal numer. Example: 0.5")
    
    feature_list = []
    feature_arg = opts.get("welcome_data_feature")
    if feature_arg:
        feature_list = get_welcome_data_feature_list([], feature_arg)
    
    examples_prompt_list = []
    examples_arg = opts.get("welcome_data_example_prompt")
    if examples_arg:
        examples_prompt_list = get_welcome_data_example_prompt([], examples_arg)

    if not assistant_id:
        raise MissingRequirementException("Cannot update existing assistant without 'assistant_id'")

    if action == "save" and not revision_id:
        raise MissingRequirementException("A revision_id is necessary when updating an existing version.")

    if ((action == "saveNewRevision" or action == "savePublishNewRevision") or revision_id) and not prompt:
        raise MissingRequirementException("Prompt must be defined if revisionId is specified or in case of actions saveNewRevision and savePublishNewRevision.")

    llm_settings = {}
    if provider_name or model_name or temperature or max_tokens:
        llm_settings = get_llm_settings(provider_name, model_name, temperature, max_tokens)

    welcome_data = {}
    if welcome_data_title or welcome_data_description:
        welcome_data = get_welcome_data(welcome_data_title, welcome_data_description, feature_list, examples_prompt_list)

    client = AssistantClient()
    result = client.update_assistant(
        assistant_id=assistant_id,
        status=status,
        action=action,
        revision_id=revision_id,
        name=name,
        prompt=prompt,
        description=description,
        llm_settings=llm_settings,
        welcome_data=welcome_data
    )
    Console.write_stdout(f"Updated assistant detail: \n{result}")


update_assistant_options = [
    Option(
        "assistant_id",
        ["--assistant-id", "--id"],
        "Assistant ID.",
        True
    ),
    Option(
        "status",
        ["--status"],
        "integer: Possible values: 1:Enabled, 2:Disabled (Optional)",
        True
    ),
    Option(
        "action",
        ["--action"],
        "string: Possible values: save, saveNewRevision (default), savePublishNewRevision",
        True
    ),
    Option(
        "revision_id",
        ["--revision-id"],
        "integer: Required if user needs to update an existent revision when action = save",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        'string: Name of the assistant (Required)',
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        'string: Description of the assistant.',
        True
    ),
    Option(
        "prompt",
        ["--prompt"],
        'string: Prompt for the assistant  (Required)',
        True
    ),
    Option(
        "provider_name",
        ["--provider-name", "--provider", "-p"],
        'string: provider to be used',
        True
    ),
    Option(
        "model_name",
        ["--model-name", "-m"],
        'string: name of model according to selected provider',
        True
    ),
    Option(
        "temperature",
        ["--temperature"],
        'decimal: Volatility of the assistant',
        True
    ),
    Option(
        "max_tokens",
        ["--max-tokens"],
        'integer: Max number of tokens',
        True
    ),
    Option(
        "welcome_data_title",
        ["--wd-title"],
        'Title for welcome data',
        True
    ),
    Option(
        "welcome_data_description",
        ["--wd-description"],
        'Description for welcome data',
        True
    ),
    Option(
        "welcome_data_feature",
        ["--wd-feature"],
        'Feature to include in welcome data. Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title" and '
        '"description". Example: \'{"title": "title of feature", "description": "Description of feature"}\'',
        True
    ),
    Option(
        "welcome_data_example_prompt",
        ["--wd-example-prompt"],
        'Example prompt to include in welcome data.  Must be in JSON format. It can be passed multiple times with one dictionary'
        'each time or one time with a list of dictionaries. Each dictionary must have exactly two keys: "title", "description" '
        ' and "prompt_text". Example: \'{"title": "Title of prompt", "description": "Description of prompt", "prompt_text": "Prompt text"}\'',
        True
    ),
]


def delete_assistant(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    assistant_id = opts.get("assistant_id")

    if not assistant_id:
        raise MissingRequirementException("Cannot delete assistant without 'assistant_id'")

    client = AssistantClient()
    result = client.delete_assistant(
        assistant_id=assistant_id,
    )
    Console.write_stdout(f"Deleted assistant: \n{result}")


delete_assistant_options = [
    Option(
        "assistant_id",
        ["--assistant-id", "--id"],
        "Assistant ID.",
        True
    ),
]


def send_chat_request(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    assistant_name = opts.get("assistant_name")
    revision = opts.get("revision")
    revision_name = opts.get("revision_name")
    
    message_list = []
    messages_arg = opts.get("messages")
    if messages_arg:
        try:
            message_json = json.loads(messages_arg)
            if isinstance(message_json, list):
                message_list = message_json
            elif isinstance(message_json, dict):
                message_list.append(message_json)
        except Exception:
            raise WrongArgumentError(
                "Each message must be in json format: '{\"role\": \"user\", \"content\": \"message content\"}' "
                "It can be a dictionary or a list of dictionaries. Each dictionary must contain role and content")

    if not assistant_name:
        raise MissingRequirementException("Cannot send chat request without specifying assistant name")

    messages = get_messages(message_list)

    client = AssistantClient()
    result = client.send_chat_request(
        assistant_name=assistant_name,
        messages=messages,
        revision=revision,
        revision_name=revision_name
    )
    Console.write_stdout(f"Chat request response: \n{result}")


send_chat_request_options = [
    Option(
        "assistant_name",
        ["--name", "-n"],
        "string: Name of the assistant.",
        True
    ),
    Option(
        "messages",
        ["--messages", "--msg"],
        "array: Chat request data. It can be passed multiple times with single dictionary each time, or a single time "
        "as a list of dictionaries. Each dictionary instance must contain 'role' and 'content'",
        True
    ),
    Option(
        "revision",
        ["--revision"],
        "integer: Revision number.",
        True
    ),
    Option(
        "revision_name",
        ["--revision-name"],
        "string:\tName of the revision.",
        True
    ),
    Option(
        "variables",
        ["--variables", "--var"],
        "collection: A list of key/value properties (optional)",
        True
    ),
]


def get_request_status(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    request_id = opts.get("request_id")

    if not request_id:
        raise MissingRequirementException("Cannot retrieve status of request without request_id.")

    client = AssistantClient()
    result = client.get_request_status(request_id)
    Console.write_stdout(f"Request status: \n{result}")


request_status_options = [
    Option(
        "request_id",
        ["--request-id", "--id"],
        "Request ID.",
        True
    ),
]


def cancel_request(option_list: list):
    opts = {opt.name: arg for opt, arg in option_list}
    request_id = opts.get("request_id")

    if not request_id:
        raise MissingRequirementException("Cannot cancel request without request_id.")

    client = AssistantClient()
    result = client.cancel_request(request_id)
    Console.write_stdout(f"Cancel request detail: \n{result}")


cancel_request_options = [
    Option(
        "request_id",
        ["--request-id", "--id"],
        "Request ID.",
        True
    ),
]


assistant_commands = [
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
        "assistant_detail",
        ["get-assistant"],
        "Get assistant detail",
        get_assistant_detail,
        ArgumentsEnum.REQUIRED,
        [],
        assistant_detail_options
    ),
    Command(
        "create_assistant",
        ["create-assistant"],
        "Create new assistant",
        create_assistant,
        ArgumentsEnum.REQUIRED,
        [],
        create_assistant_options
    ),
    Command(
        "update_assistant",
        ["update-assistant"],
        "Update existing assistant",
        update_assistant,
        ArgumentsEnum.REQUIRED,
        [],
        update_assistant_options
    ),
    Command(
        "delete_assistant",
        ["delete-assistant"],
        "Delete existing assistant",
        delete_assistant,
        ArgumentsEnum.REQUIRED,
        [],
        delete_assistant_options
    ),
    Command(
        "assistant_chat",
        ["chat"],
        "Sends a chat request to the Globant Enterprise AI Assistant.",
        send_chat_request,
        ArgumentsEnum.REQUIRED,
        [],
        send_chat_request_options
    ),
    Command(
        "request_status",
        ["request-status"],
        "Retrieves the status of a request.",
        get_request_status,
        ArgumentsEnum.REQUIRED,
        [],
        request_status_options
    ),
    Command(
        "cancel_request",
        ["cancel-request"],
        "Cancels a request.",
        cancel_request,
        ArgumentsEnum.REQUIRED,
        [],
        cancel_request_options
    ),
]
