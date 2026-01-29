"""AI-powered workflow visualization service."""

import ast
import hashlib
import inspect
import json
import re
from typing import Any, Set

from pydantic import BaseModel

from planar.ai.models import PlanarModelSettings, UserMessage
from planar.ai.pydantic_ai import model_run
from planar.logging import get_logger
from planar.object_registry import ObjectRegistry
from planar.session import get_config, get_session
from planar.workflows.models import WorkflowVisualization
from planar.workflows.visualization_exceptions import (
    WorkflowVisualizationGenerationError,
    WorkflowVisualizationNotConfiguredError,
    WorkflowVisualizationNotFoundError,
    WorkflowVisualizationSourceError,
)
from planar.workflows.visualization_result import WorkflowVisualizationResult
from planar.workflows.visualization_spec import VisualizationGraph, WorkflowMetadata

logger = get_logger(__name__)

VISUALIZATION_PROMPT = """You are a Planar workflow visualization expert. Generate a visualization graph specification.

PLANAR CONCEPTS:
- @workflow(): Main orchestration function
- @step(display_name="..."): Workflow steps - USE display_name for labels
- Agents: AI agents that process data
- @rule(description="..."): Business logic functions
- Human: Human-in-the-loop approval tasks (instantiated with Human class)

NODE TYPES:
- "step": Regular workflow step
- "agent": AI agent call
- "rule": Business rule execution
- "human": Human approval task
- "condition": If/else decision point
- "loop": For/while loop
- "return": End of workflow

OUTPUT FORMAT:
Your output must have a "graph" field containing the visualization graph.

EXAMPLE:
{{
  "graph": {{
    "nodes": [
      {{
        "id": "step1",
        "type": "step",
        "label": "Extract Invoice Data",
        "metadata": {{
          "action_id": "extract_invoice_data",
          "input_type": "PlanarFile",
          "output_type": "ExtractedInvoice"
        }}
      }},
      {{
        "id": "agent1",
        "type": "agent",
        "label": "Invoice Agent",
        "metadata": {{
          "action_id": "invoice_agent",
          "input_type": "PlanarFile",
          "output_type": "InvoiceData"
        }}
      }},
      {{
        "id": "cond1",
        "type": "condition",
        "label": "PO Found?",
        "metadata": {{
          "action_id": "check_po_exists",
          "condition": "po is not None"
        }}
      }}
    ],
    "edges": [
      {{"from_node": "step1", "to_node": "agent1"}},
      {{"from_node": "agent1", "to_node": "cond1"}}
    ]
  }}
}}

INSTRUCTIONS:
- Create a node for each step, agent, rule, or human task
- Add condition nodes for if/else branches
- Use step display_name values from STEP DEFINITIONS section
- Detect agents from AGENT DEFINITIONS section
- Detect humans from HUMAN TASK DEFINITIONS section
- Detect rules (functions decorated with @rule)
- Keep node IDs simple: step1, step2, cond1, etc.
- Label edges for conditional branches (yes/no, true/false)

CRITICAL - ALWAYS populate metadata for each node:
- metadata.action_id: The actual function/variable name (e.g., "extract_invoice_data", "invoice_agent")
- metadata.input_type: Input type from step signature or Agent definition
- metadata.output_type: Output type from step signature or Agent definition
- metadata.condition: For condition nodes, the actual boolean expression
- metadata.description: Brief description if available from docstrings

AGENT METADATA:
When you see agents in AGENT DEFINITIONS, populate agent_metadata:
- metadata.agent_metadata.tools: List of tool names (e.g., ["search_products", "get_product_price"])
- metadata.agent_metadata.max_turns: Maximum conversation turns
- metadata.agent_metadata.agent_type: "single_turn", "multi_turn", or "io_agent"

Example:
{{
  "id": "agent1",
  "type": "agent",
  "label": "Multi-Turn Product Agent",
  "metadata": {{
    "action_id": "multi_turn_agent",
    "agent_metadata": {{
      "tools": ["search_products", "get_product_price"],
      "max_turns": 5,
      "agent_type": "multi_turn"
    }}
  }}
}}

MULTIPLE EXIT POINTS - CRITICAL REQUIREMENT:
You MUST create a SEPARATE return node for EACH distinct exit point in the workflow.
NEVER reuse the same return node for multiple exit points - this is a critical error.
Each condition branch (yes/no) that ends the workflow needs its own unique return node.
The final step also needs its own unique return node.

For example, if you have:
- cond1 "no" branch that exits → create return1 (e.g., "Return: Manager Rejected")
- cond2 "no" branch that exits → create return2 (e.g., "Return: Pending Approval")
- final step that completes → create return3 (e.g., "Return: Success")

BAD EXAMPLE (DO NOT DO THIS):
Only one return node with multiple incoming edges - this creates layout problems!

CORRECT EXAMPLE:
{{
  "id": "return1",
  "type": "return",
  "label": "Return: Manager Rejected",
  "metadata": {{
    "action_id": "early_return",
    "return_condition": "Manager approval denied",
    "return_type": "early_exit"
  }}
}},
{{
  "id": "return2",
  "type": "return",
  "label": "Return: Pending Approval",
  "metadata": {{
    "action_id": "pending_return",
    "return_condition": "Awaiting approval",
    "return_type": "early_exit"
  }}
}},
{{
  "id": "return3",
  "type": "return",
  "label": "Return: Success",
  "metadata": {{
    "action_id": "workflow_complete",
    "return_condition": "All approvals granted",
    "return_type": "success"
  }}
}}

LOOP METADATA:
For loop nodes, use LOOP ANALYSIS section to populate loop_metadata:
- metadata.loop_metadata.loop_variable: Variable being iterated
- metadata.loop_metadata.iteration_source: What's being looped over
- metadata.loop_metadata.estimated_count: Number if determinable
- metadata.loop_metadata.count_type: "static", "dynamic", or "unknown"

Example:
{{
  "id": "loop1",
  "type": "loop",
  "label": "For each ticker",
  "metadata": {{
    "action_id": "process_tickers",
    "loop_metadata": {{
      "loop_variable": "ticker",
      "iteration_source": "TICKERS",
      "estimated_count": 20,
      "count_type": "static"
    }}
  }}
}}

WORKFLOW CONTEXT:
{source_code}

Generate a complete visualization graph with ALL metadata fields populated:"""


