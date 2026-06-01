import os
import requests
from dotenv import load_dotenv

load_dotenv()  # load MAILGUN_* vars

MAILGUN_DOMAIN = os.getenv("MAILGUN_DOMAIN")
MAILGUN_API_KEY = os.getenv("MAILGUN_API_KEY")
MAILGUN_FROM_EMAIL = os.getenv("MAILGUN_FROM_EMAIL")

def send_verification_email(to_email: str, name: str, code: str):
    """
    Send a verification email with the 6-digit code.
    """
    if not all([MAILGUN_DOMAIN, MAILGUN_API_KEY, MAILGUN_FROM_EMAIL]):
        raise ValueError("Mailgun configuration missing in environment variables.")

    response = requests.post(
        f"https://api.mailgun.net/v3/{MAILGUN_DOMAIN}/messages",
        auth=("api", MAILGUN_API_KEY),
        data={
            "from": f"LocaLeaks <{MAILGUN_FROM_EMAIL}>",
            "to": [to_email],
            "subject": "Verify your LocaLeaks account",
            "text": f"Hello {name},\n\nYour LocaLeaks verification code is: {code}\n\nThis code expires in 15 minutes.\n\n- The LocaLeaks Team",
            "html": f"""
                <html>
                    <body>
                        <h2>Hello {name},</h2>
                        <p>Your LocaLeaks verification code is:</p>
                        <h1 style="color:#2d89ef;">{code}</h1>
                        <p>This code expires in 15 minutes.</p>
                        <br>
                        <p>– The LocaLeaks Team</p>
                    </body>
                </html>
            """,
        },
    )

    return response.status_code, response.text