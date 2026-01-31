from pydantic import Field
from .base_model import BaseModel
from .fragments import ModelServiceData

class DeployModel(BaseModel):
    """@public"""
    deploy_model: 'DeployModelDeployModel' = Field(alias='deployModel')

class DeployModelDeployModel(ModelServiceData):
    """@public"""
    pass
DeployModel.model_rebuild()