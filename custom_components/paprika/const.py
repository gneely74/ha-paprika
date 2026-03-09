"""Constants for the Paprika Recipe Manager integration."""

DOMAIN = "paprika"

CONF_EMAIL = "email"
CONF_PASSWORD = "password"

DEFAULT_SCAN_INTERVAL = 30  # minutes

MEAL_TYPES: dict[int, str] = {
    0: "Breakfast",
    1: "Lunch",
    2: "Dinner",
    3: "Snack",
}
