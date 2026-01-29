from __future__ import annotations
import yaml
from pydantic import BaseModel

class SfMetadataInject(BaseModel):
    deployment: bool = True
    service_config: bool = True
    ingress: bool = True
    dockerfile: bool = True
    pyproject_toml: bool = True

class SfMetadata(BaseModel):
    name: str
    version: str
    description: str
    service_config: str
    config_only: bool
    env: list[dict]
    inject: SfMetadataInject = SfMetadataInject()
    enable_auth_middleware: bool = True
    mode: str = "debug"

    @classmethod
    def from_yaml_file(cls, filepath: str) -> SfMetadata:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        return cls(**data)

def load_metadata(path: str) -> SfMetadata:
    return SfMetadata.from_yaml_file(path)

def save_metadata(meta: SfMetadata, path: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        yaml.safe_dump(meta.model_dump(), f, allow_unicode=True)