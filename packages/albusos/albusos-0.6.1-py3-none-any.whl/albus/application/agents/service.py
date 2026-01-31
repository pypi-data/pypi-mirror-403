"""AgentService - Manages agent lifecycle and execution.

Agents are THE primitive in AlbusOS. This service handles:
- Agent CRUD (create, read, update, delete)
- Agent turns (send message, get response)
- Host agent (pre-registered at startup)

Uses the Agent model from pathway_engine.domain.agent.

Usage:
    service = AgentService(pathway_service=..., pathway_vm=...)
    
    # Host is pre-registered
    host = service.get("host")
    
    # Create a worker agent
    agent = service.create(
        id="researcher",
        name="Researcher",
        persona="You are a research specialist...",
        tools=["workspace.*", "web.*"],
    )
    
    # Execute a turn
    result = await service.turn("researcher", "Find info about X", thread_id="...")
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pathway_engine.domain.agent import (
    Agent,
    AgentCapabilities,
    AgentBuilder,
    agent_builder,
    CognitivePresets,
)

if TYPE_CHECKING:
    from albus.application.pathways import PathwayService
    from pathway_engine.application.kernel import PathwayVM
    from pathway_engine.domain.context import Context

logger = logging.getLogger(__name__)


# =============================================================================
# HOST AGENT DEFINITION
# =============================================================================

HOST_PERSONA = """You are Host, the primary AI assistant in AlbusOS. You are intelligent, capable, fast, and adaptable.

YOUR CAPABILITIES:

You have access to ALL tools:
- workspace.* - File operations (read, write, list, etc.)
- code.* - Code execution and debugging
- web.* - Web search, fetch, news
- search.* - Search capabilities
- memory.* - Persistent memory (set, get, search)
- llm.* - Direct LLM access (generate, embed, json)
- vector.* - Vector operations
- kg.* - Knowledge graph operations
- vision.* - Vision/OCR analysis
- speech.* - Speech TTS/ASR
- skill.* - Skills (invoke, list, load, share)
- pathway.* - Pathways (create, invoke, list)
- agent.* - Agents (spawn, turn, list)
- mcp.* - MCP tools
- env.list_tools - See what you can do

CRITICAL: ACT, DON'T DESCRIBE. When asked to CREATE/BUILD/DO → USE TOOLS IMMEDIATELY.

STRATEGY:

1. SIMPLE QUESTIONS → Answer directly
   - "What's 2+2?" → "4"
   - "What can you do?" → Use skill.list() or env.list_tools() to show actual capabilities

2. CREATE PATHWAYS → CALL pathway.create TOOL NOW
   - "Create a research pathway" → pathway.create({description: "research pathway: web search → embeddings → vector store → summarize"})
   - "Build a pathway that..." → pathway.create({description: "..."})
   - MANDATORY: Use the tool, don't describe what you would do

3. USE TOOLS → Execute immediately
   - "Search for X" → web.search({query: "X"})
   - "List skills" → skill.list()
   - "Read file" → workspace.read_file({path: "..."})

4. COMPLEX TASKS → Build → Run → Show results
   - Create pathway → pathway.invoke() → Show outputs
   - Spawn agent → agent.turn() → Get results
   - Chain skills → Execute → Output

REMEMBER: Action > Words. When user asks to create/build/do → CALL THE TOOL.

CRITICAL: When asked to create/build/do something:
- USE THE TOOLS - Don't just describe what you would do
- CREATE PATHWAYS - Use pathway.create tool
- EXECUTE - Run pathways, use tools, show results
- BE ACTION-ORIENTED - Do it, don't plan it

EXAMPLES:

Simple: "What's 2+2?" → "4"

Complex: "Build a data pipeline" →
  pathway.create({description: "Data pipeline: fetch → transform → analyze → report", run: true})

Multi-agent: "Research and code solution" →
  agent.spawn({id: "researcher", persona: "Research specialist", tools: ["web.*"]})
  agent.spawn({id: "coder", persona: "Python expert", tools: ["code.*"]})
  agent.turn({agent_id: "researcher", message: "Find best practices"})
  agent.turn({agent_id: "coder", message: "Implement based on research"})

Adaptive: "I have skills in /my-skills, create an agent that uses them" →
  agent.spawn({id: "custom", skills_directory: "/my-skills", ...})

