from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateMirroredDatabaseDefinitionRequest(TypedDict, total=False):
    definition: MirroredDatabaseDefinition

class UpdateMirroredDatabaseRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateMirroredDatabaseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: MirroredDatabaseDefinition

class MirroredDatabaseDefinition(TypedDict, total=False):
    parts: List[MirroredDatabaseDefinitionPart]

class MirroredDatabaseDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
