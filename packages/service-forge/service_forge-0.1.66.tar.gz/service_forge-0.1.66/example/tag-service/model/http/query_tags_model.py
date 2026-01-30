from service_forge.workflow.registry.sf_base_model import SfBaseModel

class QueryTagsModel(SfBaseModel):
    ids: str = ""
    page: int = 1
    page_size: int = 10
    sort_by: str = "created_at"
    order: str = "desc"