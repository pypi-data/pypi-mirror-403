"""All ToothFairyAI SDK tools for MCP server.

This module contains all MCP tool definitions that wrap SDK operations.
Tools are organized by manager/resource type.
"""

from typing import Any, Dict, List, Optional

from .sdk_tools import get_client, success_response, error_response, to_dict


# ============================================================================
# AGENT TOOLS
# ============================================================================


def create_agent(
    api_key: str,
    workspace_id: str,
    label: str,
    mode: str,
    interpolation_string: str,
    goals: str,
    region: str = "au",
    temperature: float = 0.3,
    max_tokens: int = 4096,
    max_history: int = 10,
    top_k: int = 4,
    doc_top_k: int = 3,
    description: Optional[str] = None,
    agentic_rag: bool = False,
    has_code: bool = False,
    charting: bool = False,
    allow_internet_search: bool = False,
    allow_docs_upload: bool = True,
    allow_images_upload: bool = True,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new agent."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agents.create(
            label=label,
            mode=mode,
            interpolation_string=interpolation_string,
            goals=goals,
            temperature=temperature,
            max_tokens=max_tokens,
            max_history=max_history,
            top_k=top_k,
            doc_top_k=doc_top_k,
            description=description,
            agentic_rag=agentic_rag,
            has_code=has_code,
            charting=charting,
            allow_internet_search=allow_internet_search,
            allow_docs_upload=allow_docs_upload,
            allow_images_upload=allow_images_upload,
            **kwargs,
        )
        return success_response("Agent created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create agent: {str(e)}")


