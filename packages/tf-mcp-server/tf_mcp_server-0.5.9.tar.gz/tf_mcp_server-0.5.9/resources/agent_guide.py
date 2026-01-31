"""Agent creation guide for ToothFairyAI."""

AGENT_CREATION_GUIDE = """# ToothFairyAI Agent Creation Guide

> Comprehensive documentation for creating and configuring AI agents in ToothFairyAI.
> This guide serves as the foundation for automated agent generation.

---

## Table of Contents

1. [Agent Modes Overview](#1-agent-modes-overview)
2. [Core Fields Reference](#2-core-fields-reference)
3. [Mode-Specific Configuration](#3-mode-specific-configuration)
4. [Tools System](#4-tools-system)
5. [Feature Flags & Rules](#5-feature-flags--rules)
6. [Department Configuration](#6-department-configuration)
7. [Model Configuration](#7-model-configuration)
8. [Upload Permissions](#8-upload-permissions)
9. [Voice Agent Configuration](#9-voice-agent-configuration)
10. [Orchestrator (Planner) Configuration](#10-orchestrator-planner-configuration)
11. [Field Validation Rules](#11-field-validation-rules)
12. [Best Practices](#12-best-practices)
13. [Examples](#13-examples)

---

## 1. Agent Modes Overview

The `mode` field is the most critical field that determines agent behavior and available features.

| Mode | Purpose | agenticRAG | hasCode | Key Use Cases |
|------|---------|------------|---------|---------------|
| `chatter` | Conversational, creative tasks | **NO** | Optional | Customer service, content writing, translation, Q&A |
| `retriever` | Document retrieval, analysis, research | **YES** (optional) | Optional | Research, data analysis, compliance, knowledge base |
| `coder` | Code-focused tasks | **NO** | **YES** | Code generation, formatting, programming assistance |
| `planner` | Multi-agent orchestration | **NO** | NO | Project coordination, complex workflows |
| `voice` | Real-time voice interactions | **NO** | NO | Phone support, voice assistants, appointments |

### Critical Rules

```
RULE 1: agenticRAG can ONLY be enabled for mode="retriever"
RULE 2: mode="coder" requires hasCode=true but CANNOT have agenticRAG
RULE 3: mode="planner" uses plannerAutoAgentSpawn, NOT agenticRAG
RULE 4: mode="voice" is latency-sensitive - NEVER enable agenticRAG
RULE 5: For maximum power (multi-step + code): use mode="retriever" + agenticRAG=true + hasCode=true
```

---

## 2. Core Fields Reference

### 2.1 Identity Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | String (UUID) | Yes | Unique identifier. Generate with `uuidv4()` |
| `label` | String | Yes | Display name shown to users (e.g., "Research Analyst") |
| `description` | String | Yes | Brief description of agent capabilities (1-2 sentences) |
| `__typename` | String | Yes | Always `"Agent"` |
| `workspaceID` | String | Yes | `"hireable"` for marketplace agents, or workspace UUID |

### 2.2 Behavior Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `mode` | String | Required | One of: `chatter`, `retriever`, `coder`, `planner`, `voice` |
| `agentType` | String | `"Chatbot"` | Agent type classification |
| `goals` | String | - | High-level objectives (what the agent should achieve) |
| `interpolationString` | String | - | System prompt defining agent personality and behavior |
| `customToolingInstructions` | String | - | Instructions for when/how to use specific tools |
| `placeholderInputMessage` | String | - | Placeholder text in chat input (e.g., "How can I help?") |

### 2.3 Display Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `isGlobal` | Boolean | `false` | If `true`, visible across workspaces |
| `showAgentName` | Boolean | `true` | Show agent name in chat |
| `showDocumentsReferences` | Boolean | `true` | Show document citations |
| `allowFeedback` | Boolean | `true` | Allow user feedback on responses |

### 2.4 Safety Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `inhibitionPassage` | String | - | Topics to avoid (e.g., "violence, racism, discrimination") |
| `defaultAnswer` | String | - | Response when agent cannot answer |

### 2.5 Metadata Fields

| Field | Type | Description |
|-------|------|-------------|
| `department` | String | Department classification (see Section 6) |
| `minimumSubscriptionType` | String | `"base"`, `"pro"`, or `"business"` (voice agents) |
| `_version` | Number | Schema version (typically `1`) |
| `createdAt` | String (ISO) | Creation timestamp |
| `updatedAt` | String (ISO) | Last update timestamp |
| `_lastChangedAt` | Number | Epoch timestamp |

---

## 3. Mode-Specific Configuration

### 3.1 Chatter Mode

Best for: Creative tasks, customer service, quick responses

```javascript
{
  mode: "chatter",
  agenticRAG: false,        // MUST be false
  hasCode: false,           // Usually false, can be true for code formatting
  temperature: 0.5-0.7,     // Higher for creativity
  maxTokens: 2048-8192,
  llmBaseModel: "sorcerer", // Fast model for low latency
}
```

**Use Cases:**
- Customer support (latency-sensitive)
- Content writing
- Email composition
- Translation
- General Q&A

### 3.2 Retriever Mode

Best for: Document analysis, research, complex reasoning

```javascript
{
  mode: "retriever",
  agenticRAG: true,         // Enable for multi-step autonomous tasks
  hasCode: true,            // Enable for data processing + code execution
  temperature: 0.1-0.3,     // Lower for accuracy
  maxTokens: 4096-8192,
  llmBaseModel: "mystica",  // Advanced model for complex reasoning
  topK: 7-10,               // Higher for better retrieval
  docTopK: 5-7,             // Higher for more document context
}
```

**Feature Combinations:**

| Combination | Use Case |
|-------------|----------|
| `agenticRAG: true` only | Document Q&A, compliance checks |
| `agenticRAG: true` + `hasCode: true` | Data analysis, report generation |
| `agenticRAG: true` + `hasCode: true` + `allowInternetSearch: true` | Full research capability |
| `agenticRAG: true` + `charting: true` | Data visualization |

### 3.3 Coder Mode

Best for: Pure programming tasks

```javascript
{
  mode: "coder",
  agenticRAG: false,        // MUST be false (coder mode cannot have agenticRAG)
  hasCode: true,            // MUST be true
  temperature: 0.1,         // Low for precise code
  maxTokens: 8192,
  llmBaseModel: "mystica",
}
```

**Important:** If you need code execution WITH multi-step reasoning, use `mode="retriever"` + `agenticRAG=true` + `hasCode=true` instead.

### 3.4 Planner Mode (Orchestrators)

Best for: Coordinating multiple agents

```javascript
{
  mode: "planner",
  agenticRAG: false,              // NOT used for planners
  hasCode: false,
  plannerAutoAgentSpawn: true,    // Enable dynamic agent creation
  plannerRetainsSpawnedAgents: false,
  agentsPool: [],                 // Empty for hireable agents
  maxPlanningSteps: 15,
  plannerExecutionAttempts: 3,
  allowReplanning: true,
  plannerProceedsWhenImprovementsRequired: true,
  planningInstructions: "...",    // Use instead of customToolingInstructions
}
```

### 3.5 Voice Mode

Best for: Real-time voice interactions

```javascript
{
  mode: "voice",
  agenticRAG: false,              // NEVER enable - latency critical
  hasCode: false,
  sttModel: "whisper-large-v3-turbo",
  ttsModel: "orpheus-fast",
  llmVoiceModel: "sorcerer",
  voiceName: "autumn",            // Voice persona
  defaultVoiceLanguage: "en",
  voiceMinSilenceDuration: 0.5,
  voiceMinEndpointingDelay: 0.8,
  voiceMinInterruptionDuration: 0.5,
  enableVoiceIntermissions: true,
  voiceInstructions: "...",       // Use instead of customToolingInstructions
  plainTextOutput: true,
  temperature: 0.1,               // Low for consistency
}
```

---

## 4. Tools System

### 4.1 Available Tools by Mode

Tools are referenced in `customToolingInstructions` by their `id` with `@` prefix (e.g., `@rag`, `@internet_search`).

#### Retriever Mode Tools

| Tool ID | Name | Description |
|---------|------|-------------|
| `rag` | RAG | Search and retrieve from uploaded documents |
| `internet_search` | Internet Search | Search the web for current information |
| `code_interpreter` | Code Interpreter | Execute code for data processing |
| `charting` | Charting | Create data visualizations |
| `doc_by_doc_analysis` | Cross Document Analysis | Compare across multiple documents |
| `canvas` | Canvas | Rich text/visual layout |
| `browser` | Browser | Browse web pages |
| `email` | Email | Send emails |
| `sms` | SMS | Send SMS messages |
| `messaging` | Whatsapp | Send WhatsApp messages |
| `images_retrieval` | Images Retrieval | Retrieve and analyze images |
| `scheduling` | Scheduling | Calendar/scheduling operations |
| `greeting` | Greeting | Personalized greetings |

#### Chatter Mode Tools

| Tool ID | Name | Description |
|---------|------|-------------|
| `image_creation` | Image Creation | Generate images |
| `image_adaptation` | Image Adaptation | Modify existing images |
| `video_generation` | Video Generation | Create videos |
| `3d_model_generation` | 3D Model Generation | Create 3D models |

#### Universal Tools (All Modes)

| Tool ID | Name | Description |
|---------|------|-------------|
| `deep_thinking` | Deep Thinking | Extended reasoning for complex problems |
| `long_term_memory` | Long Term Memory | Remember across sessions |
| `conversation_retrieval` | Conversation Retrieval | Recall from current conversation |
| `introspection` | Introspection | Self-reflection on approach |

### 4.2 Writing customToolingInstructions

Format: Describe WHEN and HOW to use each tool by referencing the tool `id` with `@` prefix.

**Template:**
```
Use @{tool_id} when {condition}. Use @{tool_id} for {purpose}. {Additional guidance}.
```

**IMPORTANT: Always prefix tool IDs with @ symbol**

**Example for Research Analyst:**
```javascript
customToolingInstructions: "Use @internet_search to gather current information from the web when the user needs up-to-date data, market trends, or real-time information. Use @rag to retrieve relevant information from uploaded documents and knowledge bases. Use @code_interpreter when you need to process data, perform calculations, or generate statistical analysis. Use @charting to create visual representations of data, trends, or comparisons when presenting research findings. Always cite your sources and reference specific documents when using retrieved information."
```

**Example for Document Reviewer:**
```javascript
customToolingInstructions: "Use @rag to search and retrieve specific information from uploaded documents when answering user questions. Use @doc_by_doc_analysis when you need to compare information across multiple documents or perform comprehensive cross-document analysis. Use @deep_thinking for complex document analysis that requires careful reasoning about legal terms, technical specifications, or nuanced content. Always cite specific document sections and page references when providing information."
```

### 4.3 Tool Enablement Flags

Some tools require explicit enablement via specific flags:

#### Feature Tool Flags

| Flag | Tool | Notes |
|------|------|-------|
| `hasCode: true` | `code_interpreter` | Required for code execution |
| `charting: true` | `charting` | Required for chart generation |
| `allowInternetSearch: true` | `internet_search` | Required for web search |
| `allowDeepInternetSearch: true` | Deep internet search | Extended web research |

#### Memory & Reasoning Tool Flags

| Flag | Tool | Applicable Modes | Notes |
|------|------|------------------|-------|
| `isLongTermMemoryEnabled: true` | `long_term_memory` | All modes | Remember context across sessions |
| `allowIntrospection: true` | `introspection` | All modes | Self-reflection on approach |

#### Creative Tool Flags (Chatter Mode Only)

| Flag | Tool | Notes |
|------|------|-------|
| `allowImagesGeneration: true` | `image_creation` | **Chatter mode only** - requires non-base subscription |
| `allowVideosGeneration: true` | `video_generation` | **Chatter mode only** - requires non-base subscription |
| `allow3dModelGeneration: true` | `3d_model_generation` | **Chatter mode only** - requires non-base subscription |

**Important Rules:**
- Creative generation tools (`image_creation`, `video_generation`, `3d_model_generation`) only work with `mode="chatter"`
- These require `minimumSubscriptionType` to be `"pro"` or `"business"` (not `"base"`)
- Memory tools (`long_term_memory`, `introspection`) work with all modes

#### Recommended Flag Combinations by Agent Type

```javascript
// General Assistant (chatter)
{
  isLongTermMemoryEnabled: true,
  allowIntrospection: true,
}

// Content Writer (chatter with creative tools)
{
  isLongTermMemoryEnabled: true,
  allowImagesGeneration: true,    // Enable image creation for visual content
}

// Research/Data Analyst (retriever)
{
  isLongTermMemoryEnabled: true,
  hasCode: true,
  charting: true,
  allowInternetSearch: true,
}

// Orchestrator (planner)
{
  isLongTermMemoryEnabled: true,  // Remember context across complex orchestration
}

// Voice Agent
{
  // NO additional tool flags - latency sensitive
}
```

---

## 5. Feature Flags & Rules

### 5.1 agenticRAG

Multi-step autonomous task execution.

```javascript
// VALID - retriever mode
{ mode: "retriever", agenticRAG: true }

// INVALID - other modes
{ mode: "chatter", agenticRAG: true }   // ERROR
{ mode: "coder", agenticRAG: true }     // ERROR
{ mode: "planner", agenticRAG: true }   // ERROR
{ mode: "voice", agenticRAG: true }     // ERROR
```

**When to enable:**
- Complex research tasks requiring multiple steps
- Data analysis with iterative processing
- Compliance checks with multiple document sources
- NOT for latency-sensitive applications (customer service, sales, voice)

### 5.2 hasCode

Code execution capability.

```javascript
// Enables code_interpreter tool
{ hasCode: true }

// For maximum data analysis power
{ mode: "retriever", agenticRAG: true, hasCode: true, charting: true }
```

### 5.3 Internet Search

```javascript
{
  allowInternetSearch: true,      // Basic web search
  allowDeepInternetSearch: true,  // Extended research capability
}
```

### 5.4 Multi-Language Support

```javascript
{
  isMultiLanguageEnabled: true,
  advancedLanguageDetection: true,
  defaultVoiceLanguage: "en",     // For voice agents
}
```

---

## 6. Department Configuration

### 6.1 Available Departments

| Department | Description | agenticRAG Eligible |
|------------|-------------|---------------------|
| `GENERAL` | General purpose | No |
| `CUSTOMER_SERVICE` | Customer support | **No** (latency-sensitive) |
| `SALES` | Sales support | **No** (latency-sensitive) |
| `MARKETING` | Marketing & content | **No** (creative, quick) |
| `RESEARCH_AND_DEVELOPMENT` | Research & analysis | **Yes** |
| `OPERATIONS` | Business operations | **Yes** |
| `FINANCE_AND_ACCOUNTING` | Financial tasks | No |
| `HUMAN_RESOURCES` | HR tasks | No |
| `LEGAL_AND_COMPLIANCE` | Legal & compliance | **Yes** |
| `INFORMATION_TECHNOLOGY` | IT support | **Yes** |
| `PROJECT_MANAGEMENT` | Project management | **Yes** |
| `SUPPLY_CHAIN_MANAGEMENT` | Supply chain | **Yes** |
| `QUALITY_ASSURANCE` | QA tasks | No (latency-sensitive) |
| `DATA_ANALYSIS` | Data analysis | **Yes** |

### 6.2 Feature Enablement by Department

```javascript
const featureEnablementByDepartment = {
  // Full media support + agenticRAG eligible
  RESEARCH_AND_DEVELOPMENT: {
    allowDocsUpload: true,
    allowAudiosUpload: true,
    allowVideosUpload: true,
    allowImagesUpload: true,
    agenticRAGEligible: true,
  },

  // Docs + images only, agenticRAG eligible
  LEGAL_AND_COMPLIANCE: {
    allowDocsUpload: true,
    allowAudiosUpload: false,
    allowVideosUpload: false,
    allowImagesUpload: true,
    agenticRAGEligible: true,
  },

  // Latency-sensitive - no agenticRAG
  CUSTOMER_SERVICE: {
    allowDocsUpload: true,
    allowAudiosUpload: true,
    allowVideosUpload: false,
    allowImagesUpload: true,
    agenticRAGEligible: false,
  },

  SALES: {
    allowDocsUpload: true,
    allowAudiosUpload: false,
    allowVideosUpload: false,
    allowImagesUpload: true,
    agenticRAGEligible: false,
  },
};
```

---

## 7. Model Configuration

### 7.1 Available Models

| Model | Use Case | Latency | Capability |
|-------|----------|---------|------------|
| `sorcerer` | Fast responses, voice, customer service | Low | Good |
| `mystica` | Complex reasoning, research, analysis | Medium | Advanced |

### 7.2 Model Selection Guidelines

```javascript
// Fast responses (customer service, voice, sales)
{ llmBaseModel: "sorcerer", temperature: 0.1-0.3 }

// Complex reasoning (research, analysis, compliance)
{ llmBaseModel: "mystica", temperature: 0.1-0.3 }

// Creative tasks (content writing)
{ llmBaseModel: "mystica", temperature: 0.5-0.7 }
```

### 7.3 Temperature Guidelines

| Temperature | Use Case |
|-------------|----------|
| `0.1` | Factual, precise (code, data analysis, compliance) |
| `0.2-0.3` | Balanced (research, document review) |
| `0.5` | Conversational (general assistant, email) |
| `0.7` | Creative (content writing) |

### 7.4 Token Limits

| maxTokens | Use Case |
|-----------|----------|
| `2048` | Short responses (email, quick Q&A) |
| `4096` | Standard responses (most agents) |
| `8192` | Long-form content (reports, research, analysis) |

### 7.5 Retrieval Settings

```javascript
{
  topK: 4,      // Number of chunks to retrieve (4-10)
  docTopK: 3,   // Number of documents to consider (3-7)
  maxHistory: 5-10,  // Conversation history length
}
```

**Guidelines:**
- Higher `topK` (7-10) for research and knowledge base agents
- Lower `topK` (4) for quick response agents
- Higher `docTopK` (5-7) for multi-document analysis

### 7.6 Platform Behavior Defaults

These fields control internal platform behavior and should be set for all agents:

```javascript
{
  // Adversarial/safety model configuration
  adverserialModel: "sorcerer",
  adverserialProvider: "tf",

  // Retrieval relevancy settings
  contextRelevancyRatio: 0.7,
  minRetrievalScore: 0.6,

  // Language detection
  languageDetectionConfidence: 0.9,

  // Reasoning configuration
  reasoningBudget: 1998,        // Lower for voice (2048)
  reasoningEffort: "medium",    // "none" for voice agents
  reasoningMode: "always",

  // Recency settings
  recencyImportance: 0,
  recencyTopKIncreaseFactor: 3,

  // Feature limits
  maxImagesGenerated: 4,
  maxTopics: 2,
  showCitations: true,

  // Variable per agent (set individually):
  // reRank: true/false - Enable for retriever mode agents with RAG
  // maxUrlsForInternetSearch: 5-8 - Only for agents with internet search enabled
}
```

**Variable Fields (set per agent):**

| Field | retriever + RAG | chatter | planner | voice |
|-------|-----------------|---------|---------|-------|
| `reRank` | `true` | `false` | `false` | `false` |
| `maxUrlsForInternetSearch` | `8` | N/A | `8` if enabled | `5` if enabled |

---

## 8. Upload Permissions

### 8.1 Upload Fields

```javascript
{
  allowDocsUpload: true,    // PDF, DOCX, TXT, etc.
  allowImagesUpload: true,  // PNG, JPG, etc.
  allowAudiosUpload: true,  // MP3, WAV, etc.
  allowVideosUpload: true,  // MP4, etc.
}
```

### 8.2 Recommended Configurations

| Agent Type | Docs | Images | Audio | Video |
|------------|------|--------|-------|-------|
| Research Analyst | Yes | Yes | Yes | Yes |
| Data Analyst | Yes | Yes | No | No |
| Document Reviewer | Yes | Yes | No | No |
| Meeting Summarizer | Yes | No | Yes | Yes |
| Customer Support | Yes | Yes | No | No |
| Voice Agent | No | No | No | No |
| Content Writer | Yes | Yes | No | No |

---

## 9. Voice Agent Configuration

### 9.1 Required Voice Fields

```javascript
{
  mode: "voice",

  // Models
  sttModel: "whisper-large-v3-turbo",  // Speech-to-text
  ttsModel: "orpheus-fast",             // Text-to-speech
  llmVoiceModel: "sorcerer",            // Language model for voice

  // Voice settings
  voiceName: "autumn",                  // Voice persona
  defaultVoiceLanguage: "en",

  // Timing (seconds)
  voiceMinSilenceDuration: 0.5,         // Min silence before processing
  voiceMinEndpointingDelay: 0.8,        // Delay before response
  voiceMinInterruptionDuration: 0.5,    // Min to detect interruption

  // Behavior
  enableVoiceIntermissions: true,       // Allow "um", "uh" etc.
  plainTextOutput: true,                // No markdown in voice
  voiceInstructions: "Be cheerful and friendly",
}
```

### 9.2 voiceInstructions Examples

```javascript
// Customer Support
voiceInstructions: "Be warm, patient, and professional. Speak clearly and at a moderate pace. Use a friendly, helpful tone."

// Sales
voiceInstructions: "Be enthusiastic, confident, and engaging. Show genuine interest in helping the customer find the right solution."

// Technical Support
voiceInstructions: "Be patient and clear. Break down technical instructions into simple steps. Confirm understanding before proceeding."

// Receptionist
voiceInstructions: "Be professional and welcoming. Speak clearly and efficiently. Project a positive company image."
```

### 9.3 Voice Agent Restrictions

```
- minimumSubscriptionType: "business" (voice requires business subscription)
- agenticRAG: MUST be false (latency-sensitive)
- hasCode: SHOULD be false
- reRank: SHOULD be false (latency-sensitive)
- reasoningEffort: "none" (for faster responses)
- allowDocsUpload: Usually false
- allowImagesUpload: false
- allowAudiosUpload: false
- allowVideosUpload: false
- isGlobal: Usually false (workspace-specific)
```

---

## 10. Orchestrator (Planner) Configuration

### 10.1 Required Planner Fields

```javascript
{
  mode: "planner",
  minimumSubscriptionType: "pro",       // Orchestrators require pro subscription

  // Agent spawning
  plannerAutoAgentSpawn: true,          // Enable dynamic agent creation
  plannerRetainsSpawnedAgents: false,   // Clean up after execution
  agentsPool: [],                       // Empty for hireable orchestrators

  // Execution settings
  maxPlanningSteps: 15,                 // Max steps in plan
  plannerExecutionAttempts: 3,          // Retry attempts
  allowReplanning: true,                // Allow plan adjustments
  plannerProceedsWhenImprovementsRequired: true,

  // Key settings
  agenticRAG: false,                    // NOT used for planner mode
  reRank: false,                        // Planner doesn't do RAG directly

  // Instructions (NOT customToolingInstructions)
  planningInstructions: "...",
}
```

### 10.2 planningInstructions Template

```javascript
planningInstructions: `When coordinating [task type], follow these steps:
1. Analyze the requirements and break them into phases
2. Identify the types of expertise needed
3. Spawn specialized agents for each phase:
   - [Agent Type 1] agents for [purpose]
   - [Agent Type 2] agents for [purpose]
   - [Agent Type 3] agents for [purpose]
4. Coordinate agent outputs and ensure quality
5. Synthesize results into [deliverable]

Each spawned agent should have focused expertise and clear goals.`
```

### 10.3 Orchestrator Examples

```javascript
// Project Orchestrator
planningInstructions: `When coordinating a project:
1. Analyze requirements and break into phases
2. Identify expertise needed (PM, analyst, writer, technical)
3. Spawn specialized agents:
   - Project Manager agents for timeline coordination
   - Analyst agents for research and analysis
   - Writer agents for documentation
   - Technical agents for implementation
4. Coordinate outputs and ensure quality
5. Synthesize into cohesive deliverable`

// Research Orchestrator
planningInstructions: `When conducting research:
1. Analyze research question and identify key areas
2. Break down into sub-topics
3. Spawn specialized agents:
   - Web Research agents for internet searches
   - Data Analyst agents for quantitative analysis
   - Domain Expert agents for specialized knowledge
   - Literature Review agents for academic sources
4. Coordinate to avoid duplication
5. Synthesize into structured report with citations`
```

---

## 11. Field Validation Rules

### 11.1 Required Fields

Every agent MUST have:
- `id` (UUID)
- `label`
- `description`
- `mode`
- `__typename` ("Agent")
- `workspaceID`
- `interpolationString`
- `goals`

### 11.2 Conditional Requirements

```javascript
// If mode="voice"
REQUIRED: sttModel, ttsModel, llmVoiceModel, voiceName, voiceInstructions

// If mode="planner"
REQUIRED: planningInstructions
RECOMMENDED: plannerAutoAgentSpawn, maxPlanningSteps

// If mode="coder"
REQUIRED: hasCode=true

// If agenticRAG=true
REQUIRED: mode="retriever"

// If hasCode=true and mode="retriever"
RECOMMENDED: customToolingInstructions mentioning code_interpreter
```

### 11.3 Mutual Exclusions

```javascript
// These combinations are INVALID
{ mode: "chatter", agenticRAG: true }     // ERROR
{ mode: "coder", agenticRAG: true }       // ERROR
{ mode: "planner", agenticRAG: true }     // ERROR
{ mode: "voice", agenticRAG: true }       // ERROR
{ mode: "coder", hasCode: false }         // ERROR (implicit)
```

---

## 12. Best Practices

### 12.1 Naming Conventions

```javascript
// Label: Clear, descriptive (2-4 words)
label: "Research Analyst"           // Good
label: "Data Analyst"               // Good
label: "Agent for Analyzing Data"   // Too verbose

// Description: Brief capability summary (1-2 sentences)
description: "An expert research assistant that conducts comprehensive research using internet search, document analysis, and data processing."
```

### 12.2 interpolationString Guidelines

Structure:
1. Role definition ("You are a...")
2. Primary responsibilities
3. Behavioral guidelines
4. Edge case handling

```javascript
interpolationString: "You are a Research Analyst with expertise in conducting comprehensive research across multiple domains. Your task is to gather, analyze, and synthesize information from various sources including the internet and documents. Provide well-structured, fact-based reports with proper citations. Use data analysis and visualization when appropriate to support your findings."
```

### 12.3 goals Guidelines

- Use action verbs
- Be specific about outcomes
- Include 2-4 goals

```javascript
goals: "Conduct thorough research on any topic. Synthesize information from multiple sources. Provide well-structured reports with citations and data analysis."
```

### 12.4 Latency Considerations

**Low Latency Required (use sorcerer, disable agenticRAG):**
- Customer service
- Sales support
- Voice agents
- Live chat

**Latency Acceptable (use mystica, enable agenticRAG):**
- Research tasks
- Data analysis
- Report generation
- Compliance checks

### 12.5 Avoid Over-Configuration

```javascript
// Don't enable everything - be intentional
// BAD: Enables everything
{
  agenticRAG: true,
  hasCode: true,
  charting: true,
  allowInternetSearch: true,
  allowDeepInternetSearch: true,
  allowDocsUpload: true,
  allowAudiosUpload: true,
  allowVideosUpload: true,
  allowImagesUpload: true,
}

// GOOD: Enable only what's needed for the use case
// For a Document Reviewer:
{
  agenticRAG: true,
  hasCode: false,
  charting: false,
  allowInternetSearch: false,
  allowDocsUpload: true,
  allowImagesUpload: true,
  allowAudiosUpload: false,
  allowVideosUpload: false,
}
```

---

## 13. Examples

### 13.1 Complete Chatter Agent (General Assistant)

```javascript
{
  id: uuidv4(),
  __typename: "Agent",
  workspaceID: "hireable",
  agentType: "Chatbot",

  // Identity
  label: "General Assistant",
  description: "A versatile general-purpose assistant for answering questions and helping with everyday tasks.",

  // Mode & Features
  mode: "chatter",
  agenticRAG: false,
  hasCode: false,

  // Model settings
  llmProvider: "tf",
  llmBaseModel: "sorcerer",
  temperature: 0.5,
  maxTokens: 4096,
  maxHistory: 10,
  topK: 4,
  docTopK: 3,

  // Behavior
  goals: "Provide helpful, accurate, and concise answers to user questions. Assist with a wide variety of general inquiries and tasks.",
  interpolationString: "You are a friendly and knowledgeable General Assistant. Your role is to help users with a wide variety of questions and tasks. Provide clear, accurate, and helpful responses. Be conversational and approachable while maintaining professionalism. If you don't know something, acknowledge it honestly rather than guessing.",
  customToolingInstructions: "Use @deep_thinking when the user asks complex questions that require careful reasoning. Use @long_term_memory to remember user preferences and past topics. Use @conversation_retrieval to recall relevant information from earlier in the conversation.",
  placeholderInputMessage: "How can I help you today?",

  // Safety
  inhibitionPassage: "Talking about violence, racism or discrimination",
  defaultAnswer: "I cannot answer this question, do you mind asking something different?",

  // Display
  isGlobal: true,
  allowFeedback: true,
  showDocumentsReferences: true,
  showAgentName: true,

  // Uploads
  allowDocsUpload: true,
  allowImagesUpload: true,
  allowAudiosUpload: false,
  allowVideosUpload: false,

  // Tool enable flags
  isLongTermMemoryEnabled: true,
  allowIntrospection: true,

  // Metadata
  department: "GENERAL",
  minimumSubscriptionType: "base",
  _version: 1,
}
```

### 13.2 Complete Retriever Agent (Data Analyst)

```javascript
{
  id: uuidv4(),
  __typename: "Agent",
  workspaceID: "hireable",
  agentType: "Chatbot",

  // Identity
  label: "Data Analyst",
  description: "A powerful data analysis agent capable of processing datasets, performing statistical analysis, and creating visualizations.",

  // Mode & Features - MAXIMUM POWER CONFIG
  mode: "retriever",
  agenticRAG: true,           // Multi-step autonomous execution
  hasCode: true,              // Code execution
  charting: true,             // Data visualization
  allowInternetSearch: true,  // Web search for benchmarks

  // Model settings
  llmProvider: "tf",
  llmBaseModel: "mystica",    // Advanced reasoning
  temperature: 0.1,           // Precise
  maxTokens: 8192,
  maxHistory: 5,
  topK: 7,
  docTopK: 5,

  // Behavior
  goals: "Analyze data sets and extract meaningful insights. Perform statistical analysis and create clear visualizations. Provide actionable recommendations based on data.",
  interpolationString: "You are a Data Analyst with expertise in data processing, statistical analysis, and visualization. Your role is to help users understand their data through thorough analysis. Use code execution to process data, calculate statistics, and generate charts. Present your findings clearly with actionable insights.",
  customToolingInstructions: "Use @code_interpreter for data manipulation, statistical calculations, and complex computations. Use @charting to create visual representations including bar charts, line graphs, pie charts, and scatter plots. Use @rag to retrieve relevant context from uploaded datasets. Use @internet_search for benchmarks and comparative data. Always explain your methodology and present findings with supporting visualizations.",
  placeholderInputMessage: "Upload your data or describe what you'd like me to analyze.",

  // Safety
  inhibitionPassage: "Talking about violence, racism or discrimination",
  defaultAnswer: "I cannot answer this question, do you mind asking something different?",

  // Display
  isGlobal: true,
  allowFeedback: true,
  showDocumentsReferences: true,
  showAgentName: true,

  // Uploads
  allowDocsUpload: true,
  allowImagesUpload: true,
  allowAudiosUpload: false,
  allowVideosUpload: false,

  // Tool enable flags
  isLongTermMemoryEnabled: true,

  // Metadata
  department: "RESEARCH_AND_DEVELOPMENT",
  minimumSubscriptionType: "pro",
  _version: 1,
}
```

### 13.3 Complete Voice Agent

```javascript
{
  id: uuidv4(),
  __typename: "Agent",
  workspaceID: "hireable",
  agentType: "Chatbot",

  // Identity
  label: "Voice Customer Support",
  description: "A friendly voice assistant for handling customer support inquiries via phone or web voice channels.",

  // Mode & Features
  mode: "voice",
  agenticRAG: false,          // NEVER for voice
  hasCode: false,

  // Voice-specific models
  sttModel: "whisper-large-v3-turbo",
  ttsModel: "orpheus-fast",
  llmVoiceModel: "sorcerer",
  llmBaseModel: "sorcerer",
  voiceName: "autumn",
  defaultVoiceLanguage: "en",

  // Voice timing
  voiceMinSilenceDuration: 0.5,
  voiceMinEndpointingDelay: 0.8,
  voiceMinInterruptionDuration: 0.5,
  enableVoiceIntermissions: true,

  // Model settings
  llmProvider: "tf",
  temperature: 0.1,
  maxTokens: 8192,
  maxHistory: 5,
  topK: 4,
  docTopK: 3,
  plainTextOutput: true,

  // Behavior
  goals: "Provide helpful and friendly customer support via voice. Resolve inquiries efficiently while maintaining a warm, professional tone.",
  interpolationString: "You are a Voice Customer Support agent providing assistance through voice calls. Speak naturally and conversationally. Be warm, patient, and helpful. Listen carefully to customer concerns and provide clear, concise solutions. If you cannot resolve an issue, offer to escalate or provide alternative options.",
  voiceInstructions: "Be warm, patient, and professional. Speak clearly and at a moderate pace. Use a friendly, helpful tone.",
  placeholderInputMessage: "Hello! How can I help you today?",

  // Safety
  inhibitionPassage: "Talking about violence, racism or discrimination",
  defaultAnswer: "I'm sorry, I didn't quite understand that. Could you please rephrase?",

  // Display
  isGlobal: false,            // Voice agents typically workspace-specific
  allowFeedback: true,

  // Uploads - disabled for voice
  allowDocsUpload: false,
  allowImagesUpload: false,
  allowAudiosUpload: false,
  allowVideosUpload: false,

  // Metadata
  department: "CUSTOMER_SERVICE",
  minimumSubscriptionType: "pro",
  _version: 1,
}
```

### 13.4 Complete Orchestrator Agent

```javascript
{
  id: uuidv4(),
  __typename: "Agent",
  workspaceID: "hireable",
  agentType: "Chatbot",

  // Identity
  label: "Research Orchestrator",
  description: "Conducts comprehensive research by coordinating multiple research agents to gather, analyze, and synthesize information from diverse sources.",

  // Mode & Features
  mode: "planner",
  agenticRAG: false,                    // NOT used for planners
  hasCode: false,

  // Orchestrator-specific
  plannerAutoAgentSpawn: true,          // Enable dynamic agent creation
  plannerRetainsSpawnedAgents: false,
  agentsPool: [],
  maxPlanningSteps: 15,
  plannerExecutionAttempts: 3,
  allowReplanning: true,
  plannerProceedsWhenImprovementsRequired: true,
  allowInternetSearch: true,
  allowDeepInternetSearch: true,

  // Model settings
  llmProvider: "tf",
  llmBaseModel: "mystica",
  temperature: 0.3,
  maxTokens: 8192,
  maxHistory: 10,
  topK: 4,
  docTopK: 3,

  // Behavior
  goals: "Coordinate thorough research across multiple domains. Spawn researcher and analyst agents to cover different angles. Produce comprehensive, well-cited research reports.",
  interpolationString: "You are a Research Orchestrator, an advanced AI coordinator for comprehensive research tasks. Your role is to break down research questions into components, spawn specialized researcher agents to investigate different aspects, and synthesize their findings into comprehensive reports.",
  planningInstructions: `When conducting research, follow these steps:
1. Analyze the research question and identify key areas to investigate
2. Break down the topic into sub-topics that need exploration
3. Spawn specialized agents for each research area:
   - Web Research agents for internet searches and current information
   - Data Analyst agents for quantitative analysis
   - Domain Expert agents for specialized knowledge areas
   - Literature Review agents for academic and industry sources
4. Coordinate agents to avoid duplication and ensure comprehensive coverage
5. Synthesize findings into a structured research report with citations

Each spawned agent should focus on a specific aspect of the research. Cross-reference findings for accuracy.`,
  placeholderInputMessage: "What research topic would you like me to investigate comprehensively?",

  // Safety
  inhibitionPassage: "Talking about violence, racism or discrimination",
  defaultAnswer: "I cannot answer this question, do you mind asking something different?",

  // Display
  isGlobal: true,
  allowFeedback: true,
  showDocumentsReferences: true,
  showAgentName: true,

  // Uploads
  allowDocsUpload: true,
  allowImagesUpload: true,
  allowAudiosUpload: false,
  allowVideosUpload: false,

  // Tool enable flags
  isLongTermMemoryEnabled: true,

  // Metadata
  department: "RESEARCH_AND_DEVELOPMENT",
  minimumSubscriptionType: "pro",
  _version: 1,
}
```

---

## Quick Reference Card

### Mode Selection

```
Customer Support -> chatter + sorcerer
Sales Support -> chatter + sorcerer
Content Writing -> chatter + mystica
Translation -> chatter + sorcerer

Document Analysis -> retriever + agenticRAG
Research -> retriever + agenticRAG + internet_search
Data Analysis -> retriever + agenticRAG + hasCode + charting
Report Generation -> retriever + agenticRAG + hasCode + charting

Code Tasks -> coder + hasCode (or retriever + agenticRAG + hasCode for multi-step)

Multi-Agent Coordination -> planner + plannerAutoAgentSpawn

Voice/Phone -> voice + STT/TTS models
```

### Tool Quick Reference

**Note:** In `customToolingInstructions`, prefix tool IDs with `@` (e.g., `@rag`, `@internet_search`). This applies also for custom tools such as API and MCPs.

```
mode="retriever": rag, internet_search, code_interpreter, charting, doc_by_doc_analysis, canvas, browser, email, sms, messaging, images_retrieval, scheduling
mode="chatter": image_creation, image_adaptation, video_generation, 3d_model_generation
mode="all": deep_thinking, long_term_memory, conversation_retrieval, introspection
mode="planner": Uses planningInstructions (not tools)
mode="voice": Uses voiceInstructions (not tools)
```
"""


