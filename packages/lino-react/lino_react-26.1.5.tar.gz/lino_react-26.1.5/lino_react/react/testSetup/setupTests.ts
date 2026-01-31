// Mock i18n ONLY for RTL tests (BABEL=1) to avoid language change issues
// CRITICAL: jest.mock MUST be at top level to be hoisted by Jest
// We create a real i18n instance but stub out changeLanguage to prevent disruption
jest.mock('../components/i18n', () => {
    // Only apply mock for RTL tests, return actual module otherwise
    if (process.env.BABEL === '1') {
        const i18n = require('i18next');
        const { initReactI18next } = require('react-i18next');
        
        // Create a real i18n instance for react-i18next compatibility
        const mockI18n = i18n.createInstance();
        mockI18n
            .use(initReactI18next)
            .init({
                lng: 'en',
                fallbackLng: 'en',
                resources: {
                    en: { translation: {} }
                },
                react: {
                    useSuspense: false  // Disable suspense for testing
                },
                interpolation: {
                    escapeValue: false
                }
            });
        
        // Stub changeLanguage to prevent it from triggering re-fetch
        const originalChangeLanguage = mockI18n.changeLanguage.bind(mockI18n);
        mockI18n.changeLanguage = jest.fn((lng: string) => {
            // Return resolved promise without actually changing language
            return Promise.resolve(mockI18n.t);
        });
        
        return {
            __esModule: true,
            default: mockI18n,
            TransInit: jest.fn((context: any, callback: any) => {
                // Call callback immediately with mocked i18n
                callback(mockI18n);
            }),
        };
    } else {
        // For Puppeteer tests, use actual i18n module
        return jest.requireActual('../components/i18n');
    }
});

import '@testing-library/jest-dom';
import { setTimeout } from "timers/promises";
import { get } from 'http';
import * as t from "../components/types";
import { TextEncoder, TextDecoder } from 'util';

