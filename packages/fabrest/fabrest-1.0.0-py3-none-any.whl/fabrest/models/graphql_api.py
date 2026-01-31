from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateGraphQLApiRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[GraphQLApiPublicDefinition]

class UpdateGraphQLApiRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateGraphQLApiDefinitionRequest(TypedDict, total=False):
    definition: GraphQLApiPublicDefinition

class GraphQLApiPublicDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[GraphQLApiPublicDefinitionPart]

class GraphQLApiPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
