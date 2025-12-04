# accounts/serializers.py
from rest_framework import serializers
from .models import User
from django.contrib.auth.password_validation import validate_password
from django.conf import settings


class UserSerializer(serializers.ModelSerializer):
    profile_image_url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "status", "date_joined", "profile_image_url", "phone_number"]

    def get_profile_image_url(self, obj):
        request = self.context.get('request')
        if obj.profile_image:
            # Build absolute URL if request available
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None

class SignupSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = User
        fields = ["id", "username", "email", "password"]

    def create(self, validated_data):
        user = User(
            username=validated_data["username"],
            email=validated_data["email"],
        )
        user.set_password(validated_data["password"])
        user.save()
        return user


class ProfileImageUploadSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def validate_image(self, value):
        # Optional: validate size (<= 5MB) and format
        max_size = 5 * 1024 * 1024
        if value.size > max_size:
            raise serializers.ValidationError('파일 크기는 5MB 이하이어야 합니다.')
        if value.content_type not in ['image/jpeg', 'image/png', 'image/gif']:
            raise serializers.ValidationError('JPG, PNG, GIF 형식만 허용됩니다.')
        return value

class ProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "phone_number", "avatar"]

    def get_avatar(self, obj):
        request = self.context.get('request')
        if obj.profile_image:
            if request:
                return request.build_absolute_uri(obj.profile_image.url)
            return obj.profile_image.url
        return None

    def update(self, instance, validated_data):
        request = self.context.get('request')
        # 처리할 수 있는 필드: first_name, last_name, email, phone_number
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.email = validated_data.get('email', instance.email)
        instance.phone_number = validated_data.get('phone_number', instance.phone_number)

        # avatar 처리: 파일 업로드 또는 avatar_clear 플래그
        if request and request.FILES.get('avatar'):
            # 기존 파일 삭제
            if instance.profile_image:
                try:
                    instance.profile_image.delete(save=False)
                except Exception:
                    pass
            instance.profile_image = request.FILES.get('avatar')
        else:
            # avatar_clear 플래그가 있으면 삭제
            avatar_clear = request.data.get('avatar_clear') if request else None
            if avatar_clear in ['1', 'true', 'True', True]:
                if instance.profile_image:
                    try:
                        instance.profile_image.delete(save=False)
                    except Exception:
                        pass
                    instance.profile_image = None

        instance.save()
        return instance
