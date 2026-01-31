"""Provides methods to configure the ModAcc measurement."""

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


class ModAccConfiguration(object):
    """Provides methods to configure the ModAcc measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the ModAcc measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the ModAcc measurement.

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
                Specifies whether to enable the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the ModAcc measurement.

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
                attributes.AttributeID.MODACC_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_multicarrier_filter_enabled(self, selector_string):
        r"""Gets whether to use the filter in single carrier configurations to minimize leakage into the carrier. Measurement
        ignores this attribute, if number of carriers is set to more than 1 or if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED` attribute to **False**, where in
        the multi carrier filter will always be used.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | Measurement doesn't use the filter.         |
        +--------------+---------------------------------------------+
        | True (1)     | Measurement filters out unwanted emissions. |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccMulticarrierFilterEnabled):
                Specifies whether to use the filter in single carrier configurations to minimize leakage into the carrier. Measurement
                ignores this attribute, if number of carriers is set to more than 1 or if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED` attribute to **False**, where in
                the multi carrier filter will always be used.

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
                attributes.AttributeID.MODACC_MULTICARRIER_FILTER_ENABLED.value,
            )
            attr_val = enums.ModAccMulticarrierFilterEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_multicarrier_filter_enabled(self, selector_string, value):
        r"""Sets whether to use the filter in single carrier configurations to minimize leakage into the carrier. Measurement
        ignores this attribute, if number of carriers is set to more than 1 or if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED` attribute to **False**, where in
        the multi carrier filter will always be used.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | Measurement doesn't use the filter.         |
        +--------------+---------------------------------------------+
        | True (1)     | Measurement filters out unwanted emissions. |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccMulticarrierFilterEnabled, int):
                Specifies whether to use the filter in single carrier configurations to minimize leakage into the carrier. Measurement
                ignores this attribute, if number of carriers is set to more than 1 or if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED` attribute to **False**, where in
                the multi carrier filter will always be used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccMulticarrierFilterEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_MULTICARRIER_FILTER_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_synchronization_mode(self, selector_string):
        r"""Gets whether the measurement is performed from slot or frame boundary.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Slot**.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | Slot (1)            | The measurement is performed over the ModAcc Meas Length starting at the ModAcc Meas Offset from the slot boundary. If   |
        |                     | you set the Trigger Type attribute to Digital Edge, the measurement expects the digital trigger at the slot boundary.    |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frame (5)           | The measurement is performed over the ModAcc Meas Length starting at ModAcc Meas Offset from the frame boundary. If you  |
        |                     | set the Trigger Type attribute to Digital Edge, the measurement expects the digital trigger from the frame boundary.     |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | SSB Start Frame (7) | The measurement is performed over the ModAcc Meas Length starting at ModAcc Meas Offset from the frame boundary. If you  |
        |                     | set the Trigger Type attribute to Digital Edge, the measurement expects the digital trigger from the boundary of the     |
        |                     | frame having SSB.                                                                                                        |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSynchronizationMode):
                Specifies whether the measurement is performed from slot or frame boundary.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE.value
            )
            attr_val = enums.ModAccSynchronizationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_synchronization_mode(self, selector_string, value):
        r"""Sets whether the measurement is performed from slot or frame boundary.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Slot**.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | Slot (1)            | The measurement is performed over the ModAcc Meas Length starting at the ModAcc Meas Offset from the slot boundary. If   |
        |                     | you set the Trigger Type attribute to Digital Edge, the measurement expects the digital trigger at the slot boundary.    |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frame (5)           | The measurement is performed over the ModAcc Meas Length starting at ModAcc Meas Offset from the frame boundary. If you  |
        |                     | set the Trigger Type attribute to Digital Edge, the measurement expects the digital trigger from the frame boundary.     |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | SSB Start Frame (7) | The measurement is performed over the ModAcc Meas Length starting at ModAcc Meas Offset from the frame boundary. If you  |
        |                     | set the Trigger Type attribute to Digital Edge, the measurement expects the digital trigger from the boundary of the     |
        |                     | frame having SSB.                                                                                                        |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSynchronizationMode, int):
                Specifies whether the measurement is performed from slot or frame boundary.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccSynchronizationMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_length_unit(self, selector_string):
        r"""Gets the units in which measurement offset and measurement length are specified.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Slot**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Slot (1)     | Measurement offset and measurement length are specified in units of slots.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Subframe (3) | Measurement offset and measurement length are specified in units of subframes.                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Time (6)     | Measurement offset and measurement length are specified in seconds. Specify the measurement offset and length in         |
        |              | multiples of 1 ms * (15 kHz/minimum subcarrier spacing of all carriers). All slots within this notional time duration    |
        |              | are analysed.                                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccMeasurementLengthUnit):
                Specifies the units in which measurement offset and measurement length are specified.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT.value
            )
            attr_val = enums.ModAccMeasurementLengthUnit(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_length_unit(self, selector_string, value):
        r"""Sets the units in which measurement offset and measurement length are specified.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Slot**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Slot (1)     | Measurement offset and measurement length are specified in units of slots.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Subframe (3) | Measurement offset and measurement length are specified in units of subframes.                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Time (6)     | Measurement offset and measurement length are specified in seconds. Specify the measurement offset and length in         |
        |              | multiples of 1 ms * (15 kHz/minimum subcarrier spacing of all carriers). All slots within this notional time duration    |
        |              | are analysed.                                                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccMeasurementLengthUnit, int):
                Specifies the units in which measurement offset and measurement length are specified.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccMeasurementLengthUnit else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_offset(self, selector_string):
        r"""Gets the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
        by the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. The unit for this is
        specified by :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
                by the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. The unit for this is
                specified by :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_offset(self, selector_string, value):
        r"""Sets the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
        by the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. The unit for this is
        specified by :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
                by the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. The unit for this is
                specified by :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.

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
                attributes.AttributeID.MODACC_MEASUREMENT_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_length(self, selector_string):
        r"""Gets the measurement length in units specified by
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the measurement length in units specified by
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT` attribute.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_length(self, selector_string, value):
        r"""Sets the measurement length in units specified by
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the measurement length in units specified by
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT` attribute.

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
                attributes.AttributeID.MODACC_MEASUREMENT_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency_error_estimation(self, selector_string):
        r"""Gets the operation mode of frequency error estimation.

        If frequency error is absent in the signal to be analyzed, you may disable frequency estimation to reduce
        measurement time or to avoid measurement inaccuracy due to error in frequency error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Disabled (0) | Frequency error estimation and correction is disabled.                                                                   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Normal (1)   | Estimate and correct frequency error of range +/- half subcarrier spacing.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Wide (2)     | Estimate and correct frequency error of range +/- half resource block when Auto RB Detection Enabled is True, or range   |
        |              | +/-                                                                                                                      |
        |              | number of guard subcarrier when Auto RB Detection Enabled is False.                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccFrequencyErrorEstimation):
                Specifies the operation mode of frequency error estimation.

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
                attributes.AttributeID.MODACC_FREQUENCY_ERROR_ESTIMATION.value,
            )
            attr_val = enums.ModAccFrequencyErrorEstimation(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency_error_estimation(self, selector_string, value):
        r"""Sets the operation mode of frequency error estimation.

        If frequency error is absent in the signal to be analyzed, you may disable frequency estimation to reduce
        measurement time or to avoid measurement inaccuracy due to error in frequency error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Disabled (0) | Frequency error estimation and correction is disabled.                                                                   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Normal (1)   | Estimate and correct frequency error of range +/- half subcarrier spacing.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Wide (2)     | Estimate and correct frequency error of range +/- half resource block when Auto RB Detection Enabled is True, or range   |
        |              | +/-                                                                                                                      |
        |              | number of guard subcarrier when Auto RB Detection Enabled is False.                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccFrequencyErrorEstimation, int):
                Specifies the operation mode of frequency error estimation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccFrequencyErrorEstimation else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_FREQUENCY_ERROR_ESTIMATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_symbol_clock_error_estimation_enabled(self, selector_string):
        r"""Gets whether to estimate symbol clock error.

        This attribute is ignored when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_COMMON_CLOCK_SOURCE_ENABLED` attribute is **True** and the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FREQUENCY_ERROR_ESTIMATION` attribute is **Disabled**, in which case,
        symbol clock error is not estimated.

        If symbol clock error is absent in the signal to be analyzed, you may disable symbol clock error estimation to
        reduce measurement time or to avoid measurement inaccuracy due to error in symbol clock error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------+
        | Name (Value) | Description                                                              |
        +==============+==========================================================================+
        | False (0)    | Indicates that symbol clock error estimation and correction is disabled. |
        +--------------+--------------------------------------------------------------------------+
        | True (1)     | Indicates that symbol clock error estimation and correction is enabled.  |
        +--------------+--------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSymbolClockErrorEstimationEnabled):
                Specifies whether to estimate symbol clock error.

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
                attributes.AttributeID.MODACC_SYMBOL_CLOCK_ERROR_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.ModAccSymbolClockErrorEstimationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_symbol_clock_error_estimation_enabled(self, selector_string, value):
        r"""Sets whether to estimate symbol clock error.

        This attribute is ignored when the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_COMMON_CLOCK_SOURCE_ENABLED` attribute is **True** and the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FREQUENCY_ERROR_ESTIMATION` attribute is **Disabled**, in which case,
        symbol clock error is not estimated.

        If symbol clock error is absent in the signal to be analyzed, you may disable symbol clock error estimation to
        reduce measurement time or to avoid measurement inaccuracy due to error in symbol clock error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------+
        | Name (Value) | Description                                                              |
        +==============+==========================================================================+
        | False (0)    | Indicates that symbol clock error estimation and correction is disabled. |
        +--------------+--------------------------------------------------------------------------+
        | True (1)     | Indicates that symbol clock error estimation and correction is enabled.  |
        +--------------+--------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSymbolClockErrorEstimationEnabled, int):
                Specifies whether to estimate symbol clock error.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccSymbolClockErrorEstimationEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SYMBOL_CLOCK_ERROR_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_impairments_model(self, selector_string):
        r"""Gets the I/Q impairments model used by the measurement for estimating I/Q impairments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Tx**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Tx (0)       | The measurement assumes that the I/Q impairments are introduced by a transmit DUT. |
        +--------------+------------------------------------------------------------------------------------+
        | Rx (1)       | The measurement assumes that the I/Q impairments are introduced by a receive DUT.  |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQImpairmentsModel):
                Specifies the I/Q impairments model used by the measurement for estimating I/Q impairments.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_IQ_IMPAIRMENTS_MODEL.value
            )
            attr_val = enums.ModAccIQImpairmentsModel(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_impairments_model(self, selector_string, value):
        r"""Sets the I/Q impairments model used by the measurement for estimating I/Q impairments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Tx**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Tx (0)       | The measurement assumes that the I/Q impairments are introduced by a transmit DUT. |
        +--------------+------------------------------------------------------------------------------------+
        | Rx (1)       | The measurement assumes that the I/Q impairments are introduced by a receive DUT.  |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQImpairmentsModel, int):
                Specifies the I/Q impairments model used by the measurement for estimating I/Q impairments.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccIQImpairmentsModel else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_IMPAIRMENTS_MODEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_origin_offset_estimation_enabled(self, selector_string):
        r"""Gets whether to estimate the IQ origin offset.

        If IQ origin offset is absent in the signal to be analyzed, you may disable IQ origin offset estimation to
        reduce measurement time or to avoid measurement inaccuracy due to error in IQ origin offset estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+------------------------------------------------------------------------+
        | Name (Value) | Description                                                            |
        +==============+========================================================================+
        | False (0)    | Indicates that IQ origin offset estimation and correction is disabled. |
        +--------------+------------------------------------------------------------------------+
        | True (1)     | Indicates that IQ origin offset estimation and correction is enabled.  |
        +--------------+------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQOriginOffsetEstimationEnabled):
                Specifies whether to estimate the IQ origin offset.

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
                attributes.AttributeID.MODACC_IQ_ORIGIN_OFFSET_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.ModAccIQOriginOffsetEstimationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_origin_offset_estimation_enabled(self, selector_string, value):
        r"""Sets whether to estimate the IQ origin offset.

        If IQ origin offset is absent in the signal to be analyzed, you may disable IQ origin offset estimation to
        reduce measurement time or to avoid measurement inaccuracy due to error in IQ origin offset estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+------------------------------------------------------------------------+
        | Name (Value) | Description                                                            |
        +==============+========================================================================+
        | False (0)    | Indicates that IQ origin offset estimation and correction is disabled. |
        +--------------+------------------------------------------------------------------------+
        | True (1)     | Indicates that IQ origin offset estimation and correction is enabled.  |
        +--------------+------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQOriginOffsetEstimationEnabled, int):
                Specifies whether to estimate the IQ origin offset.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccIQOriginOffsetEstimationEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_ORIGIN_OFFSET_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_mismatch_estimation_enabled(self, selector_string):
        r"""Gets whether to estimate the IQ impairments such as IQ gain imbalance and quadrature skew.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | IQ Impairments estimation is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | IQ Impairments estimation is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQMismatchEstimationEnabled):
                Specifies whether to estimate the IQ impairments such as IQ gain imbalance and quadrature skew.

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
                attributes.AttributeID.MODACC_IQ_MISMATCH_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.ModAccIQMismatchEstimationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_mismatch_estimation_enabled(self, selector_string, value):
        r"""Sets whether to estimate the IQ impairments such as IQ gain imbalance and quadrature skew.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | IQ Impairments estimation is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | IQ Impairments estimation is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQMismatchEstimationEnabled, int):
                Specifies whether to estimate the IQ impairments such as IQ gain imbalance and quadrature skew.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccIQMismatchEstimationEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_MISMATCH_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_correction_enabled(self, selector_string):
        r"""Gets whether to enable IQ gain imbalance correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | False (0)    | IQ gain imbalance correction is disabled. |
        +--------------+-------------------------------------------+
        | True (1)     | IQ gain imbalance correction is enabled.  |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQGainImbalanceCorrectionEnabled):
                Specifies whether to enable IQ gain imbalance correction.

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
                attributes.AttributeID.MODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQGainImbalanceCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_gain_imbalance_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable IQ gain imbalance correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | False (0)    | IQ gain imbalance correction is disabled. |
        +--------------+-------------------------------------------+
        | True (1)     | IQ gain imbalance correction is enabled.  |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQGainImbalanceCorrectionEnabled, int):
                Specifies whether to enable IQ gain imbalance correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccIQGainImbalanceCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_correction_enabled(self, selector_string):
        r"""Gets whether to enable IQ quadrature error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | IQ quadrature error correction is disabled. |
        +--------------+---------------------------------------------+
        | True (1)     | IQ quadrature error correction is enabled.  |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQQuadratureErrorCorrectionEnabled):
                Specifies whether to enable IQ quadrature error correction.

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
                attributes.AttributeID.MODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQQuadratureErrorCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_quadrature_error_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable IQ quadrature error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | IQ quadrature error correction is disabled. |
        +--------------+---------------------------------------------+
        | True (1)     | IQ quadrature error correction is enabled.  |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQQuadratureErrorCorrectionEnabled, int):
                Specifies whether to enable IQ quadrature error correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccIQQuadratureErrorCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_timing_skew_correction_enabled(self, selector_string):
        r"""Gets whether to enable IQ timing skew correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | IQ timing skew correction is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | IQ timing skew correction is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQTimingSkewCorrectionEnabled):
                Specifies whether to enable IQ timing skew correction.

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
                attributes.AttributeID.MODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQTimingSkewCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_timing_skew_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable IQ timing skew correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | IQ timing skew correction is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | IQ timing skew correction is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQTimingSkewCorrectionEnabled, int):
                Specifies whether to enable IQ timing skew correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccIQTimingSkewCorrectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_impairments_per_subcarrier_enabled(self, selector_string):
        r"""Gets whether to return I/Q impairments independently for each subcarrier.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                   |
        +==============+===============================================================================================+
        | False (0)    | Indicates that the independent estimation of I/Q impairments for each subcarrier is disabled. |
        +--------------+-----------------------------------------------------------------------------------------------+
        | True (1)     | Indicates that the independent estimation of I/Q impairments for each subcarrier is enabled.  |
        +--------------+-----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQImpairmentsPerSubcarrierEnabled):
                Specifies whether to return I/Q impairments independently for each subcarrier.

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
                attributes.AttributeID.MODACC_IQ_IMPAIRMENTS_PER_SUBCARRIER_ENABLED.value,
            )
            attr_val = enums.ModAccIQImpairmentsPerSubcarrierEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_impairments_per_subcarrier_enabled(self, selector_string, value):
        r"""Sets whether to return I/Q impairments independently for each subcarrier.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                   |
        +==============+===============================================================================================+
        | False (0)    | Indicates that the independent estimation of I/Q impairments for each subcarrier is disabled. |
        +--------------+-----------------------------------------------------------------------------------------------+
        | True (1)     | Indicates that the independent estimation of I/Q impairments for each subcarrier is enabled.  |
        +--------------+-----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQImpairmentsPerSubcarrierEnabled, int):
                Specifies whether to return I/Q impairments independently for each subcarrier.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccIQImpairmentsPerSubcarrierEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_IMPAIRMENTS_PER_SUBCARRIER_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_magnitude_and_phase_error_enabled(self, selector_string):
        r"""Gets whether to measure the magnitude and the phase error.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                     |
        +==============+=================================================================================+
        | False (0)    | Indicates that magnitude error and phase error results computation is disabled. |
        +--------------+---------------------------------------------------------------------------------+
        | True (1)     | Indicates that magnitude error and phase error results computation is enabled.  |
        +--------------+---------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccMagnitudeAndPhaseErrorEnabled):
                Specifies whether to measure the magnitude and the phase error.

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
                attributes.AttributeID.MODACC_MAGNITUDE_AND_PHASE_ERROR_ENABLED.value,
            )
            attr_val = enums.ModAccMagnitudeAndPhaseErrorEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_magnitude_and_phase_error_enabled(self, selector_string, value):
        r"""Sets whether to measure the magnitude and the phase error.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                     |
        +==============+=================================================================================+
        | False (0)    | Indicates that magnitude error and phase error results computation is disabled. |
        +--------------+---------------------------------------------------------------------------------+
        | True (1)     | Indicates that magnitude error and phase error results computation is enabled.  |
        +--------------+---------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccMagnitudeAndPhaseErrorEnabled, int):
                Specifies whether to measure the magnitude and the phase error.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccMagnitudeAndPhaseErrorEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_MAGNITUDE_AND_PHASE_ERROR_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_reference_data_symbols_mode(self, selector_string):
        r"""Gets whether to either use a reference waveform or an acquired waveform to create reference data symbols for EVM
        computation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Acquired Waveform**.

        +------------------------+-----------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                         |
        +========================+=====================================================================================================+
        | Acquired Waveform (0)  | Indicates that reference data symbols for EVM computation are created using the acquired waveform.  |
        +------------------------+-----------------------------------------------------------------------------------------------------+
        | Reference Waveform (1) | Indicates that reference data symbols for EVM computation are created using the reference waveform. |
        +------------------------+-----------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccEvmReferenceDataSymbolsMode):
                Specifies whether to either use a reference waveform or an acquired waveform to create reference data symbols for EVM
                computation.

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
                attributes.AttributeID.MODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE.value,
            )
            attr_val = enums.ModAccEvmReferenceDataSymbolsMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_reference_data_symbols_mode(self, selector_string, value):
        r"""Sets whether to either use a reference waveform or an acquired waveform to create reference data symbols for EVM
        computation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Acquired Waveform**.

        +------------------------+-----------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                         |
        +========================+=====================================================================================================+
        | Acquired Waveform (0)  | Indicates that reference data symbols for EVM computation are created using the acquired waveform.  |
        +------------------------+-----------------------------------------------------------------------------------------------------+
        | Reference Waveform (1) | Indicates that reference data symbols for EVM computation are created using the reference waveform. |
        +------------------------+-----------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccEvmReferenceDataSymbolsMode, int):
                Specifies whether to either use a reference waveform or an acquired waveform to create reference data symbols for EVM
                computation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccEvmReferenceDataSymbolsMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_spectrum_inverted(self, selector_string):
        r"""Gets whether the spectrum of the signal being measured  is inverted. This happens when I and Q component of the
        baseband complex signal is swapped.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                               |
        +==============+===========================================================================================================+
        | False (0)    | The signal being measured is not inverted.                                                                |
        +--------------+-----------------------------------------------------------------------------------------------------------+
        | True (1)     | The signal being measured is inverted and measurement will correct it by swapping the I and Q components. |
        +--------------+-----------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSpectrumInverted):
                Specifies whether the spectrum of the signal being measured  is inverted. This happens when I and Q component of the
                baseband complex signal is swapped.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_SPECTRUM_INVERTED.value
            )
            attr_val = enums.ModAccSpectrumInverted(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spectrum_inverted(self, selector_string, value):
        r"""Sets whether the spectrum of the signal being measured  is inverted. This happens when I and Q component of the
        baseband complex signal is swapped.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                               |
        +==============+===========================================================================================================+
        | False (0)    | The signal being measured is not inverted.                                                                |
        +--------------+-----------------------------------------------------------------------------------------------------------+
        | True (1)     | The signal being measured is inverted and measurement will correct it by swapping the I and Q components. |
        +--------------+-----------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSpectrumInverted, int):
                Specifies whether the spectrum of the signal being measured  is inverted. This happens when I and Q component of the
                baseband complex signal is swapped.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccSpectrumInverted else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SPECTRUM_INVERTED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_type(self, selector_string):
        r"""Gets the method used for channel estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Reference (0)      | Only demodulation reference (DMRS) symbol is used to calculate channel coefficients.                                     |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference+Data (1) | Both demodulation reference (DMRS) and data symbols are used to calculate channel coefficients. This method is as per    |
        |                    | definition of 3GPP NR specification.                                                                                     |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccChannelEstimationType):
                Specifies the method used for channel estimation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_CHANNEL_ESTIMATION_TYPE.value
            )
            attr_val = enums.ModAccChannelEstimationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_type(self, selector_string, value):
        r"""Sets the method used for channel estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)       | Description                                                                                                              |
        +====================+==========================================================================================================================+
        | Reference (0)      | Only demodulation reference (DMRS) symbol is used to calculate channel coefficients.                                     |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference+Data (1) | Both demodulation reference (DMRS) and data symbols are used to calculate channel coefficients. This method is as per    |
        |                    | definition of 3GPP NR specification.                                                                                     |
        +--------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccChannelEstimationType, int):
                Specifies the method used for channel estimation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccChannelEstimationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_CHANNEL_ESTIMATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phase_tracking_mode(self, selector_string):
        r"""Gets the method used for phase tracking.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+-------------------------------------------------------------+
        | Name (Value)       | Description                                                 |
        +====================+=============================================================+
        | Disabled (0)       | Disables the phase tracking.                                |
        +--------------------+-------------------------------------------------------------+
        | Reference+Data (1) | All reference and data symbols are used for phase tracking. |
        +--------------------+-------------------------------------------------------------+
        | PTRS (2)           | Only PTRS symbols are used for phase tracking.              |
        +--------------------+-------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccPhaseTrackingMode):
                Specifies the method used for phase tracking.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_PHASE_TRACKING_MODE.value
            )
            attr_val = enums.ModAccPhaseTrackingMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phase_tracking_mode(self, selector_string, value):
        r"""Sets the method used for phase tracking.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+-------------------------------------------------------------+
        | Name (Value)       | Description                                                 |
        +====================+=============================================================+
        | Disabled (0)       | Disables the phase tracking.                                |
        +--------------------+-------------------------------------------------------------+
        | Reference+Data (1) | All reference and data symbols are used for phase tracking. |
        +--------------------+-------------------------------------------------------------+
        | PTRS (2)           | Only PTRS symbols are used for phase tracking.              |
        +--------------------+-------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccPhaseTrackingMode, int):
                Specifies the method used for phase tracking.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccPhaseTrackingMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_PHASE_TRACKING_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_timing_tracking_mode(self, selector_string):
        r"""Gets the method used for timing tracking.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+--------------------------------------------------------------+
        | Name (Value)       | Description                                                  |
        +====================+==============================================================+
        | Disabled (0)       | Disables the timing tracking.                                |
        +--------------------+--------------------------------------------------------------+
        | Reference+Data (1) | All reference and data symbols are used for timing tracking. |
        +--------------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccTimingTrackingMode):
                Specifies the method used for timing tracking.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_TIMING_TRACKING_MODE.value
            )
            attr_val = enums.ModAccTimingTrackingMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_timing_tracking_mode(self, selector_string, value):
        r"""Sets the method used for timing tracking.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference+Data**.

        +--------------------+--------------------------------------------------------------+
        | Name (Value)       | Description                                                  |
        +====================+==============================================================+
        | Disabled (0)       | Disables the timing tracking.                                |
        +--------------------+--------------------------------------------------------------+
        | Reference+Data (1) | All reference and data symbols are used for timing tracking. |
        +--------------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccTimingTrackingMode, int):
                Specifies the method used for timing tracking.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccTimingTrackingMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_TIMING_TRACKING_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pre_fft_error_estimation_interval(self, selector_string):
        r"""Gets the interval used for Pre-FFT error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measurement Length**.

        +------------------------+----------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                  |
        +========================+==============================================================================================+
        | Slot (0)               | Frequency and timing error is estimated per slot in the pre-fft domain.                      |
        +------------------------+----------------------------------------------------------------------------------------------+
        | Measurement Length (1) | Frequency and timing error is estimated over the measurement interval in the pre-fft domain. |
        +------------------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccPreFftErrorEstimationInterval):
                Specifies the interval used for Pre-FFT error estimation.

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
                attributes.AttributeID.MODACC_PRE_FFT_ERROR_ESTIMATION_INTERVAL.value,
            )
            attr_val = enums.ModAccPreFftErrorEstimationInterval(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pre_fft_error_estimation_interval(self, selector_string, value):
        r"""Sets the interval used for Pre-FFT error estimation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measurement Length**.

        +------------------------+----------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                  |
        +========================+==============================================================================================+
        | Slot (0)               | Frequency and timing error is estimated per slot in the pre-fft domain.                      |
        +------------------------+----------------------------------------------------------------------------------------------+
        | Measurement Length (1) | Frequency and timing error is estimated over the measurement interval in the pre-fft domain. |
        +------------------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccPreFftErrorEstimationInterval, int):
                Specifies the interval used for Pre-FFT error estimation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccPreFftErrorEstimationInterval else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_PRE_FFT_ERROR_ESTIMATION_INTERVAL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_unit(self, selector_string):
        r"""Gets the units of the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Percentage**.

        +----------------+--------------------------------------+
        | Name (Value)   | Description                          |
        +================+======================================+
        | Percentage (0) | The EVM is reported as a percentage. |
        +----------------+--------------------------------------+
        | dB (1)         | The EVM is reported in dB.           |
        +----------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccEvmUnit):
                Specifies the units of the EVM results.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_EVM_UNIT.value
            )
            attr_val = enums.ModAccEvmUnit(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_unit(self, selector_string, value):
        r"""Sets the units of the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Percentage**.

        +----------------+--------------------------------------+
        | Name (Value)   | Description                          |
        +================+======================================+
        | Percentage (0) | The EVM is reported as a percentage. |
        +----------------+--------------------------------------+
        | dB (1)         | The EVM is reported in dB.           |
        +----------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccEvmUnit, int):
                Specifies the units of the EVM results.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccEvmUnit else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_EVM_UNIT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window_type(self, selector_string):
        r"""Gets the FFT window type used for EVM calculation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Custom**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | 3GPP (0)     | The maximum EVM between the start window position and the end window position is returned according to the 3GPP          |
        |              | specification. The FFT window positions are specified by the                                                             |
        |              | attribute.                                                                                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (1)   | Only one FFT window position is used for the EVM calculation. FFT window position is specified by ModAcc FFT Window      |
        |              | Offset attribute.                                                                                                        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccFftWindowType):
                Specifies the FFT window type used for EVM calculation.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_TYPE.value
            )
            attr_val = enums.ModAccFftWindowType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window_type(self, selector_string, value):
        r"""Sets the FFT window type used for EVM calculation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Custom**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | 3GPP (0)     | The maximum EVM between the start window position and the end window position is returned according to the 3GPP          |
        |              | specification. The FFT window positions are specified by the                                                             |
        |              | attribute.                                                                                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Custom (1)   | Only one FFT window position is used for the EVM calculation. FFT window position is specified by ModAcc FFT Window      |
        |              | Offset attribute.                                                                                                        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccFftWindowType, int):
                Specifies the FFT window type used for EVM calculation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccFftWindowType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window_offset(self, selector_string):
        r"""Gets the position of the FFT window used to calculate the EVM when
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute is set to **Custom**. The offset is
        expressed as a percentage of the cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end
        of cyclic prefix. If you set this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 50. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the position of the FFT window used to calculate the EVM when
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute is set to **Custom**. The offset is
                expressed as a percentage of the cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end
                of cyclic prefix. If you set this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window_offset(self, selector_string, value):
        r"""Sets the position of the FFT window used to calculate the EVM when
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute is set to **Custom**. The offset is
        expressed as a percentage of the cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end
        of cyclic prefix. If you set this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 50. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the position of the FFT window used to calculate the EVM when
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute is set to **Custom**. The offset is
                expressed as a percentage of the cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end
                of cyclic prefix. If you set this attribute to 100, the EVM window starts at the beginning of cyclic prefix.

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
                attributes.AttributeID.MODACC_FFT_WINDOW_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_fft_window_length(self, selector_string):
        r"""Gets the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
        attribute is used when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
        **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
        Delta_C+W/2.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is -1. Valid values range from -1 to 100, inclusive. When this attribute is set to -1, the
        measurement automatically sets the value of this attribute to the recommended value as specified in the Annexe F.5 of
        *3GPP TS 38.101-2* specification for uplink and Annexe B.5.2 and C.5.2 of *3GPP TS 38.104* specification for downlink.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
                attribute is used when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
                **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
                Delta_C+W/2.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_FFT_WINDOW_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_fft_window_length(self, selector_string, value):
        r"""Sets the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
        attribute is used when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
        **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
        Delta_C+W/2.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is -1. Valid values range from -1 to 100, inclusive. When this attribute is set to -1, the
        measurement automatically sets the value of this attribute to the recommended value as specified in the Annexe F.5 of
        *3GPP TS 38.101-2* specification for uplink and Annexe B.5.2 and C.5.2 of *3GPP TS 38.104* specification for downlink.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
                attribute is used when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
                **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
                Delta_C+W/2.

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
                attributes.AttributeID.MODACC_FFT_WINDOW_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_dc_subcarrier_removal_enabled(self, selector_string):
        r"""Gets whether the DC subcarrier is removed from the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | False (0)    | The DC subcarrier is present in the EVM results.   |
        +--------------+----------------------------------------------------+
        | True (1)     | The DC subcarrier is removed from the EVM results. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccDCSubcarrierRemovalEnabled):
                Specifies whether the DC subcarrier is removed from the EVM results.

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
                attributes.AttributeID.MODACC_DC_SUBCARRIER_REMOVAL_ENABLED.value,
            )
            attr_val = enums.ModAccDCSubcarrierRemovalEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_dc_subcarrier_removal_enabled(self, selector_string, value):
        r"""Sets whether the DC subcarrier is removed from the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | False (0)    | The DC subcarrier is present in the EVM results.   |
        +--------------+----------------------------------------------------+
        | True (1)     | The DC subcarrier is removed from the EVM results. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccDCSubcarrierRemovalEnabled, int):
                Specifies whether the DC subcarrier is removed from the EVM results.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccDCSubcarrierRemovalEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_DC_SUBCARRIER_REMOVAL_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_common_clock_source_enabled(self, selector_string):
        r"""Gets whether same reference clock is used for local oscillator and digital-to-analog converter. When same
        reference clock is used the Carrier Frequency Offset is proportional to Sample Clock Error.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------+
        | Name (Value) | Description                                                        |
        +==============+====================================================================+
        | False (0)    | The Sample Clock error is estimated independently.                 |
        +--------------+--------------------------------------------------------------------+
        | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
        +--------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccCommonClockSourceEnabled):
                Specifies whether same reference clock is used for local oscillator and digital-to-analog converter. When same
                reference clock is used the Carrier Frequency Offset is proportional to Sample Clock Error.

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
                attributes.AttributeID.MODACC_COMMON_CLOCK_SOURCE_ENABLED.value,
            )
            attr_val = enums.ModAccCommonClockSourceEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_common_clock_source_enabled(self, selector_string, value):
        r"""Sets whether same reference clock is used for local oscillator and digital-to-analog converter. When same
        reference clock is used the Carrier Frequency Offset is proportional to Sample Clock Error.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------+
        | Name (Value) | Description                                                        |
        +==============+====================================================================+
        | False (0)    | The Sample Clock error is estimated independently.                 |
        +--------------+--------------------------------------------------------------------+
        | True (1)     | The Sample Clock error is estimated from carrier frequency offset. |
        +--------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccCommonClockSourceEnabled, int):
                Specifies whether same reference clock is used for local oscillator and digital-to-analog converter. When same
                reference clock is used the Carrier Frequency Offset is proportional to Sample Clock Error.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccCommonClockSourceEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_COMMON_CLOCK_SOURCE_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_spectral_flatness_condition(self, selector_string):
        r"""Gets the test condition for Spectral Flatness measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Normal (0)   | Frequency range and maximum ripple defined in the section 6.4.2.4.1, Table 6.4.2.4.1-1 of 3GPP 38.101-1 and section      |
        |              | 6.4.2.4.1, Table 6.4.2.4.1-1 of 3GPP 38.101-2 are used.                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Extreme (1)  | Frequency range and maximum ripple defined in the section 6.4.2.4.1, Table 6.4.2.4.1-2 of 3GPP 38.101-1 and section      |
        |              | 6.4.2.4.1, Table 6.4.2.4.1-2 of 3GPP 38.101-2 are used.                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccSpectralFlatnessCondition):
                Specifies the test condition for Spectral Flatness measurement.

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
                attributes.AttributeID.MODACC_SPECTRAL_FLATNESS_CONDITION.value,
            )
            attr_val = enums.ModAccSpectralFlatnessCondition(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spectral_flatness_condition(self, selector_string, value):
        r"""Sets the test condition for Spectral Flatness measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Normal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Normal (0)   | Frequency range and maximum ripple defined in the section 6.4.2.4.1, Table 6.4.2.4.1-1 of 3GPP 38.101-1 and section      |
        |              | 6.4.2.4.1, Table 6.4.2.4.1-1 of 3GPP 38.101-2 are used.                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Extreme (1)  | Frequency range and maximum ripple defined in the section 6.4.2.4.1, Table 6.4.2.4.1-2 of 3GPP 38.101-1 and section      |
        |              | 6.4.2.4.1, Table 6.4.2.4.1-2 of 3GPP 38.101-2 are used.                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccSpectralFlatnessCondition, int):
                Specifies the test condition for Spectral Flatness measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccSpectralFlatnessCondition else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SPECTRAL_FLATNESS_CONDITION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_enabled(self, selector_string):
        r"""Gets whether the contribution of the instrument noise is compensated for EVM computation.
        You must measure the noise floor before applying the noise compensation. The instrument noise floor is measured
        for the RF path used by the ModAcc measurement and cached for future use.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Supported devices are NI 5831 and NI 5840/41. The default value is **False**.

        +--------------+-----------------------------------------------------+
        | Name (Value) | Description                                         |
        +==============+=====================================================+
        | False (0)    | Noise compensation is disabled for the measurement. |
        +--------------+-----------------------------------------------------+
        | True (1)     | Noise compensation is enabled for the measurement.  |
        +--------------+-----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccNoiseCompensationEnabled):
                Specifies whether the contribution of the instrument noise is compensated for EVM computation.
                You must measure the noise floor before applying the noise compensation. The instrument noise floor is measured
                for the RF path used by the ModAcc measurement and cached for future use.

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
                attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED.value,
            )
            attr_val = enums.ModAccNoiseCompensationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_enabled(self, selector_string, value):
        r"""Sets whether the contribution of the instrument noise is compensated for EVM computation.
        You must measure the noise floor before applying the noise compensation. The instrument noise floor is measured
        for the RF path used by the ModAcc measurement and cached for future use.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Supported devices are NI 5831 and NI 5840/41. The default value is **False**.

        +--------------+-----------------------------------------------------+
        | Name (Value) | Description                                         |
        +==============+=====================================================+
        | False (0)    | Noise compensation is disabled for the measurement. |
        +--------------+-----------------------------------------------------+
        | True (1)     | Noise compensation is enabled for the measurement.  |
        +--------------+-----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccNoiseCompensationEnabled, int):
                Specifies whether the contribution of the instrument noise is compensated for EVM computation.
                You must measure the noise floor before applying the noise compensation. The instrument noise floor is measured
                for the RF path used by the ModAcc measurement and cached for future use.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccNoiseCompensationEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_input_power_check_enabled(self, selector_string):
        r"""Gets whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
        performing noise floor calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | Disables the input power check at the RFIn port of the signal analyzer. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | Enables the input power check at the RFIn port of the signal analyzer.  |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccNoiseCompensationInputPowerCheckEnabled):
                Specifies whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
                performing noise floor calibration.

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
                attributes.AttributeID.MODACC_NOISE_COMPENSATION_INPUT_POWER_CHECK_ENABLED.value,
            )
            attr_val = enums.ModAccNoiseCompensationInputPowerCheckEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_input_power_check_enabled(self, selector_string, value):
        r"""Sets whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
        performing noise floor calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | Disables the input power check at the RFIn port of the signal analyzer. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | Enables the input power check at the RFIn port of the signal analyzer.  |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccNoiseCompensationInputPowerCheckEnabled, int):
                Specifies whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
                performing noise floor calibration.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.ModAccNoiseCompensationInputPowerCheckEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_NOISE_COMPENSATION_INPUT_POWER_CHECK_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_reference_level_coercion_limit(self, selector_string):
        r"""Gets the coercion limit for the reference level for noise compensation. When you set
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_MODE` attribute to **Measure** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED` attribute to **True**, the measurement
        attempts to read noise floor calibration data corresponding to the configured reference level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        If noise floor calibration data corresponding to the configured reference level is not found in the calibration
        database, the measurement attempts to read noise floor calibration data from the calibration database for any reference
        level in the range of the configured reference level plus the coercion limit you set for this attribute. The default
        value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the coercion limit for the reference level for noise compensation. When you set
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_MODE` attribute to **Measure** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED` attribute to **True**, the measurement
                attempts to read noise floor calibration data corresponding to the configured reference level.

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
                attributes.AttributeID.MODACC_NOISE_COMPENSATION_REFERENCE_LEVEL_COERCION_LIMIT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_reference_level_coercion_limit(self, selector_string, value):
        r"""Sets the coercion limit for the reference level for noise compensation. When you set
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_MODE` attribute to **Measure** and
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED` attribute to **True**, the measurement
        attempts to read noise floor calibration data corresponding to the configured reference level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        If noise floor calibration data corresponding to the configured reference level is not found in the calibration
        database, the measurement attempts to read noise floor calibration data from the calibration database for any reference
        level in the range of the configured reference level plus the coercion limit you set for this attribute. The default
        value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the coercion limit for the reference level for noise compensation. When you set
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_MODE` attribute to **Measure** and
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED` attribute to **True**, the measurement
                attempts to read noise floor calibration data corresponding to the configured reference level.

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
                attributes.AttributeID.MODACC_NOISE_COMPENSATION_REFERENCE_LEVEL_COERCION_LIMIT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_mode(self, selector_string):
        r"""Gets whether the measurement should calibrate the noise floor of the analyzer or perform the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                                                              |
        +===========================+==========================================================================================================================+
        | Measure (0)               | The ModAcc measurement is performed on the acquired signal.                                                              |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | The ModAcc measurement measures the noise floor of the instrument across the frequency determined by the carrier         |
        |                           | frequency and the channel bandwidth. In this mode, the measurement expects the signal generator to be turned off and     |
        |                           | checks if there is any signal power detected at RFIn port of the analyzer beyond a certain threshold. All scalar         |
        |                           | results and traces are invalid in this mode. Even if the instrument noise floor is already calibrated, the measurement   |
        |                           | performs all the required acquisitions and overwrites any pre-existing noise floor calibration data.                     |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccMeasurementMode):
                Specifies whether the measurement should calibrate the noise floor of the analyzer or perform the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_MODE.value
            )
            attr_val = enums.ModAccMeasurementMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_mode(self, selector_string, value):
        r"""Sets whether the measurement should calibrate the noise floor of the analyzer or perform the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                                                              |
        +===========================+==========================================================================================================================+
        | Measure (0)               | The ModAcc measurement is performed on the acquired signal.                                                              |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | The ModAcc measurement measures the noise floor of the instrument across the frequency determined by the carrier         |
        |                           | frequency and the channel bandwidth. In this mode, the measurement expects the signal generator to be turned off and     |
        |                           | checks if there is any signal power detected at RFIn port of the analyzer beyond a certain threshold. All scalar         |
        |                           | results and traces are invalid in this mode. Even if the instrument noise floor is already calibrated, the measurement   |
        |                           | performs all the required acquisitions and overwrites any pre-existing noise floor calibration data.                     |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccMeasurementMode, int):
                Specifies whether the measurement should calibrate the noise floor of the analyzer or perform the ModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccMeasurementMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_composite_results_include_dmrs(self, selector_string):
        r"""Gets whether the DMRS resource elements are included for composite EVM and magnitude and phase error results and
        traces.

        When using downlink test models, the DMRS resource elements are not included in composite results by default.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | The DMRS resource elements are not included. |
        +--------------+----------------------------------------------+
        | True (1)     | The DMRS resource elements are included.     |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccCompositeResultsIncludeDmrs):
                Specifies whether the DMRS resource elements are included for composite EVM and magnitude and phase error results and
                traces.

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
                attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_DMRS.value,
            )
            attr_val = enums.ModAccCompositeResultsIncludeDmrs(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_composite_results_include_dmrs(self, selector_string, value):
        r"""Sets whether the DMRS resource elements are included for composite EVM and magnitude and phase error results and
        traces.

        When using downlink test models, the DMRS resource elements are not included in composite results by default.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | The DMRS resource elements are not included. |
        +--------------+----------------------------------------------+
        | True (1)     | The DMRS resource elements are included.     |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccCompositeResultsIncludeDmrs, int):
                Specifies whether the DMRS resource elements are included for composite EVM and magnitude and phase error results and
                traces.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccCompositeResultsIncludeDmrs else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_DMRS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_composite_results_include_ptrs(self, selector_string):
        r"""Gets whether the PTRS resource elements are included for composite EVM and magnitude and phase error results and
        traces.

        When using downlink test models, the PTRS resource elements are not included in composite results by default.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | The PTRS resource elements are not included. |
        +--------------+----------------------------------------------+
        | True (1)     | The PTRS resource elements are included.     |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccCompositeResultsIncludePtrs):
                Specifies whether the PTRS resource elements are included for composite EVM and magnitude and phase error results and
                traces.

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
                attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_PTRS.value,
            )
            attr_val = enums.ModAccCompositeResultsIncludePtrs(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_composite_results_include_ptrs(self, selector_string, value):
        r"""Sets whether the PTRS resource elements are included for composite EVM and magnitude and phase error results and
        traces.

        When using downlink test models, the PTRS resource elements are not included in composite results by default.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | The PTRS resource elements are not included. |
        +--------------+----------------------------------------------+
        | True (1)     | The PTRS resource elements are included.     |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccCompositeResultsIncludePtrs, int):
                Specifies whether the PTRS resource elements are included for composite EVM and magnitude and phase error results and
                traces.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccCompositeResultsIncludePtrs else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_PTRS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Enables averaging for the measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the ModAcc Averaging   |
        |              | Count attribute.                                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccAveragingEnabled):
                Enables averaging for the measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_ENABLED.value
            )
            attr_val = enums.ModAccAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Enables averaging for the measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the ModAcc Averaging   |
        |              | Count attribute.                                                                                                         |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccAveragingEnabled, int):
                Enables averaging for the measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_level_allow_overflow(self, selector_string):
        r"""Gets whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
        overflow.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | Disables searching for the optimum reference levels while allowing ADC overflow. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | Enables searching for the optimum reference levels while allowing ADC overflow.  |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccAutoLevelAllowOverflow):
                Specifies whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
                overflow.

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
                attributes.AttributeID.MODACC_AUTO_LEVEL_ALLOW_OVERFLOW.value,
            )
            attr_val = enums.ModAccAutoLevelAllowOverflow(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_level_allow_overflow(self, selector_string, value):
        r"""Sets whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
        overflow.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | Disables searching for the optimum reference levels while allowing ADC overflow. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | Enables searching for the optimum reference levels while allowing ADC overflow.  |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccAutoLevelAllowOverflow, int):
                Specifies whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
                overflow.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccAutoLevelAllowOverflow else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_AUTO_LEVEL_ALLOW_OVERFLOW.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_short_frame_enabled(self, selector_string):
        r"""Gets whether the input signal has a periodicity shorter than the NR frame duration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | When you set the attribute to False or the Trigger Type attribute is set to a value other than None, a signal            |
        |              | periodicity equal to the maximum of 1 frame duration and the configured SSB periodicity, if SSB is active, is assumed.   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | When you set the attribute to False or the Trigger Type attribute is set to None, the measurement uses ModAcc Short      |
        |              | Frame Length as signal periodicity.                                                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccShortFrameEnabled):
                Specifies whether the input signal has a periodicity shorter than the NR frame duration.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_SHORT_FRAME_ENABLED.value
            )
            attr_val = enums.ModAccShortFrameEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_short_frame_enabled(self, selector_string, value):
        r"""Sets whether the input signal has a periodicity shorter than the NR frame duration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | When you set the attribute to False or the Trigger Type attribute is set to a value other than None, a signal            |
        |              | periodicity equal to the maximum of 1 frame duration and the configured SSB periodicity, if SSB is active, is assumed.   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | When you set the attribute to False or the Trigger Type attribute is set to None, the measurement uses ModAcc Short      |
        |              | Frame Length as signal periodicity.                                                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccShortFrameEnabled, int):
                Specifies whether the input signal has a periodicity shorter than the NR frame duration.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccShortFrameEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SHORT_FRAME_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_short_frame_length(self, selector_string):
        r"""Gets the short frame periodicity in unit specified by
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT`.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.01.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the short frame periodicity in unit specified by
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT`.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_short_frame_length(self, selector_string, value):
        r"""Sets the short frame periodicity in unit specified by
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT`.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.01.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the short frame periodicity in unit specified by
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT`.

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
                attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_short_frame_length_unit(self, selector_string):
        r"""Gets the units in which :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT` is specified.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Time**.

        +--------------+--------------------------------------------------------+
        | Name (Value) | Description                                            |
        +==============+========================================================+
        | Slot (1)     | Short frame length is specified in units of slots.     |
        +--------------+--------------------------------------------------------+
        | Subframe (3) | Short frame length is specified in units of subframes. |
        +--------------+--------------------------------------------------------+
        | Time (6)     | Short frame length is specified in units of time.      |
        +--------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccShortFrameLengthUnit):
                Specifies the units in which :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT` is specified.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT.value
            )
            attr_val = enums.ModAccShortFrameLengthUnit(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_short_frame_length_unit(self, selector_string, value):
        r"""Sets the units in which :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT` is specified.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Time**.

        +--------------+--------------------------------------------------------+
        | Name (Value) | Description                                            |
        +==============+========================================================+
        | Slot (1)     | Short frame length is specified in units of slots.     |
        +--------------+--------------------------------------------------------+
        | Subframe (3) | Short frame length is specified in units of subframes. |
        +--------------+--------------------------------------------------------+
        | Time (6)     | Short frame length is specified in units of time.      |
        +--------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccShortFrameLengthUnit, int):
                Specifies the units in which :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT` is specified.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccShortFrameLengthUnit else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transient_period_evm_mode(self, selector_string):
        r"""Configures the EVM measurement behavior for symbols affected by power transients.

        According to *3GPP 38.101-1 Rel. 17.6* transient EVM measurement (i.e. Transient Period EVM Mode set to
        **Include**) is applicable when :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` is set to **Uplink**,
        :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` is set to **Range 1**,
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` is set to **False**, and
        :py:attr:`~nirfmxnr.attributes.AttributeID.BANDWIDTH_PART_SUBCARRIER_SPACING` is set to **15kHz** or **30kHz**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Disabled (0) | No special treatment of transient symbols (old behavior).                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Exclude (1)  | Transient symbols are not considered for EVM computation.                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Include (2)  | Transient EVM measurement definition is applied to transient symbols and returned as a separate Transient RMS EVM        |
        |              | result.                                                                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccTransientPeriodEvmMode):
                Configures the EVM measurement behavior for symbols affected by power transients.

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
                attributes.AttributeID.MODACC_TRANSIENT_PERIOD_EVM_MODE.value,
            )
            attr_val = enums.ModAccTransientPeriodEvmMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transient_period_evm_mode(self, selector_string, value):
        r"""Configures the EVM measurement behavior for symbols affected by power transients.

        According to *3GPP 38.101-1 Rel. 17.6* transient EVM measurement (i.e. Transient Period EVM Mode set to
        **Include**) is applicable when :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` is set to **Uplink**,
        :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` is set to **Range 1**,
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` is set to **False**, and
        :py:attr:`~nirfmxnr.attributes.AttributeID.BANDWIDTH_PART_SUBCARRIER_SPACING` is set to **15kHz** or **30kHz**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Disabled (0) | No special treatment of transient symbols (old behavior).                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Exclude (1)  | Transient symbols are not considered for EVM computation.                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Include (2)  | Transient EVM measurement definition is applied to transient symbols and returned as a separate Transient RMS EVM        |
        |              | result.                                                                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccTransientPeriodEvmMode, int):
                Configures the EVM measurement behavior for symbols affected by power transients.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccTransientPeriodEvmMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_TRANSIENT_PERIOD_EVM_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transient_period(self, selector_string):
        r"""It configures the transient duration as specified in section 6.4.2.1a of *3GPP 38.101-1* specification.

        If :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_TRANSIENT_PERIOD_EVM_MODE` is set to **Include**,
        configures the transient duration to calculate FFT window positions used to compute the transient EVM as specified in
        section 6.4.2.1a of *3GPP 38.101-1* specification.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **2us**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                It configures the transient duration as specified in section 6.4.2.1a of *3GPP 38.101-1* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_TRANSIENT_PERIOD.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transient_period(self, selector_string, value):
        r"""It configures the transient duration as specified in section 6.4.2.1a of *3GPP 38.101-1* specification.

        If :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_TRANSIENT_PERIOD_EVM_MODE` is set to **Include**,
        configures the transient duration to calculate FFT window positions used to compute the transient EVM as specified in
        section 6.4.2.1a of *3GPP 38.101-1* specification.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **2us**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                It configures the transient duration as specified in section 6.4.2.1a of *3GPP 38.101-1* specification.

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
                updated_selector_string, attributes.AttributeID.MODACC_TRANSIENT_PERIOD.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transient_power_change_threshold(self, selector_string):
        r"""Gets transient period power change threshold level in dB.

        If a mean slot power has changed by more than this value from one slot to another, this slot boundary is
        handled as transient period. Note also that if RB mapping or modulation format has changed from one slot to another,
        this slot boundary is handled as transient period as well, even though the mean power has not changed.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies transient period power change threshold level in dB.

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
                attributes.AttributeID.MODACC_TRANSIENT_POWER_CHANGE_THRESHOLD.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transient_power_change_threshold(self, selector_string, value):
        r"""Sets transient period power change threshold level in dB.

        If a mean slot power has changed by more than this value from one slot to another, this slot boundary is
        handled as transient period. Note also that if RB mapping or modulation format has changed from one slot to another,
        this slot boundary is handled as transient period as well, even though the mean power has not changed.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies transient period power change threshold level in dB.

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
                attributes.AttributeID.MODACC_TRANSIENT_POWER_CHANGE_THRESHOLD.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

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
                Specifies whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.

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
                attributes.AttributeID.MODACC_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the ModAcc measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size,system resources,data
        availability,and other considerations.

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
                Specifies the maximum number of threads used for parallelism for the ModAcc measurement.

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
                attributes.AttributeID.MODACC_NUMBER_OF_ANALYSIS_THREADS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the ModAcc measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size,system resources,data
        availability,and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of threads used for parallelism for the ModAcc measurement.

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
                attributes.AttributeID.MODACC_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_mode(self, selector_string, measurement_mode):
        r"""Configures the measurement mode for the ModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_mode (enums.ModAccMeasurementMode, int):
                This parameter specifies whether the measurement should calibrate the noise floor of the analyzer or perform the ModAcc
                measurement. The default value is **Measure**.

                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)              | Description                                                                                                              |
                +===========================+==========================================================================================================================+
                | Measure (0)               | The ModAcc measurement is performed on the acquired signal.                                                              |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Calibrate Noise Floor (1) | The ModAcc measurement measures the noise floor of the instrument across the frequency range of interest determined by   |
                |                           | the carrier frequency and channel bandwidth. In this mode, the measurement expects that the signal generator to be       |
                |                           | turned off and checks whether no signal power is detected at the RF In port of the analyzer beyond a certain threshold.  |
                |                           | All scalar results and traces are invalid in this mode. Even if the instrument noise floor is previously calibrated,     |
                |                           | the measurement performs all the required acquisitions and overwrites any pre-existing noise floor calibration data.     |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurement_mode = (
                measurement_mode.value
                if type(measurement_mode) is enums.ModAccMeasurementMode
                else measurement_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_measurement_mode(
                updated_selector_string, measurement_mode
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_reference_waveform(self, selector_string, x0, dx, reference_waveform):
        r"""Configures the reference waveform for the creation of reference data symbols for EVM computation.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            x0 (float):
                This parameter specifies the start time, in seconds.

            dx (float):
                This parameter specifies the sample duration, in seconds.

            reference_waveform (numpy.complex64):
                This parameter specifies the complex baseband samples, in volts.

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
            error_code = self._interpreter.modacc_configure_reference_waveform(
                updated_selector_string, x0, dx, reference_waveform
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        r"""Configures whether to enable EVM noise compensation for the ModAcc measurement.

        **Supported devices: **PXIe-5830/5831/5832/5646/5840/5841/5842/5860.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            noise_compensation_enabled (enums.ModAccNoiseCompensationEnabled, int):
                This parameter specifies whether the contribution of the instrument noise is compensated for EVM computation. The
                default value is **False**.

                +--------------+---------------------------------------------------------+
                | Name (Value) | Description                                             |
                +==============+=========================================================+
                | False (0)    | Disables instrument noise compensation for EVM results. |
                +--------------+---------------------------------------------------------+
                | True (1)     | Enables instrument noise compensation for EVM results.  |
                +--------------+---------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            noise_compensation_enabled = (
                noise_compensation_enabled.value
                if type(noise_compensation_enabled) is enums.ModAccNoiseCompensationEnabled
                else noise_compensation_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_noise_compensation_enabled(
                updated_selector_string, noise_compensation_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_level(self, selector_string, timeout):
        r"""Performs the user-configured ModAcc measurement at multiple reference levels relative to the user-configured
        :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute and configures the reference level corresponding
        to the lowest :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_RESULTS_COMPOSITE_RMS_EVM_MEAN` result.

        This method only measures at the reference levels that do not result in an ADC or DSP overflow when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AUTO_LEVEL_ALLOW_OVERFLOW` attribute to **False**. If you set the
        ModAcc Auto Level Allow Overflow attribute to **True**, this method measures at a few reference levels beyond the
        overflow. After calling the ModAcc Auto Level method, you need to call the ModAcc measurement.

        .. note::
           Calling this method will also set the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL_HEADROOM` attribute to
           0.

        This method expects:

        - A valid ModAcc measurement configuration

        - Reference Level attribute set to peak power of the signal

        - Repetitive signals at the analyzer's input along with trigger settings that measure the same portion of the waveform every time the measurement is performed

        - No other measurements are running in parallel

        Auto level needs to be performed again if the input signal or RFmx configuration changes.

        For repeatable results, you must make sure that the ModAcc measurement is repeatable.

        This method measures EVM at reference levels starting at an integer at least 1 dB above the value you configure
        for the Reference Level attribute, extending upto 12 dB lower when you set the ModAcc Auto Level Allow Overflow
        attribute to **False**, and up to 17 dB lower when you set the ModAcc Auto Level Allow Overflow attribute to **True**
        with a step size of 0.5 dB.

        When you use this method with the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_NOISE_COMPENSATION_ENABLED`
        attribute set to **True**, you need to make sure that valid noise calibration data is available for the above
        measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            timeout (float):
                This parameter specifies the timeout for fetching the EVM results. This value is expressed in seconds. Set this value
                to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the method
                waits until the measurement is complete. The default value is 10.

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
            error_code = self._interpreter.modacc_auto_level(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def validate_calibration_data(self, selector_string):
        r"""Specifies whether calibration data is valid for the configuration specified by the signal name in the **Selector
        String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (calibration_data_valid, error_code):

            calibration_data_valid (enums.ModAccCalibrationDataValid):
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
            calibration_data_valid, error_code = self._interpreter.modacc_validate_calibration_data(
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return calibration_data_valid, error_code

    @_raise_if_disposed
    def clear_noise_calibration_database(self):
        r"""Clears the noise calibration database used for EVM noise compensation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_code = self._interpreter.modacc_clear_noise_calibration_database()
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