if (process.env.BABEL === '1') {
    // Set jsdom URL with hash BEFORE any polyfills or imports
    // Lino uses hash-based routing like http://localhost/#/dashboard?params
    // Must be set early to avoid popstate events with invalid URLs
    if (typeof window !== 'undefined') {
        Object.defineProperty(window, 'location', {
            value: new URL('http://localhost/#/'),
            writable: true
        });
    }

    // Set global log level from environment variable
    if (process.env.LINO_LOGLEVEL) {
        global.LINO_LOGLEVEL = parseInt(process.env.LINO_LOGLEVEL);
    }

    // Polyfills for jsdom environment - MUST be set before importing MSW
    global.TextEncoder = TextEncoder;
    (global as any).TextDecoder = TextDecoder;
    
    // Polyfill Web Streams API for MSW
    if (typeof (global as any).TransformStream === 'undefined') {
        const { TransformStream, ReadableStream, WritableStream } = require('stream/web');
        (global as any).TransformStream = TransformStream;
        (global as any).ReadableStream = ReadableStream;
        (global as any).WritableStream = WritableStream;
    }
    
    // Use Node.js native fetch (available in Node 18+) instead of whatwg-fetch
    // Native fetch is more compatible with MSW's HttpResponse
    if (typeof global.fetch === 'undefined') {
        console.log('⚠️  Native fetch not available, falling back to whatwg-fetch');
        require('whatwg-fetch');
    } else {
        console.log('✅ Using Node.js native fetch');
    }
    
    // Polyfill BroadcastChannel for MSW WebSocket support
    // MSW uses BroadcastChannel in its core module even though we're only using HTTP handlers
    if (typeof (global as any).BroadcastChannel === 'undefined') {
        class BroadcastChannel {
            constructor(public name: string) {}
            postMessage(message: any) {}
            addEventListener(type: string, listener: any) {}
            removeEventListener(type: string, listener: any) {}
            close() {}
        }
        (global as any).BroadcastChannel = BroadcastChannel;
    }
    
    // Setup MSW for network mocking in RTL tests
    // This replaces the old MOCK_NETWORK system with MSW
    const { setupServer } = require('msw/node');
    const { handlers, rtlNetworkLogger } = require('./mswHandlers');
    
    const server = setupServer(...handlers);

    // Suppress CSS parsing and act() warnings (these are expected in this test environment)
    const originalConsoleError = console.error;
    console.error = (...args) => {
        const errorStr = String(args[0]);
        if (!errorStr.includes('Could not parse CSS stylesheet')
            && !errorStr.includes('not wrapped in act(')
        ) {
            originalConsoleError(...args);
        }
    };

    const originalConsoleWarn = console.warn;
    console.warn = (...args) => {
        const warnStr = String(args[0]);
        if (warnStr.includes('quill') && String(args[1]).includes('Overwriting')) {
            return;
        };
        originalConsoleWarn(...args);
    };

    const originalConsoleLog = console.log;
    console.log = (...args) => {
        const logStr = String(args[0]);
        if (logStr.includes('top_links')) {
            return;
        };
        originalConsoleLog(...args);
    };
    
    // Start MSW server before all tests
    beforeAll(async () => {
        // Wait for cache to load before starting tests
        if (rtlNetworkLogger.loadingPromise) {
            await rtlNetworkLogger.loadingPromise;
        }
        
        server.listen({ onUnhandledRequest: 'warn' });
        console.log('🎭 MSW server started for RTL tests');
        
        if (process.env.RTL_LOG_NETWORK === '1') {
            console.log('📝 Network requests will be proxied to live server and logged');
        } else {
            console.log('📦 Network requests will be served from cached responses');
        }
    });
    
    // Reset handlers after each test
    afterEach(() => {
        server.resetHandlers();
    });
    
    // Stop MSW server after all tests
    afterAll(() => {
        console.error = originalConsoleError;
        console.warn = originalConsoleWarn;
        console.log = originalConsoleLog;
        server.close();
        console.log('🛑 MSW server stopped');
    });

    // jsdom provides Storage, but we need to ensure global.Storage is set
    // for custom_hooks.js to extend Storage.prototype
    if (!global.Storage && (window as any).Storage) {
        (global as any).Storage = (window as any).Storage;
    }

    // Mock window.Lino for React components
    (window as any).Lino = {
        site_name: "Lino",
    };

    // Mock window.matchMedia
    Object.defineProperty(window, 'matchMedia', {
        writable: true,
        value: jest.fn().mockImplementation(query => ({
            matches: false,
            media: query,
            onchange: null,
            addListener: jest.fn(),
            removeListener: jest.fn(),
            addEventListener: jest.fn(),
            removeEventListener: jest.fn(),
            dispatchEvent: jest.fn(),
        })),
    });

    // Mock IndexedDB for tests
    const mockDB = {
        close: () => {},
        transaction: () => ({
            objectStore: () => ({
                get: (key: string) => {
                    const request: any = { result: undefined };
                    // Trigger onsuccess callback asynchronously when set
                    Object.defineProperty(request, 'onsuccess', {
                        get() { return this._onsuccess; },
                        set(callback) {
                            this._onsuccess = callback;
                            if (callback) {
                                global.setTimeout(() => callback({ target: request }), 0);
                            }
                        }
                    });
                    return request;
                },
                put: (value: any, key: string) => {
                    const request: any = { result: undefined };
                    Object.defineProperty(request, 'onsuccess', {
                        get() { return this._onsuccess; },
                        set(callback) {
                            this._onsuccess = callback;
                            if (callback) {
                                global.setTimeout(() => callback({ target: request }), 0);
                            }
                        }
                    });
                    return request;
                },
                delete: (key: string) => {
                    const request: any = { result: undefined };
                    Object.defineProperty(request, 'onsuccess', {
                        get() { return this._onsuccess; },
                        set(callback) {
                            this._onsuccess = callback;
                            if (callback) {
                                global.setTimeout(() => callback({ target: request }), 0);
                            }
                        }
                    });
                    return request;
                },
            }),
        }),
    };
    
    (global as any).indexedDB = {
        open: (name: string, version: number) => {
            const request: any = {
                result: mockDB,
                _onsuccess: null,
                _onerror: null,
                _onupgradeneeded: null,
            };
            
            // Use setters to trigger callbacks immediately when assigned
            Object.defineProperty(request, 'onsuccess', {
                get() { return this._onsuccess; },
                set(callback) {
                    this._onsuccess = callback;
                    if (callback) {
                        global.setTimeout(() => callback({ target: request }), 0);
                    }
                }
            });
            
            Object.defineProperty(request, 'onerror', {
                get() { return this._onerror; },
                set(callback) { this._onerror = callback; }
            });
            
            Object.defineProperty(request, 'onupgradeneeded', {
                get() { return this._onupgradeneeded; },
                set(callback) { this._onupgradeneeded = callback; }
            });
            
            return request;
        },
    };
}

type condition = () => boolean;

global.SERVER_PATH = "127.0.0.1:3000";
global.SERVER_URL = `http://${global.SERVER_PATH}`;
global.WAIT_TIMEOUT = 20000;

