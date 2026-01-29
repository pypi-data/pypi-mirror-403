# FDP Bundles

Repository chứa các bundle workflow definitions cho FDP Workflow Engine.

## Cấu trúc thư mục

```
fdp-bundles/
├── bundles/                  # Thư mục chứa các bundle
│   ├── example/              # Mỗi pipeline một folder
│   │   └── bundle.json       # File định nghĩa bundle
│   └── ...
├── .gitlab-ci.yml            # GitLab CI configuration
├── .env.example              # Example environment config
└── README.md
```

## Bắt đầu nhanh

### 1. Cấu hình credentials

```bash
cp .env.example .env
# Chỉnh sửa .env với credentials của bạn
```

### 2. Validate bundle

```bash
fdpbundle validate bundles/example/bundle.json
```

### 3. Deploy lên môi trường

```bash
# Deploy lên DEV
fdpbundle deploy bundles/example/bundle.json --env dev

# Dry run trước khi deploy production
fdpbundle deploy bundles/example/bundle.json --env prod --dry-run
```

## Commands

| Command | Mô tả |
|---------|-------|
| `fdpbundle init [name]` | Khởi tạo project mới |
| `fdpbundle validate <file>` | Validate bundle spec |
| `fdpbundle import <file>` | Import bundle (tạo version mới) |
| `fdpbundle diff <file> --env <env>` | So sánh với trạng thái hiện tại |
| `fdpbundle apply <file> --env <env>` | Apply changes |
| `fdpbundle deploy <file> --env <env>` | Full deploy flow |

## CI/CD

Pipeline tự động chạy khi push code:

- **dev branch** → Auto deploy lên DEV
- **stg branch** → Auto deploy lên Staging  
- **main branch** → Manual deploy lên Production

### GitLab Variables cần cấu hình

| Variable | Mô tả |
|----------|-------|
| `WORKFLOW_ENGINE_URL_DEV` | URL API môi trường DEV |
| `WORKFLOW_ENGINE_URL_STG` | URL API môi trường Staging |
| `WORKFLOW_ENGINE_URL_PROD` | URL API môi trường Production |
| `WORKFLOW_ENGINE_SESSION_DEV` | Session cookie DEV |
| `WORKFLOW_ENGINE_SESSION_STG` | Session cookie Staging |
| `WORKFLOW_ENGINE_SESSION_PROD` | Session cookie Production |

## Bundle Schema

```json
{
  "bundle": {
    "name": "string (required)",
    "description": "string",
    "owner": "string"
  },
  "workflows": [...],
  "environments": {
    "dev": { "overrides": {...} },
    "stg": { "overrides": {...} },
    "prod": { "overrides": {...} }
  }
}
```

## Tạo bundle mới

```bash
# Tạo folder mới
mkdir -p bundles/my-pipeline

# Copy từ example
cp bundles/example/bundle.json bundles/my-pipeline/

# Chỉnh sửa bundle.json
```

## Support

- **CLI Help**: `fdpbundle --help`
- **Command Help**: `fdpbundle <command> --help`
