# homeassistant-easycontrols
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


