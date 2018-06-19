from django.contrib.auth import views as auth_views
from django.urls import path

from .views import DetailIssueView, IssueCreateView, IssueEditView, ListIssueView, UserSelectView

urlpatterns = [
    path('accounts/login', auth_views.login,
         {'template_name': 'tracker/signin.html'}, name='login'
         ),
    path('accounts/logout', auth_views.logout,
         {'next_page': '/accounts/login?logout=1'}, name='logout'
         ),
    path('home', ListIssueView.as_view(), name="list"),
    path('issue/<int:pk>/', DetailIssueView.as_view(), name='issue-detail'),
    path('issue/edit/<int:pk>', IssueEditView.as_view(), name="issue-edit"),
    path('users', UserSelectView.as_view(), name="user-select"),
    path('issue/create', IssueCreateView.as_view(), name="issue-create")
]
