import os
import base64
import asyncio
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition

from app.config import settings
from app.logger import logger


async def send_email(subject: str, html_content: str, to_email: str, attachments: list = None):
    try:
        if not settings.SENDGRID_API_KEY:
            logger.warning("SENDGRID_API_KEY not set; skipping email send.")
            return

        from_email = settings.DEFAULT_EMAIL_SENDER

        message = Mail(
            from_email=(from_email, "FP&A Platform"),
            to_emails=to_email,
            subject=subject,
            html_content=html_content
        )

        if attachments:
            for file_path in attachments:
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        encoded = base64.b64encode(f.read()).decode()
                        attachment = Attachment(
                            FileContent(encoded),
                            FileName(os.path.basename(file_path)),
                            FileType("application/pdf"),
                            Disposition("attachment")
                        )
                        message.add_attachment(attachment)

        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)

        response = await asyncio.to_thread(sg.send, message)

        print("STATUS:", response.status_code)
        print("BODY:", response.body)

    except Exception as e:
        logger.exception(f"send_email failed: {e}")