'''Helios Easy Controls integration.'''
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DATA_CONTROLLER, DOMAIN
from .threadsafe_controller import ThreadSafeController


# pylint: disable=unused-argument
async def async_setup(hass: HomeAssistantType, config: ConfigType) -> bool:
    '''
    Set up the Helios Easy Controls component.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config: homeassistant.helpers.typing.ConfigType
        The configuration.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''
    hass.data[DOMAIN] = {DATA_CONTROLLER: {}}
    return True


async def async_setup_entry(hass: HomeAssistantType, config_entry: ConfigEntry) -> bool:
    '''
    Initialize the sensors and the fan based on the config entry represents a Helios device.

    Parameters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    config_entry: homeassistant.config_entries.ConfigEntry
        The config entry which contains information gathered by the config flow.

    Returns
    -------
    bool
        The value indicates whether the setup succeeded.
    '''

    if not is_controller_exists(hass, config_entry.data[CONF_MAC]):
        set_controller(hass, ThreadSafeController(
            config_entry.data[CONF_NAME],
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_MAC]
        ))

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, 'fan')
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, 'sensor')
    )

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(config_entry, 'binary_sensor')
    )
    return True


def get_device_info(controller: ThreadSafeController) -> DeviceInfo:
    '''
    Gets the device info based on the specified device name and the controller

    Parameters
    ----------
    controller: ThreadSafeController
        The thread safe Helios Easy Controls controller.
    '''
    return DeviceInfo(
        connections={(device_registry.CONNECTION_NETWORK_MAC, controller.mac)},
        identifiers={(DOMAIN, controller.serial_number)},
        name=controller.device_name,
        manufacturer='Helios',
        model=controller.model,
        sw_version=controller.version,
        configuration_url=f'http://{controller.host}'
    )


def is_controller_exists(hass: HomeAssistantType, mac_address: str) -> bool:
    '''
    Gets the value indicates whether a controller already registered
    in hass.data for the given MAC address

    Paraemters
    ----------
    hass: homeassistant.helpers.typing.HomeAssistantType
        The Home Assistant instance.
    mac_address: str
        The MAC address of the Helios device.

    Returns
    -------
    bool
        the value indicates whether a controller already registered
        in hass.data for the given MAC address
    '''
    return mac_address in hass.data[DOMAIN][DATA_CONTROLLER]


def set_controller(hass: HomeAssistantType, controller: ThreadSafeController) -> None:
    '''
    Stores the specified controller in hass.data by its MAC address.

    Parameters
    ----------
    controller: ThreadSafeController
        The thread safe Helios Easy Controls instance.

    Returns
    -------
    None
    '''
    hass.data[DOMAIN][DATA_CONTROLLER][controller.mac] = controller


def get_controller(hass: HomeAssistantType, mac_address: str) -> ThreadSafeController:
    '''
    Gets the controller for the given MAC address.

    Parameters
    ----------
    mac_address: str
        The MAC address of the Helios device.

    Returns
    -------
    ThreadSafeController
        The thread safe controller associated to the given MAC address.
    '''
    return hass.data[DOMAIN][DATA_CONTROLLER][mac_address]
