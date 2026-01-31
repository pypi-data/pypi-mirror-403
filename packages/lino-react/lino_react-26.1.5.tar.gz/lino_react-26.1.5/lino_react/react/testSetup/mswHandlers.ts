/**
 * MSW (Mock Service Worker) handlers for RTL tests
 * 
 * This module provides two modes:
 * 1. RTL_LOG_NETWORK=1: Proxy requests to live Django server and cache responses
 * 2. RTL_LOG_NETWORK not set: Load cached responses from network-testing/logs
 * 
 * AUTHENTICATION HANDLING:
 * - Live mode: Session cookies from login are automatically captured and stored
 * - Cached mode: Session cookies are replayed from cached responses
 * - Credentials: Tests use demo fixtures (username: 'robin', password: '1234')
 * - The Django server must be prepared with `manage.py prep --noinput` for login to work
 */

// Import from main msw package (BroadcastChannel polyfill provided in setupTests.ts)
import { http, HttpResponse, passthrough } from 'msw';
import * as fs from 'fs';
import * as path from 'path';
import * as httpModule from 'http';

const NETWORK_LOG_DIR = path.join(__dirname, '../../../network-testing/logs');
const RTL_LOG_NETWORK = process.env.RTL_LOG_NETWORK === '1';
const BASE_SITE = process.env.BASE_SITE || 'noi';
const SERVER_URL = process.env.RTL_SERVER_URL || 'http://127.0.0.1:3001';

/**
 * Map user credentials to user_type
 * This allows us to determine user_type from session cookies in cached mode
 * These mappings come from demo fixtures created by manage.py prep
 */
const USER_CREDENTIAL_TO_TYPE: Record<string, string> = {
    'robin': '900',      // Administrator
    'romain': '900',     // Administrator  
    'rolf': '900',       // Administrator
    'jean': '400',       // Developer
    'luc': '400',        // Developer
    'mathieu': '200',    // Contributor
    'marc': '100',       // Customer
    'anonymous': '000',  // Anonymous/not logged in
};

/**
 * Default user type for anonymous (not logged in) users
 */
const ANONYMOUS_USER_TYPE = '000';

/**
 * Track pending MSW requests
 * This is used by waitForNetworkIdle to know when all requests have completed
 */
let pendingMSWRequests = 0;

export function getPendingRequestCount(): number {
    return pendingMSWRequests;
}

function incrementPendingRequests() {
    pendingMSWRequests++;
}

function decrementPendingRequests() {
    pendingMSWRequests--;
}

interface NetworkLogEntry {
    cacheKey: string;  // Pre-computed cache key for fast lookup
    timestamp: string;
    request: {
        method: string;
        url: string;
        headers?: Record<string, string>;
        body?: any;
    };
    response: {
        status: number;
        statusText?: string;
        headers?: Record<string, string>;
        body?: any;
    };
}

interface NetworkLog {
    site: string;
    timestamp: string;
    requests?: NetworkLogEntry[];  // Optional - only used during recording
}

class RTLNetworkLogger {
    private log: NetworkLog;
    private logPath: string;
    private cacheExists: boolean;  // Whether cache file exists for on-demand reading
    private currentUserType: string | undefined;  // Track current user_type during recording
    private sessionToUserType: Map<string, string>;  // Map session IDs to user_type
    public loadingPromise: Promise<void> | null;  // For compatibility with setupTests.ts

    constructor(siteName: string) {
        this.logPath = path.join(NETWORK_LOG_DIR, `network-log-rtl-${siteName}.ndjson`);
        this.cacheExists = false;
        this.sessionToUserType = new Map();
        this.loadingPromise = null;
        
        if (RTL_LOG_NETWORK) {
            // Initialize new log for recording
            this.log = {
                site: siteName,
                timestamp: new Date().toISOString()
            };
            
            // Note: Cache file is cleared once in setupJEST.mjs, not here
            // This allows all test files in the same run to append to the cache
            console.log(`📝 RTL Network logging enabled - will save to: ${this.logPath}`);
        } else {
            // Check if cache file exists (but don't load it yet - on-demand reading)
            this.cacheExists = fs.existsSync(this.logPath);
            if (this.cacheExists) {
                console.log(`📦 NDJSON cache ready for on-demand reading: ${this.logPath}`);
            } else {
                console.warn(`⚠️  RTL network log not found: ${this.logPath}`);
                console.warn(`   Run tests with RTL_LOG_NETWORK=1 to generate it`);
            }
            // Resolve immediately - no loading needed
            this.loadingPromise = Promise.resolve();
        }
    }

