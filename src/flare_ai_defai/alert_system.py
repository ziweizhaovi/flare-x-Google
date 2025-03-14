import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict
import asyncio

class AlertSystem:
    def __init__(self, gmail_user: str, gmail_password: str, recipient_email: str):
        """
        Initialize email alert system
        Args:
            gmail_user: Gmail address to send from
            gmail_password: App-specific password for Gmail
            recipient_email: Email address to send alerts to
        """
        self.gmail_user = gmail_user
        self.gmail_password = gmail_password
        self.recipient_email = recipient_email

    async def send_alert(self, analysis: Dict):
        """
        Send formatted alert via email
        """
        subject = "🚨 DeFi Liquidity Alert"
        
        body = f"""
DeFi Liquidity Alert System

Pool: {analysis['event_data']['token0']}/{analysis['event_data']['token1']}
Change: {analysis['event_data']['change_percentage']:.2f}%

AI Analysis:
{analysis['ai_analysis']}

Timestamp: {analysis['timestamp']}
        """

        msg = MIMEMultipart()
        msg['From'] = self.gmail_user
        msg['To'] = self.recipient_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        try:
            server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            server.login(self.gmail_user, self.gmail_password)
            server.send_message(msg)
            server.close()
            print(f"Email alert sent successfully to {self.recipient_email}")
        except Exception as e:
            print(f"Failed to send email alert: {e}") 