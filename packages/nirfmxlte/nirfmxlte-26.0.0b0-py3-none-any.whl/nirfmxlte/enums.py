"""enums.py - Contains enum classes."""

from enum import Enum, IntFlag


class TriggerType(Enum):
    """TriggerType."""

    NONE = 0
    r"""No Reference Trigger is configured."""

    DIGITAL_EDGE = 1
    r"""The Reference Trigger is not asserted until a digital edge is detected. The source of the digital edge is specified
    using the :py:attr:`~nirfmxlte.attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE` attribute."""

    IQ_POWER_EDGE = 2
    r"""The Reference Trigger is asserted when the signal changes past the level specified by the slope (rising or falling),
    which is configured using the :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute."""

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
    :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute."""

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
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION` attribute."""

    AUTO = 1
    r"""The measurement computes the minimum quiet time used for triggering."""


class LinkDirection(Enum):
    """LinkDirection."""

    DOWNLINK = 0
    r"""The measurement uses 3GPP LTE downlink specification to measure the received signal."""

    UPLINK = 1
    r"""The measurement uses 3GPP LTE uplink specification to measure the received signal."""

    SIDELINK = 2
    r"""The measurement uses 3GPP LTE sidelink specifications to measure the received signal."""


class DuplexScheme(Enum):
    """DuplexScheme."""

    FDD = 0
    r"""Specifies that the duplexing technique is frequency-division duplexing."""

    TDD = 1
    r"""Specifies that the duplexing technique is time-division duplexing."""

    LAA = 2
    r"""Specifies that the duplexing technique is license assisted access."""


class UplinkDownlinkConfiguration(Enum):
    """UplinkDownlinkConfiguration."""

    CONFIGURATION_0 = 0
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 0."""

    CONFIGURATION_1 = 1
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 1."""

    CONFIGURATION_2 = 2
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 2."""

    CONFIGURATION_3 = 3
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 3."""

    CONFIGURATION_4 = 4
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 4."""

    CONFIGURATION_5 = 5
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 5."""

    CONFIGURATION_6 = 6
    r"""The configuration of the LTE frame structure in the TDD duplex mode is 6."""


class eNodeBCategory(Enum):
    """eNodeBCategory."""

    WIDE_AREA_BASE_STATION_CATEGORY_A = 0
    r"""Specifies eNodeB is Wide Area Base Station - Category A."""

    WIDE_AREA_BASE_STATION_CATEGORY_B_OPTION_1 = 1
    r"""Specifies eNodeB is Wide Area Base Station - Category B Option1."""

    WIDE_AREA_BASE_STATION_CATEGORY_B_OPTION_2 = 2
    r"""Specifies eNodeB is Wide Area Base Station - Category B Option2."""

    LOCAL_AREA_BASE_STATION = 3
    r"""Specifies eNodeB is Local Area Base Station."""

    HOME_BASE_STATION = 4
    r"""Specifies eNodeB is Home Base Station."""

    MEDIUM_RANGE_BASE_STATION = 5
    r"""Specifies eNodeB is Medium Range Base Station."""


class ComponentCarrierSpacingType(Enum):
    """ComponentCarrierSpacingType."""

    NOMINAL = 0
    r"""Calculates the frequency spacing between component carriers, as defined in section 5.4.1A in the *3GPP TS 36.521*
    specification,  and sets the :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_FREQUENCY` attribute."""

    MINIMUM = 1
    r"""Calculates the frequency spacing between component carriers, as defined in section 5.4.1A of the *3GPP TS 36.521*
    specification, and sets the CC Freq attribute."""

    USER = 2
    r"""The CC frequency that you configure in the CC Freq attribute is used."""


class CyclicPrefixMode(Enum):
    """CyclicPrefixMode."""

    NORMAL = 0
    r"""The CP duration is 4.67 microseconds, and the number of symbols in a slot is 7."""

    EXTENDED = 1
    r"""The CP duration is 16.67 microseconds, and the number of symbols in a slot is 6."""


class DownlinkAutoCellIDDetectionEnabled(Enum):
    """DownlinkAutoCellIDDetectionEnabled."""

    FALSE = 0
    r"""The measurement uses the cell ID you configure."""

    TRUE = 1
    r"""The measurement auto detects the cell ID."""


class DownlinkChannelConfigurationMode(Enum):
    """DownlinkChannelConfigurationMode."""

    USER_DEFINED = 1
    r"""You have to manually set all the signals and channels."""

    TEST_MODEL = 2
    r"""You need to select a test model using the :py:attr:`~nirfmxlte.attributes.AttributeID.DOWNLINK_TEST_MODEL` attribute,
    which will configure all the signals and channels automatically according to the 3GPP specification."""


class AutoPdschChannelDetectionEnabled(Enum):
    """AutoPdschChannelDetectionEnabled."""

    FALSE = 0
    r"""The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation
    Type, and the PDSCH Power attribute that you specify."""

    TRUE = 1
    r"""The measurement uses the values of the PDSCH RB Allocation attribute, the corresponding values of PDSCH CW0 Modulation
    Type, and the PDSCH Power attribute that are auto-detected."""


class AutoControlChannelPowerDetectionEnabled(Enum):
    """AutoControlChannelPowerDetectionEnabled."""

    FALSE = 0
    r"""The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, PHICH Power, and PCFICH Power attributes that you
    specify are used for the measurement."""

    TRUE = 1
    r"""The value of the PSS Power, SSS Power, PDCCH Power, PBCH Power, and PCFICH Power attributes are auto-detected and used
    for the measurement."""


class AutoPcfichCfiDetectionEnabled(Enum):
    """AutoPcfichCfiDetectionEnabled."""

    FALSE = 0
    r"""The value of PCFICH CFI attribute used for the measurement is specified by you."""

    TRUE = 1
    r"""The value of PCFICH CFI attribute used for the measurement is auto-detected. This value is obtained by decoding the
    PCFICH channel."""


