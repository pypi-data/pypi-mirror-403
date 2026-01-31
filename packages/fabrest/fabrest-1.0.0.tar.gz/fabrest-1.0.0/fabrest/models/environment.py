from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateEnvironmentRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    definition: NotRequired[EnvironmentDefinition]

class UpdateEnvironmentDefinitionRequest(TypedDict, total=False):
    definition: EnvironmentDefinition

class UpdateEnvironmentSparkComputeRequestPreview(TypedDict, total=False):
    instancePool: NotRequired[InstancePool]
    driverCores: NotRequired[int]
    driverMemory: NotRequired[str]
    executorCores: NotRequired[int]
    executorMemory: NotRequired[str]
    dynamicExecutorAllocation: NotRequired[DynamicExecutorAllocationProperties]
    sparkProperties: NotRequired[Dict[str, Any]]
    runtimeVersion: NotRequired[str]

class UpdateEnvironmentRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class RemoveExternalLibrariesRequest(TypedDict, total=False):
    name: str
    version: str

class UpdateEnvironmentSparkComputeRequest(TypedDict, total=False):
    instancePool: NotRequired[InstancePool]
    driverCores: NotRequired[int]
    driverMemory: NotRequired[CustomPoolMemory]
    executorCores: NotRequired[int]
    executorMemory: NotRequired[CustomPoolMemory]
    dynamicExecutorAllocation: NotRequired[DynamicExecutorAllocationProperties]
    sparkProperties: NotRequired[List[SparkProperty]]
    runtimeVersion: NotRequired[str]

class EnvironmentDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[EnvironmentDefinitionPart]

class InstancePool(TypedDict, total=False):
    id: NotRequired[str]
    name: NotRequired[str]
    type: NotRequired[CustomPoolType]

class DynamicExecutorAllocationProperties(TypedDict, total=False):
    enabled: bool
    minExecutors: int
    maxExecutors: int

CustomPoolMemory = Literal['28g', '56g', '112g', '224g', '400g']

class SparkProperty(TypedDict, total=False):
    key: NotRequired[str]
    value: NotRequired[str]

class EnvironmentDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

CustomPoolType = Literal['Workspace', 'Capacity']

PayloadType = Literal['InlineBase64']
