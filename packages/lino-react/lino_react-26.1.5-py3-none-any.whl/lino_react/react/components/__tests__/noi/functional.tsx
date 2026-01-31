import React, { act } from 'react';
import ReactDOMClient from 'react-dom/client';
// import { setTimeout } from "timers/promises";
import { fireEvent, screen, waitFor } from '@testing-library/react';
// import userEvent from '@testing-library/user-event';
import { Main } from '../../App';
import { isLoggedIn, performLogin, performLogout } from '../../../testSetup/rtlTestHelpers';

/**
 * RTL Tests with MSW Network Mocking
 * 
 * Two modes available:
 * 
 * 1. Live server with logging (RTL_LOG_NETWORK=1):
 *    RTL_LOG_NETWORK=1 BASE_SITE=noi BABEL=1 npm run rtltest
 *    - Starts Django server on port 3000 (must run `manage.py prep` first)
 *    - MSW proxies all requests to live server
 *    - Responses are cached in network-testing/logs/network-log-rtl-{site}.json
 *    - Session cookies from login are automatically captured
 * 
 * 2. Cached responses (default):
 *    BASE_SITE=noi BABEL=1 npm run rtltest
 *    - MSW loads responses from network-testing/logs/network-log-rtl-{site}.json
 *    - No server needed, tests run offline
 *    - Session cookies are replayed from cache
 * 
 * AUTHENTICATION:
 * - Demo credentials: username='robin', password='1234'
 * - These are created by `manage.py prep --noinput`
 * - Login requests/responses are captured/replayed like any other request
 * - See rtlTestHelpers.ts for authentication helper functions
 * 
 * The old MOCK_NETWORK system has been replaced by MSW for better reliability.
 */

