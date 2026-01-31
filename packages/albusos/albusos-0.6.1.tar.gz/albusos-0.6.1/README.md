# AlbusOS

AI agent runtime. Build pathways. Ship products.

## Core Concepts

**Pathways** are computation graphs (nodes + connections) that process data.  
**Agents** are persistent entities with identity, memory, and skills.  
**Skills** are reusable pathways that agents can invoke.

```
Pathway = Nodes + Connections (fully serializable)
   │
   ├── LLMNode      → Text generation, reasoning (canonical)
   ├── ToolNode     → Call external tools (canonical)
   └── AgentLoopNode → Autonomous multi-step reasoning (canonical)

Agent = Identity + Capabilities + Skills + Memory
   │
   ├── Host Agent (Superagent) → All tools, spawns agents, authors pathways
   └── Worker Agents           → Specialist agents with focused skills
```

**Canonical Language**: Pathways use only `llm`, `tool`, and `agent_loop` nodes. This ensures quality, portability, and enables Host to author pathways automatically.

## Quick Start

```bash
# Install
uv sync
cp config/albus.yaml.example albus.yaml

# Configure (edit albus.yaml for Ollama or set OPENAI_API_KEY)
export OPENAI_API_KEY=sk-...  # or use local Ollama

# Start server
./bin/albus-server --port 8082

# Verify it works
curl http://127.0.0.1:8082/api/v1/health
curl http://127.0.0.1:8082/api/v1/agents/host
```

**Proven**: All concepts work live on the server. Run `python3 tests/run_all_proofs.py` to see proof exercises.

## Create Pathways

### Method 1: Host Agent Authors Pathways (Recommended)

Host agent can author pathways using canonical language:

```bash
# Host uses pathway.create tool internally
curl -X POST http://127.0.0.1:8082/api/v1/agents/host/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a pathway that searches the web and summarizes results"}'
```

### Method 2: Direct API

```bash
# Create pathway via REST API
curl -X POST http://127.0.0.1:8082/api/v1/pathways \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Research Pipeline",
    "nodes": [
      {"id": "search", "type": "tool", "config": {"tool_name": "web.search", "args": {"query": "{{topic}}"}}},
      {"id": "summarize", "type": "llm", "config": {"prompt": "Summarize: {{search.results}}", "model": "auto"}}
    ],
    "connections": [{"from": "search", "to": "summarize"}]
  }'

# Run it
curl -X POST http://127.0.0.1:8082/api/v1/pathways/{pathway_id}/run \
  -H "Content-Type: application/json" \
  -d '{"inputs": {"topic": "AI regulation"}}'
```

### Method 3: Natural Language Generation

```bash
curl -X POST http://127.0.0.1:8082/api/v1/tools/pathway.create \
  -H "Content-Type: application/json" \
  -d '{"description": "Search for news about a topic and write a summary"}'
# → LLM generates canonical pathway (llm/tool/agent_loop only)
```

## Create Agents

```bash
# Create a specialist agent
curl -X POST http://127.0.0.1:8082/api/v1/agents \
  -H "Content-Type: application/json" \
  -d '{
    "id": "researcher",
    "name": "Researcher",
    "persona": "You are a research specialist",
    "goals": ["Find accurate information", "Verify sources"],
    "tools": ["web.*", "search.*"],
    "max_steps": 10
  }'

# Agents can spawn other agents (Host only)
curl -X POST http://127.0.0.1:8082/api/v1/agents/host/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Spawn a writer agent for content creation"}'

# Agents can invoke each other
curl -X POST http://127.0.0.1:8082/api/v1/agents/researcher/turn \
  -H "Content-Type: application/json" \
  -d '{"message": "Research quantum computing applications"}'
```

## Canonical Node Types

**Only these node types are canonical** (enforced by `PATHWAY_ARCHITECT_SYSTEM`):

