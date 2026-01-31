from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateNotebookRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[NotebookDefinition]

class UpdateNotebookDefinitionRequest(TypedDict, total=False):
    definition: NotebookDefinition

class UpdateNotebookRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class NotebookDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[NotebookDefinitionPart]

class NotebookDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
