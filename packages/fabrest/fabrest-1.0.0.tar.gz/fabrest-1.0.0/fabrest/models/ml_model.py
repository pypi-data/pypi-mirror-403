from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class ScoreDataRequest(TypedDict, total=False):
    formatType: NotRequired[FormatType]
    orientation: NotRequired[Orientation]
    inputs: List[List[Dict[str, Any]]]

class UpdateMLModelRequest(TypedDict, total=False):
    description: NotRequired[str]

class UpdateMLModelEndpointRequest(TypedDict, total=False):
    defaultVersionName: NotRequired[str]
    defaultVersionAssignmentBehavior: NotRequired[EndpointDefaultVersionConfigurationPolicy]

class UpdateMLModelEndpointVersionRequest(TypedDict, total=False):
    scaleRule: NotRequired[ScaleRule]

class CreateMLModelRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]

FormatType = Literal['dataframe']

Orientation = Literal['split', 'values', 'record', 'index', 'table']

EndpointDefaultVersionConfigurationPolicy = Literal['StaticallyConfigured', 'NotConfigured']

ScaleRule = Literal['AlwaysOn', 'AllowScaleToZero']
