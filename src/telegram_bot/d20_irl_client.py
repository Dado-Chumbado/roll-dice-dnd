"""Client for the D20-IRL physical dice rolling API."""

import asyncio
import io
import logging

import httpx
from PIL import Image

logger = logging.getLogger(__name__)

POLL_INTERVAL = 1.0  # seconds between status polls
POLL_TIMEOUT = 60.0  # max seconds to wait for a result


class D20IRLError(Exception):
    pass


class D20IRLClient:
    def __init__(self, base_url: str, username: str = None, token: str = None):
        """
        Args:
            base_url: Base URL of the IRL API (e.g. http://pi-ip:5000).
            username: Username for authenticated endpoint /u/<username>/roll.
                      If omitted, falls back to the public /api/roll endpoint.
            token:    Bearer token for the authenticated endpoint.
        """
        self.base_url = base_url.rstrip("/")
        self.username = username
        self.token = token

    @property
    def _auth_headers(self) -> dict:
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @property
    def _roll_url(self) -> str:
        return f"{self.base_url}/u/{self.username}/roll"

    async def roll(self, mode: str = "normal") -> dict:
        """
        Trigger a physical dice roll and return the result.

        Uses the authenticated endpoint (/u/<username>/roll) when username +
        token are provided, otherwise falls back to the public /api/roll.

        Returns a dict with:
          - face: int         — the selected face value (1-20)
          - detections: list  — all detected dice [{face, confidence}]
          - image_url: str | None
          - gif_url: str | None
          - time_elapsed: float
          - mode: str
        """
        payload = {"mode": mode, "debug": True}

        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                self._roll_url,
                json=payload,
                headers=self._auth_headers,
            )
            if response.status_code == 401:
                raise D20IRLError("Authentication failed — check D20_IRL_TOKEN and D20_IRL_USERNAME")
            if response.status_code == 403:
                body = response.json()
                err = body.get("error", "forbidden")
                if err == "daily_limit_reached":
                    raise D20IRLError("Daily roll limit reached for this account")
                raise D20IRLError("Account is disabled")
            response.raise_for_status()
            data = response.json()

        # Both /api/roll and /u/<username>/roll always return roll_id immediately
        roll_id = data.get("roll_id")
        if not roll_id:
            raise D20IRLError(f"Unexpected API response: {data}")

        return await self._poll_status(roll_id)

    async def _poll_status(self, roll_id: str) -> dict:
        deadline = asyncio.get_event_loop().time() + POLL_TIMEOUT
        async with httpx.AsyncClient(timeout=10.0) as client:
            while asyncio.get_event_loop().time() < deadline:
                await asyncio.sleep(POLL_INTERVAL)
                response = await client.get(
                    f"{self.base_url}/api/roll/{roll_id}/status",
                    headers=self._auth_headers,
                )
                response.raise_for_status()
                data = response.json()

                status = data.get("status", "")

                if status == "unknown":
                    raise D20IRLError("Roll result expired from server cache (roll_id unknown)")

                if status == "done":
                    http_status = data.get("http_status", 200)
                    result = data.get("result", {})

                    if http_status == 422:
                        error = result.get("error", "detection_failed")
                        if error == "could_not_detect_two_dice":
                            raise D20IRLError(
                                "Could not detect two dice for advantage/disadvantage roll. "
                                "Try again."
                            )
                        raise D20IRLError(f"Roll failed: {error}")

                    return self._build_result(result)

                # status is "queued" or "rolling" — keep polling

        raise D20IRLError("Timed out waiting for roll result")

    def _build_result(self, result: dict) -> dict:
        """Parse the result object from the status 'done' response."""
        selected = result.get("selected") or {}
        face = selected.get("face")

        # Build a readable detections list [{face, confidence}]
        raw_detections = result.get("detections") or []
        detections = [
            {"face": d["face"], "confidence": round(d.get("confidence", 0), 2)}
            for d in raw_detections
            if isinstance(d, dict)
        ]

        image_path = result.get("image", "")
        gif_path = result.get("gif", "")

        return {
            "face": face,
            "detections": detections,
            "image_url": f"{self.base_url}/{image_path}" if image_path else None,
            "gif_url": f"{self.base_url}/{gif_path}" if gif_path else None,
            "time_elapsed": result.get("time_elapsed", 0.0),
            "mode": result.get("mode", "normal"),
        }

    async def fetch_bytes(self, url: str) -> bytes:
        """Download media from the IRL server."""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url, headers=self._auth_headers)
            response.raise_for_status()
            return response.content


def add_gif_loop_pause(gif_bytes: bytes, pause_ms: int = 3000, min_frame_ms: int = 50) -> bytes:
    """
    Return a new GIF preserving original frame timings (with a minimum per frame),
    and a long pause on the last frame before looping again.
    """
    img = Image.open(io.BytesIO(gif_bytes))

    frames = []
    durations = []
    try:
        while True:
            frames.append(img.copy().convert("RGBA"))
            # img.info["duration"] is only reliable when read at the current seek position
            raw_duration = img.info.get("duration", 0)
            durations.append(max(raw_duration, min_frame_ms))
            img.seek(img.tell() + 1)
    except EOFError:
        pass

    logger.debug(f"GIF: {len(frames)} frames, durations={durations}")

    durations[-1] = pause_ms

    output = io.BytesIO()
    frames[0].save(
        output,
        format="GIF",
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
    )
    output.seek(0)
    return output.getvalue()
