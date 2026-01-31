from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateMirroredAzureDatabricksCatalogRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    creationPayload: NotRequired[MirroredAzureDatabricksCatalogCreationPayload]
    definition: NotRequired[MirroredAzureDatabricksCatalogPublicDefinition]

class UpdateMirroredAzureDatabricksCatalogRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]
    publicUpdateableExtendedProperties: NotRequired[MirroredAzureDatabricksCatalogUpdatePayload]

class UpdatemirroredAzureDatabricksCatalogDefinitionRequest(TypedDict, total=False):
    definition: MirroredAzureDatabricksCatalogPublicDefinition

class MirroredAzureDatabricksCatalogCreationPayload(TypedDict, total=False):
    catalogName: str
    databricksWorkspaceConnectionId: str
    mirroringMode: MirroringModes
    storageConnectionId: NotRequired[str]

class MirroredAzureDatabricksCatalogPublicDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[MirroredAzureDatabricksCatalogPublicDefinitionPart]

class MirroredAzureDatabricksCatalogUpdatePayload(TypedDict, total=False):
    autoSync: NotRequired[AutoSync]
    mirroringMode: NotRequired[MirroringModes]
    storageConnectionId: NotRequired[str]

MirroringModes = Literal['Full', 'Partial']

class MirroredAzureDatabricksCatalogPublicDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

AutoSync = Literal['Enabled', 'Disabled']

PayloadType = Literal['InlineBase64']
