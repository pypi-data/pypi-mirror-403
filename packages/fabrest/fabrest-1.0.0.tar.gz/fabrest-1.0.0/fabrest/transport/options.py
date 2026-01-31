from dataclasses import dataclass
from typing import Any, Dict, Optional


@dataclass
class RequestOptions:
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    wait_for_completion: bool = True
    throttle_retry_interval: Optional[int] = None
    lro_check_interval: Optional[int] = None
    job_check_interval: Optional[int] = None
    item_name_in_use_max_retries: int = 6
    item_name_in_use_retry_interval: int = 60
    max_retries: int = 0
    retry_interval: int = 5
    raw_response: bool = False
