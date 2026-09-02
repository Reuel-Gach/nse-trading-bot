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

def _resolve_recipients(recipient_email: str) -> List[str]:
    """Helper to resolve recipient list from argument or environment variables."""
    if recipient_email:
        return [recipient_email]
    
    recipients_env = os.environ.get("GMAIL_RECIPIENTS") or os.environ.get("GMAIL_RECIPIENT", "")
    recipients_env = recipients_env.replace('"', '').replace("'", "")
    return [email.strip() for email in recipients_env.split(",") if email.strip()]

def _send_email_smtp(recipient_list: List[str], subject: str, email_body: str) -> bool:
    """Core SMTP dispatcher helper."""
    sender_email = os.environ.get("GMAIL_SENDER")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    
    if not sender_email or not sender_password:
        print("❌ ERROR: Missing GMAIL_SENDER or GMAIL_PASSWORD in environment.")
        return False
        
    if not recipient_list:
        print("❌ ERROR: No recipients found in environment.")
        return False

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
        return True
        
    except smtplib.SMTPAuthenticationError:
        print("❌ SMTP ERROR: Authentication failed. Your App Password may have been revoked or typed incorrectly.")
        return False
    except Exception as e:
        print(f"❌ SMTP ERROR: Connection Failed: {e}")
        return False
    finally:
        try:
            server.quit()
        except:
            pass

def format_and_dispatch_signals(
    signals: List[Dict[str, Any]],
    system_health: Dict[str, Any] = None,
    portfolio: Dict[str, Any] = None,
    market_context: Dict[str, Any] = None,
    recipient_email: str = None
):
    """Dispatches intraday tactical buy alerts during trading hours."""
    print("\n--- 📧 INTRADAY TACTICAL ALERT DISPATCH INITIATED ---")
    
    recipient_list = _resolve_recipients(recipient_email)
    now_eat = datetime.now().strftime("%d-%b-%Y")
    health = system_health or {}
    port = portfolio or {"total_equity": 0.0, "cash": 0.0, "realized_profit": 0.0, "open_positions": [], "username": "Trader"}
    mkt = market_context or {}

    equity_str = f"Ksh {port['total_equity']:,.0f}"
    subject = f"🚨 NSE Tactical Buy Alert | Equity: {equity_str}"

    username = port.get('username', 'Trader').capitalize()
    
    email_body = f"Hello {username},\n\n"
    email_body += f"Tactical intraday scan update for {now_eat}.\n\n"
    
    email_body += "💰 PORTFOLIO SUMMARY\n"
    email_body += "-" * 40 + "\n"
    email_body += f"Active Equity Value : Ksh {port['total_equity']:,.2f}\n"
    email_body += f"Realized Profit     : Ksh {port.get('realized_profit', 0.0):,.2f}\n\n"
    
    positions = port.get("open_positions", [])
    if positions:
        email_body += "Active Holdings:\n"
        for p in positions:
            pnl_str = f"{p.get('pnl_val', 0.0):+,.2f}"
            email_body += f"• {p['ticker']}: {p.get('shares', 0)} shares | Price: Ksh {p.get('current', 0):.2f} | PnL: {pnl_str}\n"
    else:
        email_body += "Active Holdings: 100% Cash.\n"
    email_body += "\n"

    email_body += "🎯 HIGH-CONVICTION TACTICAL BUY SETUPS\n"
    email_body += "-" * 40 + "\n"
    if signals:
        for sig in signals:
            ticker = sig.get("ticker", "UNKNOWN")
            action = sig.get("action", "BUY")
            sl = sig.get("suggested_stop_loss", 0.0)
            reason = sig.get("reason", "Criteria met.")
            
            email_body += f"🟢 {action}: {ticker} @ Ksh {sig.get('price', 0.0):.2f}\n"
            email_body += f"   Reason: {reason}\n"
            email_body += f"   Stop Loss: Ksh {sl:.2f}\n\n"
    else:
        email_body += "😴 No new tactical triggers in this cycle.\n\n"

    email_body += "⚙️ SYSTEM STATUS\n"
    email_body += "-" * 40 + "\n"
    email_body += f"🟢 {health.get('status', 'Operational')} | Time: {health.get('scan_time', now_eat)}\n\n"
    email_body += "Automated by Reuel & Banice's NSE Trading Bot"

    _send_email_smtp(recipient_list, subject, email_body)
    print("---------------------------------------\n")

def dispatch_eod_summary_report(
    recipient_email: str,
    username: str,
    portfolio: Dict[str, Any],
    all_signals: List[Dict[str, Any]],
    latest_prices: Dict[str, float]
):
    """Dispatches the comprehensive End-of-Day closing report at 15:00+ EAT."""
    print("\n--- 📧 EOD SUMMARY REPORT DISPATCH INITIATED ---")
    
    recipient_list = _resolve_recipients(recipient_email)
    now_eat = datetime.now().strftime("%d-%b-%Y")
    username_clean = username.capitalize()
    
    equity_str = f"Ksh {portfolio.get('total_equity', 0.0):,.0f}"
    subject = f"📊 NSE EOD Closing Report | Equity: {equity_str} ({now_eat})"

    email_body = f"Hello {username_clean},\n\n"
    email_body += f"Here is your official NSE End-of-Day Closing Report for {now_eat}.\n\n"
    
    email_body += "💰 PORTFOLIO & LEDGER SUMMARY\n"
    email_body += "-" * 40 + "\n"
    email_body += f"Active Equity Value : Ksh {portfolio.get('total_equity', 0.0):,.2f}\n"
    email_body += f"Realized Profit     : Ksh {portfolio.get('realized_profit', 0.0):,.2f}\n\n"
    
    positions = portfolio.get("open_positions", [])
    if positions:
        email_body += "Active Holdings:\n"
        for p in positions:
            pnl_str = f"{p.get('pnl_val', 0.0):+,.2f}"
            email_body += f"• {p['ticker']}: {p.get('shares', 0)} shares | Price: Ksh {p.get('current', 0):.2f} | PnL: {pnl_str}\n"
    else:
        email_body += "Active Holdings: 100% Cash.\n"
    email_body += "\n"

    email_body += f"🎯 TODAY'S PROCESSED BUY SIGNALS ({len(all_signals)})\n"
    email_body += "-" * 40 + "\n"
    if all_signals:
        for sig in all_signals:
            ticker = sig.get("ticker", "UNKNOWN")
            price = sig.get("price", 0.0)
            sl = sig.get("suggested_stop_loss", 0.0)
            reason = sig.get("reason", "Criteria met.")
            email_body += f"🟢 BUY: {ticker} @ Ksh {price:.2f}\n"
            email_body += f"   Reason: {reason}\n"
            email_body += f"   Stop Loss: Ksh {sl:.2f}\n\n"
    else:
        email_body += "😴 No high-conviction buy setups triggered during today's session. Cash preserved.\n\n"

    email_body += "⚙️ MARKET SESSION CLOSED\n"
    email_body += "-" * 40 + "\n"
    email_body += "All 20-minute intraday cycles complete. Bot resting until tomorrow's open.\n\n"
    email_body += "Automated by Reuel & Banice's NSE Trading Bot"

    _send_email_smtp(recipient_list, subject, email_body)
    print("---------------------------------------\n")