def get_agent(
    api_key: str,
    workspace_id: str,
    agent_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get agent by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agents.get(agent_id)
        return success_response("Agent retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get agent: {str(e)}")


def update_agent(
    api_key: str,
    workspace_id: str,
    agent_id: str,
    region: str = "au",
    label: Optional[str] = None,
    description: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    charting: Optional[bool] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Update an existing agent."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agents.update(
            agent_id=agent_id,
            label=label,
            description=description,
            temperature=temperature,
            max_tokens=max_tokens,
            charting=charting,
            **kwargs,
        )
        return success_response("Agent updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update agent: {str(e)}")


def delete_agent(
    api_key: str,
    workspace_id: str,
    agent_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete an agent."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.agents.delete(agent_id)
        return success_response("Agent deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete agent: {str(e)}")


def list_agents(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all agents."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agents.list(limit=limit, offset=offset)
        return success_response("Agents retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list agents: {str(e)}")


def search_agents(
    api_key: str,
    workspace_id: str,
    search_term: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Search agents by label."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agents.search(search_term)
        return success_response("Agents search completed", {"items": to_dict(result)})
    except Exception as e:
        return error_response(f"Failed to search agents: {str(e)}")


# ============================================================================
# AGENT FUNCTION TOOLS
# ============================================================================


def create_agent_function(
    api_key: str,
    workspace_id: str,
    name: str,
    description: str,
    url: str,
    region: str = "au",
    request_type: str = "GET",
    authorisation_type: str = "none",
    authorisation_key: Optional[str] = None,
    parameters: Optional[List[Dict[str, Any]]] = None,
    headers: Optional[List[Dict[str, str]]] = None,
    static_args: Optional[List[Dict[str, str]]] = None,
) -> Dict[str, Any]:
    """Create a new agent function."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agent_functions.create(
            name=name,
            description=description,
            url=url,
            request_type=request_type,
            authorisation_type=authorisation_type,
            authorisation_key=authorisation_key,
            parameters=parameters,
            headers=headers,
            static_args=static_args,
        )
        return success_response("Agent function created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create agent function: {str(e)}")


def get_agent_function(
    api_key: str,
    workspace_id: str,
    agent_function_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get agent function by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agent_functions.get(agent_function_id)
        return success_response("Agent function retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get agent function: {str(e)}")


def update_agent_function(
    api_key: str,
    workspace_id: str,
    agent_function_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update an agent function."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agent_functions.update(agent_function_id, **kwargs)
        return success_response("Agent function updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update agent function: {str(e)}")


def delete_agent_function(
    api_key: str,
    workspace_id: str,
    agent_function_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete an agent function."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.agent_functions.delete(agent_function_id)
        return success_response("Agent function deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete agent function: {str(e)}")


def list_agent_functions(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all agent functions."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.agent_functions.list(limit=limit, offset=offset)
        return success_response("Agent functions retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list agent functions: {str(e)}")


# ============================================================================
# AUTHORISATION TOOLS
# ============================================================================


def create_authorisation(
    api_key: str,
    workspace_id: str,
    name: str,
    auth_type: str,
    region: str = "au",
    description: Optional[str] = None,
    token_secret: Optional[str] = None,
    scope: Optional[str] = None,
    grant_type: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    authorization_base_url: Optional[str] = None,
    token_base_url: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a new authorisation."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.authorisations.create(
            name=name,
            auth_type=auth_type,
            description=description,
            token_secret=token_secret,
            scope=scope,
            grant_type=grant_type,
            client_id=client_id,
            client_secret=client_secret,
            authorization_base_url=authorization_base_url,
            token_base_url=token_base_url,
        )
        return success_response("Authorisation created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create authorisation: {str(e)}")


def get_authorisation(
    api_key: str,
    workspace_id: str,
    authorisation_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get authorisation by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.authorisations.get(authorisation_id)
        return success_response("Authorisation retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get authorisation: {str(e)}")


def update_authorisation(
    api_key: str,
    workspace_id: str,
    authorisation_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update an authorisation."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.authorisations.update(authorisation_id, **kwargs)
        return success_response("Authorisation updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update authorisation: {str(e)}")


def delete_authorisation(
    api_key: str,
    workspace_id: str,
    authorisation_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete an authorisation."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.authorisations.delete(authorisation_id)
        return success_response("Authorisation deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete authorisation: {str(e)}")


def list_authorisations(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all authorisations."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.authorisations.list(limit=limit, offset=offset)
        return success_response("Authorisations retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list authorisations: {str(e)}")


# ============================================================================
# SECRET TOOLS
# ============================================================================


def create_secret(
    api_key: str,
    workspace_id: str,
    authorisation_id: str,
    password_secret_value: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Create a new secret linked to an authorisation."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.secrets.create(
            authorisation_id=authorisation_id,
            password_secret_value=password_secret_value,
        )
        return success_response("Secret created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create secret: {str(e)}")


def delete_secret(
    api_key: str,
    workspace_id: str,
    secret_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a secret."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.secrets.delete(secret_id)
        return success_response("Secret deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete secret: {str(e)}")


# ============================================================================
# DOCUMENT TOOLS
# ============================================================================


def create_document(
    api_key: str,
    workspace_id: str,
    title: str,
    region: str = "au",
    content: Optional[str] = None,
    folder_id: Optional[str] = None,
    topics: Optional[List[str]] = None,
    doc_type: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new document."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.documents.create(
            title=title,
            content=content,
            folder_id=folder_id,
            topics=topics,
            doc_type=doc_type,
            **kwargs,
        )
        return success_response("Document created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create document: {str(e)}")


def get_document(
    api_key: str,
    workspace_id: str,
    document_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get document by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.documents.get(document_id)
        return success_response("Document retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get document: {str(e)}")


def update_document(
    api_key: str,
    workspace_id: str,
    document_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a document."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.documents.update(document_id, **kwargs)
        return success_response("Document updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update document: {str(e)}")


def delete_document(
    api_key: str,
    workspace_id: str,
    document_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a document."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.documents.delete(document_id)
        return success_response("Document deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete document: {str(e)}")


def list_documents(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
    folder_id: Optional[str] = None,
) -> Dict[str, Any]:
    """List all documents."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.documents.list(limit=limit, offset=offset, folder_id=folder_id)
        return success_response("Documents retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list documents: {str(e)}")


def search_documents(
    api_key: str,
    workspace_id: str,
    text: str,
    region: str = "au",
    limit: Optional[int] = None,
    topics: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Search documents by text."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.documents.search(text=text, limit=limit, topics=topics)
        return success_response("Document search completed", result)
    except Exception as e:
        return error_response(f"Failed to search documents: {str(e)}")


# ============================================================================
# ENTITY TOOLS
# ============================================================================


def create_entity(
    api_key: str,
    workspace_id: str,
    label: str,
    entity_type: str,
    region: str = "au",
    description: Optional[str] = None,
    emoji: Optional[str] = None,
    parent_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new entity (topic, intent, or NER)."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.entities.create(
            label=label,
            entity_type=entity_type,
            description=description,
            emoji=emoji,
            parent_id=parent_id,
            **kwargs,
        )
        return success_response("Entity created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create entity: {str(e)}")


def get_entity(
    api_key: str,
    workspace_id: str,
    entity_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get entity by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.entities.get(entity_id)
        return success_response("Entity retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get entity: {str(e)}")


def update_entity(
    api_key: str,
    workspace_id: str,
    entity_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update an entity."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.entities.update(entity_id, **kwargs)
        return success_response("Entity updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update entity: {str(e)}")


def delete_entity(
    api_key: str,
    workspace_id: str,
    entity_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete an entity."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.entities.delete(entity_id)
        return success_response("Entity deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete entity: {str(e)}")


def list_entities(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    entity_type: Optional[str] = None,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """List all entities."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.entities.list(entity_type=entity_type, limit=limit)
        return success_response("Entities retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list entities: {str(e)}")


def search_entities(
    api_key: str,
    workspace_id: str,
    search_term: str,
    region: str = "au",
    entity_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Search entities by label."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.entities.search(search_term, entity_type=entity_type)
        return success_response("Entity search completed", {"items": to_dict(result)})
    except Exception as e:
        return error_response(f"Failed to search entities: {str(e)}")


# ============================================================================
# FOLDER TOOLS
# ============================================================================


def create_folder(
    api_key: str,
    workspace_id: str,
    label: str,
    region: str = "au",
    parent_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new folder."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.folders.create(label=label, parent_id=parent_id, **kwargs)
        return success_response("Folder created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create folder: {str(e)}")


def get_folder(
    api_key: str,
    workspace_id: str,
    folder_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get folder by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.folders.get(folder_id)
        return success_response("Folder retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get folder: {str(e)}")


def update_folder(
    api_key: str,
    workspace_id: str,
    folder_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a folder."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.folders.update(folder_id, **kwargs)
        return success_response("Folder updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update folder: {str(e)}")


def delete_folder(
    api_key: str,
    workspace_id: str,
    folder_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a folder."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.folders.delete(folder_id)
        return success_response("Folder deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete folder: {str(e)}")


def list_folders(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all folders."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.folders.list(limit=limit, offset=offset)
        return success_response("Folders retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list folders: {str(e)}")


def get_folder_tree(
    api_key: str,
    workspace_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get the folder tree structure."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.folders.get_tree()
        return success_response("Folder tree retrieved successfully", to_dict(result))
    except Exception as e:
        return error_response(f"Failed to get folder tree: {str(e)}")


# ============================================================================
# CHAT TOOLS
# ============================================================================


def create_chat(
    api_key: str,
    workspace_id: str,
    agent_id: str,
    region: str = "au",
    title: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new chat session."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.chat.create(agent_id=agent_id, title=title, **kwargs)
        return success_response("Chat created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create chat: {str(e)}")


def get_chat(
    api_key: str,
    workspace_id: str,
    chat_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get chat by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.chat.get(chat_id)
        return success_response("Chat retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get chat: {str(e)}")


def delete_chat(
    api_key: str,
    workspace_id: str,
    chat_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a chat."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.chat.delete(chat_id)
        return success_response("Chat deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete chat: {str(e)}")


def list_chats(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all chats."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.chat.list(limit=limit, offset=offset)
        return success_response("Chats retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list chats: {str(e)}")


def send_message_to_agent(
    api_key: str,
    workspace_id: str,
    agent_id: str,
    message: str,
    region: str = "au",
    chat_id: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Send a message to an agent and get a response."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.chat.send_to_agent(
            message=message,
            agent_id=agent_id,
            chat_id=chat_id,
            **kwargs,
        )
        return success_response("Message sent successfully", result)
    except Exception as e:
        return error_response(f"Failed to send message: {str(e)}")


# ============================================================================
# PROMPT TOOLS
# ============================================================================


def create_prompt(
    api_key: str,
    workspace_id: str,
    label: str,
    interpolation_string: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Create a new prompt template."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.prompts.create(
            label=label,
            interpolation_string=interpolation_string,
            **kwargs,
        )
        return success_response("Prompt created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create prompt: {str(e)}")


def get_prompt(
    api_key: str,
    workspace_id: str,
    prompt_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get prompt by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.prompts.get(prompt_id)
        return success_response("Prompt retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get prompt: {str(e)}")


def update_prompt(
    api_key: str,
    workspace_id: str,
    prompt_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a prompt template."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.prompts.update(prompt_id, **kwargs)
        return success_response("Prompt updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update prompt: {str(e)}")


def delete_prompt(
    api_key: str,
    workspace_id: str,
    prompt_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a prompt template."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.prompts.delete(prompt_id)
        return success_response("Prompt deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete prompt: {str(e)}")


def list_prompts(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all prompts."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.prompts.list(limit=limit, offset=offset)
        return success_response("Prompts retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list prompts: {str(e)}")


# ============================================================================
# MEMBER TOOLS
# ============================================================================


def get_member(
    api_key: str,
    workspace_id: str,
    member_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get member by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.members.get(member_id)
        return success_response("Member retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get member: {str(e)}")


def update_member(
    api_key: str,
    workspace_id: str,
    member_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a member."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.members.update(member_id, **kwargs)
        return success_response("Member updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update member: {str(e)}")


def delete_member(
    api_key: str,
    workspace_id: str,
    member_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a member."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.members.delete(member_id)
        return success_response("Member deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete member: {str(e)}")


def list_members(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all members."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.members.list(limit=limit, offset=offset)
        return success_response("Members retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list members: {str(e)}")


# ============================================================================
# CHANNEL TOOLS
# ============================================================================


def create_channel(
    api_key: str,
    workspace_id: str,
    name: str,
    channel: str,
    provider: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Create a new channel."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.channels.create(
            name=name,
            channel=channel,
            provider=provider,
            **kwargs,
        )
        return success_response("Channel created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create channel: {str(e)}")


def get_channel(
    api_key: str,
    workspace_id: str,
    channel_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get channel by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.channels.get(channel_id)
        return success_response("Channel retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get channel: {str(e)}")


def update_channel(
    api_key: str,
    workspace_id: str,
    channel_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a channel."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.channels.update(channel_id, **kwargs)
        return success_response("Channel updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update channel: {str(e)}")


def delete_channel(
    api_key: str,
    workspace_id: str,
    channel_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a channel."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.channels.delete(channel_id)
        return success_response("Channel deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete channel: {str(e)}")


def list_channels(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all channels."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.channels.list(limit=limit, offset=offset)
        return success_response("Channels retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list channels: {str(e)}")


# ============================================================================
# CONNECTION TOOLS
# ============================================================================


def get_connection(
    api_key: str,
    workspace_id: str,
    connection_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get connection by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.connections.get(connection_id)
        return success_response("Connection retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get connection: {str(e)}")


def delete_connection(
    api_key: str,
    workspace_id: str,
    connection_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a connection."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.connections.delete(connection_id)
        return success_response("Connection deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete connection: {str(e)}")


def list_connections(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all connections."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.connections.list(limit=limit, offset=offset)
        return success_response("Connections retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list connections: {str(e)}")


# ============================================================================
# BENCHMARK TOOLS
# ============================================================================


def create_benchmark(
    api_key: str,
    workspace_id: str,
    name: str,
    region: str = "au",
    description: Optional[str] = None,
    questions: Optional[List[Dict[str, Any]]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new benchmark."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.benchmarks.create(
            name=name,
            description=description,
            questions=questions,
            **kwargs,
        )
        return success_response("Benchmark created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create benchmark: {str(e)}")


def get_benchmark(
    api_key: str,
    workspace_id: str,
    benchmark_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get benchmark by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.benchmarks.get(benchmark_id)
        return success_response("Benchmark retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get benchmark: {str(e)}")


def update_benchmark(
    api_key: str,
    workspace_id: str,
    benchmark_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a benchmark."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.benchmarks.update(benchmark_id, **kwargs)
        return success_response("Benchmark updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update benchmark: {str(e)}")


def delete_benchmark(
    api_key: str,
    workspace_id: str,
    benchmark_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a benchmark."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.benchmarks.delete(benchmark_id)
        return success_response("Benchmark deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete benchmark: {str(e)}")


def list_benchmarks(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all benchmarks."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.benchmarks.list(limit=limit, offset=offset)
        return success_response("Benchmarks retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list benchmarks: {str(e)}")


# ============================================================================
# HOOK TOOLS
# ============================================================================


def create_hook(
    api_key: str,
    workspace_id: str,
    name: str,
    function_name: str,
    region: str = "au",
    custom_execution_code: Optional[str] = None,
    **kwargs,
) -> Dict[str, Any]:
    """Create a new hook."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.hooks.create(
            name=name,
            function_name=function_name,
            custom_execution_code=custom_execution_code,
            **kwargs,
        )
        return success_response("Hook created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create hook: {str(e)}")


def get_hook(
    api_key: str,
    workspace_id: str,
    hook_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get hook by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.hooks.get(hook_id)
        return success_response("Hook retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get hook: {str(e)}")


def update_hook(
    api_key: str,
    workspace_id: str,
    hook_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a hook."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.hooks.update(hook_id, **kwargs)
        return success_response("Hook updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update hook: {str(e)}")


def delete_hook(
    api_key: str,
    workspace_id: str,
    hook_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a hook."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.hooks.delete(hook_id)
        return success_response("Hook deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete hook: {str(e)}")


def list_hooks(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all hooks."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.hooks.list(limit=limit, offset=offset)
        return success_response("Hooks retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list hooks: {str(e)}")


# ============================================================================
# SCHEDULED JOB TOOLS
# ============================================================================


def create_scheduled_job(
    api_key: str,
    workspace_id: str,
    name: str,
    agent_id: str,
    schedule: Dict[str, Any],
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Create a new scheduled job."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.scheduled_jobs.create(
            name=name,
            agent_id=agent_id,
            schedule=schedule,
            **kwargs,
        )
        return success_response("Scheduled job created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create scheduled job: {str(e)}")


def get_scheduled_job(
    api_key: str,
    workspace_id: str,
    scheduled_job_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get scheduled job by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.scheduled_jobs.get(scheduled_job_id)
        return success_response("Scheduled job retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get scheduled job: {str(e)}")


def update_scheduled_job(
    api_key: str,
    workspace_id: str,
    scheduled_job_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a scheduled job."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.scheduled_jobs.update(scheduled_job_id, **kwargs)
        return success_response("Scheduled job updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update scheduled job: {str(e)}")


def delete_scheduled_job(
    api_key: str,
    workspace_id: str,
    scheduled_job_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a scheduled job."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.scheduled_jobs.delete(scheduled_job_id)
        return success_response("Scheduled job deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete scheduled job: {str(e)}")


def list_scheduled_jobs(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all scheduled jobs."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.scheduled_jobs.list(limit=limit, offset=offset)
        return success_response("Scheduled jobs retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list scheduled jobs: {str(e)}")


# ============================================================================
# SITE TOOLS
# ============================================================================


def get_site(
    api_key: str,
    workspace_id: str,
    site_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get site by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.sites.get(site_id)
        return success_response("Site retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get site: {str(e)}")


def update_site(
    api_key: str,
    workspace_id: str,
    site_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update a site."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.sites.update(site_id, **kwargs)
        return success_response("Site updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update site: {str(e)}")


def delete_site(
    api_key: str,
    workspace_id: str,
    site_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Delete a site."""
    try:
        client = get_client(api_key, workspace_id, region)
        client.sites.delete(site_id)
        return success_response("Site deleted successfully")
    except Exception as e:
        return error_response(f"Failed to delete site: {str(e)}")


def list_sites(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all sites."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.sites.list(limit=limit, offset=offset)
        return success_response("Sites retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list sites: {str(e)}")


# ============================================================================
# DICTIONARY TOOLS
# ============================================================================


def get_dictionary_entry(
    api_key: str,
    workspace_id: str,
    entry_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get dictionary entry by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.dictionary.get(entry_id)
        return success_response("Dictionary entry retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get dictionary entry: {str(e)}")


def list_dictionary_entries(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all dictionary entries."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.dictionary.list(limit=limit, offset=offset)
        return success_response("Dictionary entries retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list dictionary entries: {str(e)}")


# ============================================================================
# REQUEST LOG TOOLS
# ============================================================================


def get_request_log(
    api_key: str,
    workspace_id: str,
    log_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get request log by ID."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.request_logs.get(log_id)
        return success_response("Request log retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get request log: {str(e)}")


def list_request_logs(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    limit: Optional[int] = None,
    offset: Optional[int] = None,
) -> Dict[str, Any]:
    """List all request logs."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.request_logs.list(limit=limit, offset=offset)
        return success_response("Request logs retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to list request logs: {str(e)}")


# ============================================================================
# SETTINGS TOOLS
# ============================================================================


def get_charting_settings(
    api_key: str,
    workspace_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get charting settings."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.charting_settings.get()
        return success_response("Charting settings retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get charting settings: {str(e)}")


def update_charting_settings(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update charting settings."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.charting_settings.update(**kwargs)
        return success_response("Charting settings updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update charting settings: {str(e)}")


def get_embeddings_settings(
    api_key: str,
    workspace_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Get embeddings settings."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.embeddings_settings.get()
        return success_response("Embeddings settings retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get embeddings settings: {str(e)}")


def update_embeddings_settings(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    **kwargs,
) -> Dict[str, Any]:
    """Update embeddings settings."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.embeddings_settings.update(**kwargs)
        return success_response("Embeddings settings updated successfully", result)
    except Exception as e:
        return error_response(f"Failed to update embeddings settings: {str(e)}")


# ============================================================================
# BILLING TOOLS
# ============================================================================


def get_month_costs(
    api_key: str,
    workspace_id: str,
    region: str = "au",
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Dict[str, Any]:
    """Get monthly costs."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.billing.get_month_costs(year=year, month=month)
        return success_response("Month costs retrieved successfully", result)
    except Exception as e:
        return error_response(f"Failed to get month costs: {str(e)}")


# ============================================================================
# EMBEDDINGS TOOLS
# ============================================================================


def create_embedding(
    api_key: str,
    workspace_id: str,
    text: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Create text embeddings."""
    try:
        client = get_client(api_key, workspace_id, region)
        result = client.embeddings.create(text=text)
        return success_response("Embedding created successfully", result)
    except Exception as e:
        return error_response(f"Failed to create embedding: {str(e)}")


# ============================================================================
# CREDENTIAL VALIDATION
# ============================================================================


def validate_credentials(
    api_key: str,
    workspace_id: str,
    region: str = "au",
) -> Dict[str, Any]:
    """Validate ToothFairyAI credentials."""
    try:
        client = get_client(api_key, workspace_id, region)
        # Try to list agents with limit 1 to validate credentials
        client.agents.list(limit=1)
        return success_response("Credentials validated successfully")
    except Exception as e:
        return error_response(f"Invalid credentials: {str(e)}")
