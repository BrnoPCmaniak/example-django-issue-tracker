from typing import Dict, List

from django.contrib.auth.models import User
from django.db.models import Avg, Max, Min, Q
from django.http import HttpResponseRedirect
from django.views.generic import CreateView, DetailView, ListView

from .forms import IssueEditForm
from .models import Issue, IssueCategory
from .tools import AjaxBootstrapSelectView, BootstrapEditableView, and_merge_queries


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
    fields = ["name", "category", "description", "solver"]


class UserSelectView(AjaxBootstrapSelectView):
    search_model = User

    def get_query(self) -> Q:
        """Make query to look in user in first_name, last_name and username."""
        queries = []
        for q in self.request.POST["q"].split(" "):
            queries.append(Q(first_name__icontains=q) |
                           Q(last_name__icontains=q) |
                           Q(username__icontains=q))
        return and_merge_queries(queries)

    def prepare_json_list(self, obj_list) -> List[Dict[str, str]]:
        """Create list of dicts for json."""
        return [{"ID": obj.pk, "Name": obj.get_full_name() or obj.username, "Username": obj.username} for obj in
                obj_list]


class IssueCreateView(CreateView):
    model = Issue
    fields = ("name", "category", "description")

    def form_valid(self, form):
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())
