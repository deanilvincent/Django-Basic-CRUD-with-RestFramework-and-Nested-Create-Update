from rest_framework import viewsets
from .serializers import TodoSerializers
from .models import Todo


class TodoViewsets(viewsets.ModelViewSet):
    queryset = Todo.objects.all()
    serializer_class = TodoSerializers