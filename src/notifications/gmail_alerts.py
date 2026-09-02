import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime

try:
    from dotenv import load_dotenv, find_dotenv
    # Force reload to ensure it grabs the latest .env if cached
    load_dotenv(find_dotenv(), override=True)
except ImportError:
    pass

def format_and_dispatch_signals(
    signals: List[Dict[str, Any]],
    system_health: Dict[str, Any] = None,
    portfolio: Dict[str, Any] = None,
    market_context: Dict[str, Any] = None,
    recipient_email: str = None
):
    print("\n--- 📧 EMAIL DISPATCH INITIATED ---")
    
    sender_email = os.environ.get("GMAIL_SENDER")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    
    if recipient_email:
        recipient_list = [recipient_email]
    else:
        recipients_env = os.environ.get("GMAIL_RECIPIENTS") or os.environ.get("GMAIL_RECIPIENT", "")
        recipients_env = recipients_env.replace('"', '').replace("'", "")
        recipient_list = [email.strip() for email in recipients_env.split(",") if email.strip()]

    print(f"Sender Loaded: {sender_email}")
    print(f"Recipients Loaded: {recipient_list}")
    
    if not sender_email or not sender_password:
        print("❌ ERROR: Missing GMAIL_SENDER or GMAIL_PASSWORD in environment.")
        return
        
    if not recipient_list:
        print("❌ ERROR: No recipients found in environment.")
        return

    now_eat = datetime.now().strftime("%d-%b-%Y")
    health = system_health or {}
    port = portfolio or {"total_equity": 0.0, "cash": 0.0, "daily_change_pct": 0.0, "open_positions": [], "username": "Trader"}
    mkt = market_context or {}

    equity_str = f"Ksh {port['total_equity']:,.0f}"
    subject = f"🚨 NSE Alert: Action Required | Equity: {equity_str}" if signals else f"📊 NSE Daily Update | Equity: {equity_str}"

    username = port.get('username', 'Trader').capitalize()
    
    email_body = f"Hello {username},\n\n"
    email_body += f"Here is your daily NSE portfolio update for {now_eat}.\n\n"
    
    email_body += "💰 PORTFOLIO SUMMARY\n"
    email_body += "-" * 40 + "\n"
    email_body += f"Total Equity   : Ksh {port['total_equity']:,.2f}\n"
    email_body += f"Available Cash : Ksh {port['cash']:,.2f}\n\n"
    
    positions = port.get("open_positions", [])
    if positions:
        email_body += "Active Holdings:\n"
        for p in positions:
            pnl_str = f"{p.get('pnl_val', 0.0):+,.2f}"
            email_body += f"• {p['ticker']}: {p.get('shares', 0)} shares | Price: Ksh {p.get('current', 0):.2f} | PnL: {pnl_str}\n"
    else:
        email_body += "Active Holdings: 100% Cash.\n"
    email_body += "\n"

    email_body += "🎯 HIGH-CONVICTION BUY SIGNALS\n"
    email_body += "-" * 40 + "\n"
    if signals:
        for sig in signals:
            ticker = sig.get("ticker", "UNKNOWN")
            action = sig.get("action", "HOLD")
            sl = sig.get("suggested_stop_loss", 0.0)
            reason = sig.get("reason", "Criteria met.")
            
            email_body += f"🟢 {action}: {ticker} @ Ksh {sig.get('price', 0.0):.2f}\n"
            email_body += f"   Reason: {reason}\n"
            email_body += f"   Stop Loss: Ksh {sl:.2f}\n\n"
    else:
        email_body += "😴 No high-conviction buy signals today.\n\n"

    email_body += "📉 SWING TRADE WATCHLIST (Oversold Dips)\n"
    email_body += "-" * 40 + "\n"
    
    watchlist = mkt.get("closest_watch", [])
    if watchlist and watchlist[0].get("ticker") != "MARKET":
        for watch in watchlist:
            email_body += f"• {watch['ticker']} -> {watch['note']}\n"
    else:
        email_body += "No stocks are currently oversold. Keep your cash safe.\n"
    
    email_body += "\n"
    email_body += "⚙️ SYSTEM STATUS\n"
    email_body += "-" * 40 + "\n"
    email_body += f"🟢 Scanned {health.get('counters_checked', 31)} tickers successfully.\n\n"
    email_body += "Automated by Reuel & Banice's NSE Trading Bot"

    print("Connecting to SMTP Server (smtp.gmail.com:587)...")
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        print("✅ SMTP Login Successful!")
        
        for recipient in recipient_list:
            msg = MIMEMultipart()
            msg['From'] = f"NSE Trading Bot <{sender_email}>"
            msg['To'] = recipient
            msg['Subject'] = subject
            msg.attach(MIMEText(email_body, 'plain'))
            
            try:
                server.sendmail(sender_email, recipient, msg.as_string())
                print(f"✅ Dispatch complete: Email sent to {recipient}")
            except Exception as e:
                print(f"❌ Dispatch failed for {recipient}: {e}")
                
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP ERROR: Authentication failed. Your App Password may have been revoked or typed incorrectly.")
    except Exception as e:
        print(f"❌ SMTP ERROR: Connection Failed: {e}")
    finally:
        try:
            server.quit()
        except:
            pass
    print("---------------------------------------\n")