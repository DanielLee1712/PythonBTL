# Module: root

## __init__.py

\`\`\`python

\`\`\`

---

## admin.py

\`\`\`python
from django.contrib import admin

# Register your models here.

\`\`\`

---

## apps.py

\`\`\`python
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

\`\`\`

---

## models.py

\`\`\`python
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator

class CustomUser(AbstractUser):
    username = models.CharField(
        "username",
        max_length=150,
        unique=True,
        help_text="Required. 150 characters or fewer. Letters, digits and spaces allowed.",
        validators=[RegexValidator(r'^[\w.@+-/ ]+$', "Enter a valid username.")],
        error_messages={
            "unique": "A user with that username already exists.",
        },
    )



\`\`\`

---

## serializers.py

\`\`\`python
from rest_framework import serializers
from .models import CustomUser

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'password')
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        return user

\`\`\`

---

## tests.py

\`\`\`python
from django.test import TestCase

# Create your tests here.

\`\`\`

---

## urls.py

\`\`\`python
from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import RegisterView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]

\`\`\`

---

## views.py

\`\`\`python
from rest_framework import generics, permissions
from .models import CustomUser
from .serializers import UserSerializer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = UserSerializer

\`\`\`

---

