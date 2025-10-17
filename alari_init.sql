-- Create database
CREATE DATABASE alari_db;

-- Create a dedicated user (recommended for production)
CREATE USER alari_user WITH PASSWORD 'bjorn';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE alari_db TO alari_user;

ALTER DATABASE alari_db SET timezone TO 'UTC';

