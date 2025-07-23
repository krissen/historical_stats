# Historical statistics

A custom integration for [Home Assistant](https://www.home-assistant.io/) that exposes user-defined historical statistics for any entity with numerical stats. This component allows you to create virtual sensors that show min, max, mean, exact value at time, total change, or sum over custom time periods.

<img width="469" height="376" alt="Skärmavbild 2025-07-23 kl  12 32 31" src="https://github.com/user-attachments/assets/53c343c4-77f1-4cde-83ee-cc1431ea4f38" />

---

## Features

- **Any source entity:** Works with any numeric sensor or entity with a numeric state.
- **Configurable measurement points:** Define as many time-based statistics as you want, such as "max last 7 days", "mean last 30 days", "value 24 hours ago", "total change this month", or "sum last year".
- **Custom time ranges:** Specify both the starting point and the ending point for each measurement.
- **Multiple statistics per time window:** Easily select several statistics (min, max, mean, sum) for a single period in one step.
- **All configuration via UI:** No YAML or manual editing needed; set up and edit everything through Home Assistant’s user interface.
- **Entity attributes:** All measurements/statistics are available as attributes on one virtual sensor.

---

## Example use cases

- Show yesterday’s temperature at the same time as now.
- Find the minimum, maximum, and mean humidity over the last 7 days.
- Track total energy consumption during the current month.
- Compare current outdoor temperature to what it was exactly 1 year ago.

---

## Comparison to existing solutions

Home Assistant already includes a `statistics` sensor and a **statistical value**
card. These work well for single measurements but quickly become unwieldy when
many different periods or statistics are needed. Each metric usually requires its
own sensor and they do not expose timestamps for the extreme values. Template
sensors or Python scripts did not seem to do the job either. Enter this integration.

---

## Installation

### HACS

1. **Add custom repository** `https://github.com/krissen/historical_stats` of type `integration`
2. **Add integration** `Historical statistics`
3. **Restart** Home Assistant

### Manually

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

- Choose one or more statistics (min, max, mean, sum, value at, total change).
- Select the time period (e.g., "days ago", "weeks ago", "this year", or "all history").
- Enter the number of units for the period (e.g., "7 days ago", "1 month ago").
- Add as many points as you like.

5. Save and finish.

### Editing measurement points

To modify the configuration later, open **Settings > Devices & Services**, locate
your *Historical statistics* entry and choose **Configure**. You can then add,
edit or remove points and press **Save changes**. The sensor will reload
automatically with the new settings.

All statistics for the entity will be available as attributes on a new sensor entity, e.g.
`sensor.historical_statistics_sensor_outside_temperature`
The attribute naming follows `<period>_<statistic>` where the period is `unit_value` like `days_7` or simply `full` for all history. Example: `days_7_min`.

---

## Viewing the data

- Go to **Developer Tools > States** and search for your new sensor entity.
- All configured statistics are shown as state attributes.
- You can use these attributes in Lovelace cards, automations, or scripts.

---

## Example: Show yesterday’s temperature at the same time

1. Add a measurement point:

- Statistic: Value at
- Period: Hours ago
- Value: 24

2. The result appears as the attribute `hours_24_value_at` on your sensor.

## Example: Compare two temperature sensors

<img width="469" height="376" alt="Skärmavbild 2025-07-23 kl  12 32 31" src="https://github.com/user-attachments/assets/53c343c4-77f1-4cde-83ee-cc1431ea4f38" />

The following snippet can be used in a Markdown card to display several
statistics for two sensors side by side.

```jinja
{% set porch_stats = states.sensor.historical_statistics_sensor_porch_temperature %}
{% set veranda_stats = states.sensor.historical_statistics_sensor_veranda_temperature %}

|        |  | Porch || Veranda |
|--------|--|:-----:|--|:------:|
| Now    |  | {{ states('sensor.porch_temperature') }} °C || {{ states('sensor.veranda_temperature') }} °C |
| Yesterday | | {{ porch_stats.attributes['hours_24_value_at'] }} °C || {{ veranda_stats.attributes['hours_24_value_at'] }} °C |
| <font color="#2196F3">Week min.</font> | | <font color="#2196F3">{{ porch_stats.attributes['weeks_1_min'] }} °C</font> || <font color="#2196F3">{{ veranda_stats.attributes['weeks_1_min'] }} °C</font> |
| <font color="#E53935">Week max.</font> | | <font color="#E53935">{{ porch_stats.attributes['weeks_1_max'] }} °C</font> || <font color="#E53935">{{ veranda_stats.attributes['weeks_1_max'] }} °C</font> |
| <font color="#2196F3">Overall min.</font> | | <font color="#2196F3">{{ porch_stats.attributes['full_min'] }} °C</font> || <font color="#2196F3">{{ veranda_stats.attributes['full_min'] }} °C</font> |
| <font color="#E53935">Overall max.</font> | | <font color="#E53935">{{ porch_stats.attributes['full_max'] }} °C</font> || <font color="#E53935">{{ veranda_stats.attributes['full_max'] }} °C</font> |

---
|        |   | |
|:------:|---------|:-------:|
<font color="#2196F3">{{ porch_stats.attributes['weeks_1_min_ts'][:16].replace('T',' ') }}</font> | | <font color="#2196F3">{{ veranda_stats.attributes['weeks_1_min_ts'][:16].replace('T',' ') }}</font>
<font color="#E53935">{{ porch_stats.attributes['weeks_1_max_ts'][:16].replace('T',' ') }}</font> || <font color="#E53935">{{ veranda_stats.attributes['weeks_1_max_ts'][:16].replace('T',' ') }}</font>
<font color="#2196F3">{{ porch_stats.attributes['full_min_ts'][:16].replace('T',' ') }}</font> || <font color="#2196F3">{{ veranda_stats.attributes['full_min_ts'][:16].replace('T',' ') }}</font>
<font color="#E53935">{{ porch_stats.attributes['full_max_ts'][:16].replace('T',' ') }}</font> | | <font color="#E53935">{{ veranda_stats.attributes['full_max_ts'][:16].replace('T',' ') }}</font>
```

---

## Limitations & Notes

- The integration relies on Home Assistant's history database. If raw states have been purged, min/max/mean values fall back to long‑term statistics when available.
- Only numeric states are supported.
- The “total” statistic is the difference between the first and last value in the interval.
- Large intervals may be slower to calculate if your database is very large.

---

## Upgrading

If you update this custom component, always restart Home Assistant for changes to take effect.

---

## Contributing

Pull requests and suggestions are welcome!  

- All code should be commented in English and follow KISS and DRY principles.
- Please make PR:s to the `dev` branch, not master.

---
