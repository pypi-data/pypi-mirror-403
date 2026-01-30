
from dataclasses import dataclass
from typing import Any

import requests

from oauthz.protocols import OauthChildProtocol, OauthChildUserDataResponse
from oauthz.protocols import GoogleUserDataResponse

@dataclass
class GoogleOauthChild (OauthChildProtocol):
    google_client_id: str
    router_google_oauth_callback_path: str
    google_client_secret: str

    def get_redirect_url(self, current_server_base_url: str) -> str:

        redirect_uri = current_server_base_url + self.router_google_oauth_callback_path
        return f"https://accounts.google.com/o/oauth2/v2/auth?client_id={self.google_client_id}&redirect_uri={redirect_uri}&response_type=code&scope=email%20profile"    


    def get_token_with_code(self, ephemeral_code: str, current_server_base_url: str):
        #$ The redirect_uri must be exactly the same URI that was used in the initial Google authorization request (/auth step).
        redirect_uri = current_server_base_url + self.router_google_oauth_callback_path

        response = requests.post("https://oauth2.googleapis.com/token", 
            data={
                "code": ephemeral_code,
                "client_id": self.google_client_id,
                "client_secret": self.google_client_secret,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri
            }
        )

        access_token: str = response.json()["access_token"]
        return access_token


    def get_user_data_with_token(self, access_token: str):
        response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo',
            headers={
                "Authorization": f"Bearer {access_token}"
            }
        )
        
        google_user_data_dict: dict[str, Any] = response.json()
        
        validated_google_user_data = GoogleUserDataResponse(**google_user_data_dict)

        oauth_user_data = OauthChildUserDataResponse(
            oauth_user_id=validated_google_user_data.id,
            user_name=validated_google_user_data.name,
            email=validated_google_user_data.email,
            is_verified_email=validated_google_user_data.verified_email,
            full_name=validated_google_user_data.name,
            image_url=validated_google_user_data.picture
        )

        return oauth_user_data
