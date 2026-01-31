""""""

import functools

import nirfmxnr.attributes as attributes
import nirfmxnr.enums as enums
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


class ComponentCarrier(object):
    """"""

    def __init__(self, signal_obj):
        """"""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_number_of_component_carriers(self, selector_string):
        r"""Gets the number of component carriers configured within a subblock. Set this attribute to 1 for single carrier.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of component carriers configured within a subblock. Set this attribute to 1 for single carrier.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_COMPONENT_CARRIERS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_component_carriers(self, selector_string, value):
        r"""Sets the number of component carriers configured within a subblock. Set this attribute to 1 for single carrier.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of component carriers configured within a subblock. Set this attribute to 1 for single carrier.

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
                attributes.AttributeID.NUMBER_OF_COMPONENT_CARRIERS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_test_model(self, selector_string):
        r"""Gets the NR test model type when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
        section 4.9.2 of the *3GPP 38.141* specification for more information regarding test model configurations.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **TM1.1**.

        +--------------+-----------------------------------+
        | Name (Value) | Description                       |
        +==============+===================================+
        | TM1.1 (0)    | Specifies a TM1.1 NR test model.  |
        +--------------+-----------------------------------+
        | TM1.2 (1)    | Specifies a TM1.2 NR test model.  |
        +--------------+-----------------------------------+
        | TM2 (2)      | Specifies a TM2 NR test model.    |
        +--------------+-----------------------------------+
        | TM2a (3)     | Specifies a TM2a NR test model.   |
        +--------------+-----------------------------------+
        | TM3.1 (4)    | Specifies a TM3.1 NR test model.  |
        +--------------+-----------------------------------+
        | TM3.1a (5)   | Specifies a TM3.1a NR test model. |
        +--------------+-----------------------------------+
        | TM3.2 (6)    | Specifies a TM3.2 NR test model.  |
        +--------------+-----------------------------------+
        | TM3.3 (7)    | Specifies a TM3.3 NR test model.  |
        +--------------+-----------------------------------+
        | TM2b (8)     | Specifies a TM2b NR test model.   |
        +--------------+-----------------------------------+
        | TM3.1b (9)   | Specifies a TM3.1b NR test model. |
        +--------------+-----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkTestModel):
                Specifies the NR test model type when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
                section 4.9.2 of the *3GPP 38.141* specification for more information regarding test model configurations.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DOWNLINK_TEST_MODEL.value
            )
            attr_val = enums.DownlinkTestModel(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_test_model(self, selector_string, value):
        r"""Sets the NR test model type when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
        section 4.9.2 of the *3GPP 38.141* specification for more information regarding test model configurations.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **TM1.1**.

        +--------------+-----------------------------------+
        | Name (Value) | Description                       |
        +==============+===================================+
        | TM1.1 (0)    | Specifies a TM1.1 NR test model.  |
        +--------------+-----------------------------------+
        | TM1.2 (1)    | Specifies a TM1.2 NR test model.  |
        +--------------+-----------------------------------+
        | TM2 (2)      | Specifies a TM2 NR test model.    |
        +--------------+-----------------------------------+
        | TM2a (3)     | Specifies a TM2a NR test model.   |
        +--------------+-----------------------------------+
        | TM3.1 (4)    | Specifies a TM3.1 NR test model.  |
        +--------------+-----------------------------------+
        | TM3.1a (5)   | Specifies a TM3.1a NR test model. |
        +--------------+-----------------------------------+
        | TM3.2 (6)    | Specifies a TM3.2 NR test model.  |
        +--------------+-----------------------------------+
        | TM3.3 (7)    | Specifies a TM3.3 NR test model.  |
        +--------------+-----------------------------------+
        | TM2b (8)     | Specifies a TM2b NR test model.   |
        +--------------+-----------------------------------+
        | TM3.1b (9)   | Specifies a TM3.1b NR test model. |
        +--------------+-----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkTestModel, int):
                Specifies the NR test model type when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` attribute to **Test Model**. Refer to
                section 4.9.2 of the *3GPP 38.141* specification for more information regarding test model configurations.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkTestModel else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.DOWNLINK_TEST_MODEL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_test_model_modulation_type(self, selector_string):
        r"""Gets the modulation type to be used with the selected test model. Selecting the modulation type is supported only
        for test models *NR-FR2-TM3.1* and *NR-FR2-TM2*.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Standard**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | Standard (0) | Specifies a standard modulation scheme. |
        +--------------+-----------------------------------------+
        | QPSK (1)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (2)   | Specifies a 16 QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (3)   | Specifies a 64 QAM modulation scheme.   |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkTestModelModulationType):
                Specifies the modulation type to be used with the selected test model. Selecting the modulation type is supported only
                for test models *NR-FR2-TM3.1* and *NR-FR2-TM2*.

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
                attributes.AttributeID.DOWNLINK_TEST_MODEL_MODULATION_TYPE.value,
            )
            attr_val = enums.DownlinkTestModelModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_test_model_modulation_type(self, selector_string, value):
        r"""Sets the modulation type to be used with the selected test model. Selecting the modulation type is supported only
        for test models *NR-FR2-TM3.1* and *NR-FR2-TM2*.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Standard**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | Standard (0) | Specifies a standard modulation scheme. |
        +--------------+-----------------------------------------+
        | QPSK (1)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (2)   | Specifies a 16 QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (3)   | Specifies a 64 QAM modulation scheme.   |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkTestModelModulationType, int):
                Specifies the modulation type to be used with the selected test model. Selecting the modulation type is supported only
                for test models *NR-FR2-TM3.1* and *NR-FR2-TM2*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkTestModelModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_TEST_MODEL_MODULATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_test_model_duplex_scheme(self, selector_string):
        r"""Gets the duplexing technique of the signal being measured. Refer to section 4.9.2 of *3GPP 38.141* specification
        for more information regarding test model configurations based on duplex scheme.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **FDD**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | FDD (0)      | Specifies that the duplexing technique is frequency-division duplexing. |
        +--------------+-------------------------------------------------------------------------+
        | TDD (1)      | Specifies that the duplexing technique is time-division duplexing.      |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkTestModelDuplexScheme):
                Specifies the duplexing technique of the signal being measured. Refer to section 4.9.2 of *3GPP 38.141* specification
                for more information regarding test model configurations based on duplex scheme.

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
                attributes.AttributeID.DOWNLINK_TEST_MODEL_DUPLEX_SCHEME.value,
            )
            attr_val = enums.DownlinkTestModelDuplexScheme(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_test_model_duplex_scheme(self, selector_string, value):
        r"""Sets the duplexing technique of the signal being measured. Refer to section 4.9.2 of *3GPP 38.141* specification
        for more information regarding test model configurations based on duplex scheme.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **FDD**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | FDD (0)      | Specifies that the duplexing technique is frequency-division duplexing. |
        +--------------+-------------------------------------------------------------------------+
        | TDD (1)      | Specifies that the duplexing technique is time-division duplexing.      |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkTestModelDuplexScheme, int):
                Specifies the duplexing technique of the signal being measured. Refer to section 4.9.2 of *3GPP 38.141* specification
                for more information regarding test model configurations based on duplex scheme.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DownlinkTestModelDuplexScheme else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_TEST_MODEL_DUPLEX_SCHEME.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rated_trp(self, selector_string):
        r"""Gets the rated carrier TRP output power. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the rated carrier TRP output power. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.RATED_TRP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rated_trp(self, selector_string, value):
        r"""Sets the rated carrier TRP output power. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the rated carrier TRP output power. This value is expressed in dBm.

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
                updated_selector_string, attributes.AttributeID.RATED_TRP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rated_eirp(self, selector_string):
        r"""Gets the rated carrier EIRP output power. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the rated carrier EIRP output power. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.RATED_EIRP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rated_eirp(self, selector_string, value):
        r"""Sets the rated carrier EIRP output power. This value is expressed in dBm.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the rated carrier EIRP output power. This value is expressed in dBm.

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
                updated_selector_string, attributes.AttributeID.RATED_EIRP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth(self, selector_string):
        r"""Gets the channel bandwidth of the signal being measured. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **100M**. Valid values for frequency range 1 are from **3M** to **100M**. Valid values for
        frequency range 2-1 are **50M**, **100M**, **200M**, and **400M**. Valid values for frequency range 2-2 are **100M**,
        **400M**, **800M**, **1600M**, and **2000M**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the channel bandwidth of the signal being measured. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth(self, selector_string, value):
        r"""Sets the channel bandwidth of the signal being measured. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **100M**. Valid values for frequency range 1 are from **3M** to **100M**. Valid values for
        frequency range 2-1 are **50M**, **100M**, **200M**, and **400M**. Valid values for frequency range 2-2 are **100M**,
        **400M**, **800M**, **1600M**, and **2000M**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the channel bandwidth of the signal being measured. This value is expressed in Hz.

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
                attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency(self, selector_string):
        r"""Gets the offset of the component carrier from the subblock center frequency that you configure in the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz.

        This attribute is applicable only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to **User**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset of the component carrier from the subblock center frequency that you configure in the
                :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency(self, selector_string, value):
        r"""Sets the offset of the component carrier from the subblock center frequency that you configure in the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz.

        This attribute is applicable only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to **User**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset of the component carrier from the subblock center frequency that you configure in the
                :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz.

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
                attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_allocated(self, selector_string):
        r"""Gets whether a component carrier has one or more resource elements allocated.

        While performing IBE measurement on a subblock, you set this attribute to **False** for all secondary component
        carriers  as specified in section 6.4A.2.3 of *3GPP 38.521-1* and *3GPP 38.521-2* specifications.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **True**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | False (0)    | No resource elements are allocated for the component carrier. Only subblock IBE is computed. |
        +--------------+----------------------------------------------------------------------------------------------+
        | True (1)     | One or more resource elements are allocated for the component carrier.                       |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ComponentCarrierAllocated):
                Specifies whether a component carrier has one or more resource elements allocated.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_ALLOCATED.value
            )
            attr_val = enums.ComponentCarrierAllocated(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_allocated(self, selector_string, value):
        r"""Sets whether a component carrier has one or more resource elements allocated.

        While performing IBE measurement on a subblock, you set this attribute to **False** for all secondary component
        carriers  as specified in section 6.4A.2.3 of *3GPP 38.521-1* and *3GPP 38.521-2* specifications.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **True**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | False (0)    | No resource elements are allocated for the component carrier. Only subblock IBE is computed. |
        +--------------+----------------------------------------------------------------------------------------------+
        | True (1)     | One or more resource elements are allocated for the component carrier.                       |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ComponentCarrierAllocated, int):
                Specifies whether a component carrier has one or more resource elements allocated.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ComponentCarrierAllocated else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.COMPONENT_CARRIER_ALLOCATED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_radio_access_type(self, selector_string):
        r"""Gets if a carrier is a NR or an E-UTRA carrier while using dual connectivity (EN-DC) signal.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **NR**.

        +--------------+---------------------------------------+
        | Name (Value) | Description                           |
        +==============+=======================================+
        | NR (0)       | Specifies that the carrier is NR.     |
        +--------------+---------------------------------------+
        | EUTRA (1)    | Specifies that the carrier is E-UTRA. |
        +--------------+---------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ComponentCarrierRadioAccessType):
                Specifies if a carrier is a NR or an E-UTRA carrier while using dual connectivity (EN-DC) signal.

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
                attributes.AttributeID.COMPONENT_CARRIER_RADIO_ACCESS_TYPE.value,
            )
            attr_val = enums.ComponentCarrierRadioAccessType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_radio_access_type(self, selector_string, value):
        r"""Sets if a carrier is a NR or an E-UTRA carrier while using dual connectivity (EN-DC) signal.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **NR**.

        +--------------+---------------------------------------+
        | Name (Value) | Description                           |
        +==============+=======================================+
        | NR (0)       | Specifies that the carrier is NR.     |
        +--------------+---------------------------------------+
        | EUTRA (1)    | Specifies that the carrier is E-UTRA. |
        +--------------+---------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ComponentCarrierRadioAccessType, int):
                Specifies if a carrier is a NR or an E-UTRA carrier while using dual connectivity (EN-DC) signal.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ComponentCarrierRadioAccessType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.COMPONENT_CARRIER_RADIO_ACCESS_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_cell_id(self, selector_string):
        r"""Gets a physical layer cell identity.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values are 0 to 1007, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies a physical layer cell identity.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CELL_ID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_cell_id(self, selector_string, value):
        r"""Sets a physical layer cell identity.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values are 0 to 1007, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies a physical layer cell identity.

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
                updated_selector_string, attributes.AttributeID.CELL_ID.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_grid_subcarrier_spacing(self, selector_string):
        r"""Gets the subcarrier spacing of the reference resource grid when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. This should be the
        largest subcarrier spacing used in the component carrier. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **30kHz**.

        Valid values for frequency range 1 are **15kHz**, **30kHz**, and **60kHz**.

        Valid values for frequency range 2-1 are **60kHz**, **120kHz**, and **240kHz**.

        Valid values for frequency range 2-2 are **120kHz**, **480kHz**, and **960kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the subcarrier spacing of the reference resource grid when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. This should be the
                largest subcarrier spacing used in the component carrier. This value is expressed in Hz.

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
                attributes.AttributeID.REFERENCE_GRID_SUBCARRIER_SPACING.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_grid_subcarrier_spacing(self, selector_string, value):
        r"""Sets the subcarrier spacing of the reference resource grid when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. This should be the
        largest subcarrier spacing used in the component carrier. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **30kHz**.

        Valid values for frequency range 1 are **15kHz**, **30kHz**, and **60kHz**.

        Valid values for frequency range 2-1 are **60kHz**, **120kHz**, and **240kHz**.

        Valid values for frequency range 2-2 are **120kHz**, **480kHz**, and **960kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the subcarrier spacing of the reference resource grid when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. This should be the
                largest subcarrier spacing used in the component carrier. This value is expressed in Hz.

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
                attributes.AttributeID.REFERENCE_GRID_SUBCARRIER_SPACING.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_grid_start(self, selector_string):
        r"""Gets the reference resource grid start relative to Reference Point A in terms of resource block offset when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. Center of
        subcarrier 0 in common resource block 0 is considered as Reference Point A.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the reference resource grid start relative to Reference Point A in terms of resource block offset when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. Center of
                subcarrier 0 in common resource block 0 is considered as Reference Point A.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.REFERENCE_GRID_START.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_grid_start(self, selector_string, value):
        r"""Sets the reference resource grid start relative to Reference Point A in terms of resource block offset when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. Center of
        subcarrier 0 in common resource block 0 is considered as Reference Point A.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the reference resource grid start relative to Reference Point A in terms of resource block offset when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. Center of
                subcarrier 0 in common resource block 0 is considered as Reference Point A.

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
                updated_selector_string, attributes.AttributeID.REFERENCE_GRID_START.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_grid_size(self, selector_string):
        r"""Gets the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
        attribute to **Manual**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
                attribute to **Manual**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.REFERENCE_GRID_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_grid_size(self, selector_string, value):
        r"""Sets the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
        attribute to **Manual**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
                attribute to **Manual**.

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
                updated_selector_string, attributes.AttributeID.REFERENCE_GRID_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sub_band_allocation(self, selector_string):
        r"""Gets the sub-band allocation in the NR-U wideband channel. Sub-band is the set of RBs with approximately 20 MHz
        bandwidth, where the wideband channel is uniformly divided into an integer number of 20 MHz sub-bands.

        This attribute is valid only for the bands n46, n96, n102 as defined in the 3GPP TS 37.213 for the shared
        spectrum channel access.

        The format is defined by range format specifiers.
        The range format specifier is a comma separated list of entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 0,2 will expand to {0,2}

        0:2,3 will expand to {0,1,2,3}.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last, where

        Last = 0 for 20 MHz

        1 for 40 MHz

        2 for 60 MHz

        3 for 80 MHz

        4 for 100 MHz

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the sub-band allocation in the NR-U wideband channel. Sub-band is the set of RBs with approximately 20 MHz
                bandwidth, where the wideband channel is uniformly divided into an integer number of 20 MHz sub-bands.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.SUB_BAND_ALLOCATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sub_band_allocation(self, selector_string, value):
        r"""Sets the sub-band allocation in the NR-U wideband channel. Sub-band is the set of RBs with approximately 20 MHz
        bandwidth, where the wideband channel is uniformly divided into an integer number of 20 MHz sub-bands.

        This attribute is valid only for the bands n46, n96, n102 as defined in the 3GPP TS 37.213 for the shared
        spectrum channel access.

        The format is defined by range format specifiers.
        The range format specifier is a comma separated list of entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 0,2 will expand to {0,2}

        0:2,3 will expand to {0,1,2,3}.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last, where

        Last = 0 for 20 MHz

        1 for 40 MHz

        2 for 60 MHz

        3 for 80 MHz

        4 for 100 MHz

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the sub-band allocation in the NR-U wideband channel. Sub-band is the set of RBs with approximately 20 MHz
                bandwidth, where the wideband channel is uniformly divided into an integer number of 20 MHz sub-bands.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.SUB_BAND_ALLOCATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_bandwidth_parts(self, selector_string):
        r"""Gets the number of bandwidth parts present in the component carrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of bandwidth parts present in the component carrier.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_BANDWIDTH_PARTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_bandwidth_parts(self, selector_string, value):
        r"""Sets the number of bandwidth parts present in the component carrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of bandwidth parts present in the component carrier.

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
                attributes.AttributeID.NUMBER_OF_BANDWIDTH_PARTS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth_part_subcarrier_spacing(self, selector_string):
        r"""Gets the subcarrier spacing of the bandwidth part used  in the component carrier.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is **30kHz**.

        Valid values for frequency range 1 are **15kHz**, **30kHz**, and **60kHz**.

        Valid values for frequency range 2-1 are **60kHz** and **120kHz**.

        Valid values for frequency range 2-2 are **120kHz**, **480kHz**, and **960kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the subcarrier spacing of the bandwidth part used  in the component carrier.

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
                attributes.AttributeID.BANDWIDTH_PART_SUBCARRIER_SPACING.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth_part_subcarrier_spacing(self, selector_string, value):
        r"""Sets the subcarrier spacing of the bandwidth part used  in the component carrier.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is **30kHz**.

        Valid values for frequency range 1 are **15kHz**, **30kHz**, and **60kHz**.

        Valid values for frequency range 2-1 are **60kHz** and **120kHz**.

        Valid values for frequency range 2-2 are **120kHz**, **480kHz**, and **960kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the subcarrier spacing of the bandwidth part used  in the component carrier.

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
                attributes.AttributeID.BANDWIDTH_PART_SUBCARRIER_SPACING.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth_part_cyclic_prefix_mode(self, selector_string):
        r"""Gets the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is **Normal**.

        +--------------+------------------------------------------+
        | Name (Value) | Description                              |
        +==============+==========================================+
        | Normal (0)   | The number of symbols in the slot is 14. |
        +--------------+------------------------------------------+
        | Extended (1) | The number of symbols in the slot is 12. |
        +--------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.BandwidthPartCyclicPrefixMode):
                Specifies the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

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
                attributes.AttributeID.BANDWIDTH_PART_CYCLIC_PREFIX_MODE.value,
            )
            attr_val = enums.BandwidthPartCyclicPrefixMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth_part_cyclic_prefix_mode(self, selector_string, value):
        r"""Sets the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is **Normal**.

        +--------------+------------------------------------------+
        | Name (Value) | Description                              |
        +==============+==========================================+
        | Normal (0)   | The number of symbols in the slot is 14. |
        +--------------+------------------------------------------+
        | Extended (1) | The number of symbols in the slot is 12. |
        +--------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.BandwidthPartCyclicPrefixMode, int):
                Specifies the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.BandwidthPartCyclicPrefixMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.BANDWIDTH_PART_CYCLIC_PREFIX_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_grid_start(self, selector_string):
        r"""Gets the resource grid start relative to Reference Point A in terms of resource block offset when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the resource grid start relative to Reference Point A in terms of resource block offset when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.GRID_START.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_grid_start(self, selector_string, value):
        r"""Sets the resource grid start relative to Reference Point A in terms of resource block offset when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the resource grid start relative to Reference Point A in terms of resource block offset when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**.

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
                updated_selector_string, attributes.AttributeID.GRID_START.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_grid_size(self, selector_string):
        r"""Gets the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
        attribute to **Manual**.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
                attribute to **Manual**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.GRID_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_grid_size(self, selector_string, value):
        r"""Sets the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
        attribute to **Manual**.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
                attribute to **Manual**.

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
                updated_selector_string, attributes.AttributeID.GRID_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth_part_resource_block_offset(self, selector_string):
        r"""Gets the resource block offset of a bandwidth part relative to the resource
        :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_START` attribute.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the resource block offset of a bandwidth part relative to the resource
                :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_START` attribute.

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
                attributes.AttributeID.BANDWIDTH_PART_RESOURCE_BLOCK_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth_part_resource_block_offset(self, selector_string, value):
        r"""Sets the resource block offset of a bandwidth part relative to the resource
        :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_START` attribute.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the resource block offset of a bandwidth part relative to the resource
                :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_START` attribute.

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
                attributes.AttributeID.BANDWIDTH_PART_RESOURCE_BLOCK_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth_part_number_of_resource_blocks(self, selector_string):
        r"""Sets the number of consecutive resource blocks in a bandwidth  part.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth that do not violate the minimum guard band are configured.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Sets the number of consecutive resource blocks in a bandwidth  part.

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
                attributes.AttributeID.BANDWIDTH_PART_NUMBER_OF_RESOURCE_BLOCKS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth_part_number_of_resource_blocks(self, selector_string, value):
        r"""Sets the number of consecutive resource blocks in a bandwidth  part.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth that do not violate the minimum guard band are configured.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Sets the number of consecutive resource blocks in a bandwidth  part.

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
                attributes.AttributeID.BANDWIDTH_PART_NUMBER_OF_RESOURCE_BLOCKS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth_part_dc_location_known(self, selector_string):
        r"""Gets whether Uplink Tx Direct Current location within the carrier is determined. If set to **False**, DC location
        is undetermined within the carrier. In ModAcc measurement, IQ impairments are not estimated and compensated, and only
        **General** In-Band Emission limits are applied. If set to **True**, DC location is determined within the carrier.

        This attribute is not supported when :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute is
        set to **Downlink**.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is **True**.

        +--------------+--------------------------+
        | Name (Value) | Description              |
        +==============+==========================+
        | False (0)    | DC Location is un-known. |
        +--------------+--------------------------+
        | True (1)     | DC Location is known.    |
        +--------------+--------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.BandwidthPartDCLocationKnown):
                Specifies whether Uplink Tx Direct Current location within the carrier is determined. If set to **False**, DC location
                is undetermined within the carrier. In ModAcc measurement, IQ impairments are not estimated and compensated, and only
                **General** In-Band Emission limits are applied. If set to **True**, DC location is determined within the carrier.

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
                attributes.AttributeID.BANDWIDTH_PART_DC_LOCATION_KNOWN.value,
            )
            attr_val = enums.BandwidthPartDCLocationKnown(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth_part_dc_location_known(self, selector_string, value):
        r"""Sets whether Uplink Tx Direct Current location within the carrier is determined. If set to **False**, DC location
        is undetermined within the carrier. In ModAcc measurement, IQ impairments are not estimated and compensated, and only
        **General** In-Band Emission limits are applied. If set to **True**, DC location is determined within the carrier.

        This attribute is not supported when :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute is
        set to **Downlink**.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is **True**.

        +--------------+--------------------------+
        | Name (Value) | Description              |
        +==============+==========================+
        | False (0)    | DC Location is un-known. |
        +--------------+--------------------------+
        | True (1)     | DC Location is known.    |
        +--------------+--------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.BandwidthPartDCLocationKnown, int):
                Specifies whether Uplink Tx Direct Current location within the carrier is determined. If set to **False**, DC location
                is undetermined within the carrier. In ModAcc measurement, IQ impairments are not estimated and compensated, and only
                **General** In-Band Emission limits are applied. If set to **True**, DC location is determined within the carrier.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.BandwidthPartDCLocationKnown else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.BANDWIDTH_PART_DC_LOCATION_KNOWN.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_users(self, selector_string):
        r"""Gets the number of users present in the bandwidth part.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of users present in the bandwidth part.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_USERS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_users(self, selector_string, value):
        r"""Sets the number of users present in the bandwidth part.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of users present in the bandwidth part.

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
                updated_selector_string, attributes.AttributeID.NUMBER_OF_USERS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rnti(self, selector_string):
        r"""Gets the RNTI.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the RNTI.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.RNTI.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rnti(self, selector_string, value):
        r"""Sets the RNTI.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the RNTI.

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
                updated_selector_string, attributes.AttributeID.RNTI.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_pusch_configurations(self, selector_string):
        r"""Gets the number of PUSCH slot configurations.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of PUSCH slot configurations.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_PUSCH_CONFIGURATIONS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_pusch_configurations(self, selector_string, value):
        r"""Sets the number of PUSCH slot configurations.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of PUSCH slot configurations.

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
                attributes.AttributeID.NUMBER_OF_PUSCH_CONFIGURATIONS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_transform_precoding_enabled(self, selector_string):
        r"""Gets whether transform precoding is enabled. Enable transform precoding when analyzing a DFT-s-OFDM waveform.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------------+
        | Name (Value) | Description                      |
        +==============+==================================+
        | False (0)    | Transform precoding is disabled. |
        +--------------+----------------------------------+
        | True (1)     | Transform precoding is enabled.  |
        +--------------+----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschTransformPrecodingEnabled):
                Specifies whether transform precoding is enabled. Enable transform precoding when analyzing a DFT-s-OFDM waveform.

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
                attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED.value,
            )
            attr_val = enums.PuschTransformPrecodingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_transform_precoding_enabled(self, selector_string, value):
        r"""Sets whether transform precoding is enabled. Enable transform precoding when analyzing a DFT-s-OFDM waveform.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------------+
        | Name (Value) | Description                      |
        +==============+==================================+
        | False (0)    | Transform precoding is disabled. |
        +--------------+----------------------------------+
        | True (1)     | Transform precoding is enabled.  |
        +--------------+----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschTransformPrecodingEnabled, int):
                Specifies whether transform precoding is enabled. Enable transform precoding when analyzing a DFT-s-OFDM waveform.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschTransformPrecodingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_number_of_resource_block_clusters(self, selector_string):
        r"""Gets the number of clusters of resource allocations with each cluster including one or more consecutive resource
        blocks. This attribute is ignored if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of clusters of resource allocations with each cluster including one or more consecutive resource
                blocks. This attribute is ignored if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_number_of_resource_block_clusters(self, selector_string, value):
        r"""Sets the number of clusters of resource allocations with each cluster including one or more consecutive resource
        blocks. This attribute is ignored if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of clusters of resource allocations with each cluster including one or more consecutive resource
                blocks. This attribute is ignored if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_resource_block_offset(self, selector_string):
        r"""Gets the starting resource block number of a PUSCH cluster. This attribute is ignored if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

        Use "puschcluster<*s*>" or "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>/puschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting resource block number of a PUSCH cluster. This attribute is ignored if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_resource_block_offset(self, selector_string, value):
        r"""Sets the starting resource block number of a PUSCH cluster. This attribute is ignored if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

        Use "puschcluster<*s*>" or "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>/puschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting resource block number of a PUSCH cluster. This attribute is ignored if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.

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
                attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_number_of_resource_blocks(self, selector_string):
        r"""Gets the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster. This attribute
        is ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute
        to **True**.

        Use "puschcluster<*s*>" or "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>/puschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth are configured.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster. This attribute
                is ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute
                to **True**.

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_number_of_resource_blocks(self, selector_string, value):
        r"""Sets the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster. This attribute
        is ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute
        to **True**.

        Use "puschcluster<*s*>" or "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>/puschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
        bandwidth are configured.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster. This attribute
                is ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute
                to **True**.

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
                attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_modulation_type(self, selector_string):
        r"""Gets the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

        The **PI/2 BPSK** modulation type is supported only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**. This attribute is
        ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to
        **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **QPSK**.

        +---------------+------------------------------------------+
        | Name (Value)  | Description                              |
        +===============+==========================================+
        | PI/2 BPSK (0) | Specifies a PI/2 BPSK modulation scheme. |
        +---------------+------------------------------------------+
        | QPSK (1)      | Specifies a QPSK modulation scheme.      |
        +---------------+------------------------------------------+
        | 16 QAM (2)    | Specifies a 16 QAM modulation scheme.    |
        +---------------+------------------------------------------+
        | 64 QAM (3)    | Specifies a 64 QAM modulation scheme.    |
        +---------------+------------------------------------------+
        | 256 QAM (4)   | Specifies a 256 QAM modulation scheme.   |
        +---------------+------------------------------------------+
        | 1024 QAM (5)  | Specifies a 1024 QAM modulation scheme.  |
        +---------------+------------------------------------------+
        | 8 PSK (100)   | Specifies a 8 PSK modulation scheme.     |
        +---------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschModulationType):
                Specifies the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_MODULATION_TYPE.value
            )
            attr_val = enums.PuschModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_modulation_type(self, selector_string, value):
        r"""Sets the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

        The **PI/2 BPSK** modulation type is supported only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**. This attribute is
        ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to
        **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **QPSK**.

        +---------------+------------------------------------------+
        | Name (Value)  | Description                              |
        +===============+==========================================+
        | PI/2 BPSK (0) | Specifies a PI/2 BPSK modulation scheme. |
        +---------------+------------------------------------------+
        | QPSK (1)      | Specifies a QPSK modulation scheme.      |
        +---------------+------------------------------------------+
        | 16 QAM (2)    | Specifies a 16 QAM modulation scheme.    |
        +---------------+------------------------------------------+
        | 64 QAM (3)    | Specifies a 64 QAM modulation scheme.    |
        +---------------+------------------------------------------+
        | 256 QAM (4)   | Specifies a 256 QAM modulation scheme.   |
        +---------------+------------------------------------------+
        | 1024 QAM (5)  | Specifies a 1024 QAM modulation scheme.  |
        +---------------+------------------------------------------+
        | 8 PSK (100)   | Specifies a 8 PSK modulation scheme.     |
        +---------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschModulationType, int):
                Specifies the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_MODULATION_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_release_version(self, selector_string):
        r"""Gets the 3GGP release version for PUSCH DMRS.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        +---------------+-----------------------------------------------------------------+
        | Name (Value)  | Description                                                     |
        +===============+=================================================================+
        | Release15 (0) | Specifies a 3GGP release version of 15 for PUSCH DMRS.          |
        +---------------+-----------------------------------------------------------------+
        | Release16 (1) | Specifies a 3GGP release version of 16 or later for PUSCH DMRS. |
        +---------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsReleaseVersion):
                Specifies the 3GGP release version for PUSCH DMRS.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_RELEASE_VERSION.value
            )
            attr_val = enums.PuschDmrsReleaseVersion(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_release_version(self, selector_string, value):
        r"""Sets the 3GGP release version for PUSCH DMRS.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        +---------------+-----------------------------------------------------------------+
        | Name (Value)  | Description                                                     |
        +===============+=================================================================+
        | Release15 (0) | Specifies a 3GGP release version of 15 for PUSCH DMRS.          |
        +---------------+-----------------------------------------------------------------+
        | Release16 (1) | Specifies a 3GGP release version of 16 or later for PUSCH DMRS. |
        +---------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsReleaseVersion, int):
                Specifies the 3GGP release version for PUSCH DMRS.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsReleaseVersion else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_RELEASE_VERSION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_antenna_ports(self, selector_string):
        r"""Gets the antenna ports used for DMRS transmission.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values depend on :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE`
        and :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attributes.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the antenna ports used for DMRS transmission.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_ANTENNA_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_antenna_ports(self, selector_string, value):
        r"""Sets the antenna ports used for DMRS transmission.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values depend on :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE`
        and :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attributes.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the antenna ports used for DMRS transmission.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_ANTENNA_PORTS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_power_mode(self, selector_string):
        r"""Gets whether the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER` attribute is calculated
        based on the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attribute or specified by you.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **CDM Groups**.

        +------------------+-----------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                             |
        +==================+=========================================================================================+
        | CDM Groups (0)   | The value of PUSCH DMRS Pwr is calculated based on PDSCH DMRS Num CDM Groups attribute. |
        +------------------+-----------------------------------------------------------------------------------------+
        | User Defined (1) | The value of PUSCH DMRS Pwr is specified by you.                                        |
        +------------------+-----------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsPowerMode):
                Specifies whether the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER` attribute is calculated
                based on the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attribute or specified by you.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_POWER_MODE.value
            )
            attr_val = enums.PuschDmrsPowerMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_power_mode(self, selector_string, value):
        r"""Sets whether the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER` attribute is calculated
        based on the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attribute or specified by you.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **CDM Groups**.

        +------------------+-----------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                             |
        +==================+=========================================================================================+
        | CDM Groups (0)   | The value of PUSCH DMRS Pwr is calculated based on PDSCH DMRS Num CDM Groups attribute. |
        +------------------+-----------------------------------------------------------------------------------------+
        | User Defined (1) | The value of PUSCH DMRS Pwr is specified by you.                                        |
        +------------------+-----------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsPowerMode, int):
                Specifies whether the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER` attribute is calculated
                based on the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attribute or specified by you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsPowerMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_POWER_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_power(self, selector_string):
        r"""Gets the factor which boosts the PUSCH DMRS REs. This value is expressed in dB. This attribute is ignored if you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER_MODE` attribute to **CDM Groups**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the factor which boosts the PUSCH DMRS REs. This value is expressed in dB. This attribute is ignored if you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER_MODE` attribute to **CDM Groups**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_power(self, selector_string, value):
        r"""Sets the factor which boosts the PUSCH DMRS REs. This value is expressed in dB. This attribute is ignored if you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER_MODE` attribute to **CDM Groups**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the factor which boosts the PUSCH DMRS REs. This value is expressed in dB. This attribute is ignored if you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER_MODE` attribute to **CDM Groups**.

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
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_number_of_cdm_groups(self, selector_string):
        r"""Gets the number of CDM groups, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**, otherwise it is
        coerced to 2.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of CDM groups, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**, otherwise it is
                coerced to 2.

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
                attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_number_of_cdm_groups(self, selector_string, value):
        r"""Sets the number of CDM groups, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**, otherwise it is
        coerced to 2.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of CDM groups, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**, otherwise it is
                coerced to 2.

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
                attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_scrambling_id_mode(self, selector_string):
        r"""Gets whether the configured Scrambling ID is honored or the Cell ID is used for reference signal generation.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Cell ID**.

        +------------------+----------------------------------------------------------------------+
        | Name (Value)     | Description                                                          |
        +==================+======================================================================+
        | Cell ID (0)      | The value of PUSCH DMRS Scrambling ID is based on Cell ID attribute. |
        +------------------+----------------------------------------------------------------------+
        | User Defined (1) | The value of PUSCH DMRS Scrambling ID is specified by you.           |
        +------------------+----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsScramblingIDMode):
                Specifies whether the configured Scrambling ID is honored or the Cell ID is used for reference signal generation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_SCRAMBLING_ID_MODE.value
            )
            attr_val = enums.PuschDmrsScramblingIDMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_scrambling_id_mode(self, selector_string, value):
        r"""Sets whether the configured Scrambling ID is honored or the Cell ID is used for reference signal generation.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Cell ID**.

        +------------------+----------------------------------------------------------------------+
        | Name (Value)     | Description                                                          |
        +==================+======================================================================+
        | Cell ID (0)      | The value of PUSCH DMRS Scrambling ID is based on Cell ID attribute. |
        +------------------+----------------------------------------------------------------------+
        | User Defined (1) | The value of PUSCH DMRS Scrambling ID is specified by you.           |
        +------------------+----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsScramblingIDMode, int):
                Specifies whether the configured Scrambling ID is honored or the Cell ID is used for reference signal generation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsScramblingIDMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_SCRAMBLING_ID_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_scrambling_id(self, selector_string):
        r"""Gets the value of scrambling ID. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 65535, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the value of scrambling ID. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_SCRAMBLING_ID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_scrambling_id(self, selector_string, value):
        r"""Sets the value of scrambling ID. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 65535, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the value of scrambling ID. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

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
                attributes.AttributeID.PUSCH_DMRS_SCRAMBLING_ID.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_nscid(self, selector_string):
        r"""Gets the value of PUSCH DMRS nSCID used for reference signal generation. This attribute is valid only when you set
        the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the value of PUSCH DMRS nSCID used for reference signal generation. This attribute is valid only when you set
                the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_NSCID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_nscid(self, selector_string, value):
        r"""Sets the value of PUSCH DMRS nSCID used for reference signal generation. This attribute is valid only when you set
        the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the value of PUSCH DMRS nSCID used for reference signal generation. This attribute is valid only when you set
                the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

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
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_NSCID.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_group_hopping_enabled(self, selector_string):
        r"""Gets whether the group hopping is enabled. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------+
        | Name (Value) | Description                |
        +==============+============================+
        | False (0)    | Group hopping is disabled. |
        +--------------+----------------------------+
        | True (1)     | Group hopping is enabled.  |
        +--------------+----------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsGroupHoppingEnabled):
                Specifies whether the group hopping is enabled. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.PUSCH_DMRS_GROUP_HOPPING_ENABLED.value,
            )
            attr_val = enums.PuschDmrsGroupHoppingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_group_hopping_enabled(self, selector_string, value):
        r"""Sets whether the group hopping is enabled. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------+
        | Name (Value) | Description                |
        +==============+============================+
        | False (0)    | Group hopping is disabled. |
        +--------------+----------------------------+
        | True (1)     | Group hopping is enabled.  |
        +--------------+----------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsGroupHoppingEnabled, int):
                Specifies whether the group hopping is enabled. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsGroupHoppingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_GROUP_HOPPING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_sequence_hopping_enabled(self, selector_string):
        r"""Gets whether the sequence hopping is enabled. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                        |
        +==============+====================================================================================================+
        | False (0)    | The measurement uses zero as the base sequence number for all the slots.                           |
        +--------------+----------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement calculates the base sequence number for each slot according to 3GPP specification. |
        +--------------+----------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsSequenceHoppingEnabled):
                Specifies whether the sequence hopping is enabled. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.PUSCH_DMRS_SEQUENCE_HOPPING_ENABLED.value,
            )
            attr_val = enums.PuschDmrsSequenceHoppingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_sequence_hopping_enabled(self, selector_string, value):
        r"""Sets whether the sequence hopping is enabled. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                        |
        +==============+====================================================================================================+
        | False (0)    | The measurement uses zero as the base sequence number for all the slots.                           |
        +--------------+----------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement calculates the base sequence number for each slot according to 3GPP specification. |
        +--------------+----------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsSequenceHoppingEnabled, int):
                Specifies whether the sequence hopping is enabled. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsSequenceHoppingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_SEQUENCE_HOPPING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_pusch_id_mode(self, selector_string):
        r"""Gets whether PUSCH DMRS PUSCH ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or specified by
        you. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Cell ID**.

        +------------------+-----------------------------------------------------------------+
        | Name (Value)     | Description                                                     |
        +==================+=================================================================+
        | Cell ID (0)      | The value of PUSCH DMRS PUSCH ID is based on Cell ID attribute. |
        +------------------+-----------------------------------------------------------------+
        | User Defined (1) | The value of PUSCH DMRS PUSCH ID is specified by you.           |
        +------------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsPuschIDMode):
                Specifies whether PUSCH DMRS PUSCH ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or specified by
                you. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE.value
            )
            attr_val = enums.PuschDmrsPuschIDMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_pusch_id_mode(self, selector_string, value):
        r"""Sets whether PUSCH DMRS PUSCH ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or specified by
        you. This attribute is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Cell ID**.

        +------------------+-----------------------------------------------------------------+
        | Name (Value)     | Description                                                     |
        +==================+=================================================================+
        | Cell ID (0)      | The value of PUSCH DMRS PUSCH ID is based on Cell ID attribute. |
        +------------------+-----------------------------------------------------------------+
        | User Defined (1) | The value of PUSCH DMRS PUSCH ID is specified by you.           |
        +------------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsPuschIDMode, int):
                Specifies whether PUSCH DMRS PUSCH ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or specified by
                you. This attribute is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsPuschIDMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_pusch_id(self, selector_string):
        r"""Gets the value of PUSCH DMRS PUSCH ID used for reference signal generation. This attribute is valid only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE` attribute to **User Defined**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 1007, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the value of PUSCH DMRS PUSCH ID used for reference signal generation. This attribute is valid only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE` attribute to **User Defined**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_PUSCH_ID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_pusch_id(self, selector_string, value):
        r"""Sets the value of PUSCH DMRS PUSCH ID used for reference signal generation. This attribute is valid only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE` attribute to **User Defined**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0. Valid values are from 0 to 1007, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the value of PUSCH DMRS PUSCH ID used for reference signal generation. This attribute is valid only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE` attribute to **User Defined**.

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
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_PUSCH_ID.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_configuration_type(self, selector_string):
        r"""Gets the configuration type of DMRS.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type 1**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Type 1 (0)   | One DMRS subcarrier alternates with one data subcarrier.                           |
        +--------------+------------------------------------------------------------------------------------+
        | Type 2 (1)   | Two consecutive DMRS subcarriers alternate with four consecutive data subcarriers. |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsConfigurationType):
                Specifies the configuration type of DMRS.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_CONFIGURATION_TYPE.value
            )
            attr_val = enums.PuschDmrsConfigurationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_configuration_type(self, selector_string, value):
        r"""Sets the configuration type of DMRS.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type 1**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Type 1 (0)   | One DMRS subcarrier alternates with one data subcarrier.                           |
        +--------------+------------------------------------------------------------------------------------+
        | Type 2 (1)   | Two consecutive DMRS subcarriers alternate with four consecutive data subcarriers. |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsConfigurationType, int):
                Specifies the configuration type of DMRS.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsConfigurationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PUSCH_DMRS_CONFIGURATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_mapping_type(self, selector_string):
        r"""Gets the mapping type of DMRS.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type A**.

        +--------------+-------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                           |
        +==============+=======================================================================================================+
        | Type A (0)   | The first DMRS symbol index in a slot is either 2 or 3 based on PUSCH DMRS Type A Position attribute. |
        +--------------+-------------------------------------------------------------------------------------------------------+
        | Type B (1)   | The first DMRS symbol index in a slot is the first active PUSCH symbol.                               |
        +--------------+-------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschMappingType):
                Specifies the mapping type of DMRS.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_MAPPING_TYPE.value
            )
            attr_val = enums.PuschMappingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_mapping_type(self, selector_string, value):
        r"""Sets the mapping type of DMRS.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type A**.

        +--------------+-------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                           |
        +==============+=======================================================================================================+
        | Type A (0)   | The first DMRS symbol index in a slot is either 2 or 3 based on PUSCH DMRS Type A Position attribute. |
        +--------------+-------------------------------------------------------------------------------------------------------+
        | Type B (1)   | The first DMRS symbol index in a slot is the first active PUSCH symbol.                               |
        +--------------+-------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschMappingType, int):
                Specifies the mapping type of DMRS.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschMappingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_MAPPING_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_type_a_position(self, selector_string):
        r"""Gets the position of first DMRS symbol in a slot when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE` attribute to **Type A**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the position of first DMRS symbol in a slot when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE` attribute to **Type A**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_TYPE_A_POSITION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_type_a_position(self, selector_string, value):
        r"""Sets the position of first DMRS symbol in a slot when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE` attribute to **Type A**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the position of first DMRS symbol in a slot when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE` attribute to **Type A**.

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
                attributes.AttributeID.PUSCH_DMRS_TYPE_A_POSITION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_duration(self, selector_string):
        r"""Gets whether the DMRS is single-symbol or double-symbol.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Single-Symbol**.

        +-------------------+-------------------------------------------------------------------------+
        | Name (Value)      | Description                                                             |
        +===================+=========================================================================+
        | Single-Symbol (1) | There are one or more non-consecutive DMRS symbols in a slot..          |
        +-------------------+-------------------------------------------------------------------------+
        | Double-Symbol (2) | There are one or more sets of two consecutive DMRS symbols in the slot. |
        +-------------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschDmrsDuration):
                Specifies whether the DMRS is single-symbol or double-symbol.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_DURATION.value
            )
            attr_val = enums.PuschDmrsDuration(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_duration(self, selector_string, value):
        r"""Sets whether the DMRS is single-symbol or double-symbol.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Single-Symbol**.

        +-------------------+-------------------------------------------------------------------------+
        | Name (Value)      | Description                                                             |
        +===================+=========================================================================+
        | Single-Symbol (1) | There are one or more non-consecutive DMRS symbols in a slot..          |
        +-------------------+-------------------------------------------------------------------------+
        | Double-Symbol (2) | There are one or more sets of two consecutive DMRS symbols in the slot. |
        +-------------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschDmrsDuration, int):
                Specifies whether the DMRS is single-symbol or double-symbol.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschDmrsDuration else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_DMRS_DURATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_dmrs_additional_positions(self, selector_string):
        r"""Gets the number of additional sets of consecutive DMRS symbols in a slot.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of additional sets of consecutive DMRS symbols in a slot.

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
                attributes.AttributeID.PUSCH_DMRS_ADDITIONAL_POSITIONS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_dmrs_additional_positions(self, selector_string, value):
        r"""Sets the number of additional sets of consecutive DMRS symbols in a slot.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of additional sets of consecutive DMRS symbols in a slot.

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
                attributes.AttributeID.PUSCH_DMRS_ADDITIONAL_POSITIONS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_enabled(self, selector_string):
        r"""Gets whether the PUSCH transmission contains PTRS signals.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+-------------------------------------------------------+
        | Name (Value) | Description                                           |
        +==============+=======================================================+
        | False (0)    | The PUSCH Transmission does not contain PTRS signals. |
        +--------------+-------------------------------------------------------+
        | True (1)     | The PUSCH PTRS contains PTRS signals.                 |
        +--------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschPtrsEnabled):
                Specifies whether the PUSCH transmission contains PTRS signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_ENABLED.value
            )
            attr_val = enums.PuschPtrsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_enabled(self, selector_string, value):
        r"""Sets whether the PUSCH transmission contains PTRS signals.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+-------------------------------------------------------+
        | Name (Value) | Description                                           |
        +==============+=======================================================+
        | False (0)    | The PUSCH Transmission does not contain PTRS signals. |
        +--------------+-------------------------------------------------------+
        | True (1)     | The PUSCH PTRS contains PTRS signals.                 |
        +--------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschPtrsEnabled, int):
                Specifies whether the PUSCH transmission contains PTRS signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschPtrsEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_antenna_ports(self, selector_string):
        r"""Gets the DMRS antenna ports associated with PTRS transmission. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the DMRS antenna ports associated with PTRS transmission. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_ANTENNA_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_antenna_ports(self, selector_string, value):
        r"""Sets the DMRS antenna ports associated with PTRS transmission. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the DMRS antenna ports associated with PTRS transmission. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string,
                attributes.AttributeID.PUSCH_PTRS_ANTENNA_PORTS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_power_mode(self, selector_string):
        r"""Gets whether the PUSCH PTRS power scaling is calculated as defined in 3GPP specification or specified by you. This
        attribute is valid only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to
        **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Standard**.

        +------------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                 |
        +==================+=============================================================================================================+
        | Standard (0)     | The PUSCH PTRS Pwr scaling is calculated as defined in the Table 6.2.3.1-1 of 3GPP TS 38.214 specification. |
        +------------------+-------------------------------------------------------------------------------------------------------------+
        | User Defined (1) | The PTRS RE power scaling is given by the value of PUSCH PTRS Pwr attribute.                                |
        +------------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PuschPtrsPowerMode):
                Specifies whether the PUSCH PTRS power scaling is calculated as defined in 3GPP specification or specified by you. This
                attribute is valid only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to
                **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_POWER_MODE.value
            )
            attr_val = enums.PuschPtrsPowerMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_power_mode(self, selector_string, value):
        r"""Sets whether the PUSCH PTRS power scaling is calculated as defined in 3GPP specification or specified by you. This
        attribute is valid only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to
        **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Standard**.

        +------------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                 |
        +==================+=============================================================================================================+
        | Standard (0)     | The PUSCH PTRS Pwr scaling is calculated as defined in the Table 6.2.3.1-1 of 3GPP TS 38.214 specification. |
        +------------------+-------------------------------------------------------------------------------------------------------------+
        | User Defined (1) | The PTRS RE power scaling is given by the value of PUSCH PTRS Pwr attribute.                                |
        +------------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PuschPtrsPowerMode, int):
                Specifies whether the PUSCH PTRS power scaling is calculated as defined in 3GPP specification or specified by you. This
                attribute is valid only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to
                **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PuschPtrsPowerMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_POWER_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_power(self, selector_string):
        r"""Gets the factor by which the PUSCH PTRS REs are boosted. This value is expressed in dB. This attribute is valid
        only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the factor by which the PUSCH PTRS REs are boosted. This value is expressed in dB. This attribute is valid
                only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_power(self, selector_string, value):
        r"""Sets the factor by which the PUSCH PTRS REs are boosted. This value is expressed in dB. This attribute is valid
        only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the factor by which the PUSCH PTRS REs are boosted. This value is expressed in dB. This attribute is valid
                only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_ptrs_groups(self, selector_string):
        r"""Gets the number of PTRS groups per OFDM symbol. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of PTRS groups per OFDM symbol. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_PTRS_GROUPS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_ptrs_groups(self, selector_string, value):
        r"""Sets the number of PTRS groups per OFDM symbol. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of PTRS groups per OFDM symbol. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.NUMBER_OF_PTRS_GROUPS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_samples_per_ptrs_group(self, selector_string):
        r"""Gets the number of samples per each PTRS group. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of samples per each PTRS group. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SAMPLES_PER_PTRS_GROUP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_samples_per_ptrs_group(self, selector_string, value):
        r"""Sets the number of samples per each PTRS group. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of samples per each PTRS group. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.SAMPLES_PER_PTRS_GROUP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_time_density(self, selector_string):
        r"""Gets the density of PTRS in time domain. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the density of PTRS in time domain. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_TIME_DENSITY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_time_density(self, selector_string, value):
        r"""Sets the density of PTRS in time domain. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the density of PTRS in time domain. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_TIME_DENSITY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_frequency_density(self, selector_string):
        r"""Gets the density of PTRS in frequency domain. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the density of PTRS in frequency domain. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_FREQUENCY_DENSITY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_frequency_density(self, selector_string, value):
        r"""Sets the density of PTRS in frequency domain. This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the density of PTRS in frequency domain. This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

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
                attributes.AttributeID.PUSCH_PTRS_FREQUENCY_DENSITY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_ptrs_re_offset(self, selector_string):
        r"""Gets the RE offset to be used for transmission of PTRS as defined in the Table 6.4.1.2.2.1-1 of *3GPP 38.211*
        specification.  This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **00**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the RE offset to be used for transmission of PTRS as defined in the Table 6.4.1.2.2.1-1 of *3GPP 38.211*
                specification.  This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_RE_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_ptrs_re_offset(self, selector_string, value):
        r"""Sets the RE offset to be used for transmission of PTRS as defined in the Table 6.4.1.2.2.1-1 of *3GPP 38.211*
        specification.  This attribute is valid only if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **00**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the RE offset to be used for transmission of PTRS as defined in the Table 6.4.1.2.2.1-1 of *3GPP 38.211*
                specification.  This attribute is valid only if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.

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
                updated_selector_string, attributes.AttributeID.PUSCH_PTRS_RE_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_slot_allocation(self, selector_string):
        r"""Gets the slot allocation in NR Frame. This defines the indices of the allocated slots.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to (Maximum number of slots in frame - 1), inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the slot allocation in NR Frame. This defines the indices of the allocated slots.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PUSCH_SLOT_ALLOCATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_slot_allocation(self, selector_string, value):
        r"""Sets the slot allocation in NR Frame. This defines the indices of the allocated slots.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to (Maximum number of slots in frame - 1), inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the slot allocation in NR Frame. This defines the indices of the allocated slots.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.PUSCH_SLOT_ALLOCATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pusch_symbol_allocation(self, selector_string):
        r"""Gets the symbol allocation of each slot allocation.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to 13, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the symbol allocation of each slot allocation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PUSCH_SYMBOL_ALLOCATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pusch_symbol_allocation(self, selector_string, value):
        r"""Sets the symbol allocation of each slot allocation.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to 13, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the symbol allocation of each slot allocation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.PUSCH_SYMBOL_ALLOCATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_pdsch_configurations(self, selector_string):
        r"""Gets the number of PDSCH slot configurations.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of PDSCH slot configurations.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_PDSCH_CONFIGURATIONS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_pdsch_configurations(self, selector_string, value):
        r"""Sets the number of PDSCH slot configurations.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of PDSCH slot configurations.

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
                attributes.AttributeID.NUMBER_OF_PDSCH_CONFIGURATIONS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_number_of_resource_block_clusters(self, selector_string):
        r"""Gets the number of clusters of resource allocations with each cluster including one or more consecutive resource
        blocks.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of clusters of resource allocations with each cluster including one or more consecutive resource
                blocks.

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
                attributes.AttributeID.PDSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_number_of_resource_block_clusters(self, selector_string, value):
        r"""Sets the number of clusters of resource allocations with each cluster including one or more consecutive resource
        blocks.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of clusters of resource allocations with each cluster including one or more consecutive resource
                blocks.

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
                attributes.AttributeID.PDSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_resource_block_offset(self, selector_string):
        r"""Gets the starting resource block number of a PDSCH cluster.

        Use "pdschcluster<*s*>" or "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>/pdschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting resource block number of a PDSCH cluster.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_RESOURCE_BLOCK_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_resource_block_offset(self, selector_string, value):
        r"""Sets the starting resource block number of a PDSCH cluster.

        Use "pdschcluster<*s*>" or "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>/pdschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting resource block number of a PDSCH cluster.

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
                attributes.AttributeID.PDSCH_RESOURCE_BLOCK_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_number_of_resource_blocks(self, selector_string):
        r"""Gets the number of consecutive resource blocks in a PDSCH cluster.

        Use "pdschcluster<*s*>" or "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>/pdschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks within the bandwidth
        part are configured.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of consecutive resource blocks in a PDSCH cluster.

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
                attributes.AttributeID.PDSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_number_of_resource_blocks(self, selector_string, value):
        r"""Sets the number of consecutive resource blocks in a PDSCH cluster.

        Use "pdschcluster<*s*>" or "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>/pdschcluster<*s*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is -1. If you set this attribute to -1, all available resource blocks within the bandwidth
        part are configured.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of consecutive resource blocks in a PDSCH cluster.

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
                attributes.AttributeID.PDSCH_NUMBER_OF_RESOURCE_BLOCKS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_modulation_type(self, selector_string):
        r"""Gets the modulation scheme used in PDSCH channel of the signal being measured.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | QPSK (1)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (2)   | Specifies a 16 QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (3)   | Specifies a 64 QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 256 QAM (4)  | Specifies a 256 QAM modulation scheme.  |
        +--------------+-----------------------------------------+
        | 1024 QAM (5) | Specifies a 1024 QAM modulation scheme. |
        +--------------+-----------------------------------------+
        | 8 PSK (100)  | Specifies an 8 PSK modulation scheme.   |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschModulationType):
                Specifies the modulation scheme used in PDSCH channel of the signal being measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_MODULATION_TYPE.value
            )
            attr_val = enums.PdschModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_modulation_type(self, selector_string, value):
        r"""Sets the modulation scheme used in PDSCH channel of the signal being measured.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **QPSK**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | QPSK (1)     | Specifies a QPSK modulation scheme.     |
        +--------------+-----------------------------------------+
        | 16 QAM (2)   | Specifies a 16 QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 64 QAM (3)   | Specifies a 64 QAM modulation scheme.   |
        +--------------+-----------------------------------------+
        | 256 QAM (4)  | Specifies a 256 QAM modulation scheme.  |
        +--------------+-----------------------------------------+
        | 1024 QAM (5) | Specifies a 1024 QAM modulation scheme. |
        +--------------+-----------------------------------------+
        | 8 PSK (100)  | Specifies an 8 PSK modulation scheme.   |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschModulationType, int):
                Specifies the modulation scheme used in PDSCH channel of the signal being measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschModulationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_MODULATION_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_release_version(self, selector_string):
        r"""Gets the 3GGP release version for PDSCH DMRS.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        +---------------+--------------------------------------------------------+
        | Name (Value)  | Description                                            |
        +===============+========================================================+
        | Release15 (0) | Specifies a 3GGP release version of 15 for PDSCH DMRS. |
        +---------------+--------------------------------------------------------+
        | Release16 (1) | Specifies a 3GGP release version of 16 for PDSCH DMRS. |
        +---------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschDmrsReleaseVersion):
                Specifies the 3GGP release version for PDSCH DMRS.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_RELEASE_VERSION.value
            )
            attr_val = enums.PdschDmrsReleaseVersion(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_release_version(self, selector_string, value):
        r"""Sets the 3GGP release version for PDSCH DMRS.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        +---------------+--------------------------------------------------------+
        | Name (Value)  | Description                                            |
        +===============+========================================================+
        | Release15 (0) | Specifies a 3GGP release version of 15 for PDSCH DMRS. |
        +---------------+--------------------------------------------------------+
        | Release16 (1) | Specifies a 3GGP release version of 16 for PDSCH DMRS. |
        +---------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschDmrsReleaseVersion, int):
                Specifies the 3GGP release version for PDSCH DMRS.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschDmrsReleaseVersion else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PDSCH_DMRS_RELEASE_VERSION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_antenna_ports(self, selector_string):
        r"""Gets the antenna ports used for DMRS transmission.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1000.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the antenna ports used for DMRS transmission.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_ANTENNA_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_antenna_ports(self, selector_string, value):
        r"""Sets the antenna ports used for DMRS transmission.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1000.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the antenna ports used for DMRS transmission.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string,
                attributes.AttributeID.PDSCH_DMRS_ANTENNA_PORTS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_power_mode(self, selector_string):
        r"""Gets whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_POWER` is calculated based on
        the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_NUMBER_OF_CDM_GROUPS` or specified by you.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **CDM Groups**.

        +------------------+--------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                    |
        +==================+================================================================================+
        | CDM Groups (0)   | The value of PDSCH DMRS power is calculated based on the number of CDM groups. |
        +------------------+--------------------------------------------------------------------------------+
        | User Defined (1) | The value of PDSCH DMRS power is specified by you.                             |
        +------------------+--------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschDmrsPowerMode):
                Specifies whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_POWER` is calculated based on
                the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_NUMBER_OF_CDM_GROUPS` or specified by you.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_POWER_MODE.value
            )
            attr_val = enums.PdschDmrsPowerMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_power_mode(self, selector_string, value):
        r"""Sets whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_POWER` is calculated based on
        the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_NUMBER_OF_CDM_GROUPS` or specified by you.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **CDM Groups**.

        +------------------+--------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                    |
        +==================+================================================================================+
        | CDM Groups (0)   | The value of PDSCH DMRS power is calculated based on the number of CDM groups. |
        +------------------+--------------------------------------------------------------------------------+
        | User Defined (1) | The value of PDSCH DMRS power is specified by you.                             |
        +------------------+--------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschDmrsPowerMode, int):
                Specifies whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_POWER` is calculated based on
                the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_NUMBER_OF_CDM_GROUPS` or specified by you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschDmrsPowerMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_POWER_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_power(self, selector_string):
        r"""Gets the factor by which the PDSCH DMRS REs are boosted. This value is expressed in dB.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the factor by which the PDSCH DMRS REs are boosted. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_power(self, selector_string, value):
        r"""Sets the factor by which the PDSCH DMRS REs are boosted. This value is expressed in dB.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the factor by which the PDSCH DMRS REs are boosted. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_number_of_cdm_groups(self, selector_string):
        r"""Gets the number of CDM groups.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of CDM groups.

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
                attributes.AttributeID.PDSCH_DMRS_NUMBER_OF_CDM_GROUPS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_number_of_cdm_groups(self, selector_string, value):
        r"""Sets the number of CDM groups.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of CDM groups.

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
                attributes.AttributeID.PDSCH_DMRS_NUMBER_OF_CDM_GROUPS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_scrambling_id_mode(self, selector_string):
        r"""Gets whether the configured Scrambling ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or
        specified by you.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Cell ID**.

        +------------------+------------------------------------------------------------+
        | Name (Value)     | Description                                                |
        +==================+============================================================+
        | Cell ID (0)      | The value of PDSCH DMRS Scrambling ID is based on Cell ID. |
        +------------------+------------------------------------------------------------+
        | User Defined (1) | The value of PDSCH DMRS Scrambling ID is specified by you. |
        +------------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschDmrsScramblingIDMode):
                Specifies whether the configured Scrambling ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or
                specified by you.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_SCRAMBLING_ID_MODE.value
            )
            attr_val = enums.PdschDmrsScramblingIDMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_scrambling_id_mode(self, selector_string, value):
        r"""Sets whether the configured Scrambling ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or
        specified by you.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Cell ID**.

        +------------------+------------------------------------------------------------+
        | Name (Value)     | Description                                                |
        +==================+============================================================+
        | Cell ID (0)      | The value of PDSCH DMRS Scrambling ID is based on Cell ID. |
        +------------------+------------------------------------------------------------+
        | User Defined (1) | The value of PDSCH DMRS Scrambling ID is specified by you. |
        +------------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschDmrsScramblingIDMode, int):
                Specifies whether the configured Scrambling ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or
                specified by you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschDmrsScramblingIDMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PDSCH_DMRS_SCRAMBLING_ID_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_scrambling_id(self, selector_string):
        r"""Gets the value of scrambling ID used for reference signal generation.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the value of scrambling ID used for reference signal generation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_SCRAMBLING_ID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_scrambling_id(self, selector_string, value):
        r"""Sets the value of scrambling ID used for reference signal generation.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the value of scrambling ID used for reference signal generation.

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
                attributes.AttributeID.PDSCH_DMRS_SCRAMBLING_ID.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrsn_scid(self, selector_string):
        r"""Gets the value of PDSCH DMRS nSCID used for reference signal generation.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the value of PDSCH DMRS nSCID used for reference signal generation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_NSCID.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrsn_scid(self, selector_string, value):
        r"""Sets the value of PDSCH DMRS nSCID used for reference signal generation.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the value of PDSCH DMRS nSCID used for reference signal generation.

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
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_NSCID.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_configuration_type(self, selector_string):
        r"""Gets the configuration type of DMRS.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type 1**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Type 1 (0)   | One DMRS subcarrier alternates with one data subcarrier.                           |
        +--------------+------------------------------------------------------------------------------------+
        | Type 2 (1)   | Two consecutive DMRS subcarriers alternate with four consecutive data subcarriers. |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschDmrsConfigurationType):
                Specifies the configuration type of DMRS.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_CONFIGURATION_TYPE.value
            )
            attr_val = enums.PdschDmrsConfigurationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_configuration_type(self, selector_string, value):
        r"""Sets the configuration type of DMRS.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type 1**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Type 1 (0)   | One DMRS subcarrier alternates with one data subcarrier.                           |
        +--------------+------------------------------------------------------------------------------------+
        | Type 2 (1)   | Two consecutive DMRS subcarriers alternate with four consecutive data subcarriers. |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschDmrsConfigurationType, int):
                Specifies the configuration type of DMRS.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschDmrsConfigurationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.PDSCH_DMRS_CONFIGURATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_mapping_type(self, selector_string):
        r"""Gets the mapping type of DMRS.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type A**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | Type A (0)   | The first DMRS symbol index in a slot is either 2 or 3. |
        +--------------+---------------------------------------------------------+
        | Type B (1)   | The first DMRS symbol index in a slot is 0.             |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschMappingType):
                Specifies the mapping type of DMRS.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_MAPPING_TYPE.value
            )
            attr_val = enums.PdschMappingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_mapping_type(self, selector_string, value):
        r"""Sets the mapping type of DMRS.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Type A**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | Type A (0)   | The first DMRS symbol index in a slot is either 2 or 3. |
        +--------------+---------------------------------------------------------+
        | Type B (1)   | The first DMRS symbol index in a slot is 0.             |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschMappingType, int):
                Specifies the mapping type of DMRS.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschMappingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_MAPPING_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_type_a_position(self, selector_string):
        r"""Gets the position of first DMRS symbol in a slot for Type A configurations.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the position of first DMRS symbol in a slot for Type A configurations.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_TYPE_A_POSITION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_type_a_position(self, selector_string, value):
        r"""Sets the position of first DMRS symbol in a slot for Type A configurations.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the position of first DMRS symbol in a slot for Type A configurations.

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
                attributes.AttributeID.PDSCH_DMRS_TYPE_A_POSITION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_duration(self, selector_string):
        r"""Gets whether the DMRS is single-symbol or double-symbol.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Single-Symbol**.

        +-------------------+-------------------------------------------------------------------------+
        | Name (Value)      | Description                                                             |
        +===================+=========================================================================+
        | Single-Symbol (1) | There are no consecutive DMRS symbols in the slot.                      |
        +-------------------+-------------------------------------------------------------------------+
        | Double-Symbol (2) | There are one or more sets of two consecutive DMRS symbols in the slot. |
        +-------------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschDmrsDuration):
                Specifies whether the DMRS is single-symbol or double-symbol.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_DURATION.value
            )
            attr_val = enums.PdschDmrsDuration(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_duration(self, selector_string, value):
        r"""Sets whether the DMRS is single-symbol or double-symbol.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Single-Symbol**.

        +-------------------+-------------------------------------------------------------------------+
        | Name (Value)      | Description                                                             |
        +===================+=========================================================================+
        | Single-Symbol (1) | There are no consecutive DMRS symbols in the slot.                      |
        +-------------------+-------------------------------------------------------------------------+
        | Double-Symbol (2) | There are one or more sets of two consecutive DMRS symbols in the slot. |
        +-------------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschDmrsDuration, int):
                Specifies whether the DMRS is single-symbol or double-symbol.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschDmrsDuration else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_DMRS_DURATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_additional_positions(self, selector_string):
        r"""Gets the number of additional sets of consecutive DMRS symbols in a slot.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of additional sets of consecutive DMRS symbols in a slot.

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
                attributes.AttributeID.PDSCH_DMRS_ADDITIONAL_POSITIONS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_dmrs_additional_positions(self, selector_string, value):
        r"""Sets the number of additional sets of consecutive DMRS symbols in a slot.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of additional sets of consecutive DMRS symbols in a slot.

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
                attributes.AttributeID.PDSCH_DMRS_ADDITIONAL_POSITIONS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_enabled(self, selector_string):
        r"""Gets whether PT-RS is present in the transmitted signal.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------------------------------------+
        | Name (Value) | Description                                              |
        +==============+==========================================================+
        | False (0)    | Detection of PTRS in the transmitted signal is disabled. |
        +--------------+----------------------------------------------------------+
        | True (1)     | Detection of PTRS in the transmitted signal is enabled.  |
        +--------------+----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschPtrsEnabled):
                Specifies whether PT-RS is present in the transmitted signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_ENABLED.value
            )
            attr_val = enums.PdschPtrsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_enabled(self, selector_string, value):
        r"""Sets whether PT-RS is present in the transmitted signal.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+----------------------------------------------------------+
        | Name (Value) | Description                                              |
        +==============+==========================================================+
        | False (0)    | Detection of PTRS in the transmitted signal is disabled. |
        +--------------+----------------------------------------------------------+
        | True (1)     | Detection of PTRS in the transmitted signal is enabled.  |
        +--------------+----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschPtrsEnabled, int):
                Specifies whether PT-RS is present in the transmitted signal.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschPtrsEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_antenna_ports(self, selector_string):
        r"""Gets the DMRS Antenna Ports associated with PTRS transmission.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the DMRS Antenna Ports associated with PTRS transmission.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_ANTENNA_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_antenna_ports(self, selector_string, value):
        r"""Sets the DMRS Antenna Ports associated with PTRS transmission.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the DMRS Antenna Ports associated with PTRS transmission.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string,
                attributes.AttributeID.PDSCH_PTRS_ANTENNA_PORTS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_power_mode(self, selector_string):
        r"""Gets whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER` is calculated as defined
        in 3GPP specification or configured by you.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Standard**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Standard (0)     | The PTRS RE power scaling is computed as defined in the Table 4.1-2 of 3GPP TS 38.214 specification using the value of   |
        |                  | EPRE Ratio Port attribute..                                                                                              |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (1) | The PTRS RE power scaling is given by the value of PDSCH PTRS Pwr attribute.                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PdschPtrsPowerMode):
                Specifies whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER` is calculated as defined
                in 3GPP specification or configured by you.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_POWER_MODE.value
            )
            attr_val = enums.PdschPtrsPowerMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_power_mode(self, selector_string, value):
        r"""Sets whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER` is calculated as defined
        in 3GPP specification or configured by you.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Standard**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Standard (0)     | The PTRS RE power scaling is computed as defined in the Table 4.1-2 of 3GPP TS 38.214 specification using the value of   |
        |                  | EPRE Ratio Port attribute..                                                                                              |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (1) | The PTRS RE power scaling is given by the value of PDSCH PTRS Pwr attribute.                                             |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PdschPtrsPowerMode, int):
                Specifies whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER` is calculated as defined
                in 3GPP specification or configured by you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.PdschPtrsPowerMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_POWER_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_epre_ratio_port(self, selector_string):
        r"""Gets the EPRE Ratio Port used to determine the PDSCH PT-RS RE power scaling as defined in the Table 4.1-2 of *3GPP
        TS 38.214* specification when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute
        to **Standard**.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the EPRE Ratio Port used to determine the PDSCH PT-RS RE power scaling as defined in the Table 4.1-2 of *3GPP
                TS 38.214* specification when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute
                to **Standard**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.EPRE_RATIO_PORT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_epre_ratio_port(self, selector_string, value):
        r"""Sets the EPRE Ratio Port used to determine the PDSCH PT-RS RE power scaling as defined in the Table 4.1-2 of *3GPP
        TS 38.214* specification when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute
        to **Standard**.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the EPRE Ratio Port used to determine the PDSCH PT-RS RE power scaling as defined in the Table 4.1-2 of *3GPP
                TS 38.214* specification when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute
                to **Standard**.

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
                updated_selector_string, attributes.AttributeID.EPRE_RATIO_PORT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_power(self, selector_string):
        r"""Gets the factor by which the PDSCH PTRS REs are boosted, compared to PDSCH REs. This value is expressed in dB. The
        value of this attribute is taken as an input when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute to **User Defined**. If you set the PDSCH
        PTRS Pwr Mode attribute to **Standard**, the value is computed from other parameters.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the factor by which the PDSCH PTRS REs are boosted, compared to PDSCH REs. This value is expressed in dB. The
                value of this attribute is taken as an input when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute to **User Defined**. If you set the PDSCH
                PTRS Pwr Mode attribute to **Standard**, the value is computed from other parameters.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_power(self, selector_string, value):
        r"""Sets the factor by which the PDSCH PTRS REs are boosted, compared to PDSCH REs. This value is expressed in dB. The
        value of this attribute is taken as an input when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute to **User Defined**. If you set the PDSCH
        PTRS Pwr Mode attribute to **Standard**, the value is computed from other parameters.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the factor by which the PDSCH PTRS REs are boosted, compared to PDSCH REs. This value is expressed in dB. The
                value of this attribute is taken as an input when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute to **User Defined**. If you set the PDSCH
                PTRS Pwr Mode attribute to **Standard**, the value is computed from other parameters.

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
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_time_density(self, selector_string):
        r"""Gets the density of PTRS in time domain

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the density of PTRS in time domain

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_TIME_DENSITY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_time_density(self, selector_string, value):
        r"""Sets the density of PTRS in time domain

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the density of PTRS in time domain

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
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_TIME_DENSITY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_frequency_density(self, selector_string):
        r"""Gets the density of PTRS in frequency domain

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the density of PTRS in frequency domain

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_FREQUENCY_DENSITY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_frequency_density(self, selector_string, value):
        r"""Sets the density of PTRS in frequency domain

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the density of PTRS in frequency domain

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
                attributes.AttributeID.PDSCH_PTRS_FREQUENCY_DENSITY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_re_offset(self, selector_string):
        r"""Gets the RE Offset to be used for transmission of PTRS as defined in Table 7.4.1.2.2-1 of *3GPP 38.211*
        specification.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **00**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the RE Offset to be used for transmission of PTRS as defined in Table 7.4.1.2.2-1 of *3GPP 38.211*
                specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_RE_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_ptrs_re_offset(self, selector_string, value):
        r"""Sets the RE Offset to be used for transmission of PTRS as defined in Table 7.4.1.2.2-1 of *3GPP 38.211*
        specification.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **00**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the RE Offset to be used for transmission of PTRS as defined in Table 7.4.1.2.2-1 of *3GPP 38.211*
                specification.

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
                updated_selector_string, attributes.AttributeID.PDSCH_PTRS_RE_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_slot_allocation(self, selector_string):
        r"""Gets the slot allocation in NR Frame. This defines the indices of the allocated slots.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to (Maximum number of slots in frame - 1), inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the slot allocation in NR Frame. This defines the indices of the allocated slots.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PDSCH_SLOT_ALLOCATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_slot_allocation(self, selector_string, value):
        r"""Sets the slot allocation in NR Frame. This defines the indices of the allocated slots.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to (Maximum number of slots in frame - 1), inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the slot allocation in NR Frame. This defines the indices of the allocated slots.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.PDSCH_SLOT_ALLOCATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdsch_symbol_allocation(self, selector_string):
        r"""Gets the symbol allocation of each slot allocation.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to 13, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the symbol allocation of each slot allocation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PDSCH_SYMBOL_ALLOCATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdsch_symbol_allocation(self, selector_string, value):
        r"""Sets the symbol allocation of each slot allocation.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-Last. Valid values are from 0 to 13, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the symbol allocation of each slot allocation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.PDSCH_SYMBOL_ALLOCATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_coresets(self, selector_string):
        r"""Gets the number of CORSETs present in the bandwidth part.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*> as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of CORSETs present in the bandwidth part.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_CORESETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_coresets(self, selector_string, value):
        r"""Sets the number of CORSETs present in the bandwidth part.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*> as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
        attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of CORSETs present in the bandwidth part.

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
                updated_selector_string, attributes.AttributeID.NUMBER_OF_CORESETS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_symbol_offset(self, selector_string):
        r"""Gets the starting symbol number of the CORESET within a slot.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting symbol number of the CORESET within a slot.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_SYMBOL_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_symbol_offset(self, selector_string, value):
        r"""Sets the starting symbol number of the CORESET within a slot.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting symbol number of the CORESET within a slot.

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
                updated_selector_string, attributes.AttributeID.CORESET_SYMBOL_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_number_of_symbols(self, selector_string):
        r"""Gets the number of symbols allotted to CORESET in each slot.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of symbols allotted to CORESET in each slot.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_NUMBER_OF_SYMBOLS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_number_of_symbols(self, selector_string, value):
        r"""Sets the number of symbols allotted to CORESET in each slot.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of symbols allotted to CORESET in each slot.

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
                attributes.AttributeID.CORESET_NUMBER_OF_SYMBOLS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_number_of_resource_block_clusters(self, selector_string):
        r"""Gets the number of RB clusters present in the CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of RB clusters present in the CORESET.

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
                attributes.AttributeID.CORESET_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_number_of_resource_block_clusters(self, selector_string, value):
        r"""Sets the number of RB clusters present in the CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of RB clusters present in the CORESET.

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
                attributes.AttributeID.CORESET_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_resource_block_offset(self, selector_string):
        r"""Gets the starting resource block of a CORESET cluster.

        Use "coresetcluster<*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/coresetcluster<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Valid values should be a multiple of 6. The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the starting resource block of a CORESET cluster.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_RESOURCE_BLOCK_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_resource_block_offset(self, selector_string, value):
        r"""Sets the starting resource block of a CORESET cluster.

        Use "coresetcluster<*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/coresetcluster<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Valid values should be a multiple of 6. The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the starting resource block of a CORESET cluster.

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
                attributes.AttributeID.CORESET_RESOURCE_BLOCK_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_number_of_resource_blocks(self, selector_string):
        r"""Gets the number of consecutive resource blocks of CORESET cluster.

        Use "coresetcluster<*k*>" or "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"/coresetcluster<*k*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The value should be a multiple of 6. The default value is -1. If you set this attribute to the default value,
        all available resource blocks within the bandwidth part are configured.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of consecutive resource blocks of CORESET cluster.

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
                attributes.AttributeID.CORESET_NUMBER_OF_RESOURCE_BLOCKS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_number_of_resource_blocks(self, selector_string, value):
        r"""Sets the number of consecutive resource blocks of CORESET cluster.

        Use "coresetcluster<*k*>" or "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"/coresetcluster<*k*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The value should be a multiple of 6. The default value is -1. If you set this attribute to the default value,
        all available resource blocks within the bandwidth part are configured.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of consecutive resource blocks of CORESET cluster.

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
                attributes.AttributeID.CORESET_NUMBER_OF_RESOURCE_BLOCKS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_precoding_granularity(self, selector_string):
        r"""Gets the precoding granularity of the CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Same As REG Bundle**.

        +------------------------------------+-----------------------------------------------------------------+
        | Name (Value)                       | Description                                                     |
        +====================================+=================================================================+
        | Same As REG Bundle (0)             | Precoding granularity is set to Same As REG Bundle.             |
        +------------------------------------+-----------------------------------------------------------------+
        | All Contiguous Resource Blocks (1) | Precoding granularity is set to All Contiguous Resource Blocks. |
        +------------------------------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.CoresetPrecodingGranularity):
                Specifies the precoding granularity of the CORESET.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_PRECODING_GRANULARITY.value
            )
            attr_val = enums.CoresetPrecodingGranularity(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_precoding_granularity(self, selector_string, value):
        r"""Sets the precoding granularity of the CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Same As REG Bundle**.

        +------------------------------------+-----------------------------------------------------------------+
        | Name (Value)                       | Description                                                     |
        +====================================+=================================================================+
        | Same As REG Bundle (0)             | Precoding granularity is set to Same As REG Bundle.             |
        +------------------------------------+-----------------------------------------------------------------+
        | All Contiguous Resource Blocks (1) | Precoding granularity is set to All Contiguous Resource Blocks. |
        +------------------------------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.CoresetPrecodingGranularity, int):
                Specifies the precoding granularity of the CORESET.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.CoresetPrecodingGranularity else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CORESET_PRECODING_GRANULARITY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_cce_to_reg_mapping_type(self, selector_string):
        r"""Gets the CCE-to-REG mapping type of CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Non-Interleaved**.

        +---------------------+----------------------------------+
        | Name (Value)        | Description                      |
        +=====================+==================================+
        | Non-Interleaved (0) | Mapping type is non-interleaved. |
        +---------------------+----------------------------------+
        | Interleaved (1)     | Mapping type is interleaved.     |
        +---------------------+----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.CoresetCceToRegMappingType):
                Specifies the CCE-to-REG mapping type of CORESET.

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
                attributes.AttributeID.CORESET_CCE_TO_REG_MAPPING_TYPE.value,
            )
            attr_val = enums.CoresetCceToRegMappingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_cce_to_reg_mapping_type(self, selector_string, value):
        r"""Sets the CCE-to-REG mapping type of CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Non-Interleaved**.

        +---------------------+----------------------------------+
        | Name (Value)        | Description                      |
        +=====================+==================================+
        | Non-Interleaved (0) | Mapping type is non-interleaved. |
        +---------------------+----------------------------------+
        | Interleaved (1)     | Mapping type is interleaved.     |
        +---------------------+----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.CoresetCceToRegMappingType, int):
                Specifies the CCE-to-REG mapping type of CORESET.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.CoresetCceToRegMappingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CORESET_CCE_TO_REG_MAPPING_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_reg_bundle_size(self, selector_string):
        r"""Gets the RBG bundle size of CORESET for interleaved CCE to REG mapping.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **6**.

        For interleaved Mapping Type, the valid values are 2, 3, and 6. For non-interleaved Mapping Type, the valid
        value is 6.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the RBG bundle size of CORESET for interleaved CCE to REG mapping.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_REG_BUNDLE_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_reg_bundle_size(self, selector_string, value):
        r"""Sets the RBG bundle size of CORESET for interleaved CCE to REG mapping.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **6**.

        For interleaved Mapping Type, the valid values are 2, 3, and 6. For non-interleaved Mapping Type, the valid
        value is 6.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the RBG bundle size of CORESET for interleaved CCE to REG mapping.

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
                updated_selector_string, attributes.AttributeID.CORESET_REG_BUNDLE_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_interleaver_size(self, selector_string):
        r"""Gets the interleaver size of CORESET for interleaved CCE to REG mapping.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the interleaver size of CORESET for interleaved CCE to REG mapping.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_INTERLEAVER_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_interleaver_size(self, selector_string, value):
        r"""Sets the interleaver size of CORESET for interleaved CCE to REG mapping.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **2**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the interleaver size of CORESET for interleaved CCE to REG mapping.

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
                attributes.AttributeID.CORESET_INTERLEAVER_SIZE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_coreset_shift_index(self, selector_string):
        r"""Gets the shift index of CORESET for interleaved CCE to REG mapping.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the shift index of CORESET for interleaved CCE to REG mapping.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CORESET_SHIFT_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_coreset_shift_index(self, selector_string, value):
        r"""Sets the shift index of CORESET for interleaved CCE to REG mapping.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the shift index of CORESET for interleaved CCE to REG mapping.

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
                updated_selector_string, attributes.AttributeID.CORESET_SHIFT_INDEX.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_pdcch_configurations(self, selector_string):
        r"""Gets the number of PDCCH Configurations for a CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of PDCCH Configurations for a CORESET.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.NUMBER_OF_PDCCH_CONFIGURATIONS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_pdcch_configurations(self, selector_string, value):
        r"""Sets the number of PDCCH Configurations for a CORESET.

        Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of PDCCH Configurations for a CORESET.

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
                attributes.AttributeID.NUMBER_OF_PDCCH_CONFIGURATIONS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdcch_cce_aggregation_level(self, selector_string):
        r"""Gets the CCE aggregation level of PDCCH.

        Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the CCE aggregation level of PDCCH.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDCCH_CCE_AGGREGATION_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdcch_cce_aggregation_level(self, selector_string, value):
        r"""Sets the CCE aggregation level of PDCCH.

        Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the CCE aggregation level of PDCCH.

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
                attributes.AttributeID.PDCCH_CCE_AGGREGATION_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdcch_cce_offset(self, selector_string):
        r"""Gets the PDCCH CCE offset.

        Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        It is used when the PDCCH Candidate Index is set to -1. The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the PDCCH CCE offset.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.PDCCH_CCE_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdcch_cce_offset(self, selector_string, value):
        r"""Sets the PDCCH CCE offset.

        Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        It is used when the PDCCH Candidate Index is set to -1. The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the PDCCH CCE offset.

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
                updated_selector_string, attributes.AttributeID.PDCCH_CCE_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pdcch_slot_allocation(self, selector_string):
        r"""Gets the slot allocation in NR frame. This defines the indices of the allocated slots.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-last. Valid values are between 0 and (Maximum Slots in Frame - 1).

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the slot allocation in NR frame. This defines the indices of the allocated slots.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.PDCCH_SLOT_ALLOCATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pdcch_slot_allocation(self, selector_string, value):
        r"""Sets the slot allocation in NR frame. This defines the indices of the allocated slots.

        The format is defined by range format specifiers. The range format specifier is a comma separated list of
        entries in the following format:<ul>
        <li>Single unsigned integer values or last</li>
        <li>A range of single unsigned integer values given as i0:i1, where i0 represents the first and i1 the last
        value in the range, with i0 <= i1. The keyword last expands to the largest allowed value, depending on the context of
        the range specification.</li>
        </ul>

        Examples: 2,5 will expand to {2,5}

        1:3,7 will expand to {1,2,3,7}.

        Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0-last. Valid values are between 0 and (Maximum Slots in Frame - 1).

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the slot allocation in NR frame. This defines the indices of the allocated slots.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.PDCCH_SLOT_ALLOCATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_enabled(self, selector_string):
        r"""Gets whether synchronization signal block (SSB) is present in the transmitted signal.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | Detection of SSB in the transmitted signal is disabled. |
        +--------------+---------------------------------------------------------+
        | True (1)     | Detection of SSB in the transmitted signal is enabled.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SsbEnabled):
                Specifies whether synchronization signal block (SSB) is present in the transmitted signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_ENABLED.value
            )
            attr_val = enums.SsbEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_enabled(self, selector_string, value):
        r"""Sets whether synchronization signal block (SSB) is present in the transmitted signal.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | Detection of SSB in the transmitted signal is disabled. |
        +--------------+---------------------------------------------------------+
        | True (1)     | Detection of SSB in the transmitted signal is enabled.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SsbEnabled, int):
                Specifies whether synchronization signal block (SSB) is present in the transmitted signal.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SsbEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_grid_start(self, selector_string):
        r"""Gets the SSB resource grid start relative to Reference Point A in terms of resource block offset.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the SSB resource grid start relative to Reference Point A in terms of resource block offset.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_GRID_START.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_grid_start(self, selector_string, value):
        r"""Sets the SSB resource grid start relative to Reference Point A in terms of resource block offset.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the SSB resource grid start relative to Reference Point A in terms of resource block offset.

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
                updated_selector_string, attributes.AttributeID.SSB_GRID_START.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_grid_size(self, selector_string):
        r"""Gets the SSB resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
        attribute to **Manual**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the SSB resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
                attribute to **Manual**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_GRID_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_grid_size(self, selector_string, value):
        r"""Sets the SSB resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
        attribute to **Manual**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the SSB resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
                attribute to **Manual**.

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
                updated_selector_string, attributes.AttributeID.SSB_GRID_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_crb_offset(self, selector_string):
        r"""Gets the CRB offset for the SS/PBCH block relative to the reference Point A in units of 15 kHz resource blocks for
        frequency range 1 or 60 kHz resource blocks for frequency range 2-1 and frequency range 2-2.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the CRB offset for the SS/PBCH block relative to the reference Point A in units of 15 kHz resource blocks for
                frequency range 1 or 60 kHz resource blocks for frequency range 2-1 and frequency range 2-2.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_CRB_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_crb_offset(self, selector_string, value):
        r"""Sets the CRB offset for the SS/PBCH block relative to the reference Point A in units of 15 kHz resource blocks for
        frequency range 1 or 60 kHz resource blocks for frequency range 2-1 and frequency range 2-2.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the CRB offset for the SS/PBCH block relative to the reference Point A in units of 15 kHz resource blocks for
                frequency range 1 or 60 kHz resource blocks for frequency range 2-1 and frequency range 2-2.

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
                updated_selector_string, attributes.AttributeID.SSB_CRB_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subcarrier_spacing_common(self, selector_string):
        r"""Gets the basic unit of :py:attr:`~nirfmxnr.attributes.AttributeID.SSB_SUBCARRIER_OFFSET` attribute for frequency
        range 2-1 and frequency range 2-2. The attribute refers to the MIB control element subCarrierSpacingCommon in *3GPP TS
        38.331*.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **60kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the basic unit of :py:attr:`~nirfmxnr.attributes.AttributeID.SSB_SUBCARRIER_OFFSET` attribute for frequency
                range 2-1 and frequency range 2-2. The attribute refers to the MIB control element subCarrierSpacingCommon in *3GPP TS
                38.331*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SUBCARRIER_SPACING_COMMON.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subcarrier_spacing_common(self, selector_string, value):
        r"""Sets the basic unit of :py:attr:`~nirfmxnr.attributes.AttributeID.SSB_SUBCARRIER_OFFSET` attribute for frequency
        range 2-1 and frequency range 2-2. The attribute refers to the MIB control element subCarrierSpacingCommon in *3GPP TS
        38.331*.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **60kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the basic unit of :py:attr:`~nirfmxnr.attributes.AttributeID.SSB_SUBCARRIER_OFFSET` attribute for frequency
                range 2-1 and frequency range 2-2. The attribute refers to the MIB control element subCarrierSpacingCommon in *3GPP TS
                38.331*.

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
                attributes.AttributeID.SUBCARRIER_SPACING_COMMON.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_subcarrier_offset(self, selector_string):
        r"""Gets an additional subcarrier offset for the SS/PBCH block in units of resource blocks of 15 kHz subcarrier
        spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON` attribute for frequency range 1,
        and of 60kHz subcarrier spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON`
        attribute for frequency range 2-1 and frequency range 2-2.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies an additional subcarrier offset for the SS/PBCH block in units of resource blocks of 15 kHz subcarrier
                spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON` attribute for frequency range 1,
                and of 60kHz subcarrier spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON`
                attribute for frequency range 2-1 and frequency range 2-2.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_SUBCARRIER_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_subcarrier_offset(self, selector_string, value):
        r"""Sets an additional subcarrier offset for the SS/PBCH block in units of resource blocks of 15 kHz subcarrier
        spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON` attribute for frequency range 1,
        and of 60kHz subcarrier spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON`
        attribute for frequency range 2-1 and frequency range 2-2.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies an additional subcarrier offset for the SS/PBCH block in units of resource blocks of 15 kHz subcarrier
                spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON` attribute for frequency range 1,
                and of 60kHz subcarrier spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON`
                attribute for frequency range 2-1 and frequency range 2-2.

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
                updated_selector_string, attributes.AttributeID.SSB_SUBCARRIER_OFFSET.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_periodicity(self, selector_string):
        r"""Gets the time difference with which the SS/PBCH block transmit pattern repeats.

        Possible values are 5 ms, 10 ms, 20 ms, 40 ms, 80 ms, and 160 ms.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **5 ms**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time difference with which the SS/PBCH block transmit pattern repeats.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SSB_PERIODICITY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_periodicity(self, selector_string, value):
        r"""Sets the time difference with which the SS/PBCH block transmit pattern repeats.

        Possible values are 5 ms, 10 ms, 20 ms, 40 ms, 80 ms, and 160 ms.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **5 ms**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time difference with which the SS/PBCH block transmit pattern repeats.

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
                updated_selector_string, attributes.AttributeID.SSB_PERIODICITY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_pattern(self, selector_string):
        r"""Gets the candidate SS/PBCH blocks with different subcarrier spacing configurations as defined in the section 4.1
        of *3GPP TS 38.213* specification. In order to configure **Case C up to 1.88GHz** unpaired spectrum, configure this
        attribute to **Case C up to 3GHz**. Similarly, to configure **Case C 1.88GHz to 6GHz** unpaired spectrum, configure
        this attribute to **Case C 3GHz to 6GHz**.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Case B 3GHz to 6GHz**.

        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)            | Description                                                                                                              |
        +=========================+==========================================================================================================================+
        | Case A up to 3GHz (0)   | Use with 15 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0 or 1.                                                                                                       |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case A 3GHz to 6GHz (1) | Use with 15 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0, 1, 2, or 3.                                                                                                |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case B up to 3GHz (2)   | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {4, 8, 16, 20} +   |
        |                         | 28 * n, where n is 0.                                                                                                    |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case B 3GHz to 6GHz (3) | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {4, 8, 16, 20} +   |
        |                         | 28 * n, where n is 0, 1, 2, or 3.                                                                                        |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case C up to 3GHz (4)   | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0 or 1.                                                                                                       |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case C 3GHz to 6GHz (5) | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0, 1, 2, or 3.                                                                                                |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case D (6)              | Use with 120 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {4, 8, 16, 20} + 28  |
        |                         | * n.                                                                                                                     |
        |                         | For carrier frequencies within FR-2, n is 0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, or 18.                     |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case E (7)              | Use with 240 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {8, 12, 16, 20, 32,  |
        |                         | 36, 40, 44} + 56 * n.                                                                                                    |
        |                         | For carrier frequencies within FR2-1, n is 0, 1, 2, 3, 5, 6, 7, or 8.                                                    |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case F (8)              | Use with 480 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {2, 9} + 14 * n.     |
        |                         | For carrier frequencies within FR2-2, n is 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,     |
        |                         | 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, or 31.                                                                           |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case G (9)              | Use with 960 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {2, 9} + 14 * n.     |
        |                         | For carrier frequencies within FR2-2, n is 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,     |
        |                         | 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, or 31.                                                                           |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SsbPattern):
                Specifies the candidate SS/PBCH blocks with different subcarrier spacing configurations as defined in the section 4.1
                of *3GPP TS 38.213* specification. In order to configure **Case C up to 1.88GHz** unpaired spectrum, configure this
                attribute to **Case C up to 3GHz**. Similarly, to configure **Case C 1.88GHz to 6GHz** unpaired spectrum, configure
                this attribute to **Case C 3GHz to 6GHz**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_PATTERN.value
            )
            attr_val = enums.SsbPattern(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_pattern(self, selector_string, value):
        r"""Sets the candidate SS/PBCH blocks with different subcarrier spacing configurations as defined in the section 4.1
        of *3GPP TS 38.213* specification. In order to configure **Case C up to 1.88GHz** unpaired spectrum, configure this
        attribute to **Case C up to 3GHz**. Similarly, to configure **Case C 1.88GHz to 6GHz** unpaired spectrum, configure
        this attribute to **Case C 3GHz to 6GHz**.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Case B 3GHz to 6GHz**.

        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)            | Description                                                                                                              |
        +=========================+==========================================================================================================================+
        | Case A up to 3GHz (0)   | Use with 15 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0 or 1.                                                                                                       |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case A 3GHz to 6GHz (1) | Use with 15 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0, 1, 2, or 3.                                                                                                |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case B up to 3GHz (2)   | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {4, 8, 16, 20} +   |
        |                         | 28 * n, where n is 0.                                                                                                    |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case B 3GHz to 6GHz (3) | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {4, 8, 16, 20} +   |
        |                         | 28 * n, where n is 0, 1, 2, or 3.                                                                                        |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case C up to 3GHz (4)   | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0 or 1.                                                                                                       |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case C 3GHz to 6GHz (5) | Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 * n,   |
        |                         | where n is 0, 1, 2, or 3.                                                                                                |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case D (6)              | Use with 120 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {4, 8, 16, 20} + 28  |
        |                         | * n.                                                                                                                     |
        |                         | For carrier frequencies within FR-2, n is 0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, or 18.                     |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case E (7)              | Use with 240 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {8, 12, 16, 20, 32,  |
        |                         | 36, 40, 44} + 56 * n.                                                                                                    |
        |                         | For carrier frequencies within FR2-1, n is 0, 1, 2, 3, 5, 6, 7, or 8.                                                    |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case F (8)              | Use with 480 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {2, 9} + 14 * n.     |
        |                         | For carrier frequencies within FR2-2, n is 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,     |
        |                         | 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, or 31.                                                                           |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Case G (9)              | Use with 960 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {2, 9} + 14 * n.     |
        |                         | For carrier frequencies within FR2-2, n is 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,     |
        |                         | 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, or 31.                                                                           |
        +-------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SsbPattern, int):
                Specifies the candidate SS/PBCH blocks with different subcarrier spacing configurations as defined in the section 4.1
                of *3GPP TS 38.213* specification. In order to configure **Case C up to 1.88GHz** unpaired spectrum, configure this
                attribute to **Case C up to 3GHz**. Similarly, to configure **Case C 1.88GHz to 6GHz** unpaired spectrum, configure
                this attribute to **Case C 3GHz to 6GHz**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.SsbPattern else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_PATTERN.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_active_blocks(self, selector_string):
        r"""Gets the SSB burst(s) indices for the SSB pattern that needs to be transmitted.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0 - Last.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the SSB burst(s) indices for the SSB pattern that needs to be transmitted.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string, attributes.AttributeID.SSB_ACTIVE_BLOCKS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_active_blocks(self, selector_string, value):
        r"""Sets the SSB burst(s) indices for the SSB pattern that needs to be transmitted.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0 - Last.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the SSB burst(s) indices for the SSB pattern that needs to be transmitted.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string, attributes.AttributeID.SSB_ACTIVE_BLOCKS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pss_power(self, selector_string):
        r"""Gets the power scaling value for the primary synchronization symbol in the SS/PBCH block. This value is expressed
        in dB.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power scaling value for the primary synchronization symbol in the SS/PBCH block. This value is expressed
                in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PSS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pss_power(self, selector_string, value):
        r"""Sets the power scaling value for the primary synchronization symbol in the SS/PBCH block. This value is expressed
        in dB.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power scaling value for the primary synchronization symbol in the SS/PBCH block. This value is expressed
                in dB.

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
                updated_selector_string, attributes.AttributeID.PSS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sss_power(self, selector_string):
        r"""Gets the power scaling value for the secondary synchronization symbol in the SS/PBCH block. This value is
        expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power scaling value for the secondary synchronization symbol in the SS/PBCH block. This value is
                expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.SSS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sss_power(self, selector_string, value):
        r"""Sets the power scaling value for the secondary synchronization symbol in the SS/PBCH block. This value is
        expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power scaling value for the secondary synchronization symbol in the SS/PBCH block. This value is
                expressed in dB.

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
                updated_selector_string, attributes.AttributeID.SSS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pbch_power(self, selector_string):
        r"""Gets the power scaling value for the PBCH REs in the SS/PBCH block. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power scaling value for the PBCH REs in the SS/PBCH block. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PBCH_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pbch_power(self, selector_string, value):
        r"""Sets the power scaling value for the PBCH REs in the SS/PBCH block. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power scaling value for the PBCH REs in the SS/PBCH block. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PBCH_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pbch_dmrs_power(self, selector_string):
        r"""Gets the power scaling value for the PBCH DMRS symbols in the SS/PBCH block. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power scaling value for the PBCH DMRS symbols in the SS/PBCH block. This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.PBCH_DMRS_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pbch_dmrs_power(self, selector_string, value):
        r"""Sets the power scaling value for the PBCH DMRS symbols in the SS/PBCH block. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power scaling value for the PBCH DMRS symbols in the SS/PBCH block. This value is expressed in dB.

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
                updated_selector_string, attributes.AttributeID.PBCH_DMRS_POWER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ssb_hrf_index(self, selector_string):
        r"""Gets the half radio frame in which the SS/PBCH block should be allocated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The possible values are 0 and 1. The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the half radio frame in which the SS/PBCH block should be allocated.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SSB_HRF_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ssb_hrf_index(self, selector_string, value):
        r"""Sets the half radio frame in which the SS/PBCH block should be allocated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The possible values are 0 and 1. The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the half radio frame in which the SS/PBCH block should be allocated.

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
                updated_selector_string, attributes.AttributeID.SSB_HRF_INDEX.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
