#!/bin/bash
set -e

echo "🔍 Checking database connection..."

# Wait for PostgreSQL to be ready and verify user exists
MAX_RETRIES=30
RETRY_COUNT=0

until PGPASSWORD="${POSTGRES_PASSWORD:-cgipass}" psql -h "$POSTGRES_HOST" -U "${POSTGRES_USER:-cgiuser}" -d "${POSTGRES_DB:-cgidb}" -c '\q' 2>/dev/null; do
  RETRY_COUNT=$((RETRY_COUNT + 1))
  
  if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
    echo "❌ Failed to connect to PostgreSQL after $MAX_RETRIES attempts"
    echo "   Checking if user needs to be created..."
    
    # Try to connect with postgres superuser to check/create cgiuser
    if PGPASSWORD="${POSTGRES_ADMIN_PASSWORD:-}" psql -h "$POSTGRES_HOST" -U postgres -d postgres -c '\q' 2>/dev/null; then
      echo "🔧 Creating/restoring cgiuser..."
      PGPASSWORD="${POSTGRES_ADMIN_PASSWORD:-}" psql -h "$POSTGRES_HOST" -U postgres -d postgres <<-EOSQL
        -- Create user if not exists (using DO block for conditional creation)
        DO \$\$
        BEGIN
          IF NOT EXISTS (SELECT FROM pg_catalog.pg_user WHERE usename = 'cgiuser') THEN
            CREATE USER cgiuser WITH PASSWORD 'cgipass';
            RAISE NOTICE 'Created user cgiuser';
          END IF;
        END
        \$\$;
        
        -- Ensure database exists
        SELECT 'CREATE DATABASE cgidb OWNER cgiuser'
        WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'cgidb')\gexec
        
        -- Grant necessary permissions
        GRANT ALL PRIVILEGES ON DATABASE cgidb TO cgiuser;
EOSQL
      
      # Try connecting again
      if PGPASSWORD="${POSTGRES_PASSWORD:-cgipass}" psql -h "$POSTGRES_HOST" -U "${POSTGRES_USER:-cgiuser}" -d "${POSTGRES_DB:-cgidb}" -c '\q' 2>/dev/null; then
        echo "✓ Database user restored successfully"
      else
        echo "❌ Still cannot connect. Please check database configuration."
        exit 1
      fi
    else
      echo "❌ Cannot connect to database. User may not exist."
      echo "   Set POSTGRES_ADMIN_PASSWORD in environment to auto-create user."
      exit 1
    fi
    break
  fi
  
  echo "⏳ Waiting for PostgreSQL to be ready... (attempt $RETRY_COUNT/$MAX_RETRIES)"
  sleep 2
done

echo "✓ Database connection verified"
echo "🚀 Starting application..."
exec "$@"
