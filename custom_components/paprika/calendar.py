"""Calendar platform for the Paprika meal plan."""

from __future__ import annotations

import logging
from datetime import date, datetime, time, timedelta
from typing import Any

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN, MEAL_TYPES
from .coordinator import PaprikaCoordinator

_LOGGER = logging.getLogger(__name__)

# Default start/end times for each meal type so events show at sensible slots.
MEAL_TIMES: dict[int, tuple[time, time]] = {
    0: (time(7, 0), time(9, 0)),  # Breakfast
    1: (time(11, 30), time(13, 0)),  # Lunch
    2: (time(17, 30), time(19, 0)),  # Dinner
    3: (time(14, 0), time(15, 0)),  # Snack
}
DEFAULT_MEAL_TIMES = (time(12, 0), time(13, 0))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Paprika meal plan calendar."""
    coordinator: PaprikaCoordinator = hass.data[DOMAIN][entry.entry_id]
    _LOGGER.debug(
        "Setting up Paprika calendar, coordinator has %d meals",
        len((coordinator.data or {}).get("meals", [])),
    )
    async_add_entities([PaprikaMealPlanCalendar(coordinator, entry)])


class PaprikaMealPlanCalendar(
    CoordinatorEntity[PaprikaCoordinator], CalendarEntity
):
    """A calendar entity backed by the Paprika meal plan."""

    _attr_has_entity_name = True
    _attr_name = "Meal Plan"

    def __init__(
        self, coordinator: PaprikaCoordinator, entry: ConfigEntry
    ) -> None:
        """Initialise the calendar entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_meal_plan"

    @property
    def device_info(self) -> DeviceInfo:
        """Group all Paprika entities under one device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Paprika",
            manufacturer="Hindsight Labs",
            entry_type=DeviceEntryType.SERVICE,
        )

    # ── CalendarEntity interface ─────────────────────────────────────

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming event (used for the entity state)."""
        try:
            now = dt_util.now()
            # Check today and the next 7 days for an upcoming event.
            for day_offset in range(8):
                target = now.date() + timedelta(days=day_offset)
                for ev in self._events_for_date(target):
                    if ev.end and ev.end < now:
                        continue
                    return ev
            return None
        except Exception:
            _LOGGER.exception("Error computing next Paprika calendar event")
            return None

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime,
        end_date: datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within the requested window."""
        events: list[CalendarEvent] = []
        for meal in self._meals():
            try:
                meal_date = self._parse_meal_date(meal)
                if meal_date is None:
                    continue
                if meal_date < start_date.date() or meal_date > end_date.date():
                    continue
                events.append(self._meal_to_event(meal, meal_date))
            except Exception:
                _LOGGER.debug("Skipping unparseable meal entry: %s", meal)
        return sorted(events, key=lambda e: e.start)

    # ── Helpers ──────────────────────────────────────────────────────

    def _meals(self) -> list[dict[str, Any]]:
        if not self.coordinator.data:
            return []
        return self.coordinator.data.get("meals", [])

    @staticmethod
    def _parse_meal_date(meal: dict[str, Any]) -> date | None:
        raw = (meal.get("date") or "")[:10]
        if not raw:
            return None
        try:
            return date.fromisoformat(raw)
        except ValueError:
            return None

    @staticmethod
    def _meal_to_event(meal: dict[str, Any], meal_date: date) -> CalendarEvent:
        meal_type = meal.get("type", -1)
        meal_name = meal.get("name") or "(unnamed)"
        type_label = MEAL_TYPES.get(meal_type, "Meal")
        start_t, end_t = MEAL_TIMES.get(meal_type, DEFAULT_MEAL_TIMES)
        tz = dt_util.DEFAULT_TIME_ZONE
        return CalendarEvent(
            summary=f"{type_label}: {meal_name}",
            start=datetime.combine(meal_date, start_t, tzinfo=tz),
            end=datetime.combine(meal_date, end_t, tzinfo=tz),
        )

    def _events_for_date(self, target: date) -> list[CalendarEvent]:
        events = []
        for meal in self._meals():
            meal_date = self._parse_meal_date(meal)
            if meal_date == target:
                events.append(self._meal_to_event(meal, meal_date))
        return sorted(events, key=lambda e: e.start)
