"""Prism Demo Specification - Showcasing All Features.

This specification demonstrates all Prism features including:
- All field types (STRING, TEXT, INTEGER, FLOAT, DECIMAL, BOOLEAN, DATETIME, DATE, TIME, UUID, JSON, ENUM, FOREIGN_KEY)
- All filter operators
- Relationships (one_to_many, many_to_one)
- Nested create
- Temporal/time-series queries
- Conditional validation
- Typed JSON arrays
- Custom widgets
- Soft delete and timestamps
- Lifecycle hooks
- All exposure types (REST, GraphQL, MCP, Frontend)
- Full configuration options

Run validation:
    prism validate specs/demo.py

Run one-liner:
    prism create demo-app --spec specs/demo.py && cd demo-app && prism install && prism generate && prism test && prism dev
"""

from prism import (
    CRUDOperations,
    # Stack configs
    DatabaseConfig,
    ExtensionConfig,
    FieldSpec,
    FieldType,
    FileStrategy,
    FilterOperator,
    FrontendExposure,
    GeneratorConfig,
    GraphQLConfig,
    GraphQLExposure,
    MCPExposure,
    ModelSpec,
    PaginationConfig,
    PaginationStyle,
    RelationshipSpec,
    # Exposure configs
    RESTExposure,
    # Core specs
    StackSpec,
    TemporalConfig,
    TestingConfig,
    WidgetConfig,
)

# =============================================================================
# STACK SPECIFICATION
# =============================================================================

