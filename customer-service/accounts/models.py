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


