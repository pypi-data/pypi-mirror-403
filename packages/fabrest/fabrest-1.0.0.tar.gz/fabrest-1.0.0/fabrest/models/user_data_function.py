from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateUserDataFunctionDefinitionRequest(TypedDict, total=False):
    definition: UserDataFunctionPublicDefinition

class UpdateUserDataFunctionRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateUserDataFunctionRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    definition: NotRequired[UserDataFunctionPublicDefinition]

class UserDataFunctionPublicDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[UserDataFunctionPublicDefinitionPart]

class UserDataFunctionPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
