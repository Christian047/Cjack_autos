from django.urls import path
from . import views


app_name = 'filter'  # This is important for namespacing your URLs


urlpatterns = [

    path('products/search/', views.advanced_search_view, name='advanced_search'),
    
    # API endpoint for the search functionality
    path('api/products/search/', views.product_search_api, name='product_search_api'),
    

]

