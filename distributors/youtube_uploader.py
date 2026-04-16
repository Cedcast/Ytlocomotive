"""
distributors/youtube_uploader.py
Uploads videos as YouTube Shorts via YouTube Data API v3.
OAuth 2.0 credentials are loaded from youtube_token.json (auto-refreshed).
On first run a browser window opens for authorization.
"""
import os

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

import config
from utils.logger import get_logger

logger = get_logger(__name__)

_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

def _creds() -> Credentials:
    creds = None
    if os.path.exists(config.YOUTUBE_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(config.YOUTUBE_TOKEN_FILE, _SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            logger.info("YouTube token refreshed.")
        else:
            if not os.path.exists(config.YOUTUBE_CLIENT_SECRETS_FILE):
                raise FileNotFoundError(
                    f"Missing {config.YOUTUBE_CLIENT_SECRETS_FILE}. "
                    "Download from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(config.YOUTUBE_CLIENT_SECRETS_FILE, _SCOPES)
            creds = flow.run_local_server(port=0)
        with open(config.YOUTUBE_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds

def upload_short(video_path: str, title: str, description: str, privacy_status: str = "public") -> bool:
    """
    Uploads a vertical video as a YouTube Short.

    Args:
        video_path: Local MP4 path.
        title: Video title (#Shorts appended automatically).
        description: Video description/caption.
        privacy_status: 'public', 'private', or 'unlisted'.

    Returns:
        True on success, False on failure.
    """
    try:
        youtube = build("youtube", "v3", credentials=_creds())
        shorts_title = title if "#Shorts" in title else f"{title} #Shorts"
        request = youtube.videos().insert(
            part="snippet,status",
            body={
                "snippet": {
                    "title": shorts_title[:100],
                    "description": description,
                    "categoryId": config.YOUTUBE_CATEGORY_ID,
                    "tags": ["shorts", "signals", "predictions"],
                },
                "status": {
                    "privacyStatus": privacy_status,
                    "madeForKids": False,
                    "selfDeclaredMadeForKids": False,
                },
            },
            media_body=MediaFileUpload(video_path, mimetype="video/mp4", resumable=True, chunksize=1024 * 1024),
        )
        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.debug(f"YouTube upload: {int(status.progress() * 100)}%")
        logger.info(f"YouTube Short live: https://www.youtube.com/shorts/{response['id']}")
        return True
    except Exception as exc:
        logger.error(f"YouTube upload failed: {exc}")
        return False