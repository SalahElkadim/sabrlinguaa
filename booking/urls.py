from django.urls import path
from . import views

urlpatterns = [

    # Teachers
    path('teachers/', views.list_teachers, name='list_teachers'),
    path('teachers/<int:teacher_id>/', views.get_teacher, name='get_teacher'),
    path('teachers/create/', views.create_teacher, name='create_teacher'),
    path('teachers/<int:teacher_id>/update/', views.update_teacher, name='update_teacher'),
    path('teachers/<int:teacher_id>/delete/', views.delete_teacher, name='delete_teacher'),
    path('teachers/<int:teacher_id>/reviews/', views.get_teacher_reviews, name='get_teacher_reviews'),

    # Programs
    path('programs/', views.list_programs, name='list_programs'),
    path('programs/<int:program_id>/', views.get_program, name='get_program'),
    path('programs/create/', views.create_program, name='create_program'),
    path('programs/<int:program_id>/update/', views.update_program, name='update_program'),
    path('programs/<int:program_id>/delete/', views.delete_program, name='delete_program'),

    # Subscriptions
    path('subscriptions/my/', views.my_subscriptions, name='my_subscriptions'),

    # Webhook
    path('webhooks/moyasar/', views.moyasar_webhook, name='moyasar_webhook'),

    # Custom Programs
    path('custom-programs/create/', views.create_custom_program, name='create_custom_program'),

    # Reviews
    path('reviews/create/', views.create_review, name='create_review'),
    path('teachers/<int:teacher_id>/reviews/delete/', views.delete_review, name='delete_review'),
    path('subscriptions/pay/', views.initiate_subscription_payment, name='initiate_subscription_payment'),
    path('subscriptions/callback/', views.subscription_payment_callback, name='subscription_payment_callback'),
]