from datetime import timedelta

DOMAIN = "ollama_cloud_usage"

CONF_COOKIE = "cookie"
CONF_ACCOUNT_NAME = "account_name"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 120

SETTINGS_URL = "https://ollama.com/settings"
USER_AGENT = (
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)

# Ollama resets the cloud allowance on a fixed 7-day cycle.
WEEKLY_PERIOD = timedelta(days=7)

# Below this share of the week, extrapolating a rate is noise (a single request
# right after the reset would project a 1000% week).
MIN_ELAPSED_PERCENT = 1.0
