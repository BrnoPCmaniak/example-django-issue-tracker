from django.db.models import Avg, Max, Min
from django.views.generic import DetailView, ListView

from .forms import IssueEditForm
from .models import Issue, IssueCategory
from .tools import BootstrapEditableView


class ListIssueView(ListView):
    model = Issue
    template_name = "tracker/list.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        numbers = Issue.objects.exclude(completed_in__isnull=True).aggregate(
            Avg('completed_in'), Max('completed_in'), Min('completed_in'))
        context["avg"] = numbers["completed_in__avg"]
        context["min"] = numbers["completed_in__min"]
        context["max"] = numbers["completed_in__max"]
        return context


class DetailIssueView(DetailView):
    model = Issue
    template_name = "tracker/detail.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["categories"] = [(c.pk, c.name) for c in IssueCategory.objects.all()]
        return context


class IssueEditView(BootstrapEditableView):
    model = Issue
    form_class = IssueEditForm
    fields = ["name", "category", "description"]