class MiConfiguration(Enum):
    """MiConfiguration."""

    TEST_MODEL = 0
    r"""Mi parameter is set to 1 as specified in section 6.1.2.6 of *3GPP TS 36.141* specification."""

    STANDARD = 1
    r"""Mi parameter is specified by the Table 6.9-1 of *3GPP TS 36.211* specification."""


class DownlinkUserDefinedRatio(Enum):
    """DownlinkUserDefinedRatio."""

    P_B_0 = 0
    r"""Specifies a ratio of 1 for one antenna port and 5/4 for two or four antenna ports."""

    P_B_1 = 1
    r"""Specifies a ratio of 4/5 for one antenna port and 1 for two or four antenna ports."""

    P_B_2 = 2
    r"""Specifies a ratio of 3/5 for one antenna port and 3/4 for two or four antenna ports."""

    P_B_3 = 3
    r"""Specifies a ratio of 2/5 for one antenna port and 1/2 for two or four antenna ports."""


class DownlinkUserDefinedPhichResource(Enum):
    """DownlinkUserDefinedPhichResource."""

    ONE_SIXTH = 0
    r"""Specifies the PHICH resource value is 1/6."""

    HALF = 1
    r"""Specifies the PHICH resource value is 1/2."""

    ONE = 2
    r"""Specifies the PHICH resource value is 1."""

    TWO = 3
    r"""Specifies the PHICH resource value is 2."""


class DownlinkUserDefinedPhichDuration(Enum):
    """DownlinkUserDefinedPhichDuration."""

    NORMAL = 0
    r"""Orthogonal sequences of length 4 is used to extract PHICH."""


class UserDefinedPdschCW0ModulationType(Enum):
    """UserDefinedPdschCW0ModulationType."""

    QPSK = 0
    r"""Specifies a QPSK modulation scheme."""

    QAM_16 = 1
    r"""Specifies a 16-QAM modulation scheme."""

    QAM_64 = 2
    r"""Specifies a 64-QAM modulation scheme."""

    QAM_256 = 3
    r"""Specifies a 256-QAM modulation scheme."""

    QAM_1024 = 4
    r"""Specifies a 1024-QAM modulation scheme."""


class DownlinkTestModel(Enum):
    """DownlinkTestModel."""

    TM_1_1 = 0
    r"""Specifies an E-UTRA Test Model 1.1."""

    TM_1_2 = 1
    r"""Specifies an E-UTRA Test Model 1.2."""

    TM_2 = 2
    r"""Specifies an E-UTRA Test Model 2."""

    TM_2_A = 3
    r"""Specifies an E-UTRA Test Model 2a."""

    TM_3_1 = 4
    r"""Specifies an E-UTRA Test Model 3.1."""

    TM_3_2 = 5
    r"""Specifies an E-UTRA Test Model 3.2."""

    TM_3_3 = 6
    r"""Specifies an E-UTRA Test Model 3.3."""

    TM_3_1_A = 7
    r"""Specifies an E-UTRA Test Model 3.1a."""

    TM_2_B = 8
    r"""Specifies an E-UTRA Test Model 2b."""

    TM_3_1_B = 9
    r"""Specifies an E-UTRA Test Model 3.1b."""


class AutoResourceBlockDetectionEnabled(Enum):
    """AutoResourceBlockDetectionEnabled."""

    FALSE = 0
    r"""The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes that you specify
    are used for the measurement."""

    TRUE = 1
    r"""The values of the PUSCH Mod Type, PUSCH Num Clusters, PUSCH RB Offset, and PUSCH Num RBs attributes are detected
    automatically and used for the measurement."""


class AutoDmrsDetectionEnabled(Enum):
    """AutoDmrsDetectionEnabled."""

    FALSE = 0
    r"""The user-specified DMRS parameters are used."""

    TRUE = 1
    r"""The values of the DMRS parameters are automatically detected. Measurement returns an error if you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_SYNCHRONIZATION_MODE` attribute to **Frame**, since it is not
    possible to get the frame boundary when RFmx detects DMRS parameters automatically."""


class UplinkGroupHoppingEnabled(Enum):
    """UplinkGroupHoppingEnabled."""

    FALSE = 0
    r"""The measurement uses zero as the sequence group number for all the slots."""

    TRUE = 1
    r"""Calculates the sequence group number for each slot, as defined in the section 5.5.1.3 of *3GPP 36.211 Specification.*"""


class UplinkSequenceHoppingEnabled(Enum):
    """UplinkSequenceHoppingEnabled."""

    FALSE = 0
    r"""The measurement uses zero as the base sequence number for all the slots."""

    TRUE = 1
    r"""Calculates the base sequence number for each slot, as defined in the section 5.5.1.4 of *3GPP 36.211* specification."""


class DmrsOccEnabled(Enum):
    """DmrsOccEnabled."""

    FALSE = 0
    r"""The measurement ignores the :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_CYCLIC_SHIFT_FIELD` and uses the
    :py:attr:`~nirfmxlte.attributes.AttributeID.PUSCH_N_DMRS_2` field for DMRS calculations."""

    TRUE = 1
    r"""The measurement uses the table 5.5.2.1.1-1 of *3GPP 36.211* specification to decide the value of PUSCH n_DMRS_2 and
    [w(0) w(1)] for DMRS signal based on the values you set for the Cyclic Shift Field and
    :py:attr:`~nirfmxlte.attributes.AttributeID.TRANSMIT_ANTENNA_TO_ANALYZE`."""


class PuschModulationType(Enum):
    """PuschModulationType."""

    MODULATION_TYPE_QPSK = 0
    r"""Specifies a QPSK modulation scheme."""

    MODULATION_TYPE_16_QAM = 1
    r"""Specifies a 16-QAM modulation scheme."""

    MODULATION_TYPE_64_QAM = 2
    r"""Specifies a 64-QAM modulation scheme."""

    MODULATION_TYPE_256_QAM = 3
    r"""Specifies a 256-QAM modulation scheme."""

    MODULATION_TYPE_1024_QAM = 4
    r"""Specifies a 1024-QAM modulation scheme."""


