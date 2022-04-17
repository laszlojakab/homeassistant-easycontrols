'''Helios Easy Controls integration.'''
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers import device_registry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.typing import ConfigType, HomeAssistantType

from .const import DATA_CONTROLLER, DOMAIN
from .controller import Controller


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
        controller = Controller(
            config_entry.data[CONF_NAME],
            config_entry.data[CONF_HOST],
            config_entry.data[CONF_MAC]
        )

        try:
            await controller.init()
        except Exception as exception:
            raise ConfigEntryNotReady("Error during initialization") from exception

        set_controller(hass, controller)

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


def get_device_info(controller: Controller) -> DeviceInfo:
    '''
    Gets the device info based on the specified device name and the controller

    Parameters
    ----------
    controller: Controller
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


def set_controller(hass: HomeAssistantType, controller: Controller) -> None:
    '''
    Stores the specified controller in hass.data by its MAC address.

    Parameters
    ----------
    controller: Controller
        The thread safe Helios Easy Controls instance.

    Returns
    -------
    None
    '''
    hass.data[DOMAIN][DATA_CONTROLLER][controller.mac] = controller


def get_controller(hass: HomeAssistantType, mac_address: str) -> Controller:
    '''
    Gets the controller for the given MAC address.

    Parameters
    ----------
    mac_address: str
        The MAC address of the Helios device.

    Returns
    -------
    Controller
        The thread safe controller associated to the given MAC address.
    '''
    return hass.data[DOMAIN][DATA_CONTROLLER][mac_address]
