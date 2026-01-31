from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateReportDefinitionRequest(TypedDict, total=False):
    definition: ReportDefinition

class CreateReportRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: ReportDefinition

class UpdateReportRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class ReportDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[ReportDefinitionPart]

class ReportDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
