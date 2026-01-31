from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateKQLQuerysetDefinitionRequest(TypedDict, total=False):
    definition: KQLQuerysetDefinition

class UpdateKQLQuerysetRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateKQLQuerysetRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[KQLQuerysetDefinition]

class KQLQuerysetDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[KQLQuerysetDefinitionPart]

class KQLQuerysetDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
