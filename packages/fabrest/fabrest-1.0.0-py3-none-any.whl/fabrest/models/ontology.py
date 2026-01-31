from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateOntologyRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateOntologyDefinitionRequest(TypedDict, total=False):
    definition: OntologyDefinition

class CreateOntologyRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    definition: NotRequired[OntologyDefinition]

class OntologyDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[OntologyDefinitionPart]

class OntologyDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

PayloadType = Literal['InlineBase64']
