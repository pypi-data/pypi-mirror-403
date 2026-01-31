# RTL Network Cache - GitLab Package Registry

This guide explains how to use GitLab Package Registry to store and retrieve RTL network cache files for CI/CD pipelines.

## Overview

The RTL network cache files (`network-log-rtl-*.json`) are stored in GitLab's Package Registry as generic packages. This keeps the git repository lean while providing fast, versioned access to cache files in CI pipelines.

## Quick Start

### 1. Generate Cache Locally

```bash
cd react
RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
```

This creates `react/network-testing/logs/network-log-rtl-noi.json`.

### 2. Publish to GitLab Package Registry

```bash
cd react/network-testing/tools

# Set required environment variables
export CI_PROJECT_ID=12345                    # Your GitLab project ID
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxx       # Your GitLab personal access token

# Publish cache file
./publish_cache_to_gitlab.sh noi 1.0.0
```

### 3. Use in GitLab CI

Add to your `.gitlab-ci.yml`:

```yaml
rtl-test:
  before_script:
    - cd react/network-testing/tools
    - ./download_cache_from_gitlab.sh noi latest
    - cd ../../..
  script:
    - cd react
    - BASE_SITE=noi BABEL=1 npm run rtltest
```

## Environment Variables

### For Publishing (Local or CI)

- `CI_PROJECT_ID` - Your GitLab project ID (required)
  - Find it: Project Settings → General
- `GITLAB_TOKEN` - Personal access token with `api` scope (local)
  - Create: User Settings → Access Tokens
- `CI_JOB_TOKEN` - Automatically available in GitLab CI jobs

### For Downloading (CI only)

- `CI_PROJECT_ID` - Automatically set in GitLab CI
- `CI_JOB_TOKEN` - Automatically set in GitLab CI

## Finding Your Project ID

### Method 1: From the Project Page (Easiest)

1. Go to your project on GitLab
2. The Project ID is displayed on the project overview page, right under the project name
3. Or navigate to: **Settings → General** and expand **"General project settings"**
4. The Project ID appears at the top of the settings

### Method 2: Using the API

If your project URL is `https://gitlab.com/group-name/project-name`:

```bash
# Replace slashes with %2F in the path
curl "https://gitlab.com/api/v4/projects/group-name%2Fproject-name" | jq '.id'
```

### Method 3: From Git Remote (if cloned locally)

```bash
# Get the project path from git remote
git remote get-url origin
# Example: git@gitlab.com:lino-framework/lino.git

# Extract and query (replace with your path)
curl "https://gitlab.com/api/v4/projects/lino-framework%2Flino" | jq '.id'
```

## Creating a Personal Access Token

### Step-by-Step Instructions

1. **Navigate to Access Tokens**:
   - Click your **avatar** (top right corner)
   - Select **Edit profile** or **Preferences**
   - In the left sidebar, click **Access Tokens**
   - Or go directly to: `https://gitlab.com/-/profile/personal_access_tokens`

2. **Create New Token**:
   - Click **Add new token**
   - Fill in the form:
     - **Token name**: `RTL Cache Publisher` (or any descriptive name)
     - **Expiration date**: Optional (recommended: 1 year, or leave blank for no expiration)
     - **Scopes**: Check **`api`** ✅
       - This provides full API access including Package Registry
       - Required for both uploading and downloading packages
       - Other scopes like `read_api` are insufficient for publishing

3. **Save Your Token**:
   - Click **Create personal access token**
   - ⚠️ **CRITICAL**: Copy the token immediately - you won't see it again!
   - Token format: `glpat-xxxxxxxxxxxxxxxxxxxx`

### Setting Up the Token

#### For Local Use (Publishing Cache)

```bash
# Set as environment variable (current terminal session only)
export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
export CI_PROJECT_ID=12345

# Test it works
cd react/network-testing/tools
./publish_cache_to_gitlab.sh noi 1.0.0
```

