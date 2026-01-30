import json

from pygeai.cli.commands import Command, Option, ArgumentsEnum
from pygeai.cli.commands.builders import build_help_text
from pygeai.cli.texts.help import SECRETS_HELP_TEXT
from pygeai.core.common.exceptions import MissingRequirementException, WrongArgumentError
from pygeai.core.secrets.clients import SecretClient
from pygeai.core.utils.console import Console


def show_help():
    """
    Displays help text in stdout
    """
    help_text = build_help_text(secrets_commands, SECRETS_HELP_TEXT)
    Console.write_stdout(help_text)


def get_secret(option_list: list):
    """
    Retrieves a secret by its ID.
    """
    opts = {opt.name: arg for opt, arg in option_list}
    secret_id = opts.get("secret_id")

    if not secret_id:
        raise MissingRequirementException("Cannot retrieve secret without specifying secret-id")

    client = SecretClient()
    result = client.get_secret(secret_id=secret_id)
    Console.write_stdout(f"Get secret result: \n{result}")


get_secret_options = [
    Option(
        "secret_id",
        ["--secret-id", "--sid"],
        "The unique identifier of the secret to retrieve (required)",
        True
    ),
]


def create_secret(option_list: list):
    """
    Creates a new secret with the specified details.
    """
    opts = {opt.name: arg for opt, arg in option_list}
    name = opts.get("name")
    secret_string = opts.get("secret_string")
    description = opts.get("description")

    if not (name and secret_string):
        raise MissingRequirementException("Cannot create secret without specifying name and secret-string")

    client = SecretClient()
    result = client.create_secret(
        name=name,
        secret_string=secret_string,
        description=description
    )
    Console.write_stdout(f"Create secret result: \n{result}")


create_secret_options = [
    Option(
        "name",
        ["--name", "-n"],
        "The name of the secret (required)",
        True
    ),
    Option(
        "secret_string",
        ["--secret-string", "-ss"],
        "The secret value to store (required)",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "A description of the secret (optional)",
        True
    ),
]


def update_secret(option_list: list):
    """
    Updates an existing secret by its ID.
    """
    opts = {opt.name: arg for opt, arg in option_list}
    secret_id = opts.get("secret_id")
    name = opts.get("name")
    secret_string = opts.get("secret_string")
    description = opts.get("description")

    if not (secret_id and name and secret_string):
        raise MissingRequirementException("Cannot update secret without specifying secret-id, name, and secret-string")

    client = SecretClient()
    result = client.update_secret(
        secret_id=secret_id,
        name=name,
        secret_string=secret_string,
        description=description
    )
    Console.write_stdout(f"Update secret result: \n{result}")


update_secret_options = [
    Option(
        "secret_id",
        ["--secret-id", "--sid"],
        "The unique identifier of the secret to update (required)",
        True
    ),
    Option(
        "name",
        ["--name", "-n"],
        "The updated name of the secret (required)",
        True
    ),
    Option(
        "secret_string",
        ["--secret-string", "-ss"],
        "The updated secret value (required)",
        True
    ),
    Option(
        "description",
        ["--description", "-d"],
        "The updated description of the secret (optional)",
        True
    ),
]


def list_secrets(option_list: list):
    """
    Lists secrets with optional filtering and pagination.
    """
    opts = {opt.name: arg for opt, arg in option_list}
    name = opts.get("name")
    id = opts.get("id")
    start_arg = opts.get("start")
    count_arg = opts.get("count")
    
    try:
        start = int(start_arg) if start_arg else 0
    except ValueError:
        raise WrongArgumentError("start must be an integer")
    
    try:
        count = int(count_arg) if count_arg else 10
    except ValueError:
        raise WrongArgumentError("count must be an integer")

    client = SecretClient()
    result = client.list_secrets(
        name=name,
        id=id,
        start=start,
        count=count
    )
    Console.write_stdout(f"List secrets result: \n{result}")


