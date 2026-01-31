"""Agent Loop Node - Multi-strategy agentic execution with bounds.

Supports multiple reasoning patterns from OSS agent research:
- ReAct: Reason-Act-Observe loop (default, most battle-tested)
- Plan-Execute: Plan all steps upfront, then execute (better for complex tasks)
- Reflexion: Self-critique and retry on failures (better accuracy)

Inspired by:
- LangGraph Plan-and-Execute: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/plan-and-execute/plan-and-execute.ipynb
- Reflexion: https://github.com/langchain-ai/langgraph/blob/main/docs/docs/tutorials/reflexion/reflexion.ipynb
- 500 AI Agents Projects: https://github.com/ashishpatel26/500-AI-Agents-Projects

Key features:
- Tool boundaries (only specified tools available)
- Cost control (max_steps limits iterations)
- Observability (each step is logged with full state)
- Configurable reasoning strategies
- Self-reflection for quality improvement
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Literal

import re
from pydantic import Field

from pathway_engine.domain.nodes.base import NodeBase
from pathway_engine.domain.nodes.tool_calling import (
    get_tool_schemas_for_names,
    _openai_name_to_tool_name,
)
from pathway_engine.domain.context import Context

logger = logging.getLogger(__name__)


# =============================================================================
# AGENT STATE - Internal state management
# =============================================================================

@dataclass
class AgentState:
    """Internal state for the agent loop.
    
    This tracks everything the agent knows and has done,
    enabling reflection, replanning, and resumption.
    """
    # Goal and context
    goal: str = ""
    inputs: dict = field(default_factory=dict)
    
    # Plan (for plan_execute mode)
    plan: list[str] = field(default_factory=list)
    current_plan_step: int = 0
    plan_complete: bool = False
    
    # Execution history
    steps: list[dict] = field(default_factory=list)
    tool_calls: list[dict] = field(default_factory=list)
    
    # Working memory / scratchpad
    scratchpad: dict = field(default_factory=dict)
    
    # Reflection history (for reflexion mode)
    reflections: list[dict] = field(default_factory=list)
    retry_count: int = 0
    
    # Completion
    completed: bool = False
    final_response: str = ""
    
    def to_dict(self) -> dict:
        """Serialize state for logging/persistence."""
        return {
            "goal": self.goal,
            "plan": self.plan,
            "current_plan_step": self.current_plan_step,
            "steps_taken": len(self.steps),
            "tool_calls_made": len(self.tool_calls),
            "scratchpad_keys": list(self.scratchpad.keys()),
            "reflections_count": len(self.reflections),
            "completed": self.completed,
        }


# =============================================================================
# SYSTEM PROMPTS - Strategy-specific prompts
# =============================================================================

REACT_SYSTEM = """You are an AI agent working toward a goal. You MUST USE TOOLS to accomplish tasks.

## Your Process (ReAct)
1. **Reason**: Analyze what needs to be done
2. **Act**: CALL A TOOL IMMEDIATELY - Don't describe, execute
3. **Observe**: Review the result
4. Repeat until goal is achieved

## CRITICAL RULES - YOU MUST FOLLOW THESE

**MANDATORY**: When asked to CREATE, BUILD, DO, MAKE, RUN, EXECUTE, USE, CALL, INVOKE, SEARCH, GET, SET:
- CALL THE TOOL NOW - Don't describe what you would do
- USE pathway.create if asked to create a pathway
- USE web.search if asked to search
- USE skill.invoke if asked to use a skill
- USE agent.spawn if asked to create an agent
- EXECUTE IMMEDIATELY - Action > Words

**When tools are available:**
- You MUST use them for actions - Don't just describe
- Tool calls are REQUIRED for CREATE/BUILD/DO requests
- Text responses are ONLY for simple questions or final summaries

**Completion**
When done, include "{stop_phrases}" in your response with your final answer."""

PLAN_EXECUTE_SYSTEM = """You are an AI agent that plans before acting.

