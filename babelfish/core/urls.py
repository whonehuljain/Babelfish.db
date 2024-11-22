from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('home/', views.home, name='home'),
    path('mysql/', views.mysql, name='connect_database'),
    path('chat/', views.chat, name='chat'),
    path('mongodb/', views.mongodb, name='connect_mongodb'),
]