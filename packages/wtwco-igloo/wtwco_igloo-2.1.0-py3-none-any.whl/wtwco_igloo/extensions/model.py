from datetime import datetime

from wtwco_igloo.api_client.models import ModelVersionType


class Model(object):
    """Represents a model in Igloo Cloud.

    Attributes:
        id (int): Identifier value of the model.
        model_name (str): Name of the model.
        version_name (str): Version name of the model.
        semantic_version (str): Semantic version of the model.
        upload_time (datetime): Optional. Time that the model version was uploaded.
        uploaded_by (str): Optional. User that uploaded the model version.
        type (ModelVersionType): Type of model version. Can be one of Finalized, InDevelopment or WTW.
    """

    def __init__(self, model_dict: dict) -> None:
        self.id: int = model_dict["id"]
        self.model_name: str = model_dict["model_name"]
        self.version_name: str = model_dict["version_name"]
        self.semantic_version: str = model_dict.get("semantic_version", "")
        self.upload_time: datetime | None = model_dict.get("upload_time")
        self.uploaded_by: str | None = model_dict.get("uploaded_by")
        self.type: ModelVersionType | None = model_dict.get("type")

    def __str__(self) -> str:
        return f"Model(id={self.id}, model_name='{self.model_name}', version_name='{self.version_name}')"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Model):
            return NotImplemented
        return self.id == other.id and self.model_name == other.model_name and self.version_name == other.version_name
