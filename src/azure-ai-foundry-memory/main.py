"""
Personal Assistant with Azure AI Foundry Memory
=================================================
Microsoft Agent Framework 1.0 + Foundry Memory Provider + GPT-4o

A conversational assistant that remembers user preferences across turns
using the built-in FoundryMemoryProvider as a context provider. Unlike
explicit tool-based memory (e.g. Mem0), Foundry Memory works transparently:
it retrieves relevant memories, injects them as context, and stores new
information — all without the agent calling any tools.
"""

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from agent_framework import Agent, InMemoryHistoryProvider
from agent_framework.foundry import FoundryChatClient, FoundryMemoryProvider
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import (
    MemoryStoreDefaultDefinition,
    MemoryStoreDefaultOptions,
)
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

MEMORY_USER_SCOPE = os.getenv("MEMORY_USER_SCOPE", "demo_user")


async def main() -> None:
    endpoint = os.environ["FOUNDRY_PROJECT_ENDPOINT"]

    async with AIProjectClient(
        endpoint=endpoint,
        credential=DefaultAzureCredential(),
    ) as project_client:
        # ------------------------------------------------------------------
        # 1. Create a temporary memory store
        # ------------------------------------------------------------------
        memory_store_name = (
            f"agent_fw_memory_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
        )
        options = MemoryStoreDefaultOptions(
            chat_summary_enabled=False,
            user_profile_enabled=True,
            user_profile_details=(
                "Remember the user's name, dietary preferences, hobbies, "
                "interests, and any personal facts they share. "
                "Avoid sensitive data such as financials or credentials."
            ),
        )
        memory_store_def = MemoryStoreDefaultDefinition(
            chat_model=os.environ["FOUNDRY_MODEL"],
            embedding_model=os.environ["AZURE_OPENAI_EMBEDDING_MODEL"],
            options=options,
        )

        print(f"Creating memory store '{memory_store_name}' ...")
        try:
            memory_store = await project_client.beta.memory_stores.create(
                name=memory_store_name,
                description="Personal assistant memory — Agent Framework demo",
                definition=memory_store_def,
            )
        except Exception as e:
            print(f"Failed to create memory store: {e}")
            return

        print(f"Memory store ready: {memory_store.name} ({memory_store.id})\n")

        # ------------------------------------------------------------------
        # 2. Build the agent with Foundry Memory as a context provider
        # ------------------------------------------------------------------
        client = FoundryChatClient(project_client=project_client)

        memory_provider = FoundryMemoryProvider(
            project_client=project_client,
            memory_store_name=memory_store.name,
            scope=MEMORY_USER_SCOPE,
            update_delay=0,
        )

        async with Agent(
            name="PersonalAssistant",
            client=client,
            instructions="""\
You are a personal assistant with long-term memory.
Memories from previous interactions are automatically provided to you as context.
Use them to personalise every response — reference remembered facts naturally.
When the user shares new personal details, acknowledge them warmly.\
""",
            context_providers=[
                memory_provider,
                InMemoryHistoryProvider(load_messages=False),
            ],
            default_options={"store": False},
        ) as agent:
            session = agent.create_session()

            print("=" * 60)
            print("  Personal Assistant with Azure AI Foundry Memory")
            print("  Microsoft Agent Framework 1.0  |  Foundry GPT-4o")
            print("=" * 60)
            print("  Type 'quit' to exit  |  'memories' to view stored memories")
            print("-" * 60)

            try:
                while True:
                    try:
                        user_input = input("\nYou: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print("\nGoodbye!")
                        break

                    if not user_input:
                        continue

                    if user_input.lower() in ("quit", "exit"):
                        print("Goodbye!")
                        break

                    if user_input.lower() == "memories":
                        res = await project_client.beta.memory_stores.search_memories(
                            name=memory_store.name,
                            scope=MEMORY_USER_SCOPE,
                        )
                        if res.memories:
                            print("\n  ── Stored Memories ──")
                            for m in res.memories:
                                print(f"    • {m.memory_item.content}")
                            print("  ── End ──")
                        else:
                            print("  No memories stored yet.")
                        continue

                    result = await agent.run(user_input, session=session)
                    print(f"\nAssistant: {result}")

                    # Brief pause so Foundry can process the new memory
                    await asyncio.sleep(2)

            finally:
                # ----------------------------------------------------------
                # 3. Dump all stored memories before cleanup
                # ----------------------------------------------------------
                print("\n" + "=" * 60)
                print("  MEMORY STORE INSPECTION (before deletion)")
                print("=" * 60)
                print(f"  Store name : {memory_store.name}")
                print(f"  Store ID   : {memory_store.id}")
                print(f"  User scope : {MEMORY_USER_SCOPE}")
                print("-" * 60)

                try:
                    res = await project_client.beta.memory_stores.search_memories(
                        name=memory_store.name,
                        scope=MEMORY_USER_SCOPE,
                    )
                    if res.memories:
                        print(f"  Total memories: {len(res.memories)}\n")
                        for i, m in enumerate(res.memories, 1):
                            print(f"  [{i}] {m.memory_item.content}")
                    else:
                        print("  No memories found.")
                except Exception as e:
                    print(f"  Could not fetch memories: {e}")

                print()
                print("  NOTE: Memory stores (beta) are managed via the SDK.")
                print("  You can also list all stores programmatically:")
                print("    stores = await project_client.beta.memory_stores.list()")
                print("=" * 60)
                input("\n  Press Enter to delete the memory store and exit...")

                print("Cleaning up memory store ...")
                await project_client.beta.memory_stores.delete(memory_store_name)
                print("Memory store deleted.")


if __name__ == "__main__":
    asyncio.run(main())
