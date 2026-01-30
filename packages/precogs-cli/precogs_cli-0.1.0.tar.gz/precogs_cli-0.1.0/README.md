# Precogs CLI

Command-line interface for the [Precogs AI](https://precogs.ai) security platform.

## Installation

```bash
pip install precogs-cli
```

## Quick Start

```bash
# Authenticate with your API key
precogs auth login

# List your projects
precogs projects list

# Trigger a code scan
precogs scan code <project-id>

# View vulnerabilities
precogs vulns list --severity critical

# Get AI-generated fix
precogs vulns fix <vuln-id>
```

## Commands

### Authentication

```bash
# Login with API key
precogs auth login
precogs auth login --api-key pk_live_xxx

# Check auth status
precogs auth status

# Logout
precogs auth logout
```

### Projects

```bash
# List all projects
precogs projects list

# Get project details
precogs projects get <project-id>
```

### Scanning

```bash
# Code security scan (SAST)
precogs scan code <project-id>
precogs scan code <project-id> --branch develop

# Dependency scan (SCA)
precogs scan dependency <project-id>

# Infrastructure as Code scan
precogs scan iac <project-id>

# Container image scan
precogs scan container <project-id> nginx:latest
```

### Vulnerabilities

```bash
# List vulnerabilities
precogs vulns list
precogs vulns list --project <id> --severity high

# Get vulnerability details
precogs vulns get <vuln-id>

# Get AI-generated fix
precogs vulns fix <vuln-id>
```

### Dashboard

```bash
# Show security overview
precogs dashboard
precogs dashboard --project <id>
```

## Configuration

API key is stored in `~/.precogs/config.json`

You can also set the `PRECOGS_API_KEY` environment variable:

```bash
export PRECOGS_API_KEY=pk_live_xxx
```

## License

MIT License - see [LICENSE](LICENSE) for details.