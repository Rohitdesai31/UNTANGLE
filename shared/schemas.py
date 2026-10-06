from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class Page(BaseModel):
    id: str
    page_number: int
    width: Optional[float] = None
    height: Optional[float] = None


class Symbol(BaseModel):
    id: str
    class_name: str
    tag: Optional[str] = None
    bbox: list[float] = Field(default_factory=list)
    confidence: Optional[float] = None
    page: Optional[int] = None


class OCRResult(BaseModel):
    id: str
    text: str
    bbox: list[float] = Field(default_factory=list)
    confidence: Optional[float] = None
    page: Optional[int] = None


class Line(BaseModel):
    id: str
    points: list[list[float]] = Field(default_factory=list)
    line_type: str = "process"
    confidence: Optional[float] = None
    page: Optional[int] = None


class IOItem(BaseModel):
    tag: str
    type: str
    description: str
    loop: str
    expected_status: str


class Association(BaseModel):
    source_id: str
    target_id: str
    relation: str
    confidence: Optional[float] = None


class GraphNode(BaseModel):
    id: str
    node_type: str
    tag: Optional[str] = None


class GraphEdge(BaseModel):
    source: str
    target: str
    relation: str = "process_flow"


class Graph(BaseModel):
    nodes: list[GraphNode] = Field(default_factory=list)
    edges: list[GraphEdge] = Field(default_factory=list)


class Mapping(BaseModel):
    original_id: str
    simplified_id: str


class AuditValidationChecks(BaseModel):
    all_required_equipment_preserved: bool = False
    all_found_io_tags_preserved: bool = False
    missing_io_tags_reported: bool = False
    process_connections_preserved: bool = False
    flow_direction_preserved: bool = False
    simplified_graph_valid: bool = False


class Audit(BaseModel):
    io_total: int = 0
    io_found: int = 0
    io_missing: int = 0
    io_coverage: float = 0.0

    equipment_total: int = 0
    equipment_found: int = 0

    connections_valid: bool = False
    flow_valid: bool = False

    status: str = "FAIL"

    missing_tags: list[str] = Field(default_factory=list)
    found_tags: list[str] = Field(default_factory=list)

    validation_checks: AuditValidationChecks = Field(
        default_factory=AuditValidationChecks
    )


class Sketch(BaseModel):
    svg_path: str
    width: Optional[float] = None
    height: Optional[float] = None


class Job(BaseModel):
    id: str
    status: str
    message: Optional[str] = None