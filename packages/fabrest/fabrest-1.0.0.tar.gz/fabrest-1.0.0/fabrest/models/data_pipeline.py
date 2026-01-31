from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateDataPipelineRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[DataPipelineDefinition]

class UpdateDataPipelineDefinitionRequest(TypedDict, total=False):
    definition: DataPipelineDefinition

class UpdateDataPipelineRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class DataPipelineDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[DataPipelineDefinitionPart]

class DataPipelineDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
