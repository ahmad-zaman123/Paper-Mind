from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated

from apps.users.serializers import RegisterSerializer, UserSerializer


class RegisterAPIView(generics.CreateAPIView):
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class MeAPIView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_object(self, *args, **kwargs):
        return self.request.user
