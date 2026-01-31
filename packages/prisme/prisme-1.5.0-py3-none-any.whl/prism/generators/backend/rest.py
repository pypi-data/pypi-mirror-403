"""FastAPI REST endpoints generator for Prism.

Generates FastAPI routers with CRUD endpoints following the
base+extension pattern.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prism.generators.base import GeneratedFile, ModelGenerator, create_init_file
from prism.spec.stack import FileStrategy
from prism.utils.case_conversion import pluralize, to_kebab_case, to_snake_case
from prism.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prism.spec.model import ModelSpec


class RESTGenerator(ModelGenerator):
    """Generator for FastAPI REST endpoints."""

    REQUIRED_TEMPLATES = [
        "backend/rest/deps.py.jinja2",
        "backend/rest/router_base.py.jinja2",
        "backend/rest/router_extension.py.jinja2",
        "backend/rest/main_router.py.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        backend_base = Path(self.spec.generator.backend_output)
        # Generate inside the package namespace for proper relative imports
        package_name = self.get_package_name()
        package_base = backend_base / package_name
        self.rest_path = package_base / self.spec.generator.rest_path
        self.generated_path = self.rest_path / "_generated"
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """Generate shared dependencies and utilities."""
        return [
            self._generate_deps(),
            self._generate_generated_init(),
        ]

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate REST endpoints for a single model."""
        if not model.rest.enabled:
            return []

        return [
            self._generate_base_router(model),
            self._generate_extension_router(model),
        ]

    def generate_index_files(self) -> list[GeneratedFile]:
        """Generate main router that combines all model routers."""
        return [
            self._generate_main_router(),
            self._generate_rest_init(),
        ]

    def _generate_deps(self) -> GeneratedFile:
        """Generate common dependencies."""
        project_name = self.get_package_name()
        content = self.renderer.render_file(
            "backend/rest/deps.py.jinja2",
            context={"project_name": project_name},
        )
        return GeneratedFile(
            path=self.generated_path / "deps.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="REST API dependencies",
        )

    def _generate_generated_init(self) -> GeneratedFile:
        """Generate __init__.py for _generated folder."""
        imports = [
            "from .deps import DbSession, Pagination, PaginationParams, Sorting, SortParams, get_db",
        ]
        exports = [
            "DbSession",
            "Pagination",
            "PaginationParams",
            "Sorting",
            "SortParams",
            "get_db",
        ]

        for model in self.spec.models:
            if model.rest.enabled:
                snake_name = to_snake_case(model.name)
                imports.append(
                    f"from .{snake_name}_routes import router as {snake_name}_base_router"
                )
                exports.append(f"{snake_name}_base_router")

        return create_init_file(
            self.generated_path,
            imports,
            exports,
            "Generated REST API components.",
        )

    def _generate_base_router(self, model: ModelSpec) -> GeneratedFile:
        """Generate the base router for a model."""
        snake_name = to_snake_case(model.name)
        plural_name = pluralize(snake_name)
        kebab_name = to_kebab_case(plural_name)
        package_name = self.get_package_name()
        ops = model.rest.operations
        tags = model.rest.tags or [plural_name]
        soft_delete = "True" if model.soft_delete else "False"

        # Build M2M relationships for relationship management
        m2m_relationships = [
            {
                "name": rel.name,
                "target_model": rel.target_model,
                "target_snake": to_snake_case(rel.target_model),
            }
            for rel in model.relationships
            if rel.type == "many_to_many"
        ]

        content = self.renderer.render_file(
            "backend/rest/router_base.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "plural_name": plural_name,
                "kebab_name": kebab_name,
                "package_name": package_name,
                "tags": tags,
                "ops_list": ops.list,
                "ops_read": ops.read,
                "ops_create": ops.create,
                "ops_update": ops.update,
                "ops_delete": ops.delete,
                "soft_delete": soft_delete,
                "m2m_relationships": m2m_relationships,
            },
        )

        return GeneratedFile(
            path=self.generated_path / f"{snake_name}_routes.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description=f"REST routes for {model.name}",
        )

    def _generate_extension_router(self, model: ModelSpec) -> GeneratedFile:
        """Generate the user-extensible router."""
        snake_name = to_snake_case(model.name)
        plural_name = pluralize(snake_name)

        content = self.renderer.render_file(
            "backend/rest/router_extension.py.jinja2",
            context={
                "model_name": model.name,
                "snake_name": snake_name,
                "plural_name": plural_name,
            },
        )

        return GeneratedFile(
            path=self.rest_path / f"{snake_name}.py",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Extension routes for {model.name}",
        )

    def _generate_main_router(self) -> GeneratedFile:
        """Generate main router that combines all model routers."""
        enabled_models = [m for m in self.spec.models if m.rest.enabled]
        model_names = [to_snake_case(m.name) for m in enabled_models]

        auth_enabled = self.spec.auth.enabled and self.spec.auth.preset in ("jwt", "custom")

        admin_panel_enabled = self.spec.auth.enabled and self.spec.auth.admin_panel.enabled

        content = self.renderer.render_file(
            "backend/rest/main_router.py.jinja2",
            context={
                "model_names": model_names,
                "auth_enabled": auth_enabled,
                "admin_panel_enabled": admin_panel_enabled,
            },
        )

        return GeneratedFile(
            path=self.rest_path / "router.py",
            content=content,
            strategy=FileStrategy.ALWAYS_OVERWRITE,
            description="Main REST router",
        )

    def _generate_rest_init(self) -> GeneratedFile:
        """Generate __init__.py for rest folder."""
        imports = ["from .router import router"]
        exports = ["router"]

        for model in self.spec.models:
            if model.rest.enabled:
                snake_name = to_snake_case(model.name)
                imports.append(f"from .{snake_name} import router as {snake_name}_router")
                exports.append(f"{snake_name}_router")

        return create_init_file(
            self.rest_path,
            imports,
            exports,
            "REST API routers.",
        )


__all__ = ["RESTGenerator"]