class SrsEnabled(Enum):
    """SrsEnabled."""

    FALSE = 0
    r"""Measurement expects signal without SRS transmission."""

    TRUE = 1
    r"""Measurement expects signal with SRS transmission."""


class SrsMaximumUpPtsEnabled(Enum):
    """SrsMaximumUpPtsEnabled."""

    FALSE = 0
    r"""In special subframe, SRS is transmitted in RBs specified by SRS bandwidth configurations."""

    TRUE = 1
    r"""In special subframe, SRS is transmitted in all possible RBs."""


class PsschModulationType(Enum):
    """PsschModulationType."""

    QPSK = 0
    r"""Specifies a QPSK modulation scheme."""

    QAM_16 = 1
    r"""Specifies a 16-QAM modulation scheme."""

    QAM_64 = 2
    r"""Specifies a 64-QAM modulation scheme."""


class LaaUplinkStartPosition(Enum):
    """LaaUplinkStartPosition."""

    START_POSITION_00 = 0
    r"""The symbol 0 in the first subframe of an LAA uplink burst is completely occupied. There is no idle duration."""

    START_POSITION_01 = 1
    r"""The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame
    structure type 3) of the *3GPP 36.211* specification. The symbol is partially occupied."""

    START_POSITION_10 = 2
    r"""The starting position of symbol 0 in the first subframe of an LAA uplink burst is calculated as per section 5.6 (frame
    structure type 3) of the *3GPP 36.211* specification. The symbol is partially occupied."""

    START_POSITION_11 = 3
    r"""The symbol 0 in the first subframe of an LAA uplink burst is completely idle. Symbol 0 is not transmitted in this case."""


class LaaUplinkEndingSymbol(Enum):
    """LaaUplinkEndingSymbol."""

    ENDING_SYMBOL_12 = 12
    r"""The last subframe of an LAA uplink burst ends at symbol 12."""

    ENDING_SYMBOL_13 = 13
    r"""The last subframe of an LAA uplink burst ends at symbol 13."""


class LaaDownlinkStartingSymbol(Enum):
    """LaaDownlinkStartingSymbol."""

    STARTING_SYMBOL_0 = 0
    r"""The first subframe of an LAA downlink burst starts at symbol 0."""

    STARTING_SYMBOL_7 = 7
    r"""The first subframe of an LAA downlink burst starts at symbol 7."""


class LaaDownlinkNumberOfEndingSymbols(Enum):
    """LaaDownlinkNumberOfEndingSymbols."""

    ENDING_SYMBOLS_3 = 3
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 3."""

    ENDING_SYMBOLS_6 = 6
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 6."""

    ENDING_SYMBOLS_9 = 9
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 9."""

    ENDING_SYMBOLS_10 = 10
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 10."""

    ENDING_SYMBOLS_11 = 11
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 11."""

    ENDING_SYMBOLS_12 = 12
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 12."""

    ENDING_SYMBOLS_14 = 14
    r"""The number of ending symbols in the last subframe of an LAA downlink burst is 14."""


class NBIoTUplinkSubcarrierSpacing(Enum):
    """NBIoTUplinkSubcarrierSpacing."""

    SUBCARRIER_SPACING_15_KHZ = 0
    r"""The subcarrier spacing is 15 kHz."""

    SUBCARRIER_SPACING_3_75_KHZ = 1
    r"""The subcarrier spacing is 3.75 kHz."""


class AutoNPuschChannelDetectionEnabled(Enum):
    """AutoNPuschChannelDetectionEnabled."""

    FALSE = 0
    r"""The measurement uses the values that you specify for the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod
    Type attributes."""

    TRUE = 1
    r"""The measurement uses the values of the NPUSCH Tone Offset, NPUSCH Number of Tones, and NPUSCH Mod Type attributes that
    are auto-detected."""


class NPuschModulationType(Enum):
    """NPuschModulationType."""

    BPSK = 0
    r"""Specifies a BPSK modulation scheme."""

    QPSK = 1
    r"""Specifies a QPSK modulation scheme."""


class NPuschDmrsBaseSequenceMode(Enum):
    """NPuschDmrsBaseSequenceMode."""

    MANUAL = 0
    r"""The measurement uses the value that you specify for the NPUSCH DMRS Base Sequence Index attribute."""

    AUTO = 1
    r"""The measurement uses the value of :py:attr:`~nirfmxlte.attributes.AttributeID.NCELL_ID` attribute to compute the NPUSCH
    DMRS Base Sequence Index as defined in section 10.1.4.1.2 of the *3GPP TS 36.211* specification."""


class NPuschDmrsGroupHoppingEnabled(Enum):
    """NPuschDmrsGroupHoppingEnabled."""

    FALSE = 0
    r"""Group hopping is disabled."""

    TRUE = 1
    r"""Group hopping is enabled. The sequence group number is calculated as defined in section 10.1.4.1.3 of the *3GPP TS
    36.211* specification."""


class NBIoTDownlinkChannelConfigurationMode(Enum):
    """NBIoTDownlinkChannelConfigurationMode."""

    USER_DEFINED = 1
    r"""You have to manually set all the signals and channels."""

    TEST_MODEL = 2
    r"""Configures all the signals and channels automatically according to the 3GPP NB-IoT test model specification."""


class NpdschEnabled(Enum):
    """NpdschEnabled."""

    FALSE = 0
    r"""Indicates to the measurement that NPDSCH is not present in a particular subframe."""

    TRUE = 1
    r"""Indicates to the measurement that NPDSCH is present in a particular subframe."""


class EmtcAnalysisEnabled(Enum):
    """EmtcAnalysisEnabled."""

    FALSE = 0
    r"""The measurement considers the signal as LTE FDD/TDD transmission."""

    TRUE = 1
    r"""Detects the eMTC half duplex pattern, narrow band hopping, and eMTC guard symbols present in the uplink transmission."""


class ModAccMulticarrierFilterEnabled(Enum):
    """ModAccMulticarrierFilterEnabled."""

    FALSE = 0
    r"""The measurement does not use the multicarrier filter."""

    TRUE = 1
    r"""The measurement filters out interference from out of band emissions into the carriers being measured."""


