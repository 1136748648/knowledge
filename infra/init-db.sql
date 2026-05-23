-- 知识平台数据库初始化脚本
-- PostgreSQL 15+

-- 扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "ltree";

-- Wiki页面表
CREATE TABLE IF NOT EXISTS wiki_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    parent_id UUID REFERENCES wiki_pages(id),
    acl JSONB DEFAULT '{}',
    sensitivity VARCHAR(20) DEFAULT 'public',
    dept_id VARCHAR(50),
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wiki_pages_slug ON wiki_pages(slug);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_parent_id ON wiki_pages(parent_id);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_sensitivity ON wiki_pages(sensitivity);
CREATE INDEX IF NOT EXISTS idx_wiki_pages_dept_id ON wiki_pages(dept_id);

-- Wiki版本历史表
CREATE TABLE IF NOT EXISTS wiki_page_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    version INTEGER NOT NULL,
    edited_by VARCHAR(100) NOT NULL,
    edit_summary VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_wiki_versions_page_id ON wiki_page_versions(page_id);
CREATE INDEX IF NOT EXISTS idx_wiki_versions_page_version ON wiki_page_versions(page_id, version);

-- 员工档案表
CREATE TABLE IF NOT EXISTS employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    level VARCHAR(20),
    hire_date DATE,
    manager_id VARCHAR(50) REFERENCES employees(employee_id),
    email VARCHAR(200),
    phone VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active',
    clearance_level INTEGER DEFAULT 1,
    dept_id VARCHAR(50),
    salary NUMERIC(12, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_employees_department ON employees(department);
CREATE INDEX IF NOT EXISTS idx_employees_dept_id ON employees(dept_id);
CREATE INDEX IF NOT EXISTS idx_employees_manager_id ON employees(manager_id);

-- 会话问答记录表
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    dept_id VARCHAR(50),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source_refs JSONB DEFAULT '[]',
    embedding_id VARCHAR(100),
    sensitivity VARCHAR(20) DEFAULT 'public',
    feedback INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_conversations_user_id ON conversations(user_id);
CREATE INDEX IF NOT EXISTS idx_conversations_dept_id ON conversations(dept_id);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at);

