import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    NumberSelector,
    SelectSelector,
)

from .const import DOMAIN

# Tillgängliga statistiktyper
STAT_TYPES = [
    "value_at",
    "min",
    "max",
    "mean",
    "total",
]
STAT_TYPE_LABELS = {
    "value_at": "Value at",
    "min": "Minimum",
    "max": "Maximum",
    "mean": "Mean",
    "total": "Total change",
}

TIME_UNITS = {
    "minutes": "Minutes ago",
    "hours": "Hours ago",
    "days": "Days ago",
    "weeks": "Weeks ago",
    "months": "Months ago",
    "all": "All history",
}


class HistoricalStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.data = {}
        self.measure_points = []

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Unik per entity
            await self.async_set_unique_id(user_input["entity_id"])
            self._abort_if_unique_id_configured()
            self.data = user_input
            return await self.async_step_add_point()
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("entity_id"): EntitySelector({"multiple": False}),
                    vol.Optional("update_interval", default=30): NumberSelector(
                        {"min": 1, "max": 1440, "unit_of_measurement": "min"}
                    ),
                }
            ),
            errors=errors,
        )

    async def async_step_add_point(self, user_input=None):
        """Add a new measurement point, allowing multiselect for stat_types."""
        errors = {}
        if user_input is not None:
            selected_types = user_input["stat_types"]
            time_unit = user_input["time_unit"]
            time_value = user_input.get("time_value", 1)

            # Special case: if value_at or total is selected, only one allowed
            if (
                any(t in selected_types for t in ["value_at", "total"])
                and len(selected_types) > 1
            ):
                errors["stat_types"] = (
                    "Value at / Total cannot be combined with other types."
                )
            else:
                for stat_type in selected_types:
                    self.measure_points.append(
                        {
                            "stat_type": stat_type,
                            "time_unit": time_unit,
                            "time_value": time_value,
                        }
                    )
                if user_input.get("add_another", False):
                    return await self.async_step_add_point()
                entry_data = dict(self.data)
                entry_options = {"points": self.measure_points}
                return self.async_create_entry(
                    title=f"Historical statistics: {self.data['entity_id']}",
                    data=entry_data,
                    options=entry_options,
                )

        # Use SelectSelector for proper multi-select in the HA UI
        return self.async_show_form(
            step_id="add_point",
            data_schema=vol.Schema(
                {
                    vol.Required("stat_types", default=["min", "max"]): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": STAT_TYPE_LABELS[v]}
                                for v in STAT_TYPES
                            ],
                            "multiple": True,
                            "mode": "dropdown",
                        }
                    ),
                    vol.Required("time_unit", default="days"): vol.In(TIME_UNITS),
                    vol.Optional("time_value", default=1): int,
                    vol.Optional("add_another", default=False): bool,
                }
            ),
            description_placeholders={
                "info": (
                    "Select one or more statistics for this period. "
                    "Note: 'Value at' and 'Total change' cannot be combined with others."
                )
            },
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry):
        return HistoricalStatsOptionsFlow(config_entry)


class HistoricalStatsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry
        # Copy list so we can edit before saving
        self.points = list(config_entry.options.get("points", []))
        self._current_step = "init"

    async def async_step_init(self, user_input=None):
        """Show current points and options to add/remove."""
        errors = {}
        point_labels = [
            f"{i + 1}: {point['stat_type']} {point.get('time_value', '')} {point.get('time_unit', '')}"
            for i, point in enumerate(self.points)
        ]
        choices = {str(i): lbl for i, lbl in enumerate(point_labels)}
        # Actions: add, remove, finish
        schema = vol.Schema(
            {
                vol.Optional("add_point", default=False): bool,
                vol.Optional("remove_index"): vol.In(choices) if choices else str,
                vol.Optional("finish", default=True): bool,
            }
        )
        if user_input:
            # Handle remove
            if user_input.get("remove_index") is not None:
                idx = int(user_input["remove_index"])
                if 0 <= idx < len(self.points):
                    self.points.pop(idx)
                    return await self.async_step_init()
            # Handle add
            if user_input.get("add_point"):
                return await self.async_step_add_point()
            # Done
            if user_input.get("finish"):
                return self.async_create_entry(
                    title=self.config_entry.title,
                    data=self.config_entry.data,
                    options={"points": self.points},
                )

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "current_points": (
                    "\n".join(point_labels)
                    if point_labels
                    else "No measurement points yet."
                ),
            },
            errors=errors,
        )

    async def async_step_add_point(self, user_input=None):
        """Add new measurement point."""
        errors = {}
        if user_input is not None:
            self.points.append(user_input)
            return await self.async_step_init()
        return self.async_show_form(
            step_id="add_point",
            data_schema=vol.Schema(
                {
                    vol.Required("stat_type", default="value_at"): vol.In(STAT_TYPES),
                    vol.Required("time_unit", default="days"): vol.In(TIME_UNITS),
                    vol.Optional("time_value", default=1): int,
                }
            ),
            errors=errors,
        )
