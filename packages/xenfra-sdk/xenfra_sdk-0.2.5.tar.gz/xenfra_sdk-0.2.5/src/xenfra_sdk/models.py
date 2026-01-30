"""
Pydantic models for the Xenfra SDK, representing API request and response data structures.
These models are used for data validation, serialization, and providing clear schemas
for external tools like OpenAI function calling.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DeploymentStatus(str, Enum):
    """
    Represents the possible statuses of a deployment.
    """

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"


class SourceType(str, Enum):
    """
    Represents the source type of a deployment.
    """

    LOCAL = "local"
    GIT = "git"


class Deployment(BaseModel):
    """
    Represents a single deployment instance.
    """

    id: str = Field(..., description="Unique identifier for the deployment")
    projectId: str = Field(..., description="Identifier of the project being deployed")
    status: DeploymentStatus = Field(..., description="Current status of the deployment")
    source: str = Field(..., description="Source of the deployment (e.g., 'cli', 'api')")
    created_at: datetime = Field(..., description="Timestamp when the deployment was created")
    finished_at: datetime | None = Field(None, description="Timestamp when the deployment finished")


class DeploymentRecord(BaseModel):
    """
    Represents a record of a completed deployment.
    """

    deployment_id: str = Field(..., description="Unique identifier for this deployment instance.")
    timestamp: datetime = Field(..., description="Timestamp of when the deployment succeeded.")
    source_type: SourceType = Field(..., description="The type of the source code (local or git).")
    source_identifier: str = Field(
        ...,
        description="The identifier for the source (commit SHA for git, archive path for local).",
    )


class BalanceRead(BaseModel):
    """
    Represents a snapshot of the user's account balance and usage.
    """

    month_to_date_balance: str = Field(
        ..., description="The account balance in USD at the beginning of the month."
    )
    account_balance: str = Field(..., description="The current total account balance in USD.")
    month_to_date_usage: str = Field(
        ..., description="The total usage in USD for the current month."
    )
    generated_at: str = Field(
        ..., description="The timestamp when this balance report was generated."
    )
    error: str | None = Field(
        None, description="Any error message associated with fetching the balance."
    )


class DropletCostRead(BaseModel):
    """
    Represents the cost information for a single DigitalOcean Droplet.
    """

    id: int = Field(..., description="The unique identifier for the Droplet.")
    name: str = Field(..., description="The user-given name of the Droplet.")
    ip_address: str = Field(..., description="The public IP address of the Droplet.")
    status: str = Field(
        ..., description="The current status of the Droplet (e.g., 'active', 'off')."
    )
    size_slug: str = Field(
        ..., description="The size slug representing the Droplet's resources (e.g., 's-1vcpu-1gb')."
    )
    monthly_price: float = Field(..., description="The monthly cost of this Droplet in USD.")


class ProjectRead(BaseModel):
    """
    Represents a project, including its deployment status and estimated costs.
    """

    id: int = Field(..., description="The unique identifier for the project.")
    name: str = Field(..., description="The user-given name of the project.")
    ip_address: str | None = Field(
        None, description="The public IP address of the server running the project."
    )
    status: str = Field(
        ..., description="The current status of the project (e.g., 'LIVE', 'FAILED')."
    )
    region: str = Field(
        ..., description="The geographical region where the project is deployed (e.g., 'nyc3')."
    )
    size_slug: str = Field(..., description="The size slug of the server running the project.")
    estimated_monthly_cost: float | None = Field(
        None, description="The estimated monthly cost of the project's infrastructure in USD."
    )
    created_at: datetime = Field(..., description="The timestamp when the project was created.")


# Intelligence Service Models


class PatchObject(BaseModel):
    """
    Represents a structured patch for a configuration file.
    """

    file: str | None = Field(
        None, description="The name of the file to be patched (e.g., 'requirements.txt')"
    )
    operation: str | None = Field(None, description="The patch operation (e.g., 'add', 'replace')")
    path: str | None = Field(None, description="A JSON-like path to the field to be changed")
    value: str | None = Field(None, description="The new value to apply")


class DiagnosisResponse(BaseModel):
    """
    Response from the AI diagnosis endpoint.
    """

    diagnosis: str = Field(..., description="Human-readable explanation of the problem")
    suggestion: str = Field(..., description="Recommended course of action")
    patch: PatchObject | None = Field(None, description="Optional machine-applicable patch")


class PackageManagerOption(BaseModel):
    """
    Represents a detected package manager option.
    """

    manager: str = Field(..., description="Package manager name (uv, pip, poetry, npm, etc.)")
    file: str = Field(..., description="Associated dependency file")


class CodebaseAnalysisResponse(BaseModel):
    """
    Response from the codebase analysis endpoint.
    """

    framework: str = Field(..., description="Detected framework (fastapi, flask, django)")
    entrypoint: str | None = Field(None, description="Application entrypoint (e.g., 'todo.main:app')")
    port: int = Field(..., description="Detected application port")
    database: str = Field(..., description="Detected database (postgresql, mysql, sqlite, none)")
    cache: str | None = Field(None, description="Detected cache (redis, memcached, none)")
    workers: list[str] | None = Field(None, description="Detected background workers (celery, rq)")
    env_vars: list[str] | None = Field(None, description="Required environment variables")
    package_manager: str = Field(
        ..., description="Detected package manager (uv, pip, poetry, npm, pnpm, yarn, go, bundler)"
    )
    dependency_file: str = Field(
        ...,
        description="Dependency manifest file (pyproject.toml, requirements.txt, package.json, go.mod, Gemfile)",
    )
    has_conflict: bool = Field(False, description="True if multiple package managers detected")
    detected_package_managers: list[PackageManagerOption] | None = Field(
        None, description="All detected package managers (if conflict)"
    )
    instance_size: str = Field(
        ..., description="Recommended instance size (basic, standard, premium)"
    )
    estimated_cost_monthly: float = Field(..., description="Estimated monthly cost in USD")
    is_dockerized: bool = Field(True, description="Whether to use Docker containerization")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)")
    notes: str | None = Field(None, description="Additional observations")
