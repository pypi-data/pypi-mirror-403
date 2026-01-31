"""enums.py - Contains enum classes."""

from enum import Enum, IntFlag


class TriggerType(Enum):
    """TriggerType."""

    NONE = 0
    r"""No Reference Trigger is configured."""

    DIGITAL_EDGE = 1
    r"""The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified
    using the :py:attr:`~nirfmxnr.attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE` attribute."""

    IQ_POWER_EDGE = 2
    r"""The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),
    which is configured using the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute."""

    SOFTWARE = 3
    r"""The Reference Trigger is not asserted until a software trigger occurs."""


class DigitalEdgeTriggerEdge(Enum):
    """DigitalEdgeTriggerEdge."""

    RISING_EDGE = 0
    r"""The trigger asserts on the rising edge of the signal."""

    FALLING_EDGE = 1
    r"""The trigger asserts on the falling edge of the signal."""


class IQPowerEdgeTriggerLevelType(Enum):
    """IQPowerEdgeTriggerLevelType."""

    RELATIVE = 0
    r"""The IQ Power Edge Level attribute is relative to the value of the
    :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute."""

    ABSOLUTE = 1
    r"""The IQ Power Edge Level attribute specifies the absolute power."""


class IQPowerEdgeTriggerSlope(Enum):
    """IQPowerEdgeTriggerSlope."""

    RISING_SLOPE = 0
    r"""The trigger asserts when the signal power is rising."""

    FALLING_SLOPE = 1
    r"""The trigger asserts when the signal power is falling."""


class TriggerMinimumQuietTimeMode(Enum):
    """TriggerMinimumQuietTimeMode."""

    MANUAL = 0
    r"""The minimum quiet time for triggering is the value of the
    :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION` attribute."""

    AUTO = 1
    r"""The measurement computes the minimum quiet time used for triggering."""


class LinkDirection(Enum):
    """LinkDirection."""

    DOWNLINK = 0
    r"""NR measurement uses 3GPP NR downlink specification to measure the received signal."""

    UPLINK = 1
    r"""NR measurement uses 3GPP NR uplink specification to measure the received signal."""


class gNodeBCategory(Enum):
    """gNodeBCategory."""

    WIDE_AREA_BASE_STATION_CATEGORY_A = 0
    r"""Specifies that the gNodeB type is Wide Area Base Station - Category A."""

    WIDE_AREA_BASE_STATION_CATEGORY_B_OPTION1 = 1
    r"""Specifies that the gNodeB type is Wide Area Base Station - Category B Option1."""

    WIDE_AREA_BASE_STATION_CATEGORY_B_OPTION2 = 2
    r"""Specifies that the gNodeB type is Wide Area Base Station - Category B Option2."""

    LOCAL_AREA_BASE_STATION = 3
    r"""Specifies that the gNodeB type is Local Area Base Station."""

    MEDIUM_RANGE_BASE_STATION = 5
    r"""Specifies that the gNodeB type is Medium Range Base Station."""

    FR2_CATEGORY_A = 6
    r"""Specifies that the gNodeB type is FR2 Category A."""

    FR2_CATEGORY_B = 7
    r"""Specifies that the gNodeB type is FR2 Category B."""


class gNodeBType(Enum):
    """gNodeBType."""

    TYPE_1_C = 0
    r"""Type 1-C NR base station operating at FR1 and conducted requirements apply."""

    TYPE_1_H = 1
    r"""Type 1-H base station operating at FR1 and conducted and OTA requirements apply."""

    TYPE_1_O = 2
    r"""Type 1-O base station operating at FR1 and OTA requirements apply."""

    TYPE_2_O = 3
    r"""Type 2-O base station operating at FR2 and OTA requirements apply."""


class SatelliteAccessNodeClass(Enum):
    """SatelliteAccessNodeClass."""

    GEO = 0
    r"""Specifies the downlink SAN (Satellite Access Node) class corresponding to GEO satellite constellation."""

    LEO = 1
    r"""Specifies the downlink SAN (Satellite Access Node) class corresponding to LEO satellite constellation."""


class PiBy2BpskPowerBoostEnabled(Enum):
    """PiBy2BpskPowerBoostEnabled."""

    FALSE = 0
    r"""Power boost for PI/2 BPSK modulation is not enabled."""

    TRUE = 1
    r"""Power boost for PI/2 BPSK modulation is enabled."""


class AutoResourceBlockDetectionEnabled(Enum):
    """AutoResourceBlockDetectionEnabled."""

    FALSE = 0
    r"""The values of modulation type, number of resource block clusters, resource block offsets, and number of resource blocks
    that you specify are used for the measurement."""

    TRUE = 1
    r"""The values of modulation type, number of resource block clusters, resource block offsets, and number of resource blocks
    are auto-detected by the measurement."""


class AutoCellIDDetectionEnabled(Enum):
    """AutoCellIDDetectionEnabled."""

    FALSE = 0
    r"""User-configured Cell ID is used."""

    TRUE = 1
    r"""Measurement tries to autodetect the Cell ID."""


class DownlinkChannelConfigurationMode(Enum):
    """DownlinkChannelConfigurationMode."""

    USER_DEFINED = 1
    r"""The user sets all signals and channels manually."""

    TEST_MODEL = 2
    r"""A Test Model needs to be selected in the:py:attr:`~nirfmxnr.attributes.AttributeID.DOWNLINK_TEST_MODEL` attribute to
    configure all the signals and channels automatically, according to the section 4.9.2 of *3GPP 38.141-1/2*
    specification."""


class AutoIncrementCellIDEnabled(Enum):
    """AutoIncrementCellIDEnabled."""

    FALSE = 0
    r"""The measurement uses the user-configured cell IDs."""

    TRUE = 1
    r"""The Cell ID of each CC is auto calculated as specified in section 4.9.2.3 of *3GPP 38.141* specification."""


class DownlinkTestModelCellIDMode(Enum):
    """DownlinkTestModelCellIDMode."""

    AUTO = 0
    r"""Cell ID of each CC is auto calculated as specified in section 4.9.2.3 of the *3GPP 38.141* specification."""

    MANUAL = 1
    r"""The measurement uses the user-configured cell IDs."""


class FrequencyRange(Enum):
    """FrequencyRange."""

    RANGE1 = 0
    r"""Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 1 (sub 6
    GHz)."""

    RANGE2_1 = 1
    r"""Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 2-1
    (between 24.25 GHz and 52.6 GHz)."""

    RANGE2_2 = 2
    r"""Measurement uses the channel bandwidth and the subcarrier spacing configuration supported in frequency range 2-2
    (between 52.6 GHz and 71 GHz)."""


class ComponentCarrierSpacingType(Enum):
    """ComponentCarrierSpacingType."""

    NOMINAL = 0
    r"""Calculates the frequency spacing between component carriers as defined in section 5.4A.1 in the *3GPP 38.101-1/2*
    specification and section 5.4.1.2 in the *3GPP TS 38.104* specification and sets the
    :py:attr:`~nirfmxnr.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY` attribute."""

    USER = 2
    r"""The component carrier frequency that you configure in the CC Freq attribute is used."""


class DownlinkTestModel(Enum):
    """DownlinkTestModel."""

    TM1_1 = 0
    r"""Specifies a TM1.1 NR test model."""

    TM1_2 = 1
    r"""Specifies a TM1.2 NR test model."""

    TM2 = 2
    r"""Specifies a TM2 NR test model."""

    TM2A = 3
    r"""Specifies a TM2a NR test model."""

    TM3_1 = 4
    r"""Specifies a TM3.1 NR test model."""

    TM3_1A = 5
    r"""Specifies a TM3.1a NR test model."""

    TM3_2 = 6
    r"""Specifies a TM3.2 NR test model."""

    TM3_3 = 7
    r"""Specifies a TM3.3 NR test model."""

    TM2B = 8
    r"""Specifies a TM2b NR test model."""

    TM3_1B = 9
    r"""Specifies a TM3.1b NR test model."""


class DownlinkTestModelModulationType(Enum):
    """DownlinkTestModelModulationType."""

    Standard = 0
    r"""Specifies a standard modulation scheme."""

    QPSK = 1
    r"""Specifies a QPSK modulation scheme."""

    QAM16 = 2
    r"""Specifies a 16 QAM modulation scheme."""

    QAM64 = 3
    r"""Specifies a 64 QAM modulation scheme."""


class DownlinkTestModelDuplexScheme(Enum):
    """DownlinkTestModelDuplexScheme."""

    FDD = 0
    r"""Specifies that the duplexing technique is frequency-division duplexing."""

    TDD = 1
    r"""Specifies that the duplexing technique is time-division duplexing."""


