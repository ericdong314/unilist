from django.contrib import admin

from .models import Item, List


class ItemInline(admin.TabularInline):
    model = Item
    extra = 0


@admin.register(List)
class ListAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'owner')
    list_filter = ('owner',)
    inlines = [ItemInline]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('text', 'list')
    search_fields = ('text',)
