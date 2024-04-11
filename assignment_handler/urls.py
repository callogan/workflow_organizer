from django.urls import path

from assignment_handler.views import (
    index,
    WorkerDetailView,
    WorkerCreate,
    WorkerUpdate,
    WorkerDelete,
    WorkersListView,
    TeamDetailView,
    TeamCreate,
    TeamUpdate,
    TeamDelete,
    PositionListView,
    PositionCreate,
    PositionUpdate,
    PositionDelete,
    TaskDetailView,
    TaskCreate,
    TaskUpdate,
    TaskDelete,
    TaskTypeListView,
    TaskTypeCreate,
    TaskTypeUpdate,
    TaskTypeDelete,
    ProjectDetailView,
    ProjectCreate,
    ProjectUpdate,
    ProjectDelete,
    ProjectCategoryListView,
    ProjectCategoryCreate,
    ProjectCategoryUpdate,
    ProjectCategoryDelete,
    DashboardView,
    TaskPanelView,
    ProjectTrackingPanelView,
    ToggleAssignTaskView,
    ToggleTeamTransitionView,
    SwitchTeamView,
)

urlpatterns = [
    path("", index, name="index"),
    path(
        "workers/<int:pk>/",
        WorkerDetailView.as_view(),
        name="worker-detail",
    ),
    path(
        "accounts/register/",
        WorkerCreate.as_view(),
        name="worker-create",
    ),
    path(
        "workers/<int:pk>/update/",
        WorkerUpdate.as_view(),
        name="worker-update",
    ),
    path(
        "workers/<int:pk>/delete/",
        WorkerDelete.as_view(),
        name="worker-delete",
    ),
    path(
        "workers_list/",
        WorkersListView.as_view(),
        name="workers-list",
        ),
    path(
        "positions/",
        PositionListView.as_view(),
        name="position-list",
    ),
    path(
        "positions/create/",
        PositionCreate.as_view(),
        name="position-create",
    ),
    path(
        "positions/<int:pk>/update/",
        PositionUpdate.as_view(),
        name="position-update",
    ),
    path(
        "positions/<int:pk>/delete/",
        PositionDelete.as_view(),
        name="position-delete",
    ),
    path(
        "teams/<pk>/",
        TeamDetailView.as_view(),
        name="team-detail",
    ),
    path(
        "teams/create/",
        TeamCreate.as_view(),
        name="team-create",
    ),
    path(
        "teams/<int:pk>/update/",
        TeamUpdate.as_view(),
        name="team-update",
    ),
    path(
        "teams/<int:pk>/delete",
        TeamDelete.as_view(),
        name="team-delete",
    ),
    path(
        "tasks/<int:pk>/",
        TaskDetailView.as_view(),
        name="task-detail",
    ),
    path(
        "tasks/create/",
        TaskCreate.as_view(),
        name="task-create",
    ),
    path(
        "tasks/<int:pk>/update/",
        TaskUpdate.as_view(),
        name="task-update"
    ),
    path(
        "tasks/<int:pk>/delete/",
        TaskDelete.as_view(),
        name="task-delete",
    ),
    path(
        "task-types/",
        TaskTypeListView.as_view(),
        name="task-type-list",
    ),
    path(
        "task-types/create/",
        TaskTypeCreate.as_view(),
        name="task-type-create",
    ),
    path(
        "task-types/<int:pk>/update/",
        TaskTypeUpdate.as_view(),
        name="task-type-update",
    ),
    path(
        "task-types/<int:pk>/delete/",
        TaskTypeDelete.as_view(),
        name="task-type-delete",
    ),
    path(
        "projects/<int:pk>/",
        ProjectDetailView.as_view(),
        name="project-detail",
    ),
    path(
        "projects/create/",
        ProjectCreate.as_view(),
        name="project-create",
    ),
    path(
        "projects/<int:pk>/update",
        ProjectUpdate.as_view(),
        name="project-update",
    ),
    path(
        "projects/<int:pk>/delete",
        ProjectDelete.as_view(),
        name="project-delete",
    ),
    path(
        "project-categories/",
        ProjectCategoryListView.as_view(),
        name="project-category-list",
    ),
    path(
        "project-categories/create/",
        ProjectCategoryCreate.as_view(),
        name="project-category-create",
    ),
    path(
        "project-categories/<int:pk>/update/",
        ProjectCategoryUpdate.as_view(),
        name="project-category-update",
    ),
    path(
        "project-categories/<int:pk>/delete/",
        ProjectCategoryDelete.as_view(),
        name="project-category-delete",
    ),
    path(
        "dashboard/",
        DashboardView.as_view(),
        name="dashboard",
    ),
    path(
        "task_panel/",
        TaskPanelView.as_view(),
        name="task-panel",
    ),
    path(
        "project_tracking_panel/",
        ProjectTrackingPanelView.as_view(),
        name="project-tracking-panel",
    ),
    path(
        "tasks/<int:pk>/toggle-assign/",
        ToggleAssignTaskView.as_view(),
        name="toggle-task-assign",
    ),
    path(
        "teams/<int:pk>/toggle-add/<int:team_id>/",
        ToggleTeamTransitionView.as_view(),
        name="toggle-team-transition",
    ),
    path(
        "teams/<int:pk>/switch/<str:action>/",
        SwitchTeamView.as_view(),
        name="switch-team",
    ),
]

app_name = "assignment_handler"
