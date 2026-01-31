"""Main MCP server for ToothFairyAI documentation.

This server exposes all ToothFairyAI SDK operations as MCP tools,
plus documentation and API search capabilities.
"""

from typing import Optional

from fastmcp import FastMCP

from .config import config
from .resources.docs_loader import DocsLoader
from .resources.api_loader import ApiLoader
from .resources.release_notes_loader import ReleaseNotesLoader
from .resources.agent_guide import get_agent_creation_guide as _get_guide, get_agent_creation_section
from .tools.search import SearchTool
from .tools.mcp_tools import register_all_tools


# Initialize the MCP server
# Note: For production with authentication, use a reverse proxy (nginx/traefik)
# with auth middleware, or configure OAuth via FastMCP's OAuthProvider
mcp = FastMCP(
    "ToothFairyAI Documentation",
    instructions="""Access ToothFairyAI documentation, API specs, and full workspace management via SDK.

DOCUMENTATION & SEARCH:
- search_docs: Search across all documentation
- get_doc_by_topic: Get documentation for a specific topic
- get_agent_creation_guide: Comprehensive guide for creating agents
- search_api_endpoints: Search API endpoints
- explain_api_domains: Understand Platform vs AI Services vs Voice APIs

RELEASE NOTES:
- list_release_notes: List all available release notes
- get_latest_release_notes: Get the most recent release notes
- get_release_notes: Get release notes for a specific version
- search_release_notes: Search release notes by keyword

GLOBAL UTILS (No authentication required):
- fetch_toothfairy_announcement: Get the latest emergency/single-line announcement
- fetch_toothfairy_hireable_agents: Get available hireable agents for inspiration

WORKFLOW: Always validate_toothfairy_credentials first, then use the appropriate tools.

=== SDK TOOLS (all require api_key, workspace_id, region) ===

CREDENTIAL VALIDATION:
- validate_toothfairy_credentials: Always call first to verify credentials

AGENT MANAGEMENT:
- create_toothfairy_agent: Create a new agent
- get_toothfairy_agent: Get agent by ID
- update_toothfairy_agent: Update an agent
- delete_toothfairy_agent: Delete an agent (irreversible)
- list_toothfairy_agents: List all agents
- search_toothfairy_agents: Search agents by label

AGENT FUNCTIONS (Tools for External APIs):
- create_toothfairy_function: Create a function
- get_toothfairy_function: Get function by ID
- update_toothfairy_function: Update a function
- delete_toothfairy_function: Delete a function (irreversible)
- list_toothfairy_functions: List all functions

AUTHORISATIONS (API Key/OAuth Storage):
- create_toothfairy_authorisation: Create an authorisation
- get_toothfairy_authorisation: Get authorisation by ID
- update_toothfairy_authorisation: Update an authorisation
- delete_toothfairy_authorisation: Delete an authorisation (irreversible)
- list_toothfairy_authorisations: List all authorisations

SECRETS (Secure Value Storage):
- create_toothfairy_secret: Create a secret linked to an authorisation
- delete_toothfairy_secret: Delete a secret (irreversible)

DOCUMENTS (Knowledge Base):
- create_toothfairy_document: Create a document
- get_toothfairy_document: Get document by ID
- update_toothfairy_document: Update a document
- delete_toothfairy_document: Delete a document (irreversible)
- list_toothfairy_documents: List all documents
- search_toothfairy_documents: Search documents by text

ENTITIES (Topics, Intents, NER):
- create_toothfairy_entity: Create an entity
- get_toothfairy_entity: Get entity by ID
- update_toothfairy_entity: Update an entity
- delete_toothfairy_entity: Delete an entity (irreversible)
- list_toothfairy_entities: List entities (filter by type: topic, intent, ner)
- search_toothfairy_entities: Search entities by label

FOLDERS (Document Organization):
- create_toothfairy_folder: Create a folder
- get_toothfairy_folder: Get folder by ID
- update_toothfairy_folder: Update a folder
- delete_toothfairy_folder: Delete a folder (irreversible)
- list_toothfairy_folders: List all folders
- get_toothfairy_folder_tree: Get complete folder tree

CHATS (Conversation Sessions):
- create_toothfairy_chat: Create a chat session
- get_toothfairy_chat: Get chat by ID
- delete_toothfairy_chat: Delete a chat (irreversible)
- list_toothfairy_chats: List all chats
- send_toothfairy_message: Send message to agent and get response

PROMPTS (Reusable Templates):
- create_toothfairy_prompt: Create a prompt template
- get_toothfairy_prompt: Get prompt by ID
- update_toothfairy_prompt: Update a prompt
- delete_toothfairy_prompt: Delete a prompt (irreversible)
- list_toothfairy_prompts: List all prompts

MEMBERS (Workspace Users):
- get_toothfairy_member: Get member by ID
- update_toothfairy_member: Update a member
- delete_toothfairy_member: Remove member (irreversible)
- list_toothfairy_members: List all members

CHANNELS (Communication):
- create_toothfairy_channel: Create a channel
- get_toothfairy_channel: Get channel by ID
- update_toothfairy_channel: Update a channel
- delete_toothfairy_channel: Delete a channel (irreversible)
- list_toothfairy_channels: List all channels

CONNECTIONS (Database):
- get_toothfairy_connection: Get connection by ID
- delete_toothfairy_connection: Delete a connection (irreversible)
- list_toothfairy_connections: List all connections

BENCHMARKS (Agent Testing):
- create_toothfairy_benchmark: Create a benchmark
- get_toothfairy_benchmark: Get benchmark by ID
- update_toothfairy_benchmark: Update a benchmark
- delete_toothfairy_benchmark: Delete a benchmark (irreversible)
- list_toothfairy_benchmarks: List all benchmarks

HOOKS (Custom Code Execution):
- create_toothfairy_hook: Create a hook
- get_toothfairy_hook: Get hook by ID
- update_toothfairy_hook: Update a hook
- delete_toothfairy_hook: Delete a hook (irreversible)
- list_toothfairy_hooks: List all hooks

SCHEDULED JOBS (Automation):
- create_toothfairy_scheduled_job: Create a scheduled job
- get_toothfairy_scheduled_job: Get job by ID
- update_toothfairy_scheduled_job: Update a job
- delete_toothfairy_scheduled_job: Delete a job (irreversible)
- list_toothfairy_scheduled_jobs: List all jobs

SITES:
- get_toothfairy_site: Get site by ID
- update_toothfairy_site: Update a site
- delete_toothfairy_site: Delete a site (irreversible)
- list_toothfairy_sites: List all sites

DICTIONARY:
- get_toothfairy_dictionary_entry: Get entry by ID
- list_toothfairy_dictionary_entries: List all entries

REQUEST LOGS:
- get_toothfairy_request_log: Get log by ID
- list_toothfairy_request_logs: List all logs

SETTINGS:
- get_toothfairy_charting_settings: Get charting settings
- update_toothfairy_charting_settings: Update charting settings
- get_toothfairy_embeddings_settings: Get embeddings settings
- update_toothfairy_embeddings_settings: Update embeddings settings

BILLING:
- get_toothfairy_month_costs: Get monthly costs

EMBEDDINGS:
- create_toothfairy_embedding: Create text embeddings

REGIONS: Use region="au" (default), "eu", or "us" for API region.""",
)

