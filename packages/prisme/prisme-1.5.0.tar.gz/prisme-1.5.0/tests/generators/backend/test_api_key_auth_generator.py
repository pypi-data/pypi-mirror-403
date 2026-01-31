"""Tests for API key authentication code generator."""

from pathlib import Path

import pytest

from prism.generators import GeneratorContext
from prism.generators.backend import APIKeyAuthGenerator
from prism.spec import APIKeyConfig, AuthConfig, FieldSpec, FieldType, ModelSpec, StackSpec


@pytest.fixture
def api_key_auth_spec() -> StackSpec:
    """Stack spec with API key authentication enabled."""
    return StackSpec(
        name="test-api-key-app",
        auth=AuthConfig(
            enabled=True,
            preset="api_key",
            api_key=APIKeyConfig(
                header="Authorization",
                scheme="Bearer",
                env_var="API_KEY",
            ),
        ),
        models=[
            ModelSpec(
                name="Subdomain",
                fields=[
                    FieldSpec(name="name", type=FieldType.STRING, required=True, unique=True),
                    FieldSpec(name="ip_address", type=FieldType.STRING, required=False),
                ],
            )
        ],
    )


@pytest.fixture
def api_key_auth_no_scheme_spec() -> StackSpec:
    """Stack spec with API key auth without scheme (raw header)."""
    return StackSpec(
        name="test-api-key-raw",
        auth=AuthConfig(
            enabled=True,
            preset="api_key",
            api_key=APIKeyConfig(
                header="X-API-Key",
                scheme="",  # No scheme, raw key in header
                env_var="SERVICE_API_KEY",
            ),
        ),
        models=[],
    )


@pytest.fixture
def api_key_auth_multiple_keys_spec() -> StackSpec:
    """Stack spec with API key auth allowing multiple keys."""
    return StackSpec(
        name="test-multi-key",
        auth=AuthConfig(
            enabled=True,
            preset="api_key",
            api_key=APIKeyConfig(
                header="Authorization",
                scheme="Bearer",
                env_var="API_KEYS",
                allow_multiple_keys=True,
            ),
        ),
        models=[],
    )


@pytest.fixture
def jwt_auth_spec() -> StackSpec:
    """Stack spec with JWT authentication (not API key)."""
    return StackSpec(
        name="test-jwt-app",
        auth=AuthConfig(
            enabled=True,
            preset="jwt",
            secret_key="${JWT_SECRET}",
            user_model="User",
        ),
        models=[
            ModelSpec(
                name="User",
                fields=[
                    FieldSpec(name="email", type=FieldType.STRING, required=True, unique=True),
                    FieldSpec(
                        name="password_hash", type=FieldType.STRING, required=True, hidden=True
                    ),
                    FieldSpec(name="is_active", type=FieldType.BOOLEAN, default=True),
                    FieldSpec(name="roles", type=FieldType.JSON, default=["user"]),
                ],
            )
        ],
    )


@pytest.fixture
def auth_disabled_spec() -> StackSpec:
    """Stack spec with authentication disabled."""
    return StackSpec(
        name="test-no-auth",
        models=[],
    )


