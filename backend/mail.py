import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app

def send_email(subject, body, recipients, html_body=None):
    if not recipients:
        return

    # Use MailHog defaults if environment is not fully configured for production
    mail_host = current_app.config.get("MAIL_HOST") or "localhost"
    mail_port = current_app.config.get("MAIL_PORT") or 1025
    mail_username = current_app.config.get("MAIL_USERNAME")
    mail_password = current_app.config.get("MAIL_PASSWORD")
    mail_sender = current_app.config.get("MAIL_SENDER") or mail_username or "admin@gmail.com"

    # Only turn on dummy fallback if specifically requested, else send through provided server
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = mail_sender
    message["To"] = ", ".join(recipients)
    message.attach(MIMEText(body, "plain"))
    if html_body:
        message.attach(MIMEText(html_body, "html"))

    try:
        with smtplib.SMTP(mail_host, int(mail_port)) as server:
            # If using a legitimate provider like Gmail, use TLS and login
            if mail_username and mail_password:
                server.starttls()
                server.login(mail_username, mail_password)
            
            server.sendmail(mail_sender, recipients, message.as_string())
            print(f"Email successfully sent to {recipients}")
    except Exception as e:
        print(f"\nFailed to send email via SMTP ({mail_host}:{mail_port}). Error: {e}")
        print("\n--- EMAIL FALLBACK ---")
        print("To:", ", ".join(recipients))
        print("Subject:", subject)
        print(body)
        if html_body:
            print(html_body)

if __name__ == "__main__":
    from app import app
    from models import User
    
    with app.app_context():
        print("Fetching all registered users...")
        users = User.query.all()
        
        if not users:
            print("No users found in the database.")
        else:
            recipients = [user.email for user in users]
            print(f"Sending test broadcast to {len(recipients)} users...")
            
            # Send singular emails to each person so they don't see each other's addresses
            for user_email in recipients:
                send_email(
                    subject="System Broadcast message",
                    body="Hello! This is a system broadcast to confirm the mail functionality is working for all registered users.",
                    recipients=[user_email]
                )
            
            print("Finished sending broadcast emails!")