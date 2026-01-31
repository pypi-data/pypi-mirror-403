"""Skill Loader - Discover and load skills from filesystem directories.

Supports:
- Agent Skills format (agentskills.io): folders with SKILL.md files
- Custom skill directories
- Dynamic skill discovery and registration

Usage:
    from pathway_engine.infrastructure.skill_loader import load_skills_from_directory
    
    skills = await load_skills_from_directory("/path/to/skills")
    for skill in skills:
        agent.add_skill(skill)
"""

from __future__ import annotations

import logging
import os
import re
from pathlib import Path
from typing import Any

from pathway_engine.domain.agent.skill import Skill, skill
from pathway_engine.domain.pathway import Pathway, Connection
from pathway_engine.domain.nodes.core import LLMNode, TransformNode
from pathway_engine.domain.nodes.agent_loop import AgentLoopNode

logger = logging.getLogger(__name__)


def parse_frontmatter(content: str) -> dict[str, Any]:
    """Parse YAML frontmatter from SKILL.md content.
    
    Expected format:
        ---
        name: Skill Name
        description: What this skill does
        ---
        # Skill Instructions
        ...
    """
    frontmatter = {}
    
    # Check for frontmatter delimiter
    if not content.startswith("---"):
        return frontmatter
    
    # Find end of frontmatter
    lines = content.split("\n")
    end_idx = None
    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_idx = i
            break
    
    if end_idx is None:
        return frontmatter
    
    # Parse YAML between delimiters
    yaml_lines = lines[1:end_idx]
    for line in yaml_lines:
        if ":" in line:
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            frontmatter[key] = value
    
    return frontmatter


def extract_skill_instructions(content: str) -> str:
    """Extract skill instructions from SKILL.md (content after frontmatter)."""
    # Remove frontmatter if present
    if content.startswith("---"):
        lines = content.split("\n")
        end_idx = None
        for i, line in enumerate(lines[1:], start=1):
            if line.strip() == "---":
                end_idx = i
                break
        if end_idx is not None:
            content = "\n".join(lines[end_idx + 1:])
    
    return content.strip()


def build_pathway_from_skill(
    skill_id: str,
    skill_name: str,
    instructions: str,
    bundled_resources: dict[str, str] | None = None,
) -> Pathway:
    """Build a Pathway from skill instructions.
    
    For now, creates a simple AgentLoopNode-based pathway that executes
    the skill instructions. In the future, could parse more sophisticated
    pathway definitions from the skill content.
    """
    # Create an agent loop that follows the skill instructions
    agent_node = AgentLoopNode(
        id="agent",
        goal=f"""Follow these skill instructions:

{instructions}

Complete the task. Say DONE when finished.""",
        system=f"""You are executing the skill: {skill_name}

Follow the instructions provided. Use available tools as needed.""",
        tools=["workspace.*", "web.*", "code.*"],  # Common tool patterns
        model="auto",
        reasoning_mode="react",
        max_steps=8,
    )
    
    result_node = TransformNode(
        id="result",
        expr='{"response": agent.get("response", ""), "skill": "' + skill_id + '"}',
    )
    
    return Pathway(
        id=f"skill.{skill_id}",
        name=skill_name,
        description=instructions[:200] + "..." if len(instructions) > 200 else instructions,
        nodes={
            "agent": agent_node,
            "result": result_node,
        },
        connections=[Connection(from_node="agent", to_node="result")],
    )