## Your Process (Plan-Execute)
1. **Plan**: First, create a step-by-step plan to achieve the goal
2. **Execute**: Then execute each step using tools
3. **Verify**: Confirm each step succeeded before moving on
4. **Replan**: If stuck, revise your plan

## Current Plan
{plan}

## Current Step
{current_step}

## Important Rules
- Follow the plan unless it needs revision
- Mark each step complete before moving on
- If a step fails, consider replanning

## Completion
When all steps are done, include "DONE" with your final answer."""

REFLEXION_SYSTEM = """You are an AI agent that reflects on and improves its work.

## Your Process (Reflexion)
1. **Act**: Attempt to achieve the goal
2. **Reflect**: Critically evaluate your output
3. **Improve**: If quality is low, try again with lessons learned

## Previous Attempts
{reflections}

## Lessons Learned
{lessons}

## Important Rules
- After each action, evaluate: "Did this achieve the goal well?"
- If not satisfied, explain why and try a better approach
- Learn from previous failures

## Completion
When satisfied with quality, include "DONE" with your final answer."""


PLANNING_PROMPT = """Create a step-by-step plan to achieve this goal:

## Goal
{goal}

## Available Tools
{tools}

## Context
{context}

## Instructions
Create a clear, actionable plan with 3-7 steps. Each step should be:
- Specific and achievable with the available tools
- Building toward the final goal
- Verifiable (we can tell if it succeeded)

Output your plan as a numbered list:
1. First step...
2. Second step...
etc.

Only output the plan, nothing else."""


REFLECTION_PROMPT = """Evaluate your recent work and decide if it achieves the goal:

## Goal
{goal}

## Your Action
{action}

## Result
{result}

## Questions to Consider
1. Does this fully achieve the goal?
2. Is the quality good enough?
3. What could be improved?

