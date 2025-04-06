from django.urls import path
from .views import *

urlpatterns = [
  path('like_review/', like_review, name='like_review'),
]
