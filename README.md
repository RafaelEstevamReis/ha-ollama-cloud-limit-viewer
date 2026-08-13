# Ollama Cloud Usage

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)

A Home Assistant custom integration that shows your [ollama.com](https://ollama.com) cloud usage as sensors — **session and weekly limits**, how much is remaining, and when they reset.

Ollama doesn't expose an API for this data, so the integration signs in with your browser cookie, fetches the server-rendered settings page, and parses the usage meters out of the HTML.

## Sensors

Each configured account creates the following sensors:

| Sensor | Example Value | Unit | Description |
|---|---|---|---|
| Session Usage | `45.8` | `%` | Current session usage percentage |
| Session Remaining | `54.2` | `%` | How much session allowance is left |
| Session Resets In | `4 hours` | — | Time until session usage resets |
| Weekly Usage | `80.9` | `%` | Current weekly usage percentage |
| Weekly Remaining | `19.1` | `%` | How much weekly allowance is left |
| Weekly Resets In | `3 days` | — | Time until weekly usage resets |
| Weekly Resets At | `2026-02-02T00:00:00+00:00` | — | Exact reset instant (live countdown in the UI) |
| Weekly Elapsed | `50.0` | `%` | How much of the 7-day window has gone by |
| Weekly Usage Pace | `+10.0` | `%` | How far ahead of / behind budget you are — see below |
| Model Info | `gemma3:27b, 369 requests` | — | Models used and request counts |

### Week usage pace

`Weekly Usage Pace` compares how much of the weekly allowance you spent with how much of the week went by:

```
pace = weekly_usage_% - weekly_elapsed_%
```

- `0` — exactly on budget (50% used halfway through the week).
- `+10` — 10 points ahead of budget: you spent 60% with only 50% of the week gone.
- `-10` — 10 points behind: 40% used at the halfway mark, so you are on track to finish with allowance left.

The elapsed share comes from the exact reset timestamp ollama.com renders on the settings page (`data-time`), not
from the rounded "resets in 3 days" text, so it stays accurate to the second.

The pace sensor carries extra attributes:

| Attribute | Meaning |
|---|---|
| `week_elapsed_percent` | Share of the week already gone |
| `week_usage_percent` | Weekly usage, so the two sides of the subtraction sit together |
| `projected_week_usage` | Usage the week would end at if the current rate held (`120` = you run out early) |
| `estimated_exhaustion` | When the allowance runs out at the current pace, or `null` if it lasts to the reset |

Pace itself is available as soon as the reset timestamp is known. The two extrapolations
(`projected_week_usage`, `estimated_exhaustion`) stay `null` for the first ~1.7 hours of a window (1% of the week),
where a single request would project a wild end-of-week figure.

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/vithurshanselvarajah/ha-ollama-cloud-limit-viewer` as an **Integration**
4. Search for "Ollama Cloud Usage" and install
5. Restart Home Assistant

### Manual

1. Copy the `custom_components/ollama_cloud_usage` folder into your Home Assistant `custom_components` directory
2. Restart Home Assistant

## Setup

1. Go to **Settings → Devices & Services → Add Integration**
2. Search for **Ollama Cloud Usage**
3. Enter:
   - **Account Name**: A friendly label (e.g. "Main", "Work")
   - **Cookie String**: Your ollama.com browser cookie (see below)
   - **Update Interval**: How often to check (default: 300 seconds / 5 minutes)

### Getting your cookie

1. Log in to [ollama.com](https://ollama.com) in your browser
2. Open **DevTools** (F12) → **Network** tab
3. Reload the page
4. Click the first document request (`settings` or `ollama.com`)
5. Under **Request Headers**, find the `Cookie:` line
6. Copy the **entire value** and paste it into the setup form

> **Tip**: Cookies usually last weeks to months. When one expires, the sensors will become unavailable. Use the integration's **Reconfigure** option to paste a fresh cookie — no need to delete and re-add the account.

## Cookie Expired?

When a cookie expires, the sensors will show as **unavailable** in Home Assistant.

To fix:
1. Go to **Settings → Devices & Services**
2. Find your Ollama Cloud Usage entry
3. Click the three dots menu → **Reconfigure**
4. Paste your fresh cookie string

## Multi-Account

You can add multiple ollama.com accounts. Each creates its own device with its own set of sensors. Just run the "Add Integration" flow again with a different account name and cookie.

## License

GPL-v3.0
