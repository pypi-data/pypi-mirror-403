"""
CodeMie SDK for Python
~~~~~~~~~~~~~~~~~~~~~

A Python SDK for interacting with CodeMie API.

Basic usage:

    >>> from codemie_sdk import CodeMieClient
    >>> client = CodeMieClient(
    ...     auth_server_url="https://auth.example.com",
    ...     auth_client_id="client_id",
    ...     auth_client_secret="secret",
    ...     auth_realm_name="realm",
    ...     codemie_api_domain="api.codemie.com"
    ... )
    >>> assistants = client.assistants.list()
"""

from .client.client import CodeMieClient
from .models.vendor_assistant import (
    VendorType,
    VendorAssistantSetting,
    VendorAssistantSettingsResponse,
    VendorAssistant,
    VendorAssistantVersion,
    VendorAssistantStatus,
    VendorAssistantsResponse,
    VendorAssistantAlias,
    VendorAssistantAliasesResponse,
    VendorAssistantInstallRequest,
    VendorAssistantInstallSummary,
    VendorAssistantInstallResponse,
    VendorAssistantUninstallResponse,
    PaginationInfo,
    TokenPagination,
)
from .models.vendor_workflow import (
    VendorWorkflowSetting,
    VendorWorkflowSettingsResponse,
    VendorWorkflow,
    VendorWorkflowStatus,
    VendorWorkflowsResponse,
    VendorWorkflowAlias,
    VendorWorkflowAliasesResponse,
    VendorWorkflowInstallRequest,
    VendorWorkflowInstallSummary,
    VendorWorkflowInstallResponse,
    VendorWorkflowUninstallResponse,
)
from .models.vendor_knowledgebase import (
    VendorKnowledgeBaseSetting,
    VendorKnowledgeBaseSettingsResponse,
    VendorKnowledgeBase,
    VendorKnowledgeBaseStatus,
    VendorKnowledgeBasesResponse,
    VendorKnowledgeBaseDetail,
    VendorKnowledgeBaseInstallRequest,
    VendorKnowledgeBaseInstallSummary,
    VendorKnowledgeBaseInstallResponse,
    VendorKnowledgeBaseUninstallResponse,
)
from .models.vendor_guardrail import (
    VendorGuardrailSetting,
    VendorGuardrailSettingsResponse,
    VendorGuardrail,
    VendorGuardrailStatus,
    VendorGuardrailsResponse,
    VendorGuardrailVersion,
    VendorGuardrailVersionsResponse,
    VendorGuardrailInstallRequest,
    VendorGuardrailInstallSummary,
    VendorGuardrailInstallResponse,
    VendorGuardrailUninstallResponse,
)
from .models.guardrails import (
    GuardrailAssignmentSetting,
    GuardrailAssignmentEntity,
    GuardrailAssignmentRequest,
    GuardrailAssignmentResponse,
)
from .models.analytics import (
    ResponseMetadata,
    PaginationMetadata,
    ColumnDefinition,
    Metric,
    SummariesData,
    TabularData,
    UserListItem,
    UsersListData,
    SummariesResponse,
    TabularResponse,
    UsersListResponse,
    AnalyticsQueryParams,
    PaginatedAnalyticsQueryParams,
)
from .services.vendor_assistant import VendorAssistantService
from .services.vendor_workflow import VendorWorkflowService
from .services.vendor_knowledgebase import VendorKnowledgeBaseService
from .services.vendor_guardrail import VendorGuardrailService
from .services.codemie_guardrails import CodemieGuardrailService
from .services.analytics import AnalyticsService
from .models.mermaid import (
    MermaidDiagramRequest,
    MermaidDiagramResponse,
    ContentType,
    ResponseType,
)
from .services.mermaid import MermaidService
from .models.categories import (
    Category,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    CategoryResponse,
    CategoryListResponse,
    CategoryListMetadata,
)
from .services.categories import CategoryService

__version__ = "0.2.12"
__all__ = [
    "CodeMieClient",
    "VendorType",
    "VendorAssistantSetting",
    "VendorAssistantSettingsResponse",
    "VendorAssistant",
    "VendorAssistantVersion",
    "VendorAssistantStatus",
    "VendorAssistantsResponse",
    "VendorAssistantAlias",
    "VendorAssistantAliasesResponse",
    "VendorAssistantInstallRequest",
    "VendorAssistantInstallSummary",
    "VendorAssistantInstallResponse",
    "VendorAssistantUninstallResponse",
    "PaginationInfo",
    "TokenPagination",
    "VendorAssistantService",
    "VendorWorkflowSetting",
    "VendorWorkflowSettingsResponse",
    "VendorWorkflow",
    "VendorWorkflowStatus",
    "VendorWorkflowsResponse",
    "VendorWorkflowAlias",
    "VendorWorkflowAliasesResponse",
    "VendorWorkflowInstallRequest",
    "VendorWorkflowInstallSummary",
    "VendorWorkflowInstallResponse",
    "VendorWorkflowUninstallResponse",
    "VendorWorkflowService",
    "VendorKnowledgeBaseSetting",
    "VendorKnowledgeBaseSettingsResponse",
    "VendorKnowledgeBase",
    "VendorKnowledgeBaseStatus",
    "VendorKnowledgeBasesResponse",
    "VendorKnowledgeBaseDetail",
    "VendorKnowledgeBaseInstallRequest",
    "VendorKnowledgeBaseInstallSummary",
    "VendorKnowledgeBaseInstallResponse",
    "VendorKnowledgeBaseUninstallResponse",
    "VendorKnowledgeBaseService",
    "VendorGuardrailSetting",
    "VendorGuardrailSettingsResponse",
    "VendorGuardrail",
    "VendorGuardrailStatus",
    "VendorGuardrailsResponse",
    "VendorGuardrailVersion",
    "VendorGuardrailVersionsResponse",
    "VendorGuardrailInstallRequest",
    "VendorGuardrailInstallSummary",
    "VendorGuardrailInstallResponse",
    "VendorGuardrailUninstallResponse",
    "VendorGuardrailService",
    "GuardrailAssignmentSetting",
    "GuardrailAssignmentEntity",
    "GuardrailAssignmentRequest",
    "GuardrailAssignmentResponse",
    "CodemieGuardrailService",
    "ResponseMetadata",
    "PaginationMetadata",
    "ColumnDefinition",
    "Metric",
    "SummariesData",
    "TabularData",
    "UserListItem",
    "UsersListData",
    "SummariesResponse",
    "TabularResponse",
    "UsersListResponse",
    "AnalyticsQueryParams",
    "PaginatedAnalyticsQueryParams",
    "AnalyticsService",
    "MermaidDiagramRequest",
    "MermaidDiagramResponse",
    "ContentType",
    "ResponseType",
    "MermaidService",
    "Category",
    "CategoryCreateRequest",
    "CategoryUpdateRequest",
    "CategoryResponse",
    "CategoryListResponse",
    "CategoryListMetadata",
    "CategoryService",
]
