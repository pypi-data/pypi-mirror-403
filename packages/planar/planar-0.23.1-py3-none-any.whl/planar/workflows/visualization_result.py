"""Result types for workflow visualization service."""

from datetime import datetime

from pydantic import BaseModel

from planar.workflows.visualization_spec import VisualizationGraph


class WorkflowVisualizationResult(BaseModel):
    """Result from workflow visualization generation or cache retrieval."""

    graph: VisualizationGraph | None
    from_cache: bool
    generated_at: datetime | None = None
    llm_model: str | None = None
