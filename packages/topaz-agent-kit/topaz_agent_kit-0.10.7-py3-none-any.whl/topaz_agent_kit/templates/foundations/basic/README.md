<div align="center">
  <img src="ui/static/assets/brand-logo.svg" alt="Project Logo" width="200"/>
</div>

# My Agent Project

Welcome to your agent project! This is a minimal, functional setup built with **Topaz Agent Kit** that includes an example pipeline and several independent agents ready to use.

## 🎯 What is Topaz Agent Kit?

**Topaz Agent Kit** is a powerful, config-driven multi-agent orchestration framework that enables you to build sophisticated AI agent workflows quickly and easily. Instead of writing complex code from scratch, you define your agents and pipelines using simple YAML configuration files.

### Key Features

- **🔄 Multi-Framework Support**: Build agents using LangGraph, CrewAI, Agno, ADK, OAK, Semantic Kernel, or MAF — all in one unified system
- **🤖 Multiple LLM Providers**: Azure OpenAI, OpenAI, Google AI, Anthropic, and Ollama (local models)
- **🧰 Rich Tool Ecosystem**: Access 50+ pre-built tools via MCP (Model Context Protocol) for document processing, web search, email, travel, and more
- **🔀 10 Execution Patterns**: Sequential, parallel, conditional, switch, loop, repeat, handoff, group chat, pipeline composition, and nested patterns
- **⚡ Event-Driven Pipelines**: Automatic pipeline execution triggered by file system events, webhooks, or custom triggers
- **🌐 Remote Agents (A2A)**: Deploy agents as microservices with the Agent-to-Agent protocol
- **🎛️ Modern Web UI**: Interactive web interface with real-time agent visualization, file uploads, and session management
- **📄 Document Intelligence**: Built-in RAG (Retrieval-Augmented Generation) with document upload, analysis, and semantic search
- **🚪 Human-in-the-Loop**: Approval gates, input prompts, and selection gates for interactive workflows
- **🧠 AgentOS Memory**: Filesystem-based memory system with Unix-like commands for persistent agent memory, shared templates, and semantic search
- **⚡ Rapid Development**: Go from idea to working demo in hours, not weeks

### What This Basic Project Includes

This basic template provides:

- ✅ **Example Pipeline**: A simple `hello_agent` pipeline to get you started
- ✅ **Independent Agents**: Five ready-to-use agents (content_analyzer, rag_query, content_extractor, image_extractor, web_search)
- ✅ **MCP Integration**: Pre-configured MCP server for tool access
- ✅ **Web UI**: Full-featured web interface for interacting with your agents
- ✅ **Project Structure**: Organized configuration files and auto-generated code

## 📋 Table of Contents

