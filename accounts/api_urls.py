from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import UserViewSet, BeneficiaryViewSet, VolunteerViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'beneficiaries', BeneficiaryViewSet)
router.register(r'volunteers', VolunteerViewSet)

urlpatterns = [
    path('', include(router.urls)),
]

