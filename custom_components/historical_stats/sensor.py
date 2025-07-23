"""Sensor platform providing configurable historical statistics."""

from datetime import datetime, timedelta, timezone
from dateutil.relativedelta import relativedelta
from homeassistant.components.recorder.statistics import statistics_during_period

import homeassistant.util.dt as dt_util
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import STATE_UNKNOWN
from homeassistant.helpers.event import async_track_time_interval

from .const import STATE_ERROR, STATE_NO_DATA, STATE_OK
from homeassistant.util import slugify

# Earliest possible date for "all history" calculations.
HA_START = datetime(2013, 11, 1, tzinfo=timezone.utc)


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up a HistoricalStatsSensor from a config entry."""
    entity_id = entry.data["entity_id"]
    points = entry.options.get("points", [])
    update_interval = entry.data.get("update_interval", 30)
    friendly_name = entry.data.get("friendly_name")

    if not friendly_name:
        state = hass.states.get(entity_id)
        friendly_name = state.name if state else entity_id

    name = f"Historical statistics for {friendly_name}"

    async_add_entities(
        [HistoricalStatsSensor(hass, name, entity_id, points, update_interval)],
        update_before_add=True,
    )


class HistoricalStatsSensor(SensorEntity):
    """Sensor that calculates historical statistics for a given entity."""

    def __init__(self, hass, name, entity_id, points, update_interval):
        self.hass = hass
        self._attr_name = name
        self._attr_unique_id = f"historical_stats_{slugify(entity_id)}"
        self._entity_id = entity_id
        # Each point defines a statistic type and time window
        self._points = points
        self._attr_native_value = STATE_UNKNOWN
        self._attr_extra_state_attributes = {}
        self._update_interval = timedelta(minutes=update_interval)
        self._unsub_timer = None
        self._attr_should_poll = False

    async def async_added_to_hass(self):
        """Handle when entity is added to Home Assistant."""
        await self.async_update()
        self.async_write_ha_state()
        self._unsub_timer = async_track_time_interval(
            self.hass, self._handle_interval, self._update_interval
        )

    async def async_will_remove_from_hass(self):
        """Cancel scheduled updates when entity is removed."""
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None

    async def _handle_interval(self, _now):
        """Update the sensor at the scheduled interval."""
        await self.async_update()
        self.async_write_ha_state()

    @property
    def suggested_object_id(self):
        """Return stable entity id based on source entity."""
        return f"historical_stats_{slugify(self._entity_id)}"

    @staticmethod
    def _delta_from_unit(unit, value):
        """Return timedelta or relativedelta for a unit."""
        return {
            "minutes": timedelta(minutes=value),
            "hours": timedelta(hours=value),
            "days": timedelta(days=value),
            "weeks": timedelta(weeks=value),
            "months": relativedelta(months=value),
            "years": relativedelta(years=value),
        }.get(unit, timedelta(days=value))

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
            unit_to = point.get("time_unit_to")
            value_to = int(point.get("time_value_to", 0))

            from_prefix = "full" if unit == "all" else f"{unit}_{value}"
            if unit_to:
                to_prefix = "full" if unit_to == "all" else f"{unit_to}_{value_to}"
                prefix = f"{from_prefix}_to_{to_prefix}"
            else:
                prefix = from_prefix
            label = f"{prefix}_{stat_type}"

            try:
                if unit == "all":
                    start = HA_START
                else:
                    start = now - self._delta_from_unit(unit, value)

                end = now - self._delta_from_unit(unit_to, value_to) if unit_to else now

                if stat_type == "value_at":
                    target_time = start
                    states = await self._get_states_around(
                        target_time, delta=timedelta(minutes=10)
                    )
                    found = self._find_closest_state(states, target_time)
                    if found:
                        attrs[label] = found.state
                        attrs[f"{label}_ts"] = found.last_changed.isoformat()
                        attrs[f"{label}_ts_human"] = dt_util.as_local(
                            found.last_changed
                        ).strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        attrs[label] = STATE_UNKNOWN
                    continue

                states = await self._get_states_interval(start, end)
                numeric_states = [
                    (float(s.state), s) for s in states if self._is_number(s.state)
                ]
                values_only = [val for val, _ in numeric_states]

                if not numeric_states:
                    # Try long-term statistics if states were purged
                    fallback = await self._stats_fallback(stat_type, start, end)
                    if fallback is not None:
                        attrs[label] = fallback
                        if fallback is STATE_UNKNOWN and status == STATE_OK:
                            status = STATE_NO_DATA
                        continue
                    attrs[label] = STATE_UNKNOWN
                    if status == STATE_OK:
                        status = STATE_NO_DATA
                    continue

                if stat_type == "min":
                    min_val, min_state = min(numeric_states, key=lambda x: x[0])
                    attrs[label] = min_val
                    attrs[f"{label}_ts"] = min_state.last_changed.isoformat()
                    attrs[f"{label}_ts_human"] = dt_util.as_local(
                        min_state.last_changed
                    ).strftime("%Y-%m-%d %H:%M:%S")
                elif stat_type == "max":
                    max_val, max_state = max(numeric_states, key=lambda x: x[0])
                    attrs[label] = max_val
                    attrs[f"{label}_ts"] = max_state.last_changed.isoformat()
                    attrs[f"{label}_ts_human"] = dt_util.as_local(
                        max_state.last_changed
                    ).strftime("%Y-%m-%d %H:%M:%S")
                elif stat_type == "mean":
                    attrs[label] = sum(values_only) / len(values_only)
                elif stat_type == "total":
                    attrs[label] = (
                        values_only[-1] - values_only[0]
                        if len(values_only) >= 2
                        else STATE_UNKNOWN
                    )
                elif stat_type == "sum":
                    attrs[label] = sum(values_only)
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

    async def _stats_fallback(self, stat_type, start, end):
        """Return value from long-term statistics if available."""
        if stat_type not in {"min", "max", "mean"}:
            return None

        stats = await self.hass.async_add_executor_job(
            statistics_during_period,
            self.hass,
            start,
            end,
            {self._entity_id},
            "hour",
            None,
            {stat_type},
        )

        rows = stats.get(self._entity_id)
        if not rows:
            return STATE_UNKNOWN

        values = [row.get(stat_type) for row in rows if row.get(stat_type) is not None]
        if not values:
            return STATE_UNKNOWN

        if stat_type == "mean":
            return sum(values) / len(values)

        return min(values) if stat_type == "min" else max(values)