global.waitToMeet = async (page, fn: condition, ...args) => {
    const initTime: number = Date.now();
    while ((Date.now() - initTime) < global.WAIT_TIMEOUT) {
        if (await page.evaluate(fn, ...args)) return;
        await setTimeout(300);
    }

    let err = Error("Could not satisfy condition");
    throw err;
}

global.wait = {
    actionHandlerReady: async (page) => {
        await global.waitToMeet(page, () => (
            window.App.hasOwnProperty('URLContext') &&
            window.App.URLContext.hasOwnProperty('actionHandler') &&
            window.App.URLContext.actionHandler.ready));
    },
    parserReady: async (page) => {
        await global.wait.actionHandlerReady(page);
        await global.waitToMeet(page,
            () => window.App.URLContext.actionHandler.parser.ready);
    },
    dataContextReady: async (page) => {
        await global.wait.parserReady(page);
        await global.waitToMeet(page, () => {
            return (window.App.URLContext.hasOwnProperty('dataContext') &&
                window.App.URLContext.dataContext.ready)
        })
    },
    dataLoadDone: async (page) => {
        await global.wait.dataContextReady(page);
        await global.waitToMeet(page, () => {
            // return true;
            return window.App.URLContext.dataContext.mutableContext.success;
        });
    },
    runserverInit: async () => {
        // process.stdout.write("===========================\n");
        const oto = global.WAIT_TIMEOUT;
        global.WAIT_TIMEOUT = 30000;

        let ok = false;
        const initTime = Date.now();
        while ((Date.now() - initTime) < global.WAIT_TIMEOUT) {
            if (await new Promise((resolve) => {
                get(global.SERVER_URL, (res) => {
                    // process.stdout.write(`${res.statusCode}\n!!!!!!\n`);
                    ok = res.statusCode === 200;
                    resolve(ok);
                    // resolve(res.statusCode === 200);
                }).on('error', (e) => {
                    resolve(false);
                })
            }).then(r => r))
                break;
            await setTimeout(300);
        }
        if (!ok) throw "runserver failed!";
        // process.stdout.write("===========================\n");
        global.WAIT_TIMEOUT = oto;
    },
}

global.signIn = async (page) => {
    await global.wait.dataContextReady(page);
    if (await page.evaluate(() => window.App.state.user_settings.logged_in))
        return;
    await page.evaluate(() => {
        const { actionHandler } = window.App.URLContext;
        const action = actionHandler.findUniqueAction("sign_in");
        actionHandler.runAction({actorId: "about.About", action_full_name: action.full_name});
    });
    await global.waitToMeet(page, (): boolean => {
        let { URLContext } = window.App;
        let childContext: t.NavigationContext = Object.values(URLContext.children)[0];
        if (!URLContext.filled(childContext)) return false;
        if (!URLContext.filled(childContext.dataContext)) return false;
        if (!URLContext.filled(childContext.dataContext.mutableContext.data)) return false;
        return true;
    });
    await page.evaluate(() => {
        let context: t.NavigationContext = Object.values(window.App.URLContext.children)[0];
        Object.assign(context.dataContext.mutableContext.data, {
            username: 'robin', password: '1234'});
    });
    await page.evaluate(() => {
        (Object.values(window.App.URLContext.children)[0] as t.NavigationContext).dataContext.root.ok();
    });
    await page.waitForNetworkIdle();
    await global.waitToMeet(page, (): boolean => {
        let { URLContext, state } = window.App;
        if (Object.values(URLContext.children).length) return false;
        if (!URLContext.filled(state.user_settings)) return false;
        if (!URLContext.filled(state.site_data)) return false;
        return state.user_settings.logged_in;
    });
    await global.wait.dataContextReady(page);
}

// page.on("console", message => console.log(message.text()));
// page.on('console', async (msg) => {
//     const msgArgs = msg.args();
//     for (let i = 0; i < msgArgs.length; ++i) {
//         console.log(await msgArgs[i].jsonValue());
//     }
// });

// Custom Jest error handler to suppress the intentional App.setReady error
if (process.env.BABEL === '1') {
    const originalIt = global.it;
    global.it = function(name, fn, timeout?) {
        return originalIt(name, async function(...args) {
            try {
                return await fn.apply(this, args);
            } catch (error) {
                // Suppress the intentional App.setReady error
                if (typeof error === 'string' && error.includes('Intentionally raised')) {
                    return;
                }
                throw error;
            }
        }, timeout);
    } as typeof global.it;
}

// Save network logs after all tests complete
if (global.networkLogger && process.env.BABEL !== '1') {
    afterAll(async () => {
        const site = process.env.BASE_SITE || 'unknown';
        const filename = `network-log-${site}.json`;
        await global.networkLogger.saveToFile(filename);
    });
}
