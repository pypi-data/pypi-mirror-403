"""Defines a root class which is used to identify and control NR signal configuration."""

import functools
import math

import nirfmxinstr
import nirfmxnr.acp as acp
import nirfmxnr.attributes as attributes
import nirfmxnr.chp as chp
import nirfmxnr.component_carrier as component_carrier
import nirfmxnr.enums as enums
import nirfmxnr.errors as errors
import nirfmxnr.internal._helper as _helper
import nirfmxnr.modacc as modacc
import nirfmxnr.obw as obw
import nirfmxnr.pvt as pvt
import nirfmxnr.sem as sem
import nirfmxnr.txp as txp
from nirfmxnr.internal._helper import SignalConfiguration
from nirfmxnr.internal._library_interpreter import LibraryInterpreter


class _NRSignalConfiguration:
    """Contains static methods to create and delete NR signal."""

    @staticmethod
    def get_nr_signal_configuration(instr_session, signal_name="", cloning=False):
        updated_signal_name = signal_name
        if signal_name:
            updated_signal_name = _helper.validate_and_remove_signal_qualifier(
                signal_name, "signal_name"
            )
            _helper.validate_signal_not_empty(updated_signal_name, "signal_name")
        return _NRSignalConfiguration.init(instr_session, updated_signal_name, cloning)  # type: ignore

    @staticmethod
    def init(instr_session, signal_name, cloning):
        with instr_session._signal_lock:
            if signal_name.lower() == NR._default_signal_name_user_visible.lower():
                signal_name = NR._default_signal_name

            existing_signal = instr_session._signal_manager.find_signal_configuration(
                NR._signal_configuration_type, signal_name
            )
            if existing_signal is None:
                signal_configuration = NR(instr_session, signal_name, cloning)  # type: ignore
                instr_session._signal_manager.add_signal_configuration(signal_configuration)
            else:
                signal_configuration = existing_signal
                # Checking if signal exists in C layer
                if signal_configuration._interpreter.check_if_current_signal_exists() is False:
                    if not signal_configuration.signal_configuration_name.lower():
                        instr_session._interpreter.create_default_signal_configuration(
                            NR._default_signal_name_user_visible,
                            int(math.log(nirfmxinstr.Personalities.NR.value, 2.0)) + 1,
                        )
                    else:
                        signal_configuration._interpreter.create_signal_configuration(signal_name)

            return signal_configuration

    @staticmethod
    def remove_signal_configuration(instr_session, signal_configuration):
        with instr_session._signal_lock:
            instr_session._signal_manager.remove_signal_configuration(signal_configuration)


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        signal = xs[0]  # parameter 0 is 'self' which is the signal object
        if signal.is_disposed:
            raise Exception("Cannot access a disposed NR signal configuration")
        return f(*xs, **kws)

    return aux


