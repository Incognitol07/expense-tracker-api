# app/utils/notifications.py

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import os
from fastapi import HTTPException
from app.config import settings

# Send an email notification
def send_email_notification(to_email: str, subject: str, body: str):
    try:
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = settings.SMTP_USERNAME
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Set up the server using settings
        server = smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT)
        server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        
        # Send the email
        server.sendmail(settings.SMTP_USERNAME, to_email, msg.as_string())
        server.quit()
        print(f"Email sent to {to_email}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")


# SMS configuration (assuming an SMS API, e.g., Twilio)
SMS_API_URL = settings.SMS_API_URL  # Use settings from the config
SMS_API_KEY = settings.SMS_API_KEY  # Use settings from the config

# Send an SMS notification
def send_sms_notification(phone_number: str, message: str):
    try:
        payload = {
            "to": phone_number,
            "message": message,
            "api_key": SMS_API_KEY
        }
        response = requests.post(SMS_API_URL, json=payload)

        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send SMS notification")
        print(f"SMS sent to {phone_number}")
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending SMS: {str(e)}")
