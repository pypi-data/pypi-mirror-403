from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

UpdateLakehouseRefreshMaterializedLakeViewsScheduleRequest = Dict[str, Any]

class UpdateLakehouseRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class RunOnDemandTableMaintenanceRequest(TypedDict, total=False):
    executionData: TableMaintenanceExecutionData

class CreateLakehouseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    creationPayload: NotRequired[LakehouseCreationPayload]
    definition: NotRequired[LakehouseDefinition]

class LoadTableRequest(TypedDict, total=False):
    relativePath: str
    pathType: Literal['File', 'Folder']
    fileExtension: NotRequired[str]
    mode: NotRequired[Literal['Overwrite', 'Append']]
    recursive: NotRequired[bool]
    formatOptions: NotRequired[FileFormatOptions]

CreateLakehouseRefreshMaterializedLakeViewsScheduleRequest = Dict[str, Any]

class UpdateLakehouseDefinitionRequest(TypedDict, total=False):
    definition: LakehouseDefinition

class TableMaintenanceExecutionData(TypedDict, total=False):
    tableName: str
    schemaName: NotRequired[str]
    optimizeSettings: NotRequired[OptimizeSettings]
    vacuumSettings: NotRequired[VacuumSettings]

class LakehouseCreationPayload(TypedDict, total=False):
    enableSchemas: bool

class LakehouseDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[LakehouseDefinitionPart]

class FileFormatOptions(TypedDict, total=False):
    format: Literal['Csv', 'Parquet']

class OptimizeSettings(TypedDict, total=False):
    zOrderBy: NotRequired[List[str]]
    vOrder: NotRequired[bool]

class VacuumSettings(TypedDict, total=False):
    retentionPeriod: NotRequired[str]

class LakehouseDefinitionPart(TypedDict, total=False):
    path: NotRequired[str]
    payload: NotRequired[str]
    payloadType: NotRequired[PayloadType]

PayloadType = Literal['InlineBase64']
