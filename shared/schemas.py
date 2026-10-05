from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class SymbolClass(str, Enum):
    TANK = "tank"
    VESSEL = "vessel"
    PUMP = "pump"
    EXCHANGER = "exchanger"
    VALVE = "valve"
    INSTRUMENT = "instrument"
    OTHER = "other"


class ConnectionType(str, Enum):
    PROCESS = "process"
    INSTRUMENT = "instrument"
    SIGNAL = "signal"
    UNKNOWN = "unknown"


class Direction(str, Enum):
    UPSTREAM = "upstream"
    DOWNSTREAM = "downstream"
    BIDIRECTIONAL = "bidirectional"
    UNKNOWN = "unknown"


class JobStatus(str, Enum):
    CREATED = "created"
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    NEEDS_REVIEW = "needs_review"


class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class Point(BaseModel):
    x: float
    y: float


class Page(BaseModel):
    model_config = ConfigDict(extra="forbid")

    page_id: str
    page_number: int = Field(ge=1)
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    dpi: int = Field(default=300, gt=0)
    image_path: str | None = None
    source_pdf: str | None = None


class Symbol(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    page_id: str
    class_name: SymbolClass | str
    tag: str | None = None
    bbox: BBox
    confidence: float = Field(ge=0, le=1)
    source: str = "vision"
    reviewed: bool = False


class OCRResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    page_id: str
    text: str
    bbox: BBox
    confidence: float = Field(ge=0, le=1)
    associated_symbol_id: str | None = None


class Line(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    page_id: str
    points: list[Point] = Field(min_length=2)
    confidence: float = Field(ge=0, le=1)
    is_process_line: bool = True
    thickness_px: float | None = None
    dashed: bool = False
    arrows: list[Point] = Field(default_factory=list)


class Association(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str
    line_id: str
    source_symbol_id: str | None = None
    target_symbol_id: str | None = None
    source_point: Point | None = None
    target_point: Point | None = None
    confidence: float = Field(ge=0, le=1)
    connection_type: ConnectionType = ConnectionType.PROCESS


class GraphNode(BaseModel):
    id: str
    symbol_id: str
    class_name: str
    tag: str | None = None
    page_id: str


class GraphEdge(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    line_id: str | None = None
    direction: Direction = Direction.UNKNOWN
    confidence: float = Field(ge=0, le=1)


class Graph(BaseModel):
    model_config = ConfigDict(extra="forbid")

    graph_id: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    main_path: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class SketchNode(BaseModel):
    id: str
    source_node_id: str
    label: str
    class_name: str
    x: float
    y: float


class SketchEdge(BaseModel):
    id: str
    source_node_id: str
    target_node_id: str
    direction: Direction = Direction.UNKNOWN


class Sketch(BaseModel):
    sketch_id: str
    nodes: list[SketchNode]
    edges: list[SketchEdge]
    svg_path: str | None = None
    png_path: str | None = None


class MappingEntry(BaseModel):
    sketch_node_id: str
    original_symbol_id: str
    page_id: str
    bbox: BBox


class Mapping(BaseModel):
    mapping_id: str
    entries: list[MappingEntry]


class AuditEntry(BaseModel):
    id: str
    action: str
    source_id: str | None = None
    target_id: str | None = None
    status: str
    message: str | None = None


class Audit(BaseModel):
    audit_id: str
    io_total: int = Field(ge=0)
    io_found: int = Field(ge=0)
    io_missing: int = Field(ge=0)
    io_coverage: float = Field(ge=0, le=100)
    equipment_total: int = Field(ge=0)
    equipment_found: int = Field(ge=0)
    connections_valid: bool
    flow_valid: bool
    status: str
    entries: list[AuditEntry] = Field(default_factory=list)


class Job(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: str
    status: JobStatus = JobStatus.CREATED
    pid_filename: str | None = None
    io_filename: str | None = None
    pages: list[Page] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
