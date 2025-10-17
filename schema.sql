-- ============================================================
-- Alari Motivational Chatbot Database Schema
-- PostgreSQL Database
-- Created: 2025-10-13
-- ============================================================

-- Set timezone to UTC for all operations
SET timezone = 'UTC';

-- Create database (run this separately with superuser privileges)
-- CREATE DATABASE alari_db WITH ENCODING 'UTF8' LC_COLLATE='en_US.UTF-8' LC_CTYPE='en_US.UTF-8';

-- Connect to the database
-- \c alari_db

-- Create extension for UUID generation (optional, useful for future)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- TABLE: users
-- Stores user authentication and profile information
-- ============================================================
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    user_name VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT users_email_unique UNIQUE (email)
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_created_at ON users(created_at);

-- ============================================================
-- TABLE: conversations
-- Stores chat conversation sessions
-- ============================================================
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    title VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Foreign Keys
    CONSTRAINT fk_conversations_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
    
    -- Constraints
    CONSTRAINT conversations_session_id_unique UNIQUE (session_id)
);

CREATE INDEX idx_conversations_user_id ON conversations(user_id);
CREATE INDEX idx_conversations_session_id ON conversations(session_id);
CREATE INDEX idx_conversations_updated_at ON conversations(updated_at DESC);

-- ============================================================
-- TABLE: messages
-- Stores individual chat messages within conversations
-- ============================================================
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    role VARCHAR(50) NOT NULL CHECK (role IN ('system', 'user', 'assistant')),
    content TEXT NOT NULL,
    keywords JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Foreign Keys
    CONSTRAINT fk_messages_conversation_id 
        FOREIGN KEY (conversation_id) 
        REFERENCES conversations(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_messages_conversation_id ON messages(conversation_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_role ON messages(role);
-- GIN index for JSONB keyword search
CREATE INDEX idx_messages_keywords ON messages USING GIN (keywords);

-- ============================================================
-- TABLE: goals
-- Stores user goals for tracking and motivation
-- ============================================================
CREATE TABLE goals (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    target_date TIMESTAMPTZ,
    status VARCHAR(50) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'abandoned')),
    streak_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    -- Foreign Keys
    CONSTRAINT fk_goals_user_id 
        FOREIGN KEY (user_id) 
        REFERENCES users(id) 
        ON DELETE CASCADE,
        
    -- Constraints
    CONSTRAINT goals_streak_count_non_negative CHECK (streak_count >= 0)
);

CREATE INDEX idx_goals_user_id ON goals(user_id);
CREATE INDEX idx_goals_status ON goals(status);
CREATE INDEX idx_goals_target_date ON goals(target_date);
CREATE INDEX idx_goals_created_at ON goals(created_at DESC);

-- ============================================================
-- TABLE: goal_check_ins
-- Stores daily/periodic check-ins for goal tracking
-- ============================================================
CREATE TABLE goal_check_ins (
    id SERIAL PRIMARY KEY,
    goal_id INTEGER NOT NULL,
    check_in_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    progress_note TEXT,
    completed BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Foreign Keys
    CONSTRAINT fk_goal_check_ins_goal_id 
        FOREIGN KEY (goal_id) 
        REFERENCES goals(id) 
        ON DELETE CASCADE
);

CREATE INDEX idx_goal_check_ins_goal_id ON goal_check_ins(goal_id);
CREATE INDEX idx_goal_check_ins_date ON goal_check_ins(check_in_date DESC);
CREATE INDEX idx_goal_check_ins_completed ON goal_check_ins(completed);

-- ============================================================
-- TRIGGERS: Auto-update updated_at timestamps
-- ============================================================

-- Function to update updated_at column
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger for conversations table
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for goals table
CREATE TRIGGER update_goals_updated_at
    BEFORE UPDATE ON goals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- COMMENTS: Add documentation to tables and columns
-- ============================================================

COMMENT ON TABLE users IS 'User authentication and profile information';
COMMENT ON COLUMN users.email IS 'Unique user email address';
COMMENT ON COLUMN users.hashed_password IS 'Bcrypt hashed password';

COMMENT ON TABLE conversations IS 'Chat conversation sessions between user and AI';
COMMENT ON COLUMN conversations.session_id IS 'Unique session identifier for API reference';

COMMENT ON TABLE messages IS 'Individual messages within a conversation';
COMMENT ON COLUMN messages.role IS 'Message sender role: system, user, or assistant';
COMMENT ON COLUMN messages.keywords IS 'Extracted keywords for search and analytics (JSONB)';

COMMENT ON TABLE goals IS 'User goals for tracking and motivation';
COMMENT ON COLUMN goals.streak_count IS 'Number of consecutive days goal has been maintained';

COMMENT ON TABLE goal_check_ins IS 'Daily or periodic check-ins for goal progress tracking';