class _NRBase(SignalConfiguration):
    """Defines a base class for NR."""

    _default_signal_name = ""
    _default_signal_name_user_visible = "default@NR"
    _signal_configuration_type = "<'nirfmxnr.nr.NR'>"

    def __init__(self, session, signal_name="", cloning=False):
        self.is_disposed = False
        self._rfmxinstrsession = session
        self._rfmxinstrsession_interpreter = session._interpreter
        self.signal_configuration_name = signal_name
        self.signal_configuration_type = type(self)  # type: ignore
        self._signal_configuration_mode = "Signal"
        if session._is_remote_session:
            import nirfmxnr.internal._grpc_stub_interpreter as _grpc_stub_interpreter

            interpreter = _grpc_stub_interpreter.GrpcStubInterpreter(session._grpc_options, session, self)  # type: ignore
        else:
            interpreter = LibraryInterpreter("windows-1251", session, self)  # type: ignore

        self._interpreter = interpreter
        self._interpreter.set_session_handle(self._rfmxinstrsession_interpreter._vi)  # type: ignore
        self._session_function_lock = _helper.SessionFunctionLock()

        # Measurements object
        self.modacc = modacc.ModAcc(self)  # type: ignore
        self.acp = acp.Acp(self)  # type: ignore
        self.txp = txp.Txp(self)  # type: ignore
        self.pvt = pvt.Pvt(self)  # type: ignore
        self.obw = obw.Obw(self)  # type: ignore
        self.sem = sem.Sem(self)  # type: ignore
        self.chp = chp.Chp(self)  # type: ignore
        self.component_carrier = component_carrier.ComponentCarrier(self)  # type: ignore

        if not signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._default_signal_name_user_visible
                )
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.NR.value):
                self._rfmxinstrsession_interpreter.create_default_signal_configuration(
                    self._default_signal_name_user_visible,
                    int(math.log(nirfmxinstr.Personalities.NR.value, 2.0)) + 1,
                )
        elif signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(signal_name)
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.NR.value):
                self._interpreter.create_signal_configuration(signal_name)  # type: ignore

    def __enter__(self):
        """Enters the context of the NR signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the NR signal configuration."""
        self.dispose()  # type: ignore
        pass

    def dispose(self):
        r"""Deletes the signal configuration if it is not the default signal configuration
        and clears any trace of the current signal configuration, if any.

        .. note::
            You can call this function safely more than once, even if the signal is already deleted.
        """
        if not self.is_disposed:
            if self.signal_configuration_name == self._default_signal_name:
                self.is_disposed = True
                return
            else:
                _ = self._delete_signal_configuration(True)  # type: ignore
                self.is_disposed = True

    @_raise_if_disposed
    def delete_signal_configuration(self):
        r"""Deletes the current instance of a signal.

        Returns:
            error_code:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        error_code = self._delete_signal_configuration(False)  # type: ignore
        return error_code

    def _delete_signal_configuration(self, ignore_driver_error):
        error_code = 0
        try:
            if not self.is_disposed:
                self._session_function_lock.enter_write_lock()
                error_code = self._interpreter.delete_signal_configuration(ignore_driver_error)  # type: ignore
                _NRSignalConfiguration.remove_signal_configuration(self._rfmxinstrsession, self)  # type: ignore
                self.is_disposed = True
        finally:
            self._session_function_lock.exit_write_lock()

        return error_code

    @_raise_if_disposed
    def get_warning(self):
        r"""Retrieves and then clears the warning information for the session.

        Returns:
            Tuple (warning_code, warning_message):

            warning_code (int):
                Contains the latest warning code.

            warning_message (string):
                Contains the latest warning description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            warning_code, warning_message = self._interpreter.get_error()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return warning_code, warning_message

    @_raise_if_disposed
    def get_error_string(self, error_code):
        r"""Gets the description of a driver error code.

        Args:
            error_code (int):
                Specifies an error or warning code.

        Returns:
            string:
                Contains the error description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_message = self._interpreter.get_error_string(error_code)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_message

    @_raise_if_disposed
    def reset_attribute(self, selector_string, attribute_id):
        r"""Resets the attribute to its default value.

        Args:
            selector_string (string):
                Specifies the selector string for the property being reset.

            attribute_id (PropertyId):
                Specifies an attribute identifier.

        Returns:
            int:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attribute_id = (
                attribute_id.value if type(attribute_id) is attributes.AttributeID else attribute_id
            )
            error_code = self._interpreter.reset_attribute(  # type: ignore
                updated_selector_string, attribute_id
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_selected_ports(self, selector_string):
        r"""Gets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        On a MIMO session, this attribute specifies one of the initialized devices. Use
        "port::<deviceName>/<channelNumber>" as the format for the selected port. To perform a MIMO measurement, you must
        configure the selected ports attribute for the configured number of receive chains.

        For PXIe-5830/5831/5832 devices on a MIMO session, the selected port includes the instrument port in the format
        "port::<deviceName>/<channelNumber>/<instrPort>".

        Example:

        port::myrfsa1/0/if1

        You can use the :py:meth:`build_port_string` method to build the selected port.

        Use "chain<n>" as the selector string to configure or read this attribute. You can use the
        :py:meth:`build_chain_string` method to build the selector string.

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_selected_ports(self, selector_string, value):
        r"""Sets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        On a MIMO session, this attribute specifies one of the initialized devices. Use
        "port::<deviceName>/<channelNumber>" as the format for the selected port. To perform a MIMO measurement, you must
        configure the selected ports attribute for the configured number of receive chains.

        For PXIe-5830/5831/5832 devices on a MIMO session, the selected port includes the instrument port in the format
        "port::<deviceName>/<channelNumber>/<instrPort>".

        Example:

        port::myrfsa1/0/if1

        You can use the :py:meth:`build_port_string` method to build the selected port.

        Use "chain<n>" as the selector string to configure or read this attribute. You can use the
        :py:meth:`build_chain_string` method to build the selector string.

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_center_frequency(self, selector_string):
        r"""Gets the center frequency of the acquired RF signal. This value is expressed in Hz. The signal analyzer tunes to
        this frequency.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the center frequency of the acquired RF signal. This value is expressed in Hz. The signal analyzer tunes to
                this frequency.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_center_frequency(self, selector_string, value):
        r"""Sets the center frequency of the acquired RF signal. This value is expressed in Hz. The signal analyzer tunes to
        this frequency.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the center frequency of the acquired RF signal. This value is expressed in Hz. The signal analyzer tunes to
                this frequency.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level(self, selector_string):
        r"""Gets the reference level which represents the maximum expected power of the RF input signal. This value is
        expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
                expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level(self, selector_string, value):
        r"""Sets the reference level which represents the maximum expected power of the RF input signal. This value is
        expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
                expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_external_attenuation(self, selector_string):
        r"""Gets the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
        device in the *NI RF Vector Signal Analyzers Help*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
                device in the *NI RF Vector Signal Analyzers Help*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_external_attenuation(self, selector_string, value):
        r"""Sets the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
        device in the *NI RF Vector Signal Analyzers Help*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
                device in the *NI RF Vector Signal Analyzers Help*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level_headroom(self, selector_string):
        r"""Gets the margin RFmx adds to the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute. The margin
        avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668R, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute. The margin
                avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level_headroom(self, selector_string, value):
        r"""Sets the margin RFmx adds to the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute. The margin
        avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668R, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute. The margin
                avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_type(self, selector_string):
        r"""Gets the type of trigger to be used for signal acquisition.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **None**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No Reference Trigger is configured.                                                                                      |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
        |                   | using the Digital Edge Source attribute.                                                                                 |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
        |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | The Reference Trigger is not asserted until a software trigger occurs.                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerType):
                Specifies the type of trigger to be used for signal acquisition.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value
            )
            attr_val = enums.TriggerType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_type(self, selector_string, value):
        r"""Sets the type of trigger to be used for signal acquisition.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **None**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No Reference Trigger is configured.                                                                                      |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
        |                   | using the Digital Edge Source attribute.                                                                                 |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
        |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | The Reference Trigger is not asserted until a software trigger occurs.                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerType, int):
                Specifies the type of trigger to be used for signal acquisition.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_source(self, selector_string):
        r"""Gets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_source(self, selector_string, value):
        r"""Sets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_edge(self, selector_string):
        r"""Gets the active edge for the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DigitalEdgeTriggerEdge):
                Specifies the active edge for the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value
            )
            attr_val = enums.DigitalEdgeTriggerEdge(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_edge(self, selector_string, value):
        r"""Sets the active edge for the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DigitalEdgeTriggerEdge, int):
                Specifies the active edge for the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DigitalEdgeTriggerEdge else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_source(self, selector_string):
        r"""Gets the channel from which the device monitors the trigger.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the channel from which the device monitors the trigger.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_source(self, selector_string, value):
        r"""Sets the channel from which the device monitors the trigger.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the channel from which the device monitors the trigger.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level(self, selector_string):
        r"""Gets the power level at which the device triggers. This value is expressed in dB when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative**; and in dBm when
        you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
        the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
        used only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power level at which the device triggers. This value is expressed in dB when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative**; and in dBm when
                you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
                the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
                used only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level(self, selector_string, value):
        r"""Sets the power level at which the device triggers. This value is expressed in dB when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative**; and in dBm when
        you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
        the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
        used only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power level at which the device triggers. This value is expressed in dB when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative**; and in dBm when
                you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
                the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
                used only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level_type(self, selector_string):
        r"""Gets the reference for the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
        IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerLevelType):
                Specifies the reference for the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
                IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
            )
            attr_val = enums.IQPowerEdgeTriggerLevelType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level_type(self, selector_string, value):
        r"""Sets the reference for the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
        IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerLevelType, int):
                Specifies the reference for the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
                IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerLevelType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_slope(self, selector_string):
        r"""Gets whether the device asserts the trigger when the signal power is rising or when it is falling. The device
        asserts the trigger when the signal power exceeds the specified level with the slope you specify.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerSlope):
                Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value
            )
            attr_val = enums.IQPowerEdgeTriggerSlope(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_slope(self, selector_string, value):
        r"""Sets whether the device asserts the trigger when the signal power is rising or when it is falling. The device
        asserts the trigger when the signal power exceeds the specified level with the slope you specify.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerSlope, int):
                Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerSlope else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_delay(self, selector_string):
        r"""Gets the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
        acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

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
                Specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
                acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_delay(self, selector_string, value):
        r"""Sets the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
        acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
                acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_mode(self, selector_string):
        r"""Gets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                 |
        +==============+=============================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
        +--------------+---------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
        +--------------+---------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerMinimumQuietTimeMode):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
            )
            attr_val = enums.TriggerMinimumQuietTimeMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_mode(self, selector_string, value):
        r"""Sets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                 |
        +==============+=============================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
        +--------------+---------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
        +--------------+---------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerMinimumQuietTimeMode, int):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerMinimumQuietTimeMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_duration(self, selector_string):
        r"""Gets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds. If you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising Slope**, the signal is
        quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling Slope**, the signal is quiet
        above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds. If you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising Slope**, the signal is
                quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling Slope**, the signal is quiet
                above the trigger level.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_duration(self, selector_string, value):
        r"""Sets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds. If you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising Slope**, the signal is
        quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling Slope**, the signal is quiet
        above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds. If you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising Slope**, the signal is
                quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling Slope**, the signal is quiet
                above the trigger level.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_link_direction(self, selector_string):
        r"""Gets the link direction of the received signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Uplink**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Downlink (0) | NR measurement uses 3GPP NR downlink specification to measure the received signal. |
        +--------------+------------------------------------------------------------------------------------+
        | Uplink (1)   | NR measurement uses 3GPP NR uplink specification to measure the received signal.   |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LinkDirection):
                Specifies the link direction of the received signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LINK_DIRECTION.value
            )
            attr_val = enums.LinkDirection(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_link_direction(self, selector_string, value):
        r"""Sets the link direction of the received signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Uplink**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | Downlink (0) | NR measurement uses 3GPP NR downlink specification to measure the received signal. |
        +--------------+------------------------------------------------------------------------------------+
        | Uplink (1)   | NR measurement uses 3GPP NR uplink specification to measure the received signal.   |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LinkDirection, int):
                Specifies the link direction of the received signal.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.LinkDirection else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LINK_DIRECTION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_gnodeb_category(self, selector_string):
        r"""Gets the downlink gNodeB (Base Station) category. Refer to the *3GPP 38.104* specification for more information
        about gNodeB category.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Wide Area Base Station - Category A**.

        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Name (Value)                                    | Description                                                                    |
        +=================================================+================================================================================+
        | Wide Area Base Station - Category A (0)         | Specifies that the gNodeB type is Wide Area Base Station - Category A.         |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option1 (1) | Specifies that the gNodeB type is Wide Area Base Station - Category B Option1. |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option2 (2) | Specifies that the gNodeB type is Wide Area Base Station - Category B Option2. |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Local Area Base Station (3)                     | Specifies that the gNodeB type is Local Area Base Station.                     |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Medium Range Base Station (5)                   | Specifies that the gNodeB type is Medium Range Base Station.                   |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | FR2 Category A (6)                              | Specifies that the gNodeB type is FR2 Category A.                              |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | FR2 Category B (7)                              | Specifies that the gNodeB type is FR2 Category B.                              |
        +-------------------------------------------------+--------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.gNodeBCategory):
                Specifies the downlink gNodeB (Base Station) category. Refer to the *3GPP 38.104* specification for more information
                about gNodeB category.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.GNODEB_CATEGORY.value
            )
            attr_val = enums.gNodeBCategory(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_gnodeb_category(self, selector_string, value):
        r"""Sets the downlink gNodeB (Base Station) category. Refer to the *3GPP 38.104* specification for more information
        about gNodeB category.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Wide Area Base Station - Category A**.

        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Name (Value)                                    | Description                                                                    |
        +=================================================+================================================================================+
        | Wide Area Base Station - Category A (0)         | Specifies that the gNodeB type is Wide Area Base Station - Category A.         |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option1 (1) | Specifies that the gNodeB type is Wide Area Base Station - Category B Option1. |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Wide Area Base Station - Category B Option2 (2) | Specifies that the gNodeB type is Wide Area Base Station - Category B Option2. |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Local Area Base Station (3)                     | Specifies that the gNodeB type is Local Area Base Station.                     |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | Medium Range Base Station (5)                   | Specifies that the gNodeB type is Medium Range Base Station.                   |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | FR2 Category A (6)                              | Specifies that the gNodeB type is FR2 Category A.                              |
        +-------------------------------------------------+--------------------------------------------------------------------------------+
        | FR2 Category B (7)                              | Specifies that the gNodeB type is FR2 Category B.                              |
        +-------------------------------------------------+--------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.gNodeBCategory, int):
                Specifies the downlink gNodeB (Base Station) category. Refer to the *3GPP 38.104* specification for more information
                about gNodeB category.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.gNodeBCategory else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.GNODEB_CATEGORY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_gnodeb_type(self, selector_string):
        r"""Gets the downlink gNodeB (Base Station) type. Refer to the *3GPP 38.104* specification for more information about
        gNodeB Type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Type 1-C**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | Type 1-C (0) | Type 1-C NR base station operating at FR1 and conducted requirements apply.      |
        +--------------+----------------------------------------------------------------------------------+
        | Type 1-H (1) | Type 1-H base station operating at FR1 and conducted and OTA requirements apply. |
        +--------------+----------------------------------------------------------------------------------+
        | Type 1-O (2) | Type 1-O base station operating at FR1 and OTA requirements apply.               |
        +--------------+----------------------------------------------------------------------------------+
        | Type 2-O (3) | Type 2-O base station operating at FR2 and OTA requirements apply.               |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.gNodeBType):
                Specifies the downlink gNodeB (Base Station) type. Refer to the *3GPP 38.104* specification for more information about
                gNodeB Type.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.GNODEB_TYPE.value
            )
            attr_val = enums.gNodeBType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_gnodeb_type(self, selector_string, value):
        r"""Sets the downlink gNodeB (Base Station) type. Refer to the *3GPP 38.104* specification for more information about
        gNodeB Type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Type 1-C**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | Type 1-C (0) | Type 1-C NR base station operating at FR1 and conducted requirements apply.      |
        +--------------+----------------------------------------------------------------------------------+
        | Type 1-H (1) | Type 1-H base station operating at FR1 and conducted and OTA requirements apply. |
        +--------------+----------------------------------------------------------------------------------+
        | Type 1-O (2) | Type 1-O base station operating at FR1 and OTA requirements apply.               |
        +--------------+----------------------------------------------------------------------------------+
        | Type 2-O (3) | Type 2-O base station operating at FR2 and OTA requirements apply.               |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.gNodeBType, int):
                Specifies the downlink gNodeB (Base Station) type. Refer to the *3GPP 38.104* specification for more information about
                gNodeB Type.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.gNodeBType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.GNODEB_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_satellite_access_node_class(self, selector_string):
        r"""Gets the downlink SAN (Satellite Access Node) class representing the satellite constellation as specified in
        section 6.6.4 of *3GPP 38.108* specification.

        This attribute impacts the spectral emission mask for downlink.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **GEO (0)**.

        +--------------+--------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                            |
        +==============+========================================================================================================+
        | GEO (0)      | Specifies the downlink SAN (Satellite Access Node) class corresponding to GEO satellite constellation. |
        +--------------+--------------------------------------------------------------------------------------------------------+
        | LEO (1)      | Specifies the downlink SAN (Satellite Access Node) class corresponding to LEO satellite constellation. |
        +--------------+--------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SatelliteAccessNodeClass):
                Specifies the downlink SAN (Satellite Access Node) class representing the satellite constellation as specified in
                section 6.6.4 of *3GPP 38.108* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.SATELLITE_ACCESS_NODE_CLASS.value
            )
            attr_val = enums.SatelliteAccessNodeClass(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_satellite_access_node_class(self, selector_string, value):
        r"""Sets the downlink SAN (Satellite Access Node) class representing the satellite constellation as specified in
        section 6.6.4 of *3GPP 38.108* specification.

        This attribute impacts the spectral emission mask for downlink.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **GEO (0)**.

        +--------------+--------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                            |
        +==============+========================================================================================================+
        | GEO (0)      | Specifies the downlink SAN (Satellite Access Node) class corresponding to GEO satellite constellation. |
        +--------------+--------------------------------------------------------------------------------------------------------+
        | LEO (1)      | Specifies the downlink SAN (Satellite Access Node) class corresponding to LEO satellite constellation. |
        +--------------+--------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.SatelliteAccessNodeClass, int):
                Specifies the downlink SAN (Satellite Access Node) class representing the satellite constellation as specified in
                section 6.6.4 of *3GPP 38.108* specification.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.SatelliteAccessNodeClass else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.SATELLITE_ACCESS_NODE_CLASS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transmit_antenna_to_analyze(self, selector_string):
        r"""Gets the physical antenna that is currently connected to the analyzer.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the physical antenna that is currently connected to the analyzer.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transmit_antenna_to_analyze(self, selector_string, value):
        r"""Sets the physical antenna that is currently connected to the analyzer.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the physical antenna that is currently connected to the analyzer.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_receive_chains(self, selector_string):
        r"""Gets the number of receive chains.

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
                Specifies the number of receive chains.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_RECEIVE_CHAINS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_receive_chains(self, selector_string, value):
        r"""Sets the number of receive chains.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of receive chains.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.NUMBER_OF_RECEIVE_CHAINS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_class(self, selector_string):
        r"""Gets the power class for the UE as specified in section 6.2 of *3GPP 38.101-1/2/3* specification.

        This attribute impacts the spectral flatness mask for uplink.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **3**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the power class for the UE as specified in section 6.2 of *3GPP 38.101-1/2/3* specification.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.POWER_CLASS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_class(self, selector_string, value):
        r"""Sets the power class for the UE as specified in section 6.2 of *3GPP 38.101-1/2/3* specification.

        This attribute impacts the spectral flatness mask for uplink.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **3**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the power class for the UE as specified in section 6.2 of *3GPP 38.101-1/2/3* specification.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.POWER_CLASS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_piby2bpsk_power_boost_enabled(self, selector_string):
        r"""Gets the power boost for PI/2 BPSK signal when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` attribute to **Range 1**. This attribute is valid only for
        uplink direction.

        For PI/2 BPSK modulation, if this attribute is set to True,
        :py:attr:`~nirfmxnr.attributes.AttributeID.POWER_CLASS` attribute to
        **3**,:py:attr:`~nirfmxnr.attributes.AttributeID.BAND` attribute to 40, 41, 77, 78, or 79, and the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_SLOT_ALLOCATION` attribute is set such that, at most 40% of the radio
        frame is active, then the EVM Equalizer spectral flatness mask specified in section 6.4.2.4.1 of 3GPP 38.101-1 is used.
        Otherwise the EVM Equalizer spectral flatness mask specified in section 6.4.2.4 of 3GPP 38.101-1 is used.

        When you set the Frequency Range attribute to **Range 2-1** or **Range 2-2**, the measurement ignores the
        PIby2BPSK Pwr Boost Enabled attribute. In this case, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SPECTRAL_FLATNESS_CONDITION` attribute to **Normal**, the equalizer
        spectral flatness mask as specified in section 6.4.2.5 of *3GPP TS 38.101-2* is used for the PI/2 BPSK signal.
        Otherwise, the equalizer spectral flatness mask as specified in section 6.4.2.4 of *3GPP 38.101-2* is used.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------+
        | Name (Value) | Description                                          |
        +==============+======================================================+
        | False (0)    | Power boost for PI/2 BPSK modulation is not enabled. |
        +--------------+------------------------------------------------------+
        | True (1)     | Power boost for PI/2 BPSK modulation is enabled.     |
        +--------------+------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PiBy2BpskPowerBoostEnabled):
                Specifies the power boost for PI/2 BPSK signal when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` attribute to **Range 1**. This attribute is valid only for
                uplink direction.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PIBY2BPSK_POWER_BOOST_ENABLED.value
            )
            attr_val = enums.PiBy2BpskPowerBoostEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_piby2bpsk_power_boost_enabled(self, selector_string, value):
        r"""Sets the power boost for PI/2 BPSK signal when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` attribute to **Range 1**. This attribute is valid only for
        uplink direction.

        For PI/2 BPSK modulation, if this attribute is set to True,
        :py:attr:`~nirfmxnr.attributes.AttributeID.POWER_CLASS` attribute to
        **3**,:py:attr:`~nirfmxnr.attributes.AttributeID.BAND` attribute to 40, 41, 77, 78, or 79, and the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_SLOT_ALLOCATION` attribute is set such that, at most 40% of the radio
        frame is active, then the EVM Equalizer spectral flatness mask specified in section 6.4.2.4.1 of 3GPP 38.101-1 is used.
        Otherwise the EVM Equalizer spectral flatness mask specified in section 6.4.2.4 of 3GPP 38.101-1 is used.

        When you set the Frequency Range attribute to **Range 2-1** or **Range 2-2**, the measurement ignores the
        PIby2BPSK Pwr Boost Enabled attribute. In this case, when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SPECTRAL_FLATNESS_CONDITION` attribute to **Normal**, the equalizer
        spectral flatness mask as specified in section 6.4.2.5 of *3GPP TS 38.101-2* is used for the PI/2 BPSK signal.
        Otherwise, the equalizer spectral flatness mask as specified in section 6.4.2.4 of *3GPP 38.101-2* is used.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------+
        | Name (Value) | Description                                          |
        +==============+======================================================+
        | False (0)    | Power boost for PI/2 BPSK modulation is not enabled. |
        +--------------+------------------------------------------------------+
        | True (1)     | Power boost for PI/2 BPSK modulation is enabled.     |
        +--------------+------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PiBy2BpskPowerBoostEnabled, int):
                Specifies the power boost for PI/2 BPSK signal when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.FREQUENCY_RANGE` attribute to **Range 1**. This attribute is valid only for
                uplink direction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.PiBy2BpskPowerBoostEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.PIBY2BPSK_POWER_BOOST_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_resource_block_detection_enabled(self, selector_string):
        r"""Gets whether the values of modulation type, number of resource block clusters, resource block offsets, and number
        of resource blocks are auto-detected by the measurement or configured by you.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink**, enabling
        Auto RB Detection Enabled attribute detects the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes.

        When you set the Link Direction attribute to **Downlink**, enabling Auto RB Detection Enabled attribute detects
        the PDSCH Mod Type, PDSCH Num RB Clusters, PDSCH RB Offset, and PDSCH Num RBs attributes.

        When this attribute is enabled, the modulation type, number of resource block clusters, resource block offsets,
        and number of resource blocks of the received signal are assumed to be the constant in all active symbols of the
        received signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The values of modulation type, number of resource block clusters, resource block offsets, and number of resource blocks  |
        |              | that you specify are used for the measurement.                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The values of modulation type, number of resource block clusters, resource block offsets, and number of resource blocks  |
        |              | are auto-detected by the measurement.                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoResourceBlockDetectionEnabled):
                Specifies whether the values of modulation type, number of resource block clusters, resource block offsets, and number
                of resource blocks are auto-detected by the measurement or configured by you.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED.value,
            )
            attr_val = enums.AutoResourceBlockDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_resource_block_detection_enabled(self, selector_string, value):
        r"""Sets whether the values of modulation type, number of resource block clusters, resource block offsets, and number
        of resource blocks are auto-detected by the measurement or configured by you.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to **Uplink**, enabling
        Auto RB Detection Enabled attribute detects the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MODULATION_TYPE`,
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS`,
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_RESOURCE_BLOCK_OFFSET`, and
        :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_NUMBER_OF_RESOURCE_BLOCKS` attributes.

        When you set the Link Direction attribute to **Downlink**, enabling Auto RB Detection Enabled attribute detects
        the PDSCH Mod Type, PDSCH Num RB Clusters, PDSCH RB Offset, and PDSCH Num RBs attributes.

        When this attribute is enabled, the modulation type, number of resource block clusters, resource block offsets,
        and number of resource blocks of the received signal are assumed to be the constant in all active symbols of the
        received signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The values of modulation type, number of resource block clusters, resource block offsets, and number of resource blocks  |
        |              | that you specify are used for the measurement.                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The values of modulation type, number of resource block clusters, resource block offsets, and number of resource blocks  |
        |              | are auto-detected by the measurement.                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoResourceBlockDetectionEnabled, int):
                Specifies whether the values of modulation type, number of resource block clusters, resource block offsets, and number
                of resource blocks are auto-detected by the measurement or configured by you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.AutoResourceBlockDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_cell_id_detection_enabled(self, selector_string):
        r"""Gets whether to enable the autodetection of the cell ID.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**,
        autodetection of  the Cell ID is not possible if the signal measured does not contain SSB with PSS/SSS, or if the PDSCH
        does not include enough allocated Resource Blocks.

        When you set the Link Direction attribute to **Uplink**, autodetection of the Cell ID is not possible if the
        PUSCH :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute is set to True, or if the
        PUSCH does not include enough allocated Resource Blocks.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | User-configured Cell ID is used.             |
        +--------------+----------------------------------------------+
        | True (1)     | Measurement tries to autodetect the Cell ID. |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoCellIDDetectionEnabled):
                Specifies whether to enable the autodetection of the cell ID.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.AUTO_CELL_ID_DETECTION_ENABLED.value
            )
            attr_val = enums.AutoCellIDDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_cell_id_detection_enabled(self, selector_string, value):
        r"""Sets whether to enable the autodetection of the cell ID.

        When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.LINK_DIRECTION` attribute to **Downlink**,
        autodetection of  the Cell ID is not possible if the signal measured does not contain SSB with PSS/SSS, or if the PDSCH
        does not include enough allocated Resource Blocks.

        When you set the Link Direction attribute to **Uplink**, autodetection of the Cell ID is not possible if the
        PUSCH :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute is set to True, or if the
        PUSCH does not include enough allocated Resource Blocks.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | User-configured Cell ID is used.             |
        +--------------+----------------------------------------------+
        | True (1)     | Measurement tries to autodetect the Cell ID. |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoCellIDDetectionEnabled, int):
                Specifies whether to enable the autodetection of the cell ID.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.AutoCellIDDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_CELL_ID_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_channel_configuration_mode(self, selector_string):
        r"""Gets the downlink channel configuration mode.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Test Model**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | User Defined (1) | The user sets all signals and channels manually.                                                                         |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Test Model (2)   | A Test Model needs to be selected in theDownlink Test Model attribute to configure all the signals and channels          |
        |                  | automatically, according to the section 4.9.2 of 3GPP 38.141-1/2 specification.                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkChannelConfigurationMode):
                Specifies the downlink channel configuration mode.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE.value,
            )
            attr_val = enums.DownlinkChannelConfigurationMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_channel_configuration_mode(self, selector_string, value):
        r"""Sets the downlink channel configuration mode.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Test Model**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | User Defined (1) | The user sets all signals and channels manually.                                                                         |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Test Model (2)   | A Test Model needs to be selected in theDownlink Test Model attribute to configure all the signals and channels          |
        |                  | automatically, according to the section 4.9.2 of 3GPP 38.141-1/2 specification.                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkChannelConfigurationMode, int):
                Specifies the downlink channel configuration mode.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DownlinkChannelConfigurationMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_CHANNEL_CONFIGURATION_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_increment_cell_id_enabled(self, selector_string):
        r"""Gets whether the cell ID of component carrier is auto calculated and configured by the measurement or configured
        by the user.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                             |
        +==============+=========================================================================================================+
        | False (0)    | The measurement uses the user-configured cell IDs.                                                      |
        +--------------+---------------------------------------------------------------------------------------------------------+
        | True (1)     | The Cell ID of each CC is auto calculated as specified in section 4.9.2.3 of 3GPP 38.141 specification. |
        +--------------+---------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AutoIncrementCellIDEnabled):
                Specifies whether the cell ID of component carrier is auto calculated and configured by the measurement or configured
                by the user.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.AUTO_INCREMENT_CELL_ID_ENABLED.value
            )
            attr_val = enums.AutoIncrementCellIDEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_increment_cell_id_enabled(self, selector_string, value):
        r"""Sets whether the cell ID of component carrier is auto calculated and configured by the measurement or configured
        by the user.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                             |
        +==============+=========================================================================================================+
        | False (0)    | The measurement uses the user-configured cell IDs.                                                      |
        +--------------+---------------------------------------------------------------------------------------------------------+
        | True (1)     | The Cell ID of each CC is auto calculated as specified in section 4.9.2.3 of 3GPP 38.141 specification. |
        +--------------+---------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AutoIncrementCellIDEnabled, int):
                Specifies whether the cell ID of component carrier is auto calculated and configured by the measurement or configured
                by the user.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.AutoIncrementCellIDEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_INCREMENT_CELL_ID_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_downlink_test_model_cell_id_mode(self, selector_string):
        r"""Gets whether the cell ID of downlink test model component carriers is auto calculated and configured by the
        measurement or configured by the user.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                             |
        +==============+=========================================================================================================+
        | Auto (0)     | Cell ID of each CC is auto calculated as specified in section 4.9.2.3 of the 3GPP 38.141 specification. |
        +--------------+---------------------------------------------------------------------------------------------------------+
        | Manual (1)   | The measurement uses the user-configured cell IDs.                                                      |
        +--------------+---------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DownlinkTestModelCellIDMode):
                Specifies whether the cell ID of downlink test model component carriers is auto calculated and configured by the
                measurement or configured by the user.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_TEST_MODEL_CELL_ID_MODE.value,
            )
            attr_val = enums.DownlinkTestModelCellIDMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_downlink_test_model_cell_id_mode(self, selector_string, value):
        r"""Sets whether the cell ID of downlink test model component carriers is auto calculated and configured by the
        measurement or configured by the user.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                             |
        +==============+=========================================================================================================+
        | Auto (0)     | Cell ID of each CC is auto calculated as specified in section 4.9.2.3 of the 3GPP 38.141 specification. |
        +--------------+---------------------------------------------------------------------------------------------------------+
        | Manual (1)   | The measurement uses the user-configured cell IDs.                                                      |
        +--------------+---------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DownlinkTestModelCellIDMode, int):
                Specifies whether the cell ID of downlink test model component carriers is auto calculated and configured by the
                measurement or configured by the user.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DownlinkTestModelCellIDMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DOWNLINK_TEST_MODEL_CELL_ID_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_subblocks(self, selector_string):
        r"""Gets the number of subblocks configured in intraband non-contiguous carrier aggregation scenarios.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1. Set this attribute to 1 for single carrier and intra-band contiguous carrier
        aggregation.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of subblocks configured in intraband non-contiguous carrier aggregation scenarios.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_SUBBLOCKS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_subblocks(self, selector_string, value):
        r"""Sets the number of subblocks configured in intraband non-contiguous carrier aggregation scenarios.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1. Set this attribute to 1 for single carrier and intra-band contiguous carrier
        aggregation.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of subblocks configured in intraband non-contiguous carrier aggregation scenarios.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_SUBBLOCKS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_frequency(self, selector_string):
        r"""Gets the offset of the subblock from the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the offset of the subblock from the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.SUBBLOCK_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subblock_frequency(self, selector_string, value):
        r"""Sets the offset of the subblock from the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the offset of the subblock from the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.SUBBLOCK_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_transmit_lo_frequency(self, selector_string):
        r"""Gets the frequency of the transmitters local oscillator. This value is expressed in Hz. The frequency is defined
        per subblock and relative to the respective subblock center frequency.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the frequency of the transmitters local oscillator. This value is expressed in Hz. The frequency is defined
                per subblock and relative to the respective subblock center frequency.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subblock_transmit_lo_frequency(self, selector_string, value):
        r"""Sets the frequency of the transmitters local oscillator. This value is expressed in Hz. The frequency is defined
        per subblock and relative to the respective subblock center frequency.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the frequency of the transmitters local oscillator. This value is expressed in Hz. The frequency is defined
                per subblock and relative to the respective subblock center frequency.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phase_compensation_frequency(self, selector_string):
        r"""Gets the frequency used for phase compensation of the signal when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PHASE_COMPENSATION` attribute to **User Defined**. This value is expressed
        in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the frequency used for phase compensation of the signal when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PHASE_COMPENSATION` attribute to **User Defined**. This value is expressed
                in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.PHASE_COMPENSATION_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phase_compensation_frequency(self, selector_string, value):
        r"""Sets the frequency used for phase compensation of the signal when you set the
        :py:attr:`~nirfmxnr.attributes.AttributeID.PHASE_COMPENSATION` attribute to **User Defined**. This value is expressed
        in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the frequency used for phase compensation of the signal when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.PHASE_COMPENSATION` attribute to **User Defined**. This value is expressed
                in Hz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.PHASE_COMPENSATION_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency_range(self, selector_string):
        r"""Gets whether to use channel bandwidth and subcarrier spacing configuration supported in Frequency Range 1 (sub
        6GHz), Frequency Range 2-1 (between 24.25GHz and 52.6GHz) or Frequency Range 2-2 (between 52.6GHz and 71GHz).

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Range 1**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | Range 1 (0)   | Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 1 (sub 6    |
        |               | GHz).                                                                                                                    |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Range 2-1 (1) | Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 2-1         |
        |               | (between 24.25 GHz and 52.6 GHz).                                                                                        |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Range 2-2 (2) | Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 2-2         |
        |               | (between 52.6 GHz and 71 GHz).                                                                                           |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.FrequencyRange):
                Specifies whether to use channel bandwidth and subcarrier spacing configuration supported in Frequency Range 1 (sub
                6GHz), Frequency Range 2-1 (between 24.25GHz and 52.6GHz) or Frequency Range 2-2 (between 52.6GHz and 71GHz).

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.FREQUENCY_RANGE.value
            )
            attr_val = enums.FrequencyRange(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency_range(self, selector_string, value):
        r"""Sets whether to use channel bandwidth and subcarrier spacing configuration supported in Frequency Range 1 (sub
        6GHz), Frequency Range 2-1 (between 24.25GHz and 52.6GHz) or Frequency Range 2-2 (between 52.6GHz and 71GHz).

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Range 1**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | Range 1 (0)   | Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 1 (sub 6    |
        |               | GHz).                                                                                                                    |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Range 2-1 (1) | Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 2-1         |
        |               | (between 24.25 GHz and 52.6 GHz).                                                                                        |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Range 2-2 (2) | Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 2-2         |
        |               | (between 52.6 GHz and 71 GHz).                                                                                           |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.FrequencyRange, int):
                Specifies whether to use channel bandwidth and subcarrier spacing configuration supported in Frequency Range 1 (sub
                6GHz), Frequency Range 2-1 (between 24.25GHz and 52.6GHz) or Frequency Range 2-2 (between 52.6GHz and 71GHz).

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.FrequencyRange else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.FREQUENCY_RANGE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_band(self, selector_string):
        r"""Gets the evolved universal terrestrial radio access (E-UTRA) or NR operating frequency band of a subblock as
        specified in section 5.2 of the *3GPP 38.101-1/2/3* specification. Band determines the spectral flatness mask and
        spectral emission mask.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 78.

        Valid values for frequency range 1 are 1, 2, 3, 5, 7, 8, 12, 13, 14, 18, 20, 24, 25, 26, 28, 29, 30, 31, 34,
        38, 39, 40, 41, 46, 47, 48, 50, 51, 53, 54, 65, 66, 67, 68, 70, 71, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
        86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 104, 105, 106, 109, 110, 247, 248, 250, 251,
        252, 253, 254, 255, and 256.

        Valid values for frequency range 2-1 are 257, 258, 259, 260, 261, and 262.

        Valid values for frequency range 2-2 are 263.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the evolved universal terrestrial radio access (E-UTRA) or NR operating frequency band of a subblock as
                specified in section 5.2 of the *3GPP 38.101-1/2/3* specification. Band determines the spectral flatness mask and
                spectral emission mask.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.BAND.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_band(self, selector_string, value):
        r"""Sets the evolved universal terrestrial radio access (E-UTRA) or NR operating frequency band of a subblock as
        specified in section 5.2 of the *3GPP 38.101-1/2/3* specification. Band determines the spectral flatness mask and
        spectral emission mask.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 78.

        Valid values for frequency range 1 are 1, 2, 3, 5, 7, 8, 12, 13, 14, 18, 20, 24, 25, 26, 28, 29, 30, 31, 34,
        38, 39, 40, 41, 46, 47, 48, 50, 51, 53, 54, 65, 66, 67, 68, 70, 71, 72, 74, 75, 76, 77, 78, 79, 80, 81, 82, 83, 84, 85,
        86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 101, 102, 104, 105, 106, 109, 110, 247, 248, 250, 251,
        252, 253, 254, 255, and 256.

        Valid values for frequency range 2-1 are 257, 258, 259, 260, 261, and 262.

        Valid values for frequency range 2-2 are 263.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the evolved universal terrestrial radio access (E-UTRA) or NR operating frequency band of a subblock as
                specified in section 5.2 of the *3GPP 38.101-1/2/3* specification. Band determines the spectral flatness mask and
                spectral emission mask.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.BAND.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_subblock_endc_nominal_spacing_adjustment(self, selector_string):
        r"""Gets the adjustment of the center frequency for adjacent E-UTRA and NR Channels in case of nominal spacing. The
        value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the adjustment of the center frequency for adjacent E-UTRA and NR Channels in case of nominal spacing. The
                value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.SUBBLOCK_ENDC_NOMINAL_SPACING_ADJUSTMENT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_subblock_endc_nominal_spacing_adjustment(self, selector_string, value):
        r"""Sets the adjustment of the center frequency for adjacent E-UTRA and NR Channels in case of nominal spacing. The
        value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **0**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the adjustment of the center frequency for adjacent E-UTRA and NR Channels in case of nominal spacing. The
                value is expressed in Hz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.SUBBLOCK_ENDC_NOMINAL_SPACING_ADJUSTMENT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_raster(self, selector_string):
        r"""Gets the subblock channel raster which is used for computing nominal spacing between aggregated carriers as
        specified in section 5.4A.1 of *3GPP 38.101-1/2* specification and section 5.4.1.2 of *3GPP TS 38.104* specification.
        The value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **15 kHz**.

        Valid values for frequency range 1 are **15 kHz** and **100kHz**.

        Valid values for frequency range 2-1 is **60 kHz**.

        Valid values for frequency range 2-2 are **120 kHz**, **480 kHz**, and **960 kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the subblock channel raster which is used for computing nominal spacing between aggregated carriers as
                specified in section 5.4A.1 of *3GPP 38.101-1/2* specification and section 5.4.1.2 of *3GPP TS 38.104* specification.
                The value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_RASTER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_raster(self, selector_string, value):
        r"""Sets the subblock channel raster which is used for computing nominal spacing between aggregated carriers as
        specified in section 5.4A.1 of *3GPP 38.101-1/2* specification and section 5.4.1.2 of *3GPP TS 38.104* specification.
        The value is expressed in Hz.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **15 kHz**.

        Valid values for frequency range 1 are **15 kHz** and **100kHz**.

        Valid values for frequency range 2-1 is **60 kHz**.

        Valid values for frequency range 2-2 are **120 kHz**, **480 kHz**, and **960 kHz**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the subblock channel raster which is used for computing nominal spacing between aggregated carriers as
                specified in section 5.4A.1 of *3GPP 38.101-1/2* specification and section 5.4.1.2 of *3GPP TS 38.104* specification.
                The value is expressed in Hz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_RASTER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_component_carrier_spacing_type(self, selector_string):
        r"""Gets the spacing between adjacent component carriers (CCs) within a subblock.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Nominal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Nominal (0)  | Calculates the frequency spacing between component carriers as defined in section 5.4A.1 in the 3GPP 38.101-1/2          |
        |              | specification and section 5.4.1.2 in the 3GPP TS 38.104 specification and sets the CC Freq attribute.                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | User (2)     | The component carrier frequency that you configure in the CC Freq attribute is used.                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ComponentCarrierSpacingType):
                Specifies the spacing between adjacent component carriers (CCs) within a subblock.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE.value
            )
            attr_val = enums.ComponentCarrierSpacingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_component_carrier_spacing_type(self, selector_string, value):
        r"""Sets the spacing between adjacent component carriers (CCs) within a subblock.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **Nominal**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Nominal (0)  | Calculates the frequency spacing between component carriers as defined in section 5.4A.1 in the 3GPP 38.101-1/2          |
        |              | specification and section 5.4.1.2 in the 3GPP TS 38.104 specification and sets the CC Freq attribute.                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | User (2)     | The component carrier frequency that you configure in the CC Freq attribute is used.                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ComponentCarrierSpacingType, int):
                Specifies the spacing between adjacent component carriers (CCs) within a subblock.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.ComponentCarrierSpacingType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_component_carrier_at_center_frequency(self, selector_string):
        r"""Gets the index of the component carrier having its center at the user-configured center frequency. The measurement
        uses this attribute along with :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
        calculate the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`. This attribute is
        ignored if you set the CC Spacing Type attribute to **User**.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Valid values are -1, 0, 1 ... *n* - 1, inclusive, where *n* is the number of component carriers in the
        subblock.

        The default value is -1. If the value is -1, the component carrier frequency values are calculated such that
        the center of the subcarrier(with maximum subcarrier spacing for a frequency range), which is closest to the center of
        the aggregated channel bandwidth, lies at the center frequency.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the index of the component carrier having its center at the user-configured center frequency. The measurement
                uses this attribute along with :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
                calculate the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`. This attribute is
                ignored if you set the CC Spacing Type attribute to **User**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.COMPONENT_CARRIER_AT_CENTER_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_component_carrier_at_center_frequency(self, selector_string, value):
        r"""Sets the index of the component carrier having its center at the user-configured center frequency. The measurement
        uses this attribute along with :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
        calculate the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`. This attribute is
        ignored if you set the CC Spacing Type attribute to **User**.

        Use "subblock<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        Valid values are -1, 0, 1 ... *n* - 1, inclusive, where *n* is the number of component carriers in the
        subblock.

        The default value is -1. If the value is -1, the component carrier frequency values are calculated such that
        the center of the subcarrier(with maximum subcarrier spacing for a frequency range), which is closest to the center of
        the aggregated channel bandwidth, lies at the center frequency.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the index of the component carrier having its center at the user-configured center frequency. The measurement
                uses this attribute along with :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to
                calculate the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY`. This attribute is
                ignored if you set the CC Spacing Type attribute to **User**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.COMPONENT_CARRIER_AT_CENTER_FREQUENCY.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_acquisition_bandwidth_optimization_enabled(self, selector_string):
        r"""Gets whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
        oscillator (LO) to be placed at different position than you configured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition    |
        |              | center frequency is the same as the value of the Center Frequency that you configure.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span       |
        |              | needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving     |
        |              | the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement       |
        |              | sensitive to it should have this attribute disabled.                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcquisitionBandwidthOptimizationEnabled):
                Specifies whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
                oscillator (LO) to be placed at different position than you configured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED.value,
            )
            attr_val = enums.AcquisitionBandwidthOptimizationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_acquisition_bandwidth_optimization_enabled(self, selector_string, value):
        r"""Sets whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
        oscillator (LO) to be placed at different position than you configured.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition    |
        |              | center frequency is the same as the value of the Center Frequency that you configure.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span       |
        |              | needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving     |
        |              | the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement       |
        |              | sensitive to it should have this attribute disabled.                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcquisitionBandwidthOptimizationEnabled, int):
                Specifies whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
                oscillator (LO) to be placed at different position than you configured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = (
                value.value
                if type(value) is enums.AcquisitionBandwidthOptimizationEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_transmitter_architecture(self, selector_string):
        r"""Gets the RF architecture at the transmitter, whether each component carriers have a separate LO or one common LO
        for the entire subblock.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **LO per Subblock**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | LO per Component Carrier (0) | The Carrier IQ Origin Offset Mean (dBc) and the In-Band Emission Margin (dB) are calculated as the LO per Component      |
        |                              | Carrier, the Subblock IQ Origin Offset Mean (dBc) and the Subblock In-Band Emission Margin (dB) will not be returned.    |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | LO per Subblock (1)          | The Subblock IQ Origin Offset Mean (dBc) and the Subblock In-Band Emission Margin (dB) are calculated as the LO per      |
        |                              | Subblock, the Carrier IQ Origin Offset Mean (dBc), and the In-Band Emission Margin (dB) will be NaN. In the case of a    |
        |                              | single carrier, the measurement returns the same value of IQ Origin Offset and In-Band Emission Margin for both          |
        |                              | components carrier and subblock results.                                                                                 |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TransmitterArchitecture):
                Specifies the RF architecture at the transmitter, whether each component carriers have a separate LO or one common LO
                for the entire subblock.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRANSMITTER_ARCHITECTURE.value
            )
            attr_val = enums.TransmitterArchitecture(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_transmitter_architecture(self, selector_string, value):
        r"""Sets the RF architecture at the transmitter, whether each component carriers have a separate LO or one common LO
        for the entire subblock.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **LO per Subblock**.

        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                                              |
        +==============================+==========================================================================================================================+
        | LO per Component Carrier (0) | The Carrier IQ Origin Offset Mean (dBc) and the In-Band Emission Margin (dB) are calculated as the LO per Component      |
        |                              | Carrier, the Subblock IQ Origin Offset Mean (dBc) and the Subblock In-Band Emission Margin (dB) will not be returned.    |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | LO per Subblock (1)          | The Subblock IQ Origin Offset Mean (dBc) and the Subblock In-Band Emission Margin (dB) are calculated as the LO per      |
        |                              | Subblock, the Carrier IQ Origin Offset Mean (dBc), and the In-Band Emission Margin (dB) will be NaN. In the case of a    |
        |                              | single carrier, the measurement returns the same value of IQ Origin Offset and In-Band Emission Margin for both          |
        |                              | components carrier and subblock results.                                                                                 |
        +------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TransmitterArchitecture, int):
                Specifies the RF architecture at the transmitter, whether each component carriers have a separate LO or one common LO
                for the entire subblock.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TransmitterArchitecture else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRANSMITTER_ARCHITECTURE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phase_compensation(self, selector_string):
        r"""Gets whether phase compensation is disabled, auto-set by the measurement or set by the you.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **Disabled**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Disabled (0)     | No phase compensation is applied on the signal.                                                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)         | Phase compensation is applied on the signal using value of Center Frequency attribute as the phase compensation          |
        |                  | frequency.                                                                                                               |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (2) | Phase compensation is applied on the signal using value of Ph Comp Freq attribute.                                       |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PhaseCompensation):
                Specifies whether phase compensation is disabled, auto-set by the measurement or set by the you.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PHASE_COMPENSATION.value
            )
            attr_val = enums.PhaseCompensation(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phase_compensation(self, selector_string, value):
        r"""Sets whether phase compensation is disabled, auto-set by the measurement or set by the you.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **Disabled**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Disabled (0)     | No phase compensation is applied on the signal.                                                                          |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)         | Phase compensation is applied on the signal using value of Center Frequency attribute as the phase compensation          |
        |                  | frequency.                                                                                                               |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | User Defined (2) | Phase compensation is applied on the signal using value of Ph Comp Freq attribute.                                       |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PhaseCompensation, int):
                Specifies whether phase compensation is disabled, auto-set by the measurement or set by the you.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.PhaseCompensation else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PHASE_COMPENSATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_grid_alignment_mode(self, selector_string):
        r"""Gets whether to align the bandwidthparts and the SSB in a component carrier to a reference resource grid
        automatically or manually.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | The subcarrier spacing of the reference resource grid and the grid start of each bandwidthpart is user specified.        |
        |              | Center of subcarrier 0 in common resource block 0 of the reference resource grid is considered as Reference Point A.     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The subcarrier spacing of the reference resource grid is determined by the largest subcarrier spacing among the          |
        |              | configured bandwidthparts and the SSB. The grid start of each bandwidthpart and the SSB is computed by minimizing k0 to  |
        |              | {0, +6} subcarriers.                                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ReferenceGridAlignmentMode):
                Specifies whether to align the bandwidthparts and the SSB in a component carrier to a reference resource grid
                automatically or manually.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE.value
            )
            attr_val = enums.ReferenceGridAlignmentMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_grid_alignment_mode(self, selector_string, value):
        r"""Sets whether to align the bandwidthparts and the SSB in a component carrier to a reference resource grid
        automatically or manually.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | The subcarrier spacing of the reference resource grid and the grid start of each bandwidthpart is user specified.        |
        |              | Center of subcarrier 0 in common resource block 0 of the reference resource grid is considered as Reference Point A.     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The subcarrier spacing of the reference resource grid is determined by the largest subcarrier spacing among the          |
        |              | configured bandwidthparts and the SSB. The grid start of each bandwidthpart and the SSB is computed by minimizing k0 to  |
        |              | {0, +6} subcarriers.                                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ReferenceGridAlignmentMode, int):
                Specifies whether to align the bandwidthparts and the SSB in a component carrier to a reference resource grid
                automatically or manually.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.ReferenceGridAlignmentMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_grid_size_mode(self, selector_string):
        r"""Gets whether to set the grid size of all BWPs and SSB in a component carrier automatically or manually.

        When you set this attribute to **Auto**, the grid size is set equal to the maximum transmission bandwidth
        specified in the 3GPP specification.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **Auto**.

        +--------------+-------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                           |
        +==============+=======================================================================================================+
        | Manual (0)   | The grid size is user specified.                                                                      |
        +--------------+-------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The grid size is set equal to the maximum transmission bandwidth specified by the 3GPP specification. |
        +--------------+-------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.GridSizeMode):
                Specifies whether to set the grid size of all BWPs and SSB in a component carrier automatically or manually.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.GRID_SIZE_MODE.value
            )
            attr_val = enums.GridSizeMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_grid_size_mode(self, selector_string, value):
        r"""Sets whether to set the grid size of all BWPs and SSB in a component carrier automatically or manually.

        When you set this attribute to **Auto**, the grid size is set equal to the maximum transmission bandwidth
        specified in the 3GPP specification.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for the named signals.

        The default value is **Auto**.

        +--------------+-------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                           |
        +==============+=======================================================================================================+
        | Manual (0)   | The grid size is user specified.                                                                      |
        +--------------+-------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The grid size is set equal to the maximum transmission bandwidth specified by the 3GPP specification. |
        +--------------+-------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.GridSizeMode, int):
                Specifies whether to set the grid size of all BWPs and SSB in a component carrier automatically or manually.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.GridSizeMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.GRID_SIZE_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_limited_configuration_change(self, selector_string):
        r"""Gets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies and/or
        power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
        value other than **Disabled**, the RFmx driver will use an optimized code path and skip some checks. Because RFmx skips
        some checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in
        the `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to precompute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFInstr or personality attributes while
        testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration is locked after the first Commit of the named signal configuration. Any configuration change        |
        |                                        | thereafter either in RFmxInstr attributes or personality attributes will not be considered by subsequent RFmx Commits    |
        |                                        | or Initiates of this signal.                                                                                             |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency and external attenuation, is locked after first Commit of the named    |
        |                                        | signal configuration. Thereafter, only the Center Frequency and External Attenuation attribute value changes will be     |
        |                                        | considered by subsequent driver Commits or Initiates of this signal.                                                     |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.    |
        |                                        | Thereafter only the Reference Level attribute value change will be considered by subsequent driver Commits or Initiates  |
        |                                        | of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends that you set the IQ    |
        |                                        | Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference        |
        |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
        |                                        | limitations of using this mode.                                                                                          |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first      |
        |                                        | Commit of the named signal configuration. Thereafter only Center Frequency,                                              |
        |                                        | Reference Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or     |
        |                                        | Initiates of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the  |
        |                                        | IQ Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference     |
        |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
        |                                        | limitations of using this mode.                                                                                          |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr    |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type to Relative so that the trigger level is automatically       |
        |                                        | adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic  |
        |                                        | for more details about the limitations of using this mode.                                                               |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LimitedConfigurationChange):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value
            )
            attr_val = enums.LimitedConfigurationChange(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_limited_configuration_change(self, selector_string, value):
        r"""Sets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies and/or
        power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
        value other than **Disabled**, the RFmx driver will use an optimized code path and skip some checks. Because RFmx skips
        some checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in
        the `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to precompute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFInstr or personality attributes while
        testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration is locked after the first Commit of the named signal configuration. Any configuration change        |
        |                                        | thereafter either in RFmxInstr attributes or personality attributes will not be considered by subsequent RFmx Commits    |
        |                                        | or Initiates of this signal.                                                                                             |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency and external attenuation, is locked after first Commit of the named    |
        |                                        | signal configuration. Thereafter, only the Center Frequency and External Attenuation attribute value changes will be     |
        |                                        | considered by subsequent driver Commits or Initiates of this signal.                                                     |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.    |
        |                                        | Thereafter only the Reference Level attribute value change will be considered by subsequent driver Commits or Initiates  |
        |                                        | of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends that you set the IQ    |
        |                                        | Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference        |
        |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
        |                                        | limitations of using this mode.                                                                                          |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first      |
        |                                        | Commit of the named signal configuration. Thereafter only Center Frequency,                                              |
        |                                        | Reference Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or     |
        |                                        | Initiates of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the  |
        |                                        | IQ Power Edge Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference     |
        |                                        | level. Refer to the Limitations of the Limited Configuration Change Property topic for more details about the            |
        |                                        | limitations of using this mode.                                                                                          |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr    |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type to Relative so that the trigger level is automatically       |
        |                                        | adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic  |
        |                                        | for more details about the limitations of using this mode.                                                               |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LimitedConfigurationChange, int):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.LimitedConfigurationChange else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_result_fetch_timeout(self, selector_string):
        r"""Gets the time to wait before results are available in the RFmxNR Attribute. This value is expressed in seconds.

        Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the
        RFmx Attribute waits until the measurement is complete.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time to wait before results are available in the RFmxNR Attribute. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_result_fetch_timeout(self, selector_string, value):
        r"""Sets the time to wait before results are available in the RFmxNR Attribute. This value is expressed in seconds.

        Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the
        RFmx Attribute waits until the measurement is complete.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time to wait before results are available in the RFmxNR Attribute. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def abort_measurements(self, selector_string):
        r"""Stops acquisition and measurements  associated with signal instance that you specify in the  **Selector String**
        parameter, which were previously initiated by the :py:meth:`initiate` method or measurement read methods. Calling this
        method is optional, unless you want to stop a measurement before it is complete. This method executes even if there is
        an incoming error.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.abort_measurements(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_level(self, selector_string, measurement_interval):
        r"""Examines the input signal to calculate the peak power level and sets it as the value of the
        :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute. Use this method to calculate an approximate
        setting for the reference level.

        The RFmxNR Auto Level method completes the following tasks:
        #. Resets the mixer level, mixer level offset, and IF output power offset.

        #. Sets the starting reference level to the maximum reference level supported by the device based on the current RF attenuation, mechanical attenuation, and preamplifier enabled settings.

        #. Iterates to adjust the reference level based on the input signal peak power.

        #. Uses immediate triggering and restores the trigger settings back to user setting after the execution.

        When using NI-PXIe 5663, NI-PXIe 5665, or NI-PXIe 5668R device, NI recommends that you set an appropriate value
        for mechanical attenuation before calling the RFmxNR Auto Level method. Setting an appropriate value for mechanical
        attenuation reduces the number of times the attenuator settings are changed by this function; thus reducing wear and
        tear, and maximizing the life time of the attenuator.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_interval (float):
                This parameter specifies the acquisition length. This value is expressed in seconds. Use this value to compute the
                number of samples to acquire from the signal analyzer. The default value is 10 ms.

                Auto Level method does not use any trigger for acquisition. It ignores the user-configured trigger attributes.
                NI recommends that you set a sufficiently high measurement interval to ensure that the acquired waveform is at least as
                long as one period of the signal.

        Returns:
            Tuple (reference_level, error_code):

            reference_level (float):
                This parameter returns the estimated peak power level of the input signal. This value is expressed in dBm. The default
                value of this parameter is hardware dependent.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            reference_level, error_code = self._interpreter.auto_level(  # type: ignore
                updated_selector_string, measurement_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return reference_level, error_code

    @_raise_if_disposed
    def check_measurement_status(self, selector_string):
        r"""Checks the status of the measurement. Use this method to check for any errors that may occur during measurement or to
        check whether the measurement is complete and results are available.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            Tuple (is_done, error_code):

            is_done (bool):
                This parameter indicates whether the measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            is_done, error_code = self._interpreter.check_measurement_status(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return is_done, error_code

    @_raise_if_disposed
    def clear_all_named_results(self, selector_string):
        r"""Clears all results for the signal that you specify in the **Selector String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_all_named_results(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def clear_named_result(self, selector_string):
        r"""Clears a result instance specified by the result name in the **Selector String** parameter.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_named_result(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def clear_noise_calibration_database(self, selector_string):
        r"""Clears the noise calibration database used for noise compensation.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_noise_calibration_database(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def commit(self, selector_string):
        r"""Commits settings to the hardware. Calling this method is optional. RFmxNR commits settings to the hardware when you
        call the :py:meth:`initiate` method.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.commit(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_digital_edge_trigger(
        self, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        r"""Configures the device to wait for a digital edge trigger and then marks a reference point within the record.

        Spectral measurements are sometimes implemented with multiple acquisitions and therefore will require that
        digital triggers are sent for each acquisition. Multiple factors, including the desired span versus the realtime
        bandwidth of the hardware, affect the number of acquisitions. NI recommends repeating the generation until the
        measurement is completed in order to ensure that all the acquisitions are triggered.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            digital_edge_source (string):
                This parameter specifies the source terminal for the digital edge trigger. This parameter is used when you set the
                :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**. The default value of this
                parameter is hardware dependent.

                +---------------------------+-----------------------------------------------------------+
                | Name (Value)              | Description                                               |
                +===========================+===========================================================+
                | PFI0 (0)                  | The trigger is received on PFI 0.                         |
                +---------------------------+-----------------------------------------------------------+
                | PFI1 (PFI1)               | The trigger is received on PFI 1.                         |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig0 (PXI_Trig0)     | The trigger is received on PXI trigger line 0.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig1 (PXI_Trig1)     | The trigger is received on PXI trigger line 1.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig2 (PXI_Trig2)     | The trigger is received on PXI trigger line 2.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig3 (PXI_Trig3)     | The trigger is received on PXI trigger line 3.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig4 (PXI_Trig4)     | The trigger is received on PXI trigger line 4.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig5 (PXI_Trig5)     | The trigger is received on PXI trigger line 5.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig6 (PXI_Trig6)     | The trigger is received on PXI trigger line 6.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig7 (PXI_Trig7)     | The trigger is received on PXI trigger line 7.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_STAR (PXI_STAR)       | The trigger is received on the PXI star trigger line.     |
                +---------------------------+-----------------------------------------------------------+
                | PXIe_DStarB (PXIe_DStarB) | The trigger is received on the PXIe DStar B trigger line. |
                +---------------------------+-----------------------------------------------------------+
                | TimerEvent (TimerEvent)   | The trigger is received from the timer event.             |
                +---------------------------+-----------------------------------------------------------+

            digital_edge (enums.DigitalEdgeTriggerEdge, int):
                This parameter specifies the source terminal for the digital edge trigger. This parameter is used when you set the
                Trigger Type attribute to **Digital Edge**. The default value is **Rising Edge**.

                +------------------+--------------------------------------------------------+
                | Name (Value)     | Description                                            |
                +==================+========================================================+
                | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
                +------------------+--------------------------------------------------------+
                | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
                +------------------+--------------------------------------------------------+

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the
                measurement acquires pretrigger samples. If the delay is positive, the measurement acquires post-trigger samples. The
                default value is 0.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(digital_edge_source, "digital_edge_source")
            digital_edge = (
                digital_edge.value
                if type(digital_edge) is enums.DigitalEdgeTriggerEdge
                else digital_edge
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_digital_edge_trigger(  # type: ignore
                updated_selector_string,
                digital_edge_source,
                digital_edge,
                trigger_delay,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_external_attenuation(self, selector_string, external_attenuation):
        r"""Specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer.
                This value is expressed in dB. For more information about attenuation, refer to the RF Attenuation and Signal Levels
                topic for your device in the* NI RF Vector Signal Analyzers Help*. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_external_attenuation(  # type: ignore
                updated_selector_string, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency(self, selector_string, center_frequency):
        r"""Configures the expected carrier frequency of the RF signal to acquire. The signal analyzer tunes to this frequency.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                subblock number.

                Example:

                "subblock0"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            center_frequency (float):
                This parameter specifies the expected carrier frequency, in Hz, of the RF signal to acquire. The signal analyzer tunes
                to this frequency. The default of this attribute is hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency(  # type: ignore
                updated_selector_string, center_frequency
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_gnodeb_category(self, selector_string, gnodeb_category):
        r"""Configures the gNodeB Category of the signal being measured.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            gnodeb_category (enums.gNodeBCategory, int):
                This parameter specifies the downlink gNodeB (Base station) category. Refer to *3GPP 38.104* specification for more
                information about gNodeB Category. The default value is **Wide Area Base Station - Category A**.

                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | Name (Value)                                    | Description                                                                   |
                +=================================================+===============================================================================+
                | Wide Area Base Station - Category A (0)         | Specifies that gNodeB is of type Wide Area Base Station - Category A.         |
                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | Wide Area Base Station - Category B Option1 (1) | Specifies that gNodeB is of type Wide Area Base Station - Category B Option1. |
                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | Wide Area Base Station - Category B Option2 (2) | Specifies that gNodeB is of type Wide Area Base Station - Category B Option2. |
                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | Local Area Base Station (3)                     | Specifies that gNodeB is of type Local Area Base Station.                     |
                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | Medium Range Base Station (5)                   | Specifies that gNodeB is of type Medium Range Base Station.                   |
                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | FR2 Category A (6)                              | Specifies that gNodeB is of type FR2 Category A.                              |
                +-------------------------------------------------+-------------------------------------------------------------------------------+
                | FR2 Category B (7)                              | Specifies that gNodeB is of type FR2 Category B.                              |
                +-------------------------------------------------+-------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            gnodeb_category = (
                gnodeb_category.value
                if type(gnodeb_category) is enums.gNodeBCategory
                else gnodeb_category
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_gnodeb_category(  # type: ignore
                updated_selector_string, gnodeb_category
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_iq_power_edge_trigger(
        self,
        selector_string,
        iq_power_edge_trigger_source,
        iq_power_edge_trigger_slope,
        iq_power_edge_trigger_level,
        trigger_delay,
        trigger_minimum_quiet_time_mode,
        trigger_minimum_quiet_time_duration,
        iq_power_edge_trigger_level_type,
        enable_trigger,
    ):
        r"""Configures the device to wait for the complex power of the I/Q data to cross the specified threshold and then marks a
        reference point within the record.

        To trigger on bursty signals, specify a minimum quiet time, which ensures that the trigger does not occur in
        the middle of the burst signal. The quiet time must be set to a value smaller than the time between bursts, but large
        enough to ignore power changes within a burst.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            iq_power_edge_trigger_source (string):
                This parameter specifies the channel from which the device monitors the trigger. This parameter is used only when you
                set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**. The default value of
                this parameter is hardware dependent.

            iq_power_edge_trigger_slope (enums.IQPowerEdgeTriggerSlope, int):
                This parameter specifies whether the device asserts the trigger when the signal power is rising or when it is falling.
                The device asserts the trigger when the signal power exceeds the specified level with the slope you specify. This
                parameter is used only when you set the Trigger Type attribute to **IQ Power Edge**. The default value is **Rising
                Slope**.

            iq_power_edge_trigger_level (float):
                This parameter specifies the power level at which the device triggers. This value is expressed in dB when you set the
                **IQ Power Edge Level Type** parameter to **Relative**, and this value is expressed in dBm when you set the **IQ Power
                Edge Level Type** parameter to **Absolute**. The device asserts the trigger when the signal exceeds the level specified
                by the value of this parameter, taking into consideration the specified slope. This parameter is used only when you set
                the Trigger Type attribute to **IQ Power Edge**. The default value of this parameter is hardware dependent.

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the
                measurement acquires pretrigger samples. If the delay is positive, the measurement acquires post-trigger samples. The
                default value is 0.

            trigger_minimum_quiet_time_mode (enums.TriggerMinimumQuietTimeMode, int):
                This parameter specifies whether the measurement computes the minimum quiet time used for triggering. The default value
                is **Auto**.

                +--------------+-------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                         |
                +==============+=====================================================================================+
                | Manual (0)   | The minimum quiet time for triggering is the value of the Min Quiet Time parameter. |
                +--------------+-------------------------------------------------------------------------------------+
                | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                |
                +--------------+-------------------------------------------------------------------------------------+

            trigger_minimum_quiet_time_duration (float):
                This parameter specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q
                power edge trigger. This value is expressed in seconds. If you set the **IQ Power Edge Slope** parameter to **Rising
                Slope**, the signal is quiet below the trigger level. If you set the **IQ Power Edge Slope** parameter to **Falling
                Slope**, the signal is quiet above the trigger level.

                The default value of this parameter is hardware dependent.

            iq_power_edge_trigger_level_type (enums.IQPowerEdgeTriggerLevelType, int):
                This parameter specifies the reference for the** IQ Power Edge Level** parameter. The **IQ Power Edge Level Type**
                parameter is used only when you set the Trigger Type attribute to **IQ Power Edge**.

                +--------------+----------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                  |
                +==============+==============================================================================================+
                | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
                +--------------+----------------------------------------------------------------------------------------------+
                | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
                +--------------+----------------------------------------------------------------------------------------------+

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(iq_power_edge_trigger_source, "iq_power_edge_trigger_source")
            iq_power_edge_trigger_slope = (
                iq_power_edge_trigger_slope.value
                if type(iq_power_edge_trigger_slope) is enums.IQPowerEdgeTriggerSlope
                else iq_power_edge_trigger_slope
            )
            trigger_minimum_quiet_time_mode = (
                trigger_minimum_quiet_time_mode.value
                if type(trigger_minimum_quiet_time_mode) is enums.TriggerMinimumQuietTimeMode
                else trigger_minimum_quiet_time_mode
            )
            iq_power_edge_trigger_level_type = (
                iq_power_edge_trigger_level_type.value
                if type(iq_power_edge_trigger_level_type) is enums.IQPowerEdgeTriggerLevelType
                else iq_power_edge_trigger_level_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_iq_power_edge_trigger(  # type: ignore
                updated_selector_string,
                iq_power_edge_trigger_source,
                iq_power_edge_trigger_slope,
                iq_power_edge_trigger_level,
                trigger_delay,
                trigger_minimum_quiet_time_mode,
                trigger_minimum_quiet_time_duration,
                iq_power_edge_trigger_level_type,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_reference_level(self, selector_string, reference_level):
        r"""Configures the reference level which represents the maximum expected power of an RF input signal.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of the RF input signal. This
                value is expressed in dBm for RF devices and *V\ :sub:`pk-pk*
                `\ for baseband devices. The default value of this parameter is hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_reference_level(  # type: ignore
                updated_selector_string, reference_level
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rf(
        self, selector_string, center_frequency, reference_level, external_attenuation
    ):
        r"""Configures the RF attributes of the signal specified by the selector string.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            center_frequency (float):
                This parameter specifies the expected carrier frequency, in Hz, of the RF signal to acquire. The signal analyzer tunes
                to this frequency. The default of this attribute is hardware dependent.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of the RF input signal. This
                value is expressed in dBm for RF devices and *V\ :sub:`pk-pk*
                `\ for baseband devices. The default value of this parameter is hardware dependent.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch or cable connected to the RF IN connector of the signal analyzer.
                This value is expressed in dB. For more information about attenuation, refer to the RF Attenuation and Signal Levels
                topic for your device in the* NI RF Vector Signal Analyzers Help*. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_rf(  # type: ignore
                updated_selector_string, center_frequency, reference_level, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_selected_ports_multiple(self, selector_string, selected_ports):
        r"""Configures the selected ports to each chain based on the values you set in
        :py:attr:`~nirfmxnr.attributes.AttributeID.NUMBER_OF_RECEIVE_CHAINS` attribute.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            selected_ports (string):
                This parameter specifies the list of MIMO ports to be configured. Use "port::<deviceName>/<channelNumber>" as the
                format for the selected port.

                For PXIe-5830/5831/5832 devices on a MIMO session, the selected port includes the instrument port in the format
                "port::<deviceName>/<channelNumber>/<instrPort>".

                Example:

                port::myrfsa1/0/if1

                You can use the :py:meth:`build_port_string` method to build the selected port.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(selected_ports, "selected_ports")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_selected_ports_multiple(  # type: ignore
                updated_selector_string, selected_ports
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        r"""Configures the device to wait for a software trigger and then marks a reference point within the record.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the
                measurement acquires pretrigger samples. If the delay is positive, the measurement acquires post-trigger samples. The
                default value is 0.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_software_edge_trigger(  # type: ignore
                updated_selector_string, trigger_delay, int(enable_trigger)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def disable_trigger(self, selector_string):
        r"""Configures the device to not wait for a trigger to mark a reference point within a record. This method defines the
        signal triggering as immediate.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.disable_trigger(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def initiate(self, selector_string, result_name):
        r"""Initiates all enabled measurements. Call this method after configuring the signal and measurement. This method
        asynchronously launches measurements in the background and immediately returns to the caller program. You can fetch
        measurement results using the Fetch methods or result attributes in the attribute node. To get the status of
        measurements, use the :py:meth:`wait_for_measurement_complete` method or :py:meth:`check_measurement_status` method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string) which refers to default result instance.

                Example:

                "result::r1"

                "r1"

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.initiate(  # type: ignore
                updated_selector_string, result_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def reset_to_default(self, selector_string):
        r"""Resets a signal to the default values.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.reset_to_default(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def select_measurements(self, selector_string, measurements, enable_all_traces):
        r"""Enables all the measurements that you specify in the **Measurement** parameter and disables all other measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurements (enums.MeasurementTypes, int):
                This parameter specifies the measurements to perform. You can specify one or more of the following measurements. The
                default value is an empty array.

                +--------------+---------------------------------+
                | Name (Value) | Description                     |
                +==============+=================================+
                | ModAcc (0)   | Enables the ModAcc measurement. |
                +--------------+---------------------------------+
                | SEM (1)      | Enables the SEM measurement.    |
                +--------------+---------------------------------+
                | ACP (2)      | Enables the ACP measurement.    |
                +--------------+---------------------------------+
                | CHP (3)      | Enables the CHP measurement.    |
                +--------------+---------------------------------+
                | OBW (4)      | Enables the OBW measurement.    |
                +--------------+---------------------------------+
                | PVT (5)      | Enables the PVT measurement.    |
                +--------------+---------------------------------+
                | TXP (6)      | Enables the TXP measurement.    |
                +--------------+---------------------------------+

            enable_all_traces (bool):
                This parameter specifies whether to enable all traces for the selected measurement. The default value is FALSE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurements = (
                measurements.value if type(measurements) is enums.MeasurementTypes else measurements
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.select_measurements(  # type: ignore
                updated_selector_string, measurements, int(enable_all_traces)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def wait_for_measurement_complete(self, selector_string, timeout):
        r"""Waits for the specified number for seconds for all the measurements to complete.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name. The default is "" (empty string).

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for which the method waits for the measurement to complete. This value is
                expressed in seconds. A value of -1 specifies that the method waits until the measurement is complete.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.wait_for_measurement_complete(  # type: ignore
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def load_from_generation_configuration_file(
        self, selector_string, file_path, configuration_index
    ):
        r"""Loads the attributes saved in an RFWS/TDMS file onto the RFmx session. This file can be saved using the NR Modulation
        Scheme in RFmx Waveform Creator. Make sure to select the 'store configuration' option while saving the TDMS file.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            file_path (string):
                This parameter specifies the complete path to the RFWS/TDMS file from which the configurations are to be loaded.

            configuration_index (int):
                This parameter specifies the index of the carrier set to be loaded from the RFWS/TDMS file.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(file_path, "file_path")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.load_from_generation_configuration_file(  # type: ignore
                updated_selector_string, file_path, configuration_index
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @staticmethod
    def build_result_string(result_name):
        r"""Creates selector string for use with configuration or fetch.

        Args:
            result_name (string):
                Specifies the result name for building the selector string.
                This input accepts the result name with or without the "result::" prefix.
                Example: "", "result::r1", "r1".

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(result_name, "result_name")
        return _helper.build_result_string(result_name)

    @staticmethod
    def build_bandwidth_part_string(selector_string, bandwidth_part_number):
        r"""Creates the bandwidth part string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            bandwidth_part_number (int):
                This parameter specifies the bandwidth part number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_bandwidth_part_string(selector_string, bandwidth_part_number)  # type: ignore

    @staticmethod
    def build_carrier_string(selector_string, carrier_number):
        r"""Creates the carrier string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            carrier_number (int):
                This parameter specifies the carrier number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_carrier_string(selector_string, carrier_number)  # type: ignore

    @staticmethod
    def build_coreset_cluster_string(selector_string, coreset_cluster_number):
        r"""Creates the coreset cluster string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            coreset_cluster_number (int):
                This parameter specifies the CORESET cluster number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_coreset_cluster_string(selector_string, coreset_cluster_number)  # type: ignore

    @staticmethod
    def build_coreset_string(selector_string, coreset_number):
        r"""Creates the coreset string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            coreset_number (int):
                This parameter specifies the CORESET number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_coreset_string(selector_string, coreset_number)  # type: ignore

    @staticmethod
    def build_offset_string(selector_string, offset_number):
        r"""Creates the offset string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            offset_number (int):
                This parameter specifies the offset number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_offset_string(selector_string, offset_number)  # type: ignore

    @staticmethod
    def build_pdcch_string(selector_string, pdcch_number):
        r"""Creates the PDCCH string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            pdcch_number (int):
                This parameter specifies the PDCCH number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_pdcch_string(selector_string, pdcch_number)  # type: ignore

    @staticmethod
    def build_pdsch_cluster_string(selector_string, pdsch_cluster_number):
        r"""Creates a PDSCH Cluster string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            pdsch_cluster_number (int):
                This parameter specifies the PDSCH cluster number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_pdsch_cluster_string(selector_string, pdsch_cluster_number)  # type: ignore

    @staticmethod
    def build_pdsch_string(selector_string, pdsch_number):
        r"""Creates the PDSCH string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            pdsch_number (int):
                This parameter specifies the PDSCH number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_pdsch_string(selector_string, pdsch_number)  # type: ignore

    @staticmethod
    def build_pusch_cluster_string(selector_string, pusch_cluster_number):
        r"""Creates a PUSCH Cluster string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            pusch_cluster_number (int):
                This parameter specifies the PUSCH cluster number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_pusch_cluster_string(selector_string, pusch_cluster_number)  # type: ignore

    @staticmethod
    def build_pusch_string(selector_string, pusch_number):
        r"""Creates the PUSCH string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            pusch_number (int):
                This parameter specifies the PUSCH number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_pusch_string(selector_string, pusch_number)  # type: ignore

    @staticmethod
    def build_subblock_string(selector_string, subblock_number):
        r"""Creates the subblock string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            subblock_number (int):
                This parameter specifies the number of subblocks that are configured in the non-contiguous carrier aggregation. Set
                this parameter to 1, which is the default, for single carrier and intra-band contiguous carrier aggregation.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_subblock_string(selector_string, subblock_number)  # type: ignore

    @staticmethod
    def build_user_string(selector_string, user_number):
        r"""Creates the user number string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            user_number (int):
                This parameter specifies the user number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_user_string(selector_string, user_number)  # type: ignore

    @staticmethod
    def build_layer_string(selector_string, layer_number):
        r"""Creates a layer string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            layer_number (int):
                This parameter specifies the layer number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_layer_string(selector_string, layer_number)  # type: ignore

    @staticmethod
    def build_chain_string(selector_string, chain_number):
        r"""Creates a chain string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            chain_number (int):
                This parameter specifies the chain number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_chain_string(selector_string, chain_number)  # type: ignore

    @_raise_if_disposed
    def clone_signal_configuration(self, new_signal_name):
        r"""Creates a new instance of a signal by copying all the properties from an existing signal instance.

        Args:
            new_signal_name (string):
                This parameter specifies the name of the new signal. This parameter accepts the signal name with or without the \"signal::\" prefix.

                Example:

                \"signal::NewSigName\"

                \"NewSigName\"

        Returns:
            Tuple (cloned_signal, error_code):

            cloned_signal (nr):
                Contains a new NR signal instance.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(new_signal_name, "new_signal_name")
            updated_new_signal_name = _helper.validate_and_remove_signal_qualifier(
                new_signal_name, self
            )
            cloned_signal, error_code = self._interpreter.clone_signal_configuration(  # type: ignore
                self.signal_configuration_name, updated_new_signal_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return cloned_signal, error_code

    @_raise_if_disposed
    def send_software_edge_trigger(self):
        r"""Sends a trigger to the device when you use the `RFmxNR Configure Trigger <RFmxNR_Configure_Trigger.html>`_ method to
        choose a software version of a trigger and the device is waiting for the trigger to be sent. You can also use this
        method to override a hardware trigger.

        This method returns an error in the following situations:

        - You configure an invalid trigger.

        - You have not previously called the :py:meth:`initiate` method.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_code = self._interpreter.send_software_edge_trigger()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_named_result_names(self, selector_string):
        r"""Returns all the named result names of the signal that you specify in the Selector String parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (result_names, default_result_exists, error_code):

            result_names (string):
                Returns an array of result names.

            default_result_exists (bool):
                Indicates whether the default result exists.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            result_names, default_result_exists, error_code = (
                self._interpreter.get_all_named_result_names(updated_selector_string)  # type: ignore
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return result_names, default_result_exists, error_code

    @_raise_if_disposed
    def analyze_iq_1_waveform(self, selector_string, result_name, x0, dx, iq, reset):
        r"""Performs the enabled measurements on the I/Q complex waveform that you specify in **IQ** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **IQ** or **IQ or Spectral**.

        When using the Analysis-Only mode in RFmxNR, the RFmx driver ignores the RFmx hardware settings such as
        reference level and attenuation. The only RF hardware settings that are not ignored are the center frequency and
        trigger type, since it is needed for spectral measurement traces as well as some measurements such as ModAcc, ACP, and
        SEM.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq (numpy.complex64):
                This parameter specifies an array of complex-valued time domain data. The real and imaginary parts of this complex data
                array correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_iq_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, iq, int(reset)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_spectrum_1_waveform(self, selector_string, result_name, x0, dx, spectrum, reset):
        r"""Performs the enabled measurements on the spectrum that you specify in the **Spectrum** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **Spectral** or **IQ or Spectral**.

        When using the Analysis-Only mode in RFmxNR, the RFmx driver ignores the RFmx hardware settings such as
        reference level and attenuation. The only RF hardware settings that are not ignored are the center frequency and
        trigger type, since it is needed for spectral measurement traces as well as some measurements such as ModAcc, ACP, and
        SEM.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start frequency of the spectrum. This value is expressed in Hz.

            dx (float):
                This parameter specifies the frequency interval between data points in the spectrum.

            spectrum (numpy.float32):
                This parameter specifies the real-value power spectrum.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_spectrum_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, spectrum, int(reset)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_n_waveforms_iq(self, selector_string, result_name, x0, dx, iq, reset):
        r"""Performs the enabled measurements on the I/Q complex waveform(s) that you specify in **IQ** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node. Use this method only if the
        :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value is either **IQ** or **IQ or
        Spectral**.

        When using the Analysis-Only mode in RFmxNR, the RFmx driver ignores the RFmx hardware settings such as
        reference level and attenuation. The only RF hardware settings that are not ignored are the center frequency and
        trigger type, since it is needed for spectral measurement traces as well as some measurements such as ModAcc, ACP, and
        SEM.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string) which refers to default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq ([numpy.complex64]):
                This parameter specifies an array of complex-valued time domain data. The real and imaginary parts of this complex data
                array correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for first record and
                FALSE for subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_n_waveforms_iq(  # type: ignore
                updated_selector_string, result_name, x0, dx, iq, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_n_waveforms_spectrum(self, selector_string, result_name, x0, dx, spectrum, reset):
        r"""Performs the enabled measurements on the spectrum(s) that you specify in the **Spectrum** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node. Use this method only if the
        :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value is either **Spectral** or
        **IQ or Spectral**.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do not specify the result name in this parameter, either the result name specified
                by the **Result Name** parameter or the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start frequency of the spectrum. This value is expressed in Hz.

            dx (float):
                This parameter specifies the frequency interval between data points in the spectrum.

            spectrum ([numpy.float32]):
                This parameter specifies the array of real-value power spectrum.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_n_waveforms_spectrum(  # type: ignore
                updated_selector_string, result_name, x0, dx, spectrum, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code


class NR(_NRBase):
    """Defines a root class which is used to identify and control NR signal configuration."""

    def __init__(self, session, signal_name="", cloning=False):
        """Initializes a NR signal configuration."""
        super(NR, self).__init__(
            session=session,
            signal_name=signal_name,
            cloning=cloning,
        )  # type: ignore

    def __enter__(self):
        """Enters the context of the NR signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the NR signal configuration."""
        self.dispose()  # type: ignore
        pass
