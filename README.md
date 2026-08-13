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
| Weekly Usage Pace | `120.0` | `%` | Usage relative to the elapsed week — see below |
| Model Info | `gemma3:27b, 369 requests` | — | Models used and request counts |

### Week usage pace

`Weekly Usage Pace` divides weekly usage by how far into the 7-day window you are:

```
pace = weekly_usage_% / weekly_elapsed_% * 100
```

- `100` — spending exactly on budget.
- `120` — burning the allowance 1.2x too fast; at this rate the week would end at 120% (i.e. you run out early).
- `< 100` — you will finish the week with allowance to spare.

It reads as both a pace index and the projected end-of-week usage. The elapsed share comes from the exact reset
timestamp ollama.com renders on the settings page (`data-time`), not from the rounded "resets in 3 days" text, so it
stays accurate to the second.

The pace sensor carries extra attributes:

| Attribute | Meaning |
|---|---|
| `week_elapsed_percent` | Share of the week already gone |
| `usage_vs_elapsed_points` | Usage minus elapsed, in percentage points (`+10` = 10 points ahead of budget) |
| `estimated_exhaustion` | When the allowance runs out at the current pace, or `null` if it lasts to the reset |

Pace stays `unknown` for the first ~1.7 hours of a window (1% of the week), where a single request would read as a
wild over-budget ratio, and whenever the reset timestamp cannot be parsed.

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
