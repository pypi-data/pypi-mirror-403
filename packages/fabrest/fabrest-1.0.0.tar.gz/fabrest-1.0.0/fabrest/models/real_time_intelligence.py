from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class NlToKqlRequest(TypedDict, total=False):
    itemIdForBilling: str
    clusterUrl: str
    naturalLanguage: str
    databaseName: str
    userShots: NotRequired[List[UserShot]]
    chatMessages: NotRequired[List[ChatMessage]]

class UserShot(TypedDict, total=False):
    naturalLanguage: str
    kqlQuery: str

class ChatMessage(TypedDict, total=False):
    role: Role
    content: str

Role = Literal['System', 'User', 'Assistant']
