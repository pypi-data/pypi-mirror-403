"""Stack specification for Prism.

This module defines the complete stack configuration including database,
GraphQL, generators, testing, and extension settings.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from prism.spec.auth import AuthConfig
from prism.spec.design import DesignSystemConfig
from prism.spec.exposure import (
    FrontendExposure,
    GraphQLExposure,
    MCPExposure,
    RESTExposure,
)
from prism.spec.infrastructure import TraefikConfig
from prism.spec.model import ModelSpec  # noqa: TC001


class FileStrategy(str, Enum):
    """How Prism handles each generated file."""

    ALWAYS_OVERWRITE = "always_overwrite"
    """Always regenerate. Use for pure boilerplate.
    Examples: types/generated.ts, graphql operations
    """

    GENERATE_ONCE = "generate_once"
    """Only create if doesn't exist. Never overwrite.
    Examples: custom hooks, page components
    """

    GENERATE_BASE = "generate_base"
    """Generate into _base or .generated files, user extends.
    Examples: services, forms, tables
    """

    MERGE = "merge"
    """Smart merge with conflict markers.
    Examples: schema.py aggregation files
    """


class ExtensionConfig(BaseModel):
    """Configure how Prism handles extensions.

    Controls file generation strategies and protected regions.

    Example:
        >>> config = ExtensionConfig(
        ...     services_strategy=FileStrategy.GENERATE_BASE,
        ...     components_strategy=FileStrategy.GENERATE_BASE,
        ...     use_protected_regions=True,
        ... )
    """

    # Backend strategies
    services_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_BASE,
        description="Strategy for service files",
    )
    graphql_types_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_BASE,
        description="Strategy for GraphQL type files",
    )
    graphql_queries_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_BASE,
        description="Strategy for GraphQL query files",
    )
    graphql_mutations_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_BASE,
        description="Strategy for GraphQL mutation files",
    )
    rest_endpoints_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_BASE,
        description="Strategy for REST endpoint files",
    )

    # Frontend strategies
    components_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_BASE,
        description="Strategy for component files",
    )
    hooks_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_ONCE,
        description="Strategy for hook files",
    )
    pages_strategy: FileStrategy = Field(
        default=FileStrategy.GENERATE_ONCE,
        description="Strategy for page files",
    )

    # Assembly strategies
    schema_assembly: FileStrategy = Field(
        default=FileStrategy.MERGE,
        description="Strategy for schema assembly files",
    )
    router_assembly: FileStrategy = Field(
        default=FileStrategy.MERGE,
        description="Strategy for router assembly files",
    )

    # Protected regions
    use_protected_regions: bool = Field(
        default=True,
        description="Enable protected region markers",
    )
    protected_region_marker: str = Field(
        default="PRISM:PROTECTED",
        description="Marker for protected regions",
    )

    model_config = {"extra": "forbid"}


class DatabaseConfig(BaseModel):
    """Database configuration.

    Example:
        >>> config = DatabaseConfig(
        ...     dialect="postgresql",
        ...     async_driver=True,
        ... )
    """

    dialect: str = Field(
        default="postgresql",
        description="Database dialect: 'postgresql' or 'sqlite'",
    )
    async_driver: bool = Field(
        default=True,
        description="Use async database driver",
    )
    naming_convention: dict[str, str] = Field(
        default_factory=lambda: {
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        },
        description="SQLAlchemy naming conventions",
    )

    model_config = {"extra": "forbid"}


class GraphQLConfig(BaseModel):
    """GraphQL server configuration.

    Example:
        >>> config = GraphQLConfig(
        ...     enabled=True,
        ...     path="/graphql",
        ...     graphiql=True,
        ...     subscriptions_enabled=True,
        ... )
    """

    enabled: bool = Field(default=True, description="Enable GraphQL endpoint")
    path: str = Field(default="/graphql", description="GraphQL endpoint path")
    graphiql: bool = Field(default=True, description="Enable GraphiQL playground")

    # Subscriptions
    subscriptions_enabled: bool = Field(
        default=True,
        description="Enable GraphQL subscriptions",
    )
    subscription_path: str = Field(
        default="/graphql/ws",
        description="WebSocket path for subscriptions",
    )

    # Query limits
    query_depth_limit: int = Field(
        default=10,
        description="Maximum query depth",
    )
    query_complexity_limit: int = Field(
        default=100,
        description="Maximum query complexity",
    )

    # Advanced
    enable_tracing: bool = Field(
        default=False,
        description="Enable Apollo tracing",
    )
    enable_apollo_federation: bool = Field(
        default=False,
        description="Enable Apollo Federation support",
    )
    dataloader_cache_per_request: bool = Field(
        default=True,
        description="Clear DataLoader cache per request",
    )

    model_config = {"extra": "forbid"}


class WidgetConfig(BaseModel):
    """Frontend widget configuration.

    Example:
        >>> config = WidgetConfig(
        ...     type_widgets={"string": "CustomTextInput"},
        ...     ui_widgets={"currency": "CurrencyInput"},
        ...     field_widgets={"Customer.email": "CustomerEmailWidget"},
        ... )
    """

    type_widgets: dict[str, str] = Field(
        default_factory=dict,
        description="Widget mapping by field type",
    )
    ui_widgets: dict[str, str] = Field(
        default_factory=dict,
        description="Widget mapping by ui_widget hint",
    )
    field_widgets: dict[str, str] = Field(
        default_factory=dict,
        description="Widget mapping by Model.field",
    )

    model_config = {"extra": "forbid"}


class GeneratorConfig(BaseModel):
    """Code generator configuration.

    Example:
        >>> config = GeneratorConfig(
        ...     backend_output="src/backend",
        ...     frontend_output="src/frontend",
        ...     generate_migrations=True,
        ... )
    """

    # Output paths
    backend_output: str = Field(
        default="packages/backend/src",
        description="Backend output directory",
    )
    frontend_output: str = Field(
        default="packages/frontend/src",
        description="Frontend output directory",
    )

    # Backend structure
    models_path: str = Field(default="models", description="Models subdirectory")
    schemas_path: str = Field(default="schemas", description="Schemas subdirectory")
    services_path: str = Field(default="services", description="Services subdirectory")
    services_generated_path: str = Field(
        default="services/_generated",
        description="Generated services subdirectory",
    )
    rest_path: str = Field(default="api/rest", description="REST API subdirectory")
    graphql_path: str = Field(default="api/graphql", description="GraphQL subdirectory")
    graphql_generated_path: str = Field(
        default="api/graphql/_generated",
        description="Generated GraphQL subdirectory",
    )
    mcp_path: str = Field(default="mcp_server", description="MCP tools subdirectory")
    tests_path: str = Field(default="tests", description="Tests subdirectory")

    # Frontend structure
    types_path: str = Field(default="types", description="Types subdirectory")
    graphql_operations_path: str = Field(
        default="graphql",
        description="GraphQL operations subdirectory",
    )
    api_client_path: str = Field(default="api", description="API client subdirectory")
    components_path: str = Field(default="components", description="Components subdirectory")
    components_generated_path: str = Field(
        default="components/_generated",
        description="Generated components subdirectory",
    )
    hooks_path: str = Field(default="hooks", description="Hooks subdirectory")
    pages_path: str = Field(default="pages", description="Pages subdirectory")
    prism_path: str = Field(default="prism", description="Prism system subdirectory")
    frontend_tests_path: str = Field(default="__tests__", description="Frontend tests subdirectory")

    # Options
    generate_migrations: bool = Field(
        default=True,
        description="Generate Alembic migrations",
    )
    overwrite_existing: bool = Field(
        default=False,
        description="Overwrite existing files",
    )
    dry_run: bool = Field(
        default=False,
        description="Preview changes without writing",
    )

    model_config = {"extra": "forbid"}


class TestingConfig(BaseModel):
    """Testing configuration.

    Example:
        >>> config = TestingConfig(
        ...     generate_unit_tests=True,
        ...     generate_integration_tests=True,
        ...     test_database="sqlite",
        ... )
    """

    # Test generation
    generate_unit_tests: bool = Field(
        default=True,
        description="Generate unit tests",
    )
    generate_integration_tests: bool = Field(
        default=True,
        description="Generate integration tests",
    )
    generate_factories: bool = Field(
        default=True,
        description="Generate test factories",
    )
    test_database: str = Field(
        default="sqlite",
        description="Database for tests",
    )

    # Component tests
    generate_graphql_tests: bool = Field(
        default=True,
        description="Generate GraphQL tests",
    )
    generate_component_tests: bool = Field(
        default=True,
        description="Generate frontend component tests",
    )
    generate_hook_tests: bool = Field(
        default=True,
        description="Generate frontend hook tests",
    )
    generate_e2e_tests: bool = Field(
        default=False,
        description="Generate end-to-end tests",
    )

    model_config = {"extra": "forbid"}


class StackSpec(BaseModel):
    """Complete stack specification.

    The root specification that defines all models and configuration
    for a Prism-generated application.

    Example:
        >>> stack = StackSpec(
        ...     name="my-crm",
        ...     version="1.0.0",
        ...     description="Customer Relationship Management System",
        ...     models=[
        ...         ModelSpec(
        ...             name="Customer",
        ...             fields=[...],
        ...         ),
        ...     ],
        ... )
    """

    # Basic info
    name: str = Field(..., description="Project name (kebab-case identifier)")
    title: str | None = Field(
        default=None,
        description="Human-readable project title (defaults to formatted name)",
    )
    version: str = Field(default="1.0.0", description="Project version")
    description: str | None = Field(default=None, description="Project description")

    @property
    def effective_title(self) -> str:
        """Get the effective project title."""
        if self.title:
            return self.title
        # Convert kebab-case name to title case
        return self.name.replace("-", " ").replace("_", " ").title()

    # Configuration
    database: DatabaseConfig = Field(
        default_factory=DatabaseConfig,
        description="Database configuration",
    )
    graphql: GraphQLConfig = Field(
        default_factory=GraphQLConfig,
        description="GraphQL configuration",
    )
    generator: GeneratorConfig = Field(
        default_factory=GeneratorConfig,
        description="Generator configuration",
    )
    testing: TestingConfig = Field(
        default_factory=TestingConfig,
        description="Testing configuration",
    )
    extensions: ExtensionConfig = Field(
        default_factory=ExtensionConfig,
        description="Extension configuration",
    )
    widgets: WidgetConfig = Field(
        default_factory=WidgetConfig,
        description="Widget configuration",
    )
    auth: AuthConfig = Field(
        default_factory=AuthConfig,
        description="Authentication and authorization configuration",
    )
    design: DesignSystemConfig = Field(
        default_factory=DesignSystemConfig,
        description="Design system configuration for frontend styling",
    )
    traefik: TraefikConfig = Field(
        default_factory=TraefikConfig,
        description="Traefik reverse proxy configuration",
    )

    # Models
    models: list[ModelSpec] = Field(..., description="List of model specifications")

    # Global defaults
    default_rest_exposure: RESTExposure = Field(
        default_factory=RESTExposure,
        description="Default REST exposure settings",
    )
    default_graphql_exposure: GraphQLExposure = Field(
        default_factory=GraphQLExposure,
        description="Default GraphQL exposure settings",
    )
    default_mcp_exposure: MCPExposure = Field(
        default_factory=MCPExposure,
        description="Default MCP exposure settings",
    )
    default_frontend_exposure: FrontendExposure = Field(
        default_factory=FrontendExposure,
        description="Default frontend exposure settings",
    )

    model_config = {"extra": "forbid"}
