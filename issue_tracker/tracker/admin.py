from django.contrib import admin

# Register your models here.
from .models import Issue, IssueCategory

admin.site.register(IssueCategory)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "solver", "category", "state")
