from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings 
from django.conf.urls.static import static  

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="Test description",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # API App
    path('api/', include('api.urls')),

    # Auth using Djoser with JWT
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),  # OR use .authtoken if not using JWT


    path('accounts/', include('allauth.socialaccount.urls')),  # enables /accounts/google/login/

    path('auth/registration/', include('dj_rest_auth.registration.urls')),

    # Swagger & Redoc Docs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)






# from django.contrib import admin
# from django.urls import path, include
# from drf_yasg.views import get_schema_view
# from drf_yasg import openapi
# from rest_framework import permissions

# schema_view = get_schema_view(
#     openapi.Info(
#         title="Snippets API",
#         default_version='v1',
#         description="Test description",
#         terms_of_service="https://www.google.com/policies/terms/",
#         contact=openapi.Contact(email="contact@snippets.local"),
#         license=openapi.License(name="BSD License"),
#     ),
#     public=True,
#     permission_classes=(permissions.AllowAny,),
# )

# urlpatterns = [
#     # Swagger and ReDoc Docs
#     path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
#     path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
#     path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

#     # Admin Panel
#     path('admin/', admin.site.urls),

#     # Your API Routes
#     path('api/', include('api.urls')),

#     #  Auth (Djoser - only one set of URLs is needed)
#     path('auth/', include('djoser.urls')),
#     path('auth/', include('djoser.urls.jwt')),  # JWT-based auth

#     #  Allauth - Social Login URLs (required for Google login)
#     path('accounts/', include('allauth.socialaccount.urls')),  # enables /accounts/google/login/

#     #  dj-rest-auth (if you're using it)
#     path('auth/rest/', include('dj_rest_auth.urls')),
#     path('auth/rest/registration/', include('dj_rest_auth.registration.urls')),
# ]