stack = StackSpec(
    # Project metadata
    name="prism-demo",
    version="1.0.0",
    title="Prism Demo Application",
    description="A comprehensive demo showcasing all Prism features",
    # Database configuration
    database=DatabaseConfig(
        dialect="postgresql",
        async_driver=True,
    ),
    # GraphQL configuration
    graphql=GraphQLConfig(
        enabled=True,
        path="/graphql",
        graphiql=True,
        subscriptions_enabled=True,
        subscription_path="/graphql/ws",
        query_depth_limit=10,
        query_complexity_limit=100,
    ),
    # Generator configuration
    generator=GeneratorConfig(
        backend_output="packages/backend/src",
        frontend_output="packages/frontend/src",
        generate_migrations=True,
    ),
    # Testing configuration
    testing=TestingConfig(
        generate_unit_tests=True,
        generate_integration_tests=True,
        generate_factories=True,
        test_database="sqlite",
        generate_graphql_tests=True,
        generate_component_tests=True,
        generate_hook_tests=True,
    ),
    # Extension configuration
    extensions=ExtensionConfig(
        services_strategy=FileStrategy.GENERATE_BASE,
        components_strategy=FileStrategy.GENERATE_BASE,
        hooks_strategy=FileStrategy.GENERATE_ONCE,
        pages_strategy=FileStrategy.GENERATE_ONCE,
        use_protected_regions=True,
    ),
    # Widget customization
    widgets=WidgetConfig(
        ui_widgets={
            "currency": "CurrencyInput",
            "percentage": "PercentageInput",
        },
        field_widgets={
            "Employee.email": "EmployeeEmailWidget",
            "Project.budget": "BudgetWidget",
        },
    ),
    # ==========================================================================
    # MODELS
    # ==========================================================================
    models=[
        # ======================================================================
        # COMPANY MODEL
        # Demonstrates: Basic entity, relationships, all field types, timestamps
        # ======================================================================
        ModelSpec(
            name="Company",
            description="Company entity demonstrating basic features",
            table_name="companies",
            soft_delete=True,
            timestamps=True,
            fields=[
                # STRING field with validation
                FieldSpec(
                    name="name",
                    type=FieldType.STRING,
                    max_length=255,
                    min_length=2,
                    required=True,
                    unique=True,
                    indexed=True,
                    searchable=True,
                    label="Company Name",
                    description="Official company name",
                    filter_operators=[
                        FilterOperator.EQ,
                        FilterOperator.NE,
                        FilterOperator.LIKE,
                        FilterOperator.ILIKE,
                        FilterOperator.STARTS_WITH,
                        FilterOperator.ENDS_WITH,
                        FilterOperator.CONTAINS,
                    ],
                ),
                # TEXT field
                FieldSpec(
                    name="description",
                    type=FieldType.TEXT,
                    required=False,
                    searchable=True,
                    ui_widget="richtext",
                    label="Description",
                    tooltip="Detailed company description",
                ),
                # ENUM field
                FieldSpec(
                    name="industry",
                    type=FieldType.ENUM,
                    enum_values=[
                        "technology",
                        "finance",
                        "healthcare",
                        "retail",
                        "manufacturing",
                        "other",
                    ],
                    default="other",
                    required=True,
                    filter_operators=[FilterOperator.EQ, FilterOperator.NE, FilterOperator.IN],
                ),
                # BOOLEAN field
                FieldSpec(
                    name="is_active",
                    type=FieldType.BOOLEAN,
                    default=True,
                    filter_operators=[FilterOperator.EQ],
                ),
                # INTEGER field
                FieldSpec(
                    name="employee_count",
                    type=FieldType.INTEGER,
                    min_value=0,
                    max_value=1000000,
                    default=0,
                    filter_operators=[
                        FilterOperator.EQ,
                        FilterOperator.GT,
                        FilterOperator.GTE,
                        FilterOperator.LT,
                        FilterOperator.LTE,
                        FilterOperator.BETWEEN,
                    ],
                ),
                # DECIMAL field with currency widget
                FieldSpec(
                    name="annual_revenue",
                    type=FieldType.DECIMAL,
                    precision=15,
                    scale=2,
                    min_value=0,
                    required=False,
                    ui_widget="currency",
                    ui_widget_props={"currency": "USD", "locale": "en-US"},
                ),
                # DATE field
                FieldSpec(
                    name="founded_date",
                    type=FieldType.DATE,
                    required=False,
                    filter_operators=[
                        FilterOperator.EQ,
                        FilterOperator.GT,
                        FilterOperator.LT,
                        FilterOperator.BETWEEN,
                    ],
                    ui_widget="datepicker",
                ),
                # URL field (string with URL widget)
                FieldSpec(
                    name="website",
                    type=FieldType.STRING,
                    max_length=500,
                    required=False,
                    pattern=r"^https?://.*",
                    ui_widget="url",
                ),
                # JSON field with typed array (tags)
                FieldSpec(
                    name="tags",
                    type=FieldType.JSON,
                    json_item_type="str",
                    required=False,
                    ui_widget="tags",
                    description="Company tags for categorization",
                ),
                # Generic JSON field (extra_data instead of metadata - SQLAlchemy reserved)
                FieldSpec(
                    name="extra_data",
                    type=FieldType.JSON,
                    required=False,
                    ui_widget="json",
                    description="Additional company data",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="employees",
                    target_model="Employee",
                    type="one_to_many",
                    back_populates="company",
                    use_dataloader=True,
                ),
                RelationshipSpec(
                    name="projects",
                    target_model="Project",
                    type="one_to_many",
                    back_populates="company",
                ),
            ],
            # Full exposure
            rest=RESTExposure(
                enabled=True,
                tags=["companies"],
                pagination=PaginationConfig(
                    style=PaginationStyle.OFFSET,
                    default_page_size=25,
                    max_page_size=100,
                ),
                auth_required=True,
            ),
            graphql=GraphQLExposure(
                enabled=True,
                use_connection=True,
                enable_subscriptions=True,
                use_dataloader=True,
            ),
            mcp=MCPExposure(
                enabled=True,
                tool_prefix="company",
                tool_descriptions={
                    "list": "Search and list companies",
                    "read": "Get company details by ID",
                    "create": "Create a new company",
                    "update": "Update company information",
                    "delete": "Delete a company",
                },
            ),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Companies",
                nav_icon="building-2",
                form_layout="vertical",
            ),
        ),
        # ======================================================================
        # EMPLOYEE MODEL
        # Demonstrates: Foreign keys, conditional validation, all filter ops
        # ======================================================================
        ModelSpec(
            name="Employee",
            description="Employee with conditional fields based on role",
            soft_delete=True,
            timestamps=True,
            fields=[
                # Foreign key to Company
                FieldSpec(
                    name="company_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Company",
                    on_delete="CASCADE",
                    required=True,
                    indexed=True,
                ),
                # Basic string fields
                FieldSpec(
                    name="first_name",
                    type=FieldType.STRING,
                    max_length=100,
                    required=True,
                    searchable=True,
                    label="First Name",
                ),
                FieldSpec(
                    name="last_name",
                    type=FieldType.STRING,
                    max_length=100,
                    required=True,
                    searchable=True,
                    label="Last Name",
                ),
                # Email with custom widget
                FieldSpec(
                    name="email",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    unique=True,
                    indexed=True,
                    pattern=r"^[\w\.-]+@[\w\.-]+\.\w+$",
                    ui_widget="email",
                    label="Email Address",
                ),
                # Phone with custom widget
                FieldSpec(
                    name="phone",
                    type=FieldType.STRING,
                    max_length=20,
                    required=False,
                    ui_widget="phone",
                ),
                # Role enum (used for conditional validation)
                FieldSpec(
                    name="role",
                    type=FieldType.ENUM,
                    enum_values=["engineer", "manager", "executive", "contractor"],
                    required=True,
                    default="engineer",
                ),
                # Salary - decimal with currency widget
                FieldSpec(
                    name="salary",
                    type=FieldType.DECIMAL,
                    precision=12,
                    scale=2,
                    min_value=0,
                    required=False,
                    ui_widget="currency",
                    hidden=False,  # Visible in forms
                ),
                # Hire date
                FieldSpec(
                    name="hire_date",
                    type=FieldType.DATE,
                    required=True,
                ),
                # DATETIME field
                FieldSpec(
                    name="last_login",
                    type=FieldType.DATETIME,
                    required=False,
                    filter_operators=[FilterOperator.GT, FilterOperator.LT, FilterOperator.IS_NULL],
                ),
                # TIME field
                FieldSpec(
                    name="preferred_start_time",
                    type=FieldType.TIME,
                    required=False,
                    label="Preferred Start Time",
                ),
                # UUID field
                FieldSpec(
                    name="external_id",
                    type=FieldType.UUID,
                    required=False,
                    unique=True,
                    default_factory="uuid.uuid4",
                ),
                # Conditional field - required only for managers
                FieldSpec(
                    name="team_size",
                    type=FieldType.INTEGER,
                    required=False,
                    min_value=0,
                    conditional_required="role == manager",
                    description="Required for managers - number of direct reports",
                ),
                # Conditional enum - values depend on role
                FieldSpec(
                    name="department",
                    type=FieldType.ENUM,
                    enum_values=["engineering", "sales", "hr", "finance", "operations"],
                    required=False,
                    conditional_enum={
                        "role:engineer": ["engineering"],
                        "role:manager": ["engineering", "sales", "hr", "finance", "operations"],
                        "role:executive": ["engineering", "sales", "hr", "finance", "operations"],
                    },
                ),
                # Float field
                FieldSpec(
                    name="performance_score",
                    type=FieldType.FLOAT,
                    min_value=0.0,
                    max_value=5.0,
                    required=False,
                    ui_widget="rating",
                ),
                # Boolean with switch widget
                FieldSpec(
                    name="is_remote",
                    type=FieldType.BOOLEAN,
                    default=False,
                    ui_widget="switch",
                    label="Remote Worker",
                ),
                # Skills as typed JSON array
                FieldSpec(
                    name="skills",
                    type=FieldType.JSON,
                    json_item_type="str",
                    required=False,
                    ui_widget="tags",
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="company",
                    target_model="Company",
                    type="many_to_one",
                    back_populates="employees",
                ),
            ],
            # Lifecycle hooks
            before_create="validate_employee",
            after_create="send_welcome_email",
            before_update="check_salary_change",
            after_update="notify_hr",
            # Exposure configuration
            rest=RESTExposure(
                enabled=True,
                tags=["employees"],
                operations=CRUDOperations(
                    create=True,
                    read=True,
                    update=True,
                    delete=True,
                    list=True,
                ),
            ),
            graphql=GraphQLExposure(
                enabled=True,
                use_connection=True,
                nested_queries=True,
            ),
            mcp=MCPExposure(enabled=True, tool_prefix="employee"),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Employees",
                nav_icon="users",
                table_columns=["first_name", "last_name", "email", "role", "department"],
            ),
        ),
        # ======================================================================
        # PROJECT MODEL
        # Demonstrates: Nested create with tasks
        # ======================================================================
        ModelSpec(
            name="Project",
            description="Project with nested task creation",
            timestamps=True,
            fields=[
                FieldSpec(
                    name="company_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Company",
                    required=True,
                ),
                FieldSpec(
                    name="name",
                    type=FieldType.STRING,
                    max_length=200,
                    required=True,
                    searchable=True,
                ),
                FieldSpec(
                    name="description",
                    type=FieldType.TEXT,
                    required=False,
                    ui_widget="markdown",
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["planning", "active", "on_hold", "completed", "cancelled"],
                    default="planning",
                ),
                FieldSpec(
                    name="budget",
                    type=FieldType.DECIMAL,
                    precision=15,
                    scale=2,
                    required=False,
                    ui_widget="currency",
                ),
                FieldSpec(
                    name="start_date",
                    type=FieldType.DATE,
                    required=False,
                ),
                FieldSpec(
                    name="end_date",
                    type=FieldType.DATE,
                    required=False,
                ),
                FieldSpec(
                    name="progress",
                    type=FieldType.INTEGER,
                    min_value=0,
                    max_value=100,
                    default=0,
                    ui_widget="slider",
                    ui_widget_props={"min": 0, "max": 100, "step": 5},
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="company",
                    target_model="Company",
                    type="many_to_one",
                    back_populates="projects",
                ),
                RelationshipSpec(
                    name="tasks",
                    target_model="Task",
                    type="one_to_many",
                    back_populates="project",
                    cascade="all, delete-orphan",
                ),
            ],
            # Enable nested create for tasks
            nested_create=["tasks"],
            rest=RESTExposure(enabled=True, tags=["projects"]),
            graphql=GraphQLExposure(enabled=True, use_connection=True),
            mcp=MCPExposure(enabled=True, tool_prefix="project"),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Projects",
                nav_icon="folder-kanban",
            ),
        ),
        # ======================================================================
        # TASK MODEL
        # Demonstrates: Child entity for nested create
        # ======================================================================
        ModelSpec(
            name="Task",
            description="Task belonging to a project",
            timestamps=True,
            fields=[
                FieldSpec(
                    name="project_id",
                    type=FieldType.FOREIGN_KEY,
                    references="Project",
                    required=True,
                ),
                FieldSpec(
                    name="title",
                    type=FieldType.STRING,
                    max_length=200,
                    required=True,
                ),
                FieldSpec(
                    name="description",
                    type=FieldType.TEXT,
                    required=False,
                ),
                FieldSpec(
                    name="status",
                    type=FieldType.ENUM,
                    enum_values=["todo", "in_progress", "review", "done"],
                    default="todo",
                ),
                FieldSpec(
                    name="priority",
                    type=FieldType.ENUM,
                    enum_values=["low", "medium", "high", "urgent"],
                    default="medium",
                ),
                FieldSpec(
                    name="due_date",
                    type=FieldType.DATE,
                    required=False,
                ),
                FieldSpec(
                    name="estimated_hours",
                    type=FieldType.FLOAT,
                    min_value=0,
                    required=False,
                ),
            ],
            relationships=[
                RelationshipSpec(
                    name="project",
                    target_model="Project",
                    type="many_to_one",
                    back_populates="tasks",
                ),
            ],
            rest=RESTExposure(enabled=True, tags=["tasks"]),
            graphql=GraphQLExposure(enabled=True),
            mcp=MCPExposure(enabled=False),  # Not exposed via MCP
            frontend=FrontendExposure(
                enabled=True,
                include_in_nav=False,  # Accessed via project
            ),
        ),
        # ======================================================================
        # STOCK PRICE MODEL
        # Demonstrates: Temporal/time-series queries
        # ======================================================================
        ModelSpec(
            name="StockPrice",
            description="Stock price history with temporal queries",
            timestamps=False,  # Using custom timestamp field
            fields=[
                FieldSpec(
                    name="symbol",
                    type=FieldType.STRING,
                    max_length=10,
                    required=True,
                    indexed=True,
                    filter_operators=[FilterOperator.EQ, FilterOperator.IN],
                ),
                FieldSpec(
                    name="price",
                    type=FieldType.DECIMAL,
                    precision=12,
                    scale=4,
                    required=True,
                ),
                FieldSpec(
                    name="volume",
                    type=FieldType.INTEGER,
                    required=False,
                ),
                FieldSpec(
                    name="recorded_at",
                    type=FieldType.DATETIME,
                    required=True,
                    indexed=True,
                ),
                FieldSpec(
                    name="source",
                    type=FieldType.STRING,
                    max_length=50,
                    required=False,
                ),
            ],
            # Temporal configuration for time-series queries
            temporal=TemporalConfig(
                timestamp_field="recorded_at",
                group_by_field="symbol",
                generate_latest_query=True,
                generate_history_query=True,
            ),
            rest=RESTExposure(
                enabled=True,
                tags=["stock-prices"],
                operations=CRUDOperations(
                    create=True,
                    read=True,
                    update=False,  # Prices are immutable
                    delete=False,
                    list=True,
                ),
            ),
            graphql=GraphQLExposure(enabled=True, use_connection=True),
            mcp=MCPExposure(
                enabled=True,
                tool_prefix="stock_price",
                tool_descriptions={
                    "list": "Query stock price history",
                    "read": "Get a specific stock price record",
                },
            ),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Stock Prices",
                nav_icon="trending-up",
                operations=CRUDOperations(
                    create=True,
                    read=True,
                    update=False,
                    delete=False,
                    list=True,
                ),
            ),
        ),
        # ======================================================================
        # DOCUMENT MODEL
        # Demonstrates: File handling, JSON metadata
        # ======================================================================
        ModelSpec(
            name="Document",
            description="Document with file handling and metadata",
            soft_delete=True,
            timestamps=True,
            fields=[
                FieldSpec(
                    name="title",
                    type=FieldType.STRING,
                    max_length=255,
                    required=True,
                    searchable=True,
                ),
                FieldSpec(
                    name="file_path",
                    type=FieldType.STRING,
                    max_length=1000,
                    required=True,
                    ui_widget="file",
                ),
                FieldSpec(
                    name="file_type",
                    type=FieldType.ENUM,
                    enum_values=[
                        "pdf",
                        "doc",
                        "docx",
                        "xls",
                        "xlsx",
                        "ppt",
                        "pptx",
                        "txt",
                        "image",
                        "other",
                    ],
                    required=True,
                ),
                FieldSpec(
                    name="file_size",
                    type=FieldType.INTEGER,
                    min_value=0,
                    required=False,
                    description="File size in bytes",
                ),
                FieldSpec(
                    name="category",
                    type=FieldType.ENUM,
                    enum_values=["contract", "invoice", "report", "proposal", "other"],
                    default="other",
                ),
                FieldSpec(
                    name="extra_data",
                    type=FieldType.JSON,
                    required=False,
                    ui_widget="json",
                    description="Additional document data",
                ),
                FieldSpec(
                    name="keywords",
                    type=FieldType.JSON,
                    json_item_type="str",
                    required=False,
                    ui_widget="tags",
                ),
                FieldSpec(
                    name="is_public",
                    type=FieldType.BOOLEAN,
                    default=False,
                ),
            ],
            rest=RESTExposure(enabled=True, tags=["documents"]),
            graphql=GraphQLExposure(enabled=True),
            mcp=MCPExposure(enabled=True, tool_prefix="document"),
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Documents",
                nav_icon="file-text",
            ),
        ),
        # ======================================================================
        # AUDIT LOG MODEL
        # Demonstrates: Read-only model, no mutations
        # ======================================================================
        ModelSpec(
            name="AuditLog",
            description="Audit log - read-only, no mutations",
            timestamps=True,
            fields=[
                FieldSpec(
                    name="entity_type",
                    type=FieldType.STRING,
                    max_length=100,
                    required=True,
                    indexed=True,
                ),
                FieldSpec(
                    name="entity_id",
                    type=FieldType.INTEGER,
                    required=True,
                    indexed=True,
                ),
                FieldSpec(
                    name="action",
                    type=FieldType.ENUM,
                    enum_values=["create", "update", "delete", "restore"],
                    required=True,
                ),
                FieldSpec(
                    name="user_id",
                    type=FieldType.INTEGER,
                    required=False,
                ),
                FieldSpec(
                    name="changes",
                    type=FieldType.JSON,
                    required=False,
                    description="JSON diff of changes",
                ),
                FieldSpec(
                    name="ip_address",
                    type=FieldType.STRING,
                    max_length=45,
                    required=False,
                ),
            ],
            # Read-only - no create/update/delete from API
            rest=RESTExposure(
                enabled=True,
                tags=["audit"],
                operations=CRUDOperations(
                    create=False,
                    read=True,
                    update=False,
                    delete=False,
                    list=True,
                ),
            ),
            graphql=GraphQLExposure(
                enabled=True,
                use_connection=True,
                operations=CRUDOperations(
                    create=False,
                    read=True,
                    update=False,
                    delete=False,
                    list=True,
                ),
            ),
            mcp=MCPExposure(enabled=False),  # No MCP access
            frontend=FrontendExposure(
                enabled=True,
                nav_label="Audit Log",
                nav_icon="history",
                operations=CRUDOperations(
                    create=False,
                    read=True,
                    update=False,
                    delete=False,
                    list=True,
                ),
            ),
        ),
    ],
)


# Export for prism to find
__all__ = ["stack"]
