import { query } from './config/database.js';
import { readFileSync } from 'fs';
import { join } from 'path';

async function runMigration() {
  try {
    console.log('🔄 Running analysis logs enhancement migration...');
    
    const migrationSQL = readFileSync(
      join(process.cwd(), 'database/migrations/003_enhance_analysis_logs.sql'),
      'utf-8'
    );
    
    await query(migrationSQL);
    
    console.log('✅ Migration completed successfully!');
    process.exit(0);
  } catch (error) {
    console.error('❌ Migration failed:', error);
    process.exit(1);
  }
}

runMigration();
