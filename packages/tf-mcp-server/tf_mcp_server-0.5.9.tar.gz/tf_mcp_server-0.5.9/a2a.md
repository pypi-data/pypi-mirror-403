ToothFairyAI Protocol Servers
Overview
Build protocol servers for ToothFairyAI:
MCP Server (Complete) - Exposes documentation as resources for AI assistants
A2A Server (Research Phase) - Exposes ToothFairyAI agents via Google's Agent-to-Agent protocol
Part 1: A2A Protocol Research
What is A2A?
A2A (Agent-to-Agent) is Google's open protocol for AI agent interoperability, now under the Linux Foundation. It enables agents from different vendors to discover, negotiate, and collaborate on tasks.
A2A vs MCP - Key Differences
Aspect	MCP	A2A
Purpose	Agent-to-Tool communication	Agent-to-Agent communication
Statefulness	Stateless (discrete operations)	Stateful (multi-turn tasks)
Primary Use	Tools, resources, prompts	Agent collaboration
Relationship	Complementary - use together	
A2A Core Concepts
1. Agent Cards
JSON metadata at /.well-known/agent.json describing:
Agent identity and capabilities
Service endpoint URL
Authentication requirements
Available skills
2. Tasks
Fundamental unit of work with lifecycle states:
Active: submitted, working
Interrupted: input-required, auth-required
Terminal: completed, failed, canceled, rejected
3. Messages
Communication between agents with parts:
TextPart - Text content
FilePart - File references
DataPart - Structured JSON
4. Artifacts
Tangible outputs/deliverables (documents, images, data)
A2A Required Endpoints
Discovery
GET /.well-known/agent.json    # Agent Card (required)
Communication (JSON-RPC 2.0)
POST /                         # JSON-RPC endpoint
  - message/send              # Sync request/response
  - message/stream            # SSE streaming
  - tasks/get                 # Get task state
  - tasks/cancel              # Cancel task
Push Notifications (Optional)
POST /tasks/{taskId}/pushNotificationConfigs
ToothFairyAI → A2A Mapping
ToothFairyAI	A2A Equivalent
Agent (id, label, description, capabilities)	Agent Card
Chat Session (chatid)	Task (taskId)
ChatMessage (text, role, images, files)	Message with Parts
Agent Response	Artifact
/agent SSE endpoint	message/stream
/chatter endpoint	message/send
ToothFairyAI Agent Capabilities (from OpenAPI)
Existing Endpoints:
GET /agent/list - List workspace agents
GET /agent/get/{id} - Get agent details
POST /chatter - Sync chat (non-streaming)
POST /agent - SSE streaming responses
Agent Properties Map to A2A Skills:
type: retriever, generative, planner, custom
hasMemory: conversation persistence
hasImages: image processing
hasFunctions: tool execution
charting: visualization
summarisation: content summarization
Implementation Requirements
Option A: Separate A2A Server
New server alongside MCP that:
Serves Agent Cards for each ToothFairyAI agent
Translates A2A JSON-RPC to ToothFairyAI API calls
Manages task state (maps to chat sessions)
Option B: Combined MCP + A2A Server
Single server exposing both protocols:
MCP at /mcp/v1
A2A at / (JSON-RPC) and /.well-known/agent.json
Key Implementation Tasks:
Agent Card Generator - Convert TF agents to A2A Agent Cards
JSON-RPC Handler - Route A2A methods to TF API
Task State Manager - Map chat sessions to A2A tasks
SSE Adapter - Translate TF streaming to A2A format
Authentication Bridge - Map A2A auth to TF x-api-key
References
A2A Protocol Spec
A2A Python SDK
A2A Samples
Part 2: MCP Server (Complete)
Phase 1: Documentation-Only MCP (Current Scope)
What We're Building
A remote HTTP MCP server that exposes:
47 markdown docs from docs/tf_docs/docs/ (Agents, Settings, Admin, Guides, etc.)
3 OpenAPI specs from docs/api_docs/public/ (main API, agents API, voice API)
1 integration guide - Voice API WebRTC/SIP integration
MCP Primitives Used
Primitive	Purpose
Resources	Static documentation content (markdown, JSON)
Tools	search_docs - Full-text search across all docs
Prompts	Templates for common questions (optional)
Architecture
tf_mcp_server/
├── pyproject.toml           # Package config (FastMCP, uvicorn)
├── server.py                # Main MCP server entry point
├── resources/
│   ├── docs_loader.py       # Load markdown from tf_docs
│   └── api_loader.py        # Load OpenAPI specs
├── tools/
│   └── search.py            # Full-text doc search
└── config.py                # Server configuration
Implementation Steps
Step 1: Project Setup
Create tf_mcp_server/ directory in repo root
Initialize with pyproject.toml:
Dependencies: fastmcp, uvicorn, pydantic
Entry point for HTTP server
Step 2: Documentation Loaders
docs_loader.py: Scan docs/tf_docs/docs/**/*.md
Parse frontmatter for titles/descriptions
Create resource URIs: toothfairy://docs/{category}/{slug}
api_loader.py: Load OpenAPI JSON files
Create resource URIs: toothfairy://api/{spec-name}
Step 3: MCP Server (server.py)
from fastmcp import FastMCP

