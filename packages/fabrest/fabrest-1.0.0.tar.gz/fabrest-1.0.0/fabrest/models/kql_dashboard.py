from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateKQLDashboardRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[KQLDashboardDefinition]

class UpdateKQLDashboardDefinitionRequest(TypedDict, total=False):
    definition: KQLDashboardDefinition

class UpdateKQLDashboardRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class KQLDashboardDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[KQLDashboardDefinitionPart]

class KQLDashboardDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

PayloadType = Literal['InlineBase64']
