# RiyadhAI Agents SDK

Realtime framework for production-grade multimodal and voice AI agents.

## Installation

```bash
pip install riyadhai
```

## Quickstart

```python
from dotenv import load_dotenv

from riyadhai import agents
from riyadhai.agents import AgentSession, Agent
from riyadhai.plugins import google

load_dotenv()


async def entrypoint(ctx: agents.JobContext):
    await ctx.connect()

    session = AgentSession(
        llm=google.GeminiRealtimeModel()
    )

    await session.start(
        room=ctx.room,
        agent=Agent(instructions="You are a helpful voice AI assistant.")
    )

    await session.generate_reply(
        instructions="Greet the user and offer your assistance."
    )


if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
```
