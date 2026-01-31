"""Page components generator for Prism.

Generates page components for list, detail, and create views
for each model.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from prism.generators.base import GeneratedFile, ModelGenerator
from prism.spec.stack import FileStrategy
from prism.utils.case_conversion import pluralize, to_kebab_case, to_snake_case
from prism.utils.template_engine import TemplateRenderer

if TYPE_CHECKING:
    from prism.spec.model import ModelSpec


class PagesGenerator(ModelGenerator):
    """Generator for page components."""

    REQUIRED_TEMPLATES = [
        "frontend/pages/list_page.tsx.jinja2",
        "frontend/pages/detail_page.tsx.jinja2",
        "frontend/pages/create_page.tsx.jinja2",
        "frontend/pages/edit_page.tsx.jinja2",
    ]

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[no-untyped-def]
        super().__init__(*args, **kwargs)
        frontend_base = Path(self.spec.generator.frontend_output)
        self.pages_path = frontend_base / self.spec.generator.pages_path
        self.renderer = TemplateRenderer()
        self.renderer.validate_templates_exist(self.REQUIRED_TEMPLATES)

    def generate_shared_files(self) -> list[GeneratedFile]:
        """No shared files for pages."""
        return []

    def generate_model_files(self, model: ModelSpec) -> list[GeneratedFile]:
        """Generate pages for a single model."""
        if not model.frontend.enabled:
            return []

        files = []
        ops = model.frontend.operations
        has_form = model.frontend.generate_form
        has_detail = model.frontend.generate_detail_view

        if ops.list:
            files.append(self._generate_list_page(model))

        # Only generate detail page if both operation is enabled AND detail component exists
        if ops.read and has_detail:
            files.append(self._generate_detail_page(model))

        # Only generate create/edit pages if BOTH operation is enabled AND form exists
        if ops.create and has_form:
            files.append(self._generate_create_page(model))

        if ops.update and has_form:
            files.append(self._generate_edit_page(model))

        return files

    def generate_index_files(self) -> list[GeneratedFile]:
        """No index file for pages."""
        return []

    def _get_effective_ops(self, model: ModelSpec):
        """Get effective CRUD operations based on API style."""
        if model.frontend.api_style == "graphql":
            return model.graphql.operations
        return model.frontend.operations

    def _generate_list_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate list page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_name = pluralize(model.name)
        plural_kebab = pluralize(kebab_name)

        # Check if create operation and form exist
        ops = self._get_effective_ops(model)
        has_form = model.frontend.generate_form
        show_create_button = ops.create and has_form

        content = self.renderer.render_file(
            "frontend/pages/list_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "plural_name": plural_name,
                "plural_name_lower": plural_name.lower(),
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
                "show_create_button": show_create_button,
                "ops_update": ops.update,
                "ops_delete": ops.delete,
                "has_mutations": ops.create or ops.update or ops.delete,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "index.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"List page for {plural_name}",
        )

    def _generate_detail_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate detail page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_kebab = pluralize(kebab_name)
        ops = self._get_effective_ops(model)

        content = self.renderer.render_file(
            "frontend/pages/detail_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
                "ops_update": ops.update,
                "ops_delete": ops.delete,
                "has_mutations": ops.create or ops.update or ops.delete,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "[id].tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Detail page for {model.name}",
        )

    def _generate_create_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate create page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_kebab = pluralize(kebab_name)

        content = self.renderer.render_file(
            "frontend/pages/create_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "new.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Create page for {model.name}",
        )

    def _generate_edit_page(self, model: ModelSpec) -> GeneratedFile:
        """Generate edit page component."""
        snake_name = to_snake_case(model.name)
        kebab_name = to_kebab_case(snake_name)
        plural_kebab = pluralize(kebab_name)

        content = self.renderer.render_file(
            "frontend/pages/edit_page.tsx.jinja2",
            context={
                "model_name": model.name,
                "model_name_lower": model.name.lower(),
                "kebab_name": kebab_name,
                "plural_kebab": plural_kebab,
            },
        )

        return GeneratedFile(
            path=self.pages_path / plural_kebab / "[id]/edit.tsx",
            content=content,
            strategy=FileStrategy.GENERATE_ONCE,
            description=f"Edit page for {model.name}",
        )


__all__ = ["PagesGenerator"]
