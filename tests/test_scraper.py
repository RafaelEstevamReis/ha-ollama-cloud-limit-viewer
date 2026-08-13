from datetime import UTC, datetime, timedelta

import pytest

from custom_components.ollama_cloud_usage.scraper import OllamaUsageData, parse_usage

SAMPLE_HTML = """
<div class="cloud-usage">
  <div class="block">
    <div><span>Session usage</span><span>6.7% used</span></div>
    <div data-usage-meter="session"></div>
    <div class="local-time" data-time="2026-01-30T18:00:00Z">Resets in 3 hours</div>
  </div>
  <div class="block">
    <div><span>Weekly usage</span><span>17.3% used</span></div>
    <div data-usage-meter="weekly">
      <div data-usage-segment="1" data-model="gemma3:27b" data-requests="369"></div>
    </div>
    <div class="local-time" data-time="2026-02-02T00:00:00Z">Resets in 2 days</div>
  </div>
</div>
"""

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)


def test_parses_reset_timestamps():
    data = parse_usage(SAMPLE_HTML)

    assert data.session_percent == 6.7
    assert data.session_resets_in == "3 hours"
    assert data.session_resets_at == datetime(2026, 1, 30, 18, 0, tzinfo=UTC)
    assert data.weekly_percent == 17.3
    assert data.weekly_resets_in == "2 days"
    assert data.weekly_resets_at == datetime(2026, 2, 2, 0, 0, tzinfo=UTC)
    assert data.model_note == "gemma3:27b, 369 requests"


def test_missing_data_time_keeps_relative_text():
    data = parse_usage(SAMPLE_HTML.replace(' data-time="2026-02-02T00:00:00Z"', ""))

    assert data.weekly_resets_in == "2 days"
    assert data.weekly_resets_at is None
    assert data.week_usage_pace(NOW) is None
    assert data.week_elapsed_percent(NOW) is None


@pytest.mark.parametrize(
    ("used", "expected_pace", "expected_projection"),
    [
        (50.0, 0.0, 100.0),  # dead on budget
        (60.0, 10.0, 120.0),  # 10 points ahead of budget
        (40.0, -10.0, 80.0),  # 10 points behind
        (0.0, -50.0, 0.0),  # nothing spent yet
    ],
)
def test_pace_against_a_half_spent_week(used, expected_pace, expected_projection):
    data = OllamaUsageData(
        weekly_percent=used, weekly_resets_at=NOW + timedelta(days=3.5)
    )

    assert data.week_elapsed_percent(NOW) == 50.0
    assert data.week_usage_pace(NOW) == expected_pace
    assert data.week_projected_usage(NOW) == expected_projection


def test_elapsed_is_clamped_to_the_window():
    fresh = OllamaUsageData(weekly_percent=1.0, weekly_resets_at=NOW + timedelta(days=8))
    stale = OllamaUsageData(weekly_percent=1.0, weekly_resets_at=NOW - timedelta(days=1))

    assert fresh.week_elapsed_percent(NOW) == 0.0
    assert stale.week_elapsed_percent(NOW) == 100.0


def test_pace_is_defined_right_after_a_reset_but_the_projection_is_not():
    data = OllamaUsageData(
        weekly_percent=0.5, weekly_resets_at=NOW + timedelta(days=7, minutes=-30)
    )

    assert data.week_elapsed_percent(NOW) == pytest.approx(0.298, abs=0.01)
    # A raw delta stays meaningful with barely any week gone by...
    assert data.week_usage_pace(NOW) == pytest.approx(0.2, abs=0.01)
    # ...but extrapolating from 18 minutes of data is not.
    assert data.week_projected_usage(NOW) is None
    assert data.week_exhausted_at(NOW) is None


def test_exhaustion_estimate():
    reset_at = NOW + timedelta(days=3.5)

    on_pace = OllamaUsageData(weekly_percent=50.0, weekly_resets_at=reset_at)
    burning = OllamaUsageData(weekly_percent=75.0, weekly_resets_at=reset_at)
    spent = OllamaUsageData(weekly_percent=100.0, weekly_resets_at=reset_at)

    # Exactly on budget: the allowance lasts until the reset, so nothing to warn about.
    assert on_pace.week_exhausted_at(NOW) is None
    # 75% burned in half a week: the remaining 25% buys another 3.5d * (25/75).
    assert burning.week_exhausted_at(NOW) == NOW + timedelta(days=3.5) / 3
    assert spent.week_exhausted_at(NOW) == NOW
