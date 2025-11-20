from rest_framework import serializers
from .models import User, LawyerProfile

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'role', 'phone', 'birth_date', 'gender', 'first_name')

class PersonalSignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    name = serializers.CharField()
    phone_number = serializers.CharField(allow_blank=True, required=False)
    birth_date = serializers.CharField(allow_blank=True, required=False)
    gender = serializers.CharField(allow_blank=True, required=False)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=validated_data.get('name', ''),
            role='personal',
            phone=validated_data.get('phone_number', ''),
            birth_date=validated_data.get('birth_date', ''),
            gender=validated_data.get('gender', ''),
        )
        return user

class LawyerSignupSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField()
    name = serializers.CharField()
    phone_number = serializers.CharField()
    birth_date = serializers.CharField()
    gender = serializers.CharField()
    license_number = serializers.CharField()
    office_name = serializers.CharField(allow_blank=True, required=False)
    career = serializers.CharField(allow_blank=True, required=False)
    introduction = serializers.CharField(allow_blank=True, required=False)
    signup_source = serializers.CharField(allow_blank=True, required=False)

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            email=validated_data['email'],
            first_name=validated_data['name'],
            role='lawyer',
            phone=validated_data['phone_number'],
            birth_date=validated_data['birth_date'],
            gender=validated_data['gender'],
        )
        LawyerProfile.objects.create(
            user=user,
            license_number=validated_data['license_number'],
            office_name=validated_data.get('office_name', ''),
            career=validated_data.get('career', ''),
            introduction=validated_data.get('introduction', ''),
            signup_source=validated_data.get('signup_source', ''),
        )
        return user
