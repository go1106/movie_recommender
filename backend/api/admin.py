from django.contrib import admin

from django.contrib import admin
from .models import Event, RecommendationCache, Embedding

@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('id','userId','movie','action','created_at')
    list_filter = ('action',)
    search_fields = ('userId', 'movie__title')

@admin.register(RecommendationCache)
class RecCacheAdmin(admin.ModelAdmin):
    list_display = ('userId','model_version','updated_at')
    search_fields = ('userId',)

@admin.register(Embedding)
class EmbeddingAdmin(admin.ModelAdmin):
    list_display = ('object_type','object_id','model_version','dim','created_at')
    list_filter = ('object_type','model_version')
    search_fields = ('object_id',)
