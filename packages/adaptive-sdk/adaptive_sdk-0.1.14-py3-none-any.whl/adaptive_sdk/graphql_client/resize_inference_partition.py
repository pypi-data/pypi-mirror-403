from pydantic import Field
from .base_model import BaseModel

class ResizeInferencePartition(BaseModel):
    """@public"""
    resize_inference_partition: str = Field(alias='resizeInferencePartition')