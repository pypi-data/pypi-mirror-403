# AiCippy

Enterprise-grade multi-agent CLI system powered by AWS Bedrock.

**Copyright (c) 2024-2026 AiVibe Software Services Pvt Ltd. All rights reserved.**

ISO 27001:2022 Certified | NVIDIA Inception Partner | AWS Activate | Microsoft for Startups

## Overview

AiCippy is a production-grade, multi-agent command-line system that orchestrates up to 10 parallel AI agents to complete complex tasks. Built on AWS Bedrock Agents, it provides:

- Multi-agent orchestration with parallel execution
- Real-time WebSocket communication
- MCP-style tool connectors for AWS, GitHub, Firebase, and more
- Knowledge Base integration with automated feed ingestion
- Rich terminal UI with live progress and agent status

## Installation

```bash
pip install aicippy
```

## Quick Start

```bash
# Authenticate
aicippy login

# Initialize in a project
aicippy init

# Interactive mode
aicippy

# Single query
aicippy chat "Explain this codebase"

# Multi-agent task
aicippy run "Deploy infrastructure to AWS" --agents 5
```

## Commands

| Command | Description |
|---------|-------------|
| `aicippy` | Start interactive session |
| `aicippy login` | Authenticate with Cognito |
| `aicippy logout` | Clear credentials |
| `aicippy init` | Initialize project context |
| `aicippy chat <msg>` | Single query mode |
| `aicippy run <task>` | Execute with agents |
| `aicippy config` | Show/edit configuration |
| `aicippy status` | Agent status |
| `aicippy usage` | Token usage |
| `aicippy upgrade` | Self-update |

## Interactive Commands

| Command | Description |
|---------|-------------|
| `/help` | Show all commands |
| `/model <name>` | Switch model (opus/sonnet/llama) |
| `/mode <name>` | Change mode (agent/edit/research/code) |
| `/agents spawn <n>` | Spawn parallel agents (1-10) |
| `/agents list` | List active agents |
| `/agents stop` | Stop agents |
| `/kb sync` | Sync to Knowledge Base |
| `/tools list` | List available tools |
| `/usage` | Token usage |
| `/quit` | Exit |

## Architecture

```
                     +----------------+
                     |   AiCippy CLI  |
                     +--------+-------+
                              |
                     +--------v--------+
                     | Agent Orchestrator |
                     +--------+---------+
                              |
         +--------------------+--------------------+
         |         |          |          |         |
    +----v----+ +--v---+ +----v---+ +----v----+ +--v----+
    |Agent-1  | |Agent-2| |Agent-3 | |Agent-4  | |Agent-N|
    |INFRA    | |BEDROCK| |API-GW  | |CLI-CORE | |...    |
    +---------+ +-------+ +--------+ +---------+ +-------+
         |         |          |          |         |
    +----v---------v----------v----------v---------v----+
    |              AWS Bedrock Runtime                  |
    +--------------------------------------------------+
```

## Supported Models

- **Claude Opus 4.5** (default) - Most capable model
- **Claude Sonnet 4.5** - Balanced performance
- **Llama 4 Maverick** - Open source alternative

## MCP Tool Connectors

- AWS CLI (`aws`)
- Google Cloud CLI (`gcloud`)
- GitHub CLI (`gh`)
- Firebase CLI (`firebase`)
- Figma API
- Google Drive API
- Gmail API
- Razorpay API
- PayPal API
- Stripe CLI
- Shell commands (sandboxed)

## Configuration

Environment variables (or `.env` file):

```bash
AICIPPY_AWS_REGION=us-east-1
AICIPPY_DEFAULT_MODEL=opus
AICIPPY_MAX_PARALLEL_AGENTS=10
AICIPPY_LOG_LEVEL=INFO
```

Configuration file: `~/.aicippy/config.toml`

## Security

- OAuth 2.0 authentication via AWS Cognito
- Tokens stored in OS keychain (macOS Keychain, Windows Credential Manager)
- All communications over TLS 1.3
- Secrets never logged or printed
- IAM least privilege roles

## Development

```bash
# Clone repository
git clone https://github.com/aivibe/aicippy.git
cd aicippy

# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run linter
ruff check src/

# Type checking
mypy src/aicippy/
```

## Infrastructure Deployment

```bash
# Install CDK dependencies
cd infrastructure
pip install -r requirements.txt

# Deploy all stacks
cdk deploy --all
```

## License

Proprietary - AiVibe Software Services Pvt Ltd

## Support

- Documentation: https://docs.aicippy.io
- Issues: https://github.com/aivibe/aicippy/issues
- Email: support@aivibe.in

---

Built with precision by AiVibe Software Services Pvt Ltd, Chennai, India.
