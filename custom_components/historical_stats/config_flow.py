"""Config flow for the Historical statistics integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, NumberSelector

try:
    from homeassistant.helpers.selector import TextSelector

    _HAS_TEXT = True
except Exception:  # pragma: no cover - older HA versions
    TextSelector = None
    _HAS_TEXT = False

try:
    from homeassistant.helpers.selector import SelectSelector

    _HAS_SELECT = True
except Exception:  # pragma: no cover - older HA versions
    SelectSelector = None
    _HAS_SELECT = False

from homeassistant.helpers import config_validation as cv

from .const import DOMAIN

# Available statistic types
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
    """Handle the config flow for the integration."""

    VERSION = 1

    def __init__(self):
        self.data: dict = {}
        self.measure_points: list = []

    async def async_step_user(self, user_input=None):
        """Initial step: select the source entity."""
        errors = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input["entity_id"])
            self._abort_if_unique_id_configured()
            self.data = {"entity_id": user_input["entity_id"]}
            return await self.async_step_details()

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required("entity_id"): EntitySelector({"multiple": False})}
            ),
            errors=errors,
        )

    async def async_step_details(self, user_input=None):
        """Configure friendly name and update interval."""
        errors = {}

        entity_id = self.data.get("entity_id")
        state = self.hass.states.get(entity_id) if entity_id else None
        placeholder = "friendly name"
        if state:
            placeholder = state.name

        update_default = self.data.get("update_interval", 30)
        friendly_default = self.data.get("friendly_name")
        if friendly_default is None:
            friendly_default = placeholder

        if user_input is not None:
            self.data.update(user_input)
            return await self.async_step_add_point()

        return self.async_show_form(
            step_id="details",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "update_interval", default=update_default
                    ): NumberSelector(
                        {"min": 1, "max": 1440, "unit_of_measurement": "min"}
                    ),
                    vol.Optional("friendly_name", default=friendly_default): (
                        TextSelector({"placeholder": placeholder}) if _HAS_TEXT else str
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

            # Enforce exclusive types: "value_at" and "total" cannot be combined
            exclusive = [t for t in selected_types if t in ["value_at", "total"]]
            if exclusive:
                # Keep only the last exclusive type chosen
                selected_types = [exclusive[-1]]

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
            friendly_name = entry_data.get("friendly_name")
            if not friendly_name:
                state = self.hass.states.get(entry_data["entity_id"])
                friendly_name = state.name if state else entry_data["entity_id"]
            return self.async_create_entry(
                title=f"Historical statistics: {friendly_name}",
                data=entry_data,
                options=entry_options,
            )

        stat_selector = (
            SelectSelector(
                {
                    "options": [
                        {"value": v, "label": STAT_TYPE_LABELS[v]} for v in STAT_TYPES
                    ],
                    "multiple": True,
                    "mode": "dropdown",
                }
            )
            if _HAS_SELECT
            else vol.All(cv.ensure_list, [vol.In(STAT_TYPES)])
        )

        return self.async_show_form(
            step_id="add_point",
            data_schema=vol.Schema(
                {
                    vol.Required("stat_types", default=["min", "max"]): stat_selector,
                    vol.Required("time_unit", default="days"): vol.In(TIME_UNITS),
                    vol.Optional("time_value", default=1): int,
                    vol.Optional("add_another", default=False): bool,
                }
            ),
            description_placeholders={
                "info": (
                    "Select one or more statistics for this period. "
                    "'Value at' and 'Total change' will replace any other selections."
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
        self._edit_index = None

    async def async_step_init(self, user_input=None):
        """Show current points and options to add/remove."""
        errors = {}
        point_labels = [
            f"{i + 1}: {point['stat_type']} {point.get('time_value', '')} {point.get('time_unit', '')}"
            for i, point in enumerate(self.points)
        ]
        choices = [
            {"value": str(i), "label": lbl} for i, lbl in enumerate(point_labels)
        ]
        remove_selector = (
            SelectSelector({"options": choices, "multiple": True, "mode": "list"})
            if _HAS_SELECT and choices
            else vol.All(cv.ensure_list, [vol.In([c["value"] for c in choices])])
            if choices
            else []
        )
        edit_selector = (
            SelectSelector({"options": choices, "multiple": False})
            if _HAS_SELECT and choices
            else vol.In([c["value"] for c in choices])
            if choices
            else str
        )

        schema = vol.Schema(
            {
                vol.Optional("add_point", default=False): bool,
                vol.Optional("remove_indices", default=[]): remove_selector,
                vol.Optional("edit_index"): edit_selector,
                vol.Optional("finish", default=True): bool,
            }
        )
        if user_input:
            # Handle remove (can remove multiple indices)
            if user_input.get("remove_indices"):
                for idx_str in sorted(user_input["remove_indices"], reverse=True):
                    idx = int(idx_str)
                    if 0 <= idx < len(self.points):
                        self.points.pop(idx)
                return await self.async_step_init()
            # Handle edit
            if user_input.get("edit_index") is not None:
                idx = int(user_input["edit_index"])
                if 0 <= idx < len(self.points):
                    self._edit_index = idx
                    return await self.async_step_edit_point()
            # Handle add
            if user_input.get("add_point"):
                return await self.async_step_add_point()
            # Done
            if user_input.get("finish"):
                return self.async_create_entry(
                    title=self.config_entry.title, data={"points": self.points}
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

    async def async_step_edit_point(self, user_input=None):
        """Edit an existing measurement point."""
        errors = {}
        point = self.points[self._edit_index]
        if user_input is not None:
            self.points[self._edit_index] = user_input
            self._edit_index = None
            return await self.async_step_init()
        return self.async_show_form(
            step_id="edit_point",
            data_schema=vol.Schema(
                {
                    vol.Required("stat_type", default=point["stat_type"]): vol.In(
                        STAT_TYPES
                    ),
                    vol.Required(
                        "time_unit", default=point.get("time_unit", "days")
                    ): vol.In(TIME_UNITS),
                    vol.Optional("time_value", default=point.get("time_value", 1)): int,
                }
            ),
            errors=errors,
        )
