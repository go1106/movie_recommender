from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, RatingViewSet, RecommendView, EventView, MoreLikeThisView

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'ratings', RatingViewSet, basename='rating')  
urlpatterns = [
    path('', include(router.urls)),
    path("api/recommendations/", RecommendView.as_view()),
    path("api/events/", EventView.as_view()),
    path("api/movies/<int:movieId>/more-like-this/", MoreLikeThisView.as_view()),
]