describe('(noi) functional.tsx', () => {
    describe('user type 900 (en)', () => {
        let container: HTMLElement;
        
        beforeAll(async () => {
            // Perform login before tests
            await performLogin();
            // const resp = await performLogin();
            // console.log('Login response:', resp);

            container = document.createElement('div');
            document.body.appendChild(container);

            // Initial render
            await act(async () => {
                ReactDOMClient.createRoot(container).render(<Main />);
            });
        });

        beforeEach(async () => {
            await waitFor(() => {
                expect(screen.getByText(/Hi, Robin Rood!/)).toBeTruthy();
            }, { timeout: 5000 });
        
        });

        afterEach(async () => {
            if (!window.App.dashboard) {
                await act(async () => {
                    window.App.URLContext.history.pushPath({
                        pathname: '/',
                    });
                });
            }

            await waitFor(() => {
                expect(screen.getByText(/Hi, Robin Rood!/)).toBeTruthy();
            }, { timeout: 5000 });
        });

        afterAll(async () => {
            // Perform logout after tests
            await performLogout();
            document.body.removeChild(container);
        });

        it("render App", async () => {
            // Wait for App to be available on window
            await waitFor(() => {
                expect(window.App).toBeDefined();
            }, { timeout: 2000 });

            // Wait for the app to render content
            await waitFor(() => {
                expect(container.firstChild).toBeTruthy();
            }, { timeout: 5000 });

            // Wait for site_data to load first before checking for specific UI elements
            await waitFor(() => {
                expect(window.App.state.site_data !== null).toBe(true);
            }, { timeout: 10000 });

            // Verify app structure exists (container should have child elements)
            expect(container.firstChild).toBeTruthy();
            expect(window.App).toBeDefined();
            expect(window.App.state.site_data).toBeTruthy();

            expect(isLoggedIn()).toBe(true);
        });

        it('FullParamsPanel on tickets.AllTickets', async () => {
            window.App.URLContext.history.pushPath({
                pathname: '/api/tickets/AllTickets',
            });
            await waitFor(() => {
                expect(screen.getAllByText(/All tickets/)[0]).toBeTruthy();
            }, { timeout: 5000 });

            expect(screen.queryByText(/More .../)).toBeNull();

            await waitFor(() => {
                expect(document.querySelector('.l-button-pv_control')).toBeTruthy();
            }, { timeout: 5000 });

            await act(async () => {
                fireEvent.click(document.querySelector('.l-button-pv_control'));
            });
            
            await waitFor(() => {
                expect(screen.queryByText(/More .../)).toBeTruthy();
            }, { timeout: 5000 });

            let inputCountInParamsPanel: number;

            await waitFor(() => {
                const paramsPanel: HTMLElement | null = document.querySelector('.l-params-panel');
                expect(paramsPanel).toBeTruthy();
                const inputs: NodeListOf<HTMLInputElement> = paramsPanel.querySelectorAll('input');
                expect(inputs.length).toBeGreaterThan(0);
                inputCountInParamsPanel = inputs.length;
            }, { timeout: 5000 });

            await act(async () => {
                fireEvent.click(screen.getByRole('button', { name: /More .../ }));
            });

            await waitFor(() => {
                const paramsPanel: HTMLElement | null = document.querySelector('.l-params-panel');
                expect(paramsPanel).toBeTruthy();
                const inputs: NodeListOf<HTMLInputElement> = paramsPanel.querySelectorAll('input');
                expect(inputs.length).toBeGreaterThan(inputCountInParamsPanel);
            }, { timeout: 5000 });

            const rowCount: number = window.App.URLContext.dataContext.mutableContext.count;
            expect(rowCount).toBeGreaterThan(0);

            await act(async () => {
                fireEvent.click(screen.getByText(/Assigned:/).parentElement.querySelector('.p-dropdown-trigger'));
            });

            const yesXPath = "//li[@class='p-dropdown-item']//span//div[text()='Yes']";
            
            await waitFor(() => {
                expect(document.evaluate(
                    yesXPath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                ).singleNodeValue).toBeTruthy();
            }, { timeout: 5000 });

            await act(async () => {
                fireEvent.click(document.evaluate(
                    yesXPath,
                    document,
                    null,
                    XPathResult.FIRST_ORDERED_NODE_TYPE,
                    null
                ).singleNodeValue);
            });

            await waitFor(() => {
                expect(
                    window.App.URLContext.dataContext.mutableContext.count
                ).toBeLessThan(rowCount);
            }, { timeout: 5000 });
        });
    });

    describe('user type 000 (en)', () => {
        let container: HTMLElement;

        beforeAll(async () => {
            container = document.createElement('div');
            document.body.appendChild(container);

            await act(async () => {
                ReactDOMClient.createRoot(container).render(<Main />);
            });
        });

        afterAll(async () => {
            document.body.removeChild(container);
        });

        it('test sign in and sign out', async () => {
            // Wait for page to load - check that Sign in button is present (anonymous user)
            await waitFor(() => {
                expect(screen.getByText(/Welcome to the/)).toBeTruthy();
            }, { timeout: 5000 });

            expect(isLoggedIn()).toBe(false);

            await act(async () => {
                fireEvent.click(screen.getByText(/Sign in/));
            });

            await waitFor(() => {
                expect(screen.getByText(/Username:/)).toBeTruthy();
            }, { timeout: 5000 });

            const usernameInput: HTMLInputElement = screen.getByText('Username:').parentElement.querySelector('input');
            const passwordInput: HTMLInputElement = screen.getByText('Password:').parentElement.querySelector('input');

            await act(async () => {
                fireEvent.change(usernameInput, { target: { value: 'robin' } });
                fireEvent.change(passwordInput, { target: { value: '1234' } });
            });

            await act(async () => {
                fireEvent.click(screen.getByRole('button', { name: /OK/ }));
            });

            // Wait for network to settle after login
            // await waitForNetworkIdle();

            // Check that user is actually logged in
            await waitFor(() => {
                expect(isLoggedIn()).toBe(true);
                expect(screen.getByRole('button', { name: /👤/ })).toBeTruthy();
            }, { timeout: 5000 });

            await act(async () => {
                fireEvent.click(screen.getByRole('button', { name: /👤/ }));
            });

            await act(async () => {
                fireEvent.click(screen.getByText(/Sign out/));
            });

            await waitFor(() => {
                expect(screen.getByText(/Welcome to the/)).toBeTruthy();
            }, { timeout: 5000 });

            expect(isLoggedIn()).toBe(false);
        });
            
    });
});