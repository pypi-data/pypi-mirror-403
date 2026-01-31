"""enums.py - Contains enum classes."""

from enum import Enum, IntFlag


class TriggerType(Enum):
    """TriggerType."""

    NONE = 0
    r"""No reference trigger is configured."""

    DIGITAL_EDGE = 1
    r"""The reference trigger is not asserted until a digital edge is detected. The source of the digital edge is specified
    using the :py:attr:`~nirfmxwlan.attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE` attribute."""

    IQ_POWER_EDGE = 2
    r"""The reference trigger is asserted when the signal changes past the level specified by the slope (rising or falling),
    which is configured using the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute."""

    SOFTWARE = 3
    r"""The reference trigger is not asserted until a software trigger occurs."""


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
    :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute."""

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
    :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION` attribute."""

    AUTO = 1
    r"""The measurement computes the minimum quiet time used for triggering."""


class TriggerGateEnabled(Enum):
    """TriggerGateEnabled."""

    FALSE = 0
    r"""Gate for SEM measurements is disabled."""

    TRUE = 1
    r"""Gate for SEM measurements is enabled."""


class Standard(Enum):
    """Standard."""

    STANDARD_802_11_AG = 0
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard 802.11a-1999* and *IEEE Standard 802.11g-2003*."""

    STANDARD_802_11_B = 1
    r"""Corresponds to the DSSS based PPDU formats as defined in *IEEE Standard 802.11b-1999*."""

    STANDARD_802_11_J = 2
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard 802.11j-2004*."""

    STANDARD_802_11_P = 3
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard 802.11p-2010*."""

    STANDARD_802_11_N = 4
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard 802.11n-2009*."""

    STANDARD_802_11_AC = 5
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard 802.11ac-2013*."""

    STANDARD_802_11_AX = 6
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard P802.11ax/D8.0*."""

    STANDARD_802_11_BE = 7
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard P802.11be/D7.0*."""

    STANDARD_802_11_BN = 8
    r"""Corresponds to the OFDM based PPDU formats as defined in *IEEE Standard P802.11bn/D1.2*."""

    UNKNOWN = -1
    r"""Indicates that the standard is not detected."""


class OfdmTransmitPowerClass(Enum):
    """OfdmTransmitPowerClass."""

    A = 0
    r"""Maximum STA Transmit Power is 1 mW."""

    B = 1
    r"""Maximum STA Transmit Power is 10 mW."""

    C = 2
    r"""Maximum STA Transmit Power is 100 mW."""

    D = 3
    r"""Maximum STA Transmit Power is 760 mW."""


class OfdmFrequencyBand(Enum):
    """OfdmFrequencyBand."""

    OFDM_FREQUENCY_BAND_2_4GHZ = 0
    r"""Corresponds to the ISM band ranging from 2.4 GHz to 2.5 GHz."""

    OFDM_FREQUENCY_BAND_5GHZ = 1
    r"""Corresponds to the 5 GHz band."""


class OfdmAutoPpduTypeDetectionEnabled(Enum):
    """OfdmAutoPpduTypeDetectionEnabled."""

    FALSE = 0
    r"""Auto detection of the PPDU type is disabled."""

    TRUE = 1
    r"""Auto detection of the PPDU type is enabled."""


class OfdmPpduType(Enum):
    """OfdmPpduType."""

    NON_HT = 0
    r"""Specifies an 802.11a, 802.11j, or 802.11p PPDU type, or 802.11n, 802.11ac, or 802.11ax PPDU type when operating in the
    Non-HT mode."""

    MIXED = 1
    r"""Specifies the HT-Mixed PPDU (802.11n) type."""

    GREENFIELD = 2
    r"""Specifies the HT-Greenfield PPDU (802.11n) type."""

    SU = 3
    r"""Specifies the VHT SU PPDU type if you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to
    **802.11ac** or the HE SU PPDU type if you set the Standard attribute to **802.11ax**."""

    MU = 4
    r"""Specifies the VHT MU PPDU type if you set the Standard attribute to **802.11ac**, the HE MU PPDU type if you set the
    Standard attribute to **802.11ax**, or the EHT MU PPDU type if you set the Standard attribute to **802.11be**."""

    EXTENDED_RANGE_SU = 5
    r"""Specifies the HE Extended Range SU PPDU (802.11ax) type."""

    TRIGGER_BASED = 6
    r"""Specifies the HE TB PPDU if you set the Standard attribute to **802.11ax** , the EHT TB PPDU if you set the Standard
    attribute to **802.11be** or the UHR TB PPDU if you set the Standard attribute to **802.11bn** ."""

    ELR = 7
    r""""""


class OfdmHeaderDecodingEnabled(Enum):
    """OfdmHeaderDecodingEnabled."""

    FALSE = 0
    r"""Header information is not read from the header fields in the PPDU. You must configure the following properties:
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_NUMBER_OF_USERS`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_MCS_INDEX`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_SIZE`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_OFFSET_MRU_INDEX`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_GUARD_INTERVAL_TYPE`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_LTF_SIZE`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_SPACE_TIME_STREAM_OFFSET`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_NUMBER_OF_HE_SIG_B_SYMBOLS`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_PE_DISAMBIGUITY`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_SIG_COMPRESSION_ENABLED`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_NUMBER_OF_SIG_SYMBOLS`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_DISTRIBUTION_BANDWIDTH`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_IM_PILOTS_ENABLED`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_UNEQUAL_MODULATION_ENABLED`
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_UNEQUAL_MODULATION_PATTERN_INDEX`"""

    TRUE = 1
    r"""Header information is obtained by decoding the header fields in the PPDU."""


class OfdmSigCompressionEnabled(Enum):
    """OfdmSigCompressionEnabled."""

    FALSE = 0
    r"""Specifies that SIG compression is disabled."""

    TRUE = 1
    r"""Specifies that SIG compression is enabled."""


class OfdmFecCodingType(Enum):
    """OfdmFecCodingType."""

    BCC = 0
    r"""The FEC coding type used is binary convolutional code (BCC)."""

    LDPC = 1
    r"""The FEC coding type used is low-density parity check (LDPC)."""


class OfdmRUType(Enum):
    """OfdmRUType."""

    RRU = 0
    r"""Contiguous subcarriers are present in the RU."""

    DRU = 1
    r"""Non-contiguous subcarriers are present in the RU."""


class OfdmGuardIntervalType(Enum):
    """OfdmGuardIntervalType."""

    ONE_BY_FOUR = 0
    r"""The guard interval is 1/4th of the IFFT duration."""

    ONE_BY_EIGHT = 1
    r"""The guard interval is 1/8th of the IFFT duration."""

    ONE_BY_SIXTEEN = 2
    r"""The guard interval is 1/16th of the IFFT duration."""


class OfdmLtfSize(Enum):
    """OfdmLtfSize."""

    OFDM_LTF_SIZE_4X = 0
    r"""Specifies that the LTF symbol size is 4x."""

    OFDM_LTF_SIZE_2X = 1
    r"""Specifies that the LTF symbol size is 2x."""

    OFDM_LTF_SIZE_1X = 2
    r"""Specifies that the LTF symbol size is 1x."""

    NOT_APPLICABLE = -1
    r"""Specifies that the LTF Size is invalid for the current waveform."""


class OfdmStbcEnabled(Enum):
    """OfdmStbcEnabled."""

    FALSE = 0
    r"""Specifies that space-time block coding is disabled."""

    TRUE = 1
    r"""Specifies that space-time block coding is enabled."""


class OfdmDcmEnabled(Enum):
    """OfdmDcmEnabled."""

    FALSE = 0
    r"""Specifies that DCM is not applied to the data field for 802.11ax signals."""

    TRUE = 1
    r"""Specifies that DCM is applied to the data field for 802.11ax signals."""


class Ofdm2xLdpcEnabled(Enum):
    """Ofdm2xLdpcEnabled."""

    FALSE = 0
    r"""Specifies that 2xLDPC is disabled."""

    TRUE = 1
    r"""Specifies that 2xLDPC is enabled."""


class OfdmIMPilotsEnabled(Enum):
    """OfdmIMPilotsEnabled."""

    FALSE = 0
    r"""Specifies that Interference Mitigating Pilots are absent."""

    TRUE = 1
    r"""Specifies that Interference Mitigating Pilots are present."""


class OfdmUnequalModulationEnabled(Enum):
    """OfdmUnequalModulationEnabled."""

    FALSE = 0
    r"""Specifies that Unequal Modulation is disabled."""

    TRUE = 1
    r"""Specifies that Unequal Modulation is enabled."""


class OfdmMUMimoLtfModeEnabled(Enum):
    """OfdmMUMimoLtfModeEnabled."""

    FALSE = 0
    r"""Specifies that the LTF sequence uses single stream pilots."""

    TRUE = 1
    r"""Specifies that the LTF sequence is HE masked."""


class OfdmPreamblePuncturingEnabled(Enum):
    """OfdmPreamblePuncturingEnabled."""

    FALSE = 0
    r"""Indicates that preamble puncturing is disabled."""

    TRUE = 1
    r"""Indicates that preamble puncturing is enabled."""


class OfdmAutoPhaseRotationDetectionEnabled(Enum):
    """OfdmAutoPhaseRotationDetectionEnabled."""

    FALSE = 0
    r"""Specifies that auto detection of phase rotation coefficient is disabled."""

    TRUE = 1
    r"""Specifies that auto detection of phase rotation coefficient is enabled."""


class OfdmPhaseRotationCoefficient1(Enum):
    """OfdmPhaseRotationCoefficient1."""

    PLUS_ONE = 0
    r"""Specifies that phase rotation coefficient 1 is +1."""

    MINUS_ONE = 1
    r"""Specifies that phase rotation coefficient 1 is –1."""


class OfdmPhaseRotationCoefficient2(Enum):
    """OfdmPhaseRotationCoefficient2."""

    PLUS_ONE = 0
    r"""Specifies that phase rotation coefficient 2 is +1."""

    MINUS_ONE = 1
    r"""Specifies that phase rotation coefficient 2 is –1."""


class OfdmPhaseRotationCoefficient3(Enum):
    """OfdmPhaseRotationCoefficient3."""

    PLUS_ONE = 0
    r"""Specifies that phase rotation coefficient 3 is +1."""

    MINUS_ONE = 1
    r"""Specifies that phase rotation coefficient 3 is –1."""


class DsssModAccAcquisitionLengthMode(Enum):
    """DsssModAccAcquisitionLengthMode."""

    MANUAL = 0
    r"""Uses the acquisition length specified by the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH` attribute."""

    AUTO = 1
    r"""Computes the acquisition length based on the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_MEASUREMENT_OFFSET` attribute  and the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_MAXIMUM_MEASUREMENT_LENGTH` attribute."""


class DsssModAccPulseShapingFilterType(Enum):
    """DsssModAccPulseShapingFilterType."""

    RECTANGULAR = 0
    r"""Specifies that the transmitter uses a rectangular pulse shaping filter. The measurement uses an impulse response as the
    matched filter."""

    RAISED_COSINE = 1
    r"""Specifies that the transmitter uses a raised cosine pulse shaping filter. The measurement uses an impulse response as
    the matched filter."""

    ROOT_RAISED_COSINE = 2
    r"""Specifies that the transmitter uses a root raised cosine pulse shaping filter. The measurement uses a root raised
    cosine filter as the matched filter."""

    GAUSSIAN = 3
    r"""Specifies that the transmitter uses a Gaussian filter. The measurement uses a Gaussian as the matched filter."""


class DsssModAccEqualizationEnabled(Enum):
    """DsssModAccEqualizationEnabled."""

    FALSE = 0
    r"""Disables equalization."""

    TRUE = 1
    r"""Enables equalization."""


class DsssModAccBurstStartDetectionEnabled(Enum):
    """DsssModAccBurstStartDetectionEnabled."""

    FALSE = 0
    r"""Disables detection of a rising edge of the burst in the acquired waveform for measurement."""

    TRUE = 1
    r"""Enables detection of a rising edge of the burst in the acquired waveform for measurement."""


class DsssModAccEvmUnit(Enum):
    """DsssModAccEvmUnit."""

    PERCENTAGE = 0
    r"""Returns the EVM results as a percentage."""

    DB = 1
    r"""Returns the EVM results in dB."""


class DsssModAccPowerMeasurementEnabled(Enum):
    """DsssModAccPowerMeasurementEnabled."""

    FALSE = 0
    r"""Disables power measurement."""

    TRUE = 1
    r"""Enables power measurement."""


class DsssModAccFrequencyErrorCorrectionEnabled(Enum):
    """DsssModAccFrequencyErrorCorrectionEnabled."""

    FALSE = 0
    r"""Disables frequency error correction."""

    TRUE = 1
    r"""Enables frequency error correction."""


class DsssModAccChipClockErrorCorrectionEnabled(Enum):
    """DsssModAccChipClockErrorCorrectionEnabled."""

    FALSE = 0
    r"""Disables the chip clock error correction."""

    TRUE = 1
    r"""Enables the chip clock error correction."""


class DsssModAccIQOriginOffsetCorrectionEnabled(Enum):
    """DsssModAccIQOriginOffsetCorrectionEnabled."""

    FALSE = 0
    r"""Disables the I/Q origin offset correction."""

    TRUE = 1
    r"""Enables the I/Q origin offset correction."""


class DsssModAccSpectrumInverted(Enum):
    """DsssModAccSpectrumInverted."""

    FALSE = 0
    r"""The spectrum of the measured signal is not inverted."""

    TRUE = 1
    r"""The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components."""


class DsssModAccDataDecodingEnabled(Enum):
    """DsssModAccDataDecodingEnabled."""

    FALSE = 0
    r"""Disables data decoding."""

    TRUE = 1
    r"""Enables data decoding."""


class DsssModAccAveragingEnabled(Enum):
    """DsssModAccAveragingEnabled."""

    FALSE = 0
    r"""Performs measurement on a single acquisition."""

    TRUE = 1
    r"""Measurement uses the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_COUNT` attribute for the number
    of acquisitions using which the results are averaged."""


class DsssModAccDataModulationFormat(Enum):
    """DsssModAccDataModulationFormat."""

    DSSS_1_MBPS = 0
    r"""Indicates that the modulation format is DSSS and the data rate is 1 Mbps."""

    DSSS_2_MBPS = 1
    r"""Indicates that the modulation format is DSSS and the data rate is 2 Mbps."""

    CCK_5_5_MBPS = 2
    r"""Indicates that the modulation format is CCK and the data rate is 5.5 Mbps."""

    CCK_11_MBPS = 3
    r"""Indicates that the modulation format is CCK and the data rate is 11 Mbps."""

    PBCC_5_5_MBPS = 4
    r"""Indicates that the modulation format is PBCC and the data rate is 5.5 Mbps."""

    PBCC_11_MBPS = 5
    r"""Indicates that the modulation format is PBCC and the data rate is 11 Mbps."""

    PBCC_22_MBPS = 6
    r"""Indicates that the modulation format is PBCC and the data rate is 22 Mbps."""

    PBCC_33_MBPS = 7
    r"""Indicates that the modulation format is PBCC and the data rate is 33 Mbps."""


class DsssModAccPreambleType(Enum):
    """DsssModAccPreambleType."""

    LONG = 0
    r"""Indicates that the PPDU has a long PHY preamble and header."""

    SHORT = 1
    r"""Indicates that the PPDU has a short PHY preamble and header."""


class DsssModAccPayloadHeaderCrcStatus(Enum):
    """DsssModAccPayloadHeaderCrcStatus."""

    FAIL = 0
    r"""Returns that the header CRC failed."""

    PASS = 1
    r"""Returns that the header CRC passed."""


class DsssModAccPsduCrcStatus(Enum):
    """DsssModAccPsduCrcStatus."""

    FAIL = 0
    r"""Indicates that the PSDU CRC failed."""

    PASS = 1
    r"""Indicates that the PSDU CRC passed."""


class OfdmModAccAveragingEnabled(Enum):
    """OfdmModAccAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the value of the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT`
    attribute as the number of acquisitions over which the results are computed according to the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE` attribute."""


class OfdmModAccAveragingType(Enum):
    """OfdmModAccAveragingType."""

    RMS = 0
    r"""The OFDMModAcc measurement is performed on I/Q data acquired in each averaging count. The scalar results and traces are
    linearly averaged over the averaging count."""

    VECTOR = 5
    r"""The acquired I/Q data is averaged across averaging count after aligning the data in time and phase using the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_VECTOR_AVERAGING_TIME_ALIGNMENT_ENABLED` and
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_VECTOR_AVERAGING_PHASE_ALIGNMENT_ENABLED` properties,
    respectively. The averaged I/Q data is used for the measurement. Refer to the `OFDMModAcc Vector Averaging
    <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/ofdmmodacc-vector-averaging.html>`_ concept topic for more information.
    
    .. note::
       You must ensure that the frequency reference is locked between the generator and the analyzer."""


class OfdmModAccVectorAveragingTimeAlignmentEnabled(Enum):
    """OfdmModAccVectorAveragingTimeAlignmentEnabled."""

    FALSE = 0
    r"""Disables time alignment for the acquired I/Q data across multiple acquisitions."""

    TRUE = 1
    r"""Enables time alignment for the acquired I/Q data across multiple acquisitions."""


class OfdmModAccVectorAveragingPhaseAlignmentEnabled(Enum):
    """OfdmModAccVectorAveragingPhaseAlignmentEnabled."""

    FALSE = 0
    r"""Disables phase alignment for the acquired I/Q data across multiple acquisitions."""

    TRUE = 1
    r"""Enables phase alignment for the acquired I/Q data across multiple acquisitions."""


class OfdmModAccMeasurementMode(Enum):
    """OfdmModAccMeasurementMode."""

    MEASURE = 0
    r"""The OFDMModAcc measurement is performed on the acquired signal."""

    CALIBRATE_NOISE_FLOOR = 1
    r"""The OFDMModAcc measurement measures the noise floor of the instrument across the frequency range of interest determined
    by the carrier frequency and channel bandwidth. In this mode, the measurement expects that the signal generator to be
    turned off and checks whether no signal power is detected at the RF In port of the analyzer beyond a certain threshold.
    All scalar results and traces are invalid in this mode. Even if the instrument noise floor is previously calibrated,
    the measurement performs all the required acquisitions and overwrites any pre-existing noise floor calibration data."""


class OfdmModAccEvmReferenceDataSymbolsMode(Enum):
    """OfdmModAccEvmReferenceDataSymbolsMode."""

    ACQUIRED_WAVEFORM = 0
    r"""Reference data symbols for an EVM computation are created using the acquired waveform."""

    REFERENCE_WAVEFORM = 1
    r"""Reference data symbols for an EVM computation are created using the reference waveform."""


class OfdmModAccEvmUnit(Enum):
    """OfdmModAccEvmUnit."""

    PERCENTAGE = 0
    r"""The EVM results are returned as a percentage."""

    DB = 1
    r"""The EVM results are returned in dB."""


class OfdmModAccAcquisitionLengthMode(Enum):
    """OfdmModAccAcquisitionLengthMode."""

    MANUAL = 0
    r"""Uses the acquisition length specified by the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE` attribute."""

    AUTO = 1
    r"""Computes the acquisition length based on the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` and the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MAXIMUM_MEASUREMENT_LENGTH` attributes."""


class OfdmModAccCombinedSignalDemodulationEnabled(Enum):
    """OfdmModAccCombinedSignalDemodulationEnabled."""

    FALSE = 0
    r"""Disables combined signal demodulation analysis."""

    TRUE = 1
    r"""Enables combined signal demodulation analysis."""


class OfdmModAccBurstStartDetectionEnabled(Enum):
    """OfdmModAccBurstStartDetectionEnabled."""

    FALSE = 0
    r"""Disables detecting a rising edge of a burst in the acquired waveform."""

    TRUE = 1
    r"""Enables detecting a rising edge of a burst in the acquired waveform."""


class OfdmModAccFrequencyErrorEstimationMethod(Enum):
    """OfdmModAccFrequencyErrorEstimationMethod."""

    DISABLED = 0
    r"""Carrier frequency error is not computed and the corresponding result is returned as NaN."""

    INITIAL_PREAMBLE = 1
    r"""Initial short and long training fields in the PPDU are used."""

    PREAMBLE = 2
    r"""Initial short and long training fields along with the SIGnal fields are used."""

    PREAMBLE_AND_PILOTS = 3
    r"""The initial short and long training fields, SIGnal fields, and the pilot subcarriers in the DATA field are used."""

    PREAMBLE_PILOTS_AND_DATA = 4
    r"""The initial short and long training fields, SIGnal fields, and all the subcarriers in the DATA field are used."""


class OfdmModAccCommonClockSourceEnabled(Enum):
    """OfdmModAccCommonClockSourceEnabled."""

    FALSE = 0
    r"""Specifies that the transmitter does not use a common reference clock. The OFDMModAcc measurement computes the symbol
    clock error and carrier frequency error independently."""

    TRUE = 1
    r"""Specifies that the transmitter uses a common reference clock. The OFDMModAcc measurement derives the symbol clock error
    from the configured center frequency and carrier frequency error."""


class OfdmModAccCommonPilotErrorScalingReference(Enum):
    """OfdmModAccCommonPilotErrorScalingReference."""

    NONE = 0
    r"""Specifies that Common Pilot Error is computed relative to only LTF and no scaling is performed."""

    AVERAGE_CPE = 1
    r"""Specifies that Common Pilot Error is computed relative to LTF and scaling by average CPE  is performed."""


class OfdmModAccAmplitudeTrackingEnabled(Enum):
    """OfdmModAccAmplitudeTrackingEnabled."""

    FALSE = 0
    r"""Amplitude tracking is disabled."""

    TRUE = 1
    r"""Amplitude tracking is enabled."""


class OfdmModAccPhaseTrackingEnabled(Enum):
    """OfdmModAccPhaseTrackingEnabled."""

    FALSE = 0
    r"""Phase tracking is disabled."""

    TRUE = 1
    r"""Phase tracking is enabled."""


class OfdmModAccSymbolClockErrorCorrectionEnabled(Enum):
    """OfdmModAccSymbolClockErrorCorrectionEnabled."""

    FALSE = 0
    r"""Symbol clock error correction is disabled."""

    TRUE = 1
    r"""Symbol clock error correction is enabled."""


class OfdmModAccSpectrumInverted(Enum):
    """OfdmModAccSpectrumInverted."""

    FALSE = 0
    r"""The spectrum of the measured signal is not inverted."""

    TRUE = 1
    r"""The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components."""


class OfdmModAccChannelEstimationType(Enum):
    """OfdmModAccChannelEstimationType."""

    REFERENCE = 0
    r"""The channel is estimated using long training fields (LTFs) in the preamble and the most recently received midamble, if
    present."""

    REFERENCE_AND_DATA = 1
    r"""The channel is estimated using long training fields (LTFs) in the preamble, the midamble (if present), and the data
    field."""


class OfdmModAccChannelEstimationInterpolationType(Enum):
    """OfdmModAccChannelEstimationInterpolationType."""

    LINEAR = 0
    r"""Linear interpolation is performed on reference channel estimates across subcarriers."""

    TRIANGULAR_SMOOTHING = 1
    r"""Channel estimates are smoothed using a triangular weighted moving average window across subcarriers."""

    WIENER_FILTER = 2
    r"""Wiener filter is used for interpolation and smoothing on reference channel estimates across subcarriers."""


class OfdmModAccChannelEstimationLtfAveragingEnabled(Enum):
    """OfdmModAccChannelEstimationLtfAveragingEnabled."""

    FALSE = 0
    r"""Channel estimation with LTF averaging is disabled."""

    TRUE = 1
    r"""Channel estimation with LTF averaging is enabled."""


class OfdmModAccChannelEstimationLLtfEnabled(Enum):
    """OfdmModAccChannelEstimationLLtfEnabled."""

    FALSE = 0
    r"""Channel estimation on L-LTF is disabled."""

    TRUE = 1
    r"""Channel estimation on L-LTF is enabled."""


class OfdmModAccPowerMeasurementEnabled(Enum):
    """OfdmModAccPowerMeasurementEnabled."""

    FALSE = 0
    r"""Power measurements are disabled."""

    TRUE = 1
    r"""Power measurements are enabled."""


class OfdmModAccChannelMatrixPowerEnabled(Enum):
    """OfdmModAccChannelMatrixPowerEnabled."""

    FALSE = 0
    r"""Channel frequency response matrix power measurements are disabled."""

    TRUE = 1
    r"""Channel frequency response matrix power measurements are enabled."""


class OfdmModAccIQImpairmentsEstimationEnabled(Enum):
    """OfdmModAccIQImpairmentsEstimationEnabled."""

    FALSE = 0
    r"""I/Q impairments estimation is disabled."""

    TRUE = 1
    r"""I/Q impairments estimation is enabled."""


class OfdmModAccIQImpairmentsModel(Enum):
    """OfdmModAccIQImpairmentsModel."""

    TX = 0
    r"""The measurement assumes that the I/Q impairments are introduced by a transmit DUT."""

    RX = 1
    r"""The measurement assumes that the I/Q impairments are introduced by a receive DUT."""


class OfdmModAccIQGainImbalanceCorrectionEnabled(Enum):
    """OfdmModAccIQGainImbalanceCorrectionEnabled."""

    FALSE = 0
    r"""I/Q gain imbalance correction is disabled."""

    TRUE = 1
    r"""I/Q gain imbalance correction is enabled."""


class OfdmModAccIQQuadratureErrorCorrectionEnabled(Enum):
    """OfdmModAccIQQuadratureErrorCorrectionEnabled."""

    FALSE = 0
    r"""I/Q quadrature error correction is disabled."""

    TRUE = 1
    r"""I/Q quadrature error correction is enabled."""


class OfdmModAccIQTimingSkewCorrectionEnabled(Enum):
    """OfdmModAccIQTimingSkewCorrectionEnabled."""

    FALSE = 0
    r"""I/Q timing skew correction is disabled."""

    TRUE = 1
    r"""I/Q timing skew correction is enabled."""


class OfdmModAccIQImpairmentsPerSubcarrierEnabled(Enum):
    """OfdmModAccIQImpairmentsPerSubcarrierEnabled."""

    FALSE = 0
    r"""Independent estimation of I/Q impairments for each subcarrier is disabled."""

    TRUE = 1
    r"""Independent estimation of I/Q impairments for each subcarrier is enabled."""


class OfdmModAccUnusedToneErrorMaskReference(Enum):
    """OfdmModAccUnusedToneErrorMaskReference."""

    LIMIT1 = 0
    r"""Applies the mask corresponding to the case when the transmit power of the DUT is less than or equal to the maximum
    power of MCS7."""

    LIMIT2 = 1
    r"""Applies the mask corresponding to the case when the transmit power of the DUT is more than the maximum power of MCS7."""


class OfdmModAccDataDecodingEnabled(Enum):
    """OfdmModAccDataDecodingEnabled."""

    FALSE = 0
    r"""Disables data decoding."""

    TRUE = 1
    r"""Enables data decoding."""


class OfdmModAccNoiseCompensationEnabled(Enum):
    """OfdmModAccNoiseCompensationEnabled."""

    FALSE = 0
    r"""Disables instrument noise compensation for EVM results."""

    TRUE = 1
    r"""Enables instrument noise compensation for EVM results."""


class OfdmModAccNoiseCompensationInputPowerCheckEnabled(Enum):
    """OfdmModAccNoiseCompensationInputPowerCheckEnabled."""

    FALSE = 0
    r"""Disables the input power check at the RFIn port of the signal analyzer."""

    TRUE = 1
    r"""Enables the input power check at the RFIn port of the signal analyzer."""


class OfdmModAccOptimizeDynamicRangeForEvmEnabled(Enum):
    """OfdmModAccOptimizeDynamicRangeForEvmEnabled."""

    FALSE = 0
    r"""Specifies that the dynamic range is not optimized for EVM measurement."""

    TRUE = 1
    r"""Specifies that the dynamic range is optimized for EVM measurement."""


class OfdmModAccAutoLevelAllowOverflow(Enum):
    """OfdmModAccAutoLevelAllowOverflow."""

    FALSE = 0
    r"""Disables searching for the optimum reference levels while allowing ADC overflow."""

    TRUE = 1
    r"""Enables searching for the optimum reference levels while allowing ADC overflow."""


class OfdmModAccNoiseCompensationApplied(Enum):
    """OfdmModAccNoiseCompensationApplied."""

    FALSE = 0
    r"""Noise compensation is not applied."""

    TRUE = 1
    r"""Noise compensation is applied."""


class OfdmModAccFecCodingType(Enum):
    """OfdmModAccFecCodingType."""

    BCC = 0
    r"""Indicates that the FEC coding type is BCC."""

    LDPC = 1
    r"""Indicates that the FEC coding type is LDPC."""


class OfdmModAccRUType(Enum):
    """OfdmModAccRUType."""

    RRU = 0
    r"""The RU type is rRU."""

    DRU = 1
    r"""The RU type is dRU."""


class OfdmModAccDcmEnabled(Enum):
    """OfdmModAccDcmEnabled."""

    FALSE = 0
    r"""Indicates that DCM is disabled for the specified user."""

    TRUE = 1
    r"""Indicates that DCM is enabled for the specified user."""


class OfdmModAcc2xLdpcEnabled(Enum):
    """OfdmModAcc2xLdpcEnabled."""

    FALSE = 0
    r"""Indicates that 2xLDPC is disabled for the specified user."""

    TRUE = 1
    r"""Indicates that 2xLDPC is enabled for the specified user."""


class OfdmModAccIMPilotsEnabled(Enum):
    """OfdmModAccIMPilotsEnabled."""

    FALSE = 0
    r"""Indicates that interference mitigating pilots are absent."""

    TRUE = 1
    r"""Indicates that interference mitigating pilots are present."""


class OfdmModAccUnequalModulationEnabled(Enum):
    """OfdmModAccUnequalModulationEnabled."""

    FALSE = 0
    r"""Indicates that unequal modulation is disabled for the specified user."""

    TRUE = 1
    r"""Indicates that unequal modulation is enabled for the specified user."""


class OfdmModAccLSigParityCheckStatus(Enum):
    """OfdmModAccLSigParityCheckStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the parity check is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the parity check failed."""

    PASS = 1
    r"""Returns that the parity check passed."""


class OfdmModAccSigCrcStatus(Enum):
    """OfdmModAccSigCrcStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the SIG CRC is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the SIG CRC failed."""

    PASS = 1
    r"""Returns that the SIG CRC passed."""


class OfdmModAccSigBCrcStatus(Enum):
    """OfdmModAccSigBCrcStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the SIG-B CRC  is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the SIG-B CRC failed."""

    PASS = 1
    r"""Returns that the SIG-B CRC passed."""


class OfdmModAccUSigCrcStatus(Enum):
    """OfdmModAccUSigCrcStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the U-SIG CRC is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the U-SIG CRC failed."""

    PASS = 1
    r"""Returns that the U-SIG CRC passed."""


class OfdmModAccEhtSigCrcStatus(Enum):
    """OfdmModAccEhtSigCrcStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the EHT-SIG CRC is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the EHT-SIG CRC failed."""

    PASS = 1
    r"""Returns that the EHT-SIG CRC passed."""


class OfdmModAccUhrSigCrcStatus(Enum):
    """OfdmModAccUhrSigCrcStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the UHR-SIG CRC is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the UHR-SIG CRC failed."""

    PASS = 1
    r"""Returns that the UHR-SIG CRC passed."""


class OfdmModAccElrSigCrcStatus(Enum):
    """OfdmModAccElrSigCrcStatus."""

    NOT_APPLICABLE = -1
    r"""Returns that the ELR-SIG CRC is invalid for the current waveform."""

    FAIL = 0
    r"""Returns that the ELR-SIG CRC failed."""

    PASS = 1
    r"""Returns that the ELR-SIG CRC passed."""


class OfdmModAccPsduCrcStatus(Enum):
    """OfdmModAccPsduCrcStatus."""

    FAIL = 0
    r"""Indicates that the PSDU CRC failed."""

    PASS = 1
    r"""Indicates that the PSDU CRC passed."""


class OfdmModAccPhaseRotationCoefficient1(Enum):
    """OfdmModAccPhaseRotationCoefficient1."""

    PLUS_ONE = 0
    r"""Specifies that phase rotation coefficient 1 is +1."""

    MINUS_ONE = 1
    r"""Specifies that phase rotation coefficient 1 is –1."""


class OfdmModAccPhaseRotationCoefficient2(Enum):
    """OfdmModAccPhaseRotationCoefficient2."""

    PLUS_ONE = 0
    r"""Specifies that phase rotation coefficient 2 is +1."""

    MINUS_ONE = 1
    r"""Specifies that phase rotation coefficient 2 is –1."""


class OfdmModAccPhaseRotationCoefficient3(Enum):
    """OfdmModAccPhaseRotationCoefficient3."""

    PLUS_ONE = 0
    r"""Specifies that phase rotation coefficient 3 is +1."""

    MINUS_ONE = 1
    r"""Specifies that phase rotation coefficient 3 is –1."""


class SemMaskType(Enum):
    """SemMaskType."""

    STANDARD = 0
    r"""Mask limits are configured as per the specified standard, channel bandwidth, and band."""

    CUSTOM = 1
    r"""The measurement uses the mask limits that you specify."""


class SemOffsetSideband(Enum):
    """SemOffsetSideband."""

    NEGATIVE = 0
    r"""Configures a lower offset segment to the left of the carrier."""

    POSITIVE = 1
    r"""Configures an upper offset segment to the right of the carrier."""

    BOTH = 2
    r"""Configures both negative and positive offset segments."""


class SemSpanAuto(Enum):
    """SemSpanAuto."""

    FALSE = 0
    r"""The span you configure is used as the frequency range for the SEM measurement."""

    TRUE = 1
    r"""The span is automatically computed based on the configured standard and channel bandwidth."""


class SemSweepTimeAuto(Enum):
    """SemSweepTimeAuto."""

    FALSE = 0
    r"""The measurement uses the sweep time that you specify in the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_SWEEP_TIME_INTERVAL` attribute."""

    TRUE = 1
    r"""The measurement automatically calculates the sweep time based on the standard and bandwidth you specify."""


class SemAveragingEnabled(Enum):
    """SemAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The SEM measurement uses the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_AVERAGING_COUNT` attribute as the number
    of acquisitions over which the SEM measurement is averaged."""


class SemAveragingType(Enum):
    """SemAveragingType."""

    RMS = 0
    r"""The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor."""

    LOG = 1
    r"""The power spectrum is averaged in a logarithmic scale."""

    SCALAR = 2
    r"""The square root of the power spectrum is averaged."""

    MAXIMUM = 3
    r"""The peak power in the spectrum is retained from one acquisition to the next at each frequency bin."""

    MINIMUM = 4
    r"""The least power in the spectrum is retained from one acquisition to the next at each frequency bin."""


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
    r"""The spectrum exceeds the SEM measurement mask limits for at least one of the offset segments."""

    PASS = 1
    r"""The spectrum does not exceed the SEM measurement mask limits for any offset segment."""


class SemLowerOffsetMeasurementStatus(Enum):
    """SemLowerOffsetMeasurementStatus."""

    FAIL = 0
    r"""Indicates that the measurement has failed."""

    PASS = 1
    r"""Indicates that the measurement has passed."""


class SemUpperOffsetMeasurementStatus(Enum):
    """SemUpperOffsetMeasurementStatus."""

    FAIL = 0
    r"""The spectrum exceeds the SEM measurement mask and limits for the upper offset segment."""

    PASS = 1
    r"""The spectrum does not exceed the SEM measurement mask and limits for the upper offset segment."""


class TxpBurstDetectionEnabled(Enum):
    """TxpBurstDetectionEnabled."""

    FALSE = 0
    r"""Disables burst detection."""

    TRUE = 1
    r"""Enables burst detection."""


class TxpAveragingEnabled(Enum):
    """TxpAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The TXP measurement uses the :py:attr:`~nirfmxwlan.attributes.AttributeID.TXP_AVERAGING_COUNT` attribute as the number
    of acquisitions over which the TXP measurement is averaged."""


class PowerRampAveragingEnabled(Enum):
    """PowerRampAveragingEnabled."""

    FALSE = 0
    r"""The measurement is performed on a single acquisition."""

    TRUE = 1
    r"""The measurement uses the :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_COUNT` attribute as the
    number of acquisitions using which the results are averaged."""


class LimitedConfigurationChange(Enum):
    """LimitedConfigurationChange."""

    DISABLED = 0
    r"""This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality
    attributes will be applied during RFmx Commit."""

    NO_CHANGE = 1
    r"""Signal configuration and RFmxInstr configuration are locked after the first Commit or Initiate of the named signal
    configuration. Any configuration change thereafter either in RFmxInstr attributes or personality attributes will not be
    considered by subsequent RFmx Commits or Initiates of this signal.  Use **No Change** if you have created named signal
    configurations for all measurement configurations but are setting some RFmxInstr attributes. Refer to the Limitations
    of the Limited Configuration Change Property topic for more details about the limitations of using this mode."""

    FREQUENCY = 2
    r"""Signal configuration, other than center frequency, external attenuation, and RFInstr configuration, is locked after
    first Commit or Initiate of the named signal configuration. Thereafter, only the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.CENTER_FREQUENCY` and
    :py:attr:`~nirfmxwlan.attributes.AttributeID.EXTERNAL_ATTENUATION` attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal.  Refer to the Limitations of the Limited Configuration Change
    Property topic for more details about the limitations of using this mode."""

    REFERENCE_LEVEL = 3
    r"""Signal configuration, other than the reference level and RFInstr configuration, is locked after first Commit or
    Initiate of the named signal configuration. Thereafter only the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute value change will be considered by subsequent
    driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI
    recommends that you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` to
    **Relative** so that the trigger level is automatically adjusted as you adjust the reference level. Refer to the
    Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this
    mode."""

    FREQUENCY_AND_REFERENCE_LEVEL = 4
    r"""Signal configuration, other than center frequency, reference level, external attenuation, and RFInstr configuration, is
    locked after first Commit or Initiate of the named signal configuration. Thereafter only Center Frequency, Reference
    Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of
    this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power
    Edge  Level Type to **Relative** so that the trigger level is automatically adjusted as you adjust the reference level.
    Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of
    using this mode."""

    SELECTED_PORTS_FREQUENCY_AND_REFERENCE_LEVEL = 5
    r"""Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr
    configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected
    Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by
    subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge
    Trigger, NI recommends you set the IQ Power Edge Level Type to **Relative** so that the trigger level is automatically
    adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic
    for more details about the limitations of using this mode."""


class MeasurementTypes(IntFlag):
    """MeasurementTypes."""

    TXP = 1 << 0
    r""""""

    POWERRAMP = 1 << 1
    r""""""

    DSSSMODACC = 1 << 2
    r""""""

    OFDMMODACC = 1 << 3
    r""""""

    SEM = 1 << 4
    r""""""


class OfdmModAccCalibrationDataValid(Enum):
    """OfdmModAccCalibrationDataValid."""

    FALSE = 0
    r""""""

    TRUE = 1
    r""""""