class VisualizationOutput(BaseModel):
    """Structured output from LLM containing the visualization graph."""

    graph: VisualizationGraph


def get_code_hash(source_code: str) -> str:
    """Generate stable hash of source code for caching."""
    return hashlib.sha256(source_code.encode()).hexdigest()[:16]


def extract_called_functions(workflow_source: str) -> Set[str]:
    """Extract names of all functions called with await in workflow."""
    try:
        tree = ast.parse(workflow_source)
        called = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Await) and isinstance(node.value, ast.Call):
                if isinstance(node.value.func, ast.Name):
                    called.add(node.value.func.id)
                elif isinstance(node.value.func, ast.Attribute) and isinstance(
                    node.value.func.value, ast.Name
                ):
                    called.add(node.value.func.value.id)

        return called
    except Exception as e:
        logger.warning("Failed to parse workflow AST", error=str(e))
        return set()


def get_step_metadata(module, func_names: Set[str]) -> list[str]:
    """Get step function signatures and decorators."""
    step_defs = []

    for name in func_names:
        if not hasattr(module, name):
            continue

        func = getattr(module, name)

        if hasattr(func, "original_fn"):
            try:
                source = inspect.getsource(func.original_fn)
                lines = source.split("\n")
                for i, line in enumerate(lines[:10]):
                    if line.strip().startswith("def ") or line.strip().startswith(
                        "async def "
                    ):
                        snippet = "\n".join(
                            lines[max(0, i - 1) : min(i + 2, len(lines))]
                        )
                        step_defs.append(f"{snippet}\n    ...")
                        break
            except Exception as e:
                logger.warning(
                    "failed to extract step source", step_name=name, error=str(e)
                )

    return step_defs


def get_agent_metadata(module, func_names: Set[str]) -> list[str]:
    """Get agent definitions with tool information."""
    agent_defs = []

    for name in func_names:
        if not hasattr(module, name):
            continue

        obj = getattr(module, name)

        if obj.__class__.__name__ in ("Agent", "IOAgent"):
            try:
                input_type = (
                    obj.input_type.__name__
                    if hasattr(obj.input_type, "__name__")
                    else str(obj.input_type)
                )
                output_type = (
                    obj.output_type.__name__
                    if hasattr(obj.output_type, "__name__")
                    else str(obj.output_type)
                )

                tool_names = [tool.__name__ for tool in obj.tools if callable(tool)]

                if obj.__class__.__name__ == "IOAgent":
                    agent_type = "io_agent"
                elif obj.max_turns > 2 or tool_names:
                    agent_type = "multi_turn"
                else:
                    agent_type = "single_turn"

                agent_defs.append(
                    f"{name} = Agent(\n"
                    f"    name='{obj.name}',\n"
                    f"    input_type={input_type},\n"
                    f"    output_type={output_type},\n"
                    f"    max_turns={obj.max_turns},\n"
                    f"    tools=[{', '.join(repr(t) for t in tool_names)}],\n"
                    f"    agent_type='{agent_type}'\n"
                    f")"
                )
            except Exception as e:
                logger.warning(
                    "failed to extract agent metadata", agent_name=name, error=str(e)
                )

    return agent_defs


