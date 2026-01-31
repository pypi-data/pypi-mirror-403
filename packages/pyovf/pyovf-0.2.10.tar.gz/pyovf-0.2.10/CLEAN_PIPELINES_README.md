# GitLab Pipeline Cleanup Script

## Overview

`clean_pipelines.sh` is a robust bash script to delete old GitLab pipelines based on age and optional status filters.

## Features

- ✅ Delete pipelines older than N days (default: 90)
- ✅ Filter by pipeline status (e.g., failed, canceled, skipped)
- ✅ Dry-run mode to preview deletions
- ✅ Pagination support for large pipeline lists
- ✅ Connection timeout (10s) to prevent hanging
- ✅ Graceful error handling for API failures
- ✅ Proper cleanup of temporary files

## Prerequisites

- `curl` - HTTP client (already on macOS)
- `jq` OR `python3` - JSON parsing (for output parsing)
- Valid GitLab Personal Access Token with `api` scope

## Setup

### 1. Create a GitLab Personal Access Token

1. Go to GitLab: <https://gitlab.flavio.be/>
2. Settings → Access Tokens → Create new token
3. Name it something like `pipeline-cleanup-token`
4. Select scopes: ✓ `api`
5. Copy the token

### 2. Set Environment Variables

```bash
export GITLAB_URL="https://gitlab.flavio.be"
export PROJECT_ID="16"
export PRIVATE_TOKEN="your-gitlab-token-here"
```

**IMPORTANT:** Never commit your token to git. Use environment variables or `.env` files (excluded from git).

## Usage

### Dry-run (Preview deletions)

```bash
export PRIVATE_TOKEN="your-token"
bash clean_pipelines.sh
```

Output shows what would be deleted without actually deleting anything.

### Actually Delete

```bash
export PRIVATE_TOKEN="your-token"
DRY_RUN=0 bash clean_pipelines.sh
```

### Delete pipelines older than 7 days

```bash
export PRIVATE_TOKEN="your-token"
DAYS=7 DRY_RUN=0 bash clean_pipelines.sh
```

### Delete only failed/canceled pipelines

```bash
export PRIVATE_TOKEN="your-token"
STATUSES="failed,canceled" DRY_RUN=0 bash clean_pipelines.sh
```

### Advanced: Delete failed pipelines older than 30 days with throttling

```bash
export PRIVATE_TOKEN="your-token"
DAYS=30 STATUSES="failed" SLEEP_SEC=0.1 DRY_RUN=0 bash clean_pipelines.sh
```

## Configuration Options

| Variable | Default | Description |
| -------- | ------- | ----------- |
| `GITLAB_URL` | `https://flavio.gitlab.be` | GitLab base URL |
| `PROJECT_ID` | `16` | GitLab project ID |
| `PRIVATE_TOKEN` | *(required)* | GitLab Personal Access Token |
| `DAYS` | `90` | Delete pipelines older than this many days |
| `PER_PAGE` | `100` | Items per API page (20-100) |
| `DRY_RUN` | `1` | 1 = preview only, 0 = actually delete |
| `SLEEP_SEC` | `0` | Delay between deletions (e.g., 0.2 for throttling) |
| `STATUSES` | *(all)* | Filter by status: `failed,canceled,skipped` |

## Example Workflow

```bash
# 1. Set your token
export PRIVATE_TOKEN="glpat-xxxxxxxxxx"

# 2. Preview: see what would be deleted
bash clean_pipelines.sh

# 3. Adjust parameters if needed (DAYS, STATUSES)
DAYS=30 STATUSES="failed" bash clean_pipelines.sh

# 4. Actually delete
DAYS=30 STATUSES="failed" DRY_RUN=0 bash clean_pipelines.sh
```

## Common Issues

### "ERROR: Invalid response from API"

- GitLab server may be down or unreachable
- Check: `curl -I https://flavio.gitlab.be/`
- Wait for server to recover and try again

### "ERROR: HTTP 401"

- Your token is invalid or expired
- Regenerate token in GitLab Settings → Access Tokens

### "ERROR: HTTP 403"

- Your token doesn't have API scope
- Recreate token with ✓ `api` scope selected

### Script hangs

- Timeout is set to 10 seconds per API call
- If hanging longer, interrupt with Ctrl+C
- Check network connectivity

## JSON Parsing

The script supports two JSON parsers:

1. **`jq`** - Preferred (if available)

   ```bash
   brew install jq
   ```

2. **`python3`** - Fallback (usually pre-installed on macOS)

Script automatically picks the available parser.

## Safety Features

- ✓ Dry-run mode by default (`DRY_RUN=1`)
- ✓ Pagination to handle large pipeline lists safely
- ✓ Optional status filtering to target specific pipelines
- ✓ Throttling support (`SLEEP_SEC`) for rate limiting
- ✓ Proper cleanup of temporary files

## Security

⚠️ **Never:**

- Commit tokens to git
- Paste tokens in chat or messages
- Share your `PRIVATE_TOKEN` with others

Use environment variables or `.env` files (added to `.gitignore`):

```bash
# .env (add to .gitignore!)
PRIVATE_TOKEN="your-secret-token"

# Then load and use:
source .env
bash clean_pipelines.sh
```

## License

This script is provided as-is for managing GitLab CI/CD pipelines.
