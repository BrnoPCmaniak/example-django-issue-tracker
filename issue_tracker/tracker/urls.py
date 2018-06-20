from django.contrib.auth import views as auth_views
from django.urls import path

from .views import (
    CreateIssueView, DeleteIssueView, DetailIssueView, DoneIssueView, EditIssueView, ListIssueView,
    UnassignedIssueView, UserSelectView)

urlpatterns = [
    path('accounts/login/', auth_views.login,
         {'template_name': 'tracker/signin.html'}, name='login'
         ),
    path('accounts/logout/', auth_views.logout,
         {'next_page': '/accounts/login?logout=1'}, name='logout'
         ),

    path('', ListIssueView.as_view(), name="issues-list"),
    path('issue/create/', CreateIssueView.as_view(), name="issue-create"),
    path('issue/<int:pk>/', DetailIssueView.as_view(), name='issue-detail'),
    path('issue/edit/<int:pk>/', EditIssueView.as_view(), name="issue-edit"),
    path('issue/delete/<int:pk>/', DeleteIssueView.as_view(), name="issue-delete"),
    path('issue/unassign/<int:pk>/', UnassignedIssueView.as_view(), name="issue-unassign"),
    path('issue/done/<int:pk>/', DoneIssueView.as_view(), name="issue-done"),
    path('users/', UserSelectView.as_view(), name="user-select"),

]
