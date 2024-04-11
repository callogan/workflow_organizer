import datetime
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import QuerySet, F, Q, Count
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy, reverse
from django.utils import timezone
from django.views import generic
from django.views.generic.base import View, TemplateView

from assignment_handler.forms import (
    WorkerCreateForm,
    WorkerUpdateForm,
    WorkerEvaluationForm,
    PositionForm,
    PositionSearchForm,
    TeamForm,
    TaskForm,
    TaskTypeForm,
    TaskTypeSearchForm,
    ProjectForm,
    ProjectCategoryForm,
    ProjectCategorySearchForm,
)

from assignment_handler.models import (
    Worker,
    WorkerEvaluation,
    Position,
    Team,
    Task,
    TaskType,
    Project,
    ProjectBlock,
    ProjectCategory,
)

from assignment_handler.views_helpers import (
    calculate_average_progress,
    budget_status_completed,
    budget_status_uncompleted,
)
from assignment_handler.views_validators import (
    validate_project_create_custom,
    validate_project_update_procedure_custom,
    validate_project_update_structures_custom,
)


def index(request):
    """View function for the home page of the site."""

    context = {
        "num_teams": Team.objects.count(),
        "num_projects": Project.objects.count(),
        "num_workers": get_user_model().objects.count(),
    }

    return render(request, "assignment_handler/index.html", context=context)


class WorkerDetailView(LoginRequiredMixin, generic.DetailView):
    model = Worker
    queryset = get_user_model().objects.select_related("position")
    template_name = "assignment_handler/worker_detail.html"

    def get(self, request, pk, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)

        form = WorkerEvaluationForm()
        worker = Worker.objects.get(pk=pk)

        last_evaluation = WorkerEvaluation.objects.filter(
            evaluator=request.user, worker=worker
        )

        if last_evaluation:
            last_evaluation = last_evaluation[0]
            form.fields["score"].initial = last_evaluation.score

        context["form"] = form
        context["worker"] = worker

        return self.render_to_response(context)

    def post(self, request, pk, *args, **kwargs):
        form = WorkerEvaluationForm(request.POST)
        worker = Worker.objects.get(pk=pk)
        evaluator = request.user
        evaluation: WorkerEvaluation = WorkerEvaluation.objects.filter(
            evaluator=evaluator, worker=worker
        )

        if form.is_valid():
            score = form.cleaned_data["score"]
            score = int(score)

            if evaluation:
                evaluation = evaluation[0]
                evaluation.score = score
                evaluation.save()
            else:
                evaluation: WorkerEvaluation = WorkerEvaluation(
                    evaluator=evaluator, worker=worker, score=score
                )
                evaluation.save()

            worker.rating_points += score
            worker.save()

        return redirect(
            reverse("assignment_handler:worker-detail", kwargs={"pk": worker.pk})
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        worker = self.get_object()

        form = WorkerEvaluationForm()
        last_evaluation = WorkerEvaluation.objects.filter(
            evaluator=self.request.user, worker=worker
        )

        if last_evaluation:
            last_evaluation = last_evaluation[0]
            form.fields["score"].initial = last_evaluation.score

        context["form"] = form
        context["worker"] = worker

        user_assignees = Task.objects.filter(assignees=self.request.user)
        worker_assignees = Task.objects.filter(assignees=worker)

        has_common_task = user_assignees.filter(pk__in=worker_assignees).exists()
        context["has_common_task"] = has_common_task
        last_rating = WorkerEvaluation.objects.filter(
            evaluator=self.request.user, worker=worker
        )
        context["last_rating"] = last_rating

        return context


class WorkerCreateView(generic.CreateView):
    model = Worker
    form_class = WorkerCreateForm
    template_name = "registration/register.html"
    success_url = reverse_lazy("assignment_handler:index")

    def post(self, request, *args, **kwargs):
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            self.object = None
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        form.save_m2m()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teams = Team.objects.all()
        context["teams"] = teams
        return context


class WorkerUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Worker
    form_class = WorkerUpdateForm
    template_name = "assignment_handler/worker_form.html"
    success_url = reverse_lazy("assignment_handler:worker-detail")

    def post(self, request, *args, **kwargs):
        form = WorkerUpdateForm(request.POST, instance=self.get_object())
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)

    def form_valid(self, form):
        self.object = form.save()
        return super().form_valid(form)

    def form_invalid(self, form):
        self.object = self.get_object()
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy(
            "assignment_handler:worker-detail", kwargs={"pk": self.kwargs["pk"]}
        )

    def get_object(self, queryset=None):
        worker_id = self.kwargs.get("pk")
        return get_object_or_404(Worker, id=worker_id)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teams = Team.objects.all()
        context["teams"] = teams
        return context


class WorkerDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Worker
    success_url = reverse_lazy("assignment_handler:index")
    template_name = "assignment_handler/worker_confirm_delete.html"


class WorkersListView(LoginRequiredMixin, generic.ListView):
    model = Worker
    template_name = "assignment_handler/workers_list.html"
    context_object_name = "users"
    ordering = ["-rating_points"]
    paginate_by = 10

    def get_queryset(self):
        users = super().get_queryset()
        users = users.annotate(place=F("id"))
        return users

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        top_workers = context["object_list"][:3]
        other_workers = context["object_list"][3:]

        first_place_worker = top_workers[0] if top_workers else None
        second_place_worker = top_workers[1] if len(top_workers) > 1 else None
        third_place_worker = top_workers[2] if len(top_workers) > 2 else None

        context.update(
            {
                "top_workers": top_workers,
                "other_workers": other_workers,
                "first_place_worker": first_place_worker,
                "second_place_worker": second_place_worker,
                "third_place_worker": third_place_worker,
            }
        )

        return context


class PositionListView(LoginRequiredMixin, generic.ListView):
    model = Position
    paginate_by = 3
    template_name = "assignment_handler/position_list.html"

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(PositionListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = PositionSearchForm(initial={"name": name})
        return context

    def get_queryset(self) -> QuerySet:
        queryset = Position.objects.all()
        form = PositionSearchForm(self.request.GET)

        if form.is_valid():
            queryset = Position.objects.filter(
                name__icontains=form.cleaned_data["name"]
            )
        return queryset


class PositionCreateView(LoginRequiredMixin, generic.CreateView):
    model = Position
    form_class = PositionForm
    template_name = "assignment_handler/position_form.html"
    success_url = reverse_lazy("assignment_handler:position-list")


class PositionUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Position
    form_class = PositionForm
    template_name = "assignment_handler/position_form.html"
    success_url = reverse_lazy("assignment_handler:position-list")


class PositionDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Position
    template_name = "assignment_handler/position_confirm_delete.html"
    success_url = reverse_lazy("assignment_handler:position-list")


class TeamDetailView(LoginRequiredMixin, generic.DetailView):
    model = Team
    template_name = "assignment_handler/team_detail.html"


class TeamCreateView(LoginRequiredMixin, generic.CreateView):
    model = Team
    form_class = TeamForm
    success_url = reverse_lazy("assignment_handler:dashboard")


class TeamUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Team
    form_class = TeamForm
    template_name = "assignment_handler/team_form.html"

    def get_success_url(self):
        return reverse("assignment_handler:dashboard", kwargs={"pk": self.object.pk})


class TeamDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Team
    success_url = reverse_lazy("assignment_handler:dashboard")
    template_name = "assignment_handler/team_confirm_delete.html"


class TaskDetailView(LoginRequiredMixin, generic.DetailView):
    model = Task
    queryset = Task.objects.select_related("task_type").prefetch_related("assignees")
    template_name = "assignment_handler/task_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        task = context["object"]
        now = timezone.now()
        deadline = task.time_constraints
        deadline = datetime.datetime(
            deadline.year, deadline.month, deadline.day, tzinfo=timezone.utc
        )
        diff = deadline - now

        if diff.days > 0:
            context["days_left"] = diff.days
        else:
            context["passed_deadline"] = True

        return context


class TaskCreateView(LoginRequiredMixin, generic.CreateView):
    model = Task
    form_class = TaskForm
    template_name = "assignment_handler/task_form.html"
    success_url = reverse_lazy("assignment_handler:task-panel")

    def post(self, request, *args, **kwargs):
        self.object = None
        form = TaskForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.save()
            form.save_m2m()
            return self.form_valid(form)
        else:
            return self.form_invalid(form)


class TaskUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Task
    form_class = TaskForm
    template_name = "assignment_handler/task_form.html"

    def post(self, request, *args, **kwargs):
        form = TaskForm(request.POST, instance=self.get_object())

        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user

            if obj is not None:
                obj.save()
                form.save_m2m()

        return super().post(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy(
            "assignment_handler:task-detail", kwargs={"pk": self.kwargs["pk"]}
        )


class TaskDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Task
    success_url = reverse_lazy("assignment_handler:index")
    template_name = "assignment_handler/task_confirm_delete.html"


class TaskTypeListView(LoginRequiredMixin, generic.ListView):
    model = TaskType
    template_name = "assignment_handler/task_type_list.html"
    context_object_name = "task_type_list"
    paginate_by = 3

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(TaskTypeListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = TaskTypeSearchForm(initial={"name": name})
        return context

    def get_queryset(self):
        queryset = TaskType.objects.all()

        form = TaskTypeSearchForm(self.request.GET)
        if form.is_valid():
            return queryset.filter(name__icontains=form.cleaned_data["name"])
        return queryset


class TaskTypeCreateView(LoginRequiredMixin, generic.CreateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = "assignment_handler/task_type_form.html"
    success_url = reverse_lazy("assignment_handler:task-type-list")


class TaskTypeUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = TaskType
    form_class = TaskTypeForm
    template_name = "assignment_handler/task_type_form.html"
    success_url = reverse_lazy("assignment_handler:task-type-list")


class TaskTypeDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = TaskType
    template_name = "assignment_handler/task_type_confirm_delete.html"
    success_url = reverse_lazy("assignment_handler:task-type-list")


class ProjectDetailView(generic.DetailView):
    model = Project
    template_name = "assignment_handler/project_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = context["object"]

        if project.get_project_progress() == 100:
            current_phase = {
                "name": "Implementation and closure phase",
                "depiction": "It represents the final stage of execution and project completion. "
                "During this phase, the project plan is put into action, with the IT team "
                "actively coding, configuring software, and deploying hardware as per the project "
                "requirements. It also involves rigorous monitoring and control to ensure the project "
                "progresses as planned, addressing any issues promptly to successfully close "
                "the project.",
            }
        elif project.get_project_progress():
            current_phase = {
                "name": "Execution phase",
                "depiction": "It is the active implementation stage where the project plan is being effectuated. "
                "During this phase, the project team works on coding, configuring software, "
                "and hardware deployment according to the project requirements. "
                "It involves close monitoring and control to ensure that "
                "the project progresses as planned, and any issues that arise "
                "are promptly addressed to keep the "
                "project on track.",
            }
        else:
            current_phase = {
                "name": "Initiation and planning phase",
                "depiction": "It is the foundational stage where the project's objectives, scope, "
                "and stakeholders are defined. During this phase, a project charter is developed, "
                "outlining the project's purpose and initial requirements. "
                "Additionally, the project plan is created, including a timeline, resource allocation, "
                "and risk assessment to ensure a clear and organized path forward for the project.",
            }

        context["current_phase"] = current_phase

        now = timezone.now()

        deadline = project.time_constraints
        deadline = datetime.datetime(
            deadline.year, deadline.month, deadline.day, tzinfo=timezone.utc
        )

        diff = deadline - now
        if diff.days > 0:
            context["days_left"] = diff.days
        else:
            context["passed_deadline"] = True

        context["budget"] = project.budget
        context["funds_used"] = project.funds_used

        if project.funds_used > project.budget:
            overrun = project.funds_used - project.budget
            overrun_percent = overrun / project.budget * 100
            context["overrun"] = overrun
            context[
                "overrun_text"
            ] = f"The budget is exceeded by {overrun_percent:.2f}%"
            context["overrun_percent"] = overrun_percent

        elif project.funds_used <= project.budget:
            used_percent = project.funds_used / project.budget * 100
            progress_percent = project.funds_used / project.budget * 100
            context["used_text"] = f"Used {used_percent:.2f}% of the budget"
            context["progress_percent"] = progress_percent

        context["completed_projects"] = sum(
            1 for p in Project.objects.all() if p.get_project_progress() == 100
        )

        return context


class ProjectCreateView(LoginRequiredMixin, generic.CreateView):
    queryset = Project.objects.all()
    model = Project
    form_class = ProjectForm
    template_name = "assignment_handler/project_form_create.html"

    def get(self, *args, **kwargs):
        blocks = ProjectBlock.predefined_blocks()
        form = ProjectForm()

        context = {"form": form, "project_blocks": blocks, "object": None}

        return render(
            self.request, "assignment_handler/project_form_create.html", context
        )

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            form = ProjectForm(request.POST)

            if form.is_valid():
                project = form.save(commit=False)
                project.user = request.user

                result = validate_project_create_custom(request, form)

                predefined_blocks = ProjectBlock.predefined_blocks()

                errors_occurred = False

                for message in messages.get_messages(request):
                    if message.level == messages.ERROR:
                        messages.error(request, message)
                        errors_occurred = True

                if errors_occurred:
                    return redirect("assignment_handler:project-create")
                else:
                    project.save()
                    for block_id, fields in result.validation_map.items():
                        # create new block
                        name = result.block_name_id_corp[int(block_id)]

                        if int(block_id) < len(predefined_blocks):
                            total_tasks_str = form.data.get(
                                f'block_{predefined_blocks[int(block_id)]["index"]}_total_tasks',
                                "",
                            )

                            if total_tasks_str:
                                total_tasks_value = int(total_tasks_str)
                            else:
                                total_tasks_value = 0

                            new_project_block = ProjectBlock.objects.create(
                                project=project,
                                name=name,
                                depiction="Functional block",
                                total_tasks=total_tasks_value,
                                completed_tasks=0
                            )

                            new_project_block.save()

                    project.save()
                    form.save_m2m()

                    return redirect(
                        reverse_lazy(
                            "assignment_handler:project-detail",
                            kwargs={"pk": project.pk},
                        )
                    )

            else:
                url = reverse("assignment_handler:project-create")
                context = {"redirect_url": url}
                return render(request, "assignment_handler/error_page.html", context)

    def get_success_url(self):
        return reverse_lazy("assignment_handler:dashboard")

    def form_invalid(self, form):
        return super().form_invalid(form)


class ProjectUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = Project
    form_class = ProjectForm
    template_name = "assignment_handler/project_form_update.html"

    def get(self, request, *args, **kwargs):
        project = get_object_or_404(Project, pk=kwargs["pk"])
        form = ProjectForm(instance=project)

        blocks = ProjectBlock.predefined_blocks()
        predefined_blocks = ProjectBlock.predefined_blocks()
        all_blocks = project.projectblock_set.all()
        name_to_real_blocks = {b.name: b for b in project.projectblock_set.all()}
        existing_names = list(name_to_real_blocks.keys())

        context = {
            "form": form,
            "project_blocks": blocks,
            "object": project,
            "existing_names": existing_names,
            "existing_blocks": all_blocks,
            "predefined_blocks": predefined_blocks,
        }

        return render(request, "assignment_handler/project_form_update.html", context)

    def post(self, request, *args, **kwargs):
        if request.method == "POST":
            get_object_or_404(Project, pk=kwargs["pk"])

            form = ProjectForm(request.POST, instance=self.get_object())

            if form.is_valid():
                project = form.save()
                project.user = request.user

                result = validate_project_update_structures_custom(form)
                validate_project_update_procedure_custom(request, form)

                name_to_real_blocks = {
                    b.name: b for b in project.projectblock_set.all()
                }
                existing_names = list(name_to_real_blocks.keys())
                all_blocks = project.projectblock_set.all()
                predefined_blocks = ProjectBlock.predefined_blocks()

                # Deletion block
                if result.block_name_id_corp:
                    for block in project.projectblock_set.all():
                        if not any(
                            value == block.name
                            for value in result.block_name_id_corp.values()
                        ):
                            block.delete()
                else:
                    messages.error(request, "Project has to have at least one block")
                    return redirect("assignment_handler:project-update", pk=project.pk)

                errors_occurred = False

                for message in messages.get_messages(request):
                    if message.level == messages.ERROR:
                        messages.error(request, message)
                        errors_occurred = True

                if errors_occurred:
                    return redirect("assignment_handler:project-update", pk=project.pk)
                else:
                    for block_id, fields in result.validation_map.items():
                        if int(block_id) <= 6:
                            # create new block
                            name = result.block_name_id_corp[int(block_id)]

                            if int(block_id) < len(predefined_blocks):
                                total_tasks_str = form.data.get(
                                    f'new_block_{predefined_blocks[int(block_id)]["index"]}_total_tasks',
                                    "",
                                )

                                if total_tasks_str:
                                    total_tasks_value = int(total_tasks_str)
                                else:
                                    total_tasks_value = 0

                                new_project_block = ProjectBlock.objects.create(
                                    project=project,
                                    name=name,
                                    depiction="Functional block",
                                    total_tasks=total_tasks_value,
                                    completed_tasks=0
                                )

                                new_project_block.save()

                        elif int(block_id) > 6:
                            # edit existing blocks
                            name = result.block_name_id_corp[int(block_id)]
                            block = name_to_real_blocks[name]
                            completed_tasks = int(
                                form.data.get(f"block_{block.id}_completed_tasks") or 0
                            )
                            total_tasks = int(
                                form.data.get(f"block_{block.id}_total_tasks") or 0
                            )

                            if completed_tasks <= total_tasks:
                                block.completed_tasks = str(completed_tasks)
                                block.total_tasks = str(total_tasks)
                                block.save()
                            else:
                                error_message = (
                                    "Completed tasks cannot exceed total tasks"
                                )
                                messages.error(request, error_message)

                                context = {
                                    "form": form,
                                    "project": project,
                                    "predefined_blocks": predefined_blocks,
                                    "existing_names": existing_names,
                                    "existing_blocks": all_blocks,
                                }

                                return render(
                                    request,
                                    "assignment_handler/project_form_update.html",
                                    context,
                                )

                    project.save()

                    return redirect(
                        reverse_lazy(
                            "assignment_handler:project-detail",
                            kwargs={"pk": self.kwargs["pk"]},
                        )
                    )

            else:
                url = reverse("assignment_handler:project-update", kwargs={"pk": self.kwargs["pk"]})
                context = {"redirect_url": url}
                return render(request, "assignment_handler/error_page.html", context)

    def get_success_url(self):
        return reverse_lazy(
            "assignment_handler:project-detail", kwargs={"pk": self.kwargs["pk"]}
        )


class ProjectDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = Project
    success_url = reverse_lazy("assignment_handler:dashboard")
    template_name = "assignment_handler/project_confirm_delete.html"


class ProjectCategoryListView(LoginRequiredMixin, generic.ListView):
    model = ProjectCategory
    template_name = "assignment_handler/project_category_list.html"
    context_object_name = "project_category_list"
    paginate_by = 3

    def get_context_data(self, *, object_list=None, **kwargs):
        context = super(ProjectCategoryListView, self).get_context_data(**kwargs)
        name = self.request.GET.get("name", "")
        context["search_form"] = ProjectCategorySearchForm(initial={"name": name})
        return context

    def get_queryset(self):
        queryset = ProjectCategory.objects.all()
        form = ProjectCategorySearchForm(self.request.GET)

        if form.is_valid():
            return queryset.filter(name__icontains=form.cleaned_data["name"])
        return queryset


class ProjectCategoryCreateView(LoginRequiredMixin, generic.CreateView):
    model = ProjectCategory
    form_class = ProjectCategoryForm
    template_name = "assignment_handler/project_category_form.html"
    success_url = reverse_lazy("assignment_handler:project-category-list")


class ProjectCategoryUpdateView(LoginRequiredMixin, generic.UpdateView):
    model = ProjectCategory
    form_class = ProjectCategoryForm
    template_name = "assignment_handler/project_category_form.html"
    success_url = reverse_lazy("assignment_handler:project-category-list")


class ProjectCategoryDeleteView(LoginRequiredMixin, generic.DeleteView):
    model = ProjectCategory
    template_name = "assignment_handler/project_category_confirm_delete.html"
    success_url = reverse_lazy("assignment_handler:project-category-list")


class DashboardView(TemplateView):
    template_name = "assignment_handler/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        teams = Team.objects.annotate(projects_count=Count("projects"))
        context["projects"] = Project.objects.select_related("team")
        context["teams"] = teams
        return context


class TaskPanelView(TemplateView):
    template_name = "assignment_handler/task_panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        tag = self.request.GET.get("tag") or ""
        tags = Task.tags.filter(name=tag) if tag else Task.tags.all()

        if tag:
            queue_tasks = (
                Task.objects.annotate(assignees_count=Count("assignees"))
                .filter(assignees_count=0, tags__name=tag)
                .distinct()
            )
        else:
            queue_tasks = (
                Task.objects.annotate(assignees_count=Count("assignees"))
                .filter(assignees_count=0)
                .distinct()
            )

        if tag:
            underway_tasks = (
                Task.objects.annotate(assignees_count=Count("assignees"))
                .filter(
                    Q(is_completed=False) & Q(assignees_count__gt=0), tags__name=tag
                )
                .distinct()
            )
        else:
            underway_tasks = (
                Task.objects.annotate(assignees_count=Count("assignees"))
                .filter(Q(is_completed=False) & Q(assignees_count__gt=0))
                .distinct()
            )

        if tag:
            completed_tasks = (
                Task.objects.annotate(assignees_count=Count("assignees"))
                .filter(is_completed=True, assignees_count__gt=0, tags__name=tag)
                .distinct()
            )
        else:
            completed_tasks = (
                Task.objects.annotate(assignees_count=Count("assignees"))
                .filter(is_completed=True, assignees_count__gt=0)
                .distinct()
            )

        context.update(
            {
                "queue_tasks": queue_tasks,
                "underway_tasks": underway_tasks,
                "completed_tasks": completed_tasks,
                "tags": tags
            }
        )

        return context


class ProjectTrackingPanelView(TemplateView):
    template_name = "assignment_handler/project_tracking_panel.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total_projects = Project.objects.all()
        completed_projects_number = len(
            [p for p in Project.objects.all() if p.get_project_progress() == 100]
        )
        completed_projects = list(
            filter(lambda x: x.get_project_progress() == 100, Project.objects.all())
        )
        uncompleted_projects = list(
            filter(lambda x: x.get_project_progress() != 100, Project.objects.all())
        )
        average_progress_uncompleted = calculate_average_progress(uncompleted_projects)
        (
            predominant_status_completed,
            average_percent_completed,
        ) = budget_status_completed(completed_projects)
        (
            predominant_status_uncompleted,
            average_percent_uncompleted,
        ) = budget_status_uncompleted(uncompleted_projects)

        progress_list = []

        for project in Project.objects.all():
            if project.get_project_progress() == 100:
                progress_list.append(100)
            elif project.get_project_progress():
                progress_list.append(project.get_project_progress())
            else:
                progress_list.append(0)

        context.update(
            {
                "total_projects": total_projects,
                "completed_projects_number": completed_projects_number,
                "progress": progress_list,
                "time_constraints": Project.objects.values_list(
                    "time_constraints", flat=True
                ),
                "funds": Project.objects.values_list("budget", flat=True),
                "average_progress_uncompleted": average_progress_uncompleted,
                "predominant_status_uncompleted": predominant_status_uncompleted,
                "average_percent_completed": average_percent_completed,
                "predominant_status_completed": predominant_status_completed,
                "average_percent_uncompleted": average_percent_uncompleted
            }
        )

        return context


class ToggleAssignTaskView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        assignee = request.user
        task = Task.objects.get(id=self.kwargs["pk"])

        if task in assignee.tasks.all():
            assignee.tasks.remove(task)
        else:
            assignee.tasks.add(task)

        return redirect(
            reverse_lazy(
                "assignment_handler:task-detail", kwargs={"pk": self.kwargs["pk"]}
            )
        )


class ToggleTeamTransitionView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        worker = Worker.objects.get(id=self.kwargs["pk"])
        team_id = kwargs["team_id"]
        team = get_object_or_404(Team, pk=team_id)

        if worker in team.members.all():
            team.members.remove(worker)
            team.save()
        else:
            team.members.add(worker)
            team.save()

        return redirect(
            reverse_lazy("assignment_handler:worker-detail", kwargs={"pk": worker.id})
        )


class SwitchTeamView(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        user = request.user
        new_team = Team.objects.filter(id=self.kwargs["pk"]).first()

        action = self.kwargs["action"]

        if action == "delete":
            new_team.members.remove(user)
            new_team.save()
        else:
            new_team.members.add(user)
            new_team.save()

        return redirect("assignment_handler:dashboard")
