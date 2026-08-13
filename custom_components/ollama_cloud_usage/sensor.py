from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .scraper import OllamaUsageData


@dataclass(frozen=True, kw_only=True)
class OllamaSensorDescription(SensorEntityDescription):
    value_fn: Callable[[OllamaUsageData], str | float | datetime | None]
    attrs_fn: Callable[[OllamaUsageData], dict[str, Any]] | None = None


def _round(value: float | None) -> float | None:
    return round(value, 1) if value is not None else None


def _pace_attributes(data: OllamaUsageData) -> dict[str, Any]:
    now = dt_util.utcnow()
    exhausted_at = data.week_exhausted_at(now)
    return {
        "week_elapsed_percent": _round(data.week_elapsed_percent(now)),
        "week_usage_percent": data.weekly_percent,
        "projected_week_usage": data.week_projected_usage(now),
        "estimated_exhaustion": exhausted_at.isoformat() if exhausted_at else None,
    }


SENSOR_DESCRIPTIONS: tuple[OllamaSensorDescription, ...] = (
    OllamaSensorDescription(
        key="session_usage",
        translation_key="session_usage",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge",
        value_fn=lambda d: d.session_percent,
    ),
    OllamaSensorDescription(
        key="session_remaining",
        translation_key="session_remaining",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:gauge-empty",
        value_fn=lambda d: (
            round(100.0 - d.session_percent, 1)
            if d.session_percent is not None
            else None
        ),
    ),
    OllamaSensorDescription(
        key="session_resets_in",
        translation_key="session_resets_in",
        icon="mdi:timer-sand",
        value_fn=lambda d: d.session_resets_in,
    ),
    OllamaSensorDescription(
        key="weekly_usage",
        translation_key="weekly_usage",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-bar",
        value_fn=lambda d: d.weekly_percent,
    ),
    OllamaSensorDescription(
        key="weekly_remaining",
        translation_key="weekly_remaining",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:chart-bar-stacked",
        value_fn=lambda d: (
            round(100.0 - d.weekly_percent, 1) if d.weekly_percent is not None else None
        ),
    ),
    OllamaSensorDescription(
        key="weekly_resets_in",
        translation_key="weekly_resets_in",
        icon="mdi:calendar-clock",
        value_fn=lambda d: d.weekly_resets_in,
    ),
    OllamaSensorDescription(
        key="weekly_resets_at",
        translation_key="weekly_resets_at",
        device_class=SensorDeviceClass.TIMESTAMP,
        value_fn=lambda d: d.weekly_resets_at,
    ),
    OllamaSensorDescription(
        key="weekly_elapsed",
        translation_key="weekly_elapsed",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-range",
        value_fn=lambda d: _round(d.week_elapsed_percent(dt_util.utcnow())),
    ),
    OllamaSensorDescription(
        key="weekly_pace",
        translation_key="weekly_pace",
        native_unit_of_measurement="%",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        value_fn=lambda d: d.week_usage_pace(dt_util.utcnow()),
        attrs_fn=_pace_attributes,
    ),
    OllamaSensorDescription(
        key="model_info",
        translation_key="model_info",
        icon="mdi:robot",
        value_fn=lambda d: d.model_note,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: DataUpdateCoordinator[OllamaUsageData] = entry.runtime_data

    async_add_entities(
        OllamaUsageSensor(coordinator, entry, description)
        for description in SENSOR_DESCRIPTIONS
    )


class OllamaUsageSensor(
    CoordinatorEntity[DataUpdateCoordinator[OllamaUsageData]], SensorEntity
):
    entity_description: OllamaSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: DataUpdateCoordinator[OllamaUsageData],
        entry: ConfigEntry,
        description: OllamaSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": f"Ollama {entry.title}",
            "manufacturer": "Ollama",
            "model": "Cloud Usage",
            "entry_type": "service",
        }

    @property
    def native_value(self) -> str | float | datetime | None:
        if self.coordinator.data is None:
            return None
        return self.entity_description.value_fn(self.coordinator.data)

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if self.coordinator.data is None or self.entity_description.attrs_fn is None:
            return None
        return self.entity_description.attrs_fn(self.coordinator.data)
