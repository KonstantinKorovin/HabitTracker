from django.urls import path

from users.apps import UsersConfig
from users.views import CustomUserRegisterView

app_name = UsersConfig.name


urlpatterns = [path("register/", CustomUserRegisterView.as_view(), name="register")]
