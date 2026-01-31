import { waitFor } from '@testing-library/react';
import '../../custom_hooks'; // needed for context manipulation
import { ActionHandler } from '../../ActionHandler';
import { Context } from '../../NavigationControl';

describe('actionHandler.tsx', () => {
    it('about.About.show from window with `hasActor`', async () => {
        const siteData = await (await fetch('/media/cache/json/lino_900_en.json')).json();

        const APP = {
            state: {
                site_data: siteData,
                user_settings: { user_type: "900", site_lang: "en" },
            },
            rps: {},
            data: {},
            storageName: 'lino_react_test_db',
            cacheDB: undefined as IDBDatabase | undefined,
            unsetLoadMask: jest.fn(),
        };
        
        const request = window.indexedDB.open(APP.storageName, 1);
        request.onsuccess = (event) => {
            APP.cacheDB = (event.target as IDBOpenDBRequest).result;
        }

        const context = new Context({APP, rs: "11111111", next: () => {}});

        const actionHandler = new ActionHandler({context, next: () => {}});

        await waitFor(() => {
            expect(context.history).toBeDefined();
        }, { timeout: 2000 });

        await waitFor(() => {
            expect(APP.cacheDB).toBeDefined();
            expect(actionHandler.context).toBeDefined();
        }, { timeout: 2000 });

        context.value.sr = [500];
        context.history.pushPath = jest.fn(async (...params) => {
            expect(params).toEqual([
                { pathname: '/api/about/About', params: { an: 'show', sr: [] } },
                { clickCatch: false },
            ]);
        });

        await actionHandler.runAction({action_full_name: 'about.About.show', actorId: 'about.About'});
    });
});