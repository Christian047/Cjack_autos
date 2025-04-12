from django.urls import path
from .views import *

urlpatterns = [
    path('', Home.as_view(), name='home'),
    path('products/', ProductView.as_view(), name='products'),
    path('single_product/<int:pk>/', ProductDetailView.as_view(), name='single_product'),
    path('about/', AboutView.as_view(), name='about'),
    path('search/', SearchView.as_view(), name='search'),
    path('wishlist/toggle/', toggle_wishlist, name='toggle_wishlist'),
    path('wishlist/', wishlist, name='wishlist'),
    path('car_model/<int:pk>/', car_model_items, name='car_model'),
    
    path('autocomplete/', autocomplete, name='autocomplete'),
    path('sync_guest_cart/', SyncGuestCartView.as_view(), name='sync_guest_cart'),
]