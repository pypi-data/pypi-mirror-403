import type { Config } from 'jest';

// https://jestjs.io/docs/configuration
const config: Config = {
    // bail: true, // bail after first failure
    globalSetup: "<rootDir>/lino_react/react/testSetup/setupJEST.mjs",
    globalTeardown: "<rootDir>/lino_react/react/testSetup/teardownJEST.mjs",
    testEnvironment: process.env.BABEL === '1' ? 'jsdom' : "<rootDir>/lino_react/react/testSetup/testEnvironment.mjs",
    moduleFileExtensions: ["js", "jsx", "ts", "tsx"],
    // Custom module resolution to prevent ts-jest from compiling external TypeScript
    // modulePathIgnorePatterns: [
    //     "/home/blurry/GitHub/projects/managed/quill-next/packages/quill/src",
    //     "/home/blurry/GitHub/projects/managed/parchment/src"
    // ],
    moduleNameMapper: {
        '^.+\\.(css|less)$': '<rootDir>/CSSStub.mjs',
        // Try loading real Quill modules, but keep problematic ones mocked
        // '^quill-next-react$': '<rootDir>/lino_react/react/testSetup/mocks/emptyMock.js',
        // '^quill-image-drop-and-paste$': '<rootDir>/lino_react/react/testSetup/mocks/emptyMock.js',
        // '^@enzedonline/quill-blot-formatter2$': '<rootDir>/lino_react/react/testSetup/mocks/emptyMock.js',
        // '^quill-html-edit-button$': '<rootDir>/lino_react/react/testSetup/mocks/emptyMock.js',
        // '^quill-mention$': '<rootDir>/lino_react/react/testSetup/mocks/quillMentionMock.js',
        '^quill-next-react$': '<rootDir>/node_modules/quill-next-react/dist/index.js',
        // '^quill/dist/(.*)$': '<rootDir>/node_modules/quill/dist/$1',
        // Redirect lodash-es from local quill node_modules to react's node_modules  
        // 'lodash-es': '<rootDir>/node_modules/lodash-es/lodash.js',
        // Redirect @babel/runtime from local quill to react's node_modules
        // '@babel/runtime/(.*)': '<rootDir>/node_modules/@babel/runtime/$1',
        '^@mswjs/interceptors/(.*)$': '<rootDir>/node_modules/@mswjs/interceptors/$1',
        '^msw/node$': '<rootDir>/node_modules/msw/lib/node/index.js',
    },
    preset: 'jest-puppeteer',
    // testRegex: "(/__tests__/.*|(\\.|/)(test|spec))\\.(jsx?|tsx?|js?|ts?)$",
    roots: ["<rootDir>/lino_react/react/components"],
    setupFilesAfterEnv: ["<rootDir>/lino_react/react/testSetup/setupTests.ts"],
    testMatch: [`<rootDir>/lino_react/react/components/__tests__/${process.env.BASE_SITE}/*.ts${process.env.BABEL ? 'x' : ''}`],
    testTimeout: 300000,
    transform: {
        '^.+\\.(ts|tsx)?$': 'ts-jest',
        '^.+\\.(js|jsx|mjs)$': 'babel-jest',
    },
    transformIgnorePatterns: [
        "node_modules/(?!(query-string|decode-uri-component|split-on-first|filter-obj|quill|quill-next-react|lodash-es|parchment|quill-mention|quill-html-edit-button|quill-image-drop-and-paste|msw|@mswjs|until-async)/)"
    ],
    verbose: true,
    reporters: [
        'default',
        ['jest-junit', {
            outputDirectory: '.',
            outputName: 'junit.xml',
            classNameTemplate: '{classname}',
            titleTemplate: '{title}',
            ancestorSeparator: ' › ',
            usePathForSuiteName: true,
        }],
    ],
    collectCoverage: true,
    coverageDirectory: 'coverage',
    coverageReporters: ['html', 'text', 'lcov', 'cobertura'],
    collectCoverageFrom: [
        'lino_react/react/components/**/*.{js,jsx,ts,tsx}',
        '!lino_react/react/components/**/*.test.{js,jsx,ts,tsx}',
        '!lino_react/react/components/**/__tests__/**',
        '!lino_react/react/testSetup/**',
    ],
}

export default config;
