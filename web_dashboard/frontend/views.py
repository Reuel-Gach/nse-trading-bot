import os
import time
import pandas as pd
from django.http import JsonResponse
from django.shortcuts import redirect, render, get_object_or_404
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST

from .models import Account, PortfolioPosition

@login_required(login_url='login')
def dashboard_view(request):
    """
    Fetches the portfolio, calculates live valuations, and builds the Market Radar.
    """
    positions = PortfolioPosition.objects.filter(user=request.user).exclude(status='CLOSED').order_by('-id')
    account, _ = Account.objects.get_or_create(user=request.user)
    
    csv_path = os.path.join(settings.BASE_DIR.parent, 'data', 'nse_historical_data.csv')
    latest_prices = {}
    radar_list = []
    
    if os.path.exists(csv_path):
        try:
            df = pd.read_csv(csv_path)
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'])
                df = df.sort_values(by='date', ascending=False)
                latest_df = df.drop_duplicates(subset=['ticker'], keep='first')
                
                latest_prices = latest_df.set_index('ticker')['close'].to_dict()
                
                for _, row in latest_df.iterrows():
                    ticker = row.get('ticker', '')
                    price = row.get('close', 0.0)
                    rsi = row.get('rsi_14', 50.0)
                    macd_line = row.get('macd_line', 0.0)
                    macd_signal = row.get('macd_signal', 0.0)
                    
                    rsi = rsi if pd.notna(rsi) else 50.0
                    macd_line = macd_line if pd.notna(macd_line) else 0.0
                    macd_signal = macd_signal if pd.notna(macd_signal) else 0.0
                    
                    tags = []
                    if rsi < 35:
                        tags.append({'name': 'OVERSOLD', 'color': 'text-blue-400', 'bg': 'bg-blue-900/30', 'border': 'border-blue-700/50'})
                    if macd_line > macd_signal and rsi < 60:
                        tags.append({'name': 'MACD BULLISH', 'color': 'text-green-400', 'bg': 'bg-green-900/30', 'border': 'border-green-700/50'})
                    
                    if tags:
                        radar_list.append({
                            'ticker': ticker,
                            'price': price,
                            'rsi': round(rsi, 1),
                            'tags': tags
                        })
        except Exception as e:
            print(f"⚠️ Failed to parse market data CSV: {e}")
            
    enriched_positions = []
    total_invested = 0.0
    total_current = 0.0
    
    for pos in positions:
        current_price = latest_prices.get(pos.ticker, pos.entry_price)
        invested_value = pos.shares * pos.entry_price
        current_value = pos.shares * current_price
        pnl_value = current_value - invested_value
        pnl_percent = (pnl_value / invested_value * 100) if invested_value > 0 else 0.0
        
        if pos.status == 'OPEN':
            total_invested += invested_value
            total_current += current_value
            
        enriched_positions.append({
            'id': pos.id,
            'ticker': pos.ticker,
            'shares': pos.shares,
            'entry_price': pos.entry_price,
            'current_price': current_price,
            'invested_value': invested_value,
            'current_value': current_value,
            'pnl_value': pnl_value,
            'pnl_percent': pnl_percent,
            'status': pos.status
        })
        
    net_gain = total_current - total_invested
    net_gain_pct = (net_gain / total_invested * 100) if total_invested > 0 else 0.0
    total_equity = total_current + account.available_cash

    return render(request, "dashboard.html", {
        "portfolio": enriched_positions,
        "total_invested": total_invested,
        "total_current": total_current,
        "net_gain": net_gain,
        "net_gain_pct": net_gain_pct,
        "radar_list": radar_list,
        "cash_balance": account.available_cash,
        "total_equity": total_equity if total_equity > 0 else 100000.0
    })

@login_required(login_url='login')
@require_POST
def add_position(request):
    ticker = request.POST.get('ticker', '').upper().strip()
    shares = int(request.POST.get('shares', 0))
    entry_price = float(request.POST.get('entry_price', 0.0))
    stop_loss = float(request.POST.get('stop_loss', 0.0))
    status = request.POST.get('status', 'OPEN')

    if ticker and shares > 0 and entry_price > 0:
        PortfolioPosition.objects.create(
            user=request.user,
            ticker=ticker,
            shares=shares,
            entry_price=entry_price,
            current_stop_loss=stop_loss,
            status=status
        )
    return redirect('dashboard')

@login_required(login_url='login')
@require_POST
def update_position_status(request, position_id):
    position = get_object_or_404(PortfolioPosition, id=position_id, user=request.user)
    action = request.POST.get('action')

    if action == 'confirm':
        position.status = 'OPEN'
        position.save()
        messages.success(request, f"{position.ticker} order confirmed and activated!")
    elif action == 'cancel':
        position.status = 'CLOSED'
        position.save()
        messages.info(request, f"{position.ticker} order canceled.")

    return redirect('dashboard')

@login_required(login_url='login')
@require_POST
def delete_position(request, position_id):
    position = get_object_or_404(PortfolioPosition, id=position_id, user=request.user)
    ticker = position.ticker
    position.delete()
    messages.success(request, f"Successfully deleted {ticker} position.")
    return redirect('dashboard')

@login_required(login_url='login')
@require_POST
def edit_position(request, position_id):
    position = get_object_or_404(PortfolioPosition, id=position_id, user=request.user)
    
    ticker = request.POST.get('ticker', '').upper().strip()
    shares = int(request.POST.get('shares', 0))
    entry_price = float(request.POST.get('entry_price', 0.0))
    stop_loss = float(request.POST.get('stop_loss', 0.0))
    status = request.POST.get('status', 'OPEN')

    if ticker and shares > 0 and entry_price > 0:
        position.ticker = ticker
        position.shares = shares
        position.entry_price = entry_price
        position.current_stop_loss = stop_loss
        position.status = status
        position.save()
        messages.success(request, f"Successfully updated {ticker}.")
    else:
        messages.error(request, "Invalid update data.")

    return redirect('dashboard')

def login_view(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        user = authenticate(request, username=user_name, password=pass_word)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, "login.html")

def register_view(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        user_email = request.POST.get('email')
        pass_word = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')

        if pass_word != confirm_pass or User.objects.filter(username=user_name).exists():
            return redirect('register')
        
        new_user = User.objects.create_user(username=user_name, email=user_email, password=pass_word)
        new_user.save()
        Account.objects.create(user=new_user, available_cash=0.0)
        return redirect('login')
    return render(request, "register.html")

def logout_view(request):
    logout(request)
    return redirect("login")

def stream_logs(request):
    return JsonResponse({"status": "Logs disabled in minimal view"})

def chart_data(request, ticker):
    return JsonResponse({"status": "Charts disabled in minimal view"})