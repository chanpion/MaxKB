-- MaxKB FastAPI Backend — Complete DDL
-- Target: maxkb_test on PostgreSQL + pgvector
-- Execute: psql -h HOST -p PORT -U USER -d maxkb_test -f schema.sql

CREATE EXTENSION IF NOT EXISTS vector;

-- ============================================================================
-- User & Auth
-- ============================================================================

CREATE TABLE IF NOT EXISTS "user" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            UUID PRIMARY KEY,
    email         VARCHAR(254) UNIQUE,
    phone         VARCHAR(20) DEFAULT '' NOT NULL,
    nick_name     VARCHAR(150) UNIQUE DEFAULT '' NOT NULL,
    username      VARCHAR(150) UNIQUE DEFAULT '' NOT NULL,
    password      VARCHAR(150) DEFAULT '' NOT NULL,
    role          VARCHAR(150) DEFAULT '' NOT NULL,
    source        VARCHAR(10) DEFAULT 'LOCAL' NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE NOT NULL,
    language      VARCHAR(10)
);
CREATE INDEX IF NOT EXISTS ix_user_username ON "user" (username);
CREATE INDEX IF NOT EXISTS ix_user_email ON "user" (email);
CREATE INDEX IF NOT EXISTS ix_user_is_active ON "user" (is_active);

CREATE TABLE IF NOT EXISTS "chat_user" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            UUID PRIMARY KEY,
    email         VARCHAR(254),
    phone         VARCHAR(20) DEFAULT '' NOT NULL,
    nick_name     VARCHAR(150) UNIQUE DEFAULT '' NOT NULL,
    username      VARCHAR(150) UNIQUE DEFAULT '' NOT NULL,
    password      VARCHAR(150) DEFAULT '' NOT NULL,
    source        VARCHAR(10) DEFAULT 'LOCAL' NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_chat_user_username ON chat_user (username);
CREATE INDEX IF NOT EXISTS ix_chat_user_email ON chat_user (email);
CREATE INDEX IF NOT EXISTS ix_chat_user_is_active ON chat_user (is_active);

-- ============================================================================
-- Model Provider
-- ============================================================================

