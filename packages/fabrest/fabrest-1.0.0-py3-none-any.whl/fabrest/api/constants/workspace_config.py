from typing import Literal


WORKSPACE_CONFIG = {
    "Spark": "spark",
    "ManagedPrivateEndpoint": "managedPrivateEndpoints",
    "RoleAssignment": "roleAssignments",
    "Folder": "folders",
    "Git": "git",
}

WorkspaceConfigTypeLiteral = Literal[
    "spark",
    "managedPrivateEndpoints",
    "roleAssignments",
    "folders",
    "git",
]


class WorkspaceConfigType:
    Spark = WORKSPACE_CONFIG["Spark"]
    ManagedPrivateEndpoint = WORKSPACE_CONFIG["ManagedPrivateEndpoint"]
    RoleAssignment = WORKSPACE_CONFIG["RoleAssignment"]
    Folder = WORKSPACE_CONFIG["Folder"]
    Git = WORKSPACE_CONFIG["Git"]
