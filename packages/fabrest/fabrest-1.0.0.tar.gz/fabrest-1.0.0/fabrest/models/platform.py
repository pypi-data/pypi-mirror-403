from __future__ import annotations
from typing import Any, Dict, List, TypedDict
from typing import NotRequired, Literal, Union

class ApplyTagsRequest(TypedDict, total=False):
    tags: List[str]

class DeploymentPipelineStageRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    isPublic: NotRequired[bool]

class BulkCreateShortcutsRequest(TypedDict, total=False):
    createShortcutRequests: List[CreateShortcutWithTransformRequest]

class ImmutabilityPolicyRequest(TypedDict, total=False):
    scope: ImmutabilityScope
    retentionDays: int

class CreateScheduleRequest(TypedDict, total=False):
    enabled: bool
    configuration: ScheduleConfig

class DeployRequest(TypedDict, total=False):
    sourceStageId: str
    targetStageId: str
    createdWorkspaceDetails: NotRequired[DeploymentPipelineNewWorkspaceConfiguration]
    note: NotRequired[str]
    items: NotRequired[List[ItemDeploymentRequest]]
    options: NotRequired[DeploymentOptions]

class UpdateFromGitRequest(TypedDict, total=False):
    workspaceHead: NotRequired[str]
    remoteCommitHash: str
    conflictResolution: NotRequired[WorkspaceConflictResolution]
    options: NotRequired[UpdateOptions]

class MoveItemRequest(TypedDict, total=False):
    targetFolderId: NotRequired[str]

class AddGatewayRoleAssignmentRequest(TypedDict, total=False):
    principal: Principal
    role: GatewayRole

class ModifyOneLakeDiagnosticSettingRequest(TypedDict, total=False):
    pass

class UpdateDeploymentPipelineRequest(TypedDict, total=False):
    pass

class AcceptExternalDataShareInvitationRequest(TypedDict, total=False):
    providerTenantId: str
    workspaceId: str
    itemId: str
    payload: ExternalDataShareAcceptRequestPayload

class CreateFolderRequest(TypedDict, total=False):
    displayName: str
    parentFolderId: NotRequired[str]

class BulkMoveItemsRequest(TypedDict, total=False):
    targetFolderId: NotRequired[str]
    items: List[str]

class AddConnectionRoleAssignmentRequest(TypedDict, total=False):
    principal: Principal
    role: ConnectionRole

class UpdateScheduleRequest(TypedDict, total=False):
    enabled: bool
    configuration: ScheduleConfig

class AssignWorkspaceToCapacityRequest(TypedDict, total=False):
    capacityId: str

class UpdateGitCredentialsRequest(TypedDict, total=False):
    source: GitCredentialsSource

class CreateManagedPrivateEndpointRequest(TypedDict, total=False):
    name: str
    targetPrivateLinkResourceId: str
    targetSubresourceType: NotRequired[str]
    requestMessage: NotRequired[str]
    targetFQDNs: NotRequired[List[str]]

class WorkspaceOutboundGateways(TypedDict, total=False):
    defaultAction: NotRequired[GatewayAccessActionType]
    allowedGateways: NotRequired[List[GatewayAccessRuleMetadata]]

class NetworkRules(TypedDict, total=False):
    defaultAction: NotRequired[DefaultAction]

class UpdateGatewayMemberRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    enabled: NotRequired[bool]

class WorkspaceNetworkingCommunicationPolicy(TypedDict, total=False):
    inbound: NotRequired[InboundRules]
    outbound: NotRequired[OutboundRules]

class InitializeGitConnectionRequest(TypedDict, total=False):
    initializationStrategy: NotRequired[InitializationStrategy]

class UpdateItemDefinitionRequest(TypedDict, total=False):
    definition: ItemDefinition

class MoveFolderRequest(TypedDict, total=False):
    targetFolderId: NotRequired[str]

class UpdateItemRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class UpdateWorkspaceRoleAssignmentRequest(TypedDict, total=False):
    role: WorkspaceRole

class CommitToGitRequest(TypedDict, total=False):
    mode: CommitMode
    workspaceHead: NotRequired[str]
    comment: NotRequired[str]
    items: NotRequired[List[ItemIdentifier]]