class ModAccMulticarrierTimeSynchronizationMode(Enum):
    """ModAccMulticarrierTimeSynchronizationMode."""

    COMMON = 0
    r"""Specifies that a common time synchronization value is used for synchronization of all the component carriers and time
    synchronization value is obtained from the synchronization of the first active component carrier of the first subblock."""

    PER_CARRIER = 1
    r"""Specifies that time synchronization is performed on each component carrier."""


class ModAccSynchronizationMode(Enum):
    """ModAccSynchronizationMode."""

    FRAME = 0
    r"""The frame boundary is detected, and the measurement is performed over the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute, starting at the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_OFFSET` attribute from the frame boundary. When you set
    the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**, the measurement expects a
    trigger at the frame boundary."""

    SLOT = 1
    r"""The slot boundary is detected, and the measurement is performed over the ModAcc Meas Length attribute starting at the
    ModAcc Meas Offset attribute from the slot boundary. When you set the Trigger Type attribute to **Digital Edge**, the
    measurement expects a trigger at any slot boundary."""

    MARKER = 2
    r"""The measurement expects a marker (trigger) at the frame boundary from the user. The measurement takes advantage of
    triggered acquisitions to reduce processing resulting in faster measurement time. Measurement is performed over the
    ModAcc Meas Length attribute starting at ModAcc Meas Offset attribute from the frame boundary."""


class ModAccFrequencyErrorEstimation(Enum):
    """ModAccFrequencyErrorEstimation."""

    NORMAL = 1
    r"""Estimate and correct frequency error of range +/- half subcarrier spacing."""

    WIDE = 2
    r"""Estimate and correct frequency error of range +/- half resource block when
    :py:attr:`~nirfmxlte.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` is **True**, or range +/- number of
    guard subcarrier when :py:attr:`~nirfmxlte.attributes.AttributeID.AUTO_RESOURCE_BLOCK_DETECTION_ENABLED` is **False**."""


class ModAccIQOriginOffsetEstimationEnabled(Enum):
    """ModAccIQOriginOffsetEstimationEnabled."""

    FALSE = 0
    r"""IQ origin offset estimation and correction is disabled."""

    TRUE = 1
    r"""IQ origin offset estimation and correction is enabled."""


class ModAccIQMismatchEstimationsEnabled(Enum):
    """ModAccIQMismatchEstimationsEnabled."""

    FALSE = 0
    r"""IQ mismatch estimation is disabled."""

    TRUE = 1
    r"""IQ mismatch estimation is enabled."""


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


class ModAccSpectrumInverted(Enum):
    """ModAccSpectrumInverted."""

    FALSE = 0
    r"""The spectrum of the measured signal is not inverted."""

    TRUE = 1
    r"""The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components."""


class ModAccChannelEstimationType(Enum):
    """ModAccChannelEstimationType."""

    REFERENCE = 0
    r"""Only the demodulation reference signal (DMRS) symbol is used to calculate the channel coefficients."""

    REFERENCE_AND_DATA = 1
    r"""Both the DMRS symbol and the data symbol are used to calculate the channel coefficients, as specified by the *3GPP
    36.521* specification, Annexe E."""


class ModAccEvmUnit(Enum):
    """ModAccEvmUnit."""

    PERCENTAGE = 0
    r"""The EVM is reported as a percentage."""

    DB = 1
    r"""The EVM is reported in dB."""


class ModAccFftWindowType(Enum):
    """ModAccFftWindowType."""

    TYPE_3_GPP = 0
    r"""The maximum EVM between the start window position and the end window position is returned according to the 3GPP
    specification. The FFT window positions are specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_MEASUREMENT_LENGTH` attribute. Refer to the Annexe E.3.2 of *3GPP TS
    36.521* specification for more information on the FFT window."""

    TYPE_CUSTOM = 1
    r"""Only one FFT window position is used for the EVM calculation. FFT window position is specified by
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_FFT_WINDOW_OFFSET` attribute."""


class ModAccCommonClockSourceEnabled(Enum):
    """ModAccCommonClockSourceEnabled."""

    FALSE = 0
    r"""The Sample Clock error is estimated independently."""

    TRUE = 1
    r"""The Sample Clock error is estimated from carrier frequency offset."""


class ModAccEvmWithExclusionPeriodEnabled(Enum):
    """ModAccEvmWithExclusionPeriodEnabled."""

    FALSE = 0
    r"""EVM is calculated on complete slots."""

    TRUE = 1
    r"""EVM is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and the
    defined 3GPP specification period is excluded from the slots being measured."""


class ModAccSpectralFlatnessCondition(Enum):
    """ModAccSpectralFlatnessCondition."""

    NORMAL = 0
    r"""Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-1 of *3GPP 36.521* specification."""

    EXTREME = 1
    r"""Uses the frequency range defined in the section 6.5.2.4.5, and table 6.5.2.4.3-2 of *3GPP 36.521* specification."""


class ModAccInBandEmissionMaskType(Enum):
    """ModAccInBandEmissionMaskType."""

    RELEASE_8_10 = 0
    r"""Specifies the mask type to be used for UE, supporting 3GPP Release 8 to 3GPP Release 10 specification."""

    RELEASE_11_ONWARDS = 1
    r"""Specifies the mask type to be used for UE, supporting 3GPP Release 11 and higher specification."""


class ModAccAveragingEnabled(Enum):
    """ModAccAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement is averaged over multiple acquisitions. The number of acquisitions is obtained by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.MODACC_AVERAGING_COUNT` attribute."""


class ModAccPreFftErrorEstimationInterval(Enum):
    """ModAccPreFftErrorEstimationInterval."""

    SLOT = 0
    r"""Frequency and Timing Error is estimated per slot in the pre-fft domain."""

    SUBFRAME = 1
    r"""Frequency and Timing Error is estimated per subframe in the pre-fft domain."""

    MEASUREMENT_LENGTH = 2
    r"""Frequency and Timing Error is estimated over the measurement interval in the pre-fft domain."""


