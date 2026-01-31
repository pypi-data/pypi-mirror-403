import os
import socket
from pathlib import Path
from urllib.parse import urlparse

from pydantic import BaseModel, Field, field_validator, model_validator


class DatabaseConfig(BaseModel):
    """Database connection configuration using Pydantic validation."""

    host: str = Field(default="localhost", description="Database host")
    port: int = Field(default=5432, ge=1, le=65535, description="Database port")
    database: str = Field(..., description="Database name")
    user: str = Field(..., description="Database user")
    password: str | None = Field(default=None, description="Database password")
    sslmode: str = Field(default="prefer", description="SSL mode")
    connect_timeout: int = Field(
        default=10,
        ge=1,
        description="Connection timeout in seconds",
    )
    command_timeout: int | None = Field(
        default=None,
        ge=1,
        description="Command timeout in seconds",
    )
    application_name: str | None = Field(
        default=None,
        description="Application name for PostgreSQL connection identification",
    )

    # Pool configuration
    min_size: int = Field(default=1, ge=0, description="Minimum pool size")
    max_size: int = Field(default=10, ge=1, description="Maximum pool size")

    # Migrations configuration
    migrations_paths: list[str] = Field(
        default_factory=list,
        description="Paths to directories containing SQL migration files",
    )

    @field_validator("max_size")
    @classmethod
    def validate_max_size(cls, v, info):
        """Ensure max_size is greater than or equal to min_size."""
        if info.data and "min_size" in info.data and v < info.data["min_size"]:
            raise ValueError("max_size must be greater than or equal to min_size")
        return v

    @field_validator("migrations_paths")
    @classmethod
    def validate_migrations_paths(cls, v):
        """Validate that migration paths exist and contain .sql files."""
        if not v:  # Empty list is valid
            return v

        for path_str in v:
            path = Path(path_str)

            # Check if path exists
            if not path.exists():
                raise ValueError(f"Migration path does not exist: {path_str}")

            # Check if path is a directory
            if not path.is_dir():
                raise ValueError(f"Migration path must be a directory: {path_str}")

            # Check if directory contains .sql files
            sql_files = list(path.glob("*.sql"))
            if not sql_files:
                raise ValueError(
                    f"Migration directory contains no .sql files: {path_str}",
                )

        return v

    @model_validator(mode="after")
    def set_application_name(self):
        """Set application name with fallback logic:
        
        1. Use explicit application_name if provided
        2. Use METAPG_APPLICATION_NAME environment variable  
        3. Use PGAPPNAME environment variable (standard PostgreSQL)
        4. Default to 'metapg@<hostname>'
        """
        if self.application_name is None:
            # Check environment variables
            app_name = (
                os.getenv("METAPG_APPLICATION_NAME") or 
                os.getenv("PGAPPNAME")
            )
            
            if app_name is None:
                # Generate default name: metapg@hostname
                hostname = socket.gethostname()
                app_name = f"metapg@{hostname}"
            
            self.application_name = app_name
        
        return self

    @classmethod
    def from_url(
        cls, 
        url: str, 
        migrations_paths: list[str] = [], 
        application_name: str | None = None
    ) -> "DatabaseConfig":
        """Create DatabaseConfig from a database URL.

        Args:
            url: Database URL in format postgresql://user:password@host:port/database
            migrations_paths: List of paths to migration directories
            application_name: Application name for connection identification

        Returns:
            DatabaseConfig instance

        Example:
            config = DatabaseConfig.from_url(
                "postgresql://user:pass@localhost:5432/mydb",
                application_name="my-app"
            )
        """
        parsed = urlparse(url)

        if not parsed.scheme:
            return

        if not parsed.scheme.startswith("postgres"):
            raise ValueError(f"Invalid database URL scheme: {parsed.scheme}")

        return cls(
            host=parsed.hostname or "localhost",
            port=parsed.port or 5432,
            database=parsed.path.lstrip("/") if parsed.path else "",
            user=parsed.username or "",
            password=parsed.password,
            migrations_paths=migrations_paths,
            application_name=application_name,
        )

    def as_dsn(self) -> str:
        """Convert config to PostgreSQL DSN string.

        Returns:
            DSN string for psycopg connection
        """
        dsn_parts = [
            f"host={self.host}",
            f"port={self.port}",
            f"dbname={self.database}",
            f"user={self.user}",
        ]

        if self.password:
            dsn_parts.append(f"password={self.password}")

        if self.sslmode:
            dsn_parts.append(f"sslmode={self.sslmode}")

        if self.connect_timeout:
            dsn_parts.append(f"connect_timeout={self.connect_timeout}")

        if self.command_timeout:
            dsn_parts.append(f"command_timeout={self.command_timeout}")

        if self.application_name:
            dsn_parts.append(f"application_name={self.application_name}")

        return " ".join(dsn_parts)

    def as_url(self) -> str:
        """Convert config to database URL.

        Returns:
            Database URL string
        """
        auth = self.user
        if self.password:
            auth = f"{self.user}:{self.password}"

        return f"postgresql://{auth}@{self.host}:{self.port}/{self.database}"

    def as_connection_kwargs(self) -> dict:
        """Get connection kwargs for psycopg.

        Returns:
            Dictionary of connection arguments
        """
        kwargs = {
            "host": self.host,
            "port": self.port,
            "dbname": self.database,
            "user": self.user,
            "connect_timeout": self.connect_timeout,
        }

        if self.password:
            kwargs["password"] = self.password

        if self.sslmode:
            kwargs["sslmode"] = self.sslmode

        if self.command_timeout:
            kwargs["options"] = f"-c statement_timeout={self.command_timeout}s"

        if self.application_name:
            kwargs["application_name"] = self.application_name

        return kwargs