    private initializeEmptyLog() {
        this.log = {
            site: BASE_SITE,
            timestamp: new Date().toISOString()
        };
    }

    private makeKey(method: string, url: string, requestBody?: any, userType?: string): string {
        // Normalize URL to handle query parameter variations
        const urlObj = new URL(url, 'http://dummy');
        
        // Filter out 'rp' and 'v' parameters from search
        const searchParams = new URLSearchParams(urlObj.search);
        searchParams.delete('rp');
        searchParams.delete('v');
        
        // For /user/settings, api/main_html, and dashboard/*, add user_type as search parameter for cache key
        if (userType && (
            urlObj.pathname.includes('/user/settings') ||
            urlObj.pathname.includes('/api/main_html') ||
            urlObj.pathname.includes('/dashboard/')
        )) {
            searchParams.set('user_type', userType);
        }
        
        let keyParts = urlObj.pathname;
        
        // Add filtered search params if any remain (sorted for consistency)
        const filteredSearch = searchParams.toString();
        if (filteredSearch) {
            // Sort parameters alphabetically for consistent cache keys
            const sortedParams = Array.from(searchParams.entries())
                .sort(([a], [b]) => a.localeCompare(b))
                .map(([key, value]) => `${key}=${value}`)
                .join('&');
            keyParts += '?' + sortedParams;
        }
        
        // For POST/PUT/PATCH, include body in key (excluding 'rp' and 'v')
        const mutatingMethods = ['POST', 'PUT', 'PATCH'];
        if (mutatingMethods.includes(method.toUpperCase()) && requestBody) {
            let bodyForKey = requestBody;
            
            // If body is an object, filter out 'rp' and 'v'
            if (typeof requestBody === 'object' && requestBody !== null) {
                bodyForKey = { ...requestBody };
                delete bodyForKey.rp;
                delete bodyForKey.v;
                
                // Sort object keys for consistent serialization
                const sortedBody = {};
                Object.keys(bodyForKey).sort().forEach(key => {
                    sortedBody[key] = bodyForKey[key];
                });
                bodyForKey = sortedBody;
            } else if (typeof requestBody === 'string') {
                // If body is URL-encoded string, parse and filter, then sort
                try {
                    const bodyParams = new URLSearchParams(requestBody);
                    bodyParams.delete('rp');
                    bodyParams.delete('v');
                    
                    // Sort parameters alphabetically for consistency
                    const sortedParams = Array.from(bodyParams.entries())
                        .sort(([a], [b]) => a.localeCompare(b))
                        .map(([key, value]) => `${key}=${value}`)
                        .join('&');
                    bodyForKey = sortedParams;
                } catch {
                    // If not parseable as URLSearchParams, use as-is
                    bodyForKey = requestBody;
                }
            }
            
            // Append body to key
            const bodyStr = typeof bodyForKey === 'object' 
                ? JSON.stringify(bodyForKey) 
                : bodyForKey;
            if (bodyStr) {
                keyParts += '|body:' + bodyStr;
            }
        }
        
        return `${method.toUpperCase()}:${keyParts}`;
    }

    async logRequest(method: string, url: string, requestHeaders: Headers, requestBody: any, response: Response) {
        const responseBody = await this.extractBody(response.clone());
        
        // Compute cache key once during recording
        const cacheKey = this.makeKey(method, url, requestBody, undefined);
        
        const entry: NetworkLogEntry = {
            cacheKey,
            timestamp: new Date().toISOString(),
            request: {
                method: method.toUpperCase(),
                url: url,
                headers: this.headersToObject(requestHeaders),
                body: requestBody
            },
            response: {
                status: response.status,
                statusText: response.statusText,
                headers: this.headersToObject(response.headers),
                body: responseBody
            }
        };

        this.logRequestNDJSON(entry);
    }

