
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    
path('total-score/', views.my_total_score, name='my-total-score'),
path('leaderboard/',views.leaderboard, name='leaderboard'),

]