-- ============================================================================
-- AI Coding Agent - Unified Database Schema (PostgreSQL 16 + pgvector)
-- ============================================================================

-- 1. Enable Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "vector";

-- 2. Workspaces Table
CREATE TABLE IF NOT EXISTS workspaces (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    root_path TEXT NOT NULL,
    default_branch VARCHAR(64) DEFAULT 'main',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. Code Chunks & AST Vectors Table
CREATE TABLE IF NOT EXISTS code_chunks (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    language VARCHAR(64) NOT NULL,
    symbol_name VARCHAR(255),
    symbol_type VARCHAR(64), -- 'function', 'class', 'method', 'type', 'block'
    start_line INTEGER NOT NULL,
    end_line INTEGER NOT NULL,
    content TEXT NOT NULL,
    checksum VARCHAR(64) NOT NULL, -- SHA256 checksum for incremental indexing
    embedding vector(1536),        -- 1536-dimensional vector for OpenAI / Gemini / Nomic embeddings
    metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- HNSW Vector Index for High Performance Similarity Queries (<10ms)
CREATE INDEX IF NOT EXISTS idx_code_chunks_embedding_hnsw 
ON code_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

CREATE INDEX IF NOT EXISTS idx_code_chunks_lookup 
ON code_chunks (workspace_id, file_path);

CREATE INDEX IF NOT EXISTS idx_code_chunks_symbol 
ON code_chunks (symbol_name);

-- 4. Agent Chat & Task Sessions Table
CREATE TABLE IF NOT EXISTS agent_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workspace_id UUID REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(255) DEFAULT 'New Agent Session',
    provider VARCHAR(64) DEFAULT 'openai',
    model_name VARCHAR(128) DEFAULT 'gpt-4o',
    status VARCHAR(32) DEFAULT 'active', -- 'active', 'completed', 'failed'
    active_file TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Session Messages & Tool History Table
CREATE TABLE IF NOT EXISTS agent_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL, -- 'user', 'assistant', 'system', 'tool'
    content TEXT,
    tool_calls JSONB,
    tool_call_id VARCHAR(128),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_agent_messages_session 
ON agent_messages (session_id, created_at ASC);

-- 6. Tool Execution Audit Log Table
CREATE TABLE IF NOT EXISTS tool_execution_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES agent_sessions(id) ON DELETE CASCADE,
    tool_name VARCHAR(128) NOT NULL,
    input_arguments JSONB NOT NULL,
    output_result TEXT,
    execution_time_ms INTEGER,
    status VARCHAR(32) NOT NULL, -- 'success', 'error', 'timeout'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Hybrid Similarity Search Function (pgvector Cosine Distance)
CREATE OR REPLACE FUNCTION match_code_context(
    query_embedding vector(1536),
    match_workspace_id UUID,
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 5
)
RETURNS TABLE (
    id UUID,
    file_path TEXT,
    symbol_name VARCHAR,
    symbol_type VARCHAR,
    start_line INT,
    end_line INT,
    content TEXT,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        cc.id,
        cc.file_path,
        cc.symbol_name,
        cc.symbol_type,
        cc.start_line,
        cc.end_line,
        cc.content,
        1 - (cc.embedding <=> query_embedding) AS similarity
    FROM code_chunks cc
    WHERE (match_workspace_id IS NULL OR cc.workspace_id = match_workspace_id)
      AND 1 - (cc.embedding <=> query_embedding) > match_threshold
    ORDER BY cc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;
