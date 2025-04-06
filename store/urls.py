from django.urls import path

from . import views

urlpatterns = [
	#Leave as empty string for base url
	path('', views.store, name="store"),
	path('cart/', views.cart, name="cart"),
	path('checkout/', views.checkout, name="checkout"),

	path('update_item/', views.updateItem, name="update_item"),
	path('process_order/', views.processOrder, name="process_order"),
 
 path('update-quantity/', views.update_quantity, name='update_quantity'),
path('remove-from-cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
path('clear-cart/', views.clear_cart, name='clear_cart'),

]