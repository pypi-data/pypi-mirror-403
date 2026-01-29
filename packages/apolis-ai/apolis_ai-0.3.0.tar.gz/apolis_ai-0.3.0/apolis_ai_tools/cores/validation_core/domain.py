from typing import Any, Dict, List, Optional, Literal, Union
from pydantic import BaseModel, Field
from enum import Enum


class FieldType(str, Enum):
    """Supported field types for validation"""
    STRING = "string"
    NUMBER = "number"
    INTEGER = "integer"
    BOOLEAN = "boolean"
    DATE = "date"
    DATETIME = "datetime"
    EMAIL = "email"
    PHONE = "phone"
    CURRENCY = "currency"
    PERCENTAGE = "percentage"
    ARRAY = "array"
    OBJECT = "object"


class IssueSeverity(str, Enum):
    """Severity levels for validation issues"""
    ERROR = "error"      # Critical - data is invalid
    WARNING = "warning"  # Non-critical - data is suspicious
    INFO = "info"        # Informational - potential improvement


class ValidationIssue(BaseModel):
    """A single validation issue"""
    field: str = Field(..., description="Dot-notation path to the field (e.g., 'deposits[0].amount')")
    severity: IssueSeverity
    message: str
    expected: Optional[Any] = None
    actual: Optional[Any] = None
    rule: Optional[str] = Field(None, description="Rule that was violated")


class FieldSchema(BaseModel):
    """Schema definition for a single field"""
    type: FieldType
    required: bool = False
    min: Optional[Union[int, float]] = None
    max: Optional[Union[int, float]] = None
    pattern: Optional[str] = Field(None, description="Regex pattern for string validation")
    items: Optional["FieldSchema"] = Field(None, description="Schema for array items")
    properties: Optional[Dict[str, "FieldSchema"]] = Field(None, description="Schema for object properties")
    enum: Optional[List[Any]] = Field(None, description="Allowed values")
    description: Optional[str] = None


class BusinessRule(BaseModel):
    """Business rule for custom validation logic"""
    field: str
    rule_type: Literal["min", "max", "equals", "not_equals", "in", "not_in", "custom"]
    value: Any
    message: str
    severity: IssueSeverity = IssueSeverity.ERROR


class ValidationSchema(BaseModel):
    """Complete validation schema"""
    fields: Dict[str, FieldSchema]
    rules: Optional[List[BusinessRule]] = Field(default_factory=list)
    strict: bool = Field(False, description="If True, reject any fields not in schema")


class ValidationResult(BaseModel):
    """Result of validation"""
    status: Literal["passed", "failed"]
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0.0-1.0")
    issues: List[ValidationIssue] = Field(default_factory=list)
    validated_data: Dict[str, Any] = Field(..., description="Cleaned and validated data")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary statistics")
