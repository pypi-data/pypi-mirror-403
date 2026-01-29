import os
import imaplib
import smtplib
import email
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from typing import List, Dict, Any, Optional, Union
from .utils import decode_header_value, get_email_body, is_relevant_for_namespaces

def search_gmail_messages(query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Core logic for searching Gmail messages.
    - query: IMAP search query (default 'UNSEEN')
    - limit: max emails to fetch
    - namespaces: Enforced via GMAIL_NAMESPACES env var.
    """
    imap_server = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
    email_user = os.getenv("GMAIL_EMAIL")
    email_pass = os.getenv("GMAIL_PASSWORD")

    if not email_user or not email_pass:
        raise ValueError("GMAIL_EMAIL or GMAIL_PASSWORD not set in environment.")

    # Always strictly check env for namespaces
    namespacestr = os.getenv("GMAIL_NAMESPACES", "")
    namespaces = [n.strip() for n in namespacestr.split(",") if n.strip()]

    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_user, email_pass)
    mail.select("inbox")

    try:
        search_query = query if query else "UNSEEN"
        status, messages = mail.search(None, search_query)

        if status != "OK":
            return []

        email_ids = messages[0].split()
        if not email_ids:
            return []

        # Get latest
        email_ids = email_ids[-limit:]
        results: List[Dict[str, Any]] = []

        for e_id in email_ids:
            try:
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject = decode_header_value(msg.get("Subject"))
                        from_ = decode_header_value(msg.get("From"))
                        date = decode_header_value(msg.get("Date"))
                        message_id = msg.get("Message-ID", "").strip()
                        body = get_email_body(msg)
                        
                        combined_text = f"{subject} {body}"
                        is_relevant = is_relevant_for_namespaces(combined_text, namespaces)

                        # Logic: If namespaces exist, we ONLY return relevant ones.
                        # If namespaces is empty, we return everything (is_relevant check returns True for empty list, 
                        # but let's be explicit).
                        
                        # Wait, helper returns True if list is empty?
                        # Let's check helper: "if not namespaces: return True". Yes.
                        
                        if is_relevant:
                            results.append({
                                "id": e_id.decode(),
                                "message_id": message_id,
                                "from": from_,
                                "subject": subject,
                                "date": date,
                                "body": body,
                                "is_relevant": is_relevant, # For debugging
                            })
            except Exception as e:
                print(f"Error parsing email {e_id}: {e}")
                continue
        
        return results

    finally:
        try:
            mail.close()
            mail.logout()
        except:
            pass


def create_gmail_draft(to_emails: List[str], subject: str, body: str, is_html: bool = False, reply_to_message_id: Optional[str] = None) -> str:
    """
    Core logic for creating a Gmail draft.
    """
    imap_server = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
    email_user = os.getenv("GMAIL_EMAIL")
    email_pass = os.getenv("GMAIL_PASSWORD")

    if not email_user or not email_pass:
        raise ValueError("Credentials missing.")

    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject
    msg["Date"] = email.utils.formatdate(localtime=True)
    
    if reply_to_message_id:
        msg["In-Reply-To"] = reply_to_message_id
        msg["References"] = reply_to_message_id
    
    if is_html:
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "plain"))

    mail = imaplib.IMAP4_SSL(imap_server)
    mail.login(email_user, email_pass)
    
    target_folder = '[Gmail]/Drafts'
    try:
        mail.select(target_folder)
    except:
        target_folder = 'Drafts'
        mail.select(target_folder)

    raw_email = msg.as_bytes()
    mail.append(target_folder, '(\\Seen \\Draft)', imaplib.Time2Internaldate(time.time()), raw_email)

    mail.close()
    mail.logout()
    return f"Draft saved successfully for {', '.join(to_emails)}"


def send_gmail_message(to_emails: List[str], subject: str, body: str, is_html: bool = False, attachments: Optional[List[str]] = None) -> str:
    """
    Core logic for sending an email via SMTP.
    """
    smtp_server = os.getenv("GMAIL_SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("GMAIL_SMTP_PORT", "587"))
    email_user = os.getenv("GMAIL_EMAIL")
    email_pass = os.getenv("GMAIL_PASSWORD")

    if not email_user or not email_pass:
        raise ValueError("GMAIL_EMAIL or GMAIL_PASSWORD not set in environment.")

    msg = MIMEMultipart()
    msg["From"] = email_user
    msg["To"] = ", ".join(to_emails)
    msg["Subject"] = subject

    if is_html:
        msg.attach(MIMEText(body, "html"))
    else:
        msg.attach(MIMEText(body, "plain"))

    if attachments:
        for file_path in attachments:
            try:
                # Clean up path
                file_path = file_path.strip().strip('"').strip("'")
                with open(file_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(file_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                msg.attach(part)
            except Exception as e:
                print(f"Failed to attach {file_path}: {e}")

    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    server.login(email_user, email_pass)
    server.send_message(msg)
    server.quit()
    
    return f"Email sent successfully to {', '.join(to_emails)}"