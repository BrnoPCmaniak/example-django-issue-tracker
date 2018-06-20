from datetime import timedelta

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
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
    name = models.CharField(
        verbose_name=_("Name"), help_text=_("The name of the issue."), max_length=254)
    created_by = models.ForeignKey(
        User, verbose_name=_("Created by"), help_text=_("The person which created the issue."),
        on_delete=models.CASCADE, related_name="issues")
    solver = models.ForeignKey(
        User, verbose_name=_("Solver"), help_text=_("The assigned solver of this issue."),
        blank=True, null=True, on_delete=models.SET_NULL, related_name="solving_issues")
    category = models.ForeignKey(
        IssueCategory, verbose_name=_("Category"), help_text=_("The category of the issue."),
        blank=True, null=True, on_delete=models.SET_NULL)
    state = models.CharField(
        choices=ISSUE_STATE_CHOICES, verbose_name=_("State"), help_text=_("The state of the issue."), null=False,
        blank=False, default=ISSUE_CREATED, max_length=4)
    description = models.TextField(
        verbose_name=_("Description"), help_text=_("The description of the issue."))
    completed_in = models.DurationField(
        blank=True, null=True, verbose_name=_("Completed in"),
        help_text=_("The time duration in which the task was completed."))
    assigned_at = models.DateTimeField(
        verbose_name=_("Assiged at"), blank=True, null=True)
    created_at = models.DateTimeField(
        verbose_name=_("Created"), auto_now_add=True)

    def clean(self):
        """Validate state with other fields."""
        if self.state == ISSUE_ASSIGNED and self.solver is None:
            raise ValidationError(_('State marked as assigned but no solver is assigned.'))
        super().clean()

    def save(self, *args, **kwargs):
        if self.state == ISSUE_CREATED and self.solver is not None:
            self.state = ISSUE_ASSIGNED
            self.assigned_at = timezone.now()
        elif self.state == ISSUE_DONE and self.completed_in is None and (
                self.assigned_at is not None or self.created_at is not None):
            self.completed_in = timedelta(seconds=int((timezone.now() - (self.assigned_at or self.created_at)).seconds))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('issue-detail', args=[str(self.id)])

    class Meta:
        verbose_name = _("Issue")
        verbose_name_plural = _("Issues")
