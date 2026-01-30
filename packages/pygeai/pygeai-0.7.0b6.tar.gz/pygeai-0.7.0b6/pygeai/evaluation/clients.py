from pygeai.core.base.clients import BaseClient
from pygeai.core.common.exceptions import MissingRequirementException
from pygeai.core.services.rest import GEAIApiService


class EvaluationClient(BaseClient):

    def __init__(self, api_key: str = None, base_url: str = None, alias: str = None, eval_url: str = None, *,
                 access_token: str = None, project_id: str = None):
        super().__init__(api_key, base_url, alias, access_token=access_token, project_id=project_id)
        eval_url = self.session.eval_url if not eval_url else eval_url
        if not eval_url:
            raise MissingRequirementException("EVAL URL must be defined in order to use the Evaluation module.")

        self.session.eval_url = eval_url
        token = self.session.access_token if self.session.access_token else self.session.api_key
        self.api_service = GEAIApiService(base_url=self.session.eval_url, token=token, project_id=self.session.project_id)