mcp = FastMCP("ToothFairyAI Documentation")

# Resources
@mcp.resource("toothfairy://docs/{category}/{slug}")
def get_doc(category: str, slug: str) -> str:
    """Return markdown content for a documentation page."""

@mcp.resource("toothfairy://api/{spec}")
def get_api_spec(spec: str) -> str:
    """Return OpenAPI spec as JSON string."""

# Tools
@mcp.tool()
def search_docs(query: str) -> list[dict]:
    """Search across all documentation."""
Step 4: HTTP Deployment
Add uvicorn runner for HTTP transport
Configure CORS for cross-origin requests
Environment variables: PORT, HOST, DOCS_PATH
Documentation Categories (47 files)
Category	Files	Key Content
Agents	9	Agent types, model choice, marketplace
Settings	14	Prompting, functions, channels, NER
Administrators	8	User mgmt, dashboard, embeddings
Knowledge Hub	5	Documents, images, embedding status
Guides	5	API integration, Twilio, Voice API
Training	2	Training data preparation
Benchmarks	2	Agent benchmarking
Account	1	Account management
Core	2	Quick start, glossary
OpenAPI Specs
File	Description	Endpoints
openapi.json	Main ToothFairyAI API	78 endpoints
aiopenapi.json	TF Agents API	Agent-specific
voiceapi.json	Voice Agent API	WebRTC, SIP
Phase 2: Tools Expansion (Future)
Python SDK: toothfairyai (v0.4.0)
Location: /Users/gabriele_sanguigno/TF_coding/python_sdk/src/toothfairyai PyPI: pip install toothfairyai The SDK provides these managers via ToothFairyClient:
Manager	MCP Tools to Create	Description
client.chat	send_to_agent, list_chats, get_chat	Agent messaging
client.streaming	stream_to_agent	Streaming responses
client.documents	list_docs, create_doc, upload_file	Document management
client.entities	list_entities, create_entity	Entity management
client.folders	list_folders, create_folder	Folder organization
client.prompts	list_prompts, create_prompt	Prompt templates
Integration Strategy
# Future: tools/api_tools.py
from toothfairyai import ToothFairyClient

client = ToothFairyClient(
    api_key=os.environ["TF_API_KEY"],
    workspace_id=os.environ["TF_WORKSPACE_ID"]
)

@mcp.tool()
def send_to_agent(agent_id: str, message: str) -> dict:
    """Send a message to a ToothFairyAI agent."""
    response = client.chat.send_to_agent(message, agent_id)
    return {"response": response.agent_response, "chat_id": response.chat_id}

@mcp.tool()
def search_knowledge_hub(query: str, top_k: int = 10) -> list[dict]:
    """Search the knowledge hub for relevant documents."""
    results = client.documents.search(query, top_k=top_k)
    return [{"title": r.title, "content": r.content} for r in results]
Files to Create
File	Purpose
tf_mcp_server/pyproject.toml	Package configuration
tf_mcp_server/server.py	Main FastMCP server
tf_mcp_server/resources/docs_loader.py	Markdown doc loader
tf_mcp_server/resources/api_loader.py	OpenAPI spec loader
tf_mcp_server/tools/search.py	Documentation search
tf_mcp_server/config.py	Configuration management
Source Documentation Paths
Markdown docs: docs/tf_docs/docs/**/*.md (47 files)
OpenAPI specs: docs/api_docs/public/*.json (3 files)
Integration guide: docs/api_docs/public/INTEGRATION_GUIDE.md
Deployment
HTTP server via uvicorn, configurable via environment:
MCP_HOST: Host to bind (default: 0.0.0.0)
MCP_PORT: Port to bind (default: 8000)
DOCS_BASE_PATH: Path to docs directory