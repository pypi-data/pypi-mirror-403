"""HTTP reporter for sending posture data to the API."""

import httpx

from posture_agent.core.config import Settings
from posture_agent.models.report import PostureReportPayload


async def send_report(payload: PostureReportPayload, settings: Settings) -> dict:
    """Send posture report to the API with retry."""
    url = f"{settings.api.url}/api/v1/core/posture/reports"

    last_error: Exception | None = None
    for attempt in range(settings.api.retries):
        try:
            async with httpx.AsyncClient(timeout=settings.api.timeout) as client:
                response = await client.post(
                    url,
                    json=payload.model_dump(mode="json"),
                )
                response.raise_for_status()
                return response.json()
        except (httpx.HTTPError, httpx.TimeoutException) as e:
            last_error = e
            if attempt < settings.api.retries - 1:
                import asyncio
                await asyncio.sleep(2 ** attempt)

    raise RuntimeError(f"Failed to send report after {settings.api.retries} attempts: {last_error}")