    async logRequestDirect(
        method: string,
        url: string,
        requestHeaders: Headers,
        requestBody: any,
        response: {
            status: number;
            statusText: string;
            headers: Record<string, string>;
            body: string;
        }
    ) {
        // Parse body if it's JSON
        let responseBody: any = response.body;
        const contentType = response.headers['content-type'] || '';
        if (contentType.includes('application/json')) {
            try {
                responseBody = JSON.parse(response.body);
            } catch {
                // Keep as string if parsing fails
            }
        }
        
        // Track current user_type from /user/settings responses
        const urlObj = new URL(url, 'http://dummy');
        if (urlObj.pathname.includes('/user/settings') && responseBody && typeof responseBody === 'object' && responseBody.user_type) {
            this.currentUserType = responseBody.user_type;
            
            // Also track session-to-usertype mapping
            const cookieHeader = requestHeaders.get('cookie');
            if (cookieHeader) {
                const sessionMatch = cookieHeader.match(/sessionid=([^;]+)/);
                if (sessionMatch && sessionMatch[1]) {
                    this.sessionToUserType.set(sessionMatch[1], responseBody.user_type);
                }
            }
        }
        
        // For /user/settings, /api/main_html, and /dashboard/*, append user_type to URL for cache key differentiation
        let modifiedUrl = url;
        let userTypeForUrl: string | undefined;
        
        if (urlObj.pathname.includes('/user/settings') && responseBody && typeof responseBody === 'object' && responseBody.user_type) {
            userTypeForUrl = responseBody.user_type;
        } else if (urlObj.pathname.includes('/api/main_html') || urlObj.pathname.includes('/dashboard/')) {
            // Try to get user_type from session cookie
            const cookieHeader = requestHeaders.get('cookie');
            if (cookieHeader) {
                const sessionMatch = cookieHeader.match(/sessionid=([^;]+)/);
                if (sessionMatch && sessionMatch[1]) {
                    userTypeForUrl = this.sessionToUserType.get(sessionMatch[1]);
                }
            }
            // Fallback to tracked current user_type
            if (!userTypeForUrl) {
                userTypeForUrl = this.currentUserType;
            }
        }
        
        if (userTypeForUrl) {
            const urlParams = new URLSearchParams(urlObj.search);
            urlParams.set('user_type', userTypeForUrl);
            modifiedUrl = urlObj.pathname + '?' + urlParams.toString();
            // Convert back to full URL if original was full URL
            if (url.startsWith('http')) {
                modifiedUrl = urlObj.origin + modifiedUrl;
            }
        }

        // Compute cache key using the determined userType
        const cacheKey = this.makeKey(method, modifiedUrl, requestBody, userTypeForUrl);

        const entry: NetworkLogEntry = {
            cacheKey,
            timestamp: new Date().toISOString(),
            request: {
                method: method.toUpperCase(),
                url: modifiedUrl,
                headers: this.headersToObject(requestHeaders),
                body: requestBody
            },
            response: {
                status: response.status,
                statusText: response.statusText,
                headers: response.headers,
                body: responseBody
            }
        };

        this.logRequestNDJSON(entry);
    }

    private headersToObject(headers: Headers): Record<string, string> {
        const obj: Record<string, string> = {};
        headers.forEach((value, key) => {
            obj[key] = value;
        });
        return obj;
    }

    private async extractBody(response: Response): Promise<any> {
        const contentType = response.headers.get('content-type') || '';
        
        if (contentType.includes('application/json')) {
            try {
                return await response.json();
            } catch {
                return await response.text();
            }
        } else {
            return await response.text();
        }
    }

    private saveLog() {
        try {
            // Ensure directory exists
            if (!fs.existsSync(NETWORK_LOG_DIR)) {
                fs.mkdirSync(NETWORK_LOG_DIR, { recursive: true });
            }
            
            // For NDJSON, we don't need to save anything here
            // Entries are appended immediately in logRequestNDJSON
        } catch (error) {
            console.error(`❌ Failed to save RTL network log:`, error);
        }
    }
    
    private logRequestNDJSON(entry: NetworkLogEntry) {
        try {
            // Ensure directory exists
            if (!fs.existsSync(NETWORK_LOG_DIR)) {
                fs.mkdirSync(NETWORK_LOG_DIR, { recursive: true });
            }
            
            // Append entry as single JSON line
            const line = JSON.stringify(entry) + '\n';
            fs.appendFileSync(this.logPath, line, 'utf8');
        } catch (error) {
            console.error(`❌ Failed to append to RTL network log:`, error);
        }
    }

