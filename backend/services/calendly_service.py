import httpx
from config import settings


class CalendlyService:
    BASE_URL = "https://api.calendly.com"

    def __init__(self):
        self.api_key = settings.calendly_api_key
        self.user_uri = settings.calendly_user_uri

    async def get_scheduling_link(self, event_type: str = "consulta") -> str:
        """Return a scheduling link for the given event type."""
        if not self.api_key or not self.user_uri:
            return self._fallback_message(event_type)

        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.BASE_URL}/event_types",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    params={"user": self.user_uri, "active": True},
                    timeout=10,
                )
                response.raise_for_status()
                data = response.json()

                event_types = data.get("collection", [])
                if not event_types:
                    return self._fallback_message(event_type)

                # Try to find a matching event type
                keyword = event_type.lower()
                for et in event_types:
                    name = et.get("name", "").lower()
                    if keyword in name or any(k in name for k in ["demo", "consulta", "llamada", "reunión"]):
                        return et.get("scheduling_url", self._fallback_message(event_type))

                # Return first available event type
                return event_types[0].get("scheduling_url", self._fallback_message(event_type))

        except Exception:
            return self._fallback_message(event_type)

    def _fallback_message(self, event_type: str) -> str:
        return f"Para agendar tu {event_type}, contactanos directamente y coordinamos el horario que mejor te quede."
