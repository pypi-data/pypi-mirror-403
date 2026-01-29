import email
from email.header import decode_header
from typing import Optional

def decode_header_value(value: Optional[str]) -> str:
    """Safely decode MIME-encoded email headers like Subject."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded_parts = []
    for part, enc in parts:
        if isinstance(part, bytes):
            try:
                decoded_parts.append(part.decode(enc or "utf-8", errors="ignore"))
            except Exception:
                decoded_parts.append(part.decode("utf-8", errors="ignore"))
        else:
            decoded_parts.append(part)
    return "".join(decoded_parts).strip()


def get_email_body(msg: email.message.Message) -> str:
    """
    Extract the plain-text body from an email.message.Message.
    Prefers text/plain over text/html, ignores attachments.
    """
    body = ""
    if msg.is_multipart():
        for part in msg.walk():
            content_type = part.get_content_type()
            content_disposition = str(part.get("Content-Disposition") or "")
            if content_type == "text/plain" and "attachment" not in content_disposition:
                try:
                    body = part.get_payload(decode=True)
                    if isinstance(body, bytes):
                        body = body.decode(part.get_content_charset() or "utf-8", errors="ignore")
                    return body.strip()
                except Exception:
                    continue
    else:
        try:
            body = msg.get_payload(decode=True)
            if isinstance(body, bytes):
                body = body.decode(msg.get_content_charset() or "utf-8", errors="ignore")
        except Exception:
            body = msg.get_payload()
    return (body or "").strip()

def is_relevant_for_namespaces(text: str, namespaces: list[str]) -> bool:
    """
    Check if the text contains any of the provided namespaces (keywords).
    Case-insensitive.
    """
    if not namespaces:
        return True
    
    text_lower = text.lower()
    for ns in namespaces:
        if ns.strip().lower() in text_lower:
            return True
    return False