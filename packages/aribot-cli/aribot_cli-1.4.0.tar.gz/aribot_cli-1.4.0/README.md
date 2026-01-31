# Aribot - Economic, Regulatory & Security APIs for Modern Applications

**Analyze your tech stack. Optimize architecture. Model costs. Identify threats dynamically.**

APIs that help you build better systems with practical, actionable recommendations.

[![PyPI](https://img.shields.io/pypi/v/aribot-cli)](https://pypi.org/project/aribot-cli/)
[![Python](https://img.shields.io/pypi/pyversions/aribot-cli)](https://pypi.org/project/aribot-cli/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Why Aribot?

Modern applications need more than just security scanning. They need **intelligent analysis** that understands your architecture, quantifies your risks in dollars, and ensures compliance across 100+ regulatory standards.

**Aribot is the API layer your security, finance, and compliance teams have been waiting for.**

## Platform Capabilities

| Capability | What It Does |
|------------|--------------|
| **Advanced Threat Modeling** | Multi-framework analysis: STRIDE, PASTA, NIST, Aristiun Framework |
| **Cloud Security (CSPM/CNAPP)** | Real-time posture management across AWS, Azure, GCP |
| **100+ Compliance Standards** | SOC2, ISO27001, PCI-DSS, GDPR, HIPAA, NIST, FedRAMP, CIS... |
| **Economic Intelligence** | ROI calculations, TCO analysis, risk quantification in real dollars |
| **FinOps** | Cloud cost optimization with security-aware recommendations |
| **Red Team Automation** | Simulate attacks before attackers do |
| **Living Architecture** | Dynamic diagrams that evolve with your infrastructure |
| **AI-Powered Analysis** | Multi-provider AI (Google, OpenAI, Anthropic, Azure) |
| **Digital Twin** | Architecture digital twins with cloud provider integration |
| **SBOM Management** | Software Bill of Materials tracking and vulnerability analysis |

## Installation

```bash
pip install aribot-cli
```

## Quick Start (60 Seconds to Value)

```bash
# 1. Authenticate
aribot login

# 2. Analyze your architecture
aribot analyze architecture.png

# 3. See your threats (multi-framework)
aribot threats <diagram-id>

# 4. Run compliance assessment
aribot compliance <diagram-id> --standard SOC2

# 5. Get economic analysis
aribot economics --cost <diagram-id>

# AI-powered multi-framework threat modeling in 5 commands.
```

## SDK for Developers

```python
from aribot_cli import AribotClient

client = AribotClient(api_key="ak_...")

# Upload diagram, get AI threats across all frameworks
diagram = client.threat_modeling.upload("architecture.png")
threats = client.threat_modeling.get_threats(diagram["id"])

print(f"Found {len(threats)} threats across STRIDE, PASTA, NIST & Aristiun")
for t in threats:
    print(f"  [{t['severity'].upper()}] {t['title']} - {t['category']}")

# Run compliance assessment
assessment = client.compliance.assess(diagram["id"], standard="SOC2")
print(f"SOC2 Score: {assessment['score']}%")

# Calculate security ROI
roi = client.economics.calculate_roi(
    security_investment=100000,
    risk_reduction_percent=50
)
print(f"3-Year ROI: {roi['roi_percent']}%")
```

## API Coverage (100+ Endpoints)

### Threat Modeling (Multi-Framework)
```python
client.threat_modeling.upload(file)              # AI-powered multi-framework analysis
client.threat_modeling.list()                    # List all diagrams
client.threat_modeling.get(diagram_id)           # Get diagram details
client.threat_modeling.get_threats(diagram_id)   # Threats from STRIDE, PASTA, NIST, Aristiun
client.threat_modeling.generate_threats(id)      # On-demand AI threat generation
client.threat_modeling.export(id, format="pdf")  # Export reports
```

### AI & Machine Learning
```python
client.ai.get_usage()                            # AI usage statistics
client.ai.get_quota()                            # AI quota and limits
client.ai.get_models()                           # Available AI models
client.ai.configure(options)                     # Configure AI settings
client.ai.analyze(content, options)              # Run AI analysis
client.ai.get_queue_status()                     # AI job queue status
```

### Compliance (100+ Standards)
```python
client.compliance.assess(id, "SOC2")             # Single standard assessment
client.compliance.run_scan(id, ["SOC2", "GDPR"]) # Multi-standard scan
client.compliance.list_standards()               # List available standards
client.compliance.list_reports()                 # Compliance reports
client.compliance.get_remediation(finding_id)    # Fix guidance
```

### Economic Intelligence
```python
client.economics.calculate_roi(investment)       # Security ROI
client.economics.calculate_tco("aws")            # Total cost of ownership
client.economics.analyze_costs(diagram_id)       # Diagram cost analysis
client.economics.get_market_intelligence()       # Industry benchmarks
client.economics.get_dashboard()                 # Economic dashboard
```

### Cloud Security (CSPM/CNAPP)
```python
client.cloud_security.scan_posture()             # Cloud security scan
client.cloud_security.get_findings(severity)     # Security findings
client.cloud_security.get_dashboard()            # Security dashboard
client.cloud_security.remediate(id)              # Auto-remediation
```

### Red Team & Attack Simulation
```python
client.threat_engine.list_methodologies()        # STRIDE, PASTA, NIST, etc.
client.threat_engine.get_threat_intelligence()   # Real-time threat intel
client.threat_engine.analyze_attack_paths(id)    # AI attack path analysis
client.threat_engine.comprehensive_analysis(id)  # Full threat analysis
client.threat_engine.generate_requirements(id)   # Security requirements
```

### Architecture Components
```python
client.architecture.list_components(diagram_id)  # List components
client.architecture.get_component(id, comp_id)   # Component details
client.architecture.update_component(id, data)   # Update component
client.architecture.get_connections(diagram_id)  # Get connections
```

## Supported Compliance Standards

**Financial**: SOC2, PCI-DSS, PCI-DSS-4.0, SOX, GLBA
**Healthcare**: HIPAA, HITRUST
**Privacy**: GDPR, CCPA, LGPD, PIPEDA
**Government**: FedRAMP-Low/Moderate/High, FISMA, NIST 800-53, NIST 800-171
**Cloud**: CIS AWS, CIS Azure, CIS GCP, CIS Kubernetes
**Security**: ISO27001, ISO27017, ISO27018, ISO22301, NIST CSF, CSA CCM, CSA STAR
**Attack Frameworks**: MITRE ATT&CK, OWASP TOP-10

## Secure by Design

- **OS Keyring Storage**: API keys stored in macOS Keychain, Windows Credential Manager, or Linux Secret Service
- **No Keys in Code**: Environment variable fallback (`ARIBOT_API_KEY`)
- **Request Signing**: HMAC-SHA256 signatures for integrity
- **Automatic Retry**: Exponential backoff with jitter
- **Rate Limit Handling**: Graceful degradation

## CLI Commands

### Authentication & Status
```bash
aribot login                  # Authenticate with API key
aribot login --open-portal    # Open developer portal
aribot logout                 # Clear credentials
aribot whoami                 # Current user info
aribot status                 # API status & rate limits
```

### Threat Modeling
```bash
aribot diagrams               # List your diagrams
aribot diagrams --limit 50    # List with limit
aribot analyze <file>         # Upload & analyze diagram
aribot analyze <file> -n name # With custom name
aribot threats <id>           # View threats for diagram
aribot threats <id> -s high   # Filter by severity
aribot generate-threats <id>  # AI threat generation
aribot export <id>            # Export JSON report
aribot export <id> -f pdf     # Export PDF report
```

### Red Team & Attack Simulation
```bash
aribot redteam --methodologies              # List threat modeling methodologies
aribot redteam --intelligence               # Get threat intelligence summary
aribot redteam --attack-paths -d <id>       # Analyze attack paths
aribot redteam --analyze <id>               # Comprehensive threat analysis
aribot redteam --requirements <id>          # Generate security requirements
aribot redteam --ai-insights <id>           # AI architecture insights
aribot redteam --simulate APT29 --target <id>  # Adversary simulation
```

### Compliance & Security
```bash
aribot compliance --list-standards          # List 100+ compliance standards
aribot compliance <id>                      # Run SOC2 assessment (default)
aribot compliance <id> -s ISO27001          # Specific standard
aribot cloud-security --scan                # Cloud security scan
aribot cloud-security --scan aws            # Provider-specific scan
aribot cloud-security --findings            # View security findings
aribot cloud-security --findings -s critical  # Filter by severity
aribot cloud-security --dashboard           # Security dashboard
```

### Cloud Scanning & Unified Scanner
```bash
# Dynamic scanning
aribot cloud-security --dynamic-scan <account-id>     # Run dynamic cloud scan

# Unified scanning with scope
aribot cloud-security --unified-scan --scope account --account-id 123
aribot cloud-security --unified-scan --scope standard --scope-id CIS-AWS
aribot cloud-security --unified-scan --scope diagram --scope-id <uuid>

# Scanner rules management
aribot cloud-security --rules                         # List scanner rules
aribot cloud-security --rules -s critical             # Filter by severity
aribot cloud-security --create-rule                   # Create custom rule
aribot cloud-security --sync-rules                    # Sync from cloud providers
aribot cloud-security --scanner-stats                 # View scanner statistics

# Remediation
aribot cloud-security --remediate-preview <policy-id> --account-id 123
aribot cloud-security --remediate <policy-id> --account-id 123
```

### Economic Intelligence
```bash
aribot economics --dashboard                # Economic intelligence dashboard
aribot economics --roi 100000               # Calculate security ROI
aribot economics --tco <id>                 # TCO for diagram
aribot economics --cost <id>                # Cost intelligence
aribot economics --analyze <id>             # Cost analysis
```

### Digital Twin
```bash
aribot digital-twin --providers             # List cloud providers (AWS, Azure, GCP)
aribot digital-twin --resources             # List cloud resources
aribot digital-twin --resources aws         # Filter by provider
aribot digital-twin --health                # Digital twin health status
aribot digital-twin --sync <provider-id>    # Sync cloud resources
aribot digital-twin --discover <provider-id> # Discover new resources
```

### Dashboard
```bash
aribot dashboard --overview                 # Overall security dashboard
aribot dashboard --recent                   # Recent activity
aribot dashboard --risk                     # Risk summary
```

## Environment Variables

```bash
# Set API key via environment variable
export ARIBOT_API_KEY=ak_your_api_key_here

# Then use without passing api_key
client = AribotClient()
```

## Error Handling

```python
from aribot_cli import AribotClient
from aribot_cli.exceptions import AuthenticationError, RateLimitError, APIError

try:
    client = AribotClient(api_key="ak_...")
    diagrams = client.threat_modeling.list()
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s")
except APIError as e:
    print(f"API Error: {e.status_code} - {e.message}")
```

## Resources

- **Platform**: [aribot.ayurak.com](https://aribot.ayurak.com)
- **Developer Portal**: [developer.ayurak.com](https://developer.ayurak.com)
- **API Docs**: [developer.ayurak.com/docs](https://developer.ayurak.com/docs)
- **Support**: support@ayurak.com

## Changelog

### v1.4.0 (2026-01-30)
- **Framework-Specific Compliance Scoring**: Each compliance standard now returns its own real score
  - NIST 800-53: 80.87% (183 controls, 148 passed, 35 failed)
  - SOC2: 90.99% (111 controls, 101 passed, 10 failed)
  - Powered by `ResultsRegulatory` per-framework, per-scan data
- **Export Endpoint Fix**: JSON export now uses correct `/report/` endpoint
- **Diagram ID Resolution**: Compliance command now resolves short UUIDs before API call
- **Red Team Methodologies**: Fixed fallback data when backend engine unavailable
- **All 14 CLI commands tested end-to-end** against production API
  - login, logout, whoami, status, diagrams, analyze, threats, export, generate-threats,
    compliance, economics, cloud-security, redteam, setup

### v1.3.3 (2026-01-30)
- **Compliance Assessment**: Fixed polling and real-time score retrieval
- **Diagram ID Resolution**: Support integer IDs and UUID prefix matching

### v1.2.0
- Added AI resource with usage tracking and configuration
- Added Digital Twin health and provider endpoints
- Added SBOM document management
- Added Marketplace templates and categories
- Added Knowledge Base with real-time threats
- Added Pipeline Security scanning
- Improved economic intelligence with cost analysis
- 111+ working API endpoints documented
- Updated compliance assessment endpoints

### v1.1.4
- Initial release with core threat modeling features

## License

MIT License - Copyright (c) 2026 Ayurak AI

---

**Built for teams who take security seriously.** Start analyzing in 60 seconds.
