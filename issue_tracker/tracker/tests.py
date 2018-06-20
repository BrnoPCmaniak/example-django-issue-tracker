from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.test import Client, TestCase

from tracker.models import ISSUE_ASSIGNED, ISSUE_CREATED, ISSUE_DONE, Issue, IssueCategory


class ModelTestCase(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create(username="user_a")
        self.test_user_2 = User.objects.create(username="user_b")

    def test_assign(self):
        """Test that when user is assigned the state changes too."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, description="Test description.")

        self.assertEqual(issue.state, ISSUE_CREATED)
        self.assertIsNone(issue.solver)

        issue.solver = self.test_user_2
        issue.save()

        self.assertEqual(issue.state, ISSUE_ASSIGNED)
        self.assertEqual(issue.solver, self.test_user_2)
        self.assertIsNotNone(issue.assigned_at)

    def test_done(self):
        """Test that when state is done the duration is calculated."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, description="Test description.",
                                     solver=self.test_user_2)

        self.assertEqual(issue.state, ISSUE_ASSIGNED)
        self.assertEqual(issue.solver, self.test_user_2)
        self.assertIsNotNone(issue.assigned_at)

        issue.state = ISSUE_DONE
        issue.save()

        self.assertEqual(issue.state, ISSUE_DONE)
        self.assertIsNotNone(issue.completed_in)


class EditTestCase(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create(username="user_a", is_superuser=True)
        self.test_user_2 = User.objects.create(username="user_b")

        self.issue = Issue.objects.create(name="Test", created_by=self.test_user_1, description="Test description.")

        self.category = IssueCategory.objects.create(name="Test")
        self.client = Client()
        self.client.force_login(self.test_user_1)

    def test_name(self):
        """Test changing name via API."""
        new_value = "Test change"

        response = self.client.post("/issue/edit/%d/" % self.issue.pk, {"name": "name", "value": new_value})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Issue.objects.get(pk=self.issue.pk).name, new_value)

    def test_description(self):
        """Test changing description via API."""
        new_value = "Test longer description."

        response = self.client.post("/issue/edit/%d/" % self.issue.pk, {"name": "description", "value": new_value})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Issue.objects.get(pk=self.issue.pk).description, new_value)

    def test_category(self):
        """Test changing category via API."""
        new_value = self.category.pk

        response = self.client.post("/issue/edit/%d/" % self.issue.pk, {"name": "category", "value": new_value})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Issue.objects.get(pk=self.issue.pk).category_id, new_value)

    def test_solver(self):
        """Test assigning solver via API."""
        new_value = self.test_user_2.pk

        response = self.client.post("/issue/edit/%d/" % self.issue.pk, {"name": "solver", "value": new_value})

        self.assertEqual(response.status_code, 200)
        issue = Issue.objects.get(pk=self.issue.pk)
        self.assertEqual(issue.solver_id, new_value)
        self.assertEqual(issue.state, ISSUE_ASSIGNED)

    def test_permission_denied(self):
        """Test change without permission won't do anything."""
        c = Client()
        c.force_login(self.test_user_2)

        i = Issue.objects.get(pk=self.issue.pk)
        response = c.post("/issue/edit/%d/" % self.issue.pk, {"name": "name", "value": "XX"})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(Issue.objects.get(pk=i.pk).name, i.name)


