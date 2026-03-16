import re
from youtube_transcript_api import YouTubeTranscriptApi

class InvalidYouTubeURLError(Exception):
    """Raised when a generic invalid YouTube URL is provided."""
    pass

class TranscriptNotAvailableError(Exception):
    """Raised when a transcript cannot be fetched for a video."""
    pass

def extract_video_id(url: str) -> str:
    """
    Extracts the YouTube video ID from a given URL.
    Supports both youtu.be and youtube.com formats.
    """
    # Regex to match youtube.com/watch?v=ID and youtu.be/ID
    pattern = r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:[^\/\n\s]+\/\S+\/|(?:v|e(?:mbed)?)\/|\S*?[?&]v=)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
    match = re.search(pattern, url)

    if match:
        return match.group(1)
    else:
        raise InvalidYouTubeURLError("Could not extract a valid YouTube video ID from the provided URL.")

def get_transcript(url: str) -> str:
    """
    Fetches the transcript for a given YouTube video URL.
    Returns the transcript as a single merged string.

    Compatible with youtube-transcript-api >= 1.x.x (instance-based API).
    """
    video_id = extract_video_id(url)

    try:
        # v1.x: API is now instance-based; use fetch() instead of the old get_transcript()
        ytt_api = YouTubeTranscriptApi()
        fetched = ytt_api.fetch(video_id)

        # fetched is a FetchedTranscript object — iterate over snippets and join text
        transcript_text = " ".join(snippet.text for snippet in fetched)

        return transcript_text

    except InvalidYouTubeURLError:
        raise
    except Exception as e:
        # The library throws various exceptions if the transcript doesn't exist,
        # is disabled, blocked, etc. Re-raise as a user-friendly error.
        raise TranscriptNotAvailableError(
            f"Transcript is not available for this video. Reason: {str(e)}"
        )
