from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', include('users.urls')),
    path('api/v1/', include('samples.urls')),
    path('api/v1/', include('workflows.urls')),
    path('api/v1/', include('reports.urls')),
]
