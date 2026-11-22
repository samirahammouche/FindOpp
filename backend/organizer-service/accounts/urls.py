from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("token/", views.token_login, name="token_login"),
    path("demo/", views.demo_login, name="demo_login"),
    path("logout/", views.logout_view, name="logout"),
]
