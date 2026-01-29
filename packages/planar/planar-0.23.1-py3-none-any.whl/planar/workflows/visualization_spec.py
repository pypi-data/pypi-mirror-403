"""Visualization specification models for workflow diagrams."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class AgentNodeMetadata(BaseModel):
    """Extended metadata for agent nodes."""

    tools: list[str] | None = Field(
        default=None, description="List of tool names available to the agent"
    )
    max_turns: int | None = Field(
        default=None, description="Maximum number of turns the agent can execute"
    )
    agent_type: Literal["single_turn", "multi_turn", "io_agent"] | None = Field(
        default=None, description="Type of agent execution pattern"
    )


class LoopNodeMetadata(BaseModel):
    """Extended metadata for loop nodes."""

    loop_variable: str | None = Field(
        default=None,
        description="Variable name being iterated (e.g., 'ticker', 'item')",
    )
    iteration_source: str | None = Field(
        default=None,
        description="What's being iterated over (e.g., 'TICKERS', 'dataset.rows')",
    )
    estimated_count: int | None = Field(
        default=None, description="Estimated iteration count if determinable"
    )
    count_type: Literal["static", "dynamic", "unknown"] | None = Field(
        default=None,
        description="Whether count is compile-time constant, runtime-determined, or unknown",
    )


class NodeMetadata(BaseModel):
    """Required metadata for each visualization node."""

    action_id: str = Field(description="Function or variable name being called")
    input_type: str | None = Field(default=None, description="Input type if available")
    output_type: str | None = Field(
        default=None, description="Output type if available"
    )
    condition: str | None = Field(
        default=None, description="Boolean expression for condition nodes"
    )
    description: str | None = Field(
        default=None, description="Brief description of what this node does"
    )

    # Extended metadata for specific node types
    agent_metadata: AgentNodeMetadata | None = Field(
        default=None, description="Additional metadata for agent nodes"
    )
    loop_metadata: LoopNodeMetadata | None = Field(
        default=None, description="Additional metadata for loop nodes"
    )

    # Return node metadata
    return_condition: str | None = Field(
        default=None, description="For return nodes: condition or reason for this exit"
    )
    return_type: Literal["success", "failure", "early_exit"] | None = Field(
        default=None, description="Classification of return type"
    )

    # Data flow metadata
    consumes_from: list[str] | None = Field(
        default=None, description="List of step IDs whose outputs this step consumes"
    )
    consumed_by: list[str] | None = Field(
        default=None, description="List of step IDs that consume this step's output"
    )


class VisualizationNode(BaseModel):
    """A node in the workflow visualization graph."""

    id: str = Field(description="Unique node identifier")
    type: Literal["step", "agent", "rule", "human", "condition", "loop", "return"] = (
        Field(description="Type of node")
    )
    label: str = Field(description="Display label for the node")
    metadata: NodeMetadata = Field(
        description="Required metadata with action_id and type information"
    )


class VisualizationEdge(BaseModel):
    """An edge connecting two nodes in the graph."""

    from_node: str = Field(description="Source node ID")
    to_node: str = Field(description="Target node ID")
    label: str | None = Field(
        default=None, description="Label for the edge (e.g., 'yes', 'no')"
    )


class WorkflowMetadata(BaseModel):
    """Metadata about the workflow being visualized."""

    name: str = Field(description="Workflow function name")
    fully_qualified_name: str = Field(description="Fully qualified workflow name")
    description: str | None = Field(
        default=None, description="Workflow description from docstring"
    )
    input_schema: dict[str, Any] | None = Field(
        default=None, description="JSON schema for workflow inputs"
    )
    output_schema: dict[str, Any] | None = Field(
        default=None, description="JSON schema for workflow outputs"
    )


class VisualizationGraph(BaseModel):
    """Complete visualization graph specification."""

    spec_version: str = Field(default="1.0", description="Specification format version")
    workflow: WorkflowMetadata = Field(
        description="Metadata about the workflow being visualized"
    )
    nodes: list[VisualizationNode] = Field(description="List of nodes in the graph")
    edges: list[VisualizationEdge] = Field(description="List of edges connecting nodes")
