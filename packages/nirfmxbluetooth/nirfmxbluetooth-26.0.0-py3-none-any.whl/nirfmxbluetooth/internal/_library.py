"""Wrapper around driver library.
Class will setup the correct ctypes information for every function on first call.
"""

import ctypes
import threading
from typing import Any

import nirfmxbluetooth.errors as errors
import nirfmxbluetooth.internal._custom_types as _custom_types


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
        self.RFmxBT_ResetAttribute_cfunc = None
        self.RFmxBT_GetError_cfunc = None
        self.RFmxBT_GetErrorString_cfunc = None
        self.RFmxBT_GetAttributeI8_cfunc = None
        self.RFmxBT_SetAttributeI8_cfunc = None
        self.RFmxBT_GetAttributeI8Array_cfunc = None
        self.RFmxBT_SetAttributeI8Array_cfunc = None
        self.RFmxBT_GetAttributeI16_cfunc = None
        self.RFmxBT_SetAttributeI16_cfunc = None
        self.RFmxBT_GetAttributeI32_cfunc = None
        self.RFmxBT_SetAttributeI32_cfunc = None
        self.RFmxBT_GetAttributeI32Array_cfunc = None
        self.RFmxBT_SetAttributeI32Array_cfunc = None
        self.RFmxBT_GetAttributeI64_cfunc = None
        self.RFmxBT_SetAttributeI64_cfunc = None
        self.RFmxBT_GetAttributeI64Array_cfunc = None
        self.RFmxBT_SetAttributeI64Array_cfunc = None
        self.RFmxBT_GetAttributeU8_cfunc = None
        self.RFmxBT_SetAttributeU8_cfunc = None
        self.RFmxBT_GetAttributeU8Array_cfunc = None
        self.RFmxBT_SetAttributeU8Array_cfunc = None
        self.RFmxBT_GetAttributeU16_cfunc = None
        self.RFmxBT_SetAttributeU16_cfunc = None
        self.RFmxBT_GetAttributeU32_cfunc = None
        self.RFmxBT_SetAttributeU32_cfunc = None
        self.RFmxBT_GetAttributeU32Array_cfunc = None
        self.RFmxBT_SetAttributeU32Array_cfunc = None
        self.RFmxBT_GetAttributeU64Array_cfunc = None
        self.RFmxBT_SetAttributeU64Array_cfunc = None
        self.RFmxBT_GetAttributeF32_cfunc = None
        self.RFmxBT_SetAttributeF32_cfunc = None
        self.RFmxBT_GetAttributeF32Array_cfunc = None
        self.RFmxBT_SetAttributeF32Array_cfunc = None
        self.RFmxBT_GetAttributeF64_cfunc = None
        self.RFmxBT_SetAttributeF64_cfunc = None
        self.RFmxBT_GetAttributeF64Array_cfunc = None
        self.RFmxBT_SetAttributeF64Array_cfunc = None
        self.RFmxBT_GetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxBT_SetAttributeNIComplexSingleArray_cfunc = None
        self.RFmxBT_GetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxBT_SetAttributeNIComplexDoubleArray_cfunc = None
        self.RFmxBT_GetAttributeString_cfunc = None
        self.RFmxBT_SetAttributeString_cfunc = None
        self.RFmxBT_AbortMeasurements_cfunc = None
        self.RFmxBT_AnalyzeIQ1Waveform_cfunc = None
        self.RFmxBT_AutoDetectSignal_cfunc = None
        self.RFmxBT_AutoLevel_cfunc = None
        self.RFmxBT_CheckMeasurementStatus_cfunc = None
        self.RFmxBT_ClearAllNamedResults_cfunc = None
        self.RFmxBT_ClearNamedResult_cfunc = None
        self.RFmxBT_CloneSignalConfiguration_cfunc = None
        self.RFmxBT_Commit_cfunc = None
        self.RFmxBT_CfgDigitalEdgeTrigger_cfunc = None
        self.RFmxBT_CfgFrequencyChannelNumber_cfunc = None
        self.RFmxBT_CfgIQPowerEdgeTrigger_cfunc = None
        self.RFmxBT_CfgSoftwareEdgeTrigger_cfunc = None
        self.RFmxBT_CreateSignalConfiguration_cfunc = None
        self.RFmxBT_DeleteSignalConfiguration_cfunc = None
        self.RFmxBT_DisableTrigger_cfunc = None
        self.RFmxBT_GetAllNamedResultNames_cfunc = None
        self.RFmxBT_Initiate_cfunc = None
        self.RFmxBT_ResetToDefault_cfunc = None
        self.RFmxBT_SelectMeasurements_cfunc = None
        self.RFmxBT_SendSoftwareEdgeTrigger_cfunc = None
        self.RFmxBT_WaitForMeasurementComplete_cfunc = None
        self.RFmxBT_TXPCfgAveraging_cfunc = None
        self.RFmxBT_TXPCfgBurstSynchronizationType_cfunc = None
        self.RFmxBT_ModAccCfgAveraging_cfunc = None
        self.RFmxBT_ModAccCfgBurstSynchronizationType_cfunc = None
        self.RFmxBT_20dBBandwidthCfgAveraging_cfunc = None
        self.RFmxBT_FrequencyRangeCfgAveraging_cfunc = None
        self.RFmxBT_FrequencyRangeCfgSpan_cfunc = None
        self.RFmxBT_ACPCfgAveraging_cfunc = None
        self.RFmxBT_ACPCfgBurstSynchronizationType_cfunc = None
        self.RFmxBT_ACPCfgNumberOfOffsets_cfunc = None
        self.RFmxBT_ACPCfgOffsetChannelMode_cfunc = None
        self.RFmxBT_PowerRampCfgAveraging_cfunc = None
        self.RFmxBT_PowerRampCfgBurstSynchronizationType_cfunc = None
        self.RFmxBT_ModSpectrumCfgAveraging_cfunc = None
        self.RFmxBT_ModSpectrumCfgBurstSynchronizationType_cfunc = None
        self.RFmxBT_CfgChannelNumber_cfunc = None
        self.RFmxBT_CfgDataRate_cfunc = None
        self.RFmxBT_CfgExternalAttenuation_cfunc = None
        self.RFmxBT_CfgFrequency_cfunc = None
        self.RFmxBT_CfgLEDirectionFinding_cfunc = None
        self.RFmxBT_CfgPacketType_cfunc = None
        self.RFmxBT_CfgPayloadBitPattern_cfunc = None
        self.RFmxBT_CfgPayloadLength_cfunc = None
        self.RFmxBT_CfgReferenceLevel_cfunc = None
        self.RFmxBT_CfgRF_cfunc = None
        self.RFmxBT_TXPFetchEDRPowers_cfunc = None
        self.RFmxBT_TXPFetchLECTEReferencePeriodPowers_cfunc = None
        self.RFmxBT_TXPFetchLECTETransmitSlotPowers_cfunc = None
        self.RFmxBT_TXPFetchPowers_cfunc = None
        self.RFmxBT_ModAccFetchDEVM_cfunc = None
        self.RFmxBT_ModAccFetchDEVMMagnitudeError_cfunc = None
        self.RFmxBT_ModAccFetchDEVMPhaseError_cfunc = None
        self.RFmxBT_ModAccFetchDf1_cfunc = None
        self.RFmxBT_ModAccFetchDf2_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyErrorBR_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyErrorEDR_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyErrorLE_cfunc = None
        self.RFmxBT_20dBBandwidthFetchMeasurement_cfunc = None
        self.RFmxBT_FrequencyRangeFetchMeasurement_cfunc = None
        self.RFmxBT_ACPFetchMeasurementStatus_cfunc = None
        self.RFmxBT_ACPFetchOffsetMeasurement_cfunc = None
        self.RFmxBT_ACPFetchReferenceChannelPower_cfunc = None
        self.RFmxBT_TXPFetchLECTETransmitSlotPowersArray_cfunc = None
        self.RFmxBT_TXPFetchPowerTrace_cfunc = None
        self.RFmxBT_ModAccFetchConstellationTrace_cfunc = None
        self.RFmxBT_ModAccFetchCSDetrendedPhaseTrace_cfunc = None
        self.RFmxBT_ModAccFetchCSToneTrace_cfunc = None
        self.RFmxBT_ModAccFetchDemodulatedBitTrace_cfunc = None
        self.RFmxBT_ModAccFetchDEVMPerSymbolTrace_cfunc = None
        self.RFmxBT_ModAccFetchEVMPerSymbolTrace_cfunc = None
        self.RFmxBT_ModAccFetchDf1maxTrace_cfunc = None
        self.RFmxBT_ModAccFetchDf2maxTrace_cfunc = None
        self.RFmxBT_ModAccFetchDf4avgTrace_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyErrorTraceBR_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyErrorTraceLE_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR_cfunc = None
        self.RFmxBT_ModAccFetchFrequencyTrace_cfunc = None
        self.RFmxBT_ModAccFetchRMSDEVMTrace_cfunc = None
        self.RFmxBT_20dBBandwidthFetchSpectrum_cfunc = None
        self.RFmxBT_FrequencyRangeFetchSpectrum_cfunc = None
        self.RFmxBT_ACPFetchAbsolutePowerTrace_cfunc = None
        self.RFmxBT_ACPFetchMaskTrace_cfunc = None
        self.RFmxBT_ACPFetchOffsetMeasurementArray_cfunc = None
        self.RFmxBT_ACPFetchSpectrum_cfunc = None
        self.RFmxBT_ModSpectrumFetchSpectrum_cfunc = None

    def _get_library_function(self, name: str) -> Any:
        try:
            function = getattr(self._library, name)
        except AttributeError as e:
            raise errors.DriverTooOldError() from e  # type: ignore
        return function

    def RFmxBT_ResetAttribute(self, vi, selector_string, attribute_id):
        """RFmxBT_ResetAttribute."""
        with self._func_lock:
            if self.RFmxBT_ResetAttribute_cfunc is None:
                self.RFmxBT_ResetAttribute_cfunc = self._get_library_function(
                    "RFmxBT_ResetAttribute"
                )
                self.RFmxBT_ResetAttribute_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_ResetAttribute_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ResetAttribute_cfunc(vi, selector_string, attribute_id)

    def RFmxBT_GetError(self, vi, error_code, error_description_buffer_size, error_description):
        """RFmxBT_GetError."""
        with self._func_lock:
            if self.RFmxBT_GetError_cfunc is None:
                self.RFmxBT_GetError_cfunc = self._get_library_function("RFmxBT_GetError")
                self.RFmxBT_GetError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_GetError_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetError_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxBT_GetErrorString(
        self, vi, error_code, error_description_buffer_size, error_description
    ):
        """RFmxBT_GetErrorString."""
        with self._func_lock:
            if self.RFmxBT_GetErrorString_cfunc is None:
                self.RFmxBT_GetErrorString_cfunc = self._get_library_function(
                    "RFmxBT_GetErrorString"
                )
                self.RFmxBT_GetErrorString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_GetErrorString_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetErrorString_cfunc(
            vi, error_code, error_description_buffer_size, error_description
        )

    def RFmxBT_GetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeI8."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI8_cfunc is None:
                self.RFmxBT_GetAttributeI8_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI8"
                )
                self.RFmxBT_GetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                ]
                self.RFmxBT_GetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeI8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeI8."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI8_cfunc is None:
                self.RFmxBT_SetAttributeI8_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI8"
                )
                self.RFmxBT_SetAttributeI8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int8,
                ]
                self.RFmxBT_SetAttributeI8_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeI16."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI16_cfunc is None:
                self.RFmxBT_GetAttributeI16_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI16"
                )
                self.RFmxBT_GetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int16),
                ]
                self.RFmxBT_GetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeI16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeI16."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI16_cfunc is None:
                self.RFmxBT_SetAttributeI16_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI16"
                )
                self.RFmxBT_SetAttributeI16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int16,
                ]
                self.RFmxBT_SetAttributeI16_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeI32."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI32_cfunc is None:
                self.RFmxBT_GetAttributeI32_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI32"
                )
                self.RFmxBT_GetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeI32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeI32."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI32_cfunc is None:
                self.RFmxBT_SetAttributeI32_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI32"
                )
                self.RFmxBT_SetAttributeI32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_SetAttributeI32_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeI64."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI64_cfunc is None:
                self.RFmxBT_GetAttributeI64_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI64"
                )
                self.RFmxBT_GetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                ]
                self.RFmxBT_GetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeI64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeI64."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI64_cfunc is None:
                self.RFmxBT_SetAttributeI64_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI64"
                )
                self.RFmxBT_SetAttributeI64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int64,
                ]
                self.RFmxBT_SetAttributeI64_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeU8."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeU8_cfunc is None:
                self.RFmxBT_GetAttributeU8_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeU8"
                )
                self.RFmxBT_GetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                ]
                self.RFmxBT_GetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeU8(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeU8."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeU8_cfunc is None:
                self.RFmxBT_SetAttributeU8_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeU8"
                )
                self.RFmxBT_SetAttributeU8_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint8,
                ]
                self.RFmxBT_SetAttributeU8_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeU8_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeU16."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeU16_cfunc is None:
                self.RFmxBT_GetAttributeU16_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeU16"
                )
                self.RFmxBT_GetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint16),
                ]
                self.RFmxBT_GetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeU16(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeU16."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeU16_cfunc is None:
                self.RFmxBT_SetAttributeU16_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeU16"
                )
                self.RFmxBT_SetAttributeU16_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint16,
                ]
                self.RFmxBT_SetAttributeU16_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeU16_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeU32."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeU32_cfunc is None:
                self.RFmxBT_GetAttributeU32_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeU32"
                )
                self.RFmxBT_GetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                ]
                self.RFmxBT_GetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeU32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeU32."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeU32_cfunc is None:
                self.RFmxBT_SetAttributeU32_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeU32"
                )
                self.RFmxBT_SetAttributeU32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeU32_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeU32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeF32."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeF32_cfunc is None:
                self.RFmxBT_GetAttributeF32_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeF32"
                )
                self.RFmxBT_GetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                ]
                self.RFmxBT_GetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeF32(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeF32."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeF32_cfunc is None:
                self.RFmxBT_SetAttributeF32_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeF32"
                )
                self.RFmxBT_SetAttributeF32_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_float,
                ]
                self.RFmxBT_SetAttributeF32_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeF32_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_GetAttributeF64."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeF64_cfunc is None:
                self.RFmxBT_GetAttributeF64_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeF64"
                )
                self.RFmxBT_GetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_GetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_SetAttributeF64(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeF64."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeF64_cfunc is None:
                self.RFmxBT_SetAttributeF64_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeF64"
                )
                self.RFmxBT_SetAttributeF64_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_double,
                ]
                self.RFmxBT_SetAttributeF64_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeF64_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_GetAttributeI8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI8Array_cfunc is None:
                self.RFmxBT_GetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI8Array"
                )
                self.RFmxBT_GetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeI8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeI8Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI8Array_cfunc is None:
                self.RFmxBT_SetAttributeI8Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI8Array"
                )
                self.RFmxBT_SetAttributeI8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeI8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeI32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI32Array_cfunc is None:
                self.RFmxBT_GetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI32Array"
                )
                self.RFmxBT_GetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeI32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeI32Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI32Array_cfunc is None:
                self.RFmxBT_SetAttributeI32Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI32Array"
                )
                self.RFmxBT_SetAttributeI32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeI32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeI64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeI64Array_cfunc is None:
                self.RFmxBT_GetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeI64Array"
                )
                self.RFmxBT_GetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeI64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeI64Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeI64Array_cfunc is None:
                self.RFmxBT_SetAttributeI64Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeI64Array"
                )
                self.RFmxBT_SetAttributeI64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_int64),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeI64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeI64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeU8Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeU8Array_cfunc is None:
                self.RFmxBT_GetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeU8Array"
                )
                self.RFmxBT_GetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeU8Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeU8Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeU8Array_cfunc is None:
                self.RFmxBT_SetAttributeU8Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeU8Array"
                )
                self.RFmxBT_SetAttributeU8Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint8),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeU8Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeU8Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeU32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeU32Array_cfunc is None:
                self.RFmxBT_GetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeU32Array"
                )
                self.RFmxBT_GetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeU32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeU32Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeU32Array_cfunc is None:
                self.RFmxBT_SetAttributeU32Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeU32Array"
                )
                self.RFmxBT_SetAttributeU32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint32),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeU32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeU32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeU64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeU64Array_cfunc is None:
                self.RFmxBT_GetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeU64Array"
                )
                self.RFmxBT_GetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeU64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeU64Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeU64Array_cfunc is None:
                self.RFmxBT_SetAttributeU64Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeU64Array"
                )
                self.RFmxBT_SetAttributeU64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_uint64),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeU64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeU64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeF32Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeF32Array_cfunc is None:
                self.RFmxBT_GetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeF32Array"
                )
                self.RFmxBT_GetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeF32Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeF32Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeF32Array_cfunc is None:
                self.RFmxBT_SetAttributeF32Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeF32Array"
                )
                self.RFmxBT_SetAttributeF32Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeF32Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeF32Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeF64Array(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeF64Array_cfunc is None:
                self.RFmxBT_GetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeF64Array"
                )
                self.RFmxBT_GetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeF64Array(self, vi, selector_string, attribute_id, attr_val, array_size):
        """RFmxBT_SetAttributeF64Array."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeF64Array_cfunc is None:
                self.RFmxBT_SetAttributeF64Array_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeF64Array"
                )
                self.RFmxBT_SetAttributeF64Array_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeF64Array_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeF64Array_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxBT_GetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeNIComplexSingleArray"
                )
                self.RFmxBT_GetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeNIComplexSingleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxBT_SetAttributeNIComplexSingleArray."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeNIComplexSingleArray_cfunc is None:
                self.RFmxBT_SetAttributeNIComplexSingleArray_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeNIComplexSingleArray"
                )
                self.RFmxBT_SetAttributeNIComplexSingleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeNIComplexSingleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeNIComplexSingleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
    ):
        """RFmxBT_GetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxBT_GetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeNIComplexDoubleArray"
                )
                self.RFmxBT_GetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size, actual_array_size
        )

    def RFmxBT_SetAttributeNIComplexDoubleArray(
        self, vi, selector_string, attribute_id, attr_val, array_size
    ):
        """RFmxBT_SetAttributeNIComplexDoubleArray."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeNIComplexDoubleArray_cfunc is None:
                self.RFmxBT_SetAttributeNIComplexDoubleArray_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeNIComplexDoubleArray"
                )
                self.RFmxBT_SetAttributeNIComplexDoubleArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_uint32,
                ]
                self.RFmxBT_SetAttributeNIComplexDoubleArray_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeNIComplexDoubleArray_cfunc(
            vi, selector_string, attribute_id, attr_val, array_size
        )

    def RFmxBT_GetAttributeString(self, vi, selector_string, attribute_id, array_size, attr_val):
        """RFmxBT_GetAttributeString."""
        with self._func_lock:
            if self.RFmxBT_GetAttributeString_cfunc is None:
                self.RFmxBT_GetAttributeString_cfunc = self._get_library_function(
                    "RFmxBT_GetAttributeString"
                )
                self.RFmxBT_GetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_GetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAttributeString_cfunc(
            vi, selector_string, attribute_id, array_size, attr_val
        )

    def RFmxBT_SetAttributeString(self, vi, selector_string, attribute_id, attr_val):
        """RFmxBT_SetAttributeString."""
        with self._func_lock:
            if self.RFmxBT_SetAttributeString_cfunc is None:
                self.RFmxBT_SetAttributeString_cfunc = self._get_library_function(
                    "RFmxBT_SetAttributeString"
                )
                self.RFmxBT_SetAttributeString_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_SetAttributeString_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SetAttributeString_cfunc(vi, selector_string, attribute_id, attr_val)

    def RFmxBT_AbortMeasurements(self, vi, selector_string):
        """RFmxBT_AbortMeasurements."""
        with self._func_lock:
            if self.RFmxBT_AbortMeasurements_cfunc is None:
                self.RFmxBT_AbortMeasurements_cfunc = self._get_library_function(
                    "RFmxBT_AbortMeasurements"
                )
                self.RFmxBT_AbortMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_AbortMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_AbortMeasurements_cfunc(vi, selector_string)

    def RFmxBT_AutoDetectSignal(self, vi, selector_string, timeout):
        """RFmxBT_AutoDetectSignal."""
        with self._func_lock:
            if self.RFmxBT_AutoDetectSignal_cfunc is None:
                self.RFmxBT_AutoDetectSignal_cfunc = self._get_library_function(
                    "RFmxBT_AutoDetectSignal"
                )
                self.RFmxBT_AutoDetectSignal_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxBT_AutoDetectSignal_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_AutoDetectSignal_cfunc(vi, selector_string, timeout)

    def RFmxBT_AutoLevel(self, vi, selector_string, measurement_interval, reference_level):
        """RFmxBT_AutoLevel."""
        with self._func_lock:
            if self.RFmxBT_AutoLevel_cfunc is None:
                self.RFmxBT_AutoLevel_cfunc = self._get_library_function("RFmxBT_AutoLevel")
                self.RFmxBT_AutoLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_AutoLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_AutoLevel_cfunc(
            vi, selector_string, measurement_interval, reference_level
        )

    def RFmxBT_CheckMeasurementStatus(self, vi, selector_string, is_done):
        """RFmxBT_CheckMeasurementStatus."""
        with self._func_lock:
            if self.RFmxBT_CheckMeasurementStatus_cfunc is None:
                self.RFmxBT_CheckMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxBT_CheckMeasurementStatus"
                )
                self.RFmxBT_CheckMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_CheckMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CheckMeasurementStatus_cfunc(vi, selector_string, is_done)

    def RFmxBT_ClearAllNamedResults(self, vi, selector_string):
        """RFmxBT_ClearAllNamedResults."""
        with self._func_lock:
            if self.RFmxBT_ClearAllNamedResults_cfunc is None:
                self.RFmxBT_ClearAllNamedResults_cfunc = self._get_library_function(
                    "RFmxBT_ClearAllNamedResults"
                )
                self.RFmxBT_ClearAllNamedResults_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_ClearAllNamedResults_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ClearAllNamedResults_cfunc(vi, selector_string)

    def RFmxBT_ClearNamedResult(self, vi, selector_string):
        """RFmxBT_ClearNamedResult."""
        with self._func_lock:
            if self.RFmxBT_ClearNamedResult_cfunc is None:
                self.RFmxBT_ClearNamedResult_cfunc = self._get_library_function(
                    "RFmxBT_ClearNamedResult"
                )
                self.RFmxBT_ClearNamedResult_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_ClearNamedResult_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ClearNamedResult_cfunc(vi, selector_string)

    def RFmxBT_Commit(self, vi, selector_string):
        """RFmxBT_Commit."""
        with self._func_lock:
            if self.RFmxBT_Commit_cfunc is None:
                self.RFmxBT_Commit_cfunc = self._get_library_function("RFmxBT_Commit")
                self.RFmxBT_Commit_cfunc.argtypes = [ctypes.c_uint32, ctypes.POINTER(ctypes.c_char)]
                self.RFmxBT_Commit_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_Commit_cfunc(vi, selector_string)

    def RFmxBT_CfgDigitalEdgeTrigger(
        self, vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        """RFmxBT_CfgDigitalEdgeTrigger."""
        with self._func_lock:
            if self.RFmxBT_CfgDigitalEdgeTrigger_cfunc is None:
                self.RFmxBT_CfgDigitalEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxBT_CfgDigitalEdgeTrigger"
                )
                self.RFmxBT_CfgDigitalEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgDigitalEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgDigitalEdgeTrigger_cfunc(
            vi, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
        )

    def RFmxBT_CfgFrequencyChannelNumber(self, vi, selector_string, standard, channel_number):
        """RFmxBT_CfgFrequencyChannelNumber."""
        with self._func_lock:
            if self.RFmxBT_CfgFrequencyChannelNumber_cfunc is None:
                self.RFmxBT_CfgFrequencyChannelNumber_cfunc = self._get_library_function(
                    "RFmxBT_CfgFrequencyChannelNumber"
                )
                self.RFmxBT_CfgFrequencyChannelNumber_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgFrequencyChannelNumber_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgFrequencyChannelNumber_cfunc(
            vi, selector_string, standard, channel_number
        )

    def RFmxBT_CfgIQPowerEdgeTrigger(
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
        """RFmxBT_CfgIQPowerEdgeTrigger."""
        with self._func_lock:
            if self.RFmxBT_CfgIQPowerEdgeTrigger_cfunc is None:
                self.RFmxBT_CfgIQPowerEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxBT_CfgIQPowerEdgeTrigger"
                )
                self.RFmxBT_CfgIQPowerEdgeTrigger_cfunc.argtypes = [
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
                self.RFmxBT_CfgIQPowerEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgIQPowerEdgeTrigger_cfunc(
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

    def RFmxBT_CfgSoftwareEdgeTrigger(self, vi, selector_string, trigger_delay, enable_trigger):
        """RFmxBT_CfgSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxBT_CfgSoftwareEdgeTrigger_cfunc is None:
                self.RFmxBT_CfgSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxBT_CfgSoftwareEdgeTrigger"
                )
                self.RFmxBT_CfgSoftwareEdgeTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgSoftwareEdgeTrigger_cfunc(
            vi, selector_string, trigger_delay, enable_trigger
        )

    def RFmxBT_CreateSignalConfiguration(self, vi, signal_name):
        """RFmxBT_CreateSignalConfiguration."""
        with self._func_lock:
            if self.RFmxBT_CreateSignalConfiguration_cfunc is None:
                self.RFmxBT_CreateSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxBT_CreateSignalConfiguration"
                )
                self.RFmxBT_CreateSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_CreateSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CreateSignalConfiguration_cfunc(vi, signal_name)

    def RFmxBT_DisableTrigger(self, vi, selector_string):
        """RFmxBT_DisableTrigger."""
        with self._func_lock:
            if self.RFmxBT_DisableTrigger_cfunc is None:
                self.RFmxBT_DisableTrigger_cfunc = self._get_library_function(
                    "RFmxBT_DisableTrigger"
                )
                self.RFmxBT_DisableTrigger_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_DisableTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_DisableTrigger_cfunc(vi, selector_string)

    def RFmxBT_Initiate(self, vi, selector_string, result_name):
        """RFmxBT_Initiate."""
        with self._func_lock:
            if self.RFmxBT_Initiate_cfunc is None:
                self.RFmxBT_Initiate_cfunc = self._get_library_function("RFmxBT_Initiate")
                self.RFmxBT_Initiate_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_Initiate_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_Initiate_cfunc(vi, selector_string, result_name)

    def RFmxBT_ResetToDefault(self, vi, selector_string):
        """RFmxBT_ResetToDefault."""
        with self._func_lock:
            if self.RFmxBT_ResetToDefault_cfunc is None:
                self.RFmxBT_ResetToDefault_cfunc = self._get_library_function(
                    "RFmxBT_ResetToDefault"
                )
                self.RFmxBT_ResetToDefault_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_ResetToDefault_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ResetToDefault_cfunc(vi, selector_string)

    def RFmxBT_SelectMeasurements(self, vi, selector_string, measurements, enable_all_traces):
        """RFmxBT_SelectMeasurements."""
        with self._func_lock:
            if self.RFmxBT_SelectMeasurements_cfunc is None:
                self.RFmxBT_SelectMeasurements_cfunc = self._get_library_function(
                    "RFmxBT_SelectMeasurements"
                )
                self.RFmxBT_SelectMeasurements_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_uint32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_SelectMeasurements_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SelectMeasurements_cfunc(
            vi, selector_string, measurements, enable_all_traces
        )

    def RFmxBT_WaitForMeasurementComplete(self, vi, selector_string, timeout):
        """RFmxBT_WaitForMeasurementComplete."""
        with self._func_lock:
            if self.RFmxBT_WaitForMeasurementComplete_cfunc is None:
                self.RFmxBT_WaitForMeasurementComplete_cfunc = self._get_library_function(
                    "RFmxBT_WaitForMeasurementComplete"
                )
                self.RFmxBT_WaitForMeasurementComplete_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxBT_WaitForMeasurementComplete_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_WaitForMeasurementComplete_cfunc(vi, selector_string, timeout)

    def RFmxBT_TXPCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxBT_TXPCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_TXPCfgAveraging_cfunc is None:
                self.RFmxBT_TXPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_TXPCfgAveraging"
                )
                self.RFmxBT_TXPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_TXPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_TXPCfgBurstSynchronizationType(
        self, vi, selector_string, burst_synchronization_type
    ):
        """RFmxBT_TXPCfgBurstSynchronizationType."""
        with self._func_lock:
            if self.RFmxBT_TXPCfgBurstSynchronizationType_cfunc is None:
                self.RFmxBT_TXPCfgBurstSynchronizationType_cfunc = self._get_library_function(
                    "RFmxBT_TXPCfgBurstSynchronizationType"
                )
                self.RFmxBT_TXPCfgBurstSynchronizationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_TXPCfgBurstSynchronizationType_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPCfgBurstSynchronizationType_cfunc(
            vi, selector_string, burst_synchronization_type
        )

    def RFmxBT_ModAccCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxBT_ModAccCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_ModAccCfgAveraging_cfunc is None:
                self.RFmxBT_ModAccCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_ModAccCfgAveraging"
                )
                self.RFmxBT_ModAccCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_ModAccCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_ModAccCfgBurstSynchronizationType(
        self, vi, selector_string, burst_synchronization_type
    ):
        """RFmxBT_ModAccCfgBurstSynchronizationType."""
        with self._func_lock:
            if self.RFmxBT_ModAccCfgBurstSynchronizationType_cfunc is None:
                self.RFmxBT_ModAccCfgBurstSynchronizationType_cfunc = self._get_library_function(
                    "RFmxBT_ModAccCfgBurstSynchronizationType"
                )
                self.RFmxBT_ModAccCfgBurstSynchronizationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_ModAccCfgBurstSynchronizationType_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccCfgBurstSynchronizationType_cfunc(
            vi, selector_string, burst_synchronization_type
        )

    def RFmxBT_20dBBandwidthCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count
    ):
        """RFmxBT_20dBBandwidthCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_20dBBandwidthCfgAveraging_cfunc is None:
                self.RFmxBT_20dBBandwidthCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_20dBBandwidthCfgAveraging"
                )
                self.RFmxBT_20dBBandwidthCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_20dBBandwidthCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_20dBBandwidthCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_FrequencyRangeCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count
    ):
        """RFmxBT_FrequencyRangeCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_FrequencyRangeCfgAveraging_cfunc is None:
                self.RFmxBT_FrequencyRangeCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_FrequencyRangeCfgAveraging"
                )
                self.RFmxBT_FrequencyRangeCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_FrequencyRangeCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_FrequencyRangeCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_FrequencyRangeCfgSpan(self, vi, selector_string, span):
        """RFmxBT_FrequencyRangeCfgSpan."""
        with self._func_lock:
            if self.RFmxBT_FrequencyRangeCfgSpan_cfunc is None:
                self.RFmxBT_FrequencyRangeCfgSpan_cfunc = self._get_library_function(
                    "RFmxBT_FrequencyRangeCfgSpan"
                )
                self.RFmxBT_FrequencyRangeCfgSpan_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxBT_FrequencyRangeCfgSpan_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_FrequencyRangeCfgSpan_cfunc(vi, selector_string, span)

    def RFmxBT_ACPCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxBT_ACPCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_ACPCfgAveraging_cfunc is None:
                self.RFmxBT_ACPCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_ACPCfgAveraging"
                )
                self.RFmxBT_ACPCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_ACPCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_ACPCfgBurstSynchronizationType(
        self, vi, selector_string, burst_synchronization_type
    ):
        """RFmxBT_ACPCfgBurstSynchronizationType."""
        with self._func_lock:
            if self.RFmxBT_ACPCfgBurstSynchronizationType_cfunc is None:
                self.RFmxBT_ACPCfgBurstSynchronizationType_cfunc = self._get_library_function(
                    "RFmxBT_ACPCfgBurstSynchronizationType"
                )
                self.RFmxBT_ACPCfgBurstSynchronizationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_ACPCfgBurstSynchronizationType_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPCfgBurstSynchronizationType_cfunc(
            vi, selector_string, burst_synchronization_type
        )

    def RFmxBT_ACPCfgNumberOfOffsets(self, vi, selector_string, number_of_offsets):
        """RFmxBT_ACPCfgNumberOfOffsets."""
        with self._func_lock:
            if self.RFmxBT_ACPCfgNumberOfOffsets_cfunc is None:
                self.RFmxBT_ACPCfgNumberOfOffsets_cfunc = self._get_library_function(
                    "RFmxBT_ACPCfgNumberOfOffsets"
                )
                self.RFmxBT_ACPCfgNumberOfOffsets_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_ACPCfgNumberOfOffsets_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPCfgNumberOfOffsets_cfunc(vi, selector_string, number_of_offsets)

    def RFmxBT_ACPCfgOffsetChannelMode(self, vi, selector_string, offset_channel_mode):
        """RFmxBT_ACPCfgOffsetChannelMode."""
        with self._func_lock:
            if self.RFmxBT_ACPCfgOffsetChannelMode_cfunc is None:
                self.RFmxBT_ACPCfgOffsetChannelMode_cfunc = self._get_library_function(
                    "RFmxBT_ACPCfgOffsetChannelMode"
                )
                self.RFmxBT_ACPCfgOffsetChannelMode_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_ACPCfgOffsetChannelMode_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPCfgOffsetChannelMode_cfunc(vi, selector_string, offset_channel_mode)

    def RFmxBT_PowerRampCfgAveraging(self, vi, selector_string, averaging_enabled, averaging_count):
        """RFmxBT_PowerRampCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_PowerRampCfgAveraging_cfunc is None:
                self.RFmxBT_PowerRampCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_PowerRampCfgAveraging"
                )
                self.RFmxBT_PowerRampCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_PowerRampCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_PowerRampCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_PowerRampCfgBurstSynchronizationType(
        self, vi, selector_string, burst_synchronization_type
    ):
        """RFmxBT_PowerRampCfgBurstSynchronizationType."""
        with self._func_lock:
            if self.RFmxBT_PowerRampCfgBurstSynchronizationType_cfunc is None:
                self.RFmxBT_PowerRampCfgBurstSynchronizationType_cfunc = self._get_library_function(
                    "RFmxBT_PowerRampCfgBurstSynchronizationType"
                )
                self.RFmxBT_PowerRampCfgBurstSynchronizationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_PowerRampCfgBurstSynchronizationType_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_PowerRampCfgBurstSynchronizationType_cfunc(
            vi, selector_string, burst_synchronization_type
        )

    def RFmxBT_ModSpectrumCfgAveraging(
        self, vi, selector_string, averaging_enabled, averaging_count
    ):
        """RFmxBT_ModSpectrumCfgAveraging."""
        with self._func_lock:
            if self.RFmxBT_ModSpectrumCfgAveraging_cfunc is None:
                self.RFmxBT_ModSpectrumCfgAveraging_cfunc = self._get_library_function(
                    "RFmxBT_ModSpectrumCfgAveraging"
                )
                self.RFmxBT_ModSpectrumCfgAveraging_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_ModSpectrumCfgAveraging_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModSpectrumCfgAveraging_cfunc(
            vi, selector_string, averaging_enabled, averaging_count
        )

    def RFmxBT_ModSpectrumCfgBurstSynchronizationType(
        self, vi, selector_string, burst_synchronization_type
    ):
        """RFmxBT_ModSpectrumCfgBurstSynchronizationType."""
        with self._func_lock:
            if self.RFmxBT_ModSpectrumCfgBurstSynchronizationType_cfunc is None:
                self.RFmxBT_ModSpectrumCfgBurstSynchronizationType_cfunc = (
                    self._get_library_function("RFmxBT_ModSpectrumCfgBurstSynchronizationType")
                )
                self.RFmxBT_ModSpectrumCfgBurstSynchronizationType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_ModSpectrumCfgBurstSynchronizationType_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModSpectrumCfgBurstSynchronizationType_cfunc(
            vi, selector_string, burst_synchronization_type
        )

    def RFmxBT_CfgChannelNumber(self, vi, selector_string, channel_number):
        """RFmxBT_CfgChannelNumber."""
        with self._func_lock:
            if self.RFmxBT_CfgChannelNumber_cfunc is None:
                self.RFmxBT_CfgChannelNumber_cfunc = self._get_library_function(
                    "RFmxBT_CfgChannelNumber"
                )
                self.RFmxBT_CfgChannelNumber_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgChannelNumber_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgChannelNumber_cfunc(vi, selector_string, channel_number)

    def RFmxBT_CfgDataRate(self, vi, selector_string, data_rate):
        """RFmxBT_CfgDataRate."""
        with self._func_lock:
            if self.RFmxBT_CfgDataRate_cfunc is None:
                self.RFmxBT_CfgDataRate_cfunc = self._get_library_function("RFmxBT_CfgDataRate")
                self.RFmxBT_CfgDataRate_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgDataRate_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgDataRate_cfunc(vi, selector_string, data_rate)

    def RFmxBT_CfgExternalAttenuation(self, vi, selector_string, external_attenuation):
        """RFmxBT_CfgExternalAttenuation."""
        with self._func_lock:
            if self.RFmxBT_CfgExternalAttenuation_cfunc is None:
                self.RFmxBT_CfgExternalAttenuation_cfunc = self._get_library_function(
                    "RFmxBT_CfgExternalAttenuation"
                )
                self.RFmxBT_CfgExternalAttenuation_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxBT_CfgExternalAttenuation_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgExternalAttenuation_cfunc(vi, selector_string, external_attenuation)

    def RFmxBT_CfgFrequency(self, vi, selector_string, center_frequency):
        """RFmxBT_CfgFrequency."""
        with self._func_lock:
            if self.RFmxBT_CfgFrequency_cfunc is None:
                self.RFmxBT_CfgFrequency_cfunc = self._get_library_function("RFmxBT_CfgFrequency")
                self.RFmxBT_CfgFrequency_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxBT_CfgFrequency_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgFrequency_cfunc(vi, selector_string, center_frequency)

    def RFmxBT_CfgLEDirectionFinding(
        self, vi, selector_string, direction_finding_mode, cte_length, cte_slot_duration
    ):
        """RFmxBT_CfgLEDirectionFinding."""
        with self._func_lock:
            if self.RFmxBT_CfgLEDirectionFinding_cfunc is None:
                self.RFmxBT_CfgLEDirectionFinding_cfunc = self._get_library_function(
                    "RFmxBT_CfgLEDirectionFinding"
                )
                self.RFmxBT_CfgLEDirectionFinding_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxBT_CfgLEDirectionFinding_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgLEDirectionFinding_cfunc(
            vi, selector_string, direction_finding_mode, cte_length, cte_slot_duration
        )

    def RFmxBT_CfgPacketType(self, vi, selector_string, packet_type):
        """RFmxBT_CfgPacketType."""
        with self._func_lock:
            if self.RFmxBT_CfgPacketType_cfunc is None:
                self.RFmxBT_CfgPacketType_cfunc = self._get_library_function("RFmxBT_CfgPacketType")
                self.RFmxBT_CfgPacketType_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgPacketType_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgPacketType_cfunc(vi, selector_string, packet_type)

    def RFmxBT_CfgPayloadBitPattern(self, vi, selector_string, payload_bit_pattern):
        """RFmxBT_CfgPayloadBitPattern."""
        with self._func_lock:
            if self.RFmxBT_CfgPayloadBitPattern_cfunc is None:
                self.RFmxBT_CfgPayloadBitPattern_cfunc = self._get_library_function(
                    "RFmxBT_CfgPayloadBitPattern"
                )
                self.RFmxBT_CfgPayloadBitPattern_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgPayloadBitPattern_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgPayloadBitPattern_cfunc(vi, selector_string, payload_bit_pattern)

    def RFmxBT_CfgPayloadLength(self, vi, selector_string, payload_length_mode, payload_length):
        """RFmxBT_CfgPayloadLength."""
        with self._func_lock:
            if self.RFmxBT_CfgPayloadLength_cfunc is None:
                self.RFmxBT_CfgPayloadLength_cfunc = self._get_library_function(
                    "RFmxBT_CfgPayloadLength"
                )
                self.RFmxBT_CfgPayloadLength_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.c_int32,
                ]
                self.RFmxBT_CfgPayloadLength_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgPayloadLength_cfunc(
            vi, selector_string, payload_length_mode, payload_length
        )

    def RFmxBT_CfgReferenceLevel(self, vi, selector_string, reference_level):
        """RFmxBT_CfgReferenceLevel."""
        with self._func_lock:
            if self.RFmxBT_CfgReferenceLevel_cfunc is None:
                self.RFmxBT_CfgReferenceLevel_cfunc = self._get_library_function(
                    "RFmxBT_CfgReferenceLevel"
                )
                self.RFmxBT_CfgReferenceLevel_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                ]
                self.RFmxBT_CfgReferenceLevel_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgReferenceLevel_cfunc(vi, selector_string, reference_level)

    def RFmxBT_CfgRF(
        self, vi, selector_string, center_frequency, reference_level, external_attenuation
    ):
        """RFmxBT_CfgRF."""
        with self._func_lock:
            if self.RFmxBT_CfgRF_cfunc is None:
                self.RFmxBT_CfgRF_cfunc = self._get_library_function("RFmxBT_CfgRF")
                self.RFmxBT_CfgRF_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.c_double,
                    ctypes.c_double,
                ]
                self.RFmxBT_CfgRF_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CfgRF_cfunc(
            vi, selector_string, center_frequency, reference_level, external_attenuation
        )

    def RFmxBT_TXPFetchEDRPowers(
        self,
        vi,
        selector_string,
        timeout,
        edr_gfsk_average_power_mean,
        edr_dpsk_average_power_mean,
        edr_dpsk_gfsk_average_power_ratio_mean,
    ):
        """RFmxBT_TXPFetchEDRPowers."""
        with self._func_lock:
            if self.RFmxBT_TXPFetchEDRPowers_cfunc is None:
                self.RFmxBT_TXPFetchEDRPowers_cfunc = self._get_library_function(
                    "RFmxBT_TXPFetchEDRPowers"
                )
                self.RFmxBT_TXPFetchEDRPowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_TXPFetchEDRPowers_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPFetchEDRPowers_cfunc(
            vi,
            selector_string,
            timeout,
            edr_gfsk_average_power_mean,
            edr_dpsk_average_power_mean,
            edr_dpsk_gfsk_average_power_ratio_mean,
        )

    def RFmxBT_TXPFetchLECTEReferencePeriodPowers(
        self,
        vi,
        selector_string,
        timeout,
        reference_period_average_power_mean,
        reference_period_peak_absolute_power_deviation_maximum,
    ):
        """RFmxBT_TXPFetchLECTEReferencePeriodPowers."""
        with self._func_lock:
            if self.RFmxBT_TXPFetchLECTEReferencePeriodPowers_cfunc is None:
                self.RFmxBT_TXPFetchLECTEReferencePeriodPowers_cfunc = self._get_library_function(
                    "RFmxBT_TXPFetchLECTEReferencePeriodPowers"
                )
                self.RFmxBT_TXPFetchLECTEReferencePeriodPowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_TXPFetchLECTEReferencePeriodPowers_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPFetchLECTEReferencePeriodPowers_cfunc(
            vi,
            selector_string,
            timeout,
            reference_period_average_power_mean,
            reference_period_peak_absolute_power_deviation_maximum,
        )

    def RFmxBT_TXPFetchLECTETransmitSlotPowers(
        self,
        vi,
        selector_string,
        timeout,
        transmit_slot_average_power_mean,
        transmit_slot_peak_absolute_power_deviation_maximum,
    ):
        """RFmxBT_TXPFetchLECTETransmitSlotPowers."""
        with self._func_lock:
            if self.RFmxBT_TXPFetchLECTETransmitSlotPowers_cfunc is None:
                self.RFmxBT_TXPFetchLECTETransmitSlotPowers_cfunc = self._get_library_function(
                    "RFmxBT_TXPFetchLECTETransmitSlotPowers"
                )
                self.RFmxBT_TXPFetchLECTETransmitSlotPowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_TXPFetchLECTETransmitSlotPowers_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPFetchLECTETransmitSlotPowers_cfunc(
            vi,
            selector_string,
            timeout,
            transmit_slot_average_power_mean,
            transmit_slot_peak_absolute_power_deviation_maximum,
        )

    def RFmxBT_TXPFetchPowers(
        self,
        vi,
        selector_string,
        timeout,
        average_power_mean,
        average_power_maximum,
        average_power_minimum,
        peak_to_average_power_ratio_maximum,
    ):
        """RFmxBT_TXPFetchPowers."""
        with self._func_lock:
            if self.RFmxBT_TXPFetchPowers_cfunc is None:
                self.RFmxBT_TXPFetchPowers_cfunc = self._get_library_function(
                    "RFmxBT_TXPFetchPowers"
                )
                self.RFmxBT_TXPFetchPowers_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_TXPFetchPowers_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPFetchPowers_cfunc(
            vi,
            selector_string,
            timeout,
            average_power_mean,
            average_power_maximum,
            average_power_minimum,
            peak_to_average_power_ratio_maximum,
        )

    def RFmxBT_ModAccFetchDEVM(
        self,
        vi,
        selector_string,
        timeout,
        peak_rms_devm_maximum,
        peak_devm_maximum,
        ninetynine_percent_devm,
    ):
        """RFmxBT_ModAccFetchDEVM."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDEVM_cfunc is None:
                self.RFmxBT_ModAccFetchDEVM_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDEVM"
                )
                self.RFmxBT_ModAccFetchDEVM_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchDEVM_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDEVM_cfunc(
            vi,
            selector_string,
            timeout,
            peak_rms_devm_maximum,
            peak_devm_maximum,
            ninetynine_percent_devm,
        )

    def RFmxBT_ModAccFetchDEVMMagnitudeError(
        self,
        vi,
        selector_string,
        timeout,
        average_rms_magnitude_error_mean,
        peak_rms_magnitude_error_maximum,
    ):
        """RFmxBT_ModAccFetchDEVMMagnitudeError."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDEVMMagnitudeError_cfunc is None:
                self.RFmxBT_ModAccFetchDEVMMagnitudeError_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDEVMMagnitudeError"
                )
                self.RFmxBT_ModAccFetchDEVMMagnitudeError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchDEVMMagnitudeError_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDEVMMagnitudeError_cfunc(
            vi,
            selector_string,
            timeout,
            average_rms_magnitude_error_mean,
            peak_rms_magnitude_error_maximum,
        )

    def RFmxBT_ModAccFetchDEVMPhaseError(
        self,
        vi,
        selector_string,
        timeout,
        average_rms_phase_error_mean,
        peak_rms_phase_error_maximum,
    ):
        """RFmxBT_ModAccFetchDEVMPhaseError."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDEVMPhaseError_cfunc is None:
                self.RFmxBT_ModAccFetchDEVMPhaseError_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDEVMPhaseError"
                )
                self.RFmxBT_ModAccFetchDEVMPhaseError_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchDEVMPhaseError_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDEVMPhaseError_cfunc(
            vi, selector_string, timeout, average_rms_phase_error_mean, peak_rms_phase_error_maximum
        )

    def RFmxBT_ModAccFetchDf1(self, vi, selector_string, timeout, df1avg_maximum, df1avg_minimum):
        """RFmxBT_ModAccFetchDf1."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDf1_cfunc is None:
                self.RFmxBT_ModAccFetchDf1_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDf1"
                )
                self.RFmxBT_ModAccFetchDf1_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchDf1_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDf1_cfunc(
            vi, selector_string, timeout, df1avg_maximum, df1avg_minimum
        )

    def RFmxBT_ModAccFetchDf2(
        self,
        vi,
        selector_string,
        timeout,
        df2avg_minimum,
        percentage_of_symbols_above_df2max_threshold,
    ):
        """RFmxBT_ModAccFetchDf2."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDf2_cfunc is None:
                self.RFmxBT_ModAccFetchDf2_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDf2"
                )
                self.RFmxBT_ModAccFetchDf2_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchDf2_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDf2_cfunc(
            vi,
            selector_string,
            timeout,
            df2avg_minimum,
            percentage_of_symbols_above_df2max_threshold,
        )

    def RFmxBT_ModAccFetchFrequencyErrorBR(
        self,
        vi,
        selector_string,
        timeout,
        initial_frequency_error_maximum,
        peak_frequency_drift_maximum,
        peak_frequency_drift_rate_maximum,
    ):
        """RFmxBT_ModAccFetchFrequencyErrorBR."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyErrorBR_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyErrorBR_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchFrequencyErrorBR"
                )
                self.RFmxBT_ModAccFetchFrequencyErrorBR_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchFrequencyErrorBR_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyErrorBR_cfunc(
            vi,
            selector_string,
            timeout,
            initial_frequency_error_maximum,
            peak_frequency_drift_maximum,
            peak_frequency_drift_rate_maximum,
        )

    def RFmxBT_ModAccFetchFrequencyErrorEDR(
        self,
        vi,
        selector_string,
        timeout,
        header_frequency_error_wi_maximum,
        peak_frequency_error_wi_plus_w0_maximum,
        peak_frequency_error_w0_maximum,
    ):
        """RFmxBT_ModAccFetchFrequencyErrorEDR."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyErrorEDR_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyErrorEDR_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchFrequencyErrorEDR"
                )
                self.RFmxBT_ModAccFetchFrequencyErrorEDR_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchFrequencyErrorEDR_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyErrorEDR_cfunc(
            vi,
            selector_string,
            timeout,
            header_frequency_error_wi_maximum,
            peak_frequency_error_wi_plus_w0_maximum,
            peak_frequency_error_w0_maximum,
        )

    def RFmxBT_ModAccFetchFrequencyErrorLE(
        self,
        vi,
        selector_string,
        timeout,
        peak_frequency_error_maximum,
        initial_frequency_drift_maximum,
        peak_frequency_drift_maximum,
        peak_frequency_drift_rate_maximum,
    ):
        """RFmxBT_ModAccFetchFrequencyErrorLE."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyErrorLE_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyErrorLE_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchFrequencyErrorLE"
                )
                self.RFmxBT_ModAccFetchFrequencyErrorLE_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ModAccFetchFrequencyErrorLE_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyErrorLE_cfunc(
            vi,
            selector_string,
            timeout,
            peak_frequency_error_maximum,
            initial_frequency_drift_maximum,
            peak_frequency_drift_maximum,
            peak_frequency_drift_rate_maximum,
        )

    def RFmxBT_20dBBandwidthFetchMeasurement(
        self, vi, selector_string, timeout, peak_power, bandwidth, high_frequency, low_frequency
    ):
        """RFmxBT_20dBBandwidthFetchMeasurement."""
        with self._func_lock:
            if self.RFmxBT_20dBBandwidthFetchMeasurement_cfunc is None:
                self.RFmxBT_20dBBandwidthFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxBT_20dBBandwidthFetchMeasurement"
                )
                self.RFmxBT_20dBBandwidthFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_20dBBandwidthFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_20dBBandwidthFetchMeasurement_cfunc(
            vi, selector_string, timeout, peak_power, bandwidth, high_frequency, low_frequency
        )

    def RFmxBT_FrequencyRangeFetchMeasurement(
        self, vi, selector_string, timeout, high_frequency, low_frequency
    ):
        """RFmxBT_FrequencyRangeFetchMeasurement."""
        with self._func_lock:
            if self.RFmxBT_FrequencyRangeFetchMeasurement_cfunc is None:
                self.RFmxBT_FrequencyRangeFetchMeasurement_cfunc = self._get_library_function(
                    "RFmxBT_FrequencyRangeFetchMeasurement"
                )
                self.RFmxBT_FrequencyRangeFetchMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_FrequencyRangeFetchMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_FrequencyRangeFetchMeasurement_cfunc(
            vi, selector_string, timeout, high_frequency, low_frequency
        )

    def RFmxBT_ACPFetchMeasurementStatus(self, vi, selector_string, timeout, measurement_status):
        """RFmxBT_ACPFetchMeasurementStatus."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchMeasurementStatus_cfunc is None:
                self.RFmxBT_ACPFetchMeasurementStatus_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchMeasurementStatus"
                )
                self.RFmxBT_ACPFetchMeasurementStatus_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ACPFetchMeasurementStatus_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchMeasurementStatus_cfunc(
            vi, selector_string, timeout, measurement_status
        )

    def RFmxBT_ACPFetchOffsetMeasurement(
        self,
        vi,
        selector_string,
        timeout,
        lower_absolute_power,
        upper_absolute_power,
        lower_relative_power,
        upper_relative_power,
        lower_margin,
        upper_margin,
    ):
        """RFmxBT_ACPFetchOffsetMeasurement."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchOffsetMeasurement_cfunc is None:
                self.RFmxBT_ACPFetchOffsetMeasurement_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchOffsetMeasurement"
                )
                self.RFmxBT_ACPFetchOffsetMeasurement_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ACPFetchOffsetMeasurement_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchOffsetMeasurement_cfunc(
            vi,
            selector_string,
            timeout,
            lower_absolute_power,
            upper_absolute_power,
            lower_relative_power,
            upper_relative_power,
            lower_margin,
            upper_margin,
        )

    def RFmxBT_ACPFetchReferenceChannelPower(
        self, vi, selector_string, timeout, reference_channel_power
    ):
        """RFmxBT_ACPFetchReferenceChannelPower."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchReferenceChannelPower_cfunc is None:
                self.RFmxBT_ACPFetchReferenceChannelPower_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchReferenceChannelPower"
                )
                self.RFmxBT_ACPFetchReferenceChannelPower_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                ]
                self.RFmxBT_ACPFetchReferenceChannelPower_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchReferenceChannelPower_cfunc(
            vi, selector_string, timeout, reference_channel_power
        )

    def RFmxBT_TXPFetchLECTETransmitSlotPowersArray(
        self,
        vi,
        selector_string,
        timeout,
        transmit_slot_average_power_mean,
        transmit_slot_peak_absolute_power_deviation_maximum,
        array_size,
        actual_array_size,
    ):
        """RFmxBT_TXPFetchLECTETransmitSlotPowersArray."""
        with self._func_lock:
            if self.RFmxBT_TXPFetchLECTETransmitSlotPowersArray_cfunc is None:
                self.RFmxBT_TXPFetchLECTETransmitSlotPowersArray_cfunc = self._get_library_function(
                    "RFmxBT_TXPFetchLECTETransmitSlotPowersArray"
                )
                self.RFmxBT_TXPFetchLECTETransmitSlotPowersArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_TXPFetchLECTETransmitSlotPowersArray_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPFetchLECTETransmitSlotPowersArray_cfunc(
            vi,
            selector_string,
            timeout,
            transmit_slot_average_power_mean,
            transmit_slot_peak_absolute_power_deviation_maximum,
            array_size,
            actual_array_size,
        )

    def RFmxBT_TXPFetchPowerTrace(
        self, vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
    ):
        """RFmxBT_TXPFetchPowerTrace."""
        with self._func_lock:
            if self.RFmxBT_TXPFetchPowerTrace_cfunc is None:
                self.RFmxBT_TXPFetchPowerTrace_cfunc = self._get_library_function(
                    "RFmxBT_TXPFetchPowerTrace"
                )
                self.RFmxBT_TXPFetchPowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_TXPFetchPowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_TXPFetchPowerTrace_cfunc(
            vi, selector_string, timeout, x0, dx, power, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchConstellationTrace(
        self, vi, selector_string, timeout, constellation, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchConstellationTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchConstellationTrace_cfunc is None:
                self.RFmxBT_ModAccFetchConstellationTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchConstellationTrace"
                )
                self.RFmxBT_ModAccFetchConstellationTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(_custom_types.ComplexSingle),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchConstellationTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchConstellationTrace_cfunc(
            vi, selector_string, timeout, constellation, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchCSDetrendedPhaseTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        cs_detrended_phase,
        array_size,
        actual_array_size,
    ):
        """RFmxBT_ModAccFetchCSDetrendedPhaseTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchCSDetrendedPhaseTrace_cfunc is None:
                self.RFmxBT_ModAccFetchCSDetrendedPhaseTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchCSDetrendedPhaseTrace"
                )
                self.RFmxBT_ModAccFetchCSDetrendedPhaseTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchCSDetrendedPhaseTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchCSDetrendedPhaseTrace_cfunc(
            vi, selector_string, timeout, x0, dx, cs_detrended_phase, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchCSToneTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        cs_tone_amplitude,
        cs_tone_phase,
        array_size,
        actual_array_size,
    ):
        """RFmxBT_ModAccFetchCSToneTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchCSToneTrace_cfunc is None:
                self.RFmxBT_ModAccFetchCSToneTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchCSToneTrace"
                )
                self.RFmxBT_ModAccFetchCSToneTrace_cfunc.argtypes = [
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
                self.RFmxBT_ModAccFetchCSToneTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchCSToneTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            cs_tone_amplitude,
            cs_tone_phase,
            array_size,
            actual_array_size,
        )

    def RFmxBT_ModAccFetchDemodulatedBitTrace(
        self, vi, selector_string, timeout, demodulated_bits, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchDemodulatedBitTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDemodulatedBitTrace_cfunc is None:
                self.RFmxBT_ModAccFetchDemodulatedBitTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDemodulatedBitTrace"
                )
                self.RFmxBT_ModAccFetchDemodulatedBitTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_int8),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchDemodulatedBitTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDemodulatedBitTrace_cfunc(
            vi, selector_string, timeout, demodulated_bits, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchDEVMPerSymbolTrace(
        self, vi, selector_string, timeout, devm_per_symbol, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchDEVMPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDEVMPerSymbolTrace_cfunc is None:
                self.RFmxBT_ModAccFetchDEVMPerSymbolTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDEVMPerSymbolTrace"
                )
                self.RFmxBT_ModAccFetchDEVMPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchDEVMPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDEVMPerSymbolTrace_cfunc(
            vi, selector_string, timeout, devm_per_symbol, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchEVMPerSymbolTrace(
        self, vi, selector_string, timeout, evm_per_symbol, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchEVMPerSymbolTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchEVMPerSymbolTrace_cfunc is None:
                self.RFmxBT_ModAccFetchEVMPerSymbolTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchEVMPerSymbolTrace"
                )
                self.RFmxBT_ModAccFetchEVMPerSymbolTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchEVMPerSymbolTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchEVMPerSymbolTrace_cfunc(
            vi, selector_string, timeout, evm_per_symbol, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchDf1maxTrace(
        self, vi, selector_string, timeout, time, df1max, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchDf1maxTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDf1maxTrace_cfunc is None:
                self.RFmxBT_ModAccFetchDf1maxTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDf1maxTrace"
                )
                self.RFmxBT_ModAccFetchDf1maxTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchDf1maxTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDf1maxTrace_cfunc(
            vi, selector_string, timeout, time, df1max, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchDf2maxTrace(
        self, vi, selector_string, timeout, time, df2max, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchDf2maxTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDf2maxTrace_cfunc is None:
                self.RFmxBT_ModAccFetchDf2maxTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDf2maxTrace"
                )
                self.RFmxBT_ModAccFetchDf2maxTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchDf2maxTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDf2maxTrace_cfunc(
            vi, selector_string, timeout, time, df2max, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchDf4avgTrace(
        self, vi, selector_string, timeout, time, df4avg, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchDf4avgTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchDf4avgTrace_cfunc is None:
                self.RFmxBT_ModAccFetchDf4avgTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchDf4avgTrace"
                )
                self.RFmxBT_ModAccFetchDf4avgTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchDf4avgTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchDf4avgTrace_cfunc(
            vi, selector_string, timeout, time, df4avg, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchFrequencyErrorTraceBR(
        self, vi, selector_string, timeout, time, frequency_error, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchFrequencyErrorTraceBR."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyErrorTraceBR_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyErrorTraceBR_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchFrequencyErrorTraceBR"
                )
                self.RFmxBT_ModAccFetchFrequencyErrorTraceBR_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchFrequencyErrorTraceBR_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyErrorTraceBR_cfunc(
            vi, selector_string, timeout, time, frequency_error, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchFrequencyErrorTraceLE(
        self, vi, selector_string, timeout, time, frequency_error, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchFrequencyErrorTraceLE."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyErrorTraceLE_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyErrorTraceLE_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchFrequencyErrorTraceLE"
                )
                self.RFmxBT_ModAccFetchFrequencyErrorTraceLE_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchFrequencyErrorTraceLE_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyErrorTraceLE_cfunc(
            vi, selector_string, timeout, time, frequency_error, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR(
        self,
        vi,
        selector_string,
        timeout,
        time,
        frequency_error_wi_plus_w0,
        array_size,
        actual_array_size,
    ):
        """RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR_cfunc = (
                    self._get_library_function("RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR")
                )
                self.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR_cfunc(
            vi,
            selector_string,
            timeout,
            time,
            frequency_error_wi_plus_w0,
            array_size,
            actual_array_size,
        )

    def RFmxBT_ModAccFetchFrequencyTrace(
        self, vi, selector_string, timeout, x0, dx, frequency, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchFrequencyTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchFrequencyTrace_cfunc is None:
                self.RFmxBT_ModAccFetchFrequencyTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchFrequencyTrace"
                )
                self.RFmxBT_ModAccFetchFrequencyTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchFrequencyTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchFrequencyTrace_cfunc(
            vi, selector_string, timeout, x0, dx, frequency, array_size, actual_array_size
        )

    def RFmxBT_ModAccFetchRMSDEVMTrace(
        self, vi, selector_string, timeout, rms_devm, array_size, actual_array_size
    ):
        """RFmxBT_ModAccFetchRMSDEVMTrace."""
        with self._func_lock:
            if self.RFmxBT_ModAccFetchRMSDEVMTrace_cfunc is None:
                self.RFmxBT_ModAccFetchRMSDEVMTrace_cfunc = self._get_library_function(
                    "RFmxBT_ModAccFetchRMSDEVMTrace"
                )
                self.RFmxBT_ModAccFetchRMSDEVMTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModAccFetchRMSDEVMTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModAccFetchRMSDEVMTrace_cfunc(
            vi, selector_string, timeout, rms_devm, array_size, actual_array_size
        )

    def RFmxBT_20dBBandwidthFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxBT_20dBBandwidthFetchSpectrum."""
        with self._func_lock:
            if self.RFmxBT_20dBBandwidthFetchSpectrum_cfunc is None:
                self.RFmxBT_20dBBandwidthFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxBT_20dBBandwidthFetchSpectrum"
                )
                self.RFmxBT_20dBBandwidthFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_20dBBandwidthFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_20dBBandwidthFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxBT_FrequencyRangeFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxBT_FrequencyRangeFetchSpectrum."""
        with self._func_lock:
            if self.RFmxBT_FrequencyRangeFetchSpectrum_cfunc is None:
                self.RFmxBT_FrequencyRangeFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxBT_FrequencyRangeFetchSpectrum"
                )
                self.RFmxBT_FrequencyRangeFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_FrequencyRangeFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_FrequencyRangeFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxBT_ACPFetchAbsolutePowerTrace(
        self, vi, selector_string, timeout, x0, dx, absolute_power, array_size, actual_array_size
    ):
        """RFmxBT_ACPFetchAbsolutePowerTrace."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchAbsolutePowerTrace_cfunc is None:
                self.RFmxBT_ACPFetchAbsolutePowerTrace_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchAbsolutePowerTrace"
                )
                self.RFmxBT_ACPFetchAbsolutePowerTrace_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ACPFetchAbsolutePowerTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchAbsolutePowerTrace_cfunc(
            vi, selector_string, timeout, x0, dx, absolute_power, array_size, actual_array_size
        )

    def RFmxBT_ACPFetchMaskTrace(
        self,
        vi,
        selector_string,
        timeout,
        x0,
        dx,
        limit_with_exception_mask,
        limit_without_exception_mask,
        array_size,
        actual_array_size,
    ):
        """RFmxBT_ACPFetchMaskTrace."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchMaskTrace_cfunc is None:
                self.RFmxBT_ACPFetchMaskTrace_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchMaskTrace"
                )
                self.RFmxBT_ACPFetchMaskTrace_cfunc.argtypes = [
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
                self.RFmxBT_ACPFetchMaskTrace_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchMaskTrace_cfunc(
            vi,
            selector_string,
            timeout,
            x0,
            dx,
            limit_with_exception_mask,
            limit_without_exception_mask,
            array_size,
            actual_array_size,
        )

    def RFmxBT_ACPFetchOffsetMeasurementArray(
        self,
        vi,
        selector_string,
        timeout,
        lower_absolute_power,
        upper_absolute_power,
        lower_relative_power,
        upper_relative_power,
        lower_margin,
        upper_margin,
        array_size,
        actual_array_size,
    ):
        """RFmxBT_ACPFetchOffsetMeasurementArray."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchOffsetMeasurementArray_cfunc is None:
                self.RFmxBT_ACPFetchOffsetMeasurementArray_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchOffsetMeasurementArray"
                )
                self.RFmxBT_ACPFetchOffsetMeasurementArray_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ACPFetchOffsetMeasurementArray_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchOffsetMeasurementArray_cfunc(
            vi,
            selector_string,
            timeout,
            lower_absolute_power,
            upper_absolute_power,
            lower_relative_power,
            upper_relative_power,
            lower_margin,
            upper_margin,
            array_size,
            actual_array_size,
        )

    def RFmxBT_ACPFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxBT_ACPFetchSpectrum."""
        with self._func_lock:
            if self.RFmxBT_ACPFetchSpectrum_cfunc is None:
                self.RFmxBT_ACPFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxBT_ACPFetchSpectrum"
                )
                self.RFmxBT_ACPFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ACPFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ACPFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxBT_ModSpectrumFetchSpectrum(
        self, vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
    ):
        """RFmxBT_ModSpectrumFetchSpectrum."""
        with self._func_lock:
            if self.RFmxBT_ModSpectrumFetchSpectrum_cfunc is None:
                self.RFmxBT_ModSpectrumFetchSpectrum_cfunc = self._get_library_function(
                    "RFmxBT_ModSpectrumFetchSpectrum"
                )
                self.RFmxBT_ModSpectrumFetchSpectrum_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_double,
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_double),
                    ctypes.POINTER(ctypes.c_float),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_ModSpectrumFetchSpectrum_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_ModSpectrumFetchSpectrum_cfunc(
            vi, selector_string, timeout, x0, dx, spectrum, array_size, actual_array_size
        )

    def RFmxBT_CloneSignalConfiguration(self, vi, old_signal_name, new_signal_name):
        """RFmxBT_CloneSignalConfiguration."""
        with self._func_lock:
            if self.RFmxBT_CloneSignalConfiguration_cfunc is None:
                self.RFmxBT_CloneSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxBT_CloneSignalConfiguration"
                )
                self.RFmxBT_CloneSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_CloneSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_CloneSignalConfiguration_cfunc(vi, old_signal_name, new_signal_name)

    def RFmxBT_DeleteSignalConfiguration(self, vi, signal_name):
        """RFmxBT_DeleteSignalConfiguration."""
        with self._func_lock:
            if self.RFmxBT_DeleteSignalConfiguration_cfunc is None:
                self.RFmxBT_DeleteSignalConfiguration_cfunc = self._get_library_function(
                    "RFmxBT_DeleteSignalConfiguration"
                )
                self.RFmxBT_DeleteSignalConfiguration_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                ]
                self.RFmxBT_DeleteSignalConfiguration_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_DeleteSignalConfiguration_cfunc(vi, signal_name)

    def RFmxBT_SendSoftwareEdgeTrigger(self, vi):
        """RFmxBT_SendSoftwareEdgeTrigger."""
        with self._func_lock:
            if self.RFmxBT_SendSoftwareEdgeTrigger_cfunc is None:
                self.RFmxBT_SendSoftwareEdgeTrigger_cfunc = self._get_library_function(
                    "RFmxBT_SendSoftwareEdgeTrigger"
                )
                self.RFmxBT_SendSoftwareEdgeTrigger_cfunc.argtypes = [ctypes.c_uint32]
                self.RFmxBT_SendSoftwareEdgeTrigger_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_SendSoftwareEdgeTrigger_cfunc(vi)

    def RFmxBT_GetAllNamedResultNames(
        self,
        vi,
        selector_string,
        result_names,
        result_names_buffer_size,
        actual_result_names_size,
        default_result_exists,
    ):
        """RFmxBT_GetAllNamedResultNames."""
        with self._func_lock:
            if self.RFmxBT_GetAllNamedResultNames_cfunc is None:
                self.RFmxBT_GetAllNamedResultNames_cfunc = self._get_library_function(
                    "RFmxBT_GetAllNamedResultNames"
                )
                self.RFmxBT_GetAllNamedResultNames_cfunc.argtypes = [
                    ctypes.c_uint32,
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.POINTER(ctypes.c_char),
                    ctypes.c_int32,
                    ctypes.POINTER(ctypes.c_int32),
                    ctypes.POINTER(ctypes.c_int32),
                ]
                self.RFmxBT_GetAllNamedResultNames_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_GetAllNamedResultNames_cfunc(
            vi,
            selector_string,
            result_names,
            result_names_buffer_size,
            actual_result_names_size,
            default_result_exists,
        )

    def RFmxBT_AnalyzeIQ1Waveform(
        self, vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
    ):
        """RFmxBT_AnalyzeIQ1Waveform."""
        with self._func_lock:
            if self.RFmxBT_AnalyzeIQ1Waveform_cfunc is None:
                self.RFmxBT_AnalyzeIQ1Waveform_cfunc = self._get_library_function(
                    "RFmxBT_AnalyzeIQ1Waveform"
                )
                self.RFmxBT_AnalyzeIQ1Waveform_cfunc.argtypes = [
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
                self.RFmxBT_AnalyzeIQ1Waveform_cfunc.restype = ctypes.c_int32
        return self.RFmxBT_AnalyzeIQ1Waveform_cfunc(
            vi, selector_string, result_name, x0, dx, iq, array_size, reset, reserved
        )
