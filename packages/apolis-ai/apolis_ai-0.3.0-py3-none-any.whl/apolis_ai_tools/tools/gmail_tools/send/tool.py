from crewai.tools import BaseTool
from typing import Any, Optional, List
import json
import re
from apolis_ai_tools.cores.email_core.client import send_gmail_message

class GmailSendTool(BaseTool):
    name: str = "send_email"
    description: str = "Send emails using Gmail SMTP."

    def _run(self, raw_args: Any) -> str:
        # 🔒 Normalize input (CrewAI may pass stringified JSON)
        if isinstance(raw_args, str):
            try:
                raw_args = json.loads(raw_args)
            except Exception:
                return "Invalid tool input: expected JSON object"

        if not isinstance(raw_args, dict):
            return "Invalid tool input: expected dictionary"

        # Required fields
        to_emails = raw_args.get("to_emails")
        subject = raw_args.get("subject")
        body = raw_args.get("body")

        # Optional fields
        is_html = raw_args.get("is_html", False)
        attachments = raw_args.get("attachments")

        if not to_emails or not subject or not body:
            return "Missing required fields: to_emails, subject, body"

        # Normalize recipients
        if isinstance(to_emails, list):
            recipients = to_emails
        else:
            recipients = [e.strip() for e in to_emails.split(",") if e.strip()]

        # Attachment auto-extraction from body (robustness)
        marker_pattern = r'\[\[ATTACHMENT:\s*(.*?)\]\]'
        markers = re.findall(marker_pattern, body)
        if markers:
            attachments = attachments or []
            for path in markers:
                attachments.append(path.strip())
            body = re.sub(marker_pattern, "", body).strip()

        try:
            msg = send_gmail_message(
                recipients,
                subject,
                body,
                is_html,
                attachments
            )
            return json.dumps(
                {"status": "ok", "message": msg},
                indent=2
            )
        except Exception as e:
            return json.dumps(
                {"status": "error", "message": str(e)},
                indent=2
            )
