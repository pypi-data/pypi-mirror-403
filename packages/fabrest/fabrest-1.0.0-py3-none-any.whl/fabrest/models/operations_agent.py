from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateOperationsAgentRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateOperationsAgentDefinitionRequest(TypedDict, total=False):
    definition: OperationsAgentPublicDefinition

class CreateOperationsAgentRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[OperationsAgentPublicDefinition]

class OperationsAgentPublicDefinition(TypedDict, total=False):
    format: NotRequired[Literal['OperationsAgentV1']]
    parts: List[OperationsAgentPublicDefinitionPart]

class OperationsAgentPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
