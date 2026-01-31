from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateMountedDataFactoryRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateMountedDataFactoryDefinitionRequest(TypedDict, total=False):
    definition: MountedDataFactoryDefinition

class CreateMountedDataFactoryRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[MountedDataFactoryDefinition]

class MountedDataFactoryDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[MountedDataFactoryDefinitionPart]

class MountedDataFactoryDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
