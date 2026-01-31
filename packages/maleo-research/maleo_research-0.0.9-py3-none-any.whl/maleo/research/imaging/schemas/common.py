from pydantic import BaseModel, Field
from typing import Annotated
from uuid import UUID

from nexo.schemas.mixins.identity import DataIdentifier
from nexo.types.dict import OptStrToAnyDict
from nexo.types.string import OptStr
from nexo.types.uuid import OptUUID
from ..types.annotation import OptListOfDiagnosisTypes


class AnnotationSchema(
    DataIdentifier,
):
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    filename: Annotated[str, Field(..., description="File's name")]
    url: Annotated[OptStr, Field(None, description="File's URL")] = None
    description: Annotated[OptStr, Field(None, description="Description")] = None
    impression: Annotated[OptStr, Field(None, description="Impression")] = None
    diagnoses: Annotated[
        OptListOfDiagnosisTypes, Field(None, description="List of diagnoses")
    ] = None
    observation: Annotated[OptStrToAnyDict, Field(None, description="Observation")] = (
        None
    )


class AnnotationSchemaMixin(BaseModel):
    annotation: Annotated[AnnotationSchema, Field(..., description="Annotation")]