class ComponentCarrierAllocated(Enum):
    """ComponentCarrierAllocated."""

    FALSE = 0
    r"""No resource elements are allocated for the component carrier. Only subblock IBE is computed."""

    TRUE = 1
    r"""One or more resource elements are allocated for the component carrier."""


class ComponentCarrierRadioAccessType(Enum):
    """ComponentCarrierRadioAccessType."""

    NR = 0
    r"""Specifies that the carrier is NR."""

    EUTRA = 1
    r"""Specifies that the carrier is E-UTRA."""


class BandwidthPartCyclicPrefixMode(Enum):
    """BandwidthPartCyclicPrefixMode."""

    NORMAL = 0
    r"""The number of symbols in the slot is 14."""

    EXTENDED = 1
    r"""The number of symbols in the slot is 12."""


class BandwidthPartDCLocationKnown(Enum):
    """BandwidthPartDCLocationKnown."""

    FALSE = 0
    r"""DC Location is un-known."""

    TRUE = 1
    r"""DC Location is known."""


class PuschTransformPrecodingEnabled(Enum):
    """PuschTransformPrecodingEnabled."""

    FALSE = 0
    r"""Transform precoding is disabled."""

    TRUE = 1
    r"""Transform precoding is enabled."""


class PuschModulationType(Enum):
    """PuschModulationType."""

    PI_BY_2_BPSK = 0
    r"""Specifies a PI/2 BPSK modulation scheme."""

    QPSK = 1
    r"""Specifies a QPSK modulation scheme."""

    QAM16 = 2
    r"""Specifies a 16 QAM modulation scheme."""

    QAM64 = 3
    r"""Specifies a 64 QAM modulation scheme."""

    QAM256 = 4
    r"""Specifies a 256 QAM modulation scheme."""

    QAM1024 = 5
    r"""Specifies a 1024 QAM modulation scheme."""

    PSK8 = 100
    r"""Specifies a 8 PSK modulation scheme."""


class PuschDmrsReleaseVersion(Enum):
    """PuschDmrsReleaseVersion."""

    RELEASE15 = 0
    r"""Specifies a 3GGP release version of 15 for PUSCH DMRS."""

    RELEASE16 = 1
    r"""Specifies a 3GGP release version of 16 or later for PUSCH DMRS."""


class PuschDmrsPowerMode(Enum):
    """PuschDmrsPowerMode."""

    CDM_GROUPS = 0
    r"""The value of PUSCH DMRS Pwr is calculated based on PDSCH DMRS Num CDM Groups attribute."""

    USER_DEFINED = 1
    r"""The value of PUSCH DMRS Pwr is specified by you."""


class PuschDmrsScramblingIDMode(Enum):
    """PuschDmrsScramblingIDMode."""

    CELL_ID = 0
    r"""The value of PUSCH DMRS Scrambling ID is based on Cell ID attribute."""

    USER_DEFINED = 1
    r"""The value of PUSCH DMRS Scrambling ID is specified by you."""


class PuschDmrsGroupHoppingEnabled(Enum):
    """PuschDmrsGroupHoppingEnabled."""

    FALSE = 0
    r"""Group hopping is disabled."""

    TRUE = 1
    r"""Group hopping is enabled."""


class PuschDmrsSequenceHoppingEnabled(Enum):
    """PuschDmrsSequenceHoppingEnabled."""

    FALSE = 0
    r"""The measurement uses zero as the base sequence number for all the slots."""

    TRUE = 1
    r"""The measurement calculates the base sequence number for each slot according to 3GPP specification."""


class PuschDmrsPuschIDMode(Enum):
    """PuschDmrsPuschIDMode."""

    CELL_ID = 0
    r"""The value of PUSCH DMRS PUSCH ID is based on Cell ID attribute."""

    USER_DEFINED = 1
    r"""The value of PUSCH DMRS PUSCH ID is specified by you."""


class PuschDmrsConfigurationType(Enum):
    """PuschDmrsConfigurationType."""

    TYPE1 = 0
    r"""One DMRS subcarrier alternates with one data subcarrier."""

    TYPE2 = 1
    r"""Two consecutive DMRS subcarriers alternate with four consecutive data subcarriers."""


class PuschMappingType(Enum):
    """PuschMappingType."""

    TYPE_A = 0
    r"""The first DMRS symbol index in a slot is either 2 or 3 based on
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_DMRS_TYPE_A_POSITION` attribute."""

    TYPE_B = 1
    r"""The first DMRS symbol index in a slot is the first active PUSCH symbol."""


class PuschDmrsDuration(Enum):
    """PuschDmrsDuration."""

    SINGLE_SYMBOL = 1
    r"""There are one or more non-consecutive DMRS symbols in a slot.."""

    DOUBLE_SYMBOL = 2
    r"""There are one or more sets of two consecutive DMRS symbols in the slot."""


class PuschPtrsEnabled(Enum):
    """PuschPtrsEnabled."""

    FALSE = 0
    r"""The PUSCH Transmission does not contain PTRS signals."""

    TRUE = 1
    r"""The PUSCH PTRS contains PTRS signals."""


class PuschPtrsPowerMode(Enum):
    """PuschPtrsPowerMode."""

    STANDARD = 0
    r"""The PUSCH PTRS Pwr scaling is calculated as defined in the Table 6.2.3.1-1 of *3GPP TS 38.214* specification."""

    USER_DEFINED = 1
    r"""The PTRS RE power scaling is given by the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_PTRS_POWER`
    attribute."""


class PdschModulationType(Enum):
    """PdschModulationType."""

    QPSK = 1
    r"""Specifies a QPSK modulation scheme."""

    QAM16 = 2
    r"""Specifies a 16 QAM modulation scheme."""

    QAM64 = 3
    r"""Specifies a 64 QAM modulation scheme."""

    QAM256 = 4
    r"""Specifies a 256 QAM modulation scheme."""

    QAM1024 = 5
    r"""Specifies a 1024 QAM modulation scheme."""

    PSK8 = 100
    r"""Specifies an 8 PSK modulation scheme."""


class PdschDmrsReleaseVersion(Enum):
    """PdschDmrsReleaseVersion."""

    RELEASE15 = 0
    r"""Specifies a 3GGP release version of 15 for PDSCH DMRS."""

    RELEASE16 = 1
    r"""Specifies a 3GGP release version of 16 for PDSCH DMRS."""


class PdschDmrsPowerMode(Enum):
    """PdschDmrsPowerMode."""

    CDM_GROUPS = 0
    r"""The value of PDSCH DMRS power is calculated based on the number of CDM groups."""

    USER_DEFINED = 1
    r"""The value of PDSCH DMRS power is specified by you."""


class PdschDmrsScramblingIDMode(Enum):
    """PdschDmrsScramblingIDMode."""

    CELL_ID = 0
    r"""The value of PDSCH DMRS Scrambling ID is based on Cell ID."""

    USER_DEFINED = 1
    r"""The value of PDSCH DMRS Scrambling ID is specified by you."""


class PdschDmrsConfigurationType(Enum):
    """PdschDmrsConfigurationType."""

    TYPE1 = 0
    r"""One DMRS subcarrier alternates with one data subcarrier."""

    TYPE2 = 1
    r"""Two consecutive DMRS subcarriers alternate with four consecutive data subcarriers."""


class PdschMappingType(Enum):
    """PdschMappingType."""

    TYPE_A = 0
    r"""The first DMRS symbol index in a slot is either 2 or 3."""

    TYPE_B = 1
    r"""The first DMRS symbol index in a slot is 0."""


class PdschDmrsDuration(Enum):
    """PdschDmrsDuration."""

    SINGLE_SYMBOL = 1
    r"""There are no consecutive DMRS symbols in the slot."""

    DOUBLE_SYMBOL = 2
    r"""There are one or more sets of two consecutive DMRS symbols in the slot."""


class PdschPtrsEnabled(Enum):
    """PdschPtrsEnabled."""

    FALSE = 0
    r"""Detection of PTRS in the transmitted signal is disabled."""

    TRUE = 1
    r"""Detection of PTRS in the transmitted signal is enabled."""


class PdschPtrsPowerMode(Enum):
    """PdschPtrsPowerMode."""

    STANDARD = 0
    r"""The PTRS RE power scaling is computed as defined in the Table 4.1-2 of *3GPP TS 38.214* specification using the value
    of :py:attr:`~nirfmxnr.attributes.AttributeID.EPRE_RATIO_PORT` attribute.."""

    USER_DEFINED = 1
    r"""The PTRS RE power scaling is given by the value of :py:attr:`~nirfmxnr.attributes.AttributeID.PDSCH_PTRS_POWER`
    attribute."""