class ModAccSymbolClockErrorEstimationEnabled(Enum):
    """ModAccSymbolClockErrorEstimationEnabled."""

    FALSE = 0
    r"""Symbol Clock Error estimation and correction is disabled."""

    TRUE = 1
    r"""Symbol Clock Error estimation and correction is enabled."""


class ModAccTimingTrackingEnabled(Enum):
    """ModAccTimingTrackingEnabled."""

    FALSE = 0
    r"""Disables the Timing Tracking."""

    TRUE = 1
    r"""All the reference and data symbols are used for Timing Tracking."""


class ModAccPhaseTrackingEnabled(Enum):
    """ModAccPhaseTrackingEnabled."""

    FALSE = 0
    r"""Disables the Phase Tracking."""

    TRUE = 1
    r"""All the reference and data symbols are used for Phase Tracking."""


class AcpConfigurableNumberOfOffsetsEnabled(Enum):
    """AcpConfigurableNumberOfOffsetsEnabled."""

    FALSE = 0
    r"""Measurement will set the number of offsets."""

    TRUE = 1
    r"""Measurement will use the user configured value for number of offsets."""


class AcpEutraOffsetDefinition(Enum):
    """AcpEutraOffsetDefinition."""

    AUTO = 0
    r"""Measurement will set the E-UTRA definition and offset power reference based on the link direction. For downlink, the
    definition is **Closest** and for uplink, it is **Composite**."""

    CLOSEST = 1
    r"""Integration bandwidth is derived from the closest LTE carrier. Offset power reference is set to **Closest** internally."""

    COMPOSITE = 2
    r"""Integration bandwidth is derived from the aggregated sub-block bandwidth. Offset power reference is set as **Composite
    Sub-Block**."""


class AcpRbwAutoBandwidth(Enum):
    """AcpRbwAutoBandwidth."""

    FALSE = 0
    r"""The measurement uses the RBW that you specify in the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_BANDWIDTH` attribute."""

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
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses a sweep time of 1 ms."""


class AcpPowerUnits(Enum):
    """AcpPowerUnits."""

    DBM = 0
    r"""The absolute powers are reported in dBm."""

    DBM_BY_HZ = 1
    r"""The absolute powers are reported in dBm/Hz."""


class AcpMeasurementMethod(Enum):
    """AcpMeasurementMethod."""

    NORMAL = 0
    r"""The ACP measurement acquires the spectrum using the same signal analyzer setting across frequency bands. Use this
    method when measurement speed is desirable over higher dynamic range."""

    DYNAMIC_RANGE = 1
    r"""The ACP measurement acquires the spectrum using the hardware-specific optimizations for different frequency bands. Use
    this method to get the best dynamic range. **Supported Devices**: PXIe-5665/5668"""

    SEQUENTIAL_FFT = 2
    r"""The ACP measurement acquires all the samples specified by the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SWEEP_TIME_INTERVAL` attribute and divides them in to smaller chunks of
    equal size defined by the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute.
    FFT is computed for each chunk. The resultant FFTs are averaged to get the spectrum used to compute the ACP.
    If the total acquired samples is not an integer multiple of the FFT size, the remaining samples at the end of
    the acquisition are not used.
    
    Sequential FFT method should be used for the following scenarios.
    
    #. While performing fast ACP measurements by utilizing smaller FFT sizes. However, accuracy of the results may be reduced.
    
    #. When measuring signals with time-varying spectral characteristics, sequential FFT with overlap mode set to Automatic should be used.
    
    #. For accurate power measurements when the power characteristics of the signal vary over time averaging is allowed.
    
    The following attributes have limited support when you set the ACP Measurement Method attribute to **Sequential
    FFT**.
    
    +-----------------------------------------------------------------------------+---------------------+
    | Property                                                                    | Supported Value     |
    +=============================================================================+=====================+
    | :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_AUTO_BANDWIDTH`  | True                |
    +-----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_RBW_FILTER_TYPE`            | FFT Based           |
    +-----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_COUNT`            | >=1                 |
    +-----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS` | 1                   |
    +-----------------------------------------------------------------------------+---------------------+
    | :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS` | RF Center Frequency |
    +-----------------------------------------------------------------------------+---------------------+
    
    .. note::
       For multi-span FFT, the averaging count should be 1."""


class AcpNoiseCalibrationMode(Enum):
    """AcpNoiseCalibrationMode."""

    MANUAL = 0
    r"""When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_MODE` attribute to **Calibrate Noise
    Floor**, you can initiate instrument noise calibration for ACP measurement manually. When you set the ACP Meas Mode
    attribute to **Measure**, you can initiate the ACP measurement manually."""

    AUTO = 1
    r"""When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_COMPENSATION_ENABLED` attribute to **True**,
    RFmx sets the :py:attr:`~nirfmxinstr.attribute.AttributeID.INPUT_ISOLATION_ENABLED` attribute to **Enabled** and
    calibrates the instrument noise in the current state of the instrument. RFmx then resets Input Isolation Enabled
    attribute and performs the ACP measurement including compensation for the noise contribution of the instrument. RFmx
    skips noise calibration in this mode if valid noise calibration data is already cached.
    
    When you set ACP Noise Comp Enabled to **False**, RFmx does not calibrate instrument noise and performs the ACP
    measurement without compensating for the noise contribution of the instrument."""


class AcpNoiseCalibrationAveragingAuto(Enum):
    """AcpNoiseCalibrationAveragingAuto."""

    FALSE = 0
    r"""RFmx uses the averages that you set for
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NOISE_CALIBRATION_AVERAGING_COUNT` attribute."""

    TRUE = 1
    r"""RFmx uses the following averaging counts:
    
    When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_MEASUREMENT_METHOD` attribute to **Normal** or
    **Sequential FFT**, RFmx uses a noise calibration averaging count of 32.
    
    When you set the ACP Meas Method attribute to **Dynamic Range** and sweep time is less than 5 ms, RFmx uses a
    noise calibration averaging count of 15.
    
    When you set the ACP Meas Method attribute to **Dynamic Range** and sweep time is greater than or equal to 5
    ms, RFmx uses a noise calibration averaging count of 5."""


class AcpNoiseCompensationEnabled(Enum):
    """AcpNoiseCompensationEnabled."""

    FALSE = 0
    r"""Disables compensation of the channel powers for the noise floor of the signal analyzer."""

    TRUE = 1
    r"""Enables compensation of the channel powers for the noise floor of the signal analyzer. The noise floor of the signal
    analyzer is measured for the RF path used by the ACP measurement and cached for future use. If the signal analyzer or
    the measurement parameters change, noise floors are remeasured.
    
    **Supported Devices**: PXIe-5663/5665/5668, PXIe-5830/5831/5832/5842/5860"""


class AcpNoiseCompensationType(Enum):
    """AcpNoiseCompensationType."""

    ANALYZER_AND_TERMINATION = 0
    r"""Compensates for noise from the analyzer and the 50 ohm termination. The measured power values are in excess of the
    thermal noise floor."""

    ANALYZER_ONLY = 1
    r"""Compensates for analyzer noise only."""


class AcpAveragingEnabled(Enum):
    """AcpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The ACP measurement uses the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_AVERAGING_COUNT` attribute as
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
    r"""ACP measurement is performed on the acquired signal."""

    CALIBRATE_NOISE_FLOOR = 1
    r"""Manual noise calibration of the signal analyzer is performed for the ACP measurement."""


class AcpFftOverlapMode(Enum):
    """AcpFftOverlapMode."""

    DISABLED = 0
    r"""Disables the overlap between the FFT chunks."""

    AUTOMATIC = 1
    r"""Measurement sets the  number of overlapped samples between consecutive FFT chunks to 50% of the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_SEQUENTIAL_FFT_SIZE` attribute value."""

    USER_DEFINED = 2
    r"""Measurement uses the overlap that you specify in the :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FFT_OVERLAP`
    attribute."""


class AcpIFOutputPowerOffsetAuto(Enum):
    """AcpIFOutputPowerOffsetAuto."""

    FALSE = 0
    r"""The measurement sets the IF output power level offset using the values of the
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_NEAR_IF_OUTPUT_POWER_OFFSET` and
    :py:attr:`~nirfmxlte.attributes.AttributeID.ACP_FAR_IF_OUTPUT_POWER_OFFSET` attributes."""

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
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_RBW_FILTER_BANDWIDTH` attribute."""

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