Be proactive, fast, and adaptive. Use the right tool for each task. Think architecturally for complex work.
"""


async def build_host_agent(
    *,
    external_skill_dirs: list[str] | None = None,
) -> Agent:
    """Build the Host agent with skills.
    
    Args:
        external_skill_dirs: Optional list of directories to load external skills from
                          (e.g., agentskills.io format)
    
    Returns:
        Configured Host agent
    """
    agent = (
        agent_builder()
        .id("host")
        .name("Host")
        .persona(HOST_PERSONA)
        .goal("Answer simple questions directly")
        .goal("Use the right skill for each task type")
        # Skills
        .tool("skill.*")         # All skill tools (invoke, list, load, share)
        # Pathways
        .tool("pathway.*")       # All pathway tools (create, invoke, list)
        # Agents
        .tool("agent.*")         # All agent tools (spawn, turn, list)
        # Core capabilities
        .tool("workspace.*")     # File operations
        .tool("code.*")          # Code execution
        .tool("web.*")           # Web search and fetch
        .tool("search.*")        # Search capabilities
        .tool("memory.*")        # Memory operations
        .tool("llm.*")           # Direct LLM access
        .tool("vector.*")        # Vector operations
        .tool("kg.*")            # Knowledge graph
        .tool("vision.*")        # Vision/OCR
        .tool("speech.*")        # Speech TTS/ASR
        .tool("mcp.*")           # MCP tools
        .tool("env.list_tools")  # Introspection
        .can_spawn(True)
        .max_steps(10)  # Balanced: enough for complex tasks, fast for simple ones
        .as_assistant()
        .build()
    )
    
    # Load all Host skills (built-in + external) - canonical SKILL.md format
    from albus.application.agents.skills import load_all_host_skills
    
    try:
        all_skills = await load_all_host_skills()
        for skill_obj in all_skills:
            agent.add_skill(skill_obj)
        logger.info(f"Loaded {len(all_skills)} skills for Host (canonical SKILL.md format)")
    except Exception as e:
        logger.warning(f"Failed to load Host skills: {e}", exc_info=True)
    
    # Load external skills if directories provided
    if external_skill_dirs:
        from pathway_engine.infrastructure.skill_loader import load_agent_skills_from_directories
        
        try:
            external_skills = await load_agent_skills_from_directories(*external_skill_dirs)
            for skill in external_skills:
                agent.add_skill(skill)
                logger.info(f"Loaded external skill: {skill.id}")
        except Exception as e:
            logger.warning(f"Failed to load external skills: {e}", exc_info=True)
    
    return agent


# =============================================================================
# AGENT SERVICE
# =============================================================================

class AgentService:
    """Manages agent lifecycle. Host is pre-registered at startup.
    
    Architecture:
        All agents are peers. This service provides CRUD and turn operations.
        Host is special only because it's pre-registered and has can_spawn=True.
        
        Agent execution uses the Agent.turn() method from pathway_engine,
        which handles system prompt building, tool gathering, and AgentLoopNode.
    """
    
    def __init__(
        self,
        *,
        pathway_service: "PathwayService",
        pathway_vm: "PathwayVM",
    ):
        """Create AgentService with dependencies.
        
        Args:
            pathway_service: For resolving agent skills (pathways)
            pathway_vm: For executing agent turns
        """
        self._pathway_service = pathway_service
        self._pathway_vm = pathway_vm
        self._agents: dict[str, Agent] = {}
        self._host_initialized = False
        
        # Register built-in agents (Host will be loaded synchronously, external skills loaded lazily)
        self._register_builtin()
    
    def _register_builtin(self) -> None:
        """Register Host and other built-in agents (synchronous part)."""
        # Build host with built-in skills only (synchronous)
        agent = (
            agent_builder()
            .id("host")
            .name("Host")
            .persona(HOST_PERSONA)
            .goal("Answer simple questions directly")
            .goal("Use the right skill for each task type")
            .tool("skill.invoke")    # Invoke skills
            .tool("skill.list")      # List available skills
            .tool("agent.spawn")     # Create specialist agents
            .tool("agent.turn")      # Invoke other agents
            .can_spawn(True)
            .max_steps(6)
            .as_assistant()
            .build()
        )
        
        # Skills will be loaded asynchronously (canonical SKILL.md format)
        # This includes both built-in and external skills
        self._agents["host"] = agent
        logger.info("Registered Host agent (skills will be loaded asynchronously)")
    
    async def ensure_host_external_skills(self) -> None:
        """Load all Host skills (built-in + external) using canonical SKILL.md format."""
        host = self._agents.get("host")
        if not host:
            return
        
        # Load all skills using canonical loader (SKILL.md format)
        from albus.application.agents.skills import load_all_host_skills
        
        try:
            all_skills = await load_all_host_skills()
            
            # Add skills that aren't already loaded
            existing_skills = set(host.list_skills())
            added_count = 0
            
            for skill_obj in all_skills:
                if skill_obj.id not in existing_skills:
                    host.add_skill(skill_obj)
                    added_count += 1
                    logger.info(f"Loaded skill: {skill_obj.id} ({skill_obj.name})")
            
            if added_count > 0:
                logger.info(f"Host now has {len(host.list_skills())} total skills")
        except Exception as e:
            logger.warning(f"Failed to load Host skills: {e}", exc_info=True)
    
    # =========================================================================
    # CRUD Operations
    # =========================================================================
    
    def create(
        self,
        *,
        id: str,
        name: str,
        persona: str,
        goals: list[str] | None = None,
        tools: list[str] | None = None,
        can_spawn: bool = False,
        model: str = "auto",
        max_steps: int = 10,
        temperature: float = 0.7,
        preset: str | None = None,
    ) -> Agent:
        """Create a new agent.
        
        Args:
            id: Unique identifier
            name: Display name
            persona: System prompt / identity
            goals: List of goals for the agent
            tools: Tool patterns (defaults to workspace.* and code.*)
            can_spawn: Can create other agents (default False)
            model: Default model for this agent
            max_steps: Maximum steps per turn
            temperature: LLM temperature
            preset: Cognitive preset (assistant, reasoning_agent, orator, supervisor)
            
        Returns:
            Created Agent
            
        Raises:
            ValueError: If agent with ID already exists
        """
        if id in self._agents:
            raise ValueError(f"Agent already exists: {id}")
        
        builder = agent_builder().id(id).name(name).persona(persona)
        
        # Add goals
        for goal in (goals or []):
            builder = builder.goal(goal)
        
        # Add tools
        for tool in (tools or ["workspace.*", "code.*"]):
            builder = builder.tool(tool)
        
        # Set capabilities
        builder = (
            builder
            .can_spawn(can_spawn)
            .model(model)
            .max_steps(max_steps)
            .temperature(temperature)
        )
        
        # Apply cognitive preset
        if preset == "reasoning_agent":
            builder = builder.as_reasoning_agent()
        elif preset == "orator":
            builder = builder.as_orator()
        elif preset == "supervisor":
            builder = builder.as_supervisor()
        elif preset == "assistant" or preset is None:
            builder = builder.as_assistant()
        
        agent = builder.build()
        self._agents[id] = agent
        logger.info("Created agent: %s", id)
        return agent
    
    def get(self, agent_id: str) -> Agent | None:
        """Get an agent by ID.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            Agent if found, None otherwise
        """
        return self._agents.get(agent_id)
    
    def list(self) -> list[Agent]:
        """List all registered agents.
        
        Returns:
            List of all agents
        """
        return list(self._agents.values())
    
    def delete(self, agent_id: str) -> bool:
        """Delete an agent.
        
        Args:
            agent_id: Agent identifier
            
        Returns:
            True if deleted, False if not found
            
        Note:
            Cannot delete the Host agent.
        """
        if agent_id == "host":
            logger.warning("Cannot delete Host agent")
            return False
        
        if agent_id not in self._agents:
            return False
        
        del self._agents[agent_id]
        logger.info("Deleted agent: %s", agent_id)
        return True
    
    # =========================================================================
    # Execution
    # =========================================================================
    
    async def turn(
        self,
        agent_id: str,
        message: str,
        thread_id: str,
        *,
        context: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """Execute one turn of conversation with an agent.
        
        This is the main entry point for agent interaction. It uses the
        Agent.turn() method from pathway_engine which handles:
        - Building the system prompt (persona, goals, cognitive style)
        - Gathering available tools
        - Running AgentLoopNode
        - State persistence
        
        Args:
            agent_id: Agent to invoke
            message: User message / task
            thread_id: Thread/session identifier
            context: Additional context to pass
            attachments: Files/images to attach
            
        Returns:
            dict with:
                - success: bool
                - response: str (agent's response)
                - completed: bool (did agent signal completion)
                - steps_taken: int
                - error: str | None
        """
        agent = self.get(agent_id)
        if agent is None:
            return {
                "success": False,
                "error": f"Agent not found: {agent_id}",
                "response": "",
                "completed": False,
                "steps_taken": 0,
            }
        
        try:
            # Inject services into context for tools
            ctx = self._pathway_vm.ctx
            if not hasattr(ctx, "extras") or ctx.extras is None:
                ctx.extras = {}
            ctx.extras["agent_service"] = self
            ctx.extras["pathway_service"] = self._pathway_service
            
            # Use the Agent's turn method which handles everything
            result = await agent.turn(
                message=message,
                thread_id=thread_id,
                ctx=ctx,
                attachments=attachments,
                context=context,
            )
            
            return {
                "success": True,
                "response": result.get("response", ""),
                "completed": result.get("completed", False),
                "steps_taken": result.get("steps_taken", 0),
                "agent_id": result.get("agent_id", agent_id),
                "thread_id": result.get("thread_id", thread_id),
                "error": None,
            }
            
        except Exception as e:
            logger.exception("Agent turn failed: %s", agent_id)
            return {
                "success": False,
                "response": "",
                "completed": False,
                "steps_taken": 0,
                "error": str(e),
            }


__all__ = [
    "AgentService",
    "build_host_agent",
    "HOST_PERSONA",
]