def get_human_metadata(module, func_names: Set[str]) -> list[str]:
    """Get human task definitions."""
    human_defs = []

    for name in func_names:
        if not hasattr(module, name):
            continue

        obj = getattr(module, name)

        if hasattr(obj, "__class__") and obj.__class__.__name__ == "Human":
            try:
                human_defs.append(f"{name} = Human(\n    name='{obj.name}',\n)")
            except Exception as e:
                logger.warning(
                    "failed to extract human metadata", human_name=name, error=str(e)
                )

    return human_defs


def get_return_contexts(workflow_source: str) -> list[str]:
    """
    Get code context around each return statement.

    Returns snippets showing condition + return for LLM analysis.
    """
    lines = workflow_source.split("\n")
    contexts = []

    for i, line in enumerate(lines):
        if re.match(r"\s*return\b", line):
            start = max(0, i - 3)
            snippet = "\n".join(lines[start : i + 1])
            contexts.append(snippet)

    return contexts


def extract_loop_metadata(workflow_source: str) -> list[dict[str, Any]]:
    """Extract loop information from workflow source."""
    try:
        tree = ast.parse(workflow_source)
        loops = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.AsyncFor)):
                loop_info = {
                    "line_number": node.lineno,
                    "loop_variable": None,
                    "iteration_source": None,
                    "estimated_count": None,
                    "count_type": "unknown",
                }

                if isinstance(node.target, ast.Name):
                    loop_info["loop_variable"] = node.target.id

                if isinstance(node.iter, ast.Name):
                    loop_info["iteration_source"] = node.iter.id
                    loop_info["count_type"] = "dynamic"
                elif isinstance(node.iter, ast.Call):
                    if isinstance(node.iter.func, ast.Name):
                        func_name = node.iter.func.id

                        if func_name == "range" and node.iter.args:
                            if isinstance(node.iter.args[0], ast.Constant):
                                loop_info["estimated_count"] = node.iter.args[0].value
                                loop_info["count_type"] = "static"

                        loop_info["iteration_source"] = f"{func_name}(...)"

                loops.append(loop_info)

        return loops
    except Exception as e:
        logger.warning("failed to extract loop metadata", error=str(e))
        return []


def extract_data_flow(workflow_source: str) -> dict[str, list[str]]:
    """
    Detect data flow between steps in workflow.

    Analyzes variable assignments and usage to determine which steps
    depend on outputs from other steps.

    Returns:
        Dict mapping step_name -> list of steps that consume its output
    """
    try:
        tree = ast.parse(workflow_source)
        data_flow = {}

        assignments = {}

        step_dependencies = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                    var_name = node.targets[0].id

                    if isinstance(node.value, ast.Await):
                        if isinstance(node.value.value, ast.Call):
                            if isinstance(node.value.value.func, ast.Name):
                                step_name = node.value.value.func.id
                                assignments[var_name] = step_name

            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                step_name = node.func.id
                used_vars = []

                for arg in node.args:
                    if isinstance(arg, ast.Name):
                        used_vars.append(arg.id)
                    elif isinstance(arg, ast.Attribute):
                        if isinstance(arg.value, ast.Name):
                            used_vars.append(arg.value.id)

                for keyword in node.keywords:
                    if isinstance(keyword.value, ast.Name):
                        used_vars.append(keyword.value.id)
                    elif isinstance(keyword.value, ast.Attribute):
                        if isinstance(keyword.value.value, ast.Name):
                            used_vars.append(keyword.value.value.id)

                if used_vars:
                    step_dependencies[step_name] = used_vars

        for consuming_step, vars_used in step_dependencies.items():
            for var in vars_used:
                if var in assignments:
                    producing_step = assignments[var]
                    if producing_step not in data_flow:
                        data_flow[producing_step] = []
                    if consuming_step not in data_flow[producing_step]:
                        data_flow[producing_step].append(consuming_step)

        return data_flow
    except Exception as e:
        logger.warning("failed to extract data flow", error=str(e))
        return {}


