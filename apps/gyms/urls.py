from django.urls import path
from . import views

urlpatterns = [
    path('', views.gym_list, name='gym_list'),
    path('gyms/<slug:slug>/', views.gym_detail, name='gym_detail'),
]