class ChpSweepTimeAuto(Enum):
    """ChpSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses a sweep time of 1 ms."""


class ChpNoiseCalibrationMode(Enum):
    """ChpNoiseCalibrationMode."""

    MANUAL = 0
    r"""When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_MEASUREMENT_MODE` attribute to **Calibrate Noise
    Floor**, you can initiate instrument noise calibration for CHP measurement manually. When you set the CHP Meas Mode
    attribute to **Measure**, you can initiate the CHP measurement manually."""

    AUTO = 1
    r"""When you set the :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_NOISE_COMPENSATION_ENABLED` attribute to **True**,
    RFmx sets the :py:attr:`~nirfmxinstr.attribute.AttributeID.INPUT_ISOLATION_ENABLED` attribute to **Enabled** and
    calibrates the instrument noise in the current state of the instrument. RFmx then resets the Input Isolation Enabled
    attribute and performs the CHP measurement, including compensation for the noise contribution of the instrument. RFmx
    skips noise calibration in this mode if valid noise calibration data is already cached.
    
    When you set the CHP Noise Comp Enabled attribute to **False**, RFmx does not calibrate instrument noise and
    performs the CHP measurement without compensating for the noise contribution of the instrument."""


class ChpNoiseCalibrationAveragingAuto(Enum):
    """ChpNoiseCalibrationAveragingAuto."""

    FALSE = 0
    r"""RFmx uses the averages that you set for the
    :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_NOISE_CALIBRATION_AVERAGING_COUNT` attribute."""

    TRUE = 1
    r"""RFmx uses a noise calibration averaging count of 32."""


class ChpNoiseCompensationEnabled(Enum):
    """ChpNoiseCompensationEnabled."""

    FALSE = 0
    r"""Disables noise compensation."""

    TRUE = 1
    r"""Enables noise compensation."""


class ChpNoiseCompensationType(Enum):
    """ChpNoiseCompensationType."""

    ANALYZER_AND_TERMINATION = 0
    r"""Compensates for noise from the analyzer and the 50 ohm termination. The measured power values are in excess of the
    thermal noise floor."""

    ANALYZER_ONLY = 1
    r"""Compensates only for analyzer noise."""


class ChpAveragingEnabled(Enum):
    """ChpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The CHP measurement uses the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.CHP_AVERAGING_COUNT` attribute as
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
    r"""CHP measurement is performed on the acquired signal."""

    CALIBRATE_NOISE_FLOOR = 1
    r"""Manual noise calibration of the signal analyzer is performed for the CHP measurement."""


class ChpAmplitudeCorrectionType(Enum):
    """ChpAmplitudeCorrectionType."""

    RF_CENTER_FREQUENCY = 0
    r"""All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the
    RF center frequency."""

    SPECTRUM_FREQUENCY_BIN = 1
    r"""An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that
    frequency."""


class ObwRbwAutoBandwidth(Enum):
    """ObwRbwAutoBandwidth."""

    FALSE = 0
    r"""The measurement uses the RBW that you specify in the
    :py:attr:`~nirfmxlte.attributes.AttributeID.OBW_RBW_FILTER_BANDWIDTH` attribute."""

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
    :py:attr:`~nirfmxlte.attributes.AttributeID.OBW_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses a sweep time of 1 ms."""


