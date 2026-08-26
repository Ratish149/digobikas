from video.models import Video


def create_video(*, title: str, video_url: str) -> Video:
    """
    Create and save a new Video instance.
    """
    video = Video(
        title=title,
        video_url=video_url,
    )
    video.full_clean()
    video.save()
    return video


def update_video(*, video: Video, **data) -> Video:
    """
    Update an existing Video instance.
    """
    for field, value in data.items():
        if hasattr(video, field):
            setattr(video, field, value)

    video.full_clean()
    video.save()
    return video


def delete_video(*, video: Video) -> None:
    """
    Delete a Video instance.
    """
    video.delete()
