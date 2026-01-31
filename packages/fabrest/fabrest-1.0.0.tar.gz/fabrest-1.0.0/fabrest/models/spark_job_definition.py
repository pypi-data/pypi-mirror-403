from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateSparkJobDefinitionRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class CreateSparkJobDefinitionRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[SparkJobDefinitionPublicDefinition]

class UpdateSparkJobDefinitionDefinitionRequest(TypedDict, total=False):
    definition: SparkJobDefinitionPublicDefinition

class RunSparkJobDefinitionRequest(TypedDict, total=False):
    executionData: NotRequired[ExecutionData]

class SparkJobDefinitionPublicDefinition(TypedDict, total=False):
    format: NotRequired[SparkJobDefinitionFormat]
    parts: List[SparkJobDefinitionPublicDefinitionPart]

class ExecutionData(TypedDict, total=False):
    executableFile: NotRequired[str]
    mainClass: NotRequired[str]
    commandLineArguments: NotRequired[str]
    additionalLibraryUris: NotRequired[List[libraryuris]]
    environmentId: NotRequired[ItemReference]
    defaultLakehouseId: NotRequired[ItemReference]

SparkJobDefinitionFormat = Literal['SparkJobDefinitionV1', 'SparkJobDefinitionV2']

class SparkJobDefinitionPublicDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

libraryuris = str

class ItemReference(TypedDict, total=False):
    referenceType: ItemReferenceType

PayloadType = Literal['InlineBase64']

ItemReferenceType = Literal['ById']
