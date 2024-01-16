import copy

from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse

from assignment_handler.forms import ProjectForm, TaskForm, WorkerCreateForm
from assignment_handler.models import Worker, Task, Project, Team, ProjectBlock


class AssignmentHandlerViewsTestCase(TestCase):
    fixtures = ["fixtures/test_samples.json"]

    @classmethod
    def setUpTestData(cls):
        cls.initial_num_workers = Worker.objects.count()
        cls.initial_num_tasks = Task.objects.count()
        cls.initial_num_projects = Project.objects.count()

    def test_worker_detail_get(self):
        url = f"/workers/{2}/"

        response = self.client.get(url)

        expected_url = f"/accounts/login/?next={url}"
        self.assertEqual(response.url, expected_url)

    def test_worker_detail_post(self):
        url = f"/workers/{2}/"
        data = {"score": 5}

        evaluator = Worker.objects.get(pk=1)
        worker = Worker.objects.get(pk=2)

        self.client.force_login(evaluator)

        response = self.client.post(url, data)

        self.assertEqual(response.url, f"/workers/{2}/")

        worker.rating_points += 5

        self.assertEqual(worker.rating_points, 8)

    def test_worker_create_post_valid(self):
        worker = Worker.objects.get(pk=2)

        data = model_to_dict(worker)
        data.pop("id")

        data["username"] = "test_" + data["username"]
        data["password1"] = "asdfDFGHJK12#"
        data["password2"] = "asdfDFGHJK12#"

        data.pop("last_login", None)

        valid_data = copy.deepcopy(data)

        form = WorkerCreateForm(data=valid_data)

        self.assertTrue(form.is_valid())

        form.save()

        self.assertTrue(Worker.objects.filter(username=valid_data["username"]).exists())

    def test_worker_create_post_invalid(self):
        worker = Worker.objects.get(pk=2)

        data = model_to_dict(worker)
        data.pop("id")

        data["username"] = "test_" + data["username"]
        data["password1"] = "asdfDFGHJK12#"
        data["password2"] = "asdfDFGHJK12#"

        invalid_data = copy.deepcopy(data)
        invalid_data["username"] = ""

        invalid_data.pop("last_login", None)

        form = WorkerCreateForm(data=invalid_data)
        self.assertFalse(form.is_valid())

        self.assertFalse(
            Worker.objects.filter(username=invalid_data["username"]).exists()
        )

    def test_worker_update_post_valid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        worker_primary_keys = list(range(2, 10))
        workers = [
            Worker.objects.get(pk=worker_pk) for worker_pk in worker_primary_keys
        ]

        updated_data = {"first_name": "Updated name", "email": "new@email.com"}

        for worker in workers:
            for field, value in updated_data.items():
                setattr(worker, field, value)

        for worker in workers:
            worker.save()

        for worker in workers:
            self.assertEqual(worker.first_name, updated_data["first_name"])
            self.assertEqual(worker.email, updated_data["email"])

    def test_worker_update_post_invalid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        worker_primary_keys = list(range(2, 10))
        workers = [
            Worker.objects.get(pk=worker_pk) for worker_pk in worker_primary_keys
        ]

        updated_data = {"first_name": "Updated name", "email": "new@email.com"}

        for worker in workers:
            for field, value in updated_data.items():
                setattr(worker, field, value)

        for worker in workers:
            worker.save()

        for worker in workers:
            self.assertEqual(worker.first_name, updated_data["first_name"])
            self.assertEqual(worker.email, updated_data["email"])

    def test_task_create_post_valid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        task = Task.objects.get(pk=1)

        data = model_to_dict(task)
        data.pop("id")

        valid_data = copy.deepcopy(data)

        form = TaskForm(data=valid_data)
        self.assertTrue(form.is_valid())

        self.assertTrue(Task.objects.filter(name=valid_data["name"]).exists())

    def test_task_create_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task_primary_keys = list(range(1, 6))
        tasks = [Task.objects.get(pk=task_pk) for task_pk in task_primary_keys]

        data_list = []
        for task in tasks:
            task_data = model_to_dict(task)
            task_data.pop("id")
            data_list.append(task_data)

        combined_data = {}
        for individual_data in data_list:
            combined_data.update(individual_data)

        invalid_data_list = [copy.deepcopy(data_item) for data_item in data_list]
        for invalid_data in invalid_data_list:
            invalid_data["name"] = ""

        for invalid_data in invalid_data_list:
            form = TaskForm(data=invalid_data)
            self.assertFalse(form.is_valid())

            self.assertFalse(Task.objects.filter(name=invalid_data["name"]).exists())

    def test_task_update_post_valid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task_primary_keys = list(range(1, 6))
        tasks = [Task.objects.get(pk=task_pk) for task_pk in task_primary_keys]

        updated_data = {"name": "Updated name", "priority": "S"}

        for task in tasks:
            for field, value in updated_data.items():
                setattr(task, field, value)

        for task in tasks:
            task.save()

        for task in tasks:
            self.assertEqual(task.name, updated_data["name"])
            self.assertEqual(task.priority, updated_data["priority"])

    def test_task_update_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task_primary_keys = list(range(1, 6))
        tasks = [Task.objects.get(pk=task_pk) for task_pk in task_primary_keys]

        original_data = [(task.name, task.priority) for task in tasks]

        updated_data = {"name": "Updated name", "priority": "S"}

        for task in tasks:
            for field, value in updated_data.items():
                setattr(task, field, value)

        for task in tasks:
            task.save()

        for task, (original_name, original_priority) in zip(tasks, original_data):
            updated_task = Task.objects.get(pk=task.pk)

            self.assertNotEqual(
                (updated_task.name, updated_task.priority),
                (original_name, original_priority),
            )

    def test_project_create_get(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        url = reverse("assignment_handler:project-create")

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        response = self.client.get(url)

        self.assertIn("form", response.context)
        self.assertIn("project_blocks", response.context)
        self.assertIn("object", response.context)

        self.assertIsInstance(response.context["form"], ProjectForm)

        self.assertIsNone(response.context["object"])

        predefined_blocks = ProjectBlock.predefined_blocks()
        for block in predefined_blocks:
            self.assertIn(block, response.context["project_blocks"])

        self.assertTemplateUsed(response, "assignment_handler/project_form_create.html")

    def test_project_create_post_valid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        project_primary_keys = list(range(2, 5))
        projects = [
            Project.objects.get(pk=project_pk) for project_pk in project_primary_keys
        ]
        data_list = []
        for project in projects:
            project_data = model_to_dict(project)
            project_data.pop("id")
            data_list.append(project_data)

        combined_data = {}
        for individual_data in data_list:
            combined_data.update(individual_data)

        valid_data_list = [copy.deepcopy(data_item) for data_item in data_list]

        for valid_data in valid_data_list:
            form = ProjectForm(data=valid_data)
            self.assertTrue(form.is_valid())

            self.assertTrue(Project.objects.filter(name=valid_data["name"]).exists())

    def test_project_create_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        project_primary_keys = list(range(2, 5))
        projects = [
            Project.objects.get(pk=worker_pk) for worker_pk in project_primary_keys
        ]

        for project in projects:
            data = model_to_dict(project)
            data.pop("id")

            invalid_data = copy.deepcopy(data)
            invalid_data["name"] = ""

            form = TaskForm(data=invalid_data)
            self.assertFalse(form.is_valid())

            self.assertFalse(Project.objects.filter(name=invalid_data["name"]).exists())

    def test_project_update_get(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        project_primary_keys = list(range(2, 5))
        projects = [
            Project.objects.get(pk=project_pk) for project_pk in project_primary_keys
        ]

        for project in projects:
            url = reverse("assignment_handler:project-update", args=[project.pk])
            response = self.client.get(url)

            self.assertIn("form", response.context)
            self.assertIn("object", response.context)

            self.assertIsInstance(response.context["form"], ProjectForm)
            self.assertEqual(response.context["object"], project)

            self.assertIn("project_blocks", response.context)
            self.assertIn("existing_names", response.context)
            self.assertIn("existing_blocks", response.context)
            self.assertIn("predefined_blocks", response.context)

            self.assertTemplateUsed(
                response, "assignment_handler/project_form_update.html"
            )

    def test_project_update_post_valid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        project_primary_keys = list(range(2, 5))
        projects = [
            Project.objects.get(pk=project_pk) for project_pk in project_primary_keys
        ]

        updated_data = {"name": "Updated name", "priority": "S"}

        for project in projects:
            for field, value in updated_data.items():
                setattr(project, field, value)

        for project in projects:
            project.save()

        for project in projects:
            self.assertEqual(project.name, updated_data["name"])
            self.assertEqual(project.priority, updated_data["priority"])

    def test_project_update_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        project_primary_keys = list(range(2, 5))
        projects = [
            Project.objects.get(pk=project_pk) for project_pk in project_primary_keys
        ]

        original_data = [(project.name, project.priority) for project in projects]

        updated_data = {"name": "Updated name", "priority": "S"}

        for project in projects:
            for field, value in updated_data.items():
                setattr(project, field, value)

        for project in projects:
            project.save()

        for project, (original_name, original_priority) in zip(projects, original_data):
            updated_project = Project.objects.get(pk=project.pk)

            self.assertNotEqual(
                (updated_project.name, updated_project.priority),
                (original_name, original_priority),
            )

    def test_toggle_assign_task_unassigned(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task = Task.objects.get(pk=3)

        self.assertNotIn(user, task.assignees.all())

        task.assignees.add(user)

        self.assertIn(user, task.assignees.all())

    def test_toggle_assign_task_assigned(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task = Task.objects.get(pk=2)

        self.assertIn(user, task.assignees.all())

        task.assignees.remove(user)

        self.assertNotIn(user, task.assignees.all())

    def test_toggle_team_is_not_member(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        workers = [Worker.objects.get(pk=2), Worker.objects.get(pk=3)]

        teams = [Team.objects.get(pk=1), Team.objects.get(pk=2)]

        for team in teams:
            for worker in workers:
                if worker not in team.members.all():
                    team.members.add(worker)
                    team.save()

        match_found = False

        for team in teams:
            for worker in workers:
                if worker in team.members.all():
                    match_found = True
                    break

            self.assertTrue(match_found)

            match_found = False

    def test_toggle_team_is_member(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        workers = [Worker.objects.get(pk=2), Worker.objects.get(pk=3)]

        teams = [Team.objects.get(pk=1), Team.objects.get(pk=2)]

        for team in teams:
            for worker in workers:
                if worker in team.members.all():
                    team.members.remove(worker)
                    team.save()

        match_not_found = False

        for team in teams:
            for worker in workers:
                if worker not in team.members.all():
                    match_not_found = True
                    break

            self.assertTrue(match_not_found)

            match_not_found = False

    def test_switch_team_add(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        team = Team.objects.get(pk=3)

        team.members.add(user)

        self.assertTrue(team.members.filter(username="marshall").exists())

    def test_switch_team_remove(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        team = Team.objects.get(pk=1)

        team.members.remove(user)

        self.assertFalse(team.members.filter(username="marshall").exists())
