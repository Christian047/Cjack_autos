from django.urls import path
from .views import *

urlpatterns = [
    path('', Suscribe.as_view(), name='suscribe'),
]
