from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateCustomPoolRequest(TypedDict, total=False):
    name: NotRequired[str]
    nodeFamily: NotRequired[NodeFamily]
    nodeSize: NotRequired[NodeSize]
    autoScale: NotRequired[AutoScaleProperties]
    dynamicExecutorAllocation: NotRequired[DynamicExecutorAllocationProperties]

class UpdateWorkspaceSparkSettingsRequest(TypedDict, total=False):
    automaticLog: NotRequired[AutomaticLogProperties]
    highConcurrency: NotRequired[HighConcurrencyProperties]
    pool: NotRequired[PoolProperties]
    environment: NotRequired[EnvironmentProperties]
    job: NotRequired[SparkJobsProperties]

class CreateCustomPoolRequest(TypedDict, total=False):
    name: str
    nodeFamily: NodeFamily
    nodeSize: NodeSize
    autoScale: AutoScaleProperties
    dynamicExecutorAllocation: DynamicExecutorAllocationProperties

NodeFamily = Literal['MemoryOptimized']

NodeSize = Literal['Small', 'Medium', 'Large', 'XLarge', 'XXLarge']

class AutoScaleProperties(TypedDict, total=False):
    enabled: bool
    minNodeCount: int
    maxNodeCount: int

class DynamicExecutorAllocationProperties(TypedDict, total=False):
    enabled: bool
    minExecutors: int
    maxExecutors: int

class AutomaticLogProperties(TypedDict, total=False):
    enabled: bool

class HighConcurrencyProperties(TypedDict, total=False):
    notebookInteractiveRunEnabled: NotRequired[bool]
    notebookPipelineRunEnabled: NotRequired[bool]

class PoolProperties(TypedDict, total=False):
    customizeComputeEnabled: NotRequired[bool]
    defaultPool: NotRequired[InstancePool]
    starterPool: NotRequired[StarterPoolProperties]

class EnvironmentProperties(TypedDict, total=False):
    name: NotRequired[str]
    runtimeVersion: NotRequired[str]

class SparkJobsProperties(TypedDict, total=False):
    conservativeJobAdmissionEnabled: NotRequired[bool]
    sessionTimeoutInMinutes: NotRequired[int]

class InstancePool(TypedDict, total=False):
    name: NotRequired[str]
    type: NotRequired[CustomPoolType]
    id: NotRequired[str]

class StarterPoolProperties(TypedDict, total=False):
    maxNodeCount: NotRequired[int]
    maxExecutors: NotRequired[int]

CustomPoolType = Literal['Workspace', 'Capacity']
