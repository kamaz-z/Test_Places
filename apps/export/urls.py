from django.urls import path

from .views import PlaceExportView

urlpatterns = [
    path('places/', PlaceExportView.as_view(), name='places-export'),
]