# accounts/views.py
from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import SignupSerializer, UserSerializer, ProfileImageUploadSerializer, ProfileSerializer
from .models import User
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

class MeView(generics.RetrieveAPIView):
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class ProfileImageUploadView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, format=None):
        serializer = ProfileImageUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        image = serializer.validated_data['image']
        user = request.user

        # 기존 이미지가 있으면 삭제(선택사항: 파일 시스템에서 삭제하고 싶다면 저장 방식에 따라 처리)
        # if user.profile_image:
        #     try:
        #         user.profile_image.delete(save=False)
        #     except Exception:
        #         pass

        user.profile_image = image
        user.save()

        # 반환할 URL
        profile_url = None
        if user.profile_image:
            profile_url = request.build_absolute_uri(user.profile_image.url)

        return Response({"profile_image_url": profile_url}, status=status.HTTP_200_OK)


class ProfileMeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        serializer = ProfileSerializer(request.user, context={'request': request})
        return Response(serializer.data)

    def put(self, request):
        return self.partial_update(request)

    def patch(self, request):
        return self.partial_update(request)

    def partial_update(self, request):
        serializer = ProfileSerializer(request.user, data=request.data, partial=True, context={'request': request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        new_password_confirm = request.data.get('new_password_confirm')

        if not current_password or not new_password or not new_password_confirm:
            return Response({'detail': '모든 비밀번호 필드를 입력하세요.'}, status=status.HTTP_400_BAD_REQUEST)

        if new_password != new_password_confirm:
            return Response({'detail': '새 비밀번호와 확인이 일치하지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user
        if not user.check_password(current_password):
            return Response({'detail': '현재 비밀번호가 올바르지 않습니다.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            validate_password(new_password, user)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({'detail': '비밀번호가 변경되었습니다.'})
