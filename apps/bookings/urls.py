from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:gym_id>/', views.create_booking, name='create_booking'),
    path('<int:booking_id>/<str:status>/', views.update_booking_status, name='update_booking_status'),
    path('<int:booking_id>/cancel/', views.cancel_own_booking, name='cancel_own_booking'),
]