class CoresetPrecodingGranularity(Enum):
    """CoresetPrecodingGranularity."""

    SAME_AS_REG_BUNDLE = 0
    r"""Precoding granularity is set to Same As REG Bundle."""

    ALL_CONTIGUOUS_RESOURCE_BLOCKS = 1
    r"""Precoding granularity is set to All Contiguous Resource Blocks."""


class CoresetCceToRegMappingType(Enum):
    """CoresetCceToRegMappingType."""

    NON_INTERLEAVED = 0
    r"""Mapping type is non-interleaved."""

    INTERLEAVED = 1
    r"""Mapping type is interleaved."""


class SsbEnabled(Enum):
    """SsbEnabled."""

    FALSE = 0
    r"""Detection of SSB in the transmitted signal is disabled."""

    TRUE = 1
    r"""Detection of SSB in the transmitted signal is enabled."""


class SsbPattern(Enum):
    """SsbPattern."""

    CASE_A_UP_TO_3GHZ = 0
    r"""Use with 15 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 *
    *n*, where *n* is 0 or 1."""

    CASE_A_3GHZ_TO_6GHZ = 1
    r"""Use with 15 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 *
    *n*, where *n* is 0, 1, 2, or 3."""

    CASE_B_UP_TO_3GHZ = 2
    r"""Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {4, 8, 16, 20} +
    28 * *n*, where *n* is 0."""

    CASE_B_3GHZ_TO_6GHZ = 3
    r"""Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {4, 8, 16, 20} +
    28 * *n*, where *n* is 0, 1, 2, or 3."""

    CASE_C_UP_TO_3GHZ = 4
    r"""Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 *
    *n*, where *n* is 0 or 1."""

    CASE_C_3GHZ_TO_6GHZ = 5
    r"""Use with 30 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes of {2, 8} + 14 *
    *n*, where *n* is 0, 1, 2, or 3."""

    CASE_D = 6
    r"""Use with 120 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {4, 8, 16, 20} + 28
    * *n*.
    For carrier frequencies within FR-2, *n* is 0, 1, 2, 3, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, or 18."""

    CASE_E = 7
    r"""Use with 240 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {8, 12, 16, 20, 32,
    36, 40, 44} + 56 * *n*.
    For carrier frequencies within FR2-1, *n* is 0, 1, 2, 3, 5, 6, 7, or 8."""

    CASE_F = 8
    r"""Use with 480 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {2, 9} + 14 * *n*.
    For carrier frequencies within FR2-2, *n* is 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
    19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, or 31."""

    CASE_G = 9
    r"""Use with 960 kHz subcarrier spacing. The first symbols of the candidate SS/PBCH blocks have indexes {2, 9} + 14 * *n*.
    For carrier frequencies within FR2-2, *n* is 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
    19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, or 31."""


class ModAccMulticarrierFilterEnabled(Enum):
    """ModAccMulticarrierFilterEnabled."""

    FALSE = 0
    r"""Measurement doesn't use the filter."""

    TRUE = 1
    r"""Measurement filters out unwanted emissions."""


class ModAccSynchronizationMode(Enum):
    """ModAccSynchronizationMode."""

    SLOT = 1
    r"""The measurement is performed over the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` starting at
    the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` from the slot boundary. If you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**, the measurement expects the
    digital trigger at the slot boundary."""

    FRAME = 5
    r"""The measurement is performed over the ModAcc Meas Length starting at ModAcc Meas Offset from the frame boundary. If you
    set the Trigger Type attribute to **Digital Edge**, the measurement expects the digital trigger from the frame
    boundary."""

    SSB_START_FRAME = 7
    r"""The measurement is performed over the ModAcc Meas Length starting at ModAcc Meas Offset from the frame boundary. If you
    set the Trigger Type attribute to **Digital Edge**, the measurement expects the digital trigger from the boundary of
    the frame having SSB."""


class ModAccMeasurementLengthUnit(Enum):
    """ModAccMeasurementLengthUnit."""

    SLOT = 1
    r"""Measurement offset and measurement length are specified in units of slots."""

    SUBFRAME = 3
    r"""Measurement offset and measurement length are specified in units of subframes."""

    TIME = 6
    r"""Measurement offset and measurement length are specified in seconds. Specify the measurement offset and length in
    multiples of 1 ms * (15 kHz/minimum subcarrier spacing of all carriers). All slots within this notional time duration
    are analysed."""


class ModAccFrequencyErrorEstimation(Enum):
    """ModAccFrequencyErrorEstimation."""

    DISABLED = 0
    r"""Frequency error estimation and correction is disabled."""

    NORMAL = 1
    r"""Estimate and correct frequency error of range +/- half subcarrier spacing."""

    WIDE = 2
    r"""Estimate and correct frequency error of range +/- half resource block when
    :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` is **True**, or range +/-  number of
    guard subcarrier when :py:attr:`~nirfmxnr.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` is **False**."""


class ModAccSymbolClockErrorEstimationEnabled(Enum):
    """ModAccSymbolClockErrorEstimationEnabled."""

    FALSE = 0
    r"""Indicates that symbol clock error estimation and correction is disabled."""

    TRUE = 1
    r"""Indicates that symbol clock error estimation and correction is enabled."""


class ModAccIQImpairmentsModel(Enum):
    """ModAccIQImpairmentsModel."""

    TX = 0
    r"""The measurement assumes that the I/Q impairments are introduced by a transmit DUT."""

    RX = 1
    r"""The measurement assumes that the I/Q impairments are introduced by a receive DUT."""


class ModAccIQOriginOffsetEstimationEnabled(Enum):
    """ModAccIQOriginOffsetEstimationEnabled."""

    FALSE = 0
    r"""Indicates that IQ origin offset estimation and correction is disabled."""

    TRUE = 1
    r"""Indicates that IQ origin offset estimation and correction is enabled."""


class ModAccIQMismatchEstimationEnabled(Enum):
    """ModAccIQMismatchEstimationEnabled."""

    FALSE = 0
    r"""IQ Impairments estimation is disabled."""

    TRUE = 1
    r"""IQ Impairments estimation is enabled."""


class ModAccIQGainImbalanceCorrectionEnabled(Enum):
    """ModAccIQGainImbalanceCorrectionEnabled."""

    FALSE = 0
    r"""IQ gain imbalance correction is disabled."""

    TRUE = 1
    r"""IQ gain imbalance correction is enabled."""


class ModAccIQQuadratureErrorCorrectionEnabled(Enum):
    """ModAccIQQuadratureErrorCorrectionEnabled."""

    FALSE = 0
    r"""IQ quadrature error correction is disabled."""

    TRUE = 1
    r"""IQ quadrature error correction is enabled."""


class ModAccIQTimingSkewCorrectionEnabled(Enum):
    """ModAccIQTimingSkewCorrectionEnabled."""

    FALSE = 0
    r"""IQ timing skew correction is disabled."""

    TRUE = 1
    r"""IQ timing skew correction is enabled."""


class ModAccIQImpairmentsPerSubcarrierEnabled(Enum):
    """ModAccIQImpairmentsPerSubcarrierEnabled."""

    FALSE = 0
    r"""Indicates that the independent estimation of I/Q impairments for each subcarrier is disabled."""

    TRUE = 1
    r"""Indicates that the independent estimation of I/Q impairments for each subcarrier is enabled."""


class ModAccMagnitudeAndPhaseErrorEnabled(Enum):
    """ModAccMagnitudeAndPhaseErrorEnabled."""

    FALSE = 0
    r"""Indicates that magnitude error and phase error results computation is disabled."""

    TRUE = 1
    r"""Indicates that magnitude error and phase error results computation is enabled."""


class ModAccEvmReferenceDataSymbolsMode(Enum):
    """ModAccEvmReferenceDataSymbolsMode."""

    ACQUIRED_WAVEFORM = 0
    r"""Indicates that reference data symbols for EVM computation are created using the acquired waveform."""

    REFERENCE_WAVEFORM = 1
    r"""Indicates that reference data symbols for EVM computation are created using the reference waveform."""


class ModAccSpectrumInverted(Enum):
    """ModAccSpectrumInverted."""

    FALSE = 0
    r"""The signal being measured is not inverted."""

    TRUE = 1
    r"""The signal being measured is inverted and measurement will correct it by swapping the I and Q components."""


class ModAccChannelEstimationType(Enum):
    """ModAccChannelEstimationType."""

    REFERENCE = 0
    r"""Only demodulation reference (DMRS) symbol is used to calculate channel coefficients."""

    REFERENCE_AND_DATA = 1
    r"""Both demodulation reference (DMRS) and data symbols are used to calculate channel coefficients. This method is as per
    definition of 3GPP NR specification."""


