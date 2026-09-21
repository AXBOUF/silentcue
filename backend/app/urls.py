from django.urls import path
from . import views
urlpatterns = [
    path('', views.home, name='home'),
    path('create_room/', views.create_room, name='create_room'),
    path('join_room/', views.join_room, name='join_room'),
    path('join_room/<str:room_code>/', views.join_room, name='join_room_by_code'),
    path('room/<str:room_code>/', views.room, name='room'),
    path('index/', views.index, name='index'),
]