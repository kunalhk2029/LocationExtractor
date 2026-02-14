from django.contrib import admin
from .models import ReelJob


@admin.register(ReelJob)
class ReelJobAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "created_at", "result_city", "result_country")
    list_filter = ("status", "created_at")
    search_fields = ("source_url", "result_city", "result_country")
