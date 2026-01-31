from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateWarehouseRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    creationPayload: NotRequired[WarehouseCreationPayload]

class UpdateWarehouseRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class SqlAuditSettingsUpdate(TypedDict, total=False):
    state: NotRequired[AuditSettingsState]
    retentionDays: NotRequired[int]

class CreateRestorePointRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateRestorePointRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class WarehouseCreationPayload(TypedDict, total=False):
    collationType: CollationType

AuditSettingsState = Literal['Enabled', 'Disabled']

CollationType = Literal['Latin1_General_100_BIN2_UTF8', 'Latin1_General_100_CI_AS_KS_WS_SC_UTF8']
