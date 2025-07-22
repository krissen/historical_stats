import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.selector import EntitySelector, NumberSelector
from .const import DOMAIN


class HistoricalStatsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            # Unique by entity
            await self.async_set_unique_id(user_input["entity_id"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Historical statistics: {user_input['entity_id']}",
                data=user_input,
            )
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

    # Options flow placeholder for later
    @staticmethod
    def async_get_options_flow(config_entry):
        return HistoricalStatsOptionsFlow(config_entry)


class HistoricalStatsOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        # Will be expanded with measurement points etc.
        return self.async_show_form(step_id="init", data_schema=vol.Schema({}))
