import yagmail
import os
from dotenv import load_dotenv

load_dotenv()
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PSW = os.getenv('SENDER_PSW')

yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PSW)


def send_mail(dest, subject, name, pdfile, conference):
    mail_body = f"Dear {name},\n\n Please find attached your {conference} certificate.\n\n Kind regards,\n Organization Committee"
    yag.send(to=dest, subject=subject, contents=mail_body, attachments=pdfile)
