from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class CreateMLExperimentRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    folderId: NotRequired[str]

class UpdateMLExperimentRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]
