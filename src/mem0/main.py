"""
Personal Assistant with Long-Term Memory
=========================================
Microsoft Agent Framework 1.0 + Mem0 + Azure OpenAI (Foundry GPT-4o)

A conversational assistant that remembers user preferences, interests,
and personal details across sessions using Mem0 as the memory layer.
"""

import asyncio
import os
from pathlib import Path
from typing import Annotated

from dotenv import load_dotenv
from mem0 import MemoryClient
from pydantic import Field

from agent_framework import Agent
from agent_framework.openai import OpenAIChatClient

load_dotenv(Path(__file__).resolve().parent / ".env")

USER_ID = os.getenv("USER_ID", "demo_user")

mem0 = MemoryClient(api_key=os.environ["MEM0_API_KEY"])


def _extract_memories(response) -> list:
    """Handle both list and dict response formats from Mem0 API."""
    if isinstance(response, list):
        return response
    if isinstance(response, dict):
        return response.get("results", response.get("memories", []))
    return []


class MemoryTools:
    """Function tools that give the agent long-term memory via Mem0."""

    def __init__(self, client: MemoryClient, user_id: str):
        self.client = client
        self.user_id = user_id
        self._user_filter = {"AND": [{"user_id": user_id}]}

    def save_memory(
        self,
        information: Annotated[
            str,
            Field(description="Important information about the user to remember"),
        ],
    ) -> str:
        """Save important user information to long-term memory.
        Call this when the user shares personal details, preferences,
        goals, dietary restrictions, or anything worth remembering."""
        self.client.add(
            [{"role": "user", "content": information}],
            user_id=self.user_id,
        )
        return f"Saved to memory: {information}"

    def search_memory(
        self,
        query: Annotated[
            str,
            Field(description="Natural language query to search stored memories"),
        ],
    ) -> str:
        """Search long-term memory for relevant information about the user.
        Use this to recall preferences, past details, or context before responding."""
        results = self.client.search(query, filters=self._user_filter)
        memories = _extract_memories(results)
        if not memories:
            return "No relevant memories found."
        return "\n".join(f"- {m['memory']}" for m in memories)

    def get_all_memories(self) -> str:
        """Retrieve everything stored in memory about the user.
        Use when the user asks what you remember about them."""
        results = self.client.get_all(filters=self._user_filter)
        memories = _extract_memories(results)
        if not memories:
            return "No memories stored yet."
        return "\n".join(f"- {m['memory']}" for m in memories)


AGENT_INSTRUCTIONS = """\
You are a personal assistant with long-term memory powered by Mem0.

MEMORY WORKFLOW:
1. At the START of every conversation turn, call 'search_memory' with a query
   relevant to the user's message to recall any useful context.
2. When the user shares personal information (name, preferences, allergies,
   hobbies, goals, important dates, etc.), call 'save_memory' to store it.
3. When the user asks "what do you know/remember about me?", call 'get_all_memories'.
4. Weave remembered facts naturally into your responses — don't just list them.

Be warm, helpful, and demonstrate genuine recall of the user's preferences.\
"""


async def main() -> None:
    memory_tools = MemoryTools(client=mem0, user_id=USER_ID)

    client = OpenAIChatClient(
        model=os.environ["AZURE_OPENAI_MODEL"],
        azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
        api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
    )

    agent = Agent(
        client=client,
        name="PersonalAssistant",
        instructions=AGENT_INSTRUCTIONS,
        tools=[
            memory_tools.save_memory,
            memory_tools.search_memory,
            memory_tools.get_all_memories,
        ],
    )

    print("=" * 60)
    print("  Personal Assistant with Mem0 Long-Term Memory")
    print("  Microsoft Agent Framework 1.0  |  Foundry GPT-4o")
    print("=" * 60)
    print("  Type 'quit' to exit  |  'memories' to view stored memories")
    print("-" * 60)

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
            raw = mem0.get_all(filters={"AND": [{"user_id": USER_ID}]})
            memories = _extract_memories(raw)
            if memories:
                print("\n  ── Stored Memories ──")
                for m in memories:
                    print(f"    • {m['memory']}")
                print("  ── End ──")
            else:
                print("  No memories stored yet.")
            continue

        result = await agent.run(user_input)
        print(f"\nAssistant: {result}")


if __name__ == "__main__":
    asyncio.run(main())
