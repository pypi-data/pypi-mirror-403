"""Backend code generators for Prism.

This module contains generators for:
- SQLAlchemy models
- Pydantic schemas
- Service classes
- JWT authentication
- API key authentication
- FastAPI REST endpoints
- Strawberry GraphQL types, queries, mutations
- FastMCP tools
- Alembic database migrations
"""

from prism.generators.backend.admin import AdminGenerator
from prism.generators.backend.alembic import AlembicGenerator
from prism.generators.backend.api_key_auth import APIKeyAuthGenerator
from prism.generators.backend.auth import AuthGenerator
from prism.generators.backend.graphql import GraphQLGenerator
from prism.generators.backend.mcp import MCPGenerator
from prism.generators.backend.models import ModelsGenerator
from prism.generators.backend.rest import RESTGenerator
from prism.generators.backend.schemas import SchemasGenerator
from prism.generators.backend.services import ServicesGenerator

__all__ = [
    "APIKeyAuthGenerator",
    "AdminGenerator",
    "AlembicGenerator",
    "AuthGenerator",
    "GraphQLGenerator",
    "MCPGenerator",
    "ModelsGenerator",
    "RESTGenerator",
    "SchemasGenerator",
    "ServicesGenerator",
]
