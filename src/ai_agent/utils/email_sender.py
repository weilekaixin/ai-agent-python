import logging
import smtplib
from email.mime.text import MIMEText

from ai_agent.config.settings import settings

logger = logging.getLogger(__name__)

_sender: "EmailSender | None" = None


class EmailSender:
    """SMTP 邮件发送器"""

    def __init__(self):
        self.host = settings.smtp_host
        self.port = settings.smtp_port
        self.username = settings.smtp_username
        self.password = settings.smtp_password

    def send(self, to: str, subject: str, body: str) -> str:
        """发送邮件"""
        if not self.host or not self.username:
            raise RuntimeError("SMTP 未配置，请在 .env 中设置 smtp_host / smtp_username / smtp_password")

        msg = MIMEText(body, "plain", "utf-8")
        msg["Subject"] = subject
        msg["From"] = self.username
        msg["To"] = to

        if self.port == 465:
            server = smtplib.SMTP_SSL(self.host, self.port, timeout=10)
        else:
            server = smtplib.SMTP(self.host, self.port, timeout=10)
            server.starttls()

        with server:
            server.login(self.username, self.password)
            server.send_message(msg)

        logger.info("邮件已发送: to=%s, subject=%s", to, subject)
        return f"邮件已发送给 {to}"


def send_email(to: str, subject: str, body: str) -> str:
    """便捷函数：发邮件（内部维护单例）"""
    global _sender
    if _sender is None:
        _sender = EmailSender()
    return _sender.send(to, subject, body)
