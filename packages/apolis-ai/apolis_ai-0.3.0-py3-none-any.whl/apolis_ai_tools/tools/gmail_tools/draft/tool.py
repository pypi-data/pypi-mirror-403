from crewai.tools import BaseTool
from typing import Any
import json
from apolis_ai_tools.cores.email_core.client import create_gmail_draft

class GmailDraftTool(BaseTool):
    name: str = "create_email_draft"
    description: str = "Create a draft email in Gmail using IMAP."

    def _run(self, raw_args: Any) -> str:
        # Normalize input
        if isinstance(raw_args, str):
            try:
                raw_args = json.loads(raw_args)
            except Exception:
                return "Invalid tool input: expected JSON object"

        if not isinstance(raw_args, dict):
            return "Invalid tool input: expected dictionary"

        to_emails = raw_args.get("to_emails")
        subject = raw_args.get("subject")
        body = raw_args.get("body")
        is_html = raw_args.get("is_html", False)
        reply_to_message_id = raw_args.get("reply_to_message_id")

        if not to_emails or not subject or not body:
            return "Missing required fields: to_emails, subject, body"

        recipients = (
            to_emails if isinstance(to_emails, list)
            else [e.strip() for e in to_emails.split(",") if e.strip()]
        )

        try:
            msg = create_gmail_draft(
                recipients,
                subject,
                body,
                is_html,
                reply_to_message_id
            )
            return json.dumps({"status": "ok", "message": msg}, indent=2)
        except Exception as e:
            return json.dumps({"status": "error", "message": str(e)}, indent=2)
