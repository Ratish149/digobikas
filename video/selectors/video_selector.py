from django.db.models import QuerySet

from video.models import Video


def get_videos_list() -> QuerySet[Video]:
    """
    Fetch all video records optimized with .only().
    """
    return Video.objects.only(
        "id",
        "title",
        "video_url",
        "created_at",
        "updated_at",
    )


def get_video_by_id(video_id: int) -> Video:
    """
    Fetch a single video record by ID.
    """
    return Video.objects.only(
        "id",
        "title",
        "video_url",
        "created_at",
        "updated_at",
    ).get(id=video_id)