    findCachedResponse(method: string, url: string, requestBody?: any, userType?: string): NetworkLogEntry | null {
        if (!this.cacheExists) {
            return null;
        }

        const targetKey = this.makeKey(method, url, requestBody, userType);
        
        try {
            // Stream file and check pre-computed cacheKey for fast matching
            const fd = fs.openSync(this.logPath, 'r');
            const buffer = Buffer.allocUnsafe(65536); // 64KB buffer
            let leftover = '';
            let bytesRead;
            let position = 0;
            
            while ((bytesRead = fs.readSync(fd, buffer, 0, buffer.length, position)) > 0) {
                position += bytesRead;
                const chunk = leftover + buffer.toString('utf8', 0, bytesRead);
                const lines = chunk.split('\n');
                
                // Keep last incomplete line for next iteration
                leftover = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        // Check for pre-computed cacheKey in JSON string
                        // String search is orders of magnitude faster than JSON parse
                        if (line.includes(`"cacheKey":"${targetKey}"`)) {
                            const entry: NetworkLogEntry = JSON.parse(line);
                            fs.closeSync(fd);
                            return entry; // Found match!
                        }
                    } catch (parseError) {
                        // Skip malformed lines
                        continue;
                    }
                }
            }
            
            // Process leftover (last line)
            if (leftover.trim()) {
                try {
                    if (leftover.includes(`"cacheKey":"${targetKey}"`)) {
                        const entry: NetworkLogEntry = JSON.parse(leftover);
                        fs.closeSync(fd);
                        return entry;
                    }
                } catch {
                    // Ignore
                }
            }
            
            fs.closeSync(fd);
            return null; // No match found
        } catch (error) {
            console.error(`❌ Error reading cache file:`, error);
            return null;
        }
    }
    
    /**
     * Extract username from session cookie by looking at login requests
     * @param sessionId The session ID from the cookie
     * @returns username if found, undefined otherwise
     */
    getUsernameFromSession(sessionId: string): string | undefined {
        if (!this.cacheExists) {
            return undefined;
        }

        try {
            // Stream file to find login request that created this session
            const fd = fs.openSync(this.logPath, 'r');
            const buffer = Buffer.allocUnsafe(65536);
            let leftover = '';
            let bytesRead;
            let position = 0;
            
            while ((bytesRead = fs.readSync(fd, buffer, 0, buffer.length, position)) > 0) {
                position += bytesRead;
                const chunk = leftover + buffer.toString('utf8', 0, bytesRead);
                const lines = chunk.split('\n');
                leftover = lines.pop() || '';
                
                for (const line of lines) {
                    if (!line.trim()) continue;
                    
                    try {
                        const entry: NetworkLogEntry = JSON.parse(line);
                        
                        // Look for sign_in POST requests
                        if (entry.request.method === 'POST' && 
                            entry.request.url.includes('/api/about/About') &&
                            entry.request.body && 
                            typeof entry.request.body === 'string' &&
                            entry.request.body.includes('an=sign_in')) {
                            
                            // Check if response set this session ID
                            const setCookie = entry.response.headers?.['set-cookie'];
                            if (setCookie && setCookie.includes(`sessionid=${sessionId}`)) {
                                // Extract username from request body
                                const match = entry.request.body.match(/username=([^&]+)/);
                                if (match && match[1]) {
                                    fs.closeSync(fd);
                                    return decodeURIComponent(match[1]);
                                }
                            }
                        }
                    } catch {
                        continue;
                    }
                }
            }
            
            fs.closeSync(fd);
        } catch (error) {
            console.error(`❌ Error reading cache for username lookup:`, error);
        }
        
        return undefined;
    }
}

// Create logger instance
const logger = new RTLNetworkLogger(BASE_SITE);

/**
 * Create MSW handlers for all HTTP requests
 */