def get_data_flow_context(workflow_source: str, called_functions: Set[str]) -> str:
    """
    Build human-readable data flow description for LLM.
    """
    data_flow = extract_data_flow(workflow_source)

    if not data_flow:
        return ""

    lines = ["# DATA FLOW:", "# Shows which steps consume outputs from other steps:"]

    for producer, consumers in data_flow.items():
        if producer in called_functions:
            consumer_list = ", ".join(consumers)
            lines.append(f"# {producer} → [{consumer_list}]")

    return "\n".join(lines)


def get_workflow_metadata(workflow_wrapper):
    """Extract workflow-level metadata."""
    workflow_fn = workflow_wrapper.original_fn

    name = workflow_fn.__name__
    fully_qualified_name = f"{workflow_fn.__module__}.{name}"

    description = inspect.getdoc(workflow_fn)

    input_schema = None
    if hasattr(workflow_wrapper, "pydantic_model"):
        try:
            input_schema = workflow_wrapper.pydantic_model.model_json_schema()
        except Exception as e:
            logger.warning(
                "failed to extract input schema",
                workflow_name=workflow_fn.__name__,
                error=str(e),
            )

    return WorkflowMetadata(
        name=name,
        fully_qualified_name=fully_qualified_name,
        description=description,
        input_schema=input_schema,
        output_schema=None,
    )


def build_enriched_context(workflow_wrapper) -> str:
    """Build workflow source code enriched with step/agent/human metadata."""
    workflow_fn = workflow_wrapper.original_fn
    workflow_source = inspect.getsource(workflow_fn)
    module = inspect.getmodule(workflow_fn)

    called_functions = extract_called_functions(workflow_source)

    logger.debug(
        "Extracted called functions from workflow",
        called_functions=list(called_functions),
    )

    if not called_functions or not module:
        logger.warning(
            "no called functions or module found",
            workflow_name=workflow_fn.__name__,
            has_module=module is not None,
            called_functions_count=len(called_functions),
        )
        return workflow_source

    context_parts = ["# WORKFLOW CODE:", workflow_source, ""]

    step_defs = get_step_metadata(module, called_functions)
    logger.debug("Extracted step definitions", count=len(step_defs))
    if step_defs:
        context_parts.append("# STEP DEFINITIONS:")
        context_parts.extend(step_defs)
        context_parts.append("")

    agent_defs = get_agent_metadata(module, called_functions)
    logger.debug("Extracted agent definitions", count=len(agent_defs))
    if agent_defs:
        context_parts.append("# AGENT DEFINITIONS:")
        context_parts.extend(agent_defs)
        context_parts.append("")

    human_defs = get_human_metadata(module, called_functions)
    logger.debug("Extracted human definitions", count=len(human_defs))
    if human_defs:
        context_parts.append("# HUMAN TASK DEFINITIONS:")
        context_parts.extend(human_defs)
        context_parts.append("")

    return_contexts = get_return_contexts(workflow_source)
    if return_contexts:
        context_parts.append("# RETURN STATEMENTS:")
        context_parts.append(f"# Found {len(return_contexts)} return statement(s):")
        for i, ctx in enumerate(return_contexts, 1):
            context_parts.append(f"# Return {i}:")
            context_parts.append(ctx)
            context_parts.append("")

    loop_metadata = extract_loop_metadata(workflow_source)
    if loop_metadata:
        context_parts.append("# LOOP ANALYSIS:")
        for i, loop in enumerate(loop_metadata, 1):
            context_parts.append(f"# Loop {i} (line {loop['line_number']}):")
            context_parts.append(f"#   Variable: {loop['loop_variable']}")
            context_parts.append(f"#   Source: {loop['iteration_source']}")
            context_parts.append(
                f"#   Count: {loop['estimated_count']} ({loop['count_type']})"
            )
            context_parts.append("")

    return "\n".join(context_parts)


