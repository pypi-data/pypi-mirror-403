#!/bin/bash
# Publish RTL network cache to GitLab Package Registry
#
# Usage:
#   ./publish_cache_to_gitlab.sh <site_name> <version>
#
# Environment variables required:
#   CI_PROJECT_ID - GitLab project ID
#   CI_JOB_TOKEN or GITLAB_TOKEN - Authentication token
#
# Example:
#   CI_PROJECT_ID=12345 GITLAB_TOKEN=glpat-xxx ./publish_cache_to_gitlab.sh noi 1.0.0

set -e

SITE=${1:-noi}
VERSION=${2:-latest}
CACHE_FILE="../logs/network-log-rtl-${SITE}.ndjson"
# PROJECT ID LINK: https://gitlab.com/lino-framework/react/edit
CI_PROJECT_ID="26156612"

# Check if cache file exists
if [ ! -f "$CACHE_FILE" ]; then
    echo "❌ Cache file not found: $CACHE_FILE"
    echo "   Run: RTL_LOG_NETWORK=1 BASE_SITE=${SITE} BABEL=1 npm run test:jsdom"
    exit 1
fi

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

echo "📦 Publishing RTL cache to GitLab Package Registry..."
echo "   Site: ${SITE}"
echo "   Version: ${VERSION}"
echo "   File: ${CACHE_FILE}"
echo "   Size: $(du -h "$CACHE_FILE" | cut -f1)"

# Upload to GitLab Package Registry
curl --fail --header "PRIVATE-TOKEN: ${TOKEN}" \
     --upload-file "${CACHE_FILE}" \
     "${GITLAB_URL}/projects/${CI_PROJECT_ID}/packages/generic/${PACKAGE_NAME}/${VERSION}/${FILE_NAME}"

if [ $? -eq 0 ]; then
    echo "✅ Successfully published cache file"
    echo "   URL: ${GITLAB_URL}/projects/${CI_PROJECT_ID}/packages/generic/${PACKAGE_NAME}/${VERSION}/${FILE_NAME}"
else
    echo "❌ Failed to publish cache file"
    exit 1
fi
