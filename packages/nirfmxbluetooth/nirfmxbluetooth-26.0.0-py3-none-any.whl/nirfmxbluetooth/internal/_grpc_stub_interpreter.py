"""Interpreter for interacting with a gRPC Stub class."""

import ctypes
import os
import sys
import threading
import warnings

import grpc
import numpy

current_file = __file__
absolute_path = os.path.abspath(current_file)
directory = os.path.dirname(absolute_path)
sys.path.append(directory)
import nirfmxbluetooth.enums as enums
import nirfmxbluetooth.errors as errors
import nirfmxbluetooth.internal._custom_types as _custom_types
import nirfmxbluetooth.internal._helper as _helper
import nirfmxbluetooth.internal.nidevice_pb2 as nidevice_grpc_types
import nirfmxbluetooth.internal.nirfmxbluetooth_pb2 as grpc_types
import nirfmxbluetooth.internal.nirfmxbluetooth_pb2_grpc as nirfmxbluetooth_grpc
import nirfmxbluetooth.internal.session_pb2 as session_grpc_types
import nirfmxinstr


class GrpcStubInterpreter(object):
    """Interpreter for interacting with a gRPC Stub class"""

    def __init__(self, grpc_options, session=None, signal_obj=None):
        self._grpc_options = grpc_options
        self._signal_obj = signal_obj
        self._instr_session = session
        self._client = nirfmxbluetooth_grpc.NiRFmxBluetoothStub(grpc_options.grpc_channel)  # type: ignore
        self.set_session_handle()  # type: ignore

    def set_session_handle(self, value=session_grpc_types.Session()):  # type: ignore
        self._vi = value

    def get_session_handle(self):
        return self._vi

    def _invoke(self, func, request, metadata=None, ignore_driver_error=False):
        response = None
        try:
            response = func(request, metadata=metadata)
            error_code = response.status
            error_message = ""
        except grpc.RpcError as rpc_error:
            error_code = None
            error_message = rpc_error.details()
            for entry in rpc_error.trailing_metadata() or []:
                if entry.key == "ni-error":
                    value = (
                        entry.value if isinstance(entry.value, str) else entry.value.decode("utf-8")
                    )
                    try:
                        error_code = int(value)
                    except ValueError:
                        error_message += f"\nError status: {value}"

            grpc_error = rpc_error.code()
            if grpc_error == grpc.StatusCode.NOT_FOUND:
                raise errors.DriverTooOldError() from None  # type: ignore
            elif grpc_error == grpc.StatusCode.INVALID_ARGUMENT:
                raise ValueError(error_message) from None
            elif grpc_error == grpc.StatusCode.UNAVAILABLE:
                error_message = "Failed to connect to server"
            elif grpc_error == grpc.StatusCode.UNIMPLEMENTED:
                error_message = "This operation is not supported by the NI gRPC Device Server being used. Upgrade NI gRPC Device Server."

            if error_code is None:
                raise errors.RpcError(grpc_error, error_message) from None  # type: ignore

        if error_code < 0 and not ignore_driver_error:
            import nirfmxinstr

            raise nirfmxinstr.RFmxError(error_code, error_message)  # type: ignore

        return response

    def get_error_string(self, error_code):
        """Returns the error message."""
        response = self._invoke(
            self._client.GetErrorString,
            grpc_types.GetErrorStringRequest(instrument=self._vi, error_code=error_code),  # type: ignore
        )
        return response.error_description

    def get_error(self):
        """Returns the error code and error message."""
        response = self._invoke(
            self._client.GetError, grpc_types.GetErrorRequest(instrument=self._vi)  # type: ignore
        )
        return response.error_code, response.error_description

    def get_error_description(self, error_code):
        """Returns the error description."""
        try:
            returned_error_code, error_string = self.get_error()  # type: ignore
            if returned_error_code == error_code:
                return error_string
        except errors.Error:
            pass

        try:
            """
            It is expected for get_error to raise when the session is invalid
            Use get_error_string instead. It doesn't require a session.
            """
            error_string = self.get_error_string(error_code)  # type: ignore
            return error_string
        except errors.Error:
            pass
        return "Failed to retrieve error description."

    def reset_attribute(self, selector_string, attribute_id):
        """reset_attribute."""
        response = self._invoke(
            self._client.ResetAttribute,
            grpc_types.ResetAttributeRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.status

    def check_if_current_signal_exists(self):
        """check_if_current_signal_exists."""
        return_value = False
        if not self._signal_obj.signal_configuration_name:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj._default_signal_name_user_visible
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.BT.value
            )
        else:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj.signal_configuration_name
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.BT.value
            )
        return return_value

    def get_attribute_i8(self, selector_string, attribute_id):
        """get_attribute_i8."""
        response = self._invoke(
            self._client.GetAttributeI8,
            grpc_types.GetAttributeI8Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i8(self, selector_string, attribute_id, attr_val):
        """set_attribute_i8."""
        response = self._invoke(
            self._client.SetAttributeI8,
            grpc_types.SetAttributeI8Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i8_array(self, selector_string, attribute_id):
        """get_attribute_i8_array."""
        response = self._invoke(
            self._client.GetAttributeI8Array,
            grpc_types.GetAttributeI8ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i8_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i8_array."""
        response = self._invoke(
            self._client.SetAttributeI8Array,
            grpc_types.SetAttributeI8ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i16(self, selector_string, attribute_id):
        """get_attribute_i16."""
        response = self._invoke(
            self._client.GetAttributeI16,
            grpc_types.GetAttributeI16Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i16(self, selector_string, attribute_id, attr_val):
        """set_attribute_i16."""
        response = self._invoke(
            self._client.SetAttributeI16,
            grpc_types.SetAttributeI16Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i32(self, selector_string, attribute_id):
        """get_attribute_i32."""
        response = self._invoke(
            self._client.GetAttributeI32,
            grpc_types.GetAttributeI32Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val_raw, response.status

    def set_attribute_i32(self, selector_string, attribute_id, attr_val):
        """set_attribute_i32."""
        response = self._invoke(
            self._client.SetAttributeI32,
            grpc_types.SetAttributeI32Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val_raw=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i32_array(self, selector_string, attribute_id):
        """get_attribute_i32_array."""
        response = self._invoke(
            self._client.GetAttributeI32Array,
            grpc_types.GetAttributeI32ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i32_array."""
        response = self._invoke(
            self._client.SetAttributeI32Array,
            grpc_types.SetAttributeI32ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i64(self, selector_string, attribute_id):
        """get_attribute_i64."""
        response = self._invoke(
            self._client.GetAttributeI64,
            grpc_types.GetAttributeI64Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i64(self, selector_string, attribute_id, attr_val):
        """set_attribute_i64."""
        response = self._invoke(
            self._client.SetAttributeI64,
            grpc_types.SetAttributeI64Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i64_array(self, selector_string, attribute_id):
        """get_attribute_i64_array."""
        response = self._invoke(
            self._client.GetAttributeI64Array,
            grpc_types.GetAttributeI64ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i64_array."""
        response = self._invoke(
            self._client.SetAttributeI64Array,
            grpc_types.SetAttributeI64ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u8(self, selector_string, attribute_id):
        """get_attribute_u8."""
        response = self._invoke(
            self._client.GetAttributeU8,
            grpc_types.GetAttributeU8Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u8(self, selector_string, attribute_id, attr_val):
        """set_attribute_u8."""
        response = self._invoke(
            self._client.SetAttributeU8,
            grpc_types.SetAttributeU8Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u8_array(self, selector_string, attribute_id):
        """get_attribute_u8_array."""
        response = self._invoke(
            self._client.GetAttributeU8Array,
            grpc_types.GetAttributeU8ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u8_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u8_array."""
        response = self._invoke(
            self._client.SetAttributeU8Array,
            grpc_types.SetAttributeU8ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u16(self, selector_string, attribute_id):
        """get_attribute_u16."""
        response = self._invoke(
            self._client.GetAttributeU16,
            grpc_types.GetAttributeU16Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u16(self, selector_string, attribute_id, attr_val):
        """set_attribute_u16."""
        response = self._invoke(
            self._client.SetAttributeU16,
            grpc_types.SetAttributeU16Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u32(self, selector_string, attribute_id):
        """get_attribute_u32."""
        response = self._invoke(
            self._client.GetAttributeU32,
            grpc_types.GetAttributeU32Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u32(self, selector_string, attribute_id, attr_val):
        """set_attribute_u32."""
        response = self._invoke(
            self._client.SetAttributeU32,
            grpc_types.SetAttributeU32Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u32_array(self, selector_string, attribute_id):
        """get_attribute_u32_array."""
        response = self._invoke(
            self._client.GetAttributeU32Array,
            grpc_types.GetAttributeU32ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u32_array."""
        response = self._invoke(
            self._client.SetAttributeU32Array,
            grpc_types.SetAttributeU32ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u64_array(self, selector_string, attribute_id):
        """get_attribute_u64_array."""
        response = self._invoke(
            self._client.GetAttributeU64Array,
            grpc_types.GetAttributeU64ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u64_array."""
        response = self._invoke(
            self._client.SetAttributeU64Array,
            grpc_types.SetAttributeU64ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f32(self, selector_string, attribute_id):
        """get_attribute_f32."""
        response = self._invoke(
            self._client.GetAttributeF32,
            grpc_types.GetAttributeF32Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f32(self, selector_string, attribute_id, attr_val):
        """set_attribute_f32."""
        response = self._invoke(
            self._client.SetAttributeF32,
            grpc_types.SetAttributeF32Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f32_array(self, selector_string, attribute_id):
        """get_attribute_f32_array."""
        response = self._invoke(
            self._client.GetAttributeF32Array,
            grpc_types.GetAttributeF32ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_f32_array."""
        response = self._invoke(
            self._client.SetAttributeF32Array,
            grpc_types.SetAttributeF32ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f64(self, selector_string, attribute_id):
        """get_attribute_f64."""
        response = self._invoke(
            self._client.GetAttributeF64,
            grpc_types.GetAttributeF64Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f64(self, selector_string, attribute_id, attr_val):
        """set_attribute_f64."""
        response = self._invoke(
            self._client.SetAttributeF64,
            grpc_types.SetAttributeF64Request(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f64_array(self, selector_string, attribute_id):
        """get_attribute_f64_array."""
        response = self._invoke(
            self._client.GetAttributeF64Array,
            grpc_types.GetAttributeF64ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_f64_array."""
        response = self._invoke(
            self._client.SetAttributeF64Array,
            grpc_types.SetAttributeF64ArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_nicomplexsingle_array(self, selector_string, attribute_id):
        """get_attribute_nicomplexsingle_array."""
        response = self._invoke(
            self._client.GetAttributeNIComplexSingleArray,
            grpc_types.GetAttributeNIComplexSingleArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_nicomplexsingle_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_nicomplexsingle_array."""
        response = self._invoke(
            self._client.SetAttributeNIComplexSingleArray,
            grpc_types.SetAttributeNIComplexSingleArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_nicomplexdouble_array(self, selector_string, attribute_id):
        """get_attribute_nicomplexdouble_array."""
        response = self._invoke(
            self._client.GetAttributeNIComplexDoubleArray,
            grpc_types.GetAttributeNIComplexDoubleArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_nicomplexdouble_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_nicomplexdouble_array."""
        response = self._invoke(
            self._client.SetAttributeNIComplexDoubleArray,
            grpc_types.SetAttributeNIComplexDoubleArrayRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_string(self, selector_string, attribute_id):
        """get_attribute_string."""
        response = self._invoke(
            self._client.GetAttributeString,
            grpc_types.GetAttributeStringRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_string(self, selector_string, attribute_id, attr_val):
        """set_attribute_string."""
        response = self._invoke(
            self._client.SetAttributeString,
            grpc_types.SetAttributeStringRequest(instrument=self._vi, selector_string=selector_string, attribute_id=attribute_id, attr_val_raw=attr_val),  # type: ignore
        )
        return response.status

    def abort_measurements(self, selector_string):
        """abort_measurements."""
        response = self._invoke(
            self._client.AbortMeasurements,
            grpc_types.AbortMeasurementsRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def auto_detect_signal(self, selector_string, timeout):
        """auto_detect_signal."""
        response = self._invoke(
            self._client.AutoDetectSignal,
            grpc_types.AutoDetectSignalRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.status

    def auto_level(self, selector_string, measurement_interval):
        """auto_level."""
        response = self._invoke(
            self._client.AutoLevel,
            grpc_types.AutoLevelRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.reference_level, response.status

    def check_measurement_status(self, selector_string):
        """check_measurement_status."""
        response = self._invoke(
            self._client.CheckMeasurementStatus,
            grpc_types.CheckMeasurementStatusRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return bool(response.is_done), response.status

    def clear_all_named_results(self, selector_string):
        """clear_all_named_results."""
        response = self._invoke(
            self._client.ClearAllNamedResults,
            grpc_types.ClearAllNamedResultsRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def clear_named_result(self, selector_string):
        """clear_named_result."""
        response = self._invoke(
            self._client.ClearNamedResult,
            grpc_types.ClearNamedResultRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def commit(self, selector_string):
        """commit."""
        response = self._invoke(
            self._client.Commit,
            grpc_types.CommitRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def configure_digital_edge_trigger(
        self, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        """configure_digital_edge_trigger."""
        response = self._invoke(
            self._client.CfgDigitalEdgeTrigger,
            grpc_types.CfgDigitalEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, digital_edge_source=digital_edge_source, digital_edge_raw=digital_edge, trigger_delay=trigger_delay, enable_trigger=enable_trigger),  # type: ignore
        )
        return response.status

    def configure_frequency_channel_number(self, selector_string, standard, channel_number):
        """configure_frequency_channel_number."""
        response = self._invoke(
            self._client.CfgFrequencyChannelNumber,
            grpc_types.CfgFrequencyChannelNumberRequest(instrument=self._vi, selector_string=selector_string, standard_raw=standard, channel_number=channel_number),  # type: ignore
        )
        return response.status

    def configure_iq_power_edge_trigger(
        self,
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
        """configure_iq_power_edge_trigger."""
        response = self._invoke(
            self._client.CfgIQPowerEdgeTrigger,
            grpc_types.CfgIQPowerEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, iq_power_edge_source=iq_power_edge_source, iq_power_edge_slope_raw=iq_power_edge_slope, iq_power_edge_level=iq_power_edge_level, trigger_delay=trigger_delay, trigger_min_quiet_time_mode_raw=trigger_min_quiet_time_mode, trigger_min_quiet_time_duration=trigger_min_quiet_time_duration, iq_power_edge_level_type_raw=iq_power_edge_level_type, enable_trigger=enable_trigger),  # type: ignore
        )
        return response.status

    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        """configure_software_edge_trigger."""
        response = self._invoke(
            self._client.CfgSoftwareEdgeTrigger,
            grpc_types.CfgSoftwareEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, trigger_delay=trigger_delay, enable_trigger=enable_trigger),  # type: ignore
        )
        return response.status

    def create_signal_configuration(self, signal_name):
        """create_signal_configuration."""
        response = self._invoke(
            self._client.CreateSignalConfiguration,
            grpc_types.CreateSignalConfigurationRequest(instrument=self._vi, signal_name=signal_name),  # type: ignore
        )
        return response.status

    def disable_trigger(self, selector_string):
        """disable_trigger."""
        response = self._invoke(
            self._client.DisableTrigger,
            grpc_types.DisableTriggerRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def initiate(self, selector_string, result_name):
        """initiate."""
        response = self._invoke(
            self._client.Initiate,
            grpc_types.InitiateRequest(instrument=self._vi, selector_string=selector_string, result_name=result_name),  # type: ignore
        )
        return response.status

    def reset_to_default(self, selector_string):
        """reset_to_default."""
        response = self._invoke(
            self._client.ResetToDefault,
            grpc_types.ResetToDefaultRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def select_measurements(self, selector_string, measurements, enable_all_traces):
        """select_measurements."""
        response = self._invoke(
            self._client.SelectMeasurements,
            grpc_types.SelectMeasurementsRequest(instrument=self._vi, selector_string=selector_string, measurements_raw=measurements, enable_all_traces=enable_all_traces),  # type: ignore
        )
        return response.status

    def wait_for_measurement_complete(self, selector_string, timeout):
        """wait_for_measurement_complete."""
        response = self._invoke(
            self._client.WaitForMeasurementComplete,
            grpc_types.WaitForMeasurementCompleteRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.status

    def txp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """txp_configure_averaging."""
        response = self._invoke(
            self._client.TXPCfgAveraging,
            grpc_types.TXPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def txp_configure_burst_synchronization_type(self, selector_string, burst_synchronization_type):
        """txp_configure_burst_synchronization_type."""
        response = self._invoke(
            self._client.TXPCfgBurstSynchronizationType,
            grpc_types.TXPCfgBurstSynchronizationTypeRequest(instrument=self._vi, selector_string=selector_string, burst_synchronization_type_raw=burst_synchronization_type),  # type: ignore
        )
        return response.status

    def modacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """modacc_configure_averaging."""
        response = self._invoke(
            self._client.ModAccCfgAveraging,
            grpc_types.ModAccCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def modacc_configure_burst_synchronization_type(
        self, selector_string, burst_synchronization_type
    ):
        """modacc_configure_burst_synchronization_type."""
        response = self._invoke(
            self._client.ModAccCfgBurstSynchronizationType,
            grpc_types.ModAccCfgBurstSynchronizationTypeRequest(instrument=self._vi, selector_string=selector_string, burst_synchronization_type_raw=burst_synchronization_type),  # type: ignore
        )
        return response.status

    def twenty_db_bandwidth_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count
    ):
        """twenty_db_bandwidth_configure_averaging."""
        response = self._invoke(
            self._client.TwentydBBandwidthCfgAveraging,
            grpc_types.TwentydBBandwidthCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def frequency_range_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count
    ):
        """frequency_range_configure_averaging."""
        response = self._invoke(
            self._client.FrequencyRangeCfgAveraging,
            grpc_types.FrequencyRangeCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def frequency_range_configure_span(self, selector_string, span):
        """frequency_range_configure_span."""
        response = self._invoke(
            self._client.FrequencyRangeCfgSpan,
            grpc_types.FrequencyRangeCfgSpanRequest(instrument=self._vi, selector_string=selector_string, span=span),  # type: ignore
        )
        return response.status

    def acp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """acp_configure_averaging."""
        response = self._invoke(
            self._client.ACPCfgAveraging,
            grpc_types.ACPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def acp_configure_burst_synchronization_type(self, selector_string, burst_synchronization_type):
        """acp_configure_burst_synchronization_type."""
        response = self._invoke(
            self._client.ACPCfgBurstSynchronizationType,
            grpc_types.ACPCfgBurstSynchronizationTypeRequest(instrument=self._vi, selector_string=selector_string, burst_synchronization_type_raw=burst_synchronization_type),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """acp_configure_number_of_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfOffsets,
            grpc_types.ACPCfgNumberOfOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_offsets=number_of_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_offset_channel_mode(self, selector_string, offset_channel_mode):
        """acp_configure_offset_channel_mode."""
        response = self._invoke(
            self._client.ACPCfgOffsetChannelMode,
            grpc_types.ACPCfgOffsetChannelModeRequest(instrument=self._vi, selector_string=selector_string, offset_channel_mode_raw=offset_channel_mode),  # type: ignore
        )
        return response.status

    def powerramp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """powerramp_configure_averaging."""
        response = self._invoke(
            self._client.PowerRampCfgAveraging,
            grpc_types.PowerRampCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def powerramp_configure_burst_synchronization_type(
        self, selector_string, burst_synchronization_type
    ):
        """powerramp_configure_burst_synchronization_type."""
        response = self._invoke(
            self._client.PowerRampCfgBurstSynchronizationType,
            grpc_types.PowerRampCfgBurstSynchronizationTypeRequest(instrument=self._vi, selector_string=selector_string, burst_synchronization_type_raw=burst_synchronization_type),  # type: ignore
        )
        return response.status

    def modspectrum_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """modspectrum_configure_averaging."""
        response = self._invoke(
            self._client.ModSpectrumCfgAveraging,
            grpc_types.ModSpectrumCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def modspectrum_configure_burst_synchronization_type(
        self, selector_string, burst_synchronization_type
    ):
        """modspectrum_configure_burst_synchronization_type."""
        response = self._invoke(
            self._client.ModSpectrumCfgBurstSynchronizationType,
            grpc_types.ModSpectrumCfgBurstSynchronizationTypeRequest(instrument=self._vi, selector_string=selector_string, burst_synchronization_type_raw=burst_synchronization_type),  # type: ignore
        )
        return response.status

    def configure_channel_number(self, selector_string, channel_number):
        """configure_channel_number."""
        response = self._invoke(
            self._client.CfgChannelNumber,
            grpc_types.CfgChannelNumberRequest(instrument=self._vi, selector_string=selector_string, channel_number=channel_number),  # type: ignore
        )
        return response.status

    def configure_data_rate(self, selector_string, data_rate):
        """configure_data_rate."""
        response = self._invoke(
            self._client.CfgDataRate,
            grpc_types.CfgDataRateRequest(instrument=self._vi, selector_string=selector_string, data_rate=data_rate),  # type: ignore
        )
        return response.status

    def configure_external_attenuation(self, selector_string, external_attenuation):
        """configure_external_attenuation."""
        response = self._invoke(
            self._client.CfgExternalAttenuation,
            grpc_types.CfgExternalAttenuationRequest(instrument=self._vi, selector_string=selector_string, external_attenuation=external_attenuation),  # type: ignore
        )
        return response.status

    def configure_frequency(self, selector_string, center_frequency):
        """configure_frequency."""
        response = self._invoke(
            self._client.CfgFrequency,
            grpc_types.CfgFrequencyRequest(instrument=self._vi, selector_string=selector_string, center_frequency=center_frequency),  # type: ignore
        )
        return response.status

    def configure_le_direction_finding(
        self, selector_string, direction_finding_mode, cte_length, cte_slot_duration
    ):
        """configure_le_direction_finding."""
        response = self._invoke(
            self._client.CfgLEDirectionFinding,
            grpc_types.CfgLEDirectionFindingRequest(instrument=self._vi, selector_string=selector_string, direction_finding_mode_raw=direction_finding_mode, cte_length=cte_length, cte_slot_duration=cte_slot_duration),  # type: ignore
        )
        return response.status

    def configure_packet_type(self, selector_string, packet_type):
        """configure_packet_type."""
        response = self._invoke(
            self._client.CfgPacketType,
            grpc_types.CfgPacketTypeRequest(instrument=self._vi, selector_string=selector_string, packet_type_raw=packet_type),  # type: ignore
        )
        return response.status

    def configure_payload_bit_pattern(self, selector_string, payload_bit_pattern):
        """configure_payload_bit_pattern."""
        response = self._invoke(
            self._client.CfgPayloadBitPattern,
            grpc_types.CfgPayloadBitPatternRequest(instrument=self._vi, selector_string=selector_string, payload_bit_pattern_raw=payload_bit_pattern),  # type: ignore
        )
        return response.status

    def configure_payload_length(self, selector_string, payload_length_mode, payload_length):
        """configure_payload_length."""
        response = self._invoke(
            self._client.CfgPayloadLength,
            grpc_types.CfgPayloadLengthRequest(instrument=self._vi, selector_string=selector_string, payload_length_mode_raw=payload_length_mode, payload_length=payload_length),  # type: ignore
        )
        return response.status

    def configure_reference_level(self, selector_string, reference_level):
        """configure_reference_level."""
        response = self._invoke(
            self._client.CfgReferenceLevel,
            grpc_types.CfgReferenceLevelRequest(instrument=self._vi, selector_string=selector_string, reference_level=reference_level),  # type: ignore
        )
        return response.status

    def configure_rf(
        self, selector_string, center_frequency, reference_level, external_attenuation
    ):
        """configure_rf."""
        response = self._invoke(
            self._client.CfgRF,
            grpc_types.CfgRFRequest(instrument=self._vi, selector_string=selector_string, center_frequency=center_frequency, reference_level=reference_level, external_attenuation=external_attenuation),  # type: ignore
        )
        return response.status

    def txp_fetch_edr_powers(self, selector_string, timeout):
        """txp_fetch_edr_powers."""
        response = self._invoke(
            self._client.TXPFetchEDRPowers,
            grpc_types.TXPFetchEDRPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.edr_gfsk_average_power_mean,
            response.edr_dpsk_average_power_mean,
            response.edr_dpsk_gfsk_average_power_ratio_mean,
            response.status,
        )

    def txp_fetch_le_cte_reference_period_powers(self, selector_string, timeout):
        """txp_fetch_le_cte_reference_period_powers."""
        response = self._invoke(
            self._client.TXPFetchLECTEReferencePeriodPowers,
            grpc_types.TXPFetchLECTEReferencePeriodPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.reference_period_average_power_mean,
            response.reference_period_peak_absolute_power_deviation_maximum,
            response.status,
        )

    def txp_fetch_le_cte_transmit_slot_powers(self, selector_string, timeout):
        """txp_fetch_le_cte_transmit_slot_powers."""
        response = self._invoke(
            self._client.TXPFetchLECTETransmitSlotPowers,
            grpc_types.TXPFetchLECTETransmitSlotPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.transmit_slot_average_power_mean,
            response.transmit_slot_peak_absolute_power_deviation_maximum,
            response.status,
        )

    def txp_fetch_powers(self, selector_string, timeout):
        """txp_fetch_powers."""
        response = self._invoke(
            self._client.TXPFetchPowers,
            grpc_types.TXPFetchPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_power_mean,
            response.average_power_maximum,
            response.average_power_minimum,
            response.peak_to_average_power_ratio_maximum,
            response.status,
        )

    def modacc_fetch_devm(self, selector_string, timeout):
        """modacc_fetch_devm."""
        response = self._invoke(
            self._client.ModAccFetchDEVM,
            grpc_types.ModAccFetchDEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.peak_rms_devm_maximum,
            response.peak_devm_maximum,
            response.ninetynine_percent_devm,
            response.status,
        )

    def modacc_fetch_devm_magnitude_error(self, selector_string, timeout):
        """modacc_fetch_devm_magnitude_error."""
        response = self._invoke(
            self._client.ModAccFetchDEVMMagnitudeError,
            grpc_types.ModAccFetchDEVMMagnitudeErrorRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_rms_magnitude_error_mean,
            response.peak_rms_magnitude_error_maximum,
            response.status,
        )

    def modacc_fetch_devm_phase_error(self, selector_string, timeout):
        """modacc_fetch_devm_phase_error."""
        response = self._invoke(
            self._client.ModAccFetchDEVMPhaseError,
            grpc_types.ModAccFetchDEVMPhaseErrorRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_rms_phase_error_mean,
            response.peak_rms_phase_error_maximum,
            response.status,
        )

    def modacc_fetch_df1(self, selector_string, timeout):
        """modacc_fetch_df1."""
        response = self._invoke(
            self._client.ModAccFetchDf1,
            grpc_types.ModAccFetchDf1Request(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.df1avg_maximum, response.df1avg_minimum, response.status

    def modacc_fetch_df2(self, selector_string, timeout):
        """modacc_fetch_df2."""
        response = self._invoke(
            self._client.ModAccFetchDf2,
            grpc_types.ModAccFetchDf2Request(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.df2avg_minimum,
            response.percentage_of_symbols_above_df2max_threshold,
            response.status,
        )

    def modacc_fetch_frequency_error_br(self, selector_string, timeout):
        """modacc_fetch_frequency_error_br."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorBR,
            grpc_types.ModAccFetchFrequencyErrorBRRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.initial_frequency_error_maximum,
            response.peak_frequency_drift_maximum,
            response.peak_frequency_drift_rate_maximum,
            response.status,
        )

    def modacc_fetch_frequency_error_edr(self, selector_string, timeout):
        """modacc_fetch_frequency_error_edr."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorEDR,
            grpc_types.ModAccFetchFrequencyErrorEDRRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.header_frequency_error_wi_maximum,
            response.peak_frequency_error_wi_plus_w0_maximum,
            response.peak_frequency_error_w0_maximum,
            response.status,
        )

    def modacc_fetch_frequency_error_le(self, selector_string, timeout):
        """modacc_fetch_frequency_error_le."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorLE,
            grpc_types.ModAccFetchFrequencyErrorLERequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.peak_frequency_error_maximum,
            response.initial_frequency_drift_maximum,
            response.peak_frequency_drift_maximum,
            response.peak_frequency_drift_rate_maximum,
            response.status,
        )

    def twenty_db_bandwidth_fetch_measurement(self, selector_string, timeout):
        """twenty_db_bandwidth_fetch_measurement."""
        response = self._invoke(
            self._client.TwentydBBandwidthFetchMeasurement,
            grpc_types.TwentydBBandwidthFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.peak_power,
            response.bandwidth,
            response.high_frequency,
            response.low_frequency,
            response.status,
        )

    def frequency_range_fetch_measurement(self, selector_string, timeout):
        """frequency_range_fetch_measurement."""
        response = self._invoke(
            self._client.FrequencyRangeFetchMeasurement,
            grpc_types.FrequencyRangeFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.high_frequency, response.low_frequency, response.status

    def acp_fetch_measurement_status(self, selector_string, timeout):
        """acp_fetch_measurement_status."""
        response = self._invoke(
            self._client.ACPFetchMeasurementStatus,
            grpc_types.ACPFetchMeasurementStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.AcpResultsMeasurementStatus(response.measurement_status), response.status

    def acp_fetch_offset_measurement(self, selector_string, timeout):
        """acp_fetch_offset_measurement."""
        response = self._invoke(
            self._client.ACPFetchOffsetMeasurement,
            grpc_types.ACPFetchOffsetMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.lower_absolute_power,
            response.upper_absolute_power,
            response.lower_relative_power,
            response.upper_relative_power,
            response.lower_margin,
            response.upper_margin,
            response.status,
        )

    def acp_fetch_reference_channel_power(self, selector_string, timeout):
        """acp_fetch_reference_channel_power."""
        response = self._invoke(
            self._client.ACPFetchReferenceChannelPower,
            grpc_types.ACPFetchReferenceChannelPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.reference_channel_power, response.status

    def txp_fetch_le_cte_transmit_slot_powers_array(self, selector_string, timeout):
        """txp_fetch_le_cte_transmit_slot_powers_array."""
        response = self._invoke(
            self._client.TXPFetchLECTETransmitSlotPowersArray,
            grpc_types.TXPFetchLECTETransmitSlotPowersArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.transmit_slot_average_power_mean[:],
            response.transmit_slot_peak_absolute_power_deviation_maximum[:],
            response.status,
        )

    def txp_fetch_power_trace(self, selector_string, timeout, power):
        """txp_fetch_power_trace."""
        response = self._invoke(
            self._client.TXPFetchPowerTrace,
            grpc_types.TXPFetchPowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(power, "power", "float32")
        if len(power) != response.actual_array_size:
            power.resize((response.actual_array_size,), refcheck=False)
        power.flat[:] = response.power
        return response.x0, response.dx, response.status

    def modacc_fetch_constellation_trace(self, selector_string, timeout, constellation):
        """modacc_fetch_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(constellation, "constellation", "complex64")
        if len(constellation) != response.actual_array_size // 2:
            constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.constellation, dtype=numpy.float32)
        constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_cs_detrended_phase_trace(self, selector_string, timeout, cs_detrended_phase):
        """modacc_fetch_cs_detrended_phase_trace."""
        response = self._invoke(
            self._client.ModAccFetchCSDetrendedPhaseTrace,
            grpc_types.ModAccFetchCSDetrendedPhaseTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(cs_detrended_phase, "cs_detrended_phase", "float32")
        if len(cs_detrended_phase) != response.actual_array_size:
            cs_detrended_phase.resize((response.actual_array_size,), refcheck=False)
        cs_detrended_phase.flat[:] = response.cs_detrended_phase
        return response.x0, response.dx, response.status

    def modacc_fetch_cs_tone_trace(
        self, selector_string, timeout, cs_tone_amplitude, cs_tone_phase
    ):
        """modacc_fetch_cs_tone_trace."""
        response = self._invoke(
            self._client.ModAccFetchCSToneTrace,
            grpc_types.ModAccFetchCSToneTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(cs_tone_amplitude, "cs_tone_amplitude", "float32")
        if len(cs_tone_amplitude) != response.actual_array_size:
            cs_tone_amplitude.resize((response.actual_array_size,), refcheck=False)
        cs_tone_amplitude.flat[:] = response.cs_tone_amplitude
        _helper.validate_numpy_array(cs_tone_phase, "cs_tone_phase", "float32")
        if len(cs_tone_phase) != response.actual_array_size:
            cs_tone_phase.resize((response.actual_array_size,), refcheck=False)
        cs_tone_phase.flat[:] = response.cs_tone_phase
        return response.x0, response.dx, response.status

    def modacc_fetch_demodulated_bit_trace(self, selector_string, timeout):
        """modacc_fetch_demodulated_bit_trace."""
        response = self._invoke(
            self._client.ModAccFetchDemodulatedBitTrace,
            grpc_types.ModAccFetchDemodulatedBitTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.demodulated_bits[:], response.status

    def modacc_fetch_devm_per_symbol_trace(self, selector_string, timeout):
        """modacc_fetch_devm_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchDEVMPerSymbolTrace,
            grpc_types.ModAccFetchDEVMPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.devm_per_symbol[:], response.status

    def modacc_fetch_evm_per_symbol_trace(self, selector_string, timeout):
        """modacc_fetch_evm_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchEVMPerSymbolTrace,
            grpc_types.ModAccFetchEVMPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.evm_per_symbol[:], response.status

    def modacc_fetch_df1max_trace(self, selector_string, timeout):
        """modacc_fetch_df1max_trace."""
        response = self._invoke(
            self._client.ModAccFetchDf1maxTrace,
            grpc_types.ModAccFetchDf1maxTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.time[:], response.df1max[:], response.status

    def modacc_fetch_df2max_trace(self, selector_string, timeout):
        """modacc_fetch_df2max_trace."""
        response = self._invoke(
            self._client.ModAccFetchDf2maxTrace,
            grpc_types.ModAccFetchDf2maxTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.time[:], response.df2max[:], response.status

    def modacc_fetch_df4avg_trace(self, selector_string, timeout):
        """modacc_fetch_df4avg_trace."""
        response = self._invoke(
            self._client.ModAccFetchDf4avgTrace,
            grpc_types.ModAccFetchDf4avgTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.time[:], response.df4avg[:], response.status

    def modacc_fetch_frequency_error_trace_br(self, selector_string, timeout):
        """modacc_fetch_frequency_error_trace_br."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorTraceBR,
            grpc_types.ModAccFetchFrequencyErrorTraceBRRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.time[:], response.frequency_error[:], response.status

    def modacc_fetch_frequency_error_trace_le(self, selector_string, timeout):
        """modacc_fetch_frequency_error_trace_le."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorTraceLE,
            grpc_types.ModAccFetchFrequencyErrorTraceLERequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.time[:], response.frequency_error[:], response.status

    def modacc_fetch_frequency_error_wi_plus_w0_trace_edr(self, selector_string, timeout):
        """modacc_fetch_frequency_error_wi_plus_w0_trace_edr."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorWiPlusW0TraceEDR,
            grpc_types.ModAccFetchFrequencyErrorWiPlusW0TraceEDRRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.time[:], response.frequency_error_wi_plus_w0[:], response.status

    def modacc_fetch_frequency_trace(self, selector_string, timeout, frequency):
        """modacc_fetch_frequency_trace."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyTrace,
            grpc_types.ModAccFetchFrequencyTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(frequency, "frequency", "float32")
        if len(frequency) != response.actual_array_size:
            frequency.resize((response.actual_array_size,), refcheck=False)
        frequency.flat[:] = response.frequency
        return response.x0, response.dx, response.status

    def modacc_fetch_rms_devm_trace(self, selector_string, timeout):
        """modacc_fetch_rms_devm_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSDEVMTrace,
            grpc_types.ModAccFetchRMSDEVMTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.rms_devm[:], response.status

    def twenty_db_bandwidth_fetch_spectrum(self, selector_string, timeout, spectrum):
        """twenty_db_bandwidth_fetch_spectrum."""
        response = self._invoke(
            self._client.TwentydBBandwidthFetchSpectrum,
            grpc_types.TwentydBBandwidthFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def frequency_range_fetch_spectrum(self, selector_string, timeout, spectrum):
        """frequency_range_fetch_spectrum."""
        response = self._invoke(
            self._client.FrequencyRangeFetchSpectrum,
            grpc_types.FrequencyRangeFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def acp_fetch_absolute_power_trace(self, selector_string, timeout, absolute_power):
        """acp_fetch_absolute_power_trace."""
        response = self._invoke(
            self._client.ACPFetchAbsolutePowerTrace,
            grpc_types.ACPFetchAbsolutePowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(absolute_power, "absolute_power", "float32")
        if len(absolute_power) != response.actual_array_size:
            absolute_power.resize((response.actual_array_size,), refcheck=False)
        absolute_power.flat[:] = response.absolute_power
        return response.x0, response.dx, response.status

    def acp_fetch_mask_trace(
        self, selector_string, timeout, limit_with_exception_mask, limit_without_exception_mask
    ):
        """acp_fetch_mask_trace."""
        response = self._invoke(
            self._client.ACPFetchMaskTrace,
            grpc_types.ACPFetchMaskTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            limit_with_exception_mask, "limit_with_exception_mask", "float32"
        )
        if len(limit_with_exception_mask) != response.actual_array_size:
            limit_with_exception_mask.resize((response.actual_array_size,), refcheck=False)
        limit_with_exception_mask.flat[:] = response.limit_with_exception_mask
        _helper.validate_numpy_array(
            limit_without_exception_mask, "limit_without_exception_mask", "float32"
        )
        if len(limit_without_exception_mask) != response.actual_array_size:
            limit_without_exception_mask.resize((response.actual_array_size,), refcheck=False)
        limit_without_exception_mask.flat[:] = response.limit_without_exception_mask
        return response.x0, response.dx, response.status

    def acp_fetch_offset_measurement_array(self, selector_string, timeout):
        """acp_fetch_offset_measurement_array."""
        response = self._invoke(
            self._client.ACPFetchOffsetMeasurementArray,
            grpc_types.ACPFetchOffsetMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.lower_absolute_power[:],
            response.upper_absolute_power[:],
            response.lower_relative_power[:],
            response.upper_relative_power[:],
            response.lower_margin[:],
            response.upper_margin[:],
            response.status,
        )

    def acp_fetch_spectrum(self, selector_string, timeout, spectrum):
        """acp_fetch_spectrum."""
        response = self._invoke(
            self._client.ACPFetchSpectrum,
            grpc_types.ACPFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def modspectrum_fetch_spectrum(self, selector_string, timeout, spectrum):
        """modspectrum_fetch_spectrum."""
        response = self._invoke(
            self._client.ModSpectrumFetchSpectrum,
            grpc_types.ModSpectrumFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        response = self._invoke(
            self._client.CloneSignalConfiguration,
            grpc_types.CloneSignalConfigurationRequest(instrument=self._vi, old_signal_name=old_signal_name, new_signal_name=new_signal_name),  # type: ignore
        )
        # signal_configuration = BluetoothSignalConfiguration.get_bluetooth_signal_configuration(self, new_signal_name)
        import nirfmxbluetooth

        signal_configuration = nirfmxbluetooth._BluetoothSignalConfiguration.get_bluetooth_signal_configuration(self._instr_session, new_signal_name, True)  # type: ignore
        return signal_configuration, response.status

    def delete_signal_configuration(self, ignore_driver_error):
        """delete_signal_configuration."""
        response = self._invoke(
            self._client.DeleteSignalConfiguration,
            grpc_types.DeleteSignalConfigurationRequest(instrument=self._vi, signal_name=self._signal_obj.signal_configuration_name),  # type: ignore
            None,
            ignore_driver_error,
        )
        if ignore_driver_error:
            return 0
        else:
            return response.status

    def send_software_edge_trigger(self):
        """send_software_edge_trigger."""
        response = self._invoke(
            self._client.SendSoftwareEdgeTrigger,
            grpc_types.SendSoftwareEdgeTriggerRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def get_all_named_result_names(self, selector_string):
        """get_all_named_result_names."""
        response = self._invoke(
            self._client.GetAllNamedResultNames,
            grpc_types.GetAllNamedResultNamesRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return (
            _helper.split_string_by_comma(response.result_names),
            bool(response.default_result_exists),
            response.status,
        )

    def analyze_iq_1_waveform(self, selector_string, result_name, x0, dx, iq, reset):
        """analyze_iq_1_waveform."""
        _helper.validate_numpy_array(iq, "iq", "complex64")
        iq_proto = [nidevice_grpc_types.NIComplexNumberF32(real=r, imaginary=i) for r, i in zip(iq.real, iq.imag)]  # type: ignore
        response = self._invoke(
            self._client.AnalyzeIQ1Waveform,
            grpc_types.AnalyzeIQ1WaveformRequest(instrument=self._vi, selector_string=selector_string, result_name=result_name, x0=x0, dx=dx, iq=iq_proto, reset=reset),  # type: ignore
        )
        return response.status
