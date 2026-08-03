from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),

    path('api/logs/', views.stream_logs, name='stream_logs'),
    path('api/chart/<str:ticker>/', views.chart_data, name='chart_data'),
]