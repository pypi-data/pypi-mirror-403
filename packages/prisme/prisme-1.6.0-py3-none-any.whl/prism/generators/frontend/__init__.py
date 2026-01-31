"""Frontend code generators for Prism.

This module contains generators for:
- TypeScript types
- GraphQL operations
- Widget system
- Headless UI hooks
- React components
- React hooks
- Page components
- Router configuration
- Authentication components
"""

from prism.generators.frontend.admin import FrontendAdminGenerator
from prism.generators.frontend.auth import FrontendAuthGenerator
from prism.generators.frontend.components import ComponentsGenerator
from prism.generators.frontend.design import DesignSystemGenerator
from prism.generators.frontend.graphql_ops import GraphQLOpsGenerator
from prism.generators.frontend.headless import HeadlessGenerator
from prism.generators.frontend.hooks import HooksGenerator
from prism.generators.frontend.pages import PagesGenerator
from prism.generators.frontend.router import RouterGenerator
from prism.generators.frontend.types import TypeScriptGenerator
from prism.generators.frontend.widgets import WidgetSystemGenerator

__all__ = [
    "ComponentsGenerator",
    "DesignSystemGenerator",
    "FrontendAdminGenerator",
    "FrontendAuthGenerator",
    "GraphQLOpsGenerator",
    "HeadlessGenerator",
    "HooksGenerator",
    "PagesGenerator",
    "RouterGenerator",
    "TypeScriptGenerator",
    "WidgetSystemGenerator",
]
