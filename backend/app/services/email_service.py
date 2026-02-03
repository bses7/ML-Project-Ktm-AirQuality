import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

async def send_aqi_alert(aqi_value: float, pm25: float, recipient_email: str):
    """Send email alert when AQI exceeds threshold"""
    
    sender_email = os.getenv("SENDER_EMAIL", "your-email@gmail.com")
    sender_password = os.getenv("EMAIL_PASSWORD", "your-app-password")
    
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = f"High AQI Alert: {int(aqi_value)} - Kathmandu Air Guard"
    
    body = f"""
    <html>
    <body>
        <h2>Air Quality Alert for Kathmandu</h2>
        <p><strong>Current AQI:</strong> {int(aqi_value)} (Unhealthy for Sensitive Groups)</p>
        <p><strong>PM2.5:</strong> {pm25:.1f} µg/m³</p>
        
        <h3>Health Recommendations:</h3>
        <ul>
            <li>Limit prolonged outdoor activities</li>
            <li>Keep windows closed</li>
            <li>Use air purifiers if available</li>
            <li>Wear N95 masks when going outside</li>
        </ul>
        
        <p><em>Stay safe and monitor air quality regularly.</em></p>
        <h3>Swaastha-Ktm Team</h3>
    </body>
    </html>
    """
    
    message.attach(MIMEText(body, "html"))
    
    try:
        await aiosmtplib.send(
            message,
            hostname="smtp.gmail.com",
            port=587,
            start_tls=True,
            username=sender_email,
            password=sender_password,
        )
        print(f"Alert email sent to {recipient_email}")
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False