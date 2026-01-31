from pydantic import Field
from .base_model import BaseModel

class AddModelToUseCase(BaseModel):
    """@public"""
    add_model_to_use_case: bool = Field(alias='addModelToUseCase')