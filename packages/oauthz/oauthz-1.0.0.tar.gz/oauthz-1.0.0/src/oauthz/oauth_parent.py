import asyncio
from dataclasses import dataclass

from oauthz.protocols import OauthChildProtocol, OauthChildUserDataResponse



@dataclass
class Oauthz ():
    
    current_server_base_url: str

    def get_redirect_url(self, oauth_child: OauthChildProtocol) -> str:
        return oauth_child.get_redirect_url(self.current_server_base_url)

    async def get_token_with_code_async(self, oauth_child: OauthChildProtocol, ephemeral_code: str) -> str:

        loop = asyncio.get_running_loop()

        token =  await loop.run_in_executor(
            None, #* Default thread pool created by asyncio.
            oauth_child.get_token_with_code, #* Callable.
            #* Arguments:
            ephemeral_code,
            self.current_server_base_url
        )

        return token

    async def get_user_data_by_token_async(self, oauth_child: OauthChildProtocol, access_token: str) -> OauthChildUserDataResponse:
        loop = asyncio.get_running_loop()

        oauth_user_data = await loop.run_in_executor(
            None, #* Default thread pool created by asyncio.
            oauth_child.get_user_data_with_token, #* Callable.
            #* Arguments:
            access_token,
        )

        return oauth_user_data