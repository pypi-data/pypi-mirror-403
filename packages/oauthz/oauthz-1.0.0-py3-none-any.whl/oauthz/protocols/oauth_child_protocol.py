

from typing import Protocol

from .pydantic_schemas import OauthChildUserDataResponse


class  OauthChildProtocol(Protocol):

    def get_redirect_url(self, current_server_base_url: str) -> str: ...
    def get_token_with_code(self, ephemeral_code: str, current_server_base_url: str)-> str: ...
    def get_user_data_with_token(self, access_token: str) -> OauthChildUserDataResponse: ... 