class CreateExternalDataShareRequest(TypedDict, total=False):
    paths: List[str]
    recipient: ExternalDataShareRecipient

class RunOnDemandItemJobRequest(TypedDict, total=False):
    executionData: NotRequired[Dict[str, Any]]

class CreateOrUpdateSingleDataAccessRoleRequest(TypedDict, total=False):
    value: NotRequired[List[DataAccessRoleBase]]

class UpdateGatewayRoleAssignmentRequest(TypedDict, total=False):
    role: GatewayRole

class AssignWorkspaceToDomainRequest(TypedDict, total=False):
    domainId: str

class WorkspaceOutboundConnections(TypedDict, total=False):
    defaultAction: NotRequired[ConnectionAccessActionType]
    rules: NotRequired[List[OutboundConnectionRule]]

class CreateShortcutRequest(TypedDict, total=False):
    path: str
    name: str
    target: CreatableShortcutTarget

class UpdateFolderRequest(TypedDict, total=False):
    displayName: str

class UnapplyTagsRequest(TypedDict, total=False):
    tags: List[str]

class CreateItemRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    type: ItemType
    folderId: NotRequired[str]
    definition: NotRequired[ItemDefinition]
    creationPayload: NotRequired[Dict[str, Any]]

class GitConnectRequest(TypedDict, total=False):
    gitProviderDetails: GitProviderDetails
    myGitCredentials: NotRequired[GitCredentials]

class UpdateConnectionRequest(TypedDict, total=False):
    connectivityType: ConnectivityType
    privacyLevel: NotRequired[PrivacyLevel]

class CreateDeploymentPipelineRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    stages: List[DeploymentPipelineStageRequest]

class UpdateWorkspaceRequest(TypedDict, total=False):
    displayName: NotRequired[str]
    description: NotRequired[str]

class DeploymentPipelineAssignWorkspaceRequest(TypedDict, total=False):
    workspaceId: str

class AddDeploymentPipelineRoleAssignmentRequest(TypedDict, total=False):
    principal: Principal
    role: DeploymentPipelineRole

class CreateWorkspaceRequest(TypedDict, total=False):
    displayName: str
    description: NotRequired[str]
    capacityId: NotRequired[str]
    domainId: NotRequired[str]

class CreateGatewayRequest(TypedDict, total=False):
    type: GatewayType

class AddWorkspaceRoleAssignmentRequest(TypedDict, total=False):
    principal: Principal
    role: WorkspaceRole

class UpdateConnectionRoleAssignmentRequest(TypedDict, total=False):
    role: ConnectionRole

class CreateOrUpdateDataAccessRolesRequest(TypedDict, total=False):
    value: NotRequired[List[DataAccessRole]]

class CreateConnectionRequest(TypedDict, total=False):
    connectivityType: ConnectivityType
    displayName: str
    connectionDetails: CreateConnectionDetails
    privacyLevel: NotRequired[PrivacyLevel]

class UpdateGatewayRequest(TypedDict, total=False):
    type: GatewayType
    displayName: NotRequired[str]

class CreateShortcutWithTransformRequest(TypedDict, total=False):
    transform: NotRequired[Transform]

ImmutabilityScope = Literal['DiagnosticLogs']

class ScheduleConfig(TypedDict, total=False):
    type: Literal['Cron', 'Daily', 'Weekly', 'Monthly']
    startDateTime: str
    endDateTime: str
    localTimeZoneId: str

class DeploymentPipelineNewWorkspaceConfiguration(TypedDict, total=False):
    name: str
    capacityId: NotRequired[str]

class ItemDeploymentRequest(TypedDict, total=False):
    sourceItemId: str
    itemType: ItemType

class DeploymentOptions(TypedDict, total=False):
    allowCrossRegionDeployment: NotRequired[bool]

class WorkspaceConflictResolution(TypedDict, total=False):
    conflictResolutionType: ConflictResolutionType
    conflictResolutionPolicy: ConflictResolutionPolicy

class UpdateOptions(TypedDict, total=False):
    allowOverrideItems: NotRequired[bool]

