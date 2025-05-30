from pydantic import BaseModel, Field
from typing import Optional, List

class FacebookUser(BaseModel):
    id: str
    name: str
    profileUrl: str = Field(alias="profileUrl")
    profilePic: str = Field(alias="profilePic")

class FacebookMedia(BaseModel):
    thumbnail: Optional[str] = None
    type_name: Optional[str] = Field(None, alias="__typename")
    playable_duration_in_ms: Optional[int] = None

class FacebookPost(BaseModel):
    postId: str
    pageName: str
    url: str
    time: str
    timestamp: int
    user: FacebookUser
    text: str
    likes: int
    comments: Optional[int] = 0
    shares: int
    isVideo: Optional[bool] = False
    viewsCount: Optional[int] = None
    media: Optional[List[FacebookMedia]] = None