class UserSelectViewTestCase(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create(username="user_a", is_superuser=True)
        self.test_user_2 = User.objects.create(username="user_b")

        self.client = Client()
        self.client.force_login(self.test_user_1)

    def test_username_search(self):
        """Test searching for users by their username."""
        u = User.objects.create(username="user_c")
        response = self.client.post("/users/", {"q": u.username})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('[{"ID": %d, "Name": "%s", "Username": "%s"}]' % (u.pk, u.username, u.username),
                         response.content.decode('ascii'))

    def test_first_name_search(self):
        """Test searching for users by their first name."""
        u = User.objects.create(username="user_d", first_name="John", last_name="Smith")
        response = self.client.post("/users/", {"q": u.first_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('[{"ID": %d, "Name": "%s", "Username": "%s"}]' % (u.pk, u.get_full_name(), u.username),
                         response.content.decode('ascii'))

    def test_last_name_search(self):
        """Test searching for users by their last name."""
        u = User.objects.create(username="user_e", first_name="John", last_name="Smith")
        response = self.client.post("/users/", {"q": u.last_name})
        self.assertEqual(response.status_code, 200)
        self.assertEqual('[{"ID": %d, "Name": "%s", "Username": "%s"}]' % (u.pk, u.get_full_name(), u.username),
                         response.content.decode('ascii'))

    def test_permission_denied(self):
        """Test that users without permission can't search anyone."""
        c = Client()
        c.force_login(self.test_user_2)
        u = User.objects.create(username="user_f")

        response = c.post("/users/", {"q": "user_f"})
        self.assertEqual(response.status_code, 302)


class DeleteViewTestCase(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create(username="user_a", is_superuser=True)
        self.test_user_2 = User.objects.create(username="user_b")

        self.client = Client()
        self.client.force_login(self.test_user_1)

    def test_delete(self):
        """Test deletion of an Issue."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, description="Test description.")
        response = self.client.get("/issue/delete/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        self.assertRaises(ObjectDoesNotExist, Issue.objects.get, pk=issue.pk)

    def test_permission_denied(self):
        """When user doesn't have permission do nothing."""
        c = Client()
        c.force_login(self.test_user_2)

        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, description="Test description.")
        response = c.get("/issue/delete/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Issue.objects.get(pk=issue.pk).name, issue.name)


class IssueDoneTestCase(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create(username="user_a", is_superuser=True)
        self.test_user_2 = User.objects.create(username="user_b")
        self.test_user_3 = User.objects.create(username="user_c")

        self.client_1 = Client()
        self.client_1.force_login(self.test_user_1)
        self.client_2 = Client()
        self.client_2.force_login(self.test_user_2)

    def test_superuser_done(self):
        """Test marking issue as done as superuser."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, solver=self.test_user_2,
                                     description="Test description.")
        response = self.client_1.get("/issue/done/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Issue.objects.get(pk=issue.pk).state, ISSUE_DONE)

    def test_solver_done(self):
        """Test marking issue as done as solver."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, solver=self.test_user_2,
                                     description="Test description.")
        response = self.client_2.get("/issue/done/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Issue.objects.get(pk=issue.pk).state, ISSUE_DONE)

    def test_permission_denied(self):
        """When user doesn't haver permission do nothing."""
        c = Client()
        c.force_login(self.test_user_3)

        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, solver=self.test_user_2,
                                     description="Test description.")

        response = c.get("/issue/done/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        self.assertNotEqual(Issue.objects.get(pk=issue.pk).state, ISSUE_DONE)


class UnassignedTestCase(TestCase):
    def setUp(self):
        self.test_user_1 = User.objects.create(username="user_a", is_superuser=True)
        self.test_user_2 = User.objects.create(username="user_b")

        self.client = Client()
        self.client.force_login(self.test_user_1)

    def test_correct_state(self):
        """Test unassigning solver."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, solver=self.test_user_2,
                                     description="Test description.")
        response = self.client.get("/issue/unassign/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        new_issue = Issue.objects.get(pk=issue.pk)

        self.assertEqual(new_issue.state, ISSUE_CREATED)
        self.assertIsNone(new_issue.solver)
        self.assertIsNone(new_issue.assigned_at)

    def test_done_state(self):
        """Test that solver can't be removed when issue was marked as done."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, solver=self.test_user_2,
                                     description="Test description.")
        issue.state = ISSUE_DONE
        issue.save()

        response = self.client.get("/issue/unassign/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        new_issue = Issue.objects.get(pk=issue.pk)

        self.assertEqual(new_issue.state, ISSUE_DONE)
        self.assertIsNotNone(new_issue.solver)
        self.assertIsNotNone(new_issue.assigned_at)

    def test_permission_denied(self):
        """When user doesn't haver permission do nothing."""
        issue = Issue.objects.create(name="Test", created_by=self.test_user_1, solver=self.test_user_2,
                                     description="Test description.")
        c = Client()
        c.force_login(self.test_user_2)

        response = c.get("/issue/unassign/%d/" % issue.pk)
        self.assertEqual(response.status_code, 302)
        new_issue = Issue.objects.get(pk=issue.pk)

        self.assertEqual(new_issue.state, ISSUE_ASSIGNED)
        self.assertIsNotNone(new_issue.solver)
        self.assertIsNotNone(new_issue.assigned_at)
