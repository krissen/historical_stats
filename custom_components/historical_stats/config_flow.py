"""Config flow for the Historical statistics integration."""

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import (
    EntitySelector,
    NumberSelector,
    SelectSelector,
)
from homeassistant.helpers import translation

from .const import DOMAIN

# Available statistic types
STAT_TYPES = ["value_at", "min", "max", "mean", "total", "sum"]


class HistoricalStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self.data = {}
        self.measure_points = []
        self.stat_type_labels = {}
        self.time_units = {}
        self._translations_loaded = False

    async def _async_setup_translations(self):
        """Load translations based on the configured language."""
        if self._translations_loaded:
            return
        lang = self.hass.config.language
        stat_type_strings = await translation.async_get_translations(
            self.hass, lang, "stat_type", integrations=[DOMAIN]
        )
        time_unit_strings = await translation.async_get_translations(
            self.hass, lang, "time_unit", integrations=[DOMAIN]
        )
        self.stat_type_labels = {
            key.split(".")[-1]: value for key, value in stat_type_strings.items()
        }
        self.time_units = {
            key.split(".")[-1]: value for key, value in time_unit_strings.items()
        }
        self._translations_loaded = True

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Unique per entity
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
                    vol.Optional("friendly_name"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_add_point(self, user_input=None):
        """Add a new measurement point, allowing multiselect for stat_types."""
        errors = {}
        await self._async_setup_translations()
        if user_input is not None:
            selected_types = user_input["stat_types"]
            time_unit = user_input["time_unit"]
            time_value = user_input.get("time_value", 1)
            time_unit_to = user_input.get("time_unit_to")
            time_value_to = user_input.get("time_value_to")

            for stat_type in selected_types:
                self.measure_points.append(
                    {
                        "stat_type": stat_type,
                        "time_unit": time_unit,
                        "time_value": time_value,
                        "time_unit_to": time_unit_to,
                        "time_value_to": time_value_to,
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

        # Use SelectSelector for proper multi-select in the HA UI
        return self.async_show_form(
            step_id="add_point",
            data_schema=vol.Schema(
                {
                    vol.Required("stat_types", default=["min", "max"]): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.stat_type_labels[v]}
                                for v in STAT_TYPES
                            ],
                            "multiple": True,
                            "mode": "dropdown",
                        }
                    ),
                    vol.Required("time_unit", default="days"): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.time_units[v]}
                                for v in self.time_units
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional("time_value", default=1): int,
                    vol.Optional("time_unit_to"): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.time_units[v]}
                                for v in self.time_units
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional("time_value_to", default=0): int,
                    vol.Optional("add_another", default=False): bool,
                }
            ),
            description_placeholders={
                "info": "Select one or more statistics for this period."
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
        self.stat_type_labels = {}
        self.time_units = {}
        self._translations_loaded = False

    async def _async_setup_translations(self):
        """Load translations based on the configured language."""
        if self._translations_loaded:
            return
        lang = self.config_entry.hass.config.language
        stat_type_strings = await translation.async_get_translations(
            self.config_entry.hass, lang, "stat_type", integrations=[DOMAIN]
        )
        time_unit_strings = await translation.async_get_translations(
            self.config_entry.hass, lang, "time_unit", integrations=[DOMAIN]
        )
        self.stat_type_labels = {
            key.split(".")[-1]: value for key, value in stat_type_strings.items()
        }
        self.time_units = {
            key.split(".")[-1]: value for key, value in time_unit_strings.items()
        }
        self._translations_loaded = True

    async def async_step_init(self, user_input=None):
        """Show current points and options to add/remove."""
        errors = {}
        await self._async_setup_translations()
        point_labels = [
            f"{i + 1}: {point['stat_type']} {point.get('time_value', '')} {point.get('time_unit', '')}"
            for i, point in enumerate(self.points)
        ]
        choices = [
            {"value": str(i), "label": lbl} for i, lbl in enumerate(point_labels)
        ]
        schema = vol.Schema(
            {
                vol.Optional("add_point", default=False): bool,
                vol.Optional("remove_indices", default=[]): SelectSelector(
                    {"options": choices, "multiple": True, "mode": "list"}
                )
                if choices
                else [],
                vol.Optional("edit_index"): SelectSelector(
                    {"options": choices, "multiple": False}
                )
                if choices
                else str,
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
        await self._async_setup_translations()
        if user_input is not None:
            self.points.append(user_input)
            return await self.async_step_init()
        return self.async_show_form(
            step_id="add_point",
            data_schema=vol.Schema(
                {
                    vol.Required("stat_type", default="value_at"): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.stat_type_labels[v]}
                                for v in STAT_TYPES
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Required("time_unit", default="days"): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.time_units[v]}
                                for v in self.time_units
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional("time_value", default=1): int,
                    vol.Optional("time_unit_to"): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.time_units[v]}
                                for v in self.time_units
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional("time_value_to", default=0): int,
                }
            ),
            errors=errors,
        )

    async def async_step_edit_point(self, user_input=None):
        """Edit an existing measurement point."""
        errors = {}
        await self._async_setup_translations()
        point = self.points[self._edit_index]
        if user_input is not None:
            self.points[self._edit_index] = user_input
            self._edit_index = None
            return await self.async_step_init()
        return self.async_show_form(
            step_id="edit_point",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        "stat_type", default=point["stat_type"]
                    ): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.stat_type_labels[v]}
                                for v in STAT_TYPES
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Required(
                        "time_unit", default=point.get("time_unit", "days")
                    ): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.time_units[v]}
                                for v in self.time_units
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional("time_value", default=point.get("time_value", 1)): int,
                    vol.Optional("time_unit_to"): SelectSelector(
                        {
                            "options": [
                                {"value": v, "label": self.time_units[v]}
                                for v in self.time_units
                            ],
                            "mode": "dropdown",
                        }
                    ),
                    vol.Optional(
                        "time_value_to", default=point.get("time_value_to", 0)
                    ): int,
                }
            ),
            errors=errors,
        )
