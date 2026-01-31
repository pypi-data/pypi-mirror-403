from enum import StrEnum
from typing import TypeVar
from nexo.types.string import ListOfStrs


class IdentifierType(StrEnum):
    ID = "id"
    UUID = "uuid"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]

    @property
    def column(self) -> str:
        return self.value


class DiagnosisType(StrEnum):
    TB = "tb"
    TB_AKTIF = "tb_aktif"
    PNEUMONIA = "pneumonia"
    HEALTHY = "healthy"

    @classmethod
    def choices(cls) -> ListOfStrs:
        return [e.value for e in cls]


DiagnosisTypeT = TypeVar("DiagnosisTypeT", bound=DiagnosisType)
