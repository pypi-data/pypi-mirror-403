from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateSemanticModelDefinitionRequest(TypedDict, total=False):
    definition: SemanticModelDefinition

class UpdateSemanticModelRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateSemanticModelRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: SemanticModelDefinition

class BindSemanticModelConnectionRequest(TypedDict, total=False):
    connectionBinding: ConnectionBinding

class SemanticModelDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[SemanticModelDefinitionPart]

class ConnectionBinding(TypedDict, total=False):
    id: NotRequired[str]
    connectivityType: NotRequired[ConnectivityType]
    connectionDetails: ListConnectionDetails

class SemanticModelDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

ConnectivityType = Literal['ShareableCloud', 'PersonalCloud', 'OnPremisesGateway', 'OnPremisesGatewayPersonal', 'VirtualNetworkGateway', 'Automatic', 'None']

class ListConnectionDetails(TypedDict, total=False):
    path: str

PayloadType = Literal['InlineBase64']
