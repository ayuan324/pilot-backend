-- πlot Database Schema for Supabase
-- This file contains all the necessary tables, indexes, and RLS policies

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ====================================
-- Core Tables
-- ====================================

-- Workflows table
CREATE TABLE IF NOT EXISTS workflows (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    user_id TEXT NOT NULL, -- Clerk user ID
    workflow_data JSONB NOT NULL DEFAULT '{}',
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'published', 'archived')),
    version INTEGER DEFAULT 1,
    is_public BOOLEAN DEFAULT FALSE,
    tags TEXT[] DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_executed_at TIMESTAMP WITH TIME ZONE,
    execution_count INTEGER DEFAULT 0,

    -- Constraints
    CONSTRAINT workflows_name_length CHECK (LENGTH(name) >= 1 AND LENGTH(name) <= 255),
    CONSTRAINT workflows_description_length CHECK (LENGTH(description) <= 1000)
);

-- Workflow executions table
CREATE TABLE IF NOT EXISTS workflow_executions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    workflow_id UUID NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
    user_id TEXT NOT NULL,
    input_data JSONB DEFAULT '{}',
    output_data JSONB,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled', 'paused')),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    total_tokens_used INTEGER DEFAULT 0,
    total_cost DECIMAL(10, 6) DEFAULT 0.00,
    execution_context JSONB DEFAULT '{}',
    progress DECIMAL(3, 2) DEFAULT 0.00 CHECK (progress >= 0.00 AND progress <= 1.00),
    current_node_id VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    -- Computed duration in milliseconds
    duration_ms INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN started_at IS NOT NULL AND completed_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER * 1000
            ELSE NULL
        END
    ) STORED
);

-- Node execution logs table
CREATE TABLE IF NOT EXISTS node_execution_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    node_id VARCHAR(255) NOT NULL,
    node_type VARCHAR(100) NOT NULL,
    node_name VARCHAR(255),
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed', 'skipped')),
    input_data JSONB DEFAULT '{}',
    output_data JSONB DEFAULT '{}',
    error_message TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0.00,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,

    -- Computed execution time in milliseconds
    execution_time_ms INTEGER GENERATED ALWAYS AS (
        CASE
            WHEN started_at IS NOT NULL AND completed_at IS NOT NULL
            THEN EXTRACT(EPOCH FROM (completed_at - started_at))::INTEGER * 1000
            ELSE NULL
        END
    ) STORED
);

-- Execution events table (for real-time tracking)
CREATE TABLE IF NOT EXISTS execution_events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    execution_id UUID NOT NULL REFERENCES workflow_executions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL CHECK (event_type IN (
        'workflow_started', 'workflow_completed', 'workflow_failed', 'workflow_cancelled',
        'node_started', 'node_completed', 'node_failed', 'node_skipped',
        'variable_updated', 'log_message', 'progress_update'
    )),
    node_id VARCHAR(255),
    message TEXT,
    data JSONB DEFAULT '{}',
    error_message TEXT,
    progress DECIMAL(3, 2) CHECK (progress >= 0.00 AND progress <= 1.00),
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow templates table (system-defined templates)
CREATE TABLE IF NOT EXISTS workflow_templates (
    id VARCHAR(100) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100) NOT NULL,
    difficulty VARCHAR(20) DEFAULT 'beginner' CHECK (difficulty IN ('beginner', 'intermediate', 'advanced')),
    estimated_time VARCHAR(50),
    template_data JSONB NOT NULL,
    preview_image TEXT,
    tags TEXT[] DEFAULT '{}',
    is_active BOOLEAN DEFAULT TRUE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- User workflow stats (for analytics)
