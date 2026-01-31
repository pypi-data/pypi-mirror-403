"""attributes.py - Contains the ID of all attributes belongs to the module."""

from enum import Enum


class AttributeID(Enum):
    """This enum class contains the ID of all attributes belongs to the module."""

    SELECTED_PORTS = 9441277
    r"""Specifies the instrument port to be configured to acquire a signal. Use
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
    """

    CENTER_FREQUENCY = 9437185
    r"""Specifies the center frequency of the acquired RF signal. This value is expressed in Hz. The signal analyzer tunes to
    this frequency.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default of this attribute is hardware dependent.
    """

    REFERENCE_LEVEL = 9437186
    r"""Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
    expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
    port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
    syntax for named signals.
    
    The default of this attribute is hardware dependent.
    """

    EXTERNAL_ATTENUATION = 9437187
    r"""Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
    expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
    device in the *NI RF Vector Signal Analyzers Help*.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
    port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
    syntax for named signals.
    
    The default value is 0.
    """

    REFERENCE_LEVEL_HEADROOM = 9441276
    r"""Specifies the margin RFmx adds to the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute. The margin
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
    """

    TRIGGER_TYPE = 9437188
    r"""Specifies the type of trigger to be used for signal acquisition.
    
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
    """

    DIGITAL_EDGE_TRIGGER_SOURCE = 9437189
    r"""Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default of this attribute is hardware dependent.
    """

    DIGITAL_EDGE_TRIGGER_EDGE = 9437190
    r"""Specifies the active edge for the trigger. This attribute is used only when you set the
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
    """

    IQ_POWER_EDGE_TRIGGER_SOURCE = 9437191
    r"""Specifies the channel from which the device monitors the trigger.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL = 9437192
    r"""Specifies the power level at which the device triggers. This value is expressed in dB when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative**; and in dBm when
    you set the IQ Power Edge Level Type attribute to **Absolute**. The device asserts the trigger when the signal exceeds
    the level specified by the value of this attribute, taking into consideration the specified slope. This attribute is
    used only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE = 9441279
    r"""Specifies the reference for the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute. The
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
    """

    IQ_POWER_EDGE_TRIGGER_SLOPE = 9437193
    r"""Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
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
    """

    TRIGGER_DELAY = 9437194
    r"""Specifies the trigger delay time. This value is expressed in seconds. If the delay is negative, the measurement
    acquires pre-trigger samples. If the delay is positive, the measurement acquires post-trigger samples.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    TRIGGER_MINIMUM_QUIET_TIME_MODE = 9437195
    r"""Specifies whether the measurement computes the minimum quiet time used for triggering.
    
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
    """

    TRIGGER_MINIMUM_QUIET_TIME_DURATION = 9437196
    r"""Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
    trigger. This value is expressed in seconds. If you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising Slope**, the signal is
    quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling Slope**, the signal is quiet
    above the trigger level.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default of this attribute is hardware dependent.
    """

    LINK_DIRECTION = 9437198
    r"""Specifies the link direction of the received signal.
    
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
    """

    GNODEB_CATEGORY = 9437279
    r"""Specifies the downlink gNodeB (Base Station) category. Refer to the *3GPP 38.104* specification for more information
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
    """

    GNODEB_TYPE = 9437344
    r"""Specifies the downlink gNodeB (Base Station) type. Refer to the *3GPP 38.104* specification for more information about
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
    """

    SATELLITE_ACCESS_NODE_CLASS = 9437347
    r"""Specifies the downlink SAN (Satellite Access Node) class representing the satellite constellation as specified in
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
    """

    TRANSMIT_ANTENNA_TO_ANALYZE = 9437339
    r"""Specifies the physical antenna that is currently connected to the analyzer.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    NUMBER_OF_RECEIVE_CHAINS = 9490435
    r"""Specifies the number of receive chains.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    POWER_CLASS = 9437340
    r"""Specifies the power class for the UE as specified in section 6.2 of *3GPP 38.101-1/2/3* specification.
    
    This attribute impacts the spectral flatness mask for uplink.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **3**.
    """

    PIBY2BPSK_POWER_BOOST_ENABLED = 9437342
    r"""Specifies the power boost for PI/2 BPSK signal when you set the
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
    """

    AUTO_RESOURCE_BLOCK_DETECTION_ENABLED = 9437215
    r"""Specifies whether the values of modulation type, number of resource block clusters, resource block offsets, and number
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
    """

    AUTO_CELL_ID_DETECTION_ENABLED = 9437324
    r"""Specifies whether to enable the autodetection of the cell ID.
    
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
    """

    DOWNLINK_CHANNEL_CONFIGURATION_MODE = 9437326
    r"""Specifies the downlink channel configuration mode.
    
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
    """

    AUTO_INCREMENT_CELL_ID_ENABLED = 9437343
    r"""Specifies whether the cell ID of component carrier is auto calculated and configured by the measurement or configured
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
    """

    DOWNLINK_TEST_MODEL_CELL_ID_MODE = 9437470
    r"""Specifies whether the cell ID of downlink test model component carriers is auto calculated and configured by the
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
    """

    NUMBER_OF_SUBBLOCKS = 9437200
    r"""Specifies the number of subblocks configured in intraband non-contiguous carrier aggregation scenarios.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1. Set this attribute to 1 for single carrier and intra-band contiguous carrier
    aggregation.
    """

    SUBBLOCK_FREQUENCY = 9437471
    r"""Specifies the offset of the subblock from the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    SUBBLOCK_TRANSMIT_LO_FREQUENCY = 9437280
    r"""Specifies the frequency of the transmitters local oscillator. This value is expressed in Hz. The frequency is defined
    per subblock and relative to the respective subblock center frequency.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PHASE_COMPENSATION_FREQUENCY = 9437281
    r"""Specifies the frequency used for phase compensation of the signal when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PHASE_COMPENSATION` attribute to **User Defined**. This value is expressed
    in Hz.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    FREQUENCY_RANGE = 9437237
    r"""Specifies whether to use channel bandwidth and subcarrier spacing configuration supported in Frequency Range 1 (sub
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
    """

    BAND = 9437202
    r"""Specifies the evolved universal terrestrial radio access (E-UTRA) or NR operating frequency band of a subblock as
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
    """

    SUBBLOCK_ENDC_NOMINAL_SPACING_ADJUSTMENT = 9437443
    r"""Specifies the adjustment of the center frequency for adjacent E-UTRA and NR Channels in case of nominal spacing. The
    value is expressed in Hz.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **0**.
    """

    CHANNEL_RASTER = 9437336
    r"""Specifies the subblock channel raster which is used for computing nominal spacing between aggregated carriers as
    specified in section 5.4A.1 of *3GPP 38.101-1/2* specification and section 5.4.1.2 of *3GPP TS 38.104* specification.
    The value is expressed in Hz.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **15 kHz**.
    
    Valid values for frequency range 1 are **15 kHz** and **100kHz**.
    
    Valid values for frequency range 2-1 is **60 kHz**.
    
    Valid values for frequency range 2-2 are **120 kHz**, **480 kHz**, and **960 kHz**.
    """

    COMPONENT_CARRIER_SPACING_TYPE = 9437203
    r"""Specifies the spacing between adjacent component carriers (CCs) within a subblock.
    
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
    """

    COMPONENT_CARRIER_AT_CENTER_FREQUENCY = 9437204
    r"""Specifies the index of the component carrier having its center at the user-configured center frequency. The measurement
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
    """

    NUMBER_OF_COMPONENT_CARRIERS = 9437205
    r"""Specifies the number of component carriers configured within a subblock. Set this attribute to 1 for single carrier.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    DOWNLINK_TEST_MODEL = 9437440
    r"""Specifies the NR test model type when you set the
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
    """

    DOWNLINK_TEST_MODEL_MODULATION_TYPE = 9437469
    r"""Specifies the modulation type to be used with the selected test model. Selecting the modulation type is supported only
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
    """

    DOWNLINK_TEST_MODEL_DUPLEX_SCHEME = 9437441
    r"""Specifies the duplexing technique of the signal being measured. Refer to section 4.9.2 of *3GPP 38.141* specification
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
    """

    RATED_TRP = 9437345
    r"""Specifies the rated carrier TRP output power. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    RATED_EIRP = 9437346
    r"""Specifies the rated carrier EIRP output power. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    COMPONENT_CARRIER_BANDWIDTH = 9437206
    r"""Specifies the channel bandwidth of the signal being measured. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **100M**. Valid values for frequency range 1 are from **3M** to **100M**. Valid values for
    frequency range 2-1 are **50M**, **100M**, **200M**, and **400M**. Valid values for frequency range 2-2 are **100M**,
    **400M**, **800M**, **1600M**, and **2000M**.
    """

    COMPONENT_CARRIER_FREQUENCY = 9437207
    r"""Specifies the offset of the component carrier from the subblock center frequency that you configure in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` attribute.  This value is expressed in Hz.
    
    This attribute is applicable only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_SPACING_TYPE` attribute to **User**.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    COMPONENT_CARRIER_ALLOCATED = 9437464
    r"""Specifies whether a component carrier has one or more resource elements allocated.
    
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
    """

    COMPONENT_CARRIER_RADIO_ACCESS_TYPE = 9437442
    r"""Specifies if a carrier is a NR or an E-UTRA carrier while using dual connectivity (EN-DC) signal.
    
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
    """

    CELL_ID = 9437209
    r"""Specifies a physical layer cell identity.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0. Valid values are 0 to 1007, inclusive.
    """

    REFERENCE_GRID_SUBCARRIER_SPACING = 9437282
    r"""Specifies the subcarrier spacing of the reference resource grid when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. This should be the
    largest subcarrier spacing used in the component carrier. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **30kHz**.
    
    Valid values for frequency range 1 are **15kHz**, **30kHz**, and **60kHz**.
    
    Valid values for frequency range 2-1 are **60kHz**, **120kHz**, and **240kHz**.
    
    Valid values for frequency range 2-2 are **120kHz**, **480kHz**, and **960kHz**.
    """

    REFERENCE_GRID_START = 9437283
    r"""Specifies the reference resource grid start relative to Reference Point A in terms of resource block offset when you
    set the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**. Center of
    subcarrier 0 in common resource block 0 is considered as Reference Point A.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    REFERENCE_GRID_SIZE = 9437465
    r"""Specifies the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
    attribute to **Manual**.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    """

    SUB_BAND_ALLOCATION = 9437244
    r"""Specifies the sub-band allocation in the NR-U wideband channel. Sub-band is the set of RBs with approximately 20 MHz
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
    """

    NUMBER_OF_BANDWIDTH_PARTS = 9437245
    r"""Specifies the number of bandwidth parts present in the component carrier.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    BANDWIDTH_PART_SUBCARRIER_SPACING = 9437211
    r"""Specifies the subcarrier spacing of the bandwidth part used  in the component carrier.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    
    The default value is **30kHz**.
    
    Valid values for frequency range 1 are **15kHz**, **30kHz**, and **60kHz**.
    
    Valid values for frequency range 2-1 are **60kHz** and **120kHz**.
    
    Valid values for frequency range 2-2 are **120kHz**, **480kHz**, and **960kHz**.
    """

    BANDWIDTH_PART_CYCLIC_PREFIX_MODE = 9437210
    r"""Specifies the cyclic prefix (CP) duration and the number of symbols in a slot for the signal being measured.
    
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
    """

    GRID_START = 9437334
    r"""Specifies the resource grid start relative to Reference Point A in terms of resource block offset when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_GRID_ALIGNMENT_MODE` attribute to **Manual**.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    
    The default value is 0.
    """

    GRID_SIZE = 9437338
    r"""Specifies the reference resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
    attribute to **Manual**.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    """

    BANDWIDTH_PART_RESOURCE_BLOCK_OFFSET = 9437246
    r"""Specifies the resource block offset of a bandwidth part relative to the resource
    :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_START` attribute.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>"  as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    
    The default value is 0.
    """

    BANDWIDTH_PART_NUMBER_OF_RESOURCE_BLOCKS = 9437247
    r"""Sets the number of consecutive resource blocks in a bandwidth  part.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    
    The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
    bandwidth that do not violate the minimum guard band are configured.
    """

    BANDWIDTH_PART_DC_LOCATION_KNOWN = 9437473
    r"""Specifies whether Uplink Tx Direct Current location within the carrier is determined. If set to **False**, DC location
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
    """

    NUMBER_OF_USERS = 9437284
    r"""Specifies the number of users present in the bandwidth part.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    
    The default value is 1.
    """

    RNTI = 9437285
    r"""Specifies the RNTI.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    NUMBER_OF_PUSCH_CONFIGURATIONS = 9437259
    r"""Specifies the number of PUSCH slot configurations.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    PUSCH_TRANSFORM_PRECODING_ENABLED = 9437214
    r"""Specifies whether transform precoding is enabled. Enable transform precoding when analyzing a DFT-s-OFDM waveform.
    
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
    """

    PUSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS = 9437223
    r"""Specifies the number of clusters of resource allocations with each cluster including one or more consecutive resource
    blocks. This attribute is ignored if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    PUSCH_RESOURCE_BLOCK_OFFSET = 9437224
    r"""Specifies the starting resource block number of a PUSCH cluster. This attribute is ignored if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute to **True**.
    
    Use "puschcluster<*s*>" or "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>/puschcluster<*s*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PUSCH_NUMBER_OF_RESOURCE_BLOCKS = 9437225
    r"""Specifies the number of consecutive resource blocks in a physical uplink shared channel (PUSCH) cluster. This attribute
    is ignored if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` attribute
    to **True**.
    
    Use "puschcluster<*s*>" or "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>/puschcluster<*s*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is -1. If you set this attribute to -1, all available resource blocks for the specified
    bandwidth are configured.
    """

    PUSCH_MODULATION_TYPE = 9437222
    r"""Specifies the modulation scheme used in the physical uplink shared channel (PUSCH) of the signal being measured.
    
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
    """

    PUSCH_DMRS_RELEASE_VERSION = 9437462
    r"""Specifies the 3GGP release version for PUSCH DMRS.
    
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
    """

    PUSCH_DMRS_ANTENNA_PORTS = 9437249
    r"""Specifies the antenna ports used for DMRS transmission.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0. Valid values depend on :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE`
    and :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_NUMBER_OF_CDM_GROUPS` attributes.
    """

    PUSCH_DMRS_POWER_MODE = 9437265
    r"""Specifies whether the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER` attribute is calculated
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
    """

    PUSCH_DMRS_POWER = 9437232
    r"""Specifies the factor which boosts the PUSCH DMRS REs. This value is expressed in dB. This attribute is ignored if you
    set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_POWER_MODE` attribute to **CDM Groups**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PUSCH_DMRS_NUMBER_OF_CDM_GROUPS = 9437250
    r"""Specifies the number of CDM groups, when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**, otherwise it is
    coerced to 2.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    PUSCH_DMRS_SCRAMBLING_ID_MODE = 9437252
    r"""Specifies whether the configured Scrambling ID is honored or the Cell ID is used for reference signal generation.
    
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
    """

    PUSCH_DMRS_SCRAMBLING_ID = 9437253
    r"""Specifies the value of scrambling ID. This attribute is valid only when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0. Valid values are from 0 to 65535, inclusive.
    """

    PUSCH_DMRS_NSCID = 9437254
    r"""Specifies the value of PUSCH DMRS nSCID used for reference signal generation. This attribute is valid only when you set
    the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **0**.
    """

    PUSCH_DMRS_GROUP_HOPPING_ENABLED = 9437217
    r"""Specifies whether the group hopping is enabled. This attribute is valid only when you set the
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
    """

    PUSCH_DMRS_SEQUENCE_HOPPING_ENABLED = 9437218
    r"""Specifies whether the sequence hopping is enabled. This attribute is valid only when you set the
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
    """

    PUSCH_DMRS_PUSCH_ID_MODE = 9437255
    r"""Specifies whether PUSCH DMRS PUSCH ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or specified by
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
    """

    PUSCH_DMRS_PUSCH_ID = 9437256
    r"""Specifies the value of PUSCH DMRS PUSCH ID used for reference signal generation. This attribute is valid only when you
    set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_PUSCH_ID_MODE` attribute to **User Defined**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0. Valid values are from 0 to 1007, inclusive.
    """

    PUSCH_DMRS_CONFIGURATION_TYPE = 9437233
    r"""Specifies the configuration type of DMRS.
    
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
    """

    PUSCH_MAPPING_TYPE = 9437236
    r"""Specifies the mapping type of DMRS.
    
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
    """

    PUSCH_DMRS_TYPE_A_POSITION = 9437258
    r"""Specifies the position of first DMRS symbol in a slot when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_MAPPING_TYPE` attribute to **Type A**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **2**.
    """

    PUSCH_DMRS_DURATION = 9437235
    r"""Specifies whether the DMRS is single-symbol or double-symbol.
    
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
    """

    PUSCH_DMRS_ADDITIONAL_POSITIONS = 9437234
    r"""Specifies the number of additional sets of consecutive DMRS symbols in a slot.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **0**.
    """

    PUSCH_PTRS_ENABLED = 9437269
    r"""Specifies whether the PUSCH transmission contains PTRS signals.
    
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
    """

    PUSCH_PTRS_ANTENNA_PORTS = 9437270
    r"""Specifies the DMRS antenna ports associated with PTRS transmission. This attribute is valid only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PUSCH_PTRS_POWER_MODE = 9437271
    r"""Specifies whether the PUSCH PTRS power scaling is calculated as defined in 3GPP specification or specified by you. This
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
    """

    PUSCH_PTRS_POWER = 9437272
    r"""Specifies the factor by which the PUSCH PTRS REs are boosted. This value is expressed in dB. This attribute is valid
    only if you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    NUMBER_OF_PTRS_GROUPS = 9437274
    r"""Specifies the number of PTRS groups per OFDM symbol. This attribute is valid only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **2**.
    """

    SAMPLES_PER_PTRS_GROUP = 9437275
    r"""Specifies the number of samples per each PTRS group. This attribute is valid only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **True**.
    
    The default value is **2**.
    """

    PUSCH_PTRS_TIME_DENSITY = 9437276
    r"""Specifies the density of PTRS in time domain. This attribute is valid only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **1**.
    """

    PUSCH_PTRS_FREQUENCY_DENSITY = 9437277
    r"""Specifies the density of PTRS in frequency domain. This attribute is valid only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **2**.
    """

    PUSCH_PTRS_RE_OFFSET = 9437278
    r"""Specifies the RE offset to be used for transmission of PTRS as defined in the Table 6.4.1.2.2.1-1 of *3GPP 38.211*
    specification.  This attribute is valid only if you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_ENABLED` attribute to **True** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute to **False**.
    
    Use "pusch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pusch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **00**.
    """

    PUSCH_SLOT_ALLOCATION = 9437260
    r"""Specifies the slot allocation in NR Frame. This defines the indices of the allocated slots.
    
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
    """

    PUSCH_SYMBOL_ALLOCATION = 9437261
    r"""Specifies the symbol allocation of each slot allocation.
    
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
    """

    NUMBER_OF_PDSCH_CONFIGURATIONS = 9437328
    r"""Specifies the number of PDSCH slot configurations.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    PDSCH_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS = 9437287
    r"""Specifies the number of clusters of resource allocations with each cluster including one or more consecutive resource
    blocks.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    PDSCH_RESOURCE_BLOCK_OFFSET = 9437288
    r"""Specifies the starting resource block number of a PDSCH cluster.
    
    Use "pdschcluster<*s*>" or "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>/pdschcluster<*s*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDSCH_NUMBER_OF_RESOURCE_BLOCKS = 9437289
    r"""Specifies the number of consecutive resource blocks in a PDSCH cluster.
    
    Use "pdschcluster<*s*>" or "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>/pdschcluster<*s*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is -1. If you set this attribute to -1, all available resource blocks within the bandwidth
    part are configured.
    """

    PDSCH_MODULATION_TYPE = 9437290
    r"""Specifies the modulation scheme used in PDSCH channel of the signal being measured.
    
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
    """

    PDSCH_DMRS_RELEASE_VERSION = 9437463
    r"""Specifies the 3GGP release version for PDSCH DMRS.
    
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
    """

    PDSCH_DMRS_ANTENNA_PORTS = 9437291
    r"""Specifies the antenna ports used for DMRS transmission.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1000.
    """

    PDSCH_DMRS_POWER_MODE = 9437292
    r"""Specifies whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_DMRS_POWER` is calculated based on
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
    """

    PDSCH_DMRS_POWER = 9437293
    r"""Specifies the factor by which the PDSCH DMRS REs are boosted. This value is expressed in dB.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDSCH_DMRS_NUMBER_OF_CDM_GROUPS = 9437294
    r"""Specifies the number of CDM groups.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    PDSCH_DMRS_SCRAMBLING_ID_MODE = 9437295
    r"""Specifies whether the configured Scrambling ID is based on :py:attr:`~nirfmxnr.attributes.AttributeID.CELL_ID` or
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
    """

    PDSCH_DMRS_SCRAMBLING_ID = 9437296
    r"""Specifies the value of scrambling ID used for reference signal generation.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDSCH_DMRS_NSCID = 9437297
    r"""Specifies the value of PDSCH DMRS nSCID used for reference signal generation.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **0**.
    """

    PDSCH_DMRS_CONFIGURATION_TYPE = 9437300
    r"""Specifies the configuration type of DMRS.
    
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
    """

    PDSCH_MAPPING_TYPE = 9437301
    r"""Specifies the mapping type of DMRS.
    
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
    """

    PDSCH_DMRS_TYPE_A_POSITION = 9437302
    r"""Specifies the position of first DMRS symbol in a slot for Type A configurations.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **2**.
    """

    PDSCH_DMRS_DURATION = 9437303
    r"""Specifies whether the DMRS is single-symbol or double-symbol.
    
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
    """

    PDSCH_DMRS_ADDITIONAL_POSITIONS = 9437304
    r"""Specifies the number of additional sets of consecutive DMRS symbols in a slot.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **0**.
    """

    PDSCH_PTRS_ENABLED = 9437305
    r"""Specifies whether PT-RS is present in the transmitted signal.
    
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
    """

    PDSCH_PTRS_ANTENNA_PORTS = 9437306
    r"""Specifies the DMRS Antenna Ports associated with PTRS transmission.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDSCH_PTRS_POWER_MODE = 9437307
    r"""Specifies whether the configured :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER` is calculated as defined
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
    """

    EPRE_RATIO_PORT = 9437330
    r"""Specifies the EPRE Ratio Port used to determine the PDSCH PT-RS RE power scaling as defined in the Table 4.1-2 of *3GPP
    TS 38.214* specification when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute
    to **Standard**.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDSCH_PTRS_POWER = 9437308
    r"""Specifies the factor by which the PDSCH PTRS REs are boosted, compared to PDSCH REs. This value is expressed in dB. The
    value of this attribute is taken as an input when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER_MODE` attribute to **User Defined**. If you set the PDSCH
    PTRS Pwr Mode attribute to **Standard**, the value is computed from other parameters.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDSCH_PTRS_TIME_DENSITY = 9437309
    r"""Specifies the density of PTRS in time domain
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **1**.
    """

    PDSCH_PTRS_FREQUENCY_DENSITY = 9437310
    r"""Specifies the density of PTRS in frequency domain
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **2**.
    """

    PDSCH_PTRS_RE_OFFSET = 9437311
    r"""Specifies the RE Offset to be used for transmission of PTRS as defined in Table 7.4.1.2.2-1 of *3GPP 38.211*
    specification.
    
    Use "pdsch<*r*>" or "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/pdsch<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **00**.
    """

    PDSCH_SLOT_ALLOCATION = 9437312
    r"""Specifies the slot allocation in NR Frame. This defines the indices of the allocated slots.
    
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
    """

    PDSCH_SYMBOL_ALLOCATION = 9437313
    r"""Specifies the symbol allocation of each slot allocation.
    
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
    """

    NUMBER_OF_CORESETS = 9437446
    r"""Specifies the number of CORSETs present in the bandwidth part.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*> as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this
    attribute.
    
    The default value is 0.
    """

    CORESET_SYMBOL_OFFSET = 9437447
    r"""Specifies the starting symbol number of the CORESET within a slot.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    CORESET_NUMBER_OF_SYMBOLS = 9437448
    r"""Specifies the number of symbols allotted to CORESET in each slot.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    CORESET_NUMBER_OF_RESOURCE_BLOCK_CLUSTERS = 9437449
    r"""Specifies the number of RB clusters present in the CORESET.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    CORESET_RESOURCE_BLOCK_OFFSET = 9437450
    r"""Specifies the starting resource block of a CORESET cluster.
    
    Use "coresetcluster<*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/coresetcluster<*j*> as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    Valid values should be a multiple of 6. The default value is 0.
    """

    CORESET_NUMBER_OF_RESOURCE_BLOCKS = 9437451
    r"""Specifies the number of consecutive resource blocks of CORESET cluster.
    
    Use "coresetcluster<*k*>" or "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>"/coresetcluster<*k*> as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The value should be a multiple of 6. The default value is -1. If you set this attribute to the default value,
    all available resource blocks within the bandwidth part are configured.
    """

    CORESET_PRECODING_GRANULARITY = 9437452
    r"""Specifies the precoding granularity of the CORESET.
    
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
    """

    CORESET_CCE_TO_REG_MAPPING_TYPE = 9437453
    r"""Specifies the CCE-to-REG mapping type of CORESET.
    
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
    """

    CORESET_REG_BUNDLE_SIZE = 9437454
    r"""Specifies the RBG bundle size of CORESET for interleaved CCE to REG mapping.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **6**.
    
    For interleaved Mapping Type, the valid values are 2, 3, and 6. For non-interleaved Mapping Type, the valid
    value is 6.
    """

    CORESET_INTERLEAVER_SIZE = 9437455
    r"""Specifies the interleaver size of CORESET for interleaved CCE to REG mapping.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **2**.
    """

    CORESET_SHIFT_INDEX = 9437456
    r"""Specifies the shift index of CORESET for interleaved CCE to REG mapping.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    NUMBER_OF_PDCCH_CONFIGURATIONS = 9437458
    r"""Specifies the number of PDCCH Configurations for a CORESET.
    
    Use "coreset<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/coreset<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PDCCH_CCE_AGGREGATION_LEVEL = 9437459
    r"""Specifies the CCE aggregation level of PDCCH.
    
    Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **1**.
    """

    PDCCH_CCE_OFFSET = 9437460
    r"""Specifies the PDCCH CCE offset.
    
    Use " pdcch <*j*>" or "coreset<*k*>" or "bwp<*l*>" or "carrier<*m*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*m*>/bwp<*l*>/coreset<*k*>"/pdcch<*j*> as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    It is used when the PDCCH Candidate Index is set to -1. The default value is 0.
    """

    PDCCH_SLOT_ALLOCATION = 9437461
    r"""Specifies the slot allocation in NR frame. This defines the indices of the allocated slots.
    
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
    """

    SSB_ENABLED = 9437314
    r"""Specifies whether synchronization signal block (SSB) is present in the transmitted signal.
    
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
    """

    SSB_GRID_START = 9437466
    r"""Specifies the SSB resource grid start relative to Reference Point A in terms of resource block offset.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    """

    SSB_GRID_SIZE = 9437467
    r"""Specifies the SSB resource grid size when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.GRID_SIZE_MODE`
    attribute to **Manual**.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    """

    SSB_CRB_OFFSET = 9437315
    r"""Specifies the CRB offset for the SS/PBCH block relative to the reference Point A in units of 15 kHz resource blocks for
    frequency range 1 or 60 kHz resource blocks for frequency range 2-1 and frequency range 2-2.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    SUBCARRIER_SPACING_COMMON = 9437337
    r"""Specifies the basic unit of :py:attr:`~nirfmxnr.attributes.AttributeID.SSB_SUBCARRIER_OFFSET` attribute for frequency
    range 2-1 and frequency range 2-2. The attribute refers to the MIB control element subCarrierSpacingCommon in *3GPP TS
    38.331*.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **60kHz**.
    """

    SSB_SUBCARRIER_OFFSET = 9437316
    r"""Specifies an additional subcarrier offset for the SS/PBCH block in units of resource blocks of 15 kHz subcarrier
    spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON` attribute for frequency range 1,
    and of 60kHz subcarrier spacing given by :py:attr:`~nirfmxnr.attributes.AttributeID.SUBCARRIER_SPACING_COMMON`
    attribute for frequency range 2-1 and frequency range 2-2.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    SSB_PERIODICITY = 9437332
    r"""Specifies the time difference with which the SS/PBCH block transmit pattern repeats.
    
    Possible values are 5 ms, 10 ms, 20 ms, 40 ms, 80 ms, and 160 ms.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **5 ms**.
    """

    SSB_PATTERN = 9437317
    r"""Specifies the candidate SS/PBCH blocks with different subcarrier spacing configurations as defined in the section 4.1
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
    """

    SSB_ACTIVE_BLOCKS = 9437333
    r"""Specifies the SSB burst(s) indices for the SSB pattern that needs to be transmitted.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0 - Last.
    """

    PSS_POWER = 9437318
    r"""Specifies the power scaling value for the primary synchronization symbol in the SS/PBCH block. This value is expressed
    in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    SSS_POWER = 9437319
    r"""Specifies the power scaling value for the secondary synchronization symbol in the SS/PBCH block. This value is
    expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PBCH_POWER = 9437320
    r"""Specifies the power scaling value for the PBCH REs in the SS/PBCH block. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    PBCH_DMRS_POWER = 9437321
    r"""Specifies the power scaling value for the PBCH DMRS symbols in the SS/PBCH block. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    SSB_HRF_INDEX = 9437472
    r"""Specifies the half radio frame in which the SS/PBCH block should be allocated.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The possible values are 0 and 1. The default value is **0**.
    """

    MODACC_MEASUREMENT_ENABLED = 9453568
    r"""Specifies whether to enable the ModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODACC_MULTICARRIER_FILTER_ENABLED = 9453570
    r"""Specifies whether to use the filter in single carrier configurations to minimize leakage into the carrier. Measurement
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
    """

    MODACC_SYNCHRONIZATION_MODE = 9453572
    r"""Specifies whether the measurement is performed from slot or frame boundary.
    
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
    """

    MODACC_MEASUREMENT_LENGTH_UNIT = 9453573
    r"""Specifies the units in which measurement offset and measurement length are specified.
    
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
    """

    MODACC_MEASUREMENT_OFFSET = 9453574
    r"""Specifies the measurement offset to skip from the synchronization boundary. The synchronization boundary is specified
    by the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute. The unit for this is
    specified by :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    MODACC_MEASUREMENT_LENGTH = 9453575
    r"""Specifies the measurement length in units specified by
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT` attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    MODACC_FREQUENCY_ERROR_ESTIMATION = 9453681
    r"""Specifies the operation mode of frequency error estimation.
    
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
    """

    MODACC_SYMBOL_CLOCK_ERROR_ESTIMATION_ENABLED = 9453685
    r"""Specifies whether to estimate symbol clock error.
    
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
    """

    MODACC_IQ_IMPAIRMENTS_MODEL = 9453698
    r"""Specifies the I/Q impairments model used by the measurement for estimating I/Q impairments.
    
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
    """

    MODACC_IQ_ORIGIN_OFFSET_ESTIMATION_ENABLED = 9453686
    r"""Specifies whether to estimate the IQ origin offset.
    
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
    """

    MODACC_IQ_MISMATCH_ESTIMATION_ENABLED = 9453687
    r"""Specifies whether to estimate the IQ impairments such as IQ gain imbalance and quadrature skew.
    
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
    """

    MODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED = 9453699
    r"""Specifies whether to enable IQ gain imbalance correction.
    
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
    """

    MODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED = 9453700
    r"""Specifies whether to enable IQ quadrature error correction.
    
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
    """

    MODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED = 9453701
    r"""Specifies whether to enable IQ timing skew correction.
    
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
    """

    MODACC_IQ_IMPAIRMENTS_PER_SUBCARRIER_ENABLED = 9453702
    r"""Specifies whether to return I/Q impairments independently for each subcarrier.
    
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
    """

    MODACC_MAGNITUDE_AND_PHASE_ERROR_ENABLED = 9453688
    r"""Specifies whether to measure the magnitude and the phase error.
    
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
    """

    MODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE = 9453697
    r"""Specifies whether to either use a reference waveform or an acquired waveform to create reference data symbols for EVM
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
    """

    MODACC_SPECTRUM_INVERTED = 9453576
    r"""Specifies whether the spectrum of the signal being measured  is inverted. This happens when I and Q component of the
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
    """

    MODACC_CHANNEL_ESTIMATION_TYPE = 9453577
    r"""Specifies the method used for channel estimation.
    
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
    """

    MODACC_PHASE_TRACKING_MODE = 9453649
    r"""Specifies the method used for phase tracking.
    
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
    """

    MODACC_TIMING_TRACKING_MODE = 9453650
    r"""Specifies the method used for timing tracking.
    
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
    """

    MODACC_PRE_FFT_ERROR_ESTIMATION_INTERVAL = 9453728
    r"""Specifies the interval used for Pre-FFT error estimation.
    
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
    """

    MODACC_EVM_UNIT = 9453578
    r"""Specifies the units of the EVM results.
    
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
    """

    MODACC_FFT_WINDOW_TYPE = 9453579
    r"""Specifies the FFT window type used for EVM calculation.
    
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
    """

    MODACC_FFT_WINDOW_OFFSET = 9453580
    r"""Specifies the position of the FFT window used to calculate the EVM when
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute is set to **Custom**. The offset is
    expressed as a percentage of the cyclic prefix length. If you set this attribute to 0, the EVM window starts at the end
    of cyclic prefix. If you set this attribute to 100, the EVM window starts at the beginning of cyclic prefix.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 50. Valid values are 0 to 100, inclusive.
    """

    MODACC_FFT_WINDOW_LENGTH = 9453581
    r"""Specifies the FFT window length (W). This value is expressed as a percentage of the cyclic prefix length. This
    attribute is used when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_TYPE` attribute to
    **3GPP**, where it is needed to calculate the EVM using two different FFT window positions, Delta_C-W/2, and
    Delta_C+W/2.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is -1. Valid values range from -1 to 100, inclusive. When this attribute is set to -1, the
    measurement automatically sets the value of this attribute to the recommended value as specified in the Annexe F.5 of
    *3GPP TS 38.101-2* specification for uplink and Annexe B.5.2 and C.5.2 of *3GPP TS 38.104* specification for downlink.
    """

    MODACC_DC_SUBCARRIER_REMOVAL_ENABLED = 9437231
    r"""Specifies whether the DC subcarrier is removed from the EVM results.
    
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
    """

    MODACC_COMMON_CLOCK_SOURCE_ENABLED = 9453582
    r"""Specifies whether same reference clock is used for local oscillator and digital-to-analog converter. When same
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
    """

    MODACC_SPECTRAL_FLATNESS_CONDITION = 9453584
    r"""Specifies the test condition for Spectral Flatness measurement.
    
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
    """

    MODACC_NOISE_COMPENSATION_ENABLED = 9453714
    r"""Specifies whether the contribution of the instrument noise is compensated for EVM computation.
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
    """

    MODACC_NOISE_COMPENSATION_INPUT_POWER_CHECK_ENABLED = 9453715
    r"""Specifies whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
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
    """

    MODACC_NOISE_COMPENSATION_REFERENCE_LEVEL_COERCION_LIMIT = 9453716
    r"""Specifies the coercion limit for the reference level for noise compensation. When you set
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
    """

    MODACC_MEASUREMENT_MODE = 9453717
    r"""Specifies whether the measurement should calibrate the noise floor of the analyzer or perform the ModAcc measurement.
    
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
    """

    MODACC_COMPOSITE_RESULTS_INCLUDE_DMRS = 9437240
    r"""Specifies whether the DMRS resource elements are included for composite EVM and magnitude and phase error results and
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
    """

    MODACC_COMPOSITE_RESULTS_INCLUDE_PTRS = 9437241
    r"""Specifies whether the PTRS resource elements are included for composite EVM and magnitude and phase error results and
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
    """

    MODACC_AVERAGING_ENABLED = 9453585
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
    """

    MODACC_AVERAGING_COUNT = 9453586
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    MODACC_AUTO_LEVEL_ALLOW_OVERFLOW = 9453719
    r"""Specifies whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
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
    """

    MODACC_SHORT_FRAME_ENABLED = 9453725
    r"""Specifies whether the input signal has a periodicity shorter than the NR frame duration.
    
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
    """

    MODACC_SHORT_FRAME_LENGTH = 9453726
    r"""Specifies the short frame periodicity in unit specified by
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT`.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.01.
    """

    MODACC_SHORT_FRAME_LENGTH_UNIT = 9453727
    r"""Specifies the units in which :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT` is specified.
    
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
    """

    MODACC_TRANSIENT_PERIOD_EVM_MODE = 9453731
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
    """

    MODACC_TRANSIENT_PERIOD = 9453732
    r"""It configures the transient duration as specified in section 6.4.2.1a of *3GPP 38.101-1* specification.
    
    If :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_TRANSIENT_PERIOD_EVM_MODE` is set to **Include**,
    configures the transient duration to calculate FFT window positions used to compute the transient EVM as specified in
    section 6.4.2.1a of *3GPP 38.101-1* specification.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **2us**.
    """

    MODACC_TRANSIENT_POWER_CHANGE_THRESHOLD = 9453733
    r"""Specifies transient period power change threshold level in dB.
    
    If a mean slot power has changed by more than this value from one slot to another, this slot boundary is
    handled as transient period. Note also that if RB mapping or modulation format has changed from one slot to another,
    this slot boundary is handled as transient period as well, even though the mean power has not changed.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **1**.
    """

    MODACC_ALL_TRACES_ENABLED = 9453587
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the ModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    MODACC_NUMBER_OF_ANALYSIS_THREADS = 9453588
    r"""Specifies the maximum number of threads used for parallelism for the ModAcc measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size,system resources,data
    availability,and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    MODACC_RESULTS_DETECTED_CELL_ID = 9453626
    r"""Returns the detected Cell ID, if the :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_CELL_ID_DETECTION_ENABLED`
    attribute is set to **True**. A value of **-1** is returned, if the measurement fails to auto detect the Cell ID.
    
    Returns the user configured Cell ID, if the Auto Cell ID Detection Enabled attribute is set to **False**.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_RMS_EVM_MEAN = 9453590
    r"""Returns the mean value of RMS EVMs calculated over measurement length.
    
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
    """

    MODACC_RESULTS_COMPOSITE_PEAK_EVM_MAXIMUM = 9453591
    r"""Returns the maximum value of peak EVMs calculated over measurement length.
    
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
    """

    MODACC_RESULTS_COMPOSITE_PEAK_EVM_BWP_INDEX = 9453652
    r"""Returns the bandwidth part index where ModAcc Results Max Pk Composite EVM occurs.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_PEAK_EVM_SLOT_INDEX = 9453596
    r"""Returns the slot index where ModAcc Results Max Pk Composite EVM occurs.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_PEAK_EVM_SYMBOL_INDEX = 9453597
    r"""Returns the symbol index where ModAcc Results Max Pk Composite EVM occurs.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_PEAK_EVM_SUBCARRIER_INDEX = 9453598
    r"""Returns the subcarrier index where ModAcc Results Max Pk Composite EVM occurs.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_RMS_MAGNITUDE_ERROR_MEAN = 9453592
    r"""Returns the RMS mean value of magnitude error calculated over measurement length on all configured channels.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_PEAK_MAGNITUDE_ERROR_MAXIMUM = 9453593
    r"""Returns the peak value of magnitude error calculated over measurement length on all configured channels.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_RMS_PHASE_ERROR_MEAN = 9453594
    r"""Returns the RMS mean value of Phase error calculated over measurement length on all configured channels. This value is
    expressed in degrees.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPOSITE_PEAK_PHASE_ERROR_MAXIMUM = 9453595
    r"""Returns the peak value of Phase error calculated over measurement length on all configured channels. This value is
    expressed in degrees.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SCH_SYMBOL_POWER_MEAN = 9453679
    r"""Returns the mean value (over :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`) of power calculated
    on OFDM symbols allocated only with the shared channel.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SCH_DETECTED_MODULATION_TYPE = 9453680
    r"""Returns the modulation of the shared channel user data if you set the
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
    """

    MODACC_RESULTS_PUSCH_DATA_RMS_EVM_MEAN = 9453599
    r"""Returns the mean value of RMS EVMs calculated over measurement length on PUSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_DATA_PEAK_EVM_MAXIMUM = 9453600
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PUSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_DMRS_RMS_EVM_MEAN = 9453603
    r"""Returns the mean value of RMS EVMs calculated over measurement length on PUSCH DMRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_DMRS_PEAK_EVM_MAXIMUM = 9453604
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PUSCH DMRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_PTRS_RMS_EVM_MEAN = 9453640
    r"""Returns the mean value of RMS EVMs calculated over measurement length on PUSCH PTRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_PTRS_PEAK_EVM_MAXIMUM = 9453641
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PUSCH PTRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/ bwp<*m*>/
    user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.
    """

    MODACC_RESULTS_PUSCH_DATA_RE_POWER_MEAN = 9453737
    r"""Returns the mean value (over Meas Length) of power calculated on PUSCH data REs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_DMRS_RE_POWER_MEAN = 9453738
    r"""Returns the mean value (over Meas Length) of power calculated on PUSCH DMRS REs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_PTRS_RE_POWER_MEAN = 9453739
    r"""Returns the mean value (over Meas Length) of power calculated on PUSCH PTRS REs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_DATA_TRANSIENT_RMS_EVM_MEAN = 9453734
    r"""Returns the mean value of RMS EVMs calulated over measurement interval for the PUSCH symbols where the transient
    occurs.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_PEAK_PHASE_OFFSET_MAXIMUM = 9453735
    r"""Returns the maximum value over Meas Length of peak phase offsets between the reference and measurement slots.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PUSCH_PEAK_PHASE_OFFSET_SLOT_INDEX = 9453736
    r"""Returns the slot index where ModAcc Results PUSCH Pk Phase Offset Max occurs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>/layer<*q*>" as the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_QPSK_RMS_EVM_MEAN = 9453653
    r"""Returns the mean value of RMS EVMs calculated over measurement length on all  QPSK modulated PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_16QAM_RMS_EVM_MEAN = 9453654
    r"""Returns the mean value of RMS EVMs calculated over measurement length on all  16 QAM modulated PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_64QAM_RMS_EVM_MEAN = 9453655
    r"""Returns the mean value of RMS EVMs calculated over measurement length on all  64 QAM modulated PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_256QAM_RMS_EVM_MEAN = 9453656
    r"""Returns the mean value of RMS EVMs calculated over measurement length on all  256 QAM modulated PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_1024QAM_RMS_EVM_MEAN = 9453683
    r"""Returns the mean value of RMS EVMs calculated over measurement length on all 1024 QAM modulated PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_8PSK_RMS_EVM_MEAN = 9453713
    r"""Returns the mean value of RMS EVMs calculated over measurement length on all 8 PSK modulated PDSCH data symbols.
    
    Use "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>/bwp<*m*>" as the `Selector
    String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_DATA_RMS_EVM_MEAN = 9453657
    r"""Returns the mean value of RMS EVMs calculated over measurement length on PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_DATA_PEAK_EVM_MAXIMUM = 9453658
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PDSCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_DMRS_RMS_EVM_MEAN = 9453659
    r"""Returns the mean value of RMS EVMs calculated over measurement length on PDSCH DMRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_DMRS_PEAK_EVM_MAXIMUM = 9453660
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PDSCH DMRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_PTRS_RMS_EVM_MEAN = 9453661
    r"""Returns the mean value of RMS EVMs calculated over measurement length on PDSCH PTRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_PTRS_PEAK_EVM_MAXIMUM = 9453662
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PDSCH PTRS.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_DATA_RE_POWER_MEAN = 9453740
    r"""Returns the mean value (over Meas Length) of power calculated on PDSCH data REs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_DMRS_RE_POWER_MEAN = 9453741
    r"""Returns the mean value (over Meas Length) of power calculated on PDSCH DMRS REs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PDSCH_PTRS_RE_POWER_MEAN = 9453742
    r"""Returns the mean value (over Meas Length) of power calculated on PDSCH PTRS REs.
    
    Use "user<*l*>" or "bwp<*m*>" or "carrier<*k*>" or "subblock<*n*>" or
    "subblock<*n*>/carrier<*k*>/bwp<*m*>/user<*l*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PSS_RMS_EVM_MEAN = 9453689
    r"""Returns the mean value of RMS EVMs computed over measurement length on PSS symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PSS_PEAK_EVM_MAXIMUM = 9453690
    r"""Returns the maximum value of peak EVMs calculated over measurement length on PSS symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SSS_RMS_EVM_MEAN = 9453691
    r"""Returns the mean value of RMS EVMs computed over measurement length on SSS symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SSS_PEAK_EVM_MAXIMUM = 9453692
    r"""Returns the maximum value of peak EVMs calculated over measurement length on SSS symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PBCH_DATA_RMS_EVM_MEAN = 9453693
    r"""Returns the mean value calculated over measurement length of RMS EVMs calculated on PBCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PBCH_DATA_PEAK_EVM_MAXIMUM = 9453694
    r"""Returns the maximum value calculated over measurement length of peak EVMs calculated on PBCH data symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PBCH_DMRS_RMS_EVM_MEAN = 9453695
    r"""Returns the mean value calculated over measurement length of RMS EVMs calculated on PBCH DMRS symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_PBCH_DMRS_PEAK_EVM_MAXIMUM = 9453696
    r"""Returns the maximum value calculated over measurement length of peak EVMs calculated on PBCH DMRS symbols.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_EVM_UNIT` attribute to **Percentage**, the
    measurement returns this result as a percentage. When you set the ModAcc EVM Unit attribute to **dB**, the measurement
    returns this result in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_IN_BAND_EMISSION_MARGIN = 9453607
    r"""Returns In-Band Emission Margin of the component carrier. This value is expressed in dB.
    
    Margin is the smallest difference between In-Band Emission measurement trace and limit trace. The limit is
    defined in section 6.4.2.3 and section 6.4F.2.3 of *3GPP 38.101-1* specification and section 6.4.2.3 of *3GPP 38.101-2*
    specification. In-Band emission is measured as the ratio of the power in non-allocated resource blocks to the power in
    the allocated resource blocks averaged over the measurement interval. For NR bands, the margin is not returned in case
    of clustered PUSCH allocation, or when there is full allocation of resource blocks. For NR unlicensed bands, the margin
    is returned only for RIV=1 and RIV=5 mentioned in the section 6.4F.2.3 of *3GPP 38.101-1* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_IN_BAND_EMISSION_MARGIN = 9453612
    r"""Returns In-Band Emission Margin of the subblock's aggregated bandwidth. This value is expressed in dB.
    
    Margin is the smallest difference between In-Band Emission measurement trace and the limit trace. The limit is
    defined in section 6.4A.2.2.2 of *3GPP 38.101-1* specification and section 6.4A.2.3 of *3GPP 38.101-2* specification.
    In-Band emission is measured as the ratio of the power in non-allocated resource blocks to the power in the allocated
    resource blocks averaged over the measurement interval. The margin is not returned in case of clustered PUSCH
    allocation, or when there is more than one active carrier, or when there is full allocation of resource blocks, or when
    carriers with different sub-carrier spacing are aggregated or when the number of carriers is greater than 2.
    
    Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_SLOT_INDEX = 9453704
    r"""Returns the slot index with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP
    38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2*.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE1_MINIMUM = 9453608
    r"""Returns the peak-to-peak ripple of the magnitude of EVM equalizer coefficients within Range1 for the measurement unit,
    that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
    specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE2_MINIMUM = 9453609
    r"""Returns the peak-to-peak ripple of the magnitude of EVM equalizer coefficients within Range2 for the Measurement unit,
    that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
    specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.  This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_TO_RANGE2_MINIMUM = 9453610
    r"""Returns the peak-to-peak ripple of the EVM equalizer coefficients from maximum in Range1 to minimum in Range2 for the
    Measurement unit that has the worst ripple margin among all four ripple results defined in 3section 6.4.2.4.1 of *3GPP
    38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_TO_RANGE1_MINIMUM = 9453611
    r"""Returns the peak-to-peak ripple of the EVM equalizer coefficients from maximum in Range2 to minimum in Range1 for the
    Measurement unit that has the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP
    38.101-1* specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM = 9453705
    r"""Returns the maximum magnitude of the EVM equalizer coefficients within Range1 for the measurement unit with the worst
    ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
    6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MINIMUM = 9453706
    r"""Returns the minimum magnitude of EVM equalizer coefficients within Range1 for the measurement unit with the worst
    ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
    6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM = 9453707
    r"""Returns the maximum magnitude of EVM equalizer coefficients within Range2 for the measurement unit with the worst
    ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
    6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MINIMUM = 9453708
    r"""Returns the minimum magnitude of EVM equalizer coefficients within Range2 for the measurement unit with the worst
    ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1* specification and section
    6.4.2.4.1 of *3GPP 38.101-2* specification. The value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MAXIMUM_SUBCARRIER_INDEX = 9453709
    r"""Returns the maximum subcarrier index magnitude of EVM equalizer coefficients within Range1 for the measurement unit
    with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
    specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE1_MINIMUM_SUBCARRIER_INDEX = 9453710
    r"""Returns the minimum subcarrier index magnitude of EVM equalizer coefficients within Range1 for the measurement unit
    with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
    specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MAXIMUM_SUBCARRIER_INDEX = 9453711
    r"""Returns the maximum subcarrier index magnitude of EVM equalizer coefficients within Range2 for the measurement unit
    with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
    specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SPECTRAL_FLATNESS_RANGE2_MINIMUM_SUBCARRIER_INDEX = 9453712
    r"""Returns the minimum subcarrier index magnitude of EVM equalizer coefficients within Range2 for the measurement unit
    with the worst ripple margin among all four ripple results defined in section 6.4.2.4.1 of *3GPP 38.101-1*
    specification and section 6.4.2.4.1 of *3GPP 38.101-2* specification.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_TIME_OFFSET_MEAN = 9453618
    r"""Returns the time difference between the detected slot or frame boundary depending on the sync mode and reference
    trigger location. This value is expressed in seconds.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/chain<*r*>"as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_FREQUENCY_ERROR_MEAN = 9453613
    r"""Returns the estimated carrier frequency offset averaged over measurement length. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_SLOT_FREQUENCY_ERROR_MAXIMUM = 9453729
    r"""Returns the estimated maximum per slot carrier frequency offset over the
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_SYMBOL_CLOCK_ERROR_MEAN = 9453619
    r"""Returns the estimated sample clock error averaged over measurement length. This value is expressed in ppm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_TIME_ALIGNMENT_ERROR_MEAN = 9453744
    r"""Returns the difference in the timing error, in seconds, of a CC with respect to the reference CC. The reference CC is
    fixed to Subblock0/ComponentCarrier0. The timing error reported is a frame timing error when the synchronization mode
    is set to 'Frame' and is slot timing error when the synchronization mode is set to 'Slot'.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_IQ_ORIGIN_OFFSET_MEAN = 9453614
    r"""Returns the estimated IQ origin offset averaged over measurement length.  This value is expressed in dBc.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_SLOT_IQ_ORIGIN_OFFSET_MAXIMUM = 9453730
    r"""Returns the estimated maximum per slot carrier IQ origin offset over the
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH`
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/layer<*q*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_IQ_GAIN_IMBALANCE_MEAN = 9453615
    r"""Returns the estimated IQ gain imbalance averaged over measurement length. This value is expressed in dB. IQ gain
    imbalance is the ratio of the amplitude of the I component to the Q component of the IQ signal being measured.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_QUADRATURE_ERROR_MEAN = 9453616
    r"""Returns the estimated quadrature error averaged over measurement length. This value is expressed in degrees. Quadrature
    error is the measure of skewness in degree of the I component with respect to the Q component of the IQ signal being
    measured.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_IQ_TIMING_SKEW_MEAN = 9453617
    r"""Returns the estimated IQ Timing Skew averaged over
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT`.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    IQ Timing skew is the difference between the group delay of the in-phase (I) and quadrature (Q) components of
    the signal. This value is expressed in seconds.
    """

    MODACC_RESULTS_COMPONENT_CARRIER_CROSS_POWER_MEAN = 9453743
    r"""Returns the cross power. The cross power for chain x is the power contribution from layers other than layer x in the
    chain. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" or
    "subblock<*n*>/carrier<*k*>/chain<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_LO_COMPONENT_CARRIER_INDEX = 9453666
    r"""Returns the index of the component carrier that includes the LO of the transmitter according to the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_FREQUENCY` and
    :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY` attributes. If the LO of the transmitter
    doesn't fall into any component carrier of the subblock, the attribute returns -1.  This result is valid only when you
    set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.
    
    Use "subblock<*n*>"or "subblock<*n*>/chain<*r*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_LO_SUBCARRIER_INDEX = 9453667
    r"""Returns the subcarrier index within the respective component carrier where the transmitter LO is located. Due to its
    dependence on :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_FREQUENCY` and
    :py:attr:`~nirfmxnr.attributes.AttributeID.SUBBLOCK_TRANSMIT_LO_FREQUENCY` properties, the value can be fractional, and
    the LO might reside in between subcarriers of a component carrier. This result is valid only when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE` attribute to **LO per Subblock**.
    
    Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>"   as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_SUBBLOCK_IQ_ORIGIN_OFFSET_MEAN = 9453622
    r"""Returns the estimated IQ origin offset averaged over measurement length in the subblock. This value is expressed in
    dBc. This result is valid only when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TRANSMITTER_ARCHITECTURE`
    attribute to **LO per Subblock**.
    
    Use "subblock<*n*>" or "subblock<*n*>/chain<*r*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    MODACC_RESULTS_NOISE_COMPENSATION_APPLIED = 9453718
    r"""Specifies whether the noise compensation is applied to the EVM measurement.
    
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
    """

    ACP_MEASUREMENT_ENABLED = 9441280
    r"""Specifies whether to enable the ACP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    ACP_CHANNEL_CONFIGURATION_TYPE = 9441357
    r"""Specifies the method to configure the carrier and the offset channel settings.
    
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
    """

    ACP_SUBBLOCK_INTEGRATION_BANDWIDTH = 9441282
    r"""Specifies the integration bandwidth of a subblock. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    Integration bandwidth is the span from the left edge of the leftmost carrier to the right edge of the rightmost
    carrier within the subblock. The default value is 9 MHz.
    """

    ACP_SUBBLOCK_OFFSET = 9441358
    r"""Specifies the offset of the subblock measurement relative to the subblock center. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    ACP_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH = 9441286
    r"""Specifies the integration bandwidth of the component carrier (CC). This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 9 MHz.
    """

    ACP_NUMBER_OF_UTRA_OFFSETS = 9441289
    r"""Specifies the number of universal terrestrial radio access (UTRA) adjacent channel offsets to be configured at offset
    positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to
    **Standard**  or  **NS_29**  or  **Standard Rel 16**  or  ** Standard Rel 18 **. For uplink ACP measurement in
    frequency range 2-1 and frequency range 2-2, and for downlink ACP measurement, the ACP Num UTRA Offsets has to be 0.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is dependent on 3GPP specification.
    """

    ACP_NUMBER_OF_EUTRA_OFFSETS = 9441290
    r"""Specifies the number of evolved universal terrestrial radio access (E-UTRA) adjacent channel offsets to be configured
    at offset positions when the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is
    set to **Standard** or **NS_29** or **Standard Rel 16** or **Standard Rel 18**. For uplink ACP measurement, and for
    downlink ACP measurement in frequency range 2-1 and frequency range 2-2, this attribute has to be 0.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is dependent on 3GPP specification.
    """

    ACP_NUMBER_OF_NR_OFFSETS = 9441291
    r"""Specifies the number of NR adjacent channel offsets to be configured at offset positions when the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
    **NS_29** or **Standard Rel 16** or **Standard Rel 18**.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is dependent on 3GPP specification.
    """

    ACP_NUMBER_OF_ENDC_OFFSETS = 9441347
    r"""Specifies the number of ENDC adjacent channel offsets to be configured at offset positions when the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Standard** or
    **NS_29** or **Standard Rel 16** or **Standard Rel 18**
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is dependent on 3GPP specification.
    """

    ACP_OFFSET_CHANNEL_SPACING_ADJUSTMENT = 9441349
    r"""Specifies the additional spacing of ACP offset channels at nominal spacing.
    
    It applies to UL single carrier (FR1), UL contiguous CA, and UL non-contiguous EN-DC signal configurations.
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is **0**.
    """

    ACP_NUMBER_OF_OFFSETS = 9441292
    r"""Specifies the number of configured offset channels when the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_CHANNEL_CONFIGURATION_TYPE` attribute is set to **Custom**
    
    Use "subblock<*n*>" as the selector string to configure or read this attribute.
    
    The default value is 1.
    """

    ACP_OFFSET_FREQUENCY = 9441294
    r"""Specifies the offset frequency of an offset channel. This value is expressed in Hz. The offset frequency is computed
    from the center of a reference component carrier/subblock to the center of the nearest RBW filter of the offset
    channel.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 10 MHz.
    """

    ACP_OFFSET_SIDEBAND = 9441295
    r"""Specifies the sideband measured for the offset channel.
    
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
    """

    ACP_OFFSET_INTEGRATION_BANDWIDTH = 9441298
    r"""Specifies the integration bandwidth of an offset channel. This value is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 9 MHz.
    """

    ACP_RBW_FILTER_AUTO_BANDWIDTH = 9441302
    r"""Specifies whether the measurement computes the RBW.
    
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
    """

    ACP_RBW_FILTER_BANDWIDTH = 9441303
    r"""Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH` attribute to **False**. This value is
    expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30 kHz.
    """

    ACP_RBW_FILTER_TYPE = 9441304
    r"""Specifies the shape of the RBW filter.
    
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
    """

    ACP_SWEEP_TIME_AUTO = 9441305
    r"""Specifies whether the measurement sets the sweep time.
    
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
    """

    ACP_SWEEP_TIME_INTERVAL = 9441306
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    ACP_POWER_UNITS = 9441307
    r"""Specifies the unit for absolute power.
    
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
    """

    ACP_MEASUREMENT_METHOD = 9441308
    r"""Specifies the method for performing the ACP measurement.
    
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
    """

    ACP_NOISE_CALIBRATION_MODE = 9441356
    r"""Specifies whether the noise calibration and measurement is performed manually by the user or automatically by RFmx.
    
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
    """

    ACP_NOISE_CALIBRATION_AVERAGING_AUTO = 9441355
    r"""Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.
    
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
    """

    ACP_NOISE_CALIBRATION_AVERAGING_COUNT = 9441354
    r"""Specifies the averaging count used for noise calibration when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 32.
    """

    ACP_NOISE_COMPENSATION_ENABLED = 9441309
    r"""Specifies whether RFmx compensates for the instrument noise when performing the measurement when you set
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
    """

    ACP_NOISE_COMPENSATION_TYPE = 9441353
    r"""Specifies the noise compensation type.
    
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
    """

    ACP_AVERAGING_ENABLED = 9441310
    r"""Specifies whether to enable averaging for the ACP measurement.
    
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
    """

    ACP_AVERAGING_COUNT = 9441311
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    ACP_AVERAGING_TYPE = 9441313
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for ACP
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
    """

    ACP_MEASUREMENT_MODE = 9441352
    r"""Specifies whether the measurement calibrates the noise floor of analyzer or performs the ACP measurement.
    
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
    """

    ACP_FFT_WINDOW = 9441314
    r"""Specifies the FFT window type to be used to reduce spectral leakage.
    
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
    """

    ACP_FFT_OVERLAP_MODE = 9441350
    r"""Specifies the overlap mode when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD`
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
    """

    ACP_FFT_OVERLAP = 9441351
    r"""Specifies the samples to overlap between the consecutive chunks as a percentage of the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT** and the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_OVERLAP_MODE` attribute to **User Defined**. This value is expressed
    as a percentage.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is 0.
    """

    ACP_IF_OUTPUT_POWER_OFFSET_AUTO = 9441316
    r"""Specifies whether the measurement computes an appropriate IF output power level offset for the offset channels to
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
    """

    ACP_NEAR_IF_OUTPUT_POWER_OFFSET = 9441317
    r"""Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are near the
    carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
    set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    ACP_FAR_IF_OUTPUT_POWER_OFFSET = 9441318
    r"""Specifies the offset that is needed to adjust the IF output power levels for the offset channels that are far from the
    carrier channel to improve the dynamic range. This value is expressed in dB. This attribute is applicable only when you
    set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_IF_OUTPUT_POWER_OFFSET_AUTO` attribute to **False** and
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Dynamic Range**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 20.
    """

    ACP_SEQUENTIAL_FFT_SIZE = 9441319
    r"""Specifies the number of bins to be used for FFT computation, when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Sequential FFT**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 512.
    """

    ACP_AMPLITUDE_CORRECTION_TYPE = 9441320
    r"""Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
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
    """

    ACP_ALL_TRACES_ENABLED = 9441321
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the ACP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    ACP_NUMBER_OF_ANALYSIS_THREADS = 9441322
    r"""Specifies the maximum number of threads used for parallelism for the ACP measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    ACP_RESULTS_TOTAL_AGGREGATED_POWER = 9441324
    r"""Returns the total power of all the subblocks. The power in each subblock is the sum of powers of all the frequency bins
    over the integration bandwidth of the subblocks. This value includes the power in the inter-carrier gaps within a
    subblock, but it does not include the power within the subblock gaps.
    
    The carrier power is reported in dBm when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
    Pwr Units attribute to **dBm/Hz**.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    """

    ACP_RESULTS_SUBBLOCK_POWER = 9441328
    r"""Returns the sum of powers of all the frequency bins over the integration bandwidth of the subblock. The carrier power
    is reported in dBm when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**,
    and in dBm/Hz when you set the ACP Pwr Units attribute to **dBm/Hz**.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_COMPONENT_CARRIER_ABSOLUTE_POWER = 9441331
    r"""Returns the power measured over the integration bandwidth of the component carrier. The carrier power is reported in
    dBm when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz
    when you set the ACP Pwr Units attribute to **dBm/Hz**.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_COMPONENT_CARRIER_RELATIVE_POWER = 9441332
    r"""Returns the component carrier power relative to its subblock power. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_LOWER_OFFSET_ABSOLUTE_POWER = 9441338
    r"""Returns the lower (negative) offset channel power. The carrier power is reported in dBm when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
    Pwr Units attribute to **dBm/Hz**.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_LOWER_OFFSET_RELATIVE_POWER = 9441339
    r"""Returns the power in lower (negative) offset channel relative to the total aggregated power. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_ABSOLUTE_POWER = 9441345
    r"""Returns the upper (positive) offset channel power. The carrier power is reported in dBm when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_POWER_UNITS` attribute to **dBm**, and in dBm/Hz when you set the ACP
    Pwr Units attribute to **dBm/Hz**.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    ACP_RESULTS_UPPER_OFFSET_RELATIVE_POWER = 9441346
    r"""Returns the power in the upper (positive) offset channel relative to the total aggregated power. This value is
    expressed in dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    CHP_MEASUREMENT_ENABLED = 9449472
    r"""Specifies whether to enable the channel power measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    CHP_SWEEP_TIME_AUTO = 9449474
    r"""Specifies whether the measurement sets the sweep time.
    
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
    """

    CHP_SWEEP_TIME_INTERVAL = 9449475
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_SWEEP_TIME_AUTO` attribute to
    False. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    CHP_INTEGRATION_BANDWIDTH_TYPE = 9449476
    r"""Specifies the integration bandwidth (IBW) type used to measure the power of the acquired signal. Integration bandwidth
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
    """

    CHP_SUBBLOCK_INTEGRATION_BANDWIDTH = 9449477
    r"""Specifies the integration bandwidth of the subblock. This value is expressed in Hz. It is the span from left edge of
    the integration bandwidth of the leftmost carrier to the right edge of the integration bandwidth of the rightmost
    carrier within a subblock.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.
    
    The default value is 0.
    """

    CHP_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH = 9449478
    r"""Specifies the integration bandwidth of a component carrier (CC). This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 9 MHz.
    """

    CHP_RBW_FILTER_AUTO_BANDWIDTH = 9449481
    r"""Specifies whether the measurement computes the RBW.
    
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
    """

    CHP_RBW_FILTER_BANDWIDTH = 9449482
    r"""Specifies the bandwidth of the RBW filter, used to sweep the acquired signal, when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_RBW_FILTER_AUTO_BANDWIDTH` attribute to  **False**. This value is
    expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30 kHz.
    """

    CHP_RBW_FILTER_TYPE = 9449483
    r"""Specifies the shape of the digital RBW filter.
    
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
    """

    CHP_NOISE_CALIBRATION_MODE = 9449510
    r"""Specifies whether the noise calibration and measurement is performed manually by the user or automatically by RFmx.
    
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
    """

    CHP_NOISE_CALIBRATION_AVERAGING_AUTO = 9449509
    r"""Specifies whether RFmx automatically computes the averaging count used for instrument noise calibration.
    
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
    """

    CHP_NOISE_CALIBRATION_AVERAGING_COUNT = 9449508
    r"""Specifies the averaging count used for noise calibration when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_AUTO` attribute to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 32.
    """

    CHP_NOISE_COMPENSATION_ENABLED = 9449506
    r"""Specifies whether RFmx compensates for the instrument noise when performing the measurement. To compensate for
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
    """

    CHP_NOISE_COMPENSATION_TYPE = 9449507
    r"""Specifies the noise compensation type.
    
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
    """

    CHP_AVERAGING_ENABLED = 9449485
    r"""Specifies whether to enable averaging for the CHP measurement.
    
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
    """

    CHP_AVERAGING_COUNT = 9449486
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    CHP_AVERAGING_TYPE = 9449488
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for CHP
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
    """

    CHP_MEASUREMENT_MODE = 9449505
    r"""Specifies whether the measurement calibrates the noise floor of analyzer or performs the CHP measurement.
    
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
    """

    CHP_FFT_WINDOW = 9449489
    r"""Specifies the FFT window type to be used to reduce spectral leakage.
    
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
    """

    CHP_AMPLITUDE_CORRECTION_TYPE = 9449490
    r"""Specifies whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
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
    """

    CHP_ALL_TRACES_ENABLED = 9449491
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the CHP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    CHP_NUMBER_OF_ANALYSIS_THREADS = 9449492
    r"""Specifies the maximum number of threads used for parallelism for the CHP measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    CHP_RESULTS_TOTAL_AGGREGATED_POWER = 9449494
    r"""Returns the total power of all the subblocks. This value is expressed in dBm. The power in each subblock is the sum of
    powers of all the frequency bins over the integration bandwidth of the subblocks. This value includes the power in the
    inter-carrier gaps within a subblock, but it does not include the power within the subblock gaps.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    """

    CHP_RESULTS_SUBBLOCK_POWER = 9449498
    r"""Returns the sum of powers of all the frequency bins over the integration bandwidth of the subblock. This includes the
    power in inter-carrier gaps within a subblock. This value is expressed in dBm.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    CHP_RESULTS_COMPONENT_CARRIER_ABSOLUTE_POWER = 9449501
    r"""Returns the power measured over the integration bandwidth of the component carrier. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    CHP_RESULTS_COMPONENT_CARRIER_RELATIVE_POWER = 9449503
    r"""Returns the component carrier power relative to its subblock power. This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OBW_MEASUREMENT_ENABLED = 9461760
    r"""Specifies whether to enable the OBW measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    OBW_POWER_INTEGRATION_METHOD = 9461792
    r"""Specifies if the OBW measurement window is centered around the center of the channel.
    
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
    """

    OBW_SPAN_AUTO = 9461786
    r"""Specifies whether the frequency range of the spectrum used for the OBW measurement is auto computed or configured by
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
    """

    OBW_SPAN = 9461763
    r"""Specifies the frequency range around the subblock center frequency, which is used to find the
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RESULTS_OCCUPIED_BANDWIDTH`. When
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SPAN_AUTO` is set to **False**, the configured span value is used by the
    measurement. This value is expressed in Hz.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 20 MHz.
    """

    OBW_RBW_FILTER_AUTO_BANDWIDTH = 9461766
    r"""Specifies whether the measurement computes the RBW.
    
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
    """

    OBW_RBW_FILTER_BANDWIDTH = 9461767
    r"""Specifies the bandwidth of the RBW filter used to sweep the acquired signal, when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_AUTO_BANDWIDTH` attribute to ** False**. This value is
    expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10 kHz.
    """

    OBW_RBW_FILTER_TYPE = 9461768
    r"""Specifies the shape of the digital RBW filter.
    
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
    """

    OBW_SWEEP_TIME_AUTO = 9461769
    r"""Specifies whether the measurement sets the sweep time.
    
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
    """

    OBW_SWEEP_TIME_INTERVAL = 9461770
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    OBW_AVERAGING_ENABLED = 9461771
    r"""Specifies whether to enable averaging for the OBW measurement.
    
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
    """

    OBW_AVERAGING_COUNT = 9461772
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    OBW_AVERAGING_TYPE = 9461774
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for the OBW
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
    """

    OBW_FFT_WINDOW = 9461775
    r"""Specifies the FFT window type to be used to reduce spectral leakage.
    
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
    """

    OBW_AMPLITUDE_CORRECTION_TYPE = 9461777
    r"""Specifies whether the amplitude of frequency bins in the spectrum used by the measurement is corrected for external
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
    """

    OBW_ALL_TRACES_ENABLED = 9461778
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the OBW measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    OBW_NUMBER_OF_ANALYSIS_THREADS = 9461779
    r"""Specifies the maximum number of threads used for parallelism for the OBW measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OBW_RESULTS_OCCUPIED_BANDWIDTH = 9461781
    r"""Returns the bandwidth that occupies the specified percentage of the total power of the signal. This value is expressed
    in Hz. The occupied bandwidth is calculated using the following equation:
    
    *Occupied bandwidth* = *Stop frequency* - *Start frequency*
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OBW_RESULTS_ABSOLUTE_POWER = 9461782
    r"""Returns the total power measured in the spectrum acquired by the measurement. This value is expressed in dBm.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OBW_RESULTS_START_FREQUENCY = 9461783
    r"""Returns the start frequency of the occupied bandwidth of carrier/subblock. This value is expressed in Hz. The occupied
    bandwidth is calculated using the following equation:
    
    *Occupied bandwidth* = *Stop frequency* - *Start frequency*
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OBW_RESULTS_STOP_FREQUENCY = 9461784
    r"""Returns the stop frequency of the occupied bandwidth of carrier/subblock. This value is expressed in Hz. Occupied
    bandwidth is calculated using the following equation:
    
    *Occupied bandwidth* = *Stop frequency* - *Start frequency*
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_MEASUREMENT_ENABLED = 9469952
    r"""Specifies whether to enable the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal and result
    instances. Refer to the Selector String topic for information about the string syntax for named signals and named
    results.
    
    The default value is FALSE.
    """

    SEM_UPLINK_MASK_TYPE = 9469954
    r"""Specifies the spectrum emission mask used in the measurement for uplink.
    
    You must set the mask type to **Custom** to configure the custom offset masks. Refer to section 6.5.2 of the
    *3GPP 38.101* specification for more information about standard-defined mask types.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **General**.
    
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)              | Description                                                                                                              |
    +===========================+==========================================================================================================================+
    | General (0)               | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.2-1 in section 6.5.2 of the  |
    |                           | 3GPP TS 38.101-1 specification, Table 6.5.2.1-1 and 6.5A.2.1-1 in section 6.5.2 of the 3GPP TS 38.101-2 specification    |
    |                           | and Table 6.5B.2.1.1-1 in section 6.5B of the 3GPP TS 38.101-3 specification. In case of non-contiguous EN-DC            |
    |                           | consisting of at least one subblock with all E-UTRA carriers, for the E-UTRA subblock, the measurement selects the       |
    |                           | offset frequencies and limits for the SEM, as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2, 6.6.2.1A.1.5-1, and             |
    |                           | 6.6.2.1A.1.5-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                                   |
    |                           | If the band value is set to 46 or 96 or 102, the measurement selects the offset frequencies and limits for SEM as        |
    |                           | defined in Table 6.5F.2.2-1 in section 6.5F.2 of the 3GPP TS 38.101-1 Specification.                                     |
    |                           | If the band value is set to NTN bands 254, 255 or 256, the measurement selects the offset frequencies and limits for     |
    |                           | SEM as defined in Table 6.5.2.2.1 in section 6.5.2 of the 3GPP 38.101-5 specification.                                   |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_35 (1)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.1-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification and Table 6.5B.2.1.2.1-1 in section 6.5B of the 3GPP TS 38.101-3 specification. In    |
    |                           | case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA carriers, for the E-UTRA subblock, the  |
    |                           | measurement selects the offset frequencies and limits for the SEM, as defined in Table 6.6.2.2.5.5-1 in section 6.6.2    |
    |                           | of the 3GPP TS 36.521-1 specification.                                                                                   |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Custom (2)                | You need to configure the SEM Num Offsets, SEM Offset Start Freq, SEM Offset Stop Freq,                                  |
    |                           | SEM Offset Abs Limit Start, SEM Offset Abs Limit Stop, SEM Offset Sideband, SEM Offset RBW, SEM Offset RBW Filter Type,  |
    |                           | and SEM Offset BW Integral attributes for each offset.                                                                   |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_03 (3)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.3-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification. In case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA  |
    |                           | carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in  |
    |                           | Table 6.6.2.2.5.1-1 and 6.6.2.2.5.1-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                            |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_04 (4)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.2-3 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification. Subcarrier spacing can be configured through BWP Subcarrier Spacing attribute.       |
    |                           | Subcarrier spacing corresponding to first bandwidth part is used for computing mask. Transform precoding can be          |
    |                           | configured through PUSCH Transform Precoding Enabled attribute. Transform precoding corresponding to first bandwidth     |
    |                           | part is used for computing mask. In case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA     |
    |                           | carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in  |
    |                           | Table 6.6.2.2.3.2-3 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                                              |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_06 (5)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.4-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification. In case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA  |
    |                           | carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in  |
    |                           | Table 6.6.2.2.5.3-1 and 6.6.2.2.5.3-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                            |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_21 (6)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.3-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification. In case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA  |
    |                           | carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in  |
    |                           | Table 6.6.2.2.5.1-1 and 6.6.2.2.5.1-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                            |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_27 (7)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.8-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification. In case of intra-band contiguous CA consisting of at least one subblock with all NR  |
    |                           | carriers, for the NR subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in      |
    |                           | Table 6.2A.2.3.2.1-1 in section 6.5A.2.3 of the 3GPP TS 38.101-1 specification. In case of non-contiguous EN-DC          |
    |                           | consisting of at least one subblock with all E-UTRA carriers, for the E-UTRA subblock, the measurement selects the       |
    |                           | offset frequencies and limits for the SEM, as defined in Table 6.6.2.2.3.4-1 in section 6.6.2 of the 3GPP TS 36.521-1    |
    |                           | specification.                                                                                                           |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_07 (8)                 | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.4-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification. In case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA  |
    |                           | carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in  |
    |                           | Table 6.6.2.2.5.3-1 and Table 6.6.2.2.5.3-2 in section 6.6.2 of the 3GPP TS 36.521-1 specification.                      |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_03U (9)                | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.3-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification.                                                                                      |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_21 Rel 17 Onwards (10) | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.9-1 in section 6.5.2 of    |
    |                           | the 3GPP TS 38.101-1 specification.                                                                                      |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_04N (11)               | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.1-1 in section 6.5.2.3 of  |
    |                           | the                                                                                                                      |
    |                           | 3GPP TS 38.101-5 specification.                                                                                          |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | NS_05N (12)               | The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.2-1 in section 6.5.2.3 of  |
    |                           | the                                                                                                                      |
    |                           | 3GPP TS 38.101-5 specification.                                                                                          |
    +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_DOWNLINK_MASK_TYPE = 9470008
    r"""Specifies the limits to be used in the measurement for Downlink.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Standard**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | Standard (0) | The measurement selects the offset frequencies and limits for SEM, as defined in Table 6.6.4.2.1-1, Table 6.6.4.2.1-2,   |
    |              | Table 6.6.4.2.2.1-1, Table 6.6.4.2.2.1-2, Table 6.6.4.2.2.2-1, Table 6.6.4.2.3-1, Table 6.6.4.2.3-2, and Table           |
    |              | 6.6.4.2.4-1 in section 6.6.4 and Table 9.7.4.3.2-1, 9.7.4.3.2-2, 9.7.4.3.3-1 and 9.7.4.3.3-2 in section 9.7.4 of the     |
    |              | 3GPP TS 38.104 Specification.                                                                                            |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Custom (2)   | Specifies that limits are applied based on user-defined offset segments.                                                 |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_DELTA_F_MAXIMUM = 9470009
    r"""Specifies the stop frequency for 3rd offset segment to be used in the measurement. This attribute is valid only for
    downlink and when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_DOWNLINK_MASK_TYPE` attribute to
    **Standard**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 15 MHz. The minimum value is 9.5 MHz.
    """

    SEM_SUBBLOCK_INTEGRATION_BANDWIDTH = 9469955
    r"""Returns the integration bandwidth of a subblock. This value is expressed in Hz. Integration bandwidth is the span from
    the left edge of the leftmost carrier to the right edge of the rightmost carrier within the subblock.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    SEM_SUBBLOCK_AGGREGATED_CHANNEL_BANDWIDTH = 9469956
    r"""Returns the aggregated channel bandwidth of a configured subblock. This value is expressed in Hz. The aggregated
    channel bandwidth is the sum of the subblock integration bandwidth and the guard bands on either side of the subblock
    integration bandwidth.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    SEM_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH = 9469957
    r"""Returns the integration bandwidth of a component carrier. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 9 MHz.
    """

    SEM_COMPONENT_CARRIER_RATED_OUTPUT_POWER = 9470010
    r"""Specifies the rated output power (P\ :sub:`rated, x`\), which is used only to choose the limit table for medium range
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
    """

    SEM_NUMBER_OF_OFFSETS = 9469958
    r"""Specifies the number of SEM offset segments.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    SEM_OFFSET_START_FREQUENCY = 9469959
    r"""Specifies the start frequency of an offset segment. Refer to the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_FREQUENCY_DEFINITION` attribute for more details.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    SEM_OFFSET_STOP_FREQUENCY = 9469960
    r"""Specifies the stop frequency of an offset segment. Refer to the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_FREQUENCY_DEFINITION` attribute for more details.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1 MHz.
    """

    SEM_OFFSET_SIDEBAND = 9469961
    r"""Specifies whether the offset segment is present either on one side or on both sides of a carrier.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
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
    """

    SEM_OFFSET_RBW_FILTER_BANDWIDTH = 9469962
    r"""Specifies the bandwidth of the resolution bandwidth (RBW) filter used to sweep the acquired offset segment, when you
    set the SEM Offset RBW Auto attribute to **False**. This value is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 30000 Hz.
    """

    SEM_OFFSET_RBW_FILTER_TYPE = 9469963
    r"""Specifies the shape of a digital RBW filter.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **Gaussian**.
    
    +---------------+-----------------------------------------+
    | Name (Value)  | Description                             |
    +===============+=========================================+
    | FFT Based (0) | No RBW filtering is performed.          |
    +---------------+-----------------------------------------+
    | Gaussian (1)  | The RBW filter has a Gaussian response. |
    +---------------+-----------------------------------------+
    | Flat (2)      | The RBW filter has a flat response.     |
    +---------------+-----------------------------------------+
    """

    SEM_OFFSET_BANDWIDTH_INTEGRAL = 9469964
    r"""Specifies the resolution of a spectrum to compare with the spectral mask limits as an integer multiple of the RBW.
    
    When you set this attribute to a value greater than 1, the measurement acquires the spectrum with a narrow
    resolution and then processes it digitally to get a wider resolution that is equal to the product of a bandwidth
    integral and a RBW.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 1.
    """

    SEM_OFFSET_LIMIT_FAIL_MASK = 9469965
    r"""Specifies the criteria to determine the measurement fail status.
    
    The default value is **Absolute**.
    
    +-----------------+----------------------------------------------------------------------------------------------------------------+
    | Name (Value)    | Description                                                                                                    |
    +=================+================================================================================================================+
    | Abs AND Rel (0) | Specifies that the measurement fails if the power in the segment exceeds both the absolute and relative masks. |
    +-----------------+----------------------------------------------------------------------------------------------------------------+
    | Abs OR Rel (1)  | Specifies that the measurement fails if the power in the segment exceeds either the absolute or relative mask. |
    +-----------------+----------------------------------------------------------------------------------------------------------------+
    | Absolute (2)    | Specifies that the measurement fails if the power in the segment exceeds the absolute mask.                    |
    +-----------------+----------------------------------------------------------------------------------------------------------------+
    | Relative (3)    | Specifies that the measurement fails if the power in the segment exceeds the relative mask.                    |
    +-----------------+----------------------------------------------------------------------------------------------------------------+
    """

    SEM_OFFSET_FREQUENCY_DEFINITION = 9470018
    r"""Specifies the definition of the the start frequency and stop frequency of the offset segments.
    
    If this attribute is not configured, the following values are used based on other configurations - Carrier Edge
    to Meas BW Center for a single-carrier configuration, Subblock Edge to Meas BW Center for a multi-carrier
    configuration, and Carrier Center to Meas BW Center for a single-carrier configuration in the bands n46, n96, and n102
    as defined in the 3GPP TS 37.213 for the shared spectrum channel access.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)                         | Description                                                                                                              |
    +======================================+==========================================================================================================================+
    | Carrier Center to Meas BW Center (0) | The start frequency and stop frequency are defined from the center of the closest carrier channel bandwidth to the       |
    |                                      | center of the offset segment measurement bandwidth.                                                                      |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Carrier Edge to Meas BW Center (2)   | The start frequency and stop frequency are defined from the nearest edge of the closest carrier channel bandwidth to     |
    |                                      | the center of the offset segment measurement bandwidth.                                                                  |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Subblock Edge to Meas BW Center (6)  | The start frequency and stop frequency are defined from the subblock edge of the closest subblock bandwidth to the       |
    |                                      | center of the offset segment measurement bandwidth.                                                                      |
    +--------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_OFFSET_ABSOLUTE_LIMIT_START = 9469966
    r"""Specifies the absolute power limit corresponding to the beginning of an offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is -21.
    """

    SEM_OFFSET_ABSOLUTE_LIMIT_STOP = 9469967
    r"""Specifies the absolute power limit corresponding to the end of an offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is -21.
    """

    SEM_OFFSET_RELATIVE_LIMIT_START = 9469968
    r"""Specifies the relative power limit corresponding to the beginning of the offset segment. This value is expressed in dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is -53.
    """

    SEM_OFFSET_RELATIVE_LIMIT_STOP = 9469969
    r"""Specifies the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is -60.
    """

    SEM_SWEEP_TIME_AUTO = 9469970
    r"""Specifies whether the measurement sets the sweep time.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                           |
    +==============+=======================================================================================+
    | False (0)    | The measurement uses the sweep time that you specify in the SEM Sweep Time attribute. |
    +--------------+---------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses a sweep time of 1 ms.                                            |
    +--------------+---------------------------------------------------------------------------------------+
    """

    SEM_SWEEP_TIME_INTERVAL = 9469971
    r"""Specifies the sweep time when you set the :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_SWEEP_TIME_AUTO` attribute to
    **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    SEM_AVERAGING_ENABLED = 9469972
    r"""Specifies whether to enable averaging for the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The SEM measurement uses the value of the SEM Averaging Count attribute as the number of acquisitions over which the     |
    |              | SEM measurement is averaged.                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_AVERAGING_COUNT = 9469973
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    SEM_AVERAGING_TYPE = 9469974
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for SEM
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
    """

    SEM_FFT_WINDOW = 9470016
    r"""Specifies the FFT window type to be used to reduce spectral leakage.
    
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
    """

    SEM_AMPLITUDE_CORRECTION_TYPE = 9469975
    r"""Specifies whether the amplitude of the frequency bins, used in measurements, is corrected for external attenuation at
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
    """

    SEM_ALL_TRACES_ENABLED = 9469976
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SEM_NUMBER_OF_ANALYSIS_THREADS = 9469977
    r"""Specifies the maximum number of threads used for parallelism for the SEM measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    SEM_RESULTS_TOTAL_AGGREGATED_POWER = 9469979
    r"""Returns the sum of powers of all the subblocks. This value includes the power in the inter-carrier gap within a
    subblock, but it excludes power in the  inter-subblock gaps. This value is expressed in dBm.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    """

    SEM_RESULTS_MEASUREMENT_STATUS = 9469980
    r"""Returns the overall measurement status based on the standard mask type that you configure in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    SEM_RESULTS_SUBBLOCK_POWER = 9469983
    r"""Returns the power measured over the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is
    expressed in dBm.
    
    Use "subblock<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_ABSOLUTE_INTEGRATED_POWER = 9469984
    r"""Returns the power measured over the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_COMPONENT_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is
    expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_RELATIVE_INTEGRATED_POWER = 9469985
    r"""Returns the component carrier power relative to :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_SUBBLOCK_POWER`.
    This value is expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_ABSOLUTE_PEAK_POWER = 9469986
    r"""Returns the peak power in the component carrier. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_COMPONENT_CARRIER_PEAK_FREQUENCY = 9469987
    r"""Returns the frequency at which peak power occurs in the component carrier. This value is expressed in Hz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MEASUREMENT_STATUS = 9469988
    r"""Returns the measurement status based on the spectrum emission limits defined by the standard mask type that you
    configure in the :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_INTEGRATED_POWER = 9469989
    r"""Returns the lower (negative) offset segment power. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_RELATIVE_INTEGRATED_POWER = 9469990
    r"""Returns the power in the lower (negative) offset segment relative to
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_PEAK_POWER = 9469991
    r"""Returns the peak power in the lower (negative) offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_RELATIVE_PEAK_POWER = 9469992
    r"""Returns the peak power in the lower (negative) offset segment relative to
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_PEAK_FREQUENCY = 9469993
    r"""Returns the frequency at which the peak power occurs in the lower (negative) offset segment. This value is expressed in
    Hz.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN = 9469994
    r"""Returns the margin from the absolute limit mask for lower (negative) offset. Margin is defined as the minimum
    difference between the spectrum and the limit mask. This value is expressed in dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_ABSOLUTE_POWER = 9469995
    r"""Returns the power at which the Margin occurs in the lower (negative) offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_RELATIVE_POWER = 9469996
    r"""Returns the power at which the Margin occurs in the lower (negative) offset segment relative to
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_FREQUENCY = 9469997
    r"""Returns the frequency at which the Margin occurs in the lower (negative) offset. This value is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MEASUREMENT_STATUS = 9469998
    r"""Returns the measurement status based on the user-configured standard measurement limits. Spectrum emission limits can
    be defined by setting :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_UPLINK_MASK_TYPE` attribute.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_INTEGRATED_POWER = 9469999
    r"""Returns the upper (positive) offset segment power. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_RELATIVE_INTEGRATED_POWER = 9470000
    r"""Returns the power in the upper (positive) offset segment relative to
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the selector string to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_PEAK_POWER = 9470001
    r"""Returns the peak power in the upper (positive) offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_RELATIVE_PEAK_POWER = 9470002
    r"""Returns the peak power in the upper (positive) offset segment relative to
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_PEAK_FREQUENCY = 9470003
    r"""Returns the frequency at which the peak power occurs in the upper (positive)offset segment. This value is expressed in
    Hz.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN = 9470004
    r"""Returns the margin from the absolute limit mask for upper (positive) offset. Margin is defined as the minimum
    difference between the spectrum and the limit mask. This value is expressed in dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_ABSOLUTE_POWER = 9470005
    r"""Returns the power at which the Margin occurs in the upper (positive) offset segment. This value is expressed in dBm.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_RELATIVE_POWER = 9470006
    r"""Returns the power at which the Margin occurs in the upper (positive) offset segment relative to
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_RESULTS_TOTAL_AGGREGATED_POWER` attribute. This value is expressed in
    dB.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_FREQUENCY = 9470007
    r"""Returns the frequency at which the Margin occurs in the upper (positive) offset. This value is expressed in Hz.
    
    Use "offset<*k*>" or "subblock<*n*>" or "subblock<*n*>/offset<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    TXP_MEASUREMENT_ENABLED = 9465856
    r"""Specifies whether to enable the TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is False.
    """

    TXP_MEASUREMENT_OFFSET = 9465858
    r"""Specifies the measurement offset to skip from the start of acquired waveform for TXP measurement. This value is
    expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    TXP_MEASUREMENT_INTERVAL = 9465859
    r"""Specifies the measurement interval. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 ms.
    """

    TXP_AVERAGING_ENABLED = 9465860
    r"""Specifies whether to enable averaging for TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                     |
    +==============+=================================================================================================================+
    | False (0)    | The number of acquisitions is 1.                                                                                |
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the Averaging Count for the number of acquisitions over which the measurement is averaged. |
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    """

    TXP_AVERAGING_COUNT = 9465861
    r"""Specifies the number of acquisitions used for averaging when
    :py:attr:`~nirfmxnr.attributes.AttributeID.TXP_AVERAGING_ENABLED` is **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    TXP_ALL_TRACES_ENABLED = 9465863
    r"""Enables the traces to be stored and retrieved after the TXP measurement is performed.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is False.
    """

    TXP_NUMBER_OF_ANALYSIS_THREADS = 9465864
    r"""Specifies the maximum number of threads used for parallelism inside TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The number of threads must range from 1 to the number of physical cores. The default value is 1.
    
    The number of threads set used in calculations is not guaranteed. The actual number of threads used depends on
    the problem size, system resources, data availability, and other considerations.
    """

    TXP_RESULTS_AVERAGE_POWER_MEAN = 9465866
    r"""Returns the average power of the acquired signal.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
    returns the max of the peak power computed for each averaging count.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **dBm**.
    """

    TXP_RESULTS_PEAK_POWER_MAXIMUM = 9465867
    r"""Returns the peak power of the acquired signal.
    
    When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
    returns the mean of the average power computed for each averaging count.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **dBm**.
    """

    PVT_MEASUREMENT_ENABLED = 9474048
    r"""Specifies whether to enable the PVT measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    PVT_MEASUREMENT_INTERVAL_AUTO = 9474068
    r"""Specifies whether the measurement interval is computed by the measurement or configured by the user through
    :py:attr:`~nirfmxnr.attributes.AttributeID.PVT_MEASUREMENT_INTERVAL` attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    Setting this attribute to **FALSE** is supported for downlink only. The default value is **True**. Refer to
    measurement guidelines details in the `NR Power Vs Time
    <https://www.ni.com/docs/en-US/bundle/rfmx-nr/page/nr-power-vs-time.html>`_ concept help for more information.
    
    +--------------+------------------------------------------------------------------------+
    | Name (Value) | Description                                                            |
    +==============+========================================================================+
    | False (0)    | Measurement Interval is defined by the Measurement Interval attribute. |
    +--------------+------------------------------------------------------------------------+
    | True (1)     | Measurement Inteval is computed by the measurement.                    |
    +--------------+------------------------------------------------------------------------+
    """

    PVT_MEASUREMENT_INTERVAL = 9474069
    r"""Specifies the measurement interval when the :py:attr:`~nirfmxnr.attributes.AttributeID.PVT_MEASUREMENT_INTERVAL_AUTO`
    attribute is set to **False**. This value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10 ms.
    """

    PVT_MEASUREMENT_METHOD = 9474050
    r"""Specifies the PVT measurement method.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Normal**.
    
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)      | Description                                                                                                              |
    +===================+==========================================================================================================================+
    | Normal (0)        | The measurement is performed using a single acquisition. Use this method when a high dynamic range is not required.      |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Dynamic Range (1) | The measurement is performed using two acquisitions. Use this method when a higher dynamic range is desirable over the   |
    |                   | measurement speed.                                                                                                       |
    +-------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    PVT_AVERAGING_ENABLED = 9474051
    r"""Specifies whether to enable averaging for the power versus time (PVT) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the value of the PVT Averaging Count attribute as the number of acquisitions over which the PVT     |
    |              | measurement is averaged.                                                                                                 |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    PVT_AVERAGING_COUNT = 9474052
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PVT_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    PVT_AVERAGING_TYPE = 9474053
    r"""Specifies the measurement averaging type.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **RMS**.
    
    +--------------+--------------------------------------------------------+
    | Name (Value) | Description                                            |
    +==============+========================================================+
    | RMS (0)      | The power spectrum is linearly averaged.               |
    +--------------+--------------------------------------------------------+
    | Log (1)      | The power spectrum is averaged in a logarithmic scale. |
    +--------------+--------------------------------------------------------+
    """

    PVT_OFF_POWER_EXCLUSION_BEFORE = 9474055
    r"""Specifies the time excluded from the OFF region before the burst and at the beginning for uplink and downlink,
    respectively. The value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. Refer to measurement guidelines details in the `NR Power Vs Time
    <https://www.ni.com/docs/en-US/bundle/rfmx-nr/page/nr-power-vs-time.html>`_ concept help for more information.
    """

    PVT_OFF_POWER_EXCLUSION_AFTER = 9474056
    r"""Specifies the time excluded from the OFF region after the burst and at the end for uplink and downlink, respectively.
    The value is expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0. Refer to measurement guidelines details in the `NR Power Vs Time
    <https://www.ni.com/docs/en-US/bundle/rfmx-nr/page/nr-power-vs-time.html>`_ concept help for more information.
    """

    PVT_ALL_TRACES_ENABLED = 9474057
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the power versus time (PVT)
    measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    PVT_NUMBER_OF_ANALYSIS_THREADS = 9474059
    r"""Specifies the maximum number of threads used for parallelism inside the PVT measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    PVT_RESULTS_MEASUREMENT_STATUS = 9474060
    r"""Returns the measurement status indicating whether the off power before and after is within the standard defined limit.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this attribute.
    
    The default value is 0.
    
    +--------------+--------------------------------------------+
    | Name (Value) | Description                                |
    +==============+============================================+
    | Fail (0)     | Indicates that the measurement has failed. |
    +--------------+--------------------------------------------+
    | Pass (1)     | Indicates that the measurement has passed. |
    +--------------+--------------------------------------------+
    """

    PVT_RESULTS_ABSOLUTE_OFF_POWER_BEFORE = 9474061
    r"""Returns the OFF power in the segment before the captured burst for the uplink direction, while it returns NaN in the
    segment after the captured burst for the downlink direction. The segment is defined as one slot prior to a short
    transient segment and the burst.
    
    This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    PVT_RESULTS_ABSOLUTE_OFF_POWER_AFTER = 9474062
    r"""Returns the OFF power in the segment after the captured burst for the uplink direction, while it returns NaN in the
    segment after the captured burst for the downlink direction. The segment is defined as one slot after the burst and a
    short transient segment. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    PVT_RESULTS_ABSOLUTE_ON_POWER = 9474063
    r"""Returns the average ON power within the measurement interval. This value is expressed in dBm.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    PVT_RESULTS_BURST_WIDTH = 9474064
    r"""Returns the width of the captured burst for the uplink direction, while it returns NaN of the captured burst for the
    downlink direction. This value is expressed in seconds.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    PVT_RESULTS_PEAK_WINDOWED_OFF_POWER = 9474070
    r"""Returns the NaN for the uplink direction, while it returns the peak power value of 70/N us windowed power during all
    OFF regions in the measurement interval. This value is expressed in dBm/MHz.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    
    The default value is 0.
    """

    PVT_RESULTS_PEAK_WINDOWED_OFF_POWER_MARGIN = 9474071
    r"""Returns the NaN for the uplink direction, while it returns the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PVT_RESULTS_PEAK_WINDOWED_OFF_POWER` to the 3GPP limit. This value is
    expressed in dB.
    
    Use "carrier<*k*>" or "subblock<*n*>" or "subblock<*n*>/carrier<*k*>"  as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    PVT_RESULTS_PEAK_WINDOWED_OFF_POWER_TIME = 9474072
    r"""Returns the NaN for the uplink direction, while it returns the time offset of the
    :py:attr:`~nirfmxnr.attributes.AttributeID.PVT_RESULTS_PEAK_WINDOWED_OFF_POWER`. This value is expressed in seconds.
    """

    ACQUISITION_BANDWIDTH_OPTIMIZATION_ENABLED = 9490433
    r"""Specifies whether RFmx optimizes the acquisition bandwidth. This may cause acquisition center frequency or local
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
    """

    TRANSMITTER_ARCHITECTURE = 9438267
    r"""Specifies the RF architecture at the transmitter, whether each component carriers have a separate LO or one common LO
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
    """

    PHASE_COMPENSATION = 9438269
    r"""Specifies whether phase compensation is disabled, auto-set by the measurement or set by the you.
    
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
    """

    REFERENCE_GRID_ALIGNMENT_MODE = 9437239
    r"""Specifies whether to align the bandwidthparts and the SSB in a component carrier to a reference resource grid
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
    """

    GRID_SIZE_MODE = 9437468
    r"""Specifies whether to set the grid size of all BWPs and SSB in a component carrier automatically or manually.
    
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
    """

    LIMITED_CONFIGURATION_CHANGE = 9490434
    r"""Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.
    
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
    """

    RESULT_FETCH_TIMEOUT = 9486336
    r"""Specifies the time to wait before results are available in the RFmxNR Attribute. This value is expressed in seconds.
    
    Set this value to a time longer than expected for fetching the measurement. A value of -1 specifies that the
    RFmx Attribute waits until the measurement is complete.
    
    The default value is 10.
    """
