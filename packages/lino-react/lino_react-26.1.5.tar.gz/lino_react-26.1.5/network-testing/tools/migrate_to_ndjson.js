#!/usr/bin/env node
/**
 * Migrate network-log-rtl-*.json files to NDJSON format
 * 
 * Usage:
 *   node migrate_to_ndjson.js <site>
 *   node migrate_to_ndjson.js noi
 *   node migrate_to_ndjson.js all  # Migrate all sites
 */

import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const LOGS_DIR = path.join(__dirname, '../logs');

function migrateFile(siteName) {
    const jsonPath = path.join(LOGS_DIR, `network-log-rtl-${siteName}.json`);
    const ndjsonPath = path.join(LOGS_DIR, `network-log-rtl-${siteName}.ndjson`);
    const backupPath = path.join(LOGS_DIR, `network-log-rtl-${siteName}.json.backup`);
    
    if (!fs.existsSync(jsonPath)) {
        console.log(`⏭️  Skipping ${siteName}: ${jsonPath} not found`);
        return false;
    }
    
    console.log(`\n🔄 Migrating ${siteName}...`);
    console.log(`   Input:  ${jsonPath}`);
    console.log(`   Output: ${ndjsonPath}`);
    
    try {
        // Read and parse JSON file
        const startTime = Date.now();
        console.log(`   Reading JSON file...`);
        const jsonData = fs.readFileSync(jsonPath, 'utf8');
        const log = JSON.parse(jsonData);
        
        const fileSize = (jsonData.length / 1024 / 1024).toFixed(2);
        console.log(`   Parsed ${log.requests.length} entries (${fileSize} MB)`);
        
        // Create backup
        console.log(`   Creating backup: ${backupPath}`);
        fs.copyFileSync(jsonPath, backupPath);
        
        // Write NDJSON file
        console.log(`   Writing NDJSON file...`);
        const writeStream = fs.createWriteStream(ndjsonPath, { encoding: 'utf8' });
        
        let written = 0;
        for (const entry of log.requests) {
            const line = JSON.stringify(entry) + '\n';
            writeStream.write(line);
            written++;
            
            if (written % 10000 === 0) {
                console.log(`   Progress: ${written}/${log.requests.length} entries...`);
            }
        }
        
        writeStream.end();
        
        // Wait for write to complete
        return new Promise((resolve) => {
            writeStream.on('finish', () => {
                const duration = ((Date.now() - startTime) / 1000).toFixed(2);
                const ndjsonStats = fs.statSync(ndjsonPath);
                const ndjsonSize = (ndjsonStats.size / 1024 / 1024).toFixed(2);
                
                console.log(`   ✅ Done! Wrote ${written} entries in ${duration}s`);
                console.log(`   NDJSON size: ${ndjsonSize} MB`);
                console.log(`   Compression: ${((1 - ndjsonStats.size / jsonData.length) * 100).toFixed(1)}%`);
                
                // Optionally delete old JSON file (commented out for safety)
                // console.log(`   Removing old JSON file: ${jsonPath}`);
                // fs.unlinkSync(jsonPath);
                
                console.log(`   ⚠️  Old JSON file kept as-is. Delete manually after verifying NDJSON works.`);
                
                resolve(true);
            });
            
            writeStream.on('error', (error) => {
                console.error(`   ❌ Error writing NDJSON:`, error);
                resolve(false);
            });
        });
        
    } catch (error) {
        console.error(`   ❌ Migration failed:`, error);
        return false;
    }
}

async function main() {
    const args = process.argv.slice(2);
    
    if (args.length === 0) {
        console.log('Usage: node migrate_to_ndjson.js <site>');
        console.log('       node migrate_to_ndjson.js noi');
        console.log('       node migrate_to_ndjson.js all');
        process.exit(1);
    }
    
    const target = args[0];
    
    if (target === 'all') {
        // Find all network-log-rtl-*.json files
        const files = fs.readdirSync(LOGS_DIR)
            .filter(f => f.startsWith('network-log-rtl-') && f.endsWith('.json') && !f.endsWith('.backup'));
        
        if (files.length === 0) {
            console.log('No network-log-rtl-*.json files found in', LOGS_DIR);
            process.exit(0);
        }
        
        console.log(`Found ${files.length} files to migrate:`);
        files.forEach(f => console.log(`  - ${f}`));
        
        for (const file of files) {
            const siteName = file.replace('network-log-rtl-', '').replace('.json', '');
            await migrateFile(siteName);
        }
    } else {
        await migrateFile(target);
    }
    
    console.log('\n✅ Migration complete!');
    console.log('\nNext steps:');
    console.log('1. Test the NDJSON files: BASE_SITE=noi BABEL=1 npm run itest');
    console.log('2. If tests pass, delete the .json backup files');
    console.log('3. Update .gitlab-ci.yml to download .ndjson cache files');
}

main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
});