class ModAccPhaseTrackingMode(Enum):
    """ModAccPhaseTrackingMode."""

    DISABLED = 0
    r"""Disables the phase tracking."""

    REFERENCE_AND_DATA = 1
    r"""All reference and data symbols are used for phase tracking."""

    PTRS = 2
    r"""Only PTRS symbols are used for phase tracking."""


class ModAccTimingTrackingMode(Enum):
    """ModAccTimingTrackingMode."""

    DISABLED = 0
    r"""Disables the timing tracking."""

    REFERENCE_AND_DATA = 1
    r"""All reference and data symbols are used for timing tracking."""


class ModAccPreFftErrorEstimationInterval(Enum):
    """ModAccPreFftErrorEstimationInterval."""

    SLOT = 0
    r"""Frequency and timing error is estimated per slot in the pre-fft domain."""

    MEASUREMENT_LENGTH = 1
    r"""Frequency and timing error is estimated over the measurement interval in the pre-fft domain."""


class ModAccEvmUnit(Enum):
    """ModAccEvmUnit."""

    PERCENTAGE = 0
    r"""The EVM is reported as a percentage."""

    DB = 1
    r"""The EVM is reported in dB."""


class ModAccFftWindowType(Enum):
    """ModAccFftWindowType."""

    TYPE_3GPP = 0
    r"""The maximum EVM between the start window position and the end window position is returned according to the 3GPP
    specification. The FFT window positions are specified by the
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH_UNIT` attribute."""

    TYPE_CUSTOM = 1
    r"""Only one FFT window position is used for the EVM calculation. FFT window position is specified by
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_FFT_WINDOW_OFFSET` attribute."""


class ModAccDCSubcarrierRemovalEnabled(Enum):
    """ModAccDCSubcarrierRemovalEnabled."""

    FALSE = 0
    r"""The DC subcarrier is present in the EVM results."""

    TRUE = 1
    r"""The DC subcarrier is removed from the EVM results."""


class ModAccCommonClockSourceEnabled(Enum):
    """ModAccCommonClockSourceEnabled."""

    FALSE = 0
    r"""The Sample Clock error is estimated independently."""

    TRUE = 1
    r"""The Sample Clock error is estimated from carrier frequency offset."""


class ModAccSpectralFlatnessCondition(Enum):
    """ModAccSpectralFlatnessCondition."""

    NORMAL = 0
    r"""Frequency range and maximum ripple defined in the section 6.4.2.4.1, Table 6.4.2.4.1-1 of *3GPP 38.101-1* and section
    6.4.2.4.1, Table 6.4.2.4.1-1 of *3GPP 38.101-2* are used."""

    EXTREME = 1
    r"""Frequency range and maximum ripple defined in the section 6.4.2.4.1, Table 6.4.2.4.1-2 of *3GPP 38.101-1* and section
    6.4.2.4.1, Table 6.4.2.4.1-2 of *3GPP 38.101-2* are used."""


class ModAccNoiseCompensationEnabled(Enum):
    """ModAccNoiseCompensationEnabled."""

    FALSE = 0
    r"""Noise compensation is disabled for the measurement."""

    TRUE = 1
    r"""Noise compensation is enabled for the measurement."""


class ModAccNoiseCompensationInputPowerCheckEnabled(Enum):
    """ModAccNoiseCompensationInputPowerCheckEnabled."""

    FALSE = 0
    r"""Disables the input power check at the RFIn port of the signal analyzer."""

    TRUE = 1
    r"""Enables the input power check at the RFIn port of the signal analyzer."""


class ModAccMeasurementMode(Enum):
    """ModAccMeasurementMode."""

    MEASURE = 0
    r"""The ModAcc measurement is performed on the acquired signal."""

    CALIBRATE_NOISE_FLOOR = 1
    r"""The ModAcc measurement measures the noise floor of the instrument across the frequency determined by the carrier
    frequency and the channel bandwidth. In this mode, the measurement expects the signal generator to be turned off and
    checks if there is any signal power detected at RFIn port of the analyzer beyond a certain threshold. All scalar
    results and traces are invalid in this mode. Even if the instrument noise floor is already calibrated, the measurement
    performs all the required acquisitions and overwrites any pre-existing noise floor calibration data."""


class ModAccCompositeResultsIncludeDmrs(Enum):
    """ModAccCompositeResultsIncludeDmrs."""

    FALSE = 0
    r"""The DMRS resource elements are not included."""

    TRUE = 1
    r"""The DMRS resource elements are included."""


class ModAccCompositeResultsIncludePtrs(Enum):
    """ModAccCompositeResultsIncludePtrs."""

    FALSE = 0
    r"""The PTRS resource elements are not included."""

    TRUE = 1
    r"""The PTRS resource elements are included."""


class ModAccAveragingEnabled(Enum):
    """ModAccAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_AVERAGING_COUNT` attribute."""


class ModAccAutoLevelAllowOverflow(Enum):
    """ModAccAutoLevelAllowOverflow."""

    FALSE = 0
    r"""Disables searching for the optimum reference levels while allowing ADC overflow."""

    TRUE = 1
    r"""Enables searching for the optimum reference levels while allowing ADC overflow."""


class ModAccShortFrameEnabled(Enum):
    """ModAccShortFrameEnabled."""

    FALSE = 0
    r"""When you set the attribute to False or the :py:attr:`~nirfmxnr.attributes.AttributeID.TRIGGER_TYPE` attribute is set to
    a value other than **None**, a signal periodicity equal to the maximum of 1 frame duration and the configured SSB
    periodicity, if SSB is active, is assumed."""

    TRUE = 1
    r"""When you set the attribute to False or the Trigger Type attribute is set to **None**, the measurement uses
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_SHORT_FRAME_LENGTH_UNIT` as signal periodicity."""


class ModAccShortFrameLengthUnit(Enum):
    """ModAccShortFrameLengthUnit."""

    SLOT = 1
    r"""Short frame length is specified in units of slots."""

    SUBFRAME = 3
    r"""Short frame length is specified in units of subframes."""

    TIME = 6
    r"""Short frame length is specified in units of time."""


class ModAccTransientPeriodEvmMode(Enum):
    """ModAccTransientPeriodEvmMode."""

    DISABLED = 0
    r"""No special treatment of transient symbols (old behavior)."""

    EXCLUDE = 1
    r"""Transient symbols are not considered for EVM computation."""

    INCLUDE = 2
    r"""Transient EVM measurement definition is applied to transient symbols and returned as a separate Transient RMS EVM
    result."""


class SchDetectedModulationType(Enum):
    """SchDetectedModulationType."""

    PI_BY_2_BPSK = 0
    r"""Specifies the PI/2 BPSK modulation scheme."""

    QPSK = 1
    r"""Specifies the QPSK modulation scheme."""

    QAM16 = 2
    r"""Specifies the 16 QAM modulation scheme."""

    QAM64 = 3
    r"""Specifies the 64 QAM modulation scheme."""

    QAM256 = 4
    r"""Specifies the 256 QAM modulation scheme."""

    QAM1024 = 5
    r"""Specifies a 1024 QAM modulation scheme."""

    PSK8 = 100
    r"""Specifies the PDSCH 8 PSK constellation trace"""


class ModAccNoiseCompensationApplied(Enum):
    """ModAccNoiseCompensationApplied."""

    FALSE = 0
    r"""Noise compensation is not applied to the EVM measurement."""

    TRUE = 1
    r"""Noise compensation is applied to the EVM measurement."""


class AcpChannelConfigurationType(Enum):
    """AcpChannelConfigurationType."""

    STANDARD = 0
    r"""All settings will be 3GPP compliant."""

    CUSTOM = 1
    r"""The user can manually configure integration bandwidth and offset frequencies for the ACP measurement."""

    NS_29 = 2
    r"""This is an additional requirement according to section 6.5F.2.4.2 of *3GPP 38.101-1* and is applicable only for uplink
    bandwidths of 20 MHz and 40 MHz."""

    STANDARD_REL_16 = 3
    r"""All settings will be compliant with 3GPP Specifications, Release 16 and above."""

    STANDARD_REL_18 = 4
    r"""All settings will be compliant with 3GPP Specifications, Release 18 and above."""


class AcpOffsetSideband(Enum):
    """AcpOffsetSideband."""

    NEGATIVE = 0
    r"""Configures a lower offset segment to the left of the leftmost carrier."""

    POSITIVE = 1
    r"""Configures an upper offset segment to the right of the rightmost carrier."""

    BOTH = 2
    r"""Configures both the negative and the positive offset segments."""


class AcpRbwAutoBandwidth(Enum):
    """AcpRbwAutoBandwidth."""

    FALSE = 0
    r"""The measurement uses the RBW that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_BANDWIDTH` attribute."""

    TRUE = 1
    r"""The measurement computes the RBW."""


