from django.urls import path
from . import views

urlpatterns = [
    path('', views.supabase_login, name='login'),
    path('logout/', views.supabase_logout, name='logout'),
]