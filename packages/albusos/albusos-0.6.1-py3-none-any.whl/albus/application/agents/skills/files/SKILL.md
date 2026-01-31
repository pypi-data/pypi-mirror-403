---
name: files
description: Read files, write files, list directories, manage workspace. Use for any file or folder operations.
id: files
pathway_module: albus.application.agents.skills.files.pathway
pathway_function: build_files_pathway
inputs:
  message: string - What file operation to perform
outputs:
  response: string - Result of file operation
---

# Files Skill

Workspace file operations. Uses AgentLoopNode with workspace.* tools.

Use this skill for:
- Reading files
- Writing files
- Listing directories
- File management

Tools available:
- workspace.* - All workspace operations
