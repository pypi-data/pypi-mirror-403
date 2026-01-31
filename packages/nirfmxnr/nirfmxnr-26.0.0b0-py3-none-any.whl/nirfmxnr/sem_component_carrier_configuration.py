""""""

import functools

import nirfmxnr.attributes as attributes
import nirfmxnr.errors as errors
import nirfmxnr.internal._helper as _helper


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed NR signal configuration")
        return f(*xs, **kws)

    return aux


class SemComponentCarrierConfiguration(object):
    """"""

    def __init__(self, signal_obj):
        """"""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of a component carrier. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the integration bandwidth of a component carrier. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.SEM_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rated_output_power(self, selector_string):
        r"""Gets the rated output power (P\ :sub:`rated, x`\), which is used only to choose the limit table for medium range
        base station, **FR2 Category A** and **FR2 Category B**, and also for  **NTN** supported masks. This value is expressed
        in dBm.

        In the case of FR1, this control is considered when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink**,
        :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, and
        :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute to **Medium Range Base Station**. For more
        details please refer to section 6.6.4.2.3 of *3GPP 38.104* specification. In the case of FR2, this control is
        considered when the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**. For more details please
        refer to section 9.7.4.3 of *3GPP 38.104* specification.

        If the :py:attr:`~nirfmxnr.attributes.AttributeID.BAND` attribute is set to any **NTN (Non-Terrestrial
        Network)** band values **254**, **255**, **256**, :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` attribute
        to **FR1**, :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` to **Downlink** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, then the **Rated Output
        Power** **(P\ :sub:`rated, C, SYS**)`\ specifies the sum of rated output powers for all TAB connectors of the carrier
        for the configured :py:attr:`~nirfmxnr.attributes.AttributeID.SATELLITE_ACCESS_NODE_CLASS`. For more details, please
        refer to section 6.6.4.2 of *3GPP 38.108* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the rated output power (P\ :sub:`rated, x`\), which is used only to choose the limit table for medium range
                base station, **FR2 Category A** and **FR2 Category B**, and also for  **NTN** supported masks. This value is expressed
                in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.SEM_COMPONENT_CARRIER_RATED_OUTPUT_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rated_output_power(self, selector_string, value):
        r"""Sets the rated output power (P\ :sub:`rated, x`\), which is used only to choose the limit table for medium range
        base station, **FR2 Category A** and **FR2 Category B**, and also for  **NTN** supported masks. This value is expressed
        in dBm.

        In the case of FR1, this control is considered when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink**,
        :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, and
        :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute to **Medium Range Base Station**. For more
        details please refer to section 6.6.4.2.3 of *3GPP 38.104* specification. In the case of FR2, this control is
        considered when the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute is set to **Downlink** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**. For more details please
        refer to section 9.7.4.3 of *3GPP 38.104* specification.

        If the :py:attr:`~nirfmxnr.attributes.AttributeID.BAND` attribute is set to any **NTN (Non-Terrestrial
        Network)** band values **254**, **255**, **256**, :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` attribute
        to **FR1**, :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` to **Downlink** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, then the **Rated Output
        Power** **(P\ :sub:`rated, C, SYS**)`\ specifies the sum of rated output powers for all TAB connectors of the carrier
        for the configured :py:attr:`~nirfmxnr.attributes.AttributeID.SATELLITE_ACCESS_NODE_CLASS`. For more details, please
        refer to section 6.6.4.2 of *3GPP 38.108* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the rated output power (P\ :sub:`rated, x`\), which is used only to choose the limit table for medium range
                base station, **FR2 Category A** and **FR2 Category B**, and also for  **NTN** supported masks. This value is expressed
                in dBm.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.SEM_COMPONENT_CARRIER_RATED_OUTPUT_POWER.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rated_output_power_array(
        self, selector_string, component_carrier_rated_output_power
    ):
        r"""Configures an array of the rated output power (P\ :sub:`rated`\, x) of the component carrier.

        Use "subblock<*n*>" as the selector string to read results from this method.

        .. note::
           This method is valid when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to
           **Downlink**, :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, and
           :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute to **Medium Range Base Station**. For more
           details please refer to section 6.6.4 of *3GPP 38.104* specification.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.

                Example:

                "subblock0"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            component_carrier_rated_output_power (float):
                This parameter specifies an array of the rated output power (P\ :sub:`rated`\, x), which is used only to choose the
                limit table for medium range base station, **FR2 Category A** and **FR2 Category B**. This value is expressed in dBm.
                This parameter will be considered when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute
                to **Downlink**, :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, and
                :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute to **Medium Range Base Station** or **FR2
                Category A** or **FR2 Category B**. For more details please refer to section 6.6.4 of *3GPP 38.104* specification. The
                default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_rated_output_power_array(
                updated_selector_string, component_carrier_rated_output_power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rated_output_power(self, selector_string, component_carrier_rated_output_power):
        r"""Configures the rated output power (P\ :sub:`rated`\, x) of the component carrier.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" as the selector string to configure this method.

        .. note::
           This method is valid when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to
           **Downlink**, :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, and
           :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute to **Medium Range Base Station**. For more
           details please refer to section 6.6.4 of *3GPP 38.104* specification.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of subblock
                number and carrier number.

                Example:

                "subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            component_carrier_rated_output_power (float):
                This parameter specifies the rated output power (P\ :sub:`rated`\, x), which is used only to choose the limit table for
                medium range base station, **FR2 Category A** and **FR2 Category B**. This value is expressed in dBm. This parameter
                will be considered when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to
                **Downlink**, :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to **Standard**, and
                :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute to **Medium Range Base Station** or **FR2
                Category A** or **FR2 Category B**. For more details please refer to section 6.6.4 and section 9.7.4 of *3GPP 38.104*
                specification. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.sem_configure_rated_output_power(
                updated_selector_string, component_carrier_rated_output_power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
