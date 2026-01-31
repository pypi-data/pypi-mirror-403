from pydantic import BaseModel, Field
from typing import Annotated
from uuid import UUID
from nexo.enums.status import DataStatus as DataStatusEnum, SimpleDataStatusMixin
from nexo.schemas.mixins.identity import DataIdentifier
from nexo.schemas.mixins.timestamp import LifecycleTimestamp
from nexo.types.string import OptStr
from nexo.types.uuid import OptUUID
from nexo.types.dict import OptStrToAnyDict
from .types.annotation import (
    OptListOfDiagnosisTypes,
)


class AnnotationDTO(
    SimpleDataStatusMixin[DataStatusEnum],
    LifecycleTimestamp,
    DataIdentifier,
):
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    filename: Annotated[str, Field(..., description="File's name")]
    description: Annotated[OptStr, Field(None, description="Description")] = None
    impression: Annotated[OptStr, Field(None, description="Impression")] = None
    diagnoses: Annotated[
        OptListOfDiagnosisTypes, Field(None, description="List of diagnoses")
    ] = None
    observation: Annotated[
        OptStrToAnyDict, Field(..., description="Observation data")
    ] = None


class AnnotationDTOMixin(BaseModel):
    annotation: Annotated[AnnotationDTO, Field(..., description="Annotation")]
