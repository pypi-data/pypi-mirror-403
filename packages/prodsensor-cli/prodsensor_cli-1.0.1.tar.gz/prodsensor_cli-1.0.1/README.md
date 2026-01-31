# ProdSensor CLI

Command-line tool for running ProdSensor production readiness analysis in CI/CD pipelines.

## Installation

```bash
pip install prodsensor-cli
```

## Quick Start

1. Get an API key from [prodsensor.com/app](https://prodsensor.com/app)
2. Set up authentication:

```bash
# Option 1: Environment variable (recommended for CI/CD)
export PRODSENSOR_API_KEY=ps_live_your_key_here

# Option 2: Save to config file
prodsensor config set-key ps_live_your_key_here
```

3. Run an analysis:

```bash
prodsensor analyze https://github.com/your-org/your-repo
```

## Commands

### analyze

Analyze a repository for production readiness.

```bash
# Basic usage
prodsensor analyze https://github.com/owner/repo

# With JSON output
prodsensor analyze https://github.com/owner/repo --format json

# Start analysis without waiting
prodsensor analyze https://github.com/owner/repo --no-wait

# Custom timeout (10 minutes)
prodsensor analyze https://github.com/owner/repo --timeout 600

# Only fail on blockers (not warnings)
prodsensor analyze https://github.com/owner/repo --fail-on blockers
```

### status

Check the status of an analysis run.

```bash
prodsensor status <run-id>
prodsensor status <run-id> --format json
```

### report

Get the full analysis report.

```bash
prodsensor report <run-id>
prodsensor report <run-id> --format json
prodsensor report <run-id> --format markdown
prodsensor report <run-id> --format json -o report.json
```

### config

Manage CLI configuration.

```bash
# Save API key
prodsensor config set-key ps_live_your_key

# Remove saved API key
prodsensor config clear-key

# Show current configuration
prodsensor config show
```

## Exit Codes

The CLI uses exit codes that work with CI/CD pipelines:

| Code | Meaning |
|------|---------|
| 0 | PRODUCTION_READY |
| 1 | NOT_PRODUCTION_READY |
| 2 | CONDITIONALLY_READY |
| 3 | API/Network error |
| 4 | Authentication error |
| 5 | Timeout |

## CI/CD Integration

### GitHub Actions

```yaml
- name: Run ProdSensor Analysis
  env:
    PRODSENSOR_API_KEY: ${{ secrets.PRODSENSOR_API_KEY }}
  run: |
    pip install prodsensor-cli
    prodsensor analyze https://github.com/${{ github.repository }}
```

Or use the dedicated GitHub Action:

```yaml
- uses: prodsensor/action@v1
  with:
    api-key: ${{ secrets.PRODSENSOR_API_KEY }}
```

### GitLab CI

```yaml
production-readiness:
  script:
    - pip install prodsensor-cli
    - prodsensor analyze https://gitlab.com/$CI_PROJECT_PATH
  variables:
    PRODSENSOR_API_KEY: $PRODSENSOR_API_KEY
```

### Jenkins

```groovy
pipeline {
    environment {
        PRODSENSOR_API_KEY = credentials('prodsensor-api-key')
    }
    stages {
        stage('Production Readiness') {
            steps {
                sh 'pip install prodsensor-cli'
                sh 'prodsensor analyze ${GIT_URL}'
            }
        }
    }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `PRODSENSOR_API_KEY` | API key for authentication |
| `PRODSENSOR_API_URL` | Custom API URL (for self-hosted) |

## Output Formats

### Summary (default)

Human-readable summary with verdict, score, and findings count.

### JSON

Full report data as JSON, suitable for parsing in scripts.

### Markdown

Report formatted as markdown, suitable for PR comments.

## License

MIT
