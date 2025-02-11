from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from app import views

urlpatterns = [
    path('', views.main, name='main'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('types/', views.types, name='types'),
    path('type/<id_type_offense>/new_app/', views.new_app, name='new_app'),
    path('logout/', views.logout, name='logout'),
    path('activate/<id_user_urlencode>/<token_urlencode>', views.activate, name='activate')
]  +static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
