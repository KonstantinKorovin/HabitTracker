from django.urls import path

from habits.apps import HabitsConfig
from habits.views import (
    HabitCreateView,
    HabitDestroyView,
    HabitRetrieveView,
    HabitUpdateView,
    ListHabitsTheCurrentUserView,
    ListIsPublishedHabitsView,
)

app_name = HabitsConfig.name


urlpatterns = [
    path("create/habit/", HabitCreateView.as_view(), name="create-habit"),
    path("update/<int:pk>/habit/", HabitUpdateView.as_view(), name="update-habit"),
    path("habit/<int:pk>/", HabitRetrieveView.as_view(), name="habit-retrieve"),
    path("habit/<int:pk>/destroy/", HabitDestroyView.as_view(), name="habit-destroy"),
    path("list/published/", ListIsPublishedHabitsView.as_view(), name="list-published"),
    path("my/", ListHabitsTheCurrentUserView.as_view(), name="my-habits"),
]