# Initialize loaders
docs_loader = DocsLoader(config.docs_path)
api_loader = ApiLoader(config.api_docs_path)
# Release notes are in docs/tf_docs/release-notes (sibling to docs/)
release_notes_path = config.docs_path.parent / "release-notes"
release_notes_loader = ReleaseNotesLoader(release_notes_path)
search_tool = SearchTool(docs_loader, api_loader)

# Ensure docs are loaded at startup
docs_loader.load()
api_loader.load()
release_notes_loader.load()

# Register all SDK-based tools (~88 tools)
register_all_tools(mcp)


# ============================================================================
# Resources - Documentation
# ============================================================================


@mcp.resource("toothfairy://docs/list")
def list_all_docs() -> str:
    """List all available documentation pages."""
    docs = docs_loader.list_docs()
    lines = ["# ToothFairyAI Documentation\n"]
    lines.append(f"Total documents: {len(docs)}\n")

    # Group by category
    by_category = {}
    for doc in docs:
        cat = doc["category"]
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(doc)

    for category in sorted(by_category.keys()):
        lines.append(f"\n## {category.title()}\n")
        for doc in by_category[category]:
            lines.append(f"- [{doc['title']}]({doc['uri']})")
            if doc["description"]:
                lines.append(f"  - {doc['description'][:100]}...")

    return "\n".join(lines)


