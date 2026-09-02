from django.contrib import admin
from .models import Account, PortfolioPosition, TradeJournal

@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    # Updated: Replaced available_cash with total_realized_profit
    list_display = ('user', 'total_realized_profit')

@admin.register(PortfolioPosition)
class PortfolioPositionAdmin(admin.ModelAdmin):
    # Updated: Replaced created_at with date_added
    list_display = ('user', 'ticker', 'shares', 'entry_price', 'status', 'date_added')
    list_filter = ('status', 'ticker')

@admin.register(TradeJournal)
class TradeJournalAdmin(admin.ModelAdmin):
    # New admin view for our closed trades ledger
    list_display = ('user', 'ticker', 'shares', 'exit_price', 'pnl_value', 'pnl_percent', 'exit_reason', 'date_closed')
    list_filter = ('ticker', 'exit_reason')