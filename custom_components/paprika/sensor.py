"""Sensor platform for the Paprika integration."""

from __future__ import annotations

from datetime import date
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MEAL_TYPES
from .coordinator import PaprikaCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Paprika sensors."""
    coordinator: PaprikaCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            PaprikaRecipeCountSensor(coordinator, entry),
            PaprikaTodaysMealsSensor(coordinator, entry),
        ]
    )


class PaprikaBaseSensor(
    CoordinatorEntity[PaprikaCoordinator], SensorEntity
):
    """Base class for Paprika sensors — provides shared device info."""

    _attr_has_entity_name = True

    def __init__(
        self, coordinator: PaprikaCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Paprika",
            manufacturer="Hindsight Labs",
            entry_type=DeviceEntryType.SERVICE,
        )


class PaprikaRecipeCountSensor(PaprikaBaseSensor):
    """Sensor that reports the total number of Paprika recipes."""

    _attr_name = "Recipe Count"
    _attr_icon = "mdi:book-open-variant"

    def __init__(
        self, coordinator: PaprikaCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_recipe_count"

    @property
    def native_value(self) -> int:
        if not self.coordinator.data:
            return 0
        return len(self.coordinator.data.get("recipes", []))


class PaprikaTodaysMealsSensor(PaprikaBaseSensor):
    """Sensor that shows today's meal plan as a comma-separated list."""

    _attr_name = "Today's Meals"
    _attr_icon = "mdi:silverware-fork-knife"

    def __init__(
        self, coordinator: PaprikaCoordinator, entry: ConfigEntry
    ) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_todays_meals"

    def _todays_meals(self) -> list[dict[str, Any]]:
        """Filter meal plan down to today's entries."""
        if not self.coordinator.data:
            return []
        today_str = date.today().isoformat()
        return [
            m
            for m in self.coordinator.data.get("meals", [])
            if (m.get("date") or "")[:10] == today_str
        ]

    @property
    def native_value(self) -> str | None:
        meals = self._todays_meals()
        if not meals:
            return None
        return ", ".join(m.get("name") or "(unnamed)" for m in meals)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Expose per-type meal lists as attributes (breakfast, lunch, …)."""
        meals_by_type: dict[str, list[str]] = {}
        for meal in self._todays_meals():
            meal_type = meal.get("type", -1)
            type_name = MEAL_TYPES.get(meal_type, "other")
            name = meal.get("name") or "(unnamed)"
            meals_by_type.setdefault(type_name.lower(), []).append(name)

        return {k: ", ".join(v) for k, v in meals_by_type.items()}