@mcp.resource("toothfairy://docs/{category}/{slug}")
def get_doc(category: str, slug: str) -> str:
    """
    Get a specific documentation page by category and slug.

    Args:
        category: The documentation category (e.g., "agents", "settings")
        slug: The document slug (e.g., "agents", "prompting")

    Returns:
        The markdown content of the documentation page
    """
    doc = docs_loader.get_doc(category, slug)
    if doc is None:
        return f"# Document Not Found\n\nNo document found for category='{category}', slug='{slug}'\n\nUse `toothfairy://docs/list` to see available documents."

    # Return content with metadata header
    header = f"# {doc.title}\n\n"
    if doc.description:
        header += f"> {doc.description}\n\n"
    header += f"**Category:** {doc.category} | **URI:** `{doc.uri}`\n\n---\n\n"

    return header + doc.content


# ============================================================================
# Resources - API Specifications
# ============================================================================


@mcp.resource("toothfairy://api/list")
def list_api_specs() -> str:
    """List all available API specifications."""
    specs = api_loader.list_specs()
    lines = ["# ToothFairyAI API Specifications\n"]
    lines.append(f"Total specs: {len(specs)}\n")

    lines.append("## IMPORTANT: API Domain Distinction")
    lines.append("ToothFairyAI has multiple API domains serving different purposes:")
    lines.append("- **Platform API** (`api.{region}.toothfairyai.com`): Agent management & platform operations (create, update, delete agents, functions, entities, chat management)")
    lines.append("- **AI Services API** (`ai.{region}.toothfairyai.com`): AI operations (agent interaction, planning, search, tokenization, embeddings, model listing)")
    lines.append("- **Voice API** (`voice.{region}.toothfairyai.com`): Voice-specific operations")
    lines.append("\nAlways use the correct domain for each type of operation!\n")

    # Group by API type
    by_type = {}
    for spec in specs:
        api_type = spec.get('api_type', 'unknown')
        if api_type not in by_type:
            by_type[api_type] = []
        by_type[api_type].append(spec)

    # Display in order: platform, ai-services, voice, unknown
    display_order = ['platform', 'ai-services', 'voice', 'unknown']
    for api_type in display_order:
        if api_type in by_type:
            type_display = {
                'platform': 'Platform API',
                'ai-services': 'AI Services API',
                'voice': 'Voice API',
                'unknown': 'Other APIs'
            }.get(api_type, api_type)

            lines.append(f"\n## {type_display}")
            lines.append(f"**Base Domain:** `{by_type[api_type][0].get('base_domain', 'unknown')}`")

            for spec in by_type[api_type]:
                lines.append(f"\n### {spec['title']} (v{spec['version']})")
                lines.append(f"- URI: `{spec['uri']}`")
                if spec["description"]:
                    lines.append(f"- {spec['description'][:200]}...")

    return "\n".join(lines)


@mcp.resource("toothfairy://api/{name}")
def get_api_spec(name: str) -> str:
    """
    Get an OpenAPI specification by name.

    Args:
        name: The spec name ("platform", "ai-services", or "voice")

    Returns:
        The OpenAPI spec as JSON string
    """
    spec = api_loader.get_spec(name)
    if spec is None:
        available = [s.name for s in api_loader.get_all_specs()]
        return f"# API Spec Not Found\n\nNo spec found for name='{name}'\n\nAvailable specs: {', '.join(available)}"

    return spec.raw_content


