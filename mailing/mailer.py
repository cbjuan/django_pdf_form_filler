import yagmail
import os
from dotenv import load_dotenv

load_dotenv()
SENDER_EMAIL = os.getenv('SENDER_EMAIL')
SENDER_PSW = os.getenv('SENDER_PSW')

yag = yagmail.SMTP(SENDER_EMAIL, SENDER_PSW)


def send_mail(dest, subject, pdfile):
    yag.send(dest, subject, pdfile)
