from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateDigitalTwinBuilderFlowRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateDigitalTwinBuilderFlowDefinitionRequest(TypedDict, total=False):
    definition: DigitalTwinBuilderFlowPublicDefinition

class CreateDigitalTwinBuilderFlowRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    creationPayload: NotRequired[DigitalTwinBuilderFlowCreationPayload]
    definition: NotRequired[DigitalTwinBuilderFlowPublicDefinition]

class DigitalTwinBuilderFlowPublicDefinition(TypedDict, total=False):
    parts: List[DigitalTwinBuilderFlowPublicDefinitionPart]

class DigitalTwinBuilderFlowCreationPayload(TypedDict, total=False):
    digitalTwinBuilderItemReference: ItemReference

class DigitalTwinBuilderFlowPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

class ItemReference(TypedDict, total=False):
    referenceType: ItemReferenceType

PayloadType = Literal['InlineBase64']

ItemReferenceType = Literal['ById']
