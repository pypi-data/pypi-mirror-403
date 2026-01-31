"""
Aribot CLI & SDK - Economic, Regulatory & Security APIs for Modern Applications

Platform Capabilities:
    - Advanced Threat Modeling: Multi-framework (STRIDE, PASTA, NIST, Aristiun)
    - Cloud Security: Real-time CSPM, CNAPP, misconfiguration detection
    - 100+ Compliance Standards: SOC2, ISO27001, PCI-DSS, GDPR, HIPAA...
    - Economic Intelligence: Security ROI, TCO analysis, risk quantification
    - FinOps: Cloud cost optimization & security spend tracking
    - Red Team: Automated attack simulations
    - AI: Secure AI usage management with audit logging

CLI Usage:
    $ aribot login
    $ aribot analyze diagram.png
    $ aribot threats <diagram-id>
    $ aribot export <diagram-id>

SDK Usage:
    from aribot_cli import AribotClient

    client = AribotClient(api_key="ak_...")

    # Threat Modeling (Multi-framework)
    diagram = client.threat_modeling.upload("architecture.png")
    threats = client.threat_modeling.get_threats(diagram["id"])

    # AI Usage & Configuration
    usage = client.ai.get_usage()
    client.ai.configure(model_tier="advanced")

    # Compliance
    assessment = client.compliance.assess(diagram["id"], "SOC2")

Security Features:
    - OS Keyring credential storage (macOS Keychain, Windows, Linux)
    - HMAC-SHA256 request signing
    - Automatic retry with exponential backoff
    - Rate limit handling
    - Audit logging for compliance
"""

from importlib.metadata import version as get_version

# Read version from package metadata
try:
    __version__ = get_version("aribot-cli")
except Exception:
    __version__ = "0.0.0"

# Export SDK classes
from aribot_cli.sdk import (
    # Main client
    AribotClient,
    # Data classes
    Diagram,
    Threat,
    ComplianceAssessment,
    SecurityFinding,
    # Convenience functions
    analyze_diagram,
    run_compliance_check,
    # Security utilities
    SecureCredentialManager,
    RequestSigner,
    AuditLogger,
    # Exceptions
    AribotError,
    AuthenticationError,
    RateLimitError,
    APIError,
    ValidationError,
)

__all__ = [
    # Version
    "__version__",
    # Main client
    "AribotClient",
    # Data classes
    "Diagram",
    "Threat",
    "ComplianceAssessment",
    "SecurityFinding",
    # Convenience functions
    "analyze_diagram",
    "run_compliance_check",
    # Security utilities
    "SecureCredentialManager",
    "RequestSigner",
    "AuditLogger",
    # Exceptions
    "AribotError",
    "AuthenticationError",
    "RateLimitError",
    "APIError",
    "ValidationError",
]
