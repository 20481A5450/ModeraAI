-- Ensure the database exists
CREATE DATABASE moderaai_db;

-- Connect to the correct database
\c moderaai_db;

-- Create moderation_results table if it doesn't exist
CREATE TABLE IF NOT EXISTS moderation_results (
    id SERIAL PRIMARY KEY,
    text TEXT NOT NULL,
    flagged BOOLEAN NOT NULL,
    categories JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
