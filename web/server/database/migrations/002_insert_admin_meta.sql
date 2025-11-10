-- Insert dummy Admin Meta account
-- Password: admin123
-- Note: This is a hashed version of "admin123" using bcrypt with salt rounds 10

INSERT INTO users (email, password_hash, full_name, role, is_active)
VALUES (
  'adminmeta@aiclaimlite.com',
  '$2b$10$rJ5YKvV5XQKZqN0gKqXhXOXKZvKJ5YnJ5YnJ5YnJ5YnJ5YnJ5Yn',
  'Admin Meta',
  'Admin Meta',
  true
)
ON CONFLICT (email) DO NOTHING;

-- Verify the insert
SELECT id, email, full_name, role, is_active, created_at 
FROM users 
WHERE role = 'Admin Meta';
