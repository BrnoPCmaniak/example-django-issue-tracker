from typing import Dict, List

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib.auth.models import User
from django.db.models import Avg, Max, Min, Q
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import View
from django.views.generic import CreateView, DetailView, ListView
from django.views.generic.detail import SingleObjectMixin

from .forms import IssueEditForm
from .models import ISSUE_ASSIGNED, ISSUE_CREATED, ISSUE_DONE, Issue, IssueCategory
from .tools import (
    AjaxBootstrapSelectView, BootstrapEditableView, DeleteRedirectView, and_merge_queries)


class ListIssueView(ListView):
    model = Issue
    template_name = "tracker/list.html"

    def get_context_data(self, *args, **kwargs) -> dict:
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

    def get_context_data(self, *args, **kwargs) -> dict:
        context = super().get_context_data(*args, **kwargs)
        context["categories"] = [(c.pk, c.name) for c in IssueCategory.objects.all()]
        return context


class IssueEditView(BootstrapEditableView):
    model = Issue
    form_class = IssueEditForm
    fields = ["name", "category", "description", "solver"]

    def test_func(self):
        return self.request.user.has_perm("tracker.change_issue")


class UserSelectView(PermissionRequiredMixin, AjaxBootstrapSelectView):
    search_model = User
    permission_required = "tracker.change_issue"

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


class IssueCreateView(PermissionRequiredMixin, CreateView):
    permission_required = "tracker.create_issue"
    model = Issue
    fields = ("name", "category", "description")

    def form_valid(self, form) -> HttpResponseRedirect:
        """If the form is valid, save the associated model."""
        self.object = form.save(commit=False)
        self.object.created_by = self.request.user
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class IssueDeleteView(PermissionRequiredMixin, DeleteRedirectView):
    permission_required = "tracker.delete_issue"
    model = Issue
    success_url = reverse_lazy("list")


class IssueUnassignedView(PermissionRequiredMixin, SingleObjectMixin, View):
    model = Issue
    success_url = reverse_lazy("issue-detail")
    permission_required = "tracker.change_issue"

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        self.object = self.get_object()
        if self.object.state == ISSUE_ASSIGNED:
            self.object.solver = None
            self.object.assigned_at = None
            self.object.state = ISSUE_CREATED
            self.object.save()
        return HttpResponseRedirect(reverse("issue-detail", args=[self.object.pk]))


class IssueDoneView(SingleObjectMixin, View):
    model = Issue
    success_url = reverse_lazy("issue-detail")

    def get(self, request, *args, **kwargs) -> HttpResponseRedirect:
        self.object = self.get_object()
        if self.object.state == ISSUE_ASSIGNED and request.user.has_perm(
                "tracker.change_issue") or request.user == self.object.solver:
            self.object.state = ISSUE_DONE
            self.object.save()
        return HttpResponseRedirect(reverse("issue-detail", args=[self.object.pk]))