export const handlers = RTL_LOG_NETWORK ? [
    http.all(/.*/, async ({ request }) => {
        const method = request.method;
        const url = request.url;
        
        // CRITICAL: Check if this is a direct request to port 3001
        // These are proxy requests we're making with fetch, and MSW intercepts them
        // We must passthrough immediately to prevent infinite recursion
        const urlObj = new URL(url);
        if (urlObj.port === '3001') {
            // Don't log - this creates too much noise
            return passthrough();
        }
        
        incrementPendingRequests();
        try {
            // Extract request body if present
            let requestBody = null;
            let bodyForProxy = null;
            
            // Check if this is a request type that might have a body
            if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
                try {
                    // Clone the request to read the body without consuming the original
                    const cloned = request.clone();
                    const contentType = request.headers.get('content-type') || '';
                    
                    if (contentType.includes('application/json')) {
                        requestBody = await cloned.json();
                        bodyForProxy = JSON.stringify(requestBody);
                    } else if (contentType.includes('application/x-www-form-urlencoded')) {
                        const formData = await cloned.text();
                        requestBody = formData;
                        bodyForProxy = formData;
                    } else {
                        // Try to read as text for other content types
                        const text = await cloned.text();
                        if (text) {
                            requestBody = text;
                            bodyForProxy = text;
                        }
                    }
                } catch (error) {
                    // Body not readable or already consumed - this is OK for some requests
                    console.log(`ℹ️  Could not extract request body (may be empty):`, error instanceof Error ? error.message : error);
                }
            }

            // Mode 1: Proxy to live server and log response
            
            try {
                // Convert relative URL to absolute for the Django server
                const urlObj = new URL(url, 'http://localhost');
                const targetUrl = `${SERVER_URL}${urlObj.pathname}${urlObj.search}${urlObj.hash}`;

                // Prepare headers for proxy request
                const proxyHeaders: Record<string, string> = {};
                request.headers.forEach((value, key) => {
                    // Skip host header to avoid conflicts
                    if (key.toLowerCase() !== 'host') {
                        proxyHeaders[key] = value;
                    }
                });

                // Make request using Node's http module
                // This completely bypasses jsdom/whatwg-fetch and their CORS restrictions
                // MSW won't intercept this because of our port=3001 check at the top
                
                const parsedUrl = new URL(targetUrl);
                const port = parseInt(parsedUrl.port || '80', 10);
                
                const response = await new Promise<{
                    status: number;
                    statusText: string;
                    headers: Record<string, string>;
                    body: string;
                }>((resolve, reject) => {
                    const options: httpModule.RequestOptions = {
                        hostname: parsedUrl.hostname,
                        port: port,
                        path: parsedUrl.pathname + parsedUrl.search,
                        method,
                        headers: proxyHeaders,
                    };

                    // Add Content-Length header if we have a body
                    if (bodyForProxy) {
                        const bodyLength = Buffer.byteLength(bodyForProxy, 'utf8');
                        options.headers = {
                            ...proxyHeaders,
                            'content-length': bodyLength.toString()
                        };
                    }

                    const req = httpModule.request(options, (res) => {
                        let data = '';
                        res.on('data', (chunk) => { 
                            data += chunk;
                        });
                        res.on('end', () => {
                            const headers: Record<string, string> = {};
                            Object.entries(res.headers).forEach(([key, value]) => {
                                headers[key] = Array.isArray(value) ? value.join(', ') : value || '';
                            });
                            resolve({
                                status: res.statusCode || 200,
                                statusText: res.statusMessage || 'OK',
                                headers,
                                body: data,
                            });
                        });
                    });

                    req.on('error', (err) => {
                        console.error(`❌ Request error:`, err);
                        reject(err);
                    });
                    
                    if (bodyForProxy) {
                        console.log(`✍️  Writing request body...`);
                        // Write the body as-is (already properly formatted as string)
                        req.write(bodyForProxy, 'utf8');
                    }
                    req.end();
                });

                // Log the request/response (including cookies)
                await logger.logRequestDirect(method, url, request.headers, requestBody, {
                    status: response.status,
                    statusText: response.statusText,
                    headers: response.headers,
                    body: response.body
                });

                // Prepare MSW response headers (including Set-Cookie and CORS)
                const mswHeaders = { ...response.headers };
                
                // Add CORS headers to prevent jsdom CORS errors
                mswHeaders['access-control-allow-origin'] = '*';
                mswHeaders['access-control-allow-credentials'] = 'true';
                mswHeaders['access-control-allow-methods'] = 'GET, POST, PUT, DELETE, OPTIONS';
                mswHeaders['access-control-allow-headers'] = 'Content-Type, Authorization, X-Requested-With';

                // Return HttpResponse with body as string
                // Use HttpResponse.json() for JSON responses to ensure proper body handling
                const contentType = mswHeaders['content-type'] || '';
                if (contentType.includes('application/json')) {
                    try {
                        const jsonData = JSON.parse(response.body);
                        return HttpResponse.json(jsonData, {
                            status: response.status,
                            statusText: response.statusText,
                            headers: mswHeaders,
                        });
                    } catch (parseError) {
                        console.error(`❌ Failed to parse JSON response:`, parseError);
                        console.error(`❌ Body was: ${response.body.substring(0, 200)}`);
                        throw parseError;
                    }
                } else {
                    return new HttpResponse(response.body, {
                        status: response.status,
                        statusText: response.statusText,
                        headers: mswHeaders,
                    });
                }
            } catch (error) {
                console.error(`❌ Proxy error for ${method} ${url}:`, error);
                return new HttpResponse('{"error": "Proxy failed"}', { 
                    status: 500,
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        } finally {
            decrementPendingRequests();
        }
    }),
] : [
    // Cached mode: single catch-all handler
    http.all(/.*/, async ({ request }) => {
        const method = request.method;
        const url = request.url;

        incrementPendingRequests();
        try {
            // Extract request body for cache key matching
            let requestBody = null;
            if (method === 'POST' || method === 'PUT' || method === 'PATCH') {
                try {
                    const cloned = request.clone();
                    const contentType = request.headers.get('content-type') || '';
                    
                    if (contentType.includes('application/json')) {
                        requestBody = await cloned.json();
                    } else if (contentType.includes('application/x-www-form-urlencoded')) {
                        requestBody = await cloned.text();
                    } else {
                        const text = await cloned.text();
                        if (text) requestBody = text;
                    }
                } catch {
                    // Body not readable - OK for some requests
                }
            }
            
            // For /user/settings, /api/main_html, and /dashboard/*, try to get user_type from session cookie
            let userType: string | undefined;
            const urlObj = new URL(url, 'http://dummy');
            if (urlObj.pathname.includes('/user/settings') || 
                urlObj.pathname.includes('/api/main_html') ||
                urlObj.pathname.includes('/dashboard/')) {
                // Default to anonymous user type
                userType = ANONYMOUS_USER_TYPE;
                
                try {
                    // Extract sessionid from cookie header
                    const cookieHeader = request.headers.get('cookie');
                    if (cookieHeader) {
                        const sessionMatch = cookieHeader.match(/sessionid=([^;]+)/);
                        if (sessionMatch && sessionMatch[1]) {
                            const sessionId = sessionMatch[1];
                            // Get username from session
                            const username = logger.getUsernameFromSession(sessionId);
                            if (username) {
                                // Map username to user_type
                                const mappedType = USER_CREDENTIAL_TO_TYPE[username.toLowerCase()];
                                if (mappedType) {
                                    userType = mappedType;
                                    // const pathType = urlObj.pathname.includes('/user/settings') ? '/user/settings' : 
                                    //                 urlObj.pathname.includes('/api/main_html') ? '/api/main_html' : '/dashboard/*';
                                    // console.log(`📋 Mapped username '${username}' to user_type '${userType}' for ${pathType} cache lookup`);
                                } else {
                                    console.warn(`⚠️  Unknown username '${username}', using anonymous user_type`);
                                }
                            }
                        }
                    }
                } catch (error) {
                    console.warn(`⚠️  Failed to extract user_type from session, using anonymous:`, error);
                }
            }
            
            // Mode 2: Load from cache
            const cached = logger.findCachedResponse(method, url, requestBody, userType);
            
            if (cached) {
                const body = typeof cached.response.body === 'object'
                    ? JSON.stringify(cached.response.body)
                    : cached.response.body;

                // Ensure Content-Type is set
                const headers = cached.response.headers || {};
                if (!headers['content-type'] && typeof cached.response.body === 'object') {
                    headers['content-type'] = 'application/json';
                }

                return new HttpResponse(body, {
                    status: cached.response.status,
                    statusText: cached.response.statusText || 'OK',
                    headers: headers,
                });
            } else {
                console.warn(`⚠️  Cache miss: ${method} ${url}`);
                console.warn(`   Response will be empty - run with RTL_LOG_NETWORK=1 to capture`);
                
                return new HttpResponse('{}', {
                    status: 200,
                    headers: { 'Content-Type': 'application/json' }
                });
            }
        } finally {
            decrementPendingRequests();
        }
    }),
];

export { logger as rtlNetworkLogger };
