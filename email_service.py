import smtplib
from typing import Type

from email.message import EmailMessage
from settings import Settings


settings: Settings = Settings()


SENDER: str = "ivand200@gmail.com"


def email_service(content: str, client_email: str) -> dict:
    """
    Send email via gmail
    """
    msg = EmailMessage()
    msg.set_content(content)
    msg["Subject"] = "Ivan"
    msg["From"] = SENDER
    msg["To"] = client_email

    with smtplib.SMTP("smtp.gmail.com", 587) as session:
        session.starttls()
        session.login(SENDER, settings.email_code)
        session.send_message(msg)
    return {"email": client_email, "status": "sended"}