@mcp.resource("toothfairy://api/{name}/endpoints")
def get_api_endpoints(name: str) -> str:
    """
    Get a summary of all endpoints in an API spec.

    Args:
        name: The spec name ("platform", "ai-services", or "voice")

    Returns:
        Markdown summary of all endpoints
    """
    spec = api_loader.get_spec(name)
    if spec is None:
        return f"# API Spec Not Found\n\nNo spec found for name='{name}'"

    endpoints = spec.get_endpoints_summary()
    lines = [f"# {spec.title} - Endpoints\n"]

    # Add API type and domain info
    api_type_display = {
        "platform": "Platform API",
        "ai-services": "AI Services API",
        "voice": "Voice API"
    }.get(spec.api_type, 'API')

    lines.append(f"**API Type:** {api_type_display}")
    lines.append(f"**Base Domain:** `{spec.base_domain}`")
    lines.append(f"**Total endpoints:** {len(endpoints)}\n")

    lines.append("## Endpoint Usage Notes")
    lines.append(f"- Use `{spec.base_domain}` as the base URL for all endpoints below")
    lines.append("- Replace `{region}` with your region (au, eu, us) or omit for default region")
    lines.append("- Example: `https://" + spec.base_domain.replace("{region}.", "") + "{endpoint_path}`\n")

    # Group by tag
    by_tag = {}
    for ep in endpoints:
        tags = ep.get("tags", ["Other"])
        for tag in tags:
            if tag not in by_tag:
                by_tag[tag] = []
            by_tag[tag].append(ep)

    for tag in sorted(by_tag.keys()):
        lines.append(f"\n## {tag}\n")
        for ep in by_tag[tag]:
            lines.append(f"- **{ep['method']}** `{ep['path']}`")
            lines.append(f"  - **Full URL:** `{ep.get('full_url', 'N/A')}`")
            if ep["summary"]:
                lines.append(f"  - **Summary:** {ep['summary']}")

    return "\n".join(lines)


@mcp.resource("toothfairy://api/integration-guide")
def get_integration_guide() -> str:
    """Get the Voice API integration guide."""
    guide = api_loader.get_integration_guide()
    if guide is None:
        return "# Integration Guide Not Found\n\nThe integration guide is not available."
    return guide


# ============================================================================
# Documentation Tools
# ============================================================================


@mcp.tool()
def search_docs(
    query: str,
    limit: int = 10,
    source: Optional[str] = None,
) -> list[dict]:
    """
    Search across all ToothFairyAI documentation.

    Args:
        query: The search query string
        limit: Maximum number of results (default: 10)
        source: Filter by source type ("docs" for markdown docs, "api" for API specs, or None for all)

    Returns:
        List of search results with title, uri, snippet, and relevance score
    """
    return search_tool.search(query, limit=limit, source_filter=source)


@mcp.tool()
def search_api_endpoints(query: str, limit: int = 20) -> list[dict]:
    """
    Search for specific API endpoints.

    Args:
        query: Search query (matches path, summary, description, or tags)
        limit: Maximum number of results (default: 20)

    Returns:
        List of matching endpoints with method, path, summary, tags, and API type info
    """
    endpoints = search_tool.search_endpoints(query, limit=limit)

    # Enhance the results with API type information
    enhanced_results = []
    for endpoint in endpoints:
        # Add API type display name
        api_type = endpoint.get('api_type', 'unknown')
        api_type_display = {
            'platform': 'Platform API',
            'ai-services': 'AI Services API',
            'voice': 'Voice API'
        }.get(api_type, 'API')

        enhanced_endpoint = endpoint.copy()
        enhanced_endpoint['api_type_display'] = api_type_display
        enhanced_endpoint['base_domain'] = endpoint.get('base_domain', 'unknown')

        # Add usage note
        enhanced_endpoint['usage_note'] = (
            f"Use {api_type_display} domain: {endpoint.get('base_domain', 'unknown')}"
        )

        enhanced_results.append(enhanced_endpoint)

    return enhanced_results


