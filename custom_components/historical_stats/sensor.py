"""Sensor platform providing configurable historical statistics."""

from datetime import timedelta

import homeassistant.util.dt as dt_util
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN

from .const import STATE_ERROR, STATE_NO_DATA, STATE_OK
from homeassistant.util import slugify


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a HistoricalStatsSensor from a config entry."""
    entity_id = entry.data["entity_id"]
    points = entry.options.get("points", [])
    friendly_name = entry.data.get("friendly_name")

    if not friendly_name:
        state = hass.states.get(entity_id)
        friendly_name = state.name if state else entity_id

    name = f"Historical statistics for {friendly_name}"

    async_add_entities(
        [HistoricalStatsSensor(hass, name, entity_id, points)], update_before_add=True
    )


class HistoricalStatsSensor(SensorEntity):
    """Sensor that calculates historical statistics for a given entity."""

    def __init__(self, hass, name, entity_id, points):
        self.hass = hass
        self._attr_name = name
        self._attr_unique_id = f"historical_stats_{slugify(entity_id)}"
        self._entity_id = entity_id
        # Each point defines a statistic type and time window
        self._points = points
        self._attr_native_value = STATE_UNKNOWN
        self._attr_extra_state_attributes = {}

    @property
    def suggested_object_id(self):
        """Return stable entity id based on source entity."""
        return f"historical_stats_{slugify(self._entity_id)}"

    async def async_update(self):
        """Fetch and calculate statistics for each point."""
        now = dt_util.utcnow()
        attrs = {}
        status = STATE_OK

        # Iterate over configured measurement points
        for i, point in enumerate(self._points, 1):
            stat_type = point["stat_type"]
            unit = point.get("time_unit", "days")
            value = int(point.get("time_value", 1))
            prefix = f"{unit}_{value}" if unit != "all" else "full"
            label = f"{prefix}_{stat_type}"

            try:
                if unit == "all":
                    start = dt_util.utc_from_timestamp(0)
                    end = now
                else:
                    delta = {
                        "minutes": timedelta(minutes=value),
                        "hours": timedelta(hours=value),
                        "days": timedelta(days=value),
                        "weeks": timedelta(weeks=value),
                        "months": timedelta(days=value * 30),
                    }.get(unit, timedelta(days=value))

                    if stat_type == "value_at":
                        target_time = now - delta
                        states = await self._get_states_around(
                            target_time, delta=timedelta(minutes=10)
                        )
                        found = self._find_closest_state(states, target_time)
                        if found:
                            attrs[label] = found.state
                            attrs[f"{label}_ts"] = found.last_changed.isoformat()
                        else:
                            attrs[label] = STATE_UNKNOWN
                        continue

                    start = now - delta
                    end = now

                states = await self._get_states_interval(start, end)
                numeric_states = [
                    (float(s.state), s) for s in states if self._is_number(s.state)
                ]
                values_only = [val for val, _ in numeric_states]

                if not numeric_states:
                    attrs[label] = STATE_UNKNOWN
                    if status == STATE_OK:
                        status = STATE_NO_DATA
                    continue

                if stat_type == "min":
                    min_val, min_state = min(numeric_states, key=lambda x: x[0])
                    attrs[label] = min_val
                    attrs[f"{label}_ts"] = min_state.last_changed.isoformat()
                elif stat_type == "max":
                    max_val, max_state = max(numeric_states, key=lambda x: x[0])
                    attrs[label] = max_val
                    attrs[f"{label}_ts"] = max_state.last_changed.isoformat()
                elif stat_type == "mean":
                    attrs[label] = sum(values_only) / len(values_only)
                elif stat_type == "total":
                    attrs[label] = (
                        values_only[-1] - values_only[0]
                        if len(values_only) >= 2
                        else STATE_UNKNOWN
                    )
                else:
                    attrs[label] = STATE_UNKNOWN
            except Exception:
                status = STATE_ERROR
                attrs[label] = STATE_UNKNOWN
                continue

        self._attr_extra_state_attributes = attrs
        self._attr_native_value = status

    async def _get_states_around(self, target_time, delta=timedelta(minutes=10)):
        """Return all states within +-delta of target_time."""
        start = target_time - delta
        end = target_time + delta
        return await self._get_states_interval(start, end)

    async def _get_states_interval(self, start, end):
        """Return all recorded states in interval."""
        return (
            await self.hass.async_add_executor_job(
                get_significant_states,
                self.hass,
                start,
                end,
                [self._entity_id],
                None,
                True,
                False,
            )
        )[self._entity_id]

    @staticmethod
    def _is_number(val):
        try:
            float(val)
            return True
        except Exception:
            return False

    @staticmethod
    def _find_closest_state(states, target_time):
        """Find the state with closest last_changed to target_time."""
        if not states:
            return None
        return min(states, key=lambda s: abs(s.last_changed - target_time))
