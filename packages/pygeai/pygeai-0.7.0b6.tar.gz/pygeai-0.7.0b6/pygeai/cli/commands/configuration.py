from pygeai.cli.commands import Option
from pygeai.core.common.config import get_settings
from pygeai.core.utils.console import Console


def configure(option_list: list[str, str] = None):
    if not any(option_list):
        Console.write_stdout("# Configuring GEAI credentials...")
        alias = str(input("-> Select an alias for this profile (Leave empty to use 'default'): ")).strip()
        if not alias:
            alias = "default"

        auth_type = str(input("-> Which type of authentication will this profile use? \n1.API key \n2. Oauth2 \n(Type 'enter' for default (1): ")).strip()
        if not auth_type or auth_type == "1":
            api_key = str(input("-> Insert your GEAI API KEY (Leave empty to keep current value): ")).strip()
            if api_key:
                configure_api_key(api_key, alias)

        elif auth_type == "2":
            access_token = str(input("-> Insert your GEAI OAUTH2 ACCESS TOKEN (Leave empty to keep current value): ")).strip()
            if access_token:
                configure_access_token(access_token, alias)

        base_url = str(input("-> Insert your GEAI API BASE URL (Leave empty to keep current value): ")).strip()
        if base_url:
            configure_base_url(base_url, alias)

        eval_url = str(input("-> Insert your GEAI API EVAL URL (Leave empty to keep current value): ")).strip()
        if eval_url:
            configure_eval_url(eval_url, alias)

    else:
        opts = {opt.name: arg for opt, arg in option_list}
        
        list_alias = 'list' in opts
        remove_alias = 'remove_alias' in opts
        alias = opts.get('remove_alias') if remove_alias else opts.get('profile_alias', 'default')
        api_key = opts.get('api_key')
        base_url = opts.get('base_url')
        eval_url = opts.get('eval_url')
        access_token = opts.get('access_token')
        project_id = opts.get('project_id')
        organization_id = opts.get('organization_id')

        if list_alias:
            display_alias_list()
        elif remove_alias:
            remove_alias_from_config(alias)
        else:
            if api_key and access_token:
                Console.write_stdout(
                    "WARNING: You're setting 2 different types of authentication for the same profile. "
                    "This may cause unknown behaviors. Consider using separate profiles for different "
                    "authentication types."
                )

            if api_key:
                configure_api_key(api_key=api_key, alias=alias)
            if base_url:
                configure_base_url(base_url=base_url, alias=alias)
            if eval_url:
                configure_eval_url(eval_url=eval_url, alias=alias)
            if access_token:
                configure_access_token(access_token=access_token, alias=alias)
            if project_id:
                configure_project_id(project_id=project_id, alias=alias)
            if organization_id:
                configure_organization_id(organization_id=organization_id, alias=alias)


def configure_api_key(api_key: str, alias: str = "default"):
    settings = get_settings()
    settings.set_api_key(api_key, alias)
    Console.write_stdout(f"GEAI API KEY for alias '{alias}' saved successfully!")


def configure_base_url(base_url: str, alias: str = "default"):
    settings = get_settings()
    settings.set_base_url(base_url, alias)
    Console.write_stdout(f"GEAI API BASE URL for alias '{alias}' saved successfully!")


def configure_eval_url(eval_url: str, alias: str = "default"):
    settings = get_settings()
    settings.set_eval_url(eval_url, alias)
    Console.write_stdout(f"GEAI API EVAL URL for alias '{alias}' saved successfully!")


def configure_access_token(access_token: str, alias: str = "default"):
    settings = get_settings()
    settings.set_access_token(access_token, alias)
    Console.write_stdout(f"GEAI OAUTH2 ACCESS TOKEN for alias '{alias}' saved successfully!")


def configure_project_id(project_id: str, alias: str = "default"):
    settings = get_settings()
    settings.set_project_id(project_id, alias)
    Console.write_stdout(f"GEAI PROJECT ID for alias '{alias}' saved successfully!")


def configure_organization_id(organization_id: str, alias: str = "default"):
    settings = get_settings()
    settings.set_organization_id(organization_id, alias)
    Console.write_stdout(f"GEAI ORGANIZATION ID for alias '{alias}' saved successfully!")


def display_alias_list():
    settings = get_settings()
    for alias, url in settings.list_aliases().items():
        Console.write_stdout(f"Alias: {alias} -> Base URL: {url}")


def remove_alias_from_config(alias: str):
    delete_confirmed = str(input(f"-> Are you sure you want to delete {alias} from config file? (y/N) "))
    if delete_confirmed.lower() in ["yes", "y"]:
        settings = get_settings()
        settings.remove_alias(alias)
        Console.write_stdout(f"Alias {alias} removed from configuration file.")
    else:
        Console.write_stdout(f"Alias {alias} kept in configuration file.")


configuration_options = (
    Option(
        "api_key",
        ["--key", "-k"],
        "Set GEAI API KEY",
        True
    ),
    Option(
        "base_url",
        ["--url", "-u"],
        "Set GEAI API BASE URL",
        True
    ),
    Option(
        "eval_url",
        ["--eval-url", "--eu"],
        "Set GEAI API EVAL URL for the evaluation module",
        True
    ),
    Option(
        "eval_url",
        ["--eval-url", "--eu"],
        "Set GEAI API EVAL URL for the evaluation module",
        True
    ),
    Option(
        "access_token",
        ["--access-token", "--at"],
        "Set GEAI_OAUTH_ACCESS_TOKEN for Oauth2 authentication in requests",
        True
    ),
    Option(
        "project_id",
        ["--project-id", "--pid"],
        "Set GEAI_PROJECT_ID for header configuration in some requests",
        True
    ),
    Option(
        "organization_id",
        ["--organization-id", "--oid"],
        "Set GEAI_ORGANIZATION_ID for header configuration in some requests",
        True
    ),
    Option(
        "profile_alias",
        ["--profile-alias", "--pa"],
        "Set alias for settings section",
        True
    ),
    Option(
        "list",
        ["--list", "-l"],
        "List available alias",
        False
    ),
    Option(
        "remove_alias",
        ["--remove-alias", "--ra"],
        "Remove selected alias",
        True
    ),

)
