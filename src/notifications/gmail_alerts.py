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
    market_context: Dict[str, Any] = None
):
    """
    Formats trading signals, portfolio equity, system health, and market context
    into a daily heartbeat report and dispatches via Gmail SMTP.
    """
    sender_email = os.environ.get("GMAIL_SENDER")
    sender_password = os.environ.get("GMAIL_PASSWORD")
    
    # Fetch recipients (supporting single or comma-separated emails)
    recipients_env = os.environ.get("GMAIL_RECIPIENTS") or os.environ.get("GMAIL_RECIPIENT", "")
    recipient_list = [email.strip() for email in recipients_env.split(",") if email.strip()]

    if not all([sender_email, sender_password, recipient_list]):
        print("⚠️ Gmail credentials or recipients missing in .env. Skipping email notification.")
        return

    # --- 1. SETUP DEFAULTS FOR HEARTBEAT CONTEXT ---
    now_eat = datetime.now().strftime("%d-%b-%Y | %H:%M EAT")
    
    health = system_health or {
        "status": "🟢 All Systems Operational",
        "api": "MyStocks EOD Connected",
        "scan_time": now_eat,
        "counters_checked": 32,
        "errors": 0
    }

    port = portfolio or {
        "total_equity": 100000.0,
        "cash": 100000.0,
        "daily_change_pct": 0.0,
        "open_positions": []
    }

    mkt = market_context or {
        "condition": "No Golden Cross + 1.2x Volume Surges confirmed today.",
        "closest_watch": [
            {"ticker": "SCOM", "note": "50-EMA approaching 200-EMA from below"},
            {"ticker": "EQTY", "note": "Consolidating near KES 86.50 resistance"}
        ]
    }

    # --- 2. BUILD SUBJECT LINE ---
    daily_change_str = f"{port['daily_change_pct']:+.2f}%"
    equity_str = f"Ksh {port['total_equity']:,.0f}"

    if signals:
        buy_count = sum(1 for s in signals if s.get("action") in ["BUY", "INITIAL_BUY", "SCALE_IN"])
        sell_count = sum(1 for s in signals if s.get("action") in ["SELL", "SELL_STOP_LOSS", "SELL_DEATH_CROSS"])
        subject = f"🚨 [NSE BOT ALERT] {buy_count} Buy(s), {sell_count} Sell(s) | Equity: {equity_str} ({daily_change_str})"
    else:
        subject = f"[BOT HEARTBEAT] No Active Alerts | Equity: {equity_str} ({daily_change_str})"

    # --- 3. BUILD EMAIL BODY ---
    email_body = "NSE QUANTITATIVE TRADING BOT — DAILY REPORT\n"
    email_body += "=" * 55 + "\n\n"

    # Section A: System Health
    email_body += f"SYSTEM HEALTH: {health.get('status', '🟢 All Systems Operational')}\n"
    email_body += f"• Data Source : {health.get('api', 'MyStocks Mobile Scraping Engine')}\n"
    email_body += f"• Last Scan   : {health.get('scan_time', now_eat)}\n"
    email_body += f"• Counters    : {health.get('counters_checked', 32)} NSE Stocks Checked | Errors: {health.get('errors', 0)}\n\n"

    # Section B: Portfolio Summary
    email_body += "PORTFOLIO SUMMARY:\n"
    email_body += f"• Total Equity   : Ksh {port['total_equity']:,.2f} ({daily_change_str} today)\n"
    email_body += f"• Available Cash : Ksh {port['cash']:,.2f}\n"
    
    positions = port.get("open_positions", [])
    email_body += f"• Open Positions ({len(positions)}):\n"
    if positions:
        for p in positions:
            pnl_str = f"{p.get('pnl_val', 0.0):+,.2f}"
            email_body += (
                f"  - {p['ticker']}: {p.get('shares', 0)} sh | "
                f"Entry: Ksh {p.get('entry', 0):.2f} | "
                f"Current: Ksh {p.get('current', 0):.2f} ({pnl_str})\n"
            )
    else:
        email_body += "  - No active holdings in portfolio.\n"
    email_body += "\n"

    # Section C: Active Trading Alerts (if any)
    email_body += "=" * 55 + "\n"
    if signals:
        email_body += "⚡ ACTION REQUIRED — TODAY'S SIGNALS:\n\n"
        for sig in signals:
            ticker = sig.get("ticker", "UNKNOWN")
            action = sig.get("action", "HOLD")
            reason = sig.get("reason", "No reason provided.")
            sl = sig.get("suggested_stop_loss", sig.get("stop_loss", 0.0))
            price = sig.get("price", 0.0)
            price_text = f" @ Ksh {price:.2f}" if price > 0 else ""

            if action in ["BUY", "INITIAL_BUY", "SCALE_IN"]:
                email_body += f"🟢 {action}: {ticker}{price_text}\n"
                email_body += f"   ├── Reason       : {reason}\n"
                email_body += f"   └── Stop Loss    : Ksh {sl:.2f}\n\n"
            elif action in ["SELL", "SELL_STOP_LOSS", "SELL_DEATH_CROSS"]:
                email_body += f"🔴 {action}: {ticker}{price_text}\n"
                email_body += f"   └── Reason       : {reason}\n\n"
    else:
        email_body += "😴 NO NEW ALERTS FIRED TODAY\n\n"
        email_body += "MARKET CONTEXT (Why no alerts?):\n"
        email_body += f"• Market Condition : {mkt.get('condition', 'Neutral momentum across NSE counters.')}\n"
        
        watch_items = mkt.get("closest_watch", [])
        if watch_items:
            email_body += "• Closest Watchlist:\n"
            for w in watch_items:
                email_body += f"  - {w['ticker']}: {w['note']}\n"
        email_body += "\n"

    email_body += "=" * 55 + "\n"
    email_body += "Automated by Reuel's NSE Quantitative Bot | Nairobi Securities Exchange"

    # --- 4. CONSTRUCT & DISPATCH EMAIL ---
    msg = MIMEMultipart()
    msg['From'] = f"NSE Trading Bot <{sender_email}>"
    msg['To'] = ", ".join(recipient_list)
    msg['Subject'] = subject
    msg.attach(MIMEText(email_body, 'plain'))

    try:
        print(f"📧 Connecting to Gmail SMTP server for {len(recipient_list)} recipient(s)...")
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, recipient_list, msg.as_string())
        print(f"✅ Heartbeat report dispatched successfully to: {', '.join(recipient_list)}")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
    finally:
        try:
            server.quit()
        except:
            pass

