# Paprika Recipe Manager for Home Assistant

A custom Home Assistant integration that syncs your [Paprika Recipe Manager](https://www.paprikaapp.com/) data into HA.

## Features

- **Meal Plan Calendar** — your Paprika meal plan appears as a native HA calendar entity with time-slot events (Breakfast, Lunch, Dinner, Snack).
- **Recipe Count Sensor** — total number of recipes in your Paprika account.
- **Today's Meals Sensor** — today's planned meals as a comma-separated list, with per-type attributes (`breakfast`, `lunch`, `dinner`, `snack`) for use in templates and automations.
- **Automatic Polling** — data refreshes every 30 minutes.

## Installation

### HACS (recommended)

1. Open HACS → **Integrations** → three-dot menu → **Custom repositories**.
2. Add this repo URL and select category **Integration**.
3. Install **Paprika Recipe Manager** and restart Home Assistant.

### Manual

1. Copy the `custom_components/paprika/` folder into your HA `config/custom_components/` directory.
2. Restart Home Assistant.

## Setup

1. Go to **Settings → Devices & Services → Add Integration**.
2. Search for **Paprika Recipe Manager**.
3. Enter your Paprika email and password.

## Entities Created

| Entity | Type | Description |
|--------|------|-------------|
| `calendar.paprika_meal_plan` | Calendar | Meal plan events with time slots |
| `sensor.paprika_recipe_count` | Sensor | Total recipe count |
| `sensor.paprika_todays_meals` | Sensor | Today's meals (comma-separated) |

### Today's Meals Attributes

The `sensor.paprika_todays_meals` sensor exposes per-type attributes:

```yaml
breakfast: "Eggs Benedict"
lunch: "Caesar Salad"
dinner: "Chicken Parmesan"
snack: "Trail Mix"
```

These are useful in templates, e.g. `{{ state_attr('sensor.paprika_todays_meals', 'dinner') }}`.

## Automation Examples

### Announce tonight's dinner at 4 PM

```yaml
automation:
  - alias: "Announce dinner"
    trigger:
      - platform: time
        at: "16:00:00"
    condition:
      - condition: template
        value_template: >
          {{ state_attr('sensor.paprika_todays_meals', 'dinner') is not none }}
    action:
      - service: tts.speak
        target:
          entity_id: tts.piper
        data:
          media_player_entity_id: media_player.living_room_satellite1
          message: >
            Tonight's dinner is {{ state_attr('sensor.paprika_todays_meals', 'dinner') }}.
```
