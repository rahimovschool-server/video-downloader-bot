import re
from enum import Enum


class UrlType(Enum):
    YOUTUBE_VIDEO = "youtube_video"
    YOUTUBE_SHORTS = "youtube_shorts"
    YOUTUBE_PLAYLIST = "youtube_playlist"
    INSTAGRAM_POST = "instagram_post"
    INSTAGRAM_REEL = "instagram_reel"
    INSTAGRAM_STORY = "instagram_story"
    UNKNOWN = "unknown"


YOUTUBE_PATTERNS = [
    r"(?:https?://)?(?:www\.)?youtube\.com/watch\?v=[\w-]+",
    r"(?:https?://)?(?:www\.)?youtu\.be/[\w-]+",
    r"(?:https?://)?(?:www\.)?youtube\.com/shorts/[\w-]+",
    r"(?:https?://)?(?:www\.)?youtube\.com/playlist\?list=[\w-]+",
    r"(?:https?://)?(?:m\.)?youtube\.com/watch\?v=[\w-]+",
]

INSTAGRAM_PATTERNS = [
    r"(?:https?://)?(?:www\.)?instagram\.com/p/[\w-]+",
    r"(?:https?://)?(?:www\.)?instagram\.com/reel/[\w-]+",
    r"(?:https?://)?(?:www\.)?instagram\.com/stories/[\w/]+",
    r"(?:https?://)?(?:www\.)?instagram\.com/tv/[\w-]+",
]


def detect_url(text: str) -> tuple[str | None, UrlType]:
    """
    Matndagi URL'ni aniqlaydi va turini qaytaradi.
    Returns: (url, UrlType)
    """
    # Extract URL from text
    url_pattern = r"https?://[^\s]+"
    urls = re.findall(url_pattern, text)

    if not urls:
        return None, UrlType.UNKNOWN

    url = urls[0].rstrip("/")

    # YouTube Shorts
    if re.search(r"youtube\.com/shorts/", url):
        return url, UrlType.YOUTUBE_SHORTS

    # YouTube Playlist
    if re.search(r"youtube\.com/playlist", url):
        return url, UrlType.YOUTUBE_PLAYLIST

    # YouTube Video
    for pattern in YOUTUBE_PATTERNS[:3]:
        if re.search(pattern, url):
            return url, UrlType.YOUTUBE_VIDEO

    # Instagram Reel
    if re.search(r"instagram\.com/reel/", url):
        return url, UrlType.INSTAGRAM_REEL

    # Instagram Story
    if re.search(r"instagram\.com/stories/", url):
        return url, UrlType.INSTAGRAM_STORY

    # Instagram Post
    if re.search(r"instagram\.com/p/", url) or re.search(r"instagram\.com/tv/", url):
        return url, UrlType.INSTAGRAM_POST

    return url, UrlType.UNKNOWN


def is_youtube(url_type: UrlType) -> bool:
    return url_type in (UrlType.YOUTUBE_VIDEO, UrlType.YOUTUBE_SHORTS, UrlType.YOUTUBE_PLAYLIST)


def is_instagram(url_type: UrlType) -> bool:
    return url_type in (UrlType.INSTAGRAM_POST, UrlType.INSTAGRAM_REEL, UrlType.INSTAGRAM_STORY)
