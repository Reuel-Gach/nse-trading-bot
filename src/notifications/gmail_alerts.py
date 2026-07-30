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
    if not signals:
        print("📭 No trading alerts triggered today. Skipping email notification.")
        return

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
    email_body += "=" * 45 + "\n\n"

    for sig in signals:
        ticker = sig.get("ticker", "UNKNOWN")
        action = sig.get("action", "HOLD")
        reason = sig.get("reason", "No reason provided.")
        
        # Support both 'suggested_stop_loss' (from screen_market_for_entries) and 'stop_loss'
        sl = sig.get("suggested_stop_loss", sig.get("stop_loss", 0.0))
        price = sig.get("price", 0.0)
        
        if action in ["BUY", "INITIAL_BUY", "SCALE_IN"]:
            price_text = f" @ Ksh {price:.2f}" if price > 0 else ""
            email_body += f"🟢 {action}: {ticker}{price_text}\n"
            email_body += f"   ├── Reason: {reason}\n"
            email_body += f"   └── Suggested Stop Loss: Ksh {sl:.2f}\n\n"
            
        elif action in ["SELL", "SELL_STOP_LOSS", "SELL_DEATH_CROSS"]:
            price_text = f" @ Ksh {price:.2f}" if price > 0 else ""
            email_body += f"🔴 {action}: {ticker}{price_text}\n"
            email_body += f"   └── Reason: {reason}\n\n"

    email_body += "=" * 45
    email_body += "\nAutomated by Reuel's NSE Trading Bot"

    # 2. Construct the Email Message
    msg = MIMEMultipart()
    msg['From'] = f"NSE Trading Bot <{sender_email}>"
    msg['To'] = ", ".join(recipient_list)
    msg['Subject'] = f"📈 NSE Trading Alerts: {len(signals)} Action(s) Required"

    msg.attach(MIMEText(email_body, 'plain'))

    # 3. Connect to Gmail and Send to all recipients
    try:
        print(f"📧 Connecting to Gmail SMTP server for {len(recipient_list)} recipient(s)...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls() 
        
        server.login(sender_email, sender_password)
        
        text = msg.as_string()
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
        {"ticker": "KPLC", "action": "INITIAL_BUY", "reason": "Golden Cross confirmed with 1.2x Volume Surge", "suggested_stop_loss": 15.72},
        {"ticker": "KCB", "action": "SELL", "price": 29.75, "reason": "Trend Reversal / 50-EMA crossed below 200-EMA"}
    ]
    format_and_dispatch_signals(mock_signals)