@mcp.tool()
def explain_api_domains() -> str:
    """
    Explain the different ToothFairyAI API domains and when to use each.

    Returns:
        Detailed explanation of API domain distinctions with examples
    """
    return """# ToothFairyAI API Domain Distinction Guide

## CRITICAL: Use the Correct Domain for Each Operation

ToothFairyAI has multiple API domains that serve different purposes. Using the wrong domain will result in errors or incorrect behavior.

## API Domains Overview

| API Type | Base Domain | Purpose | Example Operations |
|----------|-------------|---------|-------------------|
| **Platform API** | `api.{region}.toothfairyai.com` | Agent management & platform operations | Create/update/delete agents, functions, entities, chat management |
| **AI Services API** | `ai.{region}.toothfairyai.com` | AI operations & agent interaction | Chat with agents, planning, search, tokenization, embeddings, model listing |
| **Voice API** | `voice.{region}.toothfairyai.com` | Voice-specific operations | Voice calls, speech-to-text, text-to-speech |

## How to Identify Which API to Use

### 1. Check the OpenAPI Specification
- **Platform API** (`openapi.json`): Contains agent management endpoints (create, update, delete, list)
- **AI Services API** (`aiopenapi.json`): Contains AI operations endpoints (chat, planning, search, tokenization, embeddings)
- **Voice API** (`voiceapi.json`): Contains voice-specific endpoints

### 2. Look at the Endpoint Path
- **AI operations**: `/agent` (chat), `/planner`, `/searcher`, `/tokenizer`, `/embedder` -> Use **AI Services API**
- **Public endpoints** (no auth required): `/models_list` (AI Services), `/global_utils/fetch_hireable_agents`, `/global_utils/fetch_announcement` (Platform API)
- **Agent management**: `/agent/create`, `/agent/update/{id}`, `/agent/delete/{id}`, `/agent/list` -> Use **Platform API**
- **Voice operations**: `/voice/call`, `/transcribe` -> Use **Voice API**

### 3. Key Distinction
- **Platform API**: **MANAGING** agents and platform resources (CRUD operations)
- **AI Services API**: **USING AI** services (chat, search, tokenization, embeddings)
- **Voice API**: **VOICE** operations

## Examples

### Correct: Agent Chat (AI Service)
```bash
POST https://ai.toothfairyai.com/agent
Content-Type: application/json
{
  "workspaceid": "your-workspace-id",
  "agentid": "agent-uuid",
  "messages": [{"role": "user", "content": "Hello"}]
}
```

### Correct: Create Agent (Management)
```bash
POST https://api.toothfairyai.com/agent/create
Content-Type: application/json
{
  "workspaceID": "your-workspace-id",
  "label": "Research Assistant",
  "mode": "retriever",
  "interpolationString": "You are a research assistant..."
}
```

## Tool Integration

When using the MCP server tools:
- **Agent management operations** (`create_toothfairy_agent`, `list_toothfairy_agents`): Use Platform API domain internally
- **AI service operations**: Would use AI Services API domain
- **Always check** the `api_type` field in search results to know which domain to use

## Pro Tips
1. **Check the spec name** - `platform` = Platform API, `ai-services` = AI Services API, `voice` = Voice API
2. **Use `search_api_endpoints`** - It now includes `api_type_display` to show which API to use
3. **Regional domains** - Replace `{region}` with `au`, `eu`, or `us` (or omit for default)
4. **Remember**: Platform API manages resources, AI Services API provides AI capabilities

Remember: **Wrong domain = API errors**. Always verify you're using the correct API type!
"""


@mcp.tool()
def list_doc_categories() -> list[str]:
    """
    List all documentation categories.

    Returns:
        List of category names (e.g., ["agents", "settings", "guides"])
    """
    return search_tool.list_categories()


@mcp.tool()
def get_doc_by_topic(topic: str) -> str:
    """
    Get documentation for a specific topic.

    This is a convenience tool that searches for the topic and returns
    the most relevant document's full content.

    Args:
        topic: The topic to find (e.g., "agents", "prompting", "channels")

    Returns:
        The full markdown content of the most relevant document
    """
    results = search_tool.search(topic, limit=1, source_filter="docs")
    if not results:
        return f"No documentation found for topic: {topic}"

    # Get the full document
    uri = results[0]["uri"]
    # Parse uri: toothfairy://docs/{category}/{slug}
    parts = uri.replace("toothfairy://docs/", "").split("/")
    if len(parts) >= 2:
        category, slug = parts[0], parts[1]
        # Use docs_loader directly instead of the decorated resource function
        doc = docs_loader.get_doc(category, slug)
        if doc is None:
            return f"No document found for category='{category}', slug='{slug}'"

        # Return content with metadata header (same format as get_doc resource)
        header = f"# {doc.title}\n\n"
        if doc.description:
            header += f"> {doc.description}\n\n"
        header += f"**Category:** {doc.category} | **URI:** `{doc.uri}`\n\n---\n\n"
        return header + doc.content

    return f"Could not retrieve document for: {topic}"


