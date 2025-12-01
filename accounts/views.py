# accounts/views.py
from rest_framework import generics, permissions
from .serializers import SignupSerializer, UserSerializer
from .models import User

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
