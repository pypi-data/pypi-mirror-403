import path from 'path';
import vfs from 'vinyl-fs';
import scanner from 'i18next-scanner';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const setDefaultValue = (lang, ns, key, options) => (options.defaultValue || key);
// const setDefaultValue = (lang, ns, key, options) => {
//     if (key === 'Sort By{{colonSpaced}}{{value}}')
//         console.log(lang, ns, key, options);
//     return options.defaultValue || key;
// }

// Scan source component files
vfs.src([path.join(__dirname, '../react/components/**/*.{js,jsx,ts,tsx}')])
    .pipe(scanner({
        // See: options -> https://github.com/i18next/i18next-scanner#options
        defaultValue: setDefaultValue,
        removeUnusedKeys: true,
        lngs: ['en', 'bn', 'de', 'fr', 'et'],
        func: {
            list: ['t', 'i18n.t', 'i18next.t'],
            extensions: ['.js', '.jsx', '.ts', '.tsx']
        },
        trans: false, // Disable Trans component parsing to avoid TypeScript syntax errors
        nsSeparator: false, // Don't use namespace separator
        keySeparator: false, // Don't use key separator (allows dots in keys)
        resource: {
            loadPath: path.join(__dirname, 'extracts/i18n/{{lng}}/{{ns}}.json'),
            savePath: 'extracts/i18n/{{lng}}/{{ns}}.json',
        }
    }))
    .pipe(vfs.dest(__dirname));
