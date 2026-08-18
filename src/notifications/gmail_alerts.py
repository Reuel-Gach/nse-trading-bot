import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime

try:
    from dotenv import load_dotenv, find_dotenv
    load_dotenv(find_dotenv())
except ImportError:
    pass

def format_and_dispatch_signals(
    signals: List[Dict[str, Any]],
    system_health: Dict[str, Any] = None,
    portfolio: Dict[str, Any] = None,
    market_context: Dict[str, Any] = None,
    recipient_email: str = None
):
    sender_email = os.environ.get("GMAIL_SENDER")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    
    if recipient_email:
        recipient_list = [recipient_email]
    else:
        recipients_env = os.environ.get("GMAIL_RECIPIENTS") or os.environ.get("GMAIL_RECIPIENT", "")
        recipient_list = [email.strip() for email in recipients_env.split(",") if email.strip()]

    if not all([sender_email, sender_password, recipient_list]):
        print("⚠️ Gmail credentials missing. Skipping email notification.")
        return

    now_eat = datetime.now().strftime("%d-%b-%Y | %H:%M EAT")
    health = system_health or {}
    port = portfolio or {"total_equity": 0.0, "cash": 0.0, "daily_change_pct": 0.0, "open_positions": [], "username": "Trader"}
    mkt = market_context or {}

    daily_change_str = f"{port['daily_change_pct']:+.2f}%"
    equity_str = f"Ksh {port['total_equity']:,.0f}"

    if signals:
        subject = f"🚨 NSE TRADE ALERT: Action Required | Equity: {equity_str}"
    else:
        subject = f"📊 NSE Daily Quantitative Brief | Equity: {equity_str}"

    username = port.get('username', 'Trader').capitalize()
    
    # --- EMAIL CONSTRUCTION ---
    email_body = f"Hello {username},\n\n"
    email_body += "Here is your end-of-day Nairobi Securities Exchange quantitative analysis.\n\n"
    
    email_body += "=======================================================\n"
    email_body += " 🏦 YOUR LIVE PORTFOLIO SUMMARY\n"
    email_body += "=======================================================\n"
    email_body += f"• Total Equity   : Ksh {port['total_equity']:,.2f}\n"
    email_body += f"• Unallocated    : Ksh {port['cash']:,.2f} (Available for deployment)\n"
    
    positions = port.get("open_positions", [])
    if positions:
        email_body += f"• Active Holdings:\n"
        for p in positions:
            pnl_str = f"{p.get('pnl_val', 0.0):+,.2f}"
            email_body += f"   └── {p['ticker']}: {p.get('shares', 0)} shares | Entry: Ksh {p.get('entry', 0):.2f} | Current: Ksh {p.get('current', 0):.2f} | PnL: {pnl_str}\n"
    else:
        email_body += "• Active Holdings: No active positions. Holding 100% cash.\n"
    email_body += "\n"

    email_body += "=======================================================\n"
    email_body += " ⚙️ PRIMARY STRATEGY & RATIONALE\n"
    email_body += "=======================================================\n"
    email_body += f"• Strategy Setup : {mkt.get('primary_strategy', 'Trend Following & Momentum.')}\n"
    email_body += f"• Core Logic     : {mkt.get('strategy_logic', 'Awaiting high-probability setups.')}\n\n"

    email_body += "=======================================================\n"
    email_body += " ⚡ TODAY'S MARKET SIGNALS\n"
    email_body += "=======================================================\n"
    if signals:
        email_body += "Action is required on the following counters based on today's closing data:\n\n"
        for sig in signals:
            ticker = sig.get("ticker", "UNKNOWN")
            action = sig.get("action", "HOLD")
            sl = sig.get("suggested_stop_loss", 0.0)
            reason = sig.get("reason", "Indicator threshold met.")
            
            if "BUY" in action:
                email_body += f"🟢 {action}: {ticker}\n"
            else:
                email_body += f"🔴 {action}: {ticker}\n"
                
            email_body += f"   ├── Rationale : {reason}\n"
            email_body += f"   └── Stop Loss : Ksh {sl:.2f}\n\n"
    else:
        email_body += "😴 No long-term Golden Cross or major volume breakouts detected today.\n"
        email_body += "Your portfolio structure remains intact. No immediate action required on the primary strategy.\n\n"

    email_body += "=======================================================\n"
    email_body += " 🎯 SHORT-TERM / HIGH-RISK PLAYS (The 'Meantime' Strategy)\n"
    email_body += "=======================================================\n"
    email_body += f"{mkt.get('meantime_advice', 'Hold cash and observe.')}\n\n"
    
    email_body += "Active Watchlist for Swing Trades:\n"
    for watch in mkt.get("closest_watch", []):
        email_body += f"   🔍 {watch['ticker']}: {watch['note']}\n"
    email_body += "\n"

    email_body += "=======================================================\n"
    email_body += " 🔧 SYSTEM HEALTH\n"
    email_body += "=======================================================\n"
    email_body += f"Status: {health.get('status', 'Operational')} | Data: {health.get('api', 'EOD')} | Scanned: {health.get('counters_checked', 0)} NSE Tickers\n\n"

    email_body += "Automated by Reuel & Banice's NSE Quantitative Bot\n"
    email_body += "Nairobi Securities Exchange\n"

    msg = MIMEMultipart()
    msg['From'] = f"NSE Trading Bot <{sender_email}>"
    msg['To'] = ", ".join(recipient_list)
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_list, msg.as_string())
    except Exception as e:
        print(f"❌ Failed to send email to {recipient_email}: {e}")
    finally:
        try:
            server.quit()
        except:
            pass