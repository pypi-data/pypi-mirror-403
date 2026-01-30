import sys
import warnings
from typing import Optional

from pygeai import logger
from pygeai.core.common.config import get_settings
from pygeai.core.common.constants import AuthType
from pygeai.core.common.exceptions import MissingRequirementException, MixedAuthenticationException
from pygeai.core.singleton import Singleton


_session = None


class Session(metaclass=Singleton):
    """
    A session to store configuration state required to interact with different resources.
    
    Authentication Methods:
    - API Key: Use api_key parameter
    - OAuth 2.0: Use access_token and project_id parameters
    
    :param api_key: str - API key to interact with GEAI (mutually exclusive with access_token unless allow_mixed_auth=True)
    :param base_url: str - Base URL of the GEAI instance
    :param eval_url: Optional[str] - Optional evaluation endpoint URL
    :param access_token: Optional[str] - OAuth 2.0 access token (keyword-only, requires project_id)
    :param project_id: Optional[str] - Project ID for OAuth authentication (keyword-only, requires access_token)
    :param organization_id: Optional[str] - Organization ID for OAuth authentication (keyword-only)
    :param alias: Optional[str] - Alias name for this session
    :param allow_mixed_auth: bool - If True, allow both api_key and access_token (access_token takes precedence). Default False.
    :return: Session - Instance of the Session class
    :raises: ValueError - If authentication configuration is invalid
    """

    def __init__(
            self,
            api_key: str = None,
            base_url: str = None,
            eval_url: Optional[str] = None,
            *,
            access_token: Optional[str] = None,
            project_id: Optional[str] = None,
            organization_id: Optional[str] = None,
            alias: Optional[str] = None,
            allow_mixed_auth: bool = True,
    ):
        # Validate authentication configuration
        if api_key and access_token and not allow_mixed_auth:
            raise MixedAuthenticationException(
                "Cannot specify both 'api_key' and 'access_token'. "
                "Use 'api_key' for API Key authentication or 'access_token' with 'project_id' for OAuth 2.0. "
                "Set allow_mixed_auth=True to allow both (access_token will take precedence)."
            )
        
        if access_token and not project_id:
            raise MissingRequirementException(
                "OAuth 2.0 authentication requires 'project_id'. "
                "Provide project_id when using access_token."
            )
        
        if project_id and not access_token:
            warnings.warn(
                "project_id provided without access_token. "
                "project_id is only used with OAuth 2.0 authentication.",
                UserWarning
            )
        
        if not api_key and not access_token:
            logger.warning("No authentication method configured. API calls may fail.")
        
        if not base_url:
            logger.warning("Cannot instantiate session without base_url")

        self.__api_key = api_key
        self.__base_url = base_url
        self.__eval_url = eval_url
        self.__access_token = access_token
        self.__project_id = project_id
        self.__organization_id = organization_id
        self.__alias = alias if alias else "default"
        self.__auth_type = self._determine_auth_type()

        global _session
        _session = self

    def _determine_auth_type(self) -> AuthType:
        """Determine the active authentication type based on configuration."""
        if self.__access_token and self.__project_id:
            return AuthType.OAUTH_TOKEN
        elif self.__api_key:
            return AuthType.API_KEY
        else:
            return AuthType.NONE

    @property
    def auth_type(self) -> AuthType:
        """Get the current authentication type."""
        return self.__auth_type

    @property
    def api_key(self):
        return self.__api_key

    @api_key.setter
    def api_key(self, api_key: str):
        """Set API key and update auth type."""
        self.__api_key = api_key
        self.__auth_type = self._determine_auth_type()

    @property
    def base_url(self):
        return self.__base_url

    @base_url.setter
    def base_url(self, base_url: str):
        self.__base_url = base_url

    @property
    def eval_url(self):
        return self.__eval_url

    @eval_url.setter
    def eval_url(self, eval_url: str):
        self.__eval_url = eval_url

    @property
    def access_token(self):
        return self.__access_token

    @access_token.setter
    def access_token(self, access_token: str):
        """Set access token and update auth type."""
        self.__access_token = access_token
        self.__auth_type = self._determine_auth_type()

    @property
    def project_id(self):
        return self.__project_id

    @project_id.setter
    def project_id(self, project_id: str):
        """Set project ID and update auth type."""
        self.__project_id = project_id
        self.__auth_type = self._determine_auth_type()

    @property
    def organization_id(self):
        return self.__organization_id

    @organization_id.setter
    def organization_id(self, organization_id: str):
        self.__organization_id = organization_id

    @property
    def alias(self):
        return self.__alias

    @alias.setter
    def alias(self, alias: str):
        self.__alias = alias

    def is_oauth(self) -> bool:
        """Check if session is using OAuth authentication."""
        return self.__auth_type == AuthType.OAUTH_TOKEN

    def is_api_key(self) -> bool:
        """Check if session is using API key authentication."""
        return self.__auth_type == AuthType.API_KEY

    def get_active_token(self) -> Optional[str]:
        """Get the active authentication token based on auth type."""
        if self.is_oauth():
            return self.__access_token
        elif self.is_api_key():
            return self.__api_key
        return None


