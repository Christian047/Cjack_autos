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
    # path('auth/', include('authentication.urls')),
    # path('reviews/', include('reviews.urls')),
    # path('sendmail/', include('sendmail.urls')),
    # path('payments/', include('payments.urls')),
    # path('like/', include('like.urls')),
    # path('usercrud/', include('usercrud.urls')),
    # path('accounts/', include('allauth.urls')),

    
    ]


# append static url and root folder to urlpatterns
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


