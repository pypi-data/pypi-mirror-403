from typing import Optional
from .base_model import BaseModel
from .fragments import UserData

class Me(BaseModel):
    """@public"""
    me: Optional['MeMe']

class MeMe(UserData):
    """@public"""
    pass
Me.model_rebuild()