from django.contrib import admin
from .models import NameGroup, NameVariant, NamingGroup, GroupMembership, Swipe, Score


class NameVariantInline(admin.TabularInline):
    model = NameVariant
    extra = 1


@admin.register(NameGroup)
class NameGroupAdmin(admin.ModelAdmin):
    list_display = ['display_name', 'sex']
    list_filter = ['sex']
    inlines = [NameVariantInline]


@admin.register(NamingGroup)
class NamingGroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'owner', 'created_at']
    list_filter = ['created_at']


@admin.register(GroupMembership)
class GroupMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'group', 'joined_at']


@admin.register(Swipe)
class SwipeAdmin(admin.ModelAdmin):
    list_display = ['user', 'name_group', 'decision', 'updated_at']
    list_filter = ['decision']


@admin.register(Score)
class ScoreAdmin(admin.ModelAdmin):
    list_display = ['user', 'name_group', 'stars', 'updated_at']
    list_filter = ['stars']
