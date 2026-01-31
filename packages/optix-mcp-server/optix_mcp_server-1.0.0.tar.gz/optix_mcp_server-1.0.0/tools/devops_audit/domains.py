"""DevOps domain enums and artifact tracking."""

from dataclasses import dataclass, field
from enum import Enum

CATEGORY_ALIASES: dict[str, str] = {
    "docker": "dockerfile",
    "docker-compose": "dockerfile",
    "docker_compose": "dockerfile",
    "dockercompose": "dockerfile",
    "container": "dockerfile",
    "containers": "dockerfile",
    "ci_cd": "cicd",
    "ci-cd": "cicd",
    "ci": "cicd",
    "cd": "cicd",
    "pipeline": "cicd",
    "pipelines": "cicd",
    "workflow": "cicd",
    "workflows": "cicd",
    "github_actions": "cicd",
    "github-actions": "cicd",
    "actions": "cicd",
    "dependencies": "dependency",
    "deps": "dependency",
    "packages": "dependency",
    "package": "dependency",
    "npm": "dependency",
    "pip": "dependency",
    "requirements": "dependency",
    "security": "cicd",
    "secrets": "cicd",
    "credentials": "cicd",
}


class DevOpsCategory(Enum):
    """Categories of DevOps infrastructure issues."""

    DOCKERFILE = "dockerfile"
    CICD = "cicd"
    DEPENDENCY = "dependency"

    @property
    def display_name(self) -> str:
        """Human-readable display name for the category."""
        return {
            DevOpsCategory.DOCKERFILE: "Dockerfile Security",
            DevOpsCategory.CICD: "CI/CD Configuration",
            DevOpsCategory.DEPENDENCY: "Dependency Management",
        }[self]

    @classmethod
    def from_string(cls, value: str) -> "DevOpsCategory":
        """Parse category from string with alias normalization."""
        normalized = value.lower().strip()
        if normalized in CATEGORY_ALIASES:
            normalized = CATEGORY_ALIASES[normalized]
        try:
            return cls(normalized)
        except ValueError:
            valid_options = ", ".join(c.value for c in cls)
            raise ValueError(
                f"Invalid category: '{value}'. Must be one of: {valid_options}"
            )


class DevOpsStepDomain(Enum):
    """Four steps in the DevOps audit workflow."""

    DOCKER_AUDIT = 1
    CICD_AUDIT = 2
    DEPENDENCY_AUDIT = 3
    CROSS_DOMAIN_ANALYSIS = 4

    @property
    def display_name(self) -> str:
        """Human-readable display name for the step."""
        return {
            DevOpsStepDomain.DOCKER_AUDIT: "Docker Infrastructure Audit",
            DevOpsStepDomain.CICD_AUDIT: "CI/CD Pipeline Audit",
            DevOpsStepDomain.DEPENDENCY_AUDIT: "Dependency Security Audit",
            DevOpsStepDomain.CROSS_DOMAIN_ANALYSIS: "Cross-Domain Analysis & Report Generation",
        }[self]

    @staticmethod
    def for_step(step_number: int) -> "DevOpsStepDomain":
        """Map step number (1-4) to domain enum."""
        mapping = {
            1: DevOpsStepDomain.DOCKER_AUDIT,
            2: DevOpsStepDomain.CICD_AUDIT,
            3: DevOpsStepDomain.DEPENDENCY_AUDIT,
            4: DevOpsStepDomain.CROSS_DOMAIN_ANALYSIS,
        }
        if step_number not in mapping:
            raise ValueError(f"step_number must be 1-4, got {step_number}")
        return mapping[step_number]


@dataclass
class DiscoveredArtifacts:
    """Infrastructure artifacts discovered in repository."""

    dockerfiles: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)
    package_files: list[str] = field(default_factory=list)
    lockfiles: list[str] = field(default_factory=list)
    docker_compose_files: list[str] = field(default_factory=list)
    kubernetes_files: list[str] = field(default_factory=list)

    def has_infrastructure_files(self) -> bool:
        """Check if any infrastructure files were found."""
        return bool(self.dockerfiles or self.workflows or self.package_files)

    def to_dict(self) -> dict:
        """Convert to dictionary representation."""
        return {
            "dockerfiles": self.dockerfiles,
            "workflows": self.workflows,
            "package_files": self.package_files,
            "lockfiles": self.lockfiles,
            "docker_compose_files": self.docker_compose_files,
            "kubernetes_files": self.kubernetes_files,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DiscoveredArtifacts":
        """Create DiscoveredArtifacts from dictionary."""
        return cls(
            dockerfiles=data.get("dockerfiles", []),
            workflows=data.get("workflows", []),
            package_files=data.get("package_files", []),
            lockfiles=data.get("lockfiles", []),
            docker_compose_files=data.get("docker_compose_files", []),
            kubernetes_files=data.get("kubernetes_files", []),
        )
