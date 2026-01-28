"""
Data models and schemas using Pydantic
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ChatMode(str, Enum):
    CHAT = "chat"
    FILE = "file"
    WEB = "web"
    AEM = "aem"

class Intent(str, Enum):
    CHAT = "chat"
    FILE_UPLOAD = "file_upload"
    WEB_SEARCH = "web_search"
    AEM_QUERY = "aem_query"
    AEM_COMPLIANCE = "aem_compliance"
    UNKNOWN = "unknown"

class Message(BaseModel):
    role: str = Field(..., description="Message role (user/assistant)")
    content: str = Field(..., description="Message content")
    timestamp: datetime = Field(default_factory=datetime.now)
    mode: Optional[ChatMode] = None
    metadata: Optional[Dict[str, Any]] = None

class ChatRequest(BaseModel):
    message: str = Field(..., description="User message")
    mode: ChatMode = Field(default=ChatMode.CHAT, description="Chat mode")
    model: str = Field(default="gemma:2b", description="Model to use")
    temperature: float = Field(default=0.7, ge=0, le=1)
    conversation_id: Optional[str] = None
    context: Optional[List[Message]] = None

class ChatResponse(BaseModel):
    message: str
    mode: ChatMode
    intent: Optional[Intent] = None
    suggested_mode: Optional[ChatMode] = None
    metadata: Optional[Dict[str, Any]] = None
    conversation_id: str

class FileUploadRequest(BaseModel):
    file_path: str
    question: Optional[str] = None
    model: str = Field(default="gemma:2b")

class FileUploadResponse(BaseModel):
    content: str
    answer: Optional[str] = None
    metadata: Dict[str, Any]

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = Field(default=5, ge=1, le=10)
    model: str = Field(default="gemma:2b")

class WebSearchResponse(BaseModel):
    query: str
    results: List[Dict[str, Any]]
    summary: str
    sources: List[str]

class AEMPageInfo(BaseModel):
    path: str
    title: str
    last_modified: Optional[str] = None
    template: Optional[str] = None
    has_content: bool = True

class AEMQueryRequest(BaseModel):
    path: str = Field(default="/content", description="AEM content path to query")
    depth: int = Field(default=3, ge=1, le=10, description="Query depth")
    include_templates: Optional[List[str]] = None
    exclude_templates: Optional[List[str]] = None

class AEMQueryResponse(BaseModel):
    pages: List[AEMPageInfo]
    total_count: int
    query_path: str

class ComplianceCheckRequest(BaseModel):
    page_paths: List[str] = Field(..., description="List of page paths to check")
    categories: Optional[List[str]] = None
    model: str = Field(default="gemma:2b")

class CheckResult(BaseModel):
    id: str
    name: str
    passed: bool
    score: float
    issues: List[str]
    recommendations: List[str]
    severity: str

class CategoryResult(BaseModel):
    category: str
    name: str
    score: float
    checks: List[CheckResult]
    total_checks: int
    passed_checks: int

class ComplianceResult(BaseModel):
    page_path: str
    page_title: str
    overall_score: float
    grade: str
    categories: List[CategoryResult]
    total_issues: int
    high_priority_issues: int
    medium_priority_issues: int
    low_priority_issues: int
    checked_at: datetime = Field(default_factory=datetime.now)

class ComplianceCheckResponse(BaseModel):
    results: List[ComplianceResult]
    summary: Dict[str, Any]
    export_available: bool = True

class ExportRequest(BaseModel):
    format: str = Field(..., description="Export format (csv/pdf)")
    results: List[ComplianceResult]
    include_details: bool = True

class ExportResponse(BaseModel):
    file_path: str
    file_name: str
    format: str
    size_bytes: int

class IntentDetectionRequest(BaseModel):
    text: str
    context: Optional[List[Message]] = None

class IntentDetectionResponse(BaseModel):
    intent: Intent
    confidence: float
    suggested_mode: Optional[ChatMode] = None
    extracted_entities: Dict[str, Any] = {}

class HealthResponse(BaseModel):
    status: str
    services: Dict[str, str]
    timestamp: datetime = Field(default_factory=datetime.now)

class ErrorResponse(BaseModel):
    error: str
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = Field(default_factory=datetime.now)