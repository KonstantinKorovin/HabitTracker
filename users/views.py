from rest_framework import generics, permissions

from users.models import CustomUser
from users.serializers import CustomUserSerializer


class CustomUserRegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.AllowAny]
