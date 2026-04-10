import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465

def send_alert_email(to_email, product_name, platform, current_price, target_price):
    email_user = os.getenv('EMAIL_USER')
    email_pass = os.getenv('EMAIL_PASS')
    
    if not to_email:
        return
        
    if not email_user or not email_pass:
        print(f"\n[MAILER MOCK] ✨ Price Drop Alert! {product_name} on {platform} is now ₹{current_price} (Target was ₹{target_price}) -> {to_email}")
        print("[MAILER MOCK] (Set EMAIL_USER and EMAIL_PASS in .env to send real emails via Gmail)")
        return
        
    msg = EmailMessage()
    msg['Subject'] = f"🚨 Price Drop Alert: {product_name}!"
    msg['From'] = f"SmartCart AI <{email_user}>"
    msg['To'] = to_email
    
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; background-color: #f4f4f5; padding: 20px;">
        <div style="max-width: 600px; margin: 0 auto; background: white; padding: 30px; border-radius: 10px; border-top: 5px solid #1a8a4a; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">
          <h2 style="color: #0d0d0d; margin-top: 0;">Great news!</h2>
          <p style="color: #383838; font-size: 16px; line-height: 1.5;">
            The price for <strong>{product_name}</strong> on <strong>{platform.upper()}</strong> just dropped to your target!
          </p>
          <div style="background-color: #edfaf3; padding: 20px; border-radius: 8px; margin: 20px 0; border: 1.5px solid #a0e0b8; text-align: center;">
            <p style="margin: 0; color: #1a8a4a; font-size: 14px; text-transform: uppercase; font-weight: bold; letter-spacing: 1px;">Current Price</p>
            <p style="margin: 10px 0 0 0; color: #1a8a4a; font-size: 32px; font-weight: 900;">₹{current_price}</p>
            <p style="margin: 10px 0 0 0; color: #757575; font-size: 12px;">(Your goal was ₹{target_price})</p>
          </div>
          <p style="color: #757575; font-size: 14px;">Log in to your SmartCart dashboard to grab it before the price changes again!</p>
        </div>
      </body>
    </html>
    """
    msg.set_content(f"Price for {product_name} dropped to {current_price} on {platform}.")
    msg.add_alternative(html_content, subtype='html')
    
    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(email_user, email_pass)
            server.send_message(msg)
        print(f"[MAILER] Successfully sent actual alert email to {to_email}")
    except Exception as e:
        print(f"[MAILER ERROR] Failed to send email to {to_email}: {str(e)}")
