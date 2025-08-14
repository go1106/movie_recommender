from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, RatingViewSet

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'ratings', RatingViewSet, basename='rating')  
urlpatterns = [
    path('', include(router.urls)),
]