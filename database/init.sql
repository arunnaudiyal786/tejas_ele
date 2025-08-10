-- Database Initialization Script (init.sql)

-- Create user if not exists
DO
$do$
BEGIN
   IF NOT EXISTS (
      SELECT FROM pg_catalog.pg_roles
      WHERE  rolname = 'testuser') THEN
      CREATE ROLE testuser LOGIN PASSWORD 'testpass';
   END IF;
END
$do$;

-- Create database if not exists
SELECT 'CREATE DATABASE testdb' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'testdb')\gexec

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE testdb TO testuser;
GRANT ALL PRIVILEGES ON SCHEMA public TO testuser;

-- Connect to testdb and create table
\c testdb;

CREATE TABLE IF NOT EXISTS long_running_table (
    id SERIAL PRIMARY KEY,
    data TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Grant table permissions
GRANT ALL PRIVILEGES ON long_running_table TO testuser;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO testuser;

-- Insert data only if table is empty
INSERT INTO long_running_table (data) 
SELECT 'Row ' || generate_series(1, 1000000)
WHERE NOT EXISTS (SELECT 1 FROM long_running_table LIMIT 1);
