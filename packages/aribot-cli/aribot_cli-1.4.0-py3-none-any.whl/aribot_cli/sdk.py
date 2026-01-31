"""
Aribot Python SDK - Economic, Regulatory & Security APIs for Modern Applications

Analyze your tech stack. Optimize architecture. Model costs. Identify threats dynamically.
APIs that help you build better systems with practical, actionable recommendations.

Platform Capabilities:
    - Advanced Threat Modeling: Multi-framework analysis (STRIDE, PASTA, NIST, Aristiun Framework)
    - Cloud Security: Real-time CSPM, CNAPP, misconfiguration detection
    - Living Architecture: Dynamic architecture diagrams with real-time updates
    - Economic Intelligence: Security ROI, TCO analysis, risk quantification in real dollars
    - FinOps: Cloud cost optimization, security spend tracking
    - Compliance: 100+ regulatory standards (SOC2, ISO27001, NIST, PCI-DSS, GDPR, HIPAA, etc.)
    - Red Team: Automated attack simulations, penetration testing orchestration

Usage:
    from aribot_cli import AribotClient

    client = AribotClient(api_key="ak_...")

    # Threat Modeling
    diagram = client.threat_modeling.upload("architecture.png")
    threats = client.threat_modeling.get_threats(diagram.id)

    # Cloud Security
    posture = client.cloud_security.scan_posture()
    findings = client.cloud_security.get_findings()

    # Compliance
    assessment = client.compliance.assess(diagram_id, standard="SOC2")
    report = client.compliance.generate_report(assessment.id)

    # Economic Intelligence
    roi = client.economics.calculate_roi(security_investment=100000)
    tco = client.economics.calculate_tco(cloud_provider="aws")

    # Red Team
    simulation = client.redteam.run_simulation(target_id, attack_type="lateral_movement")
"""

import os
import time
import secrets
import hashlib
import hmac
import base64
import json
import logging
from datetime import datetime, timezone
from importlib.metadata import version as get_version
from pathlib import Path
from typing import Optional, Dict, Any, List, Union, Callable
from dataclasses import dataclass, field
from functools import wraps

import httpx

# Optional secure storage imports
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False

# Read version from package metadata
try:
    __version__ = get_version("aribot-cli")
except Exception:
    __version__ = "0.0.0"

logger = logging.getLogger("aribot")


# =============================================================================
# SECURITY UTILITIES
# =============================================================================

class SecureCredentialManager:
    """
    Secure credential management with OS keyring integration.

    Supports:
        - macOS Keychain
        - Windows Credential Manager
        - Linux Secret Service (GNOME Keyring, KWallet)
        - Fallback to environment variables

    Security Features:
        - Credentials never stored in plaintext files
        - Automatic keyring detection
        - Memory-safe credential handling
    """

    SERVICE_NAME = "aribot-api"

    @classmethod
    def store_api_key(cls, api_key: str, identifier: str = "default") -> bool:
        """Securely store API key in OS keyring."""
        if not KEYRING_AVAILABLE:
            logger.warning("Keyring not available. Install with: pip install keyring")
            return False

        try:
            keyring.set_password(cls.SERVICE_NAME, identifier, api_key)
            logger.info(f"API key stored securely for '{identifier}'")
            return True
        except Exception as e:
            logger.error(f"Failed to store API key: {e}")
            return False

    @classmethod
    def get_api_key(cls, identifier: str = "default") -> Optional[str]:
        """Retrieve API key from OS keyring or environment."""
        # Try keyring first
        if KEYRING_AVAILABLE:
            try:
                key = keyring.get_password(cls.SERVICE_NAME, identifier)
                if key:
                    return key
            except Exception as e:
                logger.debug(f"Keyring lookup failed: {e}")

        # Fallback to environment variable
        return os.environ.get("ARIBOT_API_KEY")

    @classmethod
    def delete_api_key(cls, identifier: str = "default") -> bool:
        """Remove API key from keyring."""
        if not KEYRING_AVAILABLE:
            return False

        try:
            keyring.delete_password(cls.SERVICE_NAME, identifier)
            return True
        except Exception:
            return False

    @classmethod
    def rotate_api_key(cls, old_key: str, new_key: str, identifier: str = "default") -> bool:
        """Safely rotate API key."""
        if cls.get_api_key(identifier) == old_key:
            return cls.store_api_key(new_key, identifier)
        return False


