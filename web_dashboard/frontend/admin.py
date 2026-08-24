from django.contrib import admin
from .models import Account, PortfolioPosition

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'available_cash')
    search_fields = ('user__username',)

@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    list_display = ('user', 'ticker', 'shares', 'entry_price', 'status', 'created_at')
    list_filter = ('status', 'ticker')
    search_fields = ('user__username', 'ticker')