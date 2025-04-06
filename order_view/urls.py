from django.urls import path
from . import views



urlpatterns = [
    path('', views.order_list, name='orders'),
    # path('confirm<int:pending_id>/', views.confirm_order, name='confirm'),
    path('dashboard/', views.admin_dashboard, name='admin_dashboard'),
    
    # Order management
    path('orders/', views.order_list, name='order_list'),
    path('mark_order_complete/<int:order_id>/', views.order_list, name='mark_order_complete'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    

    path('debug/', views.debug_order_view, name='debug_order_view'),
  
    
    # Order detail views
    path('detail/<int:order_id>/', views.order_detail, name='order_detail'),
    
    # Order actions
    path('complete/<int:order_id>/', views.mark_order_complete, name='mark_order_complete'),
    
    # Sales reports
    path('reports/', views.sales_report, name='sales_report'),

]