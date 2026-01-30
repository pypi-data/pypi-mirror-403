from service_forge.workflow.registry.sf_base_model import SfBaseModel

class CreateTagModel(SfBaseModel):
    name: str
    description: str
    example: str