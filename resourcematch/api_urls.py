from django.urls import path, include
from rest_framework import routers
from accounts.api import UserViewSet, BeneficiaryViewSet, VolunteerViewSet
from resources.api import ResourceViewSet, ResourceTypeViewSet
from matches.api import MatchViewSet
from feedback.api import FeedbackViewSet

router = routers.DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'beneficiaries', BeneficiaryViewSet)
router.register(r'volunteers', VolunteerViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'resource-types', ResourceTypeViewSet)
router.register(r'matches', MatchViewSet)
router.register(r'feedback', FeedbackViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('rest_framework.urls', namespace='rest_framework')),
]

