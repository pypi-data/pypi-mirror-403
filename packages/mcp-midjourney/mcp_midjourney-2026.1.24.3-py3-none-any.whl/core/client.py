"""HTTP client for Midjourney API."""

import json
from typing import Any

import httpx
from loguru import logger

from core.config import settings
from core.exceptions import MidjourneyAPIError, MidjourneyAuthError, MidjourneyTimeoutError


class MidjourneyClient:
    """Async HTTP client for AceDataCloud Midjourney API."""

    def __init__(self, api_token: str | None = None, base_url: str | None = None):
        """Initialize the Midjourney API client.

        Args:
            api_token: API token for authentication. If not provided, uses settings.
            base_url: Base URL for the API. If not provided, uses settings.
        """
        self.api_token = api_token if api_token is not None else settings.api_token
        self.base_url = base_url or settings.api_base_url
        self.timeout = settings.request_timeout

        logger.info(f"MidjourneyClient initialized with base_url: {self.base_url}")
        logger.debug(f"API token configured: {'Yes' if self.api_token else 'No'}")
        logger.debug(f"Request timeout: {self.timeout}s")

    def _get_headers(self) -> dict[str, str]:
        """Get request headers with authentication."""
        if not self.api_token:
            logger.error("API token not configured!")
            raise MidjourneyAuthError("API token not configured")

        return {
            "accept": "application/json",
            "authorization": f"Bearer {self.api_token}",
            "content-type": "application/json",
        }

    async def request(
        self,
        endpoint: str,
        payload: dict[str, Any],
        timeout: float | None = None,
    ) -> dict[str, Any]:
        """Make a POST request to the Midjourney API.

        Args:
            endpoint: API endpoint path (e.g., "/midjourney/imagine")
            payload: Request body as dictionary
            timeout: Optional timeout override

        Returns:
            API response as dictionary

        Raises:
            MidjourneyAuthError: If authentication fails
            MidjourneyAPIError: If the API request fails
            MidjourneyTimeoutError: If the request times out
        """
        url = f"{self.base_url}{endpoint}"
        request_timeout = timeout or self.timeout

        logger.info(f"🚀 POST {url}")
        logger.debug(f"Request payload: {json.dumps(payload, ensure_ascii=False, indent=2)}")
        logger.debug(f"Timeout: {request_timeout}s")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers=self._get_headers(),
                    timeout=request_timeout,
                )

                logger.info(f"📥 Response status: {response.status_code}")

                if response.status_code == 401:
                    logger.error("❌ Authentication failed: Invalid API token")
                    raise MidjourneyAuthError("Invalid API token")

                if response.status_code == 403:
                    logger.error("❌ Access denied: Check API permissions")
                    raise MidjourneyAuthError("Access denied. Check your API permissions.")

                response.raise_for_status()

                result = response.json()
                logger.success(f"✅ Request successful! Task ID: {result.get('task_id', 'N/A')}")

                # Log summary of response
                if result.get("success"):
                    if "image_url" in result:
                        logger.info(
                            f"📊 Image generated: {result.get('image_width', 'N/A')}x{result.get('image_height', 'N/A')}"
                        )
                    elif "video_urls" in result:
                        logger.info(
                            f"📊 Videos generated: {len(result.get('video_urls', []))} video(s)"
                        )
                    elif "descriptions" in result:
                        logger.info(
                            f"📊 Descriptions: {len(result.get('descriptions', []))} description(s)"
                        )
                else:
                    logger.warning(f"⚠️ API returned success=false: {result.get('error', {})}")

                return result  # type: ignore[no-any-return]

            except httpx.TimeoutException as e:
                logger.error(f"⏰ Request timeout after {request_timeout}s: {e}")
                raise MidjourneyTimeoutError(
                    f"Request to {endpoint} timed out after {request_timeout}s"
                ) from e

            except MidjourneyAuthError:
                raise

            except httpx.HTTPStatusError as e:
                logger.error(f"❌ HTTP error {e.response.status_code}: {e.response.text}")
                raise MidjourneyAPIError(
                    message=e.response.text,
                    code=f"http_{e.response.status_code}",
                    status_code=e.response.status_code,
                ) from e

            except Exception as e:
                logger.error(f"❌ Request error: {e}")
                raise MidjourneyAPIError(message=str(e)) from e

    # Convenience methods for specific endpoints
    async def imagine(self, **kwargs: Any) -> dict[str, Any]:
        """Generate image using the imagine endpoint."""
        logger.info(f"🎨 Generating image with action: {kwargs.get('action', 'generate')}")
        return await self.request("/midjourney/imagine", kwargs)

    async def describe(self, **kwargs: Any) -> dict[str, Any]:
        """Describe image using the describe endpoint."""
        logger.info(f"🔍 Describing image: {kwargs.get('image_url', '')[:50]}...")
        return await self.request("/midjourney/describe", kwargs)

    async def edit(self, **kwargs: Any) -> dict[str, Any]:
        """Edit image using the edits endpoint."""
        logger.info(f"✏️ Editing image with prompt: {kwargs.get('prompt', '')[:50]}...")
        return await self.request("/midjourney/edits", kwargs)

    async def generate_video(self, **kwargs: Any) -> dict[str, Any]:
        """Generate video using the videos endpoint."""
        logger.info(f"🎬 Generating video with action: {kwargs.get('action', 'generate')}")
        return await self.request("/midjourney/videos", kwargs)

    async def translate(self, **kwargs: Any) -> dict[str, Any]:
        """Translate content using the translate endpoint."""
        logger.info(f"🌐 Translating content: {kwargs.get('content', '')[:50]}...")
        return await self.request("/midjourney/translate", kwargs)

    async def query_task(self, **kwargs: Any) -> dict[str, Any]:
        """Query task status using the tasks endpoint."""
        task_id = kwargs.get("id") or kwargs.get("ids", [])
        logger.info(f"🔍 Querying task(s): {task_id}")
        return await self.request("/midjourney/tasks", kwargs)


# Global client instance
client = MidjourneyClient()