CREATE TABLE IF NOT EXISTS user_workflow_stats (
    user_id TEXT PRIMARY KEY,
    total_workflows INTEGER DEFAULT 0,
    total_executions INTEGER DEFAULT 0,
    successful_executions INTEGER DEFAULT 0,
    failed_executions INTEGER DEFAULT 0,
    total_tokens_used BIGINT DEFAULT 0,
    total_cost DECIMAL(10, 2) DEFAULT 0.00,
    last_activity_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ====================================
-- Indexes for Performance
-- ====================================

-- Workflows indexes
CREATE INDEX IF NOT EXISTS idx_workflows_user_id ON workflows(user_id);
CREATE INDEX IF NOT EXISTS idx_workflows_status ON workflows(status);
CREATE INDEX IF NOT EXISTS idx_workflows_is_public ON workflows(is_public);
CREATE INDEX IF NOT EXISTS idx_workflows_created_at ON workflows(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_updated_at ON workflows(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_workflows_name_trgm ON workflows USING gin(name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_workflows_description_trgm ON workflows USING gin(description gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_workflows_tags ON workflows USING gin(tags);

-- Workflow executions indexes
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON workflow_executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_user_id ON workflow_executions(user_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON workflow_executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_created_at ON workflow_executions(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_executions_user_workflow ON workflow_executions(user_id, workflow_id);

-- Node execution logs indexes
CREATE INDEX IF NOT EXISTS idx_node_logs_execution_id ON node_execution_logs(execution_id);
CREATE INDEX IF NOT EXISTS idx_node_logs_node_id ON node_execution_logs(node_id);
CREATE INDEX IF NOT EXISTS idx_node_logs_status ON node_execution_logs(status);

-- Execution events indexes
CREATE INDEX IF NOT EXISTS idx_events_execution_id ON execution_events(execution_id);
CREATE INDEX IF NOT EXISTS idx_events_type ON execution_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_timestamp ON execution_events(timestamp DESC);

-- Templates indexes
CREATE INDEX IF NOT EXISTS idx_templates_category ON workflow_templates(category);
CREATE INDEX IF NOT EXISTS idx_templates_difficulty ON workflow_templates(difficulty);
CREATE INDEX IF NOT EXISTS idx_templates_is_active ON workflow_templates(is_active);

-- ====================================
-- Row Level Security (RLS) Policies
-- ====================================

-- Enable RLS on all tables
ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;
ALTER TABLE workflow_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE node_execution_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE execution_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_workflow_stats ENABLE ROW LEVEL SECURITY;

-- Workflows policies
CREATE POLICY "Users can view their own workflows and public workflows" ON workflows
    FOR SELECT USING (
        user_id = auth.jwt() ->> 'sub' OR is_public = true
    );

CREATE POLICY "Users can create their own workflows" ON workflows
    FOR INSERT WITH CHECK (user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can update their own workflows" ON workflows
    FOR UPDATE USING (user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can delete their own workflows" ON workflows
    FOR DELETE USING (user_id = auth.jwt() ->> 'sub');

-- Workflow executions policies
CREATE POLICY "Users can view their own executions" ON workflow_executions
    FOR SELECT USING (user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can create their own executions" ON workflow_executions
    FOR INSERT WITH CHECK (user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can update their own executions" ON workflow_executions
    FOR UPDATE USING (user_id = auth.jwt() ->> 'sub');

-- Node execution logs policies
CREATE POLICY "Users can view logs for their executions" ON node_execution_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM workflow_executions
            WHERE id = execution_id AND user_id = auth.jwt() ->> 'sub'
        )
    );

CREATE POLICY "Users can create logs for their executions" ON node_execution_logs
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM workflow_executions
            WHERE id = execution_id AND user_id = auth.jwt() ->> 'sub'
        )
    );

-- Execution events policies
CREATE POLICY "Users can view events for their executions" ON execution_events
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM workflow_executions
            WHERE id = execution_id AND user_id = auth.jwt() ->> 'sub'
        )
    );

CREATE POLICY "Users can create events for their executions" ON execution_events
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM workflow_executions
            WHERE id = execution_id AND user_id = auth.jwt() ->> 'sub'
        )
    );

-- User stats policies
CREATE POLICY "Users can view their own stats" ON user_workflow_stats
    FOR SELECT USING (user_id = auth.jwt() ->> 'sub');

CREATE POLICY "Users can update their own stats" ON user_workflow_stats
    FOR ALL USING (user_id = auth.jwt() ->> 'sub');

-- Templates are publicly readable (no RLS needed, but we'll add a policy for clarity)
ALTER TABLE workflow_templates ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Templates are publicly readable" ON workflow_templates
    FOR SELECT USING (is_active = true);

-- ====================================
-- Functions and Triggers
-- ====================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at
CREATE TRIGGER update_workflows_updated_at
    BEFORE UPDATE ON workflows
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_executions_updated_at
    BEFORE UPDATE ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_templates_updated_at
    BEFORE UPDATE ON workflow_templates
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_stats_updated_at
    BEFORE UPDATE ON user_workflow_stats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to update workflow execution count
CREATE OR REPLACE FUNCTION update_workflow_execution_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE workflows
        SET execution_count = execution_count + 1,
            last_executed_at = NOW()
        WHERE id = NEW.workflow_id;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for workflow execution count
CREATE TRIGGER trigger_update_workflow_execution_count
    AFTER INSERT ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_workflow_execution_count();

-- Function to update user stats
CREATE OR REPLACE FUNCTION update_user_stats()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO user_workflow_stats (user_id, total_executions, last_activity_at)
        VALUES (NEW.user_id, 1, NOW())
        ON CONFLICT (user_id) DO UPDATE SET
            total_executions = user_workflow_stats.total_executions + 1,
            last_activity_at = NOW();
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' AND OLD.status != NEW.status THEN
        IF NEW.status = 'completed' THEN
            UPDATE user_workflow_stats SET
                successful_executions = successful_executions + 1,
                total_tokens_used = total_tokens_used + COALESCE(NEW.total_tokens_used, 0),
                total_cost = total_cost + COALESCE(NEW.total_cost, 0),
                last_activity_at = NOW()
            WHERE user_id = NEW.user_id;
        ELSIF NEW.status = 'failed' THEN
            UPDATE user_workflow_stats SET
                failed_executions = failed_executions + 1,
                last_activity_at = NOW()
            WHERE user_id = NEW.user_id;
        END IF;
        RETURN NEW;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Trigger for user stats
CREATE TRIGGER trigger_update_user_stats
    AFTER INSERT OR UPDATE ON workflow_executions
    FOR EACH ROW EXECUTE FUNCTION update_user_stats();

-- Function to clean up old execution events (optional, for data retention)
CREATE OR REPLACE FUNCTION cleanup_old_execution_events()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM execution_events
    WHERE timestamp < NOW() - INTERVAL '30 days';
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ====================================
-- Views for Analytics
-- ====================================

-- Workflow execution summary view
CREATE OR REPLACE VIEW workflow_execution_summary AS
SELECT
    w.id as workflow_id,
    w.name as workflow_name,
    w.user_id,
    COUNT(we.id) as total_executions,
    COUNT(CASE WHEN we.status = 'completed' THEN 1 END) as successful_executions,
    COUNT(CASE WHEN we.status = 'failed' THEN 1 END) as failed_executions,
    ROUND(
        COUNT(CASE WHEN we.status = 'completed' THEN 1 END)::DECIMAL /
        NULLIF(COUNT(we.id), 0) * 100, 2
    ) as success_rate_percent,
    AVG(we.duration_ms) as avg_duration_ms,
    SUM(we.total_tokens_used) as total_tokens_used,
    SUM(we.total_cost) as total_cost,
    MAX(we.created_at) as last_execution_at
FROM workflows w
LEFT JOIN workflow_executions we ON w.id = we.workflow_id
GROUP BY w.id, w.name, w.user_id;

-- User analytics view
CREATE OR REPLACE VIEW user_analytics AS
SELECT
    uws.user_id,
    uws.total_workflows,
    uws.total_executions,
    uws.successful_executions,
    uws.failed_executions,
    ROUND(
        uws.successful_executions::DECIMAL /
        NULLIF(uws.total_executions, 0) * 100, 2
    ) as success_rate_percent,
    uws.total_tokens_used,
    uws.total_cost,
    uws.last_activity_at,
    COUNT(DISTINCT w.id) as public_workflows_count
FROM user_workflow_stats uws
LEFT JOIN workflows w ON w.user_id = uws.user_id AND w.is_public = true
GROUP BY uws.user_id, uws.total_workflows, uws.total_executions,
         uws.successful_executions, uws.failed_executions,
         uws.total_tokens_used, uws.total_cost, uws.last_activity_at;

-- ====================================
-- Seed Data - Default Templates
-- ====================================

INSERT INTO workflow_templates (id, name, description, category, difficulty, estimated_time, template_data, tags) VALUES
(
    'simple_chatbot',
    'Simple Chatbot',
    'A basic chatbot that responds to user messages using AI',
    'conversational',
    'beginner',
    '2 minutes',
    '{
        "name": "Simple Chatbot",
        "description": "Basic conversational AI workflow",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "User Input"},
                "inputs": [],
                "outputs": [{"id": "output", "label": "User Message"}]
            },
            {
                "id": "llm",
                "type": "llm",
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "AI Response",
                    "model": "gpt-3.5-turbo",
                    "temperature": 0.7,
                    "prompt_template": "You are a helpful assistant. Respond to the user message: {input}"
                },
                "inputs": [{"id": "input", "label": "Input"}],
                "outputs": [{"id": "output", "label": "Response"}]
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 500, "y": 100},
                "config": {"name": "Bot Response"},
                "inputs": [{"id": "input", "label": "Response"}],
                "outputs": []
            }
        ],
        "edges": [
            {"source": "start", "target": "llm", "source_handle": "output", "target_handle": "input"},
            {"source": "llm", "target": "output", "source_handle": "output", "target_handle": "input"}
        ],
        "variables": [
            {"name": "input", "type": "string", "is_input": true},
            {"name": "output", "type": "string", "is_output": true}
        ]
    }',
    ARRAY['chatbot', 'conversational', 'beginner']
),
(
    'content_generator',
    'Content Generator',
    'Generate blog posts or articles from a topic using AI',
    'content',
    'intermediate',
    '5 minutes',
    '{
        "name": "Content Generator",
        "description": "AI-powered content generation workflow",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "Topic Input"},
                "outputs": [{"id": "output", "label": "Topic"}]
            },
            {
                "id": "outline",
                "type": "llm",
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "Generate Outline",
                    "model": "gpt-3.5-turbo",
                    "prompt_template": "Create a detailed outline for an article about: {input}"
                }
            },
            {
                "id": "content",
                "type": "llm",
                "position": {"x": 500, "y": 100},
                "config": {
                    "name": "Write Content",
                    "model": "gpt-4",
                    "prompt_template": "Write a comprehensive article based on this outline: {outline}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 700, "y": 100},
                "config": {"name": "Final Article"}
            }
        ],
        "edges": [
            {"source": "start", "target": "outline"},
            {"source": "outline", "target": "content"},
            {"source": "content", "target": "output"}
        ]
    }',
    ARRAY['content', 'writing', 'articles', 'intermediate']
),
(
    'data_analyzer',
    'Data Analyzer',
    'Analyze data and generate insights using AI',
    'analysis',
    'advanced',
    '8 minutes',
    '{
        "name": "Data Analyzer",
        "description": "AI-powered data analysis workflow",
        "nodes": [
            {
                "id": "start",
                "type": "start",
                "position": {"x": 100, "y": 100},
                "config": {"name": "Data Input"}
            },
            {
                "id": "preprocess",
                "type": "code",
                "position": {"x": 300, "y": 100},
                "config": {
                    "name": "Preprocess Data",
                    "language": "python",
                    "code": "# Clean and preprocess the data\nimport pandas as pd\ndata = pd.DataFrame(input_data)\nprocessed_data = data.dropna()\nreturn processed_data.to_dict()"
                }
            },
            {
                "id": "analyze",
                "type": "llm",
                "position": {"x": 500, "y": 100},
                "config": {
                    "name": "Generate Insights",
                    "model": "gpt-4",
                    "prompt_template": "Analyze this data and provide insights: {preprocessed_data}"
                }
            },
            {
                "id": "output",
                "type": "output",
                "position": {"x": 700, "y": 100},
                "config": {"name": "Analysis Report"}
            }
        ],
        "edges": [
            {"source": "start", "target": "preprocess"},
            {"source": "preprocess", "target": "analyze"},
            {"source": "analyze", "target": "output"}
        ]
    }',
    ARRAY['analysis', 'data', 'insights', 'advanced']
)
ON CONFLICT (id) DO NOTHING;

-- Create helpful comments
COMMENT ON TABLE workflows IS 'User-created AI workflows with nodes and connections';
COMMENT ON TABLE workflow_executions IS 'Individual execution instances of workflows';
COMMENT ON TABLE node_execution_logs IS 'Detailed logs for each node execution';
COMMENT ON TABLE execution_events IS 'Real-time events during workflow execution';
COMMENT ON TABLE workflow_templates IS 'Pre-built workflow templates for quick start';
COMMENT ON TABLE user_workflow_stats IS 'Aggregated statistics for user activity';

-- Grant necessary permissions (adjust based on your setup)
-- GRANT ALL ON ALL TABLES IN SCHEMA public TO authenticated;
-- GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO authenticated;
