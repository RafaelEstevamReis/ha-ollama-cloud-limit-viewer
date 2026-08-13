from datetime import timedelta
from unittest.mock import patch

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ollama_cloud_usage.const import (
    CONF_COOKIE,
    CONF_SCAN_INTERVAL,
    DOMAIN,
)
from custom_components.ollama_cloud_usage.scraper import OllamaUsageData


async def _setup(hass: HomeAssistant, data: OllamaUsageData) -> MockConfigEntry:
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Main Account",
        data={CONF_COOKIE: "test_cookie_value", CONF_SCAN_INTERVAL: 60},
    )
    entry.add_to_hass(hass)

    with patch(
        "custom_components.ollama_cloud_usage.fetch_and_parse", return_value=data
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    return entry


def _state(hass: HomeAssistant, entry: MockConfigEntry, key: str):
    entity_id = er.async_get(hass).async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_{key}"
    )
    assert entity_id is not None
    return hass.states.get(entity_id)


async def test_pace_sensors(hass: HomeAssistant):
    """60% of the weekly allowance spent halfway through the week = 120% pace."""
    resets_at = dt_util.utcnow() + timedelta(days=3.5)
    entry = await _setup(
        hass,
        OllamaUsageData(
            session_percent=10.0,
            weekly_percent=60.0,
            weekly_resets_in="3 days",
            weekly_resets_at=resets_at,
        ),
    )

    pace = _state(hass, entry, "weekly_pace")
    assert float(pace.state) == pytest.approx(120.0, abs=0.5)
    assert pace.attributes["week_elapsed_percent"] == pytest.approx(50.0, abs=0.2)
    assert pace.attributes["usage_vs_elapsed_points"] == pytest.approx(10.0, abs=0.2)
    assert pace.attributes["estimated_exhaustion"] is not None

    assert float(_state(hass, entry, "weekly_elapsed").state) == pytest.approx(
        50.0, abs=0.2
    )
    # HA renders timestamp states with second precision.
    reported = dt_util.parse_datetime(_state(hass, entry, "weekly_resets_at").state)
    assert abs((reported - resets_at).total_seconds()) < 1


async def test_pace_unknown_without_reset_timestamp(hass: HomeAssistant):
    entry = await _setup(
        hass,
        OllamaUsageData(weekly_percent=60.0, weekly_resets_in="3 days"),
    )

    assert _state(hass, entry, "weekly_pace").state == "unknown"
    assert _state(hass, entry, "weekly_elapsed").state == "unknown"
    assert _state(hass, entry, "weekly_resets_at").state == "unknown"
