from .models import Event

def log_event(user_id: int | None, action: str, movie_id: int | None, **ctx):
    Event.objects.create(userId=user_id, action=action, movie_id=movie_id, context=ctx)
