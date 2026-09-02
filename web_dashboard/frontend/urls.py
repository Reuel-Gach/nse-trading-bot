from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication & Registration
    path('login/', auth_views.LoginView.as_view(template_name='frontend/login.html'), name='login'),
    path('register/', views.register, name='register'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Active Operations Dashboard
    path('', views.dashboard, name='dashboard'),
    path('add-position/', views.add_position, name='add_position'),
    path('edit-position/<int:position_id>/', views.edit_position, name='edit_position'),
    path('update-status/<int:position_id>/', views.update_position_status, name='update_position_status'),
    path('delete-position/<int:position_id>/', views.delete_position, name='delete_position'),
    
    # Trade Journal
    path('journal/', views.trade_journal, name='trade_journal'),
    path('close-position/<int:position_id>/', views.close_position, name='close_position'),
    
    # Control Room & System Overrides
    path('control-room/', views.control_room, name='control_room'),
    path('control-room/refresh/', views.refresh_market_data, name='refresh_market_data'),

    # Algorithmic Market Radar
    path('radar/', views.market_radar, name='market_radar'),
]