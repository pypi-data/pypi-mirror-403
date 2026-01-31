from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class UpdateWarehouseSnapshotRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]
    properties: NotRequired[WarehouseSnapshotUpdateProperties]

class CreateWarehouseSnapshotRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]
    creationPayload: NotRequired[WarehouseSnapshotCreationPayload]

class WarehouseSnapshotUpdateProperties(TypedDict, total=False):
    snapshotDateTime: str

class WarehouseSnapshotCreationPayload(TypedDict, total=False):
    parentWarehouseId: str
    snapshotDateTime: NotRequired[str]