class ObwAveragingEnabled(Enum):
    """ObwAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The OBW measurement uses the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.OBW_AVERAGING_COUNT` attribute as
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

    GENERAL_NS_01 = 0
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1.5-1, 6.6.2.1.5-2,
    6.6.2.1A.5-1, 6.6.2.1A.1.5-2, 6.6.2.1A.1.5-3, and 6.6.2.1A.5-4 in section 6.6.2 of the *3GPP TS 36.521-1*
    specification."""

    NS_03_OR_NS_11_OR_NS_20_OR_NS_21 = 1
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.1-1 and
    6.6.2.2.5.1-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS_04 = 2
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.3.2-3 in section
    6.6.2 of the *3GPP TS 36.521-1* specification.
    
    .. note::
       When :py:attr:`~nirfmxlte.attributes.AttributeID.COMPONENT_CARRIER_BANDWIDTH` is **1.4 M** or **3.0 M**, the
       measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.2-1 in section 6.6.2 of
       the *3GPP TS 36.521-1* specification."""

    NS_06_OR_NS_07 = 3
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.3-1 and
    6.6.2.2.5.3-2 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    CA_NS_04 = 4
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.1.5.1-1 in section
    6.6.2 of the *3GPP TS 36.521-1* specification. This mask applies only for aggregated carriers."""

    CUSTOM = 5
    r"""You need to configure the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_NUMBER_OF_OFFSETS`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_START_FREQUENCY`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_STOP_FREQUENCY`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_START`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_STOP`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_SIDEBAND`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_BANDWIDTH`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_TYPE`, and
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_BANDWIDTH_INTEGRAL` attributes for each offset."""

    GENERAL_CA_CLASS_B = 6
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.1A.1.5-3 and 6.6.2.1A.1.5-4
    in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    CA_NC_NS_01 = 7
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.3.5-1 and 6.6.2.2A.3.5-2
    in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS_27_OR_NS_43 = 8
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5-1 in section 6.6.2.2.5
    of the *3GPP TS 36.101-1* specification."""

    NS_35 = 9
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.5.5-1 in section
    6.6.2.2.5.5 of the *3GPP TS 36.521-1* specification."""

    NS_28 = 10
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2.6-1 in section 6.6.2.2.6
    of the *3GPP TS 36.101-1* specification."""

    CA_NS_09 = 11
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.2-1 in section
    6.6.2.2A.2, and Table 6.6.2.2A.3-1 in section 6.6.2.2A.3 of the *3GPP TS 36.101-1* specification."""

    CA_NS_10 = 12
    r"""The measurement selects offset frequencies and limits for the SEM as defined in Table 6.6.2.2A.4-1 in section
    6.6.2.2A.4 of the *3GPP TS 36.101-1* specification."""


class SemDownlinkMaskType(Enum):
    """SemDownlinkMaskType."""

    ENODEB_CATEGORY_BASED = 0
    r"""The limits are applied based on :py:attr:`~nirfmxlte.attributes.AttributeID.ENODEB_CATEGORY` attribute."""

    BAND_46 = 1
    r"""The limits are applied based on Band 46 test requirements."""

    CUSTOM = 5
    r"""You need to configure the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_NUMBER_OF_OFFSETS`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_START_FREQUENCY`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_STOP_FREQUENCY`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_START`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_STOP`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RELATIVE_LIMIT_START`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RELATIVE_LIMIT_STOP`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_SIDEBAND`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_BANDWIDTH`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_TYPE`, and
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_BANDWIDTH_INTEGRAL` attributes for each offset."""


class SemSidelinkMaskType(Enum):
    """SemSidelinkMaskType."""

    GENERAL_NS_01 = 0
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.1G.1.5-1 and Table
    6.6.2.1G.3.5-1 in section 6.6.2 of the *3GPP TS 36.521-1* specification."""

    NS_33_OR_NS_34 = 1
    r"""The measurement selects the offset frequencies and limits for the SEM as defined in Table 6.6.2.2G.1.5-1 in section
    6.6.2 of the *3GPP TS 36.521-1* specification."""

    CUSTOM = 5
    r"""You need to configure the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_NUMBER_OF_OFFSETS`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_START_FREQUENCY`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_STOP_FREQUENCY`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_START`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_ABSOLUTE_LIMIT_STOP`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_SIDEBAND`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_BANDWIDTH`,
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_RBW_FILTER_TYPE`, and
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_OFFSET_BANDWIDTH_INTEGRAL` attributes for each offset."""


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
    r"""Specifies the fail in measurement if the power in the segment exceeds both the absolute and relative masks."""

    ABS_OR_REL = 1
    r"""Specifies the fail in measurement if the power in the segment exceeds either the absolute or relative mask."""

    ABSOLUTE = 2
    r"""Specifies the fail in measurement if the power in the segment exceeds the absolute mask."""

    RELATIVE = 3
    r"""Specifies the fail in measurement if the power in the segment exceeds the relative mask."""


class SemSweepTimeAuto(Enum):
    """SemSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement uses a sweep time of 1 ms."""


class SemAveragingEnabled(Enum):
    """SemAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The SEM measurement uses the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.SEM_AVERAGING_COUNT` attribute as
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


class PvtMeasurementMethod(Enum):
    """PvtMeasurementMethod."""

    NORMAL = 0
    r"""The measurement is performed using a single acquisition. Use this method when a high dynamic range is not required."""

    DYNAMIC_RANGE = 1
    r"""The measurement is performed using two acquisitions. Use this method when a higher dynamic range is desirable over the
    measurement speed. **Supported Devices**: PXIe-5644/5645/5646, PXIe-5840/5841/5842/5860"""


class PvtAveragingEnabled(Enum):
    """PvtAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The PVT measurement uses the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.PVT_AVERAGING_COUNT` attribute as
    the number of acquisitions over which the PVT measurement is averaged."""


