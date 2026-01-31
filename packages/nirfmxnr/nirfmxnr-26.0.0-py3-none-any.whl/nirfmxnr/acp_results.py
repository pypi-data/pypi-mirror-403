"""Provides methods to fetch and read the Acp measurement results."""

import functools

import nirfmxnr.acp_component_carrier_results as component_carrier
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


class AcpResults(object):
    """Provides methods to fetch and read the Acp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Acp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter
        self.component_carrier = component_carrier.AcpComponentCarrierResults(signal_obj)  # type: ignore

    @_raise_if_disposed
    def get_total_aggregated_power(self, selector_string):
        r"""Gets the total power of all the subblocks. The power in each subblock is the sum of powers of all the frequency bins
        over the integration bandwidth of the subblocks. This value includes the power in the inter-carrier gaps within a
        subblock, but it does not include the power within the subblock gaps.

        The carrier power is reported in dBm when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
        Pwr Units attribute to **dBm/Hz**.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the total power of all the subblocks. The power in each subblock is the sum of powers of all the frequency bins
                over the integration bandwidth of the subblocks. This value includes the power in the inter-carrier gaps within a
                subblock, but it does not include the power within the subblock gaps.

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
                attributes.AttributeID.ACP_RESULTS_TOTAL_AGGREGATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_subblock_power(self, selector_string):
        r"""Gets the sum of powers of all the frequency bins over the integration bandwidth of the subblock. The carrier power
        is reported in dBm when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**,
        and in dBm/Hz when you set the ACP Pwr Units attribute to **dBm/Hz**.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the sum of powers of all the frequency bins over the integration bandwidth of the subblock. The carrier power
                is reported in dBm when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**,
                and in dBm/Hz when you set the ACP Pwr Units attribute to **dBm/Hz**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_RESULTS_SUBBLOCK_POWER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_absolute_power(self, selector_string):
        r"""Gets the lower (negative) offset channel power. The carrier power is reported in dBm when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
        Pwr Units attribute to **dBm/Hz**.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the lower (negative) offset channel power. The carrier power is reported in dBm when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
                Pwr Units attribute to **dBm/Hz**.

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
                attributes.AttributeID.ACP_RESULTS_LOWER_OFFSET_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_relative_power(self, selector_string):
        r"""Gets the power in lower (negative) offset channel relative to the total aggregated power. This value is expressed in
        dB.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power in lower (negative) offset channel relative to the total aggregated power. This value is expressed in
                dB.

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
                attributes.AttributeID.ACP_RESULTS_LOWER_OFFSET_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_absolute_power(self, selector_string):
        r"""Gets the upper (positive) offset channel power. The carrier power is reported in dBm when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
        Pwr Units attribute to **dBm/Hz**.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the upper (positive) offset channel power. The carrier power is reported in dBm when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
                Pwr Units attribute to **dBm/Hz**.

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
                attributes.AttributeID.ACP_RESULTS_UPPER_OFFSET_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_relative_power(self, selector_string):
        r"""Gets the power in the upper (positive) offset channel relative to the total aggregated power. This value is
        expressed in dB.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power in the upper (positive) offset channel relative to the total aggregated power. This value is
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
                updated_selector_string,
                attributes.AttributeID.ACP_RESULTS_UPPER_OFFSET_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_absolute_powers_trace(
        self, selector_string, timeout, trace_index, absolute_powers_trace
    ):
        r"""Fetches the absolute powers trace for ACP measurement.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            trace_index (int):
                Specifies the index of the trace to fetch. The **traceIndex** can range from 0 to (Number of carriers + 2*Number of
                offsets).

            absolute_powers_trace (numpy.float32):
                This parameter returns an array the power measured in each channel. The carrier power is reported in dBm when you set
                the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the
                ACP Pwr Units attribute to **dBm/Hz**.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency of the channel. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.acp_fetch_absolute_powers_trace(
                updated_selector_string, timeout, trace_index, absolute_powers_trace
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_offset_measurement_array(self, selector_string, timeout):
        r"""Returns an array of the absolute and relative power of the lower and upper offset channel.

        The relative power is relative to the subblock power. The order of the offsets in the result array is UTRA (1,
        2, â€¦k) and NR (1, 2, â€¦n) for Uplink, and EUTRA (1, 2, â€¦m) and NR (1, 2, â€¦n) for Downlink, where k, m, and n are
        the number of UTRA offsets, number of EUTRA offsets, and number of NR offsets, respectively.

        Use "subblock<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (lower_relative_power, upper_relative_power, lower_absolute_power, upper_absolute_power, error_code):

            lower_relative_power (float):
                This parameter returns an array of the power in lower (negative) offset channel relative to the total aggregated power.
                This value is expressed in dB.

            upper_relative_power (float):
                This parameter returns an array of the power in the upper (positive) offset channel relative to the total aggregated
                power. This value is expressed in dB.

            lower_absolute_power (float):
                This parameter returns an array of the lower offset channel power. The carrier power is reported in dBm when you set
                the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the
                ACP Pwr Units attribute to **dBm/Hz**.

            upper_absolute_power (float):
                This parameter returns an array of the upper offset channel power. The carrier power is reported in dBm when you set
                the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the
                ACP Pwr Units attribute to **dBm/Hz**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            (
                lower_relative_power,
                upper_relative_power,
                lower_absolute_power,
                upper_absolute_power,
                error_code,
            ) = self._interpreter.acp_fetch_offset_measurement_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            lower_relative_power,
            upper_relative_power,
            lower_absolute_power,
            upper_absolute_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_offset_measurement(self, selector_string, timeout):
        r"""Returns the absolute and relative power of the lower and upper offset channel. The relative power is relative to
        subblock power.

        Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the selector string to read results from
        this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, subblock number, carrier number, and offset number.

                Example:

                "subblock0/offset0"

                "result::r1/subblock0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (lower_relative_power, upper_relative_power, lower_absolute_power, upper_absolute_power, error_code):

            lower_relative_power (float):
                This parameter returns the power in lower (negative) offset channel relative to the total aggregated power. This value
                is expressed in dB.

            upper_relative_power (float):
                This parameter returns the power in the upper (positive) offset channel relative to the total aggregated power. This
                value is expressed in dB.

            lower_absolute_power (float):
                This parameter returns the lower offset channel power. The carrier power is reported in dBm when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
                Pwr Units attribute to **dBm/Hz**.

            upper_absolute_power (float):
                This parameter returns the upper offset channel power. The carrier power is reported in dBm when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
                Pwr Units attribute to **dBm/Hz**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            (
                lower_relative_power,
                upper_relative_power,
                lower_absolute_power,
                upper_absolute_power,
                error_code,
            ) = self._interpreter.acp_fetch_offset_measurement(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            lower_relative_power,
            upper_relative_power,
            lower_absolute_power,
            upper_absolute_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_relative_powers_trace(
        self, selector_string, timeout, trace_index, relative_powers_trace
    ):
        r"""Fetches the relative powers trace for ACP measurement.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            trace_index (int):
                Specifies the index of the trace to fetch. The **traceIndex** can range from 0 to (Number of carriers + 2*Number of
                offsets).

            relative_powers_trace (numpy.float32):
                This parameter returns an array of the relative power measured in each channel relative to total aggregated power. This
                value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency of the channel. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.acp_fetch_relative_powers_trace(
                updated_selector_string, timeout, trace_index, relative_powers_trace
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum):
        r"""Fetches the spectrum used for ACP measurements.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

            spectrum (numpy.float32):
                This parameter returns the array of averaged power measured at each frequency bin. The carrier power is reported in dBm
                when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when
                you set the ACP Pwr Units attribute to **dBm/Hz**.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency of the channel. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.acp_fetch_spectrum(
                updated_selector_string, timeout, spectrum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_total_aggregated_power(self, selector_string, timeout):
        r"""Returns the sum of powers in all the subblocks.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (total_aggregated_power, error_code):

            total_aggregated_power (float):
                This parameter returns the total power of all the subblocks. The power in each subblock is the sum of powers of all the
                frequency bins over the integration bandwidth of the subblocks. This value includes the power in the inter-carrier gaps
                within a subblock, but it does not include the power within the subblock gaps.
                The carrier power is reported in dBm when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS`
                attribute to **dBm**, and in dBm/Hz when you set the ACP Pwr Units attribute to **dBm/Hz**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            total_aggregated_power, error_code = self._interpreter.acp_fetch_total_aggregated_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return total_aggregated_power, error_code

    @_raise_if_disposed
    def fetch_subblock_measurement(self, selector_string, timeout):
        r"""Fetches the power, integration bandwidth, and center frequency of the subblock.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and subblock number.

                Example:

                "subblock0"

                "result::r1/subblock0"

                You can use the :py:meth:`build_subblock_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (subblock_power, integration_bandwidth, frequency, error_code):

            subblock_power (float):
                This parameter returns the sum of powers of all the frequency bins over the integration bandwidth of the subblock. This
                includes the power in inter-carrier gaps within a subblock. The carrier power is reported in dBm when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
                Pwr Units attribute to **dBm/Hz**.

            integration_bandwidth (float):
                This parameter returns the integration bandwidth used in calculating the power of the subblock. Integration bandwidth
                is the span from left edge of the leftmost carrier to the right edge of the rightmost carrier within a subblock. This
                value is expressed in Hz.

            frequency (float):
                This parameter returns the absolute center frequency of the subblock. This value is the center of the subblock
                integration bandwidth. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            subblock_power, integration_bandwidth, frequency, error_code = (
                self._interpreter.acp_fetch_subblock_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return subblock_power, integration_bandwidth, frequency, error_code
