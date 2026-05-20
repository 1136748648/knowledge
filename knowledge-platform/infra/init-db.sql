-- 启用必要的扩展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "ltree";

-- Wiki 文档表
CREATE TABLE wiki_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    slug VARCHAR(500) UNIQUE NOT NULL,
    parent_id UUID REFERENCES wiki_pages(id) ON DELETE SET NULL,
    acl JSONB DEFAULT '{}',
    sensitivity VARCHAR(20) DEFAULT 'public' CHECK (sensitivity IN ('public', 'internal', 'confidential', 'secret')),
    dept_id VARCHAR(50),
    created_by VARCHAR(100) NOT NULL,
    updated_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wiki_pages_slug ON wiki_pages(slug);
CREATE INDEX idx_wiki_pages_parent ON wiki_pages(parent_id);
CREATE INDEX idx_wiki_pages_dept ON wiki_pages(dept_id);
CREATE INDEX idx_wiki_pages_sensitivity ON wiki_pages(sensitivity);

-- Wiki 页面版本历史
CREATE TABLE wiki_page_versions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    page_id UUID NOT NULL REFERENCES wiki_pages(id) ON DELETE CASCADE,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    version INT NOT NULL,
    edited_by VARCHAR(100) NOT NULL,
    edit_summary VARCHAR(500),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_wiki_versions_page ON wiki_page_versions(page_id);

-- 员工档案表
CREATE TABLE employees (
    employee_id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department VARCHAR(100),
    level VARCHAR(20),
    hire_date DATE,
    manager_id VARCHAR(50) REFERENCES employees(employee_id) ON DELETE SET NULL,
    email VARCHAR(200),
    phone VARCHAR(50),
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'on_leave', 'resigned')),
    clearance_level INT DEFAULT 1 CHECK (clearance_level BETWEEN 1 AND 5),
    dept_id VARCHAR(50),
    salary NUMERIC(12, 2),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_employees_dept ON employees(department);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_employees_status ON employees(status);

-- 会话问答记录
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id VARCHAR(100) NOT NULL,
    dept_id VARCHAR(50),
    question TEXT NOT NULL,
    answer TEXT NOT NULL,
    source_refs JSONB DEFAULT '[]',
    embedding_id VARCHAR(100),
    sensitivity VARCHAR(20) DEFAULT 'public' CHECK (sensitivity IN ('public', 'internal', 'confidential', 'secret')),
    feedback INT CHECK (feedback BETWEEN -1 AND 1),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_conversations_user ON conversations(user_id);
CREATE INDEX idx_conversations_dept ON conversations(dept_id);
CREATE INDEX idx_conversations_created ON conversations(created_at DESC);

-- 知识导航树
CREATE TABLE knowledge_nav (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(200) NOT NULL,
    parent_id UUID REFERENCES knowledge_nav(id) ON DELETE CASCADE,
    path LTREE,
    icon VARCHAR(50),
    description TEXT,
    sort_order INT DEFAULT 0,
    visibility_roles TEXT[] DEFAULT '{}',
    created_by VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_nav_parent ON knowledge_nav(parent_id);
CREATE INDEX idx_nav_path ON knowledge_nav USING GIST(path);

-- 导航节点与内容关联
CREATE TABLE nav_content_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    nav_id UUID NOT NULL REFERENCES knowledge_nav(id) ON DELETE CASCADE,
    content_type VARCHAR(20) NOT NULL CHECK (content_type IN ('wiki', 'conversation', 'external')),
    content_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_nav_links_nav ON nav_content_links(nav_id);
CREATE INDEX idx_nav_links_content ON nav_content_links(content_type, content_id);

-- Casbin 策略表
CREATE TABLE casbin_rule (
    id SERIAL PRIMARY KEY,
    ptype VARCHAR(100) NOT NULL,
    v0 VARCHAR(100),
    v1 VARCHAR(100),
    v2 VARCHAR(100),
    v3 VARCHAR(100),
    v4 VARCHAR(100),
    v5 VARCHAR(100)
);

CREATE INDEX idx_casbin_ptype ON casbin_rule(ptype);

-- 操作审计日志
CREATE TABLE audit_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id VARCHAR(100) NOT NULL,
    user_roles TEXT[],
    action VARCHAR(50) NOT NULL,
    resource_type VARCHAR(50),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    user_agent TEXT,
    status_code INT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_user ON audit_logs(user_id);
CREATE INDEX idx_audit_action ON audit_logs(action);
CREATE INDEX idx_audit_created ON audit_logs(created_at DESC);

-- 本地用户表（初始认证，后续可对接 Keycloak）
CREATE TABLE local_users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(200) NOT NULL,
    email VARCHAR(200) DEFAULT '',
    roles TEXT[] DEFAULT '{employee}',
    dept_id VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_local_users_username ON local_users(username);

-- 系统配置表
CREATE TABLE system_config (
    id SERIAL PRIMARY KEY,
    category VARCHAR(50) NOT NULL,
    key VARCHAR(200) NOT NULL,
    value TEXT,
    value_type VARCHAR(20) DEFAULT 'string',
    description VARCHAR(500),
    is_sensitive BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(category, key)
);

CREATE INDEX idx_config_category ON system_config(category);
CREATE INDEX idx_config_category_key ON system_config(category, key);

-- 预设知识导航类目
INSERT INTO knowledge_nav (id, name, path, icon, sort_order, visibility_roles) VALUES
    ('a0000000-0000-0000-0000-000000000001', '企业资料', 'enterprise', 'building', 1, '{}'),
    ('a0000000-0000-0000-0000-000000000002', '工作制度', 'policy', 'document', 2, '{}'),
    ('a0000000-0000-0000-0000-000000000003', '项目资料', 'project', 'folder', 3, '{}'),
    ('a0000000-0000-0000-0000-000000000004', '客户资料', 'customer', 'user', 4, '{manager,hr}'),
    ('a0000000-0000-0000-0000-000000000005', '销售资料', 'sales', 'chart', 5, '{manager,sales}'),
    ('a0000000-0000-0000-0000-000000000006', '运维资料', 'ops', 'server', 6, '{manager,ops}'),
    ('a0000000-0000-0000-0000-000000000007', '研发资料', 'dev', 'code', 7, '{manager,dev}'),
    ('a0000000-0000-0000-0000-000000000008', '软件工具', 'tools', 'tools', 8, '{}');

-- 预设 Casbin 策略
INSERT INTO casbin_rule (ptype, v0, v1, v2, v3) VALUES
    ('p', 'employee', 'employees', 'read', 'own'),
    ('p', 'employee', 'wiki', 'read', 'public'),
    ('p', 'employee', 'wiki', 'read', 'internal'),
    ('p', 'employee', 'conversation', 'read', 'own'),
    ('p', 'manager', 'employees', 'read', 'department'),
    ('p', 'manager', 'wiki', 'read', 'all'),
    ('p', 'manager', 'conversation', 'read', 'department'),
    ('p', 'hr', 'employees', 'read', 'all'),
    ('p', 'hr', 'employees', 'write', 'all'),
    ('p', 'hr', 'wiki', 'read', 'all'),
    ('p', 'hr', 'wiki', 'write', 'all'),
    ('p', 'admin', 'all', 'all', 'all');
