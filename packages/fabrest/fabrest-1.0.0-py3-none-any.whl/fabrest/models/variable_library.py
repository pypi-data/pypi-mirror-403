from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateVariableLibraryRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]
    properties: NotRequired[VariableLibraryProperties]

class UpdateVariableLibraryDefinitionRequest(TypedDict, total=False):
    definition: VariableLibraryPublicDefinition

class CreateVariableLibraryRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[VariableLibraryPublicDefinition]

class VariableLibraryProperties(TypedDict, total=False):
    activeValueSetName: str

class VariableLibraryPublicDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[VariableLibraryPublicDefinitionPart]

class VariableLibraryPublicDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

PayloadType = Literal['InlineBase64']
