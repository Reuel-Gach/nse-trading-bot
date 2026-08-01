import sqlite3
import os
from django.shortcuts import redirect, render
from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages

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