async def load_skill_from_directory(skill_dir: Path) -> Skill | None:
    """Load a single skill from a directory.
    
    Expected structure:
        skill_dir/
            SKILL.md (required)
            ... (optional bundled resources)
    """
    skill_md_path = skill_dir / "SKILL.md"
    
    if not skill_md_path.exists():
        logger.warning(f"No SKILL.md found in {skill_dir}")
        return None
    
    try:
        content = skill_md_path.read_text(encoding="utf-8")
        frontmatter = parse_frontmatter(content)
        instructions = extract_skill_instructions(content)
        
        # Get skill metadata
        skill_id = frontmatter.get("id") or skill_dir.name
        skill_name = frontmatter.get("name") or skill_dir.name.title()
        description = frontmatter.get("description") or instructions[:100] + "..."
        
        # Parse inputs/outputs if provided
        inputs_schema = {}
        outputs_schema = {}
        
        if "inputs" in frontmatter:
            # Parse inputs schema (could be YAML dict or string)
            inputs_raw = frontmatter["inputs"]
            if isinstance(inputs_raw, dict):
                inputs_schema = inputs_raw
            elif isinstance(inputs_raw, str):
                # Simple parsing: "message: string - The user message"
                for line in inputs_raw.split("\n"):
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip()
                        desc = parts[1].strip() if len(parts) > 1 else ""
                        inputs_schema[key] = desc
        
        if "outputs" in frontmatter:
            outputs_raw = frontmatter["outputs"]
            if isinstance(outputs_raw, dict):
                outputs_schema = outputs_raw
            elif isinstance(outputs_raw, str):
                for line in outputs_raw.split("\n"):
                    if ":" in line:
                        parts = line.split(":", 1)
                        key = parts[0].strip()
                        desc = parts[1].strip() if len(parts) > 1 else ""
                        outputs_schema[key] = desc
        
        # Build pathway builder
        # Check if pathway is defined in a module (for built-in skills)
        pathway_module = frontmatter.get("pathway_module")
        pathway_function = frontmatter.get("pathway_function")
        
        if pathway_module and pathway_function:
            # Load pathway from Python module (built-in skills)
            try:
                import importlib
                module = importlib.import_module(pathway_module)
                pathway_func = getattr(module, pathway_function)
                pathway_builder = pathway_func
            except Exception as e:
                logger.warning(f"Failed to load pathway from {pathway_module}.{pathway_function}: {e}")
                # Fall back to instruction-based pathway
                pathway_builder = lambda: build_pathway_from_skill(
                    skill_id=skill_id,
                    skill_name=skill_name,
                    instructions=instructions,
                )
        else:
            # Build pathway from instructions (external skills)
            pathway_builder = lambda: build_pathway_from_skill(
                skill_id=skill_id,
                skill_name=skill_name,
                instructions=instructions,
            )
        
        # Create skill
        return skill(
            id=skill_id,
            name=skill_name,
            description=description,
            pathway_builder=pathway_builder,
            inputs=inputs_schema or {"message": "string - The task to perform"},
            outputs=outputs_schema or {"response": "string - The result"},
        )
        
    except Exception as e:
        logger.error(f"Failed to load skill from {skill_dir}: {e}", exc_info=True)
        return None


async def load_skills_from_directory(
    skills_dir: str | Path,
    *,
    recursive: bool = True,
) -> list[Skill]:
    """Discover and load all skills from a directory.
    
    Args:
        skills_dir: Path to directory containing skill folders
        recursive: If True, search subdirectories (default: True)
    
    Returns:
        List of loaded Skill objects
    """
    skills_dir = Path(skills_dir)
    
    if not skills_dir.exists():
        logger.warning(f"Skills directory does not exist: {skills_dir}")
        return []
    
    if not skills_dir.is_dir():
        logger.warning(f"Not a directory: {skills_dir}")
        return []
    
    loaded_skills: list[Skill] = []
    
    # Find all directories that might contain skills
    if recursive:
        # Look for any directory with SKILL.md
        for skill_dir in skills_dir.rglob("SKILL.md"):
            skill_dir = skill_dir.parent
            skill = await load_skill_from_directory(skill_dir)
            if skill:
                loaded_skills.append(skill)
    else:
        # Only check immediate subdirectories
        for item in skills_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):  # Skip __pycache__, __init__, etc.
                skill = await load_skill_from_directory(item)
                if skill:
                    loaded_skills.append(skill)
    
    logger.info(f"Loaded {len(loaded_skills)} skills from {skills_dir}")
    return loaded_skills


async def load_agent_skills_from_directories(
    *skill_directories: str | Path,
) -> list[Skill]:
    """Load skills from multiple directories (e.g., agentskills.io format).
    
    Usage:
        skills = await load_agent_skills_from_directories(
            "/path/to/agentskills/skills",
            "/path/to/custom/skills",
        )
    """
    all_skills: list[Skill] = []
    
    for skill_dir in skill_directories:
        skills = await load_skills_from_directory(skill_dir)
        all_skills.extend(skills)
    
    return all_skills


__all__ = [
    "load_skill_from_directory",
    "load_skills_from_directory",
    "load_agent_skills_from_directories",
    "parse_frontmatter",
    "build_pathway_from_skill",
]
