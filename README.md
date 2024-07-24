# homeassistant-easycontrols

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/laszlojakab/homeassistant-easycontrols)
![GitHub](https://img.shields.io/github/license/laszlojakab/homeassistant-easycontrols)
![GitHub all releases](https://img.shields.io/github/downloads/laszlojakab/homeassistant-easycontrols/total)
[![HA integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.easycontrols.total)](https://analytics.home-assistant.io/custom_integrations.json)
[![Donate](https://img.shields.io/badge/donate-Coffee-yellow.svg)](https://www.buymeacoffee.com/laszlojakab)

Helios EasyControls (2.x) Modbus TCP/IP integration for [Home Assistant](https://www.home-assistant.io/). The integration won't work with EasyControls 3.x version devices.

## Installation

You can install this integration via [HACS](#hacs) or [manually](#manual).

### HACS

This integration is included in HACS. Search for the `Easy Controls` integration and choose install. Reboot Home Assistant and configure the 'Helios Easy Controls' integration via the integrations page or press the blue button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=easycontrols)

### Manual

Copy the `custom_components/easycontrols` to your `custom_components` folder. Reboot Home Assistant and configure the 'Helios Easy Controls' integration via the integrations page or press the blue button below.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=easycontrols)

## Setup

- Login to device's configuration page.
- Tick `Modbus activated` checkbox under `Configuration/Device/Building control system` menu item.  
- Set `Minimum fan speed` to `0` under `Configuration/Fan/Fan configuration` menu item.

## Features

The integration adds the following entities and services to Home Assistant:

- **Fan**

  The ventilation unit can be controlled by the fan entity. Supported features:

  - turning on/off
  - settings speed
  - setting preset (auto, party, stand-by mode)

- **Sensors**
  - Pre-heater and after-heater related sensors:
    - Preheater operation hours
    - Preheater percentage
    - Afterheater operation hours
    - Afterheater percentage
  - Temperature sensors:
    - Outside air temperature
    - Supply air temperature
    - Extract air temperature
    - Outgoing air temperature
  - Humidity sensors:
    - Extract air relative humidity
  - External sensors:
    - FTF Humidity
  - Operation related sensors:
    - Fan speed percentage
    - Fan stage
    - Extract air fan rpm
    - Extract air fan stage
    - Supply air fan rpm
    - Supply air fan stage
  - Binary sensors:
    - Bypass
    - Filter change required
  - Text sensors:
    - Errors
    - Warnings
    - Information
  - Additional computed sensors which values are not provided by the ventilation unit:
    - Airflow rate (approximately value)
    - Heat recovery efficiency (based on: https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html)
- **Services**
  - `easycontrols.party_mode`

## Enable debug logging

The [logger](https://www.home-assistant.io/integrations/logger/) integration lets you define the level of logging activities in Home Assistant. Turning on debug mode will show more information about the running of the integration in the homeassistant.log file.

```yaml
logger:
  default: error
  logs:
    custom_components.easycontrols: debug
```
