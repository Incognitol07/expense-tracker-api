# app/utils/notifications.py

import requests
from fastapi import HTTPException
from app.config import settings

# Send an email notification using Mailgun
def send_email_notification(to_email: str, subject: str, body: str):
    try:
        # Define Mailgun endpoint and authentication
        mailgun_url = f"{settings.MAILGUN_API_BASE_URL}/{settings.MAILGUN_DOMAIN}/messages"
        auth = ("api", settings.MAILGUN_API_KEY)

        # Define the payload
        data = {
            "from": f"Expense Tracker <mailgun@{settings.MAILGUN_DOMAIN}>",
            "to": to_email,
            "subject": subject,
            "text": body
        }

        # Send the email request to Mailgun API
        response = requests.post(mailgun_url, auth=auth, data=data)

        # Check for successful response
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Failed to send email notification")
        
        print(f"Email sent to {to_email}")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error sending email: {str(e)}")



# SMS configuration (assuming an SMS API, e.g., Twilio)
# SMS_API_URL = settings.SMS_API_URL  # Use settings from the config
# SMS_API_KEY = settings.SMS_API_KEY  # Use settings from the config

# Send an SMS notification
# def send_sms_notification(phone_number: str, message: str):
#     try:
#         payload = {
#             "to": phone_number,
#             "message": message,
#             "api_key": SMS_API_KEY
#         }
#         response = requests.post(SMS_API_URL, json=payload)

#         if response.status_code != 200:
#             raise HTTPException(status_code=500, detail="Failed to send SMS notification")
#         print(f"SMS sent to {phone_number}")
    
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=f"Error sending SMS: {str(e)}")
