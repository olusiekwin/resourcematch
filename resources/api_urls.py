from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import ResourceViewSet, ResourceTypeViewSet

router = DefaultRouter()
router.register(r'resources', ResourceViewSet)
router.register(r'types', ResourceTypeViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

