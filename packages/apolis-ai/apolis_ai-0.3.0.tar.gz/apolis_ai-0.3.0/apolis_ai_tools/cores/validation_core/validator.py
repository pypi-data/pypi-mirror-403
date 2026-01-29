import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from .domain import (
    FieldType,
    FieldSchema,
    ValidationSchema,
    ValidationResult,
    ValidationIssue,
    IssueSeverity,
    BusinessRule
)


class ExtractionValidator:
    """Core validation engine for extracted data"""

    def __init__(self, base_confidence: float = 1.0):
        """
        Initialize validator

        Args:
            base_confidence: Starting confidence score (0.0-1.0)
        """
        self.base_confidence = max(0.0, min(1.0, base_confidence))

    def validate(
        self,
        data: Dict[str, Any],
        schema: ValidationSchema,
        base_confidence: Optional[float] = None
    ) -> ValidationResult:
        """
        Validate extracted data against schema

        Args:
            data: Extracted data to validate
            schema: Validation schema
            base_confidence: Override base confidence

        Returns:
            ValidationResult with status, confidence, and issues
        """
        if base_confidence is not None:
            self.base_confidence = max(0.0, min(1.0, base_confidence))

        issues: List[ValidationIssue] = []
        validated_data = {}
        confidence = self.base_confidence

        # Validate each field in schema
        for field_name, field_schema in schema.fields.items():
            field_value = data.get(field_name)

            # Check required fields
            if field_schema.required and field_value is None:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=IssueSeverity.ERROR,
                    message=f"Required field '{field_name}' is missing",
                    expected="non-null value",
                    actual=None
                ))
                confidence -= 0.2  # Heavy penalty for missing required field
                continue

            # Skip validation if field is optional and missing
            if field_value is None:
                continue

            # Validate field type and constraints
            field_issues, cleaned_value = self._validate_field(
                field_name,
                field_value,
                field_schema
            )
            issues.extend(field_issues)
            validated_data[field_name] = cleaned_value

            # Deduct confidence for field issues
            for issue in field_issues:
                if issue.severity == IssueSeverity.ERROR:
                    confidence -= 0.15
                elif issue.severity == IssueSeverity.WARNING:
                    confidence -= 0.05

        # Check for extra fields in strict mode
        if schema.strict:
            for field_name in data.keys():
                if field_name not in schema.fields:
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=IssueSeverity.WARNING,
                        message=f"Unexpected field '{field_name}' not in schema",
                        actual=data[field_name]
                    ))
                    confidence -= 0.05

        # Validate business rules
        if schema.rules:
            rule_issues = self._validate_business_rules(validated_data, schema.rules)
            issues.extend(rule_issues)
            for issue in rule_issues:
                if issue.severity == IssueSeverity.ERROR:
                    confidence -= 0.1
                elif issue.severity == IssueSeverity.WARNING:
                    confidence -= 0.03

        # Ensure confidence stays in bounds
        confidence = max(0.0, min(1.0, confidence))

        # Determine status
        error_count = sum(1 for i in issues if i.severity == IssueSeverity.ERROR)
        status = "failed" if error_count > 0 else "passed"

        # Build summary
        summary = {
            "total_fields": len(schema.fields),
            "validated_fields": len(validated_data),
            "total_issues": len(issues),
            "errors": sum(1 for i in issues if i.severity == IssueSeverity.ERROR),
            "warnings": sum(1 for i in issues if i.severity == IssueSeverity.WARNING),
            "info": sum(1 for i in issues if i.severity == IssueSeverity.INFO),
        }

        return ValidationResult(
            status=status,
            confidence=round(confidence, 4),
            issues=issues,
            validated_data=validated_data,
            summary=summary
        )

    def _validate_field(
        self,
        field_name: str,
        value: Any,
        schema: FieldSchema
    ) -> Tuple[List[ValidationIssue], Any]:
        """Validate a single field"""
        issues: List[ValidationIssue] = []
        cleaned_value = value

        # Type validation
        type_valid, type_issues, cleaned = self._validate_type(
            field_name,
            value,
            schema.type
        )
        if not type_valid:
            issues.extend(type_issues)
            return issues, value  # Return original value if type is wrong
        cleaned_value = cleaned

        # Constraint validation
        constraint_issues = self._validate_constraints(
            field_name,
            cleaned_value,
            schema
        )
        issues.extend(constraint_issues)

        # Array items validation
        if schema.type == FieldType.ARRAY and schema.items and isinstance(cleaned_value, list):
            for idx, item in enumerate(cleaned_value):
                item_issues, cleaned_item = self._validate_field(
                    f"{field_name}[{idx}]",
                    item,
                    schema.items
                )
                issues.extend(item_issues)
                cleaned_value[idx] = cleaned_item

        # Object properties validation
        if schema.type == FieldType.OBJECT and schema.properties and isinstance(cleaned_value, dict):
            for prop_name, prop_schema in schema.properties.items():
                prop_value = cleaned_value.get(prop_name)

                # Check required fields
                if prop_schema.required and prop_value is None:
                    issues.append(ValidationIssue(
                        field=f"{field_name}.{prop_name}",
                        severity=IssueSeverity.ERROR,
                        message=f"Required field '{prop_name}' is missing",
                        expected="non-null value",
                        actual=None
                    ))
                    continue

                # Skip validation if field is optional and missing
                if prop_value is None:
                    continue

                prop_issues, cleaned_prop = self._validate_field(
                    f"{field_name}.{prop_name}",
                    prop_value,
                    prop_schema
                )
                issues.extend(prop_issues)
                cleaned_value[prop_name] = cleaned_prop

        return issues, cleaned_value

    def _validate_type(
        self,
        field_name: str,
        value: Any,
        field_type: FieldType
    ) -> Tuple[bool, List[ValidationIssue], Any]:
        """Validate field type and convert if possible"""
        issues: List[ValidationIssue] = []
        cleaned_value = value

        try:
            if field_type == FieldType.STRING:
                if not isinstance(value, str):
                    cleaned_value = str(value)

            elif field_type == FieldType.NUMBER:
                if not isinstance(value, (int, float)):
                    cleaned_value = float(value)

            elif field_type == FieldType.INTEGER:
                if not isinstance(value, int):
                    cleaned_value = int(value)

            elif field_type == FieldType.BOOLEAN:
                if not isinstance(value, bool):
                    if isinstance(value, str):
                        cleaned_value = value.lower() in ("true", "yes", "1")
                    else:
                        cleaned_value = bool(value)

            elif field_type == FieldType.DATE:
                if isinstance(value, str):
                    cleaned_value = self._parse_date(value)
                elif not isinstance(value, datetime):
                    raise ValueError(f"Cannot convert {type(value)} to date")

            elif field_type == FieldType.DATETIME:
                if isinstance(value, str):
                    cleaned_value = self._parse_datetime(value)
                elif not isinstance(value, datetime):
                    raise ValueError(f"Cannot convert {type(value)} to datetime")

            elif field_type == FieldType.EMAIL:
                if not isinstance(value, str):
                    cleaned_value = str(value)
                if not self._is_valid_email(cleaned_value):
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=IssueSeverity.ERROR,
                        message=f"Invalid email format",
                        expected="valid email address",
                        actual=value
                    ))
                    return False, issues, value

            elif field_type == FieldType.PHONE:
                if not isinstance(value, str):
                    cleaned_value = str(value)
                cleaned_value = self._clean_phone(cleaned_value)

            elif field_type == FieldType.CURRENCY:
                if isinstance(value, str):
                    cleaned_value = self._parse_currency(value)
                elif not isinstance(value, (int, float)):
                    cleaned_value = float(value)

            elif field_type == FieldType.PERCENTAGE:
                if isinstance(value, str):
                    cleaned_value = self._parse_percentage(value)
                elif isinstance(value, (int, float)):
                    # Assume already a decimal (0-100)
                    cleaned_value = float(value)
                else:
                    raise ValueError(f"Cannot convert {type(value)} to percentage")

            elif field_type == FieldType.ARRAY:
                if not isinstance(value, list):
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=IssueSeverity.ERROR,
                        message=f"Expected array, got {type(value).__name__}",
                        expected="array",
                        actual=type(value).__name__
                    ))
                    return False, issues, value

            elif field_type == FieldType.OBJECT:
                if not isinstance(value, dict):
                    issues.append(ValidationIssue(
                        field=field_name,
                        severity=IssueSeverity.ERROR,
                        message=f"Expected object, got {type(value).__name__}",
                        expected="object",
                        actual=type(value).__name__
                    ))
                    return False, issues, value

        except (ValueError, TypeError) as e:
            issues.append(ValidationIssue(
                field=field_name,
                severity=IssueSeverity.ERROR,
                message=f"Type conversion failed: {str(e)}",
                expected=field_type.value,
                actual=type(value).__name__
            ))
            return False, issues, value

        return True, issues, cleaned_value

    def _validate_constraints(
        self,
        field_name: str,
        value: Any,
        schema: FieldSchema
    ) -> List[ValidationIssue]:
        """Validate field constraints (min, max, pattern, enum)"""
        issues: List[ValidationIssue] = []

        # Min constraint
        if schema.min is not None:
            if isinstance(value, (int, float)) and value < schema.min:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=IssueSeverity.ERROR,
                    message=f"Value {value} is below minimum {schema.min}",
                    expected=f">= {schema.min}",
                    actual=value,
                    rule="min"
                ))
            elif isinstance(value, str) and len(value) < schema.min:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=IssueSeverity.WARNING,
                    message=f"String length {len(value)} is below minimum {schema.min}",
                    expected=f"length >= {schema.min}",
                    actual=len(value),
                    rule="min_length"
                ))

        # Max constraint
        if schema.max is not None:
            if isinstance(value, (int, float)) and value > schema.max:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=IssueSeverity.ERROR,
                    message=f"Value {value} exceeds maximum {schema.max}",
                    expected=f"<= {schema.max}",
                    actual=value,
                    rule="max"
                ))
            elif isinstance(value, str) and len(value) > schema.max:
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=IssueSeverity.WARNING,
                    message=f"String length {len(value)} exceeds maximum {schema.max}",
                    expected=f"length <= {schema.max}",
                    actual=len(value),
                    rule="max_length"
                ))

        # Pattern constraint
        if schema.pattern and isinstance(value, str):
            if not re.match(schema.pattern, value):
                issues.append(ValidationIssue(
                    field=field_name,
                    severity=IssueSeverity.ERROR,
                    message=f"Value does not match pattern {schema.pattern}",
                    expected=f"pattern: {schema.pattern}",
                    actual=value,
                    rule="pattern"
                ))

        # Enum constraint
        if schema.enum and value not in schema.enum:
            issues.append(ValidationIssue(
                field=field_name,
                severity=IssueSeverity.ERROR,
                message=f"Value not in allowed values: {schema.enum}",
                expected=f"one of {schema.enum}",
                actual=value,
                rule="enum"
            ))

        return issues

    def _validate_business_rules(
        self,
        data: Dict[str, Any],
        rules: List[BusinessRule]
    ) -> List[ValidationIssue]:
        """Validate custom business rules"""
        issues: List[ValidationIssue] = []

        for rule in rules:
            field_value = self._get_nested_value(data, rule.field)

            if field_value is None:
                continue  # Skip if field doesn't exist

            violated = False

            if rule.rule_type == "min":
                if isinstance(field_value, (list, str)) and isinstance(rule.value, (int, float)):
                    if len(field_value) < rule.value:
                        violated = True
                elif field_value < rule.value:
                    violated = True
            elif rule.rule_type == "max":
                if isinstance(field_value, (list, str)) and isinstance(rule.value, (int, float)):
                    if len(field_value) > rule.value:
                        violated = True
                elif field_value > rule.value:
                    violated = True
            elif rule.rule_type == "equals" and field_value != rule.value:
                violated = True
            elif rule.rule_type == "not_equals" and field_value == rule.value:
                violated = True
            elif rule.rule_type == "in" and field_value not in rule.value:
                violated = True
            elif rule.rule_type == "not_in" and field_value in rule.value:
                violated = True

            if violated:
                issues.append(ValidationIssue(
                    field=rule.field,
                    severity=rule.severity,
                    message=rule.message,
                    expected=rule.value,
                    actual=field_value,
                    rule=rule.rule_type
                ))

        return issues

    def _get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dict using dot notation"""
        keys = path.split(".")
        value = data
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                return None
        return value

    def _parse_date(self, date_str: str) -> datetime:
        """Parse date from various formats"""
        formats = [
            "%Y-%m-%d",
            "%m/%d/%Y",
            "%d/%m/%Y",
            "%B %d, %Y",
            "%b %d, %Y",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%d %H:%M:%S"
        ]

        for fmt in formats:
            try:
                return datetime.strptime(date_str.strip(), fmt)
            except ValueError:
                continue

        raise ValueError(f"Unable to parse date: {date_str}")

    def _parse_datetime(self, datetime_str: str) -> datetime:
        """Parse datetime from various formats"""
        return self._parse_date(datetime_str)  # Reuse date parser

    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    def _clean_phone(self, phone: str) -> str:
        """Clean phone number (remove formatting)"""
        return re.sub(r'[^\d+]', '', phone)

    def _parse_currency(self, currency_str: str) -> float:
        """Parse currency string to float"""
        # Remove currency symbols and commas
        cleaned = re.sub(r'[$,€£¥]', '', currency_str.strip())
        return float(cleaned)

    def _parse_percentage(self, percent_str: str) -> float:
        """Parse percentage string to float"""
        # Remove % symbol
        cleaned = percent_str.strip().replace('%', '')
        value = float(cleaned)
        # If value is > 1, assume it's already in 0-100 range
        return value
