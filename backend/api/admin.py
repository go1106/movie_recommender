# backend/api/admin.py
from django.contrib import admin
from .models import Event, RecommendationCache, Movie, Rating  # etc.

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "movie", "action", "created_at")

@admin.register(RecommendationCache)
class RecCacheAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "model_version", "created_at")

# If you register others, do it once, e.g.:
@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "release_year", "avg_rating", "rating_count")

