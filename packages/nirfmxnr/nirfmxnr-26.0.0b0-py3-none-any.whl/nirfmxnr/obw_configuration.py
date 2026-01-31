"""Provides methods to configure the Obw measurement."""

import functools

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


class ObwConfiguration(object):
    """Provides methods to configure the Obw measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the Obw measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the OBW measurement.

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
                Specifies whether to enable the OBW measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the OBW measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the OBW measurement.

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
                attributes.AttributeID.OBW_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_integration_method(self, selector_string):
        r"""Gets if the OBW measurement window is centered around the center of the channel.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +-----------------+--------------------------------------------------------------------------+
        | Name (Value)    | Description                                                              |
        +=================+==========================================================================+
        | Normal (0)      | The OBW measurement window is centered around the signal in the channel. |
        +-----------------+--------------------------------------------------------------------------+
        | From Center (1) | The OBW measurement window is centered around the RF Center Frequency.   |
        +-----------------+--------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ObwPowerIntegrationMethod):
                Specifies if the OBW measurement window is centered around the center of the channel.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_POWER_INTEGRATION_METHOD.value
            )
            attr_val = enums.ObwPowerIntegrationMethod(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_integration_method(self, selector_string, value):
        r"""Sets if the OBW measurement window is centered around the center of the channel.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +-----------------+--------------------------------------------------------------------------+
        | Name (Value)    | Description                                                              |
        +=================+==========================================================================+
        | Normal (0)      | The OBW measurement window is centered around the signal in the channel. |
        +-----------------+--------------------------------------------------------------------------+
        | From Center (1) | The OBW measurement window is centered around the RF Center Frequency.   |
        +-----------------+--------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ObwPowerIntegrationMethod, int):
                Specifies if the OBW measurement window is centered around the center of the channel.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ObwPowerIntegrationMethod else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OBW_POWER_INTEGRATION_METHOD.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_span_auto(self, selector_string):
        r"""Gets whether the frequency range of the spectrum used for the OBW measurement is auto computed or configured by
        the user.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | False (0)    | Indicates that the user-configured span is used.                                      |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | Indicates that the measurement will auto compute the span based on the configuration. |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ObwSpanAuto):
                Specifies whether the frequency range of the spectrum used for the OBW measurement is auto computed or configured by
                the user.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_SPAN_AUTO.value
            )
            attr_val = enums.ObwSpanAuto(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_span_auto(self, selector_string, value):
        r"""Sets whether the frequency range of the spectrum used for the OBW measurement is auto computed or configured by
        the user.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                           |
        +==============+=======================================================================================+
        | False (0)    | Indicates that the user-configured span is used.                                      |
        +--------------+---------------------------------------------------------------------------------------+
        | True (1)     | Indicates that the measurement will auto compute the span based on the configuration. |
        +--------------+---------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ObwSpanAuto, int):
                Specifies whether the frequency range of the spectrum used for the OBW measurement is auto computed or configured by
                the user.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ObwSpanAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_SPAN_AUTO.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_span(self, selector_string):
        r"""Gets the frequency range around the subblock center frequency, which is used to find the
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RESULTS_OCCUPIED_BANDWIDTH`. When
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SPAN_AUTO` is set to **False**, the configured span value is used by the
        measurement. This value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 20 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the frequency range around the subblock center frequency, which is used to find the
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RESULTS_OCCUPIED_BANDWIDTH`. When
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SPAN_AUTO` is set to **False**, the configured span value is used by the
                measurement. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.OBW_SPAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_span(self, selector_string, value):
        r"""Sets the frequency range around the subblock center frequency, which is used to find the
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RESULTS_OCCUPIED_BANDWIDTH`. When
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SPAN_AUTO` is set to **False**, the configured span value is used by the
        measurement. This value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 20 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the frequency range around the subblock center frequency, which is used to find the
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RESULTS_OCCUPIED_BANDWIDTH`. When
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SPAN_AUTO` is set to **False**, the configured span value is used by the
                measurement. This value is expressed in Hz.

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
                updated_selector_string, attributes.AttributeID.OBW_SPAN.value, value
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
        | False (0)    | The measurement uses the RBW that you specify in the OBW RBW attribute. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                       |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ObwRbwAutoBandwidth):
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
                updated_selector_string, attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH.value
            )
            attr_val = enums.ObwRbwAutoBandwidth(attr_val)
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
        | False (0)    | The measurement uses the RBW that you specify in the OBW RBW attribute. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                       |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ObwRbwAutoBandwidth, int):
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
            value = value.value if type(value) is enums.ObwRbwAutoBandwidth else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_bandwidth(self, selector_string):
        r"""Gets the bandwidth of the RBW filter used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH` attribute to ** False**. This value is
        expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10 kHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the bandwidth of the RBW filter used to sweep the acquired signal, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH` attribute to ** False**. This value is
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
                updated_selector_string, attributes.AttributeID.OBW_RBW_FILTER_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_bandwidth(self, selector_string, value):
        r"""Sets the bandwidth of the RBW filter used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH` attribute to ** False**. This value is
        expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10 kHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the bandwidth of the RBW filter used to sweep the acquired signal, when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH` attribute to ** False**. This value is
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
                attributes.AttributeID.OBW_RBW_FILTER_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_type(self, selector_string):
        r"""Gets the shape of the digital RBW filter.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Gaussian**.

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

            attr_val (enums.ObwRbwFilterType):
                Specifies the shape of the digital RBW filter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_RBW_FILTER_TYPE.value
            )
            attr_val = enums.ObwRbwFilterType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_type(self, selector_string, value):
        r"""Sets the shape of the digital RBW filter.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Gaussian**.

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

            value (enums.ObwRbwFilterType, int):
                Specifies the shape of the digital RBW filter.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ObwRbwFilterType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_RBW_FILTER_TYPE.value, value
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

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the OBW Sweep Time attribute.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement calculates the sweep time internally. For DL, the sweep time is calculated based on the value of the     |
        |              | OBW RBW attribute, and for UL, it uses a sweep time of 1 ms.                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ObwSweepTimeAuto):
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
                updated_selector_string, attributes.AttributeID.OBW_SWEEP_TIME_AUTO.value
            )
            attr_val = enums.ObwSweepTimeAuto(attr_val)
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

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the OBW Sweep Time attribute.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement calculates the sweep time internally. For DL, the sweep time is calculated based on the value of the     |
        |              | OBW RBW attribute, and for UL, it uses a sweep time of 1 ms.                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ObwSweepTimeAuto, int):
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
            value = value.value if type(value) is enums.ObwSweepTimeAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_SWEEP_TIME_AUTO.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_interval(self, selector_string):
        r"""Gets the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SWEEP_TIME_AUTO` attribute to
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
                Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SWEEP_TIME_AUTO` attribute to
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
                updated_selector_string, attributes.AttributeID.OBW_SWEEP_TIME_INTERVAL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_interval(self, selector_string, value):
        r"""Sets the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SWEEP_TIME_AUTO` attribute to
        **False**. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SWEEP_TIME_AUTO` attribute to
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
                updated_selector_string, attributes.AttributeID.OBW_SWEEP_TIME_INTERVAL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the OBW measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The OBW measurement uses the value of the OBW Averaging Count attribute as the number of acquisitions over which the     |
        |              | OBW measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ObwAveragingEnabled):
                Specifies whether to enable averaging for the OBW measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_AVERAGING_ENABLED.value
            )
            attr_val = enums.ObwAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the OBW measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The OBW measurement uses the value of the OBW Averaging Count attribute as the number of acquisitions over which the     |
        |              | OBW measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ObwAveragingEnabled, int):
                Specifies whether to enable averaging for the OBW measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ObwAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_AVERAGING_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.OBW_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_type(self, selector_string):
        r"""Gets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the OBW
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RMS**.

        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                 |
        +==============+=============================================================================================================+
        | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor. |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                      |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Scalar (2)   | The square root of the power spectrum is averaged.                                                          |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.          |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.        |
        +--------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ObwAveragingType):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the OBW
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
                updated_selector_string, attributes.AttributeID.OBW_AVERAGING_TYPE.value
            )
            attr_val = enums.ObwAveragingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_type(self, selector_string, value):
        r"""Sets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the OBW
        measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RMS**.

        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                 |
        +==============+=============================================================================================================+
        | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor. |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                      |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Scalar (2)   | The square root of the power spectrum is averaged.                                                          |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Max (3)      | The peak power in the spectrum at each frequency bin is retained from one acquisition to the next.          |
        +--------------+-------------------------------------------------------------------------------------------------------------+
        | Min (4)      | The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next.        |
        +--------------+-------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ObwAveragingType, int):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the OBW
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
            value = value.value if type(value) is enums.ObwAveragingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_AVERAGING_TYPE.value, value
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

            attr_val (enums.ObwFftWindow):
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
                updated_selector_string, attributes.AttributeID.OBW_FFT_WINDOW.value
            )
            attr_val = enums.ObwFftWindow(attr_val)
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

            value (enums.ObwFftWindow, int):
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
            value = value.value if type(value) is enums.ObwFftWindow else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_FFT_WINDOW.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_amplitude_correction_type(self, selector_string):
        r"""Gets whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
        attenuation at RF center frequency or corrected for external attenuation at individual frequency bins. Use the
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

            attr_val (enums.ObwAmplitudeCorrectionType):
                Specifies whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
                attenuation at RF center frequency or corrected for external attenuation at individual frequency bins. Use the
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
                updated_selector_string, attributes.AttributeID.OBW_AMPLITUDE_CORRECTION_TYPE.value
            )
            attr_val = enums.ObwAmplitudeCorrectionType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_amplitude_correction_type(self, selector_string, value):
        r"""Sets whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
        attenuation at RF center frequency or corrected for external attenuation at individual frequency bins. Use the
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

            value (enums.ObwAmplitudeCorrectionType, int):
                Specifies whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
                attenuation at RF center frequency or corrected for external attenuation at individual frequency bins. Use the
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
            value = value.value if type(value) is enums.ObwAmplitudeCorrectionType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OBW_AMPLITUDE_CORRECTION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the OBW measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the OBW measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the OBW measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the OBW measurement.

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
                attributes.AttributeID.OBW_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the OBW measurement.

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
                Specifies the maximum number of threads used for parallelism for the OBW measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OBW_NUMBER_OF_ANALYSIS_THREADS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the OBW measurement.

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
                Specifies the maximum number of threads used for parallelism for the OBW measurement.

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
                attributes.AttributeID.OBW_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        r"""Configures averaging for the OBW measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.ObwAveragingEnabled, int):
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

            averaging_type (enums.ObwAveragingType, int):
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
                if type(averaging_enabled) is enums.ObwAveragingEnabled
                else averaging_enabled
            )
            averaging_type = (
                averaging_type.value
                if type(averaging_type) is enums.ObwAveragingType
                else averaging_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.obw_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count, averaging_type
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

            rbw_auto (enums.ObwRbwAutoBandwidth, int):
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
                Auto** parameter to **False**. This value is expressed in Hz. The default value is 10 kHz.

            rbw_filter_type (enums.ObwRbwFilterType, int):
                This parameter specifies the shape of the RBW filter. The default value is **Gaussian**.

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
            rbw_auto = rbw_auto.value if type(rbw_auto) is enums.ObwRbwAutoBandwidth else rbw_auto
            rbw_filter_type = (
                rbw_filter_type.value
                if type(rbw_filter_type) is enums.ObwRbwFilterType
                else rbw_filter_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.obw_configure_rbw_filter(
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

            sweep_time_auto (enums.ObwSweepTimeAuto, int):
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
                if type(sweep_time_auto) is enums.ObwSweepTimeAuto
                else sweep_time_auto
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.obw_configure_sweep_time(
                updated_selector_string, sweep_time_auto, sweep_time_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
