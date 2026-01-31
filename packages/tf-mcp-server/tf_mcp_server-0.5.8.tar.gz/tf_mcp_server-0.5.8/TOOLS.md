# ToothFairyAI MCP Server - Complete Tool Reference

**Version:** 0.5.6 (aligned with ToothFairyAI SDK)

This document provides a comprehensive reference for all tools available in the ToothFairyAI MCP Server. Use this guide to understand what each tool does, its parameters, and when to use it.

---

## Quick Reference

| Category | Tools | Authentication Required |
|----------|-------|------------------------|
| Documentation | 6 | No |
| Release Notes | 4 | No |
| Credential Validation | 1 | Yes |
| Agent Management | 6 | Yes |
| Agent Functions | 5 | Yes |
| Authorisations | 5 | Yes |
| Secrets | 2 | Yes |
| Documents | 6 | Yes |
| Entities | 6 | Yes |
| Folders | 6 | Yes |
| Chats | 5 | Yes |
| Prompts | 5 | Yes |
| Members | 4 | Yes |
| Channels | 5 | Yes |
| Connections | 3 | Yes |
| Benchmarks | 5 | Yes |
| Hooks | 5 | Yes |
| Scheduled Jobs | 5 | Yes |
| Sites | 4 | Yes |
| Dictionary | 2 | Yes |
| Request Logs | 2 | Yes |
| Settings | 4 | Yes |
| Billing | 1 | Yes |
| Embeddings | 1 | Yes |
| **Total** | **98** | |

### Authentication Parameters

All SDK tools (everything except Documentation tools) require these parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | ToothFairyAI API key from Admin > API Integration |
| `workspace_id` | string | Yes | Your workspace UUID |
| `region` | string | No | API region: `"au"` (default), `"eu"`, or `"us"` |

### Response Format

All SDK tools return a consistent response format:

```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

Or on error:

```json
{
  "success": false,
  "error": "Error message description"
}
```

---

## Documentation Tools (No Auth Required)

These tools provide access to ToothFairyAI documentation and API specifications without authentication.

### `search_docs`

Search across all ToothFairyAI documentation.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query string |
| `limit` | int | No | 10 | Maximum number of results |
| `source` | string | No | None | Filter: `"docs"`, `"api"`, or `None` for all |

**Returns:** List of search results with title, uri, snippet, and relevance score.

**Example:**
```python
search_docs(query="agent creation", limit=5, source="docs")
```

---

### `search_api_endpoints`

Search for specific API endpoints across all ToothFairyAI APIs.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (matches path, summary, description, tags) |
| `limit` | int | No | 20 | Maximum number of results |

**Returns:** List of endpoints with method, path, summary, tags, API type, and base domain.

**Example:**
```python
search_api_endpoints(query="create agent", limit=10)
```

---

### `explain_api_domains`

Get detailed explanation of ToothFairyAI API domains and when to use each.

**Parameters:** None

**Returns:** Comprehensive guide explaining Platform API vs AI Services API vs Voice API.

**Example:**
```python
explain_api_domains()
```

---

### `list_doc_categories`

List all available documentation categories.

**Parameters:** None

**Returns:** List of category names (e.g., `["agents", "settings", "guides"]`).

**Example:**
```python
list_doc_categories()
```

---

### `get_doc_by_topic`

Get full documentation content for a specific topic.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `topic` | string | Yes | Topic to find (e.g., "agents", "prompting", "channels") |

**Returns:** Full markdown content of the most relevant document.

**Example:**
```python
get_doc_by_topic("webhooks")
```

---

### `get_agent_creation_guide`

Get the comprehensive guide for creating ToothFairyAI agents.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `section` | string | No | None | Specific section to retrieve |

**Available sections:** `modes`, `core-fields`, `mode-config`, `tools`, `features`, `departments`, `models`, `uploads`, `voice`, `planner`, `validation`, `best-practices`, `examples`, `quick-reference`

**Returns:** Agent creation guide content (full or specific section).

**Example:**
```python
get_agent_creation_guide(section="examples")
```

---

## Release Notes Tools (No Auth Required)

These tools provide access to ToothFairyAI release notes and product updates.

### `list_release_notes`

List all available ToothFairyAI release notes.

**Parameters:** None

**Returns:** List of release notes sorted by version (newest first), with version, release_date, title, summary, and uri.

**Example:**
```python
list_release_notes()
```

---

### `get_latest_release_notes`

Get the most recent ToothFairyAI release notes.

**Parameters:** None

**Returns:** Full markdown content of the latest release notes including all new features, improvements, and fixes.

**Example:**
```python
get_latest_release_notes()
```

---

### `get_release_notes`

Get release notes for a specific version.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `version` | string | Yes | Version number (e.g., "0.668.0", "v0.668.0", or "0.668") |

**Returns:** Full markdown content of the release notes for that version.

**Example:**
```python
get_release_notes(version="0.668.0")
```

---

### `search_release_notes`

Search release notes by keyword or phrase.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search query (e.g., "voice agents", "MCP", "agentic tooling") |
| `limit` | int | No | 10 | Maximum number of results |

**Returns:** List of matching release notes with version, title, snippet, and relevance score.

**Example:**
```python
search_release_notes(query="voice agents", limit=5)
```

---

## Credential Validation

### `validate_toothfairy_credentials`

Validate ToothFairyAI API credentials before performing operations. **Always call this first.**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | ToothFairyAI API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `region` | string | No | `"au"` | API region |

**Returns:** Success/failure status with message.

**Example:**
```python
validate_toothfairy_credentials(
    api_key="your-api-key",
    workspace_id="your-workspace-id",
    region="au"
)
```

---

## Agent Management (6 tools)

### `create_toothfairy_agent`

Create a new AI agent in your workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `label` | string | Yes | - | Human-readable agent name |
| `mode` | string | Yes | - | Agent mode: `"chatter"`, `"retriever"`, `"coder"`, `"planner"`, `"voice"` |
| `interpolation_string` | string | Yes | - | System prompt defining agent personality |
| `goals` | string | Yes | - | High-level objectives for the agent |
| `region` | string | No | `"au"` | API region |
| `temperature` | float | No | 0.3 | Response randomness (0.001-1.0) |
| `max_tokens` | int | No | 4096 | Maximum response length |
| `description` | string | No | None | Brief agent description |
| `agentic_rag` | bool | No | False | Enable multi-step RAG (retriever mode only) |
| `has_code` | bool | No | False | Enable code execution |
| `charting` | bool | No | False | Enable chart generation (retriever mode only) |
| `allow_internet_search` | bool | No | False | Enable web search |

**Returns:** Created agent data.

**Example:**
```python
create_toothfairy_agent(
    api_key="key",
    workspace_id="ws-id",
    label="Research Assistant",
    mode="retriever",
    interpolation_string="You are a helpful research assistant...",
    goals="Help users find and analyze information",
    agentic_rag=True,
    allow_internet_search=True
)
```

---

### `get_toothfairy_agent`

Get details of a specific agent by ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `agent_id` | string | Yes | Agent UUID to retrieve |
| `region` | string | No | API region (default: `"au"`) |

**Returns:** Agent details including configuration, stats, and metadata.

---

### `update_toothfairy_agent`

Update an existing agent's configuration.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `agent_id` | string | Yes | Agent UUID to update |
| `updates` | dict | Yes | Fields to update (e.g., `{"label": "New Name", "temperature": 0.5}`) |
| `region` | string | No | API region (default: `"au"`) |

**Note:** Agent `mode` cannot be changed after creation.

**Returns:** Updated agent data.

---

### `delete_toothfairy_agent`

Delete an agent permanently. **WARNING: Irreversible.**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `agent_id` | string | Yes | Agent UUID to delete |
| `region` | string | No | API region (default: `"au"`) |

**Returns:** Success confirmation.

---

### `list_toothfairy_agents`

List all agents in a workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `region` | string | No | `"au"` | API region |
| `limit` | int | No | 100 | Maximum results |

**Returns:** List of agents with basic info.

---

### `search_toothfairy_agents`

Search agents by label.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `search_term` | string | Yes | Search query for agent labels |
| `region` | string | No | API region (default: `"au"`) |

**Returns:** Matching agents.

---

## Agent Functions (5 tools)

Agent Functions are external API tools that agents can call during conversations.

### `create_toothfairy_function`

Create a new function (external API tool) for agents.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `name` | string | Yes | - | Function name (e.g., `"search_tickets"`) |
| `description` | string | Yes | - | What the function does (AI uses this to decide when to call) |
| `url` | string | Yes | - | Endpoint URL to call |
| `region` | string | No | `"au"` | API region |
| `request_type` | string | No | `"GET"` | HTTP method: `"GET"`, `"POST"`, `"PUT"`, `"PATCH"`, `"DELETE"` |
| `authorisation_type` | string | No | `"none"` | Auth type: `"bearer"`, `"apikey"`, `"none"` |
| `parameters` | list | No | None | Function parameters in OpenAI JSON Schema format |
| `headers` | list | No | None | Custom headers: `[{"name": "X-Custom", "value": "value"}]` |
| `static_args` | list | No | None | Static args always passed: `[{"name": "key", "value": "value"}]` |

**Returns:** Created function data.

---

### `get_toothfairy_function`

Get function details by ID.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `function_id` | string | Yes | Function UUID |
| `region` | string | No | API region (default: `"au"`) |

---

### `update_toothfairy_function`

Update an existing function.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `function_id` | string | Yes | Function UUID |
| `updates` | dict | Yes | Fields to update |
| `region` | string | No | API region (default: `"au"`) |

---

### `delete_toothfairy_function`

Delete a function. **WARNING: Irreversible.**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `function_id` | string | Yes | Function UUID |
| `region` | string | No | API region (default: `"au"`) |

---

### `list_toothfairy_functions`

List all functions in a workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `region` | string | No | `"au"` | API region |
| `limit` | int | No | 100 | Maximum results |

---

## Authorisations (5 tools)

Authorisations store API credentials (keys, tokens, OAuth) for functions.

### `create_toothfairy_authorisation`

Create a new authorisation record.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `name` | string | Yes | - | Human-readable name |
| `auth_type` | string | Yes | - | Type: `"bearer"`, `"apikey"`, `"oauth"`, `"password"`, `"none"` |
| `region` | string | No | `"au"` | API region |
| `description` | string | No | None | Purpose description |
| `token_secret` | string | No | None | Token/secret value (encrypted) |

---

### `get_toothfairy_authorisation`

Get authorisation by ID. Note: Sensitive values may be masked.

---

### `update_toothfairy_authorisation`

Update an authorisation record.

---

### `delete_toothfairy_authorisation`

Delete an authorisation. **WARNING: Irreversible.** Ensure no functions reference it.

---

### `list_toothfairy_authorisations`

List all authorisations in a workspace.

---

## Secrets (2 tools)

Secrets store encrypted sensitive values linked to Authorisations.

### `create_toothfairy_secret`

Create a secret linked to an authorisation.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `authorisation_id` | string | Yes | Authorisation UUID to link |
| `password_secret_value` | string | Yes | Secret value (will be encrypted) |
| `region` | string | No | API region (default: `"au"`) |

---

### `delete_toothfairy_secret`

Delete a secret. **WARNING: Irreversible.**

---

## Documents (6 tools)

Documents are knowledge base entries that agents can search and reference.

### `create_toothfairy_document`

Create a new document in the knowledge base.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `title` | string | Yes | - | Document title |
| `region` | string | No | `"au"` | API region |
| `content` | string | No | None | Document content (markdown supported) |
| `folder_id` | string | No | None | Parent folder UUID |
| `topics` | list | No | None | List of topic IDs to associate |

---

### `get_toothfairy_document`

Get document by ID.

---

### `update_toothfairy_document`

Update a document.

---

### `delete_toothfairy_document`

Delete a document. **WARNING: Irreversible.**

---

### `list_toothfairy_documents`

List documents in a workspace.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `region` | string | No | `"au"` | API region |
| `limit` | int | No | 100 | Maximum results |
| `folder_id` | string | No | None | Filter by folder |

---

### `search_toothfairy_documents`

Search documents by text content.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `text` | string | Yes | - | Search query |
| `region` | string | No | `"au"` | API region |
| `limit` | int | No | 10 | Maximum results |

---

## Entities (6 tools)

Entities are Topics, Intents, or Named Entity Recognition (NER) items.

### `create_toothfairy_entity`

Create a new entity.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `label` | string | Yes | - | Entity name |
| `entity_type` | string | Yes | - | Type: `"topic"`, `"intent"`, `"ner"` |
| `region` | string | No | `"au"` | API region |
| `description` | string | No | None | Entity description |
| `emoji` | string | No | None | Display emoji |

---

### `get_toothfairy_entity`

Get entity by ID.

---

### `update_toothfairy_entity`

Update an entity.

---

### `delete_toothfairy_entity`

Delete an entity. **WARNING: Irreversible.**

---

### `list_toothfairy_entities`

List entities with optional type filter.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `region` | string | No | `"au"` | API region |
| `entity_type` | string | No | None | Filter: `"topic"`, `"intent"`, `"ner"` |
| `limit` | int | No | 100 | Maximum results |

---

### `search_toothfairy_entities`

Search entities by label.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `search_term` | string | Yes | - | Search query |
| `region` | string | No | `"au"` | API region |
| `entity_type` | string | No | None | Filter by type |

---

## Folders (6 tools)

Folders organize documents in the knowledge base.

### `create_toothfairy_folder`

Create a new folder.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `label` | string | Yes | - | Folder name |
| `region` | string | No | `"au"` | API region |
| `parent_id` | string | No | None | Parent folder UUID for nesting |

---

### `get_toothfairy_folder`

Get folder by ID.

---

### `update_toothfairy_folder`

Update a folder.

---

### `delete_toothfairy_folder`

Delete a folder. **WARNING: Irreversible.**

---

### `list_toothfairy_folders`

List all folders.

---

### `get_toothfairy_folder_tree`

Get the complete hierarchical folder tree structure.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `region` | string | No | API region (default: `"au"`) |

---

## Chats (5 tools)

Chats are conversation sessions with agents.

### `create_toothfairy_chat`

Create a new chat session.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `agent_id` | string | Yes | - | Agent UUID for this chat |
| `region` | string | No | `"au"` | API region |
| `title` | string | No | None | Chat session title |

---

### `get_toothfairy_chat`

Get chat session by ID (includes message history).

---

### `delete_toothfairy_chat`

Delete a chat session. **WARNING: Irreversible.**

---

### `list_toothfairy_chats`

List all chat sessions.

---

### `send_toothfairy_message`

Send a message to an agent and get a response.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `agent_id` | string | Yes | - | Agent UUID to message |
| `message` | string | Yes | - | User message content |
| `region` | string | No | `"au"` | API region |
| `chat_id` | string | No | None | Existing chat UUID (creates new if not provided) |

**Returns:** Agent response with message content and metadata.

**Example:**
```python
send_toothfairy_message(
    api_key="key",
    workspace_id="ws-id",
    agent_id="agent-uuid",
    message="What is ToothFairyAI?"
)
```

---

## Prompts (5 tools)

Prompts are reusable text templates with variable interpolation.

### `create_toothfairy_prompt`

Create a new prompt template.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `label` | string | Yes | Prompt name |
| `interpolation_string` | string | Yes | Template text with `{{variables}}` |
| `region` | string | No | API region (default: `"au"`) |

---

### `get_toothfairy_prompt`

Get prompt by ID.

---

### `update_toothfairy_prompt`

Update a prompt template.

---

### `delete_toothfairy_prompt`

Delete a prompt. **WARNING: Irreversible.**

---

### `list_toothfairy_prompts`

List all prompt templates.

---

## Members (4 tools)

Members are users in a workspace.

### `get_toothfairy_member`

Get member by ID.

---

### `update_toothfairy_member`

Update member details (role, permissions, etc.).

---

### `delete_toothfairy_member`

Remove a member from workspace. **WARNING: Irreversible.**

---

### `list_toothfairy_members`

List all workspace members.

---

## Channels (5 tools)

Channels are communication integrations (Slack, Teams, WhatsApp, etc.).

### `create_toothfairy_channel`

Create a new channel integration.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `name` | string | Yes | Channel display name |
| `channel` | string | Yes | Channel type (e.g., `"slack"`, `"teams"`) |
| `provider` | string | Yes | Provider identifier |
| `region` | string | No | API region (default: `"au"`) |

---

### `get_toothfairy_channel`

Get channel by ID.

---

### `update_toothfairy_channel`

Update channel configuration.

---

### `delete_toothfairy_channel`

Delete a channel. **WARNING: Irreversible.**

---

### `list_toothfairy_channels`

List all channels.

---

## Connections (3 tools)

Connections are database connections for data querying.

### `get_toothfairy_connection`

Get database connection by ID.

---

### `delete_toothfairy_connection`

Delete a connection. **WARNING: Irreversible.**

---

### `list_toothfairy_connections`

List all database connections.

---

## Benchmarks (5 tools)

Benchmarks are test suites for evaluating agent performance.

### `create_toothfairy_benchmark`

Create a new benchmark.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `name` | string | Yes | - | Benchmark name |
| `region` | string | No | `"au"` | API region |
| `description` | string | No | None | Benchmark description |
| `questions` | list | No | None | Test questions with expected answers |

---

### `get_toothfairy_benchmark`

Get benchmark by ID.

---

### `update_toothfairy_benchmark`

Update a benchmark.

---

### `delete_toothfairy_benchmark`

Delete a benchmark. **WARNING: Irreversible.**

---

### `list_toothfairy_benchmarks`

List all benchmarks.

---

## Hooks (5 tools)

Hooks execute custom code during agent workflows.

### `create_toothfairy_hook`

Create a new hook.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `name` | string | Yes | - | Hook name |
| `function_name` | string | Yes | - | Entry point function name |
| `region` | string | No | `"au"` | API region |
| `custom_execution_code` | string | No | None | Custom JavaScript/Python code |

---

### `get_toothfairy_hook`

Get hook by ID.

---

### `update_toothfairy_hook`

Update a hook.

---

### `delete_toothfairy_hook`

Delete a hook. **WARNING: Irreversible.**

---

### `list_toothfairy_hooks`

List all hooks.

---

## Scheduled Jobs (5 tools)

Scheduled Jobs automate recurring agent tasks.

### `create_toothfairy_scheduled_job`

Create a new scheduled job.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `name` | string | Yes | Job name |
| `agent_id` | string | Yes | Agent UUID to run |
| `schedule` | dict | Yes | Schedule configuration (cron-like) |
| `region` | string | No | API region (default: `"au"`) |

---

### `get_toothfairy_scheduled_job`

Get scheduled job by ID.

---

### `update_toothfairy_scheduled_job`

Update a scheduled job.

---

### `delete_toothfairy_scheduled_job`

Delete a scheduled job. **WARNING: Irreversible.**

---

### `list_toothfairy_scheduled_jobs`

List all scheduled jobs.

---

## Sites (4 tools)

Sites are web deployments or embedded chat widgets.

### `get_toothfairy_site`

Get site by ID.

---

### `update_toothfairy_site`

Update site configuration.

---

### `delete_toothfairy_site`

Delete a site. **WARNING: Irreversible.**

---

### `list_toothfairy_sites`

List all sites.

---

## Dictionary (2 tools)

Dictionary entries define custom terminology and definitions.

### `get_toothfairy_dictionary_entry`

Get dictionary entry by ID.

---

### `list_toothfairy_dictionary_entries`

List all dictionary entries.

---

## Request Logs (2 tools)

Request logs track API usage and agent interactions.

### `get_toothfairy_request_log`

Get request log by ID.

---

### `list_toothfairy_request_logs`

List all request logs.

---

## Settings (4 tools)

Workspace-level configuration settings.

### `get_toothfairy_charting_settings`

Get charting/visualization settings.

---

### `update_toothfairy_charting_settings`

Update charting settings.

---

### `get_toothfairy_embeddings_settings`

Get embeddings model settings.

---

### `update_toothfairy_embeddings_settings`

Update embeddings settings.

---

## Billing (1 tool)

### `get_toothfairy_month_costs`

Get monthly usage costs and intelligence budget consumption.

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `api_key` | string | Yes | - | API key |
| `workspace_id` | string | Yes | - | Workspace UUID |
| `region` | string | No | `"au"` | API region |
| `year` | int | No | Current | Year to query |
| `month` | int | No | Current | Month to query (1-12) |

---

## Embeddings (1 tool)

### `create_toothfairy_embedding`

Generate text embeddings for semantic search.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `api_key` | string | Yes | API key |
| `workspace_id` | string | Yes | Workspace UUID |
| `text` | string | Yes | Text to embed |
| `region` | string | No | API region (default: `"au"`) |

**Returns:** Vector embedding array.

---

## Common Workflows

### 1. Creating Your First Agent

```python
# Step 1: Validate credentials
validate_toothfairy_credentials(api_key="...", workspace_id="...", region="au")