class Principal(TypedDict, total=False):
    id: str
    displayName: NotRequired[str]
    type: Literal['User', 'ServicePrincipal', 'Group', 'ServicePrincipalProfile', 'EntireTenant']
    userDetails: NotRequired[Principal_userDetails]
    servicePrincipalDetails: NotRequired[Principal_servicePrincipalDetails]
    groupDetails: NotRequired[Principal_groupDetails]
    servicePrincipalProfileDetails: NotRequired[Principal_servicePrincipalProfileDetails]

GatewayRole = Literal['Admin', 'ConnectionCreatorWithResharing', 'ConnectionCreator']

class ExternalDataShareAcceptRequestPayload(TypedDict, total=False):
    payloadType: Literal['ShortcutCreation']

ConnectionRole = Literal['User', 'UserWithReshare', 'Owner']

GitCredentialsSource = Literal['ConfiguredConnection', 'Automatic', 'None']

GatewayAccessActionType = Literal['Allow', 'Deny']

class GatewayAccessRuleMetadata(TypedDict, total=False):
    id: str

DefaultAction = Literal['Allow', 'Deny']

class InboundRules(TypedDict, total=False):
    publicAccessRules: NotRequired[NetworkRules]

class OutboundRules(TypedDict, total=False):
    publicAccessRules: NotRequired[NetworkRules]

InitializationStrategy = Literal['None', 'PreferRemote', 'PreferWorkspace']

class ItemDefinition(TypedDict, total=False):
    format: NotRequired[str]
    parts: List[ItemDefinitionPart]

WorkspaceRole = Literal['Admin', 'Member', 'Contributor', 'Viewer']

CommitMode = Literal['All', 'Selective']

class ItemIdentifier(TypedDict, total=False):
    objectId: NotRequired[str]
    logicalId: NotRequired[str]

class ExternalDataShareRecipient(TypedDict, total=False):
    userPrincipalName: str
    tenantId: NotRequired[str]

class DataAccessRoleBase(TypedDict, total=False):
    name: str
    decisionRules: List[DecisionRule]
    members: NotRequired[Members]

ConnectionAccessActionType = Literal['Allow', 'Deny']

class OutboundConnectionRule(TypedDict, total=False):
    connectionType: str
    defaultAction: NotRequired[ConnectionAccessActionType]
    allowedEndpoints: NotRequired[List[ConnectionRuleEndpointMetadata]]
    allowedWorkspaces: NotRequired[List[ConnectionRuleWorkspaceMetadata]]

class CreatableShortcutTarget(TypedDict, total=False):
    oneLake: NotRequired[OneLake]
    amazonS3: NotRequired[AmazonS3]
    adlsGen2: NotRequired[AdlsGen2]
    googleCloudStorage: NotRequired[GoogleCloudStorage]
    s3Compatible: NotRequired[S3Compatible]
    dataverse: NotRequired[Dataverse]
    azureBlobStorage: NotRequired[AzureBlobStorage]
    oneDriveSharePoint: NotRequired[OneDriveSharePoint]

ItemType = Literal['Dashboard', 'Report', 'SemanticModel', 'PaginatedReport', 'Datamart', 'Lakehouse', 'Eventhouse', 'Environment', 'KQLDatabase', 'KQLQueryset', 'KQLDashboard', 'DataPipeline', 'Notebook', 'SparkJobDefinition', 'MLExperiment', 'MLModel', 'Warehouse', 'Eventstream', 'SQLEndpoint', 'MirroredWarehouse', 'MirroredDatabase', 'Reflex', 'GraphQLApi', 'MountedDataFactory', 'SQLDatabase', 'CopyJob', 'VariableLibrary', 'Dataflow', 'ApacheAirflowJob', 'WarehouseSnapshot', 'DigitalTwinBuilder', 'DigitalTwinBuilderFlow', 'MirroredAzureDatabricksCatalog', 'Map', 'AnomalyDetector', 'UserDataFunction', 'GraphModel', 'GraphQuerySet', 'SnowflakeDatabase', 'OperationsAgent', 'CosmosDBDatabase', 'Ontology', 'EventSchemaSet']

class GitProviderDetails(TypedDict, total=False):
    gitProviderType: GitProviderType
    repositoryName: str
    branchName: str
    directoryName: str

class GitCredentials(TypedDict, total=False):
    source: GitCredentialsSource

