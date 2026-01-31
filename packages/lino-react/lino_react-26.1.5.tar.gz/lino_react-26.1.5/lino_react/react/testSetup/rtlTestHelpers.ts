/**
 * Helper utilities for RTL tests
 * Provides common test patterns and authentication helpers
 */

import queryString from 'query-string';
import { waitFor } from '@testing-library/react';
import { getPendingRequestCount } from './mswHandlers';

/**
 * Default test credentials
 * These match the demo fixtures created by manage.py prep
 */
export const TEST_CREDENTIALS = {
    username: 'robin',
    password: '1234',
};

/**
 * Wait for window.App to be initialized
 */
export async function waitForAppReady(timeout = 5000) {
    await waitFor(() => {
        expect(window.App).toBeDefined();
        expect(window.App.URLContext).toBeDefined();
    }, { timeout });
}

/**
 * Check if user is logged in
 */
export function isLoggedIn(): boolean {
    return window.App?.state?.user_settings?.logged_in || false;
}

/**
 * Perform login action (for tests that need authenticated state)
 * 
 * Note: When using RTL_LOG_NETWORK=1, login requests are proxied to the live server
 * and the session cookies are automatically captured and cached. When running with
 * cached responses, the login response (including session) is replayed from cache.
 * 
 * @param credentials - Login credentials (defaults to TEST_CREDENTIALS)
 */
export async function performLogin(credentials = TEST_CREDENTIALS) {
    // if (isLoggedIn()) {
    //     return; // Already logged in
    // }

    // window.App.onSignOutIn();

    const params = new URLSearchParams(queryString.stringify({ an: "sign_in", ...TEST_CREDENTIALS }));

    const resp = await fetch('/api/about/About', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8' },
        body: params,
        credentials: 'include', // Important for cookies
    });
    return resp.json();

    // Wait for login to complete
    // await waitFor(() => {
    //     expect(isLoggedIn()).toBe(true);
    // }, { timeout: 5000 });
}

export async function performLogout() {
    if (!isLoggedIn()) {
        return; // Already logged out
    }
    const resp = await fetch('auth');
    return resp.text();
}

/**
 * Common test setup that waits for app initialization
 */
export async function setupTest() {
    await waitForAppReady();
}

/**
 * Wait for network to be idle (no pending requests)
 * Useful after actions that trigger network requests
 * 
 * This implementation uses MSW's request tracking to know when all requests have completed.
 * Works in both live and cached modes.
 * 
 * @param timeout - Maximum time to wait in milliseconds (default: 3000)
 * @param idleTime - How long to wait for no new requests in milliseconds (default: 100)
 */
export async function waitForNetworkIdle(timeout = 3000, idleTime = 100): Promise<void> {
    const startTime = Date.now();
    let lastChangeTime = Date.now();
    let lastRequestCount = getPendingRequestCount();
    
    // If already idle, return immediately
    if (lastRequestCount === 0) {
        console.log('Network is already idle');
        return Promise.resolve();
    }
    
    return new Promise((resolve, reject) => {
        const interval = setInterval(() => {
            const currentCount = getPendingRequestCount();
            
            // Detect any change in request count
            if (currentCount !== lastRequestCount) {
                lastChangeTime = Date.now();
                lastRequestCount = currentCount;
            }
            
            // Check if we're idle: no pending requests and enough idle time has passed
            const timeSinceChange = Date.now() - lastChangeTime;
            if (currentCount === 0 && timeSinceChange >= idleTime) {
                clearInterval(interval);
                resolve();
            } else if (Date.now() - startTime > timeout) {
                clearInterval(interval);
                reject(new Error(`Network did not become idle within ${timeout}ms (${currentCount} pending)`));
            }
        }, 50);
    });
}

/**
 * Clean up after tests
 */
export function cleanupTest() {
    // Add any cleanup logic here if needed
}