@pytest.fixture
def generator_context_api_key(api_key_auth_spec: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Generator context with API key auth enabled."""
    return GeneratorContext(
        spec=api_key_auth_spec,
        output_dir=tmp_path,
        dry_run=True,
    )


@pytest.fixture
def generator_context_jwt(jwt_auth_spec: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Generator context with JWT auth (should skip API key generator)."""
    return GeneratorContext(
        spec=jwt_auth_spec,
        output_dir=tmp_path,
        dry_run=True,
    )


@pytest.fixture
def generator_context_no_auth(auth_disabled_spec: StackSpec, tmp_path: Path) -> GeneratorContext:
    """Generator context with auth disabled."""
    return GeneratorContext(
        spec=auth_disabled_spec,
        output_dir=tmp_path,
        dry_run=True,
    )


class TestAPIKeyAuthGenerator:
    """Tests for APIKeyAuthGenerator."""

    def test_generator_skips_when_auth_disabled(self, generator_context_no_auth: GeneratorContext):
        """Generator returns empty list when auth is disabled."""
        generator = APIKeyAuthGenerator(generator_context_no_auth)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_generator_skips_when_jwt_preset(self, generator_context_jwt: GeneratorContext):
        """Generator returns empty list when preset is JWT."""
        generator = APIKeyAuthGenerator(generator_context_jwt)
        files = generator.generate_files()
        assert files == []
        assert generator.skip_generation is True

    def test_generator_creates_files_when_api_key_preset(
        self, generator_context_api_key: GeneratorContext
    ):
        """Generator creates files when preset is api_key."""
        generator = APIKeyAuthGenerator(generator_context_api_key)
        files = generator.generate_files()

        # Should generate 4 files: api_key_service, middleware, 2x __init__
        assert len(files) == 4
        assert not hasattr(generator, "skip_generation") or not generator.skip_generation

    def test_generator_creates_api_key_service(self, generator_context_api_key: GeneratorContext):
        """Generator creates API key service file."""
        generator = APIKeyAuthGenerator(generator_context_api_key)
        files = generator.generate_files()

        file_paths = [str(f.path) for f in files]
        assert any("api_key_service.py" in p for p in file_paths)

        # Check content
        service_file = next(f for f in files if "api_key_service.py" in str(f.path))
        assert "class APIKeyService" in service_file.content
        assert "verify_key" in service_file.content
        assert "require_key" in service_file.content
        assert "API_KEY" in service_file.content  # env_var

    def test_generator_creates_middleware(self, generator_context_api_key: GeneratorContext):
        """Generator creates API key middleware file."""
        generator = APIKeyAuthGenerator(generator_context_api_key)
        files = generator.generate_files()

        # Find middleware file
        middleware_files = [
            f for f in files if "middleware" in str(f.path) and "api_key.py" in str(f.path)
        ]
        assert len(middleware_files) == 1

        middleware_file = middleware_files[0]
        assert "get_api_key" in middleware_file.content
        assert "require_api_key" in middleware_file.content
        assert "Authorization" in middleware_file.content  # header
        assert "Bearer" in middleware_file.content  # scheme

    def test_generator_uses_project_name_in_imports(
        self, generator_context_api_key: GeneratorContext
    ):
        """Generator uses correct project name in imports."""
        generator = APIKeyAuthGenerator(generator_context_api_key)
        files = generator.generate_files()

        project_name = "test_api_key_app"  # snake_case

        for file in files:
            if "api_key_service.py" in str(file.path):
                # Service doesn't need project imports
                pass
            elif "middleware" in str(file.path) and "api_key.py" in str(file.path):
                assert f"from {project_name}.auth.api_key_service" in file.content

    def test_generator_with_custom_header(
        self, api_key_auth_no_scheme_spec: StackSpec, tmp_path: Path
    ):
        """Generator uses custom header from config."""
        context = GeneratorContext(
            spec=api_key_auth_no_scheme_spec,
            output_dir=tmp_path,
            dry_run=True,
        )
        generator = APIKeyAuthGenerator(context)
        files = generator.generate_files()

        service_file = next(f for f in files if "api_key_service.py" in str(f.path))
        assert "SERVICE_API_KEY" in service_file.content

        middleware_file = next(
            f for f in files if "api_key.py" in str(f.path) and "middleware" in str(f.path)
        )
        assert "X-API-Key" in middleware_file.content

    def test_generator_with_multiple_keys(
        self, api_key_auth_multiple_keys_spec: StackSpec, tmp_path: Path
    ):
        """Generator supports multiple API keys mode."""
        context = GeneratorContext(
            spec=api_key_auth_multiple_keys_spec,
            output_dir=tmp_path,
            dry_run=True,
        )
        generator = APIKeyAuthGenerator(context)
        files = generator.generate_files()

        service_file = next(f for f in files if "api_key_service.py" in str(f.path))
        assert "self._allow_multiple = True" in service_file.content

    def test_generator_file_strategies(self, generator_context_api_key: GeneratorContext):
        """Generator uses appropriate file strategies."""
        from prism.spec.stack import FileStrategy

        generator = APIKeyAuthGenerator(generator_context_api_key)
        files = generator.generate_files()

        # All files should be ALWAYS_OVERWRITE for API key auth
        service = next(f for f in files if "api_key_service.py" in str(f.path))
        assert service.strategy == FileStrategy.ALWAYS_OVERWRITE

        middleware = next(
            f for f in files if "middleware" in str(f.path) and "api_key.py" in str(f.path)
        )
        assert middleware.strategy == FileStrategy.ALWAYS_OVERWRITE


class TestAPIKeyConfig:
    """Tests for APIKeyConfig model."""

    def test_default_config(self):
        """APIKeyConfig has sensible defaults."""
        config = APIKeyConfig()
        assert config.header == "Authorization"
        assert config.scheme == "Bearer"
        assert config.env_var == "API_KEY"
        assert config.allow_multiple_keys is False

    def test_custom_config(self):
        """Can create APIKeyConfig with custom values."""
        config = APIKeyConfig(
            header="X-API-Key",
            scheme="",
            env_var="SERVICE_KEY",
            allow_multiple_keys=True,
        )
        assert config.header == "X-API-Key"
        assert config.scheme == ""
        assert config.env_var == "SERVICE_KEY"
        assert config.allow_multiple_keys is True


class TestAuthConfigPreset:
    """Tests for AuthConfig preset field."""

    def test_default_preset_is_jwt(self):
        """Default preset is JWT for backward compatibility."""
        auth = AuthConfig()
        assert auth.preset == "jwt"

    def test_api_key_preset(self):
        """Can set preset to api_key."""
        auth = AuthConfig(
            enabled=True,
            preset="api_key",
        )
        assert auth.preset == "api_key"

    def test_jwt_preset_explicit(self):
        """Can explicitly set preset to jwt."""
        auth = AuthConfig(
            enabled=True,
            preset="jwt",
            secret_key="${JWT_SECRET}",
        )
        assert auth.preset == "jwt"

    def test_api_key_preset_has_default_config(self):
        """API key preset has default APIKeyConfig."""
        auth = AuthConfig(
            enabled=True,
            preset="api_key",
        )
        assert auth.api_key is not None
        assert auth.api_key.header == "Authorization"
        assert auth.api_key.scheme == "Bearer"
        assert auth.api_key.env_var == "API_KEY"