ConnectivityType = Literal['ShareableCloud', 'PersonalCloud', 'OnPremisesGateway', 'OnPremisesGatewayPersonal', 'VirtualNetworkGateway', 'Automatic', 'None']

PrivacyLevel = Literal['None', 'Private', 'Organizational', 'Public']

DeploymentPipelineRole = Literal['Admin']

GatewayType = Literal['OnPremises', 'OnPremisesPersonal', 'VirtualNetwork']

class DataAccessRole(TypedDict, total=False):
    pass

class CreateConnectionDetails(TypedDict, total=False):
    creationMethod: str
    parameters: List[ConnectionDetailsParameter]

class Transform(TypedDict, total=False):
    type: Literal['csvToDelta']

ConflictResolutionType = Literal['Workspace']

ConflictResolutionPolicy = Literal['PreferRemote', 'PreferWorkspace']

class Principal_userDetails(TypedDict, total=False):
    userPrincipalName: NotRequired[str]

class Principal_servicePrincipalDetails(TypedDict, total=False):
    aadAppId: NotRequired[str]

class Principal_groupDetails(TypedDict, total=False):
    groupType: NotRequired[Literal['Unknown', 'SecurityGroup', 'DistributionList']]

class Principal_servicePrincipalProfileDetails(TypedDict, total=False):
    parentPrincipal: NotRequired[Principal]

class ItemDefinitionPart(TypedDict, total=False):
    path: str
    payload: str
    payloadType: PayloadType

class DecisionRule(TypedDict, total=False):
    effect: NotRequired[Literal['Permit']]
    permission: List[PermissionScope]
    constraints: NotRequired[DecisionRule_constraints]

class Members(TypedDict, total=False):
    fabricItemMembers: NotRequired[List[FabricItemMember]]
    microsoftEntraMembers: NotRequired[List[MicrosoftEntraMember]]

class ConnectionRuleEndpointMetadata(TypedDict, total=False):
    hostNamePattern: str

class ConnectionRuleWorkspaceMetadata(TypedDict, total=False):
    workspaceId: str

class OneLake(TypedDict, total=False):
    itemId: str
    workspaceId: str
    path: str
    connectionId: NotRequired[str]

class AmazonS3(TypedDict, total=False):
    location: str
    subpath: NotRequired[str]
    connectionId: str

class AdlsGen2(TypedDict, total=False):
    location: str
    subpath: str
    connectionId: str

class GoogleCloudStorage(TypedDict, total=False):
    location: str
    subpath: str
    connectionId: str

class S3Compatible(TypedDict, total=False):
    location: str
    subpath: str
    bucket: str
    connectionId: str

class Dataverse(TypedDict, total=False):
    environmentDomain: str
    connectionId: str
    deltaLakeFolder: str
    tableName: str

class AzureBlobStorage(TypedDict, total=False):
    location: str
    subpath: str
    connectionId: str

class OneDriveSharePoint(TypedDict, total=False):
    location: str
    subpath: str
    connectionId: str

GitProviderType = Literal['AzureDevOps', 'GitHub']

class ConnectionDetailsParameter(TypedDict, total=False):
    dataType: DataType
    name: str

PayloadType = Literal['InlineBase64']

class DecisionRule_constraints(TypedDict, total=False):
    columns: NotRequired[List[ColumnConstraint]]
    rows: NotRequired[List[RowConstraint]]

class PermissionScope(TypedDict, total=False):
    attributeName: Literal['Path', 'Action']
    attributeValueIncludedIn: List[str]

class FabricItemMember(TypedDict, total=False):
    itemAccess: List[Literal['Read', 'Write', 'Reshare', 'Explore', 'Execute', 'ReadAll']]
    sourcePath: str

class MicrosoftEntraMember(TypedDict, total=False):
    tenantId: str
    objectId: str
    objectType: NotRequired[Literal['Group', 'User', 'ServicePrincipal', 'ManagedIdentity']]

DataType = Literal['Text', 'Number', 'Boolean', 'Duration', 'Date', 'DateTime', 'DateTimeZone', 'Time']

class ColumnConstraint(TypedDict, total=False):
    tablePath: str
    columnNames: List[str]
    columnEffect: Literal['Permit']
    columnAction: List[Literal['Read']]

class RowConstraint(TypedDict, total=False):
    tablePath: str
    value: str
