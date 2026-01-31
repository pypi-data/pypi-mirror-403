# Nexula CLI

Enterprise-grade CLI for Nexula AI Supply Chain Security Platform.

## Installation

```bash
cd nexula-cli
pip install -e .
```

## Quick Start

### 1. Authentication

Login with your API key (generate from dashboard):

```bash
nexula auth login
# Enter API key when prompted
```

Check authentication status:

```bash
nexula auth whoami
```

### 2. Initialize Project

Initialize Nexula in your AI/ML project directory:

```bash
cd /path/to/your/ai-project
nexula init
```

This will:
- List available workspaces
- Let you select or create a project
- Save configuration to `.nexula.yaml`

### 3. Generate AIBOM

Generate AI Bill of Materials (discovers all AI/ML assets):

```bash
nexula aibom generate
```

List AIBOMs:

```bash
nexula aibom list
```

View AIBOM details:

```bash
nexula aibom view <aibom-id>
```

### 4. Run Security Scan

Run comprehensive security scan:

```bash
nexula scan run --wait
```

Run specific scanners:

```bash
nexula scan run --scanners sast --scanners cve --wait
```

Check scan status:

```bash
nexula scan status <scan-id>
```

View scan results:

```bash
nexula scan results <scan-id>
```

List all scans:

```bash
nexula scan list
```

## Available Scanners

- `sast` - Static Application Security Testing
- `cve` - CVE/Vulnerability Detection
- `secrets` - Secrets Detection
- `ml_poisoning` - ML Model Poisoning Detection
- `dataset_poisoning` - Dataset Poisoning Detection
- `llm_security` - LLM Security Analysis
- `rag_security` - RAG Security Analysis
- `model_provenance` - Model Provenance Verification
- `container_registry` - Container Registry Security
- `license` - License Compliance

## Configuration

### Global Config (`~/.nexula/config.yaml`)

Stores:
- API key (encrypted)
- API URL
- User preferences

### Project Config (`.nexula.yaml`)

Stores:
- Workspace ID
- Project ID
- Project-specific settings

## Commands Reference

### Auth Commands

```bash
nexula auth login              # Login with API key
nexula auth logout             # Logout and clear credentials
nexula auth whoami             # Show current user
```

### Project Commands

```bash
nexula init                    # Initialize project
nexula init --create           # Create new project
nexula init --workspace-id 1   # Use specific workspace
```

### AIBOM Commands

```bash
nexula aibom generate          # Generate AIBOM
nexula aibom generate --path . # Specify path
nexula aibom list              # List AIBOMs
nexula aibom view <id>         # View AIBOM details
```

### Scan Commands

```bash
nexula scan run                           # Run all scanners
nexula scan run --wait                    # Wait for completion
nexula scan run --scanners sast --scanners cve  # Specific scanners
nexula scan status <id>                   # Check status
nexula scan results <id>                  # View results
nexula scan results <id> --format json    # JSON output
nexula scan list                          # List scans
```

## CI/CD Integration

### GitHub Actions

```yaml
name: Nexula Security Scan

on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Install Nexula CLI
        run: pip install nexula-cli
      
      - name: Run Security Scan
        env:
          NEXULA_API_KEY: ${{ secrets.NEXULA_API_KEY }}
        run: |
          echo "$NEXULA_API_KEY" | nexula auth login --api-key -
          nexula init --workspace-id 1 --project-id 1
          nexula aibom generate
          nexula scan run --wait
```

### GitLab CI

```yaml
nexula-scan:
  image: python:3.11
  script:
    - pip install nexula-cli
    - echo "$NEXULA_API_KEY" | nexula auth login --api-key -
    - nexula init --workspace-id 1 --project-id 1
    - nexula aibom generate
    - nexula scan run --wait
  variables:
    NEXULA_API_KEY: $NEXULA_API_KEY
```

## Environment Variables

- `NEXULA_API_KEY` - API key (alternative to interactive login)
- `NEXULA_API_URL` - API URL (default: http://localhost:8000/api/v1)

## Troubleshooting

### Authentication Issues

```bash
# Clear credentials and re-login
nexula auth logout
nexula auth login
```

### Project Not Found

```bash
# Re-initialize project
nexula init
```

### API Connection Issues

```bash
# Check API URL
nexula auth whoami

# Set custom API URL
nexula auth login --api-url https://api.nexula.one/api/v1
```

## Support

- Documentation: https://docs.nexula.one
- Dashboard: https://cloud.nexula.one
- Issues: https://github.com/nexula/nexula-cli/issues
