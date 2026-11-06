from django.urls import path

from . import views

app_name = 'todolist'
urlpatterns = [
    path('', views.home_page, name='home'),
    path('lists/new/', views.new_list, name='new_list'),
    path('lists/mine/', views.my_lists, name='my_lists'),
    path('lists/<int:list_id>/', views.view_list, name='view_list'),
]
