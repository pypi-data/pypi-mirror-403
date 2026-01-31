"""Type stub for golpo.client — public API only. Private methods are omitted so they do not appear in IntelliSense."""

from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union

__all__ = ["Golpo"]


class Golpo:
    """Python SDK for Golpo with transparent, parallel uploads."""

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.golpoai.com",
    ) -> None: ...

    def create_podcast(
        self,
        prompt: str,
        uploads: Optional[Union[str, Path, Iterable[Union[str, Path]]]] = None,
        *,
        add_music: bool = False,
        voice_instructions: Optional[str] = None,
        personality_1: Optional[str] = None,
        personality_2: Optional[str] = None,
        do_research: bool = False,
        tts_model: str = "accurate",
        language: Optional[str] = None,
        style: Optional[str] = "conversational",
        bg_music: Optional[str] = None,
        poll_interval: int = 2,
        max_workers: int = 8,
        output_volume: float = 1.0,
        no_voice_chunking: bool = False,
    ) -> tuple[str, str]: ...

    def create_video(
        self,
        prompt: str,
        uploads: Optional[Union[str, Path, Iterable[Union[str, Path]]]] = None,
        *,
        voice_instructions: Optional[str] = None,
        personality_1: Optional[str] = None,
        do_research: bool = False,
        tts_model: str = "accurate",
        language: Optional[str] = None,
        style: Optional[str] = "solo-female",
        bg_music: Optional[str] = "engaging",
        bg_volume: float = 1.4,
        video_type: Optional[str] = "long",
        include_watermark: bool = True,
        new_script: Optional[str] = None,
        just_return_script: bool = False,
        logo: Optional[Union[str, Path]] = None,
        timing: str = "1",
        poll_interval: int = 2,
        max_workers: int = 8,
        output_volume: float = 1.0,
        video_instructions: Optional[str] = None,
        use_color: bool = False,
    ) -> tuple[str, str]: ...

    def edit_video(
        self,
        video_id: str,
        frame_ids: List[str],
        edit_prompts: List[str],
        video_url: str,
        *,
        reference_images: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        poll_interval_ms: int = 2000,
        auto_combine: bool = False,
    ) -> Dict[str, str]: ...

    def combine_videos(
        self,
        mp4_urls: List[str],
        *,
        video_url: Optional[str] = None,
        poll_interval_ms: int = 2000,
    ) -> str: ...

    def update_video(
        self,
        video_id: str,
        *,
        prompt: Optional[str] = None,
        context: Optional[str] = None,
        scenes: Optional[int] = None,
        video_url: Optional[str] = None,
        frame_animations: Optional[Dict[str, Any]] = None,
        jwt_token: str = ...,
    ) -> Dict[str, Any]: ...
