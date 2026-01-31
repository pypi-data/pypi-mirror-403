import concurrent.futures
import mimetypes
import time
from pathlib import Path
from typing import Iterable, Union, List, Optional, Dict, Any
import re
import math
import warnings

import requests


class Golpo:
    """Python SDK for Golpo with transparent, parallel uploads.

    • Local file paths are uploaded to S3 via `/upload-url` (done in parallel).
    • Already‑hosted resources (strings that look like URLs) are passed through.
    • The backend receives every document as an **upload_urls** form field so it
      can fetch them internally.  This avoids the ALB 1‑MB limit.
    • The call blocks until the podcast is finished and returns its final URL.
    """

    _URL_RE = re.compile(r"^(https?|s3)://", re.I)

    def __init__(self, api_key: str, base_url: str = "https://api.golpoai.com") -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = {"x-api-key": api_key}

    # ------------------------------------------------------------------
    # internal helper: presign → PUT → return S3 URL
    # ------------------------------------------------------------------
    def _upload_to_s3(self, path: Path) -> str:
        presign = requests.post(
            f"{self.base_url}/upload-url",
            headers=self.headers,
            data={"filename": path.name},
            timeout=30,
        )
        presign.raise_for_status()
        info = presign.json()  # {'url': ..., 'key': ...}

        ctype = mimetypes.guess_type(path)[0] or "application/octet-stream"
        with path.open("rb") as fh:
            put = requests.put(info["url"], data=fh, headers={"Content-Type": ctype})
        put.raise_for_status()
        return info["url"].split("?", 1)[0]

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------
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
        style: Optional[str] = "conversational", # either conversational, solo-male or solo-female
        bg_music: Optional[str] = None, # either None, jazz, lofi or dramatic. 
        poll_interval: int = 2,
        max_workers: int = 8,
        output_volume: float = 1.0,
        no_voice_chunking: bool = False
    ) -> str:
        """Generate a podcast and return its final URL."""
        if not prompt:
            raise ValueError("Prompt is mandatory")
        # --------- basic form fields ----------------------------------
        fields: List[tuple[str, str]] = [
            ("prompt", prompt),
            ("add_music", str(add_music).lower()),
            ("do_research", str(do_research).lower()),
            ("tts_model", tts_model),
            ("style", style)
        ]
        if voice_instructions:
            fields.append(("voice_instructions", voice_instructions))
        if personality_1:
            fields.append(("personality_1", personality_1))
        if personality_2:
            fields.append(("personality_2", personality_2))
        if language:
            fields.append(("language", language))
        if bg_music:
            fields.append(("bg_music", bg_music))
        if output_volume:
            fields.append(("output_volume", str(output_volume)))
        if no_voice_chunking:
            fields.append(("no_voice_chunking", str(no_voice_chunking).lower()))


        # --------- gather documents -----------------------------------
        if uploads:
            if isinstance(uploads, (str, Path)):
                uploads = [uploads]

            local_paths: List[Path] = []
            passthrough_urls: List[str] = []

            for item in uploads:  # type: ignore[not-an-iterable]
                # treat str & Path uniformly
                if isinstance(item, Path):
                    path_obj = item.expanduser()
                else:
                    # trim any accidental angle‑brackets or whitespace
                    item_str = str(item).strip().lstrip("<").rstrip(">")
                    if self._URL_RE.match(item_str):
                        passthrough_urls.append(item_str)
                        continue
                    path_obj = Path(item_str).expanduser()

                if path_obj.exists():
                    local_paths.append(path_obj)
                else:
                    raise FileNotFoundError(path_obj)

            # upload local files in parallel
            if local_paths:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(max_workers, len(local_paths))
                ) as pool:
                    futs = [pool.submit(self._upload_to_s3, p) for p in local_paths]
                    for fut in concurrent.futures.as_completed(futs):
                        passthrough_urls.append(fut.result())

            # add to multipart body
            fields += [("upload_urls", url) for url in passthrough_urls]

        # --------- POST /generate ------------------------------------
        gen = requests.post(
            f"{self.base_url}/generate",
            headers=self.headers,
            data=fields,  # list[tuple] keeps order & repeats
            timeout=60,
        )
        gen.raise_for_status()
        job_id = gen.json()["job_id"]

        # --------- poll until finished -------------------------------
        while True:
            status = requests.get(
                f"{self.base_url}/status/{job_id}", headers=self.headers, timeout=30
            ).json()
            if status["status"] == "completed":
                return status["podcast_url"], status["podcast_script"]
            time.sleep(poll_interval)

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
        style: Optional[str] = "solo-female", # either solo-male or solo-female
        bg_music: Optional[str] = "engaging", 
        bg_volume = 1.4,
        video_type: Optional[str] = "long", 
        include_watermark = True, 
        new_script: Optional[str] = None, 
        just_return_script: bool = False, 
        logo = None, 
        timing="1", 
        poll_interval: int = 2,
        max_workers: int = 8,
        output_volume: float = 1.0, 
        video_instructions: str = None, 
        use_color=False
    ) -> str:
        """Generate a podcast and return its final URL."""
        def estimate_read_time(script: str) -> str:
            words_per_minute = 150
            word_count = len(script.split())
            minutes = word_count / words_per_minute
            rounded_minutes = round(minutes * 2) / 2
            return str(rounded_minutes)
        if new_script:
            timing = estimate_read_time(new_script)
        # Validate timing parameter
        try:
            timing_float = float(timing)
            if timing_float < 0.25:
                raise ValueError(f"Timing parameter must be 0.25 or above, got {timing_float}")
        except (ValueError, TypeError) as e:
            if "could not convert" in str(e):
                raise ValueError(f"Timing parameter must be a valid number, got {timing}")
            raise

        # --------- basic form fields ----------------------------------
        fields: List[tuple[str, str]] = [
            ("prompt", prompt),
            ("do_research", str(do_research).lower()),
            ("tts_model", tts_model),
            ("bg_volume", str(bg_volume)),
            ("style", style)
        ]
        if language:
            fields.append(("language", language))
        if video_instructions:
            fields.append(("video_instructions", video_instructions))
        if voice_instructions:
            fields.append(("voice_instructions", voice_instructions))
        if personality_1:
            fields.append(("personality_1", personality_1))
        if use_color:
            fields.append(("use_color", use_color))      
        if bg_music:
            fields.append(("bg_music", bg_music))
        if timing:
            fields.append(("timing", timing))
        if new_script:
            fields.append(("new_script", new_script))
        if just_return_script:
            fields.append(("just_return_script", just_return_script))
        if output_volume:
            fields.append(("output_volume", output_volume))

        if video_type:
            fields.append(("video_type", video_type))
        else:
            fields.append(("video_type", "long"))
        
        if bg_volume:
            fields.append(("bg_volume", bg_volume))
        
        if logo:
            logo_str = str(logo).strip().lstrip("<").rstrip(">")
            if not self._URL_RE.match(logo_str):
                logo_url = self._upload_to_s3(Path(logo_str).expanduser())
            else:
                logo_url = logo_str
            include_watermark=True
            fields.append(("logo", logo_url))
        fields.append(("include_watermark", str(include_watermark).lower()))
        # --------- gather documents -----------------------------------
        if uploads:
            if isinstance(uploads, (str, Path)):
                uploads = [uploads]

            local_paths: List[Path] = []
            passthrough_urls: List[str] = []

            for item in uploads:  # type: ignore[not-an-iterable]
                # treat str & Path uniformly
                if isinstance(item, Path):
                    path_obj = item.expanduser()
                else:
                    # trim any accidental angle‑brackets or whitespace
                    item_str = str(item).strip().lstrip("<").rstrip(">")
                    if self._URL_RE.match(item_str):
                        passthrough_urls.append(item_str)
                        continue
                    path_obj = Path(item_str).expanduser()

                if path_obj.exists():
                    local_paths.append(path_obj)
                else:
                    raise FileNotFoundError(path_obj)

            # upload local files in parallel
            if local_paths:
                with concurrent.futures.ThreadPoolExecutor(
                    max_workers=min(max_workers, len(local_paths))
                ) as pool:
                    futs = [pool.submit(self._upload_to_s3, p) for p in local_paths]
                    for fut in concurrent.futures.as_completed(futs):
                        passthrough_urls.append(fut.result())

            # add to multipart body
            fields += [("upload_urls", url) for url in passthrough_urls]

        # --------- POST /generate ------------------------------------
        print(fields)
        gen = requests.post(
            f"{self.base_url}/generate",
            headers=self.headers,
            data=fields,  # list[tuple] keeps order & repeats
            timeout=60,
        )
        gen.raise_for_status()
        job_id = gen.json()["job_id"]

        # --------- poll until finished -------------------------------
        while True:
            response = requests.get(
                f"{self.base_url}/status/{job_id}", headers=self.headers, timeout=30
            )
            try:
                response.raise_for_status()
                status = response.json()
            except requests.exceptions.HTTPError:
                time.sleep(poll_interval)
                continue
            except ValueError:  # includes JSONDecodeError
                time.sleep(poll_interval)
                continue
            
            if status["status"] == "completed":
                return status["podcast_url"], status["podcast_script"]
            time.sleep(poll_interval)

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
        auto_combine: bool = False
    ) -> Dict[str, str]:
        """Edit specific frames of a video and regenerate the video.
        
        This method polls until completion and returns the final edited video URL.
        If auto_combine is True, it will also combine all frames into a final video.
        
        Args:
            video_id: The ID of the video to edit
            frame_ids: List of frame IDs to edit
            edit_prompts: List of edit prompts (must match frame_ids length)
            video_url: URL of the original video (required)
            reference_images: Optional list of reference image URLs
            user_id: Optional user ID
            poll_interval_ms: Polling interval in milliseconds
            auto_combine: If True, automatically combine all frames after editing
            
        Returns:
            Dictionary with 'video_url' and 'job_id' keys
        """
        if len(frame_ids) != len(edit_prompts):
            raise ValueError("frame_ids and edit_prompts must have the same length")
        
        if not video_url:
            raise ValueError("video_url is required")
        
        # Create the edit job
        job_id = self._edit_video_job(video_id, {
            "frame_ids": frame_ids,
            "edit_prompts": edit_prompts,
            "reference_images": reference_images,
            "video_url": video_url,
            "user_id": user_id
        })
        
        # Poll for completion
        edit_result = self._poll_edit_status(job_id, poll_interval_ms)
        # If auto_combine is enabled, combine all frames after edit completes
        if auto_combine:
            return self._combine_edited_frames(video_id, {
                "frame_ids": frame_ids,
                "video_url": video_url,
                "poll_interval_ms": poll_interval_ms
            })
        
        return {
            "video_url": edit_result,
            "job_id": job_id
        }

    def combine_videos(
        self,
        mp4_urls: List[str],
        *,
        video_url: Optional[str] = None,
        poll_interval_ms: int = 2000
    ) -> str:
        """Combine multiple MP4 videos into a single video.
        
        This is used to combine frame animations into a final video.
        
        Args:
            mp4_urls: List of MP4 video URLs to combine
            video_url: Optional original video URL for audio
            poll_interval_ms: Polling interval in milliseconds
            
        Returns:
            URL of the combined video
        """
        if not mp4_urls or len(mp4_urls) == 0:
            raise ValueError("At least one MP4 URL is required")
        
        body: Dict[str, Any] = {
            "mp4_urls": mp4_urls
        }
        
        if video_url:
            body["video_url"] = video_url
        
        # Create the combine job
        response = requests.post(
            f"{self.base_url}/combine-videos",
            headers={**self.headers, "Content-Type": "application/json"},
            json=body,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        combine_job_id = data.get("job_id")
        if not combine_job_id:
            raise ValueError("No job ID received from combine-videos API")
        
        # Poll for completion using the same edit-status endpoint
        return self._poll_edit_status(combine_job_id, poll_interval_ms)

    # ------------------------------------------------------------------
    # Private helper methods
    # ------------------------------------------------------------------
    
    def _edit_video_job(
        self,
        video_id: str,
        opts: Dict[str, Any]
    ) -> str:
        """Create an edit job for a video without waiting for completion.
        
        Returns the job ID that can be used to check status later.
        """
        frame_ids = opts["frame_ids"]
        edit_prompts = opts["edit_prompts"]
        
        if len(frame_ids) != len(edit_prompts):
            raise ValueError("frame_ids and edit_prompts must have the same length")
        
        body: Dict[str, Any] = {
            "job_id": video_id,
            "frame_ids": frame_ids,
            "edit_prompts": edit_prompts,
            "return_single_frame": True
        }
        
        if opts.get("reference_images"):
            body["reference_images"] = opts["reference_images"]
        if opts.get("video_url"):
            body["video_url"] = opts["video_url"]
        if opts.get("user_id"):
            body["user_id"] = opts["user_id"]

        response = requests.post(
            f"{self.base_url}/api/edit-and-reanimate-frames",
            headers={**self.headers, "Content-Type": "application/json"},
            json=body,
            timeout=60
        )
        response.raise_for_status()
        data = response.json()
        
        return data["job_id"]

    def _get_edit_status(
        self,
        job_id: str
    ) -> Dict[str, Any]:
        """Check the status of an edit job.
        
        Returns the video URL if completed, or status information if still processing.
        """
        response = requests.post(
            f"{self.base_url}/api/edit-status",
            headers={**self.headers, "Content-Type": "application/json"},
            json={"job_id": job_id}
        )
        response.raise_for_status()
        return response.json()

    def _poll_edit_status(
        self,
        job_id: str,
        interval_ms: int
    ) -> str:
        """Poll edit status until completion.
        
        Returns the video URL when completed.
        """
        max_attempts = 1200
        attempts = 0
        retry_count = 0
        max_retries = 3
        interval_seconds = interval_ms / 1000.0
        
        while True:
            if attempts >= max_attempts:
                raise TimeoutError("Edit job timed out")
            
            try:
                status = self._get_edit_status(job_id)
                
                if status.get("status") == "completed":
                    return status["url"]
                elif status.get("status") in ("failed", "not found"):
                    raise ValueError(f"Edit job failed: {status.get('status')}")
                else:
                    print(f"Edit job status: {status.get('status')}")
                
                # Reset retry count on successful request
                retry_count = 0
            except (requests.exceptions.ConnectionError, 
                    requests.exceptions.Timeout,
                    requests.exceptions.RequestException) as error:
                # Check if it's a server error that we should retry
                if hasattr(error, 'response') and error.response is not None:
                    status_code = error.response.status_code
                    if 500 <= status_code < 600:
                        if retry_count < max_retries:
                            retry_count += 1
                            wait_time = min(5.0 * retry_count, 15.0)
                            warnings.warn(
                                f"Retrying request ({retry_count}/{max_retries}) after server error..."
                            )
                            time.sleep(wait_time)
                            continue  # Don't increment attempts, just retry
                        else:
                            warnings.warn(f"Max retries ({max_retries}) exceeded for server errors")
                            retry_count = 0
                    else:
                        # Non-server error, log and continue polling
                        warnings.warn(
                            f"Error on attempt {attempts + 1}, continuing polling: {error}"
                        )
                else:
                    # Network error, retry
                    if retry_count < max_retries:
                        retry_count += 1
                        wait_time = min(5.0 * retry_count, 15.0)
                        warnings.warn(
                            f"Retrying request ({retry_count}/{max_retries}) after network error..."
                        )
                        time.sleep(wait_time)
                        continue
                    else:
                        warnings.warn(f"Max retries ({max_retries}) exceeded for network errors")
                        retry_count = 0
            except Exception as error:
                # Non-network error, log and continue polling
                warnings.warn(
                    f"Error on attempt {attempts + 1}, continuing polling: {error}"
                )
            
            time.sleep(interval_seconds)
            attempts += 1

    def _get_frame_versions(self, video_id: str) -> Dict[str, Any]:
        """Get frame versions and animations for a video.
        
        Returns both the current frame_animations and available frame_animation_versions.
        """
        response = requests.get(
            f"{self.base_url}/api/frame-versions/{video_id}",
            headers={**self.headers, "Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()

    def _get_frame_animations(self, video_id: str) -> Dict[str, str]:
        """Get frame animations for a video.
        
        Returns a dictionary mapping frame indices to animation URLs.
        This is a convenience method that extracts frame_animations from get_frame_versions.
        """
        versions = self._get_frame_versions(video_id)
        return versions.get("frame_animations", {})

    def _set_frame_version(
        self,
        video_id: str,
        frame_id: str,
        animation_url: str
    ) -> Dict[str, str]:
        """Set a specific frame animation version.
        
        Updates the frame_animations for a specific frame in the video.
        """
        response = requests.post(
            f"{self.base_url}/api/set-frame-version",
            headers={**self.headers, "Content-Type": "application/json"},
            json={
                "job_id": video_id,
                "frame_id": frame_id,
                "url": animation_url
            }
        )
        response.raise_for_status()
        return response.json()

    def _combine_edited_frames(
        self,
        video_id: str,
        opts: Dict[str, Any]
    ) -> Dict[str, str]:
        """Combines edited frames into a final video with audio.
        
        This is a helper method used by edit_video when auto_combine is enabled.
        """
        edit_result = ''
        frame_ids = opts["frame_ids"]
        video_url = opts.get("video_url")
        poll_interval_ms = opts["poll_interval_ms"]
        job_id = video_id  # Use video_id as job_id for return value
        
        try:
            # Get current frame animations
            frame_versions = self._get_frame_versions(video_id)
            frame_animations = frame_versions.get("frame_animations", {}).copy()

            # Set frame versions for edited frames
            for frame_id in frame_ids:
                self._set_frame_version(video_id, frame_id, frame_animations[frame_id])
                # Refresh to get updated frame_animations
                updated_versions = self._get_frame_versions(video_id)
                frame_animations = updated_versions.get("frame_animations", {})
            
            # Combine all frames
            mp4_urls = [
                url for _, url in sorted(
                    frame_animations.items(),
                    key=lambda x: int(x[0]) if x[0].isdigit() else 0
                )
            ]
            if len(mp4_urls) == 0:
                raise ValueError("No frame animations found to combine")
            
            combined_url = self.combine_videos(
                mp4_urls,
                video_url=video_url,
                poll_interval_ms=poll_interval_ms
            )
            
            return {
                "video_url": combined_url,
                "job_id": job_id
            }
        except Exception as error:
            warnings.warn(f"Failed to auto-combine videos, returning edit result: {error}")
            # Return the edit result even if combine fails
            return {
                "video_url": edit_result,
                "job_id": job_id
            }

    def update_video(
        self,
        video_id: str,
        *,
        prompt: Optional[str] = None,
        context: Optional[str] = None,
        scenes: Optional[int] = None,
        video_url: Optional[str] = None,
        frame_animations: Optional[Dict[str, Any]] = None,
        jwt_token: str
    ) -> Dict[str, Any]:
        """Update video metadata (prompt, context, scenes, video_url, frame_animations).
        
        Note: This requires JWT authentication.
        
        Args:
            video_id: The ID of the video to update
            prompt: Optional new prompt
            context: Optional new context
            scenes: Optional number of scenes
            video_url: Optional new video URL
            frame_animations: Optional frame animations dictionary
            jwt_token: JWT token for authentication (required)
            
        Returns:
            Dictionary with updated video data
        """
        if not jwt_token:
            raise ValueError("JWT token is required for updating video metadata")
        
        headers = {
            **self.headers,
            "Content-Type": "application/json",
            "Authorization": f"Bearer {jwt_token}"
        }
        
        body: Dict[str, Any] = {}
        if prompt is not None:
            body["prompt"] = prompt
        if context is not None:
            body["context"] = context
        if scenes is not None:
            body["scenes"] = scenes
        if video_url is not None:
            body["video_url"] = video_url
        if frame_animations is not None:
            body["frame_animations"] = frame_animations
        
        response = requests.put(
            f"{self.base_url}/api/videos/{video_id}",
            headers=headers,
            json=body
        )
        response.raise_for_status()
        return response.json()
