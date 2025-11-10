import pool from '../config/database.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runMigration(migrationFile: string) {
  try {
    const migrationPath = path.join(__dirname, '..', 'database', 'migrations', migrationFile);
    console.log(`📄 Reading migration: ${migrationFile}`);
    
    const sql = fs.readFileSync(migrationPath, 'utf8');
    
    console.log('🔄 Executing migration...');
    await pool.query(sql);
    
    console.log(`✅ Migration ${migrationFile} completed successfully`);
    await pool.end();
    process.exit(0);
  } catch (error) {
    console.error('❌ Migration failed:', error);
    await pool.end();
    process.exit(1);
  }
}

// Get migration file from command line argument
const migrationFile = process.argv[2];

if (!migrationFile) {
  console.error('❌ Please provide a migration file name');
  console.log('Usage: npm run migrate <migration-file>');
  console.log('Example: npm run migrate 002_create_analysis_logs.sql');
  process.exit(1);
}

runMigration(migrationFile);
