from typing import Optional
from pydantic import BaseModel, ConfigDict


class GoogleUserDataResponse(BaseModel):
    model_config = ConfigDict(extra="allow") #* Allowed by default, just for explicitness.

    id: str
    email: str
    verified_email: bool
    name: str
    given_name: str
    family_name: str
    picture: str

class OauthChildUserDataResponse(BaseModel):
    oauth_user_id: str
    user_name: str
    email: str
    is_verified_email: bool
    full_name: str
    image_url: Optional[str]