| Node | Use For | Config |
|------|---------|--------|
| `llm` | Text generation, reasoning, analysis | `prompt`, `model`, `temperature` |
| `tool` | External operations | `tool_name`, `args` |
| `agent_loop` | Autonomous multi-step reasoning | `goal`, `tools`, `max_steps` |

**Not canonical**: `code`, `transform` (use `llm` instead for text processing)

## stdlib Tools

| Category | Tools |
|----------|-------|
| **Web** | `web.search`, `web.fetch`, `web.news` |
| **LLM** | `llm.generate`, `llm.embed`, `llm.json` |
| **Code** | `code.execute` |
| **Memory** | `memory.set`, `memory.get`, `memory.search` |
| **Workspace** | `workspace.read_file`, `workspace.write_file` |
| **Vision** | `vision.analyze`, `vision.ocr` |
| **Speech** | `speech.tts`, `speech.asr` |
| **Knowledge Graph** | `kg.upsert`, `kg.query` |

## User Experience: Talking to Host

**Host is the superagent** - your pathway editor, agent editor, and co-creator.

The recommended entry point is `/api/v1/chat` which delegates to the Host superagent:

```bash
# Simple entry point - Host handles everything
curl -X POST http://127.0.0.1:8082/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Create a pathway that summarizes articles"}'

# Host will:
# 1. Use pathway.create tool to build the pathway
# 2. Store it for you
# 3. Return the pathway ID and details
```

**What Host can do:**
- **Pathway Editor**: "Create a pathway that..." → Host uses `pathway.create` tool
- **Agent Editor**: "Spawn a researcher agent" → Host uses `agent.spawn` tool  
- **Co-Creator**: "Build a data pipeline" → Host creates pathway, runs it, shows results
- **Conversation**: Maintains history and memory across turns (via `thread_id`)

**Conversation continuity:**
```bash
# First turn
curl -X POST http://127.0.0.1:8082/api/v1/chat \
  -d '{"message": "Create a research pathway", "thread_id": "my-session"}'

# Follow-up (Host remembers context)
curl -X POST http://127.0.0.1:8082/api/v1/chat \
  -d '{"message": "Now run it with topic=AI", "thread_id": "my-session"}'
```

## API Endpoints

### Chat (Recommended Entry Point)
| Endpoint | Description |
|----------|-------------|
| `POST /api/v1/chat` | Talk to Host superagent (pathway editor, agent orchestrator, co-creator) |

### Agents
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/agents` | List all agents |
| `GET /api/v1/agents/{id}` | Get agent details (includes skills) |
| `GET /api/v1/agents/{id}/skills` | List all skills for an agent |
| `POST /api/v1/agents` | Create new agent |
| `POST /api/v1/agents/{id}/turn` | Execute agent turn (direct access) |
| `DELETE /api/v1/agents/{id}` | Delete agent |

### Pathways
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/pathways` | List all pathways |
| `GET /api/v1/pathways/{id}` | Get pathway details |
| `POST /api/v1/pathways` | Create pathway (direct API) |
| `POST /api/v1/pathways/{id}/run` | Execute pathway |
| `GET /api/v1/pathways/{id}/export` | Export as JSON |

### Tools
| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/tools` | List all tools |
| `POST /api/v1/tools/{name}` | Call tool directly |

## Skills: Reusable Pathways

**Skills are pathways wrapped as tools** that agents can invoke. They're the primary way agents extend capabilities.

### What Are Skills?

- **Skills = Pathways**: Every skill wraps a `Pathway` (computation graph)
- **Invoked via `skill.invoke`**: Agents call `skill.invoke({skill_id: "code", inputs: {...}})`
- **Reusable**: Same skill can be used by multiple agents
- **Composable**: Skills can contain any nodes (`llm`, `tool`, `agent_loop`)

See: `docs/SKILLS.md` for full documentation.

### Host Skills

Host (the superagent) has 3 built-in skills:

1. **`code`**: Programming tasks (`code.*`, `workspace.*` tools)
2. **`research`**: Web/search information (`web.*` tools)
3. **`files`**: Workspace operations (`workspace.*` tools)

Note: Simple conversation is handled directly by agents via `AgentLoopNode` with conversation history and memory - no separate chat skill needed.

### Creating Skills

Skills are pathways that agents can invoke:

```python
from pathway_engine.domain.agent.skill import skill
from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.core import LLMNode, TransformNode

