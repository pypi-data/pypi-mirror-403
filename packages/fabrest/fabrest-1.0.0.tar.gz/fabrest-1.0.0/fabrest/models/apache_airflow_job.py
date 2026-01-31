from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateApacheAirflowJobRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateApacheAirflowJobDefinitionRequest(TypedDict, total=False):
    definition: ApacheAirflowJobDefinition

class CreateApacheAirflowJobRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[ApacheAirflowJobDefinition]

class CreateAirflowPoolTemplateRequest(TypedDict, total=False):
    name: str
    nodeSize: NodeSize
    computeScalability: ComputeScalability
    apacheAirflowJobVersion: str

class UpdateAirflowWorkspaceSettingsRequest(TypedDict, total=False):
    defaultPoolTemplateId: NotRequired[str]

class ApacheAirflowJobDefinition(TypedDict, total=False):
    parts: List[ApacheAirflowJobDefinitionPart]

NodeSize = Literal['Small', 'Large']

class ComputeScalability(TypedDict, total=False):
    minNodeCount: int
    maxNodeCount: int

class ApacheAirflowJobDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
