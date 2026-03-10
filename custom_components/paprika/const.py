"""Constants for the Paprika Recipe Manager integration."""

DOMAIN = "paprika"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"
CONF_SCAN_INTERVAL = "scan_interval"

DEFAULT_SCAN_INTERVAL = 30  # minutes
MIN_SCAN_INTERVAL = 5
MAX_SCAN_INTERVAL = 1440

MEAL_TYPES: dict[int, str] = {
    0: "Breakfast",
    1: "Lunch",
    2: "Dinner",
    3: "Snack",
}
