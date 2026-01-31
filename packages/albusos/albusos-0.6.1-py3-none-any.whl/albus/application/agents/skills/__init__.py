"""Host Skills - Canonical SKILL.md format.

All Host skills are defined using SKILL.md files (canonical format).
This replaces the old host_skills.py approach.

Skills are loaded from:
1. Built-in: src/albus/application/agents/skills/
2. External: ALBUS_SKILL_DIRS environment variable

All skills use the same SKILL.md format, making them:
- Version control friendly
- Easy to share
- Compatible with Agent Skills ecosystem
"""

from __future__ import annotations

import os
from pathlib import Path

from pathway_engine.infrastructure.skill_loader import load_skills_from_directory


async def load_all_host_skills() -> list:
    """Load all Host skills (built-in + external).
    
    Returns:
        List of Skill objects
    """
    import logging
    from pathway_engine.domain.agent.skill import Skill
    
    logger = logging.getLogger(__name__)
    all_skills: list[Skill] = []
    
    # Load built-in skills from this directory (skills/)
    # __file__ is __init__.py, parent is skills/ directory
    builtin_dir = Path(__file__).parent
    if builtin_dir.exists():
        try:
            builtin_skills = await load_skills_from_directory(builtin_dir, recursive=False)
            all_skills.extend(builtin_skills)
            logger.info(f"Loaded {len(builtin_skills)} built-in skills from {builtin_dir}")
        except Exception as e:
            logger.warning(f"Failed to load built-in skills: {e}", exc_info=True)
    
    # Load external skills from ALBUS_SKILL_DIRS
    skill_dirs_env = os.getenv("ALBUS_SKILL_DIRS", "")
    if skill_dirs_env:
        for skill_dir_str in skill_dirs_env.split(","):
            skill_dir_str = skill_dir_str.strip()
            if not skill_dir_str:
                continue
            
            skill_dir = Path(skill_dir_str)
            if skill_dir.exists():
                try:
                    external_skills = await load_skills_from_directory(skill_dir, recursive=False)
                    all_skills.extend(external_skills)
                    logger.info(f"Loaded {len(external_skills)} external skills from {skill_dir}")
                except Exception as e:
                    logger.warning(f"Failed to load skills from {skill_dir}: {e}", exc_info=True)
    
    return all_skills


__all__ = ["load_all_host_skills"]
