"""Provides methods to configure the Acp measurement."""

import functools

import nirfmxnr.acp_component_carrier_configuration as component_carrier
import nirfmxnr.attributes as attributes
import nirfmxnr.enums as enums
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


class AcpConfiguration(object):
    """Provides methods to configure the Acp measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the Acp measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.component_carrier = component_carrier.AcpComponentCarrierConfiguration(signal_obj)  # type: ignore

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_configuration_type(self, selector_string):
        r"""Gets the method to configure the carrier and the offset channel settings.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Standard**.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | Standard (0)        | All settings will be 3GPP compliant.                                                                                     |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (1)          | The user can manually configure integration bandwidth and offset frequencies for the ACP measurement.                    |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_29 (2)           | This is an additional requirement according to section 6.5F.2.4.2 of 3GPP 38.101-1 and is applicable only for uplink     |
        |                     | bandwidths of 20 MHz and 40 MHz.                                                                                         |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Standard Rel 16 (3) | All settings will be compliant with 3GPP Specifications, Release 16 and above.                                           |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Standard Rel 18 (4) | All settings will be compliant with 3GPP Specifications, Release 18 and above.                                           |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpChannelConfigurationType):
                Specifies the method to configure the carrier and the offset channel settings.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE.value
            )
            attr_val = enums.AcpChannelConfigurationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_configuration_type(self, selector_string, value):
        r"""Sets the method to configure the carrier and the offset channel settings.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Standard**.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | Standard (0)        | All settings will be 3GPP compliant.                                                                                     |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (1)          | The user can manually configure integration bandwidth and offset frequencies for the ACP measurement.                    |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | NS_29 (2)           | This is an additional requirement according to section 6.5F.2.4.2 of 3GPP 38.101-1 and is applicable only for uplink     |
        |                     | bandwidths of 20 MHz and 40 MHz.                                                                                         |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Standard Rel 16 (3) | All settings will be compliant with 3GPP Specifications, Release 16 and above.                                           |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Standard Rel 18 (4) | All settings will be compliant with 3GPP Specifications, Release 18 and above.                                           |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpChannelConfigurationType, int):
                Specifies the method to configure the carrier and the offset channel settings.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpChannelConfigurationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of a subblock. This value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Integration bandwidth is the span from the left edge of the leftmost carrier to the right edge of the rightmost
        carrier within the subblock. The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the integration bandwidth of a subblock. This value is expressed in Hz.

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
                attributes.AttributeID.ACP_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subblock_integration_bandwidth(self, selector_string, value):
        r"""Sets the integration bandwidth of a subblock. This value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Integration bandwidth is the span from the left edge of the leftmost carrier to the right edge of the rightmost
        carrier within the subblock. The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the integration bandwidth of a subblock. This value is expressed in Hz.

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
                attributes.AttributeID.ACP_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_offset(self, selector_string):
        r"""Gets the offset of the subblock measurement relative to the subblock center. This value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset of the subblock measurement relative to the subblock center. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_SUBBLOCK_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subblock_offset(self, selector_string, value):
        r"""Sets the offset of the subblock measurement relative to the subblock center. This value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset of the subblock measurement relative to the subblock center. This value is expressed in Hz.

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
                updated_selector_string, attributes.AttributeID.ACP_SUBBLOCK_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_utra_offsets(self, selector_string):
        r"""Gets the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
        positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to
        **Standard**  or  **NS_29**  or  **Standard Rel 16**  or  ** Standard Rel 18 **. For uplink ACP measurement in
        frequency range 2-1 and frequency range 2-2, and for downlink ACP measurement, the ACP Num UTRA Offsets has to be 0.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
                positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to
                **Standard**  or  **NS_29**  or  **Standard Rel 16**  or  ** Standard Rel 18 **. For uplink ACP measurement in
                frequency range 2-1 and frequency range 2-2, and for downlink ACP measurement, the ACP Num UTRA Offsets has to be 0.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_UTRA_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_utra_offsets(self, selector_string, value):
        r"""Sets the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
        positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to
        **Standard**  or  **NS_29**  or  **Standard Rel 16**  or  ** Standard Rel 18 **. For uplink ACP measurement in
        frequency range 2-1 and frequency range 2-2, and for downlink ACP measurement, the ACP Num UTRA Offsets has to be 0.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
                positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to
                **Standard**  or  **NS_29**  or  **Standard Rel 16**  or  ** Standard Rel 18 **. For uplink ACP measurement in
                frequency range 2-1 and frequency range 2-2, and for downlink ACP measurement, the ACP Num UTRA Offsets has to be 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NUMBER_OF_UTRA_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_eutra_offsets(self, selector_string):
        r"""Gets the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
        at offset positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is
        set to **Standard** or **NS_29** or **Standard Rel 16** or **Standard Rel 18**. For uplink ACP measurement, and for
        downlink ACP measurement in frequency range 2-1 and frequency range 2-2, this attribute has to be 0.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
                at offset positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is
                set to **Standard** or **NS_29** or **Standard Rel 16** or **Standard Rel 18**. For uplink ACP measurement, and for
                downlink ACP measurement in frequency range 2-1 and frequency range 2-2, this attribute has to be 0.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_EUTRA_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_eutra_offsets(self, selector_string, value):
        r"""Sets the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
        at offset positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is
        set to **Standard** or **NS_29** or **Standard Rel 16** or **Standard Rel 18**. For uplink ACP measurement, and for
        downlink ACP measurement in frequency range 2-1 and frequency range 2-2, this attribute has to be 0.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
                at offset positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is
                set to **Standard** or **NS_29** or **Standard Rel 16** or **Standard Rel 18**. For uplink ACP measurement, and for
                downlink ACP measurement in frequency range 2-1 and frequency range 2-2, this attribute has to be 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NUMBER_OF_EUTRA_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_nr_offsets(self, selector_string):
        r"""Gets the number of NR adjacent channel offsets to be configured at offset positions when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
        **NS_29** or **Standard Rel 16** or **Standard Rel 18**.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of NR adjacent channel offsets to be configured at offset positions when the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
                **NS_29** or **Standard Rel 16** or **Standard Rel 18**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_NR_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_nr_offsets(self, selector_string, value):
        r"""Sets the number of NR adjacent channel offsets to be configured at offset positions when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
        **NS_29** or **Standard Rel 16** or **Standard Rel 18**.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of NR adjacent channel offsets to be configured at offset positions when the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
                **NS_29** or **Standard Rel 16** or **Standard Rel 18**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NUMBER_OF_NR_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_endc_offsets(self, selector_string):
        r"""Gets the number of ENDC adjacent channel offsets to be configured at offset positions when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
        **NS_29** or **Standard Rel 16** or **Standard Rel 18**

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of ENDC adjacent channel offsets to be configured at offset positions when the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
                **NS_29** or **Standard Rel 16** or **Standard Rel 18**

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_ENDC_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_endc_offsets(self, selector_string, value):
        r"""Sets the number of ENDC adjacent channel offsets to be configured at offset positions when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
        **NS_29** or **Standard Rel 16** or **Standard Rel 18**

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is dependent on 3GPP specification.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of ENDC adjacent channel offsets to be configured at offset positions when the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
                **NS_29** or **Standard Rel 16** or **Standard Rel 18**

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NUMBER_OF_ENDC_OFFSETS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_channel_spacing_adjustment(self, selector_string):
        r"""Gets the additional spacing of ACP offset channels at nominal spacing.

        It applies to UL single carrier (FR1), UL contiguous CA, and UL non-contiguous EN-DC signal configurations.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the additional spacing of ACP offset channels at nominal spacing.

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
                attributes.AttributeID.ACP_OFFSET_CHANNEL_SPACING_ADJUSTMENT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_channel_spacing_adjustment(self, selector_string, value):
        r"""Sets the additional spacing of ACP offset channels at nominal spacing.

        It applies to UL single carrier (FR1), UL contiguous CA, and UL non-contiguous EN-DC signal configurations.

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the additional spacing of ACP offset channels at nominal spacing.

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
                attributes.AttributeID.ACP_OFFSET_CHANNEL_SPACING_ADJUSTMENT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_offsets(self, selector_string):
        r"""Gets the number of configured offset channels when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Custom**

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of configured offset channels when the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Custom**

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_offsets(self, selector_string, value):
        r"""Sets the number of configured offset channels when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Custom**

        Use "subblock<*n*>" as the selector string to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of configured offset channels when the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Custom**

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_OFFSETS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_frequency(self, selector_string):
        r"""Gets the offset frequency of an offset channel. This value is expressed in Hz. The offset frequency is computed
        from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
        channel.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 10 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset frequency of an offset channel. This value is expressed in Hz. The offset frequency is computed
                from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
                channel.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_frequency(self, selector_string, value):
        r"""Sets the offset frequency of an offset channel. This value is expressed in Hz. The offset frequency is computed
        from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
        channel.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 10 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset frequency of an offset channel. This value is expressed in Hz. The offset frequency is computed
                from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
                channel.

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
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_sideband(self, selector_string):
        r"""Gets the sideband measured for the offset channel.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is **Both**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
        +--------------+---------------------------------------------------------------------------+
        | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
        +--------------+---------------------------------------------------------------------------+
        | Both (2)     | Configures both the negative and the positive offset segments.            |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpOffsetSideband):
                Specifies the sideband measured for the offset channel.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_SIDEBAND.value
            )
            attr_val = enums.AcpOffsetSideband(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_sideband(self, selector_string, value):
        r"""Sets the sideband measured for the offset channel.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is **Both**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | Neg (0)      | Configures a lower offset segment to the left of the leftmost carrier.    |
        +--------------+---------------------------------------------------------------------------+
        | Pos (1)      | Configures an upper offset segment to the right of the rightmost carrier. |
        +--------------+---------------------------------------------------------------------------+
        | Both (2)     | Configures both the negative and the positive offset segments.            |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpOffsetSideband, int):
                Specifies the sideband measured for the offset channel.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpOffsetSideband else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_SIDEBAND.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of an offset channel. This value is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the integration bandwidth of an offset channel. This value is expressed in Hz.

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
                attributes.AttributeID.ACP_OFFSET_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_integration_bandwidth(self, selector_string, value):
        r"""Sets the integration bandwidth of an offset channel. This value is expressed in Hz.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 9 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the integration bandwidth of an offset channel. This value is expressed in Hz.

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
                attributes.AttributeID.ACP_OFFSET_INTEGRATION_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_auto_bandwidth(self, selector_string):
        r"""Gets whether the measurement computes the RBW.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | The measurement uses the RBW that you specify in the ACP RBW attribute. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                       |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpRbwAutoBandwidth):
                Specifies whether the measurement computes the RBW.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH.value
            )
            attr_val = enums.AcpRbwAutoBandwidth(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_auto_bandwidth(self, selector_string, value):
        r"""Sets whether the measurement computes the RBW.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | The measurement uses the RBW that you specify in the ACP RBW attribute. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                       |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpRbwAutoBandwidth, int):
                Specifies whether the measurement computes the RBW.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpRbwAutoBandwidth else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_bandwidth(self, selector_string):
        r"""Gets the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
        expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30 kHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
                expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_bandwidth(self, selector_string, value):
        r"""Sets the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
        expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30 kHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
                expressed in Hz.

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
                attributes.AttributeID.ACP_RBW_FILTER_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_type(self, selector_string):
        r"""Gets the shape of the RBW filter.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **FFT Based**.

        +---------------+----------------------------------------------------+
        | Name (Value)  | Description                                        |
        +===============+====================================================+
        | FFT Based (0) | No RBW filtering is performed.                     |
        +---------------+----------------------------------------------------+
        | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
        +---------------+----------------------------------------------------+
        | Flat (2)      | An RBW filter with a flat response is applied.     |
        +---------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpRbwFilterType):
                Specifies the shape of the RBW filter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_TYPE.value
            )
            attr_val = enums.AcpRbwFilterType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_type(self, selector_string, value):
        r"""Sets the shape of the RBW filter.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **FFT Based**.

        +---------------+----------------------------------------------------+
        | Name (Value)  | Description                                        |
        +===============+====================================================+
        | FFT Based (0) | No RBW filtering is performed.                     |
        +---------------+----------------------------------------------------+
        | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
        +---------------+----------------------------------------------------+
        | Flat (2)      | An RBW filter with a flat response is applied.     |
        +---------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpRbwFilterType, int):
                Specifies the shape of the RBW filter.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpRbwFilterType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RBW_FILTER_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_auto(self, selector_string):
        r"""Gets whether the measurement sets the sweep time.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the ACP Sweep Time attribute. |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpSweepTimeAuto):
                Specifies whether the measurement sets the sweep time.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_AUTO.value
            )
            attr_val = enums.AcpSweepTimeAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_auto(self, selector_string, value):
        r"""Sets whether the measurement sets the sweep time.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the ACP Sweep Time attribute. |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpSweepTimeAuto, int):
                Specifies whether the measurement sets the sweep time.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpSweepTimeAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_AUTO.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_interval(self, selector_string):
        r"""Gets the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
        **False**. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
                **False**. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_interval(self, selector_string, value):
        r"""Sets the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
        **False**. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
                **False**. This value is expressed in seconds.

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
                updated_selector_string, attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_units(self, selector_string):
        r"""Gets the unit for absolute power.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **dBm**.

        +--------------+-----------------------------------------------------------+
        | Name (Value) | Description                                               |
        +==============+===========================================================+
        | dBm (0)      | Indicates that the absolute power is expressed in dBm.    |
        +--------------+-----------------------------------------------------------+
        | dBm/Hz (1)   | Indicates that the absolute power is expressed in dBm/Hz. |
        +--------------+-----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpPowerUnits):
                Specifies the unit for absolute power.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_POWER_UNITS.value
            )
            attr_val = enums.AcpPowerUnits(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_units(self, selector_string, value):
        r"""Sets the unit for absolute power.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **dBm**.

        +--------------+-----------------------------------------------------------+
        | Name (Value) | Description                                               |
        +==============+===========================================================+
        | dBm (0)      | Indicates that the absolute power is expressed in dBm.    |
        +--------------+-----------------------------------------------------------+
        | dBm/Hz (1)   | Indicates that the absolute power is expressed in dBm/Hz. |
        +--------------+-----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpPowerUnits, int):
                Specifies the unit for absolute power.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpPowerUnits else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_POWER_UNITS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_method(self, selector_string):
        r"""Gets the method for performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
        |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
        |                    | this method to get the best dynamic range. Supported Devices: PXIe 5665/5668R                                            |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sequential FFT (2) | The ACP measurement acquires I/Q samples for a duration specified by the ACP Sweep Time attribute. These samples are     |
        |                    | divided into smaller chunks. The size of each chunk is defined by the ACP Sequential FFT Size attribute, and the FFT is  |
        |                    | computed on each of these chunks. The resultant FFTs are averaged to get the spectrum and is used to compute the ACP.    |
        |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
        |                    | acquisition are not used for the measurement. Use this method to optimize ACP Measurement speed. The accuracy of         |
        |                    | results may be reduced when using this measurement method.                                                               |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpMeasurementMethod):
                Specifies the method for performing the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_METHOD.value
            )
            attr_val = enums.AcpMeasurementMethod(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_method(self, selector_string, value):
        r"""Sets the method for performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
        |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
        |                    | this method to get the best dynamic range. Supported Devices: PXIe 5665/5668R                                            |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sequential FFT (2) | The ACP measurement acquires I/Q samples for a duration specified by the ACP Sweep Time attribute. These samples are     |
        |                    | divided into smaller chunks. The size of each chunk is defined by the ACP Sequential FFT Size attribute, and the FFT is  |
        |                    | computed on each of these chunks. The resultant FFTs are averaged to get the spectrum and is used to compute the ACP.    |
        |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
        |                    | acquisition are not used for the measurement. Use this method to optimize ACP Measurement speed. The accuracy of         |
        |                    | results may be reduced when using this measurement method.                                                               |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpMeasurementMethod, int):
                Specifies the method for performing the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpMeasurementMethod else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_METHOD.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_mode(self, selector_string):
        r"""Gets whether the noise calibration and measurement is performed manually by the user or automatically by RFmx.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | When you set the ACP Meas Mode attribute to Noise Calibrate, you can initiate instrument noise calibration for ACP       |
        |              | manually. When you set the ACP Meas Mode attribute to Measure, you can initiate the ACP measurement manually.            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | When you set the ACP Noise Comp Enabled attribute to True, RFmx sets Input Isolation Enabled attribute to Enabled and    |
        |              | calibrates the instrument noise in the current state of the instrument. Next, RFmx resets the Input Isolation Enabled    |
        |              | attribute and performs the ACP measurement, including compensation for the noise contribution of the instrument. RFmx    |
        |              | skips noise calibration in this mode if valid noise calibration data is already cached.                                  |
        |              | When you set the ACP Noise Comp Enabled attribute to False, RFmx does not calibrate instrument noise and performs the    |
        |              | ACP measurement without compensating for the noise contribution of the instrument.                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCalibrationMode):
                Specifies whether the noise calibration and measurement is performed manually by the user or automatically by RFmx.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE.value
            )
            attr_val = enums.AcpNoiseCalibrationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_mode(self, selector_string, value):
        r"""Sets whether the noise calibration and measurement is performed manually by the user or automatically by RFmx.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | When you set the ACP Meas Mode attribute to Noise Calibrate, you can initiate instrument noise calibration for ACP       |
        |              | manually. When you set the ACP Meas Mode attribute to Measure, you can initiate the ACP measurement manually.            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | When you set the ACP Noise Comp Enabled attribute to True, RFmx sets Input Isolation Enabled attribute to Enabled and    |
        |              | calibrates the instrument noise in the current state of the instrument. Next, RFmx resets the Input Isolation Enabled    |
        |              | attribute and performs the ACP measurement, including compensation for the noise contribution of the instrument. RFmx    |
        |              | skips noise calibration in this mode if valid noise calibration data is already cached.                                  |
        |              | When you set the ACP Noise Comp Enabled attribute to False, RFmx does not calibrate instrument noise and performs the    |
        |              | ACP measurement without compensating for the noise contribution of the instrument.                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCalibrationMode, int):
                Specifies whether the noise calibration and measurement is performed manually by the user or automatically by RFmx.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCalibrationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_averaging_auto(self, selector_string):
        r"""Gets whether RFmx automatically computes the averaging count used for instrument noise calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | RFmx uses the averaging count that you set for the ACP Noise Cal Averaging Count attribute.                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | When you set the ACP Meas Method attribute to Normal or Sequential FFT, RFmx uses a noise calibration averaging count    |
        |              | of 32. When you set the ACP Meas Method attribute to Dynamic Range and the sweep time is less than 5 ms, RFmx uses a     |
        |              | noise calibration averaging count of 15. When you set the ACP Meas Method to Dynamic Range and the sweep time is         |
        |              | greater than or equal to 5 ms, RFmx uses a noise calibration averaging count of 5.                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCalibrationAveragingAuto):
                Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO.value,
            )
            attr_val = enums.AcpNoiseCalibrationAveragingAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_averaging_auto(self, selector_string, value):
        r"""Sets whether RFmx automatically computes the averaging count used for instrument noise calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | RFmx uses the averaging count that you set for the ACP Noise Cal Averaging Count attribute.                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | When you set the ACP Meas Method attribute to Normal or Sequential FFT, RFmx uses a noise calibration averaging count    |
        |              | of 32. When you set the ACP Meas Method attribute to Dynamic Range and the sweep time is less than 5 ms, RFmx uses a     |
        |              | noise calibration averaging count of 15. When you set the ACP Meas Method to Dynamic Range and the sweep time is         |
        |              | greater than or equal to 5 ms, RFmx uses a noise calibration averaging count of 5.                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCalibrationAveragingAuto, int):
                Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCalibrationAveragingAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_averaging_count(self, selector_string):
        r"""Gets the averaging count used for noise calibration when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 32.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the averaging count used for noise calibration when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_COUNT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_averaging_count(self, selector_string, value):
        r"""Sets the averaging count used for noise calibration when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 32.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the averaging count used for noise calibration when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_COUNT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_enabled(self, selector_string):
        r"""Gets whether RFmx compensates for the instrument noise when performing the measurement when you set
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set ACP Noise
        Cal Mode to **Manual** and :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_MODE` attribute to **Measure**

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                 |
        +==============+=============================================================================================================+
        | False (0)    | Disables noise compensation.                                                                                |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | True (1)     | Enables noise compensation.                                                                                 |
        |              | Supported Devices: PXIe-5663/5665/5668R, PXIe-5830/5831/5832/5842/5860                                      |
        +--------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCompensationEnabled):
                Specifies whether RFmx compensates for the instrument noise when performing the measurement when you set
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set ACP Noise
                Cal Mode to **Manual** and :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_MODE` attribute to **Measure**

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NOISE_COMPENSATION_ENABLED.value
            )
            attr_val = enums.AcpNoiseCompensationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_enabled(self, selector_string, value):
        r"""Sets whether RFmx compensates for the instrument noise when performing the measurement when you set
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set ACP Noise
        Cal Mode to **Manual** and :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_MODE` attribute to **Measure**

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                 |
        +==============+=============================================================================================================+
        | False (0)    | Disables noise compensation.                                                                                |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | True (1)     | Enables noise compensation.                                                                                 |
        |              | Supported Devices: PXIe-5663/5665/5668R, PXIe-5830/5831/5832/5842/5860                                      |
        +--------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCompensationEnabled, int):
                Specifies whether RFmx compensates for the instrument noise when performing the measurement when you set
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or when you set ACP Noise
                Cal Mode to **Manual** and :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_MODE` attribute to **Measure**

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCompensationEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_COMPENSATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_type(self, selector_string):
        r"""Gets the noise compensation type.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Analyzer and Termination**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | Analyzer and Termination (0) | Compensates for noise from the analyzer and the 50-ohm termination. The measured power values are in excess of the       |
        |                              | thermal noise floor.                                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Analyzer Only (1)            | Compensates only for analyzer noise only.                                                                                |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpNoiseCompensationType):
                Specifies the noise compensation type.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NOISE_COMPENSATION_TYPE.value
            )
            attr_val = enums.AcpNoiseCompensationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_type(self, selector_string, value):
        r"""Sets the noise compensation type.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Analyzer and Termination**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | Analyzer and Termination (0) | Compensates for noise from the analyzer and the 50-ohm termination. The measured power values are in excess of the       |
        |                              | thermal noise floor.                                                                                                     |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Analyzer Only (1)            | Compensates only for analyzer noise only.                                                                                |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpNoiseCompensationType, int):
                Specifies the noise compensation type.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpNoiseCompensationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NOISE_COMPENSATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The ACP measurement uses the value of the ACP Averaging Count attribute as the number of acquisitions over which the     |
        |              | ACP measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAveragingEnabled):
                Specifies whether to enable averaging for the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_ENABLED.value
            )
            attr_val = enums.AcpAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The ACP measurement uses the value of the ACP Averaging Count attribute as the number of acquisitions over which the     |
        |              | ACP measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAveragingEnabled, int):
                Specifies whether to enable averaging for the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_type(self, selector_string):
        r"""Gets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Default value is **RMS**.

        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                  |
        +==============+==============================================================================================================+
        | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor. |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Scalar (2)   | The square root of the power spectrum is averaged.                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.         |
        +--------------+--------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAveragingType):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
                measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_TYPE.value
            )
            attr_val = enums.AcpAveragingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_type(self, selector_string, value):
        r"""Sets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Default value is **RMS**.

        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                  |
        +==============+==============================================================================================================+
        | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor. |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                       |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Scalar (2)   | The square root of the power spectrum is averaged.                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.           |
        +--------------+--------------------------------------------------------------------------------------------------------------+
        | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.         |
        +--------------+--------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAveragingType, int):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
                measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAveragingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_mode(self, selector_string):
        r"""Gets whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+-----------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                       |
        +===========================+===================================================================================+
        | Measure (0)               | Performs the ACP measurement on the acquired signal.                              |
        +---------------------------+-----------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | Performs manual noise calibration of the signal analyzer for the ACP measurement. |
        +---------------------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpMeasurementMode):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_MODE.value
            )
            attr_val = enums.AcpMeasurementMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_mode(self, selector_string, value):
        r"""Sets whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+-----------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                       |
        +===========================+===================================================================================+
        | Measure (0)               | Performs the ACP measurement on the acquired signal.                              |
        +---------------------------+-----------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | Performs manual noise calibration of the signal analyzer for the ACP measurement. |
        +---------------------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpMeasurementMode, int):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpMeasurementMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window(self, selector_string):
        r"""Gets the FFT window type to be used to reduce spectral leakage.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Flat Top**.

        +---------------------+----------------------------------------------------------------+
        | Name (Value)        | Description                                                    |
        +=====================+================================================================+
        | None (0)            | No spectral leakage.                                           |
        +---------------------+----------------------------------------------------------------+
        | Flat Top (1)        | Spectral leakage is reduced using flat top window type.        |
        +---------------------+----------------------------------------------------------------+
        | Hanning (2)         | Spectral leakage is reduced using Hanning window type.         |
        +---------------------+----------------------------------------------------------------+
        | Hamming (3)         | Spectral leakage is reduced using Hamming window type.         |
        +---------------------+----------------------------------------------------------------+
        | Gaussian (4)        | Spectral leakage is reduced using Gaussian window type.        |
        +---------------------+----------------------------------------------------------------+
        | Blackman (5)        | Spectral leakage is reduced using Blackman window type.        |
        +---------------------+----------------------------------------------------------------+
        | Blackman-Harris (6) | Spectral leakage is reduced using Blackman-Harris window type. |
        +---------------------+----------------------------------------------------------------+
        | Kaiser-Bessel (7)   | Spectral leakage is reduced using Kaiser-Bessel window type.   |
        +---------------------+----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpFftWindow):
                Specifies the FFT window type to be used to reduce spectral leakage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_FFT_WINDOW.value
            )
            attr_val = enums.AcpFftWindow(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window(self, selector_string, value):
        r"""Sets the FFT window type to be used to reduce spectral leakage.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Flat Top**.

        +---------------------+----------------------------------------------------------------+
        | Name (Value)        | Description                                                    |
        +=====================+================================================================+
        | None (0)            | No spectral leakage.                                           |
        +---------------------+----------------------------------------------------------------+
        | Flat Top (1)        | Spectral leakage is reduced using flat top window type.        |
        +---------------------+----------------------------------------------------------------+
        | Hanning (2)         | Spectral leakage is reduced using Hanning window type.         |
        +---------------------+----------------------------------------------------------------+
        | Hamming (3)         | Spectral leakage is reduced using Hamming window type.         |
        +---------------------+----------------------------------------------------------------+
        | Gaussian (4)        | Spectral leakage is reduced using Gaussian window type.        |
        +---------------------+----------------------------------------------------------------+
        | Blackman (5)        | Spectral leakage is reduced using Blackman window type.        |
        +---------------------+----------------------------------------------------------------+
        | Blackman-Harris (6) | Spectral leakage is reduced using Blackman-Harris window type. |
        +---------------------+----------------------------------------------------------------+
        | Kaiser-Bessel (7)   | Spectral leakage is reduced using Kaiser-Bessel window type.   |
        +---------------------+----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpFftWindow, int):
                Specifies the FFT window type to be used to reduce spectral leakage.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpFftWindow else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_FFT_WINDOW.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_overlap_mode(self, selector_string):
        r"""Gets the overlap mode when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
        attribute to **Sequential FFT**. In the Sequential FFT method, the measurement divides all the acquired samples into
        smaller FFT chunks of equal size. The FFT is then computed for each chunk. The resultant FFTs are averaged to get the
        spectrum used to compute the ACP.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Disabled (0)     | Disables the overlap between the FFT chunks.                                                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Automatic (1)    | Measurement sets the overlap based on the value you have set for the ACP FFT Window attribute. When you set the ACP FFT  |
        |                  | Window attribute to any value other than None, the number of overlapped samples between consecutive chunks is set to     |
        |                  | 50% of the value of the ACP Sequential FFT Size attribute. When you set the ACP FFT Window attribute to None, the        |
        |                  | chunks are not overlapped and the overlap is set to 0%.                                                                  |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (2) | Measurement uses the overlap that you specify in the ACP FFT Overlap attribute.                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpFftOverlapMode):
                Specifies the overlap mode when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
                attribute to **Sequential FFT**. In the Sequential FFT method, the measurement divides all the acquired samples into
                smaller FFT chunks of equal size. The FFT is then computed for each chunk. The resultant FFTs are averaged to get the
                spectrum used to compute the ACP.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP_MODE.value
            )
            attr_val = enums.AcpFftOverlapMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_overlap_mode(self, selector_string, value):
        r"""Sets the overlap mode when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
        attribute to **Sequential FFT**. In the Sequential FFT method, the measurement divides all the acquired samples into
        smaller FFT chunks of equal size. The FFT is then computed for each chunk. The resultant FFTs are averaged to get the
        spectrum used to compute the ACP.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Disabled (0)     | Disables the overlap between the FFT chunks.                                                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Automatic (1)    | Measurement sets the overlap based on the value you have set for the ACP FFT Window attribute. When you set the ACP FFT  |
        |                  | Window attribute to any value other than None, the number of overlapped samples between consecutive chunks is set to     |
        |                  | 50% of the value of the ACP Sequential FFT Size attribute. When you set the ACP FFT Window attribute to None, the        |
        |                  | chunks are not overlapped and the overlap is set to 0%.                                                                  |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (2) | Measurement uses the overlap that you specify in the ACP FFT Overlap attribute.                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpFftOverlapMode, int):
                Specifies the overlap mode when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
                attribute to **Sequential FFT**. In the Sequential FFT method, the measurement divides all the acquired samples into
                smaller FFT chunks of equal size. The FFT is then computed for each chunk. The resultant FFTs are averaged to get the
                spectrum used to compute the ACP.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpFftOverlapMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_overlap(self, selector_string):
        r"""Gets the samples to overlap between the consecutive chunks as a percentage of the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**. This value is expressed
        as a percentage.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the samples to overlap between the consecutive chunks as a percentage of the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**. This value is expressed
                as a percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_overlap(self, selector_string, value):
        r"""Sets the samples to overlap between the consecutive chunks as a percentage of the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**. This value is expressed
        as a percentage.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the samples to overlap between the consecutive chunks as a percentage of the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**. This value is expressed
                as a percentage.

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
                updated_selector_string, attributes.AttributeID.ACP_FFT_OVERLAP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_if_output_power_offset_auto(self, selector_string):
        r"""Gets whether the measurement computes an appropriate IF output power level offset for the offset channels to
        improve the dynamic range of the ACP measurement. This attribute is applicable only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement sets the IF output power level offset using the values of the ACP Near IF Output Pwr Offset (dB) and     |
        |              | ACP Far IF Output Pwr Offset (dB) attributes.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement automatically computes an IF output power level offset for the offset channels to improve the dynamic    |
        |              | range of the ACP measurement.                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpIFOutputPowerOffsetAuto):
                Specifies whether the measurement computes an appropriate IF output power level offset for the offset channels to
                improve the dynamic range of the ACP measurement. This attribute is applicable only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO.value,
            )
            attr_val = enums.AcpIFOutputPowerOffsetAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_if_output_power_offset_auto(self, selector_string, value):
        r"""Sets whether the measurement computes an appropriate IF output power level offset for the offset channels to
        improve the dynamic range of the ACP measurement. This attribute is applicable only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement sets the IF output power level offset using the values of the ACP Near IF Output Pwr Offset (dB) and     |
        |              | ACP Far IF Output Pwr Offset (dB) attributes.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement automatically computes an IF output power level offset for the offset channels to improve the dynamic    |
        |              | range of the ACP measurement.                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpIFOutputPowerOffsetAuto, int):
                Specifies whether the measurement computes an appropriate IF output power level offset for the offset channels to
                improve the dynamic range of the ACP measurement. This attribute is applicable only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpIFOutputPowerOffsetAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_near_if_output_power_offset(self, selector_string):
        r"""Gets the offset that is needed to adjust the IF output power levels for the offset channels that are near the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are near the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_NEAR_IF_OUTPUT_POWER_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_near_if_output_power_offset(self, selector_string, value):
        r"""Sets the offset that is needed to adjust the IF output power levels for the offset channels that are near the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are near the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_NEAR_IF_OUTPUT_POWER_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_far_if_output_power_offset(self, selector_string):
        r"""Gets the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 20.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_FAR_IF_OUTPUT_POWER_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_far_if_output_power_offset(self, selector_string, value):
        r"""Sets the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
        carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 20.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
                carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.

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
                attributes.AttributeID.ACP_FAR_IF_OUTPUT_POWER_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sequential_fft_size(self, selector_string):
        r"""Gets the number of bins to be used for FFT computation, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 512.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of bins to be used for FFT computation, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sequential_fft_size(self, selector_string, value):
        r"""Sets the number of bins to be used for FFT computation, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 512.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of bins to be used for FFT computation, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_amplitude_correction_type(self, selector_string):
        r"""Gets whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
        the RF center frequency, or at the individual frequency bins. Use the
        :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
        attenuation table.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RF Center Frequency**.

        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)               | Description                                                                                                              |
        +============================+==========================================================================================================================+
        | RF Center Frequency (0)    | All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the  |
        |                            | RF center frequency.                                                                                                     |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Spectrum Frequency Bin (1) | An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that     |
        |                            | frequency.                                                                                                               |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAmplitudeCorrectionType):
                Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
                the RF center frequency, or at the individual frequency bins. Use the
                :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
                attenuation table.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AMPLITUDE_CORRECTION_TYPE.value
            )
            attr_val = enums.AcpAmplitudeCorrectionType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_amplitude_correction_type(self, selector_string, value):
        r"""Sets whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
        the RF center frequency, or at the individual frequency bins. Use the
        :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
        attenuation table.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RF Center Frequency**.

        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)               | Description                                                                                                              |
        +============================+==========================================================================================================================+
        | RF Center Frequency (0)    | All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the  |
        |                            | RF center frequency.                                                                                                     |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Spectrum Frequency Bin (1) | An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that     |
        |                            | frequency.                                                                                                               |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAmplitudeCorrectionType, int):
                Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
                the RF center frequency, or at the individual frequency bins. Use the
                :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
                attenuation table.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAmplitudeCorrectionType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_AMPLITUDE_CORRECTION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the ACP measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size, system resources, data
        availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the maximum number of threads used for parallelism for the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the ACP measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size, system resources, data
        availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of threads used for parallelism for the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        r"""Configures averaging for the ACP measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.AcpAveragingEnabled, int):
                This parameter specifies whether to enable averaging for the measurement. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the Averaging Count    |
                |              | parameter.                                                                                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            averaging_count (int):
                This parameter specifies the number of acquisitions used for averaging when you set the **Averaging Enabled** parameter
                to **True**. The default value is 10.

            averaging_type (enums.AcpAveragingType, int):
                This parameter specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used
                for the measurement. The default value is **RMS**.

                +--------------+--------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                  |
                +==============+==============================================================================================================+
                | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor. |
                +--------------+--------------------------------------------------------------------------------------------------------------+
                | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                       |
                +--------------+--------------------------------------------------------------------------------------------------------------+
                | Scalar (2)   | The square root of the power spectrum is averaged.                                                           |
                +--------------+--------------------------------------------------------------------------------------------------------------+
                | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.           |
                +--------------+--------------------------------------------------------------------------------------------------------------+
                | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.         |
                +--------------+--------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            averaging_enabled = (
                averaging_enabled.value
                if type(averaging_enabled) is enums.AcpAveragingEnabled
                else averaging_enabled
            )
            averaging_type = (
                averaging_type.value
                if type(averaging_type) is enums.AcpAveragingType
                else averaging_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count, averaging_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_method(self, selector_string, measurement_method):
        r"""Configures the method for performing the ACP measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_method (enums.AcpMeasurementMethod, int):
                This parameter specifies the method for performing the ACP measurement. The default value is **Normal**.

                +--------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)       | Description                                                                                                              |
                +====================+==========================================================================================================================+
                | Normal (0)         | The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this        |
                |                    | method when measurement speed is desirable over higher dynamic range.                                                    |
                +--------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Dynamic Range (1)  | The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use   |
                |                    | this method to get the best dynamic range. Supported Devices:PXIe-5665/5668R                                             |
                +--------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Sequential FFT (2) | The ACP measurement acquires I/Q samples for a duration specified by the ACP Sweep Time attribute. These samples are     |
                |                    | divided into smaller chunks. The size of each chunk is defined by the ACP Sequential FFT Size attribute, and the FFT is  |
                |                    | computed on each of these chunks. The resultant FFTs are averaged to get the spectrum and is used to compute the ACP.    |
                |                    | If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of the        |
                |                    | acquisition are not used for the measurement. Use this method to optimize ACP Measurement speed. The accuracy of         |
                |                    | results may be reduced when using this measurement method.                                                               |
                +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurement_method = (
                measurement_method.value
                if type(measurement_method) is enums.AcpMeasurementMethod
                else measurement_method
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_measurement_method(
                updated_selector_string, measurement_method
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        r"""Configures compensation of the channel powers for the inherent noise floor of the signal analyzer.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            noise_compensation_enabled (enums.AcpNoiseCompensationEnabled, int):
                This parameter specifies whether to enable compensation of the channel powers for the inherent noise floor of the
                signal analyzer. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Disables compensation of the channel powers for the noise floor of the signal analyzer.                                  |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Enables compensation of the channel powers for the noise floor of the signal analyzer. The noise floor of the signal     |
                |              | analyzer is measured for the RF path used by the ACP measurement and cached for future use.                              |
                |              | If signal analyzer or measurement parameters change, noise floors are remeasured.                                        |
                |              | Supported Devices: PXIe-5663/5665/5668R, PXIe-5830/5831/5832/5842/5860                                                   |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            noise_compensation_enabled = (
                noise_compensation_enabled.value
                if type(noise_compensation_enabled) is enums.AcpNoiseCompensationEnabled
                else noise_compensation_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_noise_compensation_enabled(
                updated_selector_string, noise_compensation_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_endc_offsets(self, selector_string, number_of_endc_offsets):
        r"""Configures the number of ENDC adjacent channels of the subblock.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.  The default is
                "subblock0".

                Example:

                "subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            number_of_endc_offsets (int):
                This parameter specifies the number of ENDC adjacent channel offsets to be configured at offset positions. The default
                value is dependent on 3GPP specification.

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
            error_code = self._interpreter.acp_configure_number_of_endc_offsets(
                updated_selector_string, number_of_endc_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_eutra_offsets(self, selector_string, number_of_eutra_offsets):
        r"""Configures the number of E-UTRA adjacent channels of the subblock.

        Use "subblock<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.

                Example:

                "subblock0"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            number_of_eutra_offsets (int):
                This parameter specifies the number of E-UTRA adjacent channel offsets to be configured at offset positions. For
                downlink ACP measurement in frequency range 2, and for uplink ACP measurement, this parameter has to be 0. The default
                value is dependent on 3GPP specification.

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
            error_code = self._interpreter.acp_configure_number_of_eutra_offsets(
                updated_selector_string, number_of_eutra_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_nr_offsets(self, selector_string, number_of_nr_offsets):
        r"""Configures the number of NR adjacent channels of the subblock.

        Use "subblock<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.

                Example:

                "subblock0"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            number_of_nr_offsets (int):
                This parameter specifies the number of NR adjacent channel offsets to be configured at offset positions. The default
                value is dependent on 3GPP specification.

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
            error_code = self._interpreter.acp_configure_number_of_nr_offsets(
                updated_selector_string, number_of_nr_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_utra_offsets(self, selector_string, number_of_utra_offsets):
        r"""Configures the number of UTRA adjacent channels of the subblock.

        Use "subblock<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.

                Example:

                "subblock0"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            number_of_utra_offsets (int):
                This parameter  specifies the number of UTRA adjacent channel offsets to be configured at offset positions. For uplink
                ACP measurement in frequency range 2, and for downlink ACP measurement, this parameter has to be 0. The default value
                is dependent on 3GPP specification.

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
            error_code = self._interpreter.acp_configure_number_of_utra_offsets(
                updated_selector_string, number_of_utra_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        r"""Configures the resolution bandwidth (RBW) filter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            rbw_auto (enums.AcpRbwAutoBandwidth, int):
                This parameter specifies whether the measurement computes the RBW. The default value is **True**.

                +--------------+---------------------------------------------------------------------+
                | Name (Value) | Description                                                         |
                +==============+=====================================================================+
                | False (0)    | The measurement uses the RBW that you specify in the RBW parameter. |
                +--------------+---------------------------------------------------------------------+
                | True (1)     | The measurement computes the RBW.                                   |
                +--------------+---------------------------------------------------------------------+

            rbw (float):
                This parameter specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the **RBW
                Auto** parameter to **False**. This value is expressed in Hz. The default value is 30 kHz.

            rbw_filter_type (enums.AcpRbwFilterType, int):
                This parameter specifies the shape of the RBW filter. The default value is **FFT Based**.

                +---------------+----------------------------------------------------+
                | Name (Value)  | Description                                        |
                +===============+====================================================+
                | FFT Based (0) | No RBW filtering is performed.                     |
                +---------------+----------------------------------------------------+
                | Gaussian (1)  | An RBW filter with a Gaussian response is applied. |
                +---------------+----------------------------------------------------+
                | Flat (2)      | An RBW filter with a flat response is applied.     |
                +---------------+----------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            rbw_auto = rbw_auto.value if type(rbw_auto) is enums.AcpRbwAutoBandwidth else rbw_auto
            rbw_filter_type = (
                rbw_filter_type.value
                if type(rbw_filter_type) is enums.AcpRbwFilterType
                else rbw_filter_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_rbw_filter(
                updated_selector_string, rbw_auto, rbw, rbw_filter_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        r"""Configures the sweep time.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            sweep_time_auto (enums.AcpSweepTimeAuto, int):
                This parameter specifies whether the measurement sets the sweep time. The default value is **True**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement uses the sweep time that you specify in the Sweep Time Interval parameter.                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement calculates the sweep time internally. For DL, the sweep time is calculated based on the value of the     |
                |              | OBW RBW attribute, and for UL, it uses a sweep time of 1 ms.                                                             |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            sweep_time_interval (float):
                This parameter specifies the sweep time when you set the **Sweep Time Auto** parameter to **False**. This value is
                expressed in seconds. The default value is 1 ms.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            sweep_time_auto = (
                sweep_time_auto.value
                if type(sweep_time_auto) is enums.AcpSweepTimeAuto
                else sweep_time_auto
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_sweep_time(
                updated_selector_string, sweep_time_auto, sweep_time_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_power_units(self, selector_string, power_units):
        r"""Configures the unit for absolute power.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            power_units (enums.AcpPowerUnits, int):
                This parameter specifies the unit of absolute power. The default value is **dBm**.

                +--------------+-----------------------------------------------------------+
                | Name (Value) | Description                                               |
                +==============+===========================================================+
                | dBm (0)      | Indicates that the absolute power is expressed in dBm.    |
                +--------------+-----------------------------------------------------------+
                | dBm/Hz (1)   | Indicates that the absolute power is expressed in dBm/Hz. |
                +--------------+-----------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            power_units = (
                power_units.value if type(power_units) is enums.AcpPowerUnits else power_units
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_power_units(
                updated_selector_string, power_units
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def validate_noise_calibration_data(self, selector_string):
        r"""Indicates whether the ACP noise calibration data is valid for the configuration specified by the signal name in the
        **Selector String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (noise_calibration_data_valid, error_code):

            noise_calibration_data_valid (enums.AcpNoiseCalibrationDataValid):
                This parameter returns whether the calibration data is valid.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Returns false if the calibration data is not present for the specified configuration or if the difference between the    |
                |              | current device temperature and the calibration temperature exceeds the [-5 °C, 5 °C] range.                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Returns true if the calibration data is present for the configuration specified by the signal name in the Selector       |
                |              | String parameter.                                                                                                        |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            noise_calibration_data_valid, error_code = (
                self._interpreter.acp_validate_noise_calibration_data(updated_selector_string)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return noise_calibration_data_valid, error_code
