from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateCosmosDBDatabaseRequest(TypedDict, total=False):
    description: NotRequired[str]

class CreateCosmosDBDatabaseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    definition: NotRequired[CosmosDBDatabaseDefinition]

class UpdateCosmosDBDatabaseDefinitionRequest(TypedDict, total=False):
    definition: CosmosDBDatabaseDefinition

class CosmosDBDatabaseDefinition(TypedDict, total=False):
    parts: List[CosmosDBDatabaseDefinitionPart]

class CosmosDBDatabaseDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

PayloadType = Literal['InlineBase64']
