import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Organization(models.Model):
    """A tenant organization in the ESG platform."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self) -> str:
        return self.name


class User(AbstractUser):
    """Custom user model with UUID pk, organization FK, and role."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    organization = models.ForeignKey(
        Organization,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name='users',
    )

    ROLES = [
        ('analyst', 'Analyst'),
        ('reviewer', 'Reviewer'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLES, default='analyst')

    class Meta:
        ordering = ['username']

    def __str__(self) -> str:
        return self.email or self.username
