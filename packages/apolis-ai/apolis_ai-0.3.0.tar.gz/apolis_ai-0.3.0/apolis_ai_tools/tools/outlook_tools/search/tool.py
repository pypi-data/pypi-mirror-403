from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional, Type
import json
from apolis_ai_tools.cores.outlook_core.client import fetch_emails

class OutlookSearchInput(BaseModel):
    """Input schema for Outlook Search Tool."""
    query: Optional[str] = Field(
        "ALL", 
        description="IMAP search query (e.g., 'UNSEEN', 'ALL', 'FROM \"...\"'). Defaults to 'ALL'."
    )
    limit: int = Field(10, description="Max emails to fetch.")

class OutlookSearchTool(BaseTool):
    name: str = "outlook_search_emails"
    description: str = "Search and fetch emails from Outlook/Office365 user account."
    args_schema: Type[BaseModel] = OutlookSearchInput

    def _run(self, query: str = "ALL", limit: int = 10) -> str:
        try:
            results = fetch_emails(limit=limit, query=query)
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