- [Quick Start](#quick-start)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Branding & Customization](#branding--customization)
- [AI-Assisted Pipeline Generation](#ai-assisted-pipeline-generation)
- [Adding a New Pipeline](#adding-a-new-pipeline)
- [Agent Configuration](#agent-configuration)
  - [Model Providers](#model-providers)
  - [Remote Agents (A2A)](#remote-agents-a2a)
  - [Local Tools](#local-tools)
- [Standard Operating Procedures (SOPs)](#standard-operating-procedures-sops)
- [Pipeline Patterns](#pipeline-patterns)
- [Human-in-the-Loop Gates](#human-in-the-loop-gates)
- [Scripts & Data Setup](#scripts--data-setup)
- [Running Your Project](#running-your-project)
- [Next Steps](#next-steps)
- [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

1. **Set up your environment variables** (see [Environment Setup](#environment-setup))
2. **Start the services**:
   ```bash
   topaz-agent-kit serve fastapi --project .
   ```
3. **Open your browser** to `http://127.0.0.1:8090`

## 🔧 Environment Setup

### Step 1: Create Your `.env` File

Copy the example environment file:

```bash
cp .env.example .env
```

### Step 2: Configure Required Variables

Open `.env` and fill in the required values. The basic template uses **Azure OpenAI** by default, so you need:

```bash
# Azure OpenAI Configuration (Required)
AZURE_OPENAI_API_BASE=https://your-resource.openai.azure.com
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT=your-deployment-name
AZURE_OPENAI_MODEL=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview
```

**Note**: If you want to use a different model provider (Google AI, Ollama), you'll need to:
1. Update the `model` field in your agent YAML files
2. Add the corresponding environment variables (see `.env.example` for all options)

### Optional: Other Model Providers

If you want to use other providers, uncomment and configure the relevant sections in `.env`:

- **Google AI**: `GOOGLE_API_KEY` (for Gemini models)
- **Ollama**: `OLLAMA_BASE_URL` (defaults to `http://localhost:11434` for local models)

### Optional: MCP Toolkits

If you plan to use MCP toolkits, you'll need to configure the corresponding API keys:

- **Web Search**: `SERPER_API_KEY` (for Serper API) or `TAVILY_API_KEY` (for Tavily)
- **SEC API**: `SEC_API_KEY` (for SEC filings search)
- **Amadeus Travel**: `AMADEUS_CLIENT_ID` and `AMADEUS_CLIENT_SECRET` (for flights, hotels, activities)
- **Gmail**: `GMAIL_CREDENTIALS_PATH` (path to `client_secret.json` for email operations)
- **Browser Automation**: `BROWSERLESS_API_KEY` (for browser automation tools)

See `.env.example` for all available options.

## 📁 Project Structure

```
.
├── config/
│   ├── pipeline.yml              # Main pipeline configuration
│   ├── ui_manifest.yml           # Global UI configuration
│   ├── agents/                   # Agent configurations
│   │   ├── hello_agent.yml       # Example agent
│   │   ├── content_analyzer.yml  # Independent agents
│   │   ├── rag_query.yml
│   │   └── ...
│   ├── pipelines/                # Individual pipeline definitions
│   │   └── example.yml           # Example pipeline
│   ├── prompts/                  # Jinja2 prompt templates
│   │   ├── hello_agent.jinja
│   │   └── ...
│   └── ui_manifests/             # Pipeline-specific UI configs
│       ├── example.yml
│       └── independent_agents.yml
├── docs/                        # Documentation
│   └── workflows/
│       └── pipeline_generation/ # AI workflow reference docs
├── rules/                       # AI assistant rules
│   └── pipeline_generation.mdc  # Cursor rule for pipeline creation
├── agents/                      # Generated agent code (auto-generated)
├── services/                    # Generated service code (auto-generated)
├── ui/                          # UI assets
│   └── static/
│       └── assets/              # Logos, icons, workflow diagrams
│           ├── brand-logo.svg   # Your brand logo (replace this)
│           └── brand-icon.svg   # Your brand icon (replace this)
├── data/                        # Runtime data (created automatically)
│   ├── chat.db                  # Chat history
│   ├── chroma_db/               # Vector database
│   ├── rag_files/               # RAG document storage
│   └── user_files/              # User-uploaded files
├── .env                         # Your environment variables (create from .env.example)
└── README.md                    # This file
```

## 🎨 Branding & Customization

### Replacing the Logo

The project includes a **placeholder logo** (`ui/static/assets/brand-logo.svg`) that displays "YOUR BRAND LOGO". You should replace this with your own company/project logo.

**Option 1: Replace the placeholder file directly**

```bash
# Replace with your own logo (SVG or PNG)
cp /path/to/your-logo.svg ui/static/assets/brand-logo.svg

# Or if using PNG
cp /path/to/your-logo.png ui/static/assets/brand-logo.png
```

If using a different filename or format, update `config/ui_manifest.yml`:

```yaml
brand:
  logo: "assets/your-logo.png"      # Your main logo
  logo2: "assets/tak-logo.png"      # Secondary logo (Topaz Agent Kit)
```

**Option 2: Keep your logo with a custom name**

1. Copy your logo to `ui/static/assets/`:
   ```bash
   cp /path/to/acme-logo.png ui/static/assets/acme-logo.png
   ```

2. Update `config/ui_manifest.yml`:
   ```yaml
   brand:
     logo: "assets/acme-logo.png"
     logo2: "assets/tak-logo.png"
   ```

**Logo specifications:**
- **Dimensions**: 1050 x 750 pixels (or similar aspect ratio ~1.4:1)
- **Format**: SVG (preferred) or PNG with transparency
- **Location**: `ui/static/assets/`

### Customizing the UI

Edit `config/ui_manifest.yml` to customize:

| Setting | Location | Description |
|---------|----------|-------------|
| **Project Title** | `title` | Main heading in the UI |
| **Subtitle** | `subtitle` | Description shown below title |
| **Theme** | `appearance.default_theme` | `system`, `light`, or `dark` |
| **Accent Color** | `appearance.default_accent` | HSL color value (e.g., `"210 92% 56%"`) |
| **Chat Placeholder** | `chat.placeholder` | Input field placeholder text |
| **Footer** | `footer.text` | Footer text (`{{year}}` = current year) |

**Example customization:**

```yaml
title: "Acme AI Assistant"
subtitle: "Intelligent automation for your business"

brand:
  logo: "assets/acme-logo.png"    # Your company logo
  logo2: "assets/tak-logo.png"    # Topaz Agent Kit branding

appearance:
  default_theme: "dark"
  default_accent: "142 76% 36%"   # Green accent

footer:
  text: "© {{year}} Acme Corp — Powered by Topaz Agent Kit"
```

---

## 🤖 AI-Assisted Pipeline Generation

This project includes a structured workflow for creating new pipelines with AI assistance. If you're using **Cursor IDE** or another AI-powered editor, you can leverage the included rules and documentation for guided pipeline creation.

### What's Included

| Folder | Purpose |
|--------|---------|
| `rules/pipeline_generation.mdc` | Cursor rule that guides the AI through a 5-step workflow |
| `docs/workflows/pipeline_generation/` | Detailed reference documentation for each step |

### How to Use (Cursor IDE)

1. **Enable the Rule**: Copy `rules/pipeline_generation.mdc` to your `.cursor/rules/` folder:
   ```bash
   mkdir -p .cursor/rules
   cp rules/pipeline_generation.mdc .cursor/rules/
   ```

2. **Start the Workflow**: In Cursor chat, say:
   > "Follow the pipeline generation workflow to create a new pipeline for [your use case]"

3. **Follow the Steps**: The AI will guide you through:
   - **Step 1**: Requirements gathering (use case, agents, patterns)
   - **Step 2**: Workflow design (execution pattern, HITL gates)
   - **Step 3**: Interactive refinement (feedback and adjustments)
   - **Step 4**: File generation (configs, prompts, icons)
   - **Step 5**: Validation and testing

### Reference Documentation

The `docs/workflows/pipeline_generation/` folder contains detailed references:

| File | Contents |
|------|----------|
| `README.md` | Overview and quick start |
| `step1_requirements.md` | Requirements gathering guide |
| `step2_design.md` | Workflow design patterns |
| `step3_refinement.md` | Refinement process |
| `step4_generation.md` | File generation details |
| `step5_validation.md` | Validation checklist |
| `reference_patterns.md` | All 9 execution patterns with examples |
| `reference_hitl.md` | Human-in-the-loop gate configurations |
| `reference_jinja.md` | Jinja2 variable syntax and filters |
| `reference_icons.md` | SVG icon templates |
| `reference_troubleshooting.md` | Common issues and solutions |

### Without AI Assistance

If you prefer to create pipelines manually, see the [Adding a New Pipeline](#adding-a-new-pipeline) section below. The reference documentation in `docs/workflows/pipeline_generation/` is still useful for understanding patterns and best practices.

---

## ➕ Adding a New Pipeline

### Step 1: Create the Pipeline Configuration

Create a new file in `config/pipelines/` (e.g., `config/pipelines/my_pipeline.yml`):

```yaml
name: "My Pipeline"
description: "Description of what this pipeline does"

nodes:
  - id: my_agent
    config_file: agents/my_agent.yml

pattern:
  type: sequential
  steps:
    - node: my_agent
```

### Step 2: Create Agent Configuration

Create `config/agents/my_agent.yml`:

```yaml
id: my_agent
type: agno
model: "azure_openai"
run_mode: "local"

prompt:
  instruction:
    jinja: prompts/my_agent.jinja
  inputs:
    inline: |
      - User Query: {{user_text}}

outputs:
  final:
    selectors:
      - response
    selector_mode: "first"
    transform: |
      {{ value.response }}
```

### Step 3: Create Prompt Template

Create `config/prompts/my_agent.jinja`:

```jinja
You are a helpful assistant. Respond to user queries.

## Guidelines:
- Be clear and concise
- Provide accurate information

## Response:
Provide a helpful response to the user's query.
```

### Step 4: Register the Pipeline

Add your pipeline to `config/pipeline.yml`:

```yaml
pipelines:
  - id: example
    config_file: pipelines/example.yml
  - id: my_pipeline
    config_file: pipelines/my_pipeline.yml  # Add this line
```

### Step 5: Create UI Manifest (Optional)

Create `config/ui_manifests/my_pipeline.yml`:

```yaml
title: "My Pipeline"
subtitle: "Description of what this pipeline does"

agents:
  - id: my_agent
    title: "My Agent"
    subtitle: "Agent description"
    icon: "assets/my_agent.svg"

interaction_diagram: "assets/my_pipeline_workflow.svg"
```

And add it to `config/ui_manifest.yml`:

```yaml
pipelines:
  - id: "example"
    title: "Example Pipeline"
    ui_manifest: "ui_manifests/example.yml"
  - id: "my_pipeline"
    title: "My Pipeline"
    ui_manifest: "ui_manifests/my_pipeline.yml"  # Add this
```

### Step 6: Generate Code

After creating your configuration files, regenerate the agent and service code:

```bash
topaz-agent-kit generate agents --project .
topaz-agent-kit generate services --project .
topaz-agent-kit generate diagrams --project .
```

---

## ⚙️ Agent Configuration

### Model Providers

Topaz Agent Kit supports multiple LLM providers. Configure the `model` field in your agent YAML:

| Provider | Model Value | Required Environment Variables |
|----------|-------------|-------------------------------|
| **Azure OpenAI** | `azure_openai` | `AZURE_OPENAI_API_BASE`, `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_DEPLOYMENT` |

**Example Agent with OpenAI:**

```yaml
id: my_agent
type: agno
model: "openai"  # Uses OPENAI_API_KEY from .env
run_mode: "local"
```

**Example with Ollama (local models):**

```yaml
id: local_agent
type: agno
model: "ollama_llama3.2:latest"  # Format: ollama_<model_name>
run_mode: "local"
```

### Remote Agents (A2A)

Agents can run locally (in-process) or remotely via the A2A (Agent-to-Agent) protocol. Remote agents run as separate services and communicate over HTTP.

**Local Agent (default):**

```yaml
id: my_agent
type: agno
model: "azure_openai"
run_mode: "local"  # Runs in the same process
```

**Remote Agent:**

```yaml
id: my_remote_agent
type: agno
model: "azure_openai"
run_mode: "remote"  # Runs as separate A2A service
```

**When to Use Remote Agents:**
- **Scaling**: Run multiple instances of compute-heavy agents
- **Isolation**: Keep agents isolated for security or resource management
- **Mixed deployments**: Some agents local, others on different machines
- **Microservices**: Deploy agents as independent services

**Starting Remote Services:**

```bash
# Generate remote services
topaz-agent-kit generate services --project .

# Start remote agent services (A2A unified service)
topaz-agent-kit serve services --project .
```

Remote agents are automatically discovered and connected via the A2A protocol.

### Local Tools

You can add custom Python tools that agents can use. Create a `tools/` folder with your custom tool implementations.

**Step 1: Create Tool File**

Create `tools/my_tools.py`:

```python
def calculate_discount(price: float, discount_percent: float) -> float:
    """Calculate the discounted price.
    
    Args:
        price: Original price
        discount_percent: Discount percentage (0-100)
    
    Returns:
        Discounted price
    """
    return price * (1 - discount_percent / 100)

def validate_email(email: str) -> bool:
    """Validate email format.
    
    Args:
        email: Email address to validate
    
    Returns:
        True if valid, False otherwise
    """
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))
```

**Step 2: Configure Agent to Use Tools**

```yaml
id: my_agent
type: agno
model: "azure_openai"
run_mode: "local"

local_tools:
  - module: tools.my_tools
    functions:
      - calculate_discount
      - validate_email

prompt:
  instruction:
    jinja: prompts/my_agent.jinja
```

The agent will automatically have access to these tools and can call them during execution.

---

## 🧠 AgentOS Memory System

**AgentOS** provides a filesystem-based memory system that enables agents to store, retrieve, and search information using familiar Unix-like commands. This is ideal for agents that need to remember context, access templates, or maintain persistent data.

### Overview

AgentOS provides a **3-level memory hierarchy** with declarative schema definitions:

- **`/global/`** - Project-wide shared memory (system docs, cross-pipeline data)
- **`/shared/`** - Pipeline-wide shared memory (templates, shared runtime data)
- **`/memory/`** - Agent-specific individual memory (isolated, not shared)
- **`/workspace/`** - Agent workspace (temporary files)

**Key Features**:
- ✅ **Declarative schemas**: Define file structures in YAML, auto-generate instructions
- ✅ **Template-based initialization**: Copy templates from `config/memory/shared/` to runtime
- ✅ **Two types of shared memory**: System files (read-only templates) and runtime data (write-once, read-many)
- ✅ **Auto-indexing**: Semantic search across indexed files
- ✅ **Isolation**: Agent memory is isolated; use `/shared/` or `/global/` for sharing

**Configuration Structure**:
```
config/memory/
├── memory.yml                    # Global memory configuration (future)
├── prompts/                      # Custom memory prompt templates
│   └── {agent_id}.jinja
└── shared/
    ├── global/                   # Global memory templates
    └── pipeline/                 # Pipeline memory templates
        └── {pipeline_id}/
```

### Quick Start

**Step 1: Enable AgentOS in Agent Configuration**

```yaml
# config/agents/my_agent.yml
id: my_agent
type: agno
model: "azure_openai"

# Enable MCP and AgentOS
mcp:
  enabled: true
  servers:
    - url: "http://localhost:8050/mcp"
      toolkits: ["agentos_memory"]
      tools: ["agentos_shell"]

# Memory configuration
memory:
  inherit: true  # Inherit shared memory from pipeline (if configured)
  directories:
    - path: "/memory/data/"
      description: "Agent-specific data storage"
      readonly: false
      auto_index: true
      bootstrap: true
    - path: "/workspace/"
      description: "Working directory for temporary files"
      readonly: false
      auto_index: false
      bootstrap: true
```

**Step 2: Update Agent Prompt**

Add the `{{agentos_memory_section}}` marker to your prompt template:

```jinja
# config/prompts/my_agent.jinja
You are a helpful assistant with filesystem-based memory.

{{agentos_memory_section}}

## Workflow:
1. Check existing data: `agentos_shell("ls /memory/data/")`
2. Read a file: `agentos_shell("cat /memory/data/info.md")`
3. Store new data: `agentos_shell('echo "new data" > /memory/data/info.md')`
4. Search semantically: `agentos_shell('semgrep "similar pattern"')`
```

**Step 3: Use in Agent Workflow**

The agent can now use `agentos_shell` to manage memory:

```python
# List directories
agentos_shell("ls /")

# Read a file
agentos_shell("cat /memory/data/info.md")

# Write a file
agentos_shell('echo "content" > /memory/data/info.md')

# Semantic search
agentos_shell('semgrep "query text"')
```

### Pipeline-Level Shared Memory

For templates and reference data shared across all agents in a pipeline:

**Step 1: Configure Pipeline Shared Memory**

```yaml
# config/pipelines/my_pipeline.yml
name: "My Pipeline"

memory:
  shared:
    directories:
      # Type 1: System files (read-only templates)
      - path: "/shared/templates/"
        description: "Template library (READ-ONLY)"
        readonly: true
        auto_index: true
        bootstrap: true
        template_source: "config/memory/shared/pipeline/my_pipeline/templates/"
      
      # Type 2: Runtime data (write-once, read-many)
      - path: "/shared/data/"
        description: "Shared runtime data (agents can write)"
        readonly: false
        auto_index: true
        bootstrap: true
        schemas:
          records:
            file: "records.jsonl"
            format: "jsonl"
            write_mode: "append"
            structure:
              timestamp: "ISO 8601 timestamp"
              data: "string"
```

**Step 2: Create Template Files**

Create template files in `config/memory/shared/pipeline/{pipeline_id}/`:

```bash
mkdir -p config/memory/shared/pipeline/my_pipeline/templates
mkdir -p config/memory/shared/pipeline/my_pipeline/reference

# Create template files
echo "# Template 1" > config/memory/shared/pipeline/my_pipeline/templates/template1.md
echo "# Reference Data" > config/memory/shared/pipeline/my_pipeline/reference/data.md
```

**Note**: The old location `config/shared/` is deprecated but still supported for backward compatibility. New projects should use `config/memory/shared/pipeline/`.

**Step 3: Agents Access Shared Memory**

**Inheritance**: Agents with `memory.inherit: true` (the default) automatically have access to all pipeline-level shared directories. They can access these via `/shared/` paths. Set `inherit: false` in an agent's configuration to disable inheritance for that specific agent.

```jinja
# In agent prompt
## Access Shared Templates:
agentos_shell("ls /shared/templates/")
agentos_shell("cat /shared/templates/template1.md")
```

### Memory Configuration Options

| Option | Type | Default | Description |
|-------|------|---------|-------------|
| `inherit` | `bool` | `true` | **Inherit shared memory from pipeline**. When `true`, agent automatically has access to all pipeline-level shared directories (e.g., `/shared/templates/`, `/shared/reference/`). Set to `false` to disable inheritance. |
| `directories` | `list[object]` | `[]` | Agent-specific directories (agent-level individual memory, **isolated from other agents**) |
| `directories[].path` | `str` | **required** | Virtual path (e.g., `/memory/data/`) |
| `directories[].description` | `str` | **required** | Human-readable description |
| `directories[].readonly` | `bool` | `false` | Make directory read-only |
| `directories[].auto_index` | `bool` | `true` | Enable semantic search indexing |
| `directories[].bootstrap` | `bool` | `true` | Create directory on initialization |
| `directories[].template_source` | `str` | `null` | **Optional**: Template source path relative to project root (e.g., `config/memory/shared/pipeline/my_pipeline/templates/`) |
| `directories[].schemas` | `object` | `{}` | **Optional**: File schemas for this directory (see Schema Definitions below) |
| `prompt_section` | `object` | `null` | **Optional**: Custom memory prompt template (inline/file/jinja). Paths are relative to `config/memory/prompts/` (e.g., `memory/prompts/my_agent.jinja`). If not provided, system uses a default template that lists available directories, commands, and schema documentation. |

**Inheritance Behavior**:

- **`inherit: true`** (default): Agent automatically inherits all pipeline-level shared memory directories. These are accessible via `/shared/` paths and are read-only by default.
- **`inherit: false`**: Agent does not inherit pipeline shared memory. Only agent-specific directories are available.

**Memory Isolation**:

- **`/memory/`** directories are **agent-specific and isolated** - agents cannot access each other's `/memory/` directories
- If agents need to share data, use `/shared/` (pipeline-level) or `/global/` (project-level)
- **`/workspace/`** is also agent-specific and temporary

### Memory Hierarchy

AgentOS provides a **3-level memory hierarchy**:

1. **`/global/`** - Global shared memory (project-wide)
   - Shared across all pipelines
   - Read-only for agents (templates) or write-once read-many (runtime data)
   - Templates: `config/memory/shared/global/`
   - Runtime: `data/agentos/global_shared/`

2. **`/shared/`** - Pipeline-level shared memory (pipeline-wide)
   - Shared across all agents in a pipeline
   - Read-only for agents (templates) or write-once read-many (runtime data)
   - Templates: `config/memory/shared/pipeline/{pipeline_id}/`
   - Runtime: `data/agentos/{pipeline_id}/shared/`

3. **`/memory/`** - Agent-level individual memory (agent-specific)
   - Isolated per agent (not shared with other agents)
   - Read-write for the owning agent
   - Runtime: `data/agentos/{pipeline_id}/agents/{agent_id}/memory/`

4. **`/workspace/`** - Agent workspace (agent-specific, temporary)
   - Temporary working directory
   - Can be cleared between sessions
   - Runtime: `data/agentos/{pipeline_id}/agents/{agent_id}/workspace/`

### Schema Definitions

Define file structures declaratively in YAML configuration:

```yaml
memory:
  shared:
    directories:
      - path: "/shared/data/"
        schemas:
          records:
            file: "records.jsonl"
            format: "jsonl"           # jsonl, json, markdown
            write_mode: "append"      # append, overwrite
            structure:
              timestamp: "ISO 8601 timestamp"
              data: "string"
              metadata: "object"
            # Optional: Custom instructions (overrides auto-generated)
            instructions:
              read: "Read all records: `agentos_shell(command='cat /shared/data/records.jsonl')`"
              write: "Append new record: `agentos_shell(command='echo \"<single_line_json>\" >> /shared/data/records.jsonl')`"
```

**Schema Benefits**:
- Auto-generated instructions in prompts
- Clear structure documentation
- Proper file formats (JSONL for append, JSON for overwrite)
- Scalable and maintainable

**Schema Fields**:
- `file` (required): Filename
- `format`: `jsonl`, `json`, `markdown` (default: `json`)
- `write_mode`: `append`, `overwrite` (default: `overwrite`)
- `readonly`: Whether file is read-only (default: `false`)
- `structure`: Simple structure definition (key-value mapping)
- `instructions`: Custom read/write instructions (optional, overrides auto-generated)

**Default Memory Prompt**:

If `prompt_section` is not specified, the system automatically provides a default memory prompt that:
- Lists all available memory directories (agent-specific and inherited shared)
- Shows directory descriptions and read-only status
- Provides examples of available commands

**When to Use Default Template** (Recommended for most cases):

✅ **Use the default template when:**
- You have simple memory needs (just listing directories and basic commands)
- You want to get started quickly without customizing prompts
- Your agents have standard memory usage patterns
- You prefer consistency across agents
- You want to reduce maintenance overhead

**When to Use Custom Template**:

✅ **Create a custom template when:**
- You need **workflow-specific guidance** for how agents should use memory
- You want to provide **step-by-step instructions** tailored to your agent's task
- You need to **emphasize specific commands** or usage patterns
- You want to include **domain-specific examples** or use cases
- Your agent has **complex memory workflows** that need detailed explanation

**Best Practice**: Start with the default template. Only create a custom template if you find that agents need more specific guidance or workflow instructions for your use case.

You can customize the prompt by adding a `prompt_section` configuration (see examples above).

### Available Commands

The `agentos_shell` tool supports these Unix-like commands:

| Command | Description | Example |
|---------|-------------|---------|
| `ls [path]` | List directory contents | `agentos_shell("ls /memory/data/")` |
| `cat [file]` | Read file contents | `agentos_shell("cat /memory/data/info.md")` |
| `echo "text" > [file]` | Write to file | `agentos_shell('echo "data" > /memory/data/info.md')` |
| `echo "text" >> [file]` | Append to file | `agentos_shell('echo "more" >> /memory/data/info.md')` |
| `grep "pattern" [file]` | Search text in file | `agentos_shell('grep "keyword" /memory/data/info.md')` |
| `semgrep "query"` | Semantic search across indexed files | `agentos_shell('semgrep "similar pattern"')` |
| `mkdir -p [path]` | Create directory | `agentos_shell("mkdir -p /memory/data/subdir")` |

### Best Practices

1. **Use `/shared/` for Read-Only Reference Data**
   - Templates, company info, policies
   - Set `readonly: true` to prevent modifications

2. **Use `/memory/` for Agent-Specific Persistent Data**
   - Preferences, history, patterns
   - Enable `auto_index: true` for semantic search

3. **Use `/workspace/` for Temporary Files**
   - Drafts, intermediate results
   - Set `auto_index: false` to skip indexing

4. **Enable Auto-Indexing Strategically**
   - Enable for data you want to search semantically
   - Disable for temporary or frequently-changing files

5. **Organize by Pipeline**
   - Each pipeline has isolated shared memory
   - Use `config/memory/shared/pipeline/{pipeline_id}/` for templates

### Example: Content Analyzer with Memory

Here's a complete example of an agent that uses AgentOS memory:

**Agent Configuration** (`config/agents/content_analyzer.yml`):

```yaml
id: content_analyzer
type: agno
model: "azure_openai"
run_mode: "local"

mcp:
  enabled: true
  servers:
    - url: "http://localhost:8050/mcp"
      toolkits: ["agentos_memory"]
      tools: ["agentos_shell"]

memory:
  directories:
    - path: "/memory/analysis_history/"
      description: "Previous analysis results"
      readonly: false
      auto_index: true
      bootstrap: true
    - path: "/workspace/"
      description: "Working directory"
      readonly: false
      auto_index: false
      bootstrap: true

prompt:
  instruction:
    jinja: prompts/content_analyzer.jinja
  inputs:
    inline: |
      - Content to analyze: {{user_text}}
```

**Agent Prompt** (`config/prompts/content_analyzer.jinja`):

```jinja
You are a content analyzer with memory capabilities.

{{agentos_memory_section}}

## Workflow:
1. **Check previous analyses**: `agentos_shell("ls /memory/analysis_history/")`
2. **Search similar content**: `agentos_shell('semgrep "similar content pattern"')`
3. **Analyze content**: Perform your analysis
4. **Store results**: `agentos_shell('echo "{{analysis_result}}" > /memory/analysis_history/{{timestamp}}.md')`

## Response:
Provide a detailed analysis of the content.
```

### Troubleshooting

**Memory directories not created**:
- Ensure `bootstrap: true` is set
- Check that agent has `memory` configuration
- Verify MCP server is running

**Template files not initialized**:
- Ensure files exist in `config/memory/shared/pipeline/{pipeline_id}/`
- Check pipeline has `memory.shared.directories` configuration
- Verify `bootstrap: true` is set

**Semantic search not working**:
- Ensure `auto_index: true` is set
- Files must be written to indexed directories
- Use `semgrep` command, not `grep`

### Troubleshooting AgentOS Memory

**Memory directories not created**:
- Ensure `bootstrap: true` is set for directories that should be created automatically
- Check that agent has `memory` configuration in its YAML file
- Verify MCP server is running and `agentos_memory` toolkit is enabled

**Template files not initialized**:
- Ensure template files exist in `config/memory/shared/pipeline/{pipeline_id}/`
- Check pipeline has `memory.shared.directories` configuration
- Verify `bootstrap: true` is set for shared directories
- Check logs for initialization errors

**Semantic search not working**:
- Ensure `auto_index: true` is set for directories you want to search
- Files must be written to indexed directories (not just read)
- Use `semgrep` command, not `grep` for semantic search

**Permission denied errors**:
- Check `readonly: true` settings - agents cannot write to read-only directories
- Verify path mappings are correct in memory configuration
- Check sandbox security logs for blocked operations

**Agents not accessing shared memory**:
- Verify `memory.inherit: true` is set in agent configuration (default)
- Check that pipeline has `memory.shared.directories` configured
- Ensure shared directories are properly initialized from template files

For more detailed documentation, see the [AgentOS Memory System](../../../../README.md#-agentos-memory-system) section in the main README.

---

## 📖 Standard Operating Procedures (SOPs)

Standard Operating Procedures (SOPs) enable agents to follow structured, documented procedures stored as markdown files. This allows you to update agent behavior without code changes, maintain consistency, and include domain expertise directly in your agent configurations.

### What Are SOPs?

SOPs are structured documents that guide agents through complex workflows:
- **Procedural Steps**: Step-by-step instructions for agents to follow
- **Examples & Scenarios**: Concrete examples showing how to handle different cases
- **Troubleshooting Guides**: Common issues and their resolutions
- **Domain Glossaries**: Definitions of business-specific terms

### How Agents Use SOPs

Agents interact with SOPs through MCP (Model Context Protocol) tools:

1. **Initialize**: `sop_initialize` - Load the SOP manifest
2. **Read Sections**: `sop_get_section` - Read specific steps or sections
3. **Get Examples**: `sop_get_example` - Retrieve scenario examples
4. **Troubleshoot**: `sop_get_troubleshooting` - Get error resolution guidance
5. **Look Up Terms**: `sop_get_glossary_term` - Find domain term definitions

### Creating an SOP

#### Minimum Requirements

**Absolute Minimum** (SOP will work):
```yaml
# config/sop/<pipeline>/<agent>/manifest.yml
sop_id: my_agent
version: "1.0.0"
description: "SOP description"
sections: []
```

**Recommended Minimum** (actually useful):
```yaml
# config/sop/<pipeline>/<agent>/manifest.yml
sop_id: my_agent
version: "1.0.0"
description: "SOP description"

sections:
  - id: overview
    file: overview.md
    type: reference
    description: "Overview of the agent's role"
    read_at: start
```

```markdown
# config/sop/<pipeline>/<agent>/overview.md
## Your Role
[What the agent does]

## Key Steps
1. Step 1: [Description]
2. Step 2: [Description]

## Tools
- tool_name - [Description]

## Output Format
Return JSON with fields...
```

#### Directory Structure

```
config/sop/
└── <pipeline>/                    # Pipeline-specific SOPs
    ├── glossary.md               # Pipeline glossary (shared across agents)
    └── <agent>/                  # Agent-specific SOP
        ├── manifest.yml          # REQUIRED: SOP structure definition
        ├── overview.md           # RECOMMENDED: High-level guidance
        ├── steps/                # OPTIONAL: Procedural steps
        │   ├── step_01_*.md
        │   └── step_02_*.md
        ├── scenarios/            # OPTIONAL: Example scenarios
        │   └── scenario_*.md
        └── troubleshooting.md    # OPTIONAL: Error resolution guide
```

### Configuring an Agent to Use SOPs

Add SOP configuration to your agent YAML:

```yaml
# config/agents/my_agent.yml
id: my_agent
type: oak  # OAK framework supports SOPs
model: "azure_openai"
run_mode: "local"

# SOP configuration - points to the manifest
sop: "config/sop/<pipeline>/<agent>/manifest.yml"

# Increase max_turns for SOP-driven workflows
max_turns: 50

# MCP tools for SOP access
mcp:
  servers:
    - url: "http://localhost:8050/mcp"
      toolkits: ["sop"]
      tools: ["sop_initialize", "sop_get_section", "sop_get_example", "sop_get_troubleshooting", "sop_get_glossary_term"]
```

### Agent Prompt Template

Update your agent prompt to instruct it to use SOPs:

```jinja
# config/prompts/my_agent.jinja
You are a [Agent Name] (SOP-Driven) responsible for [task].

Tasks:
1. **Initialize SOP**: Call `sop_initialize` with `project_dir` and `sop_path` from inputs.
2. **Read SOP Overview**: Call `sop_get_section(section_id="overview")`.
3. **Follow SOP Steps in Order**:
   - **Step 1**: Call `sop_get_section(section_id="step_01_...")`, then execute.
   - **Step 2**: Call `sop_get_section(section_id="step_02_...")`, then execute.
4. **If Stuck**: Use `sop_get_example(scenario_name="...")` or `sop_get_troubleshooting(issue="...")`.
5. **If Uncertain About Terms**: Use `sop_get_glossary_term(term_id="<term>")`.
```

### Example: Complete SOP Structure

```yaml
# config/sop/my_pipeline/my_agent/manifest.yml
sop_id: my_agent
version: "1.0.0"
description: "SOP for processing items"

sections:
  # Overview
  - id: overview
    file: overview.md
    type: reference
    description: "High-level workflow"
    read_at: start

  # Procedural Steps
  - id: step_01_identify
    file: steps/step_01_identify.md
    type: procedure
    description: "Identify the target"
    read_at: on_demand
    depends_on: []
    outputs:
      - target_id
    tools_used:
      - my_tool.get_target

  - id: step_02_process
    file: steps/step_02_process.md
    type: procedure
    description: "Process the target"
    read_at: on_demand
    depends_on:
      - step_01_identify
    outputs:
      - result
    tools_used:
      - my_tool.process

  # Examples
  - id: scenario_simple
    file: scenarios/simple.md
    type: example
    description: "Simple processing example"
    read_at: on_demand

  # Troubleshooting
  - id: troubleshooting
    file: troubleshooting.md
    type: troubleshooting
    description: "Common issues"
    read_at: on_demand
```

### Best Practices

1. **Start Simple**: Begin with just `manifest.yml` and `overview.md`, then add sections as needed
2. **Organize Clearly**: Use section comments and consistent naming (`step_01_`, `step_02_`, etc.)
3. **Be Specific**: Include exact tool calls, parameters, and expected outputs in step files
4. **Provide Examples**: Concrete scenarios help agents understand patterns
5. **Document Errors**: Troubleshooting guides help agents handle edge cases
6. **Define Terms**: Glossaries clarify domain-specific terminology

### Reference Documentation

For detailed guidance on creating SOPs:

- **Complete Guide**: See `docs/sop/SOP_CREATION_GUIDE.md` in the Topaz Agent Kit repository
- **Quick Reference**: See `docs/sop/SOP_QUICK_REFERENCE.md` for templates and quick lookups
- **Example Implementation**: Review the ReconVoy SOP at `config/sop/reconvoy/sop_matcher/` in the ICP starter template

### When to Use SOPs

**Use SOPs when:**
- ✅ Agents need to follow complex, multi-step procedures
- ✅ Business rules change frequently (update SOPs, not code)
- ✅ Domain expertise needs to be captured in documentation
- ✅ Consistency across agent executions is critical
- ✅ Troubleshooting guidance is needed for edge cases

**Don't use SOPs when:**
- ❌ Simple, single-step operations
- ❌ Procedures change with every execution
- ❌ Real-time decision making without structure

---

## 🔀 Pipeline Patterns

Topaz Agent Kit supports multiple execution patterns. Here are the most common ones:

### 1. Sequential Pattern

Execute agents one after another in order:

```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - node: agent2
    - node: agent3
```

**Use when**: Each agent depends on the output of the previous agent.

### 2. Parallel Pattern

Execute multiple agents simultaneously:

```yaml
pattern:
  type: sequential
  steps:
    - node: coordinator
    - type: parallel
      steps:
        - node: agent1
        - node: agent2
        - node: agent3
    - node: aggregator
```

**Use when**: Agents are independent and can run concurrently to save time.

### 3. Conditional Pattern

Execute steps based on conditions:

```yaml
pattern:
  type: sequential
  steps:
    - node: analyzer
    - type: sequential
      condition: "analyzer.needs_review == true"
      steps:
        - node: reviewer
        - gate: approve_review
    - node: finalizer
```

**Use when**: You need to conditionally execute parts of the pipeline based on previous results.

### 4. Switch Pattern

Route to different branches based on a condition:

```yaml
pattern:
  type: sequential
  steps:
    - node: classifier
    - type: switch(classifier.complexity > 5)
      cases:
        true:
          - node: complex_processor
          - node: validator
        false:
          - node: simple_processor
    - node: finalizer
```

**Use when**: You need to choose between different execution paths.

### 5. Loop Pattern

Repeat a step or pattern multiple times. There are two ways to control loops:

#### 5a. Numeric Loop (with max_iterations)

Iterate a fixed number of times or until a termination condition is met:

```yaml
pattern:
  type: sequential
  steps:
    - node: initializer
    - type: loop
      body:
        type: sequential
        steps:
          - node: processor
          - gate: continue_loop
            condition: "processor.has_more == true"
      termination:
        max_iterations: 10
        condition: "processor.has_more == false"  # Optional: early exit condition
    - node: finalizer
```

**Use when**: You need to iterate until a condition is met or a maximum number of iterations is reached.

#### 5b. List Iteration (with iterate_over)

Iterate over a list/array from a previous agent's output:

```yaml
pattern:
  type: sequential
  steps:
    - node: scanner
    - type: loop
      condition: "scanner.total_count > 0"  # Optional: skip loop if list is empty
      iterate_over: "scanner.items_list"   # Path to the list/array
      loop_item_key: "current_item"         # Context key for current item (default: "loop_item")
      termination:
        max_iterations: 100  # Optional: safety limit to prevent infinite loops
      body:
        type: sequential
        steps:
          - node: processor  # current_item is automatically available in context
          - node: validator
          - node: recorder
    - node: finalizer
```

**Key Features**:
- **`iterate_over`**: Path to the list/array to iterate over (e.g., `"scanner.pending_items"`)
- **`loop_item_key`**: Context key where the current item is injected (default: `"loop_item"`)
- **`max_iterations`**: Optional safety limit (recommended for large lists)
- **`condition`**: Optional pattern-level condition to skip the loop entirely if the list is empty

**Accessing the Current Item**:
- In agent prompts: Use `{{current_item.field_name}}` or `{{loop_item.field_name}}` (depending on `loop_item_key`)
- In agent inputs: Use `{{current_item.field_name}}` in the YAML input mapping
- The loop automatically terminates when all items in the list are processed

**Accessing Accumulated Results** (when `accumulate_results=true`, default):
- After the loop completes, downstream agents can access all loop iteration results using `{agent_id}_instances`
- Example: If `validator` runs inside a loop, use `{{validator_instances}}` in downstream agents
- The `*_instances` dictionary contains keys like `validator_0`, `validator_1`, etc., with each iteration's result
- This allows summary/aggregation agents to process all loop results, not just the last one

**Example from ECI Claims Vetter**:
```yaml
- type: loop
  condition: "eci_pending_claims_scanner.total_pending_count > 0"
  iterate_over: "eci_pending_claims_scanner.pending_claims_list"
  loop_item_key: "current_claim"
  termination:
    max_iterations: 100  # Safety limit
  body:
    type: sequential
    steps:
      - node: eci_claims_extractor  # Accesses current_claim.claim_id, current_claim.claim_form_path, etc.
      - node: eci_claim_validator    # Accesses current_claim.claim_id
```

**Use when**: You have a list of items to process (e.g., pending claims, files, emails, orders) and want to process each item through the same sequence of steps.

#### 5c. Dynamic List Iteration (with dynamic_iterate_over)

For recursive discovery or scenarios where new items are added during iteration, enable dynamic re-evaluation of the list:

```yaml
pattern:
  type: sequential
  steps:
    - node: scanner
    - type: loop
      iterate_over: "scanner.items_list"
      loop_item_key: "current_item"
      dynamic_iterate_over: true  # Re-evaluate list before each iteration
      termination:
        max_iterations: 50  # Safety limit (required for dynamic mode)
      body:
        type: sequential
        steps:
          - node: processor
          - node: discovery_agent  # May add new items to scanner.items_list
          - node: recorder
    - node: finalizer
```

**Key Features**:
- **`dynamic_iterate_over: true`**: Re-evaluates the `iterate_over` list before each iteration
- **Picks up new items**: Items added during iteration (e.g., by `discovery_agent`) are automatically processed
- **Duplicate prevention**: Tracks processed items to avoid processing the same item twice
- **Safety limit**: Always use `max_iterations` to prevent infinite loops

**How It Works**:
1. Before each iteration, the loop re-resolves the `iterate_over` path
2. Filters out already processed items (using item ID or hash)
3. Processes the first unprocessed item
4. Continues until no new items are found or `max_iterations` is reached

**Use Cases**:
- **Recursive Discovery**: Finding related items that may lead to more items (e.g., ReconVoy pipeline)
- **Database Updates**: Processing items that may trigger new items to be added to the queue
- **Dynamic Workloads**: When the work list grows during processing

**Example: Recursive Discovery**:
```yaml
- type: loop
  iterate_over: "related_items_discovery.related_items"
  loop_item_key: "related_item"
  dynamic_iterate_over: true  # Pick up newly discovered items
  termination:
    max_iterations: 50  # Safety limit
  body:
    type: sequential
    steps:
      - node: item_discovery  # Finds foreign book matches
      - node: related_items_discovery  # May add more items to related_items list
```

**Performance Note**: Dynamic iteration re-evaluates the list on each iteration, which may have performance implications for expensive operations (database queries, complex context resolution). Use static iteration (`dynamic_iterate_over: false` or omitted) when the list doesn't change during processing.

### 6. Repeat Pattern

Run the same agent multiple times in parallel with different inputs:

```yaml
pattern:
  type: sequential
  steps:
    - node: file_scanner
    - type: parallel
      repeat:
        node: processor
        instances: "file_scanner.file_count"
        instance_id_template: "processor_{{index}}"
        input_mapping:
          user_text: "{{file_scanner.file_paths[index]}}"
    - node: aggregator
```

**Use when**: You need to process multiple items in parallel (e.g., multiple files, multiple problems).

### 7. Handoff Pattern

Let the LLM dynamically choose which specialist agent to route to:

```yaml
pattern:
  type: sequential
  steps:
    - node: intake_agent
    - type: handoff
      name: "Specialist Routing"
      description: "Route to appropriate specialist based on query type"
      router: intake_agent  # Agent that decides the routing
      specialists:
        - id: billing_expert
          description: "Handles billing, payments, and invoice questions"
        - id: technical_support
          description: "Handles technical issues and troubleshooting"
        - id: sales_agent
          description: "Handles pricing, upgrades, and new services"
      fallback: general_support  # If no specialist matches
    - node: response_formatter
```

**Use when**: You need intelligent, LLM-driven routing based on query content rather than fixed conditions.

### 8. Group Chat Pattern

Enable multiple agents to have a collaborative discussion:

```yaml
pattern:
  type: sequential
  steps:
    - node: proposal_generator
    - type: group_chat
      name: "Expert Review Panel"
      description: "Experts discuss and refine the proposal"
      participants:
        - id: domain_expert
          role: "Domain Expert - validates technical accuracy"
        - id: risk_assessor
          role: "Risk Assessor - identifies potential issues"
        - id: quality_reviewer
          role: "Quality Reviewer - ensures completeness"
      max_rounds: 4
      termination:
        condition: "contains({{last_message}}, 'REVIEW COMPLETE')"
    - node: proposal_finalizer
```

**Use when**: You need collaborative refinement where multiple expert perspectives improve the output.

### 9. Pipeline Composition

Reuse an entire existing pipeline as a step in another pipeline:

```yaml
pattern:
  type: sequential
  steps:
    - node: intake_parser
    - type: pipeline
      pipeline_id: validation_pipeline  # Reference to another pipeline
      input_mapping:
        user_text: "{{intake_parser.extracted_text}}"
    - node: response_generator
```

**Use when**: You have reusable sub-workflows that can be composed into larger pipelines.

### 10. Nested Patterns

Combine patterns for complex workflows:

```yaml
pattern:
  type: sequential
  steps:
    - node: coordinator
    - type: parallel
      steps:
        - type: sequential
          condition: "coordinator.needs_flights == true"
          steps:
            - node: flights_expert
            - gate: select_flights
        - type: sequential
          condition: "coordinator.needs_hotels == true"
          steps:
            - node: hotels_expert
            - gate: select_hotels
    - node: aggregator
```

**Use when**: You need complex workflows with conditional parallel execution.

---

## 🎯 Accessing Agent Outputs

In your patterns, you can access outputs from previous agents using Jinja2 expressions:

```yaml
pattern:
  type: sequential
  steps:
    - node: agent1
    - node: agent2
      # agent2 can access agent1's output
      # In agent2's prompt, use: {{agent1.field_name}}
```

**Example**: If `agent1` returns `{"summary": "..."}`, you can access it in `agent2`'s prompt as `{{agent1.summary}}`.

---

## ⚡ Event-Driven Pipelines

Pipelines can be automatically triggered by external events, enabling reactive workflows that respond to file system changes, webhooks, or custom triggers.

### Configuration

Add `event_triggers` section to your pipeline configuration:

```yaml
name: "Document Processor"
description: "Automatically processes documents when uploaded"

# Event triggers configuration
event_triggers:
  type: "file_watcher"
  watch_directory: "data/documents"
  file_patterns:
    - "*.pdf"
    - "*.docx"
  event_types:
    - "created"
  extract_context:
    user_text_template: "Process document: {{file_name}}"
  session_strategy: "per_file"

# Normal pipeline pattern (unchanged)
pattern:
  type: sequential
  steps:
    - node: document_parser
    - node: document_analyzer
```

### Trigger Types

**File Watcher** (currently supported):
- Monitors a directory for file system events
- Supports wildcard patterns (`*.txt`, `contract_*.pdf`)
- Event types: `created`, `modified`, `deleted`, `moved`
- Automatically passes file paths to pipeline execution

**Future trigger types**:
- `webhook`: HTTP POST triggers
- `database`: Row insert/update triggers
- `scheduled`: Cron-based scheduling

### Context Extraction

Use Jinja2 templates to extract context from trigger events:

```yaml
extract_context:
  user_text_template: "Process file: {{file_name}} ({{file_size}} bytes)"
```

**Available variables** (file_watcher):
- `{{source}}` - Full file path
- `{{file_path}}` - Alias for source
- `{{file_name}}` - Filename only
- `{{file_size}}` - File size in bytes
- `{{event_type}}` - Event type (created, modified, etc.)

### Session Strategies

- **`per_file`** (default): New session for each file event - isolated, no shared context
- **`per_pipeline`**: One session for all events - accumulates context across files
- **`custom`**: Pipeline-specific logic (e.g., per contract_id, per user_id)

### Important Notes

- Event triggers are **additive** - they don't change normal pipeline execution
- Normal user-initiated execution still works unchanged
- Both paths (user-initiated and event-triggered) converge at START
- Workflow diagrams show triggers as alternative entry points

## 🚪 Human-in-the-Loop Gates

HITL gates pause pipeline execution for human review, input, or selection. There are three gate types:

### 1. Approval Gate

Pause for human approval before continuing:

```yaml
# In pipeline pattern
pattern:
  type: sequential
  steps:
    - node: analyzer
    - type: gate
      gate_id: analysis_review
      gate_type: approval
      title: "Review Analysis"
      description: "Review the analysis before proceeding"
    - node: processor
```

**Gate Configuration** (`config/hitl/analysis_review.jinja`):

```jinja
## Analysis Review Required

The analyzer has completed. Please review the results:

**Summary**: {{analyzer.summary}}

**Confidence**: {{analyzer.confidence}}%

Do you approve this analysis to proceed?
```

### 2. Input Gate

Pause to collect additional information from the user:

```yaml
- type: gate
  gate_id: additional_info
  gate_type: input
  title: "Additional Information Needed"
  fields:
    - name: priority
      type: select
      options: ["low", "medium", "high"]
      required: true
    - name: notes
      type: text
      required: false
```

### 3. Selection Gate

Pause to let user choose from options:

```yaml
- type: gate
  gate_id: option_selection
  gate_type: selection
  title: "Select Recommendation"
  options_source: "recommender.options"  # List from previous agent
  selection_mode: single  # or "multiple"
```

### Gate Placement

Gates can be placed:
- **After agents**: `after: agent_id`
- **Inline in pattern**: As a step in the pattern
- **Conditionally**: With `condition` field

```yaml
# Conditional gate - only shows if condition is true
- type: gate
  gate_id: fraud_review
  condition: "{{fraud_detector.score}} > 0.7"
```

### ⚡ Async HITL (Advanced)

For batch processing and loop patterns, you can enable **async HITL** mode, which allows pipelines to continue processing while HITL requests are queued for review. This is ideal for processing many items where only some need human review.

#### Why Use Async HITL?

**Sync HITL** (default) blocks the pipeline until a human responds:
- Simple and straightforward
- Pipeline stops completely, waiting for response
- Inefficient for batch processing (e.g., processing 100 items where only 10 need review)

**Async HITL** queues review requests and continues processing:
- Pipeline continues processing other items
- Perfect for batch/loop workflows
- Review requests queued for later processing in Operations UI
- Cases tracked independently

#### Enabling Async HITL

Enable async HITL in your pipeline configuration:

```yaml
# config/pipelines/my_pipeline.yml
name: "My Pipeline"

# Enable async HITL mode
execution_settings:
  hitl_mode: "async"              # "sync" (default) or "async"
  checkpoint_expiry_days: 7       # How long checkpoints remain valid

# Configure case management (required for async HITL)
case_management:
  config_file: "cases/my_pipeline.yml"  # Case configuration file
```

#### Case YAML Configuration

Create a case configuration file to define how cases are displayed in the Operations UI:

```yaml
# config/cases/my_pipeline.yml

# Identity configuration - how to identify cases
identity:
  prefix: "CASE"                    # Case ID prefix (e.g., "CASE-ABC12345")
  uniqueness: "uuid_suffix"         # "uuid_suffix" (default), "timestamp", or "none"

# Detail view - what to show in case detail panel
detail_view:
  sections:
    - name: "Item Details"
      fields:
        - field: "current_item.id"
          label: "Item ID"
          type: text
        - field: "analyzer.result"
          label: "Result"
          type: text
```

**Field Types**: `text`, `multiline`, `number`, `boolean`, `list`, `object`

#### List View Configuration

Configure how cases are displayed in the Operations UI case list table:

```yaml
# config/cases/my_pipeline.yml

list_view:
  # Define pipeline-specific fields (extracted from upstream context)
  pipeline_fields:
    - key: "transaction_id"
      field: "current_item.transaction_id"
      label: "Transaction ID"
      type: text
    - key: "amount"
      field: "current_item.amount"
      label: "Amount"
      type: number
      value_mapping:  # Optional: map raw values to display labels
        "capital_revenue_misclassification": "CAPITAL/REVENUE MISCLASSIFICATION"
  
  # Column order for pipeline-specific tab
  # Mix common field keys and pipeline field keys
  column_order:
    - "case_id"           # Common field
    - "transaction_id"    # Pipeline field
    - "amount"            # Pipeline field
    - "status"            # Common field
    - "hitl_status"       # Common field
    - "created_at"        # Common field
```

**Common Fields** (always available): `case_id`, `pipeline_id`, `status`, `hitl_gate_title`, `hitl_description`, `hitl_status`, `hitl_decision`, `responded_by`, `created_at`, `updated_at`, `actions`

**Pipeline Fields**: Define custom fields with `key`, `field` (dot-notation path), `label`, `type`, and optional `value_mapping`

#### Dashboard Configuration

Configure pipeline-specific analytics cards for the Operations dashboard:

```yaml
# config/cases/my_pipeline.yml

dashboard:
  enabled: true
  
  cards:
    # Percentage metric
    - type: "percentage"
      title: "Anomaly Detection Rate"
      icon: "AlertTriangle"
      numerator:
        field: "analyzer.anomaly_detected"
        filter: true
      denominator:
        field: "total"
      color: "amber"
    
    # Numeric metric
    - type: "metric"
      title: "Average Confidence Score"
      icon: "TrendingUp"
      field: "analyzer.confidence_score"
      aggregation: "avg"  # count, sum, avg, min, max
      format: "number"
      decimals: 2
      color: "blue"
    
    # Distribution chart
    - type: "donut"
      title: "Anomaly Types"
      icon: "PieChart"
      field: "analyzer.anomaly_type"
      show_legend: true
      show_percentages: true
    
    # Timeline
    - type: "timeline"
      title: "Cases Timeline"
      icon: "Calendar"
```

**Card Types**: `metric`, `percentage`, `donut`, `bar`, `timeline`, `default`

#### Resume Behavior

Control how agents behave when resuming from checkpoints:

```yaml
# config/agents/my_agent.yml
id: my_agent
type: agno
model: "azure_openai"

# Resume behavior options:
# - "always" (default): Always run, unless output already in upstream
# - "skip_on_resume": Never run when resuming (skip completely)
# - "run_only_when_complete": Only run when all loop iterations complete
resume_behavior: "always"
```

**When to Use**:
- **`always`**: Most agents that should run after HITL (default)
- **`skip_on_resume`**: One-time agents (scanners, initializers)
- **`run_only_when_complete`**: Summary agents that need all loop results

#### Operations UI

Access the Operations UI at `/operations` in the web interface:

- **Case List**: 
  - Tabbed view: "All" tab shows all cases, pipeline-specific tabs show custom columns
  - Custom columns: Pipeline-specific fields from `list_view` configuration
  - Filter by pipeline, status, time range, and search
- **Dashboard**: Pipeline-specific analytics cards (if `dashboard.enabled: true`)
  - Metrics, percentages, distribution charts, timelines
  - Filtered by same criteria as list view
- **Case Detail**: Review HITL requests, view case data, respond via buttons or chat
- **Operations Assistant**: Natural language interface for managing cases

**Responding to HITL**:
1. **Direct**: Click Approve/Reject in Review tab
2. **Via Chat**: Ask Operations Assistant to approve/reject cases

#### Example: Batch Processing with Async HITL

```yaml
# config/pipelines/batch_processor.yml
name: "Batch Processor"

execution_settings:
  hitl_mode: "async"
  checkpoint_expiry_days: 7

case_management:
  config_file: "cases/batch_processor.yml"

pattern:
  type: sequential
  steps:
    - node: batch_scanner
    
    - type: loop
      iterate_over: "batch_scanner.items_list"
      loop_item_key: "current_item"
      body:
        type: sequential
        steps:
          - node: item_processor
          - gate: review_item  # Async HITL - queues and continues
          - node: item_finalizer
    
    - node: batch_summary  # Reports on all items
```

For more details, see the [main README Async HITL section](../../../../README.md#-async-hitl-human-in-the-loop).

---

## 📜 Scripts & Data Setup

Some pipelines require database setup or mock data. Scripts are located in the `scripts/` folder.

### Running Scripts

```bash
# List available scripts
topaz-agent-kit scripts --project .

# Run a specific script
topaz-agent-kit scripts --project . --run setup_database
```

### Common Scripts

| Script | Purpose |
|--------|---------|
| `setup_database.py` | Initialize SQLite database with schema |
| `generate_mock_data.py` | Populate database with sample data |
| `fetch_documents.py` | Download required documents |

### Creating Custom Scripts

Create a Python script in `scripts/` and register it in `scripts/scripts.yml`:

```yaml
scripts:
  - id: setup_my_data
    name: "Setup My Data"
    description: "Initialize data for my pipeline"
    script: setup_my_data.py
    requires_confirmation: true
```

---

## 🚀 Running Your Project

### Start FastAPI Service (Web UI)

```bash
topaz-agent-kit serve fastapi --project .
```

This starts:
- FastAPI server (UI) on `http://127.0.0.1:8090`

**Note**: Services must be started individually. Each service runs in its own process.

### Start Other Services

```bash
# UI only
topaz-agent-kit serve fastapi --project .

# CLI only
topaz-agent-kit serve cli --project .

# MCP server only
topaz-agent-kit serve mcp --project .

# Services (A2A unified service for remote agents)
topaz-agent-kit serve services --project .
```

### Validate Configuration

```bash
topaz-agent-kit validate .
```

## 📚 Next Steps

### Getting Started
1. **Customize the example pipeline**: Edit `config/pipelines/example.yml` and `config/agents/hello_agent.yml`
2. **Try different models**: Update the `model` field to use OpenAI, Google AI, or Ollama
3. **Use independent agents**: The project includes several independent agents (content_analyzer, rag_query, etc.) that can be used directly

### Building New Pipelines
4. **Use AI-assisted generation**: If using Cursor IDE, try the [AI-Assisted Pipeline Generation](#ai-assisted-pipeline-generation) workflow
5. **Add pipelines manually**: Follow the [Adding a New Pipeline](#adding-a-new-pipeline) guide
6. **Explore execution patterns**: Try [Pipeline Patterns](#pipeline-patterns) for complex workflows

### Advanced Features
7. **Add HITL gates**: Implement [Human-in-the-Loop Gates](#human-in-the-loop-gates) for user interaction
8. **Create SOPs**: Build [Standard Operating Procedures (SOPs)](#standard-operating-procedures-sops) for structured agent workflows
9. **Use remote agents**: Configure [Remote Agents (A2A)](#remote-agents-a2a) for microservices architecture
10. **Add custom tools**: Create [Local Tools](#local-tools) for agent-specific functionality
11. **Set up data**: Use [Scripts](#scripts--data-setup) to initialize databases and mock data

## 🆘 Troubleshooting

### Environment Variables Not Loading

- Make sure `.env` exists (copy from `.env.example`)
- Check that variable names match exactly (case-sensitive)
- Restart the services after changing `.env`

### Agents Not Generating

- Run `topaz-agent-kit generate agents --project .` after creating agent configs
- Check that agent YAML files are valid (use `topaz-agent-kit validate .`)
- Verify `config/pipeline.yml` references your agents correctly

### Pipeline Not Appearing in UI

- Make sure the pipeline is registered in `config/pipeline.yml`
- Create a UI manifest in `config/ui_manifests/`
- Add the pipeline to `config/ui_manifest.yml`
- Regenerate diagrams: `topaz-agent-kit generate diagrams --project .`

### Model Connection Errors

- Verify API keys are set correctly in `.env`
- Check model name matches provider format (e.g., `azure_openai`, `openai`, `ollama_llama3.2`)
- For Ollama, ensure the model is pulled locally: `ollama pull llama3.2`

### Remote Agents Not Connecting

- Ensure remote services are running: `topaz-agent-kit serve services --project .`
- Check that `run_mode: "remote"` is set in agent config
- Verify no port conflicts with other services

### HITL Gate Not Showing

- Verify `gate_id` matches the filename in `config/hitl/`
- Check `gate_type` is valid (`approval`, `input`, or `selection`)
- Ensure the gate's `condition` (if any) evaluates to true

### Variable Not Found in Template

- Check the variable name matches the agent's output field exactly
- Verify the upstream agent is in the pattern before the current agent
- Use `{{agent_id.field}}` syntax for explicit access

---

## 📋 Quick Reference: Adding a Pipeline Checklist

When adding a new pipeline, ensure you've completed these steps:

- [ ] Created pipeline config in `config/pipelines/{pipeline_id}.yml`
- [ ] Created agent configs in `config/agents/{agent_id}.yml` for each agent
- [ ] Created prompt templates in `config/prompts/{agent_id}.jinja` for each agent
- [ ] Added pipeline to `config/pipeline.yml`
- [ ] Created UI manifest in `config/ui_manifests/{pipeline_id}.yml`
- [ ] Added UI manifest reference to `config/ui_manifest.yml`
- [ ] Created HITL templates in `config/hitl/` (if using gates)
- [ ] Created case YAML in `config/cases/{pipeline_id}.yml` (if using async HITL)
- [ ] Created icons in `ui/static/assets/` (optional)
- [ ] Ran `topaz-agent-kit generate agents --project .`
- [ ] Ran `topaz-agent-kit generate services --project .`
- [ ] Ran `topaz-agent-kit generate diagrams --project .`
- [ ] Tested with `topaz-agent-kit serve cli --project .`

---

**Happy Building! 🎉**

