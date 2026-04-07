    # Personal Assistant with Azure AI Foundry Memory

A conversational assistant built with **Microsoft Agent Framework 1.0** that uses **Azure AI Foundry Memory** as a built-in context provider and **GPT-4o** for language understanding.

## Mem0 vs Foundry Memory

| Aspect | Mem0 (`src/mem0`) | Foundry Memory (this project) |
|--------|-------------------|-------------------------------|
| Memory mechanism | Explicit tool calls (`save_memory`, `search_memory`) | Transparent context provider — no tools needed |
| Storage | Mem0 Platform (cloud) | Azure AI Foundry memory store |
| How it works | Agent decides when to save/search | Provider auto-retrieves, injects context, and stores new info |
| Auth | Mem0 API key | Azure AD (`DefaultAzureCredential`) |
| Embedding model | Managed by Mem0 | You deploy your own (e.g. `text-embedding-3-small`) |

## What It Does

The `FoundryMemoryProvider` works transparently behind the scenes:

1. **Retrieves** user-profile memories and contextual memories on each turn
2. **Injects** them into the agent's context automatically
3. **Stores** new information from the conversation after each turn

The agent doesn't need any memory tools — it just sees relevant memories in its context and responds naturally.

## Prerequisites

- Python 3.10+
- Azure AI Foundry project with:
  - A chat model deployment (e.g. `gpt-4o`)
  - An embedding model deployment (e.g. `text-embedding-3-small`)
  - Project endpoint (from the Foundry portal Overview page)
- Azure CLI installed and signed in (`az login`)

## Setup

**1. Navigate to the project folder**

    cd src\azure-ai-foundry-memory

**2. Create and activate a virtual environment**

    python -m venv .venv
    .venv\Scripts\activate

**3. Install dependencies**

    pip install -r requirements.txt

**4. Configure environment** -- copy `.env.example` to `.env` and fill in your values:

    cp .env.example .env

| Variable | Description |
|----------|-------------|
| `FOUNDRY_PROJECT_ENDPOINT` | Your Azure AI Foundry project endpoint URL |
| `FOUNDRY_MODEL` | Chat model deployment name (e.g. `gpt-4o`) |
| `AZURE_OPENAI_EMBEDDING_MODEL` | Embedding model deployment name (e.g. `text-embedding-3-small`) |
| `MEMORY_USER_SCOPE` | User identifier for memory isolation (default: `demo_user`) |

**5. Sign in to Azure**

The app uses `DefaultAzureCredential` for authentication, which requires a valid Azure login:

    az login

Verify the correct subscription is selected:

    az account show

**6. Run**

    python main.py

## Example Conversation

    Creating memory store 'agent_fw_memory_20260404_120000' ...
    Memory store ready: agent_fw_memory_20260404_120000 (memstore_abc123)

    ============================================================
      Personal Assistant with Azure AI Foundry Memory
      Microsoft Agent Framework 1.0  |  Foundry GPT-4o
    ============================================================
      Type 'quit' to exit  |  'memories' to view stored memories
    ------------------------------------------------------------

    You: Hi! I love hiking and I'm vegetarian.
    Assistant: Hey! Great to meet you. I'll keep in mind that you
    love hiking and are vegetarian.

    You: Suggest a weekend plan for me.
    Assistant: Since you enjoy hiking and are vegetarian, how about a
    morning trail hike followed by lunch at a vegetarian-friendly spot?

    You: memories
      -- Stored Memories --
        * The user loves hiking
        * The user is vegetarian
      -- End --

    You: quit
    Goodbye!

    ============================================================
      MEMORY STORE INSPECTION (before deletion)
    ============================================================
      Store name : agent_fw_memory_20260404_120000
      Store ID   : memstore_abc123
      User scope : demo_user
    ------------------------------------------------------------
      Total memories: 2


      [1] The user loves hiking
      [2] The user is vegetarian

      Press Enter to delete the memory store and exit...

    Cleaning up memory store ...
    Memory store deleted.

## Inspecting the Memory Store

Memory stores is a **beta** feature and does not have a dedicated page in the Azure Foundry portal yet. The app dumps all stored memories to the console before deletion so you can review them.

You can also inspect memory stores programmatically at any time:

    # List all memory stores in your project
    stores = await project_client.beta.memory_stores.list()

    # Search memories in a specific store
    res = await project_client.beta.memory_stores.search_memories(
        name="your_store_name",
        scope="demo_user",
    )
    for m in res.memories:
        print(m.memory_item.content)

## How It Works

1. A temporary **memory store** is created in Azure AI Foundry at startup (with user-profile extraction enabled)
2. `FoundryChatClient` connects to your Foundry project for LLM calls
3. `FoundryMemoryProvider` is attached as a **context provider** on the Agent
4. On each turn the provider transparently retrieves relevant memories, injects them, and stores new ones
5. Conversation history is intentionally not stored — the agent relies solely on Foundry Memory to demonstrate the capability
6. The memory store is **deleted on exit** to keep things clean (in production you'd persist it)

## Tech Stack

| Component | Package |
|-----------|---------|
| Agent orchestration | `agent-framework==1.0.0` |
| Memory provider | `agent_framework.foundry.FoundryMemoryProvider` |
| Foundry client | `azure-ai-projects` |
| LLM | GPT-4o via Azure AI Foundry |
| Embeddings | `text-embedding-3-small` (or your choice) |
| Auth | API key (`AzureKeyCredential`) |
