from pydantic import BaseModel, Field
from typing import (
    Annotated,
    Generic,
    Literal,
    Self,
    TypeVar,
    overload,
)
from uuid import UUID, uuid4
from nexo.enums.status import (
    ListOfDataStatuses,
    FULL_DATA_STATUSES,
)
from nexo.schemas.mixins.filter import convert as convert_filter
from nexo.schemas.mixins.identity import (
    IdentifierMixin,
    Ids,
    UUIDs,
    UUIDOrganizationIds,
    UUIDUserIds,
)
from nexo.schemas.mixins.sort import convert as convert_sort
from nexo.schemas.operation.enums import ResourceOperationStatusUpdateType
from nexo.schemas.parameter import (
    ReadSingleParameter as BaseReadSingleParameter,
    ReadPaginatedMultipleParameter,
    StatusUpdateParameter as BaseStatusUpdateParameter,
    DeleteSingleParameter as BaseDeleteSingleParameter,
)
from nexo.types.dict import StrToAnyDict, OptStrToAnyDict
from nexo.types.integer import OptListOfInts
from nexo.types.string import OptStr
from nexo.types.uuid import OptListOfUUIDs, OptUUID
from ..enums.annotation import IdentifierType
from ..mixins.annotation import AnnotationIdentifier
from ..types.annotation import (
    IdentifierValueType,
    ListOfDiagnosisTypes,
    OptListOfDiagnosisTypes,
)


class CreateParameter(BaseModel):
    annotation_id: Annotated[UUID, Field(uuid4(), description="Annotation ID")] = (
        uuid4()
    )
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    content_type: Annotated[str, Field(..., description="Content type")]
    image: Annotated[bytes, Field(..., description="Image data")]
    filename: Annotated[str, Field(..., description="File name")]
    description: Annotated[OptStr, Field(None, description="Description")] = None
    impression: Annotated[OptStr, Field(None, description="Impression")] = None
    diagnoses: Annotated[
        OptListOfDiagnosisTypes, Field(None, description="List of diagnoses")
    ] = None
    observation: Annotated[
        OptStrToAnyDict, Field(None, description="Observation data")
    ] = None

    def to_insert_data(self) -> "InsertData":
        return InsertData.from_create_parameter(self)


class InsertData(BaseModel):
    uuid: Annotated[UUID, Field(uuid4(), description="Record ID")] = uuid4()
    organization_id: Annotated[OptUUID, Field(None, description="Organization ID")] = (
        None
    )
    user_id: Annotated[UUID, Field(..., description="User ID")]
    filename: Annotated[str, Field(..., description="File name")]
    description: Annotated[OptStr, Field(None, description="Description")] = None
    impression: Annotated[OptStr, Field(None, description="Impression")] = None
    diagnoses: Annotated[
        OptListOfDiagnosisTypes, Field(None, description="List of diagnoses")
    ] = None
    observation: Annotated[
        OptStrToAnyDict, Field(..., description="Observation data")
    ] = None

    @classmethod
    def from_create_parameter(cls, parameters: CreateParameter) -> Self:
        return cls(
            uuid=parameters.annotation_id,
            organization_id=parameters.organization_id,
            user_id=parameters.user_id,
            filename=parameters.filename,
            description=parameters.description,
            impression=parameters.impression,
            diagnoses=parameters.diagnoses,
            observation=parameters.observation,
        )


class ReadMultipleParameter(
    ReadPaginatedMultipleParameter,
    UUIDUserIds[OptListOfUUIDs],
    UUIDOrganizationIds[OptListOfUUIDs],
    UUIDs[OptListOfUUIDs],
    Ids[OptListOfInts],
):
    @property
    def _query_param_fields(self) -> set[str]:
        return {
            "ids",
            "uuids",
            "statuses",
            "organization_ids",
            "user_ids",
            "search",
            "page",
            "limit",
            "use_cache",
        }

    def to_query_params(self) -> StrToAnyDict:
        params = self.model_dump(
            mode="json", include=self._query_param_fields, exclude_none=True
        )
        params["filters"] = convert_filter(self.date_filters)
        params["sorts"] = convert_sort(self.sort_columns)
        params = {k: v for k, v in params.items()}
        return params


