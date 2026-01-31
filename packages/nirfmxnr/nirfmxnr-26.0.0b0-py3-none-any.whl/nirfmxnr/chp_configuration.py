"""Provides methods to configure the Chp measurement."""

import functools

import nirfmxnr.attributes as attributes
import nirfmxnr.chp_component_carrier_configuration as component_carrier
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


class ChpConfiguration(object):
    """Provides methods to configure the Chp measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the Chp measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.component_carrier = component_carrier.ChpComponentCarrierConfiguration(signal_obj)  # type: ignore

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the channel power measurement.

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
                Specifies whether to enable the channel power measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the channel power measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the channel power measurement.

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
                attributes.AttributeID.CHP_MEASUREMENT_ENABLED.value,
                int(value),
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

        +--------------+--------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                |
        +==============+============================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the Sweep Time Interval attribute. |
        +--------------+--------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the sweep time based on the resolution bandwidth.                     |
        +--------------+--------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpSweepTimeAuto):
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
                updated_selector_string, attributes.AttributeID.CHP_SWEEP_TIME_AUTO.value
            )
            attr_val = enums.ChpSweepTimeAuto(attr_val)
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

        +--------------+--------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                |
        +==============+============================================================================================+
        | False (0)    | The measurement uses the sweep time that you specify in the Sweep Time Interval attribute. |
        +--------------+--------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the sweep time based on the resolution bandwidth.                     |
        +--------------+--------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpSweepTimeAuto, int):
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
            value = value.value if type(value) is enums.ChpSweepTimeAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_SWEEP_TIME_AUTO.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sweep_time_interval(self, selector_string):
        r"""Gets the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_SWEEP_TIME_AUTO` attribute to
        False. This value is expressed in seconds.

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
                Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_SWEEP_TIME_AUTO` attribute to
                False. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.CHP_SWEEP_TIME_INTERVAL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sweep_time_interval(self, selector_string, value):
        r"""Sets the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_SWEEP_TIME_AUTO` attribute to
        False. This value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 ms.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_SWEEP_TIME_AUTO` attribute to
                False. This value is expressed in seconds.

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
                updated_selector_string, attributes.AttributeID.CHP_SWEEP_TIME_INTERVAL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_integration_bandwidth_type(self, selector_string):
        r"""Gets the integration bandwidth (IBW) type used to measure the power of the acquired signal. Integration bandwidth
        is the frequency interval over which the power in each frequency bin is added to measure the total power in that
        interval.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Signal Bandwidth**.

        +-----------------------+---------------------------------------------------------------------------+
        | Name (Value)          | Description                                                               |
        +=======================+===========================================================================+
        | Signal Bandwidth (0)  | The IBW excludes the guard bands at the edges of the carrier or subblock. |
        +-----------------------+---------------------------------------------------------------------------+
        | Channel Bandwidth (1) | The IBW includes the guard bands at the edges of the carrier or subblock. |
        +-----------------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpIntegrationBandwidthType):
                Specifies the integration bandwidth (IBW) type used to measure the power of the acquired signal. Integration bandwidth
                is the frequency interval over which the power in each frequency bin is added to measure the total power in that
                interval.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_INTEGRATION_BANDWIDTH_TYPE.value
            )
            attr_val = enums.ChpIntegrationBandwidthType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_integration_bandwidth_type(self, selector_string, value):
        r"""Sets the integration bandwidth (IBW) type used to measure the power of the acquired signal. Integration bandwidth
        is the frequency interval over which the power in each frequency bin is added to measure the total power in that
        interval.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Signal Bandwidth**.

        +-----------------------+---------------------------------------------------------------------------+
        | Name (Value)          | Description                                                               |
        +=======================+===========================================================================+
        | Signal Bandwidth (0)  | The IBW excludes the guard bands at the edges of the carrier or subblock. |
        +-----------------------+---------------------------------------------------------------------------+
        | Channel Bandwidth (1) | The IBW includes the guard bands at the edges of the carrier or subblock. |
        +-----------------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpIntegrationBandwidthType, int):
                Specifies the integration bandwidth (IBW) type used to measure the power of the acquired signal. Integration bandwidth
                is the frequency interval over which the power in each frequency bin is added to measure the total power in that
                interval.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ChpIntegrationBandwidthType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_INTEGRATION_BANDWIDTH_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_integration_bandwidth(self, selector_string):
        r"""Gets the integration bandwidth of the subblock. This value is expressed in Hz. It is the span from left edge of
        the integration bandwidth of the leftmost carrier to the right edge of the integration bandwidth of the rightmost
        carrier within a subblock.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the integration bandwidth of the subblock. This value is expressed in Hz. It is the span from left edge of
                the integration bandwidth of the leftmost carrier to the right edge of the integration bandwidth of the rightmost
                carrier within a subblock.

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
                attributes.AttributeID.CHP_SUBBLOCK_INTEGRATION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rbw_filter_auto_bandwidth(self, selector_string):
        r"""Gets whether the measurement computes the RBW.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                  |
        +==============+==============================================================================+
        | False (0)    | The measurement uses the RBW that you specify in the CHP RBW (Hz) attribute. |
        +--------------+------------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                            |
        +--------------+------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpRbwAutoBandwidth):
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
                updated_selector_string, attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH.value
            )
            attr_val = enums.ChpRbwAutoBandwidth(attr_val)
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

        +--------------+------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                  |
        +==============+==============================================================================+
        | False (0)    | The measurement uses the RBW that you specify in the CHP RBW (Hz) attribute. |
        +--------------+------------------------------------------------------------------------------+
        | True (1)     | The measurement computes the RBW.                                            |
        +--------------+------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpRbwAutoBandwidth, int):
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
            value = value.value if type(value) is enums.ChpRbwAutoBandwidth else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_rbw_filter_bandwidth(self, selector_string):
        r"""Gets the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH` attribute to  **False**. This value is
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
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH` attribute to  **False**. This value is
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
                updated_selector_string, attributes.AttributeID.CHP_RBW_FILTER_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_rbw_filter_bandwidth(self, selector_string, value):
        r"""Sets the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH` attribute to  **False**. This value is
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
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH` attribute to  **False**. This value is
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
                attributes.AttributeID.CHP_RBW_FILTER_BANDWIDTH.value,
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

            attr_val (enums.ChpRbwFilterType):
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
                updated_selector_string, attributes.AttributeID.CHP_RBW_FILTER_TYPE.value
            )
            attr_val = enums.ChpRbwFilterType(attr_val)
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

            value (enums.ChpRbwFilterType, int):
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
            value = value.value if type(value) is enums.ChpRbwFilterType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_RBW_FILTER_TYPE.value, value
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
        | Manual (0)   | When you set CHP Meas Mode attribute to Calibrate Noise Floor, you can initiate the instrument noise calibration for     |
        |              | CHP manually. When you set the CHP Meas Mode attribute to Measure, you can initiate the CHP measurement manually.        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | When you set the CHP Noise Comp Enabled attribute to True, RFmx sets the Input Isolation Enabled attribute to Enabled    |
        |              | and calibrates the instrument noise in the current state of the instrument. Next, RFmx resets the Input Isolation        |
        |              | Enabled attribute and performs the CHP measurement including compensation for the noise contribution of the instrument.  |
        |              | RFmx skips noise calibration in this mode if valid noise calibration data is already cached. When you set the CHP Noise  |
        |              | Comp Enabled to False, RFmx does not calibrate instrument noise and performs the CHP measurement without compensating    |
        |              | for the noise contribution of the instrument.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpNoiseCalibrationMode):
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
                updated_selector_string, attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE.value
            )
            attr_val = enums.ChpNoiseCalibrationMode(attr_val)
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
        | Manual (0)   | When you set CHP Meas Mode attribute to Calibrate Noise Floor, you can initiate the instrument noise calibration for     |
        |              | CHP manually. When you set the CHP Meas Mode attribute to Measure, you can initiate the CHP measurement manually.        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | When you set the CHP Noise Comp Enabled attribute to True, RFmx sets the Input Isolation Enabled attribute to Enabled    |
        |              | and calibrates the instrument noise in the current state of the instrument. Next, RFmx resets the Input Isolation        |
        |              | Enabled attribute and performs the CHP measurement including compensation for the noise contribution of the instrument.  |
        |              | RFmx skips noise calibration in this mode if valid noise calibration data is already cached. When you set the CHP Noise  |
        |              | Comp Enabled to False, RFmx does not calibrate instrument noise and performs the CHP measurement without compensating    |
        |              | for the noise contribution of the instrument.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpNoiseCalibrationMode, int):
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
            value = value.value if type(value) is enums.ChpNoiseCalibrationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE.value,
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

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | RFmx uses the averages that you set for CHP Noise Cal Averaging Count attribute. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | RFmx uses a noise calibration averaging count of 32.                             |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpNoiseCalibrationAveragingAuto):
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
                attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO.value,
            )
            attr_val = enums.ChpNoiseCalibrationAveragingAuto(attr_val)
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

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | RFmx uses the averages that you set for CHP Noise Cal Averaging Count attribute. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | RFmx uses a noise calibration averaging count of 32.                             |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpNoiseCalibrationAveragingAuto, int):
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
            value = value.value if type(value) is enums.ChpNoiseCalibrationAveragingAuto else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_calibration_averaging_count(self, selector_string):
        r"""Gets the averaging count used for noise calibration when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

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
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

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
                attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_COUNT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_calibration_averaging_count(self, selector_string, value):
        r"""Sets the averaging count used for noise calibration when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 32.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the averaging count used for noise calibration when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.

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
                attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_COUNT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_enabled(self, selector_string):
        r"""Gets whether RFmx compensates for the instrument noise when performing the measurement. To compensate for
        instrument noise when performing a CHP measurement, set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or set the CHP Noise Cal
        Mode attribute to **Manual** and the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to
        **Measure**.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------+
        | Name (Value) | Description                                    |
        +==============+================================================+
        | False (0)    | Indicates that noise compensation is disabled. |
        +--------------+------------------------------------------------+
        | True (1)     | Indicates that noise compensation is enabled.  |
        +--------------+------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpNoiseCompensationEnabled):
                Specifies whether RFmx compensates for the instrument noise when performing the measurement. To compensate for
                instrument noise when performing a CHP measurement, set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or set the CHP Noise Cal
                Mode attribute to **Manual** and the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to
                **Measure**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_NOISE_COMPENSATION_ENABLED.value
            )
            attr_val = enums.ChpNoiseCompensationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_enabled(self, selector_string, value):
        r"""Sets whether RFmx compensates for the instrument noise when performing the measurement. To compensate for
        instrument noise when performing a CHP measurement, set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or set the CHP Noise Cal
        Mode attribute to **Manual** and the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to
        **Measure**.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------+
        | Name (Value) | Description                                    |
        +==============+================================================+
        | False (0)    | Indicates that noise compensation is disabled. |
        +--------------+------------------------------------------------+
        | True (1)     | Indicates that noise compensation is enabled.  |
        +--------------+------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpNoiseCompensationEnabled, int):
                Specifies whether RFmx compensates for the instrument noise when performing the measurement. To compensate for
                instrument noise when performing a CHP measurement, set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_MODE` attribute to **Auto**, or set the CHP Noise Cal
                Mode attribute to **Manual** and the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to
                **Measure**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ChpNoiseCompensationEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_NOISE_COMPENSATION_ENABLED.value,
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
        | Analyzer and Termination (0) | Compensates for noise contribution of the analyzer instrument and the 50-ohm termination. The measured power values are  |
        |                              | in excess of the thermal noise floor.                                                                                    |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Analyzer Only (1)            | Compensates only for analyzer noise only.                                                                                |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpNoiseCompensationType):
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
                updated_selector_string, attributes.AttributeID.CHP_NOISE_COMPENSATION_TYPE.value
            )
            attr_val = enums.ChpNoiseCompensationType(attr_val)
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
        | Analyzer and Termination (0) | Compensates for noise contribution of the analyzer instrument and the 50-ohm termination. The measured power values are  |
        |                              | in excess of the thermal noise floor.                                                                                    |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Analyzer Only (1)            | Compensates only for analyzer noise only.                                                                                |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpNoiseCompensationType, int):
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
            value = value.value if type(value) is enums.ChpNoiseCompensationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_NOISE_COMPENSATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the CHP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The CHP measurement uses the value of the CHP Averaging Count attribute as the number of acquisitions over which the     |
        |              | CHP measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpAveragingEnabled):
                Specifies whether to enable averaging for the CHP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_AVERAGING_ENABLED.value
            )
            attr_val = enums.ChpAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the CHP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The CHP measurement uses the value of the CHP Averaging Count attribute as the number of acquisitions over which the     |
        |              | CHP measurement is averaged.                                                                                             |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpAveragingEnabled, int):
                Specifies whether to enable averaging for the CHP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ChpAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_AVERAGING_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.CHP_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_type(self, selector_string):
        r"""Gets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for CHP
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

            attr_val (enums.ChpAveragingType):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for CHP
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
                updated_selector_string, attributes.AttributeID.CHP_AVERAGING_TYPE.value
            )
            attr_val = enums.ChpAveragingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_type(self, selector_string, value):
        r"""Sets the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for CHP
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

            value (enums.ChpAveragingType, int):
                Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for CHP
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
            value = value.value if type(value) is enums.ChpAveragingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_AVERAGING_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_mode(self, selector_string):
        r"""Gets whether the measurement calibrates the noise floor of analyzer or performs the CHP measurement.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+-----------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                       |
        +===========================+===================================================================================+
        | Measure (0)               | Performs the CHP measurement on the acquired signal.                              |
        +---------------------------+-----------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | Performs manual noise calibration of the signal analyzer for the CHP measurement. |
        +---------------------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpMeasurementMode):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the CHP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_MEASUREMENT_MODE.value
            )
            attr_val = enums.ChpMeasurementMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_mode(self, selector_string, value):
        r"""Sets whether the measurement calibrates the noise floor of analyzer or performs the CHP measurement.

        Refer to the measurement guidelines section in the `Noise Compensation Algorithm
        <www.ni.com/docs/en-US/bundle/rfmx-nr/page/noise-compensation-algorithm.html>`_ topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+-----------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                       |
        +===========================+===================================================================================+
        | Measure (0)               | Performs the CHP measurement on the acquired signal.                              |
        +---------------------------+-----------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | Performs manual noise calibration of the signal analyzer for the CHP measurement. |
        +---------------------------+-----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpMeasurementMode, int):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the CHP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ChpMeasurementMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_MEASUREMENT_MODE.value, value
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

            attr_val (enums.ChpFftWindow):
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
                updated_selector_string, attributes.AttributeID.CHP_FFT_WINDOW.value
            )
            attr_val = enums.ChpFftWindow(attr_val)
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

            value (enums.ChpFftWindow, int):
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
            value = value.value if type(value) is enums.ChpFftWindow else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_FFT_WINDOW.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_amplitude_correction_type(self, selector_string):
        r"""Gets whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
        attenuation at RF center frequency or corrected for external attenuation at individual frequency bins Use the
        :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
        attenuation table.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RF Center Frequency**.

        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)               | Description                                                                                                              |
        +============================+==========================================================================================================================+
        | RF Center Frequency (0)    | All frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the RF   |
        |                            | center frequency.                                                                                                        |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Spectrum Frequency Bin (1) | Individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that        |
        |                            | frequency.                                                                                                               |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChpAmplitudeCorrectionType):
                Specifies whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
                attenuation at RF center frequency or corrected for external attenuation at individual frequency bins Use the
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
                updated_selector_string, attributes.AttributeID.CHP_AMPLITUDE_CORRECTION_TYPE.value
            )
            attr_val = enums.ChpAmplitudeCorrectionType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_amplitude_correction_type(self, selector_string, value):
        r"""Sets whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
        attenuation at RF center frequency or corrected for external attenuation at individual frequency bins Use the
        :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
        attenuation table.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RF Center Frequency**.

        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)               | Description                                                                                                              |
        +============================+==========================================================================================================================+
        | RF Center Frequency (0)    | All frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the RF   |
        |                            | center frequency.                                                                                                        |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Spectrum Frequency Bin (1) | Individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that        |
        |                            | frequency.                                                                                                               |
        +----------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChpAmplitudeCorrectionType, int):
                Specifies whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
                attenuation at RF center frequency or corrected for external attenuation at individual frequency bins Use the
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
            value = value.value if type(value) is enums.ChpAmplitudeCorrectionType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.CHP_AMPLITUDE_CORRECTION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the CHP measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the CHP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the CHP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the CHP measurement.

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
                attributes.AttributeID.CHP_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the CHP measurement.

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
                Specifies the maximum number of threads used for parallelism for the CHP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.CHP_NUMBER_OF_ANALYSIS_THREADS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the CHP measurement.

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
                Specifies the maximum number of threads used for parallelism for the CHP measurement.

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
                attributes.AttributeID.CHP_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        r"""Configures averaging for the CHP measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.ChpAveragingEnabled, int):
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

            averaging_type (enums.ChpAveragingType, int):
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
                if type(averaging_enabled) is enums.ChpAveragingEnabled
                else averaging_enabled
            )
            averaging_type = (
                averaging_type.value
                if type(averaging_type) is enums.ChpAveragingType
                else averaging_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.chp_configure_averaging(
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

            rbw_auto (enums.ChpRbwAutoBandwidth, int):
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

            rbw_filter_type (enums.ChpRbwFilterType, int):
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
            rbw_auto = rbw_auto.value if type(rbw_auto) is enums.ChpRbwAutoBandwidth else rbw_auto
            rbw_filter_type = (
                rbw_filter_type.value
                if type(rbw_filter_type) is enums.ChpRbwFilterType
                else rbw_filter_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.chp_configure_rbw_filter(
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

            sweep_time_auto (enums.ChpSweepTimeAuto, int):
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
                if type(sweep_time_auto) is enums.ChpSweepTimeAuto
                else sweep_time_auto
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.chp_configure_sweep_time(
                updated_selector_string, sweep_time_auto, sweep_time_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def validate_noise_calibration_data(self, selector_string):
        r"""Indicates whether the CHP noise calibration data is valid for the configuration specified by the signal name in the
        **Selector String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (noise_calibration_data_valid, error_code):

            noise_calibration_data_valid (enums.ChpNoiseCalibrationDataValid):
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
                self._interpreter.chp_validate_noise_calibration_data(updated_selector_string)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return noise_calibration_data_valid, error_code
