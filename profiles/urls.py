from django.urls import path
from . import views

app_name = 'profiles'

urlpatterns = [
    path('',views.profile_view,name='profile'),
    path('login/',views.login_view,name='login'),
    path('register/',views.register_view,name='register'),
    path('logout/',views.logout_view,name='logout'),
]