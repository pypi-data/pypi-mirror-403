# Network Logs Directory

This directory stores cached network request/response logs from RTL (React Testing Library) tests using MSW (Mock Service Worker).

## File Format

Each site has its own log file:
- `network-log-rtl-noi.json` - Noi site RTL test requests
- `network-log-rtl-avanti.json` - Avanti site RTL test requests
- `network-log-rtl-*.json` - Other site RTL test requests

**Note:** Each test run with `RTL_LOG_NETWORK=1` overwrites the previous log for that site.

## How to Generate

Run RTL tests with live server mode to capture network traffic:

```bash
RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
```

This will:
- Start Django server on port 3001
- Run RTL tests with MSW intercepting requests
- Proxy requests to the live server
- Cache responses in `network-log-rtl-{site}.json`

## How to Use

### Run RTL Tests with Cached Responses (Offline)

Once you've generated the cache, run tests without a server:

```bash
BASE_SITE=noi BABEL=1 npm run rtltest
```

MSW will load cached responses from the log file, allowing tests to run offline.

## File Structure

Each RTL log file contains:

```json
{
  "site": "noi",
  "timestamp": "2025-12-09T14:30:45.123Z",
  "requests": [
    {
      "timestamp": "2025-12-09T14:30:46.123Z",
      "request": {
        "method": "GET",
        "url": "http://127.0.0.1:3001/api/...",
        "headers": {...},
        "body": null
      },
      "response": {
        "status": 200,
        "statusText": "OK",
        "headers": {...},
        "body": {...}
      }
    }
  ]
}
```

## Typical File Sizes

- Small test suite: ~100 KB - 1 MB
- Medium test suite: 1 MB - 5 MB
- Large test suite: 5 MB - 20 MB

## Maintenance

These files are generated automatically and can be safely deleted. They will be recreated on the next test run with `RTL_LOG_NETWORK=1`.

To clean up old logs:
```bash
rm network-testing/logs/network-log-rtl-*.json
```

## Version Control

These cache files should be committed to version control so other developers can run RTL tests offline without needing to start a Django server.

## See Also

- `../../RTL_NETWORK_TESTING.md` - Complete RTL network testing documentation
- `../../lino_react/react/testSetup/RTL_AUTH_GUIDE.md` - Authentication guide
- `../../lino_react/react/testSetup/mswHandlers.ts` - MSW implementation
