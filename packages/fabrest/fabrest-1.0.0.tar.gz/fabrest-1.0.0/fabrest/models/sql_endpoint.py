from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class SqlAuditSettingsUpdate(TypedDict, total=False):
    state: NotRequired[AuditSettingsState]
    retentionDays: NotRequired[int]

class SqlEndpointRefreshMetadataRequest(TypedDict, total=False):
    timeout: NotRequired[Duration]
    recreateTables: NotRequired[bool]

AuditSettingsState = Literal['Enabled', 'Disabled']

class Duration(TypedDict, total=False):
    value: float
    timeUnit: Literal['Seconds', 'Minutes', 'Hours', 'Days']
