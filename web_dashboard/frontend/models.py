from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    # Global cash is removed. We now track total historical profit/loss.
    total_realized_profit = models.FloatField(default=0.0) 

    def __str__(self):
        return f"{self.user.username}'s Account Settings"

class PortfolioPosition(models.Model):
    STATUS_CHOICES = (
        ('OPEN', 'Open'),
        ('PENDING', 'Pending'),
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    shares = models.IntegerField()
    entry_price = models.FloatField()
    current_stop_loss = models.FloatField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.shares} {self.ticker} ({self.status})"

# NEW: The Trade Journal Ledger for Closed Positions
class TradeJournal(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticker = models.CharField(max_length=10)
    shares = models.IntegerField()
    entry_price = models.FloatField()
    exit_price = models.FloatField()
    pnl_value = models.FloatField()
    pnl_percent = models.FloatField()
    exit_reason = models.CharField(max_length=100, default="Manual Exit") # e.g., "Hit Stop Loss", "Take Profit"
    date_closed = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.ticker} CLOSED at {self.exit_price}"