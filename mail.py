import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import SMTP_HOST, SMTP_PORT, SMTP_PASSWORD, SMTP_USER


def send_email(receiver: str, body: str, order_id: str = None, filename: str = None):
    """
    Отправляет пользователю `receiver` письмо по заказу `order_id` с приложенным файлом `filename`

    Вы можете изменить логику работы данной функции
    """
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(SMTP_USER, SMTP_PASSWORD)

        email = MIMEMultipart()

        email['Subject'] = f'Изображения. Заказ №{order_id}' if filename else 'Еженедельная рассылка!'
        email['From'] = SMTP_USER
        email['To'] = receiver
        email['Bcc'] = receiver

        email.attach(MIMEText(body, "plain"))

        if filename:
            with open(filename, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())

            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename={filename}'
            )
            email.attach(part)

        text = email.as_string()

        server.sendmail(SMTP_USER, receiver, text)
