# Personal Assistant with Mem0 Long-Term Memory

A conversational assistant built with **Microsoft Agent Framework 1.0** that uses **Mem0** for persistent long-term memory and **Azure OpenAI GPT-4o** (via Microsoft Foundry) for language understanding.

## What It Does

The assistant remembers user preferences, interests, and personal details **across sessions**. It uses three memory tools powered by Mem0:

| Tool | Purpose |
|------|---------|
| `save_memory` | Stores user info (preferences, allergies, hobbies, etc.) |
| `search_memory` | Retrieves relevant memories for the current conversation |
| `get_all_memories` | Lists everything the assistant knows about the user |

## Prerequisites

- Python 3.10+
- [Mem0 API key](https://app.mem0.ai) (platform account)
- Azure OpenAI GPT-4o deployment in Microsoft Foundry

## Setup

**1. Navigate to the project folder**

    cd src\mem0

**2. Create and activate a virtual environment**

    python -m venv .venv
    .venv\Scripts\activate

**3. Install dependencies**

    pip install -r requirements.txt

**4. Configure environment** -- copy `.env.example` to `.env` and fill in your values:

    cp .env.example .env

| Variable | Description |
|----------|-------------|
| `MEM0_API_KEY` | Your Mem0 platform API key |
| `AZURE_OPENAI_ENDPOINT` | Azure OpenAI resource endpoint |
| `AZURE_OPENAI_MODEL` | Deployment name (e.g. `gpt-4o`) |
| `AZURE_OPENAI_API_KEY` | Azure OpenAI API key |
| `AZURE_OPENAI_API_VERSION` | API version (default: `2024-12-01-preview`) |
| `USER_ID` | Identifier for Mem0 memory scoping (default: `demo_user`) |

**5. Run**

    python main.py

## Example Conversation

    You: Hi! I love hiking and I'm vegetarian.
    Assistant: Hey! I've noted your love for hiking
    and that you're vegetarian. How can I help you today?

    You: Suggest a weekend plan for me.
    Assistant: Since you enjoy hiking and are vegetarian, how about a morning
    trail hike followed by lunch at a vegetarian-friendly restaurant nearby?

    You: memories
      -- Stored Memories --
        - Loves hiking
        - Is vegetarian
      -- End --

    You: quit
    Goodbye!

## How It Works

1. **Agent Framework 1.0** creates an `Agent` with `OpenAIChatClient` pointing at your Foundry GPT-4o deployment
2. Three `MemoryTools` class methods are registered as function tools on the agent
3. On each turn the agent autonomously decides whether to search/save memories via Mem0
4. Mem0 Platform handles vector storage, deduplication, and semantic search in the cloud
5. Memories persist across sessions -- restart the script and the assistant still remembers

## Tech Stack

| Component | Package |
|-----------|---------|
| Agent orchestration | `agent-framework==1.0.0` |
| Long-term memory | `mem0ai` (Mem0 Platform) |
| LLM | Azure OpenAI GPT-4o via Microsoft Foundry |
| Auth | API key or `azure-identity` (DefaultAzureCredential) |
