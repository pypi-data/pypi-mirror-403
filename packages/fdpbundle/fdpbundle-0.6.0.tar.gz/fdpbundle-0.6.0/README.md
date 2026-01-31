# FDP Bundle CLI

CLI tool for managing and deploying workflow bundles to FDP Workflow Engine.

## Installation

```bash
pip install fdpbundle
```

## Quick Start

### 1. Initialize a new project

```bash
fdpbundle init my-project
cd my-project
```

This command will create the following structure:

```
my-project/
├── bundles/
│   └── example/
│       └── bundle.json
├── .gitlab-ci.yml
├── .gitignore
├── .env.example
└── README.md
```

### 2. Configure credentials

```bash
cp .env.example .env
# Edit .env with your credentials
```

Or export environment variables:

```bash
export WORKFLOW_ENGINE_URL=https://airflow.example.com/fdp_tools
export SERVICE_ACCOUNT_NAME=your-service-account-name
export SERVICE_ACCOUNT_TOKEN=your-service-account-token
```

### 3. Validate bundle

```bash
fdpbundle validate bundles/example/bundle.json
```

### 4. Deploy

```bash
# Deploy to DEV
fdpbundle deploy bundles/example/bundle.json --env dev

# Dry run before production deployment
fdpbundle deploy bundles/example/bundle.json --env prod --dry-run

# Deploy to production
fdpbundle deploy bundles/example/bundle.json --env prod
```

## Commands

### `fdpbundle init [PROJECT_NAME]`

Initialize a new FDP bundles project with standard structure.

```bash
fdpbundle init my-project
fdpbundle init  # Use default name 'fdp-bundles'
fdpbundle init my-project --force  # Override if already exists
```

### `fdpbundle validate BUNDLE_FILE`

Validate bundle spec with Workflow Engine API.

```bash
fdpbundle validate bundles/etl-pipeline/bundle.json
```

### `fdpbundle import BUNDLE_FILE`

Import bundle spec into the system (create new version).

```bash
fdpbundle import bundles/etl-pipeline/bundle.json
fdpbundle import bundles/etl-pipeline/bundle.json --no-set-current
```

### `fdpbundle diff BUNDLE_FILE`

Compare bundle with current state.

```bash
fdpbundle diff bundles/etl-pipeline/bundle.json --env dev
fdpbundle diff bundles/etl-pipeline/bundle.json --env prod -v  # Verbose
```

### `fdpbundle apply BUNDLE_FILE`

Apply bundle changes to environment.

```bash
fdpbundle apply bundles/etl-pipeline/bundle.json --env dev
fdpbundle apply bundles/etl-pipeline/bundle.json --env prod --dry-run
```

### `fdpbundle deploy BUNDLE_FILE`

Full deployment flow: validate → import → diff → apply

```bash
fdpbundle deploy bundles/etl-pipeline/bundle.json --env dev
fdpbundle deploy bundles/etl-pipeline/bundle.json --env prod --dry-run
```

## Global Options

| Option | Environment Variable | Description |
|--------|---------------------|-------------|
| `--api-url` | `WORKFLOW_ENGINE_URL` | Workflow Engine API URL |
| `--username` | `SERVICE_ACCOUNT_NAME` | Service account name for Basic Auth |
| `--password` | `SERVICE_ACCOUNT_TOKEN` | Service account token for Basic Auth |
| `-v, --verbose` | - | Show detailed output |
| `--version` | - | Show version |
| `--help` | - | Show help |

## CI/CD Integration

This package is designed for use in GitLab CI/CD. When running `fdpbundle init`, the `.gitlab-ci.yml` file will be automatically created with the following jobs:

- **validate:changed-bundles** - Validate changed bundle files
- **deploy:dev** - Auto deploy to DEV when pushing to `dev` branch
- **deploy:stg** - Auto deploy to Staging when pushing to `stg` branch
- **deploy:prod** - Manual deploy to Production when pushing to `main` branch

### GitLab Variables to configure

| Variable | Protected | Masked |
|----------|-----------|--------|
| `WORKFLOW_ENGINE_URL_DEV` | No | No |
| `WORKFLOW_ENGINE_URL_STG` | Yes | No |
| `WORKFLOW_ENGINE_URL_PROD` | Yes | No |
| `SERVICE_ACCOUNT_NAME_DEV` | No | No |
| `SERVICE_ACCOUNT_NAME_STG` | Yes | No |
| `SERVICE_ACCOUNT_NAME_PROD` | Yes | No |
| `SERVICE_ACCOUNT_TOKEN_DEV` | No | Yes |
| `SERVICE_ACCOUNT_TOKEN_STG` | Yes | Yes |
| `SERVICE_ACCOUNT_TOKEN_PROD` | Yes | Yes |




## Bundle JSON Schema

```json
{
  "bundle": {
    "name": "string (required, unique)",
    "description": "string",
    "owner": "string"
  },
  "workflows": [
    {
      "name": "string (required)",
      "description": "string",
      "schedule_interval": "cron expression or null",
      "tasks": [...]
    }
  ],
  "environments": {
    "dev": { "overrides": {...} },
    "stg": { "overrides": {...} },
    "prod": { "overrides": {...} }
  }
}
```