def get_agent_creation_guide() -> str:
    """Return the full agent creation guide."""
    return AGENT_CREATION_GUIDE


def get_agent_creation_section(section: str) -> str:
    """
    Get a specific section of the agent creation guide.

    Args:
        section: Section name (e.g., "modes", "tools", "voice", "planner", "examples")

    Returns:
        The requested section content or error message
    """
    section_mapping = {
        "modes": "## 1. Agent Modes Overview",
        "core-fields": "## 2. Core Fields Reference",
        "mode-config": "## 3. Mode-Specific Configuration",
        "tools": "## 4. Tools System",
        "features": "## 5. Feature Flags & Rules",
        "departments": "## 6. Department Configuration",
        "models": "## 7. Model Configuration",
        "uploads": "## 8. Upload Permissions",
        "voice": "## 9. Voice Agent Configuration",
        "planner": "## 10. Orchestrator (Planner) Configuration",
        "validation": "## 11. Field Validation Rules",
        "best-practices": "## 12. Best Practices",
        "examples": "## 13. Examples",
        "quick-reference": "## Quick Reference Card",
    }

    section_key = section.lower().replace(" ", "-")

    if section_key not in section_mapping:
        available = ", ".join(section_mapping.keys())
        return f"Section '{section}' not found. Available sections: {available}"

    start_marker = section_mapping[section_key]

    # Find the next section marker
    section_keys = list(section_mapping.keys())
    current_idx = section_keys.index(section_key)

    start_pos = AGENT_CREATION_GUIDE.find(start_marker)
    if start_pos == -1:
        return f"Section '{section}' content not found in guide."

    # Find end of section
    if current_idx + 1 < len(section_keys):
        next_marker = section_mapping[section_keys[current_idx + 1]]
        end_pos = AGENT_CREATION_GUIDE.find(next_marker)
        if end_pos == -1:
            end_pos = len(AGENT_CREATION_GUIDE)
    else:
        end_pos = len(AGENT_CREATION_GUIDE)

    return AGENT_CREATION_GUIDE[start_pos:end_pos].strip()
