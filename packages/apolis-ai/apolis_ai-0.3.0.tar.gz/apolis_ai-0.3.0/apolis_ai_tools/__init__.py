"""
Apolis AI Tools Package
Unified entry point for Tools, Cores, and Intelligence Assets.
"""

# Intelligence (MLCore) Registry
from apolis_ai_tools.mlcore import register_model, get_model_wrapper

# Gmail Tools
from apolis_ai_tools.tools.gmail_tools import (
    GmailSendTool,
    GmailSearchTool,
    GmailDraftTool,
)

# Outlook Tools
from apolis_ai_tools.tools.outlook_tools import (
    OutlookSendTool,
    OutlookSearchTool,
)

# Document Parser
from apolis_ai_tools.tools.doc_parser.tool import parse_document

# Validation Tool
from apolis_ai_tools.tools.validation import ValidateExtractionTool

__all__ = [
    "register_model",
    "get_model_wrapper",
    "GmailSendTool",
    "GmailSearchTool",
    "GmailDraftTool",
    "OutlookSendTool",
    "OutlookSearchTool",
    "parse_document",
    "ValidateExtractionTool",
]