def _build_research_pathway():
    return Pathway(
        id="skill.research",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message}}\n\nResearch thoroughly. Say DONE when finished.",
                tools=["web.*", "search.*"],
                max_steps=6
            ),
            "result": TransformNode(
                id="result",
                expr='{"response": agent.get("response", ""), "skill": "research"}'
            )
        },
        connections=[Connection(from_node="agent", to_node="result")]
    )

RESEARCH_SKILL = skill(
    id="research",
    name="Research",
    description="Search the web and synthesize information",
    pathway_builder=_build_research_pathway,
    inputs={"message": "string - What to research"},
    outputs={"response": "string - Research findings"}
)

# Add to agent
agent.add_skill(RESEARCH_SKILL)
# Agent can now invoke: skill.invoke({skill_id: "research", inputs: {...}})
```

### Host Creates Pathways/Agents On Demand

Users can ask Host to create pathways or agents:

```
User: "Create a cool pathway that summarizes articles"
→ Host uses pathway.create tool (natural language → pathway)
→ Pathway stored and ready to use

User: "Create a cool agent that visualizes data"
→ Host uses agent.spawn tool
→ Agent created with visualization capabilities
```

**Proof**: `tests/proof_host_creates_pathways_and_agents.py`

### External Skills Integration

**Agent Skills Format** (agentskills.io): Filesystem-based skills with `SKILL.md` files.

**Current Status**: AlbusOS uses pathways (not Agent Skills format), but integration is possible:
- Load `SKILL.md` files from directories
- Convert to pathways (wrap scripts as `code.execute` nodes)
- Add to agents as skills

**Future**: Skill marketplace, remote skills, agent templates.

See: `docs/SKILLS.md` for integration details.

### External Skills (Agent Skills Format)

Load skills from filesystem directories compatible with [Agent Skills](https://agentskills.io):

```bash
# Set skill directories (comma-separated)
export ALBUS_SKILL_DIRS="/path/to/skills,/path/to/more/skills"
./bin/albus-server

# Or use CLI
albus skills list --agent-id host
```

**CLI Commands:**
- `albus skills list [--agent-id host]` - List skills for an agent
- `albus skills load --dirs /path/to/skills` - Show instructions for loading skills

**API Endpoints:**
- `GET /api/v1/agents/{id}/skills` - List all skills for an agent

See `docs/EXTERNAL_SKILLS.md` and `docs/SKILLS_GUIDE.md` for details.

## Triggered Pathways

Pathways can have triggers attached directly - no pack wrapper needed:

### Simple Examples

**Daily scheduled pathway** (runs every day at 9am):
```bash
curl -X POST http://127.0.0.1:8082/api/v1/chat \
  -d '{"message": "Create a pathway that summarizes my emails, triggered daily at 9am"}'

# Host creates:
# pathway.create({
#   name: "email_summary",
#   nodes: [...],
#   trigger: {type: "timer", schedule: "0 9 * * *"}
# })
```

**Webhook-triggered pathway**:
```bash
curl -X POST http://127.0.0.1:8082/api/v1/chat \
  -d '{"message": "Create a pathway that processes GitHub events when a webhook fires"}'

# Host creates:
# pathway.create({
#   name: "github_processor",
#   nodes: [...],
#   trigger: {type: "webhook", topic: "github-events"}
# })
```

**Event-bus triggered pathway**:
```bash
curl -X POST http://127.0.0.1:8082/api/v1/chat \
  -d '{"message": "Create a pathway that runs when a user signs up"}'

