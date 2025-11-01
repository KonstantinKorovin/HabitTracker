from rest_framework import generics, permissions
from rest_framework.permissions import IsAuthenticated

from habits.models import Habit
from habits.pagination import ListCurrentUserPaginator
from habits.serializers import HabitSerializer


class ListIsPublishedHabitsView(generics.ListAPIView):
    queryset = Habit.objects.filter(is_published=True)
    serializer_class = HabitSerializer
    permission_classes = [permissions.IsAuthenticated]


class ListHabitsTheCurrentUserView(generics.ListAPIView):
    serializer_class = HabitSerializer
    pagination_class = ListCurrentUserPaginator
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Habit.objects.filter(user=self.request.user)

        return Habit.objects.none()


class HabitCreateView(generics.CreateAPIView):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]


class HabitUpdateView(generics.UpdateAPIView):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]


class HabitRetrieveView(generics.RetrieveAPIView):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]


class HabitDestroyView(generics.DestroyAPIView):
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
