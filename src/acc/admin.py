from django.contrib import admin

from .models import Token, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    search_fields = ('email',)


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ('email', 'created_at', 'uid')
    search_fields = ('email',)
    readonly_fields = ('uid', 'created_at')
