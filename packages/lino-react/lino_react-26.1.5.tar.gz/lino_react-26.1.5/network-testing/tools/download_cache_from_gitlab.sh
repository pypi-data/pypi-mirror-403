#!/bin/bash
# Download RTL network cache from GitLab Package Registry
#
# Usage:
#   ./download_cache_from_gitlab.sh <site_name> <version>
#
# Environment variables required:
#   CI_PROJECT_ID - GitLab project ID
#   CI_JOB_TOKEN or GITLAB_TOKEN - Authentication token
#
# Example:
#   CI_PROJECT_ID=12345 CI_JOB_TOKEN=xxx ./download_cache_from_gitlab.sh noi latest

set -e

SITE=${1:-noi}
VERSION=${2:-latest}
CACHE_DIR="../logs"
CACHE_FILE="${CACHE_DIR}/network-log-rtl-${SITE}.ndjson"

# Create logs directory if it doesn't exist
mkdir -p "$CACHE_DIR"

# Check required environment variables
if [ -z "$CI_PROJECT_ID" ]; then
    echo "❌ CI_PROJECT_ID environment variable is required"
    exit 1
fi

# Use CI_JOB_TOKEN if available (in CI), otherwise use GITLAB_TOKEN
TOKEN=${CI_JOB_TOKEN:-$GITLAB_TOKEN}
if [ -z "$TOKEN" ]; then
    echo "❌ Either CI_JOB_TOKEN or GITLAB_TOKEN environment variable is required"
    exit 1
fi

# GitLab instance URL (adjust if using self-hosted)
GITLAB_URL=${CI_API_V4_URL:-"https://gitlab.com/api/v4"}

# Package details
PACKAGE_NAME="rtl-network-cache"
FILE_NAME="network-log-rtl-${SITE}.ndjson"

echo "📥 Downloading RTL cache from GitLab Package Registry..."
echo "   Site: ${SITE}"
echo "   Version: ${VERSION}"
echo "   Target: ${CACHE_FILE}"

# Download from GitLab Package Registry
curl --fail --header "PRIVATE-TOKEN: ${TOKEN}" \
     --output "${CACHE_FILE}" \
     "${GITLAB_URL}/projects/${CI_PROJECT_ID}/packages/generic/${PACKAGE_NAME}/${VERSION}/${FILE_NAME}"

if [ $? -eq 0 ]; then
    echo "✅ Successfully downloaded cache file"
    echo "   Size: $(du -h "$CACHE_FILE" | cut -f1)"
    echo "   Entries: $(wc -l < "$CACHE_FILE" 2>/dev/null || echo "unknown")"
else
    echo "❌ Failed to download cache file"
    echo "   The cache may not exist yet. Generate it with:"
    echo "   RTL_LOG_NETWORK=1 BASE_SITE=${SITE} BABEL=1 npm run test:jsdom"
    exit 1
fi