@mcp.tool()
def get_agent_creation_guide(section: Optional[str] = None) -> str:
    """
    Get the comprehensive guide for creating ToothFairyAI agents.

    This guide covers all aspects of agent creation including:
    - Agent modes (chatter, retriever, coder, planner, voice)
    - Core fields and configuration
    - Tools system and customToolingInstructions
    - Feature flags and rules
    - Model configuration
    - Complete examples for each agent type

    Args:
        section: Optional section to retrieve. If not provided, returns the full guide.
                 Available sections: modes, core-fields, mode-config, tools, features,
                 departments, models, uploads, voice, planner, validation,
                 best-practices, examples, quick-reference

    Returns:
        The agent creation guide content (full or specific section)
    """
    if section:
        return get_agent_creation_section(section)
    return _get_guide()


# ============================================================================
# Release Notes Tools
# ============================================================================


@mcp.tool()
def list_release_notes() -> list[dict]:
    """
    List all available ToothFairyAI release notes.

    Returns a list of all release notes sorted by version (newest first),
    including version number, release date, title, and summary.

    Returns:
        List of release notes with version, release_date, title, summary, and uri
    """
    return release_notes_loader.list_notes()


@mcp.tool()
def get_latest_release_notes() -> str:
    """
    Get the most recent ToothFairyAI release notes.

    Returns the full content of the latest release notes including
    all new features, improvements, and fixes.

    Returns:
        The full markdown content of the latest release notes
    """
    note = release_notes_loader.get_latest()
    if note is None:
        return "No release notes found."

    header = f"# {note.title}\n\n"
    header += f"**Version:** {note.version} | **Released:** {note.release_date}\n\n"
    header += f"**URI:** `{note.uri}`\n\n---\n\n"

    return header + note.content


@mcp.tool()
def get_release_notes(version: str) -> str:
    """
    Get release notes for a specific version.

    Args:
        version: The version number to retrieve (e.g., "0.668.0", "v0.668.0", or "0.668")

    Returns:
        The full markdown content of the release notes for that version
    """
    note = release_notes_loader.get_note(version)
    if note is None:
        available = [n.version for n in release_notes_loader.get_all_notes()[:5]]
        return (
            f"No release notes found for version: {version}\n\n"
            f"Recent versions available: {', '.join(available)}\n\n"
            "Use `list_release_notes()` to see all available versions."
        )

    header = f"# {note.title}\n\n"
    header += f"**Version:** {note.version} | **Released:** {note.release_date}\n\n"
    header += f"**URI:** `{note.uri}`\n\n---\n\n"

    return header + note.content


@mcp.tool()
def search_release_notes(query: str, limit: int = 10) -> list[dict]:
    """
    Search release notes by keyword or phrase.

    Search across all release notes to find features, fixes, or changes
    mentioning the specified terms.

    Args:
        query: Search query (e.g., "voice agents", "MCP", "agentic tooling")
        limit: Maximum number of results (default: 10)

    Returns:
        List of matching release notes with version, title, snippet, and relevance score
    """
    return release_notes_loader.search(query, limit=limit)


# ============================================================================
# Prompts (Templates)
# ============================================================================


@mcp.prompt()
def api_usage_guide(endpoint: str) -> str:
    """
    Generate a guide for using a specific API endpoint.

    Args:
        endpoint: The API endpoint path (e.g., "/chatter", "/agent/update")
    """
    return f"""Please help me understand how to use the ToothFairyAI API endpoint: {endpoint}

Search for this endpoint in the API documentation and provide:
1. The HTTP method and full path
2. Required authentication
3. Request parameters/body
4. Response format
5. Example usage

Use the search_api_endpoints and get_api_spec tools to find the information."""


@mcp.prompt()
def feature_guide(feature: str) -> str:
    """
    Generate a guide for a ToothFairyAI feature.

    Args:
        feature: The feature name (e.g., "agents", "knowledge hub", "channels")
    """
    return f"""Please help me understand the ToothFairyAI feature: {feature}

Search the documentation and provide:
1. What this feature does
2. How to configure it
3. Best practices
4. Related features

Use the search_docs and get_doc_by_topic tools to find the information."""


