from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class ExecuteQueryRequest(TypedDict, total=False):
    queryName: str
    customMashupDocument: NotRequired[str]

class CreateDataflowRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[DataflowDefinition]

class UpdateDataflowDefinitionRequest(TypedDict, total=False):
    definition: DataflowDefinition

class UpdateDataflowRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

CreateDataflowExecuteScheduleRequest = Dict[str, Any]

CreateDataflowApplyChangesScheduleRequest = Dict[str, Any]

class RunOnDemandDataflowExecuteJobRequest(TypedDict, total=False):
    executionData: NotRequired[DataflowExecutionPayload]

class DataflowDefinition(TypedDict, total=False):
    parts: List[DataflowDefinitionPart]

class DataflowExecutionPayload(TypedDict, total=False):
    executeOption: NotRequired[Literal['SkipApplyChanges', 'ApplyChangesIfNeeded']]
    parameters: NotRequired[List[ItemJobParameter]]

class DataflowDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

class ItemJobParameter(TypedDict, total=False):
    parameterName: str
    type: Literal['Automatic']
    value: Any

PayloadType = Literal['InlineBase64']
