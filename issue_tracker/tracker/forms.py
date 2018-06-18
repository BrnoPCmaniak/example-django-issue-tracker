from django.forms import ModelForm

from .models import Issue


class IssueEditForm(ModelForm):
    class Meta:
        model = Issue
        fields = ("name", "category", "description")
