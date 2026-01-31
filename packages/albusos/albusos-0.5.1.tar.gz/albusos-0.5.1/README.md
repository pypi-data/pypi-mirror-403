# AlbusOS

AI agent runtime. Build agents. Ship products.

## The Model

```
Agent → uses Pack → contains Pathways → made of Nodes
```

| Layer | What | Stateful? |
|-------|------|-----------|
| **Agent** | Entity with persona, goals, memory | Yes |
| **Pack** | Bundle of pathways | No |
| **Pathway** | DAG of nodes | No |
| **Node** | LLM, Tool, Code, etc. | No |

## Quick Start

```bash
uv sync
cp env.example .env
# Edit .env: set OPENAI_API_KEY or configure Ollama
uv run albus server --debug
```

## Example

### 1. Pack (the skills)

```python
# src/packs/research/pack.py
from packs.registry import deployable
from pathway_engine import pack_builder, Pathway, Connection, LLMNode, ToolNode

def build_research() -> Pathway:
    return Pathway(
        id="research.analyze.v1",
        nodes={
            "search": ToolNode(id="search", tool="web.search", args={"query": "{{topic}}"}),
            "analyze": LLMNode(id="analyze", prompt="Analyze: {{search.output.results}}"),
        },
        connections=[
            Connection(from_node="input", to_node="search"),
            Connection(from_node="search", to_node="analyze"),
            Connection(from_node="analyze", to_node="output"),
        ],
    )

@deployable
def RESEARCH_PACK():
    return pack_builder().id("research").pathway("research.analyze.v1", build_research).build()
```

### 2. Agent (uses the pack)

```python
# src/agents/researcher/agent.py
from agents.registry import agent
from pathway_engine import agent_builder

@agent
def RESEARCHER():
    return (
        agent_builder()
        .id("researcher")
        .persona("You are a thorough research analyst.")
        .use_pack("research")
        .as_reasoning_agent()
        .build()
    )
```

### 3. Use it

```bash
curl -X POST http://localhost:8080/api/v1/agents/researcher/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Research quantum computing", "thread_id": "s1"}'
```

## Node Types

| Node | What |
|------|------|
| `LLMNode` | LLM completion |
| `ToolNode` | Call stdlib tool |
| `CodeNode` | Python in sandbox |
| `AgentLoopNode` | Autonomous reasoning |
| `VisionNode` | Image analysis |
| `ASRNode` / `TTSNode` | Speech |

## stdlib Tools

| Tool | What |
|------|------|
| `web.search` / `web.fetch` | Web access |
| `llm.generate` | LLM completion |
| `code.execute` | Python sandbox |
| `memory.*` | Persistent storage |
| `vision.analyze` | Image analysis |
| `speech.*` | ASR / TTS |

## API

| Endpoint | What |
|----------|------|
| `POST /api/v1/agents/{id}/turn` | Talk to agent |
| `POST /api/v1/pathways/{id}/run` | Run pathway |
| `GET /api/v1/agents` | List agents |
| `GET /api/v1/packs` | List packs |

## Included Examples

| Pack | What it shows |
|------|---------------|
| `competitor_intel` | Web research, AgentLoopNode, CodeNode |
| `image_narrator` | Vision → TTS pipeline |
| `voice_assistant` | ASR → LLM → TTS voice loop |

## Docs

- [Building Agents](docs/BUILDING_AGENTS.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development](docs/DEVELOPMENT.md)
