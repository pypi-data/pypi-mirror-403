from typing import Literal


COLLECTIONS = {
    "Workspace": "workspaces",
    "Admin": "admin",
    "Capacity": "capacities",
    "Connection": "connections",
    "DeploymentPipeline": "deploymentPipelines",
    "ExternalDataShare": "externalDataShares",
    "Gateway": "gateways",
    "Operation": "operations",
}

ADMIN_COLLECTIONS = {
    "Workspace": "workspaces",
    "Domain": "domains",
    "Item": "items",
    "Capacity": "capacities",
    "Tag": "tags",
    "User": "users",
}

WORKSPACE_OPERATIONS = {
    "AssignToCapacity": "assignToCapacity",
    "UnassignFromCapacity": "unassignFromCapacity",
    "ProvisionIdentity": "provisionIdentity",
}

GIT_OPERATIONS = {
    "UpdateFromGit": "updateFromGit",
    "InitializeConnection": "initializeConnection",
    "MyGitCredentials": "myGitCredentials",
    "Status": "status",
    "Connection": "connection",
    "Disconnect": "disconnect",
    "Connect": "connect",
    "CommitToGit": "commitToGit",
}

CollectionLiteral = Literal[
    "workspaces",
    "admin",
    "capacities",
    "connections",
    "deploymentPipelines",
    "externalDataShares",
    "gateways",
    "operations",
]

AdminCollectionLiteral = Literal[
    "workspaces",
    "domains",
    "items",
    "capacities",
    "tags",
    "users",
]


class Collection:
    Workspace = COLLECTIONS["Workspace"]
    Admin = COLLECTIONS["Admin"]
    Capacity = COLLECTIONS["Capacity"]
    Connection = COLLECTIONS["Connection"]
    DeploymentPipeline = COLLECTIONS["DeploymentPipeline"]
    ExternalDataShare = COLLECTIONS["ExternalDataShare"]
    Gateway = COLLECTIONS["Gateway"]
    Operation = COLLECTIONS["Operation"]


class AdminCollection:
    Workspace = ADMIN_COLLECTIONS["Workspace"]
    Domain = ADMIN_COLLECTIONS["Domain"]
    Item = ADMIN_COLLECTIONS["Item"]
    Capacity = ADMIN_COLLECTIONS["Capacity"]
    Tag = ADMIN_COLLECTIONS["Tag"]
    User = ADMIN_COLLECTIONS["User"]


class WorkspaceOperation:
    AssignToCapacity = WORKSPACE_OPERATIONS["AssignToCapacity"]
    UnassignFromCapacity = WORKSPACE_OPERATIONS["UnassignFromCapacity"]
    ProvisionIdentity = WORKSPACE_OPERATIONS["ProvisionIdentity"]


class GitOperation:
    UpdateFromGit = GIT_OPERATIONS["UpdateFromGit"]
    InitializeConnection = GIT_OPERATIONS["InitializeConnection"]
    MyGitCredentials = GIT_OPERATIONS["MyGitCredentials"]
    Status = GIT_OPERATIONS["Status"]
    Connection = GIT_OPERATIONS["Connection"]
    Disconnect = GIT_OPERATIONS["Disconnect"]
    Connect = GIT_OPERATIONS["Connect"]
    CommitToGit = GIT_OPERATIONS["CommitToGit"]