class ReadSingleParameter(BaseReadSingleParameter[AnnotationIdentifier]):
    @classmethod
    def from_identifier(
        cls,
        identifier: AnnotationIdentifier,
        statuses: ListOfDataStatuses = FULL_DATA_STATUSES,
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(identifier=identifier, statuses=statuses, use_cache=use_cache)

    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        statuses: ListOfDataStatuses = list(FULL_DATA_STATUSES),
        use_cache: bool = True,
    ) -> "ReadSingleParameter":
        return cls(
            identifier=AnnotationIdentifier(
                type=identifier_type, value=identifier_value
            ),
            statuses=statuses,
            use_cache=use_cache,
        )

    def to_query_params(self) -> StrToAnyDict:
        return self.model_dump(
            mode="json", include={"statuses", "use_cache"}, exclude_none=True
        )


class FullUpdateData(BaseModel):
    description: Annotated[str, Field(..., description="Description")]
    impression: Annotated[str, Field(..., description="Impression")]
    diagnoses: Annotated[
        ListOfDiagnosisTypes, Field(..., description="List of diagnoses")
    ]
    observation: Annotated[StrToAnyDict, Field(..., description="observation")]


class PartialUpdateData(BaseModel):
    description: Annotated[OptStr, Field(None, description="Description")] = None
    impression: Annotated[OptStr, Field(None, description="Impression")] = None
    diagnoses: Annotated[
        OptListOfDiagnosisTypes, Field(None, description="List of diagnoses")
    ] = None
    observation: Annotated[OptStrToAnyDict, Field(None, description="observation")] = (
        None
    )


UpdateDataT = TypeVar("UpdateDataT", FullUpdateData, PartialUpdateData)


class UpdateDataMixin(BaseModel, Generic[UpdateDataT]):
    data: UpdateDataT = Field(..., description="Update data")


class UpdateParameter(
    UpdateDataMixin[UpdateDataT],
    IdentifierMixin[AnnotationIdentifier],
    Generic[UpdateDataT],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
    ) -> "UpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        data: UpdateDataT,
    ) -> "UpdateParameter":
        return cls(
            identifier=AnnotationIdentifier(
                type=identifier_type, value=identifier_value
            ),
            data=data,
        )


class StatusUpdateParameter(
    BaseStatusUpdateParameter[AnnotationIdentifier],
):
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.ID],
        identifier_value: int,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: Literal[IdentifierType.UUID],
        identifier_value: UUID,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @overload
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter": ...
    @classmethod
    def new(
        cls,
        identifier_type: IdentifierType,
        identifier_value: IdentifierValueType,
        type: ResourceOperationStatusUpdateType,
    ) -> "StatusUpdateParameter":
        return cls(
            identifier=AnnotationIdentifier(
                type=identifier_type, value=identifier_value
            ),
            type=type,
        )


class DeleteSingleParameter(BaseDeleteSingleParameter[AnnotationIdentifier]):
    @overload
    @classmethod
    def new(
        cls, identifier_type: Literal[IdentifierType.ID], identifier_value: int
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls, identifier_type: Literal[IdentifierType.UUID], identifier_value: UUID
    ) -> "DeleteSingleParameter": ...
    @overload
    @classmethod
    def new(
        cls, identifier_type: IdentifierType, identifier_value: IdentifierValueType
    ) -> "DeleteSingleParameter": ...
    @classmethod
    def new(
        cls, identifier_type: IdentifierType, identifier_value: IdentifierValueType
    ) -> "DeleteSingleParameter":
        return cls(
            identifier=AnnotationIdentifier(
                type=identifier_type, value=identifier_value
            )
        )
