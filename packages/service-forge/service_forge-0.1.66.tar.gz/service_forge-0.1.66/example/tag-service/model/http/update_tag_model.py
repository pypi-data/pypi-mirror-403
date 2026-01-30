from service_forge.workflow.registry.sf_base_model import SfBaseModel

class UpdateTagModel(SfBaseModel):
    id: str
    name: str
    description: str
    example: str