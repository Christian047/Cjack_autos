from django.contrib import admin
from django.urls import path, include

# Import media related methods/libraries
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('base.urls')),
    path('store/', include('store.urls')),
    path('payments/', include('payments.urls')),
    path('receipts/', include('receipts.urls')),
    path('order/', include('order_view.urls')),

    ]



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


