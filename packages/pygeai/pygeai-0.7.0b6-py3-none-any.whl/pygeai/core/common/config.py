import os
import sys
from pathlib import Path
import configparser

from pygeai import logger

HOME_DIR = Path.home()
SETTINGS_DIR = HOME_DIR / ".geai"
SETTINGS_DIR.mkdir(parents=True, exist_ok=True)


class SettingsManager:
    """
    Base class to handle settings.
    If environment variables are defined, it retrieves settings from them first.
    Else, it looks for settings in the .geai/credentials file
    """

    GEAI_SETTINGS_DIR = str(SETTINGS_DIR)
    GEAI_CREDS_FILE = SETTINGS_DIR / "credentials"

    def __init__(self, credentials_file: str = None):
        self.config = configparser.ConfigParser()
        
        if credentials_file:
            self.GEAI_CREDS_FILE = Path(credentials_file)
            logger.debug(f"Using custom credentials file: {self.GEAI_CREDS_FILE}")
        
        if self.GEAI_CREDS_FILE.exists():
            self.config.read(self.GEAI_CREDS_FILE)
        else:
            self.GEAI_CREDS_FILE.touch()
            sys.stdout.write(f"INFO: Credentials file not found. Creating empty one at {self.GEAI_CREDS_FILE}\n")

    def has_value(self, setting_key: str, alias: str):
        """Checks if a setting value exists for a specific alias in the credentials file."""
        return alias in self.config and setting_key in self.config[alias]

    def get_setting_value(self, setting_key: str, alias: str):
        """Reads a setting value for a specific alias from the credentials file."""
        if alias not in self.config:
            logger.warning(f"Alias '{alias}' not found in the credentials file.")
            return
        
        if setting_key not in self.config[alias]:
            logger.debug(f"'{setting_key}' not found in alias '{alias}' in the credentials file.\n")

            if setting_key.lower() == "geai_api_eval_url" or ("geai_oauth_access_token" in self.config[alias] and setting_key.lower() in ["geai_project_id", "geai_organization_id"]):
                sys.stdout.write(f"'{setting_key}' not found in alias '{alias}' in the credentials file. Adding empty value\n")

            if setting_key.lower() == "geai_api_eval_url":
                self.set_eval_url("", alias)

            if "geai_oauth_access_token" in self.config[alias]:
                if setting_key.lower() == "geai_project_id":
                    self.set_project_id("", alias)
                if setting_key.lower() == "geai_organization_id":
                    self.set_organization_id("", alias)

        return self.config[alias].get(setting_key, "")

    def set_setting_value(self, setting_key: str, setting_value: str, alias: str):
        """Writes or updates a setting value for a specific alias in the credentials file."""
        if alias not in self.config:
            self.config.add_section(alias)

        self.config[alias][setting_key] = setting_value

        with self.GEAI_CREDS_FILE.open("w") as file:
            self.config.write(file)

    def get_api_key(self, alias: str = "default"):
        api_key = os.environ.get("GEAI_API_KEY") if not alias or alias == "default" else None
        if not api_key:
            api_key = self.get_setting_value("GEAI_API_KEY", alias)

        return api_key

    def set_api_key(self, api_key, alias: str = "default"):
        self.set_setting_value("GEAI_API_KEY", api_key, alias)

    def get_base_url(self, alias: str = "default"):
        base_url = os.environ.get("GEAI_API_BASE_URL") if not alias or alias == "default" else None
        if not base_url:
            base_url = self.get_setting_value("GEAI_API_BASE_URL", alias)

        return base_url

    def set_base_url(self, base_url, alias: str = "default"):
        self.set_setting_value("GEAI_API_BASE_URL", base_url, alias)

    def get_access_token(self, alias: str = "default"):
        access_token = os.environ.get("GEAI_OAUTH_ACCESS_TOKEN") if not alias or alias == "default" else None
        if not access_token:
            access_token = self.get_setting_value("GEAI_OAUTH_ACCESS_TOKEN", alias)

        return access_token

    def set_access_token(self, access_token, alias: str = "default"):
        self.set_setting_value("GEAI_OAUTH_ACCESS_TOKEN", access_token, alias)

    def get_project_id(self, alias: str = "default"):
        project_id = os.environ.get("GEAI_PROJECT_ID") if not alias or alias == "default" else None
        if not project_id:
            project_id = self.get_setting_value("GEAI_PROJECT_ID", alias)

        return project_id

    def set_project_id(self, project_id, alias: str = "default"):
        self.set_setting_value("GEAI_PROJECT_ID", project_id, alias)

    def get_eval_url(self, alias: str = "default"):
        eval_url = os.environ.get("GEAI_API_EVAL_URL") if not alias or alias == "default" else None
        if not eval_url:
            eval_url = self.get_setting_value("GEAI_API_EVAL_URL", alias)

        return eval_url

    def set_eval_url(self, eval_url, alias: str = "default"):
        self.set_setting_value("GEAI_API_EVAL_URL", eval_url, alias)

    def get_organization_id(self, alias: str = "default"):
        organization_id = os.environ.get("GEAI_ORGANIZATION_ID") if not alias or alias == "default" else None
        if not organization_id:
            organization_id = self.get_setting_value("GEAI_ORGANIZATION_ID", alias)

        return organization_id

    def set_organization_id(self, organization_id, alias: str = "default"):
        self.set_setting_value("GEAI_ORGANIZATION_ID", organization_id, alias)

    def list_aliases(self):
        """Returns a dict of all aliases and their base URLs."""
        return {
            section: self.config[section].get("GEAI_API_BASE_URL", "")
            for section in self.config.sections()
        }

    def remove_alias(self, alias: str):
        """Removes a specific alias and its settings from the credentials file."""
        if alias in self.config:
            self.config.remove_section(alias)
            with self.GEAI_CREDS_FILE.open("w") as file:
                self.config.write(file)
            logger.info(f"Alias '{alias}' removed from the credentials file.")
        else:
            logger.warning(f"Alias '{alias}' not found in the credentials file.")


_settings_instance = None


def get_settings(credentials_file: str = None):
    """
    Get or create the SettingsManager instance.
    
    :param credentials_file: Optional path to a custom credentials file.
                            If provided on first call, uses that file.
                            Subsequent calls ignore this parameter.
    :return: SettingsManager instance
    """
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = SettingsManager(credentials_file=credentials_file)
    return _settings_instance


def reset_settings():
    """Reset the settings instance. Useful for testing."""
    global _settings_instance
    _settings_instance = None


if __name__ == "__main__":
    settings = get_settings()
    geai_base_url = settings.get_base_url()
    geai_eval_url = settings.get_eval_url()
    print(f"base_url: {geai_base_url}")
    print(f"eval_url: {geai_eval_url}")