## Response Format
EVALUATION: [PASS/FAIL/PARTIAL]
REASONING: [Why you gave this evaluation]
IMPROVEMENTS: [What to do differently if trying again]"""


# =============================================================================
# AGENT LOOP NODE
# =============================================================================

class AgentLoopNode(NodeBase):
    """Enhanced agentic loop with multiple reasoning strategies.
    
    Reasoning Modes:
        - react: (default) Reason-Act-Observe loop - fast, good for simple tasks
        - plan_execute: Plan first, then execute - better for complex multi-step tasks
        - reflexion: Self-critique and retry - better for tasks requiring accuracy

    Attributes:
        goal: What the agent should accomplish (template string)
        tools: Tool patterns available (e.g. ["search.*", "workspace.read_file"])
        reasoning_mode: Strategy to use ("react", "plan_execute", "reflexion")
        max_steps: Maximum iterations (cost control)
        model: LLM to use for main reasoning
        reflection_model: Optional different model for reflection (can be cheaper/faster)
        images: Optional list of base64 images for vision (template or list)
        
    Example:
        # Simple ReAct agent
        AgentLoopNode(
            goal="Research {{topic}} and summarize",
            tools=["web.search"],
            reasoning_mode="react",
            max_steps=5,
        )
        
        # Plan-Execute for complex tasks
        AgentLoopNode(
            goal="Build a pathway that {{description}}",
            tools=["pathway.create", "pathway.list"],
            reasoning_mode="plan_execute",
            max_steps=10,
        )
        
        # Reflexion for quality-sensitive tasks
        AgentLoopNode(
            goal="Write a {{type}} about {{topic}}",
            tools=["workspace.write_file"],
            reasoning_mode="reflexion",
            reflect_after_steps=1,
            max_retries=2,
        )
    """

    type: Literal["agent_loop"] = "agent_loop"
    
    # Core settings
    goal: str = ""
    tools: list[str] = Field(default_factory=list)
    max_steps: int = 5
    model: str = "auto"  # "auto" uses capability routing for tool_calling
    temperature: float = 0.7
    system: str | None = None
    images: str | list[str] | None = None  # Vision: base64 images or template
    
    # Reasoning strategy
    reasoning_mode: Literal["react", "plan_execute", "reflexion"] = "react"
    
    # Plan-Execute settings
    max_plan_steps: int = 7
    replan_on_stuck: bool = True
    
    # Reflexion settings  
    reflect_after_steps: int = 1  # Reflect after N steps (0 = only at end)
    max_retries: int = 2  # Max retry attempts after reflection
    reflection_model: str | None = None  # Separate model for reflection (can be cheaper)
    quality_threshold: float = 0.7  # Minimum quality to accept (0-1, used in prompt)
    
    # Completion
    on_stuck: Literal["summarize", "error", "return_partial"] = "summarize"
    stop_phrases: list[str] = Field(
        default_factory=lambda: ["DONE", "COMPLETE", "FINISHED"]
    )

    async def compute(self, inputs: dict[str, Any], ctx: Context) -> dict[str, Any]:
        """Run the agentic loop with selected reasoning strategy."""
        # Initialize state
        state = AgentState(
            goal=self._format_template(self.goal, inputs),
            inputs=inputs,
        )

        # Resolve images for vision (can be template or literal list)
        resolved_images: list[str] | None = None
        if self.images is not None:
            if isinstance(self.images, str) and "{{" in self.images:
                raw = self._resolve_path(inputs, self.images.strip("{}"))
                if isinstance(raw, list):
                    resolved_images = [str(img) for img in raw if img]
                elif isinstance(raw, str) and raw:
                    resolved_images = [raw]
            elif isinstance(self.images, list):
                resolved_images = [str(img) for img in self.images if img]
            elif isinstance(self.images, str) and self.images:
                resolved_images = [self.images]
        
        # Store resolved images in state for LLM calls
        state.scratchpad["_images"] = resolved_images

        # Get LLM handler
        llm_generate = ctx.tools.get("llm.generate")
        if not llm_generate:
            raise RuntimeError("llm.generate tool not available")

        # Get tool schemas
        tool_schemas = get_tool_schemas_for_names(self.tools, ctx)
        
        # Dispatch to reasoning strategy
        if self.reasoning_mode == "plan_execute":
            await self._run_plan_execute(state, llm_generate, tool_schemas, ctx)
        elif self.reasoning_mode == "reflexion":
            await self._run_reflexion(state, llm_generate, tool_schemas, ctx)
        else:  # react (default)
            await self._run_react(state, llm_generate, tool_schemas, ctx)
        
        # Build output
        return {
            "response": state.final_response,
            "completed": state.completed,
            "steps_taken": len(state.steps),
            "max_steps": self.max_steps,
            "step_results": state.steps,
            "goal": state.goal,
            "plan": state.plan if self.reasoning_mode == "plan_execute" else None,
            "reflections": state.reflections if self.reasoning_mode == "reflexion" else None,
            "scratchpad": state.scratchpad,
        }

    # =========================================================================
    # REACT STRATEGY - Reason-Act-Observe loop
    # =========================================================================
    
    async def _run_react(
        self,
        state: AgentState,
        llm_generate,
        tool_schemas: list[dict],
        ctx: Context,
    ) -> None:
        """Run ReAct reasoning loop."""
        stop_phrases_str = ", ".join(f'"{p}"' for p in self.stop_phrases)
        system = self.system or REACT_SYSTEM.format(stop_phrases=stop_phrases_str)
        
        history: list[dict[str, Any]] = []

        # Initial prompt - user-facing, not internal
        initial_prompt = f"""{state.goal}

## Instructions
Help the user by taking action immediately.
- If asked to CREATE/BUILD/DO something → USE THE APPROPRIATE TOOL NOW
- Don't describe what you would do - DO IT
- When complete, provide a clear response TO THE USER and say "DONE"

