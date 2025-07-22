# Historical statistics

A flexible and efficient custom integration for [Home Assistant](https://www.home-assistant.io/) that exposes user-defined historical statistics for any entity. This component allows you to create virtual sensors that show min, max, mean, exact value at time, or total change over custom time periods – all configurable via the Home Assistant UI.

---

## Features

- **Any source entity:** Works with any numeric sensor or entity with a numeric state.
- **Configurable measurement points:** Define as many time-based statistics as you want, such as "max last 7 days", "mean last 30 days", "value 24 hours ago", or "total change this month".
- **Multiple statistics per time window:** Easily select several statistics (min, max, mean) for a single period in one step.
- **All configuration via UI:** No YAML or manual editing needed; set up and edit everything through Home Assistant’s user interface.
- **Smart caching:** Efficient use of Home Assistant’s history database; only queries necessary periods.
- **Entity attributes:** Each measurement/statistic is available as an attribute on the virtual sensor.

---

## Example use cases

- Show yesterday’s temperature at the same time as now.
- Find the minimum, maximum, and mean humidity over the last 7 days.
- Track total energy consumption during the current month.
- Compare current outdoor temperature to what it was exactly 1 year ago.

---

## Installation

1. **Copy the custom component**  
   Place the entire `historical_stats` directory under your Home Assistant `custom_components/` folder.

2. **Restart Home Assistant**  
For Home Assistant to recognize the new integration, restart the server.

---

## Configuration

1. Go to **Settings > Devices & Services > Add Integration** and search for **Historical statistics**.
2. **Select the source entity** you wish to track (for example, a temperature sensor).
3. **Set the update interval** (how often the statistics should be recalculated).
4. **Define your measurement points:**

- Choose one or more statistics (min, max, mean, value at, total change).
- Select the time period (e.g., "days ago", "weeks ago", or "all history").
- Enter the number of units for the period (e.g., "7 days ago", "1 month ago").
- Add as many points as you like.

5. Save and finish.

All statistics for the entity will be available as attributes on a new sensor entity, e.g.  
`sensor.historical_statistics_sensor_outside_temperature`

---

## Viewing the data

- Go to **Developer Tools > States** and search for your new sensor entity.
- All configured statistics are shown as state attributes.
- You can use these attributes in Lovelace cards, automations, or scripts.

---

## Example: Show yesterday’s temperature at the same time

1. Add a measurement point:

- Statistic: Value at
- Period: Days ago
- Value: 1

2. The result appears as the attribute `value_at_1_days` on your sensor.

---

## Limitations & Notes

- The integration uses Home Assistant's history/recorder database. If you purge or limit your recorder history, statistics beyond that range will be unavailable.
- Only numeric states are supported.
- The “total” statistic is the difference between the first and last value in the interval.
- Large intervals may be slower to calculate if your database is very large.

---

## Upgrading

If you update this custom component, always restart Home Assistant for changes to take effect.

---

## Contributing

Pull requests and suggestions are welcome!  
All code should be commented in English and follow KISS and DRY principles.

---
