from uuid import uuid4

from oauthz.protocols import OauthChildProtocol, OauthChildUserDataResponse


class MockOauthChild (OauthChildProtocol):
    def get_redirect_url(self, current_server_base_url: str) -> str:
        return "https://www.google.com"
    
    def get_token_with_code(self, ephemeral_code: str, current_server_base_url: str):
        return "mock_token"
    
    def get_user_data_with_token(self, access_token: str):
        return OauthChildUserDataResponse(
            oauth_user_id="mock_user_id",
            user_name="mock_user_name",
            email="mock_email@example.com" + str(uuid4()),
            is_verified_email=True,
            full_name="mock_full_name",
            image_url="mock_image_url"
        )






