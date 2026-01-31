from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateCopyJobRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateCopyJobRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[CopyJobDefinition]

class UpdateCopyJobDefinitionRequest(TypedDict, total=False):
    definition: CopyJobDefinition

class CopyJobDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[CopyJobDefinitionPart]

class CopyJobDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
