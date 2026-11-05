from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from apps.users.views import (
    ChangePasswordAPIView,
    DemoAPIView,
    ForgotPasswordAPIView,
    GoogleAuthAPIView,
    LoginAPIView,
    MeAPIView,
    RegisterAPIView,
    ResetPasswordAPIView,
)

urlpatterns = (
    path("auth/register/", RegisterAPIView.as_view(), name="auth-register"),
    path("auth/token/", LoginAPIView.as_view(), name="auth-token"),
    path("auth/demo/", DemoAPIView.as_view(), name="auth-demo"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="auth-token-refresh"),
    path("auth/me/", MeAPIView.as_view(), name="auth-me"),
    path("auth/google/", GoogleAuthAPIView.as_view(), name="auth-google"),
    path("auth/password/", ChangePasswordAPIView.as_view(), name="auth-password"),
    path("auth/password/forgot/", ForgotPasswordAPIView.as_view(), name="auth-password-forgot"),
    path("auth/password/reset/", ResetPasswordAPIView.as_view(), name="auth-password-reset"),
)