class RequestSigner:
    """
    HMAC-SHA256 request signing for API request integrity.

    Provides:
        - Request tampering detection
        - Replay attack prevention via timestamps
        - Non-repudiation of API calls
    """

    @staticmethod
    def sign_request(
        api_key: str,
        method: str,
        path: str,
        timestamp: str,
        body: Optional[str] = None,
    ) -> str:
        """
        Generate HMAC-SHA256 signature for request.

        Args:
            api_key: The API key (used as signing key)
            method: HTTP method (GET, POST, etc.)
            path: Request path
            timestamp: ISO timestamp
            body: Request body (for POST/PUT)

        Returns:
            Base64-encoded signature
        """
        # Create canonical request string
        parts = [method.upper(), path, timestamp]
        if body:
            body_hash = hashlib.sha256(body.encode()).hexdigest()
            parts.append(body_hash)

        canonical = "\n".join(parts)

        # Sign with HMAC-SHA256
        signature = hmac.new(
            api_key.encode(),
            canonical.encode(),
            hashlib.sha256
        ).digest()

        return base64.b64encode(signature).decode()

    @staticmethod
    def verify_signature(
        api_key: str,
        signature: str,
        method: str,
        path: str,
        timestamp: str,
        body: Optional[str] = None,
        max_age_seconds: int = 300,
    ) -> bool:
        """Verify request signature and timestamp freshness."""
        # Check timestamp freshness
        try:
            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - ts).total_seconds()
            if abs(age) > max_age_seconds:
                return False
        except Exception:
            return False

        # Verify signature
        expected = RequestSigner.sign_request(api_key, method, path, timestamp, body)
        return hmac.compare_digest(signature, expected)


class AuditLogger:
    """
    Security audit logging for compliance and forensics.

    Logs:
        - All API requests (sanitized)
        - Authentication events
        - Error conditions
        - Rate limit events
    """

    def __init__(self, log_file: Optional[Path] = None):
        self.log_file = log_file
        self._setup_logger()

    def _setup_logger(self):
        """Configure audit logger."""
        self.logger = logging.getLogger("aribot.audit")
        self.logger.setLevel(logging.INFO)

        if self.log_file:
            handler = logging.FileHandler(self.log_file)
            handler.setFormatter(logging.Formatter(
                '%(asctime)s | %(levelname)s | %(message)s'
            ))
            self.logger.addHandler(handler)

    def log_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        request_id: str,
        duration_ms: float,
        user_id: Optional[str] = None,
    ):
        """Log API request (sanitized - no sensitive data)."""
        self.logger.info(
            f"REQUEST | {method} {endpoint} | status={status_code} | "
            f"request_id={request_id} | duration={duration_ms:.2f}ms | user={user_id or 'unknown'}"
        )

    def log_auth_event(self, event_type: str, success: bool, details: str = ""):
        """Log authentication event."""
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, f"AUTH | {event_type} | success={success} | {details}")

    def log_security_event(self, event_type: str, severity: str, details: str):
        """Log security-related event."""
        self.logger.warning(f"SECURITY | {event_type} | severity={severity} | {details}")


# =============================================================================
# EXCEPTIONS
# =============================================================================

class AribotError(Exception):
    """Base exception for Aribot SDK errors."""
    pass


class AuthenticationError(AribotError):
    """API key is invalid or expired."""
    pass


class RateLimitError(AribotError):
    """Rate limit exceeded."""
    def __init__(self, message: str, retry_after: int = None):
        super().__init__(message)
        self.retry_after = retry_after


class APIError(AribotError):
    """API returned an error response."""
    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class ValidationError(AribotError):
    """Invalid input data."""
    pass


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class Diagram:
    """Represents a threat model diagram."""
    id: str
    name: str
    filename: Optional[str]
    stage: str
    threats_count: int
    created_at: str
    updated_at: Optional[str]

    @classmethod
    def from_dict(cls, data: dict) -> "Diagram":
        return cls(
            id=data.get("id", ""),
            name=data.get("name") or data.get("filename", "Unnamed"),
            filename=data.get("filename"),
            stage=data.get("stage", "pending"),
            threats_count=data.get("threats_count", 0),
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at"),
        )


@dataclass
class Threat:
    """Represents a security threat."""
    id: str
    title: str
    description: Optional[str]
    severity: str
    category: str
    stride_category: Optional[str]
    mitigation: Optional[str]
    cvss_score: Optional[float] = None
    attack_vector: Optional[str] = None

    @classmethod
    def from_dict(cls, data: dict) -> "Threat":
        return cls(
            id=str(data.get("id", "")),
            title=data.get("title") or data.get("name", "Untitled"),
            description=data.get("description"),
            severity=data.get("severity", "medium"),
            category=data.get("category") or data.get("stride_category", ""),
            stride_category=data.get("stride_category"),
            mitigation=data.get("mitigation"),
            cvss_score=data.get("cvss_score"),
            attack_vector=data.get("attack_vector"),
        )


@dataclass
class ComplianceAssessment:
    """Represents a compliance assessment result."""
    id: str
    standard: str
    score: float
    passed_controls: int
    failed_controls: int
    status: str
    created_at: str

    @classmethod
    def from_dict(cls, data: dict) -> "ComplianceAssessment":
        return cls(
            id=data.get("id", ""),
            standard=data.get("standard", ""),
            score=data.get("score", 0.0),
            passed_controls=data.get("passed_controls", 0),
            failed_controls=data.get("failed_controls", 0),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
        )