class AcpRbwFilterType(Enum):
    """AcpRbwFilterType."""

    FFT_BASED = 0
    r"""No RBW filtering is performed."""

    GAUSSIAN = 1
    r"""An RBW filter with a Gaussian response is applied."""

    FLAT = 2
    r"""An RBW filter with a flat response is applied."""


class AcpSweepTimeAuto(Enum):
    """AcpSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses a sweep time of 1 ms."""


class AcpPowerUnits(Enum):
    """AcpPowerUnits."""

    DBM = 0
    r"""Indicates that the absolute power is expressed in dBm."""

    DBM_BY_HZ = 1
    r"""Indicates that the absolute power is expressed in dBm/Hz."""


class AcpMeasurementMethod(Enum):
    """AcpMeasurementMethod."""

    NORMAL = 0
    r"""The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this
    method when measurement speed is desirable over higher dynamic range."""

    DYNAMIC_RANGE = 1
    r"""The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use
    this method to get the best dynamic range. **Supported Devices**: PXIe 5665/5668R"""

    SEQUENTIAL_FFT = 2
    r"""The ACP measurement acquires I/Q samples for a duration specified by the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL` attribute. These samples are divided into smaller
    chunks. The size of each chunk is defined by the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE`
    attribute, and the FFT is computed on each of these chunks. The resultant FFTs are averaged to get the spectrum and is
    used to compute the ACP. If the total acquired samples is not an integer multiple of the FFT size, the remaining
    samples at the end of the acquisition are not used for the measurement. Use this method to optimize ACP Measurement
    speed. The accuracy of results may be reduced when using this measurement method.
    
    For accurate power measurements when the power characteristics of the signal vary over time, averaging is
    allowed.
    
    The following attributes have limited support when you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` to **Sequential FFT**.
    
    +----------------------------------------------------------------------------+---------------------+
    | Property                                                                   | Supported Value     |
    +============================================================================+=====================+
    | :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH`  | True                |
    +----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_RBW_FILTER_TYPE`            | FFT Based           |
    +----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_COUNT`            | >=1                 |
    +----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS` | 1                   |
    +----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AMPLITUDE_CORRECTION_TYPE`  | RF Center Frequency |
    +----------------------------------------------------------------------------+---------------------+"""


class AcpNoiseCalibrationMode(Enum):
    """AcpNoiseCalibrationMode."""

    MANUAL = 0
    r"""When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_MODE` attribute to **Noise Calibrate**, you
    can initiate instrument noise calibration for ACP manually. When you set the ACP Meas Mode attribute to **Measure**,
    you can initiate the ACP measurement manually."""

    AUTO = 1
    r"""When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_COMPENSATION_ENABLED` attribute to **True**, RFmx
    sets :py:attr:`~nirfmxinstr.attribute.AttributeID.INPUT_ISOLATION_ENABLED` attribute to **Enabled** and calibrates the
    instrument noise in the current state of the instrument. Next, RFmx resets the Input Isolation Enabled attribute and
    performs the ACP measurement, including compensation for the noise contribution of the instrument. RFmx skips noise
    calibration in this mode if valid noise calibration data is already cached.
    
    When you set the ACP Noise Comp Enabled attribute to **False**, RFmx does not calibrate instrument noise and
    performs the ACP measurement without compensating for the noise contribution of the instrument."""


class AcpNoiseCalibrationAveragingAuto(Enum):
    """AcpNoiseCalibrationAveragingAuto."""

    FALSE = 0
    r"""RFmx uses the averaging count that you set for the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_COUNT` attribute."""

    TRUE = 1
    r"""When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Normal** or
    **Sequential FFT**, RFmx uses a noise calibration averaging count of 32. When you set the ACP Meas Method attribute to
    **Dynamic Range** and the sweep time is less than 5 ms, RFmx uses a noise calibration averaging count of 15. When you
    set the ACP Meas Method to **Dynamic Range** and the sweep time is greater than or equal to 5 ms, RFmx uses a noise
    calibration averaging count of 5."""


class AcpNoiseCompensationEnabled(Enum):
    """AcpNoiseCompensationEnabled."""

    FALSE = 0
    r"""Disables noise compensation."""

    TRUE = 1
    r"""Enables noise compensation.
    
    **Supported Devices**: PXIe-5663/5665/5668R, PXIe-5830/5831/5832/5842/5860"""


class AcpNoiseCompensationType(Enum):
    """AcpNoiseCompensationType."""

    ANALYZER_AND_TERMINATION = 0
    r"""Compensates for noise from the analyzer and the 50-ohm termination. The measured power values are in excess of the
    thermal noise floor."""

    ANALYZER_ONLY = 1
    r"""Compensates only for analyzer noise only."""


class AcpAveragingEnabled(Enum):
    """AcpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The ACP measurement uses the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_AVERAGING_COUNT` attribute as
    the number of acquisitions over which the ACP measurement is averaged."""


