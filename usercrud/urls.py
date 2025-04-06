from django.urls import path
from .views import *


urlpatterns = [
    path('profile/', ProfileView.as_view(), name='profile'),
    # path('profilepage', ProfilePage.as_view(), name='profilepage'),
    # path('updateprofile', UserProfileUpdateView.as_view(), name='updateprofile'),

]