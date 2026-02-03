-- ============================================================================
-- Create Read-Only Database User for Enhanced Security
-- ============================================================================
-- This script creates a PostgreSQL user with SELECT-only permissions
-- Use this user in production to prevent accidental or malicious writes
-- even if validation is bypassed
-- ============================================================================

-- Drop user if exists (for re-running script)
DROP USER IF EXISTS cgi_readonly;

-- Create read-only user with strong password
-- IMPORTANT: Change this password in production!
CREATE USER cgi_readonly WITH PASSWORD 'readonly_secure_password_change_me';

-- Grant CONNECT privilege to the database
GRANT CONNECT ON DATABASE cgidb TO cgi_readonly;

-- Grant USAGE on schema
GRANT USAGE ON SCHEMA public TO cgi_readonly;

-- Grant SELECT on all existing tables
GRANT SELECT ON ALL TABLES IN SCHEMA public TO cgi_readonly;

-- Grant SELECT on all existing sequences (for viewing)
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO cgi_readonly;

-- Grant SELECT on future tables (important for new tables)
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO cgi_readonly;

-- Grant SELECT on future sequences
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON SEQUENCES TO cgi_readonly;

-- Explicitly revoke write permissions (belt and suspenders)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA public FROM cgi_readonly;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM cgi_readonly;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO cgi_readonly;

-- Prevent user from creating new objects
REVOKE CREATE ON SCHEMA public FROM cgi_readonly;

-- ============================================================================
-- Verification Queries
-- ============================================================================

-- Check user privileges
SELECT 
    grantee,
    table_schema,
    table_name,
    privilege_type
FROM information_schema.table_privileges
WHERE grantee = 'cgi_readonly'
ORDER BY table_name, privilege_type;

-- Expected output: Only SELECT privileges on tables

-- ============================================================================
-- Test the user (run as separate connection)
-- ============================================================================
-- psql -U cgi_readonly -d cgidb -c "SELECT count(*) FROM customers;"  -- Should work
-- psql -U cgi_readonly -d cgidb -c "DELETE FROM customers;"           -- Should fail

-- ============================================================================
-- Usage in Application
-- ============================================================================
-- Update your .env file:
--   POSTGRES_USER=cgi_readonly
--   POSTGRES_PASSWORD=readonly_secure_password_change_me
--
-- Or use credentials_setup.py:
--   python tools/credentials_setup.py
--
-- The application will now be unable to perform writes at the database level,
-- even if all validation layers are bypassed!
-- ============================================================================

-- Print success message
DO $$
BEGIN
    RAISE NOTICE '✓ Read-only user "cgi_readonly" created successfully';
    RAISE NOTICE '✓ User has SELECT permission on all tables';
    RAISE NOTICE '✓ User cannot INSERT, UPDATE, DELETE, or perform DDL operations';
    RAISE NOTICE '';
    RAISE NOTICE 'Next steps:';
    RAISE NOTICE '1. Change the password to something secure';
    RAISE NOTICE '2. Update POSTGRES_USER and POSTGRES_PASSWORD in .env';
    RAISE NOTICE '3. Restart the application';
    RAISE NOTICE '4. Test with: python test_llm_prompt_injection.py';
END $$;