def get_session(alias: str = None) -> Session:
    """
    Session is a singleton object:
    On the first invocation, returns Session configured with the API KEY and BASE URL corresponding to the
    alias provided. On the following invocations, it returns the first object instantiated.
    
    Loads both API Key and OAuth 2.0 credentials from configuration if available.
    """
    try:
        settings = get_settings()
        global _session
        if _session is None:
            if not alias:
                alias = "default"
            
            _validate_alias(alias, allow_missing_default=True)

            api_key = settings.get_api_key(alias)
            access_token = settings.get_access_token(alias)
            
            # Allow mixed auth for backward compatibility
            # If both are configured, allow mixed (with warning logged in Session)
            allow_mixed = bool(api_key and access_token)
            
            if allow_mixed:
                logger.warning(
                    f"Both API key and OAuth token configured for alias '{alias}'. "
                    "OAuth token will take precedence. Consider using separate aliases."
                )

            _session = Session(
                api_key=api_key,
                base_url=settings.get_base_url(alias),
                eval_url=settings.get_eval_url(alias),
                access_token=access_token,
                project_id=settings.get_project_id(alias),
                organization_id=settings.get_organization_id(alias),
                alias=alias,
                allow_mixed_auth=allow_mixed,
            )
                
        elif _session is not None and alias:
            _validate_alias(alias, allow_missing_default=False)
            
            api_key = settings.get_api_key(alias)
            access_token = settings.get_access_token(alias)
            
            _session.alias = alias
            _session.api_key = api_key
            _session.base_url = settings.get_base_url(alias)
            _session.eval_url = settings.get_eval_url(alias)
            _session.access_token = access_token
            _session.project_id = settings.get_project_id(alias)
            _session.organization_id = settings.get_organization_id(alias)

        return _session
    except ValueError as e:
        logger.warning(f"Warning: API_KEY and/or BASE_URL not set. {e}")
        sys.stdout.write("Warning: API_KEY and/or BASE_URL not set. Please run geai configure to set them up.\n")


def _validate_alias(alias: str, allow_missing_default: bool = False):
    settings = get_settings()
    available_aliases = settings.list_aliases()
    if alias not in available_aliases:
        if allow_missing_default and alias == "default":
            return
        raise MissingRequirementException(
            f"The profile '{alias}' doesn't exist. Use 'geai configure --list' to see available profiles."
        )


def reset_session():
    """
    Reset the session instance. Useful for testing.
    
    This clears both the module-level _session variable and the
    Singleton metaclass cache to ensure proper test isolation.
    """
    global _session
    _session = None
    
    from pygeai.core.singleton import Singleton
    Singleton.reset_instance(Session)
