from django.http import JsonResponse
import pandas as pd
import sqlite3
from django.http import HttpResponse, StreamingHttpResponse
import time
import os
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection

def stream_logs(request):
    """
    Streams log file contents line-by-line in real-time (similar to tail -f).
    """
    # Define the path to your trading bot's log file
    # Adjust this path based on where your bot saves its logs
    log_file_path = os.path.join(settings.BASE_DIR, '../logs/trading_bot.log') 

    def log_generator():
        # Check if file exists, if not wait or yield a notice
        if not os.path.exists(log_file_path):
            yield "data: Log file not found. Waiting for bot to initialize...\n\n"
            while not os.path.exists(log_file_path):
                time.sleep(2)

        with open(log_file_path, 'r') as f:
            # Move to the end of the file to read only new logs (or omit to read from start)
            f.seek(0, os.SEEK_END)
            
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.5)  # Sleep briefly if no new line is written
                    continue
                
                # Format as Server-Sent Events (SSE) data
                yield f"data: {line.strip()}\n\n"

    response = StreamingHttpResponse(log_generator(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    return response

@login_required(login_url='login')
def chart_data(request, ticker):
    # 1. Query PostgreSQL using Django's active database connection
    query = """
        SELECT date as time, open, high, low, close, volume 
        FROM historical_prices 
        WHERE ticker = %s 
        ORDER BY date ASC
    """
    
    with connection.cursor() as cursor:
        cursor.execute(query, [ticker])
        columns = [col[0] for col in cursor.description]
        data = cursor.fetchall()
        
    # 2. Load the data into a Pandas DataFrame
    df = pd.DataFrame(data, columns=columns)
    
    # Safety Check: If no data exists, return empty arrays to prevent frontend crashes
    if df.empty:
        return JsonResponse({
            "ticker": ticker, 
            "candles": [], 
            "volume": [], 
            "ema50": [], 
            "ema200": []
        })
    
    # 3. Calculate 50 EMA and 200 EMA using Pandas
    # span=X controls the decay weight, adjust=False uses the standard recursive EMA formula
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean().round(2)
    df['ema200'] = df['close'].ewm(span=200, adjust=False).mean().round(2)
    
    # 4. Format the Data for TradingView
    # Convert dates to the string format TradingView requires: 'YYYY-MM-DD'
    df['time'] = pd.to_datetime(df['time']).dt.strftime('%Y-%m-%d')
    
    # Extract the Candlesticks
    candles = df[['time', 'open', 'high', 'low', 'close']].to_dict(orient='records')
    
    # Extract the Volume and dynamically color it based on daily performance
    # Green if the closing price is higher than the open, Red if it dropped
    df['volume_color'] = df.apply(
        lambda row: 'rgba(34, 197, 94, 0.4)' if row['close'] >= row['open'] else 'rgba(239, 68, 68, 0.4)', 
        axis=1
    )
    volume = df.rename(columns={'volume': 'value', 'volume_color': 'color'})[['time', 'value', 'color']].to_dict(orient='records')
    
    # Extract the EMAs
    ema50 = df.rename(columns={'ema50': 'value'})[['time', 'value']].to_dict(orient='records')
    ema200 = df.rename(columns={'ema200': 'value'})[['time', 'value']].to_dict(orient='records')
    
    # 5. Send the structured payload back to the frontend
    return JsonResponse({
        "ticker": ticker,
        "candles": candles,
        "volume": volume,
        "ema50": ema50,
        "ema200": ema200
    })


@login_required(login_url='login')
def dashboard_view(request):
    # Navigate up one directory to find the bot's database
    db_path = os.path.join(settings.BASE_DIR.parent, "market_data.sqlite")
    
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Filter positions to only show those belonging to the currently logged-in user
    cursor.execute("""
        SELECT position_id, ticker, entry_price, current_stop_loss, shares, pyramid_level, status 
        FROM portfolio 
        WHERE username = ? AND status != 'CLOSED'
        ORDER BY position_id DESC
    """, (request.user.username,))
    
    positions = cursor.fetchall()
    conn.close()
    
    return render(request, "dashboard.html", {"portfolio": positions})


def login_view(request):
    # If the user submits the login form
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        
        # Verify credentials
        user = authenticate(request, username=user_name, password=pass_word)
        
        if user is not None:
            # Create the session and log them in
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
            return redirect('login')
    return render(request, "login.html")

def register_view(request):
    # If the user submits the registration form
    if request.method == 'POST':
        user_name = request.POST.get('username')
        user_email = request.POST.get('email')
        pass_word = request.POST.get('password')
        confirm_pass = request.POST.get('confirm_password')

        # 1. Check if passwords match
        if pass_word != confirm_pass:
            messages.error(request, 'Passwords do not match!')
            return redirect('register')
        
        # 2. Check if username already exists
        if User.objects.filter(username=user_name).exists():
            messages.error(request, 'Username is already taken!')
            return redirect('register')
        
        # 3. Create and save the new user
        new_user = User.objects.create_user(username=user_name, email=user_email, password=pass_word)
        new_user.save()
        
        messages.success(request, 'Account created successfully! You can now log in.')
        return redirect('login')
    return render(request, "register.html")

def logout_view(request):
    messages.success(request, 'You have been logged out.')
    logout(request)
    return redirect("login")