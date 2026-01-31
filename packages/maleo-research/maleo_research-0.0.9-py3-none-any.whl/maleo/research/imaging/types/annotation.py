from uuid import UUID
from ..enums.annotation import DiagnosisType


IdentifierValueType = int | UUID
ListOfDiagnosisTypes = list[DiagnosisType]
OptListOfDiagnosisTypes = ListOfDiagnosisTypes | None
