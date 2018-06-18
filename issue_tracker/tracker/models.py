from datetime import datetime

from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

ISSUE_ASSIGNED = "ass"
ISSUE_DONE = "don"
ISSUE_CANCELED = "can"
ISSUE_CREATED = "cre"
ISSUE_STATE_CHOICES = (
    (ISSUE_ASSIGNED, _("Assigned")),
    (ISSUE_DONE, _("Done")),
    (ISSUE_CANCELED, _("Canceled")),
    (ISSUE_CREATED, _("Created"))
)


class IssueCategory(models.Model):
    name = models.CharField(verbose_name=_("Name"), help_text=_("The name of the issue category."), max_length=254)

    class Meta:
        verbose_name = _("Issue category")
        verbose_name_plural = _("Issue categories")


    def __str__(self):
        return self.name


class Issue(models.Model):
    name = models.CharField(verbose_name=_("Name"), help_text=_("The name of the issue."), max_length=254)
    created_by = models.ForeignKey(User, verbose_name=_("Created by"),
                                   help_text=_("The person which created the issue."), on_delete=models.CASCADE,
                                   related_name="issues")
    solver = models.ForeignKey(User, verbose_name=_("Solver"), help_text=_("The assigned solver of this issue."),
                               blank=True, null=True, on_delete=models.SET_NULL, related_name="solving_issues")
    category = models.ForeignKey(IssueCategory, verbose_name=_("Category"), help_text=_("The category of the issue."),
                                 blank=True, null=True, on_delete=models.SET_NULL)
    state = models.CharField(choices=ISSUE_STATE_CHOICES, verbose_name=_("State"),
                             help_text=_("The state of the issue."), null=False, blank=False, default=ISSUE_CREATED,
                             max_length=4)
    description = models.TextField(verbose_name=_("Description"), help_text=_("The description of the issue."))
    completed_in = models.DurationField(blank=True, null=True, verbose_name=_("Completed in"),
                                        help_text=_("The time duration in which the task was completed."))
    created_at = models.DateTimeField(verbose_name=_("Created"), auto_now_add=True)

    def save(self, *args, **kwargs):
        if self.state == ISSUE_CREATED and self.solver is not None:
            self.state = ISSUE_ASSIGNED
        elif self.state == ISSUE_DONE and self.completed_in is None:
            self.completed_in = datetime.now() - self.created_at
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")
