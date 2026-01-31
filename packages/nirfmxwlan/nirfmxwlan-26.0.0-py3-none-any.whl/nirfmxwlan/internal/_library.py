"""Wrapper around driver library.
Class will setup the correct ctypes information for every function on first call.
"""

import ctypes
import threading
from typing import Any

import nirfmxwlan.errors as errors
import nirfmxwlan.internal._custom_types as _custom_types


class Library(object):
    """Library

    Wrapper around driver library.
    Class will setup the correct ctypes information for every function on first call.
    """

    def __init__(self, ctypes_library):
        """Initialize the Library object."""
        self._func_lock = threading.Lock()
        self._library = ctypes_library
        # We cache the cfunc object from the ctypes.CDLL object
        self.RFmxWLAN_ResetAttribute_cfunc = None
        self.RFmxWLAN_GetError_cfunc = None
        self.RFmxWLAN_GetErrorString_cfunc = None
        self.RFmxWLAN_GetAttributeI8_cfunc = None
        self.RFmxWLAN_SetAttributeI8_cfunc = None
        self.RFmxWLAN_GetAttributeI8Array_cfunc = None
        self.RFmxWLAN_SetAttributeI8Array_cfunc = None
        self.RFmxWLAN_GetAttributeI16_cfunc = None
        self.RFmxWLAN_SetAttributeI16_cfunc = None
        self.RFmxWLAN_GetAttributeI32_cfunc = None
        self.RFmxWLAN_SetAttributeI32_cfunc = None
        self.RFmxWLAN_GetAttributeI32Array_cfunc = None
        self.RFmxWLAN_SetAttributeI32Array_cfunc = None
        self.RFmxWLAN_GetAttributeI64_cfunc = None
        self.RFmxWLAN_SetAttributeI64_cfunc = None
        self.RFmxWLAN_GetAttributeI64Array_cfunc = None
        self.RFmxWLAN_SetAttributeI64Array_cfunc = None
        self.RFmxWLAN_GetAttributeU8_cfunc = None
        self.RFmxWLAN_SetAttributeU8_cfunc = None
        self.RFmxWLAN_GetAttributeU8Array_cfunc = None
        self.RFmxWLAN_SetAttributeU8Array_cfunc = None
        self.RFmxWLAN_GetAttributeU16_cfunc = None
        self.RFmxWLAN_SetAttributeU16_cfunc = None
        self.RFmxWLAN_GetAttributeU32_cfunc = None
        self.RFmxWLAN_SetAttributeU32_cfunc = None
        self.RFmxWLAN_GetAttributeU32Array_cfunc = None
        self.RFmxWLAN_SetAttributeU32Array_cfunc = None
        self.RFmxWLAN_GetAttributeU64Array_cfunc = None
        self.RFmxWLAN_SetAttributeU64Array_cfunc = None
        self.RFmxWLAN_GetAttributeF32_cfunc = None
        self.RFmxWLAN_SetAttributeF32_cfunc = None
        self.RFmxWLAN_GetAttributeF32Array_cfunc = None
        self.RFmxWLAN_SetAttributeF32Array_cfunc = None
        self.RFmxWLAN_GetAttributeF64_cfunc = None
        self.RFmxWLAN_SetAttributeF64_cfunc = None
        self.RFmxWLAN_GetAttributeF64Array_cfunc = None
        self.RFmxWLAN_SetAttributeF64Array_cfunc = None
        self.RFmxWLAN_GetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxWLAN_SetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxWLAN_GetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxWLAN_SetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxWLAN_GetAttributeString_cfunc = None
        self.RFmxWLAN_SetAttributeString_cfunc = None
        self.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase_cfunc = None
        self.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms_cfunc = None
        self.RFmxWLAN_OFDMModAccAutoLevel_cfunc = None
        self.RFmxWLAN_OFDMModAccValidateCalibrationData_cfunc = None
        self.RFmxWLAN_AbortMeasurements_cfunc = None
        self.RFmxWLAN_AnalyzeIQ1Waveform_cfunc = None
        self.RFmxWLAN_AnalyzeSpectrum1Waveform_cfunc = None
        self.RFmxWLAN_AnalyzeNWaveformsIQ_cfunc = None
        self.RFmxWLAN_AnalyzeNWaveformsSpectrum_cfunc = None
        self.RFmxWLAN_AutoDetectSignal_cfunc = None
        self.RFmxWLAN_AutoLevel_cfunc = None
        self.RFmxWLAN_CheckMeasurementStatus_cfunc = None
        self.RFmxWLAN_ClearAllNamedResults_cfunc = None
        self.RFmxWLAN_ClearNamedResult_cfunc = None
        self.RFmxWLAN_CloneSignalConfiguration_cfunc = None
        self.RFmxWLAN_Commit_cfunc = None
        self.RFmxWLAN_CfgDigitalEdgeTrigger_cfunc = None
        self.RFmxWLAN_CfgIQPowerEdgeTrigger_cfunc = None
        self.RFmxWLAN_CfgSelectedPortsMultiple_cfunc = None
        self.RFmxWLAN_CfgSoftwareEdgeTrigger_cfunc = None
        self.RFmxWLAN_CreateSignalConfiguration_cfunc = None
        self.RFmxWLAN_DeleteSignalConfiguration_cfunc = None
        self.RFmxWLAN_DisableTrigger_cfunc = None
        self.RFmxWLAN_GetAllNamedResultNames_cfunc = None
        self.RFmxWLAN_Initiate_cfunc = None
        self.RFmxWLAN_ResetToDefault_cfunc = None
        self.RFmxWLAN_SelectMeasurements_cfunc = None
        self.RFmxWLAN_SendSoftwareEdgeTrigger_cfunc = None
        self.RFmxWLAN_WaitForMeasurementComplete_cfunc = None
        self.RFmxWLAN_AutoDetectSignalAnalysisOnly_cfunc = None
        self.RFmxWLAN_TXPCfgAveraging_cfunc = None
        self.RFmxWLAN_TXPCfgBurstDetectionEnabled_cfunc = None
        self.RFmxWLAN_TXPCfgMaximumMeasurementInterval_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgAcquisitionLength_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgAveraging_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgEVMUnit_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgMeasurementLength_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled_cfunc = None
        self.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates_cfunc = None
        self.RFmxWLAN_PowerRampCfgAcquisitionLength_cfunc = None
        self.RFmxWLAN_PowerRampCfgAveraging_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgAcquisitionLength_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgAveraging_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgChannelEstimationType_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgEVMUnit_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgMeasurementLength_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgMeasurementMode_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled_cfunc = None
        self.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled_cfunc = None
        self.RFmxWLAN_SEMCfgAveraging_cfunc = None
        self.RFmxWLAN_SEMCfgMaskType_cfunc = None
        self.RFmxWLAN_SEMCfgNumberOfOffsets_cfunc = None
        self.RFmxWLAN_SEMCfgOffsetFrequencyArray_cfunc = None
        self.RFmxWLAN_SEMCfgOffsetRelativeLimitArray_cfunc = None
        self.RFmxWLAN_SEMCfgSpan_cfunc = None
        self.RFmxWLAN_SEMCfgSweepTime_cfunc = None
        self.RFmxWLAN_CfgChannelBandwidth_cfunc = None
        self.RFmxWLAN_CfgExternalAttenuation_cfunc = None
        self.RFmxWLAN_CfgFrequencyArray_cfunc = None
        self.RFmxWLAN_CfgFrequency_cfunc = None
        self.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains_cfunc = None
        self.RFmxWLAN_CfgReferenceLevel_cfunc = None
        self.RFmxWLAN_CfgStandard_cfunc = None
        self.RFmxWLAN_TXPFetchMeasurement_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchAveragePowers_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchEVM_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchIQImpairments_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchPeakPowers_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchPPDUInformation_cfunc = None
        self.RFmxWLAN_PowerRampFetchMeasurement_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchChainRMSEVM_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchCrossPower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDataAveragePower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDataPeakPower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchGuardIntervalType_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchLTFSize_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchIQImpairments_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchMCSIndex_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchNumberOfUsers_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPEAveragePower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPEPeakPower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPPDUAveragePower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPPDUPeakPower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPPDUType_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPEDuration_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSIGCRCStatus_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSpectralFlatness_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchStreamRMSEVM_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUnusedToneError_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserPower_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM_cfunc = None
        self.RFmxWLAN_SEMFetchCarrierMeasurement_cfunc = None
        self.RFmxWLAN_SEMFetchLowerOffsetMargin_cfunc = None
        self.RFmxWLAN_SEMFetchLowerOffsetPower_cfunc = None
        self.RFmxWLAN_SEMFetchMeasurementStatus_cfunc = None
        self.RFmxWLAN_SEMFetchUpperOffsetMargin_cfunc = None
        self.RFmxWLAN_SEMFetchUpperOffsetPower_cfunc = None
        self.RFmxWLAN_TXPFetchPowerTrace_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchConstellationTrace_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace_cfunc = None
        self.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace_cfunc = None
        self.RFmxWLAN_PowerRampFetchFallTrace_cfunc = None
        self.RFmxWLAN_PowerRampFetchRiseTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDataConstellationTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace_cfunc = None
        self.RFmxWLAN_SEMFetchLowerOffsetMarginArray_cfunc = None
        self.RFmxWLAN_SEMFetchLowerOffsetPowerArray_cfunc = None
        self.RFmxWLAN_SEMFetchSpectrum_cfunc = None
        self.RFmxWLAN_SEMFetchUpperOffsetMarginArray_cfunc = None
        self.RFmxWLAN_SEMFetchUpperOffsetPowerArray_cfunc = None

    def _get_library_function(self, name: str) -> Any:
        try:
            function = getattr(self._library, name)
        except AttributeError as e:
            raise errors.DriverTooOldError() from e  # type: ignore
        return function

    def RFmxWLAN_ResetAttribute(self, vi, selector_string, attribute_id):
        """RFmxWLAN_ResetAttribute."""
        with self._func_lock:
            if self.RFmxWLAN_ResetAttribute_cfunc is None:
                self.RFmxWLAN_ResetAttribute_cfunc = self._get_library_function(
                    "RFmxWLAN_ResetAttribute"
                )
                self.RFmxWLAN_ResetAttribute_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_ResetAttribute_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_ResetAttribute_cfunc(vi, selector_string, attribute_id)

    def RFmxWLAN_GetError(self, vi, error_code, error_description_buffer_size, error_description):
        """RFmxWLAN_GetError."""
        with self._func_lock:
            if self.RFmxWLAN_GetError_cfunc is None:
                self.RFmxWLAN_GetError_cfunc = self._get_library_function("RFmxWLAN_GetError")
                self.RFmxWLAN_GetError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_GetError_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetError_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxWLAN_GetErrorString(
        self, vi, error_code, error_description_buffer_size, error_description
    ):
        """RFmxWLAN_GetErrorString."""
        with self._func_lock:
            if self.RFmxWLAN_GetErrorString_cfunc is None:
                self.RFmxWLAN_GetErrorString_cfunc = self._get_library_function(
                    "RFmxWLAN_GetErrorString"
                )
                self.RFmxWLAN_GetErrorString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_GetErrorString_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetErrorString_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxWLAN_GetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeI8."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI8_cfunc is None:
                self.RFmxWLAN_GetAttributeI8_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI8"
                )
                self.RFmxWLAN_GetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                ]
                self.RFmxWLAN_GetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeI8."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI8_cfunc is None:
                self.RFmxWLAN_SetAttributeI8_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI8"
                )
                self.RFmxWLAN_SetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int8,
                ]
                self.RFmxWLAN_SetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeI16."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI16_cfunc is None:
                self.RFmxWLAN_GetAttributeI16_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI16"
                )
                self.RFmxWLAN_GetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int16),
                ]
                self.RFmxWLAN_GetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeI16."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI16_cfunc is None:
                self.RFmxWLAN_SetAttributeI16_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI16"
                )
                self.RFmxWLAN_SetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int16,
                ]
                self.RFmxWLAN_SetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeI32."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI32_cfunc is None:
                self.RFmxWLAN_GetAttributeI32_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI32"
                )
                self.RFmxWLAN_GetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeI32."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI32_cfunc is None:
                self.RFmxWLAN_SetAttributeI32_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI32"
                )
                self.RFmxWLAN_SetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeI64."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI64_cfunc is None:
                self.RFmxWLAN_GetAttributeI64_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI64"
                )
                self.RFmxWLAN_GetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                ]
                self.RFmxWLAN_GetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeI64."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI64_cfunc is None:
                self.RFmxWLAN_SetAttributeI64_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI64"
                )
                self.RFmxWLAN_SetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int64,
                ]
                self.RFmxWLAN_SetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeU8."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeU8_cfunc is None:
                self.RFmxWLAN_GetAttributeU8_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeU8"
                )
                self.RFmxWLAN_GetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                ]
                self.RFmxWLAN_GetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeU8."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeU8_cfunc is None:
                self.RFmxWLAN_SetAttributeU8_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeU8"
                )
                self.RFmxWLAN_SetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint8,
                ]
                self.RFmxWLAN_SetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeU16."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeU16_cfunc is None:
                self.RFmxWLAN_GetAttributeU16_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeU16"
                )
                self.RFmxWLAN_GetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint16),
                ]
                self.RFmxWLAN_GetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeU16."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeU16_cfunc is None:
                self.RFmxWLAN_SetAttributeU16_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeU16"
                )
                self.RFmxWLAN_SetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint16,
                ]
                self.RFmxWLAN_SetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeU32."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeU32_cfunc is None:
                self.RFmxWLAN_GetAttributeU32_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeU32"
                )
                self.RFmxWLAN_GetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                ]
                self.RFmxWLAN_GetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeU32."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeU32_cfunc is None:
                self.RFmxWLAN_SetAttributeU32_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeU32"
                )
                self.RFmxWLAN_SetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeF32."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeF32_cfunc is None:
                self.RFmxWLAN_GetAttributeF32_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeF32"
                )
                self.RFmxWLAN_GetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                ]
                self.RFmxWLAN_GetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeF32."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeF32_cfunc is None:
                self.RFmxWLAN_SetAttributeF32_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeF32"
                )
                self.RFmxWLAN_SetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_float,
                ]
                self.RFmxWLAN_SetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_GetAttributeF64."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeF64_cfunc is None:
                self.RFmxWLAN_GetAttributeF64_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeF64"
                )
                self.RFmxWLAN_GetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_GetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_SetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeF64."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeF64_cfunc is None:
                self.RFmxWLAN_SetAttributeF64_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeF64"
                )
                self.RFmxWLAN_SetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_double,
                ]
                self.RFmxWLAN_SetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_GetAttributeI8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI8Array_cfunc is None:
                self.RFmxWLAN_GetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI8Array"
                )
                self.RFmxWLAN_GetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeI8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxWLAN_SetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI8Array_cfunc is None:
                self.RFmxWLAN_SetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI8Array"
                )
                self.RFmxWLAN_SetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeI32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI32Array_cfunc is None:
                self.RFmxWLAN_GetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI32Array"
                )
                self.RFmxWLAN_GetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeI32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI32Array_cfunc is None:
                self.RFmxWLAN_SetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI32Array"
                )
                self.RFmxWLAN_SetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeI64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeI64Array_cfunc is None:
                self.RFmxWLAN_GetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeI64Array"
                )
                self.RFmxWLAN_GetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeI64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeI64Array_cfunc is None:
                self.RFmxWLAN_SetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeI64Array"
                )
                self.RFmxWLAN_SetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeU8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeU8Array_cfunc is None:
                self.RFmxWLAN_GetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeU8Array"
                )
                self.RFmxWLAN_GetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeU8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxWLAN_SetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeU8Array_cfunc is None:
                self.RFmxWLAN_SetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeU8Array"
                )
                self.RFmxWLAN_SetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeU32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeU32Array_cfunc is None:
                self.RFmxWLAN_GetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeU32Array"
                )
                self.RFmxWLAN_GetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeU32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeU32Array_cfunc is None:
                self.RFmxWLAN_SetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeU32Array"
                )
                self.RFmxWLAN_SetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeU64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeU64Array_cfunc is None:
                self.RFmxWLAN_GetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeU64Array"
                )
                self.RFmxWLAN_GetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeU64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeU64Array_cfunc is None:
                self.RFmxWLAN_SetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeU64Array"
                )
                self.RFmxWLAN_SetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeF32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeF32Array_cfunc is None:
                self.RFmxWLAN_GetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeF32Array"
                )
                self.RFmxWLAN_GetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeF32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeF32Array_cfunc is None:
                self.RFmxWLAN_SetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeF32Array"
                )
                self.RFmxWLAN_SetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeF64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeF64Array_cfunc is None:
                self.RFmxWLAN_GetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeF64Array"
                )
                self.RFmxWLAN_GetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeF64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeF64Array_cfunc is None:
                self.RFmxWLAN_SetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeF64Array"
                )
                self.RFmxWLAN_SetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxWLAN_GetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeNIComplexSingleArray"
                )
                self.RFmxWLAN_GetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxWLAN_SetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeNIComplexSingleArray"
                )
                self.RFmxWLAN_SetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxWLAN_GetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxWLAN_GetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeNIComplexDoubleArray"
                )
                self.RFmxWLAN_GetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxWLAN_SetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxWLAN_SetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxWLAN_SetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeNIComplexDoubleArray"
                )
                self.RFmxWLAN_SetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxWLAN_SetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxWLAN_GetAttributeString(self, vi, selector_string, attribute_id, array_size, attr_val):
        """RFmxWLAN_GetAttributeString."""
        with self._func_lock:
            if self.RFmxWLAN_GetAttributeString_cfunc is None:
                self.RFmxWLAN_GetAttributeString_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAttributeString"
                )
                self.RFmxWLAN_GetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_GetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAttributeString_cfunc(
            vi, selector_string, attribute_id, array_size, attr_val
        )

    def RFmxWLAN_SetAttributeString(self, vi, selector_string, attribute_id, attr_val):
        """RFmxWLAN_SetAttributeString."""
        with self._func_lock:
            if self.RFmxWLAN_SetAttributeString_cfunc is None:
                self.RFmxWLAN_SetAttributeString_cfunc = self._get_library_function(
                    "RFmxWLAN_SetAttributeString"
                )
                self.RFmxWLAN_SetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_SetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SetAttributeString_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxWLAN_OFDMModAccCfg1ReferenceWaveform(
        self, vi, selector_string, x0, dx, reference_waveform, array_size
    ):
        """RFmxWLAN_OFDMModAccCfg1ReferenceWaveform."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfg1ReferenceWaveform"
                )
                self.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform_cfunc(
            vi, selector_string, x0, dx, reference_waveform, array_size
        )

    def RFmxWLAN_OFDMModAccAutoLevel(self, vi, selector_string, timeout):
        """RFmxWLAN_OFDMModAccAutoLevel."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccAutoLevel_cfunc is None:
                self.RFmxWLAN_OFDMModAccAutoLevel_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccAutoLevel"
                )
                self.RFmxWLAN_OFDMModAccAutoLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_OFDMModAccAutoLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccAutoLevel_cfunc(vi, selector_string, timeout)

    def RFmxWLAN_OFDMModAccValidateCalibrationData(
        self, vi, selector_string, calibration_data_valid
    ):
        """RFmxWLAN_OFDMModAccValidateCalibrationData."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccValidateCalibrationData_cfunc is None:
                self.RFmxWLAN_OFDMModAccValidateCalibrationData_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccValidateCalibrationData"
                )
                self.RFmxWLAN_OFDMModAccValidateCalibrationData_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccValidateCalibrationData_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccValidateCalibrationData_cfunc(
            vi, selector_string, calibration_data_valid
        )

    def RFmxWLAN_AbortMeasurements(self, vi, selector_string):
        """RFmxWLAN_AbortMeasurements."""
        with self._func_lock:
            if self.RFmxWLAN_AbortMeasurements_cfunc is None:
                self.RFmxWLAN_AbortMeasurements_cfunc = self._get_library_function(
                    "RFmxWLAN_AbortMeasurements"
                )
                self.RFmxWLAN_AbortMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_AbortMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AbortMeasurements_cfunc(vi, selector_string)

    def RFmxWLAN_AutoDetectSignal(self, vi, selector_string, timeout):
        """RFmxWLAN_AutoDetectSignal."""
        with self._func_lock:
            if self.RFmxWLAN_AutoDetectSignal_cfunc is None:
                self.RFmxWLAN_AutoDetectSignal_cfunc = self._get_library_function(
                    "RFmxWLAN_AutoDetectSignal"
                )
                self.RFmxWLAN_AutoDetectSignal_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_AutoDetectSignal_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AutoDetectSignal_cfunc(vi, selector_string, timeout)

    def RFmxWLAN_AutoLevel(self, vi, selector_string, measurement_interval):
        """RFmxWLAN_AutoLevel."""
        with self._func_lock:
            if self.RFmxWLAN_AutoLevel_cfunc is None:
                self.RFmxWLAN_AutoLevel_cfunc = self._get_library_function("RFmxWLAN_AutoLevel")
                self.RFmxWLAN_AutoLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_AutoLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AutoLevel_cfunc(vi, selector_string, measurement_interval)

    def RFmxWLAN_CheckMeasurementStatus(self, vi, selector_string, is_done):
        """RFmxWLAN_CheckMeasurementStatus."""
        with self._func_lock:
            if self.RFmxWLAN_CheckMeasurementStatus_cfunc is None:
                self.RFmxWLAN_CheckMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxWLAN_CheckMeasurementStatus"
                )
                self.RFmxWLAN_CheckMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_CheckMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CheckMeasurementStatus_cfunc(vi, selector_string, is_done)

    def RFmxWLAN_ClearAllNamedResults(self, vi, selector_string):
        """RFmxWLAN_ClearAllNamedResults."""
        with self._func_lock:
            if self.RFmxWLAN_ClearAllNamedResults_cfunc is None:
                self.RFmxWLAN_ClearAllNamedResults_cfunc = self._get_library_function(
                    "RFmxWLAN_ClearAllNamedResults"
                )
                self.RFmxWLAN_ClearAllNamedResults_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_ClearAllNamedResults_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_ClearAllNamedResults_cfunc(vi, selector_string)

    def RFmxWLAN_ClearNamedResult(self, vi, selector_string):
        """RFmxWLAN_ClearNamedResult."""
        with self._func_lock:
            if self.RFmxWLAN_ClearNamedResult_cfunc is None:
                self.RFmxWLAN_ClearNamedResult_cfunc = self._get_library_function(
                    "RFmxWLAN_ClearNamedResult"
                )
                self.RFmxWLAN_ClearNamedResult_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_ClearNamedResult_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_ClearNamedResult_cfunc(vi, selector_string)

    def RFmxWLAN_Commit(self, vi, selector_string):
        """RFmxWLAN_Commit."""
        with self._func_lock:
            if self.RFmxWLAN_Commit_cfunc is None:
                self.RFmxWLAN_Commit_cfunc = self._get_library_function("RFmxWLAN_Commit")
                self.RFmxWLAN_Commit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_Commit_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_Commit_cfunc(vi, selector_string)

    def RFmxWLAN_CfgDigitalEdgeTrigger(
        self, vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        """RFmxWLAN_CfgDigitalEdgeTrigger."""
        with self._func_lock:
            if self.RFmxWLAN_CfgDigitalEdgeTrigger_cfunc is None:
                self.RFmxWLAN_CfgDigitalEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgDigitalEdgeTrigger"
                )
                self.RFmxWLAN_CfgDigitalEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_CfgDigitalEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgDigitalEdgeTrigger_cfunc(
            vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
        )

    def RFmxWLAN_CfgIQPowerEdgeTrigger(
        self,
        vi,
        selector_string,
        iq_power_edge_source,
        iq_power_edge_slope,
        iq_power_edge_level,
        trigger_delay,
        trigger_min_quiet_time_mode,
        trigger_min_quiet_time_duration,
        iq_power_edge_level_type,
        enable_trigger,
    ):
        """RFmxWLAN_CfgIQPowerEdgeTrigger."""
        with self._func_lock:
            if self.RFmxWLAN_CfgIQPowerEdgeTrigger_cfunc is None:
                self.RFmxWLAN_CfgIQPowerEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgIQPowerEdgeTrigger"
                )
                self.RFmxWLAN_CfgIQPowerEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_CfgIQPowerEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgIQPowerEdgeTrigger_cfunc(
            vi,
            selector_string,
            iq_power_edge_source,
            iq_power_edge_slope,
            iq_power_edge_level,
            trigger_delay,
            trigger_min_quiet_time_mode,
            trigger_min_quiet_time_duration,
            iq_power_edge_level_type,
            enable_trigger,
        )

    def RFmxWLAN_CfgSelectedPortsMultiple(self, vi, selector_string, selected_ports):
        """RFmxWLAN_CfgSelectedPortsMultiple."""
        with self._func_lock:
            if self.RFmxWLAN_CfgSelectedPortsMultiple_cfunc is None:
                self.RFmxWLAN_CfgSelectedPortsMultiple_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgSelectedPortsMultiple"
                )
                self.RFmxWLAN_CfgSelectedPortsMultiple_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_CfgSelectedPortsMultiple_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgSelectedPortsMultiple_cfunc(vi, selector_string, selected_ports)

    def RFmxWLAN_CfgSoftwareEdgeTrigger(self, vi, selector_string, trigger_delay, enable_trigger):
        """RFmxWLAN_CfgSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxWLAN_CfgSoftwareEdgeTrigger_cfunc is None:
                self.RFmxWLAN_CfgSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgSoftwareEdgeTrigger"
                )
                self.RFmxWLAN_CfgSoftwareEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_CfgSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgSoftwareEdgeTrigger_cfunc(
            vi, selector_string, trigger_delay, enable_trigger
        )

    def RFmxWLAN_CreateSignalConfiguration(self, vi, signal_name):
        """RFmxWLAN_CreateSignalConfiguration."""
        with self._func_lock:
            if self.RFmxWLAN_CreateSignalConfiguration_cfunc is None:
                self.RFmxWLAN_CreateSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxWLAN_CreateSignalConfiguration"
                )
                self.RFmxWLAN_CreateSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_CreateSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CreateSignalConfiguration_cfunc(vi, signal_name)

    def RFmxWLAN_DisableTrigger(self, vi, selector_string):
        """RFmxWLAN_DisableTrigger."""
        with self._func_lock:
            if self.RFmxWLAN_DisableTrigger_cfunc is None:
                self.RFmxWLAN_DisableTrigger_cfunc = self._get_library_function(
                    "RFmxWLAN_DisableTrigger"
                )
                self.RFmxWLAN_DisableTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_DisableTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DisableTrigger_cfunc(vi, selector_string)

    def RFmxWLAN_Initiate(self, vi, selector_string, result_name):
        """RFmxWLAN_Initiate."""
        with self._func_lock:
            if self.RFmxWLAN_Initiate_cfunc is None:
                self.RFmxWLAN_Initiate_cfunc = self._get_library_function("RFmxWLAN_Initiate")
                self.RFmxWLAN_Initiate_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_Initiate_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_Initiate_cfunc(vi, selector_string, result_name)

    def RFmxWLAN_ResetToDefault(self, vi, selector_string):
        """RFmxWLAN_ResetToDefault."""
        with self._func_lock:
            if self.RFmxWLAN_ResetToDefault_cfunc is None:
                self.RFmxWLAN_ResetToDefault_cfunc = self._get_library_function(
                    "RFmxWLAN_ResetToDefault"
                )
                self.RFmxWLAN_ResetToDefault_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_ResetToDefault_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_ResetToDefault_cfunc(vi, selector_string)

    def RFmxWLAN_SelectMeasurements(self, vi, selector_string, measurements, enable_all_traces):
        """RFmxWLAN_SelectMeasurements."""
        with self._func_lock:
            if self.RFmxWLAN_SelectMeasurements_cfunc is None:
                self.RFmxWLAN_SelectMeasurements_cfunc = self._get_library_function(
                    "RFmxWLAN_SelectMeasurements"
                )
                self.RFmxWLAN_SelectMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SelectMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SelectMeasurements_cfunc(
            vi, selector_string, measurements, enable_all_traces
        )

    def RFmxWLAN_WaitForMeasurementComplete(self, vi, selector_string, timeout):
        """RFmxWLAN_WaitForMeasurementComplete."""
        with self._func_lock:
            if self.RFmxWLAN_WaitForMeasurementComplete_cfunc is None:
                self.RFmxWLAN_WaitForMeasurementComplete_cfunc = self._get_library_function(
                    "RFmxWLAN_WaitForMeasurementComplete"
                )
                self.RFmxWLAN_WaitForMeasurementComplete_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_WaitForMeasurementComplete_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_WaitForMeasurementComplete_cfunc(vi, selector_string, timeout)

    def RFmxWLAN_AutoDetectSignalAnalysisOnly(self, vi, selector_string, x0, dx, iq, array_size):
        """RFmxWLAN_AutoDetectSignalAnalysisOnly."""
        with self._func_lock:
            if self.RFmxWLAN_AutoDetectSignalAnalysisOnly_cfunc is None:
                self.RFmxWLAN_AutoDetectSignalAnalysisOnly_cfunc = self._get_library_function(
                    "RFmxWLAN_AutoDetectSignalAnalysisOnly"
                )
                self.RFmxWLAN_AutoDetectSignalAnalysisOnly_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_AutoDetectSignalAnalysisOnly_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AutoDetectSignalAnalysisOnly_cfunc(
            vi, selector_string, x0, dx, iq, array_size
        )

    def RFmxWLAN_TXPCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxWLAN_TXPCfgAveraging."""
        with self._func_lock:
            if self.RFmxWLAN_TXPCfgAveraging_cfunc is None:
                self.RFmxWLAN_TXPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxWLAN_TXPCfgAveraging"
                )
                self.RFmxWLAN_TXPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_TXPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_TXPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxWLAN_TXPCfgBurstDetectionEnabled(self, vi, selector_string, burst_detection_enabled):
        """RFmxWLAN_TXPCfgBurstDetectionEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_TXPCfgBurstDetectionEnabled_cfunc is None:
                self.RFmxWLAN_TXPCfgBurstDetectionEnabled_cfunc = self._get_library_function(
                    "RFmxWLAN_TXPCfgBurstDetectionEnabled"
                )
                self.RFmxWLAN_TXPCfgBurstDetectionEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_TXPCfgBurstDetectionEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_TXPCfgBurstDetectionEnabled_cfunc(
            vi, selector_string, burst_detection_enabled
        )

    def RFmxWLAN_TXPCfgMaximumMeasurementInterval(
        self, vi, selector_string, maximum_measurement_interval
    ):
        """RFmxWLAN_TXPCfgMaximumMeasurementInterval."""
        with self._func_lock:
            if self.RFmxWLAN_TXPCfgMaximumMeasurementInterval_cfunc is None:
                self.RFmxWLAN_TXPCfgMaximumMeasurementInterval_cfunc = self._get_library_function(
                    "RFmxWLAN_TXPCfgMaximumMeasurementInterval"
                )
                self.RFmxWLAN_TXPCfgMaximumMeasurementInterval_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_TXPCfgMaximumMeasurementInterval_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_TXPCfgMaximumMeasurementInterval_cfunc(
            vi, selector_string, maximum_measurement_interval
        )

    def RFmxWLAN_DSSSModAccCfgAcquisitionLength(
        self, vi, selector_string, acquisition_length_mode, acquisition_length
    ):
        """RFmxWLAN_DSSSModAccCfgAcquisitionLength."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgAcquisitionLength_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgAcquisitionLength_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccCfgAcquisitionLength"
                )
                self.RFmxWLAN_DSSSModAccCfgAcquisitionLength_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxWLAN_DSSSModAccCfgAcquisitionLength_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccCfgAcquisitionLength_cfunc(
            vi, selector_string, acquisition_length_mode, acquisition_length
        )

    def RFmxWLAN_DSSSModAccCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count
    ):
        """RFmxWLAN_DSSSModAccCfgAveraging."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgAveraging_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgAveraging_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccCfgAveraging"
                )
                self.RFmxWLAN_DSSSModAccCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_DSSSModAccCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxWLAN_DSSSModAccCfgEVMUnit(self, vi, selector_string, evm_unit):
        """RFmxWLAN_DSSSModAccCfgEVMUnit."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgEVMUnit_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgEVMUnit_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccCfgEVMUnit"
                )
                self.RFmxWLAN_DSSSModAccCfgEVMUnit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_DSSSModAccCfgEVMUnit_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccCfgEVMUnit_cfunc(vi, selector_string, evm_unit)

    def RFmxWLAN_DSSSModAccCfgMeasurementLength(
        self, vi, selector_string, measurement_offset, maximum_measurement_length
    ):
        """RFmxWLAN_DSSSModAccCfgMeasurementLength."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgMeasurementLength_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgMeasurementLength_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccCfgMeasurementLength"
                )
                self.RFmxWLAN_DSSSModAccCfgMeasurementLength_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_DSSSModAccCfgMeasurementLength_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccCfgMeasurementLength_cfunc(
            vi, selector_string, measurement_offset, maximum_measurement_length
        )

    def RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray(
        self, vi, selector_string, start_time, stop_time, number_of_elements
    ):
        """RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray"
                    )
                )
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray_cfunc(
            vi, selector_string, start_time, stop_time, number_of_elements
        )

    def RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled(
        self, vi, selector_string, power_measurement_enabled
    ):
        """RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled_cfunc = (
                    self._get_library_function("RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled")
                )
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled_cfunc(
            vi, selector_string, power_measurement_enabled
        )

    def RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates(
        self, vi, selector_string, number_of_custom_gates
    ):
        """RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates_cfunc is None:
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates"
                    )
                )
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates_cfunc(
            vi, selector_string, number_of_custom_gates
        )

    def RFmxWLAN_PowerRampCfgAcquisitionLength(self, vi, selector_string, acquisition_length):
        """RFmxWLAN_PowerRampCfgAcquisitionLength."""
        with self._func_lock:
            if self.RFmxWLAN_PowerRampCfgAcquisitionLength_cfunc is None:
                self.RFmxWLAN_PowerRampCfgAcquisitionLength_cfunc = self._get_library_function(
                    "RFmxWLAN_PowerRampCfgAcquisitionLength"
                )
                self.RFmxWLAN_PowerRampCfgAcquisitionLength_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_PowerRampCfgAcquisitionLength_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_PowerRampCfgAcquisitionLength_cfunc(
            vi, selector_string, acquisition_length
        )

    def RFmxWLAN_PowerRampCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count
    ):
        """RFmxWLAN_PowerRampCfgAveraging."""
        with self._func_lock:
            if self.RFmxWLAN_PowerRampCfgAveraging_cfunc is None:
                self.RFmxWLAN_PowerRampCfgAveraging_cfunc = self._get_library_function(
                    "RFmxWLAN_PowerRampCfgAveraging"
                )
                self.RFmxWLAN_PowerRampCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_PowerRampCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_PowerRampCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxWLAN_OFDMModAccCfgAcquisitionLength(
        self, vi, selector_string, acquisition_length_mode, acquisition_length
    ):
        """RFmxWLAN_OFDMModAccCfgAcquisitionLength."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgAcquisitionLength_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgAcquisitionLength_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgAcquisitionLength"
                )
                self.RFmxWLAN_OFDMModAccCfgAcquisitionLength_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxWLAN_OFDMModAccCfgAcquisitionLength_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgAcquisitionLength_cfunc(
            vi, selector_string, acquisition_length_mode, acquisition_length
        )

    def RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled(
        self, vi, selector_string, amplitude_tracking_enabled
    ):
        """RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled")
                )
                self.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled_cfunc(
            vi, selector_string, amplitude_tracking_enabled
        )

    def RFmxWLAN_OFDMModAccCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count
    ):
        """RFmxWLAN_OFDMModAccCfgAveraging."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgAveraging_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgAveraging_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgAveraging"
                )
                self.RFmxWLAN_OFDMModAccCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxWLAN_OFDMModAccCfgChannelEstimationType(
        self, vi, selector_string, channel_estimation_type
    ):
        """RFmxWLAN_OFDMModAccCfgChannelEstimationType."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgChannelEstimationType_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgChannelEstimationType_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgChannelEstimationType"
                )
                self.RFmxWLAN_OFDMModAccCfgChannelEstimationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgChannelEstimationType_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgChannelEstimationType_cfunc(
            vi, selector_string, channel_estimation_type
        )

    def RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled(
        self, vi, selector_string, common_clock_source_enabled
    ):
        """RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled")
                )
                self.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled_cfunc(
            vi, selector_string, common_clock_source_enabled
        )

    def RFmxWLAN_OFDMModAccCfgEVMUnit(self, vi, selector_string, evm_unit):
        """RFmxWLAN_OFDMModAccCfgEVMUnit."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgEVMUnit_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgEVMUnit_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgEVMUnit"
                )
                self.RFmxWLAN_OFDMModAccCfgEVMUnit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgEVMUnit_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgEVMUnit_cfunc(vi, selector_string, evm_unit)

    def RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod(
        self, vi, selector_string, frequency_error_estimation_method
    ):
        """RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod"
                    )
                )
                self.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod_cfunc(
            vi, selector_string, frequency_error_estimation_method
        )

    def RFmxWLAN_OFDMModAccCfgMeasurementLength(
        self, vi, selector_string, measurement_offset, maximum_measurement_length
    ):
        """RFmxWLAN_OFDMModAccCfgMeasurementLength."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgMeasurementLength_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgMeasurementLength_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgMeasurementLength"
                )
                self.RFmxWLAN_OFDMModAccCfgMeasurementLength_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgMeasurementLength_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgMeasurementLength_cfunc(
            vi, selector_string, measurement_offset, maximum_measurement_length
        )

    def RFmxWLAN_OFDMModAccCfgMeasurementMode(self, vi, selector_string, measurement_mode):
        """RFmxWLAN_OFDMModAccCfgMeasurementMode."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgMeasurementMode_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgMeasurementMode_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgMeasurementMode"
                )
                self.RFmxWLAN_OFDMModAccCfgMeasurementMode_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgMeasurementMode_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgMeasurementMode_cfunc(
            vi, selector_string, measurement_mode
        )

    def RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled(
        self, vi, selector_string, noise_compensation_enabled
    ):
        """RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled")
                )
                self.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled_cfunc(
            vi, selector_string, noise_compensation_enabled
        )

    def RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM(
        self,
        vi,
        selector_string,
        optimize_dynamic_range_for_evm_enabled,
        optimize_dynamic_range_for_evm_margin,
    ):
        """RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM")
                )
                self.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM_cfunc(
            vi,
            selector_string,
            optimize_dynamic_range_for_evm_enabled,
            optimize_dynamic_range_for_evm_margin,
        )

    def RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled(
        self, vi, selector_string, phase_tracking_enabled
    ):
        """RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled"
                )
                self.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled_cfunc(
            vi, selector_string, phase_tracking_enabled
        )

    def RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled(
        self, vi, selector_string, symbol_clock_error_correction_enabled
    ):
        """RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled"
                    )
                )
                self.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled_cfunc(
            vi, selector_string, symbol_clock_error_correction_enabled
        )

    def RFmxWLAN_SEMCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxWLAN_SEMCfgAveraging."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgAveraging_cfunc is None:
                self.RFmxWLAN_SEMCfgAveraging_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMCfgAveraging"
                )
                self.RFmxWLAN_SEMCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SEMCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxWLAN_SEMCfgMaskType(self, vi, selector_string, mask_type):
        """RFmxWLAN_SEMCfgMaskType."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgMaskType_cfunc is None:
                self.RFmxWLAN_SEMCfgMaskType_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMCfgMaskType"
                )
                self.RFmxWLAN_SEMCfgMaskType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SEMCfgMaskType_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgMaskType_cfunc(vi, selector_string, mask_type)

    def RFmxWLAN_SEMCfgNumberOfOffsets(self, vi, selector_string, number_of_offsets):
        """RFmxWLAN_SEMCfgNumberOfOffsets."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgNumberOfOffsets_cfunc is None:
                self.RFmxWLAN_SEMCfgNumberOfOffsets_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMCfgNumberOfOffsets"
                )
                self.RFmxWLAN_SEMCfgNumberOfOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SEMCfgNumberOfOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgNumberOfOffsets_cfunc(vi, selector_string, number_of_offsets)

    def RFmxWLAN_SEMCfgOffsetFrequencyArray(
        self,
        vi,
        selector_string,
        offset_start_frequency,
        offset_stop_frequency,
        offset_sideband,
        number_of_elements,
    ):
        """RFmxWLAN_SEMCfgOffsetFrequencyArray."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgOffsetFrequencyArray_cfunc is None:
                self.RFmxWLAN_SEMCfgOffsetFrequencyArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMCfgOffsetFrequencyArray"
                )
                self.RFmxWLAN_SEMCfgOffsetFrequencyArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SEMCfgOffsetFrequencyArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgOffsetFrequencyArray_cfunc(
            vi,
            selector_string,
            offset_start_frequency,
            offset_stop_frequency,
            offset_sideband,
            number_of_elements,
        )

    def RFmxWLAN_SEMCfgOffsetRelativeLimitArray(
        self, vi, selector_string, relative_limit_start, relative_limit_stop, number_of_elements
    ):
        """RFmxWLAN_SEMCfgOffsetRelativeLimitArray."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgOffsetRelativeLimitArray_cfunc is None:
                self.RFmxWLAN_SEMCfgOffsetRelativeLimitArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMCfgOffsetRelativeLimitArray"
                )
                self.RFmxWLAN_SEMCfgOffsetRelativeLimitArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_SEMCfgOffsetRelativeLimitArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgOffsetRelativeLimitArray_cfunc(
            vi, selector_string, relative_limit_start, relative_limit_stop, number_of_elements
        )

    def RFmxWLAN_SEMCfgSpan(self, vi, selector_string, span_auto, span):
        """RFmxWLAN_SEMCfgSpan."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgSpan_cfunc is None:
                self.RFmxWLAN_SEMCfgSpan_cfunc = self._get_library_function("RFmxWLAN_SEMCfgSpan")
                self.RFmxWLAN_SEMCfgSpan_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxWLAN_SEMCfgSpan_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgSpan_cfunc(vi, selector_string, span_auto, span)

    def RFmxWLAN_SEMCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxWLAN_SEMCfgSweepTime."""
        with self._func_lock:
            if self.RFmxWLAN_SEMCfgSweepTime_cfunc is None:
                self.RFmxWLAN_SEMCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMCfgSweepTime"
                )
                self.RFmxWLAN_SEMCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxWLAN_SEMCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxWLAN_CfgChannelBandwidth(self, vi, selector_string, channel_bandwidth):
        """RFmxWLAN_CfgChannelBandwidth."""
        with self._func_lock:
            if self.RFmxWLAN_CfgChannelBandwidth_cfunc is None:
                self.RFmxWLAN_CfgChannelBandwidth_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgChannelBandwidth"
                )
                self.RFmxWLAN_CfgChannelBandwidth_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_CfgChannelBandwidth_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgChannelBandwidth_cfunc(vi, selector_string, channel_bandwidth)

    def RFmxWLAN_CfgExternalAttenuation(self, vi, selector_string, external_attenuation):
        """RFmxWLAN_CfgExternalAttenuation."""
        with self._func_lock:
            if self.RFmxWLAN_CfgExternalAttenuation_cfunc is None:
                self.RFmxWLAN_CfgExternalAttenuation_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgExternalAttenuation"
                )
                self.RFmxWLAN_CfgExternalAttenuation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_CfgExternalAttenuation_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgExternalAttenuation_cfunc(vi, selector_string, external_attenuation)

    def RFmxWLAN_CfgFrequencyArray(self, vi, selector_string, center_frequency, number_of_elements):
        """RFmxWLAN_CfgFrequencyArray."""
        with self._func_lock:
            if self.RFmxWLAN_CfgFrequencyArray_cfunc is None:
                self.RFmxWLAN_CfgFrequencyArray_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgFrequencyArray"
                )
                self.RFmxWLAN_CfgFrequencyArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_CfgFrequencyArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgFrequencyArray_cfunc(
            vi, selector_string, center_frequency, number_of_elements
        )

    def RFmxWLAN_CfgFrequency(self, vi, selector_string, center_frequency):
        """RFmxWLAN_CfgFrequency."""
        with self._func_lock:
            if self.RFmxWLAN_CfgFrequency_cfunc is None:
                self.RFmxWLAN_CfgFrequency_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgFrequency"
                )
                self.RFmxWLAN_CfgFrequency_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_CfgFrequency_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgFrequency_cfunc(vi, selector_string, center_frequency)

    def RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains(
        self, vi, selector_string, number_of_frequency_segments, number_of_receive_chains
    ):
        """RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains."""
        with self._func_lock:
            if self.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains_cfunc is None:
                self.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains"
                    )
                )
                self.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains_cfunc(
            vi, selector_string, number_of_frequency_segments, number_of_receive_chains
        )

    def RFmxWLAN_CfgReferenceLevel(self, vi, selector_string, reference_level):
        """RFmxWLAN_CfgReferenceLevel."""
        with self._func_lock:
            if self.RFmxWLAN_CfgReferenceLevel_cfunc is None:
                self.RFmxWLAN_CfgReferenceLevel_cfunc = self._get_library_function(
                    "RFmxWLAN_CfgReferenceLevel"
                )
                self.RFmxWLAN_CfgReferenceLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxWLAN_CfgReferenceLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgReferenceLevel_cfunc(vi, selector_string, reference_level)

    def RFmxWLAN_CfgStandard(self, vi, selector_string, standard):
        """RFmxWLAN_CfgStandard."""
        with self._func_lock:
            if self.RFmxWLAN_CfgStandard_cfunc is None:
                self.RFmxWLAN_CfgStandard_cfunc = self._get_library_function("RFmxWLAN_CfgStandard")
                self.RFmxWLAN_CfgStandard_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_CfgStandard_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CfgStandard_cfunc(vi, selector_string, standard)

    def RFmxWLAN_TXPFetchMeasurement(
        self, vi, selector_string, timeout, average_power_mean, peak_power_maximum
    ):
        """RFmxWLAN_TXPFetchMeasurement."""
        with self._func_lock:
            if self.RFmxWLAN_TXPFetchMeasurement_cfunc is None:
                self.RFmxWLAN_TXPFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxWLAN_TXPFetchMeasurement"
                )
                self.RFmxWLAN_TXPFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_TXPFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_TXPFetchMeasurement_cfunc(
            vi, selector_string, timeout, average_power_mean, peak_power_maximum
        )

    def RFmxWLAN_DSSSModAccFetchAveragePowers(
        self,
        vi,
        selector_string,
        timeout,
        preamble_average_power_mean,
        header_average_power_mean,
        data_average_power_mean,
        ppdu_average_power_mean,
    ):
        """RFmxWLAN_DSSSModAccFetchAveragePowers."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchAveragePowers_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchAveragePowers_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchAveragePowers"
                )
                self.RFmxWLAN_DSSSModAccFetchAveragePowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_DSSSModAccFetchAveragePowers_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchAveragePowers_cfunc(
            vi,
            selector_string,
            timeout,
            preamble_average_power_mean,
            header_average_power_mean,
            data_average_power_mean,
            ppdu_average_power_mean,
        )

    def RFmxWLAN_DSSSModAccFetchEVM(
        self,
        vi,
        selector_string,
        timeout,
        rms_evm_mean,
        peak_evm_80211_2016_maximum,
        peak_evm_80211_2007_maximum,
        peak_evm_80211_1999_maximum,
        frequency_error_mean,
        chip_clock_error_mean,
        number_of_chips_used,
    ):
        """RFmxWLAN_DSSSModAccFetchEVM."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchEVM_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchEVM_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchEVM"
                )
                self.RFmxWLAN_DSSSModAccFetchEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchEVM_cfunc(
            vi,
            selector_string,
            timeout,
            rms_evm_mean,
            peak_evm_80211_2016_maximum,
            peak_evm_80211_2007_maximum,
            peak_evm_80211_1999_maximum,
            frequency_error_mean,
            chip_clock_error_mean,
            number_of_chips_used,
        )

    def RFmxWLAN_DSSSModAccFetchIQImpairments(
        self,
        vi,
        selector_string,
        timeout,
        iq_origin_offset_mean,
        iq_gain_imbalance_mean,
        iq_quadrature_error_mean,
    ):
        """RFmxWLAN_DSSSModAccFetchIQImpairments."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchIQImpairments_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchIQImpairments_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchIQImpairments"
                )
                self.RFmxWLAN_DSSSModAccFetchIQImpairments_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_DSSSModAccFetchIQImpairments_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchIQImpairments_cfunc(
            vi,
            selector_string,
            timeout,
            iq_origin_offset_mean,
            iq_gain_imbalance_mean,
            iq_quadrature_error_mean,
        )

    def RFmxWLAN_DSSSModAccFetchPeakPowers(
        self,
        vi,
        selector_string,
        timeout,
        preamble_peak_power_maximum,
        header_peak_power_maximum,
        data_peak_power_maximum,
        ppdu_peak_power_maximum,
    ):
        """RFmxWLAN_DSSSModAccFetchPeakPowers."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchPeakPowers_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchPeakPowers_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchPeakPowers"
                )
                self.RFmxWLAN_DSSSModAccFetchPeakPowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_DSSSModAccFetchPeakPowers_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchPeakPowers_cfunc(
            vi,
            selector_string,
            timeout,
            preamble_peak_power_maximum,
            header_peak_power_maximum,
            data_peak_power_maximum,
            ppdu_peak_power_maximum,
        )

    def RFmxWLAN_DSSSModAccFetchPPDUInformation(
        self,
        vi,
        selector_string,
        timeout,
        data_modulation_format,
        payload_length,
        preamble_type,
        locked_clocks_bit,
        header_crc_status,
        psdu_crc_status,
    ):
        """RFmxWLAN_DSSSModAccFetchPPDUInformation."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchPPDUInformation_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchPPDUInformation_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchPPDUInformation"
                )
                self.RFmxWLAN_DSSSModAccFetchPPDUInformation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchPPDUInformation_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchPPDUInformation_cfunc(
            vi,
            selector_string,
            timeout,
            data_modulation_format,
            payload_length,
            preamble_type,
            locked_clocks_bit,
            header_crc_status,
            psdu_crc_status,
        )

    def RFmxWLAN_PowerRampFetchMeasurement(
        self, vi, selector_string, timeout, rise_time_mean, fall_time_mean
    ):
        """RFmxWLAN_PowerRampFetchMeasurement."""
        with self._func_lock:
            if self.RFmxWLAN_PowerRampFetchMeasurement_cfunc is None:
                self.RFmxWLAN_PowerRampFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxWLAN_PowerRampFetchMeasurement"
                )
                self.RFmxWLAN_PowerRampFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_PowerRampFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_PowerRampFetchMeasurement_cfunc(
            vi, selector_string, timeout, rise_time_mean, fall_time_mean
        )

    def RFmxWLAN_OFDMModAccFetchChainRMSEVM(
        self,
        vi,
        selector_string,
        timeout,
        chain_rms_evm_mean,
        chain_data_rms_evm_mean,
        chain_pilot_rms_evm_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchChainRMSEVM."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchChainRMSEVM_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVM_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchChainRMSEVM"
                )
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchChainRMSEVM_cfunc(
            vi,
            selector_string,
            timeout,
            chain_rms_evm_mean,
            chain_data_rms_evm_mean,
            chain_pilot_rms_evm_mean,
        )

    def RFmxWLAN_OFDMModAccFetchCompositeRMSEVM(
        self,
        vi,
        selector_string,
        timeout,
        composite_rms_evm_mean,
        composite_data_rms_evm_mean,
        composite_pilot_rms_evm_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchCompositeRMSEVM."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchCompositeRMSEVM"
                )
                self.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM_cfunc(
            vi,
            selector_string,
            timeout,
            composite_rms_evm_mean,
            composite_data_rms_evm_mean,
            composite_pilot_rms_evm_mean,
        )

    def RFmxWLAN_OFDMModAccFetchCrossPower(self, vi, selector_string, timeout, cross_power_mean):
        """RFmxWLAN_OFDMModAccFetchCrossPower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchCrossPower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchCrossPower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchCrossPower"
                )
                self.RFmxWLAN_OFDMModAccFetchCrossPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchCrossPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchCrossPower_cfunc(
            vi, selector_string, timeout, cross_power_mean
        )

    def RFmxWLAN_OFDMModAccFetchDataAveragePower(
        self, vi, selector_string, timeout, data_average_power_mean
    ):
        """RFmxWLAN_OFDMModAccFetchDataAveragePower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDataAveragePower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDataAveragePower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchDataAveragePower"
                )
                self.RFmxWLAN_OFDMModAccFetchDataAveragePower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchDataAveragePower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDataAveragePower_cfunc(
            vi, selector_string, timeout, data_average_power_mean
        )

    def RFmxWLAN_OFDMModAccFetchDataPeakPower(
        self, vi, selector_string, timeout, data_peak_power_maximum
    ):
        """RFmxWLAN_OFDMModAccFetchDataPeakPower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDataPeakPower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDataPeakPower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchDataPeakPower"
                )
                self.RFmxWLAN_OFDMModAccFetchDataPeakPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchDataPeakPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDataPeakPower_cfunc(
            vi, selector_string, timeout, data_peak_power_maximum
        )

    def RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent(
        self, vi, selector_string, timeout, frequency_error_ccdf_10_percent
    ):
        """RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent_cfunc(
            vi, selector_string, timeout, frequency_error_ccdf_10_percent
        )

    def RFmxWLAN_OFDMModAccFetchFrequencyErrorMean(
        self, vi, selector_string, timeout, frequency_error_mean
    ):
        """RFmxWLAN_OFDMModAccFetchFrequencyErrorMean."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchFrequencyErrorMean"
                )
                self.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean_cfunc(
            vi, selector_string, timeout, frequency_error_mean
        )

    def RFmxWLAN_OFDMModAccFetchGuardIntervalType(
        self, vi, selector_string, timeout, guard_interval_type
    ):
        """RFmxWLAN_OFDMModAccFetchGuardIntervalType."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchGuardIntervalType_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchGuardIntervalType_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchGuardIntervalType"
                )
                self.RFmxWLAN_OFDMModAccFetchGuardIntervalType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchGuardIntervalType_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchGuardIntervalType_cfunc(
            vi, selector_string, timeout, guard_interval_type
        )

    def RFmxWLAN_OFDMModAccFetchLTFSize(self, vi, selector_string, timeout, ltf_size):
        """RFmxWLAN_OFDMModAccFetchLTFSize."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchLTFSize_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchLTFSize_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchLTFSize"
                )
                self.RFmxWLAN_OFDMModAccFetchLTFSize_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchLTFSize_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchLTFSize_cfunc(vi, selector_string, timeout, ltf_size)

    def RFmxWLAN_OFDMModAccFetchIQImpairments(
        self,
        vi,
        selector_string,
        timeout,
        relative_iq_origin_offset_mean,
        iq_gain_imbalance_mean,
        iq_quadrature_error_mean,
        absolute_iq_origin_offset_mean,
        iq_timing_skew_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchIQImpairments."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchIQImpairments_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchIQImpairments_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchIQImpairments"
                )
                self.RFmxWLAN_OFDMModAccFetchIQImpairments_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchIQImpairments_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchIQImpairments_cfunc(
            vi,
            selector_string,
            timeout,
            relative_iq_origin_offset_mean,
            iq_gain_imbalance_mean,
            iq_quadrature_error_mean,
            absolute_iq_origin_offset_mean,
            iq_timing_skew_mean,
        )

    def RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus(
        self, vi, selector_string, timeout, l_sig_parity_check_status
    ):
        """RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus")
                )
                self.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus_cfunc(
            vi, selector_string, timeout, l_sig_parity_check_status
        )

    def RFmxWLAN_OFDMModAccFetchMCSIndex(self, vi, selector_string, timeout, mcs_index):
        """RFmxWLAN_OFDMModAccFetchMCSIndex."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchMCSIndex_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchMCSIndex_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchMCSIndex"
                )
                self.RFmxWLAN_OFDMModAccFetchMCSIndex_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchMCSIndex_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchMCSIndex_cfunc(vi, selector_string, timeout, mcs_index)

    def RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols(
        self, vi, selector_string, timeout, number_of_he_sig_b_symbols
    ):
        """RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols")
                )
                self.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols_cfunc(
            vi, selector_string, timeout, number_of_he_sig_b_symbols
        )

    def RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams(
        self, vi, selector_string, timeout, number_of_space_time_streams
    ):
        """RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams")
                )
                self.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams_cfunc(
            vi, selector_string, timeout, number_of_space_time_streams
        )

    def RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed(
        self, vi, selector_string, timeout, number_of_symbols_used
    ):
        """RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed"
                )
                self.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed_cfunc(
            vi, selector_string, timeout, number_of_symbols_used
        )

    def RFmxWLAN_OFDMModAccFetchNumberOfUsers(self, vi, selector_string, timeout, number_of_users):
        """RFmxWLAN_OFDMModAccFetchNumberOfUsers."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchNumberOfUsers_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchNumberOfUsers_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchNumberOfUsers"
                )
                self.RFmxWLAN_OFDMModAccFetchNumberOfUsers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchNumberOfUsers_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchNumberOfUsers_cfunc(
            vi, selector_string, timeout, number_of_users
        )

    def RFmxWLAN_OFDMModAccFetchPEAveragePower(
        self, vi, selector_string, timeout, pe_average_power_mean
    ):
        """RFmxWLAN_OFDMModAccFetchPEAveragePower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPEAveragePower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPEAveragePower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPEAveragePower"
                )
                self.RFmxWLAN_OFDMModAccFetchPEAveragePower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPEAveragePower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPEAveragePower_cfunc(
            vi, selector_string, timeout, pe_average_power_mean
        )

    def RFmxWLAN_OFDMModAccFetchPEPeakPower(
        self, vi, selector_string, timeout, pe_peak_power_maximum
    ):
        """RFmxWLAN_OFDMModAccFetchPEPeakPower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPEPeakPower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPEPeakPower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPEPeakPower"
                )
                self.RFmxWLAN_OFDMModAccFetchPEPeakPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPEPeakPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPEPeakPower_cfunc(
            vi, selector_string, timeout, pe_peak_power_maximum
        )

    def RFmxWLAN_OFDMModAccFetchPPDUAveragePower(
        self, vi, selector_string, timeout, ppdu_average_power_mean
    ):
        """RFmxWLAN_OFDMModAccFetchPPDUAveragePower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPPDUAveragePower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPPDUAveragePower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPPDUAveragePower"
                )
                self.RFmxWLAN_OFDMModAccFetchPPDUAveragePower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPPDUAveragePower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPPDUAveragePower_cfunc(
            vi, selector_string, timeout, ppdu_average_power_mean
        )

    def RFmxWLAN_OFDMModAccFetchPPDUPeakPower(
        self, vi, selector_string, timeout, ppdu_peak_power_maximum
    ):
        """RFmxWLAN_OFDMModAccFetchPPDUPeakPower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPPDUPeakPower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPPDUPeakPower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPPDUPeakPower"
                )
                self.RFmxWLAN_OFDMModAccFetchPPDUPeakPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPPDUPeakPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPPDUPeakPower_cfunc(
            vi, selector_string, timeout, ppdu_peak_power_maximum
        )

    def RFmxWLAN_OFDMModAccFetchPPDUType(self, vi, selector_string, timeout, ppdu_type):
        """RFmxWLAN_OFDMModAccFetchPPDUType."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPPDUType_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPPDUType_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPPDUType"
                )
                self.RFmxWLAN_OFDMModAccFetchPPDUType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchPPDUType_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPPDUType_cfunc(vi, selector_string, timeout, ppdu_type)

    def RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac(
        self,
        vi,
        selector_string,
        timeout,
        vht_sig_a_average_power_mean,
        vht_stf_average_power_mean,
        vht_ltf_average_power_mean,
        vht_sig_b_average_power_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac_cfunc(
            vi,
            selector_string,
            timeout,
            vht_sig_a_average_power_mean,
            vht_stf_average_power_mean,
            vht_ltf_average_power_mean,
            vht_sig_b_average_power_mean,
        )

    def RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax(
        self,
        vi,
        selector_string,
        timeout,
        rl_sig_average_power_mean,
        he_sig_a_average_power_mean,
        he_sig_b_average_power_mean,
        he_stf_average_power_mean,
        he_ltf_average_power_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax_cfunc(
            vi,
            selector_string,
            timeout,
            rl_sig_average_power_mean,
            he_sig_a_average_power_mean,
            he_sig_b_average_power_mean,
            he_stf_average_power_mean,
            he_ltf_average_power_mean,
        )

    def RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be(
        self,
        vi,
        selector_string,
        timeout,
        rl_sig_average_power_mean,
        u_sig_average_power_mean,
        eht_sig_average_power_mean,
        eht_stf_average_power_mean,
        eht_ltf_average_power_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be_cfunc(
            vi,
            selector_string,
            timeout,
            rl_sig_average_power_mean,
            u_sig_average_power_mean,
            eht_sig_average_power_mean,
            eht_stf_average_power_mean,
            eht_ltf_average_power_mean,
        )

    def RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n(
        self,
        vi,
        selector_string,
        timeout,
        ht_sig_average_power_mean,
        ht_stf_average_power_mean,
        ht_dltf_average_power_mean,
        ht_eltf_average_power_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n_cfunc(
            vi,
            selector_string,
            timeout,
            ht_sig_average_power_mean,
            ht_stf_average_power_mean,
            ht_dltf_average_power_mean,
            ht_eltf_average_power_mean,
        )

    def RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon(
        self,
        vi,
        selector_string,
        timeout,
        l_stf_average_power_mean,
        l_ltf_average_power_mean,
        l_sig_average_power_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon_cfunc(
            vi,
            selector_string,
            timeout,
            l_stf_average_power_mean,
            l_ltf_average_power_mean,
            l_sig_average_power_mean,
        )

    def RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac(
        self,
        vi,
        selector_string,
        timeout,
        vht_sig_a_peak_power_maximum,
        vht_stf_peak_power_maximum,
        vht_ltf_peak_power_maximum,
        vht_sig_b_peak_power_maximum,
    ):
        """RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac")
                )
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac_cfunc(
            vi,
            selector_string,
            timeout,
            vht_sig_a_peak_power_maximum,
            vht_stf_peak_power_maximum,
            vht_ltf_peak_power_maximum,
            vht_sig_b_peak_power_maximum,
        )

    def RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax(
        self,
        vi,
        selector_string,
        timeout,
        rl_sig_peak_power_maximum,
        he_sig_a_peak_power_maximum,
        he_sig_b_peak_power_maximum,
        he_stf_peak_power_maximum,
        he_ltf_peak_power_maximum,
    ):
        """RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax")
                )
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax_cfunc(
            vi,
            selector_string,
            timeout,
            rl_sig_peak_power_maximum,
            he_sig_a_peak_power_maximum,
            he_sig_b_peak_power_maximum,
            he_stf_peak_power_maximum,
            he_ltf_peak_power_maximum,
        )

    def RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be(
        self,
        vi,
        selector_string,
        timeout,
        rl_sig_peak_power_maximum,
        u_sig_peak_power_maximum,
        eht_sig_peak_power_maximum,
        eht_stf_peak_power_maximum,
        eht_ltf_peak_power_maximum,
    ):
        """RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be")
                )
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be_cfunc(
            vi,
            selector_string,
            timeout,
            rl_sig_peak_power_maximum,
            u_sig_peak_power_maximum,
            eht_sig_peak_power_maximum,
            eht_stf_peak_power_maximum,
            eht_ltf_peak_power_maximum,
        )

    def RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n(
        self,
        vi,
        selector_string,
        timeout,
        ht_sig_peak_power_maximum,
        ht_stf_peak_power_maximum,
        ht_dltf_peak_power_maximum,
        ht_eltf_peak_power_maximum,
    ):
        """RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n")
                )
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n_cfunc(
            vi,
            selector_string,
            timeout,
            ht_sig_peak_power_maximum,
            ht_stf_peak_power_maximum,
            ht_dltf_peak_power_maximum,
            ht_eltf_peak_power_maximum,
        )

    def RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon(
        self,
        vi,
        selector_string,
        timeout,
        l_stf_peak_power_maximum,
        l_ltf_peak_power_maximum,
        l_sig_peak_power_maximum,
    ):
        """RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon")
                )
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon_cfunc(
            vi,
            selector_string,
            timeout,
            l_stf_peak_power_maximum,
            l_ltf_peak_power_maximum,
            l_sig_peak_power_maximum,
        )

    def RFmxWLAN_OFDMModAccFetchPSDUCRCStatus(self, vi, selector_string, timeout, psdu_crc_status):
        """RFmxWLAN_OFDMModAccFetchPSDUCRCStatus."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPSDUCRCStatus"
                )
                self.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus_cfunc(
            vi, selector_string, timeout, psdu_crc_status
        )

    def RFmxWLAN_OFDMModAccFetchPEDuration(self, vi, selector_string, timeout, pe_duration):
        """RFmxWLAN_OFDMModAccFetchPEDuration."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPEDuration_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPEDuration_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchPEDuration"
                )
                self.RFmxWLAN_OFDMModAccFetchPEDuration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchPEDuration_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPEDuration_cfunc(
            vi, selector_string, timeout, pe_duration
        )

    def RFmxWLAN_OFDMModAccFetchRUOffsetAndSize(
        self, vi, selector_string, timeout, ru_offset, ru_size
    ):
        """RFmxWLAN_OFDMModAccFetchRUOffsetAndSize."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchRUOffsetAndSize"
                )
                self.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize_cfunc(
            vi, selector_string, timeout, ru_offset, ru_size
        )

    def RFmxWLAN_OFDMModAccFetchSIGCRCStatus(self, vi, selector_string, timeout, sig_crc_status):
        """RFmxWLAN_OFDMModAccFetchSIGCRCStatus."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSIGCRCStatus_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSIGCRCStatus_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchSIGCRCStatus"
                )
                self.RFmxWLAN_OFDMModAccFetchSIGCRCStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSIGCRCStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchSIGCRCStatus_cfunc(
            vi, selector_string, timeout, sig_crc_status
        )

    def RFmxWLAN_OFDMModAccFetchSIGBCRCStatus(self, vi, selector_string, timeout, sig_b_crc_status):
        """RFmxWLAN_OFDMModAccFetchSIGBCRCStatus."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchSIGBCRCStatus"
                )
                self.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus_cfunc(
            vi, selector_string, timeout, sig_b_crc_status
        )

    def RFmxWLAN_OFDMModAccFetchSpectralFlatness(
        self,
        vi,
        selector_string,
        timeout,
        spectral_flatness_margin,
        spectral_flatness_margin_subcarrier_index,
    ):
        """RFmxWLAN_OFDMModAccFetchSpectralFlatness."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSpectralFlatness_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSpectralFlatness_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchSpectralFlatness"
                )
                self.RFmxWLAN_OFDMModAccFetchSpectralFlatness_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSpectralFlatness_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchSpectralFlatness_cfunc(
            vi,
            selector_string,
            timeout,
            spectral_flatness_margin,
            spectral_flatness_margin_subcarrier_index,
        )

    def RFmxWLAN_OFDMModAccFetchStreamRMSEVM(
        self,
        vi,
        selector_string,
        timeout,
        stream_rms_evm_mean,
        stream_data_rms_evm_mean,
        stream_pilot_rms_evm_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchStreamRMSEVM."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchStreamRMSEVM_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVM_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchStreamRMSEVM"
                )
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchStreamRMSEVM_cfunc(
            vi,
            selector_string,
            timeout,
            stream_rms_evm_mean,
            stream_data_rms_evm_mean,
            stream_pilot_rms_evm_mean,
        )

    def RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean(
        self, vi, selector_string, timeout, symbol_clock_error_mean
    ):
        """RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean")
                )
                self.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean_cfunc(
            vi, selector_string, timeout, symbol_clock_error_mean
        )

    def RFmxWLAN_OFDMModAccFetchUnusedToneError(
        self,
        vi,
        selector_string,
        timeout,
        unused_tone_error_margin,
        unused_tone_error_margin_ru_index,
    ):
        """RFmxWLAN_OFDMModAccFetchUnusedToneError."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUnusedToneError_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUnusedToneError_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchUnusedToneError"
                )
                self.RFmxWLAN_OFDMModAccFetchUnusedToneError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUnusedToneError_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchUnusedToneError_cfunc(
            vi,
            selector_string,
            timeout,
            unused_tone_error_margin,
            unused_tone_error_margin_ru_index,
        )

    def RFmxWLAN_OFDMModAccFetchUserPower(self, vi, selector_string, timeout, user_power_mean):
        """RFmxWLAN_OFDMModAccFetchUserPower."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserPower_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserPower_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchUserPower"
                )
                self.RFmxWLAN_OFDMModAccFetchUserPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchUserPower_cfunc(
            vi, selector_string, timeout, user_power_mean
        )

    def RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM(
        self,
        vi,
        selector_string,
        timeout,
        user_stream_rms_evm_mean,
        user_stream_data_rms_evm_mean,
        user_stream_pilot_rms_evm_mean,
    ):
        """RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM"
                )
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM_cfunc(
            vi,
            selector_string,
            timeout,
            user_stream_rms_evm_mean,
            user_stream_data_rms_evm_mean,
            user_stream_pilot_rms_evm_mean,
        )

    def RFmxWLAN_SEMFetchCarrierMeasurement(
        self, vi, selector_string, timeout, absolute_power, relative_power
    ):
        """RFmxWLAN_SEMFetchCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchCarrierMeasurement_cfunc is None:
                self.RFmxWLAN_SEMFetchCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchCarrierMeasurement"
                )
                self.RFmxWLAN_SEMFetchCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_SEMFetchCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchCarrierMeasurement_cfunc(
            vi, selector_string, timeout, absolute_power, relative_power
        )

    def RFmxWLAN_SEMFetchLowerOffsetMargin(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
    ):
        """RFmxWLAN_SEMFetchLowerOffsetMargin."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchLowerOffsetMargin_cfunc is None:
                self.RFmxWLAN_SEMFetchLowerOffsetMargin_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchLowerOffsetMargin"
                )
                self.RFmxWLAN_SEMFetchLowerOffsetMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_SEMFetchLowerOffsetMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchLowerOffsetMargin_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
        )

    def RFmxWLAN_SEMFetchLowerOffsetPower(
        self,
        vi,
        selector_string,
        timeout,
        total_absolute_power,
        total_relative_power,
        peak_absolute_power,
        peak_frequency,
        peak_relative_power,
    ):
        """RFmxWLAN_SEMFetchLowerOffsetPower."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchLowerOffsetPower_cfunc is None:
                self.RFmxWLAN_SEMFetchLowerOffsetPower_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchLowerOffsetPower"
                )
                self.RFmxWLAN_SEMFetchLowerOffsetPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_SEMFetchLowerOffsetPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchLowerOffsetPower_cfunc(
            vi,
            selector_string,
            timeout,
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
        )

    def RFmxWLAN_SEMFetchMeasurementStatus(self, vi, selector_string, timeout, measurement_status):
        """RFmxWLAN_SEMFetchMeasurementStatus."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchMeasurementStatus_cfunc is None:
                self.RFmxWLAN_SEMFetchMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchMeasurementStatus"
                )
                self.RFmxWLAN_SEMFetchMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_SEMFetchMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchMeasurementStatus_cfunc(
            vi, selector_string, timeout, measurement_status
        )

    def RFmxWLAN_SEMFetchUpperOffsetMargin(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
    ):
        """RFmxWLAN_SEMFetchUpperOffsetMargin."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchUpperOffsetMargin_cfunc is None:
                self.RFmxWLAN_SEMFetchUpperOffsetMargin_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchUpperOffsetMargin"
                )
                self.RFmxWLAN_SEMFetchUpperOffsetMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_SEMFetchUpperOffsetMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchUpperOffsetMargin_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
        )

    def RFmxWLAN_SEMFetchUpperOffsetPower(
        self,
        vi,
        selector_string,
        timeout,
        total_absolute_power,
        total_relative_power,
        peak_absolute_power,
        peak_frequency,
        peak_relative_power,
    ):
        """RFmxWLAN_SEMFetchUpperOffsetPower."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchUpperOffsetPower_cfunc is None:
                self.RFmxWLAN_SEMFetchUpperOffsetPower_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchUpperOffsetPower"
                )
                self.RFmxWLAN_SEMFetchUpperOffsetPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxWLAN_SEMFetchUpperOffsetPower_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchUpperOffsetPower_cfunc(
            vi,
            selector_string,
            timeout,
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
        )

    def RFmxWLAN_TXPFetchPowerTrace(
        self, vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
    ):
        """RFmxWLAN_TXPFetchPowerTrace."""
        with self._func_lock:
            if self.RFmxWLAN_TXPFetchPowerTrace_cfunc is None:
                self.RFmxWLAN_TXPFetchPowerTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_TXPFetchPowerTrace"
                )
                self.RFmxWLAN_TXPFetchPowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_TXPFetchPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_TXPFetchPowerTrace_cfunc(
            vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
        )

    def RFmxWLAN_DSSSModAccFetchConstellationTrace(
        self, vi, selector_string, timeout, constellation, array_size, actual_array_size
    ):
        """RFmxWLAN_DSSSModAccFetchConstellationTrace."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchConstellationTrace_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchConstellationTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchConstellationTrace"
                )
                self.RFmxWLAN_DSSSModAccFetchConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchConstellationTrace_cfunc(
            vi, selector_string, timeout, constellation, array_size, actual_array_size
        )

    def RFmxWLAN_DSSSModAccFetchCustomGatePowersArray(
        self,
        vi,
        selector_string,
        timeout,
        average_power_mean,
        peak_power_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_DSSSModAccFetchCustomGatePowersArray."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray_cfunc = (
                    self._get_library_function("RFmxWLAN_DSSSModAccFetchCustomGatePowersArray")
                )
                self.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray_cfunc(
            vi,
            selector_string,
            timeout,
            average_power_mean,
            peak_power_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace(
        self, vi, selector_string, timeout, decoded_header_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace")
                )
                self.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_header_bits, array_size, actual_array_size
        )

    def RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace(
        self, vi, selector_string, timeout, decoded_psdu_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace")
                )
                self.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_psdu_bits, array_size, actual_array_size
        )

    def RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace(
        self, vi, selector_string, timeout, x0, dx, evm_per_chip_mean, array_size, actual_array_size
    ):
        """RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace_cfunc is None:
                self.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace"
                )
                self.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace_cfunc(
            vi, selector_string, timeout, x0, dx, evm_per_chip_mean, array_size, actual_array_size
        )

    def RFmxWLAN_PowerRampFetchFallTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        raw_waveform,
        processed_waveform,
        threshold,
        power_reference,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_PowerRampFetchFallTrace."""
        with self._func_lock:
            if self.RFmxWLAN_PowerRampFetchFallTrace_cfunc is None:
                self.RFmxWLAN_PowerRampFetchFallTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_PowerRampFetchFallTrace"
                )
                self.RFmxWLAN_PowerRampFetchFallTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_PowerRampFetchFallTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_PowerRampFetchFallTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            raw_waveform,
            processed_waveform,
            threshold,
            power_reference,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_PowerRampFetchRiseTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        raw_waveform,
        processed_waveform,
        threshold,
        power_reference,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_PowerRampFetchRiseTrace."""
        with self._func_lock:
            if self.RFmxWLAN_PowerRampFetchRiseTrace_cfunc is None:
                self.RFmxWLAN_PowerRampFetchRiseTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_PowerRampFetchRiseTrace"
                )
                self.RFmxWLAN_PowerRampFetchRiseTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_PowerRampFetchRiseTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_PowerRampFetchRiseTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            raw_waveform,
            processed_waveform,
            threshold,
            power_reference,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        chain_data_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            chain_data_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        chain_pilot_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            chain_pilot_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        chain_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            chain_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        chain_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            chain_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        channel_frequency_response_mean_magnitude,
        channel_frequency_response_mean_phase,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            channel_frequency_response_mean_magnitude,
            channel_frequency_response_mean_phase,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace(
        self, vi, selector_string, timeout, x0, dx, group_delay_mean, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace"
                )
                self.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace_cfunc(
            vi, selector_string, timeout, x0, dx, group_delay_mean, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        common_pilot_error_magnitude,
        common_pilot_error_phase,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            common_pilot_error_magnitude,
            common_pilot_error_phase,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchCustomGatePowersArray(
        self,
        vi,
        selector_string,
        timeout,
        average_power_mean,
        peak_power_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchCustomGatePowersArray."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchCustomGatePowersArray")
                )
                self.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray_cfunc(
            vi,
            selector_string,
            timeout,
            average_power_mean,
            peak_power_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchDataConstellationTrace(
        self, vi, selector_string, timeout, data_constellation, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDataConstellationTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDataConstellationTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDataConstellationTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDataConstellationTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDataConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDataConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDataConstellationTrace_cfunc(
            vi, selector_string, timeout, data_constellation, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace(
        self,
        vi,
        selector_string,
        timeout,
        reference_data_constellation,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace_cfunc(
            vi,
            selector_string,
            timeout,
            reference_data_constellation,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace(
        self, vi, selector_string, timeout, decoded_l_sig_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_l_sig_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace(
        self, vi, selector_string, timeout, decoded_psdu_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_psdu_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace(
        self, vi, selector_string, timeout, decoded_service_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_service_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace(
        self, vi, selector_string, timeout, decoded_sig_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace"
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_sig_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace(
        self, vi, selector_string, timeout, decoded_sig_b_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_sig_b_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace(
        self, vi, selector_string, timeout, decoded_u_sig_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_u_sig_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace(
        self, vi, selector_string, timeout, decoded_eht_sig_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_eht_sig_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace(
        self, vi, selector_string, timeout, decoded_uhr_sig_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_uhr_sig_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace(
        self, vi, selector_string, timeout, decoded_elr_sig_bits, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace_cfunc(
            vi, selector_string, timeout, decoded_elr_sig_bits, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices(
        self, vi, selector_string, timeout, subcarrier_indices, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices")
                )
                self.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices_cfunc(
            vi, selector_string, timeout, subcarrier_indices, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        iq_gain_imbalance_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            iq_gain_imbalance_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        iq_quadrature_error_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            iq_quadrature_error_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchPilotConstellationTrace(
        self, vi, selector_string, timeout, pilot_constellation, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchPilotConstellationTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPilotConstellationTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace_cfunc(
            vi, selector_string, timeout, pilot_constellation, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        preamble_frequency_error,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            preamble_frequency_error,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        spectral_flatness_mean,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            spectral_flatness_mean,
            spectral_flatness_lower_mask,
            spectral_flatness_upper_mask,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        stream_data_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            stream_data_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        stream_pilot_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            stream_pilot_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        stream_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            stream_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        stream_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            stream_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        subcarrier_index,
        x0,
        dx,
        subcarrier_chain_evm_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            subcarrier_index,
            x0,
            dx,
            subcarrier_chain_evm_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace(
        self,
        vi,
        selector_string,
        timeout,
        subcarrier_index,
        x0,
        dx,
        subcarrier_stream_evm_per_symbol,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace_cfunc(
            vi,
            selector_string,
            timeout,
            subcarrier_index,
            x0,
            dx,
            subcarrier_stream_evm_per_symbol,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace(
        self,
        vi,
        selector_string,
        timeout,
        symbol_index,
        x0,
        dx,
        symbol_chain_evm_per_subcarrier,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace_cfunc(
            vi,
            selector_string,
            timeout,
            symbol_index,
            x0,
            dx,
            symbol_chain_evm_per_subcarrier,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace(
        self,
        vi,
        selector_string,
        timeout,
        symbol_index,
        x0,
        dx,
        symbol_stream_evm_per_subcarrier,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace_cfunc(
            vi,
            selector_string,
            timeout,
            symbol_index,
            x0,
            dx,
            symbol_stream_evm_per_subcarrier,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU(
        self,
        vi,
        selector_string,
        timeout,
        unused_tone_error_margin_per_ru,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU")
                )
                self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU_cfunc(
            vi,
            selector_string,
            timeout,
            unused_tone_error_margin_per_ru,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        unused_tone_error,
        unused_tone_error_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            unused_tone_error,
            unused_tone_error_mask,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace(
        self, vi, selector_string, timeout, user_data_constellation, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace_cfunc(
            vi, selector_string, timeout, user_data_constellation, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace(
        self, vi, selector_string, timeout, user_pilot_constellation, array_size, actual_array_size
    ):
        """RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace_cfunc(
            vi, selector_string, timeout, user_pilot_constellation, array_size, actual_array_size
        )

    def RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        user_stream_data_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            user_stream_data_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        user_stream_pilot_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            user_stream_pilot_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        user_stream_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            user_stream_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        user_stream_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace"
                    )
                )
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            user_stream_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        phase_noise_psd_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace_cfunc is None:
                self.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace")
                )
                self.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            phase_noise_psd_mean,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_SEMFetchLowerOffsetMarginArray(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_SEMFetchLowerOffsetMarginArray."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchLowerOffsetMarginArray_cfunc is None:
                self.RFmxWLAN_SEMFetchLowerOffsetMarginArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchLowerOffsetMarginArray"
                )
                self.RFmxWLAN_SEMFetchLowerOffsetMarginArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_SEMFetchLowerOffsetMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchLowerOffsetMarginArray_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_SEMFetchLowerOffsetPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        total_absolute_power,
        total_relative_power,
        peak_absolute_power,
        peak_frequency,
        peak_relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_SEMFetchLowerOffsetPowerArray."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchLowerOffsetPowerArray_cfunc is None:
                self.RFmxWLAN_SEMFetchLowerOffsetPowerArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchLowerOffsetPowerArray"
                )
                self.RFmxWLAN_SEMFetchLowerOffsetPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_SEMFetchLowerOffsetPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchLowerOffsetPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_SEMFetchSpectrum(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        spectrum,
        composite_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_SEMFetchSpectrum."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchSpectrum_cfunc is None:
                self.RFmxWLAN_SEMFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchSpectrum"
                )
                self.RFmxWLAN_SEMFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_SEMFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchSpectrum_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            spectrum,
            composite_mask,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_SEMFetchUpperOffsetMarginArray(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        margin,
        margin_frequency,
        margin_absolute_power,
        margin_relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_SEMFetchUpperOffsetMarginArray."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchUpperOffsetMarginArray_cfunc is None:
                self.RFmxWLAN_SEMFetchUpperOffsetMarginArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchUpperOffsetMarginArray"
                )
                self.RFmxWLAN_SEMFetchUpperOffsetMarginArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_SEMFetchUpperOffsetMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchUpperOffsetMarginArray_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_SEMFetchUpperOffsetPowerArray(
        self,
        vi,
        selector_string,
        timeout,
        total_absolute_power,
        total_relative_power,
        peak_absolute_power,
        peak_frequency,
        peak_relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxWLAN_SEMFetchUpperOffsetPowerArray."""
        with self._func_lock:
            if self.RFmxWLAN_SEMFetchUpperOffsetPowerArray_cfunc is None:
                self.RFmxWLAN_SEMFetchUpperOffsetPowerArray_cfunc = self._get_library_function(
                    "RFmxWLAN_SEMFetchUpperOffsetPowerArray"
                )
                self.RFmxWLAN_SEMFetchUpperOffsetPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_SEMFetchUpperOffsetPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SEMFetchUpperOffsetPowerArray_cfunc(
            vi,
            selector_string,
            timeout,
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxWLAN_CloneSignalConfiguration(self, vi, old_signal_name, new_signal_name):
        """RFmxWLAN_CloneSignalConfiguration."""
        with self._func_lock:
            if self.RFmxWLAN_CloneSignalConfiguration_cfunc is None:
                self.RFmxWLAN_CloneSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxWLAN_CloneSignalConfiguration"
                )
                self.RFmxWLAN_CloneSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_CloneSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_CloneSignalConfiguration_cfunc(vi, old_signal_name, new_signal_name)

    def RFmxWLAN_DeleteSignalConfiguration(self, vi, signal_name):
        """RFmxWLAN_DeleteSignalConfiguration."""
        with self._func_lock:
            if self.RFmxWLAN_DeleteSignalConfiguration_cfunc is None:
                self.RFmxWLAN_DeleteSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxWLAN_DeleteSignalConfiguration"
                )
                self.RFmxWLAN_DeleteSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_DeleteSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_DeleteSignalConfiguration_cfunc(vi, signal_name)

    def RFmxWLAN_SendSoftwareEdgeTrigger(self, vi):
        """RFmxWLAN_SendSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxWLAN_SendSoftwareEdgeTrigger_cfunc is None:
                self.RFmxWLAN_SendSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxWLAN_SendSoftwareEdgeTrigger"
                )
                self.RFmxWLAN_SendSoftwareEdgeTrigger_cfunc.argtypes = [ctypes.c_uint32]
                self.RFmxWLAN_SendSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_SendSoftwareEdgeTrigger_cfunc(vi)

    def RFmxWLAN_GetAllNamedResultNames(
        self,
        vi,
        selector_string,
        result_names,
        result_names_buffer_size,
        actual_result_names_size,
        default_result_exists,
    ):
        """RFmxWLAN_GetAllNamedResultNames."""
        with self._func_lock:
            if self.RFmxWLAN_GetAllNamedResultNames_cfunc is None:
                self.RFmxWLAN_GetAllNamedResultNames_cfunc = self._get_library_function(
                    "RFmxWLAN_GetAllNamedResultNames"
                )
                self.RFmxWLAN_GetAllNamedResultNames_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxWLAN_GetAllNamedResultNames_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_GetAllNamedResultNames_cfunc(
            vi,
            selector_string,
            result_names,
            result_names_buffer_size,
            actual_result_names_size,
            default_result_exists,
        )

    def RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase(self, vi, selector_string):
        """RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase_cfunc is None:
                self.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase_cfunc = (
                    self._get_library_function("RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase")
                )
                self.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase_cfunc(vi, selector_string)

    def RFmxWLAN_AnalyzeIQ1Waveform(
        self, vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
    ):
        """RFmxWLAN_AnalyzeIQ1Waveform."""
        with self._func_lock:
            if self.RFmxWLAN_AnalyzeIQ1Waveform_cfunc is None:
                self.RFmxWLAN_AnalyzeIQ1Waveform_cfunc = self._get_library_function(
                    "RFmxWLAN_AnalyzeIQ1Waveform"
                )
                self.RFmxWLAN_AnalyzeIQ1Waveform_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int64,
                ]
                self.RFmxWLAN_AnalyzeIQ1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AnalyzeIQ1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
        )

    def RFmxWLAN_AnalyzeSpectrum1Waveform(
        self, vi, selector_string, result_name, x0, dx, spectrum, array_size, reset, reserved
    ):
        """RFmxWLAN_AnalyzeSpectrum1Waveform."""
        with self._func_lock:
            if self.RFmxWLAN_AnalyzeSpectrum1Waveform_cfunc is None:
                self.RFmxWLAN_AnalyzeSpectrum1Waveform_cfunc = self._get_library_function(
                    "RFmxWLAN_AnalyzeSpectrum1Waveform"
                )
                self.RFmxWLAN_AnalyzeSpectrum1Waveform_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int64,
                ]
                self.RFmxWLAN_AnalyzeSpectrum1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AnalyzeSpectrum1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, spectrum, array_size, reset, reserved
        )

    def RFmxWLAN_AnalyzeNWaveformsIQ(
        self, vi, selector_string, result_name, x0, dx, iq, iq_size, array_size, reset
    ):
        """RFmxWLAN_AnalyzeNWaveformsIQ."""
        with self._func_lock:
            if self.RFmxWLAN_AnalyzeNWaveformsIQ_cfunc is None:
                self.RFmxWLAN_AnalyzeNWaveformsIQ_cfunc = self._get_library_function(
                    "RFmxWLAN_AnalyzeNWaveformsIQ"
                )
                self.RFmxWLAN_AnalyzeNWaveformsIQ_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_AnalyzeNWaveformsIQ_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AnalyzeNWaveformsIQ_cfunc(
            vi, selector_string, result_name, x0, dx, iq, iq_size, array_size, reset
        )

    def RFmxWLAN_AnalyzeNWaveformsSpectrum(
        self, vi, selector_string, result_name, x0, dx, spectrum, spectrum_size, array_size, reset
    ):
        """RFmxWLAN_AnalyzeNWaveformsSpectrum."""
        with self._func_lock:
            if self.RFmxWLAN_AnalyzeNWaveformsSpectrum_cfunc is None:
                self.RFmxWLAN_AnalyzeNWaveformsSpectrum_cfunc = self._get_library_function(
                    "RFmxWLAN_AnalyzeNWaveformsSpectrum"
                )
                self.RFmxWLAN_AnalyzeNWaveformsSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_AnalyzeNWaveformsSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_AnalyzeNWaveformsSpectrum_cfunc(
            vi, selector_string, result_name, x0, dx, spectrum, spectrum_size, array_size, reset
        )

    def RFmxWLAN_OFDMModAccCfgNReferenceWaveforms(
        self, vi, selector_string, x0, dx, reference_waveform, reference_waveform_size, array_size
    ):
        """RFmxWLAN_OFDMModAccCfgNReferenceWaveforms."""
        with self._func_lock:
            if self.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms_cfunc is None:
                self.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms_cfunc = self._get_library_function(
                    "RFmxWLAN_OFDMModAccCfgNReferenceWaveforms"
                )
                self.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms_cfunc.restype = ctypes.c_int32
        return self.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms_cfunc(
            vi, selector_string, x0, dx, reference_waveform, reference_waveform_size, array_size
        )
        return 0
