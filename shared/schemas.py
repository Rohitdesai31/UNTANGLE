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

class Audit(BaseModel):
    io_total: int = 0
    io_found: int = 0
    io_missing: int = 0
    io_coverage: float = 0
    equipment_total: int = 0
    equipment_found: int = 0
    connections_valid: bool = False
    flow_valid: bool = False
    status: str = "FAIL"

class Sketch(BaseModel):
    svg_path: str
    width: Optional[float] = None
    height: Optional[float] = None

class Job(BaseModel):
    id: str
    status: str
    message: Optional[str] = None
