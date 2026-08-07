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
    recipient_email: str = None  # NEW PARAMETER
):
    sender_email = os.environ.get("GMAIL_SENDER")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    
    # Override the .env list if a specific recipient is passed
    if recipient_email:
        recipient_list = [recipient_email]
    else:
        recipients_env = os.environ.get("GMAIL_RECIPIENTS") or os.environ.get("GMAIL_RECIPIENT", "")
        recipient_list = [email.strip() for email in recipients_env.split(",") if email.strip()]

    if not all([sender_email, sender_password, recipient_list]):
        print("⚠️ Gmail credentials missing. Skipping email notification.")
        return

    now_eat = datetime.now().strftime("%d-%b-%Y | %H:%M EAT")
    health = system_health or {"status": "🟢 All Systems Operational", "api": "MyStocks EOD Connected", "scan_time": now_eat, "counters_checked": 32, "errors": 0}
    port = portfolio or {"total_equity": 0.0, "cash": 0.0, "daily_change_pct": 0.0, "open_positions": [], "username": "Trader"}
    mkt = market_context or {"condition": "Market condition data pending."}

    daily_change_str = f"{port['daily_change_pct']:+.2f}%"
    equity_str = f"Ksh {port['total_equity']:,.0f}"

    if signals:
        buy_count = sum(1 for s in signals if s.get("action") in ["BUY", "INITIAL_BUY", "SCALE_IN"])
        sell_count = sum(1 for s in signals if s.get("action") in ["SELL", "SELL_STOP_LOSS", "SELL_DEATH_CROSS"])
        subject = f"🚨 [NSE BOT ALERT] {buy_count} Buy(s), {sell_count} Sell(s) | Equity: {equity_str} ({daily_change_str})"
    else:
        subject = f"[BOT HEARTBEAT] No Active Alerts | Equity: {equity_str} ({daily_change_str})"

    # --- PERSONALIZED GREETING ---
    username = port.get('username', 'Trader').capitalize()
    email_body = f"Hello {username},\n\n"
    
    email_body += "NSE QUANTITATIVE TRADING BOT — DAILY REPORT\n"
    email_body += "=" * 55 + "\n\n"

    email_body += f"SYSTEM HEALTH: {health.get('status', '🟢 All Systems Operational')}\n"
    email_body += f"• Data Source : {health.get('api', 'MyStocks Mobile')}\n"
    email_body += f"• Last Scan   : {health.get('scan_time', now_eat)}\n"
    email_body += f"• Counters    : {health.get('counters_checked', 32)} Stocks Checked | Errors: {health.get('errors', 0)}\n\n"

    email_body += "YOUR PORTFOLIO SUMMARY:\n"
    email_body += f"• Total Equity   : Ksh {port['total_equity']:,.2f} ({daily_change_str} today)\n"
    email_body += f"• Available Cash : Ksh {port['cash']:,.2f}\n"
    
    positions = port.get("open_positions", [])
    email_body += f"• Open Positions ({len(positions)}):\n"
    if positions:
        for p in positions:
            pnl_str = f"{p.get('pnl_val', 0.0):+,.2f}"
            email_body += f"  - {p['ticker']}: {p.get('shares', 0)} sh | Entry: Ksh {p.get('entry', 0):.2f} | Current: Ksh {p.get('current', 0):.2f} ({pnl_str})\n"
    else:
        email_body += "  - No active holdings in portfolio.\n"
    email_body += "\n"

    email_body += "=" * 55 + "\n"
    if signals:
        email_body += "⚡ ACTION REQUIRED — TODAY'S SIGNALS:\n\n"
        for sig in signals:
            ticker = sig.get("ticker", "UNKNOWN")
            action = sig.get("action", "HOLD")
            sl = sig.get("suggested_stop_loss", 0.0)
            email_body += f"{action}: {ticker} | Stop Loss: Ksh {sl:.2f} | Reason: {sig.get('reason')}\n"
    else:
        email_body += "😴 NO NEW ALERTS FIRED TODAY\n\n"

    email_body += "\n" + "=" * 55 + "\n"
    email_body += "Automated by Reuel & Banice's NSE Quantitative Bot | Nairobi Securities Exchange"

    msg = MIMEMultipart()
    msg['From'] = f"NSE Trading Bot <{sender_email}>"
    msg['To'] = ", ".join(recipient_list)
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        print(f"📧 Connecting to SMTP... Sending to {', '.join(recipient_list)}")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_list, msg.as_string())
        print(f"✅ Report dispatched successfully to: {', '.join(recipient_list)}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
    finally:
        try:
            server.quit()
        except:
            pass