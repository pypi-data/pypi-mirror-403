"""Production Docker configuration generator."""

from dataclasses import dataclass
from pathlib import Path

from jinja2 import Environment, PackageLoader
from rich.console import Console


@dataclass
class ProductionConfig:
    """Configuration for production Docker setup."""

    project_name: str
    use_redis: bool
    domain: str = ""
    ssl_enabled: bool = False
    backend_replicas: int = 2
    enable_monitoring: bool = False


class ProductionComposeGenerator:
    """Generate production Docker Compose configuration."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.env = Environment(loader=PackageLoader("prism", "templates/jinja2"))
        self.console = Console()

    def generate(self, config: ProductionConfig) -> None:
        """Generate production Docker files."""
        # Generate production Dockerfiles
        self._generate_backend_dockerfile(config)
        self._generate_frontend_dockerfile(config)

        # Generate nginx configuration
        self._generate_nginx_config(config)

        # Generate production compose file
        self._generate_compose_file(config)

        # Generate .env.example for production
        self._generate_env_example(config)

        self.console.print("[green]✓ Production Docker configuration generated[/green]")
        self.console.print(f"  Location: {self.project_dir}")
        self.console.print("\n[bold]Next steps:[/bold]")
        self.console.print("  1. Copy .env.prod.example to .env.prod and configure")
        self.console.print(
            "  2. Generate SSL certificates (if using HTTPS): "
            "mkdir -p nginx/ssl && openssl req -x509 -nodes -days 365 -newkey rsa:2048 "
            "-keyout nginx/ssl/key.pem -out nginx/ssl/cert.pem"
        )
        self.console.print("  3. Run: docker compose -f docker-compose.prod.yml up -d")

    def _generate_backend_dockerfile(self, config: ProductionConfig) -> None:
        """Generate production backend Dockerfile."""
        template = self.env.get_template("docker/Dockerfile.backend.prod.jinja2")
        content = template.render(project_name=config.project_name)
        (self.project_dir / "Dockerfile.backend.prod").write_text(content)
        self.console.print("  ✓ Dockerfile.backend.prod")

    def _generate_frontend_dockerfile(self, config: ProductionConfig) -> None:
        """Generate production frontend Dockerfile."""
        template = self.env.get_template("docker/Dockerfile.frontend.prod.jinja2")
        content = template.render(project_name=config.project_name)
        (self.project_dir / "Dockerfile.frontend.prod").write_text(content)
        self.console.print("  ✓ Dockerfile.frontend.prod")

    def _generate_nginx_config(self, config: ProductionConfig) -> None:
        """Generate nginx configuration."""
        template = self.env.get_template("docker/nginx.conf.jinja2")
        content = template.render(
            domain=config.domain,
            ssl_enabled=config.ssl_enabled,
        )
        (self.project_dir / "nginx.conf").write_text(content)
        self.console.print("  ✓ nginx.conf")

        # Create nginx directories
        nginx_dir = self.project_dir / "nginx"
        nginx_dir.mkdir(exist_ok=True)
        (nginx_dir / "static").mkdir(exist_ok=True)
        if config.ssl_enabled:
            (nginx_dir / "ssl").mkdir(exist_ok=True)
            self.console.print("  ✓ nginx/ssl/ (add your SSL certificates here)")

    def _generate_compose_file(self, config: ProductionConfig) -> None:
        """Generate production docker-compose.yml."""
        template = self.env.get_template("docker/docker-compose.prod.yml.jinja2")
        content = template.render(
            PROJECT_NAME=config.project_name,
            use_redis=config.use_redis,
            backend_replicas=config.backend_replicas,
            ssl_enabled=config.ssl_enabled,
        )
        (self.project_dir / "docker-compose.prod.yml").write_text(content)
        self.console.print("  ✓ docker-compose.prod.yml")

    def _generate_env_example(self, config: ProductionConfig) -> None:
        """Generate .env.example for production."""
        env_example = f"""# Production Environment Variables

# Project
PROJECT_NAME={config.project_name}

# Database
DB_USER=postgres
DB_PASSWORD=CHANGE_ME_IN_PRODUCTION
POSTGRES_PASSWORD=CHANGE_ME_IN_PRODUCTION

# Backend
SECRET_KEY=GENERATE_RANDOM_SECRET_KEY_HERE
ALLOWED_HOSTS={config.domain + "," if config.domain else ""}localhost,127.0.0.1
ENVIRONMENT=production

# Redis (if used)
{"REDIS_URL=redis://redis:6379/0" if config.use_redis else "# REDIS_URL=redis://redis:6379/0"}

# Ports
HTTP_PORT=80
{"HTTPS_PORT=443" if config.ssl_enabled else "# HTTPS_PORT=443"}

# SSL (if enabled)
{"# Uncomment and configure if using SSL" if not config.ssl_enabled else ""}
{"# SSL_CERTIFICATE_PATH=/etc/nginx/ssl/cert.pem" if not config.ssl_enabled else "SSL_CERTIFICATE_PATH=/etc/nginx/ssl/cert.pem"}
{"# SSL_CERTIFICATE_KEY_PATH=/etc/nginx/ssl/key.pem" if not config.ssl_enabled else "SSL_CERTIFICATE_KEY_PATH=/etc/nginx/ssl/key.pem"}
"""
        (self.project_dir / ".env.prod.example").write_text(env_example)
        self.console.print("  ✓ .env.prod.example")