@mcp.prompt()
def create_agent(agent_type: str, use_case: str) -> str:
    """
    Generate configuration for a ToothFairyAI agent.

    Args:
        agent_type: Type of agent (e.g., "chatter", "retriever", "voice", "planner")
        use_case: Description of the agent's intended purpose
    """
    return f"""Please help me create a ToothFairyAI agent configuration.

Agent type: {agent_type}
Use case: {use_case}

Use the get_agent_creation_guide tool to:
1. Get the appropriate mode configuration for this agent type
2. Select the right model and temperature settings
3. Configure the appropriate tools and features
4. Write effective interpolationString (system prompt)
5. Write customToolingInstructions for the enabled tools
6. Set proper upload permissions based on the use case

Provide a complete, valid agent configuration object following the guide's best practices."""


# ============================================================================
# Custom HTTP Routes
# ============================================================================


@mcp.custom_route("/health", methods=["GET"])
async def health_check(request):
    """Health check endpoint for load balancers and monitoring."""
    from starlette.responses import JSONResponse

    return JSONResponse({
        "status": "healthy",
        "server": "ToothFairyAI Documentation MCP",
        "docs_loaded": len(docs_loader.get_all_docs()),
        "api_specs_loaded": len(api_loader.get_all_specs()),
    })


@mcp.custom_route("/info", methods=["GET"])
async def server_info(request):
    """Server information endpoint."""
    from starlette.responses import JSONResponse

    return JSONResponse({
        "name": "ToothFairyAI Documentation MCP Server",
        "version": "0.5.6",
        "documentation": {
            "total_docs": len(docs_loader.get_all_docs()),
            "categories": docs_loader.get_categories(),
        },
        "release_notes": {
            "total": len(release_notes_loader.get_all_notes()),
            "latest_version": (
                release_notes_loader.get_latest().version
                if release_notes_loader.get_latest()
                else None
            ),
        },
        "api_specs": [
            {"name": spec.name, "title": spec.title, "version": spec.version}
            for spec in api_loader.get_all_specs()
        ],
        "endpoints": {
            "sse": "/sse",
            "health": "/health",
            "info": "/info",
        },
    })


# ============================================================================
# Main Entry Point
# ============================================================================


def main():
    """Run the MCP server."""
    import sys

    # Check for --stdio flag to override config
    use_stdio = "--stdio" in sys.argv or config.transport == "stdio"

    print("=" * 60, file=sys.stderr)
    print("ToothFairyAI Documentation MCP Server", file=sys.stderr)
    print("=" * 60, file=sys.stderr)
    print(f"Transport: {'stdio' if use_stdio else 'http'}", file=sys.stderr)
    if not use_stdio:
        print(f"Host: {config.host}", file=sys.stderr)
        print(f"Port: {config.port}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Docs path: {config.docs_path}", file=sys.stderr)
    print(f"API docs path: {config.api_docs_path}", file=sys.stderr)
    print(file=sys.stderr)
    print(f"Loaded {len(docs_loader.get_all_docs())} documentation pages", file=sys.stderr)
    print(f"Loaded {len(api_loader.get_all_specs())} API specifications", file=sys.stderr)
    print(f"Loaded {len(release_notes_loader.get_all_notes())} release notes", file=sys.stderr)
    print(file=sys.stderr)
    if not use_stdio:
        print("Endpoints:", file=sys.stderr)
        print(f"  - SSE (MCP): http://{config.host}:{config.port}/sse", file=sys.stderr)
        print(f"  - Health: http://{config.host}:{config.port}/health", file=sys.stderr)
        print(f"  - Info: http://{config.host}:{config.port}/info", file=sys.stderr)
    else:
        print("Running in stdio mode (for local MCP clients)", file=sys.stderr)
    print("=" * 60, file=sys.stderr)

    if use_stdio:
        # Run with stdio transport for local use (Claude Code, etc.)
        mcp.run(transport="stdio")
    else:
        # Run with SSE transport for remote access (Claude Code compatible)
        mcp.run(transport="sse", host=config.host, port=config.port)


if __name__ == "__main__":
    main()
