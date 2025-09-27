from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime

class MacroClass(str, Enum):
    TERMINOLOGY = "Terminology"
    PUNCTUATION = "Punctuation"
    MECHANICS = "Mechanics"
    STANDARDS = "Standards"
    STYLE = "Style"
    ACCURACY = "Accuracy"
    LEGAL = "Legal"

class Severity(str, Enum):
    MINOR = "Minor"
    MAJOR = "Major"
    CRITICAL = "Critical"

class Citation(BaseModel):
    section_path: List[str] = Field(..., description="Path to the section in the source document")
    page_number: Optional[int] = None
    document_name: Optional[str] = None

class Rule(BaseModel):
    rule_id: str = Field(..., description="Unique identifier for the rule")
    macro_class: MacroClass = Field(..., description="High-level category of the rule")
    micro_class: str = Field(..., description="Specific subcategory of the rule")
    rule_text: str = Field(..., description="Human-readable description of the rule")
    examples_pos: List[str] = Field(default=[], description="Positive examples (correct usage)")
    examples_neg: List[str] = Field(default=[], description="Negative examples (incorrect usage)")
    default_severity: Severity = Field(..., description="Default severity level")
    default_weight: int = Field(..., description="Default weight for scoring")
    citation: Citation = Field(..., description="Reference to source document")
    regex_ready: bool = Field(default=False, description="Whether rule can be checked with regex")
    regex_pattern: Optional[str] = Field(None, description="Regex pattern if applicable")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Finding(BaseModel):
    segment_id: str = Field(..., description="Unique identifier for the text segment")
    rule_id: str = Field(..., description="Rule that was violated")
    severity: Severity = Field(..., description="Severity of the violation")
    penalty: int = Field(..., description="Point deduction for this finding")
    justification: str = Field(..., description="Explanation of why this is a violation")
    citation: Citation = Field(..., description="Reference to the rule source")
    deterministic: bool = Field(..., description="Whether this was found by deterministic check")
    span_start: Optional[int] = Field(None, description="Start position of the violation in text")
    span_end: Optional[int] = Field(None, description="End position of the violation in text")
    highlighted_text: Optional[str] = Field(None, description="The specific text that violates the rule")

class ScoreBreakdown(BaseModel):
    penalty: int = Field(..., description="Total penalty for this category")
    count: int = Field(..., description="Number of violations in this category")
    rules_triggered: List[str] = Field(default=[], description="Rule IDs that were triggered")

class ScoreReport(BaseModel):
    job_id: str = Field(..., description="Unique identifier for this evaluation job")
    kb_version: str = Field(..., description="Version of the knowledge base used")
    rubric_version: str = Field(..., description="Version of the scoring rubric used")
    model_prompt_version: str = Field(..., description="Version of the LLM prompt used")
    final_score: int = Field(..., description="Final score out of 100")
    findings: List[Finding] = Field(..., description="All findings from the evaluation")
    by_macro: Dict[str, ScoreBreakdown] = Field(..., description="Score breakdown by macro category")
    source_text: str = Field(..., description="Original source text")
    target_text: str = Field(..., description="Translation being evaluated")
    locale: str = Field(..., description="Target locale (e.g., zh-CN)")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class FeedbackAction(str, Enum):
    ACCEPT = "accept"
    CHANGE_SEVERITY = "change_severity"
    RECLASSIFY = "reclassify"
    DISMISS = "dismiss"

class FeedbackEvent(BaseModel):
    event_id: str = Field(..., description="Unique identifier for this feedback event")
    segment_id: str = Field(..., description="Segment that was reviewed")
    rule_id: str = Field(..., description="Rule that was overridden")
    action: FeedbackAction = Field(..., description="Action taken by reviewer")
    old_value: str = Field(..., description="Original value")
    new_value: str = Field(..., description="New value after override")
    reason: str = Field(..., description="Reason for the override")
    actor: str = Field(..., description="Reviewer who made the change")
    created_at: datetime = Field(default_factory=datetime.utcnow)

class KnowledgeBase(BaseModel):
    kb_version: str = Field(..., description="Version identifier for this KB")
    rubric_version: str = Field(..., description="Version identifier for scoring rubric")
    rules: List[Rule] = Field(..., description="All rules in this knowledge base")
    source_document: str = Field(..., description="Name of the source style guide")
    locale: str = Field(..., description="Target locale for this KB")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    rule_count: int = Field(..., description="Total number of rules")

# Request/Response models for API
class DocumentUploadRequest(BaseModel):
    filename: str
    locale: str = Field(..., description="Target locale (e.g., zh-CN)")

class EvaluationRequest(BaseModel):
    source_text: str = Field(..., description="Original source text")
    target_text: str = Field(..., description="Translation to evaluate")
    locale: str = Field(..., description="Target locale")
    kb_version: Optional[str] = Field(None, description="Specific KB version to use")

class ReviewOverrideRequest(BaseModel):
    finding_id: str = Field(..., description="ID of the finding to override")
    action: FeedbackAction = Field(..., description="Action to take")
    new_severity: Optional[Severity] = Field(None, description="New severity if changing")
    reason: str = Field(..., description="Reason for the override")
    reviewer: str = Field(..., description="Reviewer making the change")