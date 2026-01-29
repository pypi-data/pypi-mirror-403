import imaplib
import smtplib
import email
from email.header import decode_header
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from typing import List, Dict, Any, Optional

def _get_credentials() -> tuple[str, str]:
    username = os.getenv("OUTLOOK_EMAIL")
    password = os.getenv("OUTLOOK_PASSWORD")
    if not username or not password:
        raise ValueError("OUTLOOK_EMAIL and OUTLOOK_PASSWORD environment variables must be set")
    return username, password

def _clean_header(header_value: Any) -> str:
    if not header_value:
        return ""
    decoded_list = decode_header(header_value)
    result = []
    for content, encoding in decoded_list:
        if isinstance(content, bytes):
            if encoding:
                try:
                    result.append(content.decode(encoding))
                except LookupError:
                    result.append(content.decode("utf-8", errors="replace"))
            else:
                result.append(content.decode("utf-8", errors="replace"))
        else:
            result.append(str(content))
    return "".join(result)

def fetch_emails(limit: int = 10, query: str = "ALL") -> List[Dict[str, Any]]:
    # Connect to Outlook IMAP
    username, password = _get_credentials()
    imap_server = "outlook.office365.com"
    mail = None
    results = []

    try:
        mail = imaplib.IMAP4_SSL(imap_server)
        try:
            mail.login(username, password)
        except imaplib.IMAP4.error as e:
            raise e
        mail.select("INBOX")

        status, messages = mail.search(None, query)
        if status != "OK":
            return []

        email_ids = messages[0].split()
        # Get latest N emails
        email_ids = email_ids[-limit:]

        for e_id in reversed(email_ids):
            try:
                _, msg_data = mail.fetch(e_id, "(RFC822)")
                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        message_id = msg.get("Message-ID", "").strip()
                        from_addr = _clean_header(msg.get("From"))
                        subject = _clean_header(msg.get("Subject"))
                        date = msg.get("Date", "")
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))
                                
                                # Ignore attachments
                                if "attachment" in content_disposition:
                                    continue

                                if content_type == "text/plain":
                                    try:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body += payload.decode(errors="replace")
                                    except Exception:
                                        pass
                        else:
                            if msg.get_content_type() == "text/plain":
                                try:
                                    payload = msg.get_payload(decode=True)
                                    if payload:
                                        body = payload.decode(errors="replace")
                                except Exception:
                                    pass

                        results.append({
                            "message_id": message_id,
                            "from": from_addr,
                            "subject": subject,
                            "date": date,
                            "body": body.strip()
                        })
            except Exception as e:
                # Log error but continue fetching other emails
                print(f"Error parsing email {e_id}: {e}")
                continue

    except Exception as e:
        print(f"IMAP Error: {e}")
        raise e
        
    finally:
        if mail:
            try:
                mail.close()
                mail.logout()
            except Exception:
                pass

    return results

def send_email(to_email: str, subject: str, body: str) -> None:
    username, password = _get_credentials()
    smtp_server = "smtp.office365.com"
    smtp_port = 587

    msg = MIMEMultipart()
    msg["From"] = username
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    server = None
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(username, password)
        server.send_message(msg)
    except Exception as e:
        raise Exception(f"Failed to send email: {str(e)}")
    finally:
        if server:
            try:
                server.quit()
            except Exception:
                pass
