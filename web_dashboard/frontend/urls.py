from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Authentication
    path('login/', auth_views.LoginView.as_view(template_name='frontend/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # Active Operations Dashboard
    path('', views.dashboard, name='dashboard'),
    
    # Portfolio CRUD
    path('add-position/', views.add_position, name='add_position'),
    path('edit-position/<int:position_id>/', views.edit_position, name='edit_position'),
    path('update-status/<int:position_id>/', views.update_position_status, name='update_position_status'),
    path('delete-position/<int:position_id>/', views.delete_position, name='delete_position'),
    
    # Trade Journal
    path('journal/', views.trade_journal, name='trade_journal'),
    path('close-position/<int:position_id>/', views.close_position, name='close_position'),
]