# Quick Local Test — Try running: python src/notifications/gmail_alerts.py
if __name__ == "__main__":
    # Test 1: Simulating a Heartbeat day with NO active alerts
    mock_health = {
        "status": "🟢 All Systems Operational",
        "api": "MyStocks EOD Scraper",
        "scan_time": datetime.now().strftime("%d-%b-%Y | %H:%M EAT"),
        "counters_checked": 31,
        "errors": 0
    }
    
    mock_portfolio = {
        "total_equity": 145000.00,
        "cash": 85000.00,
        "daily_change_pct": 0.45,
        "open_positions": [
            {"ticker": "SCOM", "shares": 1000, "entry": 34.00, "current": 35.50, "pnl_val": 1500.00},
            {"ticker": "KPLC", "shares": 5000, "entry": 16.00, "current": 17.15, "pnl_val": 5750.00}
        ]
    }
    
    mock_market = {
        "condition": "Low volume across banking sector; waiting for momentum.",
        "closest_watch": [
            {"ticker": "ABSA", "note": "50-EMA (30.10) approaching 200-EMA (28.17); watch volume."},
            {"ticker": "EQTY", "note": "Volume at 0.9x VMA-20 (needs 1.2x surge)."}
        ]
    }

    # Dispatching with zero alerts (Heartbeat mode)
    format_and_dispatch_signals(
        signals=[],
        system_health=mock_health,
        portfolio=mock_portfolio,
        market_context=mock_market
    )