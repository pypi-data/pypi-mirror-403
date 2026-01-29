# FDP Bundle CLI

CLI tool để quản lý và deploy workflow bundles cho FDP Workflow Engine.

## Cài đặt

```bash
pip install fdpbundle
```

Hoặc cài đặt từ source:

```bash
git clone https://gitlab.example.com/data-team/fdpbundle.git
cd fdpbundle
pip install -e .
```

## Bắt đầu nhanh

### 1. Khởi tạo project mới

```bash
fdpbundle init my-project
cd my-project
```

Lệnh này sẽ tạo ra cấu trúc:

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

### 2. Cấu hình credentials

```bash
cp .env.example .env
# Chỉnh sửa .env với credentials của bạn
```

Hoặc export environment variables:

```bash
export WORKFLOW_ENGINE_URL=https://airflow.example.com/fdp_tools
export WORKFLOW_ENGINE_SESSION=your-session-cookie
```

### 3. Validate bundle

```bash
fdpbundle validate bundles/example/bundle.json
```

### 4. Deploy

```bash
# Deploy lên DEV
fdpbundle deploy bundles/example/bundle.json --env dev

# Dry run trước khi deploy production
fdpbundle deploy bundles/example/bundle.json --env prod --dry-run

# Deploy production
fdpbundle deploy bundles/example/bundle.json --env prod
```

## Commands

### `fdpbundle init [PROJECT_NAME]`

Khởi tạo project FDP bundles mới với cấu trúc chuẩn.

```bash
fdpbundle init my-project
fdpbundle init  # Sử dụng tên mặc định 'fdp-bundles'
fdpbundle init my-project --force  # Ghi đè nếu đã tồn tại
```

### `fdpbundle validate BUNDLE_FILE`

Validate bundle spec với Workflow Engine API.

```bash
fdpbundle validate bundles/etl-pipeline/bundle.json
```

### `fdpbundle import BUNDLE_FILE`

Import bundle spec vào hệ thống (tạo version mới).

```bash
fdpbundle import bundles/etl-pipeline/bundle.json
fdpbundle import bundles/etl-pipeline/bundle.json --no-set-current
```

### `fdpbundle diff BUNDLE_FILE`

So sánh bundle với trạng thái hiện tại.

```bash
fdpbundle diff bundles/etl-pipeline/bundle.json --env dev
fdpbundle diff bundles/etl-pipeline/bundle.json --env prod -v  # Verbose
```

### `fdpbundle apply BUNDLE_FILE`

Apply bundle changes lên môi trường.

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

| Option | Environment Variable | Mô tả |
|--------|---------------------|-------|
| `--api-url` | `WORKFLOW_ENGINE_URL` | URL của Workflow Engine API |
| `--session` | `WORKFLOW_ENGINE_SESSION` | Airflow session cookie |
| `-v, --verbose` | - | Hiển thị output chi tiết |
| `--version` | - | Hiển thị version |
| `--help` | - | Hiển thị help |

## CI/CD Integration

Package này được thiết kế để sử dụng trong GitLab CI/CD. Khi chạy `fdpbundle init`, file `.gitlab-ci.yml` sẽ được tạo tự động với các jobs:

- **validate:changed-bundles** - Validate các bundle files đã thay đổi
- **deploy:dev** - Auto deploy lên DEV khi push vào `dev` branch
- **deploy:stg** - Auto deploy lên Staging khi push vào `stg` branch
- **deploy:prod** - Manual deploy lên Production khi push vào `main` branch

### GitLab Variables cần cấu hình

| Variable | Protected | Masked |
|----------|-----------|--------|
| `WORKFLOW_ENGINE_URL_DEV` | No | No |
| `WORKFLOW_ENGINE_URL_STG` | Yes | No |
| `WORKFLOW_ENGINE_URL_PROD` | Yes | No |
| `WORKFLOW_ENGINE_SESSION_DEV` | No | Yes |
| `WORKFLOW_ENGINE_SESSION_STG` | Yes | Yes |
| `WORKFLOW_ENGINE_SESSION_PROD` | Yes | Yes |

## Development

### Setup development environment

```bash
git clone https://gitlab.example.com/data-team/fdpbundle.git
cd fdpbundle
pip install -e ".[dev]"
```

### Run tests

```bash
pytest
```

### Code formatting

```bash
black src/
ruff check src/
```

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

## License

MIT License