Remember: You're talking TO the user, not about yourself. Respond naturally."""

        history.append({"role": "user", "content": initial_prompt})

        # Get images from scratchpad (only pass on first call)
        images = state.scratchpad.get("_images")
        
        # Main loop
        for step_num in range(self.max_steps):
            logger.info(f"[AgentLoop:ReAct] Step {step_num + 1}/{self.max_steps}")
            
            # Pass images only on first call
            call_images = images if step_num == 0 else None
            
            result = await self._llm_call(
                llm_generate, history, system, tool_schemas, ctx, images=call_images
            )

            response_text = result.get("content", "") or result.get("response", "")
            tool_calls = result.get("tool_calls") or []

            step_result = {
                "step": step_num + 1,
                "mode": "react",
                "response": response_text,
                "tool_calls": tool_calls,
                "tool_results": [],
            }

            # Check completion
            if self._check_completion(response_text):
                logger.info("[AgentLoop:ReAct] Completion detected")
                # Extract actual response - prefer content before DONE, or use full conversation
                state.final_response = self._extract_final_response(response_text, state.steps)
                state.completed = True
                state.steps.append(step_result)
                return
            
            # No tool calls - STRONGLY prompt to use tools
            if not tool_calls:
                logger.info("[AgentLoop:ReAct] No tool calls, prompting tool use")
                state.steps.append(step_result)
                history.append({"role": "assistant", "content": response_text})
                
                # Check if this is an action request
                action_verbs = ["create", "build", "do", "make", "run", "execute", "use", "call", "invoke", "search", "get", "set"]
                is_action_request = any(verb in state.goal.lower() for verb in action_verbs)
                
                if is_action_request:
                    history.append({
                        "role": "user",
                        "content": "You MUST use a tool to accomplish this. The goal requires action - call a tool now. Don't describe - execute.",
                    })
                else:
                    history.append({
                        "role": "user",
                        "content": "Continue toward the goal. Use a tool if needed, or say 'DONE' if complete.",
                    })
                continue

            # Execute tools
            tool_results = await self._execute_tools(tool_calls, ctx)
            step_result["tool_results"] = tool_results
            state.steps.append(step_result)
            state.tool_calls.extend(tool_results)
            
            # Update history
            history.append({"role": "assistant", "content": response_text or "Using tools..."})
            results_text = self._format_tool_results(tool_results)
            history.append({
                "role": "user", 
                "content": f"Tool results:\n{results_text}\n\nContinue helping the user or say 'DONE' with your response to them.",
            })
        
        # Max steps reached
        await self._handle_stuck(state, llm_generate, ctx)

    # =========================================================================
    # PLAN-EXECUTE STRATEGY - Plan first, then execute
    # =========================================================================
    
    async def _run_plan_execute(
        self,
        state: AgentState,
        llm_generate,
        tool_schemas: list[dict],
        ctx: Context,
    ) -> None:
        """Run Plan-Execute reasoning loop."""
        logger.info("[AgentLoop:PlanExecute] Starting planning phase")
        
        # Phase 1: Create plan
        tools_desc = "\n".join(f"- {t['function']['name']}: {t['function'].get('description', '')}" 
                               for t in tool_schemas) if tool_schemas else "No tools available"
        
        plan_result = await llm_generate({
            "prompt": PLANNING_PROMPT.format(
                goal=state.goal,
                tools=tools_desc,
                context=json.dumps(state.inputs, indent=2, default=str),
            ),
            "model": self.model,
            "temperature": 0.3,  # Lower temp for planning
        }, ctx)
        
        plan_text = plan_result.get("content", "") or plan_result.get("response", "")
        state.plan = self._parse_plan(plan_text)
        
        logger.info(f"[AgentLoop:PlanExecute] Created plan with {len(state.plan)} steps")
        
        state.steps.append({
            "step": 0,
            "mode": "plan",
            "response": plan_text,
            "plan": state.plan,
        })
        
        # Phase 2: Execute each step
        history: list[dict[str, Any]] = []
        
        for plan_idx, plan_step in enumerate(state.plan):
            if len(state.steps) >= self.max_steps:
                break
                
            state.current_plan_step = plan_idx
            logger.info(f"[AgentLoop:PlanExecute] Executing step {plan_idx + 1}: {plan_step[:50]}...")
            
            system = PLAN_EXECUTE_SYSTEM.format(
                plan="\n".join(f"{i+1}. {s}" for i, s in enumerate(state.plan)),
                current_step=f"Step {plan_idx + 1}: {plan_step}",
            )
            
            exec_prompt = f"""Execute this step of the plan:

## Current Step
{plan_idx + 1}. {plan_step}

## Goal
{state.goal}

## Previous Results
{json.dumps(state.scratchpad, indent=2, default=str) if state.scratchpad else "None yet"}

Use tools to complete this step, then confirm it's done."""

            history.append({"role": "user", "content": exec_prompt})
            
            # Get images from scratchpad
            images = state.scratchpad.get("_images")
            
            # Execute step (mini react loop)
            for sub_step in range(3):  # Max 3 tool calls per plan step
                # Pass images only on first sub_step of first plan step
                call_images = images if plan_idx == 0 and sub_step == 0 else None
                
                result = await self._llm_call(
                    llm_generate, history, system, tool_schemas, ctx, images=call_images
                )
                
                response_text = result.get("content", "") or result.get("response", "")
                tool_calls = result.get("tool_calls") or []
                
                step_result = {
                    "step": len(state.steps) + 1,
                    "mode": "execute",
                    "plan_step": plan_idx + 1,
                    "response": response_text,
                    "tool_calls": tool_calls,
                    "tool_results": [],
                }
                
                if not tool_calls:
                    # Step complete, save to scratchpad
                    state.scratchpad[f"step_{plan_idx + 1}"] = response_text
                    state.steps.append(step_result)
                    break
                
                # Execute tools
                tool_results = await self._execute_tools(tool_calls, ctx)
                step_result["tool_results"] = tool_results
                state.steps.append(step_result)
                state.tool_calls.extend(tool_results)
                
                history.append({"role": "assistant", "content": response_text or "Using tools..."})
                results_text = self._format_tool_results(tool_results)
                history.append({
                    "role": "user",
                    "content": f"## Tool Results\n{results_text}\n\nContinue with this step or confirm done.",
                })
            
            history.clear()  # Fresh context for next plan step
        
        # Final synthesis
        state.plan_complete = True
        synthesis_result = await llm_generate({
            "prompt": f"""All plan steps are complete. Synthesize the final result.

## Goal
{state.goal}

## Plan Results
{json.dumps(state.scratchpad, indent=2, default=str)}

Provide a comprehensive final answer. Say "DONE" when finished.""",
            "model": self.model,
            "temperature": 0.4,
        }, ctx)
        
        state.final_response = synthesis_result.get("content", "") or synthesis_result.get("response", "")
        state.completed = True

    # =========================================================================
    # REFLEXION STRATEGY - Self-critique and retry
    # =========================================================================
    
    async def _run_reflexion(
        self,
        state: AgentState,
        llm_generate,
        tool_schemas: list[dict],
        ctx: Context,
    ) -> None:
        """Run Reflexion reasoning loop with self-critique."""
        
        for attempt in range(self.max_retries + 1):
            logger.info(f"[AgentLoop:Reflexion] Attempt {attempt + 1}/{self.max_retries + 1}")
            
            # Build context with previous reflections
            lessons = "\n".join(
                f"- {r.get('improvements', 'None')}" 
                for r in state.reflections
            ) if state.reflections else "None yet"
            
            system = REFLEXION_SYSTEM.format(
                reflections=json.dumps(state.reflections[-3:], indent=2) if state.reflections else "None",
                lessons=lessons,
            )
            
            # Run a react-style execution
            history: list[dict[str, Any]] = []
            initial_prompt = f"""## Goal
{state.goal}

## Context
{json.dumps(state.inputs, indent=2, default=str)}

{"## Previous Failures - Learn from these:" + chr(10) + lessons if lessons != "None yet" else ""}

Execute the goal, applying lessons from any previous attempts."""

            history.append({"role": "user", "content": initial_prompt})
            
            attempt_response = ""
            
            # Get images from scratchpad
            images = state.scratchpad.get("_images")
            
            # Mini execution loop
            for step_num in range(max(3, self.max_steps // (self.max_retries + 1))):
                # Pass images only on first step of first attempt
                call_images = images if attempt == 0 and step_num == 0 else None
                
                result = await self._llm_call(
                    llm_generate, history, system, tool_schemas, ctx, images=call_images
                )
                
                response_text = result.get("content", "") or result.get("response", "")
                tool_calls = result.get("tool_calls") or []
                attempt_response = response_text
                
                step_result = {
                    "step": len(state.steps) + 1,
                    "mode": "reflexion",
                    "attempt": attempt + 1,
                    "response": response_text,
                    "tool_calls": tool_calls,
                    "tool_results": [],
                }
                
                if self._check_completion(response_text) or not tool_calls:
                    state.steps.append(step_result)
                    break
                
                # Execute tools
                tool_results = await self._execute_tools(tool_calls, ctx)
                step_result["tool_results"] = tool_results
                state.steps.append(step_result)
                state.tool_calls.extend(tool_results)
                
                history.append({"role": "assistant", "content": response_text or "Using tools..."})
                results_text = self._format_tool_results(tool_results)
                history.append({
                    "role": "user",
                    "content": f"## Tool Results\n{results_text}\n\nContinue or say 'DONE'.",
                })
            
            # Reflect on the attempt
            reflection = await self._reflect(
                state, attempt_response, llm_generate, ctx
            )
            state.reflections.append(reflection)
            
            if reflection.get("evaluation") == "PASS":
                logger.info("[AgentLoop:Reflexion] Reflection passed, completing")
                state.final_response = attempt_response
                state.completed = True
                return
            
            logger.info(f"[AgentLoop:Reflexion] Reflection: {reflection.get('evaluation')} - retrying")
            state.retry_count += 1
        
        # Max retries reached, use best attempt
        state.final_response = attempt_response
        state.completed = False
        await self._handle_stuck(state, llm_generate, ctx)

    async def _reflect(
        self,
        state: AgentState,
        response: str,
        llm_generate,
        ctx: Context,
    ) -> dict:
        """Run reflection on the agent's output."""
        model = self.reflection_model or self.model
        
        result = await llm_generate({
            "prompt": REFLECTION_PROMPT.format(
                goal=state.goal,
                action=f"Attempt {state.retry_count + 1}",
                result=response[:1000],  # Truncate for reflection
            ),
            "model": model,
            "temperature": 0.2,  # Low temp for evaluation
        }, ctx)
        
        reflection_text = result.get("content", "") or result.get("response", "")
        
        # Parse reflection
        evaluation = "FAIL"
        if "PASS" in reflection_text.upper():
            evaluation = "PASS"
        elif "PARTIAL" in reflection_text.upper():
            evaluation = "PARTIAL"
        
        return {
            "attempt": state.retry_count + 1,
            "evaluation": evaluation,
            "text": reflection_text,
            "improvements": self._extract_improvements(reflection_text),
        }

    def _extract_improvements(self, text: str) -> str:
        """Extract improvement suggestions from reflection."""
        if "IMPROVEMENTS:" in text.upper():
            parts = text.upper().split("IMPROVEMENTS:")
            if len(parts) > 1:
                return parts[1].strip()[:200]
        return ""

    # =========================================================================
    # SHARED HELPERS
    # =========================================================================
    
    async def _llm_call(
        self,
        llm_generate,
        history: list[dict],
        system: str,
        tool_schemas: list[dict],
        ctx: Context,
        images: list[str] | None = None,
    ) -> dict:
        """Make an LLM call with tools and optional images."""
        # If tools are available and this is an action request, prefer tool use
        # Check if the last message contains action verbs
        last_message = history[-1]["content"] if history else ""
        action_verbs = ["create", "build", "do", "make", "run", "execute", "use", "call", "invoke", "search", "get", "set"]
        prefers_tool = any(verb in last_message.lower() for verb in action_verbs) if tool_schemas else False
        
        request = {
            "prompt": last_message,
            "messages": history[:-1] if len(history) > 1 else None,
            "model": self.model,
            "system": system,
            "tools": tool_schemas if tool_schemas else None,
            # Use auto - let the improved prompts guide tool use
            "tool_choice": "auto" if tool_schemas else None,
            "temperature": self.temperature,
        }
        
        # Add images for vision models
        if images:
            request["images"] = images
        
        return await llm_generate(request, ctx)

    async def _execute_tools(
        self,
        tool_calls: list[dict],
        ctx: Context,
    ) -> list[dict]:
        """Execute a list of tool calls."""
        results = []
        for tc in tool_calls:
            tool_name = "unknown"
            try:
                if isinstance(tc, dict):
                    func = tc.get("function", tc)
                    tool_name = _openai_name_to_tool_name(func.get("name", ""))
                    args = func.get("arguments", {})
                    if isinstance(args, str):
                        args = json.loads(args)
                else:
                    continue

                handler = ctx.tools.get(tool_name)
                if handler:
                    logger.info(f"[AgentLoop] Executing: {tool_name}")
                    output = await handler(args, ctx)
                    results.append({
                        "tool": tool_name,
                        "args": args,
                        "success": True,
                        "output": output,
                    })
                else:
                    results.append({
                        "tool": tool_name,
                        "args": args,
                        "success": False,
                        "error": f"Tool not found: {tool_name}",
                    })

            except Exception as e:
                logger.error(f"[AgentLoop] Tool failed: {e}")
                results.append({
                    "tool": tool_name,
                    "success": False,
                    "error": str(e),
                })
        return results

    def _format_tool_results(self, results: list[dict]) -> str:
        """Format tool results for the LLM."""
        lines = []
        for r in results:
            if r.get("success"):
                output_str = json.dumps(r["output"], default=str)[:500]
                lines.append(f"✓ {r['tool']}: {output_str}")
            else:
                lines.append(f"✗ {r['tool']}: {r.get('error', 'Failed')}")
        return "\n".join(lines)

    def _parse_plan(self, text: str) -> list[str]:
        """Parse numbered plan from LLM output."""
        import re
        lines = text.strip().split("\n")
        plan = []
        for line in lines:
            # Match numbered items: "1. Step" or "1) Step"
            match = re.match(r"^\d+[\.\)]\s*(.+)$", line.strip())
            if match:
                plan.append(match.group(1).strip())
        return plan[:self.max_plan_steps]

    def _check_completion(self, text: str) -> bool:
        """Check if response contains completion signal."""
        if not text:
            return False
        # Completion should be an explicit sentinel, not incidental language.
        # We treat a completion phrase as present when it begins a line, e.g.:
        #   "DONE"
        #   "DONE 42"
        # This avoids false positives like "Not done yet."
        for phrase in self.stop_phrases:
            p = (phrase or "").strip()
            if not p:
                continue
            pattern = rf"(?m)^\s*{re.escape(p)}\b"
            if re.search(pattern, text):
                return True
        return False

    def _extract_final_response(self, current_text: str, steps: list[dict]) -> str:
        """Extract the actual answer from the agent's responses.
        
        When agent says "DONE", we need to find the actual answer which might be:
        1. In the same response, before "DONE" 
        2. In a previous step's response
        
        Always strips the DONE marker and internal reasoning artifacts from the final response.
        """
        def strip_done(text: str) -> str:
            """Remove DONE and similar markers from text."""
            result = text
            for phrase in self.stop_phrases:
                p = (phrase or "").strip()
                if not p:
                    continue
                # Remove DONE at end of text or on its own line
                result = re.sub(rf"\s*{re.escape(p)}\.?\s*$", "", result, flags=re.IGNORECASE)
                result = re.sub(rf"(?m)^\s*{re.escape(p)}\.?\s*$", "", result)
            return result.strip()
        
        def remove_internal_reasoning(text: str) -> str:
            """Remove internal reasoning artifacts that shouldn't be shown to users."""
            # Remove common internal reasoning patterns
            patterns = [
                r"(?i)^\s*Summary:\s*",
                r"(?i)^\s*Accomplishments:\s*",
                r"(?i)^\s*Remaining Tasks?:\s*",
                r"(?i)^\s*Next Steps?:\s*",
                r"(?i)^\s*Status:\s*",
                r"(?i)^\s*What remains:\s*",
                r"(?i)^\s*The goal is to\s*",
                r"(?i)^\s*I have understood\s*",
                r"(?i)^\s*I will\s*",
            ]
            result = text
            for pattern in patterns:
                result = re.sub(pattern, "", result, flags=re.MULTILINE)
            
            # Remove bullet points that are internal planning
            lines = result.split('\n')
            filtered_lines = []
            skip_next = False
            for i, line in enumerate(lines):
                # Skip lines that look like internal planning
                if re.match(r'^\s*[-*•]\s*(Develop|Implement|Create|Design|Research|Explore|Begin|Select|Choose|Mark)', line, re.IGNORECASE):
                    skip_next = True
                    continue
                if skip_next and line.strip() == "":
                    skip_next = False
                    continue
                skip_next = False
                filtered_lines.append(line)
            
            return '\n'.join(filtered_lines).strip()
        
        # Clean the current response
        cleaned = strip_done(current_text)
        cleaned = remove_internal_reasoning(cleaned)
        
        # If there's substantial content, return it
        if cleaned and len(cleaned) > 5:
            return cleaned
        
        # If current response is just "DONE" or similar, look at previous steps
        for step in reversed(steps):
            prev_response = step.get("response", "")
            if prev_response:
                cleaned_prev = strip_done(prev_response)
                cleaned_prev = remove_internal_reasoning(cleaned_prev)
                if cleaned_prev and len(cleaned_prev) > 10:
                    return cleaned_prev
        
        # Fallback to original (shouldn't happen)
        return remove_internal_reasoning(current_text)

    async def _handle_stuck(
        self,
        state: AgentState,
        llm_generate,
        ctx: Context,
    ) -> None:
        """Handle when agent reaches max steps without completing."""
        logger.warning(f"[AgentLoop] Max steps reached, on_stuck={self.on_stuck}")
        
        if self.on_stuck == "error":
            raise RuntimeError(f"Agent reached max steps ({self.max_steps}) without completing")
        
        elif self.on_stuck == "summarize":
            # Build a summary of what actually happened
            tool_summary = []
            for step in state.steps:
                tool_calls = step.get("tool_calls", [])
                tool_results = step.get("tool_results", [])
                if tool_calls:
                    for tc in tool_calls:
                        func = tc.get("function", tc)
                        tool_name = func.get("name", "unknown")
                        tool_summary.append(f"- Called {tool_name}")
                if tool_results:
                    for tr in tool_results:
                        if tr.get("success"):
                            tool_summary.append(f"  ✓ {tr.get('tool', 'unknown')}: succeeded")
                        else:
                            tool_summary.append(f"  ✗ {tr.get('tool', 'unknown')}: {tr.get('error', 'failed')}")
            
            tool_summary_text = "\n".join(tool_summary[:20]) if tool_summary else "No tools were called."
            
            summary_result = await llm_generate({
                "prompt": f"""You reached the maximum number of steps ({self.max_steps}) before completing the goal. Provide a clear summary of what was accomplished.

## Goal
{state.goal}

## Execution Summary
- Total steps executed: {len(state.steps)}/{self.max_steps}
- Tool calls made: {len(state.tool_calls)}
- Plan: {state.plan if state.plan else "No plan was created"}

## Tools Used
{tool_summary_text}

## Instructions
Provide a concise summary that:
1. States what was actually accomplished (be specific about tool results)
2. Explains what remains to be done
3. Acknowledges this is a partial result due to step limit

Be factual and specific - only mention what actually happened based on the tool calls above.""",
                "model": self.model,
                "temperature": 0.2,  # Lower temp for more factual summaries
            }, ctx)
            state.final_response = summary_result.get("content", "") or summary_result.get("response", "")
        
        else:  # return_partial
            state.final_response = state.steps[-1]["response"] if state.steps else "No progress"


__all__ = ["AgentLoopNode", "AgentState"]
