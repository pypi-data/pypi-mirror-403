from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type
import json
from apolis_ai_tools.cores.outlook_core.client import send_email

class OutlookSendInput(BaseModel):
    """Input schema for Outlook Send Tool."""
    to_email: str = Field(..., description="Recipient email address.")
    subject: str = Field(..., description="Email subject.")
    body: str = Field(..., description="Email body content.")

class OutlookSendTool(BaseTool):
    name: str = "outlook_send_email"
    description: str = "Send an email using Outlook/Office365 SMTP."
    args_schema: Type[BaseModel] = OutlookSendInput

    def _run(self, to_email: str, subject: str, body: str) -> str:
        try:
            send_email(to_email, subject, body)
            return json.dumps({
                "status": "ok",
                "message": f"Email sent successfully to {to_email}"
            }, indent=2)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error sending email: {str(e)}"
            }, indent=2)
