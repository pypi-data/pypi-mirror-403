LOG_EVENTS = {
    "api_error": {"level": "error", "template": "API error {code}: {message}"},
    "request_timeout": {"level": "error", "template": "Request timed out"},
    "throttling_timeout": {
        "level": "error",
        "template": "Throttling handler timed out",
    },
    "pagination_timeout": {
        "level": "error",
        "template": "Pagination handler timed out",
    },
    "item_name_in_use_timeout": {
        "level": "error",
        "template": "Item name in use handler timed out",
    },
    "lro_started": {"level": "info", "template": "LRO started"},
    "lro_status": {"level": "info", "template": "LRO status {status}"},
    "lro_timeout": {"level": "error", "template": "LRO handler timed out"},
    "lro_final_timeout": {
        "level": "error",
        "template": "LRO final fetch timed out",
    },
    "job_started": {"level": "info", "template": "Job started"},
    "job_status": {"level": "info", "template": "Job status {status}"},
    "job_timeout": {"level": "error", "template": "Job handler timed out"},
}
