import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass

def format_and_dispatch_signals(signals: List[Dict[str, Any]]):
    """
    Formats trading signals and emails them via Gmail SMTP to multiple recipients.
    """
    sender_email = os.environ.get("GMAIL_SENDER")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    
    # Fetch recipients (supporting both single or comma-separated keys)
    recipients_env = os.environ.get("GMAIL_RECIPIENTS") or os.environ.get("GMAIL_RECIPIENT", "")
    recipient_list = [email.strip() for email in recipients_env.split(",") if email.strip()]

    if not all([sender_email, sender_password, recipient_list]):
        print("⚠️ Gmail credentials or recipients missing in .env. Skipping email notification.")
        return

    # 1. Format the Email Body
    email_body = "Trading Bot Morning Report\n"
    email_body += "=" * 30 + "\n\n"

    for sig in signals:
        ticker = sig.get("ticker", "UNKNOWN")
        action = sig.get("action", "HOLD")
        price = sig.get("price", 0.0)
        
        if action == "BUY":
            sl = sig.get("stop_loss", 0.0)
            email_body += f"🟢 BUY {ticker} @ Ksh {price:.2f} (Suggested Stop Loss: {sl:.2f})\n"
        elif action == "SELL":
            email_body += f"🔴 SELL {ticker} @ Ksh {price:.2f} (Trend Reversal/Stop Hit)\n"

    email_body += "\n" + "=" * 30
    email_body += "\nAutomated by Reuel's NSE Trading Bot"

    # 2. Construct the Email Message
    msg = MIMEMultipart()
    msg['From'] = f"NSE Trading Bot <{sender_email}>"
    msg['To'] = ", ".join(recipient_list)  # Display all recipients in header
    msg['Subject'] = f"📈 NSE Trading Alerts: {len(signals)} Action(s) Required"

    msg.attach(MIMEText(email_body, 'plain'))

    # 3. Connect to Gmail and Send to all recipients
    try:
        print(f"📧 Connecting to Gmail SMTP server for {len(recipient_list)} recipient(s)...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
        # sendmail accepts a list of email addresses natively
        server.sendmail(sender_email, recipient_list, text)
        print(f"✅ Email notifications dispatched successfully to: {', '.join(recipient_list)}")
        
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        
    finally:
        try:
            server.quit()
        except:
            pass

# Quick Local Test
if __name__ == "__main__":
    mock_signals = [
        {"ticker": "SCOM", "action": "BUY", "price": 14.50, "stop_loss": 13.80},
        {"ticker": "KCB", "action": "SELL", "price": 29.75}
    ]
    format_and_dispatch_signals(mock_signals)