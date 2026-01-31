from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class RemoveAllSharingLinksRequest(TypedDict, total=False):
    sharingLinkType: SharingLinkType

class AssignDomainWorkspacesByCapacitiesRequest(TypedDict, total=False):
    capacitiesIds: NotRequired[List[str]]

class AssignDomainWorkspacesByPrincipalsRequest(TypedDict, total=False):
    principals: NotRequired[List[Principal]]

class SetLabelsRequest(TypedDict, total=False):
    items: List[ItemInfo]
    labelId: str
    delegatedPrincipal: NotRequired[Principal]
    assignmentMethod: NotRequired[Literal['Standard', 'Priviledged']]

class UpdateDomainRequest(TypedDict, total=False):
    defaultLabelId: NotRequired[str]

class AssignDomainWorkspacesByIdsRequest(TypedDict, total=False):
    workspacesIds: NotRequired[List[str]]

class DomainRoleAssignmentRequest(TypedDict, total=False):
    type: DomainRole
    principals: NotRequired[List[Principal]]

class SyncRoleAssignmentsToSubdomainsRequest(TypedDict, total=False):
    role: DomainRole

class RemoveLabelsRequest(TypedDict, total=False):
    items: NotRequired[List[ItemInfo]]

class UpdateTagRequest(TypedDict, total=False):
    displayName: str

class RestoreWorkspaceRequest(TypedDict, total=False):
    newWorkspaceName: NotRequired[str]
    newWorkspaceAdminPrincipal: NotRequired[Principal]

class UpdateTenantSettingRequest(TypedDict, total=False):
    enabled: bool
    enabledSecurityGroups: NotRequired[List[TenantSettingSecurityGroup]]
    excludedSecurityGroups: NotRequired[List[TenantSettingSecurityGroup]]
    properties: NotRequired[List[TenantSettingProperty]]
    delegateToCapacity: NotRequired[bool]
    delegateToDomain: NotRequired[bool]
    delegateToWorkspace: NotRequired[bool]

class BulkRemoveSharingLinksRequest(TypedDict, total=False):
    items: List[ItemInfo]
    sharingLinkType: SharingLinkType

class DomainRoleUnassignmentRequest(TypedDict, total=False):
    type: DomainRole
    principals: NotRequired[List[Principal]]

class UnassignDomainWorkspacesByIdsRequest(TypedDict, total=False):
    workspacesIds: NotRequired[List[str]]

class UpdateDomainRequestPreview(TypedDict, total=False):
    contributorsScope: NotRequired[ContributorsScopeType]

class UpdateCapacityTenantSettingOverrideRequest(TypedDict, total=False):
    enabled: bool
    enabledSecurityGroups: NotRequired[List[TenantSettingSecurityGroup]]
    excludedSecurityGroups: NotRequired[List[TenantSettingSecurityGroup]]
    delegateToWorkspace: NotRequired[bool]

class CreateDomainRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    parentDomainId: NotRequired[str]

class CreateTagsRequest(TypedDict, total=False):
    scope: NotRequired[TagScope]
    createTagsRequest: List[CreateTagRequest]

SharingLinkType = Literal['OrgLink']

class Principal(TypedDict, total=False):
    id: str
    displayName: NotRequired[str]
    type: Literal['User', 'ServicePrincipal', 'Group', 'ServicePrincipalProfile', 'EntireTenant']
    userDetails: NotRequired[Principal_userDetails]
    servicePrincipalDetails: NotRequired[Principal_servicePrincipalDetails]
    groupDetails: NotRequired[Principal_groupDetails]
    servicePrincipalProfileDetails: NotRequired[Principal_servicePrincipalProfileDetails]

class ItemInfo(TypedDict, total=False):
    id: str
    type: ItemType

DomainRole = Literal['Admin', 'Contributor']

class TenantSettingSecurityGroup(TypedDict, total=False):
    graphId: str
    name: str

class TenantSettingProperty(TypedDict, total=False):
    name: NotRequired[str]
    value: NotRequired[str]
    type: NotRequired[TenantSettingPropertyType]

ContributorsScopeType = Literal['AllTenant', 'SpecificUsersAndGroups', 'AdminsOnly']

class TagScope(TypedDict, total=False):
    type: Literal['Tenant', 'Domain']

class CreateTagRequest(TypedDict, total=False):
    displayName: str

class Principal_userDetails(TypedDict, total=False):
    userPrincipalName: NotRequired[str]

class Principal_servicePrincipalDetails(TypedDict, total=False):
    aadAppId: NotRequired[str]

class Principal_groupDetails(TypedDict, total=False):
    groupType: NotRequired[Literal['Unknown', 'SecurityGroup', 'DistributionList']]

class Principal_servicePrincipalProfileDetails(TypedDict, total=False):
    parentPrincipal: NotRequired[Principal]

ItemType = Literal['Dashboard', 'Report', 'SemanticModel', 'PaginatedReport', 'Datamart', 'Lakehouse', 'Eventhouse', 'Environment', 'KQLDatabase', 'KQLQueryset', 'KQLDashboard', 'DataPipeline', 'Notebook', 'SparkJobDefinition', 'MLExperiment', 'MLModel', 'Warehouse', 'Eventstream', 'SQLEndpoint', 'MirroredWarehouse', 'MirroredDatabase', 'Reflex', 'GraphQLApi', 'MountedDataFactory', 'SQLDatabase', 'CopyJob', 'VariableLibrary', 'Dataflow', 'ApacheAirflowJob', 'WarehouseSnapshot', 'DigitalTwinBuilder', 'DigitalTwinBuilderFlow', 'MirroredAzureDatabricksCatalog', 'Map', 'AnomalyDetector', 'UserDataFunction', 'GraphModel', 'GraphQuerySet', 'SnowflakeDatabase', 'OperationsAgent', 'CosmosDBDatabase', 'Ontology', 'EventSchemaSet']

TenantSettingPropertyType = Literal['FreeText', 'Url', 'Boolean', 'MailEnabledSecurityGroup', 'Integer']