CREATE TABLE IF NOT EXISTS "model" (
    create_time        TIMESTAMP WITHOUT TIME ZONE,
    update_time        TIMESTAMP WITHOUT TIME ZONE,
    id                 UUID PRIMARY KEY,
    name               VARCHAR(128) DEFAULT '' NOT NULL,
    status             VARCHAR(20) DEFAULT 'SUCCESS' NOT NULL,
    model_type         VARCHAR(128) DEFAULT '' NOT NULL,
    model_name         VARCHAR(128) DEFAULT '' NOT NULL,
    user_id            UUID,
    provider           VARCHAR(128) DEFAULT '' NOT NULL,
    credential         VARCHAR(102400) DEFAULT '' NOT NULL,
    meta               JSONB DEFAULT '{}' NOT NULL,
    model_params_form  JSONB DEFAULT '[]' NOT NULL,
    workspace_id       VARCHAR(64) DEFAULT 'default' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_model_name ON model (name);
CREATE INDEX IF NOT EXISTS ix_model_status ON model (status);
CREATE INDEX IF NOT EXISTS ix_model_model_type ON model (model_type);
CREATE INDEX IF NOT EXISTS ix_model_model_name ON model (model_name);
CREATE INDEX IF NOT EXISTS ix_model_provider ON model (provider);
CREATE INDEX IF NOT EXISTS ix_model_workspace_id ON model (workspace_id);


-- ============================================================================
-- Application
-- ============================================================================

CREATE TABLE IF NOT EXISTS "application_folder" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            VARCHAR(64) PRIMARY KEY,
    name          VARCHAR(64) DEFAULT '' NOT NULL,
    "desc"        VARCHAR(200),
    user_id       UUID,
    workspace_id  VARCHAR(64) DEFAULT 'default' NOT NULL,
    parent_id     VARCHAR(64),
    tree_id       INTEGER DEFAULT 0 NOT NULL,
    level         INTEGER DEFAULT 0 NOT NULL,
    lft           INTEGER DEFAULT 0 NOT NULL,
    rght          INTEGER DEFAULT 0 NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_application_folder_name ON application_folder (name);
CREATE INDEX IF NOT EXISTS ix_application_folder_workspace_id ON application_folder (workspace_id);

CREATE TABLE IF NOT EXISTS "application" (
    create_time                    TIMESTAMP WITHOUT TIME ZONE,
    update_time                    TIMESTAMP WITHOUT TIME ZONE,
    id                             UUID PRIMARY KEY,
    workspace_id                   VARCHAR(64) DEFAULT 'default' NOT NULL,
    folder_id                      VARCHAR(64) DEFAULT 'default' NOT NULL,
    is_publish                     BOOLEAN DEFAULT FALSE NOT NULL,
    name                           VARCHAR(128) DEFAULT '' NOT NULL,
    "desc"                         VARCHAR(512) DEFAULT '' NOT NULL,
    prologue                       VARCHAR(40960) DEFAULT '' NOT NULL,
    dialogue_number                INTEGER DEFAULT 0 NOT NULL,
    user_id                        UUID,
    model_id                       UUID,
    knowledge_setting              JSONB DEFAULT '{}' NOT NULL,
    model_setting                  JSONB DEFAULT '{}' NOT NULL,
    model_params_setting           JSONB DEFAULT '{}' NOT NULL,
    tts_model_params_setting       JSONB DEFAULT '{}' NOT NULL,
    stt_model_params_setting       JSONB DEFAULT '{}' NOT NULL,
    problem_optimization           BOOLEAN DEFAULT FALSE NOT NULL,
    icon                           VARCHAR(256) DEFAULT './favicon.ico' NOT NULL,
    work_flow                      JSONB DEFAULT '{}' NOT NULL,
    type                           VARCHAR(256) DEFAULT 'SIMPLE' NOT NULL,
    problem_optimization_prompt    VARCHAR(102400),
    tts_model_id                   UUID,
    stt_model_id                   UUID,
    tts_model_enable               BOOLEAN DEFAULT FALSE NOT NULL,
    stt_model_enable               BOOLEAN DEFAULT FALSE NOT NULL,
    tts_type                       VARCHAR(20) DEFAULT 'BROWSER' NOT NULL,
    tts_autoplay                   BOOLEAN DEFAULT FALSE NOT NULL,
    stt_autosend                   BOOLEAN DEFAULT FALSE NOT NULL,
    clean_time                     INTEGER DEFAULT 180 NOT NULL,
    publish_time                   TIMESTAMP WITHOUT TIME ZONE,
    file_upload_enable             BOOLEAN DEFAULT FALSE NOT NULL,
    file_upload_setting            JSONB DEFAULT '{}' NOT NULL,
    mcp_enable                     BOOLEAN DEFAULT FALSE NOT NULL,
    mcp_tool_ids                   JSONB DEFAULT '[]' NOT NULL,
    mcp_servers                    JSONB DEFAULT '{}' NOT NULL,
    mcp_source                     VARCHAR(20) DEFAULT 'referencing' NOT NULL,
    tool_enable                    BOOLEAN DEFAULT FALSE NOT NULL,
    tool_ids                       JSONB DEFAULT '[]' NOT NULL,
    application_enable             BOOLEAN DEFAULT FALSE NOT NULL,
    application_ids                JSONB DEFAULT '[]' NOT NULL,
    skill_tool_ids                 JSONB DEFAULT '[]' NOT NULL,
    mcp_output_enable              BOOLEAN DEFAULT TRUE NOT NULL,
    file_clean_time                INTEGER DEFAULT 180 NOT NULL,
    long_term_enable               BOOLEAN DEFAULT FALSE NOT NULL,
    long_term_model_id             UUID,
    long_term_model_params_setting JSONB DEFAULT '{}' NOT NULL,
    long_term_trigger_type         VARCHAR(20) DEFAULT 'ROUND' NOT NULL,
    long_term_trigger_setting      JSONB DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_application_name ON application (name);
CREATE INDEX IF NOT EXISTS ix_application_workspace_id ON application (workspace_id);

CREATE TABLE IF NOT EXISTS "application_knowledge_mapping" (
    create_time     TIMESTAMP WITHOUT TIME ZONE,
    update_time     TIMESTAMP WITHOUT TIME ZONE,
    id              UUID PRIMARY KEY,
    application_id  UUID NOT NULL,
    knowledge_id    UUID NOT NULL
);

CREATE TABLE IF NOT EXISTS "application_version" (
    create_time                    TIMESTAMP WITHOUT TIME ZONE,
    update_time                    TIMESTAMP WITHOUT TIME ZONE,
    id                             UUID PRIMARY KEY,
    application_id                 UUID NOT NULL,
    name                           VARCHAR(128) DEFAULT '' NOT NULL,
    "desc"                         VARCHAR(512) DEFAULT '' NOT NULL,
    publish_user_id                UUID,
    publish_user_name              VARCHAR(128) DEFAULT '' NOT NULL,
    prologue                       VARCHAR(40960) DEFAULT '' NOT NULL,
    dialogue_number                INTEGER DEFAULT 0 NOT NULL,
    user_id                        UUID,
    model_id                       UUID,
    knowledge_setting              JSONB DEFAULT '{}' NOT NULL,
    model_setting                  JSONB DEFAULT '{}' NOT NULL,
    model_params_setting           JSONB DEFAULT '{}' NOT NULL,
    tts_model_params_setting       JSONB DEFAULT '{}' NOT NULL,
    stt_model_params_setting       JSONB DEFAULT '{}' NOT NULL,
    problem_optimization           BOOLEAN DEFAULT FALSE NOT NULL,
    icon                           VARCHAR(256) DEFAULT './favicon.ico' NOT NULL,
    work_flow                      JSONB DEFAULT '{}' NOT NULL,
    type                           VARCHAR(256) DEFAULT 'SIMPLE' NOT NULL,
    problem_optimization_prompt    VARCHAR(102400),
    tts_model_id                   UUID,
    stt_model_id                   UUID,
    tts_model_enable               BOOLEAN DEFAULT FALSE NOT NULL,
    stt_model_enable               BOOLEAN DEFAULT FALSE NOT NULL,
    tts_type                       VARCHAR(20) DEFAULT 'BROWSER' NOT NULL,
    tts_autoplay                   BOOLEAN DEFAULT FALSE NOT NULL,
    stt_autosend                   BOOLEAN DEFAULT FALSE NOT NULL,
    clean_time                     INTEGER DEFAULT 180 NOT NULL,
    file_upload_enable             BOOLEAN DEFAULT FALSE NOT NULL,
    file_upload_setting            JSONB DEFAULT '{}' NOT NULL,
    mcp_enable                     BOOLEAN DEFAULT FALSE NOT NULL,
    mcp_tool_ids                   JSONB DEFAULT '[]' NOT NULL,
    mcp_servers                    JSONB DEFAULT '{}' NOT NULL,
    mcp_source                     VARCHAR(20) DEFAULT 'referencing' NOT NULL,
    tool_enable                    BOOLEAN DEFAULT FALSE NOT NULL,
    tool_ids                       JSONB DEFAULT '[]' NOT NULL,
    application_enable             BOOLEAN DEFAULT FALSE NOT NULL,
    application_ids                JSONB DEFAULT '[]' NOT NULL,
    skill_tool_ids                 JSONB DEFAULT '[]' NOT NULL,
    mcp_output_enable              BOOLEAN DEFAULT TRUE NOT NULL,
    long_term_enable               BOOLEAN DEFAULT FALSE NOT NULL,
    long_term_model_id             UUID,
    long_term_model_params_setting JSONB DEFAULT '{}' NOT NULL,
    long_term_trigger_type         VARCHAR(20) DEFAULT 'ROUND' NOT NULL,
    long_term_trigger_setting      JSONB DEFAULT '{}' NOT NULL
);

CREATE TABLE IF NOT EXISTS "application_chat" (
    create_time       TIMESTAMP WITHOUT TIME ZONE,
    update_time       TIMESTAMP WITHOUT TIME ZONE,
    id                UUID PRIMARY KEY,
    application_id    UUID NOT NULL,
    abstract          VARCHAR(1024) DEFAULT '' NOT NULL,
    chat_user_id      VARCHAR(128),
    chat_user_type    VARCHAR(64) DEFAULT 'ANONYMOUS_USER' NOT NULL,
    is_deleted        BOOLEAN DEFAULT FALSE NOT NULL,
    asker             JSONB DEFAULT '{"username":"游客"}' NOT NULL,
    meta              JSONB DEFAULT '{}' NOT NULL,
    star_num          INTEGER DEFAULT 0 NOT NULL,
    trample_num       INTEGER DEFAULT 0 NOT NULL,
    chat_record_count INTEGER DEFAULT 0 NOT NULL,
    mark_sum          INTEGER DEFAULT 0 NOT NULL,
    source            JSONB DEFAULT '{}' NOT NULL,
    ip_address        VARCHAR(128) DEFAULT '' NOT NULL
);

CREATE TABLE IF NOT EXISTS "application_chat_record" (
    create_time               TIMESTAMP WITHOUT TIME ZONE,
    update_time               TIMESTAMP WITHOUT TIME ZONE,
    id                        UUID PRIMARY KEY,
    chat_id                   UUID NOT NULL,
    vote_status               VARCHAR(10) DEFAULT '-1' NOT NULL,
    vote_reason               VARCHAR(50),
    vote_other_content        VARCHAR(1024) DEFAULT '' NOT NULL,
    problem_text              VARCHAR(10240) DEFAULT '' NOT NULL,
    answer_text               VARCHAR(40960) DEFAULT '' NOT NULL,
    answer_text_list          JSONB[] DEFAULT '{}' NOT NULL,
    message_tokens            INTEGER DEFAULT 0 NOT NULL,
    answer_tokens             INTEGER DEFAULT 0 NOT NULL,
    const                     INTEGER DEFAULT 0 NOT NULL,
    details                   JSONB DEFAULT '{}' NOT NULL,
    improve_paragraph_id_list UUID[] DEFAULT '{}' NOT NULL,
    run_time                  DOUBLE PRECISION DEFAULT 0.0 NOT NULL,
    index                     INTEGER NOT NULL,
    source                    JSONB DEFAULT '{}' NOT NULL,
    ip_address                VARCHAR(128) DEFAULT '' NOT NULL
);

CREATE TABLE IF NOT EXISTS "application_chat_share_link" (
    create_time      TIMESTAMP WITHOUT TIME ZONE,
    update_time      TIMESTAMP WITHOUT TIME ZONE,
    id               UUID PRIMARY KEY,
    chat_id          UUID NOT NULL,
    application_id   UUID NOT NULL,
    share_type       VARCHAR(20) DEFAULT 'PUBLIC' NOT NULL,
    user_id          UUID,
    chat_record_ids  UUID[] DEFAULT '{}' NOT NULL
);

CREATE TABLE IF NOT EXISTS "application_chat_user_stats" (
    create_time          TIMESTAMP WITHOUT TIME ZONE,
    update_time          TIMESTAMP WITHOUT TIME ZONE,
    id                   UUID PRIMARY KEY,
    chat_user_id         UUID NOT NULL,
    chat_user_type       VARCHAR(64) DEFAULT 'ANONYMOUS_USER' NOT NULL,
    application_id       UUID NOT NULL,
    access_num           INTEGER DEFAULT 0 NOT NULL,
    intraday_access_num  INTEGER DEFAULT 0 NOT NULL
);

CREATE TABLE IF NOT EXISTS "application_long_term_memory" (
    create_time     TIMESTAMP WITHOUT TIME ZONE,
    update_time     TIMESTAMP WITHOUT TIME ZONE,
    id              UUID PRIMARY KEY,
    application_id  UUID NOT NULL,
    chat_user_id    VARCHAR(128) DEFAULT '' NOT NULL,
    memory          TEXT DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_application_long_term_memory_chat_user_id ON application_long_term_memory (chat_user_id);

CREATE TABLE IF NOT EXISTS "application_access_token" (
    create_time          TIMESTAMP WITHOUT TIME ZONE,
    update_time          TIMESTAMP WITHOUT TIME ZONE,
    application_id       UUID PRIMARY KEY,
    access_token         VARCHAR(128) UNIQUE DEFAULT '' NOT NULL,
    is_active            BOOLEAN DEFAULT TRUE NOT NULL,
    access_num           INTEGER DEFAULT 100 NOT NULL,
    white_active         BOOLEAN DEFAULT FALSE NOT NULL,
    white_list           UUID[] DEFAULT '{}' NOT NULL,
    show_source          BOOLEAN DEFAULT FALSE NOT NULL,
    show_exec            BOOLEAN DEFAULT FALSE NOT NULL,
    authentication       BOOLEAN DEFAULT FALSE NOT NULL,
    authentication_value JSONB DEFAULT '{}' NOT NULL,
    language             VARCHAR(10)
);

CREATE TABLE IF NOT EXISTS "application_api_key" (
    create_time        TIMESTAMP WITHOUT TIME ZONE,
    update_time        TIMESTAMP WITHOUT TIME ZONE,
    id                 UUID PRIMARY KEY,
    secret_key         VARCHAR(1024) UNIQUE DEFAULT '' NOT NULL,
    workspace_id       VARCHAR(64) DEFAULT 'default' NOT NULL,
    application_id     UUID NOT NULL,
    is_active          BOOLEAN DEFAULT TRUE NOT NULL,
    allow_cross_domain BOOLEAN DEFAULT FALSE NOT NULL,
    cross_domain_list  UUID[] DEFAULT '{}' NOT NULL,
    expire_time        TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    is_permanent       BOOLEAN DEFAULT TRUE NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_application_api_key_workspace_id ON application_api_key (workspace_id);


-- ============================================================================
-- Knowledge
-- ============================================================================

CREATE TABLE IF NOT EXISTS "knowledge_folder" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            VARCHAR(64) PRIMARY KEY,
    name          VARCHAR(64) DEFAULT '' NOT NULL,
    "desc"        VARCHAR(200),
    user_id       UUID,
    workspace_id  VARCHAR(64) DEFAULT 'default' NOT NULL,
    parent_id     VARCHAR(64),
    tree_id       INTEGER DEFAULT 0 NOT NULL,
    level         INTEGER DEFAULT 0 NOT NULL,
    lft           INTEGER DEFAULT 0 NOT NULL,
    rght          INTEGER DEFAULT 0 NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_knowledge_folder_name ON knowledge_folder (name);
CREATE INDEX IF NOT EXISTS ix_knowledge_folder_workspace_id ON knowledge_folder (workspace_id);

CREATE TABLE IF NOT EXISTS "knowledge" (
    create_time        TIMESTAMP WITHOUT TIME ZONE,
    update_time        TIMESTAMP WITHOUT TIME ZONE,
    id                 UUID PRIMARY KEY,
    name               VARCHAR(150) DEFAULT '' NOT NULL,
    workspace_id       VARCHAR(64) DEFAULT 'default' NOT NULL,
    "desc"             VARCHAR(256) DEFAULT '' NOT NULL,
    user_id            UUID,
    type               INTEGER DEFAULT 0 NOT NULL,
    scope              VARCHAR(20) DEFAULT 'WORKSPACE' NOT NULL,
    folder_id          VARCHAR(64) DEFAULT 'default' NOT NULL,
    embedding_model_id UUID,
    file_size_limit    INTEGER DEFAULT 100 NOT NULL,
    file_count_limit   INTEGER DEFAULT 50 NOT NULL,
    meta               JSONB DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_knowledge_name ON knowledge (name);
CREATE INDEX IF NOT EXISTS ix_knowledge_workspace_id ON knowledge (workspace_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_type ON knowledge (type);
CREATE INDEX IF NOT EXISTS ix_knowledge_scope ON knowledge (scope);

CREATE TABLE IF NOT EXISTS "knowledge_workflow" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            UUID PRIMARY KEY,
    knowledge_id  UUID NOT NULL,
    workspace_id  VARCHAR(64) DEFAULT 'default' NOT NULL,
    work_flow     JSONB DEFAULT '{}' NOT NULL,
    is_publish    BOOLEAN DEFAULT FALSE NOT NULL,
    publish_time  TIMESTAMP WITHOUT TIME ZONE
);
CREATE INDEX IF NOT EXISTS ix_knowledge_workflow_workspace_id ON knowledge_workflow (workspace_id);
CREATE INDEX IF NOT EXISTS ix_knowledge_workflow_is_publish ON knowledge_workflow (is_publish);

CREATE TABLE IF NOT EXISTS "knowledge_workflow_version" (
    create_time       TIMESTAMP WITHOUT TIME ZONE,
    update_time       TIMESTAMP WITHOUT TIME ZONE,
    id                UUID PRIMARY KEY,
    knowledge_id      UUID NOT NULL,
    workspace_id      VARCHAR(64) DEFAULT 'default' NOT NULL,
    name              VARCHAR(128) DEFAULT '' NOT NULL,
    work_flow         JSONB DEFAULT '{}' NOT NULL,
    publish_user_id   UUID,
    publish_user_name VARCHAR(128) DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_knowledge_workflow_version_workspace_id ON knowledge_workflow_version (workspace_id);

CREATE TABLE IF NOT EXISTS "document" (
    create_time                TIMESTAMP WITHOUT TIME ZONE,
    update_time                TIMESTAMP WITHOUT TIME ZONE,
    id                         UUID PRIMARY KEY,
    knowledge_id               UUID NOT NULL,
    name                       VARCHAR(150) DEFAULT '' NOT NULL,
    char_length                INTEGER DEFAULT 0 NOT NULL,
    status                     VARCHAR(20) DEFAULT '' NOT NULL,
    status_meta                JSONB DEFAULT '{}' NOT NULL,
    user_id                    UUID,
    is_active                  BOOLEAN DEFAULT TRUE NOT NULL,
    type                       INTEGER DEFAULT 0 NOT NULL,
    hit_handling_method        VARCHAR(20) DEFAULT 'optimization' NOT NULL,
    directly_return_similarity DOUBLE PRECISION DEFAULT 0.9 NOT NULL,
    meta                       JSONB DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_document_name ON document (name);
CREATE INDEX IF NOT EXISTS ix_document_status ON document (status);
CREATE INDEX IF NOT EXISTS ix_document_is_active ON document (is_active);
CREATE INDEX IF NOT EXISTS ix_document_type ON document (type);

CREATE TABLE IF NOT EXISTS "paragraph" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    document_id  UUID NOT NULL,
    knowledge_id UUID NOT NULL,
    content      VARCHAR(102400) DEFAULT '' NOT NULL,
    title        VARCHAR(256) DEFAULT '' NOT NULL,
    status       VARCHAR(20) DEFAULT '' NOT NULL,
    status_meta  JSONB DEFAULT '{}' NOT NULL,
    hit_num      INTEGER DEFAULT 0 NOT NULL,
    is_active    BOOLEAN DEFAULT TRUE NOT NULL,
    position     INTEGER DEFAULT 0 NOT NULL,
    chunks       VARCHAR(256)[] DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_paragraph_title ON paragraph (title);
CREATE INDEX IF NOT EXISTS ix_paragraph_status ON paragraph (status);
CREATE INDEX IF NOT EXISTS ix_paragraph_is_active ON paragraph (is_active);
CREATE INDEX IF NOT EXISTS ix_paragraph_position ON paragraph (position);

CREATE TABLE IF NOT EXISTS "problem" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    knowledge_id UUID NOT NULL,
    content      VARCHAR(256) DEFAULT '' NOT NULL,
    hit_num      INTEGER DEFAULT 0 NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_problem_content ON problem (content);

CREATE TABLE IF NOT EXISTS "problem_paragraph_mapping" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    knowledge_id UUID NOT NULL,
    document_id  UUID NOT NULL,
    problem_id   UUID NOT NULL,
    paragraph_id UUID NOT NULL
);

CREATE TABLE IF NOT EXISTS "tag" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    knowledge_id UUID NOT NULL,
    key          VARCHAR(64) DEFAULT '' NOT NULL,
    value        VARCHAR(128) DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tag_key ON tag (key);
CREATE INDEX IF NOT EXISTS ix_tag_value ON tag (value);

CREATE TABLE IF NOT EXISTS "document_tag" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    id          UUID PRIMARY KEY,
    document_id UUID NOT NULL,
    tag_id      UUID NOT NULL
);

CREATE TABLE IF NOT EXISTS "termbase" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    knowledge_id UUID NOT NULL,
    content      VARCHAR(256) DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_termbase_content ON termbase (content);

CREATE TABLE IF NOT EXISTS "embedding" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            VARCHAR(128) PRIMARY KEY,
    source_id     VARCHAR(128) DEFAULT '' NOT NULL,
    source_type   VARCHAR(5) DEFAULT '0' NOT NULL,
    is_active     BOOLEAN DEFAULT TRUE NOT NULL,
    knowledge_id  UUID NOT NULL,
    document_id   UUID NOT NULL,
    paragraph_id  UUID NOT NULL,
    embedding     vector(1536),
    search_vector tsvector,
    meta          JSONB DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_embedding_source_id ON embedding (source_id);
CREATE INDEX IF NOT EXISTS ix_embedding_source_type ON embedding (source_type);

CREATE TABLE IF NOT EXISTS "file" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    id          UUID PRIMARY KEY,
    file_name   VARCHAR(256) DEFAULT '' NOT NULL,
    file_size   INTEGER DEFAULT 0 NOT NULL,
    sha256_hash VARCHAR(256) DEFAULT '' NOT NULL,
    source_type VARCHAR(256) DEFAULT 'TEMPORARY_120_MINUTE' NOT NULL,
    source_id   VARCHAR(256) DEFAULT 'TEMPORARY_120_MINUTE' NOT NULL,
    loid        INTEGER DEFAULT 0 NOT NULL,
    meta        JSONB DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_file_source_type ON file (source_type);
CREATE INDEX IF NOT EXISTS ix_file_source_id ON file (source_id);


-- ============================================================================
-- Tools
-- ============================================================================

CREATE TABLE IF NOT EXISTS "tool_folder" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           VARCHAR(64) PRIMARY KEY,
    name         VARCHAR(64) DEFAULT '' NOT NULL,
    "desc"       VARCHAR(200),
    user_id      UUID,
    workspace_id VARCHAR(64) DEFAULT 'default' NOT NULL,
    parent_id    VARCHAR(64),
    tree_id      INTEGER DEFAULT 0 NOT NULL,
    level        INTEGER DEFAULT 0 NOT NULL,
    lft          INTEGER DEFAULT 0 NOT NULL,
    rght         INTEGER DEFAULT 0 NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tool_folder_name ON tool_folder (name);
CREATE INDEX IF NOT EXISTS ix_tool_folder_workspace_id ON tool_folder (workspace_id);

CREATE TABLE IF NOT EXISTS "tool" (
    create_time      TIMESTAMP WITHOUT TIME ZONE,
    update_time      TIMESTAMP WITHOUT TIME ZONE,
    id               UUID PRIMARY KEY,
    user_id          UUID,
    name             VARCHAR(64) DEFAULT '' NOT NULL,
    "desc"           VARCHAR(128) DEFAULT '' NOT NULL,
    code             VARCHAR(102400) DEFAULT '' NOT NULL,
    input_field_list JSONB DEFAULT '[]' NOT NULL,
    init_field_list  JSONB DEFAULT '[]' NOT NULL,
    icon             VARCHAR(256) DEFAULT '' NOT NULL,
    is_active        BOOLEAN DEFAULT TRUE NOT NULL,
    scope            VARCHAR(20) DEFAULT 'WORKSPACE' NOT NULL,
    tool_type        VARCHAR(20) DEFAULT 'CUSTOM' NOT NULL,
    template_id      VARCHAR(128),
    folder_id        VARCHAR(64) DEFAULT 'default' NOT NULL,
    workspace_id     VARCHAR(64) DEFAULT 'default' NOT NULL,
    init_params      VARCHAR(102400),
    label            VARCHAR(128),
    version          VARCHAR(64)
);
CREATE INDEX IF NOT EXISTS ix_tool_name ON tool (name);
CREATE INDEX IF NOT EXISTS ix_tool_is_active ON tool (is_active);
CREATE INDEX IF NOT EXISTS ix_tool_scope ON tool (scope);
CREATE INDEX IF NOT EXISTS ix_tool_tool_type ON tool (tool_type);
CREATE INDEX IF NOT EXISTS ix_tool_workspace_id ON tool (workspace_id);
CREATE INDEX IF NOT EXISTS ix_tool_template_id ON tool (template_id);
CREATE INDEX IF NOT EXISTS ix_tool_label ON tool (label);

CREATE TABLE IF NOT EXISTS "tool_record" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    tool_id      UUID,
    workspace_id VARCHAR(64) DEFAULT 'default' NOT NULL,
    source_type  VARCHAR(256) DEFAULT 'APPLICATION' NOT NULL,
    source_id    UUID NOT NULL,
    meta         JSONB DEFAULT '{}' NOT NULL,
    state        VARCHAR(20) DEFAULT '1' NOT NULL,
    run_time     DOUBLE PRECISION DEFAULT 0.0 NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tool_record_workspace_id ON tool_record (workspace_id);

CREATE TABLE IF NOT EXISTS "tool_workflow" (
    create_time  TIMESTAMP WITHOUT TIME ZONE,
    update_time  TIMESTAMP WITHOUT TIME ZONE,
    id           UUID PRIMARY KEY,
    tool_id      UUID NOT NULL,
    workspace_id VARCHAR(64) DEFAULT 'default' NOT NULL,
    work_flow    JSONB DEFAULT '{}' NOT NULL,
    is_publish   BOOLEAN DEFAULT FALSE NOT NULL,
    publish_time TIMESTAMP WITHOUT TIME ZONE
);
CREATE INDEX IF NOT EXISTS ix_tool_workflow_workspace_id ON tool_workflow (workspace_id);
CREATE INDEX IF NOT EXISTS ix_tool_workflow_is_publish ON tool_workflow (is_publish);

CREATE TABLE IF NOT EXISTS "tool_workflow_version" (
    create_time       TIMESTAMP WITHOUT TIME ZONE,
    update_time       TIMESTAMP WITHOUT TIME ZONE,
    id                UUID PRIMARY KEY,
    tool_id           UUID NOT NULL,
    workspace_id      VARCHAR(64) DEFAULT 'default' NOT NULL,
    name              VARCHAR(128) DEFAULT '' NOT NULL,
    work_flow         JSONB DEFAULT '{}' NOT NULL,
    publish_user_id   UUID,
    publish_user_name VARCHAR(128) DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_tool_workflow_version_workspace_id ON tool_workflow_version (workspace_id);


-- ============================================================================
-- Trigger
-- ============================================================================

CREATE TABLE IF NOT EXISTS "event_trigger" (
    create_time     TIMESTAMP WITHOUT TIME ZONE,
    update_time     TIMESTAMP WITHOUT TIME ZONE,
    id              UUID PRIMARY KEY,
    workspace_id    VARCHAR(64) DEFAULT 'default' NOT NULL,
    name            VARCHAR(128) DEFAULT '' NOT NULL,
    "desc"          VARCHAR(512) DEFAULT '' NOT NULL,
    trigger_type    VARCHAR(256) DEFAULT 'SCHEDULED' NOT NULL,
    trigger_setting JSONB DEFAULT '{}' NOT NULL,
    meta            JSONB DEFAULT '{}' NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    user_id         UUID
);
CREATE INDEX IF NOT EXISTS ix_event_trigger_name ON event_trigger (name);
CREATE INDEX IF NOT EXISTS ix_event_trigger_workspace_id ON event_trigger (workspace_id);
CREATE INDEX IF NOT EXISTS ix_event_trigger_is_active ON event_trigger (is_active);

CREATE TABLE IF NOT EXISTS "event_trigger_task" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    id          UUID PRIMARY KEY,
    trigger_id  UUID NOT NULL,
    source_type VARCHAR(256) DEFAULT 'APPLICATION' NOT NULL,
    source_id   UUID NOT NULL,
    is_active   BOOLEAN DEFAULT TRUE NOT NULL,
    parameter   JSONB DEFAULT '[]' NOT NULL,
    meta        JSONB DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_event_trigger_task_is_active ON event_trigger_task (is_active);

CREATE TABLE IF NOT EXISTS "event_trigger_task_record" (
    create_time     TIMESTAMP WITHOUT TIME ZONE,
    update_time     TIMESTAMP WITHOUT TIME ZONE,
    id              UUID PRIMARY KEY,
    trigger_id      UUID NOT NULL,
    trigger_task_id UUID NOT NULL,
    source_type     VARCHAR(256) DEFAULT 'APPLICATION' NOT NULL,
    source_id       UUID NOT NULL,
    task_record_id  UUID NOT NULL,
    meta            JSONB DEFAULT '{}' NOT NULL,
    state           VARCHAR(20) DEFAULT '1' NOT NULL,
    run_time        DOUBLE PRECISION DEFAULT 0.0 NOT NULL
);


-- ============================================================================
-- System
-- ============================================================================

CREATE TABLE IF NOT EXISTS "system_setting" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    type INTEGER PRIMARY KEY DEFAULT 0 NOT NULL,
    meta JSONB DEFAULT '{}' NOT NULL
);

CREATE TABLE IF NOT EXISTS "user_group" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    id          VARCHAR(128) PRIMARY KEY,
    name        VARCHAR(150) UNIQUE DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_user_group_name ON user_group (name);

CREATE TABLE IF NOT EXISTS "user_group_relation" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    id          UUID PRIMARY KEY,
    user_id     UUID NOT NULL,
    group_id    VARCHAR(128) NOT NULL
);

CREATE TABLE IF NOT EXISTS "resource_chat_user_authorize" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            UUID PRIMARY KEY,
    workspace_id  VARCHAR(64),
    user_group_id VARCHAR(128) NOT NULL,
    user_id       UUID NOT NULL,
    resource_id   UUID NOT NULL,
    resource_type VARCHAR NOT NULL,
    is_auth       BOOLEAN NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_resource_chat_user_authorize_resource_id ON resource_chat_user_authorize (resource_id);
CREATE INDEX IF NOT EXISTS ix_resource_chat_user_authorize_resource_type ON resource_chat_user_authorize (resource_type);
CREATE INDEX IF NOT EXISTS ix_resource_chat_user_authorize_workspace_id ON resource_chat_user_authorize (workspace_id);

CREATE TABLE IF NOT EXISTS "resource_chat_user_group_authorize" (
    create_time   TIMESTAMP WITHOUT TIME ZONE,
    update_time   TIMESTAMP WITHOUT TIME ZONE,
    id            UUID PRIMARY KEY,
    workspace_id  VARCHAR(64),
    user_group_id VARCHAR(128) NOT NULL,
    resource_id   UUID NOT NULL,
    resource_type VARCHAR NOT NULL,
    is_auth       BOOLEAN NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_resource_chat_user_group_authorize_resource_id ON resource_chat_user_group_authorize (resource_id);
CREATE INDEX IF NOT EXISTS ix_resource_chat_user_group_authorize_resource_type ON resource_chat_user_group_authorize (resource_type);
CREATE INDEX IF NOT EXISTS ix_resource_chat_user_group_authorize_workspace_id ON resource_chat_user_group_authorize (workspace_id);

CREATE TABLE IF NOT EXISTS "log" (
    create_time       TIMESTAMP WITHOUT TIME ZONE,
    update_time       TIMESTAMP WITHOUT TIME ZONE,
    id                UUID PRIMARY KEY,
    menu              VARCHAR(128) DEFAULT '' NOT NULL,
    operate           VARCHAR(128) DEFAULT '' NOT NULL,
    operation_object  JSONB DEFAULT '{}' NOT NULL,
    "user"            JSONB DEFAULT '{}' NOT NULL,
    status            INTEGER DEFAULT 0 NOT NULL,
    ip_address        VARCHAR(128) DEFAULT '' NOT NULL,
    details           JSONB DEFAULT '{}' NOT NULL,
    workspace_id      VARCHAR(64) DEFAULT 'default' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_log_operate ON log (operate);
CREATE INDEX IF NOT EXISTS ix_log_status ON log (status);
CREATE INDEX IF NOT EXISTS ix_log_workspace_id ON log (workspace_id);

CREATE TABLE IF NOT EXISTS "resource_mapping" (
    create_time TIMESTAMP WITHOUT TIME ZONE,
    update_time TIMESTAMP WITHOUT TIME ZONE,
    id          UUID PRIMARY KEY,
    source_type VARCHAR NOT NULL,
    target_type VARCHAR NOT NULL,
    source_id   VARCHAR(128) DEFAULT '' NOT NULL,
    target_id   VARCHAR(128) DEFAULT '' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_resource_mapping_source_type ON resource_mapping (source_type);
CREATE INDEX IF NOT EXISTS ix_resource_mapping_target_type ON resource_mapping (target_type);
CREATE INDEX IF NOT EXISTS ix_resource_mapping_source_id ON resource_mapping (source_id);
CREATE INDEX IF NOT EXISTS ix_resource_mapping_target_id ON resource_mapping (target_id);

CREATE TABLE IF NOT EXISTS "workspace_user_resource_permission" (
    create_time      TIMESTAMP WITHOUT TIME ZONE,
    update_time      TIMESTAMP WITHOUT TIME ZONE,
    id               UUID PRIMARY KEY,
    workspace_id     VARCHAR(128) DEFAULT 'default' NOT NULL,
    user_id          UUID NOT NULL,
    auth_target_type VARCHAR(128) DEFAULT '' NOT NULL,
    target           VARCHAR(128) DEFAULT '' NOT NULL,
    auth_type        VARCHAR(128) DEFAULT 'ROLE' NOT NULL,
    permission_list  VARCHAR(256)[] DEFAULT '{}' NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_workspace_user_resource_permission_workspace_id ON workspace_user_resource_permission (workspace_id);
CREATE INDEX IF NOT EXISTS ix_workspace_user_resource_permission_auth_target_type ON workspace_user_resource_permission (auth_target_type);
CREATE INDEX IF NOT EXISTS ix_workspace_user_resource_permission_target ON workspace_user_resource_permission (target);
CREATE INDEX IF NOT EXISTS ix_workspace_user_resource_permission_auth_type ON workspace_user_resource_permission (auth_type);
