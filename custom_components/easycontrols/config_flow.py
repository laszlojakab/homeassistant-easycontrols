''' The configuration flow for Helios Easy Controls integration. '''
import logging
from typing import Any, Dict

import voluptuous as vol
from eazyctrl import EazyController
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN, VARIABLE_ARTICLE_DESCRIPTION, VARIABLE_MAC_ADDRESS

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class EasyControlsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    '''
    Configuration flow handler for Helios Easy Controls integration.
    '''
    VERSION = 1

    async def async_step_user(self, user_info: Dict[str, Any]) -> FlowResult:
        '''
        Handles the step when integration added from the UI.
        '''
        data_schema = vol.Schema({
            vol.Required(CONF_HOST): str,
            vol.Required(CONF_NAME): str
        })

        if user_info is not None:
            await self.async_set_unique_id(user_info[CONF_NAME])
            self._abort_if_unique_id_configured()

            try:
                controller = EazyController(user_info[CONF_HOST])
                device_type = controller.get_variable(
                    VARIABLE_ARTICLE_DESCRIPTION.name, VARIABLE_ARTICLE_DESCRIPTION.size
                )
                mac_address = controller.get_variable(
                    VARIABLE_MAC_ADDRESS.name, VARIABLE_MAC_ADDRESS.size
                )
            # pylint: disable=broad-except
            except Exception as error:
                _LOGGER.error('Error while creating controller: %s', error)

                return self.async_show_form(
                    step_id='user',
                    data_schema=data_schema,
                    errors={CONF_HOST: 'invalid_host'}
                )

            data = {
                CONF_NAME: user_info[CONF_NAME],
                CONF_HOST: user_info[CONF_HOST],
                CONF_MAC: mac_address
            }

            return self.async_create_entry(
                title=f'Helios {device_type} ({user_info[CONF_NAME]})', data=data
            )

        return self.async_show_form(
            step_id='user',
            data_schema=data_schema,
        )
