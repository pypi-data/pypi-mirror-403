from pydantic import Field, BaseModel
from typing import Annotated, Generic

from src.imaging.types.annotation import ListOfDiagnosisTypes
from ..enums.annotation import DiagnosisType, DiagnosisTypeT


class DiagnosisMixin(BaseModel, Generic[DiagnosisTypeT]):
    """
    Generic mixin for diagnosis types.
    Untuk single diagnosis type.
    """

    diagnosis: Annotated[
        DiagnosisTypeT,
        Field(
            ...,
            description="Diagnosis type",
            examples=DiagnosisType.choices(),
        ),
    ]


class DiagnosesMixin(BaseModel):
    """
    Mixin untuk multiple diagnosis types.
    """

    diagnoses: Annotated[
        ListOfDiagnosisTypes,
        Field(
            ...,
            description="List of diagnosis types",
            examples=DiagnosisType.choices(),
        ),
    ]
