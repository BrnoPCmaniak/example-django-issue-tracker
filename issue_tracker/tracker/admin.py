from django.contrib import admin

# Register your models here.
from .models import Issue, IssueCategory

admin.site.register(IssueCategory)


@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ("name", "created_by", "solver", "category", "state")
    fields = ("name", "created_by", "solver", "category", "state", "description")
    readonly_fields = ('created_by',)

    def save_model(self, request, obj, form, change):
        """When new objects is created save it's author."""
        if obj.pk is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
