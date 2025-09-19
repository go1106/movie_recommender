from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MovieViewSet, RatingViewSet, RecommendView
from .views import RecCacheView, top_rated,trending
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

router = DefaultRouter()
router.register(r'movies', MovieViewSet, basename='movie')
router.register(r'ratings', RatingViewSet, basename='rating')  
urlpatterns = [
    path('', include(router.urls)),
    path("api/recommendations/", RecommendView.as_view()),
    path("rec-cache/<str:username>/", RecCacheView.as_view()),
    path("trending/", trending),
    path("top-rated/", top_rated),
    #path("api/events/", EventView.as_view()),
    #path("api/movies/<int:movieId>/more-like-this/", MoreLikeThisView.as_view()),
]