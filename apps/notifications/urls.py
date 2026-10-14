from django.urls import path

from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.subscription_list, name='subscriptions'),
]
