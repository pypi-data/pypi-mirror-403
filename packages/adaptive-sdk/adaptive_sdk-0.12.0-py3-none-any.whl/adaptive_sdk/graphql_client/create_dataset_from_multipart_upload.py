from typing import Any, Optional
from pydantic import Field
from .base_model import BaseModel
from .enums import SessionStatus

class CreateDatasetFromMultipartUpload(BaseModel):
    """@public"""
    create_dataset_from_multipart_upload: 'CreateDatasetFromMultipartUploadCreateDatasetFromMultipartUpload' = Field(alias='createDatasetFromMultipartUpload')

class CreateDatasetFromMultipartUploadCreateDatasetFromMultipartUpload(BaseModel):
    """@public"""
    dataset_id: Any = Field(alias='datasetId')
    status: SessionStatus
    total_parts: int = Field(alias='totalParts')
    processed_parts: int = Field(alias='processedParts')
    progress: float
    error: Optional[str]
CreateDatasetFromMultipartUpload.model_rebuild()