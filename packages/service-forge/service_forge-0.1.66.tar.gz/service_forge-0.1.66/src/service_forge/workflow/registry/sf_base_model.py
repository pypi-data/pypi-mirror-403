from __future__ import annotations
from pydantic import BaseModel

from service_forge.utils.register import Register

class SfBaseModel(BaseModel):
    def __init_subclass__(cls) -> None:
        if cls.__name__ not in ["SfBaseModel"]:
            sf_basemodel_register.register(cls.__name__, cls)
        return super().__init_subclass__()

sf_basemodel_register = Register[SfBaseModel]()