class AcpAveragingType(Enum):
    """AcpAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations, but not the noise floor."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""

    SCALAR = 2
    r"""The square root of the power spectrum is averaged."""

    MAXIMUM = 3
    r"""The peak power in the spectrum at each frequency bin is retained from one acquisition to the next."""

    MINIMUM = 4
    r"""The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next."""


class AcpMeasurementMode(Enum):
    """AcpMeasurementMode."""

    MEASURE = 0
    r"""Performs the ACP measurement on the acquired signal."""

    CALIBRATE_NOISE_FLOOR = 1
    r"""Performs manual noise calibration of the signal analyzer for the ACP measurement."""


class AcpFftWindow(Enum):
    """AcpFftWindow."""

    NONE = 0
    r"""No spectral leakage."""

    FLAT_TOP = 1
    r"""Spectral leakage is reduced using flat top window type."""

    HANNING = 2
    r"""Spectral leakage is reduced using Hanning window type."""

    HAMMING = 3
    r"""Spectral leakage is reduced using Hamming window type."""

    GAUSSIAN = 4
    r"""Spectral leakage is reduced using Gaussian window type."""

    BLACKMAN = 5
    r"""Spectral leakage is reduced using Blackman window type."""

    BLACKMAN_HARRIS = 6
    r"""Spectral leakage is reduced using Blackman-Harris window type."""

    KAISER_BESSEL = 7
    r"""Spectral leakage is reduced using Kaiser-Bessel window type."""


class AcpFftOverlapMode(Enum):
    """AcpFftOverlapMode."""

    DISABLED = 0
    r"""Disables the overlap between the FFT chunks."""

    AUTOMATIC = 1
    r"""Measurement sets the overlap based on the value you have set for the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_WINDOW` attribute. When you set the ACP FFT Window attribute to any
    value other than **None**, the number of overlapped samples between consecutive chunks is set to 50% of the value of
    the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute. When you set the ACP FFT Window
    attribute to **None**, the chunks are not overlapped and the overlap is set to 0%."""

    USER_DEFINED = 2
    r"""Measurement uses the overlap that you specify in the :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FFT_OVERLAP`
    attribute."""


class AcpIFOutputPowerOffsetAuto(Enum):
    """AcpIFOutputPowerOffsetAuto."""

    FALSE = 0
    r"""The measurement sets the IF output power level offset using the values of the
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_NEAR_IF_OUTPUT_POWER_OFFSET` and
    :py:attr:`~nirfmxnr.attributes.AttributeID.ACP_FAR_IF_OUTPUT_POWER_OFFSET` attributes."""

    TRUE = 1
    r"""The measurement automatically computes an IF output power level offset for the offset channels to improve the dynamic
    range of the ACP measurement."""


class AcpAmplitudeCorrectionType(Enum):
    """AcpAmplitudeCorrectionType."""

    RF_CENTER_FREQUENCY = 0
    r"""All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the
    RF center frequency."""

    SPECTRUM_FREQUENCY_BIN = 1
    r"""An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that
    frequency."""


class ChpSweepTimeAuto(Enum):
    """ChpSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses the sweep time based on the resolution bandwidth."""


class ChpIntegrationBandwidthType(Enum):
    """ChpIntegrationBandwidthType."""

    SIGNAL_BANDWIDTH = 0
    r"""The IBW excludes the guard bands at the edges of the carrier or subblock."""

    CHANNEL_BANDWIDTH = 1
    r"""The IBW includes the guard bands at the edges of the carrier or subblock."""


class ChpRbwAutoBandwidth(Enum):
    """ChpRbwAutoBandwidth."""

    FALSE = 0
    r"""The measurement uses the RBW that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_RBW_FILTER_BANDWIDTH` attribute."""

    TRUE = 1
    r"""The measurement computes the RBW."""


class ChpRbwFilterType(Enum):
    """ChpRbwFilterType."""

    FFT_BASED = 0
    r"""No RBW filtering is performed."""

    GAUSSIAN = 1
    r"""An RBW filter with a Gaussian response is applied."""

    FLAT = 2
    r"""An RBW filter with a flat response is applied."""


class ChpNoiseCalibrationMode(Enum):
    """ChpNoiseCalibrationMode."""

    MANUAL = 0
    r"""When you set :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to **Calibrate Noise Floor**,
    you can initiate the instrument noise calibration for CHP manually. When you set the CHP Meas Mode attribute to
    **Measure**, you can initiate the CHP measurement manually."""

    AUTO = 1
    r"""When you set the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_COMPENSATION_ENABLED` attribute to **True**, RFmx
    sets the :py:attr:`~nirfmxinstr.attribute.AttributeID.INPUT_ISOLATION_ENABLED` attribute to **Enabled** and calibrates
    the instrument noise in the current state of the instrument. Next, RFmx resets the Input Isolation Enabled attribute
    and performs the CHP measurement including compensation for the noise contribution of the instrument. RFmx skips noise
    calibration in this mode if valid noise calibration data is already cached. When you set the CHP Noise Comp Enabled to
    **False**, RFmx does not calibrate instrument noise and performs the CHP measurement without compensating for the noise
    contribution of the instrument."""


class ChpNoiseCalibrationAveragingAuto(Enum):
    """ChpNoiseCalibrationAveragingAuto."""

    FALSE = 0
    r"""RFmx uses the averages that you set for
    :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_COUNT` attribute."""

    TRUE = 1
    r"""RFmx uses a noise calibration averaging count of 32."""


class ChpNoiseCompensationEnabled(Enum):
    """ChpNoiseCompensationEnabled."""

    FALSE = 0
    r"""Indicates that noise compensation is disabled."""

    TRUE = 1
    r"""Indicates that noise compensation is enabled."""


class ChpNoiseCompensationType(Enum):
    """ChpNoiseCompensationType."""

    ANALYZER_AND_TERMINATION = 0
    r"""Compensates for noise contribution of the analyzer instrument and the 50-ohm termination. The measured power values are
    in excess of the thermal noise floor."""

    ANALYZER_ONLY = 1
    r"""Compensates only for analyzer noise only."""


class ChpAveragingEnabled(Enum):
    """ChpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The CHP measurement uses the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.CHP_AVERAGING_COUNT` attribute as
    the number of acquisitions over which the CHP measurement is averaged."""


class ChpAveragingType(Enum):
    """ChpAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""

    SCALAR = 2
    r"""The square root of the power spectrum is averaged."""

    MAXIMUM = 3
    r"""The peak power in the spectrum at each frequency bin is retained from one acquisition to the next."""

    MINIMUM = 4
    r"""The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next."""


class ChpMeasurementMode(Enum):
    """ChpMeasurementMode."""

    MEASURE = 0
    r"""Performs the CHP measurement on the acquired signal."""

    CALIBRATE_NOISE_FLOOR = 1
    r"""Performs manual noise calibration of the signal analyzer for the CHP measurement."""


class ChpFftWindow(Enum):
    """ChpFftWindow."""

    NONE = 0
    r"""No spectral leakage."""

    FLAT_TOP = 1
    r"""Spectral leakage is reduced using flat top window type."""

    HANNING = 2
    r"""Spectral leakage is reduced using Hanning window type."""

    HAMMING = 3
    r"""Spectral leakage is reduced using Hamming window type."""

    GAUSSIAN = 4
    r"""Spectral leakage is reduced using Gaussian window type."""

    BLACKMAN = 5
    r"""Spectral leakage is reduced using Blackman window type."""

    BLACKMAN_HARRIS = 6
    r"""Spectral leakage is reduced using Blackman-Harris window type."""

    KAISER_BESSEL = 7
    r"""Spectral leakage is reduced using Kaiser-Bessel window type."""


class ChpAmplitudeCorrectionType(Enum):
    """ChpAmplitudeCorrectionType."""

    RF_CENTER_FREQUENCY = 0
    r"""All frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the RF
    center frequency."""

    SPECTRUM_FREQUENCY_BIN = 1
    r"""Individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that
    frequency."""


class ObwPowerIntegrationMethod(Enum):
    """ObwPowerIntegrationMethod."""

    NORMAL = 0
    r"""The OBW measurement window is centered around the signal in the channel."""

    FROM_CENTER = 1
    r"""The OBW measurement window is centered around the RF Center Frequency."""


class ObwSpanAuto(Enum):
    """ObwSpanAuto."""

    FALSE = 0
    r"""Indicates that the user-configured span is used."""

    TRUE = 1
    r"""Indicates that the measurement will auto compute the span based on the configuration."""


class ObwRbwAutoBandwidth(Enum):
    """ObwRbwAutoBandwidth."""

    FALSE = 0
    r"""The measurement uses the RBW that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_BANDWIDTH` attribute."""

    TRUE = 1
    r"""The measurement computes the RBW."""


class ObwRbwFilterType(Enum):
    """ObwRbwFilterType."""

    FFT_BASED = 0
    r"""No RBW filtering is performed."""

    GAUSSIAN = 1
    r"""An RBW filter with a Gaussian response is applied."""

    FLAT = 2
    r"""An RBW filter with a flat response is applied."""


class ObwSweepTimeAuto(Enum):
    """ObwSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement calculates the sweep time internally. For DL, the sweep time is calculated based on the value of the
    :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_RBW_FILTER_BANDWIDTH` attribute, and for UL, it uses a sweep time of 1
    ms."""


class ObwAveragingEnabled(Enum):
    """ObwAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The OBW measurement uses the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.OBW_AVERAGING_COUNT` attribute as
    the number of acquisitions over which the OBW measurement is averaged."""


class ObwAveragingType(Enum):
    """ObwAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""

    SCALAR = 2
    r"""The square root of the power spectrum is averaged."""

    MAXIMUM = 3
    r"""The peak power in the spectrum at each frequency bin is retained from one acquisition to the next."""

    MINIMUM = 4
    r"""The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next."""


class ObwFftWindow(Enum):
    """ObwFftWindow."""

    NONE = 0
    r"""No spectral leakage."""

    FLAT_TOP = 1
    r"""Spectral leakage is reduced using flat top window type."""

    HANNING = 2
    r"""Spectral leakage is reduced using Hanning window type."""

    HAMMING = 3
    r"""Spectral leakage is reduced using Hamming window type."""

    GAUSSIAN = 4
    r"""Spectral leakage is reduced using Gaussian window type."""

    BLACKMAN = 5
    r"""Spectral leakage is reduced using Blackman window type."""

    BLACKMAN_HARRIS = 6
    r"""Spectral leakage is reduced using Blackman-Harris window type."""

    KAISER_BESSEL = 7
    r"""Spectral leakage is reduced using Kaiser-Bessel window type."""


class ObwAmplitudeCorrectionType(Enum):
    """ObwAmplitudeCorrectionType."""

    RF_CENTER_FREQUENCY = 0
    r"""All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the
    RF center frequency."""

    SPECTRUM_FREQUENCY_BIN = 1
    r"""An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that
    frequency."""