list_secrets_options = [
    Option(
        "name",
        ["--name", "-n"],
        "Filter secrets by name (optional)",
        True
    ),
    Option(
        "id",
        ["--id"],
        "Filter secrets by ID (optional)",
        True
    ),
    Option(
        "start",
        ["--start"],
        "Starting index for pagination (integer, default: 0)",
        True
    ),
    Option(
        "count",
        ["--count"],
        "Number of secrets to return (integer, default: 10)",
        True
    ),
]


def set_secret_accesses(option_list: list):
    """
    Sets access configurations for a secret by its ID.
    """
    opts = {opt.name: arg for opt, arg in option_list}
    secret_id = opts.get("secret_id")
    access_list_arg = opts.get("access_list")
    
    access_list = None
    if access_list_arg:
        try:
            access_list = json.loads(access_list_arg)
            if not isinstance(access_list, list):
                raise WrongArgumentError("access-list must be a JSON array")
        except json.JSONDecodeError:
            raise WrongArgumentError("access-list must be a valid JSON array")

    if not (secret_id and access_list):
        raise MissingRequirementException("Cannot set secret accesses without specifying secret-id and access-list")

    client = SecretClient()
    result = client.set_secret_accesses(
        secret_id=secret_id,
        access_list=access_list
    )
    Console.write_stdout(f"Set secret accesses result: \n{result}")


set_secret_accesses_options = [
    Option(
        "secret_id",
        ["--secret_id", "--sid"],
        "The unique identifier of the secret to set accesses for (required)",
        True
    ),
    Option(
        "access_list",
        ["--access-list", "--al"],
        "JSON array of access configurations, e.g., '[{\"accessLevel\": \"write\", \"principalType\": \"service\"}]' (required)",
        True
    ),
]


def get_secret_accesses(option_list: list):
    """
    Retrieves access configurations for a secret by its ID.
    """
    opts = {opt.name: arg for opt, arg in option_list}
    secret_id = opts.get("secret_id")

    if not secret_id:
        raise MissingRequirementException("Cannot retrieve secret accesses without specifying secret-id")

    client = SecretClient()
    result = client.get_secret_accesses(secret_id=secret_id)
    Console.write_stdout(f"Get secret accesses result: \n{result}")


get_secret_accesses_options = [
    Option(
        "secret_id",
        ["--secret-id", "--sid"],
        "The unique identifier of the secret to retrieve accesses for (required)",
        True
    ),
]

secrets_commands = [
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
        "get_secret",
        ["get-secret", "gs"],
        "Retrieve a secret by its ID",
        get_secret,
        ArgumentsEnum.REQUIRED,
        [],
        get_secret_options
    ),
    Command(
        "create_secret",
        ["create-secret", "cs"],
        "Create a new secret",
        create_secret,
        ArgumentsEnum.REQUIRED,
        [],
        create_secret_options
    ),
    Command(
        "update_secret",
        ["update-secret", "us"],
        "Update an existing secret by its ID",
        update_secret,
        ArgumentsEnum.REQUIRED,
        [],
        update_secret_options
    ),
    Command(
        "list_secrets",
        ["list-secrets", "ls"],
        "List secrets with optional filtering and pagination",
        list_secrets,
        ArgumentsEnum.REQUIRED,
        [],
        list_secrets_options
    ),
    # Command(
    #     "set_accesses",
    #     ["set-accesses", "sa"],
    #     "Set access configurations for a secret by its ID",
    #     set_secret_accesses,
    #     ArgumentsEnum.REQUIRED,
    #     [],
    #     set_secret_accesses_options
    # ),
    # Command(
    #     "get_accesses",
    #     ["get-accesses", "ga"],
    #     "Retrieve access configurations for a secret by its ID",
    #     get_secret_accesses,
    #     ArgumentsEnum.REQUIRED,
    #     [],
    #     get_secret_accesses_options
    # ),

]
