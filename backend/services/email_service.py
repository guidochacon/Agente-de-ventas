import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from config import settings


class EmailService:
    async def send_quote(self, to_email: str, to_name: str, pdf_path: str, quote_id: str) -> bool:
        """Send a quote PDF via email."""
        try:
            if settings.sendgrid_api_key:
                return await self._send_via_sendgrid(to_email, to_name, pdf_path, quote_id)
            else:
                # Log that email is not configured
                print(f"[EMAIL] Quote {quote_id} would be sent to {to_email} (email not configured)")
                return True
        except Exception as e:
            print(f"[EMAIL] Error sending quote: {e}")
            return False

    async def _send_via_sendgrid(self, to_email: str, to_name: str, pdf_path: str, quote_id: str) -> bool:
        try:
            import sendgrid
            from sendgrid.helpers.mail import Mail, Attachment, FileContent, FileName, FileType, Disposition
            import base64

            sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)

            with open(pdf_path, "rb") as f:
                pdf_data = base64.b64encode(f.read()).decode()

            message = Mail(
                from_email=(settings.from_email, settings.from_name),
                to_emails=to_email,
                subject=f"Tu cotización de {settings.agent_business_name}",
                html_content=f"""
                <p>Hola {to_name},</p>
                <p>Adjunto encontrás la cotización que preparamos para vos.</p>
                <p>Si tenés alguna pregunta, no dudes en responder este email.</p>
                <br>
                <p>Saludos,<br>{settings.agent_name}<br>{settings.agent_business_name}</p>
                """,
            )

            attachment = Attachment(
                FileContent(pdf_data),
                FileName(f"cotizacion_{quote_id[:8]}.pdf"),
                FileType("application/pdf"),
                Disposition("attachment"),
            )
            message.attachment = attachment

            sg.send(message)
            return True
        except Exception as e:
            print(f"[SENDGRID] Error: {e}")
            return False
