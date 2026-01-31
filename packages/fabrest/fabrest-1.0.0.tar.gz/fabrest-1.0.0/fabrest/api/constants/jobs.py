from typing import Literal


JOB_COLLECTIONS = {
    "Schedule": "schedules",
    "Instance": "instances",
}

JOB_TYPES = {
    "Notebook": "RunNotebook",
    "DataPipeline": "Pipeline",
    "SparkJobDefinition": "sparkjob",
    "CopyJob": "CopyJob",
    "TableMaintenance": "TableMaintenance",
    "RefreshGraph": "RefreshGraph",
    "ApplyChange": "ApplyChanges",
    "Execute": "Execute",
}

JOB_STATUSES = {
    "CANCELLED": "Cancelled",
    "COMPLETED": "Completed",
    "DEDUPE": "Deduped",
    "FAILED": "Failed",
    "IN_PROGRESS": "InProgress",
    "NOT_STARTED": "NotStarted",
}

LRO_STATUSES = {
    "FAILED": "Failed",
    "NOTSTARTED": "NotStarted",
    "RUNNING": "Running",
    "SUCCEEDED": "Succeeded",
    "UNDEFINED": "Undefined",
}

JobTypeLiteral = Literal[
    "RunNotebook",
    "Pipeline",
    "sparkjob",
    "CopyJob",
    "TableMaintenance",
    "RefreshGraph",
    "ApplyChanges",
    "Execute",
]


class JobCollection:
    Schedule = JOB_COLLECTIONS["Schedule"]
    Instance = JOB_COLLECTIONS["Instance"]


class JobType:
    Notebook = JOB_TYPES["Notebook"]
    DataPipeline = JOB_TYPES["DataPipeline"]
    SparkJobDefinition = JOB_TYPES["SparkJobDefinition"]
    CopyJob = JOB_TYPES["CopyJob"]
    TableMaintenance = JOB_TYPES["TableMaintenance"]
    RefreshGraph = JOB_TYPES["RefreshGraph"]
    ApplyChange = JOB_TYPES["ApplyChange"]
    Execute = JOB_TYPES["Execute"]


class JobStatus:
    CANCELLED = JOB_STATUSES["CANCELLED"]
    COMPLETED = JOB_STATUSES["COMPLETED"]
    DEDUPE = JOB_STATUSES["DEDUPE"]
    FAILED = JOB_STATUSES["FAILED"]
    IN_PROGRESS = JOB_STATUSES["IN_PROGRESS"]
    NOT_STARTED = JOB_STATUSES["NOT_STARTED"]


class LongRunningOperationStatus:
    FAILED = LRO_STATUSES["FAILED"]
    NOTSTARTED = LRO_STATUSES["NOTSTARTED"]
    RUNNING = LRO_STATUSES["RUNNING"]
    SUCCEEDED = LRO_STATUSES["SUCCEEDED"]
    UNDEFINED = LRO_STATUSES["UNDEFINED"]
