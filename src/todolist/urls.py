from django.urls import path

from . import views

app_name = 'todolist'
urlpatterns = [
    path('', views.home_page, name='home'),
    path('lists/new/', views.new_list, name='new_list'),
    path('lists/mine/', views.my_lists, name='my_lists'),
    path('lists/<int:list_id>/', views.view_list, name='view_list'),
    path('lists/<int:list_id>/share/', views.share_list, name='share_list'),
    path('lists/<int:list_id>/delete/', views.delete_list, name='delete_list'),
    path('items/<int:item_id>/toggle/', views.toggle_item, name='toggle_item'),
    path('items/<int:item_id>/delete/', views.delete_item, name='delete_item'),
]
