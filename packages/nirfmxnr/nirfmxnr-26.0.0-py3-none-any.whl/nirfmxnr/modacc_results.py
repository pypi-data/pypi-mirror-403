"""Provides methods to fetch and read the ModAcc measurement results."""

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


class ModAccResults(object):
    """Provides methods to fetch and read the ModAcc measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the ModAcc measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_detected_cell_id(self, selector_string):
        r"""Gets the detected Cell ID, if the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_CELL_ID_DETECTION_ENABLED`
        attribute is set to **True**. A value of **-1** is returned, if the measurement fails to auto detect the Cell ID.

        Returns the user configured Cell ID, if the Auto Cell ID Detection Enabled attribute is set to **False**.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the detected Cell ID, if the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_CELL_ID_DETECTION_ENABLED`
                attribute is set to **True**. A value of **-1** is returned, if the measurement fails to auto detect the Cell ID.

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
                attributes.AttributeID.MODACC_RESULTS_DETECTED_CELL_ID.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length.

        .. note::
           If :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_DMRS` attribute and
           :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_PTRS` attribute are set to **False**, EVM
           is computed only for the shared channel.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length.

        .. note::
           If :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_DMRS` attribute and
           :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_COMPOSITE_RESULTS_INCLUDE_PTRS` attribute are set to **False**, EVM
           is computed only for the shared channel.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_evm_bwp_index(self, selector_string):
        r"""Gets the bandwidth part index where ModAcc Results Max Pk Composite EVM occurs.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the bandwidth part index where ModAcc Results Max Pk Composite EVM occurs.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_EVM_BWP_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_evm_slot_index(self, selector_string):
        r"""Gets the slot index where ModAcc Results Max Pk Composite EVM occurs.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the slot index where ModAcc Results Max Pk Composite EVM occurs.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_EVM_SLOT_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_evm_symbol_index(self, selector_string):
        r"""Gets the symbol index where ModAcc Results Max Pk Composite EVM occurs.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the symbol index where ModAcc Results Max Pk Composite EVM occurs.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_EVM_SYMBOL_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_evm_subcarrier_index(self, selector_string):
        r"""Gets the subcarrier index where ModAcc Results Max Pk Composite EVM occurs.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the subcarrier index where ModAcc Results Max Pk Composite EVM occurs.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_EVM_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_rms_magnitude_error_mean(self, selector_string):
        r"""Gets the RMS mean value of magnitude error calculated over measurement length on all configured channels.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS mean value of magnitude error calculated over measurement length on all configured channels.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_RMS_MAGNITUDE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_magnitude_error_maximum(self, selector_string):
        r"""Gets the peak value of magnitude error calculated over measurement length on all configured channels.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak value of magnitude error calculated over measurement length on all configured channels.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_MAGNITUDE_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_rms_phase_error_mean(self, selector_string):
        r"""Gets the RMS mean value of Phase error calculated over measurement length on all configured channels. This value is
        expressed in degrees.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS mean value of Phase error calculated over measurement length on all configured channels. This value is
                expressed in degrees.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_RMS_PHASE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_peak_phase_error_maximum(self, selector_string):
        r"""Gets the peak value of Phase error calculated over measurement length on all configured channels. This value is
        expressed in degrees.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak value of Phase error calculated over measurement length on all configured channels. This value is
                expressed in degrees.

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
                attributes.AttributeID.MODACC_RESULTS_COMPOSITE_PEAK_PHASE_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sch_symbol_power_mean(self, selector_string):
        r"""Gets the mean value (over :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`) of power calculated
        on OFDM symbols allocated only with the shared channel.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`) of power calculated
                on OFDM symbols allocated only with the shared channel.

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
                attributes.AttributeID.MODACC_RESULTS_SCH_SYMBOL_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sch_detected_modulation_type(self, selector_string):
        r"""Gets the modulation of the shared channel user data if you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**; otherwise,
        returns the configured modulation of the shared user data.

        In case of downlink test model, the modulation type specified by the 3GPP standard is returned.

        The returned values of detected modulation type for uplink are as shown in the following table:

        +-----------------------------------------------------------------------------------+-------------------------------------------------------------------------------------+
        | :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` | Returned Value                                                                      |
        +===================================================================================+=====================================================================================+
        | True                                                                              | Detected modulation of PUSCH user data                                              |
        +-----------------------------------------------------------------------------------+-------------------------------------------------------------------------------------+
        | False                                                                             | Value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MODULATION_TYPE` property |
        +-----------------------------------------------------------------------------------+-------------------------------------------------------------------------------------+

        The returned values of detected modulation type for downlink are as shown in the following table:

        +---------------------------------------------------------------------------------+-----------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
        | :py:attr:`~nirfmxnr.attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE` | :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` | Returned Value                                                                                                     |
        +=================================================================================+===================================================================================+====================================================================================================================+
        | User Defined                                                                    | True                                                                              | Detected modulation of PDSCH User Data                                                                             |
        +---------------------------------------------------------------------------------+-----------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
        | User Defined                                                                    | False                                                                             | Value of :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_MODULATION_TYPE` property                                |
        +---------------------------------------------------------------------------------+-----------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------+
        | Test Model                                                                      | -                                                                                 | Modulation of specified user of test model as specified in the 3GPP TS38.141-1 and 3GPP TS38.141-2 specifications. |
        +---------------------------------------------------------------------------------+-----------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------------+

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/ bwp<*m*>/
        user<*l*>" or "subblock<*n*>/carrier<*k*>/ bwp<*m*>/ user<*l*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.

        +---------------+-----------------------------------------------+
        | Name (Value)  | Description                                   |
        +===============+===============================================+
        | PI/2 BPSK (0) | Specifies the PI/2 BPSK modulation scheme.    |
        +---------------+-----------------------------------------------+
        | QPSK (1)      | Specifies the QPSK modulation scheme.         |
        +---------------+-----------------------------------------------+
        | 16 QAM (2)    | Specifies the 16 QAM modulation scheme.       |
        +---------------+-----------------------------------------------+
        | 64 QAM (3)    | Specifies the 64 QAM modulation scheme.       |
        +---------------+-----------------------------------------------+
        | 256 QAM (4)   | Specifies the 256 QAM modulation scheme.      |
        +---------------+-----------------------------------------------+
        | 1024 QAM (5)  | Specifies a 1024 QAM modulation scheme.       |
        +---------------+-----------------------------------------------+
        | 8 PSK (100)   | Specifies the PDSCH 8 PSK constellation trace |
        +---------------+-----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SchDetectedModulationType):
                Returns the modulation of the shared channel user data if you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**; otherwise,
                returns the configured modulation of the shared user data.

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
                attributes.AttributeID.MODACC_RESULTS_SCH_DETECTED_MODULATION_TYPE.value,
            )
            attr_val = enums.SchDetectedModulationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_data_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on PUSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on PUSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_data_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PUSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PUSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DATA_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_dmrs_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on PUSCH DMRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on PUSCH DMRS.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DMRS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_dmrs_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PUSCH DMRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PUSCH DMRS.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DMRS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_ptrs_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on PUSCH PTRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on PUSCH PTRS.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_PTRS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_ptrs_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PUSCH PTRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/ bwp<*m*>/
        user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PUSCH PTRS.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_PTRS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_data_re_power_mean(self, selector_string):
        r"""Gets the mean value (over Meas Length) of power calculated on PUSCH data REs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over Meas Length) of power calculated on PUSCH data REs.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DATA_RE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_dmrs_re_power_mean(self, selector_string):
        r"""Gets the mean value (over Meas Length) of power calculated on PUSCH DMRS REs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over Meas Length) of power calculated on PUSCH DMRS REs.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DMRS_RE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_ptrs_re_power_mean(self, selector_string):
        r"""Gets the mean value (over Meas Length) of power calculated on PUSCH PTRS REs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over Meas Length) of power calculated on PUSCH PTRS REs.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_PTRS_RE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_data_transient_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calulated over measurement interval for the PUSCH symbols where the transient
        occurs.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calulated over measurement interval for the PUSCH symbols where the transient
                occurs.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_DATA_TRANSIENT_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_peak_phase_offset_maximum(self, selector_string):
        r"""Gets the maximum value over Meas Length of peak phase offsets between the reference and measurement slots.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value over Meas Length of peak phase offsets between the reference and measurement slots.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_PEAK_PHASE_OFFSET_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pusch_peak_phase_offset_slot_index(self, selector_string):
        r"""Gets the slot index where ModAcc Results PUSCH Pk Phase Offset Max occurs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the slot index where ModAcc Results PUSCH Pk Phase Offset Max occurs.

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
                attributes.AttributeID.MODACC_RESULTS_PUSCH_PEAK_PHASE_OFFSET_SLOT_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_qpsk_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on all  QPSK modulated PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on all  QPSK modulated PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_QPSK_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_16qam_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on all  16 QAM modulated PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on all  16 QAM modulated PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_16QAM_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_64qam_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on all  64 QAM modulated PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on all  64 QAM modulated PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_64QAM_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_256qam_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on all  256 QAM modulated PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on all  256 QAM modulated PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_256QAM_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_1024qam_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on all 1024 QAM modulated PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on all 1024 QAM modulated PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_1024QAM_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_8psk_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on all 8 PSK modulated PDSCH data symbols.

        Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
        String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on all 8 PSK modulated PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_8PSK_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_data_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_data_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PDSCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PDSCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_DATA_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on PDSCH DMRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on PDSCH DMRS.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_DMRS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PDSCH DMRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PDSCH DMRS.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_DMRS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs calculated over measurement length on PDSCH PTRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs calculated over measurement length on PDSCH PTRS.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_PTRS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PDSCH PTRS.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PDSCH PTRS.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_PTRS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_data_re_power_mean(self, selector_string):
        r"""Gets the mean value (over Meas Length) of power calculated on PDSCH data REs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over Meas Length) of power calculated on PDSCH data REs.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_DATA_RE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_dmrs_re_power_mean(self, selector_string):
        r"""Gets the mean value (over Meas Length) of power calculated on PDSCH DMRS REs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over Meas Length) of power calculated on PDSCH DMRS REs.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_DMRS_RE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pdsch_ptrs_re_power_mean(self, selector_string):
        r"""Gets the mean value (over Meas Length) of power calculated on PDSCH PTRS REs.

        Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
        "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value (over Meas Length) of power calculated on PDSCH PTRS REs.

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
                attributes.AttributeID.MODACC_RESULTS_PDSCH_PTRS_RE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pss_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs computed over measurement length on PSS symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs computed over measurement length on PSS symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PSS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pss_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on PSS symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on PSS symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PSS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sss_rms_evm_mean(self, selector_string):
        r"""Gets the mean value of RMS EVMs computed over measurement length on SSS symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value of RMS EVMs computed over measurement length on SSS symbols.

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
                attributes.AttributeID.MODACC_RESULTS_SSS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sss_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value of peak EVMs calculated over measurement length on SSS symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value of peak EVMs calculated over measurement length on SSS symbols.

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
                attributes.AttributeID.MODACC_RESULTS_SSS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pbch_data_rms_evm_mean(self, selector_string):
        r"""Gets the mean value calculated over measurement length of RMS EVMs calculated on PBCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value calculated over measurement length of RMS EVMs calculated on PBCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PBCH_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pbch_data_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value calculated over measurement length of peak EVMs calculated on PBCH data symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value calculated over measurement length of peak EVMs calculated on PBCH data symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PBCH_DATA_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pbch_dmrs_rms_evm_mean(self, selector_string):
        r"""Gets the mean value calculated over measurement length of RMS EVMs calculated on PBCH DMRS symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the mean value calculated over measurement length of RMS EVMs calculated on PBCH DMRS symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PBCH_DMRS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pbch_dmrs_peak_evm_maximum(self, selector_string):
        r"""Gets the maximum value calculated over measurement length of peak EVMs calculated on PBCH DMRS symbols.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
        measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
        returns this result in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum value calculated over measurement length of peak EVMs calculated on PBCH DMRS symbols.

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
                attributes.AttributeID.MODACC_RESULTS_PBCH_DMRS_PEAK_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_in_band_emission_margin(self, selector_string):
        r"""Gets In-Band Emission Margin of the component carrier. This value is expressed in dB.

        Margin is the smallest difference between In-Band Emission measurement trace and limit trace. The limit is
        defined in section 6.4.2.3 and section 6.4F.2.3 of *3GPP 38.101-1* specification and section 6.4.2.3 of *3GPP 38.101-2*
        specification. In-Band emission is measured as the ratio of the power in non-allocated resource blocks to the power in
        the allocated resource blocks averaged over the measurement interval. For NR bands, the margin is not returned in case
        of clustered PUSCH allocation, or when there is full allocation of resource blocks. For NR unlicensed bands, the margin
        is returned only for RIV=1 and RIV=5 mentioned in the section 6.4F.2.3 of *3GPP 38.101-1* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns In-Band Emission Margin of the component carrier. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_IN_BAND_EMISSION_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_in_band_emission_margin(self, selector_string):
        r"""Gets In-Band Emission Margin of the subblock's aggregated bandwidth. This value is expressed in dB.

        Margin is the smallest difference between In-Band Emission measurement trace and the limit trace. The limit is
        defined in section 6.4A.2.2.2 of *3GPP 38.101-1* specification and section 6.4A.2.3 of *3GPP 38.101-2* specification.
        In-Band emission is measured as the ratio of the power in non-allocated resource blocks to the power in the allocated
        resource blocks averaged over the measurement interval. The margin is not returned in case of clustered PUSCH
        allocation, or when there is more than one active carrier, or when there is full allocation of resource blocks, or when
        carriers with different sub-carrier spacing are aggregated or when the number of carriers is greater than 2.

        Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns In-Band Emission Margin of the subblock's aggregated bandwidth. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_IN_BAND_EMISSION_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_margin_slot_index(self, selector_string):
        r"""Gets the slot index with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP
        38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2*.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the slot index with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP
                38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2*.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_SLOT_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range1_maximum_to_range1_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the magnitude of EVM equalizer coefficients within Range1 for the measurement unit,
        that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
        specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the magnitude of EVM equalizer coefficients within Range1 for the measurement unit,
                that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
                specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE1_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range2_maximum_to_range2_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the magnitude of EVM equalizer coefficients within Range2 for the Measurement unit,
        that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
        specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.  This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the magnitude of EVM equalizer coefficients within Range2 for the Measurement unit,
                that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
                specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.  This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE2_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range1_maximum_to_range2_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the EVM equalizer coefficients from maximum in Range1 to minimum in Range2 for the
        Measurement unit that has the worst ripple margin among all four ripple results defined in 3section 6.4.2.4.1 of *3GPP
        38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the EVM equalizer coefficients from maximum in Range1 to minimum in Range2 for the
                Measurement unit that has the worst ripple margin among all four ripple results defined in 3section 6.4.2.4.1 of *3GPP
                38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE2_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range2_maximum_to_range1_minimum(self, selector_string):
        r"""Gets the peak-to-peak ripple of the EVM equalizer coefficients from maximum in Range2 to minimum in Range1 for the
        Measurement unit that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP
        38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak-to-peak ripple of the EVM equalizer coefficients from maximum in Range2 to minimum in Range1 for the
                Measurement unit that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP
                38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE1_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range1_maximum(self, selector_string):
        r"""Gets the maximum magnitude of the EVM equalizer coefficients within Range1 for the measurement unit with the worst
        ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
        6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum magnitude of the EVM equalizer coefficients within Range1 for the measurement unit with the worst
                ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
                6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range1_minimum(self, selector_string):
        r"""Gets the minimum magnitude of EVM equalizer coefficients within Range1 for the measurement unit with the worst
        ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
        6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the minimum magnitude of EVM equalizer coefficients within Range1 for the measurement unit with the worst
                ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
                6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range2_maximum(self, selector_string):
        r"""Gets the maximum magnitude of EVM equalizer coefficients within Range2 for the measurement unit with the worst
        ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
        6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the maximum magnitude of EVM equalizer coefficients within Range2 for the measurement unit with the worst
                ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
                6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range2_minimum(self, selector_string):
        r"""Gets the minimum magnitude of EVM equalizer coefficients within Range2 for the measurement unit with the worst
        ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
        6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the minimum magnitude of EVM equalizer coefficients within Range2 for the measurement unit with the worst
                ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
                6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range1_maximum_subcarrier_index(self, selector_string):
        r"""Gets the maximum subcarrier index magnitude of EVM equalizer coefficients within Range1 for the measurement unit
        with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
        specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the maximum subcarrier index magnitude of EVM equalizer coefficients within Range1 for the measurement unit
                with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
                specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range1_minimum_subcarrier_index(self, selector_string):
        r"""Gets the minimum subcarrier index magnitude of EVM equalizer coefficients within Range1 for the measurement unit
        with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
        specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the minimum subcarrier index magnitude of EVM equalizer coefficients within Range1 for the measurement unit
                with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
                specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MINIMUM_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range2_maximum_subcarrier_index(self, selector_string):
        r"""Gets the maximum subcarrier index magnitude of EVM equalizer coefficients within Range2 for the measurement unit
        with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
        specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the maximum subcarrier index magnitude of EVM equalizer coefficients within Range2 for the measurement unit
                with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
                specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_range2_minimum_subcarrier_index(self, selector_string):
        r"""Gets the minimum subcarrier index magnitude of EVM equalizer coefficients within Range2 for the measurement unit
        with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
        specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the minimum subcarrier index magnitude of EVM equalizer coefficients within Range2 for the measurement unit
                with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
                specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.

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
                attributes.AttributeID.MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MINIMUM_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_time_offset_mean(self, selector_string):
        r"""Gets the time difference between the detected slot or frame boundary depending on the sync mode and reference
        trigger location. This value is expressed in seconds.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/chain<*r*>"as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the time difference between the detected slot or frame boundary depending on the sync mode and reference
                trigger location. This value is expressed in seconds.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_TIME_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_frequency_error_mean(self, selector_string):
        r"""Gets the estimated carrier frequency offset averaged over measurement length. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated carrier frequency offset averaged over measurement length. This value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_FREQUENCY_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_slot_frequency_error_maximum(self, selector_string):
        r"""Gets the estimated maximum per slot carrier frequency offset over the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated maximum per slot carrier frequency offset over the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_SLOT_FREQUENCY_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_symbol_clock_error_mean(self, selector_string):
        r"""Gets the estimated sample clock error averaged over measurement length. This value is expressed in ppm.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated sample clock error averaged over measurement length. This value is expressed in ppm.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_SYMBOL_CLOCK_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_time_alignment_error_mean(self, selector_string):
        r"""Gets the difference in the timing error, in seconds, of a CC with respect to the reference CC. The reference CC is
        fixed to Subblock0/ComponentCarrier0. The timing error reported is a frame timing error when the synchronization mode
        is set to 'Frame' and is slot timing error when the synchronization mode is set to 'Slot'.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the difference in the timing error, in seconds, of a CC with respect to the reference CC. The reference CC is
                fixed to Subblock0/ComponentCarrier0. The timing error reported is a frame timing error when the synchronization mode
                is set to 'Frame' and is slot timing error when the synchronization mode is set to 'Slot'.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_TIME_ALIGNMENT_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_iq_origin_offset_mean(self, selector_string):
        r"""Gets the estimated IQ origin offset averaged over measurement length.  This value is expressed in dBc.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated IQ origin offset averaged over measurement length.  This value is expressed in dBc.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_IQ_ORIGIN_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_slot_iq_origin_offset_maximum(self, selector_string):
        r"""Gets the estimated maximum per slot carrier IQ origin offset over the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated maximum per slot carrier IQ origin offset over the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_SLOT_IQ_ORIGIN_OFFSET_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_iq_gain_imbalance_mean(self, selector_string):
        r"""Gets the estimated IQ gain imbalance averaged over measurement length. This value is expressed in dB. IQ gain
        imbalance is the ratio of the amplitude of the I component to the Q component of the IQ signal being measured.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated IQ gain imbalance averaged over measurement length. This value is expressed in dB. IQ gain
                imbalance is the ratio of the amplitude of the I component to the Q component of the IQ signal being measured.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_IQ_GAIN_IMBALANCE_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_quadrature_error_mean(self, selector_string):
        r"""Gets the estimated quadrature error averaged over measurement length. This value is expressed in degrees. Quadrature
        error is the measure of skewness in degree of the I component with respect to the Q component of the IQ signal being
        measured.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated quadrature error averaged over measurement length. This value is expressed in degrees. Quadrature
                error is the measure of skewness in degree of the I component with respect to the Q component of the IQ signal being
                measured.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_QUADRATURE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_iq_timing_skew_mean(self, selector_string):
        r"""Gets the estimated IQ Timing Skew averaged over
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        IQ Timing skew is the difference between the group delay of the in-phase (I) and quadrature (Q) components of
        the signal. This value is expressed in seconds.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated IQ Timing Skew averaged over
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_IQ_TIMING_SKEW_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_component_carrier_cross_power_mean(self, selector_string):
        r"""Gets the cross power. The cross power for chain x is the power contribution from layers other than layer x in the
        chain. This value is expressed in dB.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the cross power. The cross power for chain x is the power contribution from layers other than layer x in the
                chain. This value is expressed in dB.

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
                attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_CROSS_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_lo_component_carrier_index(self, selector_string):
        r"""Gets the index of the component carrier that includes the LO of the transmitter according to the
        :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_FREQUENCY` and
        :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY` attributes. If the LO of the transmitter
        doesn't fall into any component carrier of the subblock, the attribute returns -1.  This result is valid only when you
        set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.

        Use "subblock<*n*>"or "subblock<*n*>/chain<*r*>"  as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the index of the component carrier that includes the LO of the transmitter according to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_FREQUENCY` and
                :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY` attributes. If the LO of the transmitter
                doesn't fall into any component carrier of the subblock, the attribute returns -1.  This result is valid only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_LO_COMPONENT_CARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_lo_subcarrier_index(self, selector_string):
        r"""Gets the subcarrier index within the respective component carrier where the transmitter LO is located. Due to its
        dependence on :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_FREQUENCY` and
        :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY` properties, the value can be fractional, and
        the LO might reside in between subcarriers of a component carrier. This result is valid only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.

        Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>"   as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the subcarrier index within the respective component carrier where the transmitter LO is located. Due to its
                dependence on :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_FREQUENCY` and
                :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY` properties, the value can be fractional, and
                the LO might reside in between subcarriers of a component carrier. This result is valid only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_LO_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_iq_origin_offset_mean(self, selector_string):
        r"""Gets the estimated IQ origin offset averaged over measurement length in the subblock. This value is expressed in
        dBc. This result is valid only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE`
        attribute to **LO per Subblock**.

        Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the estimated IQ origin offset averaged over measurement length in the subblock. This value is expressed in
                dBc. This result is valid only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE`
                attribute to **LO per Subblock**.

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
                attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_IQ_ORIGIN_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_noise_compensation_applied(self, selector_string):
        r"""Gets whether the noise compensation is applied to the EVM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------+
        | Name (Value) | Description                                               |
        +==============+===========================================================+
        | False (0)    | Noise compensation is not applied to the EVM measurement. |
        +--------------+-----------------------------------------------------------+
        | True (1)     | Noise compensation is applied to the EVM measurement.     |
        +--------------+-----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccNoiseCompensationApplied):
                Specifies whether the noise compensation is applied to the EVM measurement.

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
                attributes.AttributeID.MODACC_RESULTS_NOISE_COMPENSATION_APPLIED.value,
            )
            attr_val = enums.ModAccNoiseCompensationApplied(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_composite_evm(self, selector_string, timeout):
        r"""Fetches the composite EVM for ModAcc measurements.

        Use "carrier<*k*>" or "subblock<*n*>/carrier<*k*>" or "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector
        string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (composite_rms_evm_mean, composite_peak_evm_maximum, error_code):

            composite_rms_evm_mean (float):
                This parameter returns the mean value of the RMS EVMs calculated on all configured channels over the slots specified by
                the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns this
                result as a percentage.When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to
                **dB**, the measurement returns this result in dB.

            composite_peak_evm_maximum (float):
                This parameter returns the maximum value of the peak EVMs calculated on all configured channels over the slots
                specified by the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. When you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns this
                result as a percentage.When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to
                **dB**, the measurement returns this result in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            composite_rms_evm_mean, composite_peak_evm_maximum, error_code = (
                self._interpreter.modacc_fetch_composite_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return composite_rms_evm_mean, composite_peak_evm_maximum, error_code

    @_raise_if_disposed
    def fetch_frequency_error_mean(self, selector_string, timeout):
        r"""Fetches the estimated carrier frequency offset averaged over measurement length. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read this result.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (frequency_error_mean, error_code):

            frequency_error_mean (float):
                This parameter returns the estimated carrier frequency offset averaged over measurement length. This value is expressed
                in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            frequency_error_mean, error_code = self._interpreter.modacc_fetch_frequency_error_mean(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return frequency_error_mean, error_code

    @_raise_if_disposed
    def fetch_in_band_emission_trace(
        self, selector_string, timeout, in_band_emission, in_band_emission_mask
    ):
        r"""Fetches the in-band emission trace and limits trace for the component carrier. In-band emission is measured as the
        ratio of the power in non-allocated resource blocks to the power in the allocated resource blocks averaged over the
        measurement interval. The IBE for various regions (general, carrier leakage, and I/Q Image) are obtained and
        concatenated to form a composite trace and the limits are defined in section 6.4.2.3 of *3GPP 38.101-1*, and section
        6.4.2.3 of *3GPP 38.101-2*. The trace is not returned when there is full allocation of bandwidth, or there is clustered
        PUSCH or there is more than one active component carrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/chain<*r*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and chain number.

                Example:

                "subblock0/carrier0/chain0"

                "result::r1/subblock0/carrier0/chain0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_chain_string`VIs to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            in_band_emission (numpy.float32):
                This parameter returns an array of the in-band emission value as an array for each of the resource blocks. In-band
                emission is the interference falling into non-allocated resource blocks. This value is expressed in dB.

            in_band_emission_mask (numpy.float32):
                This parameter returns an array of the in-band emission value as an array for each of the resource blocks. In-band
                emission is the interference falling into non-allocated resource blocks. This value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns the subcarrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_in_band_emission_trace(
                updated_selector_string, timeout, in_band_emission, in_band_emission_mask
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pbch_data_constellation_trace(
        self, selector_string, timeout, pbch_data_constellation
    ):
        r"""Fetches the PBCH data trace. The constellation points of different slots in the measurement length is concatenated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pbch_data_constellation (numpy.complex64):
                This parameter returns the PBCH data trace.

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
            error_code = self._interpreter.modacc_fetch_pbch_data_constellation_trace(
                updated_selector_string, timeout, pbch_data_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pbch_data_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pbch_data_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the mean PBCH data RMS EVM of each subcarrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pbch_data_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns an array which the EVM of each allocated subcarrier averaged across all the symbols allocated
                with PBCH data within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource grid.

            dx (float):
                This parameter returns the subcarrier spacing of SSB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_pbch_data_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, pbch_data_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pbch_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pbch_data_rms_evm_per_symbol_mean
    ):
        r"""Fetches the mean PBCH data RMS EVM for each symbol.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pbch_data_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array which the EVM of each symbol averaged across all the allocated subcarriers allocated
                with PBCH data within symbol.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start symbol index from the frame start in terms of SSB numerology.

            dx (float):
                This parameter returns the width in terms of symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_pbch_data_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, pbch_data_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pbch_dmrs_constellation_trace(
        self, selector_string, timeout, pbch_dmrs_constellation
    ):
        r"""Fetches the PBCH DMRS trace. The constellation points of different slots in the measurement length is concatenated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pbch_dmrs_constellation (numpy.complex64):
                This parameter returns the PBCH DMRS trace.

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
            error_code = self._interpreter.modacc_fetch_pbch_dmrs_constellation_trace(
                updated_selector_string, timeout, pbch_dmrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pbch_dmrs_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pbch_dmrs_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the mean PBCH DMRS RMS EVM for each subcarrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pbch_dmrs_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns an array which the EVM of each allocated subcarrier averaged across all the symbols allocated
                with PBCH DMRS within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource grid.

            dx (float):
                This parameter returns the subcarrier spacing of SSB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_pbch_dmrs_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, pbch_dmrs_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pbch_dmrs_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pbch_dmrs_rms_evm_per_symbol_mean
    ):
        r"""Fetches the mean PBCH DMRS RMS EVM for each symbol.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pbch_dmrs_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array which the EVM of each symbol averaged across all the allocated subcarriers allocated
                with PBCH DMRS within symbol.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start symbol index from the frame start in terms of SSB numerology.

            dx (float):
                This parameter returns the width in terms of symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_pbch_dmrs_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, pbch_dmrs_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pdsch8_psk_constellation_trace(self, selector_string, timeout, psk8_constellation):
        r"""Fetches PDSCH 8 PSK constellation trace.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            psk8_constellation (numpy.complex64):
                This parameter returns the PDSCH 8 PSK constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch8_psk_constellation_trace(
                updated_selector_string, timeout, psk8_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch1024_qam_constellation_trace(
        self, selector_string, timeout, qam1024_constellation
    ):
        r"""Fetches the PDSCH 1024 QAM constellation trace.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            qam1024_constellation (numpy.complex64):
                This parameter returns the 1024 QAM constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch1024_qam_constellation_trace(
                updated_selector_string, timeout, qam1024_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch16_qam_constellation_trace(self, selector_string, timeout, qam16_constellation):
        r"""Fetches PDSCH 16 QAM trace.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            qam16_constellation (numpy.complex64):
                This parameter returns the 16 QAM constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch16_qam_constellation_trace(
                updated_selector_string, timeout, qam16_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch256_qam_constellation_trace(
        self, selector_string, timeout, qam256_constellation
    ):
        r"""Fetches PDSCH 256 QAM trace.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            qam256_constellation (numpy.complex64):
                This parameter returns the 256 QAM constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch256_qam_constellation_trace(
                updated_selector_string, timeout, qam256_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch64_qam_constellation_trace(self, selector_string, timeout, qam64_constellation):
        r"""Fetches PDSCH 64 QAM trace.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            qam64_constellation (numpy.complex64):
                This parameter returns the 64 QAM constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch64_qam_constellation_trace(
                updated_selector_string, timeout, qam64_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_data_constellation_trace(
        self, selector_string, timeout, pdsch_data_constellation
    ):
        r"""Fetches the recovered PDSCH data constellation points. The constellation points of different slots in the measurement
        length is concatenated.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" as the selector
        string to read this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and user number.

                Example:

                "subblock0/carrier0/user0"

                "result::r1/subblock0/carrier0/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pdsch_data_constellation (numpy.complex64):
                This parameter returns the PDSCH data constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch_data_constellation_trace(
                updated_selector_string, timeout, pdsch_data_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_demodulated_bits(self, selector_string, timeout, bits):
        r"""Fetches the recovered bits during EVM calculation. The bits of different slots in the measurement length are
        concatenated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            bits (numpy.int8):
                This parameter returns an array of the recovered bits during EVM calculation.

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
            error_code = self._interpreter.modacc_fetch_pdsch_demodulated_bits(
                updated_selector_string, timeout, bits
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_dmrs_constellation_trace(
        self, selector_string, timeout, pdsch_dmrs_constellation
    ):
        r"""Fetches PDSCH DMRS trace. The constellation points of different slots in the measurement length is concatenated.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" as the selector
        string to read this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and user number.

                Example:

                "subblock0/carrier0/user0"

                "result::r1/subblock0/carrier0/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pdsch_dmrs_constellation (numpy.complex64):
                This parameter returns the PDSCH DMRS constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch_dmrs_constellation_trace(
                updated_selector_string, timeout, pdsch_dmrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_ptrs_constellation_trace(
        self, selector_string, timeout, pdsch_ptrs_constellation
    ):
        r"""Fetches PDSCH PTRS trace.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" as the selector
        string to read this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and user number.

                Example:

                "subblock0/carrier0/user0"

                "result::r1/subblock0/carrier0/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pdsch_ptrs_constellation (numpy.complex64):
                This parameter returns the PDSCH PTRS constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch_ptrs_constellation_trace(
                updated_selector_string, timeout, pdsch_ptrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pdsch_qpsk_constellation_trace(self, selector_string, timeout, qpsk_constellation):
        r"""Fetches PDSCH QPSK trace.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            qpsk_constellation (numpy.complex64):
                This parameter returns the QPSK constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pdsch_qpsk_constellation_trace(
                updated_selector_string, timeout, qpsk_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_peak_evm_per_slot_maximum_trace(
        self, selector_string, timeout, peak_evm_per_slot_maximum
    ):
        r"""Fetches the peak value of EVM  for each slot computed across all the symbols and all the allocated subcarriers.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"or "subblock<*n*>/carrier<*k*>/layer<*q*>"
        as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            peak_evm_per_slot_maximum (numpy.float32):
                This parameter returns an array the peak value of EVM  for each slot computed across all the symbols and all the
                allocated subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns the subcarrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_peak_evm_per_slot_maximum_trace(
                updated_selector_string, timeout, peak_evm_per_slot_maximum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_peak_evm_per_subcarrier_maximum_trace(
        self, selector_string, timeout, peak_evm_per_subcarrier_maximum
    ):
        r"""Fetches the peak value of EVM  for each allocated subcarrier computed across all the symbols within the measurement
        length.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            peak_evm_per_subcarrier_maximum (numpy.float32):
                This parameter returns an array the peak value of EVM for each allocated subcarrier computed across all the symbols
                within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns the subcarrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_peak_evm_per_subcarrier_maximum_trace(
                    updated_selector_string, timeout, peak_evm_per_subcarrier_maximum
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_peak_evm_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_per_symbol_maximum
    ):
        r"""Fetches the peak value of EVM  for each symbol computed across all the allocated subcarriers.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            peak_evm_per_symbol_maximum (numpy.float32):
                This parameter returns an array the the peak value of EVM  for each symbol computed across all the allocated
                subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_peak_evm_per_symbol_maximum_trace(
                updated_selector_string, timeout, peak_evm_per_symbol_maximum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pss_constellation_trace(self, selector_string, timeout, pss_constellation):
        r"""Fetches the PSS constellation trace. The constellation points of different slots in the measurement length is
        concatenated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pss_constellation (numpy.complex64):
                This parameter returns the PSS constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pss_constellation_trace(
                updated_selector_string, timeout, pss_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pss_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pss_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the mean PSS RMS EVM of each subcarrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pss_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns an array which the EVM of each allocated subcarrier averaged across all the symbols allocated
                with PSS within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource grid.

            dx (float):
                This parameter returns the subcarrier spacing of SSB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_pss_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, pss_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pss_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pss_rms_evm_per_symbol_mean
    ):
        r"""Fetches the mean PSS RMS EVM of each symbol.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pss_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array which the EVM of each symbol averaged across all the allocated subcarriers allocated
                with PSS within symbol.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start symbol index from the frame start in terms of SSB numerology.

            dx (float):
                This parameter returns the width in terms of symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_pss_rms_evm_per_symbol_mean_trace(
                updated_selector_string, timeout, pss_rms_evm_per_symbol_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pusch_data_constellation_trace(
        self, selector_string, timeout, pusch_data_constellation
    ):
        r"""Fetches PUSCH Data Constellation trace. The constellation points of different slots in the measurement length is
        concatenated.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" or
        "subblock<*n*>/carrier<*k*>/user<*k*>/layer<*q*>" as the selector string to read this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, user number and layer number.

                Example:

                "subblock0/carrier0/user0/layer0"

                "result::r1/subblock0/carrier0/user0/layer0"

                You can use the :py:meth:`build_user_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pusch_data_constellation (numpy.complex64):
                This parameter returns the PUSCH data constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pusch_data_constellation_trace(
                updated_selector_string, timeout, pusch_data_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pusch_demodulated_bits(self, selector_string, timeout, bits):
        r"""Fetches the recovered bits during EVM calculation. The bits of different slots in the measurement length are
        concatenated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            bits (numpy.int8):
                This parameter returns an array of the recovered bits during EVM calculation.

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
            error_code = self._interpreter.modacc_fetch_pusch_demodulated_bits(
                updated_selector_string, timeout, bits
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pusch_dmrs_constellation_trace(
        self, selector_string, timeout, pusch_dmrs_constellation
    ):
        r"""Fetches PUSCH DMRS trace. The constellation points of different slots in the measurement length is concatenated.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" or
        "subblock<*n*>/carrier<*k*>/user<*k*>/layer<*q*>" as the selector string to read this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, user number and layer number.

                Example:

                "subblock0/carrier0/user0/layer0"

                "result::r1/subblock0/carrier0/user0/layer0"

                You can use the :py:meth:`build_user_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pusch_dmrs_constellation (numpy.complex64):
                This parameter returns the PDSCH DMRS constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pusch_dmrs_constellation_trace(
                updated_selector_string, timeout, pusch_dmrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_pusch_ptrs_constellation_trace(
        self, selector_string, timeout, pusch_ptrs_constellation
    ):
        r"""Fetches PUSCH PTRS trace. The constellation points of different slots in the measurement length is concatenated.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" or
        "subblock<*n*>/carrier<*k*>/user<*k*>/layer<*q*>" as the selector string to read this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, user number and layer number.

                Example:

                "subblock0/carrier0/user0/layer0"

                "result::r1/subblock0/carrier0/user0/layer0"

                You can use the :py:meth:`build_user_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pusch_ptrs_constellation (numpy.complex64):
                This parameter returns the PUSCH PTRS constellation trace.

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
            error_code = self._interpreter.modacc_fetch_pusch_ptrs_constellation_trace(
                updated_selector_string, timeout, pusch_ptrs_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_rms_evm_per_slot_mean_trace(self, selector_string, timeout, rms_evm_per_slot_mean):
        r"""Fetches the EVM of each slot averaged across all the symbols and all the allocated subcarriers within each slot.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            rms_evm_per_slot_mean (numpy.float32):
                This parameter returns an array the EVM of each slot averaged across all the symbols and all the allocated subcarriers
                within each slot.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns the subcarrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_rms_evm_per_slot_mean_trace(
                updated_selector_string, timeout, rms_evm_per_slot_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the EVM of each allocated subcarrier averaged across all the symbols within the measurement length.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns an array the EVM of each allocated subcarrier averaged across all the symbols within the
                measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns the subcarrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_rms_evm_per_subcarrier_mean_trace(
                updated_selector_string, timeout, rms_evm_per_subcarrier_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_per_symbol_mean
    ):
        r"""Fetches the EVM on each symbol within the measurement length averaged across all the allocated subcarriers.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array the EVM on each symbol within the measurement length averaged across all the allocated
                subcarriers.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_rms_evm_per_symbol_mean_trace(
                updated_selector_string, timeout, rms_evm_per_symbol_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_rms_evm_high_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_high_per_symbol_mean
    ):
        r"""Fetches the EVM per symbol trace for all confgured slots. The EVM is obtained by using FFT window position Delta_C+W/2.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            rms_evm_high_per_symbol_mean (numpy.float32):
                This parameter returns an array of the EVM per symbol for all confgured slots.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_rms_evm_high_per_symbol_mean_trace(
                updated_selector_string, timeout, rms_evm_high_per_symbol_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_peak_evm_high_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_high_per_symbol_maximum
    ):
        r"""Fetches the peak EVM per symbol trace for all confgured slots. The EVM is obtained by using FFT window position
        Delta_C+W/2.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            peak_evm_high_per_symbol_maximum (numpy.float32):
                This parameter returns an array of the peak EVM per symbol for all confgured slots.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_peak_evm_high_per_symbol_maximum_trace(
                    updated_selector_string, timeout, peak_evm_high_per_symbol_maximum
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_rms_evm_low_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_low_per_symbol_mean
    ):
        r"""Fetches the EVM per symbol trace for all confgured slots. The EVM is obtained by using FFT window position Delta_C-W/2.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            rms_evm_low_per_symbol_mean (numpy.float32):
                This parameter returns an array of the EVM per symbol for all confgured slots.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_rms_evm_low_per_symbol_mean_trace(
                updated_selector_string, timeout, rms_evm_low_per_symbol_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_peak_evm_low_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_low_per_symbol_maximum
    ):
        r"""Fetches the peak EVM per symbol trace for all confgured slots. The EVM is obtained by using FFT window position
        Delta_C-W/2.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            peak_evm_low_per_symbol_maximum (numpy.float32):
                This parameter returns an array of the peak EVM per symbol for all confgured slots.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol position corresponding to the
                :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns 1 as the value.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_peak_evm_low_per_symbol_maximum_trace(
                    updated_selector_string, timeout, peak_evm_low_per_symbol_maximum
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_transient_period_locations_trace(
        self, selector_string, timeout, transient_period_locations
    ):
        r"""Returns the symbol indices that were identified to have a transient period.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        The length of the trace is equal to the number of symbols within the measurement length.

        The trace returns a 1 for the symbol index that was identified to have a transient period; otherwise returns a
        0.

        The trace is intended to be used as additional context information for the following traces:
        <ul>
        <li>RMS EVM per Symbol Mean Trace</li>
        <li>RMS EVM-High per Symbol Mean Trace</li>
        <li>RMS EVM-Low per Symbol Mean Trace</li>
        </ul>

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            transient_period_locations (numpy.float32):
                This parameter returns a 1 for the symbol index that was identified to have a transient period; otherwise returns a 0.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start symbol index from the frame start.

            dx (float):
                This parameter returns the width in terms of symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_transient_period_locations_trace(
                updated_selector_string, timeout, transient_period_locations
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_pusch_phase_offset_trace(self, selector_string, timeout, pusch_phase_offset):
        r"""Returns the phase offset for the slots with respect to the reference slot.

        Use "user<*k*>" or "carrier<*l*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*l*>/user<*k*>" or
        "subblock<*n*>/carrier<*k*>/user<*k*>/layer<*q*>" as the selector string to read this method.

        The length of the trace is equal to the number of slots within the measurement length.

        For each burst of continuously allocated slots, the first active slot in the burst is used as the reference
        slot.

        The reference slot is reset at frame boundary.

        The phase offset is calculated for slots that are contiguous to the reference slot and have overlapping
        subcarrier allocations. For all other slots, NaN is provided.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, user number and layer number.

                Example:

                "subblock0/carrier0/user0/layer0"

                "result::r1/subblock0/carrier0/user0/layer0"

                You can use the :py:meth:`build_user_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            pusch_phase_offset (numpy.float32):
                This parameter returns an array of the maximum value across averaging counts of the phase error per slot for all slots
                within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the index of the first active slot.

            dx (float):
                This parameter returns the increment value. This is always set to one slot.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_pusch_phase_offset_trace(
                updated_selector_string, timeout, pusch_phase_offset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_frequency_error_per_slot_maximum_trace(
        self, selector_string, timeout, frequency_error_per_slot_maximum
    ):
        r"""Fetches an array of the maximum value across averaging counts of the frequency error per slot for all slots within the
        measurement length. This value is expressed in Hz.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read this result.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            frequency_error_per_slot_maximum (numpy.float32):
                This parameter returns an array of the maximum value across averaging counts of the frequency error per slot for all
                slots within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the index of the first active slot.

            dx (float):
                This parameter returns the increment value. This is always set to one slot.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_frequency_error_per_slot_maximum_trace(
                    updated_selector_string, timeout, frequency_error_per_slot_maximum
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_spectral_flatness_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        r"""Returns the spectral flatness, upper mask, and lower mask traces. Spectral flatness is the magnitude of equalizer
        coefficients at each allocated subcarrier. Lower and upper masks are derived from section 6.5.2.4.5 of *3GPP TS
        38.521-1* specification.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
        "subblock<*n*>/carrier<*k*>/layer<*q*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number and layer number.

                Example:

                "subblock0/carrier0/layer0"

                "result::r1/subblock0/carrier0/layer0"

                You can use the :py:meth:`build_carrier_string` and :py:meth:`build_layer_string` methods to build the selector
                string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            spectral_flatness (numpy.float32):
                This parameter returns an array of the spectral flatness values at each allocated subcarrier.

            spectral_flatness_lower_mask (numpy.float32):
                This parameter returns an array of the spectral flatness values at each allocated subcarrier.

            spectral_flatness_upper_mask (numpy.float32):
                This parameter returns an array of the spectral flatness values at each allocated subcarrier.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource block.

            dx (float):
                This parameter returns the subcarrier spacing.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_spectral_flatness_trace(
                updated_selector_string,
                timeout,
                spectral_flatness,
                spectral_flatness_lower_mask,
                spectral_flatness_upper_mask,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_sss_constellation_trace(self, selector_string, timeout, sss_constellation):
        r"""Fetches the SSS constellation trace. The constellation points of different slots in the measurement length is
        concatenated.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            sss_constellation (numpy.complex64):
                This parameter returns the SSS constellation trace.

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
            error_code = self._interpreter.modacc_fetch_sss_constellation_trace(
                updated_selector_string, timeout, sss_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_sss_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, sss_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the mean SSS RMS EVM of each subcarrier.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            sss_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns an array which the EVM of each allocated subcarrier averaged across all the symbols allocated
                with SSS within the measurement length.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource grid.

            dx (float):
                This parameter returns the subcarrier spacing of SSB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_sss_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, sss_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_sss_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, sss_rms_evm_per_symbol_mean
    ):
        r"""Fetches the mean SSS RMS EVM of each symbol.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            sss_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array which the EVM of each symbol averaged across all the allocated subcarriers allocated
                with SSS within symbol.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start symbol index from the frame start in terms of SSB numerology.

            dx (float):
                This parameter returns the width in terms of symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_sss_rms_evm_per_symbol_mean_trace(
                updated_selector_string, timeout, sss_rms_evm_per_symbol_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_subblock_in_band_emission_trace(
        self,
        selector_string,
        timeout,
        subblock_in_band_emission,
        subblock_in_band_emission_mask,
        subblock_in_band_emission_rb_indices,
    ):
        r"""Returns the in-band emission trace and limit trace for the the subblocks aggregated bandwidth. In-band emission is
        measured as the ratio of the power in non-allocated resource blocks to the power in the allocated resource blocks
        averaged over the measurement interval. The IBE for various regions (general, carrier leakage, and I/Q Image) are
        obtained and concatenated to form a composite trace and the limits are defined in section 6.4A.2.2.2  of *3GPP
        38.101-1*, and section 6.4A.2.3 of *3GPP 38.101-2*. The trace is not returned when there is clustered PUSCH allocation,
        or when there is more than one active carrier, or when there is full allocation of resource blocks, or when carriers
        with different sub-carrier spacing are aggregated, or when the number of carriers is greater than 2.

        Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number and chain number.

                Example:

                "subblock0/chain0"

                "result::r1/subblock0/chain0"

                You can use the :py:meth:`build_subblock_string` and :py:meth:`build_chain_string` methods to build the
                selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            subblock_in_band_emission (numpy.float64):
                This parameter returns the array of subblock in-band emission measurement trace.

            subblock_in_band_emission_mask (numpy.float64):
                This parameter returns the array of subblock in-band emission mask trace.

            subblock_in_band_emission_rb_indices (numpy.float64):
                This parameter returns the array of resource block indices for the subblock in-band emission trace. It can have non
                integer values depending upon the spacing between carriers.

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
            error_code = self._interpreter.modacc_fetch_subblock_in_band_emission_trace(
                updated_selector_string,
                timeout,
                subblock_in_band_emission,
                subblock_in_band_emission_mask,
                subblock_in_band_emission_rb_indices,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
    ):
        r"""Fetches mean value of IQ Gain Imbalance.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            iq_gain_imbalance_per_subcarrier_mean (numpy.float32):
                This parameter returns the mean value of IQ Gain Imbalance. This value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource grid.

            dx (float):
                This parameter returns the sampling duration of the analyzed signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_iq_quadrature_error_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
    ):
        r"""Fetches the mean value of IQ Quadrature Error.

        Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the selector string to read results
        from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, and carrier number.

                Example:

                "subblock0/carrier0"

                "result::r1/subblock0/carrier0"

                You can use the :py:meth:`build_carrier_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            iq_quadrature_error_per_subcarrier_mean (numpy.float32):
                This parameter returns the mean value of IQ Quadrature Error. This value is expressed in degrees.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start point of the of the resource grid.

            dx (float):
                This parameter returns the sampling duration of the analyzed signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.modacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
