from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateAnomalyDetectorRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateAnomalyDetectorDefinitionRequest(TypedDict, total=False):
    definition: AnomalyDetectorDefinition

class CreateAnomalyDetectorRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[AnomalyDetectorDefinition]

class AnomalyDetectorDefinition(TypedDict, total=False):
    format: NotRequired[Literal['AnomalyDetectorV1']]
    parts: List[AnomalyDetectorDefinitionPart]

class AnomalyDetectorDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