#### For Persistent Use

```bash
# Add to your shell profile
echo 'export GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx' >> ~/.bashrc
echo 'export CI_PROJECT_ID=12345' >> ~/.bashrc
source ~/.bashrc

# Or use a .env file (recommended for security)
cat > react/network-testing/.env << EOF
GITLAB_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
CI_PROJECT_ID=12345
EOF

# Add .env to .gitignore to avoid committing secrets
echo "network-testing/.env" >> react/.gitignore

# Load environment variables when needed
source react/network-testing/.env
```

### For GitLab CI/CD

**No manual token setup needed!** GitLab automatically provides `CI_JOB_TOKEN`:

```yaml
# In .gitlab-ci.yml
rtl-test:
  script:
    - cd react/network-testing/tools
    - ./download_cache_from_gitlab.sh noi latest
    # CI_JOB_TOKEN and CI_PROJECT_ID are automatically available
```

The scripts automatically detect and use `CI_JOB_TOKEN` when running in GitLab CI.

### Token Scopes Explained

For RTL cache publishing, you need:

| Scope | Required | Purpose |
|-------|----------|---------|
| `api` | ✅ Yes | Full API access (read/write Package Registry) |
| `read_api` | ❌ No | Read-only (can't publish packages) |
| `read_repository` | ❌ No | Only for cloning repos |
| `write_repository` | ❌ No | Only for pushing code |

### Security Best Practices

1. **Never commit tokens to git**
   ```bash
   # Always add token files to .gitignore
   echo ".env" >> .gitignore
   echo "*.token" >> .gitignore
   ```

2. **Use environment variables, not hardcoded values**
   ```bash
   # ❌ Bad: hardcoded in scripts
   GITLAB_TOKEN="glpat-xxx" ./publish_cache_to_gitlab.sh
   
   # ✅ Good: from environment
   export GITLAB_TOKEN=glpat-xxx
   ./publish_cache_to_gitlab.sh
   ```

3. **Set expiration dates** (recommended: 1 year)
   - Tokens without expiration are security risks
   - Set calendar reminders to rotate tokens

4. **Use Project Access Tokens for CI** (if available):
   - Navigate to: Project → Settings → Access Tokens
   - More secure than personal tokens (scoped to single project)
   - Requires Maintainer role or higher

5. **Rotate tokens periodically** (every 6-12 months)
   - Create new token
   - Update environment variables
   - Revoke old token

6. **Limit token permissions**
   - Only select `api` scope (don't enable unnecessary scopes)
   - Use separate tokens for different purposes

### Troubleshooting Token Issues

#### "401 Unauthorized"
- **Cause**: Token is invalid, expired, or revoked
- **Solution**: Create a new token and update `GITLAB_TOKEN`

#### "403 Forbidden"  
- **Cause**: Insufficient permissions on the project
- **Solution**: Need at least **Maintainer** role to write packages

#### "Invalid token format"
- **Cause**: Token copied incorrectly (extra spaces, line breaks)
- **Solution**: Ensure token is copied exactly: `glpat-xxxxxxxxxxxxxxxxxxxx`

#### Lost Your Token?
- Tokens cannot be retrieved after creation
- **Solution**: 
  1. Create a new token
  2. Revoke the old one: Access Tokens → Revoke
  3. Update your `GITLAB_TOKEN` environment variable

#### Token Works Locally but Not in CI
- **Cause**: Personal tokens don't work in CI without setup
- **Solution**: Use `CI_JOB_TOKEN` (automatically available) or add token as CI/CD variable:
  1. Settings → CI/CD → Variables
  2. Add variable: `GITLAB_TOKEN`
  3. Keep it masked and protected

## Versioning Strategy

### Semantic Versioning (Recommended)

```bash
# Breaking changes to cache format
./publish_cache_to_gitlab.sh noi 2.0.0

# New features or significant updates
./publish_cache_to_gitlab.sh noi 1.1.0

# Bug fixes or minor updates
./publish_cache_to_gitlab.sh noi 1.0.1
```

### Date-Based Versioning

```bash
# Use date as version
./publish_cache_to_gitlab.sh noi $(date +%Y.%m.%d)
```

### Latest Tag

Always publish with `latest` tag for convenience:

```bash
# Publish both versioned and latest
./publish_cache_to_gitlab.sh noi 1.0.0
./publish_cache_to_gitlab.sh noi latest
```

## Managing Cache Updates

### Manual Update

```bash
# Regenerate cache
cd react
RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest

# Publish new version
cd network-testing/tools
./publish_cache_to_gitlab.sh noi 1.1.0
./publish_cache_to_gitlab.sh noi latest
```

### Automated Update (GitLab CI)

Create a scheduled pipeline in GitLab:

1. Go to: CI/CD → Schedules
2. Create schedule:
   - Description: "Regenerate RTL cache"
   - Interval: Weekly (Sunday 2am)
   - Target branch: `main`
3. Set variable: `REGENERATE_CACHE=true`

Add to `.gitlab-ci.yml`:

```yaml
regenerate-rtl-cache:
  script:
    - cd react/puppeteers/noi && python manage.py prep --noinput && cd ../..
    - cd react && RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
    - cd network-testing/tools
    - ./publish_cache_to_gitlab.sh noi $(date +%Y.%m.%d)
    - ./publish_cache_to_gitlab.sh noi latest
  only:
    variables:
      - $REGENERATE_CACHE == "true"
```

## Viewing Published Packages

1. Navigate to: Packages & Registries → Package Registry
2. Find package: `rtl-network-cache`
3. View versions and download URLs

## Troubleshooting

### 401 Unauthorized

- Check `GITLAB_TOKEN` has `api` scope
- Verify token hasn't expired
- Ensure `CI_PROJECT_ID` is correct

### 404 Not Found

- Cache file hasn't been published yet
- Wrong project ID
- Wrong version number

### Cache Miss Warnings

The cache file might be outdated. Regenerate and republish:

```bash
cd react
RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
cd network-testing/tools
./publish_cache_to_gitlab.sh noi latest
```

## Multiple Sites

Publish cache for each site separately:

```bash
# Noi site
RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
./publish_cache_to_gitlab.sh noi latest

# Avanti site
RTL_LOG_NETWORK=1 BASE_SITE=avanti BABEL=1 npm run rtltest
./publish_cache_to_gitlab.sh avanti latest

# Welfare site
RTL_LOG_NETWORK=1 BASE_SITE=welfare BABEL=1 npm run rtltest
./publish_cache_to_gitlab.sh welfare latest
```

## Cost Considerations

GitLab Package Registry:
- **Free tier**: 10 GB storage
- **Premium**: 100 GB storage
- Each cache file: ~1-5 MB (depends on site)

You can safely store 2000-10000 cache files on free tier.

## Security Notes

1. Cache files may contain demo data - ensure it's not sensitive
2. Use project access tokens instead of personal tokens in CI
3. Tokens should have minimal required scopes (`api` only)
4. Rotate tokens periodically

## API Reference

### Publish

```bash
curl --header "PRIVATE-TOKEN: <token>" \
     --upload-file network-log-rtl-noi.json \
     "https://gitlab.com/api/v4/projects/<project_id>/packages/generic/rtl-network-cache/<version>/network-log-rtl-noi.json"
```

### Download

```bash
curl --header "PRIVATE-TOKEN: <token>" \
     "https://gitlab.com/api/v4/projects/<project_id>/packages/generic/rtl-network-cache/<version>/network-log-rtl-noi.json" \
     -o network-log-rtl-noi.json
```

### List Versions

```bash
curl --header "PRIVATE-TOKEN: <token>" \
     "https://gitlab.com/api/v4/projects/<project_id>/packages?package_name=rtl-network-cache"
```