-- 知识导航树表
CREATE TABLE IF NOT EXISTS knowledge_nav (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    parent_id UUID REFERENCES knowledge_nav(id) ON DELETE CASCADE,
    path VARCHAR(500),
    icon VARCHAR(50),
    description TEXT,
    sort_order INTEGER DEFAULT 0,
    visibility_roles TEXT[],
    created_by VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_knowledge_nav_parent_id ON knowledge_nav(parent_id);
CREATE INDEX IF NOT EXISTS idx_knowledge_nav_path ON knowledge_nav(path);

-- 导航节点与内容关联表
CREATE TABLE IF NOT EXISTS nav_content_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nav_id UUID NOT NULL REFERENCES knowledge_nav(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL,
    content_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_nav_content_links_nav_id ON nav_content_links(nav_id);
CREATE INDEX IF NOT EXISTS idx_nav_content_links_content ON nav_content_links(content_type, content_id);

-- Casbin策略表
CREATE TABLE IF NOT EXISTS casbin_rule (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ptype VARCHAR(100) NOT NULL,
    v0 VARCHAR(100),
    v1 VARCHAR(100),
    v2 VARCHAR(100),
    v3 VARCHAR(100),
    v4 VARCHAR(100),
    v5 VARCHAR(100)
);

-- 审计日志表
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT PRIMARY KEY AUTOINCREMENT,
    user_id VARCHAR(100) NOT NULL,
    user_roles TEXT[],
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    status_code INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);

-- 本地用户表
CREATE TABLE IF NOT EXISTS local_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    email VARCHAR(200) DEFAULT '',
    roles TEXT[] DEFAULT '{}',
    dept_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_local_users_username ON local_users(username);
CREATE INDEX IF NOT EXISTS idx_local_users_dept_id ON local_users(dept_id);

-- 系统配置表
CREATE TABLE IF NOT EXISTS system_config (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(200) NOT NULL,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    description VARCHAR(500),
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_system_config_category_key ON system_config(category, key);

-- 搜索事件表
CREATE TABLE IF NOT EXISTS search_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_text VARCHAR(500) NOT NULL,
    query_embedding TEXT,
    user_id VARCHAR(128),
    dept_id VARCHAR(64),
    hit_doc_ids TEXT[],
    hit_scores FLOAT[],
    filter_conditions JSONB,
    search_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_search_events_created_at ON search_events(created_at);
CREATE INDEX IF NOT EXISTS idx_search_events_user_id ON search_events(user_id);

-- 热力图统计表
CREATE TABLE IF NOT EXISTS heatmap_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stat_type VARCHAR(20) NOT NULL,
    stat_key VARCHAR(500) NOT NULL,
    stat_date DATE NOT NULL,
    count INTEGER DEFAULT 0,
    unique_users INTEGER DEFAULT 0,
    avg_duration_ms FLOAT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_heatmap_stats_type_date ON heatmap_stats(stat_type, stat_date);
CREATE UNIQUE INDEX IF NOT EXISTS idx_heatmap_stats_unique ON heatmap_stats(stat_type, stat_key, stat_date);

-- 链路追踪会话表
CREATE TABLE IF NOT EXISTS trace_sessions (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL UNIQUE,
    request_id VARCHAR(32) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    username VARCHAR(128),
    endpoint VARCHAR(256),
    method VARCHAR(16),
    question TEXT,
    intent VARCHAR(32),
    status VARCHAR(16) DEFAULT 'running',
    total_spans INTEGER DEFAULT 0,
    total_events INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms FLOAT,
    result_summary TEXT,
    output_preview TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_trace_user_time ON trace_sessions(user_id, start_time);
CREATE INDEX IF NOT EXISTS idx_trace_status_time ON trace_sessions(status, start_time);

-- 链路追踪Span表
CREATE TABLE IF NOT EXISTS trace_spans (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    span_id VARCHAR(32) NOT NULL,
    parent_span_id VARCHAR(32),
    session_id VARCHAR(64) NOT NULL,
    agent_id VARCHAR(64) NOT NULL,
    agent_name VARCHAR(128),
    action VARCHAR(64),
    input_summary JSON,
    output_summary JSON,
    status VARCHAR(16) DEFAULT 'running',
    error_message TEXT,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    duration_ms FLOAT,
    confidence FLOAT,
    sources_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_span_session FOREIGN KEY (session_id) REFERENCES trace_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_span_parent FOREIGN KEY (parent_span_id) REFERENCES trace_spans(span_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_span_trace_id ON trace_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_span_session_agent ON trace_spans(session_id, agent_id);

-- 链路追踪事件表
CREATE TABLE IF NOT EXISTS trace_events (
    id VARCHAR(64) PRIMARY KEY,
    trace_id VARCHAR(32) NOT NULL,
    span_id VARCHAR(32) NOT NULL,
    event_type VARCHAR(32) NOT NULL,
    event_name VARCHAR(128),
    data JSON,
    message TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_event_span FOREIGN KEY (span_id) REFERENCES trace_spans(span_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_event_trace_id ON trace_events(trace_id);

-- 链路追踪统计表
CREATE TABLE IF NOT EXISTS trace_stats (
    id VARCHAR(64) PRIMARY KEY,
    user_id VARCHAR(64) NOT NULL,
    stat_date TIMESTAMP NOT NULL,
    total_requests INTEGER DEFAULT 0,
    success_requests INTEGER DEFAULT 0,
    failed_requests INTEGER DEFAULT 0,
    total_duration_ms FLOAT DEFAULT 0,
    avg_duration_ms FLOAT DEFAULT 0,
    p95_duration_ms FLOAT DEFAULT 0,
    agent_usage JSON,
    intent_distribution JSON,
    error_types JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_stats_user_date ON trace_stats(user_id, stat_date);

-- 初始化数据
INSERT INTO system_config (category, key, value, description) VALUES
('system', 'version', '0.1.0', '系统版本'),
('system', 'name', 'Knowledge Platform', '系统名称'),
('security', 'session_timeout', '3600', '会话超时时间（秒）');

INSERT INTO casbin_rule (ptype, v0, v1, v2) VALUES
('p', 'admin', 'wiki', 'read'),
('p', 'admin', 'wiki', 'write'),
('p', 'admin', 'wiki', 'delete'),
('p', 'admin', 'employee', 'read'),
('p', 'admin', 'employee', 'write'),
('p', 'hr', 'employee', 'read'),
('p', 'hr', 'wiki', 'read'),
('p', 'hr', 'wiki', 'write'),
('p', 'manager', 'wiki', 'read'),
('p', 'manager', 'employee', 'read'),
('p', 'user', 'wiki', 'read');

INSERT INTO casbin_rule (ptype, v0, v1) VALUES
('g', 'admin', 'admin'),
('g', 'hr_user', 'hr'),
('g', 'manager_user', 'manager'),
('g', 'normal_user', 'user');
