# Precogs SDK

Official Python SDK for the [Precogs AI](https://precogs.ai) security platform.

## Installation

```bash
pip install precogs-sdk
```

## Quick Start

```python
from precogs import PrecogsClient

# Initialize with your API key
client = PrecogsClient(api_key="pk_live_xxxxxxxxxxxx")

# Or use environment variable
# export PRECOGS_API_KEY=pk_live_xxxxxxxxxxxx
client = PrecogsClient()

# List your projects
projects = client.projects.list()
for project in projects:
    print(f"Project: {project['name']}")

# Trigger a code scan
scan = client.scans.trigger_code_scan(project_id="proj_123")
print(f"Scan started: {scan['id']}")

# Get vulnerabilities
vulns = client.vulnerabilities.list(severity="critical")
for vuln in vulns:
    print(f"[{vuln['severity']}] {vuln['title']}")
```

## Features

- **Code Security Scanning** - SAST analysis for 20+ languages
- **Dependency Scanning** - SCA for npm, pip, maven, etc.
- **IaC Scanning** - Terraform, CloudFormation, Kubernetes
- **Container Scanning** - Docker image vulnerability detection
- **AI-Powered Fixes** - Get suggested code fixes for vulnerabilities

## API Reference

### Projects

```python
# List all projects
projects = client.projects.list()

# Get a specific project
project = client.projects.get("proj_123")

# Create a new project
project = client.projects.create(
    name="My App",
    repo_url="https://github.com/org/repo",
    provider="github",
    branch="main"
)
```

### Scans

```python
# Trigger different scan types
scan = client.scans.trigger_code_scan(project_id="proj_123")
scan = client.scans.trigger_dependency_scan(project_id="proj_123")
scan = client.scans.trigger_iac_scan(project_id="proj_123")
scan = client.scans.trigger_container_scan(
    project_id="proj_123", 
    image="nginx:latest"
)

# Check scan status
status = client.scans.get_status(scan_id="scan_456")

# Get scan results
results = client.scans.get_results(scan_id="scan_456")
```

### Vulnerabilities

```python
# List vulnerabilities with filters
vulns = client.vulnerabilities.list(
    project_id="proj_123",
    severity="high",
    status="open"
)

# Get vulnerability details
vuln = client.vulnerabilities.get("vuln_789")

# Get AI-generated fix
fix = client.vulnerabilities.get_ai_fix("vuln_789")
print(fix['suggestedCode'])

# Update status
client.vulnerabilities.update_status(
    vuln_id="vuln_789",
    status="fixed",
    reason="Patched in v2.1.0"
)
```

### Dashboard

```python
# Get overall security metrics
overview = client.dashboard.get_overview()

# Get severity distribution
distribution = client.dashboard.get_severity_distribution()

# Get vulnerability trend
trend = client.dashboard.get_trend(days=30)
```

## Error Handling

```python
from precogs import PrecogsClient, AuthenticationError, RateLimitError

try:
    client = PrecogsClient(api_key="pk_live_xxx")
    projects = client.projects.list()
except AuthenticationError:
    print("Invalid API key")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after} seconds")
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PRECOGS_API_KEY` | Your Precogs API key |

## License

MIT License - see [LICENSE](LICENSE) for details.