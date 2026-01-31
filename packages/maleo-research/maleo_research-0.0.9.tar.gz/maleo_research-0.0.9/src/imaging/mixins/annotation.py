from pydantic import BaseModel, Field
from typing import Annotated, Generic, Literal, TypeGuard
from uuid import UUID
from nexo.schemas.mixins.identity import Identifier
from nexo.types.dict import OptStrToAnyDict
from nexo.types.string import OptStr
from nexo.types.uuid import OptListOfUUIDsT
from ..enums.annotation import IdentifierType
from ..types.annotation import IdentifierValueType, OptListOfDiagnosisTypes


class Description(BaseModel):
    description: Annotated[OptStr, Field(None, description="Imaging's description")] = (
        None
    )


class Impression(BaseModel):
    impression: Annotated[OptStr, Field(None, description="Imaging's name")] = None


class Diagnosis(BaseModel):
    diagnoses: Annotated[
        OptListOfDiagnosisTypes, Field(None, description="List of diagnosis types")
    ] = None


class Observation(BaseModel):
    observation: Annotated[
        OptStrToAnyDict, Field(None, description="Imaging's Observation")
    ] = None


class AnnotationIds(BaseModel, Generic[OptListOfUUIDsT]):
    annotation_ids: Annotated[
        OptListOfUUIDsT, Field(..., description="Annotation's ids")
    ]


class AnnotationIdentifier(Identifier[IdentifierType, IdentifierValueType]):
    @property
    def column_and_value(self) -> tuple[str, IdentifierValueType]:
        return self.type.column, self.value


class IdAnnotationIdentifier(Identifier[Literal[IdentifierType.ID], int]):
    type: Annotated[
        Literal[IdentifierType.ID],
        Field(IdentifierType.ID, description="Identifier's type"),
    ] = IdentifierType.ID
    value: Annotated[int, Field(..., description="Identifier's value", ge=1)]


class UUIDAnnotationIdentifier(Identifier[Literal[IdentifierType.UUID], UUID]):
    type: Annotated[
        Literal[IdentifierType.UUID],
        Field(IdentifierType.UUID, description="Identifier's type"),
    ] = IdentifierType.UUID


AnyAnnotationIdentifier = (
    AnnotationIdentifier | IdAnnotationIdentifier | UUIDAnnotationIdentifier
)


def is_id_identifier(
    identifier: AnyAnnotationIdentifier,
) -> TypeGuard[IdAnnotationIdentifier]:
    return identifier.type is IdentifierType.ID and isinstance(identifier.value, int)


def is_uuid_identifier(
    identifier: AnyAnnotationIdentifier,
) -> TypeGuard[UUIDAnnotationIdentifier]:
    return identifier.type is IdentifierType.UUID and isinstance(identifier.value, UUID)
