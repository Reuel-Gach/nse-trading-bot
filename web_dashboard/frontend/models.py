from django.db import models
from django.contrib.auth.models import User

class Account(models.Model):
    # Links one-to-one with Django's built-in User (reuel, banice, etc.)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='account')
    available_cash = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.user.username} | Cash: Ksh {self.available_cash:,.2f}"

class PortfolioPosition(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('CLOSED', 'Closed'),
    ]

    # Links multiple stock positions to a single user
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='positions')
    ticker = models.CharField(max_length=15)
    entry_price = models.FloatField()
    current_stop_loss = models.FloatField()
    shares = models.IntegerField()
    pyramid_level = models.IntegerField(default=0)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='OPEN')
    
    # Helpful timestamps to track when a trade was taken
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"[{self.status}] {self.user.username} - {self.shares} sh of {self.ticker}"