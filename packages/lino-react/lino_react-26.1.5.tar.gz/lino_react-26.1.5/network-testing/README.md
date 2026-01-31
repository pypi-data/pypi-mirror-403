# Network Testing - RTL Request Caching System

This directory contains tools and cached responses for React Testing Library (RTL) tests using MSW (Mock Service Worker).

## Overview

RTL tests use MSW to intercept and mock network requests. This system supports two modes:

1. **Live Server Mode** (`RTL_LOG_NETWORK=1`) - Proxy requests to Django server and cache responses
2. **Cached Mode** (default) - Use previously cached responses for offline testing

## Quick Start

### First-time setup (Live server mode)

Capture responses from a live Django server:

```bash
RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
```

### Subsequent runs (Cached mode)

Run tests using cached responses (no server needed):

```bash
BASE_SITE=noi BABEL=1 npm run rtltest
```

## Directory Structure

```
network-testing/
├── README.md                              # This file
├── logs/                                  # Cached network responses
│   ├── README.md                          # Logs directory documentation
│   ├── network-log-rtl-noi.json          # Noi site cache
│   ├── network-log-rtl-avanti.json       # Avanti site cache
│   └── network-log-rtl-*.json            # Other site caches
├── tools/                                 # Utility scripts
│   ├── publish_cache_to_gitlab.sh        # Publish cache to GitLab registry
│   └── download_cache_from_gitlab.sh     # Download cache from GitLab registry
└── docs/                                  # Documentation
    ├── GITLAB_PACKAGE_REGISTRY.md        # GitLab cache distribution guide
    └── gitlab-ci-example.yml             # Example CI/CD configuration
```

## How It Works

### Live Server Mode (`RTL_LOG_NETWORK=1`)

1. Django server starts on port 3001
2. RTL tests run with MSW enabled
3. When app makes request (e.g., `fetch('/api/user')`):
   - MSW intercepts the request
   - Forwards request to `http://127.0.0.1:3001/api/user`
   - Receives real response from Django
   - Caches response to `logs/network-log-rtl-{site}.json`
   - Returns response to app

### Cached Mode (default)

1. No Django server starts
2. RTL tests run with MSW enabled
3. When app makes request (e.g., `fetch('/api/user')`):
   - MSW intercepts the request
   - Looks up request in cached log file
   - Returns cached response to app
   - If no cache found, returns empty response with warning

## Tools

### Cache Distribution (GitLab)

For team environments, distribute cache files via GitLab Package Registry:

```bash
# Publish cache to GitLab
./tools/publish_cache_to_gitlab.sh noi

# Download cache from GitLab
./tools/download_cache_from_gitlab.sh noi
```

See `docs/GITLAB_PACKAGE_REGISTRY.md` for setup instructions.

## Best Practices

1. **Commit cache files** to version control - enables offline testing for all developers
2. **Regenerate after API changes** - Run with `RTL_LOG_NETWORK=1` when backend responses change
3. **Use different sites** for different scenarios:
   ```bash
   RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
   RTL_LOG_NETWORK=1 BASE_SITE=avanti BABEL=1 npm run rtltest
   ```
4. **Verify cache periodically** - Occasionally run live mode to ensure cache is current

## Troubleshooting

### "Cache miss" warnings

If you see `⚠️ Cache miss: GET /api/user`, run tests with `RTL_LOG_NETWORK=1` to capture that request.

### Server fails to start

Ensure the demo site is prepared:
```bash
python puppeteers/noi/manage.py prep --noinput
```

### Port already in use

The RTL server uses port 3001. If it's in use:
```bash
lsof -ti:3001 | xargs kill -9
```

## See Also

- `../../RTL_NETWORK_TESTING.md` - Complete RTL network testing documentation
- `../../lino_react/react/testSetup/RTL_AUTH_GUIDE.md` - Authentication guide
- `../../lino_react/react/testSetup/mswHandlers.ts` - MSW handler implementation
- `../../lino_react/react/testSetup/rtlTestHelpers.ts` - RTL test utilities
- [MSW Documentation](https://mswjs.io/)