class PvtAveragingType(Enum):
    """PvtAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""


class PvtMeasurementStatus(Enum):
    """PvtMeasurementStatus."""

    FAIL = 0
    r"""Indicates that the measurement has failed."""

    PASS = 1
    r"""Indicates that the measurement has passed."""


class SlotPhaseSynchronizationMode(Enum):
    """SlotPhaseSynchronizationMode."""

    FRAME = 0
    r"""The frame boundary in the acquired signal is detected, and the measurement is performed over the number of slots
    specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_LENGTH` attribute, starting at the
    offset from the boundary specified by the :py:attr:`~nirfmxlte.attributes.AttributeID.SLOTPHASE_MEASUREMENT_OFFSET`
    attribute. When the :py:attr:`~nirfmxlte.attributes.AttributeID.TRIGGER_TYPE` attribute is set to **Digital**, the
    measurement expects a trigger at the frame boundary."""

    SLOT = 1
    r"""The slot boundary in the acquired signal is detected, and the measurement is performed over the number of slots
    specified by the SlotPhase Meas Length attribute, starting at the offset from the boundary specified by the SlotPhase
    Meas Offset attribute. When the Trigger Type attribute is set to **Digital**, the measurement expects a trigger at any
    slot boundary."""


class SlotPhaseExclusionPeriodEnabled(Enum):
    """SlotPhaseExclusionPeriodEnabled."""

    FALSE = 0
    r"""Phase is calculated on complete slots."""

    TRUE = 1
    r"""Phase is calculated on truncated slots. The power changes at the slot boundaries are detected by the measurement, and
    the defined 3GPP specification period is excluded from the slots being measured."""


class SlotPhaseCommonClockSourceEnabled(Enum):
    """SlotPhaseCommonClockSourceEnabled."""

    FALSE = 0
    r"""The Sample Clock error is estimated independently."""

    TRUE = 1
    r"""The Sample Clock error is estimated from carrier frequency offset."""


class SlotPhaseSpectrumInverted(Enum):
    """SlotPhaseSpectrumInverted."""

    FALSE = 0
    r"""The spectrum of the measured signal is not inverted."""

    TRUE = 1
    r"""The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components."""


class SlotPowerCommonClockSourceEnabled(Enum):
    """SlotPowerCommonClockSourceEnabled."""

    FALSE = 0
    r"""The Sample Clock error is estimated independently."""

    TRUE = 1
    r"""The Sample Clock error is estimated from carrier frequency offset."""


class SlotPowerSpectrumInverted(Enum):
    """SlotPowerSpectrumInverted."""

    FALSE = 0
    r"""The spectrum of the measured signal is not inverted."""

    TRUE = 1
    r"""The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components."""


class TxpAveragingEnabled(Enum):
    """TxpAveragingEnabled."""

    FALSE = 0
    r"""The number of acquisitions is 1."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxlte.attributes.AttributeID.TXP_AVERAGING_COUNT` for the number of
    acquisitions over which the measurement is averaged."""


class AcquisitionBandwidthOptimizationEnabled(Enum):
    """AcquisitionBandwidthOptimizationEnabled."""

    FALSE = 0
    r"""RFmx does not optimize acquisition bandwidth and will be based on the Nyquist criterion. The value of the acquisition
    center frequency is the same as the value of the :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` that you
    configure."""

    TRUE = 1
    r"""RFmx positions the acquisition center frequency to acquire the least bandwidth based on the configuration and span
    needed for the measurement. This helps in reducing the amount of data to process for the measurement, thus improving
    the speed. However this might cause the LO to be positioned at a non-dc subcarrier position, hence the measurement
    sensitive to it should have this attribute disabled."""


class TransmitterArchitecture(Enum):
    """TransmitterArchitecture."""

    LO_PER_COMPONENT_CARRIER = 0
    r"""IQ impairments and In-band emission are calculated per component carrier."""

    LO_PER_SUBBLOCK = 1
    r"""Additional subblock based results such as Subblock IQ Offset and Subblock In band emission are calculated apart from
    per carrier results."""


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
    signal configuration. Thereafter, only the :py:attr:`~nirfmxlte.attributes.AttributeID.CENTER_FREQUENCY` and
    :py:attr:`~nirfmxlte.attributes.AttributeID.EXTERNAL_ATTENUATION` attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal.  Refer to the Limitations of the Limited Configuration Change
    Property topic for more details about the limitations of using this mode."""

    REFERENCE_LEVEL = 3
    r"""Signal configuration, other than the reference level, is locked after first Commit of the named signal configuration.
    Thereafter only the :py:attr:`~nirfmxlte.attributes.AttributeID.REFERENCE_LEVEL` attribute value change will be
    considered by subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ
    Power Edge Trigger, NI recommends that you set the
    :py:attr:`~nirfmxlte.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` to **Relative** so that the trigger level
    is automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration
    Change Property topic for more details about the limitations of using this mode."""

    FREQUENCY_AND_REFERENCE_LEVEL = 4
    r"""Signal configuration, other than center frequency, reference level, and external attenuation, is locked after first
    Commit of the named signal configuration. Thereafter only Center Frequency, Reference Level, and External Attenuation
    attribute value changes will be considered by subsequent driver Commits or Initiates of this signal. If you have
    configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power Edge Level Type attribute to
    **Relative** so that the trigger level is automatically adjusted as you adjust the reference level. Refer to the
    Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this
    mode."""

    SELECTED_PORTS_FREQUENCY_AND_REFERENCE_LEVEL = 5
    r"""Signal configuration, other than Selected Ports, Center frequency, Reference level, External attenuation, and RFmxInstr
    configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected
    Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge
    Trigger, NI recommends you set the IQ Power Edge Level Type attribute to **Relative** so that the trigger level is
    automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change
    Property topic for more details about the limitations of using this mode."""


class MeasurementTypes(IntFlag):
    """MeasurementTypes."""

    ACP = 1 << 0
    r""""""

    CHP = 1 << 1
    r""""""

    MODACC = 1 << 2
    r""""""

    OBW = 1 << 3
    r""""""

    SEM = 1 << 4
    r""""""

    PVT = 1 << 5
    r""""""

    SLOTPHASE = 1 << 6
    r""""""

    SLOTPOWER = 1 << 7
    r""""""

    TXP = 1 << 8
    r""""""


class AcpNoiseCalibrationDataValid(Enum):
    """AcpNoiseCalibrationDataValid."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""


class ChpNoiseCalibrationDataValid(Enum):
    """ChpNoiseCalibrationDataValid."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""
