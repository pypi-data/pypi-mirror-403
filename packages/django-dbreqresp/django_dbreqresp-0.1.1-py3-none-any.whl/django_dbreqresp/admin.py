from django.contrib import admin

from .models import RequestLog


@admin.register(RequestLog)
class RequestLogAdmin(admin.ModelAdmin):
    list_display = ["start", "user", "duration", "method", "url", "response_status"]
    search_fields = ("url", "response_status")
    list_filter = ["response_status", "start", "user", "method"]
