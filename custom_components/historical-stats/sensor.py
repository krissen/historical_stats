from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN
from .const import DOMAIN


async def async_setup_entry(hass, entry, async_add_entities):
    # Placeholder sensor, will be extended
    sensor_entity_id = entry.data["entity_id"]
    name = f"Historical statistics {sensor_entity_id}"
    async_add_entities([HistoricalStatsSensor(name)], update_before_add=True)


class HistoricalStatsSensor(SensorEntity):
    def __init__(self, name):
        self._attr_name = name
        self._attr_unique_id = f"historical_stats_{name.lower().replace(' ', '_')}"
        self._attr_native_value = STATE_UNKNOWN
        self._attr_extra_state_attributes = {}

    @property
    def extra_state_attributes(self):
        return self._attr_extra_state_attributes