async def get_workflow_visualization(
    workflow_name: str, force_regenerate: bool = False
) -> WorkflowVisualizationResult:
    """
    Generate or retrieve cached workflow visualization.

    Uses customer's existing LLM configuration (same as Agents).
    Results are cached in database by source code hash.

    Args:
        workflow_name: Name of the workflow to visualize
        force_regenerate: If True, regenerate even if cached version exists

    Returns:
        WorkflowVisualizationResult containing graph and metadata

    Raises:
        WorkflowVisualizationNotConfiguredError: AI models not configured
        WorkflowVisualizationNotFoundError: Workflow not found
        WorkflowVisualizationSourceError: Cannot read workflow source
        WorkflowVisualizationGenerationError: LLM generation failed
    """
    session = get_session()
    config = get_config()

    if not config.ai_models:
        raise WorkflowVisualizationNotConfiguredError(
            "AI models not configured. Add ai_models section to planar.yaml"
        )

    registry = ObjectRegistry.get_instance()
    wf = next((w for w in registry.get_workflows() if w.name == workflow_name), None)
    if not wf:
        raise WorkflowVisualizationNotFoundError(
            f"Workflow '{workflow_name}' not found"
        )

    try:
        enriched_context = build_enriched_context(wf.obj)
        code_hash = get_code_hash(enriched_context)

        logger.debug(
            "built enriched context for workflow",
            workflow_name=workflow_name,
            context_length=len(enriched_context),
        )
    except Exception as e:
        logger.exception("Failed to read workflow source code")
        raise WorkflowVisualizationSourceError("Could not read source code") from e

    if not force_regenerate:
        cached = await session.get(WorkflowVisualization, workflow_name)

        if cached and cached.code_hash == code_hash and not cached.error:
            logger.debug(
                "returning cached visualization",
                workflow_name=workflow_name,
                code_hash=code_hash,
            )
            try:
                graph_data = json.loads(cached.diagram)
                cached_graph = VisualizationGraph(**graph_data)
            except Exception as e:
                logger.warning("failed to parse cached graph", error=str(e))
            else:
                return WorkflowVisualizationResult(
                    graph=cached_graph,
                    from_cache=True,
                    generated_at=cached.updated_at,
                    llm_model=cached.llm_model,
                )

        logger.debug("no valid cache, not generating", workflow_name=workflow_name)
        return WorkflowVisualizationResult(graph=None, from_cache=False)

    # Generate using customer's LLM (same as Agents)
    logger.debug("generating new visualization", workflow_name=workflow_name)

    try:
        # Get or create model registry using public API
        model_registry = config.get_model_registry()

        # Use default model (same as agents if not specified)
        model = await model_registry.resolve(None)

        # Call LLM with structured output
        prompt = VISUALIZATION_PROMPT.format(source_code=enriched_context)

        response = await model_run(
            model=model,
            max_extra_turns=0,
            messages=[UserMessage(content=prompt)],
            output_type=VisualizationOutput,
            model_settings=PlanarModelSettings(temperature=0),  # Deterministic output
        )

        # Extract graph from structured response
        output = response.response.content
        if output is None:
            raise ValueError("LLM returned no content")

        graph = output.graph

        # Inject workflow metadata and spec version
        wf_metadata = get_workflow_metadata(wf.obj)
        complete_graph = graph.model_copy(
            update={"spec_version": "1.0", "workflow": wf_metadata}
        )

        logger.info(
            "generated visualization graph",
            workflow_name=workflow_name,
            node_count=len(complete_graph.nodes),
            edge_count=len(complete_graph.edges),
        )

        # Validate graph structure
        if not complete_graph.nodes:
            raise ValueError("LLM returned graph with no nodes")

        if len(complete_graph.nodes) > 100:
            raise ValueError(
                f"Graph too large: {len(complete_graph.nodes)} nodes (max 100 for visualization)"
            )

        # Validate edge references
        node_ids = {node.id for node in complete_graph.nodes}
        for edge in complete_graph.edges:
            if edge.from_node not in node_ids:
                raise ValueError(
                    f"Invalid edge: from_node '{edge.from_node}' not in graph"
                )
            if edge.to_node not in node_ids:
                raise ValueError(f"Invalid edge: to_node '{edge.to_node}' not in graph")

        # Convert to JSON for storage
        diagram = complete_graph.model_dump_json()

        model_name = f"{model.system}:{model.model_name}"

        # Save to database (cache)
        viz = WorkflowVisualization(
            workflow_name=workflow_name,
            code_hash=code_hash,
            diagram=diagram,
            llm_model=model_name,
            error=None,
        )

        # Upsert
        existing = await session.get(WorkflowVisualization, workflow_name)
        if existing:
            existing.code_hash = code_hash
            existing.diagram = diagram
            existing.error = None
            existing.llm_model = model_name
        else:
            session.add(viz)

        await session.commit()

        return WorkflowVisualizationResult(
            graph=complete_graph,
            from_cache=False,
            llm_model=model_name,
        )

    except Exception as e:
        logger.exception(
            "Failed to generate visualization", workflow_name=workflow_name
        )

        viz = WorkflowVisualization(
            workflow_name=workflow_name,
            code_hash=code_hash,
            diagram="",
            llm_model="",
            error=str(e),
        )

        existing = await session.get(WorkflowVisualization, workflow_name)
        if existing:
            existing.error = str(e)
            existing.code_hash = code_hash
        else:
            session.add(viz)

        await session.commit()

        raise WorkflowVisualizationGenerationError(
            "Failed to generate visualization"
        ) from e
