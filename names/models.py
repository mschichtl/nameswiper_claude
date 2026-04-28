import uuid
from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class NameGroup(models.Model):
    SEX_MALE = 'M'
    SEX_FEMALE = 'F'
    SEX_NEUTRAL = 'N'
    SEX_CHOICES = [
        (SEX_MALE, 'Male'),
        (SEX_FEMALE, 'Female'),
        (SEX_NEUTRAL, 'Neutral'),
    ]
    sex = models.CharField(max_length=1, choices=SEX_CHOICES)

    def display_name(self):
        return ' / '.join(self.variants.values_list('name', flat=True))

    def __str__(self):
        return self.display_name()


class NameVariant(models.Model):
    group = models.ForeignKey(NameGroup, related_name='variants', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class NamingGroup(models.Model):
    name = models.CharField(max_length=200)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_naming_groups')
    members = models.ManyToManyField(User, through='GroupMembership', related_name='naming_groups')
    invite_token = models.UUIDField(default=uuid.uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GroupMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    group = models.ForeignKey(NamingGroup, on_delete=models.CASCADE)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'group']


class Swipe(models.Model):
    LIKE = 'like'
    DISLIKE = 'dislike'
    SKIP = 'skip'
    DECISION_CHOICES = [
        (LIKE, 'Like'),
        (DISLIKE, 'Dislike'),
        (SKIP, 'Skip'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='swipes')
    name_group = models.ForeignKey(NameGroup, on_delete=models.CASCADE, related_name='swipes')
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'name_group']

    def __str__(self):
        return f'{self.user.username} → {self.name_group} ({self.decision})'


class Score(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='scores')
    name_group = models.ForeignKey(NameGroup, on_delete=models.CASCADE, related_name='scores')
    stars = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    preferred_variants = models.ManyToManyField(
        NameVariant, blank=True, related_name='preferred_in_scores'
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['user', 'name_group']

    def __str__(self):
        return f'{self.user.username} → {self.name_group} ({self.stars}★)'
