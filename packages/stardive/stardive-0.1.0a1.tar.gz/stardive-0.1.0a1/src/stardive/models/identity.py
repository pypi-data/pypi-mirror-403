"""
Identity and Provenance Models for Stardive Execution Kernel.

This module defines models that capture the "who, where, and with what" of every
execution, enabling audit-grade provenance tracking.

For audit-grade systems, we must be able to answer:
- **Who** initiated the execution? (Identity)
- **Where** did it run? (EnvironmentFingerprint)
- **With what model**? (ModelIdentity)
- **With what tool**? (ToolIdentity)
- **What secrets were accessed**? (SecretRef)

Key Principles:
1. **Complete Provenance**: Capture all context needed to understand/reproduce execution
2. **Cryptographic Verification**: Support for signed attestations and verified identities
3. **Security by Design**: Secrets are referenced, never stored
4. **Reproducibility**: Environment fingerprints enable exact reproduction
5. **Audit Trail**: Every field supports regulatory compliance

Organization:
- Identity: Who initiated the execution (human, service, or system)
- EnvironmentFingerprint: Where the execution occurred (code, dependencies, infrastructure)
- ModelIdentity: What AI model was used (provider, version, configuration)
- ToolIdentity: What tool/adapter was used (version, dependencies)
- SecretRef: Reference to secrets (never stores actual secret values)

For detailed specifications, see:
- docs/identity-provenance.md - Complete identity and provenance model
- docs/canonical-ir.md - How identity fits into the canonical IR

Security Note:
    All models in this module are frozen (immutable) after creation to ensure
    audit integrity. Secrets are NEVER persisted - only references to where
    they are stored.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, computed_field

from .enums import AuthMethod, SecretSource, UserType


# ============================================================================
# Identity Models
# ============================================================================


class Identity(BaseModel):
    """
    Identity of the entity that initiated an execution or performed an action.

    This captures the 'who' in audit trails, supporting both human users and
    service accounts with cryptographic verification.

    Purpose:
        For audit-grade systems, every action must be attributable to a specific
        identity. This model captures:
        - User identification (email, service account)
        - Authentication method (how identity was verified)
        - Verification status (cryptographically verified or not)
        - Session context (for correlation)

    Audit Implications:
        - HUMAN users may require approval workflows, MFA
        - SERVICE accounts need proper authorization
        - Verified identities provide stronger audit evidence
        - IP addresses aid in security analysis and fraud detection

    Examples:
        Human user via CLI with OAuth:
            Identity(
                user_id="alice@company.com",
                user_type=UserType.HUMAN,
                auth_method=AuthMethod.OAUTH,
                auth_provider="okta",
                verified=True,
                verification_method="jwt_signature"
            )

        Service account with certificate:
            Identity(
                user_type=UserType.SERVICE,
                service_id="ml-inference-service",
                service_role="model-executor",
                auth_method=AuthMethod.CERT,
                verified=True,
                verification_method="x509_cert_chain"
            )

        Development/testing (no auth):
            Identity(
                user_id="dev@localhost",
                user_type=UserType.HUMAN,
                auth_method=AuthMethod.NONE,
                verified=False
            )
    """

    # Human User
    user_id: Optional[str] = Field(
        None,
        description="User identifier (email, username, or unique ID)",
        examples=["alice@company.com", "user_12345"],
    )
    user_type: UserType = Field(
        ..., description="Type of user initiating the action"
    )

    # Service Account
    service_id: Optional[str] = Field(
        None,
        description="Service account identifier for non-human initiators",
        examples=["ml-inference-service", "automation-bot"],
    )
    service_role: Optional[str] = Field(
        None,
        description="Role or permission set of the service account",
        examples=["model-executor", "data-processor"],
    )

    # Authentication
    auth_method: AuthMethod = Field(
        ..., description="Authentication method used to verify identity"
    )
    auth_provider: Optional[str] = Field(
        None,
        description="Identity provider used for authentication",
        examples=["okta", "auth0", "internal-ldap"],
    )

    # Session Context
    session_id: Optional[str] = Field(
        None, description="Session ID for correlating related actions"
    )
    ip_address: Optional[str] = Field(
        None,
        description="Source IP address of the initiator (if available)",
        examples=["192.168.1.100", "2001:db8::1"],
    )

    # Verification
    verified: bool = Field(
        False, description="Whether identity was cryptographically verified"
    )
    verification_method: Optional[str] = Field(
        None,
        description="Method used to verify identity",
        examples=["jwt_signature", "cert_chain", "api_key_hmac"],
    )

    model_config = {"frozen": True}  # Immutable after creation


# ============================================================================
# Environment Provenance
# ============================================================================


class EnvironmentFingerprint(BaseModel):
    """
    Captures the execution environment for reproducibility and audit purposes.

    This captures the 'where' in audit trails, recording code versions,
    dependencies, runtime environment, and infrastructure details needed
    to reproduce or understand execution context.

    Purpose:
        For audit-grade and regulated environments, we must answer:
        "What exact code and environment was used?"

        This enables:
        - **Reproducible builds and executions**
        - **Root cause analysis of failures**
        - **Compliance verification** (was approved code used?)
        - **Dependency tracking for security audits**
        - **Change impact analysis** (what changed between runs?)

    Rationale:
        Different code versions, dependencies, or infrastructure can produce
        different results. For audit and compliance, we must record the exact
        environment to:
        - Reproduce results for verification
        - Identify unapproved changes
        - Track security vulnerabilities in dependencies
        - Correlate failures with environment changes

    Audit Scenario:
        Auditor: "This credit decision was made on June 15th. What code was used?"
        System: "Git commit abc123def (clean, no uncommitted changes)"
                "Dependencies: requirements.txt hash sha256:def456..."
                "Container: stardive:v1.2.3 (digest sha256:abc...)"
                "Running on AWS us-east-1, m5.large instance"

    Examples:
        Local development environment:
            EnvironmentFingerprint(
                git_sha="abc123def456789abcdef123456789abcdef1234",
                git_branch="main",
                git_dirty=False,
                dependencies_hash="sha256:abc123...",
                python_version="3.11.5",
                os="Darwin",
                os_version="macOS 14.0",
                arch="arm64",
                fingerprint_hash="sha256:def456..."
            )

        Production containerized deployment:
            EnvironmentFingerprint(
                git_sha="abc123def456789abcdef123456789abcdef1234",
                git_branch="main",
                git_dirty=False,
                dependencies_hash="sha256:abc123...",
                python_version="3.11.5",
                container_image="stardive:v1.2.3",
                container_digest="sha256:abc...",
                os="Linux",
                os_version="Ubuntu 22.04",
                arch="x86_64",
                cloud_provider="aws",
                region="us-east-1",
                instance_type="m5.large",
                deployment_id="k8s-prod-deployment-abc123",
                namespace="production",
                fingerprint_hash="sha256:ghi789..."
            )
    """

    # Code Version Control
    git_sha: Optional[str] = Field(
        None,
        description="Git commit hash of the code being executed",
        pattern=r"^[a-f0-9]{40}$",
    )
    git_branch: Optional[str] = Field(
        None, description="Git branch name", examples=["main", "develop", "feature/x"]
    )
    git_dirty: bool = Field(
        False, description="Whether working directory has uncommitted changes"
    )

    # Dependency Tracking
    dependencies_hash: str = Field(
        ...,
        description="Hash of dependency manifest (requirements.txt, pyproject.toml)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )
    python_version: str = Field(
        ...,
        description="Python interpreter version",
        examples=["3.11.5", "3.12.0"],
    )

    # Runtime Environment
    os: str = Field(
        ..., description="Operating system", examples=["Linux", "Darwin", "Windows"]
    )
    os_version: str = Field(
        ...,
        description="Operating system version",
        examples=["Ubuntu 22.04", "macOS 14.0"],
    )
    arch: str = Field(
        ..., description="CPU architecture", examples=["x86_64", "arm64", "aarch64"]
    )

    # Container/Deployment (if applicable)
    container_image: Optional[str] = Field(
        None,
        description="Container image name and tag",
        examples=["stardive:v1.2.3", "my-app:latest"],
    )
    container_digest: Optional[str] = Field(
        None,
        description="Immutable container digest (sha256)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    # Cloud/Infrastructure Context
    cloud_provider: Optional[str] = Field(
        None,
        description="Cloud provider hosting the execution",
        examples=["aws", "gcp", "azure", "on-premises"],
    )
    region: Optional[str] = Field(
        None,
        description="Cloud region or data center",
        examples=["us-east-1", "europe-west1"],
    )
    instance_type: Optional[str] = Field(
        None,
        description="VM or instance type",
        examples=["m5.large", "n1-standard-4"],
    )

    # Kubernetes/Orchestration
    deployment_id: Optional[str] = Field(
        None, description="Deployment or pod identifier in orchestration system"
    )
    namespace: Optional[str] = Field(
        None,
        description="Kubernetes namespace or logical grouping",
        examples=["production", "staging"],
    )

    # Overall Fingerprint
    fingerprint_hash: str = Field(
        ...,
        description="SHA256 hash of all environment fields for quick comparison",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    model_config = {"frozen": True, "protected_namespaces": ()}


# ============================================================================
# Model & Tool Identity ("With What")
# ============================================================================


class ModelIdentity(BaseModel):
    """
    Exact AI model configuration used for a step.

    This captures the 'with what model' in audit trails. For AI/LLM steps,
    recording the exact model configuration is critical for:
    - Understanding model behavior and potential biases
    - Reproducing results (if deterministic)
    - Tracking model versions across time
    - Compliance with AI regulations (EU AI Act, etc.)

    Rationale:
        Different model versions, configurations (temperature, seed), and even
        API endpoints can produce vastly different results. For audit-grade
        systems, we must record exactly what model configuration was used.

        Key factors that affect model output:
        - Model version: GPT-4 from April vs. June may behave differently
        - Temperature: 0.0 (deterministic) vs. 0.7 (creative) vs. 1.5 (random)
        - Seed: Enables deterministic sampling for reproducibility
        - Fine-tuning: Custom models behave differently from base models
        - API endpoint: Different regions/versions may have different behavior

    Compliance:
        - EU AI Act: Requires tracking of high-risk AI systems
        - GDPR: AI decisions must be explainable
        - Financial regulations: AI trading decisions must be auditable

    Examples:
        OpenAI GPT-4 with deterministic sampling:
            ModelIdentity(
                provider="openai",
                model_name="gpt-4-turbo-preview",
                model_version="2024-04-09",
                temperature=0.0,
                seed=42,
                api_endpoint="https://api.openai.com/v1",
                api_version="2024-02-01",
                config_hash="sha256:abc123..."
            )

        Anthropic Claude with non-deterministic sampling:
            ModelIdentity(
                provider="anthropic",
                model_name="claude-3-opus-20240229",
                temperature=0.7,
                max_tokens=1000,
                api_endpoint="https://api.anthropic.com",
                api_version="2023-06-01",
                config_hash="sha256:def456..."
            )

        Fine-tuned OpenAI model:
            ModelIdentity(
                provider="openai",
                model_name="gpt-3.5-turbo",
                fine_tune_id="ft:gpt-3.5-turbo:my-org:custom:abc123",
                temperature=0.0,
                seed=0,
                api_endpoint="https://api.openai.com/v1",
                config_hash="sha256:ghi789..."
            )
    """

    # Provider & Model
    provider: str = Field(
        ...,
        description="AI model provider",
        examples=["openai", "anthropic", "huggingface", "azure-openai"],
    )
    model_name: str = Field(
        ...,
        description="Model name or identifier",
        examples=["gpt-4-turbo-preview", "claude-3-opus", "llama-2-70b"],
    )
    model_version: Optional[str] = Field(
        None,
        description="Specific model version (if provider supports versioning)",
        examples=["2024-04-09", "v1.5"],
    )

    # Sampling Configuration (affects output)
    temperature: Optional[float] = Field(
        None,
        description="Sampling temperature (0.0 = deterministic, higher = more random)",
        ge=0.0,
        le=2.0,
    )
    top_p: Optional[float] = Field(
        None, description="Nucleus sampling parameter", ge=0.0, le=1.0
    )
    max_tokens: Optional[int] = Field(
        None, description="Maximum tokens to generate", ge=1
    )
    seed: Optional[int] = Field(
        None,
        description="Random seed for deterministic sampling (if supported)",
    )

    # Fine-tuning
    fine_tune_id: Optional[str] = Field(
        None,
        description="Fine-tuned model identifier (if using custom model)",
    )

    # API Configuration
    api_endpoint: str = Field(
        ...,
        description="API endpoint URL",
        examples=["https://api.openai.com/v1", "https://api.anthropic.com"],
    )
    api_version: Optional[str] = Field(
        None,
        description="API version",
        examples=["2024-02-01", "v1"],
    )

    # Model Weights Hash (rare, but useful for on-prem models)
    model_hash: Optional[str] = Field(
        None,
        description="Hash of model weights (for self-hosted models)",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    # Configuration Hash
    config_hash: str = Field(
        ...,
        description="Hash of all configuration parameters for integrity",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_deterministic(self) -> bool:
        """
        Whether this model configuration is deterministic.

        A model is considered deterministic if and only if:
        1. Temperature is exactly 0.0 (no randomness in sampling)
        2. Seed is set (enables reproducible randomness if temp > 0)

        For audit purposes, deterministic models can be replayed exactly.
        Non-deterministic models require snapshot mode for replay.

        Returns:
            True if model is deterministic (temp=0 and seed set), False otherwise
        """
        return self.temperature == 0.0 and self.seed is not None

    model_config = {"frozen": True, "protected_namespaces": ()}


class ToolIdentity(BaseModel):
    """
    Identifies the exact version and configuration of a tool/adapter used.

    This captures 'with what tool' for non-AI steps (databases, APIs, file I/O).
    Essential for understanding exactly what code executed a step.

    Purpose:
        Just as ModelIdentity tracks AI models, ToolIdentity tracks traditional
        tools and adapters. This is critical for:
        - Reproducibility (exact tool version used)
        - Security audits (known vulnerabilities in dependencies)
        - Debugging (behavior changes between versions)
        - Compliance (approved tool versions)

    Rationale:
        Tool versions and configurations affect behavior:
        - Database connector version may have different query semantics
        - HTTP client version may have different retry logic
        - Different adapter versions may parse data differently

        For audit-grade systems, we must track exactly what tool version
        was used to produce a result.

    Examples:
        PostgreSQL database adapter:
            ToolIdentity(
                tool_name="postgres_connector",
                tool_version="2.1.0",
                tool_config={"host": "db.example.com", "port": 5432},
                tool_config_hash="sha256:abc123...",
                adapter_module="stardive.adapters.sql",
                adapter_class="PostgresAdapter",
                adapter_version="0.1.0",
                dependency_hashes={"psycopg2": "sha256:def456..."}
            )

        S3 file uploader:
            ToolIdentity(
                tool_name="s3_uploader",
                tool_version="1.5.2",
                tool_config={"bucket": "my-bucket", "region": "us-east-1"},
                tool_config_hash="sha256:ghi789...",
                adapter_module="stardive.adapters.storage",
                adapter_class="S3Adapter",
                adapter_version="0.1.0",
                dependency_hashes={"boto3": "sha256:jkl012..."}
            )
    """

    # Tool Information
    tool_name: str = Field(
        ...,
        description="Name of the tool or adapter",
        examples=["postgres_connector", "s3_uploader", "http_client"],
    )
    tool_version: str = Field(
        ..., description="Version of the tool", examples=["1.2.3", "v2.0.0"]
    )

    # Tool Configuration
    tool_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Tool configuration (secrets redacted)",
    )
    tool_config_hash: str = Field(
        ...,
        description="Hash of tool configuration",
        pattern=r"^sha256:[a-f0-9]{64}$",
    )

    # Adapter Implementation
    adapter_module: str = Field(
        ...,
        description="Python module containing the adapter",
        examples=["stardive.adapters.llm", "stardive.adapters.sql"],
    )
    adapter_class: str = Field(
        ...,
        description="Adapter class name",
        examples=["OpenAIAdapter", "PostgresAdapter"],
    )
    adapter_version: str = Field(
        ..., description="Version of the Stardive adapter framework"
    )

    # Dependency Hashes
    dependency_hashes: Dict[str, str] = Field(
        default_factory=dict,
        description="Hashes of key dependencies (e.g., {'openai': 'sha256:...'})",
    )

    model_config = {"frozen": True, "protected_namespaces": ()}


# ============================================================================
# Secret Management
# ============================================================================


class SecretRef(BaseModel):
    """
    Reference to a secret (API key, password, token).

    CRITICAL: Secrets are NEVER persisted in RunRecord or artifacts.
    This model only stores references to where secrets are stored.

    Purpose:
        Audit trails must never contain actual secrets. This would be a
        catastrophic security failure. Instead, we record:
        - WHERE the secret came from (secret manager, env var)
        - WHO accessed it
        - WHEN it was accessed
        - WHETHER access was granted

        This provides complete audit trail without compromising security.

    Rationale:
        Secrets in audit logs create multiple risks:
        - Secrets exposed to anyone with log access
        - Secrets in backups (long-term exposure)
        - Secrets in archived data (cannot be rotated)
        - Compliance violations (PCI-DSS, HIPAA, etc.)

        By storing only references, we:
        - Maintain audit trail (who accessed what, when)
        - Enable secret rotation (logs don't become stale)
        - Limit exposure (only secret manager has actual values)
        - Meet compliance requirements

    Security Model:
        - Secrets retrieved from source at runtime
        - Secrets injected into adapter execution context
        - Secrets never serialized or logged
        - Only references and access records persisted

    Examples:
        Environment variable secret:
            SecretRef(
                secret_id="OPENAI_API_KEY",
                secret_source=SecretSource.ENV,
                injected_at=datetime.now(timezone.utc),
                accessed_by=Identity(user_id="alice@company.com", ...),
                access_granted=True
            )

        AWS Secrets Manager:
            SecretRef(
                secret_id="prod/db/password",
                secret_source=SecretSource.AWS_SECRETS,
                injected_at=datetime.now(timezone.utc),
                accessed_by=Identity(service_id="ml-service", ...),
                access_granted=True
            )

        Access denied (for audit):
            SecretRef(
                secret_id="admin/root_key",
                secret_source=SecretSource.VAULT,
                injected_at=datetime.now(timezone.utc),
                accessed_by=Identity(user_id="bob@company.com", ...),
                access_granted=False  # ❌ Access denied, logged for audit
            )
    """

    secret_id: str = Field(
        ...,
        description="Identifier of the secret (name in secret manager or env var name)",
        examples=["OPENAI_API_KEY", "prod/db/password"],
    )
    secret_source: SecretSource = Field(
        ..., description="Where the secret is stored"
    )

    # Audit Trail
    injected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the secret was accessed",
    )
    accessed_by: Identity = Field(..., description="Who accessed the secret")
    access_granted: bool = Field(..., description="Whether access was permitted")

    model_config = {"frozen": True}


# ============================================================================
# Module Exports
# ============================================================================

__all__ = [
    "Identity",
    "EnvironmentFingerprint",
    "ModelIdentity",
    "ToolIdentity",
    "SecretRef",
]
