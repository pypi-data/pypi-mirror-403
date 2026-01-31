"""Prism specification models.

This module contains all the Pydantic models for defining Prism specifications.
"""

from prism.spec.auth import (
    AdminPanelConfig,
    APIKeyConfig,
    AuthConfig,
    EmailConfig,
    OAuthProviderConfig,
    Role,
    SignupAccessConfig,
    SignupWhitelist,
)
from prism.spec.exposure import (
    CRUDOperations,
    FrontendExposure,
    GraphQLExposure,
    MCPExposure,
    PaginationConfig,
    PaginationStyle,
    RESTExposure,
)
from prism.spec.fields import FieldSpec, FieldType, FilterOperator
from prism.spec.model import ModelSpec, RelationshipSpec
from prism.spec.stack import (
    DatabaseConfig,
    ExtensionConfig,
    FileStrategy,
    GeneratorConfig,
    GraphQLConfig,
    StackSpec,
    TestingConfig,
    WidgetConfig,
)

__all__ = [
    "APIKeyConfig",
    "AdminPanelConfig",
    "AuthConfig",
    "CRUDOperations",
    "DatabaseConfig",
    "EmailConfig",
    "ExtensionConfig",
    "FieldSpec",
    "FieldType",
    "FileStrategy",
    "FilterOperator",
    "FrontendExposure",
    "GeneratorConfig",
    "GraphQLConfig",
    "GraphQLExposure",
    "MCPExposure",
    "ModelSpec",
    "OAuthProviderConfig",
    "PaginationConfig",
    "PaginationStyle",
    "RESTExposure",
    "RelationshipSpec",
    "Role",
    "SignupAccessConfig",
    "SignupWhitelist",
    "StackSpec",
    "TestingConfig",
    "WidgetConfig",
]
