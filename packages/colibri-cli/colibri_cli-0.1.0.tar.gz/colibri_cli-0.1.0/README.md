# Colibri CLI

Upload dbt artifacts to Colibri Cloud for automatic lineage analysis.

## Overview

This CLI is designed to integrate your CI/CD pipeline with Colibri Cloud, syncing your dbt `manifest.json` and `catalog.json` files.
The CLI automatically includes git commit information when available, making it easy to track which code version generated each upload.

## Installation

```bash
pip install colibri-cli
```

## Configuration

Set the following environment variables in your CI/CD environment:

```bash
COLIBRI_API_URL=https://api.colibri-data.com
COLIBRI_API_KEY=your-api-key-here
COLIBRI_PROJECT_ID=your-project-id
```


## Usage

### Upload Artifacts

After running your dbt project, upload the artifacts:

```bash
# Upload from default ./target directory
colibri-pro upload

# Upload from custom directory
colibri-pro upload --target-dir path/to/target

## CI/CD Integration

### GitHub Actions

```yaml
name: Upload dbt Lineage

on:
  push:
    branches: [main]
  workflow_dispatch:

jobs:
  upload-lineage:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Fetch full history for git info

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install dbt-core dbt-duckdb  # or your adapter
          pip install colibri-cli

      - name: Run dbt
        run: |
          dbt deps
          dbt build
          dbt docs generate
        env:
          DBT_PROFILES_DIR: .

      - name: Upload to Colibri Pro
        run: colibri-pro upload
        env:
          COLIBRI_API_URL: ${{ secrets.COLIBRI_API_URL }}
          COLIBRI_API_KEY: ${{ secrets.COLIBRI_API_KEY }}
          COLIBRI_PROJECT_ID: ${{ secrets.COLIBRI_PROJECT_ID }}
```

### GitLab CI

```yaml
upload-lineage:
  stage: deploy
  image: python:3.11
  script:
    - pip install dbt-core dbt-duckdb colibri-cli
    - dbt deps && dbt build && dbt docs generate
    - colibri-pro upload
  variables:
    COLIBRI_API_URL: $COLIBRI_API_URL
    COLIBRI_API_KEY: $COLIBRI_API_KEY
    COLIBRI_PROJECT_ID: $COLIBRI_PROJECT_ID
  only:
    - main
```

### Metadata Included

The CLI automatically includes:
- `git_commit` - Current git commit hash (if available)
- `git_branch` - Current git branch (if available)
- `colibri_cli_version` - CLI version used for upload
- `uploaded_at` - ISO 8601 timestamp of uploads