# Host creates:
# pathway.create({
#   name: "welcome_user",
#   nodes: [...],
#   trigger: {type: "event", channel: "user-signup"}
# })
```

### Trigger Types

| Type | Config | Example |
|------|--------|---------|
| `timer` | `schedule` (cron) | `{type: "timer", schedule: "0 9 * * *"}` |
| `webhook` | `topic` | `{type: "webhook", topic: "github-events"}` |
| `event` | `channel` | `{type: "event", channel: "user-signup"}` |
| `mcp.*` | `event` | `{type: "mcp.gmail", event: "message_received"}` |

**For most users:** Just create triggered pathways directly via Host. The trigger is stored with the pathway.

## Pathway Storage

Pathways are persisted via `StudioStore`:
- **Host-authored**: `source="host:authored"` (created via `pathway.create` tool)
- **User pathways**: `source="user:api"` or `source="user:session_xyz"`

## Multi-Agent Systems

Agents can work together:

```python
# Host spawns specialist agents
host.turn("Spawn a researcher agent", thread_id="...")
# → Uses agent.spawn tool

# Agents invoke each other
researcher.turn("Find info about X", thread_id="...")
# → Uses agent.turn tool

# Agents share skills
shared_skill = skill(...)
researcher.add_skill(shared_skill)
writer.add_skill(shared_skill)  # Same skill instance
```

## Model Routing

AlbusOS automatically routes to the best model for each task:

```yaml
# albus.yaml
model_routing:
  default_profile: local  # or: balanced, premium
```

| Profile | Models |
|---------|--------|
| `local` | Ollama (qwen2.5:7b, llama3.1:8b) |
| `balanced` | Mix of local + cloud |
| `premium` | Best cloud models (GPT-4o, Claude) |

## Architecture

```
┌─────────────────────────────────────────┐
│              Transport                  │
│    REST API (/api/v1/agents,            │
│     /api/v1/pathways)                   │
├─────────────────────────────────────────┤
│            Application                  │
│  AgentService (CRUD, turns)             │
│  PathwayService (deploy, create)        │
├─────────────────────────────────────────┤
│           Pathway Engine                │
│  PathwayVM (execution)                  │
│  Nodes (llm, tool, agent_loop)          │
│  AgentLoopNode (agentic execution)      │
├─────────────────────────────────────────┤
│              stdlib                     │
│  Tools (web.*, workspace.*, etc.)       │
│  LLM Providers (OpenAI, Anthropic, etc.)│
│  Capability Routing                     │
└─────────────────────────────────────────┘
```

**Key Principles:**
- **Pathways** = Computation graphs (serializable, executable)
- **Agents** = Persistent entities (identity, memory, skills)
- **Host (Superagent)** = Primary agent with all tools, spawns workers, authors pathways
- **Skills** = Reusable pathways (agents invoke via `skill.invoke`)
- **Canonical Language** = Only `llm`, `tool`, `agent_loop` nodes
- **Multi-Agent** = Host spawns workers, agents communicate via `agent.turn`
- **Storage** = Unified `StudioStore` for all pathways

## Proof Exercises

Run proof exercises to validate the product vision:

```bash
# Run all proofs
python3 tests/run_all_proofs.py

# Individual proofs
python3 tests/proof_pathways_are_computation_graphs.py
python3 tests/proof_agents_are_persistent_entities.py
python3 tests/proof_canonical_language_enforcement.py
python3 tests/proof_host_agent_can_author_pathways.py
python3 tests/proof_pathways_can_be_shipped.py
python3 tests/proof_multiagent_systems_with_skills.py
python3 tests/proof_live_server_pathways.py  # Requires server running
python3 tests/proof_live_server_agents.py    # Requires server running
python3 tests/proof_host_stores_pathways.py  # Host storage proof
python3 tests/proof_host_creates_pathways_and_agents.py  # Host creates on demand
```

## Development

```bash
# Run tests
uv run pytest tests/ -v

# Check layering
uv run python tools/check_layering.py

# Start server
./bin/albus-server --port 8082

# Verify live
curl http://127.0.0.1:8082/api/v1/health
```

## License

Apache 2.0
