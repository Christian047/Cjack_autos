# receipts/urls.py
from django.urls import path
from . import views

app_name = 'receipts'

urlpatterns = [
    path('download/<int:order_id>/', views.download_receipt, name='download_receipt'),
    path('email/<int:order_id>/', views.email_receipt, name='email_receipt'),
]