"""Intent Router - Smart routing based on user intent.

Instead of giving Host all tools and letting it decide, we:
1. Classify intent (fast, cheap LLM call)
2. Route to appropriate pathway
3. Execute with minimal tools

Intents:
- chat: Simple conversation, no tools needed
- code: Programming tasks
- research: Information gathering (web, search)
- files: Workspace operations
- agent: Create/invoke other agents
- complex: Multi-step tasks needing full agent
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.core import LLMNode, TransformNode, RouterNode
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode

if TYPE_CHECKING:
    from albus.application.pathways import PathwayService


# =============================================================================
# INTENT CLASSIFICATION
# =============================================================================

INTENT_CLASSIFIER_PROMPT = """Classify the user's intent into ONE category.

Categories:
- chat: Simple conversation, greeting, or question that can be answered from knowledge (no tools needed)
- code: Programming, coding, debugging, or technical implementation tasks
- research: Finding information, searching the web, looking things up
- files: Reading, writing, or managing files in the workspace
- agent: Creating or invoking specialist agents
- complex: Multi-step tasks that need planning and multiple capabilities

User message: {{message}}

Respond with ONLY the category name, nothing else."""


def build_intent_classifier_pathway() -> Pathway:
    """Classify user intent with a fast LLM call."""
    return Pathway(
        id="host.classify",
        name="Intent Classifier",
        description="Fast intent classification",
        nodes={
            "classify": LLMNode(
                id="classify",
                prompt=INTENT_CLASSIFIER_PROMPT,
                model="routing",  # Use fast routing model
                temperature=0.0,  # Deterministic
                max_tokens=20,
            ),
            "normalize": TransformNode(
                id="normalize",
                # Normalize the intent to lowercase, strip whitespace
                expr='classify.strip().lower().split()[0] if classify else "chat"',
            ),
        },
        connections=[
            Connection(from_node="classify", to_node="normalize"),
        ],
    )


# =============================================================================
# INTENT-SPECIFIC PATHWAYS
# =============================================================================

CHAT_SYSTEM = """You are a helpful AI assistant. Answer the user's question directly and concisely.
Do NOT use tools - just respond with your knowledge."""


def build_chat_pathway() -> Pathway:
    """Simple chat - no tools, just conversation."""
    return Pathway(
        id="host.chat",
        name="Chat",
        description="Direct conversation without tools",
        nodes={
            "respond": LLMNode(
                id="respond",
                prompt="{{message}}",
                system=CHAT_SYSTEM,
                model="chat",  # Use chat model
                temperature=0.7,
            ),
            "result": TransformNode(
                id="result",
                expr='{"response": respond, "completed": True, "intent": "chat"}',
            ),
        },
        connections=[
            Connection(from_node="respond", to_node="result"),
        ],
    )


CODE_SYSTEM = """You are a coding assistant. Help with programming tasks.
Use code.* and workspace.* tools as needed.
Be concise and focus on the code."""


def build_code_pathway() -> Pathway:
    """Code tasks - code and workspace tools only."""
    return Pathway(
        id="host.code",
        name="Code",
        description="Programming tasks with code tools",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message}}\n\nComplete the coding task. Say DONE when finished.",
                system=CODE_SYSTEM,
                tools=["code.*", "workspace.*"],
                model="code",  # Use code model (Claude)
                reasoning_mode="react",
                max_steps=8,
            ),
            "result": TransformNode(
                id="result",
                expr="""{
                    "response": agent.get("response", ""),
                    "completed": agent.get("completed", False),
                    "intent": "code"
                }""",
            ),
        },
        connections=[
            Connection(from_node="agent", to_node="result"),
        ],
    )


RESEARCH_SYSTEM = """You are a research assistant. Find and synthesize information.
Use web.* and search.* tools to find information.
Summarize findings clearly."""


def build_research_pathway() -> Pathway:
    """Research tasks - web and search tools."""
    return Pathway(
        id="host.research",
        name="Research",
        description="Information gathering with web tools",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message or query}}\n\nResearch this topic. Say DONE when finished.",
                system=RESEARCH_SYSTEM,
                tools=["web.*", "search.*", "llm.generate"],
                model="balanced",
                reasoning_mode="react",
                max_steps=6,
            ),
            "result": TransformNode(
                id="result",
                expr="""{
                    "response": agent.get("response", ""),
                    "completed": agent.get("completed", False),
                    "steps_taken": agent.get("steps_taken", 0),
                    "intent": "research"
                }""",
            ),
        },
        connections=[
            Connection(from_node="agent", to_node="result"),
        ],
    )


FILES_SYSTEM = """You are a file assistant. Help with workspace operations.
Use workspace.* tools to read, write, and manage files.
Be careful with file operations."""


def build_files_pathway() -> Pathway:
    """File operations - workspace tools only."""
    return Pathway(
        id="host.files",
        name="Files",
        description="Workspace file operations",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message}}\n\nComplete the file task. Say DONE when finished.",
                system=FILES_SYSTEM,
                tools=["workspace.*"],
                model="balanced",
                reasoning_mode="react",
                max_steps=6,
            ),
            "result": TransformNode(
                id="result",
                expr="""{
                    "response": agent.get("response", ""),
                    "completed": agent.get("completed", False),
                    "intent": "files"
                }""",
            ),
        },
        connections=[
            Connection(from_node="agent", to_node="result"),
        ],
    )


COMPLEX_SYSTEM = """You are Host, a capable AI assistant.
You can use any tools needed to complete complex tasks.
Plan your approach, then execute step by step."""


def build_complex_pathway() -> Pathway:
    """Complex tasks - full tool access with planning."""
    return Pathway(
        id="host.complex",
        name="Complex",
        description="Multi-step tasks with full capabilities",
        nodes={
            "agent": AgentLoopNode(
                id="agent",
                goal="{{message}}\n\nPlan and execute this task. Say DONE when finished.",
                system=COMPLEX_SYSTEM,
                tools=[
                    "workspace.*",
                    "code.*",
                    "web.*",
                    "search.*",
                    "llm.*",
                    "agent.*",
                ],
                model="reasoning",  # Use reasoning model for complex tasks
                reasoning_mode="plan_execute",  # Plan first
                max_steps=12,
            ),
            "result": TransformNode(
                id="result",
                expr="""{
                    "response": agent.get("response", ""),
                    "completed": agent.get("completed", False),
                    "intent": "complex"
                }""",
            ),
        },
        connections=[
            Connection(from_node="agent", to_node="result"),
        ],
    )


# =============================================================================
# MAIN ROUTER PATHWAY
# =============================================================================

def build_router_pathway() -> Pathway:
    """Main router - classifies intent and routes to appropriate pathway.
    
    This is the entry point for all user messages.
    """
    return Pathway(
        id="host.router",
        name="Intent Router",
        description="Classify intent and route to appropriate handler",
        nodes={
            # Step 1: Classify intent
            "classify": LLMNode(
                id="classify",
                prompt=INTENT_CLASSIFIER_PROMPT,
                model="routing",
                temperature=0.0,
                max_tokens=20,
            ),
            # Step 2: Normalize intent
            "normalize": TransformNode(
                id="normalize",
                expr='classify.strip().lower().split()[0] if classify else "chat"',
            ),
            # Step 3: Route based on intent
            "router": RouterNode(
                id="router",
                condition="normalize",
                routes={
                    "chat": "chat_handler",
                    "code": "code_handler",
                    "research": "research_handler",
                    "files": "files_handler",
                    "agent": "complex_handler",  # Agent tasks use complex
                    "complex": "complex_handler",
                },
                default="chat_handler",  # Default to chat (safe)
            ),
            # Intent handlers - these invoke sub-pathways
            "chat_handler": LLMNode(
                id="chat_handler",
                prompt="{{message}}",
                system=CHAT_SYSTEM,
                model="chat",
                temperature=0.7,
            ),
            "code_handler": AgentLoopNode(
                id="code_handler",
                goal="{{message}}\n\nComplete the coding task. Say DONE when finished.",
                system=CODE_SYSTEM,
                tools=["code.*", "workspace.*"],
                model="code",
                reasoning_mode="react",
                max_steps=8,
            ),
            "research_handler": AgentLoopNode(
                id="research_handler",
                goal="{{message}}\n\nResearch this topic. Say DONE when finished.",
                system=RESEARCH_SYSTEM,
                tools=["web.*", "search.*", "llm.generate"],
                model="balanced",
                reasoning_mode="react",
                max_steps=6,
            ),
            "files_handler": AgentLoopNode(
                id="files_handler",
                goal="{{message}}\n\nComplete the file task. Say DONE when finished.",
                system=FILES_SYSTEM,
                tools=["workspace.*"],
                model="balanced",
                reasoning_mode="react",
                max_steps=6,
            ),
            "complex_handler": AgentLoopNode(
                id="complex_handler",
                goal="{{message}}\n\nPlan and execute this task. Say DONE when finished.",
                system=COMPLEX_SYSTEM,
                tools=["workspace.*", "code.*", "web.*", "search.*", "llm.*", "agent.*"],
                model="reasoning",
                reasoning_mode="plan_execute",
                max_steps=12,
            ),
            # Final result transform
            "result": TransformNode(
                id="result",
                expr="""{
                    "response": (
                        chat_handler if normalize == "chat" else
                        code_handler.get("response", "") if normalize == "code" else
                        research_handler.get("response", "") if normalize == "research" else
                        files_handler.get("response", "") if normalize == "files" else
                        complex_handler.get("response", "")
                    ),
                    "completed": True,
                    "intent": normalize
                }""",
            ),
        },
        connections=[
            Connection(from_node="classify", to_node="normalize"),
            Connection(from_node="normalize", to_node="router"),
            # Router outputs to handlers (handled by RouterNode)
            Connection(from_node="chat_handler", to_node="result"),
            Connection(from_node="code_handler", to_node="result"),
            Connection(from_node="research_handler", to_node="result"),
            Connection(from_node="files_handler", to_node="result"),
            Connection(from_node="complex_handler", to_node="result"),
        ],
    )


# =============================================================================
# REGISTRATION
# =============================================================================

INTENT_PATHWAY_BUILDERS = {
    "host.router": build_router_pathway,
    "host.classify": build_intent_classifier_pathway,
    "host.chat": build_chat_pathway,
    "host.code": build_code_pathway,
    "host.research": build_research_pathway,
    "host.files": build_files_pathway,
    "host.complex": build_complex_pathway,
}


def register_intent_pathways(pathway_service: "PathwayService") -> None:
    """Register all intent-based pathways."""
    for pathway_id, builder in INTENT_PATHWAY_BUILDERS.items():
        pathway_service.deploy(
            builder,
            pathway_id=pathway_id,
            source="builtin:intent",
            version="1",
        )


__all__ = [
    "INTENT_PATHWAY_BUILDERS",
    "register_intent_pathways",
    "build_router_pathway",
]
