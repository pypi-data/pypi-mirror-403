from crewai.tools import BaseTool
from typing import Any, Optional, Dict
import json
from apolis_ai_tools.cores.validation_core import (
    ExtractionValidator,
    ValidationSchema,
    FieldSchema,
    FieldType,
    BusinessRule,
    IssueSeverity,
    get_hotel_contract_schema,
    get_invoice_schema,
    get_contact_schema
)


class ValidateExtractionTool(BaseTool):
    name: str = "validate_extraction"
    description: str = """Validate extracted data against a schema with automatic confidence scoring.

Supports:
- Type validation (string, number, date, email, currency, etc.)
- Required field checking
- Range constraints (min/max)
- Business rule validation
- Automatic confidence calculation

Use presets for common schemas: "hotel_contract", "invoice", "contact"
Or provide custom schema with fields and rules.
"""

    def _run(self, raw_args: Any) -> str:
        """
        Validate extracted data.

        Args:
            raw_args: Dictionary with:
                - extracted_data: Dict of data to validate
                - schema: Dict or preset name ("hotel_contract", "invoice", "contact")
                - base_confidence: Optional float (0.0-1.0)
                - rules: Optional list of business rules

        Returns:
            JSON string with validation result
        """
        # Normalize input (CrewAI may pass stringified JSON)
        if isinstance(raw_args, str):
            try:
                raw_args = json.loads(raw_args)
            except Exception:
                return json.dumps({
                    "status": "error",
                    "message": "Invalid tool input: expected JSON object"
                }, indent=2)

        if not isinstance(raw_args, dict):
            return json.dumps({
                "status": "error",
                "message": "Invalid tool input: expected dictionary"
            }, indent=2)

        # Extract parameters
        extracted_data = raw_args.get("extracted_data")
        schema_input = raw_args.get("schema")
        base_confidence = raw_args.get("base_confidence", 1.0)
        custom_rules = raw_args.get("rules", [])

        # Validate required parameters
        if not extracted_data:
            return json.dumps({
                "status": "error",
                "message": "Missing required parameter: extracted_data"
            }, indent=2)

        if not schema_input:
            return json.dumps({
                "status": "error",
                "message": "Missing required parameter: schema"
            }, indent=2)

        try:
            # Load schema (preset or custom)
            if isinstance(schema_input, str):
                schema = self._load_preset_schema(schema_input)
            elif isinstance(schema_input, dict):
                schema = self._parse_custom_schema(schema_input)
            else:
                return json.dumps({
                    "status": "error",
                    "message": "Schema must be a preset name or dictionary"
                }, indent=2)

            # Add custom rules if provided
            if custom_rules:
                parsed_rules = self._parse_business_rules(custom_rules)
                if schema.rules:
                    schema.rules.extend(parsed_rules)
                else:
                    schema.rules = parsed_rules

            # Validate
            validator = ExtractionValidator(base_confidence=base_confidence)
            result = validator.validate(extracted_data, schema)

            # Convert to dict and return
            return json.dumps(result.model_dump(), indent=2, default=str)

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Validation failed: {str(e)}"
            }, indent=2)

    def _load_preset_schema(self, preset_name: str) -> ValidationSchema:
        """Load a pre-built schema"""
        presets = {
            "hotel_contract": get_hotel_contract_schema,
            "invoice": get_invoice_schema,
            "contact": get_contact_schema
        }

        if preset_name not in presets:
            raise ValueError(
                f"Unknown preset '{preset_name}'. "
                f"Available: {', '.join(presets.keys())}"
            )

        return presets[preset_name]()

    def _parse_custom_schema(self, schema_dict: Dict) -> ValidationSchema:
        """Parse custom schema from dictionary"""
        fields = {}

        for field_name, field_config in schema_dict.get("fields", {}).items():
            fields[field_name] = self._parse_field_schema(field_config)

        rules = []
        if "rules" in schema_dict:
            rules = self._parse_business_rules(schema_dict["rules"])

        return ValidationSchema(
            fields=fields,
            rules=rules,
            strict=schema_dict.get("strict", False)
        )

    def _parse_field_schema(self, config: Dict) -> FieldSchema:
        """Parse field schema from config dict"""
        # Parse nested items schema for arrays
        items_schema = None
        if "items" in config:
            items_schema = self._parse_field_schema(config["items"])

        # Parse nested properties for objects
        properties = None
        if "properties" in config:
            properties = {
                name: self._parse_field_schema(prop_config)
                for name, prop_config in config["properties"].items()
            }

        return FieldSchema(
            type=FieldType(config["type"]),
            required=config.get("required", False),
            min=config.get("min"),
            max=config.get("max"),
            pattern=config.get("pattern"),
            items=items_schema,
            properties=properties,
            enum=config.get("enum"),
            description=config.get("description")
        )

    def _parse_business_rules(self, rules_list: list) -> list:
        """Parse business rules from list of dicts"""
        parsed_rules = []

        for rule_dict in rules_list:
            parsed_rules.append(BusinessRule(
                field=rule_dict["field"],
                rule_type=rule_dict["rule_type"],
                value=rule_dict["value"],
                message=rule_dict["message"],
                severity=IssueSeverity(rule_dict.get("severity", "error"))
            ))

        return parsed_rules