class SemUplinkMaskType(Enum):
    """SemUplinkMaskType."""

    GENERAL = 0
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.2-1 in section 6.5.2 of the
    *3GPP TS 38.101-1* specification, Table 6.5.2.1-1 and 6.5A.2.1-1 in section 6.5.2 of the *3GPP TS 38.101-2*
    specification and Table 6.5B.2.1.1-1 in section 6.5B of the *3GPP TS 38.101-3* specification. In case of non-contiguous
    EN-DC consisting of at least one subblock with all E-UTRA carriers, for the E-UTRA subblock, the measurement selects
    the offset frequencies and limits for the SEM, as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2, 6.6.2.1A.1.5-1, and
    6.6.2.1A.1.5-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification.
    
    If the band value is set to 46 or 96 or 102, the measurement selects the offset frequencies and limits for SEM
    as defined in Table 6.5F.2.2-1 in section 6.5F.2 of the *3GPP TS 38.101-1* Specification.
    
    If the band value is set to NTN bands 254, 255 or 256, the measurement selects the offset frequencies and
    limits for SEM as defined in Table 6.5.2.2.1 in section 6.5.2 of the 3GPP 38.101-5 specification."""

    NS35 = 1
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.1-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification and Table 6.5B.2.1.2.1-1 in section 6.5B of the *3GPP TS 38.101-3* specification.
    In case of non-contiguous EN-DC consisting of at least one subblock with all E-UTRA carriers, for the E-UTRA subblock,
    the measurement selects the offset frequencies and limits for the SEM, as defined in Table 6.6.2.2.5.5-1 in section
    6.6.2 of the *3GPP TS 36.521-1* specification."""

    CUSTOM = 2
    r"""You need to configure the :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_NUMBER_OF_OFFSETS`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_START_FREQUENCY`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_STOP_FREQUENCY`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_START`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_STOP`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_SIDEBAND`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_BANDWIDTH`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_TYPE`, and
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_OFFSET_BANDWIDTH_INTEGRAL` attributes for each offset."""

    NS03 = 3
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.3-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification. In case of non-contiguous EN-DC consisting of at least one subblock with all
    E-UTRA carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as
    defined in Table 6.6.2.2.5.1-1 and 6.6.2.2.5.1-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS04 = 4
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.2-3 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification. Subcarrier spacing can be configured through
    :py:attr:`~nirfmxnr.attributes.AttributeID.BANDWIDTH_PART_SUBCARRIER_SPACING` attribute. Subcarrier spacing
    corresponding to first bandwidth part is used for computing mask. Transform precoding can be configured through
    :py:attr:`~nirfmxnr.attributes.AttributeID.PUSCH_TRANSFORM_PRECODING_ENABLED` attribute. Transform precoding
    corresponding to first bandwidth part is used for computing mask. In case of non-contiguous EN-DC consisting of at
    least one subblock with all E-UTRA carriers, for the E-UTRA subblock, the measurement selects the offset frequencies
    and limits for the SEM, as defined in Table 6.6.2.2.3.2-3 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS06 = 5
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.4-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification. In case of non-contiguous EN-DC consisting of at least one subblock with all
    E-UTRA carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as
    defined in Table 6.6.2.2.5.3-1 and 6.6.2.2.5.3-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS21 = 6
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.3-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification. In case of non-contiguous EN-DC consisting of at least one subblock with all
    E-UTRA carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as
    defined in Table 6.6.2.2.5.1-1 and 6.6.2.2.5.1-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS27 = 7
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.8-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification. In case of intra-band contiguous CA consisting of at least one subblock with all
    NR carriers, for the NR subblock, the measurement selects the offset frequencies and limits for the SEM, as defined in
    Table 6.2A.2.3.2.1-1 in section 6.5A.2.3 of the *3GPP TS 38.101-1* specification. In case of non-contiguous EN-DC
    consisting of at least one subblock with all E-UTRA carriers, for the E-UTRA subblock, the measurement selects the
    offset frequencies and limits for the SEM, as defined in Table 6.6.2.2.3.4-1 in section 6.6.2 of the *3GPP TS 36.521-1*
    specification."""

    NS07 = 8
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.4-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification. In case of non-contiguous EN-DC consisting of at least one subblock with all
    E-UTRA carriers, for the E-UTRA subblock, the measurement selects the offset frequencies and limits for the SEM, as
    defined in Table 6.6.2.2.5.3-1 and Table 6.6.2.2.5.3-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS03U = 9
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.3-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification."""

    NS21_REL_17_ONWARDS = 10
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.9-1 in section 6.5.2 of
    the *3GPP TS 38.101-1* specification."""

    NS04N = 11
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.1-1 in section 6.5.2.3 of
    the * 3GPP TS 38.101-5* specification."""

    NS05N = 12
    r"""The measurement selects the offset frequencies and limits for SEM as defined in Table 6.5.2.3.2-1 in section 6.5.2.3 of
    the * 3GPP TS 38.101-5* specification."""


class SemDownlinkMaskType(Enum):
    """SemDownlinkMaskType."""

    STANDARD = 0
    r"""The measurement selects the offset frequencies and limits for SEM, as defined in Table 6.6.4.2.1-1, Table 6.6.4.2.1-2,
    Table 6.6.4.2.2.1-1, Table 6.6.4.2.2.1-2, Table 6.6.4.2.2.2-1, Table 6.6.4.2.3-1, Table 6.6.4.2.3-2, and Table
    6.6.4.2.4-1 in section 6.6.4 and Table 9.7.4.3.2-1, 9.7.4.3.2-2, 9.7.4.3.3-1 and 9.7.4.3.3-2 in section 9.7.4 of the
    *3GPP TS 38.104* Specification.
    
    If the band value is set to 46 or 96 or 102 the measurement selects the offset frequencies and limits for SEM
    as defined in Table 6.6.4.5.5A-1, Table  6.6.4.5.5A-2,  Table  6.6.4.5.5A-3, and  Table 6.6.4.5.5A-4, in section
    6.6.4.5 of the *3GPP TS 38.141-1* Specification.
    
    If the band value is set to NTN bands 254, 255 or 256, the measurement selects the offset frequencies and
    limits for SEM as defined in Table 6.6.4.2-1 in section 6.6.4 of the 3GPP 38.108 specification.
    
    The offset frequencies in Table 9.7.4.3.2-1, 9.7.4.3.2-2, 9.7.4.3.3-1 and 9.7.4.3.3-2 are relative to the
    contiguous transmission bandwidth edge. The measurement converts these offset frequencies to make them relative to the
    subblock edge before applying the masks.
    
    For frequency range 1, the :py:attr:`~nirfmxnr.attributes.AttributeID.GNODEB_CATEGORY` attribute can be set to
    any of the following values: Wide Area Base Station - Category A, Wide Area Base Station - Category B Option1, Wide
    Area Base Station - Category B Option2, Local Area Base Station, or Medium Range Base Station. Set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.BAND` attribute for selecting limits table within a gNodeB category.
    
    For frequency range 2-1 and frequency range 2-2, the gNodeB Category attribute can be set to any of the
    following values: FR2 Category A or FR2 Category B. Set the Band attribute for selecting limits table."""

    CUSTOM = 2
    r"""Specifies that limits are applied based on user-defined offset segments."""


class SemOffsetSideband(Enum):
    """SemOffsetSideband."""

    NEGATIVE = 0
    r"""Configures a lower offset segment to the left of the leftmost carrier."""

    POSITIVE = 1
    r"""Configures an upper offset segment to the right of the rightmost carrier."""

    BOTH = 2
    r"""Configures both the negative and the positive offset segments."""


class SemOffsetRbwFilterType(Enum):
    """SemOffsetRbwFilterType."""

    FFT_BASED = 0
    r"""No RBW filtering is performed."""

    GAUSSIAN = 1
    r"""The RBW filter has a Gaussian response."""

    FLAT = 2
    r"""The RBW filter has a flat response."""


class SemOffsetLimitFailMask(Enum):
    """SemOffsetLimitFailMask."""

    ABS_AND_REL = 0
    r"""Specifies that the measurement fails if the power in the segment exceeds both the absolute and relative masks."""

    ABS_OR_REL = 1
    r"""Specifies that the measurement fails if the power in the segment exceeds either the absolute or relative mask."""

    ABSOLUTE = 2
    r"""Specifies that the measurement fails if the power in the segment exceeds the absolute mask."""

    RELATIVE = 3
    r"""Specifies that the measurement fails if the power in the segment exceeds the relative mask."""


class SemOffsetFrequencyDefinition(Enum):
    """SemOffsetFrequencyDefinition."""

    CARRIER_CENTER_TO_MEAS_BW_CENTER = 0
    r"""The start frequency and stop frequency are defined from the center of the closest carrier channel bandwidth to the
    center of the offset segment measurement bandwidth."""

    CARRIER_EDGE_TO_MEAS_BW_CENTER = 2
    r"""The start frequency and stop frequency are defined from the nearest edge of the closest carrier channel bandwidth to
    the center of the offset segment measurement bandwidth."""

    SUBBLOCK_EDGE_TO_MEAS_BW_CENTER = 6
    r"""The start frequency and stop frequency are defined from the subblock edge of the closest subblock bandwidth to the
    center of the offset segment measurement bandwidth."""


class SemSweepTimeAuto(Enum):
    """SemSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses a sweep time of 1 ms."""


class SemAveragingEnabled(Enum):
    """SemAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The SEM measurement uses the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.SEM_AVERAGING_COUNT` attribute as
    the number of acquisitions over which the SEM measurement is averaged."""


