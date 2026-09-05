from unittest.mock import MagicMock, patch

from app.services.youtube_service import YouTubeService


def test_playlist_reuses_metadata_without_second_extract_info(tmp_path):
    metadata = {
        "_type": "playlist",
        "title": "Playlist de teste",
        "entries": [
            {"_type": "url", "url": "https://www.youtube.com/watch?v=one", "id": "one", "title": "Um"},
            {"_type": "url", "url": "https://www.youtube.com/watch?v=two", "id": "two", "title": "Dois"},
        ],
    }
    fake_ydl = MagicMock()
    fake_ydl.__enter__.return_value = fake_ydl
    fake_ydl.__exit__.return_value = False

    with patch("app.services.youtube_service.yt_dlp.YoutubeDL", return_value=fake_ydl) as ydl_cls:
        service = YouTubeService(str(tmp_path))
        result = service.extract_audio(
            "https://www.youtube.com/watch?v=one&list=PLTEST",
            format="mp3",
            quality="128K",
            metadata=metadata,
        )

    assert result["success"] is True
    assert result["playlist_count"] == 2
    fake_ydl.extract_info.assert_not_called()
    assert fake_ydl.process_ie_result.call_count == 2
    assert ydl_cls.call_count == 1
