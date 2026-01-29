from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import json
from apolis_ai_tools.cores.email_core.client import search_gmail_messages

class GmailSearchInput(BaseModel):
    """Input schema for Gmail Search Tool."""
    query: Optional[str] = Field(
        None,
        description="IMAP search query (e.g., 'UNSEEN', 'ALL'). Defaults to 'UNSEEN'."
    )
    limit: int = Field(10, description="Max emails to fetch.")

class GmailSearchTool(BaseTool):
    name: str = "search_emails"
    description: str = "Search and fetch emails from Gmail using IMAP."
    args_schema: Type[BaseModel] = GmailSearchInput

    def _run(self, query: Optional[str] = None, limit: int = 10) -> str:
        try:
            results = search_gmail_messages(query, limit)
            return json.dumps({
                "status": "ok",
                "message": f"Fetched {len(results)} emails.",
                "emails": results
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error searching emails: {str(e)}",
                "emails": []
            }, indent=2)