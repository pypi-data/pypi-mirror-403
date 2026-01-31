from typing import Any, Optional
from pydantic import Field
from .base_model import BaseModel
from .enums import SessionStatus

class DatasetUploadProcessingStatus(BaseModel):
    """@public"""
    dataset_upload_processing_status: 'DatasetUploadProcessingStatusDatasetUploadProcessingStatus' = Field(alias='datasetUploadProcessingStatus')

class DatasetUploadProcessingStatusDatasetUploadProcessingStatus(BaseModel):
    """@public"""
    dataset_id: Any = Field(alias='datasetId')
    status: SessionStatus
    total_parts: int = Field(alias='totalParts')
    processed_parts: int = Field(alias='processedParts')
    progress: float
    error: Optional[str]
DatasetUploadProcessingStatus.model_rebuild()