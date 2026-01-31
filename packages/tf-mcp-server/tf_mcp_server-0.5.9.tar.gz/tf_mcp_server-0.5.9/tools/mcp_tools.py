"""MCP tool registration for all ToothFairyAI SDK operations.

This module provides functions to register all SDK operations as MCP tools.
Call register_all_tools(mcp) to register all tools with your FastMCP instance.
"""

from typing import Optional, List, Dict, Any
from . import all_tools
from . import global_utils_tools


def register_all_tools(mcp):
    """Register all ToothFairyAI SDK tools with the MCP server.

    Args:
        mcp: FastMCP instance to register tools with
    """
    # ========================================================================
    # CREDENTIAL VALIDATION
    # ========================================================================

    @mcp.tool()
    def validate_toothfairy_credentials(
        api_key: str,
        workspace_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Validate ToothFairyAI credentials. Always call this first."""
        return all_tools.validate_credentials(api_key, workspace_id, region)

    # ========================================================================
    # AGENT TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_agent(
        api_key: str,
        workspace_id: str,
        label: str,
        mode: str,
        interpolation_string: str,
        goals: str,
        region: str = "au",
        temperature: float = 0.3,
        max_tokens: int = 4096,
        description: Optional[str] = None,
        agentic_rag: bool = False,
        has_code: bool = False,
        charting: bool = False,
        allow_internet_search: bool = False,
    ) -> Dict[str, Any]:
        """Create a new ToothFairyAI agent."""
        return all_tools.create_agent(
            api_key=api_key,
            workspace_id=workspace_id,
            label=label,
            mode=mode,
            interpolation_string=interpolation_string,
            goals=goals,
            region=region,
            temperature=temperature,
            max_tokens=max_tokens,
            description=description,
            agentic_rag=agentic_rag,
            has_code=has_code,
            charting=charting,
            allow_internet_search=allow_internet_search,
        )

    @mcp.tool()
    def get_toothfairy_agent(
        api_key: str,
        workspace_id: str,
        agent_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a ToothFairyAI agent by ID."""
        return all_tools.get_agent(api_key, workspace_id, agent_id, region)

    @mcp.tool()
    def update_toothfairy_agent(
        api_key: str,
        workspace_id: str,
        agent_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update an existing ToothFairyAI agent."""
        return all_tools.update_agent(api_key, workspace_id, agent_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_agent(
        api_key: str,
        workspace_id: str,
        agent_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a ToothFairyAI agent. WARNING: Irreversible."""
        return all_tools.delete_agent(api_key, workspace_id, agent_id, region)

    @mcp.tool()
    def list_toothfairy_agents(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all agents in a ToothFairyAI workspace."""
        return all_tools.list_agents(api_key, workspace_id, region, limit=limit)

    @mcp.tool()
    def search_toothfairy_agents(
        api_key: str,
        workspace_id: str,
        search_term: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Search ToothFairyAI agents by label."""
        return all_tools.search_agents(api_key, workspace_id, search_term, region)

    # ========================================================================
    # AGENT FUNCTION TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_function(
        api_key: str,
        workspace_id: str,
        name: str,
        description: str,
        url: str,
        region: str = "au",
        request_type: str = "GET",
        authorisation_type: str = "none",
        parameters: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new agent function (tool) for calling external APIs."""
        return all_tools.create_agent_function(
            api_key=api_key,
            workspace_id=workspace_id,
            name=name,
            description=description,
            url=url,
            region=region,
            request_type=request_type,
            authorisation_type=authorisation_type,
            parameters=parameters,
        )

    @mcp.tool()
    def get_toothfairy_function(
        api_key: str,
        workspace_id: str,
        function_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get an agent function by ID."""
        return all_tools.get_agent_function(api_key, workspace_id, function_id, region)

    @mcp.tool()
    def update_toothfairy_function(
        api_key: str,
        workspace_id: str,
        function_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update an agent function."""
        return all_tools.update_agent_function(api_key, workspace_id, function_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_function(
        api_key: str,
        workspace_id: str,
        function_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete an agent function. WARNING: Irreversible."""
        return all_tools.delete_agent_function(api_key, workspace_id, function_id, region)

    @mcp.tool()
    def list_toothfairy_functions(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all agent functions in a workspace."""
        return all_tools.list_agent_functions(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # AUTHORISATION TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_authorisation(
        api_key: str,
        workspace_id: str,
        name: str,
        auth_type: str,
        region: str = "au",
        description: Optional[str] = None,
        token_secret: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new authorisation for storing API credentials."""
        return all_tools.create_authorisation(
            api_key=api_key,
            workspace_id=workspace_id,
            name=name,
            auth_type=auth_type,
            region=region,
            description=description,
            token_secret=token_secret,
        )

    @mcp.tool()
    def get_toothfairy_authorisation(
        api_key: str,
        workspace_id: str,
        authorisation_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get an authorisation by ID."""
        return all_tools.get_authorisation(api_key, workspace_id, authorisation_id, region)

    @mcp.tool()
    def update_toothfairy_authorisation(
        api_key: str,
        workspace_id: str,
        authorisation_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update an authorisation."""
        return all_tools.update_authorisation(api_key, workspace_id, authorisation_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_authorisation(
        api_key: str,
        workspace_id: str,
        authorisation_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete an authorisation. WARNING: Irreversible."""
        return all_tools.delete_authorisation(api_key, workspace_id, authorisation_id, region)

    @mcp.tool()
    def list_toothfairy_authorisations(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all authorisations in a workspace."""
        return all_tools.list_authorisations(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # SECRET TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_secret(
        api_key: str,
        workspace_id: str,
        authorisation_id: str,
        password_secret_value: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Create a secret linked to an authorisation."""
        return all_tools.create_secret(
            api_key=api_key,
            workspace_id=workspace_id,
            authorisation_id=authorisation_id,
            password_secret_value=password_secret_value,
            region=region,
        )

    @mcp.tool()
    def delete_toothfairy_secret(
        api_key: str,
        workspace_id: str,
        secret_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a secret. WARNING: Irreversible."""
        return all_tools.delete_secret(api_key, workspace_id, secret_id, region)

    # ========================================================================
    # DOCUMENT TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_document(
        api_key: str,
        workspace_id: str,
        title: str,
        region: str = "au",
        content: Optional[str] = None,
        folder_id: Optional[str] = None,
        topics: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a new document in the knowledge base."""
        return all_tools.create_document(
            api_key=api_key,
            workspace_id=workspace_id,
            title=title,
            region=region,
            content=content,
            folder_id=folder_id,
            topics=topics,
        )

    @mcp.tool()
    def get_toothfairy_document(
        api_key: str,
        workspace_id: str,
        document_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a document by ID."""
        return all_tools.get_document(api_key, workspace_id, document_id, region)

    @mcp.tool()
    def update_toothfairy_document(
        api_key: str,
        workspace_id: str,
        document_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a document."""
        return all_tools.update_document(api_key, workspace_id, document_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_document(
        api_key: str,
        workspace_id: str,
        document_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a document. WARNING: Irreversible."""
        return all_tools.delete_document(api_key, workspace_id, document_id, region)

    @mcp.tool()
    def list_toothfairy_documents(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
        folder_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List all documents in a workspace."""
        return all_tools.list_documents(api_key, workspace_id, region, limit=limit, folder_id=folder_id)

    @mcp.tool()
    def search_toothfairy_documents(
        api_key: str,
        workspace_id: str,
        text: str,
        region: str = "au",
        limit: int = 10,
    ) -> Dict[str, Any]:
        """Search documents by text."""
        return all_tools.search_documents(api_key, workspace_id, text, region, limit=limit)

    # ========================================================================
    # ENTITY TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_entity(
        api_key: str,
        workspace_id: str,
        label: str,
        entity_type: str,
        region: str = "au",
        description: Optional[str] = None,
        emoji: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new entity (topic, intent, or NER)."""
        return all_tools.create_entity(
            api_key=api_key,
            workspace_id=workspace_id,
            label=label,
            entity_type=entity_type,
            region=region,
            description=description,
            emoji=emoji,
        )

    @mcp.tool()
    def get_toothfairy_entity(
        api_key: str,
        workspace_id: str,
        entity_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get an entity by ID."""
        return all_tools.get_entity(api_key, workspace_id, entity_id, region)

    @mcp.tool()
    def update_toothfairy_entity(
        api_key: str,
        workspace_id: str,
        entity_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update an entity."""
        return all_tools.update_entity(api_key, workspace_id, entity_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_entity(
        api_key: str,
        workspace_id: str,
        entity_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete an entity. WARNING: Irreversible."""
        return all_tools.delete_entity(api_key, workspace_id, entity_id, region)

    @mcp.tool()
    def list_toothfairy_entities(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        entity_type: Optional[str] = None,
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all entities. Filter by type: topic, intent, ner."""
        return all_tools.list_entities(api_key, workspace_id, region, entity_type=entity_type, limit=limit)

    @mcp.tool()
    def search_toothfairy_entities(
        api_key: str,
        workspace_id: str,
        search_term: str,
        region: str = "au",
        entity_type: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Search entities by label."""
        return all_tools.search_entities(api_key, workspace_id, search_term, region, entity_type=entity_type)

    # ========================================================================
    # FOLDER TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_folder(
        api_key: str,
        workspace_id: str,
        label: str,
        region: str = "au",
        parent_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new folder for organizing documents."""
        return all_tools.create_folder(api_key, workspace_id, label, region, parent_id=parent_id)

    @mcp.tool()
    def get_toothfairy_folder(
        api_key: str,
        workspace_id: str,
        folder_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a folder by ID."""
        return all_tools.get_folder(api_key, workspace_id, folder_id, region)

    @mcp.tool()
    def update_toothfairy_folder(
        api_key: str,
        workspace_id: str,
        folder_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a folder."""
        return all_tools.update_folder(api_key, workspace_id, folder_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_folder(
        api_key: str,
        workspace_id: str,
        folder_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a folder. WARNING: Irreversible."""
        return all_tools.delete_folder(api_key, workspace_id, folder_id, region)

    @mcp.tool()
    def list_toothfairy_folders(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all folders in a workspace."""
        return all_tools.list_folders(api_key, workspace_id, region, limit=limit)

    @mcp.tool()
    def get_toothfairy_folder_tree(
        api_key: str,
        workspace_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get the complete folder tree structure."""
        return all_tools.get_folder_tree(api_key, workspace_id, region)

    # ========================================================================
    # CHAT TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_chat(
        api_key: str,
        workspace_id: str,
        agent_id: str,
        region: str = "au",
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new chat session with an agent."""
        return all_tools.create_chat(api_key, workspace_id, agent_id, region, title=title)

    @mcp.tool()
    def get_toothfairy_chat(
        api_key: str,
        workspace_id: str,
        chat_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a chat session by ID."""
        return all_tools.get_chat(api_key, workspace_id, chat_id, region)

    @mcp.tool()
    def delete_toothfairy_chat(
        api_key: str,
        workspace_id: str,
        chat_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a chat session. WARNING: Irreversible."""
        return all_tools.delete_chat(api_key, workspace_id, chat_id, region)

    @mcp.tool()
    def list_toothfairy_chats(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all chat sessions in a workspace."""
        return all_tools.list_chats(api_key, workspace_id, region, limit=limit)

    @mcp.tool()
    def send_toothfairy_message(
        api_key: str,
        workspace_id: str,
        agent_id: str,
        message: str,
        region: str = "au",
        chat_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a message to a ToothFairyAI agent and get a response."""
        return all_tools.send_message_to_agent(
            api_key=api_key,
            workspace_id=workspace_id,
            agent_id=agent_id,
            message=message,
            region=region,
            chat_id=chat_id,
        )

    # ========================================================================
    # PROMPT TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_prompt(
        api_key: str,
        workspace_id: str,
        label: str,
        interpolation_string: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Create a new prompt template."""
        return all_tools.create_prompt(api_key, workspace_id, label, interpolation_string, region)

    @mcp.tool()
    def get_toothfairy_prompt(
        api_key: str,
        workspace_id: str,
        prompt_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a prompt template by ID."""
        return all_tools.get_prompt(api_key, workspace_id, prompt_id, region)

    @mcp.tool()
    def update_toothfairy_prompt(
        api_key: str,
        workspace_id: str,
        prompt_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a prompt template."""
        return all_tools.update_prompt(api_key, workspace_id, prompt_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_prompt(
        api_key: str,
        workspace_id: str,
        prompt_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a prompt template. WARNING: Irreversible."""
        return all_tools.delete_prompt(api_key, workspace_id, prompt_id, region)

    @mcp.tool()
    def list_toothfairy_prompts(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all prompt templates in a workspace."""
        return all_tools.list_prompts(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # MEMBER TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_member(
        api_key: str,
        workspace_id: str,
        member_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a workspace member by ID."""
        return all_tools.get_member(api_key, workspace_id, member_id, region)

    @mcp.tool()
    def update_toothfairy_member(
        api_key: str,
        workspace_id: str,
        member_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a workspace member."""
        return all_tools.update_member(api_key, workspace_id, member_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_member(
        api_key: str,
        workspace_id: str,
        member_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Remove a member from workspace. WARNING: Irreversible."""
        return all_tools.delete_member(api_key, workspace_id, member_id, region)

    @mcp.tool()
    def list_toothfairy_members(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all members in a workspace."""
        return all_tools.list_members(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # CHANNEL TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_channel(
        api_key: str,
        workspace_id: str,
        name: str,
        channel: str,
        provider: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Create a new communication channel."""
        return all_tools.create_channel(api_key, workspace_id, name, channel, provider, region)

    @mcp.tool()
    def get_toothfairy_channel(
        api_key: str,
        workspace_id: str,
        channel_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a channel by ID."""
        return all_tools.get_channel(api_key, workspace_id, channel_id, region)

    @mcp.tool()
    def update_toothfairy_channel(
        api_key: str,
        workspace_id: str,
        channel_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a channel."""
        return all_tools.update_channel(api_key, workspace_id, channel_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_channel(
        api_key: str,
        workspace_id: str,
        channel_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a channel. WARNING: Irreversible."""
        return all_tools.delete_channel(api_key, workspace_id, channel_id, region)

    @mcp.tool()
    def list_toothfairy_channels(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all channels in a workspace."""
        return all_tools.list_channels(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # CONNECTION TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_connection(
        api_key: str,
        workspace_id: str,
        connection_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a database connection by ID."""
        return all_tools.get_connection(api_key, workspace_id, connection_id, region)

    @mcp.tool()
    def delete_toothfairy_connection(
        api_key: str,
        workspace_id: str,
        connection_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a connection. WARNING: Irreversible."""
        return all_tools.delete_connection(api_key, workspace_id, connection_id, region)

    @mcp.tool()
    def list_toothfairy_connections(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all database connections in a workspace."""
        return all_tools.list_connections(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # BENCHMARK TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_benchmark(
        api_key: str,
        workspace_id: str,
        name: str,
        region: str = "au",
        description: Optional[str] = None,
        questions: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new benchmark for testing agents."""
        return all_tools.create_benchmark(api_key, workspace_id, name, region, description=description, questions=questions)

    @mcp.tool()
    def get_toothfairy_benchmark(
        api_key: str,
        workspace_id: str,
        benchmark_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a benchmark by ID."""
        return all_tools.get_benchmark(api_key, workspace_id, benchmark_id, region)

    @mcp.tool()
    def update_toothfairy_benchmark(
        api_key: str,
        workspace_id: str,
        benchmark_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a benchmark."""
        return all_tools.update_benchmark(api_key, workspace_id, benchmark_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_benchmark(
        api_key: str,
        workspace_id: str,
        benchmark_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a benchmark. WARNING: Irreversible."""
        return all_tools.delete_benchmark(api_key, workspace_id, benchmark_id, region)

    @mcp.tool()
    def list_toothfairy_benchmarks(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all benchmarks in a workspace."""
        return all_tools.list_benchmarks(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # HOOK TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_hook(
        api_key: str,
        workspace_id: str,
        name: str,
        function_name: str,
        region: str = "au",
        custom_execution_code: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new hook for custom code execution."""
        return all_tools.create_hook(api_key, workspace_id, name, function_name, region, custom_execution_code=custom_execution_code)

    @mcp.tool()
    def get_toothfairy_hook(
        api_key: str,
        workspace_id: str,
        hook_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a hook by ID."""
        return all_tools.get_hook(api_key, workspace_id, hook_id, region)

    @mcp.tool()
    def update_toothfairy_hook(
        api_key: str,
        workspace_id: str,
        hook_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a hook."""
        return all_tools.update_hook(api_key, workspace_id, hook_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_hook(
        api_key: str,
        workspace_id: str,
        hook_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a hook. WARNING: Irreversible."""
        return all_tools.delete_hook(api_key, workspace_id, hook_id, region)

    @mcp.tool()
    def list_toothfairy_hooks(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all hooks in a workspace."""
        return all_tools.list_hooks(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # SCHEDULED JOB TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_scheduled_job(
        api_key: str,
        workspace_id: str,
        name: str,
        agent_id: str,
        schedule: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Create a new scheduled job."""
        return all_tools.create_scheduled_job(api_key, workspace_id, name, agent_id, schedule, region)

    @mcp.tool()
    def get_toothfairy_scheduled_job(
        api_key: str,
        workspace_id: str,
        job_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a scheduled job by ID."""
        return all_tools.get_scheduled_job(api_key, workspace_id, job_id, region)

    @mcp.tool()
    def update_toothfairy_scheduled_job(
        api_key: str,
        workspace_id: str,
        job_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a scheduled job."""
        return all_tools.update_scheduled_job(api_key, workspace_id, job_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_scheduled_job(
        api_key: str,
        workspace_id: str,
        job_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a scheduled job. WARNING: Irreversible."""
        return all_tools.delete_scheduled_job(api_key, workspace_id, job_id, region)

    @mcp.tool()
    def list_toothfairy_scheduled_jobs(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all scheduled jobs in a workspace."""
        return all_tools.list_scheduled_jobs(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # SITE TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_site(
        api_key: str,
        workspace_id: str,
        site_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a site by ID."""
        return all_tools.get_site(api_key, workspace_id, site_id, region)

    @mcp.tool()
    def update_toothfairy_site(
        api_key: str,
        workspace_id: str,
        site_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update a site."""
        return all_tools.update_site(api_key, workspace_id, site_id, region, **updates)

    @mcp.tool()
    def delete_toothfairy_site(
        api_key: str,
        workspace_id: str,
        site_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Delete a site. WARNING: Irreversible."""
        return all_tools.delete_site(api_key, workspace_id, site_id, region)

    @mcp.tool()
    def list_toothfairy_sites(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all sites in a workspace."""
        return all_tools.list_sites(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # DICTIONARY TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_dictionary_entry(
        api_key: str,
        workspace_id: str,
        entry_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a dictionary entry by ID."""
        return all_tools.get_dictionary_entry(api_key, workspace_id, entry_id, region)

    @mcp.tool()
    def list_toothfairy_dictionary_entries(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all dictionary entries in a workspace."""
        return all_tools.list_dictionary_entries(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # REQUEST LOG TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_request_log(
        api_key: str,
        workspace_id: str,
        log_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get a request log by ID."""
        return all_tools.get_request_log(api_key, workspace_id, log_id, region)

    @mcp.tool()
    def list_toothfairy_request_logs(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        limit: int = 100,
    ) -> Dict[str, Any]:
        """List all request logs in a workspace."""
        return all_tools.list_request_logs(api_key, workspace_id, region, limit=limit)

    # ========================================================================
    # SETTINGS TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_charting_settings(
        api_key: str,
        workspace_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get charting settings for the workspace."""
        return all_tools.get_charting_settings(api_key, workspace_id, region)

    @mcp.tool()
    def update_toothfairy_charting_settings(
        api_key: str,
        workspace_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update charting settings."""
        return all_tools.update_charting_settings(api_key, workspace_id, region, **updates)

    @mcp.tool()
    def get_toothfairy_embeddings_settings(
        api_key: str,
        workspace_id: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Get embeddings settings for the workspace."""
        return all_tools.get_embeddings_settings(api_key, workspace_id, region)

    @mcp.tool()
    def update_toothfairy_embeddings_settings(
        api_key: str,
        workspace_id: str,
        updates: Dict[str, Any],
        region: str = "au",
    ) -> Dict[str, Any]:
        """Update embeddings settings."""
        return all_tools.update_embeddings_settings(api_key, workspace_id, region, **updates)

    # ========================================================================
    # BILLING TOOLS
    # ========================================================================

    @mcp.tool()
    def get_toothfairy_month_costs(
        api_key: str,
        workspace_id: str,
        region: str = "au",
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get monthly costs for billing."""
        return all_tools.get_month_costs(api_key, workspace_id, region, year=year, month=month)

    # ========================================================================
    # EMBEDDINGS TOOLS
    # ========================================================================

    @mcp.tool()
    def create_toothfairy_embedding(
        api_key: str,
        workspace_id: str,
        text: str,
        region: str = "au",
    ) -> Dict[str, Any]:
        """Create text embeddings."""
        return all_tools.create_embedding(api_key, workspace_id, text, region)

    # ========================================================================
    # PUBLIC TOOLS (No authentication required)
    # ========================================================================
    # These tools access public endpoints that do not require API key or workspace ID:
    # - fetch_toothfairy_announcement: Get system announcements
    # - fetch_toothfairy_hireable_agents: Browse available agent templates
    # - fetch_ai_models_list: Get AI models and pricing information

    @mcp.tool()
    def fetch_toothfairy_announcement() -> Dict[str, Any]:
        """Fetch the latest ToothFairyAI announcement (Public endpoint - no auth required).

        Returns the latest announcement message and announcement ID,
        typically used for emergencies and important single line updates.

        This is a PUBLIC endpoint that does not require API key or workspace ID.

        Returns:
            Dict containing announcement data with fields:
            - last_announcement_int: Integer identifier for the announcement
            - announcement: The announcement message text (single line)
            - success: Boolean indicating if the request succeeded
        """
        return global_utils_tools.fetch_announcement()

    @mcp.tool()
    def fetch_toothfairy_hireable_agents(
        label: Optional[str] = None,
        description: Optional[str] = None,
        mode: Optional[str] = None,
        department: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Fetch available hireable agents with optional filtering (Public endpoint - no auth required).

        This tool retrieves the list of pre-configured agents that can be used
        as inspiration or templates when creating new agents. These agents are
        available in the ToothFairyAI marketplace/workspace.

        This is a PUBLIC endpoint that does not require API key or workspace ID.

        Use this tool when you need inspiration for creating new agents or want
        to see examples of well-configured agents for specific use cases.

        Args:
            label: Filter by agent name (case-insensitive substring match)
            description: Filter by agent description (case-insensitive substring match)
            mode: Filter by agent mode - exact match (e.g., "coder", "retriever",
                  "chatter", "planner", "voice", "speed", "accuracy", "mathematician")
            department: Filter by department - exact match (e.g., "LEGAL_AND_COMPLIANCE",
                       "OPERATIONS", "INFORMATION_TECHNOLOGY", "SALES", "MARKETING",
                       "CUSTOMER_SUPPORT", "FINANCE", "HUMAN_RESOURCES", "PRODUCT",
                       "ENGINEERING", "RESEARCH_AND_DEVELOPMENT", "ADMINISTRATION",
                       "BUSINESS_DEVELOPMENT", "STRATEGY", "DATA_SCIENCE")

        Returns:
            Dict containing:
            - success: Boolean indicating if the request succeeded
            - count: Number of agents returned
            - agents: List of agent objects with key configuration details
            - error: Error message if the request failed
        """
        return global_utils_tools.fetch_hireable_agents(
            label=label,
            description=description,
            mode=mode,
            department=department,
        )

    @mcp.tool()
    def fetch_ai_models_list() -> Dict[str, Any]:
        """Fetch the list of supported AI models with pricing (Public endpoint).

        This tool retrieves the complete list of AI models supported by ToothFairyAI,
        including pricing information and model characteristics. This is a PUBLIC endpoint
        that does not require API key or workspace ID.

        Use this tool to discover available models, their capabilities, and associated
        costs before making API calls.

        Returns:
            Dict containing:
            - success: Boolean indicating if the request succeeded
            - count: Number of models returned
            - models: List of AI models with their details including:
                - model name and provider
                - pricing information
                - context window size
                - supported features
            - error: Error message if the request failed
        """
        return global_utils_tools.fetch_models_list()
