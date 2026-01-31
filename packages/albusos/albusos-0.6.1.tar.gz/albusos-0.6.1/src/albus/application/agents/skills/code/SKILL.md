---
name: code
description: Programming, coding, debugging, writing code, reviewing code. Use for any technical implementation task.
id: code
pathway_module: albus.application.agents.skills.code.pathway
pathway_function: build_code_pathway
inputs:
  message: string - The coding task or question
outputs:
  response: string - Code or explanation
---

# Code Skill

Programming tasks with code tools. Uses AgentLoopNode with code.* and workspace.* tools.

Use this skill for:
- Writing code
- Debugging
- Code review
- Technical implementation

Tools available:
- code.* - Code execution and analysis
- workspace.* - File operations
