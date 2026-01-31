"""Wrapper around driver library.
Class will setup the correct ctypes information for every function on first call.
"""

import ctypes
import threading
from typing import Any

import nirfmxnr.errors as errors
import nirfmxnr.internal._custom_types as _custom_types


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
        self.RFmxNR_ResetAttribute_cfunc = None
        self.RFmxNR_GetError_cfunc = None
        self.RFmxNR_GetErrorString_cfunc = None
        self.RFmxNR_GetAttributeI8_cfunc = None
        self.RFmxNR_SetAttributeI8_cfunc = None
        self.RFmxNR_GetAttributeI8Array_cfunc = None
        self.RFmxNR_SetAttributeI8Array_cfunc = None
        self.RFmxNR_GetAttributeI16_cfunc = None
        self.RFmxNR_SetAttributeI16_cfunc = None
        self.RFmxNR_GetAttributeI32_cfunc = None
        self.RFmxNR_SetAttributeI32_cfunc = None
        self.RFmxNR_GetAttributeI32Array_cfunc = None
        self.RFmxNR_SetAttributeI32Array_cfunc = None
        self.RFmxNR_GetAttributeI64_cfunc = None
        self.RFmxNR_SetAttributeI64_cfunc = None
        self.RFmxNR_GetAttributeI64Array_cfunc = None
        self.RFmxNR_SetAttributeI64Array_cfunc = None
        self.RFmxNR_GetAttributeU8_cfunc = None
        self.RFmxNR_SetAttributeU8_cfunc = None
        self.RFmxNR_GetAttributeU8Array_cfunc = None
        self.RFmxNR_SetAttributeU8Array_cfunc = None
        self.RFmxNR_GetAttributeU16_cfunc = None
        self.RFmxNR_SetAttributeU16_cfunc = None
        self.RFmxNR_GetAttributeU32_cfunc = None
        self.RFmxNR_SetAttributeU32_cfunc = None
        self.RFmxNR_GetAttributeU32Array_cfunc = None
        self.RFmxNR_SetAttributeU32Array_cfunc = None
        self.RFmxNR_GetAttributeU64Array_cfunc = None
        self.RFmxNR_SetAttributeU64Array_cfunc = None
        self.RFmxNR_GetAttributeF32_cfunc = None
        self.RFmxNR_SetAttributeF32_cfunc = None
        self.RFmxNR_GetAttributeF32Array_cfunc = None
        self.RFmxNR_SetAttributeF32Array_cfunc = None
        self.RFmxNR_GetAttributeF64_cfunc = None
        self.RFmxNR_SetAttributeF64_cfunc = None
        self.RFmxNR_GetAttributeF64Array_cfunc = None
        self.RFmxNR_SetAttributeF64Array_cfunc = None
        self.RFmxNR_GetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxNR_SetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxNR_GetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxNR_SetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxNR_GetAttributeString_cfunc = None
        self.RFmxNR_SetAttributeString_cfunc = None
        self.RFmxNR_ModAccCfgReferenceWaveform_cfunc = None
        self.RFmxNR_ModAccAutoLevel_cfunc = None
        self.RFmxNR_ModAccValidateCalibrationData_cfunc = None
        self.RFmxNR_ModAccClearNoiseCalibrationDatabase_cfunc = None
        self.RFmxNR_ACPValidateNoiseCalibrationData_cfunc = None
        self.RFmxNR_CHPValidateNoiseCalibrationData_cfunc = None
        self.RFmxNR_AbortMeasurements_cfunc = None
        self.RFmxNR_AnalyzeIQ1Waveform_cfunc = None
        self.RFmxNR_AnalyzeSpectrum1Waveform_cfunc = None
        self.RFmxNR_AnalyzeNWaveformsIQ_cfunc = None
        self.RFmxNR_AnalyzeNWaveformsSpectrum_cfunc = None
        self.RFmxNR_AutoLevel_cfunc = None
        self.RFmxNR_CheckMeasurementStatus_cfunc = None
        self.RFmxNR_ClearAllNamedResults_cfunc = None
        self.RFmxNR_ClearNamedResult_cfunc = None
        self.RFmxNR_ClearNoiseCalibrationDatabase_cfunc = None
        self.RFmxNR_CloneSignalConfiguration_cfunc = None
        self.RFmxNR_Commit_cfunc = None
        self.RFmxNR_CfgDigitalEdgeTrigger_cfunc = None
        self.RFmxNR_CfgIQPowerEdgeTrigger_cfunc = None
        self.RFmxNR_CfgSelectedPortsMultiple_cfunc = None
        self.RFmxNR_CfgSoftwareEdgeTrigger_cfunc = None
        self.RFmxNR_CreateList_cfunc = None
        self.RFmxNR_CreateListStep_cfunc = None
        self.RFmxNR_CreateSignalConfiguration_cfunc = None
        self.RFmxNR_DeleteList_cfunc = None
        self.RFmxNR_DeleteSignalConfiguration_cfunc = None
        self.RFmxNR_DisableTrigger_cfunc = None
        self.RFmxNR_GetAllNamedResultNames_cfunc = None
        self.RFmxNR_Initiate_cfunc = None
        self.RFmxNR_ResetToDefault_cfunc = None
        self.RFmxNR_SelectMeasurements_cfunc = None
        self.RFmxNR_SendSoftwareEdgeTrigger_cfunc = None
        self.RFmxNR_WaitForMeasurementComplete_cfunc = None
        self.RFmxNR_LoadFromGenerationConfigurationFile_cfunc = None
        self.RFmxNR_ModAccCfgMeasurementMode_cfunc = None
        self.RFmxNR_ModAccCfgNoiseCompensationEnabled_cfunc = None
        self.RFmxNR_ACPCfgAveraging_cfunc = None
        self.RFmxNR_ACPCfgMeasurementMethod_cfunc = None
        self.RFmxNR_ACPCfgNoiseCompensationEnabled_cfunc = None
        self.RFmxNR_ACPCfgNumberOfENDCOffsets_cfunc = None
        self.RFmxNR_ACPCfgNumberOfEUTRAOffsets_cfunc = None
        self.RFmxNR_ACPCfgNumberOfNROffsets_cfunc = None
        self.RFmxNR_ACPCfgNumberOfUTRAOffsets_cfunc = None
        self.RFmxNR_ACPCfgRBWFilter_cfunc = None
        self.RFmxNR_ACPCfgSweepTime_cfunc = None
        self.RFmxNR_ACPCfgPowerUnits_cfunc = None
        self.RFmxNR_PVTCfgAveraging_cfunc = None
        self.RFmxNR_PVTCfgMeasurementMethod_cfunc = None
        self.RFmxNR_PVTCfgOFFPowerExclusionPeriods_cfunc = None
        self.RFmxNR_OBWCfgAveraging_cfunc = None
        self.RFmxNR_OBWCfgRBWFilter_cfunc = None
        self.RFmxNR_OBWCfgSweepTime_cfunc = None
        self.RFmxNR_SEMCfgAveraging_cfunc = None
        self.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray_cfunc = None
        self.RFmxNR_SEMCfgComponentCarrierRatedOutputPower_cfunc = None
        self.RFmxNR_SEMCfgNumberOfOffsets_cfunc = None
        self.RFmxNR_SEMCfgOffsetAbsoluteLimitArray_cfunc = None
        self.RFmxNR_SEMCfgOffsetAbsoluteLimit_cfunc = None
        self.RFmxNR_SEMCfgOffsetBandwidthIntegralArray_cfunc = None
        self.RFmxNR_SEMCfgOffsetBandwidthIntegral_cfunc = None
        self.RFmxNR_SEMCfgOffsetFrequencyArray_cfunc = None
        self.RFmxNR_SEMCfgOffsetFrequency_cfunc = None
        self.RFmxNR_SEMCfgOffsetLimitFailMaskArray_cfunc = None
        self.RFmxNR_SEMCfgOffsetLimitFailMask_cfunc = None
        self.RFmxNR_SEMCfgOffsetRBWFilterArray_cfunc = None
        self.RFmxNR_SEMCfgOffsetRBWFilter_cfunc = None
        self.RFmxNR_SEMCfgOffsetRelativeLimitArray_cfunc = None
        self.RFmxNR_SEMCfgOffsetRelativeLimit_cfunc = None
        self.RFmxNR_SEMCfgSweepTime_cfunc = None
        self.RFmxNR_SEMCfgUplinkMaskType_cfunc = None
        self.RFmxNR_CHPCfgAveraging_cfunc = None
        self.RFmxNR_CHPCfgRBWFilter_cfunc = None
        self.RFmxNR_CHPCfgSweepTime_cfunc = None
        self.RFmxNR_CfgExternalAttenuation_cfunc = None
        self.RFmxNR_CfgFrequency_cfunc = None
        self.RFmxNR_CfggNodeBCategory_cfunc = None
        self.RFmxNR_CfgReferenceLevel_cfunc = None
        self.RFmxNR_CfgRF_cfunc = None
        self.RFmxNR_ModAccFetchCompositeEVM_cfunc = None
        self.RFmxNR_ModAccFetchFrequencyErrorMean_cfunc = None
        self.RFmxNR_ACPFetchComponentCarrierMeasurement_cfunc = None
        self.RFmxNR_ACPFetchOffsetMeasurement_cfunc = None
        self.RFmxNR_ACPFetchTotalAggregatedPower_cfunc = None
        self.RFmxNR_ACPFetchSubblockMeasurement_cfunc = None
        self.RFmxNR_TXPFetchMeasurement_cfunc = None
        self.RFmxNR_PVTFetchMeasurement_cfunc = None
        self.RFmxNR_OBWFetchMeasurement_cfunc = None
        self.RFmxNR_SEMFetchComponentCarrierMeasurement_cfunc = None
        self.RFmxNR_SEMFetchLowerOffsetMargin_cfunc = None
        self.RFmxNR_SEMFetchLowerOffsetPower_cfunc = None
        self.RFmxNR_SEMFetchMeasurementStatus_cfunc = None
        self.RFmxNR_SEMFetchTotalAggregatedPower_cfunc = None
        self.RFmxNR_SEMFetchUpperOffsetMargin_cfunc = None
        self.RFmxNR_SEMFetchUpperOffsetPower_cfunc = None
        self.RFmxNR_SEMFetchSubblockMeasurement_cfunc = None
        self.RFmxNR_CHPFetchComponentCarrierMeasurement_cfunc = None
        self.RFmxNR_CHPFetchSubblockPower_cfunc = None
        self.RFmxNR_CHPFetchTotalAggregatedPower_cfunc = None
        self.RFmxNR_ModAccFetchInBandEmissionTrace_cfunc = None
        self.RFmxNR_ModAccFetchPBCHDataConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCHDataConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCHDemodulatedBits_cfunc = None
        self.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace_cfunc = None
        self.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace_cfunc = None
        self.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace_cfunc = None
        self.RFmxNR_ModAccFetchPSSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPUSCHDataConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPUSCHDemodulatedBits_cfunc = None
        self.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace_cfunc = None
        self.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace_cfunc = None
        self.RFmxNR_ModAccFetchTransientPeriodLocationsTrace_cfunc = None
        self.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace_cfunc = None
        self.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace_cfunc = None
        self.RFmxNR_ModAccFetchSpectralFlatnessTrace_cfunc = None
        self.RFmxNR_ModAccFetchSSSConstellationTrace_cfunc = None
        self.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchSubblockInBandEmissionTrace_cfunc = None
        self.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc = None
        self.RFmxNR_ACPFetchAbsolutePowersTrace_cfunc = None
        self.RFmxNR_ACPFetchComponentCarrierMeasurementArray_cfunc = None
        self.RFmxNR_ACPFetchOffsetMeasurementArray_cfunc = None
        self.RFmxNR_ACPFetchRelativePowersTrace_cfunc = None
        self.RFmxNR_ACPFetchSpectrum_cfunc = None
        self.RFmxNR_TXPFetchPowerTrace_cfunc = None
        self.RFmxNR_PVTFetchMeasurementArray_cfunc = None
        self.RFmxNR_PVTFetchSignalPowerTrace_cfunc = None
        self.RFmxNR_PVTFetchWindowedSignalPowerTrace_cfunc = None
        self.RFmxNR_OBWFetchSpectrum_cfunc = None
        self.RFmxNR_SEMFetchComponentCarrierMeasurementArray_cfunc = None
        self.RFmxNR_SEMFetchLowerOffsetMarginArray_cfunc = None
        self.RFmxNR_SEMFetchLowerOffsetPowerArray_cfunc = None
        self.RFmxNR_SEMFetchSpectrum_cfunc = None
        self.RFmxNR_SEMFetchUpperOffsetMarginArray_cfunc = None
        self.RFmxNR_SEMFetchUpperOffsetPowerArray_cfunc = None
        self.RFmxNR_CHPFetchComponentCarrierMeasurementArray_cfunc = None
        self.RFmxNR_CHPFetchSpectrum_cfunc = None

    def _get_library_function(self, name: str) -> Any:
        try:
            function = getattr(self._library, name)
        except AttributeError as e:
            raise errors.DriverTooOldError() from e  # type: ignore
        return function

    def RFmxNR_ResetAttribute(self, vi, selector_string, attribute_id):
        """RFmxNR_ResetAttribute."""
        with self._func_lock:
            if self.RFmxNR_ResetAttribute_cfunc is None:
                self.RFmxNR_ResetAttribute_cfunc = self._get_library_function(
                    "RFmxNR_ResetAttribute"
                )
                self.RFmxNR_ResetAttribute_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ResetAttribute_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ResetAttribute_cfunc(vi, selector_string, attribute_id)

    def RFmxNR_GetError(self, vi, error_code, error_description_buffer_size, error_description):
        """RFmxNR_GetError."""
        with self._func_lock:
            if self.RFmxNR_GetError_cfunc is None:
                self.RFmxNR_GetError_cfunc = self._get_library_function("RFmxNR_GetError")
                self.RFmxNR_GetError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_GetError_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetError_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxNR_GetErrorString(
        self, vi, error_code, error_description_buffer_size, error_description
    ):
        """RFmxNR_GetErrorString."""
        with self._func_lock:
            if self.RFmxNR_GetErrorString_cfunc is None:
                self.RFmxNR_GetErrorString_cfunc = self._get_library_function(
                    "RFmxNR_GetErrorString"
                )
                self.RFmxNR_GetErrorString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_GetErrorString_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetErrorString_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxNR_GetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeI8."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI8_cfunc is None:
                self.RFmxNR_GetAttributeI8_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI8"
                )
                self.RFmxNR_GetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                ]
                self.RFmxNR_GetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeI8."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI8_cfunc is None:
                self.RFmxNR_SetAttributeI8_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI8"
                )
                self.RFmxNR_SetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int8,
                ]
                self.RFmxNR_SetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeI16."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI16_cfunc is None:
                self.RFmxNR_GetAttributeI16_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI16"
                )
                self.RFmxNR_GetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int16),
                ]
                self.RFmxNR_GetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeI16."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI16_cfunc is None:
                self.RFmxNR_SetAttributeI16_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI16"
                )
                self.RFmxNR_SetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int16,
                ]
                self.RFmxNR_SetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeI32."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI32_cfunc is None:
                self.RFmxNR_GetAttributeI32_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI32"
                )
                self.RFmxNR_GetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeI32."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI32_cfunc is None:
                self.RFmxNR_SetAttributeI32_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI32"
                )
                self.RFmxNR_SetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_SetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeI64."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI64_cfunc is None:
                self.RFmxNR_GetAttributeI64_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI64"
                )
                self.RFmxNR_GetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                ]
                self.RFmxNR_GetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeI64."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI64_cfunc is None:
                self.RFmxNR_SetAttributeI64_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI64"
                )
                self.RFmxNR_SetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int64,
                ]
                self.RFmxNR_SetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeU8."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeU8_cfunc is None:
                self.RFmxNR_GetAttributeU8_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeU8"
                )
                self.RFmxNR_GetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                ]
                self.RFmxNR_GetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeU8."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeU8_cfunc is None:
                self.RFmxNR_SetAttributeU8_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeU8"
                )
                self.RFmxNR_SetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint8,
                ]
                self.RFmxNR_SetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeU16."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeU16_cfunc is None:
                self.RFmxNR_GetAttributeU16_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeU16"
                )
                self.RFmxNR_GetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint16),
                ]
                self.RFmxNR_GetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeU16."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeU16_cfunc is None:
                self.RFmxNR_SetAttributeU16_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeU16"
                )
                self.RFmxNR_SetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint16,
                ]
                self.RFmxNR_SetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeU32."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeU32_cfunc is None:
                self.RFmxNR_GetAttributeU32_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeU32"
                )
                self.RFmxNR_GetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                ]
                self.RFmxNR_GetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeU32."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeU32_cfunc is None:
                self.RFmxNR_SetAttributeU32_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeU32"
                )
                self.RFmxNR_SetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeF32."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeF32_cfunc is None:
                self.RFmxNR_GetAttributeF32_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeF32"
                )
                self.RFmxNR_GetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                ]
                self.RFmxNR_GetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeF32."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeF32_cfunc is None:
                self.RFmxNR_SetAttributeF32_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeF32"
                )
                self.RFmxNR_SetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_float,
                ]
                self.RFmxNR_SetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_GetAttributeF64."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeF64_cfunc is None:
                self.RFmxNR_GetAttributeF64_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeF64"
                )
                self.RFmxNR_GetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_GetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_SetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeF64."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeF64_cfunc is None:
                self.RFmxNR_SetAttributeF64_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeF64"
                )
                self.RFmxNR_SetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_double,
                ]
                self.RFmxNR_SetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_GetAttributeI8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI8Array_cfunc is None:
                self.RFmxNR_GetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI8Array"
                )
                self.RFmxNR_GetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeI8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI8Array_cfunc is None:
                self.RFmxNR_SetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI8Array"
                )
                self.RFmxNR_SetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeI32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI32Array_cfunc is None:
                self.RFmxNR_GetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI32Array"
                )
                self.RFmxNR_GetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeI32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI32Array_cfunc is None:
                self.RFmxNR_SetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI32Array"
                )
                self.RFmxNR_SetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeI64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeI64Array_cfunc is None:
                self.RFmxNR_GetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeI64Array"
                )
                self.RFmxNR_GetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeI64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeI64Array_cfunc is None:
                self.RFmxNR_SetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeI64Array"
                )
                self.RFmxNR_SetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeU8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeU8Array_cfunc is None:
                self.RFmxNR_GetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeU8Array"
                )
                self.RFmxNR_GetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeU8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeU8Array_cfunc is None:
                self.RFmxNR_SetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeU8Array"
                )
                self.RFmxNR_SetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeU32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeU32Array_cfunc is None:
                self.RFmxNR_GetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeU32Array"
                )
                self.RFmxNR_GetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeU32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeU32Array_cfunc is None:
                self.RFmxNR_SetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeU32Array"
                )
                self.RFmxNR_SetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeU64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeU64Array_cfunc is None:
                self.RFmxNR_GetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeU64Array"
                )
                self.RFmxNR_GetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeU64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeU64Array_cfunc is None:
                self.RFmxNR_SetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeU64Array"
                )
                self.RFmxNR_SetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeF32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeF32Array_cfunc is None:
                self.RFmxNR_GetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeF32Array"
                )
                self.RFmxNR_GetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeF32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeF32Array_cfunc is None:
                self.RFmxNR_SetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeF32Array"
                )
                self.RFmxNR_SetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeF64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeF64Array_cfunc is None:
                self.RFmxNR_GetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeF64Array"
                )
                self.RFmxNR_GetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeF64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxNR_SetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeF64Array_cfunc is None:
                self.RFmxNR_SetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeF64Array"
                )
                self.RFmxNR_SetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxNR_GetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeNIComplexSingleArray"
                )
                self.RFmxNR_GetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxNR_SetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxNR_SetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeNIComplexSingleArray"
                )
                self.RFmxNR_SetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxNR_GetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxNR_GetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeNIComplexDoubleArray"
                )
                self.RFmxNR_GetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxNR_SetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxNR_SetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxNR_SetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeNIComplexDoubleArray"
                )
                self.RFmxNR_SetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxNR_SetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxNR_GetAttributeString(self, vi, selector_string, attribute_id, array_size, attr_val):
        """RFmxNR_GetAttributeString."""
        with self._func_lock:
            if self.RFmxNR_GetAttributeString_cfunc is None:
                self.RFmxNR_GetAttributeString_cfunc = self._get_library_function(
                    "RFmxNR_GetAttributeString"
                )
                self.RFmxNR_GetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_GetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAttributeString_cfunc(
            vi, selector_string, attribute_id, array_size, attr_val
        )

    def RFmxNR_SetAttributeString(self, vi, selector_string, attribute_id, attr_val):
        """RFmxNR_SetAttributeString."""
        with self._func_lock:
            if self.RFmxNR_SetAttributeString_cfunc is None:
                self.RFmxNR_SetAttributeString_cfunc = self._get_library_function(
                    "RFmxNR_SetAttributeString"
                )
                self.RFmxNR_SetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_SetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SetAttributeString_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxNR_ModAccCfgReferenceWaveform(
        self, vi, selector_string, x0, dx, reference_waveform, array_size
    ):
        """RFmxNR_ModAccCfgReferenceWaveform."""
        with self._func_lock:
            if self.RFmxNR_ModAccCfgReferenceWaveform_cfunc is None:
                self.RFmxNR_ModAccCfgReferenceWaveform_cfunc = self._get_library_function(
                    "RFmxNR_ModAccCfgReferenceWaveform"
                )
                self.RFmxNR_ModAccCfgReferenceWaveform_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ModAccCfgReferenceWaveform_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccCfgReferenceWaveform_cfunc(
            vi, selector_string, x0, dx, reference_waveform, array_size
        )

    def RFmxNR_ModAccAutoLevel(self, vi, selector_string, timeout):
        """RFmxNR_ModAccAutoLevel."""
        with self._func_lock:
            if self.RFmxNR_ModAccAutoLevel_cfunc is None:
                self.RFmxNR_ModAccAutoLevel_cfunc = self._get_library_function(
                    "RFmxNR_ModAccAutoLevel"
                )
                self.RFmxNR_ModAccAutoLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxNR_ModAccAutoLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccAutoLevel_cfunc(vi, selector_string, timeout)

    def RFmxNR_ModAccValidateCalibrationData(self, vi, selector_string, calibration_data_valid):
        """RFmxNR_ModAccValidateCalibrationData."""
        with self._func_lock:
            if self.RFmxNR_ModAccValidateCalibrationData_cfunc is None:
                self.RFmxNR_ModAccValidateCalibrationData_cfunc = self._get_library_function(
                    "RFmxNR_ModAccValidateCalibrationData"
                )
                self.RFmxNR_ModAccValidateCalibrationData_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccValidateCalibrationData_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccValidateCalibrationData_cfunc(
            vi, selector_string, calibration_data_valid
        )

    def RFmxNR_ModAccClearNoiseCalibrationDatabase(self, vi):
        """RFmxNR_ModAccClearNoiseCalibrationDatabase."""
        with self._func_lock:
            if self.RFmxNR_ModAccClearNoiseCalibrationDatabase_cfunc is None:
                self.RFmxNR_ModAccClearNoiseCalibrationDatabase_cfunc = self._get_library_function(
                    "RFmxNR_ModAccClearNoiseCalibrationDatabase"
                )
                self.RFmxNR_ModAccClearNoiseCalibrationDatabase_cfunc.argtypes = [ctypes.c_uint32]
                self.RFmxNR_ModAccClearNoiseCalibrationDatabase_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccClearNoiseCalibrationDatabase_cfunc(vi)

    def RFmxNR_ACPValidateNoiseCalibrationData(
        self, vi, selector_string, noise_calibration_data_valid
    ):
        """RFmxNR_ACPValidateNoiseCalibrationData."""
        with self._func_lock:
            if self.RFmxNR_ACPValidateNoiseCalibrationData_cfunc is None:
                self.RFmxNR_ACPValidateNoiseCalibrationData_cfunc = self._get_library_function(
                    "RFmxNR_ACPValidateNoiseCalibrationData"
                )
                self.RFmxNR_ACPValidateNoiseCalibrationData_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ACPValidateNoiseCalibrationData_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPValidateNoiseCalibrationData_cfunc(
            vi, selector_string, noise_calibration_data_valid
        )

    def RFmxNR_CHPValidateNoiseCalibrationData(
        self, vi, selector_string, noise_calibration_data_valid
    ):
        """RFmxNR_CHPValidateNoiseCalibrationData."""
        with self._func_lock:
            if self.RFmxNR_CHPValidateNoiseCalibrationData_cfunc is None:
                self.RFmxNR_CHPValidateNoiseCalibrationData_cfunc = self._get_library_function(
                    "RFmxNR_CHPValidateNoiseCalibrationData"
                )
                self.RFmxNR_CHPValidateNoiseCalibrationData_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_CHPValidateNoiseCalibrationData_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPValidateNoiseCalibrationData_cfunc(
            vi, selector_string, noise_calibration_data_valid
        )

    def RFmxNR_AbortMeasurements(self, vi, selector_string):
        """RFmxNR_AbortMeasurements."""
        with self._func_lock:
            if self.RFmxNR_AbortMeasurements_cfunc is None:
                self.RFmxNR_AbortMeasurements_cfunc = self._get_library_function(
                    "RFmxNR_AbortMeasurements"
                )
                self.RFmxNR_AbortMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_AbortMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_AbortMeasurements_cfunc(vi, selector_string)

    def RFmxNR_AutoLevel(self, vi, selector_string, measurement_interval, reference_level):
        """RFmxNR_AutoLevel."""
        with self._func_lock:
            if self.RFmxNR_AutoLevel_cfunc is None:
                self.RFmxNR_AutoLevel_cfunc = self._get_library_function("RFmxNR_AutoLevel")
                self.RFmxNR_AutoLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_AutoLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_AutoLevel_cfunc(
            vi, selector_string, measurement_interval, reference_level
        )

    def RFmxNR_CheckMeasurementStatus(self, vi, selector_string, is_done):
        """RFmxNR_CheckMeasurementStatus."""
        with self._func_lock:
            if self.RFmxNR_CheckMeasurementStatus_cfunc is None:
                self.RFmxNR_CheckMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxNR_CheckMeasurementStatus"
                )
                self.RFmxNR_CheckMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_CheckMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CheckMeasurementStatus_cfunc(vi, selector_string, is_done)

    def RFmxNR_ClearAllNamedResults(self, vi, selector_string):
        """RFmxNR_ClearAllNamedResults."""
        with self._func_lock:
            if self.RFmxNR_ClearAllNamedResults_cfunc is None:
                self.RFmxNR_ClearAllNamedResults_cfunc = self._get_library_function(
                    "RFmxNR_ClearAllNamedResults"
                )
                self.RFmxNR_ClearAllNamedResults_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_ClearAllNamedResults_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ClearAllNamedResults_cfunc(vi, selector_string)

    def RFmxNR_ClearNamedResult(self, vi, selector_string):
        """RFmxNR_ClearNamedResult."""
        with self._func_lock:
            if self.RFmxNR_ClearNamedResult_cfunc is None:
                self.RFmxNR_ClearNamedResult_cfunc = self._get_library_function(
                    "RFmxNR_ClearNamedResult"
                )
                self.RFmxNR_ClearNamedResult_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_ClearNamedResult_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ClearNamedResult_cfunc(vi, selector_string)

    def RFmxNR_ClearNoiseCalibrationDatabase(self, vi, selector_string):
        """RFmxNR_ClearNoiseCalibrationDatabase."""
        with self._func_lock:
            if self.RFmxNR_ClearNoiseCalibrationDatabase_cfunc is None:
                self.RFmxNR_ClearNoiseCalibrationDatabase_cfunc = self._get_library_function(
                    "RFmxNR_ClearNoiseCalibrationDatabase"
                )
                self.RFmxNR_ClearNoiseCalibrationDatabase_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_ClearNoiseCalibrationDatabase_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ClearNoiseCalibrationDatabase_cfunc(vi, selector_string)

    def RFmxNR_Commit(self, vi, selector_string):
        """RFmxNR_Commit."""
        with self._func_lock:
            if self.RFmxNR_Commit_cfunc is None:
                self.RFmxNR_Commit_cfunc = self._get_library_function("RFmxNR_Commit")
                self.RFmxNR_Commit_cfunc.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_char)]
                self.RFmxNR_Commit_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_Commit_cfunc(vi, selector_string)

    def RFmxNR_CfgDigitalEdgeTrigger(
        self, vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        """RFmxNR_CfgDigitalEdgeTrigger."""
        with self._func_lock:
            if self.RFmxNR_CfgDigitalEdgeTrigger_cfunc is None:
                self.RFmxNR_CfgDigitalEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxNR_CfgDigitalEdgeTrigger"
                )
                self.RFmxNR_CfgDigitalEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_CfgDigitalEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgDigitalEdgeTrigger_cfunc(
            vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
        )

    def RFmxNR_CfgIQPowerEdgeTrigger(
        self,
        vi,
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
        """RFmxNR_CfgIQPowerEdgeTrigger."""
        with self._func_lock:
            if self.RFmxNR_CfgIQPowerEdgeTrigger_cfunc is None:
                self.RFmxNR_CfgIQPowerEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxNR_CfgIQPowerEdgeTrigger"
                )
                self.RFmxNR_CfgIQPowerEdgeTrigger_cfunc.argtypes = [
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
                self.RFmxNR_CfgIQPowerEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgIQPowerEdgeTrigger_cfunc(
            vi,
            selector_string,
            iq_power_edge_trigger_source,
            iq_power_edge_trigger_slope,
            iq_power_edge_trigger_level,
            trigger_delay,
            trigger_minimum_quiet_time_mode,
            trigger_minimum_quiet_time_duration,
            iq_power_edge_trigger_level_type,
            enable_trigger,
        )

    def RFmxNR_CfgSelectedPortsMultiple(self, vi, selector_string, selected_ports):
        """RFmxNR_CfgSelectedPortsMultiple."""
        with self._func_lock:
            if self.RFmxNR_CfgSelectedPortsMultiple_cfunc is None:
                self.RFmxNR_CfgSelectedPortsMultiple_cfunc = self._get_library_function(
                    "RFmxNR_CfgSelectedPortsMultiple"
                )
                self.RFmxNR_CfgSelectedPortsMultiple_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_CfgSelectedPortsMultiple_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgSelectedPortsMultiple_cfunc(vi, selector_string, selected_ports)

    def RFmxNR_CfgSoftwareEdgeTrigger(self, vi, selector_string, trigger_delay, enable_trigger):
        """RFmxNR_CfgSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxNR_CfgSoftwareEdgeTrigger_cfunc is None:
                self.RFmxNR_CfgSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxNR_CfgSoftwareEdgeTrigger"
                )
                self.RFmxNR_CfgSoftwareEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_CfgSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgSoftwareEdgeTrigger_cfunc(
            vi, selector_string, trigger_delay, enable_trigger
        )

    def RFmxNR_CreateList(self, vi, list_name):
        """RFmxNR_CreateList."""
        with self._func_lock:
            if self.RFmxNR_CreateList_cfunc is None:
                self.RFmxNR_CreateList_cfunc = self._get_library_function("RFmxNR_CreateList")
                self.RFmxNR_CreateList_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_CreateList_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CreateList_cfunc(vi, list_name)

    def RFmxNR_CreateListStep(self, vi, selector_string, created_step_index):
        """RFmxNR_CreateListStep."""
        with self._func_lock:
            if self.RFmxNR_CreateListStep_cfunc is None:
                self.RFmxNR_CreateListStep_cfunc = self._get_library_function(
                    "RFmxNR_CreateListStep"
                )
                self.RFmxNR_CreateListStep_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_CreateListStep_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CreateListStep_cfunc(vi, selector_string, created_step_index)

    def RFmxNR_CreateSignalConfiguration(self, vi, signal_name):
        """RFmxNR_CreateSignalConfiguration."""
        with self._func_lock:
            if self.RFmxNR_CreateSignalConfiguration_cfunc is None:
                self.RFmxNR_CreateSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxNR_CreateSignalConfiguration"
                )
                self.RFmxNR_CreateSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_CreateSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CreateSignalConfiguration_cfunc(vi, signal_name)

    def RFmxNR_DeleteList(self, vi, list_name):
        """RFmxNR_DeleteList."""
        with self._func_lock:
            if self.RFmxNR_DeleteList_cfunc is None:
                self.RFmxNR_DeleteList_cfunc = self._get_library_function("RFmxNR_DeleteList")
                self.RFmxNR_DeleteList_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_DeleteList_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_DeleteList_cfunc(vi, list_name)

    def RFmxNR_DisableTrigger(self, vi, selector_string):
        """RFmxNR_DisableTrigger."""
        with self._func_lock:
            if self.RFmxNR_DisableTrigger_cfunc is None:
                self.RFmxNR_DisableTrigger_cfunc = self._get_library_function(
                    "RFmxNR_DisableTrigger"
                )
                self.RFmxNR_DisableTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_DisableTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_DisableTrigger_cfunc(vi, selector_string)

    def RFmxNR_Initiate(self, vi, selector_string, result_name):
        """RFmxNR_Initiate."""
        with self._func_lock:
            if self.RFmxNR_Initiate_cfunc is None:
                self.RFmxNR_Initiate_cfunc = self._get_library_function("RFmxNR_Initiate")
                self.RFmxNR_Initiate_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_Initiate_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_Initiate_cfunc(vi, selector_string, result_name)

    def RFmxNR_ResetToDefault(self, vi, selector_string):
        """RFmxNR_ResetToDefault."""
        with self._func_lock:
            if self.RFmxNR_ResetToDefault_cfunc is None:
                self.RFmxNR_ResetToDefault_cfunc = self._get_library_function(
                    "RFmxNR_ResetToDefault"
                )
                self.RFmxNR_ResetToDefault_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_ResetToDefault_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ResetToDefault_cfunc(vi, selector_string)

    def RFmxNR_SelectMeasurements(self, vi, selector_string, measurements, enable_all_traces):
        """RFmxNR_SelectMeasurements."""
        with self._func_lock:
            if self.RFmxNR_SelectMeasurements_cfunc is None:
                self.RFmxNR_SelectMeasurements_cfunc = self._get_library_function(
                    "RFmxNR_SelectMeasurements"
                )
                self.RFmxNR_SelectMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_SelectMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SelectMeasurements_cfunc(
            vi, selector_string, measurements, enable_all_traces
        )

    def RFmxNR_WaitForMeasurementComplete(self, vi, selector_string, timeout):
        """RFmxNR_WaitForMeasurementComplete."""
        with self._func_lock:
            if self.RFmxNR_WaitForMeasurementComplete_cfunc is None:
                self.RFmxNR_WaitForMeasurementComplete_cfunc = self._get_library_function(
                    "RFmxNR_WaitForMeasurementComplete"
                )
                self.RFmxNR_WaitForMeasurementComplete_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxNR_WaitForMeasurementComplete_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_WaitForMeasurementComplete_cfunc(vi, selector_string, timeout)

    def RFmxNR_LoadFromGenerationConfigurationFile(
        self, vi, selector_string, file_path, configuration_index
    ):
        """RFmxNR_LoadFromGenerationConfigurationFile."""
        with self._func_lock:
            if self.RFmxNR_LoadFromGenerationConfigurationFile_cfunc is None:
                self.RFmxNR_LoadFromGenerationConfigurationFile_cfunc = self._get_library_function(
                    "RFmxNR_LoadFromGenerationConfigurationFile"
                )
                self.RFmxNR_LoadFromGenerationConfigurationFile_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_LoadFromGenerationConfigurationFile_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_LoadFromGenerationConfigurationFile_cfunc(
            vi, selector_string, file_path, configuration_index
        )

    def RFmxNR_ModAccCfgMeasurementMode(self, vi, selector_string, measurement_mode):
        """RFmxNR_ModAccCfgMeasurementMode."""
        with self._func_lock:
            if self.RFmxNR_ModAccCfgMeasurementMode_cfunc is None:
                self.RFmxNR_ModAccCfgMeasurementMode_cfunc = self._get_library_function(
                    "RFmxNR_ModAccCfgMeasurementMode"
                )
                self.RFmxNR_ModAccCfgMeasurementMode_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ModAccCfgMeasurementMode_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccCfgMeasurementMode_cfunc(vi, selector_string, measurement_mode)

    def RFmxNR_ModAccCfgNoiseCompensationEnabled(
        self, vi, selector_string, noise_compensation_enabled
    ):
        """RFmxNR_ModAccCfgNoiseCompensationEnabled."""
        with self._func_lock:
            if self.RFmxNR_ModAccCfgNoiseCompensationEnabled_cfunc is None:
                self.RFmxNR_ModAccCfgNoiseCompensationEnabled_cfunc = self._get_library_function(
                    "RFmxNR_ModAccCfgNoiseCompensationEnabled"
                )
                self.RFmxNR_ModAccCfgNoiseCompensationEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ModAccCfgNoiseCompensationEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccCfgNoiseCompensationEnabled_cfunc(
            vi, selector_string, noise_compensation_enabled
        )

    def RFmxNR_ACPCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxNR_ACPCfgAveraging."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgAveraging_cfunc is None:
                self.RFmxNR_ACPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgAveraging"
                )
                self.RFmxNR_ACPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxNR_ACPCfgMeasurementMethod(self, vi, selector_string, measurement_method):
        """RFmxNR_ACPCfgMeasurementMethod."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgMeasurementMethod_cfunc is None:
                self.RFmxNR_ACPCfgMeasurementMethod_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgMeasurementMethod"
                )
                self.RFmxNR_ACPCfgMeasurementMethod_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgMeasurementMethod_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgMeasurementMethod_cfunc(vi, selector_string, measurement_method)

    def RFmxNR_ACPCfgNoiseCompensationEnabled(
        self, vi, selector_string, noise_compensation_enabled
    ):
        """RFmxNR_ACPCfgNoiseCompensationEnabled."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgNoiseCompensationEnabled_cfunc is None:
                self.RFmxNR_ACPCfgNoiseCompensationEnabled_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgNoiseCompensationEnabled"
                )
                self.RFmxNR_ACPCfgNoiseCompensationEnabled_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgNoiseCompensationEnabled_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgNoiseCompensationEnabled_cfunc(
            vi, selector_string, noise_compensation_enabled
        )

    def RFmxNR_ACPCfgNumberOfENDCOffsets(self, vi, selector_string, number_of_endc_offsets):
        """RFmxNR_ACPCfgNumberOfENDCOffsets."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgNumberOfENDCOffsets_cfunc is None:
                self.RFmxNR_ACPCfgNumberOfENDCOffsets_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgNumberOfENDCOffsets"
                )
                self.RFmxNR_ACPCfgNumberOfENDCOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgNumberOfENDCOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgNumberOfENDCOffsets_cfunc(
            vi, selector_string, number_of_endc_offsets
        )

    def RFmxNR_ACPCfgNumberOfEUTRAOffsets(self, vi, selector_string, number_of_eutra_offsets):
        """RFmxNR_ACPCfgNumberOfEUTRAOffsets."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgNumberOfEUTRAOffsets_cfunc is None:
                self.RFmxNR_ACPCfgNumberOfEUTRAOffsets_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgNumberOfEUTRAOffsets"
                )
                self.RFmxNR_ACPCfgNumberOfEUTRAOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgNumberOfEUTRAOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgNumberOfEUTRAOffsets_cfunc(
            vi, selector_string, number_of_eutra_offsets
        )

    def RFmxNR_ACPCfgNumberOfNROffsets(self, vi, selector_string, number_of_nr_offsets):
        """RFmxNR_ACPCfgNumberOfNROffsets."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgNumberOfNROffsets_cfunc is None:
                self.RFmxNR_ACPCfgNumberOfNROffsets_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgNumberOfNROffsets"
                )
                self.RFmxNR_ACPCfgNumberOfNROffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgNumberOfNROffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgNumberOfNROffsets_cfunc(vi, selector_string, number_of_nr_offsets)

    def RFmxNR_ACPCfgNumberOfUTRAOffsets(self, vi, selector_string, number_of_utra_offsets):
        """RFmxNR_ACPCfgNumberOfUTRAOffsets."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgNumberOfUTRAOffsets_cfunc is None:
                self.RFmxNR_ACPCfgNumberOfUTRAOffsets_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgNumberOfUTRAOffsets"
                )
                self.RFmxNR_ACPCfgNumberOfUTRAOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgNumberOfUTRAOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgNumberOfUTRAOffsets_cfunc(
            vi, selector_string, number_of_utra_offsets
        )

    def RFmxNR_ACPCfgRBWFilter(self, vi, selector_string, rbw_auto, rbw, rbw_filter_type):
        """RFmxNR_ACPCfgRBWFilter."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgRBWFilter_cfunc is None:
                self.RFmxNR_ACPCfgRBWFilter_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgRBWFilter"
                )
                self.RFmxNR_ACPCfgRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgRBWFilter_cfunc(
            vi, selector_string, rbw_auto, rbw, rbw_filter_type
        )

    def RFmxNR_ACPCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxNR_ACPCfgSweepTime."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgSweepTime_cfunc is None:
                self.RFmxNR_ACPCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgSweepTime"
                )
                self.RFmxNR_ACPCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxNR_ACPCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxNR_ACPCfgPowerUnits(self, vi, selector_string, power_units):
        """RFmxNR_ACPCfgPowerUnits."""
        with self._func_lock:
            if self.RFmxNR_ACPCfgPowerUnits_cfunc is None:
                self.RFmxNR_ACPCfgPowerUnits_cfunc = self._get_library_function(
                    "RFmxNR_ACPCfgPowerUnits"
                )
                self.RFmxNR_ACPCfgPowerUnits_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_ACPCfgPowerUnits_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPCfgPowerUnits_cfunc(vi, selector_string, power_units)

    def RFmxNR_PVTCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxNR_PVTCfgAveraging."""
        with self._func_lock:
            if self.RFmxNR_PVTCfgAveraging_cfunc is None:
                self.RFmxNR_PVTCfgAveraging_cfunc = self._get_library_function(
                    "RFmxNR_PVTCfgAveraging"
                )
                self.RFmxNR_PVTCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_PVTCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxNR_PVTCfgMeasurementMethod(self, vi, selector_string, measurement_method):
        """RFmxNR_PVTCfgMeasurementMethod."""
        with self._func_lock:
            if self.RFmxNR_PVTCfgMeasurementMethod_cfunc is None:
                self.RFmxNR_PVTCfgMeasurementMethod_cfunc = self._get_library_function(
                    "RFmxNR_PVTCfgMeasurementMethod"
                )
                self.RFmxNR_PVTCfgMeasurementMethod_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_PVTCfgMeasurementMethod_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTCfgMeasurementMethod_cfunc(vi, selector_string, measurement_method)

    def RFmxNR_PVTCfgOFFPowerExclusionPeriods(
        self, vi, selector_string, off_power_exclusion_before, off_power_exclusion_after
    ):
        """RFmxNR_PVTCfgOFFPowerExclusionPeriods."""
        with self._func_lock:
            if self.RFmxNR_PVTCfgOFFPowerExclusionPeriods_cfunc is None:
                self.RFmxNR_PVTCfgOFFPowerExclusionPeriods_cfunc = self._get_library_function(
                    "RFmxNR_PVTCfgOFFPowerExclusionPeriods"
                )
                self.RFmxNR_PVTCfgOFFPowerExclusionPeriods_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxNR_PVTCfgOFFPowerExclusionPeriods_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTCfgOFFPowerExclusionPeriods_cfunc(
            vi, selector_string, off_power_exclusion_before, off_power_exclusion_after
        )

    def RFmxNR_OBWCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxNR_OBWCfgAveraging."""
        with self._func_lock:
            if self.RFmxNR_OBWCfgAveraging_cfunc is None:
                self.RFmxNR_OBWCfgAveraging_cfunc = self._get_library_function(
                    "RFmxNR_OBWCfgAveraging"
                )
                self.RFmxNR_OBWCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_OBWCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_OBWCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxNR_OBWCfgRBWFilter(self, vi, selector_string, rbw_auto, rbw, rbw_filter_type):
        """RFmxNR_OBWCfgRBWFilter."""
        with self._func_lock:
            if self.RFmxNR_OBWCfgRBWFilter_cfunc is None:
                self.RFmxNR_OBWCfgRBWFilter_cfunc = self._get_library_function(
                    "RFmxNR_OBWCfgRBWFilter"
                )
                self.RFmxNR_OBWCfgRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_OBWCfgRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_OBWCfgRBWFilter_cfunc(
            vi, selector_string, rbw_auto, rbw, rbw_filter_type
        )

    def RFmxNR_OBWCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxNR_OBWCfgSweepTime."""
        with self._func_lock:
            if self.RFmxNR_OBWCfgSweepTime_cfunc is None:
                self.RFmxNR_OBWCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxNR_OBWCfgSweepTime"
                )
                self.RFmxNR_OBWCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxNR_OBWCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_OBWCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxNR_SEMCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxNR_SEMCfgAveraging."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgAveraging_cfunc is None:
                self.RFmxNR_SEMCfgAveraging_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgAveraging"
                )
                self.RFmxNR_SEMCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray(
        self, vi, selector_string, component_carrier_rated_output_power, number_of_elements
    ):
        """RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray_cfunc is None:
                self.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray_cfunc = (
                    self._get_library_function("RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray")
                )
                self.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray_cfunc(
            vi, selector_string, component_carrier_rated_output_power, number_of_elements
        )

    def RFmxNR_SEMCfgComponentCarrierRatedOutputPower(
        self, vi, selector_string, component_carrier_rated_output_power
    ):
        """RFmxNR_SEMCfgComponentCarrierRatedOutputPower."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgComponentCarrierRatedOutputPower_cfunc is None:
                self.RFmxNR_SEMCfgComponentCarrierRatedOutputPower_cfunc = (
                    self._get_library_function("RFmxNR_SEMCfgComponentCarrierRatedOutputPower")
                )
                self.RFmxNR_SEMCfgComponentCarrierRatedOutputPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxNR_SEMCfgComponentCarrierRatedOutputPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgComponentCarrierRatedOutputPower_cfunc(
            vi, selector_string, component_carrier_rated_output_power
        )

    def RFmxNR_SEMCfgNumberOfOffsets(self, vi, selector_string, number_of_offsets):
        """RFmxNR_SEMCfgNumberOfOffsets."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgNumberOfOffsets_cfunc is None:
                self.RFmxNR_SEMCfgNumberOfOffsets_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgNumberOfOffsets"
                )
                self.RFmxNR_SEMCfgNumberOfOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgNumberOfOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgNumberOfOffsets_cfunc(vi, selector_string, number_of_offsets)

    def RFmxNR_SEMCfgOffsetAbsoluteLimitArray(
        self, vi, selector_string, absolute_limit_start, absolute_limit_stop, number_of_elements
    ):
        """RFmxNR_SEMCfgOffsetAbsoluteLimitArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetAbsoluteLimitArray_cfunc is None:
                self.RFmxNR_SEMCfgOffsetAbsoluteLimitArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetAbsoluteLimitArray"
                )
                self.RFmxNR_SEMCfgOffsetAbsoluteLimitArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetAbsoluteLimitArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetAbsoluteLimitArray_cfunc(
            vi, selector_string, absolute_limit_start, absolute_limit_stop, number_of_elements
        )

    def RFmxNR_SEMCfgOffsetAbsoluteLimit(
        self, vi, selector_string, absolute_limit_start, absolute_limit_stop
    ):
        """RFmxNR_SEMCfgOffsetAbsoluteLimit."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetAbsoluteLimit_cfunc is None:
                self.RFmxNR_SEMCfgOffsetAbsoluteLimit_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetAbsoluteLimit"
                )
                self.RFmxNR_SEMCfgOffsetAbsoluteLimit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxNR_SEMCfgOffsetAbsoluteLimit_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetAbsoluteLimit_cfunc(
            vi, selector_string, absolute_limit_start, absolute_limit_stop
        )

    def RFmxNR_SEMCfgOffsetBandwidthIntegralArray(
        self, vi, selector_string, bandwidth_integral, number_of_elements
    ):
        """RFmxNR_SEMCfgOffsetBandwidthIntegralArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetBandwidthIntegralArray_cfunc is None:
                self.RFmxNR_SEMCfgOffsetBandwidthIntegralArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetBandwidthIntegralArray"
                )
                self.RFmxNR_SEMCfgOffsetBandwidthIntegralArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetBandwidthIntegralArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetBandwidthIntegralArray_cfunc(
            vi, selector_string, bandwidth_integral, number_of_elements
        )

    def RFmxNR_SEMCfgOffsetBandwidthIntegral(self, vi, selector_string, bandwidth_integral):
        """RFmxNR_SEMCfgOffsetBandwidthIntegral."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetBandwidthIntegral_cfunc is None:
                self.RFmxNR_SEMCfgOffsetBandwidthIntegral_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetBandwidthIntegral"
                )
                self.RFmxNR_SEMCfgOffsetBandwidthIntegral_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetBandwidthIntegral_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetBandwidthIntegral_cfunc(
            vi, selector_string, bandwidth_integral
        )

    def RFmxNR_SEMCfgOffsetFrequencyArray(
        self,
        vi,
        selector_string,
        offset_start_frequency,
        offset_stop_frequency,
        offset_sideband,
        number_of_elements,
    ):
        """RFmxNR_SEMCfgOffsetFrequencyArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetFrequencyArray_cfunc is None:
                self.RFmxNR_SEMCfgOffsetFrequencyArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetFrequencyArray"
                )
                self.RFmxNR_SEMCfgOffsetFrequencyArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetFrequencyArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetFrequencyArray_cfunc(
            vi,
            selector_string,
            offset_start_frequency,
            offset_stop_frequency,
            offset_sideband,
            number_of_elements,
        )

    def RFmxNR_SEMCfgOffsetFrequency(
        self, vi, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        """RFmxNR_SEMCfgOffsetFrequency."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetFrequency_cfunc is None:
                self.RFmxNR_SEMCfgOffsetFrequency_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetFrequency"
                )
                self.RFmxNR_SEMCfgOffsetFrequency_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetFrequency_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetFrequency_cfunc(
            vi, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
        )

    def RFmxNR_SEMCfgOffsetLimitFailMaskArray(
        self, vi, selector_string, limit_fail_mask, number_of_elements
    ):
        """RFmxNR_SEMCfgOffsetLimitFailMaskArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetLimitFailMaskArray_cfunc is None:
                self.RFmxNR_SEMCfgOffsetLimitFailMaskArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetLimitFailMaskArray"
                )
                self.RFmxNR_SEMCfgOffsetLimitFailMaskArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetLimitFailMaskArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetLimitFailMaskArray_cfunc(
            vi, selector_string, limit_fail_mask, number_of_elements
        )

    def RFmxNR_SEMCfgOffsetLimitFailMask(self, vi, selector_string, limit_fail_mask):
        """RFmxNR_SEMCfgOffsetLimitFailMask."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetLimitFailMask_cfunc is None:
                self.RFmxNR_SEMCfgOffsetLimitFailMask_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetLimitFailMask"
                )
                self.RFmxNR_SEMCfgOffsetLimitFailMask_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetLimitFailMask_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetLimitFailMask_cfunc(vi, selector_string, limit_fail_mask)

    def RFmxNR_SEMCfgOffsetRBWFilterArray(
        self, vi, selector_string, offset_rbw, offset_rbw_filter_type, number_of_elements
    ):
        """RFmxNR_SEMCfgOffsetRBWFilterArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetRBWFilterArray_cfunc is None:
                self.RFmxNR_SEMCfgOffsetRBWFilterArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetRBWFilterArray"
                )
                self.RFmxNR_SEMCfgOffsetRBWFilterArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetRBWFilterArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetRBWFilterArray_cfunc(
            vi, selector_string, offset_rbw, offset_rbw_filter_type, number_of_elements
        )

    def RFmxNR_SEMCfgOffsetRBWFilter(self, vi, selector_string, offset_rbw, offset_rbw_filter_type):
        """RFmxNR_SEMCfgOffsetRBWFilter."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetRBWFilter_cfunc is None:
                self.RFmxNR_SEMCfgOffsetRBWFilter_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetRBWFilter"
                )
                self.RFmxNR_SEMCfgOffsetRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetRBWFilter_cfunc(
            vi, selector_string, offset_rbw, offset_rbw_filter_type
        )

    def RFmxNR_SEMCfgOffsetRelativeLimitArray(
        self, vi, selector_string, relative_limit_start, relative_limit_stop, number_of_elements
    ):
        """RFmxNR_SEMCfgOffsetRelativeLimitArray."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetRelativeLimitArray_cfunc is None:
                self.RFmxNR_SEMCfgOffsetRelativeLimitArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetRelativeLimitArray"
                )
                self.RFmxNR_SEMCfgOffsetRelativeLimitArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgOffsetRelativeLimitArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetRelativeLimitArray_cfunc(
            vi, selector_string, relative_limit_start, relative_limit_stop, number_of_elements
        )

    def RFmxNR_SEMCfgOffsetRelativeLimit(
        self, vi, selector_string, relative_limit_start, relative_limit_stop
    ):
        """RFmxNR_SEMCfgOffsetRelativeLimit."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgOffsetRelativeLimit_cfunc is None:
                self.RFmxNR_SEMCfgOffsetRelativeLimit_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgOffsetRelativeLimit"
                )
                self.RFmxNR_SEMCfgOffsetRelativeLimit_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxNR_SEMCfgOffsetRelativeLimit_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgOffsetRelativeLimit_cfunc(
            vi, selector_string, relative_limit_start, relative_limit_stop
        )

    def RFmxNR_SEMCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxNR_SEMCfgSweepTime."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgSweepTime_cfunc is None:
                self.RFmxNR_SEMCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgSweepTime"
                )
                self.RFmxNR_SEMCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxNR_SEMCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxNR_SEMCfgUplinkMaskType(self, vi, selector_string, uplink_mask_type):
        """RFmxNR_SEMCfgUplinkMaskType."""
        with self._func_lock:
            if self.RFmxNR_SEMCfgUplinkMaskType_cfunc is None:
                self.RFmxNR_SEMCfgUplinkMaskType_cfunc = self._get_library_function(
                    "RFmxNR_SEMCfgUplinkMaskType"
                )
                self.RFmxNR_SEMCfgUplinkMaskType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_SEMCfgUplinkMaskType_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMCfgUplinkMaskType_cfunc(vi, selector_string, uplink_mask_type)

    def RFmxNR_CHPCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """RFmxNR_CHPCfgAveraging."""
        with self._func_lock:
            if self.RFmxNR_CHPCfgAveraging_cfunc is None:
                self.RFmxNR_CHPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxNR_CHPCfgAveraging"
                )
                self.RFmxNR_CHPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxNR_CHPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count, averaging_type
        )

    def RFmxNR_CHPCfgRBWFilter(self, vi, selector_string, rbw_auto, rbw, rbw_filter_type):
        """RFmxNR_CHPCfgRBWFilter."""
        with self._func_lock:
            if self.RFmxNR_CHPCfgRBWFilter_cfunc is None:
                self.RFmxNR_CHPCfgRBWFilter_cfunc = self._get_library_function(
                    "RFmxNR_CHPCfgRBWFilter"
                )
                self.RFmxNR_CHPCfgRBWFilter_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxNR_CHPCfgRBWFilter_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPCfgRBWFilter_cfunc(
            vi, selector_string, rbw_auto, rbw, rbw_filter_type
        )

    def RFmxNR_CHPCfgSweepTime(self, vi, selector_string, sweep_time_auto, sweep_time_interval):
        """RFmxNR_CHPCfgSweepTime."""
        with self._func_lock:
            if self.RFmxNR_CHPCfgSweepTime_cfunc is None:
                self.RFmxNR_CHPCfgSweepTime_cfunc = self._get_library_function(
                    "RFmxNR_CHPCfgSweepTime"
                )
                self.RFmxNR_CHPCfgSweepTime_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                ]
                self.RFmxNR_CHPCfgSweepTime_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPCfgSweepTime_cfunc(
            vi, selector_string, sweep_time_auto, sweep_time_interval
        )

    def RFmxNR_CfgExternalAttenuation(self, vi, selector_string, external_attenuation):
        """RFmxNR_CfgExternalAttenuation."""
        with self._func_lock:
            if self.RFmxNR_CfgExternalAttenuation_cfunc is None:
                self.RFmxNR_CfgExternalAttenuation_cfunc = self._get_library_function(
                    "RFmxNR_CfgExternalAttenuation"
                )
                self.RFmxNR_CfgExternalAttenuation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxNR_CfgExternalAttenuation_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgExternalAttenuation_cfunc(vi, selector_string, external_attenuation)

    def RFmxNR_CfgFrequency(self, vi, selector_string, center_frequency):
        """RFmxNR_CfgFrequency."""
        with self._func_lock:
            if self.RFmxNR_CfgFrequency_cfunc is None:
                self.RFmxNR_CfgFrequency_cfunc = self._get_library_function("RFmxNR_CfgFrequency")
                self.RFmxNR_CfgFrequency_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxNR_CfgFrequency_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgFrequency_cfunc(vi, selector_string, center_frequency)

    def RFmxNR_CfggNodeBCategory(self, vi, selector_string, gnodeb_category):
        """RFmxNR_CfggNodeBCategory."""
        with self._func_lock:
            if self.RFmxNR_CfggNodeBCategory_cfunc is None:
                self.RFmxNR_CfggNodeBCategory_cfunc = self._get_library_function(
                    "RFmxNR_CfggNodeBCategory"
                )
                self.RFmxNR_CfggNodeBCategory_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxNR_CfggNodeBCategory_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfggNodeBCategory_cfunc(vi, selector_string, gnodeb_category)

    def RFmxNR_CfgReferenceLevel(self, vi, selector_string, reference_level):
        """RFmxNR_CfgReferenceLevel."""
        with self._func_lock:
            if self.RFmxNR_CfgReferenceLevel_cfunc is None:
                self.RFmxNR_CfgReferenceLevel_cfunc = self._get_library_function(
                    "RFmxNR_CfgReferenceLevel"
                )
                self.RFmxNR_CfgReferenceLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxNR_CfgReferenceLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgReferenceLevel_cfunc(vi, selector_string, reference_level)

    def RFmxNR_CfgRF(
        self, vi, selector_string, center_frequency, reference_level, external_attenuation
    ):
        """RFmxNR_CfgRF."""
        with self._func_lock:
            if self.RFmxNR_CfgRF_cfunc is None:
                self.RFmxNR_CfgRF_cfunc = self._get_library_function("RFmxNR_CfgRF")
                self.RFmxNR_CfgRF_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxNR_CfgRF_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CfgRF_cfunc(
            vi, selector_string, center_frequency, reference_level, external_attenuation
        )

    def RFmxNR_ModAccFetchCompositeEVM(
        self, vi, selector_string, timeout, composite_rms_evm_mean, composite_peak_evm_maximum
    ):
        """RFmxNR_ModAccFetchCompositeEVM."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchCompositeEVM_cfunc is None:
                self.RFmxNR_ModAccFetchCompositeEVM_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchCompositeEVM"
                )
                self.RFmxNR_ModAccFetchCompositeEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_ModAccFetchCompositeEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchCompositeEVM_cfunc(
            vi, selector_string, timeout, composite_rms_evm_mean, composite_peak_evm_maximum
        )

    def RFmxNR_ModAccFetchFrequencyErrorMean(
        self, vi, selector_string, timeout, frequency_error_mean
    ):
        """RFmxNR_ModAccFetchFrequencyErrorMean."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchFrequencyErrorMean_cfunc is None:
                self.RFmxNR_ModAccFetchFrequencyErrorMean_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchFrequencyErrorMean"
                )
                self.RFmxNR_ModAccFetchFrequencyErrorMean_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_ModAccFetchFrequencyErrorMean_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchFrequencyErrorMean_cfunc(
            vi, selector_string, timeout, frequency_error_mean
        )

    def RFmxNR_ACPFetchComponentCarrierMeasurement(
        self, vi, selector_string, timeout, absolute_power, relative_power
    ):
        """RFmxNR_ACPFetchComponentCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchComponentCarrierMeasurement_cfunc is None:
                self.RFmxNR_ACPFetchComponentCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchComponentCarrierMeasurement"
                )
                self.RFmxNR_ACPFetchComponentCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_ACPFetchComponentCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchComponentCarrierMeasurement_cfunc(
            vi, selector_string, timeout, absolute_power, relative_power
        )

    def RFmxNR_ACPFetchOffsetMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        lower_relative_power,
        upper_relative_power,
        lower_absolute_power,
        upper_absolute_power,
    ):
        """RFmxNR_ACPFetchOffsetMeasurement."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchOffsetMeasurement_cfunc is None:
                self.RFmxNR_ACPFetchOffsetMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchOffsetMeasurement"
                )
                self.RFmxNR_ACPFetchOffsetMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_ACPFetchOffsetMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchOffsetMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            lower_relative_power,
            upper_relative_power,
            lower_absolute_power,
            upper_absolute_power,
        )

    def RFmxNR_ACPFetchTotalAggregatedPower(
        self, vi, selector_string, timeout, total_aggregated_power
    ):
        """RFmxNR_ACPFetchTotalAggregatedPower."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchTotalAggregatedPower_cfunc is None:
                self.RFmxNR_ACPFetchTotalAggregatedPower_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchTotalAggregatedPower"
                )
                self.RFmxNR_ACPFetchTotalAggregatedPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_ACPFetchTotalAggregatedPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchTotalAggregatedPower_cfunc(
            vi, selector_string, timeout, total_aggregated_power
        )

    def RFmxNR_ACPFetchSubblockMeasurement(
        self, vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
    ):
        """RFmxNR_ACPFetchSubblockMeasurement."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchSubblockMeasurement_cfunc is None:
                self.RFmxNR_ACPFetchSubblockMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchSubblockMeasurement"
                )
                self.RFmxNR_ACPFetchSubblockMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_ACPFetchSubblockMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchSubblockMeasurement_cfunc(
            vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
        )

    def RFmxNR_TXPFetchMeasurement(
        self, vi, selector_string, timeout, average_power_mean, peak_power_maximum
    ):
        """RFmxNR_TXPFetchMeasurement."""
        with self._func_lock:
            if self.RFmxNR_TXPFetchMeasurement_cfunc is None:
                self.RFmxNR_TXPFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_TXPFetchMeasurement"
                )
                self.RFmxNR_TXPFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_TXPFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_TXPFetchMeasurement_cfunc(
            vi, selector_string, timeout, average_power_mean, peak_power_maximum
        )

    def RFmxNR_PVTFetchMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        absolute_off_power_before,
        absolute_off_power_after,
        absolute_on_power,
        burst_width,
    ):
        """RFmxNR_PVTFetchMeasurement."""
        with self._func_lock:
            if self.RFmxNR_PVTFetchMeasurement_cfunc is None:
                self.RFmxNR_PVTFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_PVTFetchMeasurement"
                )
                self.RFmxNR_PVTFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_PVTFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTFetchMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            absolute_off_power_before,
            absolute_off_power_after,
            absolute_on_power,
            burst_width,
        )

    def RFmxNR_OBWFetchMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        occupied_bandwidth,
        absolute_power,
        start_frequency,
        stop_frequency,
    ):
        """RFmxNR_OBWFetchMeasurement."""
        with self._func_lock:
            if self.RFmxNR_OBWFetchMeasurement_cfunc is None:
                self.RFmxNR_OBWFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_OBWFetchMeasurement"
                )
                self.RFmxNR_OBWFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_OBWFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_OBWFetchMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            occupied_bandwidth,
            absolute_power,
            start_frequency,
            stop_frequency,
        )

    def RFmxNR_SEMFetchComponentCarrierMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        absolute_power,
        peak_absolute_power,
        peak_frequency,
        relative_power,
    ):
        """RFmxNR_SEMFetchComponentCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchComponentCarrierMeasurement_cfunc is None:
                self.RFmxNR_SEMFetchComponentCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchComponentCarrierMeasurement"
                )
                self.RFmxNR_SEMFetchComponentCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchComponentCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchComponentCarrierMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_power,
            peak_absolute_power,
            peak_frequency,
            relative_power,
        )

    def RFmxNR_SEMFetchLowerOffsetMargin(
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
        """RFmxNR_SEMFetchLowerOffsetMargin."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchLowerOffsetMargin_cfunc is None:
                self.RFmxNR_SEMFetchLowerOffsetMargin_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchLowerOffsetMargin"
                )
                self.RFmxNR_SEMFetchLowerOffsetMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchLowerOffsetMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchLowerOffsetMargin_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
        )

    def RFmxNR_SEMFetchLowerOffsetPower(
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
        """RFmxNR_SEMFetchLowerOffsetPower."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchLowerOffsetPower_cfunc is None:
                self.RFmxNR_SEMFetchLowerOffsetPower_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchLowerOffsetPower"
                )
                self.RFmxNR_SEMFetchLowerOffsetPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchLowerOffsetPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchLowerOffsetPower_cfunc(
            vi,
            selector_string,
            timeout,
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
        )

    def RFmxNR_SEMFetchMeasurementStatus(self, vi, selector_string, timeout, measurement_status):
        """RFmxNR_SEMFetchMeasurementStatus."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchMeasurementStatus_cfunc is None:
                self.RFmxNR_SEMFetchMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchMeasurementStatus"
                )
                self.RFmxNR_SEMFetchMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_SEMFetchMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchMeasurementStatus_cfunc(
            vi, selector_string, timeout, measurement_status
        )

    def RFmxNR_SEMFetchTotalAggregatedPower(
        self, vi, selector_string, timeout, total_aggregated_power
    ):
        """RFmxNR_SEMFetchTotalAggregatedPower."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchTotalAggregatedPower_cfunc is None:
                self.RFmxNR_SEMFetchTotalAggregatedPower_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchTotalAggregatedPower"
                )
                self.RFmxNR_SEMFetchTotalAggregatedPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchTotalAggregatedPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchTotalAggregatedPower_cfunc(
            vi, selector_string, timeout, total_aggregated_power
        )

    def RFmxNR_SEMFetchUpperOffsetMargin(
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
        """RFmxNR_SEMFetchUpperOffsetMargin."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchUpperOffsetMargin_cfunc is None:
                self.RFmxNR_SEMFetchUpperOffsetMargin_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchUpperOffsetMargin"
                )
                self.RFmxNR_SEMFetchUpperOffsetMargin_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchUpperOffsetMargin_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchUpperOffsetMargin_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
        )

    def RFmxNR_SEMFetchUpperOffsetPower(
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
        """RFmxNR_SEMFetchUpperOffsetPower."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchUpperOffsetPower_cfunc is None:
                self.RFmxNR_SEMFetchUpperOffsetPower_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchUpperOffsetPower"
                )
                self.RFmxNR_SEMFetchUpperOffsetPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchUpperOffsetPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchUpperOffsetPower_cfunc(
            vi,
            selector_string,
            timeout,
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
        )

    def RFmxNR_SEMFetchSubblockMeasurement(
        self, vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
    ):
        """RFmxNR_SEMFetchSubblockMeasurement."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchSubblockMeasurement_cfunc is None:
                self.RFmxNR_SEMFetchSubblockMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchSubblockMeasurement"
                )
                self.RFmxNR_SEMFetchSubblockMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_SEMFetchSubblockMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchSubblockMeasurement_cfunc(
            vi, selector_string, timeout, subblock_power, integration_bandwidth, frequency
        )

    def RFmxNR_CHPFetchComponentCarrierMeasurement(
        self, vi, selector_string, timeout, absolute_power, relative_power
    ):
        """RFmxNR_CHPFetchComponentCarrierMeasurement."""
        with self._func_lock:
            if self.RFmxNR_CHPFetchComponentCarrierMeasurement_cfunc is None:
                self.RFmxNR_CHPFetchComponentCarrierMeasurement_cfunc = self._get_library_function(
                    "RFmxNR_CHPFetchComponentCarrierMeasurement"
                )
                self.RFmxNR_CHPFetchComponentCarrierMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_CHPFetchComponentCarrierMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPFetchComponentCarrierMeasurement_cfunc(
            vi, selector_string, timeout, absolute_power, relative_power
        )

    def RFmxNR_CHPFetchSubblockPower(self, vi, selector_string, timeout, subblock_power):
        """RFmxNR_CHPFetchSubblockPower."""
        with self._func_lock:
            if self.RFmxNR_CHPFetchSubblockPower_cfunc is None:
                self.RFmxNR_CHPFetchSubblockPower_cfunc = self._get_library_function(
                    "RFmxNR_CHPFetchSubblockPower"
                )
                self.RFmxNR_CHPFetchSubblockPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_CHPFetchSubblockPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPFetchSubblockPower_cfunc(vi, selector_string, timeout, subblock_power)

    def RFmxNR_CHPFetchTotalAggregatedPower(
        self, vi, selector_string, timeout, total_aggregated_power
    ):
        """RFmxNR_CHPFetchTotalAggregatedPower."""
        with self._func_lock:
            if self.RFmxNR_CHPFetchTotalAggregatedPower_cfunc is None:
                self.RFmxNR_CHPFetchTotalAggregatedPower_cfunc = self._get_library_function(
                    "RFmxNR_CHPFetchTotalAggregatedPower"
                )
                self.RFmxNR_CHPFetchTotalAggregatedPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxNR_CHPFetchTotalAggregatedPower_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPFetchTotalAggregatedPower_cfunc(
            vi, selector_string, timeout, total_aggregated_power
        )

    def RFmxNR_ModAccFetchInBandEmissionTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        in_band_emission,
        in_band_emission_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchInBandEmissionTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchInBandEmissionTrace_cfunc is None:
                self.RFmxNR_ModAccFetchInBandEmissionTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchInBandEmissionTrace"
                )
                self.RFmxNR_ModAccFetchInBandEmissionTrace_cfunc.argtypes = [
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
                self.RFmxNR_ModAccFetchInBandEmissionTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchInBandEmissionTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            in_band_emission,
            in_band_emission_mask,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPBCHDataConstellationTrace(
        self, vi, selector_string, timeout, pbch_data_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPBCHDataConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPBCHDataConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPBCHDataConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPBCHDataConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPBCHDataConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPBCHDataConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPBCHDataConstellationTrace_cfunc(
            vi, selector_string, timeout, pbch_data_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pbch_data_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            pbch_data_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pbch_data_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace")
                )
                self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            pbch_data_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPBCHDMRSConstellationTrace(
        self, vi, selector_string, timeout, pbch_dmrs_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPBCHDMRSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPBCHDMRSConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace_cfunc(
            vi, selector_string, timeout, pbch_dmrs_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pbch_dmrs_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            pbch_dmrs_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pbch_dmrs_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace")
                )
                self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            pbch_dmrs_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace(
        self, vi, selector_string, timeout, psk8_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace_cfunc(
            vi, selector_string, timeout, psk8_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace(
        self, vi, selector_string, timeout, qam1024_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace_cfunc(
            vi, selector_string, timeout, qam1024_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace(
        self, vi, selector_string, timeout, qam16_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace_cfunc(
            vi, selector_string, timeout, qam16_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace(
        self, vi, selector_string, timeout, qam256_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace_cfunc(
            vi, selector_string, timeout, qam256_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace(
        self, vi, selector_string, timeout, qam64_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace_cfunc(
            vi, selector_string, timeout, qam64_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCHDataConstellationTrace(
        self, vi, selector_string, timeout, pdsch_data_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCHDataConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCHDataConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCHDataConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCHDataConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCHDataConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCHDataConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCHDataConstellationTrace_cfunc(
            vi, selector_string, timeout, pdsch_data_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCHDemodulatedBits(
        self, vi, selector_string, timeout, bits, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCHDemodulatedBits."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCHDemodulatedBits_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCHDemodulatedBits_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchPDSCHDemodulatedBits"
                )
                self.RFmxNR_ModAccFetchPDSCHDemodulatedBits_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCHDemodulatedBits_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCHDemodulatedBits_cfunc(
            vi, selector_string, timeout, bits, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace(
        self, vi, selector_string, timeout, pdsch_dmrs_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace_cfunc(
            vi, selector_string, timeout, pdsch_dmrs_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace(
        self, vi, selector_string, timeout, pdsch_ptrs_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace_cfunc(
            vi, selector_string, timeout, pdsch_ptrs_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace(
        self, vi, selector_string, timeout, qpsk_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace_cfunc(
            vi, selector_string, timeout, qpsk_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        peak_evm_per_slot_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace")
                )
                self.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            peak_evm_per_slot_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        peak_evm_per_subcarrier_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace")
                )
                self.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            peak_evm_per_subcarrier_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        peak_evm_per_symbol_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace")
                )
                self.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            peak_evm_per_symbol_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPSSConstellationTrace(
        self, vi, selector_string, timeout, pss_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPSSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPSSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPSSConstellationTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchPSSConstellationTrace"
                )
                self.RFmxNR_ModAccFetchPSSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPSSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPSSConstellationTrace_cfunc(
            vi, selector_string, timeout, pss_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pss_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace")
                )
                self.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            pss_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pss_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace")
                )
                self.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            pss_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPUSCHDataConstellationTrace(
        self, vi, selector_string, timeout, pusch_data_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPUSCHDataConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPUSCHDataConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPUSCHDataConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPUSCHDataConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPUSCHDataConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPUSCHDataConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPUSCHDataConstellationTrace_cfunc(
            vi, selector_string, timeout, pusch_data_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPUSCHDemodulatedBits(
        self, vi, selector_string, timeout, bits, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPUSCHDemodulatedBits."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPUSCHDemodulatedBits_cfunc is None:
                self.RFmxNR_ModAccFetchPUSCHDemodulatedBits_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchPUSCHDemodulatedBits"
                )
                self.RFmxNR_ModAccFetchPUSCHDemodulatedBits_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPUSCHDemodulatedBits_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPUSCHDemodulatedBits_cfunc(
            vi, selector_string, timeout, bits, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace(
        self, vi, selector_string, timeout, pusch_dmrs_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace_cfunc(
            vi, selector_string, timeout, pusch_dmrs_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace(
        self, vi, selector_string, timeout, pusch_ptrs_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace")
                )
                self.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace_cfunc(
            vi, selector_string, timeout, pusch_ptrs_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_evm_per_slot_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace"
                )
                self.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_evm_per_slot_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace")
                )
                self.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace"
                )
                self.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_evm_high_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace")
                )
                self.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_evm_high_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        peak_evm_high_per_symbol_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace")
                )
                self.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            peak_evm_high_per_symbol_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        rms_evm_low_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace")
                )
                self.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            rms_evm_low_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        peak_evm_low_per_symbol_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace")
                )
                self.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            peak_evm_low_per_symbol_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchTransientPeriodLocationsTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        transient_period_locations,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchTransientPeriodLocationsTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchTransientPeriodLocationsTrace_cfunc is None:
                self.RFmxNR_ModAccFetchTransientPeriodLocationsTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchTransientPeriodLocationsTrace")
                )
                self.RFmxNR_ModAccFetchTransientPeriodLocationsTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchTransientPeriodLocationsTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchTransientPeriodLocationsTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            transient_period_locations,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        pusch_phase_offset,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace_cfunc is None:
                self.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace"
                )
                self.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace_cfunc(
            vi, selector_string, timeout, x0, dx, pusch_phase_offset, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        frequency_error_per_slot_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace_cfunc is None:
                self.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace_cfunc = (
                    self._get_library_function(
                        "RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace"
                    )
                )
                self.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            frequency_error_per_slot_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchSpectralFlatnessTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        spectral_flatness,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchSpectralFlatnessTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchSpectralFlatnessTrace_cfunc is None:
                self.RFmxNR_ModAccFetchSpectralFlatnessTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchSpectralFlatnessTrace"
                )
                self.RFmxNR_ModAccFetchSpectralFlatnessTrace_cfunc.argtypes = [
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
                self.RFmxNR_ModAccFetchSpectralFlatnessTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchSpectralFlatnessTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            spectral_flatness,
            spectral_flatness_lower_mask,
            spectral_flatness_upper_mask,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchSSSConstellationTrace(
        self, vi, selector_string, timeout, sss_constellation, array_size, actual_array_size
    ):
        """RFmxNR_ModAccFetchSSSConstellationTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchSSSConstellationTrace_cfunc is None:
                self.RFmxNR_ModAccFetchSSSConstellationTrace_cfunc = self._get_library_function(
                    "RFmxNR_ModAccFetchSSSConstellationTrace"
                )
                self.RFmxNR_ModAccFetchSSSConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchSSSConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchSSSConstellationTrace_cfunc(
            vi, selector_string, timeout, sss_constellation, array_size, actual_array_size
        )

    def RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        sss_rms_evm_per_subcarrier_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace")
                )
                self.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            sss_rms_evm_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        sss_rms_evm_per_symbol_mean,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace")
                )
                self.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            sss_rms_evm_per_symbol_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchSubblockInBandEmissionTrace(
        self,
        vi,
        selector_string,
        timeout,
        subblock_in_band_emission,
        subblock_in_band_emission_mask,
        subblock_in_band_emission_rb_indices,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ModAccFetchSubblockInBandEmissionTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchSubblockInBandEmissionTrace_cfunc is None:
                self.RFmxNR_ModAccFetchSubblockInBandEmissionTrace_cfunc = (
                    self._get_library_function("RFmxNR_ModAccFetchSubblockInBandEmissionTrace")
                )
                self.RFmxNR_ModAccFetchSubblockInBandEmissionTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchSubblockInBandEmissionTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ModAccFetchSubblockInBandEmissionTrace_cfunc(
            vi,
            selector_string,
            timeout,
            subblock_in_band_emission,
            subblock_in_band_emission_mask,
            subblock_in_band_emission_rb_indices,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace(
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
        """RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace"
                    )
                )
                self.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            iq_gain_imbalance_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace(
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
        """RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace."""
        with self._func_lock:
            if self.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc is None:
                self.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc = (
                    self._get_library_function(
                        "RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace"
                    )
                )
                self.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc.restype = (
                    ctypes.c_int32
                )
        return self.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            iq_quadrature_error_per_subcarrier_mean,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ACPFetchAbsolutePowersTrace(
        self,
        vi,
        selector_string,
        timeout,
        trace_index,
        x0,
        dx,
        absolute_powers_trace,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ACPFetchAbsolutePowersTrace."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchAbsolutePowersTrace_cfunc is None:
                self.RFmxNR_ACPFetchAbsolutePowersTrace_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchAbsolutePowersTrace"
                )
                self.RFmxNR_ACPFetchAbsolutePowersTrace_cfunc.argtypes = [
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
                self.RFmxNR_ACPFetchAbsolutePowersTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchAbsolutePowersTrace_cfunc(
            vi,
            selector_string,
            timeout,
            trace_index,
            x0,
            dx,
            absolute_powers_trace,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ACPFetchComponentCarrierMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_power,
        relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ACPFetchComponentCarrierMeasurementArray."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchComponentCarrierMeasurementArray_cfunc is None:
                self.RFmxNR_ACPFetchComponentCarrierMeasurementArray_cfunc = (
                    self._get_library_function("RFmxNR_ACPFetchComponentCarrierMeasurementArray")
                )
                self.RFmxNR_ACPFetchComponentCarrierMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ACPFetchComponentCarrierMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchComponentCarrierMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_power,
            relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ACPFetchOffsetMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        lower_relative_power,
        upper_relative_power,
        lower_absolute_power,
        upper_absolute_power,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ACPFetchOffsetMeasurementArray."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchOffsetMeasurementArray_cfunc is None:
                self.RFmxNR_ACPFetchOffsetMeasurementArray_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchOffsetMeasurementArray"
                )
                self.RFmxNR_ACPFetchOffsetMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ACPFetchOffsetMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchOffsetMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            lower_relative_power,
            upper_relative_power,
            lower_absolute_power,
            upper_absolute_power,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ACPFetchRelativePowersTrace(
        self,
        vi,
        selector_string,
        timeout,
        trace_index,
        x0,
        dx,
        relative_powers_trace,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_ACPFetchRelativePowersTrace."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchRelativePowersTrace_cfunc is None:
                self.RFmxNR_ACPFetchRelativePowersTrace_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchRelativePowersTrace"
                )
                self.RFmxNR_ACPFetchRelativePowersTrace_cfunc.argtypes = [
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
                self.RFmxNR_ACPFetchRelativePowersTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchRelativePowersTrace_cfunc(
            vi,
            selector_string,
            timeout,
            trace_index,
            x0,
            dx,
            relative_powers_trace,
            array_size,
            actual_array_size,
        )

    def RFmxNR_ACPFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxNR_ACPFetchSpectrum."""
        with self._func_lock:
            if self.RFmxNR_ACPFetchSpectrum_cfunc is None:
                self.RFmxNR_ACPFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxNR_ACPFetchSpectrum"
                )
                self.RFmxNR_ACPFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_ACPFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_ACPFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxNR_TXPFetchPowerTrace(
        self, vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
    ):
        """RFmxNR_TXPFetchPowerTrace."""
        with self._func_lock:
            if self.RFmxNR_TXPFetchPowerTrace_cfunc is None:
                self.RFmxNR_TXPFetchPowerTrace_cfunc = self._get_library_function(
                    "RFmxNR_TXPFetchPowerTrace"
                )
                self.RFmxNR_TXPFetchPowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_TXPFetchPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_TXPFetchPowerTrace_cfunc(
            vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
        )

    def RFmxNR_PVTFetchMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        measurement_status,
        absolute_off_power_before,
        absolute_off_power_after,
        absolute_on_power,
        burst_width,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_PVTFetchMeasurementArray."""
        with self._func_lock:
            if self.RFmxNR_PVTFetchMeasurementArray_cfunc is None:
                self.RFmxNR_PVTFetchMeasurementArray_cfunc = self._get_library_function(
                    "RFmxNR_PVTFetchMeasurementArray"
                )
                self.RFmxNR_PVTFetchMeasurementArray_cfunc.argtypes = [
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
                self.RFmxNR_PVTFetchMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTFetchMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            measurement_status,
            absolute_off_power_before,
            absolute_off_power_after,
            absolute_on_power,
            burst_width,
            array_size,
            actual_array_size,
        )

    def RFmxNR_PVTFetchSignalPowerTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        signal_power,
        absolute_limit,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_PVTFetchSignalPowerTrace."""
        with self._func_lock:
            if self.RFmxNR_PVTFetchSignalPowerTrace_cfunc is None:
                self.RFmxNR_PVTFetchSignalPowerTrace_cfunc = self._get_library_function(
                    "RFmxNR_PVTFetchSignalPowerTrace"
                )
                self.RFmxNR_PVTFetchSignalPowerTrace_cfunc.argtypes = [
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
                self.RFmxNR_PVTFetchSignalPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTFetchSignalPowerTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            signal_power,
            absolute_limit,
            array_size,
            actual_array_size,
        )

    def RFmxNR_PVTFetchWindowedSignalPowerTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        windowed_signal_power,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_PVTFetchWindowedSignalPowerTrace."""
        with self._func_lock:
            if self.RFmxNR_PVTFetchWindowedSignalPowerTrace_cfunc is None:
                self.RFmxNR_PVTFetchWindowedSignalPowerTrace_cfunc = self._get_library_function(
                    "RFmxNR_PVTFetchWindowedSignalPowerTrace"
                )
                self.RFmxNR_PVTFetchWindowedSignalPowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_PVTFetchWindowedSignalPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_PVTFetchWindowedSignalPowerTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            windowed_signal_power,
            array_size,
            actual_array_size,
        )

    def RFmxNR_OBWFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxNR_OBWFetchSpectrum."""
        with self._func_lock:
            if self.RFmxNR_OBWFetchSpectrum_cfunc is None:
                self.RFmxNR_OBWFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxNR_OBWFetchSpectrum"
                )
                self.RFmxNR_OBWFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_OBWFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_OBWFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxNR_SEMFetchComponentCarrierMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_power,
        peak_absolute_power,
        peak_frequency,
        relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_SEMFetchComponentCarrierMeasurementArray."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchComponentCarrierMeasurementArray_cfunc is None:
                self.RFmxNR_SEMFetchComponentCarrierMeasurementArray_cfunc = (
                    self._get_library_function("RFmxNR_SEMFetchComponentCarrierMeasurementArray")
                )
                self.RFmxNR_SEMFetchComponentCarrierMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_SEMFetchComponentCarrierMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchComponentCarrierMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_power,
            peak_absolute_power,
            peak_frequency,
            relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxNR_SEMFetchLowerOffsetMarginArray(
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
        """RFmxNR_SEMFetchLowerOffsetMarginArray."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchLowerOffsetMarginArray_cfunc is None:
                self.RFmxNR_SEMFetchLowerOffsetMarginArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchLowerOffsetMarginArray"
                )
                self.RFmxNR_SEMFetchLowerOffsetMarginArray_cfunc.argtypes = [
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
                self.RFmxNR_SEMFetchLowerOffsetMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchLowerOffsetMarginArray_cfunc(
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

    def RFmxNR_SEMFetchLowerOffsetPowerArray(
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
        """RFmxNR_SEMFetchLowerOffsetPowerArray."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchLowerOffsetPowerArray_cfunc is None:
                self.RFmxNR_SEMFetchLowerOffsetPowerArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchLowerOffsetPowerArray"
                )
                self.RFmxNR_SEMFetchLowerOffsetPowerArray_cfunc.argtypes = [
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
                self.RFmxNR_SEMFetchLowerOffsetPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchLowerOffsetPowerArray_cfunc(
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

    def RFmxNR_SEMFetchSpectrum(
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
        """RFmxNR_SEMFetchSpectrum."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchSpectrum_cfunc is None:
                self.RFmxNR_SEMFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchSpectrum"
                )
                self.RFmxNR_SEMFetchSpectrum_cfunc.argtypes = [
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
                self.RFmxNR_SEMFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchSpectrum_cfunc(
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

    def RFmxNR_SEMFetchUpperOffsetMarginArray(
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
        """RFmxNR_SEMFetchUpperOffsetMarginArray."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchUpperOffsetMarginArray_cfunc is None:
                self.RFmxNR_SEMFetchUpperOffsetMarginArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchUpperOffsetMarginArray"
                )
                self.RFmxNR_SEMFetchUpperOffsetMarginArray_cfunc.argtypes = [
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
                self.RFmxNR_SEMFetchUpperOffsetMarginArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchUpperOffsetMarginArray_cfunc(
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

    def RFmxNR_SEMFetchUpperOffsetPowerArray(
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
        """RFmxNR_SEMFetchUpperOffsetPowerArray."""
        with self._func_lock:
            if self.RFmxNR_SEMFetchUpperOffsetPowerArray_cfunc is None:
                self.RFmxNR_SEMFetchUpperOffsetPowerArray_cfunc = self._get_library_function(
                    "RFmxNR_SEMFetchUpperOffsetPowerArray"
                )
                self.RFmxNR_SEMFetchUpperOffsetPowerArray_cfunc.argtypes = [
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
                self.RFmxNR_SEMFetchUpperOffsetPowerArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SEMFetchUpperOffsetPowerArray_cfunc(
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

    def RFmxNR_CHPFetchComponentCarrierMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        absolute_power,
        relative_power,
        array_size,
        actual_array_size,
    ):
        """RFmxNR_CHPFetchComponentCarrierMeasurementArray."""
        with self._func_lock:
            if self.RFmxNR_CHPFetchComponentCarrierMeasurementArray_cfunc is None:
                self.RFmxNR_CHPFetchComponentCarrierMeasurementArray_cfunc = (
                    self._get_library_function("RFmxNR_CHPFetchComponentCarrierMeasurementArray")
                )
                self.RFmxNR_CHPFetchComponentCarrierMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_CHPFetchComponentCarrierMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPFetchComponentCarrierMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            absolute_power,
            relative_power,
            array_size,
            actual_array_size,
        )

    def RFmxNR_CHPFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxNR_CHPFetchSpectrum."""
        with self._func_lock:
            if self.RFmxNR_CHPFetchSpectrum_cfunc is None:
                self.RFmxNR_CHPFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxNR_CHPFetchSpectrum"
                )
                self.RFmxNR_CHPFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_CHPFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CHPFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxNR_CloneSignalConfiguration(self, vi, old_signal_name, new_signal_name):
        """RFmxNR_CloneSignalConfiguration."""
        with self._func_lock:
            if self.RFmxNR_CloneSignalConfiguration_cfunc is None:
                self.RFmxNR_CloneSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxNR_CloneSignalConfiguration"
                )
                self.RFmxNR_CloneSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_CloneSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_CloneSignalConfiguration_cfunc(vi, old_signal_name, new_signal_name)

    def RFmxNR_SendSoftwareEdgeTrigger(self, vi):
        """RFmxNR_SendSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxNR_SendSoftwareEdgeTrigger_cfunc is None:
                self.RFmxNR_SendSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxNR_SendSoftwareEdgeTrigger"
                )
                self.RFmxNR_SendSoftwareEdgeTrigger_cfunc.argtypes = [ctypes.c_uint32]
                self.RFmxNR_SendSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_SendSoftwareEdgeTrigger_cfunc(vi)

    def RFmxNR_DeleteSignalConfiguration(self, vi, signal_name):
        """RFmxNR_DeleteSignalConfiguration."""
        with self._func_lock:
            if self.RFmxNR_DeleteSignalConfiguration_cfunc is None:
                self.RFmxNR_DeleteSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxNR_DeleteSignalConfiguration"
                )
                self.RFmxNR_DeleteSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxNR_DeleteSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_DeleteSignalConfiguration_cfunc(vi, signal_name)

    def RFmxNR_GetAllNamedResultNames(
        self,
        vi,
        selector_string,
        result_names,
        result_names_buffer_size,
        actual_result_names_size,
        default_result_exists,
    ):
        """RFmxNR_GetAllNamedResultNames."""
        with self._func_lock:
            if self.RFmxNR_GetAllNamedResultNames_cfunc is None:
                self.RFmxNR_GetAllNamedResultNames_cfunc = self._get_library_function(
                    "RFmxNR_GetAllNamedResultNames"
                )
                self.RFmxNR_GetAllNamedResultNames_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxNR_GetAllNamedResultNames_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_GetAllNamedResultNames_cfunc(
            vi,
            selector_string,
            result_names,
            result_names_buffer_size,
            actual_result_names_size,
            default_result_exists,
        )

    def RFmxNR_AnalyzeIQ1Waveform(
        self, vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
    ):
        """RFmxNR_AnalyzeIQ1Waveform."""
        with self._func_lock:
            if self.RFmxNR_AnalyzeIQ1Waveform_cfunc is None:
                self.RFmxNR_AnalyzeIQ1Waveform_cfunc = self._get_library_function(
                    "RFmxNR_AnalyzeIQ1Waveform"
                )
                self.RFmxNR_AnalyzeIQ1Waveform_cfunc.argtypes = [
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
                self.RFmxNR_AnalyzeIQ1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_AnalyzeIQ1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
        )

    def RFmxNR_AnalyzeSpectrum1Waveform(
        self, vi, selector_string, result_name, x0, dx, spectrum, array_size, reset, reserved
    ):
        """RFmxNR_AnalyzeSpectrum1Waveform."""
        with self._func_lock:
            if self.RFmxNR_AnalyzeSpectrum1Waveform_cfunc is None:
                self.RFmxNR_AnalyzeSpectrum1Waveform_cfunc = self._get_library_function(
                    "RFmxNR_AnalyzeSpectrum1Waveform"
                )
                self.RFmxNR_AnalyzeSpectrum1Waveform_cfunc.argtypes = [
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
                self.RFmxNR_AnalyzeSpectrum1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_AnalyzeSpectrum1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, spectrum, array_size, reset, reserved
        )

    def RFmxNR_AnalyzeNWaveformsIQ(
        self, vi, selector_string, result_name, x0, dx, iq, iq_size, array_size, reset
    ):
        """RFmxNR_AnalyzeNWaveformsIQ."""
        with self._func_lock:
            if self.RFmxNR_AnalyzeNWaveformsIQ_cfunc is None:
                self.RFmxNR_AnalyzeNWaveformsIQ_cfunc = self._get_library_function(
                    "RFmxNR_AnalyzeNWaveformsIQ"
                )
                self.RFmxNR_AnalyzeNWaveformsIQ_cfunc.argtypes = [
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
                self.RFmxNR_AnalyzeNWaveformsIQ_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_AnalyzeNWaveformsIQ_cfunc(
            vi, selector_string, result_name, x0, dx, iq, iq_size, array_size, reset
        )

    def RFmxNR_AnalyzeNWaveformsSpectrum(
        self, vi, selector_string, result_name, x0, dx, spectrum, spectrum_size, array_size, reset
    ):
        """RFmxNR_AnalyzeNWaveformsSpectrum."""
        with self._func_lock:
            if self.RFmxNR_AnalyzeNWaveformsSpectrum_cfunc is None:
                self.RFmxNR_AnalyzeNWaveformsSpectrum_cfunc = self._get_library_function(
                    "RFmxNR_AnalyzeNWaveformsSpectrum"
                )
                self.RFmxNR_AnalyzeNWaveformsSpectrum_cfunc.argtypes = [
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
                self.RFmxNR_AnalyzeNWaveformsSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxNR_AnalyzeNWaveformsSpectrum_cfunc(
            vi, selector_string, result_name, x0, dx, spectrum, spectrum_size, array_size, reset
        )