@dataclass
class SecurityFinding:
    """Represents a cloud security finding."""
    id: str
    title: str
    severity: str
    resource_type: str
    resource_id: str
    policy: str
    remediation: Optional[str]
    status: str

    @classmethod
    def from_dict(cls, data: dict) -> "SecurityFinding":
        return cls(
            id=data.get("id", ""),
            title=data.get("title", ""),
            severity=data.get("severity", "medium"),
            resource_type=data.get("resource_type", ""),
            resource_id=data.get("resource_id", ""),
            policy=data.get("policy", ""),
            remediation=data.get("remediation"),
            status=data.get("status", "open"),
        )


# =============================================================================
# API CLIENT
# =============================================================================

class AribotClient:
    """
    Secure API client for Aribot Enterprise Security Platform.

    Args:
        api_key: Your Aribot API key. If not provided, reads from ARIBOT_API_KEY env var.
        base_url: API base URL. Defaults to production API.
        timeout: Request timeout in seconds. Default 60.
        max_retries: Max retry attempts for failed requests. Default 3.
        verify_ssl: Whether to verify SSL certificates. Default True.

    Example:
        >>> client = AribotClient(api_key="ak_...")
        >>> client.threat_modeling.list()
        >>> client.compliance.assess("diagram-id", standard="SOC2")
    """

    DEFAULT_BASE_URL = "https://api.aribot.ayurak.com/aribot-api"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
        max_retries: int = 3,
        verify_ssl: bool = True,
    ):
        self.api_key = api_key or os.environ.get("ARIBOT_API_KEY")
        if not self.api_key:
            raise AuthenticationError(
                "API key required. Pass api_key parameter or set ARIBOT_API_KEY env var."
            )

        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.verify_ssl = verify_ssl

        # Initialize resource managers
        self.threat_modeling = ThreatModelingResource(self)
        self.cloud_security = CloudSecurityResource(self)
        self.compliance = ComplianceResource(self)
        self.economics = EconomicsResource(self)
        self.finops = FinOpsResource(self)
        self.redteam = RedTeamResource(self)
        self.architecture = ArchitectureResource(self)
        self.user = UserResource(self)
        self.ai = AIResource(self)  # Secure AI usage management

        # Aliases for convenience
        self.diagrams = self.threat_modeling  # Backward compatibility

    def _get_headers(self, content_type: str = "application/json") -> Dict[str, str]:
        """Get request headers with authentication."""
        headers = {
            "X-API-Key": self.api_key,
            "User-Agent": f"aribot-sdk/{__version__} (Python)",
            "X-Request-ID": secrets.token_urlsafe(16),
            "X-Request-Timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if content_type:
            headers["Content-Type"] = content_type
        return headers

    def _get_auth_header(self) -> Dict[str, str]:
        """Get Authorization header only (for file uploads)."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": f"aribot-sdk/{__version__} (Python)",
            "X-Request-ID": secrets.token_urlsafe(16),
            "X-Request-Timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict] = None,
        files: Optional[Dict] = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Any:
        """Make API request with retry logic."""
        url = f"{self.base_url}{endpoint}"

        # Choose headers based on request type
        if files:
            headers = self._get_auth_header()
        else:
            headers = self._get_headers()

        last_error = None
        for attempt in range(self.max_retries):
            try:
                with httpx.Client(
                    timeout=self.timeout,
                    verify=self.verify_ssl
                ) as client:
                    if method == "GET":
                        response = client.get(url, headers=headers, params=params)
                    elif method == "POST":
                        if files:
                            response = client.post(
                                url, headers=headers, files=files, data=data
                            )
                        else:
                            response = client.post(
                                url, headers=headers, json=json_data, params=params
                            )
                    elif method == "PUT":
                        response = client.put(
                            url, headers=headers, json=json_data, params=params
                        )
                    elif method == "PATCH":
                        response = client.patch(
                            url, headers=headers, json=json_data, params=params
                        )
                    elif method == "DELETE":
                        response = client.delete(url, headers=headers, params=params)
                    else:
                        raise ValueError(f"Unsupported method: {method}")

                    return self._handle_response(response)

            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    sleep_time = (2 ** attempt) + (secrets.randbelow(1000) / 1000)
                    logger.warning(f"Request failed, retrying in {sleep_time:.2f}s...")
                    time.sleep(sleep_time)
                continue
            except RateLimitError as e:
                if attempt < self.max_retries - 1 and e.retry_after:
                    logger.warning(f"Rate limited, waiting {e.retry_after}s...")
                    time.sleep(e.retry_after)
                    continue
                raise

        raise APIError(f"Request failed after {self.max_retries} attempts: {last_error}")

    def _handle_response(self, response: httpx.Response) -> Any:
        """Handle API response and raise appropriate errors."""
        if response.status_code in (200, 201, 202):
            try:
                return response.json()
            except Exception:
                return response.content

        elif response.status_code == 401:
            raise AuthenticationError("Invalid or expired API key")

        elif response.status_code == 403:
            raise AuthenticationError("Access denied. Check API key permissions.")

        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                "Rate limit exceeded",
                retry_after=int(retry_after) if retry_after else None
            )

        elif response.status_code == 404:
            raise APIError("Resource not found", status_code=404)

        else:
            try:
                error_data = response.json()
                message = error_data.get("detail") or error_data.get("message") or str(error_data)
            except Exception:
                message = response.text or f"HTTP {response.status_code}"

            raise APIError(message, status_code=response.status_code)


# =============================================================================
# THREAT MODELING RESOURCE
# =============================================================================

class ThreatModelingResource:
    """
    Advanced AI-powered threat modeling with multi-framework analysis.

    Supported Frameworks:
        - STRIDE: Spoofing, Tampering, Repudiation, Info Disclosure, DoS, Elevation
        - PASTA: Process for Attack Simulation and Threat Analysis
        - NIST: National Institute of Standards threat methodology
        - Aristiun: Proprietary advanced threat intelligence framework
    """

    def __init__(self, client: AribotClient):
        self._client = client

    def list(self, limit: int = 20, offset: int = 0) -> Dict[str, Any]:
        """List all threat model diagrams."""
        return self._client._request(
            "GET",
            "/v2/threat-modeling/diagrams/",
            params={"limit": limit, "offset": offset}
        )

    def get(self, diagram_id: str) -> Diagram:
        """Get a specific diagram."""
        data = self._client._request("GET", f"/v2/threat-modeling/diagrams/{diagram_id}/")
        return Diagram.from_dict(data)

    def upload(
        self,
        file_path: Union[str, Path],
        name: Optional[str] = None,
        auto_generate_threats: bool = True,
    ) -> Dict[str, Any]:
        """Upload and analyze a diagram file."""
        file_path = Path(file_path)
        if not file_path.exists():
            raise ValidationError(f"File not found: {file_path}")

        with open(file_path, "rb") as f:
            files = {"file": (file_path.name, f)}
            data = {
                "name": name or file_path.stem,
                "auto_generate_threats": str(auto_generate_threats).lower()
            }
            return self._client._request(
                "POST",
                "/v2/threat-modeling/diagrams/upload-analyze/",
                files=files,
                data=data
            )

    def get_threats(self, diagram_id: str, severity: Optional[str] = None) -> List[Threat]:
        """Get threats for a diagram."""
        params = {"severity": severity} if severity else {}
        data = self._client._request(
            "GET",
            f"/v2/threat-modeling/diagrams/{diagram_id}/threats/",
            params=params
        )
        threats_list = data.get("threats") or data.get("results") or []
        return [Threat.from_dict(t) for t in threats_list]

    def generate_threats(
        self,
        diagram_id: str,
        wait_for_completion: bool = True,
        timeout: int = 120,
    ) -> Dict[str, Any]:
        """Generate AI threats for a diagram."""
        self._client._request(
            "POST",
            f"/v2/threat-modeling/diagrams/{diagram_id}/analyze-threats/"
        )

        if wait_for_completion:
            start_time = time.time()
            while time.time() - start_time < timeout:
                data = self._client._request(
                    "GET",
                    f"/v2/threat-modeling/diagrams/{diagram_id}/"
                )
                if data.get("ai_threats_generated") or data.get("stage") == "completed":
                    return data
                time.sleep(2)

        return self._client._request("GET", f"/v2/threat-modeling/diagrams/{diagram_id}/")

    def export(
        self,
        diagram_id: str,
        format: str = "json",
        output_path: Optional[Union[str, Path]] = None,
    ) -> Union[Dict, bytes]:
        """Export diagram report."""
        data = self._client._request(
            "GET",
            f"/v2/threat-modeling/diagrams/{diagram_id}/export/",
            params={"format": format}
        )

        if output_path:
            output_path = Path(output_path)
            if isinstance(data, bytes):
                output_path.write_bytes(data)
            else:
                import json
                output_path.write_text(json.dumps(data, indent=2))

        return data


# =============================================================================
# CLOUD SECURITY RESOURCE
# =============================================================================

class CloudSecurityResource:
    """Cloud Security Posture Management (CSPM) and CNAPP."""

    def __init__(self, client: AribotClient):
        self._client = client

    def scan_posture(self, cloud_provider: Optional[str] = None) -> Dict[str, Any]:
        """Run cloud security posture scan."""
        params = {"provider": cloud_provider} if cloud_provider else {}
        return self._client._request(
            "POST",
            "/v2/cloud-security/scan/",
            params=params
        )

    def get_findings(
        self,
        severity: Optional[str] = None,
        status: str = "open",
        limit: int = 50,
    ) -> List[SecurityFinding]:
        """Get security findings."""
        params = {"status": status, "limit": limit}
        if severity:
            params["severity"] = severity

        data = self._client._request(
            "GET",
            "/v2/cloud-security/findings/",
            params=params
        )
        findings = data.get("results") or data.get("findings") or []
        return [SecurityFinding.from_dict(f) for f in findings]

    def get_dashboard(self) -> Dict[str, Any]:
        """Get cloud security dashboard metrics."""
        return self._client._request("GET", "/v2/cloud-security/dashboard/")

    def remediate(self, finding_id: str, auto_fix: bool = False) -> Dict[str, Any]:
        """Remediate a security finding."""
        return self._client._request(
            "POST",
            f"/v2/cloud-security/findings/{finding_id}/remediate/",
            json_data={"auto_fix": auto_fix}
        )


# =============================================================================
# COMPLIANCE RESOURCE
# =============================================================================

class ComplianceResource:
    """
    Compliance management for 100+ regulatory standards.

    Supported Standards:
        SOC2, ISO27001, NIST CSF, NIST 800-53, PCI-DSS, GDPR, HIPAA,
        FedRAMP, CIS Benchmarks, CCPA, SOX, GLBA, FISMA, and many more.
    """

    # List of supported compliance standards
    SUPPORTED_STANDARDS = [
        "SOC2", "ISO27001", "ISO27017", "ISO27018", "ISO22301",
        "NIST-CSF", "NIST-800-53", "NIST-800-171",
        "PCI-DSS", "PCI-DSS-4.0",
        "GDPR", "CCPA", "LGPD", "PIPEDA",
        "HIPAA", "HITRUST",
        "FedRAMP-Low", "FedRAMP-Moderate", "FedRAMP-High",
        "CIS-AWS", "CIS-Azure", "CIS-GCP", "CIS-Kubernetes",
        "SOX", "GLBA", "FISMA",
        "CSA-CCM", "CSA-STAR",
        "MITRE-ATT&CK", "OWASP-TOP-10",
    ]

    def __init__(self, client: AribotClient):
        self._client = client

    def list_standards(self) -> List[Dict[str, Any]]:
        """List all available compliance standards."""
        return self._client._request("GET", "/v2/compliances/custom-standards/")

    def assess(
        self,
        diagram_id: str,
        standard: str = "SOC2",
        include_recommendations: bool = True,
    ) -> ComplianceAssessment:
        """
        Assess a diagram against a compliance standard.

        Args:
            diagram_id: UUID of the diagram to assess.
            standard: Compliance standard (e.g., SOC2, ISO27001, PCI-DSS).
            include_recommendations: Include remediation recommendations.

        Returns:
            ComplianceAssessment object.
        """
        data = self._client._request(
            "POST",
            "/v2/compliances/assess_diagram/",
            json_data={
                "diagram_id": diagram_id,
                "standard": standard,
                "include_recommendations": include_recommendations,
            }
        )
        return ComplianceAssessment.from_dict(data)

    def get_assessment(self, assessment_id: str) -> ComplianceAssessment:
        """Get a specific compliance assessment."""
        data = self._client._request(
            "GET",
            f"/v2/compliances/compliance-reports/{assessment_id}/"
        )
        return ComplianceAssessment.from_dict(data)

    def list_reports(self, limit: int = 20) -> List[ComplianceAssessment]:
        """List compliance reports."""
        data = self._client._request(
            "GET",
            "/v2/compliances/reports/",
            params={"limit": limit}
        )
        reports = data.get("results") or []
        return [ComplianceAssessment.from_dict(r) for r in reports]

    def run_scan(
        self,
        target_id: str,
        standards: List[str] = None,
        scan_type: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Run a compliance scan against multiple standards.

        Args:
            target_id: Diagram or resource ID to scan.
            standards: List of standards to check. Defaults to all applicable.
            scan_type: 'quick', 'standard', or 'comprehensive'.

        Returns:
            Scan results with findings per standard.
        """
        return self._client._request(
            "POST",
            "/v2/compliances/scan/",
            json_data={
                "target_id": target_id,
                "standards": standards or ["SOC2", "ISO27001"],
                "scan_type": scan_type,
            }
        )

    def get_remediation(self, finding_id: str) -> Dict[str, Any]:
        """Get remediation steps for a compliance finding."""
        return self._client._request(
            "GET",
            f"/v2/compliances/remediation/{finding_id}/"
        )

    def get_dashboard(self) -> Dict[str, Any]:
        """Get compliance dashboard with trends and stats."""
        return self._client._request("GET", "/v2/compliances/dashboard/trends/")


# =============================================================================
# ECONOMICS INTELLIGENCE RESOURCE
# =============================================================================

class EconomicsResource:
    """Security economics, ROI analysis, and risk quantification."""

    def __init__(self, client: AribotClient):
        self._client = client

    def calculate_roi(
        self,
        security_investment: float,
        risk_reduction_percent: float = 50,
        time_horizon_years: int = 3,
    ) -> Dict[str, Any]:
        """
        Calculate security ROI.

        Args:
            security_investment: Total security investment in USD.
            risk_reduction_percent: Expected risk reduction percentage.
            time_horizon_years: Analysis time horizon.

        Returns:
            ROI analysis with NPV, payback period, etc.
        """
        return self._client._request(
            "POST",
            "/v2/economic-intelligence/v2/roi/create/",
            json_data={
                "investment": security_investment,
                "risk_reduction": risk_reduction_percent,
                "time_horizon": time_horizon_years,
            }
        )

    def calculate_tco(
        self,
        cloud_provider: str,
        workload_type: str = "general",
        duration_months: int = 36,
    ) -> Dict[str, Any]:
        """
        Calculate Total Cost of Ownership.

        Args:
            cloud_provider: 'aws', 'azure', 'gcp'.
            workload_type: 'general', 'compute', 'storage', 'ai_ml'.
            duration_months: TCO calculation period.

        Returns:
            TCO breakdown with costs per category.
        """
        return self._client._request(
            "POST",
            "/v2/economic-intelligence/tco/",
            json_data={
                "provider": cloud_provider,
                "workload_type": workload_type,
                "duration_months": duration_months,
            }
        )

    def analyze_costs(self, diagram_id: str) -> Dict[str, Any]:
        """Analyze security costs for an architecture."""
        return self._client._request(
            "POST",
            "/v2/economic-intelligence/analyze/",
            json_data={"diagram_id": diagram_id}
        )

    def get_market_intelligence(self) -> Dict[str, Any]:
        """Get security market intelligence and trends."""
        return self._client._request("GET", "/v2/economic-intelligence/v2/intelligence/")

    def get_dashboard(self) -> Dict[str, Any]:
        """Get economics dashboard for the company."""
        return self._client._request("GET", "/v2/economic-intelligence/v2/dashboard/")

    def create_forecast(self, months: int = 12) -> Dict[str, Any]:
        """Create economic forecast for security spending."""
        return self._client._request(
            "POST",
            "/v2/economic-intelligence/v2/forecast/create/",
            json_data={"forecast_months": months}
        )


# =============================================================================
# FINOPS RESOURCE
# =============================================================================

class FinOpsResource:
    """Cloud FinOps - Cost optimization and security spend tracking."""

    def __init__(self, client: AribotClient):
        self._client = client

    def get_cloud_costs(
        self,
        provider: Optional[str] = None,
        period: str = "month",
    ) -> Dict[str, Any]:
        """Get cloud cost breakdown."""
        params = {"period": period}
        if provider:
            params["provider"] = provider
        return self._client._request(
            "GET",
            "/v2/finops/costs/",
            params=params
        )

    def get_security_spend(self) -> Dict[str, Any]:
        """Get security-specific spending breakdown."""
        return self._client._request("GET", "/v2/finops/security-spend/")

    def get_optimization_recommendations(self) -> List[Dict[str, Any]]:
        """Get cost optimization recommendations."""
        data = self._client._request("GET", "/v2/finops/recommendations/")
        return data.get("recommendations") or []

    def get_pricing(self, service: str, provider: str = "aws") -> Dict[str, Any]:
        """Get current cloud pricing for a service."""
        return self._client._request(
            "GET",
            "/v2/economic-intelligence/pricing/",
            params={"service": service, "provider": provider}
        )


# =============================================================================
# RED TEAM RESOURCE
# =============================================================================

class RedTeamResource:
    """
    Automated red team simulations and attack path analysis.

    Attack Types:
        - lateral_movement: Simulate lateral movement attacks
        - privilege_escalation: Test privilege escalation paths
        - data_exfiltration: Simulate data theft scenarios
        - ransomware: Ransomware attack simulation
        - supply_chain: Supply chain attack vectors
        - insider_threat: Insider threat scenarios
    """

    ATTACK_TYPES = [
        "lateral_movement",
        "privilege_escalation",
        "data_exfiltration",
        "ransomware",
        "supply_chain",
        "insider_threat",
        "credential_theft",
        "api_abuse",
    ]

    def __init__(self, client: AribotClient):
        self._client = client

    def run_simulation(
        self,
        target_id: str,
        attack_type: str = "lateral_movement",
        intensity: str = "medium",
    ) -> Dict[str, Any]:
        """
        Run an attack simulation.

        Args:
            target_id: Diagram or infrastructure ID to test.
            attack_type: Type of attack to simulate.
            intensity: 'low', 'medium', 'high'.

        Returns:
            Simulation results with attack paths and vulnerabilities.
        """
        if attack_type not in self.ATTACK_TYPES:
            raise ValidationError(f"Invalid attack type. Choose from: {self.ATTACK_TYPES}")

        return self._client._request(
            "POST",
            "/v2/redteam/simulate/",
            json_data={
                "target_id": target_id,
                "attack_type": attack_type,
                "intensity": intensity,
            }
        )

    def get_attack_paths(self, diagram_id: str) -> List[Dict[str, Any]]:
        """Get potential attack paths for an architecture."""
        data = self._client._request(
            "GET",
            f"/v2/threat-modeling/diagrams/{diagram_id}/attack-paths/"
        )
        return data.get("attack_paths") or []

    def list_simulations(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List past simulations."""
        data = self._client._request(
            "GET",
            "/v2/redteam/simulations/",
            params={"limit": limit}
        )
        return data.get("results") or []

    def get_simulation(self, simulation_id: str) -> Dict[str, Any]:
        """Get details of a specific simulation."""
        return self._client._request("GET", f"/v2/redteam/simulations/{simulation_id}/")


# =============================================================================
# ARCHITECTURE RESOURCE
# =============================================================================

class ArchitectureResource:
    """Living Strategic Architecture - Dynamic architecture management."""

    def __init__(self, client: AribotClient):
        self._client = client

    def list_components(self, diagram_id: str) -> List[Dict[str, Any]]:
        """List all components in an architecture."""
        data = self._client._request(
            "GET",
            f"/v2/threat-modeling/diagrams/{diagram_id}/components/"
        )
        return data.get("components") or data.get("results") or []

    def get_component(self, diagram_id: str, component_id: str) -> Dict[str, Any]:
        """Get details of a specific component."""
        return self._client._request(
            "GET",
            f"/v2/threat-modeling/diagrams/{diagram_id}/components/{component_id}/"
        )

    def update_component(
        self,
        diagram_id: str,
        component_id: str,
        **updates,
    ) -> Dict[str, Any]:
        """Update a component's properties."""
        return self._client._request(
            "PATCH",
            f"/v2/threat-modeling/diagrams/{diagram_id}/components/{component_id}/",
            json_data=updates
        )

    def get_connections(self, diagram_id: str) -> List[Dict[str, Any]]:
        """Get all connections/data flows in an architecture."""
        data = self._client._request(
            "GET",
            f"/v2/threat-modeling/diagrams/{diagram_id}/connections/"
        )
        return data.get("connections") or data.get("results") or []


# =============================================================================
# USER RESOURCE
# =============================================================================

class UserResource:
    """User and account management."""

    def __init__(self, client: AribotClient):
        self._client = client

    def me(self) -> Dict[str, Any]:
        """Get current user information."""
        return self._client._request("GET", "/v1/users/me/")

    def api_keys(self) -> List[Dict[str, Any]]:
        """List API keys for the current user."""
        return self._client._request("GET", "/v1/developer/api-keys/")

    def get_usage(self) -> Dict[str, Any]:
        """Get API usage statistics."""
        return self._client._request("GET", "/v1/developer/usage/")

    def get_rate_limits(self) -> Dict[str, Any]:
        """Get current rate limit status."""
        return self._client._request("GET", "/v1/developer/rate-limits/")


# =============================================================================
# AI RESOURCE - Secure AI Usage Management
# =============================================================================

class AIResource:
    """
    Secure AI usage management and configuration.

    Features:
        - AI model selection and configuration
        - Usage tracking and quotas
        - Cost monitoring for AI operations
        - Secure prompt/response handling
        - AI processing queue management

    Security:
        - All AI requests are signed and authenticated
        - Sensitive data is sanitized before AI processing
        - Usage is tracked per API key for audit compliance
        - Rate limiting prevents abuse
    """

    # Supported AI operations
    AI_OPERATIONS = [
        "threat_analysis",
        "diagram_parsing",
        "compliance_mapping",
        "risk_scoring",
        "attack_path_analysis",
        "remediation_generation",
        "architecture_optimization",
    ]

    # AI model tiers
    MODEL_TIERS = ["standard", "advanced", "enterprise"]

    def __init__(self, client: "AribotClient"):
        self._client = client

    def get_usage(self) -> Dict[str, Any]:
        """
        Get AI usage statistics for the current billing period.

        Returns:
            Dict with:
                - total_requests: Total AI requests made
                - tokens_used: Total tokens consumed
                - cost_usd: Estimated cost in USD
                - quota_remaining: Remaining quota
                - reset_date: Quota reset date
        """
        return self._client._request("GET", "/v2/ai/usage/")

    def get_quota(self) -> Dict[str, Any]:
        """Get current AI quota and limits."""
        return self._client._request("GET", "/v2/ai/quota/")

    def get_models(self) -> List[Dict[str, Any]]:
        """
        List available AI models for your subscription tier.

        Returns:
            List of available models with capabilities and pricing.
        """
        return self._client._request("GET", "/v2/ai/models/")

    def configure(
        self,
        model_tier: str = "standard",
        max_tokens: int = 4000,
        temperature: float = 0.7,
        enable_caching: bool = True,
    ) -> Dict[str, Any]:
        """
        Configure AI settings for your account.

        Args:
            model_tier: 'standard', 'advanced', or 'enterprise'
            max_tokens: Maximum tokens per request
            temperature: Model temperature (0.0-1.0)
            enable_caching: Cache similar requests to reduce costs

        Returns:
            Updated configuration
        """
        if model_tier not in self.MODEL_TIERS:
            raise ValidationError(f"Invalid model tier. Choose from: {self.MODEL_TIERS}")

        return self._client._request(
            "POST",
            "/v2/ai/configure/",
            json_data={
                "model_tier": model_tier,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "enable_caching": enable_caching,
            }
        )

    def analyze(
        self,
        content: str,
        operation: str = "threat_analysis",
        context: Optional[Dict[str, Any]] = None,
        sanitize_pii: bool = True,
    ) -> Dict[str, Any]:
        """
        Run AI analysis on content.

        Args:
            content: Content to analyze (text, JSON, etc.)
            operation: Type of analysis to perform
            context: Additional context for the analysis
            sanitize_pii: Remove PII before processing (recommended)

        Returns:
            Analysis results

        Security:
            - PII is automatically detected and masked when sanitize_pii=True
            - All content is encrypted in transit
            - Requests are signed for integrity verification
        """
        if operation not in self.AI_OPERATIONS:
            raise ValidationError(f"Invalid operation. Choose from: {self.AI_OPERATIONS}")

        return self._client._request(
            "POST",
            "/v2/ai/analyze/",
            json_data={
                "content": content,
                "operation": operation,
                "context": context or {},
                "sanitize_pii": sanitize_pii,
            }
        )

    def get_queue_status(self) -> Dict[str, Any]:
        """Get status of pending AI processing jobs."""
        return self._client._request("GET", "/v2/ai/queue/status/")

    def list_jobs(self, status: str = "all", limit: int = 20) -> List[Dict[str, Any]]:
        """
        List AI processing jobs.

        Args:
            status: Filter by status ('pending', 'processing', 'completed', 'failed', 'all')
            limit: Maximum number of jobs to return

        Returns:
            List of AI jobs with status and results
        """
        data = self._client._request(
            "GET",
            "/v2/ai/jobs/",
            params={"status": status, "limit": limit}
        )
        return data.get("results") or []

    def get_job(self, job_id: str) -> Dict[str, Any]:
        """Get details of a specific AI job."""
        return self._client._request("GET", f"/v2/ai/jobs/{job_id}/")

    def cancel_job(self, job_id: str) -> Dict[str, Any]:
        """Cancel a pending AI job."""
        return self._client._request("POST", f"/v2/ai/jobs/{job_id}/cancel/")

    def get_cost_estimate(
        self,
        operation: str,
        content_length: int,
        model_tier: str = "standard",
    ) -> Dict[str, Any]:
        """
        Get cost estimate for an AI operation before executing.

        Args:
            operation: Type of AI operation
            content_length: Approximate content length in characters
            model_tier: Model tier to use

        Returns:
            Cost estimate with token count and USD amount
        """
        return self._client._request(
            "POST",
            "/v2/ai/estimate/",
            json_data={
                "operation": operation,
                "content_length": content_length,
                "model_tier": model_tier,
            }
        )

    def get_audit_log(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Get AI usage audit log for compliance.

        Args:
            start_date: Filter from date (ISO format)
            end_date: Filter to date (ISO format)
            limit: Maximum entries to return

        Returns:
            Audit log entries with timestamps, operations, and costs
        """
        params = {"limit": limit}
        if start_date:
            params["start_date"] = start_date
        if end_date:
            params["end_date"] = end_date

        data = self._client._request("GET", "/v2/ai/audit/", params=params)
        return data.get("entries") or []


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_diagram(
    file_path: Union[str, Path],
    api_key: Optional[str] = None,
    name: Optional[str] = None,
    wait_for_threats: bool = True,
) -> Dict[str, Any]:
    """
    Quick function to analyze a diagram and get threats.

    Args:
        file_path: Path to the diagram file.
        api_key: API key. Reads from ARIBOT_API_KEY if not provided.
        name: Optional name for the diagram.
        wait_for_threats: Whether to wait for AI threat generation.

    Returns:
        Dict with diagram info and threats.

    Example:
        >>> result = analyze_diagram("architecture.png")
        >>> print(f"Found {len(result['threats'])} threats")
    """
    client = AribotClient(api_key=api_key)
    diagram = client.threat_modeling.upload(
        file_path,
        name=name,
        auto_generate_threats=wait_for_threats
    )

    if wait_for_threats:
        time.sleep(2)
        for _ in range(30):
            updated = client.threat_modeling.get(diagram["id"])
            if updated.stage == "completed":
                break
            time.sleep(2)

        threats = client.threat_modeling.get_threats(diagram["id"])
        return {
            "diagram": diagram,
            "threats": [
                {
                    "id": t.id,
                    "title": t.title,
                    "severity": t.severity,
                    "category": t.category,
                    "description": t.description,
                }
                for t in threats
            ]
        }

    return {"diagram": diagram, "threats": []}


def run_compliance_check(
    diagram_id: str,
    standards: List[str] = None,
    api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Quick compliance check against multiple standards.

    Args:
        diagram_id: UUID of the diagram.
        standards: List of standards. Defaults to SOC2 and ISO27001.
        api_key: API key. Reads from ARIBOT_API_KEY if not provided.

    Returns:
        Compliance results per standard.
    """
    client = AribotClient(api_key=api_key)
    return client.compliance.run_scan(
        target_id=diagram_id,
        standards=standards or ["SOC2", "ISO27001"],
    )
