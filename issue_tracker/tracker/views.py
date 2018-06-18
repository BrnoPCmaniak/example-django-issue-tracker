from django.db.models import Avg, Max, Min
from django.views.generic import ListView, DetailView

from .models import Issue


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
