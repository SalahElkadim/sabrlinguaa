from django.urls import path
from . import views

urlpatterns = [

    # ============================================
    # TEACHERS
    # ============================================
    path('teachers/', views.list_teachers, name='list-teachers'),
    path('teachers/<int:teacher_id>/', views.get_teacher, name='get-teacher'),
    path('teachers/create/', views.create_teacher, name='create-teacher'),
    path('teachers/<int:teacher_id>/update/', views.update_teacher, name='update-teacher'),
    path('teachers/<int:teacher_id>/delete/', views.delete_teacher, name='delete-teacher'),

    # ============================================
    # BOOKINGS
    # ============================================
    path('create/', views.create_booking, name='create-booking'),
    path('my-bookings/', views.my_bookings, name='my-bookings'),
    path('<int:booking_id>/', views.get_booking, name='get-booking'),
    path('<int:booking_id>/cancel/', views.cancel_booking, name='cancel-booking'),

    # ============================================
    # ADMIN
    # ============================================
    path('all/', views.list_all_bookings, name='list-all-bookings'),
]