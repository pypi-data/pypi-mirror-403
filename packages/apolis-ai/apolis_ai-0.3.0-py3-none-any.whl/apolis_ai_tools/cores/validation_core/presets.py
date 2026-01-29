"""Pre-built validation schemas for common use cases"""

from .domain import FieldType, FieldSchema, ValidationSchema, BusinessRule, IssueSeverity


def get_hotel_contract_schema() -> ValidationSchema:
    """
    Pre-built validation schema for hotel contract extraction.

    Expected structure:
    {
        "organization": "Marriott Downtown",
        "contact": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1-234-567-8900"
        },
        "event": {
            "name": "Annual Conference 2025",
            "start_date": "2025-06-15",
            "end_date": "2025-06-18",
            "guest_rooms": 150,
            "estimated_revenue": 125000.00
        },
        "deposits": [
            {
                "amount": 24070.00,
                "percentage": 25,
                "due_date": "2025-03-15",
                "description": "First deposit"
            }
        ],
        "total_contract_value": 96280.00
    }
    """
    return ValidationSchema(
        fields={
            "organization": FieldSchema(
                type=FieldType.STRING,
                required=True,
                min=2,
                description="Hotel or organization name"
            ),
            "contact": FieldSchema(
                type=FieldType.OBJECT,
                required=True,
                properties={
                    "name": FieldSchema(
                        type=FieldType.STRING,
                        required=True,
                        min=2
                    ),
                    "email": FieldSchema(
                        type=FieldType.EMAIL,
                        required=True
                    ),
                    "phone": FieldSchema(
                        type=FieldType.PHONE,
                        required=False
                    )
                }
            ),
            "event": FieldSchema(
                type=FieldType.OBJECT,
                required=True,
                properties={
                    "name": FieldSchema(
                        type=FieldType.STRING,
                        required=True
                    ),
                    "start_date": FieldSchema(
                        type=FieldType.DATE,
                        required=True
                    ),
                    "end_date": FieldSchema(
                        type=FieldType.DATE,
                        required=True
                    ),
                    "guest_rooms": FieldSchema(
                        type=FieldType.INTEGER,
                        required=False,
                        min=1
                    ),
                    "estimated_revenue": FieldSchema(
                        type=FieldType.CURRENCY,
                        required=False,
                        min=0
                    )
                }
            ),
            "deposits": FieldSchema(
                type=FieldType.ARRAY,
                required=True,
                items=FieldSchema(
                    type=FieldType.OBJECT,
                    properties={
                        "amount": FieldSchema(
                            type=FieldType.CURRENCY,
                            required=True,
                            min=0.01,
                            description="Deposit amount in currency"
                        ),
                        "percentage": FieldSchema(
                            type=FieldType.PERCENTAGE,
                            required=False,
                            min=0,
                            max=100,
                            description="Percentage of total contract value"
                        ),
                        "due_date": FieldSchema(
                            type=FieldType.DATE,
                            required=True,
                            description="Payment due date"
                        ),
                        "description": FieldSchema(
                            type=FieldType.STRING,
                            required=False
                        )
                    }
                )
            ),
            "total_contract_value": FieldSchema(
                type=FieldType.CURRENCY,
                required=False,
                min=0,
                description="Total contract value"
            ),
            "hotel_property": FieldSchema(
                type=FieldType.STRING,
                required=False,
                enum=["ROH", "TGH", "TSH"],
                description="Hotel property code"
            ),
            "signing_date": FieldSchema(
                type=FieldType.DATE,
                required=False,
                description="Contract signing date"
            )
        },
        rules=[
            BusinessRule(
                field="deposits",
                rule_type="min",
                value=1,
                message="At least one deposit is required",
                severity=IssueSeverity.ERROR
            )
        ],
        strict=False
    )


def get_invoice_schema() -> ValidationSchema:
    """
    Pre-built validation schema for invoice extraction.

    Expected structure:
    {
        "invoice_number": "INV-2025-001",
        "vendor": "Acme Corp",
        "date": "2025-01-15",
        "due_date": "2025-02-15",
        "items": [
            {
                "description": "Product A",
                "quantity": 10,
                "unit_price": 50.00,
                "total": 500.00
            }
        ],
        "subtotal": 500.00,
        "tax": 50.00,
        "total": 550.00
    }
    """
    return ValidationSchema(
        fields={
            "invoice_number": FieldSchema(
                type=FieldType.STRING,
                required=True,
                min=1
            ),
            "vendor": FieldSchema(
                type=FieldType.STRING,
                required=True,
                min=2
            ),
            "date": FieldSchema(
                type=FieldType.DATE,
                required=True
            ),
            "due_date": FieldSchema(
                type=FieldType.DATE,
                required=False
            ),
            "items": FieldSchema(
                type=FieldType.ARRAY,
                required=True,
                items=FieldSchema(
                    type=FieldType.OBJECT,
                    properties={
                        "description": FieldSchema(
                            type=FieldType.STRING,
                            required=True
                        ),
                        "quantity": FieldSchema(
                            type=FieldType.NUMBER,
                            required=True,
                            min=0
                        ),
                        "unit_price": FieldSchema(
                            type=FieldType.CURRENCY,
                            required=True,
                            min=0
                        ),
                        "total": FieldSchema(
                            type=FieldType.CURRENCY,
                            required=True,
                            min=0
                        )
                    }
                )
            ),
            "subtotal": FieldSchema(
                type=FieldType.CURRENCY,
                required=True,
                min=0
            ),
            "tax": FieldSchema(
                type=FieldType.CURRENCY,
                required=False,
                min=0
            ),
            "total": FieldSchema(
                type=FieldType.CURRENCY,
                required=True,
                min=0
            )
        },
        strict=False
    )


def get_contact_schema() -> ValidationSchema:
    """
    Pre-built validation schema for contact information extraction.

    Expected structure:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "phone": "+1-234-567-8900",
        "company": "Acme Corp",
        "title": "Sales Manager"
    }
    """
    return ValidationSchema(
        fields={
            "name": FieldSchema(
                type=FieldType.STRING,
                required=True,
                min=2
            ),
            "email": FieldSchema(
                type=FieldType.EMAIL,
                required=True
            ),
            "phone": FieldSchema(
                type=FieldType.PHONE,
                required=False
            ),
            "company": FieldSchema(
                type=FieldType.STRING,
                required=False
            ),
            "title": FieldSchema(
                type=FieldType.STRING,
                required=False
            )
        },
        strict=False
    )
