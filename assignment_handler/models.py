from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models import QuerySet, Q, Count
from taggit.managers import TaggableManager


class Position(models.Model):
    name = models.CharField(max_length=255, unique=True)
    duties = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name

    def duties_to_a_list(self) -> list:
        return list(self.duties.split(";"))[:-1]


class Team(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name

    def sum_of_budget(self) -> int:
        return sum(project.budget for project in self.projects.all())

    def add_member(self, user):
        self.members.add(user)

    def remove_member(self, user):
        self.members.remove(user)


class Worker(AbstractUser):
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name="workers",
        blank=True,
        null=True,
    )
    teams = models.ManyToManyField(
        Team,
        related_name="members",
        blank=True,
    )
    rating_points = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.username} ({self.first_name} {self.last_name})"

    def completed_tasks(self) -> QuerySet:
        return (
            self.tasks.annotate(assignees_count=Count("assignees"))
            .filter(is_completed=True, assignees_count__gt=0)
            .distinct()
        )

    def underway_tasks(self) -> QuerySet:
        return (
            self.tasks.annotate(assignees_count=Count("assignees"))
            .filter(Q(is_completed=False) & Q(assignees_count__gt=0))
            .distinct()
        )


class WorkerEvaluation(models.Model):
    SCORE_CHOICES = (
        (1, "1"),
        (2, "2"),
        (3, "3"),
        (4, "4"),
        (5, "5"),
    )
    evaluator = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name="reviews_by"
    )
    worker = models.ForeignKey(
        Worker, on_delete=models.CASCADE, related_name="reviews_of"
    )
    score = models.IntegerField(choices=SCORE_CHOICES)


class ProjectCategory(models.Model):
    name = models.CharField(max_length=255, unique=True)
    depiction = models.TextField(blank=True)

    class Meta:
        verbose_name_plural = "project categories"

    def __str__(self) -> str:
        return self.name


class Project(models.Model):
    PRIORITY_CHOICES = [("U", "Urgent"), ("A", "Average"), ("S", "Side-tracked")]

    name = models.CharField(max_length=255)
    depiction = models.TextField()
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default="S")
    time_constraints = models.DateField()
    project_category = models.ForeignKey(
        ProjectCategory,
        on_delete=models.CASCADE,
        related_name="projects",
    )
    team = models.ForeignKey(
        Team, on_delete=models.CASCADE, blank=True, null=True, related_name="projects"
    )
    budget = models.DecimalField(decimal_places=2, max_digits=8, default=0)
    funds_used = models.DecimalField(
        decimal_places=2, max_digits=8, default=0, blank=True
    )
    tags = TaggableManager(blank=True)

    def get_project_progress(self):
        total_progress = 0
        number_of_blocks = 0
        blocks = self.projectblock_set.all()

        for block in blocks:
            block_progress = block.get_block_progress()
            total_progress += block_progress
            number_of_blocks += 1

        if number_of_blocks > 0:
            avg_progress = total_progress / number_of_blocks
        else:
            avg_progress = 0

        return round(avg_progress, 2)

    def get_current_phase(self):
        if self.get_project_progress() == 0:
            return "Initiation and planning phase"
        elif 0 < self.get_project_progress() < 100:
            return "Execution phase"
        elif self.get_project_progress() == 100:
            return "Implementation and closure phase"
        else:
            return "Unknown phase"

    def __str__(self) -> str:
        return self.name


class ProjectBlock(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    depiction = models.TextField()
    total_tasks = models.PositiveIntegerField(null=False, blank=False)
    completed_tasks = models.PositiveIntegerField(default=0)

    @staticmethod
    def predefined_blocks():
        return [
            {"name": "Frontend development", "index": 0},
            {"name": "Backend development", "index": 1},
            {"name": "Database/data layer", "index": 2},
            {"name": "Testing", "index": 3},
            {"name": "Infrastructure setup", "index": 4},
            {"name": "Documentation", "index": 5},
            {"name": "UX/design", "index": 6},
        ]

    def get_block_progress(self):
        if self.total_tasks > 0:
            return round((self.completed_tasks / self.total_tasks) * 100, 2)
        else:
            return 0.00

    def __str__(self) -> str:
        return f"Project name: {self.project} (project block: {self.name})"


class TaskType(models.Model):
    name = models.CharField(max_length=255, unique=True)
    depiction = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Task(models.Model):
    PRIORITY_CHOICES = [("U", "Urgent"), ("A", "Average"), ("S", "Side-tracked")]

    name = models.CharField(max_length=255)
    depiction = models.TextField()
    time_constraints = models.DateField()
    is_completed = models.BooleanField(default=False)
    priority = models.CharField(max_length=1, choices=PRIORITY_CHOICES, default="S")
    task_type = models.ForeignKey(
        TaskType, on_delete=models.CASCADE, related_name="tasks"
    )
    assignees = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="tasks", blank=True
    )
    tags = TaggableManager(blank=True)

    def tags_remained(self) -> int:
        count = self.tags.count() - 1
        return count if count > 0 else 0

    def __str__(self) -> str:
        return f"{self.name} (priority: {self.priority})"
