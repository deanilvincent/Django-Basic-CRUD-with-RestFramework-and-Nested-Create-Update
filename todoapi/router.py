from rest_framework import routers
from .viewsets import TodoViewsets
router = routers.DefaultRouter()
router.register('todo', TodoViewsets)
