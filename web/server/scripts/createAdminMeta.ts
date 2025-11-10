import bcrypt from 'bcrypt';
import { query } from '../config/database.js';

const SALT_ROUNDS = 10;

async function createAdminMeta() {
  try {
    const email = 'adminmeta@aiclaimlite.com';
    const password = 'admin123';
    const full_name = 'Admin Meta';
    const role = 'Admin Meta';

    // Check if admin meta already exists
    const existingUser = await query(
      'SELECT id FROM users WHERE email = $1',
      [email]
    );

    if (existingUser.rows.length > 0) {
      console.log('❌ Admin Meta already exists');
      return;
    }

    // Hash password
    const password_hash = await bcrypt.hash(password, SALT_ROUNDS);

    // Insert admin meta
    const result = await query(
      `INSERT INTO users (email, password_hash, full_name, role, is_active) 
       VALUES ($1, $2, $3, $4, $5) 
       RETURNING id, email, full_name, role, is_active, created_at`,
      [email, password_hash, full_name, role, true]
    );

    console.log('✅ Admin Meta created successfully:');
    console.log('   Email:', result.rows[0].email);
    console.log('   Password: admin123');
    console.log('   Role:', result.rows[0].role);
    console.log('   ID:', result.rows[0].id);
  } catch (error) {
    console.error('❌ Error creating Admin Meta:', error);
  } finally {
    process.exit(0);
  }
}

createAdminMeta();
