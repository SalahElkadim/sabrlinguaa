
from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    
path('total-score/', views.my_total_score, name='my-total-score'),
# urls.py
path('leaderboard/', views.leaderboard),
path('leaderboard/ielts/', views.ielts_leaderboard),
path('leaderboard/step/', views.step_leaderboard),
path('leaderboard/general/categories/', views.general_all_categories_leaderboard),
path('leaderboard/general/categories/<int:category_id>/', views.general_category_leaderboard),
path('leaderboard/esp/categories/', views.esp_all_categories_leaderboard),
path('leaderboard/esp/categories/<int:category_id>/', views.esp_category_leaderboard),

]