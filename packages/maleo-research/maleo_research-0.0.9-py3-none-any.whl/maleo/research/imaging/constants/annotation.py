from copy import deepcopy
from typing import Callable
from uuid import UUID
from nexo.schemas.resource import ResourceIdentifier
from ..enums.annotation import IdentifierType
from ..types.annotation import IdentifierValueType
from .common import IMAGING_RESOURCE


IDENTIFIER_TYPE_VALUE_TYPE_MAP: dict[
    IdentifierType,
    Callable[..., IdentifierValueType],
] = {
    IdentifierType.ID: int,
    IdentifierType.UUID: UUID,
}


ANNOTATION_RESOURCE = deepcopy(IMAGING_RESOURCE)
ANNOTATION_RESOURCE.identifiers.append(
    ResourceIdentifier(key="annotation", name="Annotation", slug="annotations")
)
