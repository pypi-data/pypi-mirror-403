from pydantic import Field
from .base_model import BaseModel

class RemoveModelFromUseCase(BaseModel):
    """@public"""
    remove_model_from_use_case: bool = Field(alias='removeModelFromUseCase')