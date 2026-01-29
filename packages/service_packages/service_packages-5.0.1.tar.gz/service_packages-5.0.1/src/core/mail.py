from email.message import EmailMessage
import smtplib

from loguru import logger

from .settings import MailSettings, settings


class MailClient:
    def __init__(self, config: MailSettings, debug: bool = False):
        self.settings = config
        self.debug = debug

    def send(self, recipients: list[str], subject: str, body: str):
        if self.debug:
            logger.info(
                "Emulate sending email to {} with subject '{}' and body '{}' in debug mode",
                recipients,
                subject,
                body,
            )
            return

        msg = EmailMessage()
        msg.set_content(body)
        server = smtplib.SMTP(self.settings.host, self.settings.port, timeout=5)
        server.starttls()
        server.login(self.settings.login, self.settings.password)

        msg = EmailMessage()
        msg["Subject"] = subject
        msg.set_content(body)
        msg["From"] = self.settings.login

        for recipient in recipients:
            msg["To"] = recipient
            server.send_message(msg)

        server.quit()


async def provide_mail_client():
    return MailClient(settings.mail_config, settings.debug)