class SemAveragingType(Enum):
    """SemAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""

    SCALAR = 2
    r"""The square root of the power spectrum is averaged."""

    MAXIMUM = 3
    r"""The peak power in the spectrum at each frequency bin is retained from one acquisition to the next."""

    MINIMUM = 4
    r"""The lowest power in the spectrum at each frequency bin is retained from one acquisition to the next."""


class SemFftWindow(Enum):
    """SemFftWindow."""

    NONE = 0
    r"""No spectral leakage."""

    FLAT_TOP = 1
    r"""Spectral leakage is reduced using flat top window type."""

    HANNING = 2
    r"""Spectral leakage is reduced using Hanning window type."""

    HAMMING = 3
    r"""Spectral leakage is reduced using Hamming window type."""

    GAUSSIAN = 4
    r"""Spectral leakage is reduced using Gaussian window type."""

    BLACKMAN = 5
    r"""Spectral leakage is reduced using Blackman window type."""

    BLACKMAN_HARRIS = 6
    r"""Spectral leakage is reduced using Blackman-Harris window type."""

    KAISER_BESSEL = 7
    r"""Spectral leakage is reduced using Kaiser-Bessel window type."""


class SemAmplitudeCorrectionType(Enum):
    """SemAmplitudeCorrectionType."""

    RF_CENTER_FREQUENCY = 0
    r"""All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the
    RF center frequency."""

    SPECTRUM_FREQUENCY_BIN = 1
    r"""An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that
    frequency."""


class SemMeasurementStatus(Enum):
    """SemMeasurementStatus."""

    FAIL = 0
    r"""Indicates that the measurement has failed."""

    PASS = 1
    r"""Indicates that the measurement has passed."""


class SemLowerOffsetMeasurementStatus(Enum):
    """SemLowerOffsetMeasurementStatus."""

    FAIL = 0
    r"""Indicates that the measurement has failed."""

    PASS = 1
    r"""Indicates that the measurement has passed."""


class SemUpperOffsetMeasurementStatus(Enum):
    """SemUpperOffsetMeasurementStatus."""

    FAIL = 0
    r"""Indicates that the measurement has failed."""

    PASS = 1
    r"""Indicates that the measurement has passed."""


class TxpAveragingEnabled(Enum):
    """TxpAveragingEnabled."""

    FALSE = 0
    r"""The number of acquisitions is 1."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxnr.attributes.AttributeID.TXP_AVERAGING_COUNT` for the number of acquisitions
    over which the measurement is averaged."""


class PvtMeasurementIntervalAuto(Enum):
    """PvtMeasurementIntervalAuto."""

    FALSE = 0
    r"""Measurement Interval is defined by the Measurement Interval attribute."""

    TRUE = 1
    r"""Measurement Inteval is computed by the measurement."""


class PvtMeasurementMethod(Enum):
    """PvtMeasurementMethod."""

    NORMAL = 0
    r"""The measurement is performed using a single acquisition. Use this method when a high dynamic range is not required."""

    DYNAMIC_RANGE = 1
    r"""The measurement is performed using two acquisitions. Use this method when a higher dynamic range is desirable over the
    measurement speed.
    
    **Supported Devices**: PXIe-5644R/5645R/5646R, PXIe-5840/5841/5842/5860"""


class PvtAveragingEnabled(Enum):
    """PvtAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.PVT_AVERAGING_COUNT` attribute as the
    number of acquisitions over which the PVT measurement is averaged."""


class PvtAveragingType(Enum):
    """PvtAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""


class PvtMeasurementStatus(Enum):
    """PvtMeasurementStatus."""

    FAIL = 0
    r"""Indicates that the measurement has failed."""

    PASS = 1
    r"""Indicates that the measurement has passed."""


class AcquisitionBandwidthOptimizationEnabled(Enum):
    """AcquisitionBandwidthOptimizationEnabled."""

    FALSE = 0
    r"""RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition
    center frequency is the same as the value of the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` that you
    configure."""

    TRUE = 1
    r"""RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span
    needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving
    the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement
    sensitive to it should have this attribute disabled."""


class TransmitterArchitecture(Enum):
    """TransmitterArchitecture."""

    LO_PER_COMPONENT_CARRIER = 0
    r"""The :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_RESULTS_COMPONENT_CARRIER_IQ_ORIGIN_OFFSET_MEAN` and the
    :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_RESULTS_IN_BAND_EMISSION_MARGIN` are calculated as the **LO per
    Component Carrier**, the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_IQ_ORIGIN_OFFSET_MEAN` and
    the :py:attr:`~nirfmxnr.attributes.AttributeID.MODACC_RESULTS_SUBBLOCK_IN_BAND_EMISSION_MARGIN` will not be returned."""

    LO_PER_SUBBLOCK = 1
    r"""The Subblock IQ Origin Offset Mean (dBc) and the Subblock In-Band Emission Margin (dB) are calculated as the **LO per
    Subblock**, the Carrier IQ Origin Offset Mean (dBc), and the In-Band Emission Margin (dB) will be NaN. In the case of a
    single carrier, the measurement returns the same value of IQ Origin Offset and In-Band Emission Margin for both
    components carrier and subblock results."""


class PhaseCompensation(Enum):
    """PhaseCompensation."""

    DISABLED = 0
    r"""No phase compensation is applied on the signal."""

    AUTO = 1
    r"""Phase compensation is applied on the signal using value of :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`
    attribute as the phase compensation frequency."""

    USER_DEFINED = 2
    r"""Phase compensation is applied on the signal using value of
    :py:attr:`~nirfmxnr.attributes.AttributeID.PHASE_COMPENSATION_FREQUENCY` attribute."""


class ReferenceGridAlignmentMode(Enum):
    """ReferenceGridAlignmentMode."""

    MANUAL = 0
    r"""The subcarrier spacing of the reference resource grid and the grid start of each bandwidthpart is user specified.
    Center of subcarrier 0 in common resource block 0 of the reference resource grid is considered as Reference Point A."""

    AUTO = 1
    r"""The subcarrier spacing of the reference resource grid is determined by the largest subcarrier spacing among the
    configured bandwidthparts and the SSB. The grid start of each bandwidthpart and the SSB is computed by minimizing k0 to
    {0, +6} subcarriers."""


class GridSizeMode(Enum):
    """GridSizeMode."""

    MANUAL = 0
    r"""The grid size is user specified."""

    AUTO = 1
    r"""The grid size is set equal to the maximum transmission bandwidth specified by the 3GPP specification."""


class LimitedConfigurationChange(Enum):
    """LimitedConfigurationChange."""

    DISABLED = 0
    r"""This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality
    attributes will be applied during RFmx Commit."""

    NO_CHANGE = 1
    r"""Signal configuration is locked after the first Commit of the named signal configuration. Any configuration change
    thereafter either in RFmxInstr attributes or personality attributes will not be considered by subsequent RFmx Commits
    or Initiates of this signal.  Use **No Change** if you have created named signal configurations for all measurement
    configurations but are setting some RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change
    Property topic for more details about the limitations of using this mode."""

    FREQUENCY = 2
    r"""Signal configuration, other than center frequency and external attenuation, is locked after first Commit of the named
    signal configuration. Thereafter, only the :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY` and
    :py:attr:`~nirfmxnr.attributes.AttributeID.EXTERNAL_ATTENUATION` attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal.  Refer to the Limitations of the Limited Configuration Change
    Property topic for more details about the limitations of using this mode."""

    REFERENCE_LEVEL = 3
    r"""Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.
    Thereafter only the :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL` attribute value change will be
    considered by subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ
    Power Edge Trigger, NI recommends that you set the
    :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` to **Relative** so that the trigger level
    is automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration
    Change Property topic for more details about the limitations of using this mode."""

    FREQUENCY_AND_REFERENCE_LEVEL = 4
    r"""Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first
    Commit of the named signal configuration. Thereafter only :py:attr:`~nirfmxnr.attributes.AttributeID.CENTER_FREQUENCY`,
    :py:attr:`~nirfmxnr.attributes.AttributeID.REFERENCE_LEVEL`, and
    :py:attr:`~nirfmxnr.attributes.AttributeID.EXTERNAL_ATTENUATION` attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge
    Trigger, NI recommends you set the :py:attr:`~nirfmxnr.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` to
    **Relative** so that the trigger level is automatically adjusted as you adjust the reference level. Refer to the
    Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this
    mode."""

    SELECTED_PORTS_FREQUENCY_AND_REFERENCE_LEVEL = 5
    r"""Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr
    configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected
    Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge
    Trigger, NI recommends you set the IQ Power Edge Level Type to **Relative** so that the trigger level is automatically
    adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic
    for more details about the limitations of using this mode."""


class ChpNoiseCalibrationDataValid(Enum):
    """ChpNoiseCalibrationDataValid."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""


class AcpNoiseCalibrationDataValid(Enum):
    """AcpNoiseCalibrationDataValid."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""


class ModAccCalibrationDataValid(Enum):
    """ModAccCalibrationDataValid."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""


class MeasurementTypes(IntFlag):
    """MeasurementTypes."""

    MODACC = 1 << 0
    r""""""

    SEM = 1 << 1
    r""""""

    ACP = 1 << 2
    r""""""

    CHP = 1 << 3
    r""""""

    OBW = 1 << 4
    r""""""

    PVT = 1 << 5
    r""""""

    TXP = 1 << 6
    r""""""
