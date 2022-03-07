# homeassistant-easycontrols

[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration)
![GitHub release (latest by date)](https://img.shields.io/github/v/release/laszlojakab/homeassistant-easycontrols)
![GitHub](https://img.shields.io/github/license/laszlojakab/homeassistant-easycontrols)
![GitHub all releases](https://img.shields.io/github/downloads/laszlojakab/homeassistant-easycontrols/total)
[![HA integration usage](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=integration%20usage&suffix=%20installs&cacheSeconds=15600&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.easycontrols.total)](https://analytics.home-assistant.io/custom_integrations.json)
[![Donate](https://img.shields.io/badge/donate-Coffee-yellow.svg)](https://www.buymeacoffee.com/laszlojakab)

Helios EasyControls Modbus TCP/IP integration for [Home Assistant](https://www.home-assistant.io/)

## Usage:
Enable Modbus on device and set minimum fan speed to 0.<br/>
Install component than select Helios Easy Controls from Home Assistant integrations. 

## Features:
Integration adds a fan entity, and the following sensors:

- Preheater operation hours
- Preheater percentage
- Afterheater operation hours
- Afterheater percentage

- Outside air temperature
- Supply air temperature
- Extract air temperature
- Outgoing air temperature

- Extract air relative humidity

- Party mode remaning time

- Airflow rate (approximately value)
- Fan speed percentage
- Fan stage

- Extract air fan operation hours
- Extract air fan rpm
- Extract air fan stage

- Supply air fan operation hours
- Supply air fan rpm
- Supply air fan stage

- Heat recovery efficiency (based on: https://www.engineeringtoolbox.com/heat-recovery-efficiency-d_201.html)

- Bypass state
- Filter change

- Errors
- Warnings
- Information

Also it adds service `easycontrols.party_mode` to change fan speed for limited time.