# Step 2: Read the agent creation guide
get_agent_creation_guide(section="examples")

# Step 3: Create the agent
create_toothfairy_agent(
    api_key="...",
    workspace_id="...",
    label="Customer Support Agent",
    mode="retriever",
    interpolation_string="You are a helpful customer support agent for Acme Corp...",
    goals="Answer customer questions accurately using the knowledge base.",
    agentic_rag=True,
    temperature=0.3
)
```

### 2. Setting Up Knowledge Base

```python
# Create folder structure
create_toothfairy_folder(api_key="...", workspace_id="...", label="Product Docs")

# Add documents
create_toothfairy_document(
    api_key="...",
    workspace_id="...",
    title="Getting Started Guide",
    content="# Welcome to Acme...",
    folder_id="folder-uuid"
)

# Create topics for organization
create_toothfairy_entity(
    api_key="...",
    workspace_id="...",
    label="Pricing",
    entity_type="topic"
)
```

### 3. Sending Messages to an Agent

```python
# Send a message and get response
response = send_toothfairy_message(
    api_key="...",
    workspace_id="...",
    agent_id="agent-uuid",
    message="What are your business hours?"
)
```

---

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid API key | Check key in Admin > API Integration |
| `403 Forbidden` | Insufficient permissions | Upgrade to Business/Enterprise |
| `404 Not Found` | Invalid ID or wrong endpoint | Verify UUIDs and API domain |
| `429 Too Many Requests` | Rate limit exceeded | Wait and retry with backoff |
| `Budget Exceeded` | Monthly UoI limit reached | Upgrade plan or wait for reset |

---

## Version History

- **0.5.6** - Initial comprehensive documentation aligned with SDK
