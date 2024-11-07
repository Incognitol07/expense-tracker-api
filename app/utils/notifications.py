# app/utils/notifications.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from fastapi import HTTPException
from app.config import settings

def send_email_notification(to_email: str, subject: str, body: str):
    try:
        # Set up MIME message
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Set up server connection using Gmail's SMTP server
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)

        # Send the email
        server.sendmail(settings.SMTP_USERNAME, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")
