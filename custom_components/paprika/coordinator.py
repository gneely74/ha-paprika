"""DataUpdateCoordinator for the Paprika integration."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import CONF_EMAIL, CONF_PASSWORD, DEFAULT_SCAN_INTERVAL, DOMAIN
from .paprika_api import PaprikaApi, PaprikaApiError

_LOGGER = logging.getLogger(__name__)


class PaprikaCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator that polls Paprika for recipes and meal plan data."""

    config_entry: ConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialise the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=DEFAULT_SCAN_INTERVAL),
        )
        session = async_get_clientsession(hass)
        self.api = PaprikaApi(
            email=entry.data[CONF_EMAIL],
            password=entry.data[CONF_PASSWORD],
            session=session,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from the Paprika API."""
        try:
            recipes = await self.api.get_recipes()
            meals = await self.api.get_meals()
            categories = await self.api.get_categories()
        except PaprikaApiError as err:
            raise UpdateFailed(f"Paprika API error: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err

        return {
            "recipes": recipes,
            "meals": meals,
            "categories": categories,
        }
