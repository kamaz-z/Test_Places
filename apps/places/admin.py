from django.contrib import admin

from .models import Place


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'author', 'created_at', 'deleted_at')
    list_filter = ('category', 'deleted_at')
    search_fields = ('title', 'address')

    def get_queryset(self, request):
        return Place.all_objects.select_related('category', 'author')