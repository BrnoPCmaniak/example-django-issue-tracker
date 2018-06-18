from django.contrib import admin

# Register your models here.
from .models import IssueCategory, Issue

admin.site.register(IssueCategory)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "solver", "category", "state")
