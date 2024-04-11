from django.forms import model_to_dict
from django.test import TestCase
from django.urls import reverse

from assignment_handler.forms import ProjectForm
from assignment_handler.models import (
    Worker,
    Team,
    Task,
    TaskType,
    Project,
    ProjectBlock,
    ProjectCategory,
)


class AssignmentHandlerViewsTestCase(TestCase):
    fixtures = ["fixtures/test_samples.json"]

    def test_worker_detail_get(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        worker = Worker.objects.get(pk=2)

        url = reverse(
            "assignment_handler:worker-detail", kwargs={"pk": worker.pk}
        )

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, worker.first_name)
        self.assertContains(resp, worker.last_name)
        self.assertContains(resp, worker.email)
        self.assertContains(resp, worker.position)
        self.assertContains(resp, worker.rating_points)

    def test_worker_detail_post(self):
        user = Worker.objects.get(pk=1)
        evaluator = user
        self.client.force_login(evaluator)

        worker = Worker.objects.get(pk=2)

        data = {"score": 3}

        url = reverse(
            "assignment_handler:worker-detail", kwargs={"pk": worker.pk}
        )

        resp = self.client.post(url, data)

        worker.refresh_from_db()

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(worker.rating_points, 3)

    def test_worker_create_post_valid(self):
        worker = Worker.objects.get(pk=2)

        original_data = model_to_dict(worker)
        original_data.pop("id")
        original_data.pop("password")
        original_data.pop("teams")
        original_data.pop("last_login", None)

        original_data["username"] = "test_" + original_data["username"]
        original_data["password1"] = "asdfDFGHJK12#"
        original_data["password2"] = "asdfDFGHJK12#"

        valid_data = original_data

        url = reverse("assignment_handler:worker-create")

        resp = self.client.post(url, valid_data)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Worker.objects.filter(username=valid_data["username"]).exists()
        )

    def test_worker_create_post_invalid(self):
        worker = Worker.objects.get(pk=2)

        original_data = model_to_dict(worker)
        original_data.pop("id")
        original_data.pop("password")
        original_data.pop("teams")
        original_data.pop("last_login", None)

        original_data["username"] = ""
        original_data["password1"] = "asdfDFGHJK12#"
        original_data["password2"] = "asdfDFGHJK12#"

        invalid_data = original_data

        url = reverse("assignment_handler:worker-create")

        resp = self.client.post(url, invalid_data)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            Worker.objects.filter(username=invalid_data["username"]).exists()
        )

    def test_worker_update_post_valid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        data = model_to_dict(user)
        data.pop("password")
        data.pop("teams")

        data["email"] = "test@gmail.com"

        url = reverse(
            "assignment_handler:worker-update", kwargs={"pk": user.id}
        )

        resp = self.client.post(url, data)

        user.refresh_from_db()

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(user.email, data["email"])

    def test_worker_update_post_invalid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)
        data = model_to_dict(user)
        data.pop("password")
        data.pop("teams")

        data["email"] = "test"

        url = reverse(
            "assignment_handler:worker-update", kwargs={"pk": user.id}
        )

        resp = self.client.post(url, data)

        user.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(user.email, data["email"])

    def test_task_create_post_valid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        task = Task.objects.get(pk=2)

        original_data = model_to_dict(task)
        original_data.pop("id")
        original_data.pop("assignees")

        original_data["name"] = "Test " + original_data["name"]

        valid_data = original_data

        url = reverse("assignment_handler:task-create")

        resp = self.client.post(url, valid_data)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(Task.objects.filter(name=valid_data["name"]).exists())

    def test_task_create_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task = Task.objects.get(pk=2)

        original_data = model_to_dict(task)
        original_data.pop("id")
        original_data.pop("assignees")

        original_data["name"] = ""

        invalid_data = original_data

        url = reverse("assignment_handler:task-create")

        resp = self.client.post(url, invalid_data)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            Task.objects.filter(name=invalid_data["name"]).exists()
        )

    def test_task_update_post_valid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task_type = TaskType.objects.create(
            name="test task type", depiction="Some_depiction"
        )
        task = Task.objects.create(
            name="Test task",
            depiction="Some depiction",
            time_constraints="2025-07-24",
            is_completed=False,
            priority="U",
            task_type=task_type
        )

        update_info_task = Task.objects.get(pk=1)

        original_data = model_to_dict(update_info_task)

        original_data["priority"] = "A"
        original_data["time_constraints"] = "2025-07-30"

        valid_data = original_data

        url = reverse("assignment_handler:task-update", kwargs={"pk": task.pk})

        resp = self.client.post(url, valid_data)

        task.refresh_from_db()

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(task.priority, valid_data["priority"])
        self.assertEqual(
            task.time_constraints.strftime("%Y-%m-%d"),
            valid_data["time_constraints"]
        )

    def test_task_update_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task_type = TaskType.objects.create(
            name="test task type", depiction="Some_depiction"
        )
        task = Task.objects.create(
            name="Test task",
            depiction="Some depiction",
            time_constraints="2025-07-24",
            is_completed=False,
            priority="U",
            task_type=task_type
        )

        update_info_task = Task.objects.get(pk=1)

        original_data = model_to_dict(update_info_task)

        original_data["priority"] = "B"
        original_data["time_constraints"] = "2025-07-99"

        invalid_data = original_data

        url = reverse("assignment_handler:task-update", kwargs={"pk": task.pk})

        resp = self.client.post(url, invalid_data)

        task.refresh_from_db()

        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(task.priority, invalid_data["priority"])
        self.assertNotEqual(
            task.time_constraints.strftime("%Y-%m-%d"),
            invalid_data["time_constraints"]
        )

    def test_project_create_get(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        url = reverse("assignment_handler:project-create")

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

        context = resp.context

        self.assertIn("form", context)
        self.assertIn("project_blocks", context)
        self.assertIn("object", context)

        self.assertIsInstance(context["form"], ProjectForm)

        self.assertIsNone(context["object"])

        predefined_blocks = ProjectBlock.predefined_blocks()
        for block in predefined_blocks:
            self.assertIn(block, context["project_blocks"])

        self.assertTemplateUsed(
            resp, "assignment_handler/project_form_create.html"
        )

    def test_project_create_post_valid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        project = Project.objects.get(pk=2)

        original_data = model_to_dict(project)
        original_data.pop("id")

        original_data["name"] = "Test " + original_data["name"]
        original_data["project_blocks"] = [0, 1, 2, 3]
        original_data["block_0_total_tasks"] = 17
        original_data["block_1_total_tasks"] = 18
        original_data["block_2_total_tasks"] = 20
        original_data["block_3_total_tasks"] = 23

        frontend_block = project.projectblock_set.all()[0]
        frontend_name = frontend_block.name
        backend_block = project.projectblock_set.all()[1]
        backend_name = backend_block.name
        database_data_layer_block = project.projectblock_set.all()[2]
        database_data_layer_name = (
            database_data_layer_block.name
        )
        testing_block = project.projectblock_set.all()[3]
        testing_name = testing_block.name

        valid_data = original_data

        url = reverse("assignment_handler:project-create")

        resp = self.client.post(url, valid_data)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(
            Project.objects.filter(name=valid_data["name"]).exists()
        )
        self.assertTrue(
            project.projectblock_set.all()
            .filter(name=frontend_name)
            .exists()
        )
        self.assertTrue(
            project.projectblock_set.all()
            .filter(name=backend_name)
            .exists()
        )
        self.assertTrue(
            project.projectblock_set.all()
            .filter(name=database_data_layer_name)
            .exists()
        )
        self.assertTrue(
            project.projectblock_set.all()
            .filter(name=testing_name)
            .exists()
        )

    def test_project_create_post_invalid(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        project = Project.objects.get(pk=2)

        original_data = model_to_dict(project)
        original_data.pop("id")

        original_data["name"] = "Test " + original_data["name"]
        original_data["priority"] = "B"
        original_data["project_blocks"] = [0, 2]
        original_data["block_1_total_tasks"] = 18
        original_data["block_3_total_tasks"] = 23

        invalid_data = original_data

        url = reverse("assignment_handler:project-create")

        resp = self.client.post(url, invalid_data)

        self.assertEqual(resp.status_code, 200)
        self.assertFalse(
            Project.objects.filter(name=invalid_data["name"]).exists()
        )

    def test_project_update_get(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        project = Project.objects.get(pk=1)

        url = reverse(
            "assignment_handler:project-update", kwargs={"pk": project.pk}
        )

        resp = self.client.get(url)

        self.assertEqual(resp.status_code, 200)

        context = resp.context

        self.assertIn("form", context)
        self.assertIn("object", context)

        self.assertIsInstance(context["form"], ProjectForm)
        self.assertEqual(context["object"], project)

        self.assertIn("project_blocks", context)
        self.assertIn("existing_names", context)
        self.assertIn("existing_blocks", context)
        self.assertIn("predefined_blocks", context)

        self.assertTemplateUsed(
            resp, "assignment_handler/project_form_update.html"
        )

    def test_project_update_post_valid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        team = Team.objects.create(name="Test team")
        project_category = ProjectCategory.objects.create(
            name="test project category", depiction="Some_depiction"
        )
        project = Project.objects.create(
            name="Test project",
            depiction="Some depiction",
            priority="S",
            time_constraints="2026-06-14",
            project_category=project_category,
            team=team,
            budget="48000.00",
            funds_used="14000.00"
        )
        blocks_configurations = [
            {
                "name": "Frontend development",
                "depiction": "Some_depiction",
                "total_tasks": 12
            },
            {
                "name": "Backend development",
                "depiction": "Some_depiction",
                "total_tasks": 16
            },
            {
                "name": "Database/data layer",
                "depiction": "Some_depiction",
                "total_tasks": 14
            },
            {
                "name": "Documentation",
                "depiction": "Some_depiction",
                "total_tasks": 10
            },
            {
                "name": "UX/design",
                "depiction": "Some_depiction",
                "total_tasks": 8
            }
        ]

        for block_config in blocks_configurations:
            ProjectBlock.objects.create(project=project, **block_config)

        existing_frontend_block = project.projectblock_set.all()[0]
        existing_frontend_index = existing_frontend_block.id
        existing_backend_block = project.projectblock_set.all()[1]
        existing_backend_index = existing_backend_block.id
        existing_database_data_layer_block = project.projectblock_set.all()[2]
        existing_database_data_layer_index = (
            existing_database_data_layer_block.id
        )
        existing_documentation_block = project.projectblock_set.all()[3]
        existing_documentation_index = existing_documentation_block.id
        existing_ux_design_block = project.projectblock_set.all()[4]
        existing_ux_design_index = existing_ux_design_block.id

        predefined_blocks = ProjectBlock.predefined_blocks()

        sixth_block = predefined_blocks[3]
        testing_name = sixth_block["name"]
        testing_index = sixth_block["index"]
        seventh_block = predefined_blocks[4]
        infrastructure_setup_name = seventh_block["name"]
        infrastructure_setup_index = seventh_block["index"]

        update_info_project = Project.objects.get(pk=1)

        original_data = model_to_dict(update_info_project)

        original_data["priority"] = "A"
        original_data["existing_project_blocks"] = [
            existing_frontend_index,
            existing_backend_index,
            existing_database_data_layer_index,
            existing_documentation_index,
            existing_ux_design_index
        ]
        original_data["block_19_total_tasks"] = 14
        original_data["block_19_completed_tasks"] = 6
        original_data["block_20_total_tasks"] = 18
        original_data["block_20_completed_tasks"] = 4
        original_data["block_21_total_tasks"] = 15
        original_data["block_21_completed_tasks"] = 8
        original_data["block_22_total_tasks"] = 14
        original_data["block_22_completed_tasks"] = 8
        original_data["block_23_total_tasks"] = 10
        original_data["block_23_completed_tasks"] = 5
        original_data["new_project_blocks"] = [
            testing_index,
            infrastructure_setup_index
        ]
        original_data["new_block_3_total_tasks"] = 20
        original_data["new_block_4_total_tasks"] = 15
        original_data["new_block_3_completed_tasks"] = 0
        original_data["new_block_4_completed_tasks"] = 0

        valid_data = original_data

        url = reverse(
            "assignment_handler:project-update", kwargs={"pk": project.id}
        )

        resp = self.client.post(url, valid_data)

        project.refresh_from_db()

        project_total_tasks_block1 = (
            project.projectblock_set.all()[0].total_tasks
        )
        project_completed_tasks_block1 = (
            project.projectblock_set.all()[0].completed_tasks
        )
        project_total_tasks_block2 = (
            project.projectblock_set.all()[1].total_tasks
        )
        project_completed_tasks_block2 = (
            project.projectblock_set.all()[1].completed_tasks)
        project_total_tasks_block3 = (
            project.projectblock_set.all()[2].total_tasks
        )
        project_completed_tasks_block3 = (
            project.projectblock_set.all()[2].completed_tasks
        )
        project_total_tasks_block4 = (
            project.projectblock_set.all()[3].total_tasks
        )
        project_completed_tasks_block4 = (
            project.projectblock_set.all()[3].completed_tasks
        )
        project_total_tasks_block5 = (
            project.projectblock_set.all()[4].total_tasks
        )
        project_completed_tasks_block5 = (
            project.projectblock_set.all()[4].completed_tasks
        )
        project_total_tasks_block6 = (
            project.projectblock_set.all()[5].total_tasks
        )
        project_completed_tasks_block6 = (
            project.projectblock_set.all()[5].completed_tasks
        )
        project_total_tasks_block7 = (
            project.projectblock_set.all()[6].total_tasks
        )
        project_completed_tasks_block7 = (
            project.projectblock_set.all()[6].completed_tasks
        )

        self.assertEqual(resp.status_code, 302)
        self.assertEqual(project.priority, valid_data["priority"])
        self.assertEqual(
            project_total_tasks_block1,
            valid_data["block_19_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block1,
            valid_data["block_19_completed_tasks"]
        )
        self.assertEqual(
            project_total_tasks_block2,
            valid_data["block_20_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block2,
            valid_data["block_20_completed_tasks"]
        )
        self.assertEqual(
            project_total_tasks_block3,
            valid_data["block_21_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block3,
            valid_data["block_21_completed_tasks"]
        )
        self.assertEqual(
            project_total_tasks_block4,
            valid_data["block_22_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block4,
            valid_data["block_22_completed_tasks"]
        )
        self.assertEqual(
            project_total_tasks_block5,
            valid_data["block_23_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block5,
            valid_data["block_23_completed_tasks"]
        )
        self.assertTrue(
            project.projectblock_set.all()
            .filter(name=testing_name)
            .exists()
        )
        self.assertTrue(
            project.projectblock_set.all()
            .filter(name=infrastructure_setup_name)
            .exists()
        )
        self.assertEqual(
            project_total_tasks_block6,
            valid_data["new_block_3_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block6,
            valid_data["new_block_3_completed_tasks"]
        )
        self.assertEqual(
            project_total_tasks_block7,
            valid_data["new_block_4_total_tasks"]
        )
        self.assertEqual(
            project_completed_tasks_block7,
            valid_data["new_block_4_completed_tasks"]
        )

    def test_project_update_post_invalid(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        team = Team.objects.create(name="Test team")
        project_category = ProjectCategory.objects.create(
            name="test project category", depiction="Some_depiction"
        )
        project = Project.objects.create(
            name="Test project",
            depiction="Some depiction",
            priority="S",
            time_constraints="2026-06-14",
            project_category=project_category,
            team=team,
            budget="48000.00",
            funds_used="14000.00"
        )
        blocks_configurations = [
            {
                "name": "Frontend development",
                "depiction": "Some_depiction",
                "total_tasks": 12
            },
            {
                "name": "Backend development",
                "depiction": "Some_depiction",
                "total_tasks": 16
            },
            {
                "name": "Database/data layer",
                "depiction": "Some_depiction",
                "total_tasks": 14
            },
            {
                "name": "Documentation",
                "depiction": "Some_depiction",
                "total_tasks": 10
            },
            {
                "name": "UX/design",
                "depiction": "Some_depiction",
                "total_tasks": 8
             }
        ]

        for block_config in blocks_configurations:
            ProjectBlock.objects.create(project=project, **block_config)

        existing_frontend_block = project.projectblock_set.all()[0]
        existing_frontend_index = existing_frontend_block.id
        existing_backend_block = project.projectblock_set.all()[1]
        existing_backend_index = existing_backend_block.id
        existing_database_data_layer_block = project.projectblock_set.all()[2]
        existing_database_data_layer_index = (
            existing_database_data_layer_block.id
        )
        existing_documentation_block = project.projectblock_set.all()[3]
        existing_documentation_index = existing_documentation_block.id
        existing_ux_design_block = project.projectblock_set.all()[4]
        existing_ux_design_index = existing_ux_design_block.id

        predefined_blocks = ProjectBlock.predefined_blocks()

        sixth_block = predefined_blocks[3]
        testing_name = sixth_block["name"]
        seventh_block = predefined_blocks[4]
        infrastructure_setup_name = seventh_block["name"]
        infrastructure_setup_index = seventh_block["index"]

        update_info_project = Project.objects.get(pk=1)

        original_data = model_to_dict(update_info_project)

        original_data["priority"] = "B"
        original_data["existing_project_blocks"] = [
            existing_frontend_index,
            existing_backend_index,
            existing_database_data_layer_index,
            existing_documentation_index,
            existing_ux_design_index
        ]
        original_data["block_19_total_tasks"] = 14
        original_data["block_19_completed_tasks"] = 16
        original_data["block_20_total_tasks"] = 18
        original_data["block_20_completed_tasks"] = 20
        original_data["block_21_total_tasks"] = 15
        original_data["block_21_completed_tasks"] = 18
        original_data["block_22_total_tasks"] = 14
        original_data["block_22_completed_tasks"] = 17
        original_data["block_23_total_tasks"] = 10
        original_data["block_23_completed_tasks"] = 14
        original_data["new_project_blocks"] = [infrastructure_setup_index]
        original_data["new_block_3_total_tasks"] = 20
        original_data["new_block_3_completed_tasks"] = 0
        original_data["new_block_4_completed_tasks"] = 0

        invalid_data = original_data

        url = reverse(
            "assignment_handler:project-update", kwargs={"pk": project.id}
        )

        resp = self.client.post(url, invalid_data)

        project.refresh_from_db()

        project_total_tasks_block1 = (
            project.projectblock_set.all()[0].total_tasks
        )
        project_completed_tasks_block1 = (
            project.projectblock_set.all()[0].completed_tasks
        )
        project_total_tasks_block2 = (
            project.projectblock_set.all()[1].total_tasks
        )
        project_completed_tasks_block2 = (
            project.projectblock_set.all()[1].completed_tasks
        )
        project_total_tasks_block3 = (
            project.projectblock_set.all()[2].total_tasks
        )
        project_completed_tasks_block3 = (
            project.projectblock_set.all()[2].completed_tasks
        )
        project_total_tasks_block4 = (
            project.projectblock_set.all()[3].total_tasks
        )
        project_completed_tasks_block4 = (
            project.projectblock_set.all()[3].completed_tasks
        )
        project_total_tasks_block5 = (
            project.projectblock_set.all()[4].total_tasks
        )
        project_completed_tasks_block5 = (
            project.projectblock_set.all()[4].completed_tasks
        )

        self.assertEqual(resp.status_code, 200)
        self.assertNotEqual(project.priority, invalid_data["priority"])
        self.assertNotEqual(
            project_total_tasks_block1,
            invalid_data["block_19_total_tasks"]
        )
        self.assertNotEqual(
            project_completed_tasks_block1,
            invalid_data["block_19_completed_tasks"]
        )
        self.assertNotEqual(
            project_total_tasks_block2,
            invalid_data["block_20_total_tasks"]
        )
        self.assertNotEqual(
            project_completed_tasks_block2,
            invalid_data["block_20_completed_tasks"]
        )
        self.assertNotEqual(
            project_total_tasks_block3,
            invalid_data["block_21_total_tasks"]
        )
        self.assertNotEqual(
            project_completed_tasks_block3,
            invalid_data["block_21_completed_tasks"]
        )
        self.assertNotEqual(
            project_total_tasks_block4,
            invalid_data["block_22_total_tasks"]
        )
        self.assertNotEqual(
            project_completed_tasks_block4,
            invalid_data["block_22_completed_tasks"]
        )
        self.assertNotEqual(
            project_total_tasks_block5,
            invalid_data["block_23_total_tasks"]
        )
        self.assertNotEqual(
            project_completed_tasks_block5,
            invalid_data["block_23_completed_tasks"]
        )
        self.assertFalse(
            project.projectblock_set.all()
            .filter(name=testing_name)
            .exists()
        )
        self.assertFalse(
            project.projectblock_set.all()
            .filter(name=infrastructure_setup_name)
            .exists()
        )

    def test_toggle_assign_task_unassigned(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task = Task.objects.get(pk=3)

        self.assertNotIn(user, task.assignees.all())

        url = reverse(
            "assignment_handler:toggle-task-assign", kwargs={"pk": task.pk}
        )

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertIn(user, task.assignees.all())

    def test_toggle_unassign_task_assigned(self):
        user = Worker.objects.get(pk=1)
        self.client.force_login(user)

        task = Task.objects.get(pk=2)

        self.assertIn(user, task.assignees.all())

        url = reverse(
            "assignment_handler:toggle-task-assign", kwargs={"pk": task.pk}
        )

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertNotIn(user, task.assignees.all())

    def test_toggle_team_is_not_member(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        worker = Worker.objects.get(pk=2)

        team = Team.objects.get(pk=2)

        self.assertFalse(worker in team.members.all())

        url = reverse(
            "assignment_handler:toggle-team-transition",
            kwargs={"pk": worker.pk, "team_id": team.pk},
        )

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(worker in team.members.all())

    def test_toggle_team_is_member(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        worker = Worker.objects.get(pk=2)

        team = Team.objects.get(pk=1)

        self.assertTrue(worker in team.members.all())

        url = reverse(
            "assignment_handler:toggle-team-transition",
            kwargs={"pk": worker.pk, "team_id": team.pk},
        )

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(worker in team.members.all())

    def test_switch_team_add(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        team = Team.objects.get(pk=1)

        self.assertFalse(team.members.filter(username="marshall").exists())

        url = reverse(
            "assignment_handler:switch-team",
            kwargs={"pk": team.pk, "action": "add"}
        )

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertTrue(team.members.filter(username="marshall").exists())

    def test_switch_team_remove(self):
        user = Worker.objects.get(pk=1)

        self.client.force_login(user)

        team = Team.objects.get(pk=2)

        self.assertTrue(team.members.filter(username="marshall").exists())

        url = reverse(
            "assignment_handler:switch-team",
            kwargs={"pk": team.pk, "action": "delete"}
        )

        resp = self.client.post(url)

        self.assertEqual(resp.status_code, 302)
        self.assertFalse(team.members.filter(username="marshall").exists())
