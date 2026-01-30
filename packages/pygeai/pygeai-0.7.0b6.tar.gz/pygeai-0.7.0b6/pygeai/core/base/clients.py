from abc import ABC
from pygeai import logger

from pygeai.core.base.session import get_session, Session
from pygeai.core.common.exceptions import MissingRequirementException, MixedAuthenticationException
from pygeai.core.services.rest import GEAIApiService


class BaseClient(ABC):
    _logged_session_config = None

    def __init__(
        self, 
        api_key: str = None, 
        base_url: str = None, 
        alias: str = None, 
        *,
        access_token: str = None, 
        project_id: str = None,
        organization_id: str = None,
        allow_mixed_auth: bool = True
    ):
        """
        Initialize a client with authentication credentials.
        
        Authentication Options:
        1. API Key: Provide api_key and base_url
        2. OAuth 2.0: Provide access_token, project_id, and base_url
        3. From credentials: Provide alias to load from config
        
        :param api_key: GEAI API KEY to access services
        :param base_url: URL for GEAI instance to be used
        :param alias: Alias to use from credentials file
        :param access_token: OAuth 2.0 access token (keyword-only)
        :param project_id: Project ID for OAuth authentication (keyword-only)
        :param organization_id: Organization ID for OAuth authentication (keyword-only)
        :param allow_mixed_auth: Allow both api_key and access_token (default: False)
        :raises: MissingRequirementException - If authentication configuration is incomplete
        :raises: ValueError - If authentication configuration is invalid
        """
        
        # Case 1: Use credentials from alias
        if not (api_key or access_token) and alias:
            self.__session = get_session(alias)
            if not self.__session:
                raise MissingRequirementException(
                    "API KEY and BASE URL must be defined in order to use this functionality"
                )
        
        # Case 2: Direct credential provision
        elif (api_key or access_token) and base_url:
            # Validate auth parameters before mutating singleton session
            if access_token and api_key and not allow_mixed_auth:
                raise MixedAuthenticationException(
                    "Cannot specify both 'api_key' and 'access_token'. "
                    "Use 'allow_mixed_auth=True' to allow both (OAuth will take precedence)."
                )
            
            if access_token and not project_id:
                raise MissingRequirementException(
                    "project_id is required when using access_token for OAuth authentication"
                )
            
            # Get singleton session and update its properties
            # Note: Setters automatically update auth_type via _determine_auth_type()
            self.__session = get_session()
            self.__session.api_key = api_key
            self.__session.access_token = access_token
            self.__session.project_id = project_id
            self.__session.organization_id = organization_id
            self.__session.base_url = base_url
        
        # Case 3: Use default session
        else:
            self.__session = get_session()
        
        if self.session is None:
            raise MissingRequirementException(
                "Cannot access this functionality without setting API_KEY and BASE_URL"
            )
        
        # Log session config only once per unique configuration
        session_config_key = (
            self.session.alias,
            self.session.base_url,
            self.session.auth_type
        )
        
        if BaseClient._logged_session_config != session_config_key:
            self._log_authentication_info()
            BaseClient._logged_session_config = session_config_key
        
        # Initialize API service with active token
        token = self.session.get_active_token()
        
        self.__api_service = GEAIApiService(
            base_url=self.session.base_url,
            token=token,
            project_id=self.session.project_id,
            organization_id=self.session.organization_id
        )

    def _log_authentication_info(self):
        """Log authentication configuration for debugging."""
        if self.session.is_oauth():
            logger.info("Using OAuth 2.0 authentication")
            logger.info(f"Project ID: {self.session.project_id}")
            if self.session.organization_id:
                logger.info(f"Organization ID: {self.session.organization_id}")
        elif self.session.is_api_key():
            logger.info("Using API Key authentication")
        else:
            logger.warning("No authentication method configured")
        
        logger.info(f"Base URL: {self.session.base_url}")
        logger.info(f"Alias: {self.session.alias}")

    @property
    def session(self):
        return self.__session

    @session.setter
    def session(self, session: Session):
        self.__session = session

    @property
    def api_service(self):
        return self.__api_service

    @api_service.setter
    def api_service(self, api_service: GEAIApiService):
        self.__api_service = api_service
