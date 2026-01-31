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
import nirfmxinstr
import nirfmxnr.enums as enums
import nirfmxnr.errors as errors
import nirfmxnr.internal._custom_types as _custom_types
import nirfmxnr.internal._helper as _helper
import nirfmxnr.internal.nidevice_pb2 as nidevice_grpc_types
import nirfmxnr.internal.nirfmxnr_pb2 as grpc_types
import nirfmxnr.internal.nirfmxnr_pb2_grpc as nirfmxnr_grpc
import nirfmxnr.internal.session_pb2 as session_grpc_types


class GrpcStubInterpreter(object):
    """Interpreter for interacting with a gRPC Stub class"""

    def __init__(self, grpc_options, session=None, signal_obj=None):
        self._grpc_options = grpc_options
        self._signal_obj = signal_obj
        self._instr_session = session
        self._client = nirfmxnr_grpc.NiRFmxNRStub(grpc_options.grpc_channel)  # type: ignore
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
                local_personality.value == nirfmxinstr.Personalities.NR.value
            )
        else:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj.signal_configuration_name
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.NR.value
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

    def modacc_configure_reference_waveform(self, selector_string, x0, dx, reference_waveform):
        """modacc_configure_reference_waveform."""
        _helper.validate_numpy_array(reference_waveform, "reference_waveform", "complex64")
        reference_waveform_proto = reference_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.ModAccCfgReferenceWaveformInterleavedIQ,
            grpc_types.ModAccCfgReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, reference_waveform=reference_waveform_proto),  # type: ignore
        )
        return response.status

    def modacc_auto_level(self, selector_string, timeout):
        """modacc_auto_level."""
        response = self._invoke(
            self._client.ModAccAutoLevel,
            grpc_types.ModAccAutoLevelRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.status

    def modacc_validate_calibration_data(self, selector_string):
        """modacc_validate_calibration_data."""
        response = self._invoke(
            self._client.ModAccValidateCalibrationData,
            grpc_types.ModAccValidateCalibrationDataRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return enums.ModAccCalibrationDataValid(response.calibration_data_valid), response.status

    def modacc_clear_noise_calibration_database(self):
        """modacc_clear_noise_calibration_database."""
        response = self._invoke(
            self._client.ModAccClearNoiseCalibrationDatabase,
            grpc_types.ModAccClearNoiseCalibrationDatabaseRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def acp_validate_noise_calibration_data(self, selector_string):
        """acp_validate_noise_calibration_data."""
        response = self._invoke(
            self._client.ACPValidateNoiseCalibrationData,
            grpc_types.ACPValidateNoiseCalibrationDataRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return (
            enums.AcpNoiseCalibrationDataValid(response.noise_calibration_data_valid),
            response.status,
        )

    def chp_validate_noise_calibration_data(self, selector_string):
        """chp_validate_noise_calibration_data."""
        response = self._invoke(
            self._client.CHPValidateNoiseCalibrationData,
            grpc_types.CHPValidateNoiseCalibrationDataRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return (
            enums.ChpNoiseCalibrationDataValid(response.noise_calibration_data_valid),
            response.status,
        )

    def abort_measurements(self, selector_string):
        """abort_measurements."""
        response = self._invoke(
            self._client.AbortMeasurements,
            grpc_types.AbortMeasurementsRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
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

    def clear_noise_calibration_database(self, selector_string):
        """clear_noise_calibration_database."""
        response = self._invoke(
            self._client.ClearNoiseCalibrationDatabase,
            grpc_types.ClearNoiseCalibrationDatabaseRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
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
            grpc_types.CfgDigitalEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, digital_edge_source_raw=digital_edge_source, digital_edge_raw=digital_edge, trigger_delay=trigger_delay, enable_trigger=enable_trigger),  # type: ignore
        )
        return response.status

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
        """configure_iq_power_edge_trigger."""
        response = self._invoke(
            self._client.CfgIQPowerEdgeTrigger,
            grpc_types.CfgIQPowerEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, iq_power_edge_source=iq_power_edge_trigger_source, iq_power_edge_slope_raw=iq_power_edge_trigger_slope, iq_power_edge_level=iq_power_edge_trigger_level, trigger_delay=trigger_delay, trigger_min_quiet_time_mode_raw=trigger_minimum_quiet_time_mode, trigger_min_quiet_time_duration=trigger_minimum_quiet_time_duration, iq_power_edge_level_type_raw=iq_power_edge_trigger_level_type, enable_trigger=enable_trigger),  # type: ignore
        )
        return response.status

    def configure_selected_ports_multiple(self, selector_string, selected_ports):
        """configure_selected_ports_multiple."""
        response = self._invoke(
            self._client.CfgSelectedPortsMultiple,
            grpc_types.CfgSelectedPortsMultipleRequest(instrument=self._vi, selector_string=selector_string, selected_ports=selected_ports),  # type: ignore
        )
        return response.status

    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        """configure_software_edge_trigger."""
        response = self._invoke(
            self._client.CfgSoftwareEdgeTrigger,
            grpc_types.CfgSoftwareEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, trigger_delay=trigger_delay, enable_trigger=enable_trigger),  # type: ignore
        )
        return response.status

    def create_list(self, list_name):
        """create_list."""
        response = self._invoke(
            self._client.CreateList,
            grpc_types.CreateListRequest(instrument=self._vi, list_name=list_name),  # type: ignore
        )
        return response.status

    def create_list_step(self, selector_string):
        """create_list_step."""
        response = self._invoke(
            self._client.CreateListStep,
            grpc_types.CreateListStepRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.created_step_index, response.status

    def create_signal_configuration(self, signal_name):
        """create_signal_configuration."""
        response = self._invoke(
            self._client.CreateSignalConfiguration,
            grpc_types.CreateSignalConfigurationRequest(instrument=self._vi, signal_name=signal_name),  # type: ignore
        )
        return response.status

    def delete_list(self, list_name):
        """delete_list."""
        response = self._invoke(
            self._client.DeleteList,
            grpc_types.DeleteListRequest(instrument=self._vi, list_name=list_name),  # type: ignore
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

    def load_from_generation_configuration_file(
        self, selector_string, file_path, configuration_index
    ):
        """load_from_generation_configuration_file."""
        response = self._invoke(
            self._client.LoadFromGenerationConfigurationFile,
            grpc_types.LoadFromGenerationConfigurationFileRequest(instrument=self._vi, selector_string=selector_string, file_path=file_path, configuration_index=configuration_index),  # type: ignore
        )
        return response.status

    def modacc_configure_measurement_mode(self, selector_string, measurement_mode):
        """modacc_configure_measurement_mode."""
        response = self._invoke(
            self._client.ModAccCfgMeasurementMode,
            grpc_types.ModAccCfgMeasurementModeRequest(instrument=self._vi, selector_string=selector_string, measurement_mode_raw=measurement_mode),  # type: ignore
        )
        return response.status

    def modacc_configure_noise_compensation_enabled(
        self, selector_string, noise_compensation_enabled
    ):
        """modacc_configure_noise_compensation_enabled."""
        response = self._invoke(
            self._client.ModAccCfgNoiseCompensationEnabled,
            grpc_types.ModAccCfgNoiseCompensationEnabledRequest(instrument=self._vi, selector_string=selector_string, noise_compensation_enabled_raw=noise_compensation_enabled),  # type: ignore
        )
        return response.status

    def acp_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """acp_configure_averaging."""
        response = self._invoke(
            self._client.ACPCfgAveraging,
            grpc_types.ACPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def acp_configure_measurement_method(self, selector_string, measurement_method):
        """acp_configure_measurement_method."""
        response = self._invoke(
            self._client.ACPCfgMeasurementMethod,
            grpc_types.ACPCfgMeasurementMethodRequest(instrument=self._vi, selector_string=selector_string, measurement_method_raw=measurement_method),  # type: ignore
        )
        return response.status

    def acp_configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        """acp_configure_noise_compensation_enabled."""
        response = self._invoke(
            self._client.ACPCfgNoiseCompensationEnabled,
            grpc_types.ACPCfgNoiseCompensationEnabledRequest(instrument=self._vi, selector_string=selector_string, noise_compensation_enabled_raw=noise_compensation_enabled),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_endc_offsets(self, selector_string, number_of_endc_offsets):
        """acp_configure_number_of_endc_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfENDCOffsets,
            grpc_types.ACPCfgNumberOfENDCOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_endc_offsets=number_of_endc_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_eutra_offsets(self, selector_string, number_of_eutra_offsets):
        """acp_configure_number_of_eutra_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfEUTRAOffsets,
            grpc_types.ACPCfgNumberOfEUTRAOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_eutra_offsets=number_of_eutra_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_nr_offsets(self, selector_string, number_of_nr_offsets):
        """acp_configure_number_of_nr_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfNROffsets,
            grpc_types.ACPCfgNumberOfNROffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_nr_offsets=number_of_nr_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_utra_offsets(self, selector_string, number_of_utra_offsets):
        """acp_configure_number_of_utra_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfUTRAOffsets,
            grpc_types.ACPCfgNumberOfUTRAOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_utra_offsets=number_of_utra_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """acp_configure_rbw_filter."""
        response = self._invoke(
            self._client.ACPCfgRBWFilter,
            grpc_types.ACPCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def acp_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """acp_configure_sweep_time."""
        response = self._invoke(
            self._client.ACPCfgSweepTime,
            grpc_types.ACPCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def acp_configure_power_units(self, selector_string, power_units):
        """acp_configure_power_units."""
        response = self._invoke(
            self._client.ACPCfgPowerUnits,
            grpc_types.ACPCfgPowerUnitsRequest(instrument=self._vi, selector_string=selector_string, power_units_raw=power_units),  # type: ignore
        )
        return response.status

    def pvt_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """pvt_configure_averaging."""
        response = self._invoke(
            self._client.PVTCfgAveraging,
            grpc_types.PVTCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def pvt_configure_measurement_method(self, selector_string, measurement_method):
        """pvt_configure_measurement_method."""
        response = self._invoke(
            self._client.PVTCfgMeasurementMethod,
            grpc_types.PVTCfgMeasurementMethodRequest(instrument=self._vi, selector_string=selector_string, measurement_method_raw=measurement_method),  # type: ignore
        )
        return response.status

    def pvt_configure_off_power_exclusion_periods(
        self, selector_string, off_power_exclusion_before, off_power_exclusion_after
    ):
        """pvt_configure_off_power_exclusion_periods."""
        response = self._invoke(
            self._client.PVTCfgOFFPowerExclusionPeriods,
            grpc_types.PVTCfgOFFPowerExclusionPeriodsRequest(instrument=self._vi, selector_string=selector_string, off_power_exclusion_before=off_power_exclusion_before, off_power_exclusion_after=off_power_exclusion_after),  # type: ignore
        )
        return response.status

    def obw_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """obw_configure_averaging."""
        response = self._invoke(
            self._client.OBWCfgAveraging,
            grpc_types.OBWCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def obw_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """obw_configure_rbw_filter."""
        response = self._invoke(
            self._client.OBWCfgRBWFilter,
            grpc_types.OBWCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def obw_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """obw_configure_sweep_time."""
        response = self._invoke(
            self._client.OBWCfgSweepTime,
            grpc_types.OBWCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def sem_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """sem_configure_averaging."""
        response = self._invoke(
            self._client.SEMCfgAveraging,
            grpc_types.SEMCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def sem_configure_rated_output_power_array(
        self, selector_string, component_carrier_rated_output_power
    ):
        """sem_configure_rated_output_power_array."""
        response = self._invoke(
            self._client.SEMCfgComponentCarrierRatedOutputPowerArray,
            grpc_types.SEMCfgComponentCarrierRatedOutputPowerArrayRequest(instrument=self._vi, selector_string=selector_string, component_carrier_rated_output_power=component_carrier_rated_output_power),  # type: ignore
        )
        return response.status

    def sem_configure_rated_output_power(
        self, selector_string, component_carrier_rated_output_power
    ):
        """sem_configure_rated_output_power."""
        response = self._invoke(
            self._client.SEMCfgComponentCarrierRatedOutputPower,
            grpc_types.SEMCfgComponentCarrierRatedOutputPowerRequest(instrument=self._vi, selector_string=selector_string, component_carrier_rated_output_power=component_carrier_rated_output_power),  # type: ignore
        )
        return response.status

    def sem_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """sem_configure_number_of_offsets."""
        response = self._invoke(
            self._client.SEMCfgNumberOfOffsets,
            grpc_types.SEMCfgNumberOfOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_offsets=number_of_offsets),  # type: ignore
        )
        return response.status

    def sem_configure_offset_absolute_limit_array(
        self, selector_string, absolute_limit_start, absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetAbsoluteLimitArray,
            grpc_types.SEMCfgOffsetAbsoluteLimitArrayRequest(instrument=self._vi, selector_string=selector_string, absolute_limit_start=absolute_limit_start, absolute_limit_stop=absolute_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_absolute_limit(
        self, selector_string, absolute_limit_start, absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit."""
        response = self._invoke(
            self._client.SEMCfgOffsetAbsoluteLimit,
            grpc_types.SEMCfgOffsetAbsoluteLimitRequest(instrument=self._vi, selector_string=selector_string, absolute_limit_start=absolute_limit_start, absolute_limit_stop=absolute_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_bandwidth_integral_array(self, selector_string, bandwidth_integral):
        """sem_configure_offset_bandwidth_integral_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetBandwidthIntegralArray,
            grpc_types.SEMCfgOffsetBandwidthIntegralArrayRequest(instrument=self._vi, selector_string=selector_string, bandwidth_integral=bandwidth_integral),  # type: ignore
        )
        return response.status

    def sem_configure_offset_bandwidth_integral(self, selector_string, bandwidth_integral):
        """sem_configure_offset_bandwidth_integral."""
        response = self._invoke(
            self._client.SEMCfgOffsetBandwidthIntegral,
            grpc_types.SEMCfgOffsetBandwidthIntegralRequest(instrument=self._vi, selector_string=selector_string, bandwidth_integral=bandwidth_integral),  # type: ignore
        )
        return response.status

    def sem_configure_offset_frequency_array(
        self, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        """sem_configure_offset_frequency_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetFrequencyArray,
            grpc_types.SEMCfgOffsetFrequencyArrayRequest(instrument=self._vi, selector_string=selector_string, offset_start_frequency=offset_start_frequency, offset_stop_frequency=offset_stop_frequency, offset_sideband=offset_sideband),  # type: ignore
        )
        return response.status

    def sem_configure_offset_frequency(
        self, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        """sem_configure_offset_frequency."""
        response = self._invoke(
            self._client.SEMCfgOffsetFrequency,
            grpc_types.SEMCfgOffsetFrequencyRequest(instrument=self._vi, selector_string=selector_string, offset_start_frequency=offset_start_frequency, offset_stop_frequency=offset_stop_frequency, offset_sideband_raw=offset_sideband),  # type: ignore
        )
        return response.status

    def sem_configure_offset_limit_fail_mask_array(self, selector_string, limit_fail_mask):
        """sem_configure_offset_limit_fail_mask_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetLimitFailMaskArray,
            grpc_types.SEMCfgOffsetLimitFailMaskArrayRequest(instrument=self._vi, selector_string=selector_string, limit_fail_mask=limit_fail_mask),  # type: ignore
        )
        return response.status

    def sem_configure_offset_limit_fail_mask(self, selector_string, limit_fail_mask):
        """sem_configure_offset_limit_fail_mask."""
        response = self._invoke(
            self._client.SEMCfgOffsetLimitFailMask,
            grpc_types.SEMCfgOffsetLimitFailMaskRequest(instrument=self._vi, selector_string=selector_string, limit_fail_mask_raw=limit_fail_mask),  # type: ignore
        )
        return response.status

    def sem_configure_offset_rbw_filter_array(
        self, selector_string, offset_rbw, offset_rbw_filter_type
    ):
        """sem_configure_offset_rbw_filter_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetRBWFilterArray,
            grpc_types.SEMCfgOffsetRBWFilterArrayRequest(instrument=self._vi, selector_string=selector_string, offset_rbw=offset_rbw, offset_rbw_filter_type=offset_rbw_filter_type),  # type: ignore
        )
        return response.status

    def sem_configure_offset_rbw_filter(self, selector_string, offset_rbw, offset_rbw_filter_type):
        """sem_configure_offset_rbw_filter."""
        response = self._invoke(
            self._client.SEMCfgOffsetRBWFilter,
            grpc_types.SEMCfgOffsetRBWFilterRequest(instrument=self._vi, selector_string=selector_string, offset_rbw=offset_rbw, offset_rbw_filter_type_raw=offset_rbw_filter_type),  # type: ignore
        )
        return response.status

    def sem_configure_offset_relative_limit_array(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeLimitArray,
            grpc_types.SEMCfgOffsetRelativeLimitArrayRequest(instrument=self._vi, selector_string=selector_string, relative_limit_start=relative_limit_start, relative_limit_stop=relative_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_relative_limit(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeLimit,
            grpc_types.SEMCfgOffsetRelativeLimitRequest(instrument=self._vi, selector_string=selector_string, relative_limit_start=relative_limit_start, relative_limit_stop=relative_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """sem_configure_sweep_time."""
        response = self._invoke(
            self._client.SEMCfgSweepTime,
            grpc_types.SEMCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def sem_configure_uplink_mask_type(self, selector_string, uplink_mask_type):
        """sem_configure_uplink_mask_type."""
        response = self._invoke(
            self._client.SEMCfgUplinkMaskType,
            grpc_types.SEMCfgUplinkMaskTypeRequest(instrument=self._vi, selector_string=selector_string, uplink_mask_type_raw=uplink_mask_type),  # type: ignore
        )
        return response.status

    def chp_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """chp_configure_averaging."""
        response = self._invoke(
            self._client.CHPCfgAveraging,
            grpc_types.CHPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def chp_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """chp_configure_rbw_filter."""
        response = self._invoke(
            self._client.CHPCfgRBWFilter,
            grpc_types.CHPCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def chp_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """chp_configure_sweep_time."""
        response = self._invoke(
            self._client.CHPCfgSweepTime,
            grpc_types.CHPCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
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

    def configure_gnodeb_category(self, selector_string, gnodeb_category):
        """configure_gnodeb_category."""
        response = self._invoke(
            self._client.CfggNodeBCategory,
            grpc_types.CfggNodeBCategoryRequest(instrument=self._vi, selector_string=selector_string, gnodeb_category_raw=gnodeb_category),  # type: ignore
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

    def modacc_fetch_composite_evm(self, selector_string, timeout):
        """modacc_fetch_composite_evm."""
        response = self._invoke(
            self._client.ModAccFetchCompositeEVM,
            grpc_types.ModAccFetchCompositeEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.composite_rms_evm_mean, response.composite_peak_evm_maximum, response.status

    def modacc_fetch_frequency_error_mean(self, selector_string, timeout):
        """modacc_fetch_frequency_error_mean."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorMean,
            grpc_types.ModAccFetchFrequencyErrorMeanRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency_error_mean, response.status

    def acp_fetch_measurement(self, selector_string, timeout):
        """acp_fetch_measurement."""
        response = self._invoke(
            self._client.ACPFetchComponentCarrierMeasurement,
            grpc_types.ACPFetchComponentCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power, response.relative_power, response.status

    def acp_fetch_offset_measurement(self, selector_string, timeout):
        """acp_fetch_offset_measurement."""
        response = self._invoke(
            self._client.ACPFetchOffsetMeasurement,
            grpc_types.ACPFetchOffsetMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.lower_relative_power,
            response.upper_relative_power,
            response.lower_absolute_power,
            response.upper_absolute_power,
            response.status,
        )

    def acp_fetch_total_aggregated_power(self, selector_string, timeout):
        """acp_fetch_total_aggregated_power."""
        response = self._invoke(
            self._client.ACPFetchTotalAggregatedPower,
            grpc_types.ACPFetchTotalAggregatedPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_aggregated_power, response.status

    def acp_fetch_subblock_measurement(self, selector_string, timeout):
        """acp_fetch_subblock_measurement."""
        response = self._invoke(
            self._client.ACPFetchSubblockMeasurement,
            grpc_types.ACPFetchSubblockMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.subblock_power,
            response.integration_bandwidth,
            response.frequency,
            response.status,
        )

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        response = self._invoke(
            self._client.TXPFetchMeasurement,
            grpc_types.TXPFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.average_power_mean, response.peak_power_maximum, response.status

    def pvt_fetch_measurement(self, selector_string, timeout):
        """pvt_fetch_measurement."""
        response = self._invoke(
            self._client.PVTFetchMeasurement,
            grpc_types.PVTFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.PvtMeasurementStatus(response.measurement_status),
            response.absolute_off_power_before,
            response.absolute_off_power_after,
            response.absolute_on_power,
            response.burst_width,
            response.status,
        )

    def obw_fetch_measurement(self, selector_string, timeout):
        """obw_fetch_measurement."""
        response = self._invoke(
            self._client.OBWFetchMeasurement,
            grpc_types.OBWFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.occupied_bandwidth,
            response.absolute_power,
            response.start_frequency,
            response.stop_frequency,
            response.status,
        )

    def sem_fetch_measurement(self, selector_string, timeout):
        """sem_fetch_measurement."""
        response = self._invoke(
            self._client.SEMFetchComponentCarrierMeasurement,
            grpc_types.SEMFetchComponentCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.absolute_power,
            response.peak_absolute_power,
            response.peak_frequency,
            response.relative_power,
            response.status,
        )

    def sem_fetch_lower_offset_margin(self, selector_string, timeout):
        """sem_fetch_lower_offset_margin."""
        response = self._invoke(
            self._client.SEMFetchLowerOffsetMargin,
            grpc_types.SEMFetchLowerOffsetMarginRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.SemLowerOffsetMeasurementStatus(response.measurement_status),
            response.margin,
            response.margin_frequency,
            response.margin_absolute_power,
            response.margin_relative_power,
            response.status,
        )

    def sem_fetch_lower_offset_power(self, selector_string, timeout):
        """sem_fetch_lower_offset_power."""
        response = self._invoke(
            self._client.SEMFetchLowerOffsetPower,
            grpc_types.SEMFetchLowerOffsetPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.total_absolute_power,
            response.total_relative_power,
            response.peak_absolute_power,
            response.peak_frequency,
            response.peak_relative_power,
            response.status,
        )

    def sem_fetch_measurement_status(self, selector_string, timeout):
        """sem_fetch_measurement_status."""
        response = self._invoke(
            self._client.SEMFetchMeasurementStatus,
            grpc_types.SEMFetchMeasurementStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.SemMeasurementStatus(response.measurement_status), response.status

    def sem_fetch_total_aggregated_power(self, selector_string, timeout):
        """sem_fetch_total_aggregated_power."""
        response = self._invoke(
            self._client.SEMFetchTotalAggregatedPower,
            grpc_types.SEMFetchTotalAggregatedPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_aggregated_power, response.status

    def sem_fetch_upper_offset_margin(self, selector_string, timeout):
        """sem_fetch_upper_offset_margin."""
        response = self._invoke(
            self._client.SEMFetchUpperOffsetMargin,
            grpc_types.SEMFetchUpperOffsetMarginRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.SemUpperOffsetMeasurementStatus(response.measurement_status),
            response.margin,
            response.margin_frequency,
            response.margin_absolute_power,
            response.margin_relative_power,
            response.status,
        )

    def sem_fetch_upper_offset_power(self, selector_string, timeout):
        """sem_fetch_upper_offset_power."""
        response = self._invoke(
            self._client.SEMFetchUpperOffsetPower,
            grpc_types.SEMFetchUpperOffsetPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.total_absolute_power,
            response.total_relative_power,
            response.peak_absolute_power,
            response.peak_frequency,
            response.peak_relative_power,
            response.status,
        )

    def sem_fetch_subblock_measurement(self, selector_string, timeout):
        """sem_fetch_subblock_measurement."""
        response = self._invoke(
            self._client.SEMFetchSubblockMeasurement,
            grpc_types.SEMFetchSubblockMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.subblock_power,
            response.integration_bandwidth,
            response.frequency,
            response.status,
        )

    def chp_fetch_measurement(self, selector_string, timeout):
        """chp_fetch_measurement."""
        response = self._invoke(
            self._client.CHPFetchComponentCarrierMeasurement,
            grpc_types.CHPFetchComponentCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power, response.relative_power, response.status

    def chp_fetch_subblock_power(self, selector_string, timeout):
        """chp_fetch_subblock_power."""
        response = self._invoke(
            self._client.CHPFetchSubblockPower,
            grpc_types.CHPFetchSubblockPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.subblock_power, response.status

    def chp_fetch_total_aggregated_power(self, selector_string, timeout):
        """chp_fetch_total_aggregated_power."""
        response = self._invoke(
            self._client.CHPFetchTotalAggregatedPower,
            grpc_types.CHPFetchTotalAggregatedPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_aggregated_power, response.status

    def modacc_fetch_in_band_emission_trace(
        self, selector_string, timeout, in_band_emission, in_band_emission_mask
    ):
        """modacc_fetch_in_band_emission_trace."""
        response = self._invoke(
            self._client.ModAccFetchInBandEmissionTrace,
            grpc_types.ModAccFetchInBandEmissionTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(in_band_emission, "in_band_emission", "float32")
        if len(in_band_emission) != response.actual_array_size:
            in_band_emission.resize((response.actual_array_size,), refcheck=False)
        in_band_emission.flat[:] = response.in_band_emission
        _helper.validate_numpy_array(in_band_emission_mask, "in_band_emission_mask", "float32")
        if len(in_band_emission_mask) != response.actual_array_size:
            in_band_emission_mask.resize((response.actual_array_size,), refcheck=False)
        in_band_emission_mask.flat[:] = response.in_band_emission_mask
        return response.x0, response.dx, response.status

    def modacc_fetch_pbch_data_constellation_trace(
        self, selector_string, timeout, pbch_data_constellation
    ):
        """modacc_fetch_pbch_data_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPBCHDataConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPBCHDataConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pbch_data_constellation, "pbch_data_constellation", "complex64"
        )
        if len(pbch_data_constellation) != response.actual_array_size // 2:
            pbch_data_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pbch_data_constellation, dtype=numpy.float32)
        pbch_data_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pbch_data_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pbch_data_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_pbch_data_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace,
            grpc_types.ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pbch_data_rms_evm_per_subcarrier_mean,
            "pbch_data_rms_evm_per_subcarrier_mean",
            "float32",
        )
        if len(pbch_data_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            pbch_data_rms_evm_per_subcarrier_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        pbch_data_rms_evm_per_subcarrier_mean.flat[:] = (
            response.pbch_data_rms_evm_per_subcarrier_mean
        )
        return response.x0, response.dx, response.status

    def modacc_fetch_pbch_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pbch_data_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_pbch_data_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace,
            grpc_types.ModAccFetchPBCHDataRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pbch_data_rms_evm_per_symbol_mean, "pbch_data_rms_evm_per_symbol_mean", "float32"
        )
        if len(pbch_data_rms_evm_per_symbol_mean) != response.actual_array_size:
            pbch_data_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        pbch_data_rms_evm_per_symbol_mean.flat[:] = response.pbch_data_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_pbch_dmrs_constellation_trace(
        self, selector_string, timeout, pbch_dmrs_constellation
    ):
        """modacc_fetch_pbch_dmrs_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPBCHDMRSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPBCHDMRSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pbch_dmrs_constellation, "pbch_dmrs_constellation", "complex64"
        )
        if len(pbch_dmrs_constellation) != response.actual_array_size // 2:
            pbch_dmrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pbch_dmrs_constellation, dtype=numpy.float32)
        pbch_dmrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pbch_dmrs_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pbch_dmrs_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_pbch_dmrs_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace,
            grpc_types.ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pbch_dmrs_rms_evm_per_subcarrier_mean,
            "pbch_dmrs_rms_evm_per_subcarrier_mean",
            "float32",
        )
        if len(pbch_dmrs_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            pbch_dmrs_rms_evm_per_subcarrier_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        pbch_dmrs_rms_evm_per_subcarrier_mean.flat[:] = (
            response.pbch_dmrs_rms_evm_per_subcarrier_mean
        )
        return response.x0, response.dx, response.status

    def modacc_fetch_pbch_dmrs_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pbch_dmrs_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_pbch_dmrs_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace,
            grpc_types.ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pbch_dmrs_rms_evm_per_symbol_mean, "pbch_dmrs_rms_evm_per_symbol_mean", "float32"
        )
        if len(pbch_dmrs_rms_evm_per_symbol_mean) != response.actual_array_size:
            pbch_dmrs_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        pbch_dmrs_rms_evm_per_symbol_mean.flat[:] = response.pbch_dmrs_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_pdsch8_psk_constellation_trace(
        self, selector_string, timeout, psk8_constellation
    ):
        """modacc_fetch_pdsch8_psk_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH8PSKConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCH8PSKConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(psk8_constellation, "psk8_constellation", "complex64")
        if len(psk8_constellation) != response.actual_array_size // 2:
            psk8_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.psk8_constellation, dtype=numpy.float32)
        psk8_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch1024_qam_constellation_trace(
        self, selector_string, timeout, qam1024_constellation
    ):
        """modacc_fetch_pdsch1024_qam_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH1024QAMConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCH1024QAMConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam1024_constellation, "qam1024_constellation", "complex64")
        if len(qam1024_constellation) != response.actual_array_size // 2:
            qam1024_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam1024_constellation, dtype=numpy.float32)
        qam1024_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch16_qam_constellation_trace(
        self, selector_string, timeout, qam16_constellation
    ):
        """modacc_fetch_pdsch16_qam_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH16QAMConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCH16QAMConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam16_constellation, "qam16_constellation", "complex64")
        if len(qam16_constellation) != response.actual_array_size // 2:
            qam16_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam16_constellation, dtype=numpy.float32)
        qam16_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch256_qam_constellation_trace(
        self, selector_string, timeout, qam256_constellation
    ):
        """modacc_fetch_pdsch256_qam_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH256QAMConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCH256QAMConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam256_constellation, "qam256_constellation", "complex64")
        if len(qam256_constellation) != response.actual_array_size // 2:
            qam256_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam256_constellation, dtype=numpy.float32)
        qam256_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch64_qam_constellation_trace(
        self, selector_string, timeout, qam64_constellation
    ):
        """modacc_fetch_pdsch64_qam_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH64QAMConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCH64QAMConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam64_constellation, "qam64_constellation", "complex64")
        if len(qam64_constellation) != response.actual_array_size // 2:
            qam64_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam64_constellation, dtype=numpy.float32)
        qam64_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_data_constellation_trace(
        self, selector_string, timeout, pdsch_data_constellation
    ):
        """modacc_fetch_pdsch_data_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHDataConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCHDataConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pdsch_data_constellation, "pdsch_data_constellation", "complex64"
        )
        if len(pdsch_data_constellation) != response.actual_array_size // 2:
            pdsch_data_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pdsch_data_constellation, dtype=numpy.float32)
        pdsch_data_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_demodulated_bits(self, selector_string, timeout, bits):
        """modacc_fetch_pdsch_demodulated_bits."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHDemodulatedBits,
            grpc_types.ModAccFetchPDSCHDemodulatedBitsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(bits, "bits", "int8")
        if len(bits) != response.actual_array_size:
            bits.resize((response.actual_array_size,), refcheck=False)
        bits.flat[:] = response.bits
        return response.status

    def modacc_fetch_pdsch_dmrs_constellation_trace(
        self, selector_string, timeout, pdsch_dmrs_constellation
    ):
        """modacc_fetch_pdsch_dmrs_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHDMRSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCHDMRSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pdsch_dmrs_constellation, "pdsch_dmrs_constellation", "complex64"
        )
        if len(pdsch_dmrs_constellation) != response.actual_array_size // 2:
            pdsch_dmrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pdsch_dmrs_constellation, dtype=numpy.float32)
        pdsch_dmrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_ptrs_constellation_trace(
        self, selector_string, timeout, pdsch_ptrs_constellation
    ):
        """modacc_fetch_pdsch_ptrs_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHPTRSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCHPTRSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pdsch_ptrs_constellation, "pdsch_ptrs_constellation", "complex64"
        )
        if len(pdsch_ptrs_constellation) != response.actual_array_size // 2:
            pdsch_ptrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pdsch_ptrs_constellation, dtype=numpy.float32)
        pdsch_ptrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_qpsk_constellation_trace(
        self, selector_string, timeout, qpsk_constellation
    ):
        """modacc_fetch_pdsch_qpsk_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHQPSKConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPDSCHQPSKConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qpsk_constellation, "qpsk_constellation", "complex64")
        if len(qpsk_constellation) != response.actual_array_size // 2:
            qpsk_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qpsk_constellation, dtype=numpy.float32)
        qpsk_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_peak_evm_per_slot_maximum_trace(
        self, selector_string, timeout, peak_evm_per_slot_maximum
    ):
        """modacc_fetch_peak_evm_per_slot_maximum_trace."""
        response = self._invoke(
            self._client.ModAccFetchPeakEVMPerSlotMaximumTrace,
            grpc_types.ModAccFetchPeakEVMPerSlotMaximumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            peak_evm_per_slot_maximum, "peak_evm_per_slot_maximum", "float32"
        )
        if len(peak_evm_per_slot_maximum) != response.actual_array_size:
            peak_evm_per_slot_maximum.resize((response.actual_array_size,), refcheck=False)
        peak_evm_per_slot_maximum.flat[:] = response.peak_evm_per_slot_maximum
        return response.x0, response.dx, response.status

    def modacc_fetch_peak_evm_per_subcarrier_maximum_trace(
        self, selector_string, timeout, peak_evm_per_subcarrier_maximum
    ):
        """modacc_fetch_peak_evm_per_subcarrier_maximum_trace."""
        response = self._invoke(
            self._client.ModAccFetchPeakEVMPerSubcarrierMaximumTrace,
            grpc_types.ModAccFetchPeakEVMPerSubcarrierMaximumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            peak_evm_per_subcarrier_maximum, "peak_evm_per_subcarrier_maximum", "float32"
        )
        if len(peak_evm_per_subcarrier_maximum) != response.actual_array_size:
            peak_evm_per_subcarrier_maximum.resize((response.actual_array_size,), refcheck=False)
        peak_evm_per_subcarrier_maximum.flat[:] = response.peak_evm_per_subcarrier_maximum
        return response.x0, response.dx, response.status

    def modacc_fetch_peak_evm_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_per_symbol_maximum
    ):
        """modacc_fetch_peak_evm_per_symbol_maximum_trace."""
        response = self._invoke(
            self._client.ModAccFetchPeakEVMPerSymbolMaximumTrace,
            grpc_types.ModAccFetchPeakEVMPerSymbolMaximumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            peak_evm_per_symbol_maximum, "peak_evm_per_symbol_maximum", "float32"
        )
        if len(peak_evm_per_symbol_maximum) != response.actual_array_size:
            peak_evm_per_symbol_maximum.resize((response.actual_array_size,), refcheck=False)
        peak_evm_per_symbol_maximum.flat[:] = response.peak_evm_per_symbol_maximum
        return response.x0, response.dx, response.status

    def modacc_fetch_pss_constellation_trace(self, selector_string, timeout, pss_constellation):
        """modacc_fetch_pss_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPSSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPSSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(pss_constellation, "pss_constellation", "complex64")
        if len(pss_constellation) != response.actual_array_size // 2:
            pss_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pss_constellation, dtype=numpy.float32)
        pss_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pss_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pss_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_pss_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace,
            grpc_types.ModAccFetchPSSRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pss_rms_evm_per_subcarrier_mean, "pss_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(pss_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            pss_rms_evm_per_subcarrier_mean.resize((response.actual_array_size,), refcheck=False)
        pss_rms_evm_per_subcarrier_mean.flat[:] = response.pss_rms_evm_per_subcarrier_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_pss_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pss_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_pss_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchPSSRMSEVMPerSymbolMeanTrace,
            grpc_types.ModAccFetchPSSRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pss_rms_evm_per_symbol_mean, "pss_rms_evm_per_symbol_mean", "float32"
        )
        if len(pss_rms_evm_per_symbol_mean) != response.actual_array_size:
            pss_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        pss_rms_evm_per_symbol_mean.flat[:] = response.pss_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_pusch_data_constellation_trace(
        self, selector_string, timeout, pusch_data_constellation
    ):
        """modacc_fetch_pusch_data_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDataConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPUSCHDataConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pusch_data_constellation, "pusch_data_constellation", "complex64"
        )
        if len(pusch_data_constellation) != response.actual_array_size // 2:
            pusch_data_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pusch_data_constellation, dtype=numpy.float32)
        pusch_data_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pusch_demodulated_bits(self, selector_string, timeout, bits):
        """modacc_fetch_pusch_demodulated_bits."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDemodulatedBits,
            grpc_types.ModAccFetchPUSCHDemodulatedBitsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(bits, "bits", "int8")
        if len(bits) != response.actual_array_size:
            bits.resize((response.actual_array_size,), refcheck=False)
        bits.flat[:] = response.bits
        return response.status

    def modacc_fetch_pusch_dmrs_constellation_trace(
        self, selector_string, timeout, pusch_dmrs_constellation
    ):
        """modacc_fetch_pusch_dmrs_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDMRSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPUSCHDMRSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pusch_dmrs_constellation, "pusch_dmrs_constellation", "complex64"
        )
        if len(pusch_dmrs_constellation) != response.actual_array_size // 2:
            pusch_dmrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pusch_dmrs_constellation, dtype=numpy.float32)
        pusch_dmrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pusch_ptrs_constellation_trace(
        self, selector_string, timeout, pusch_ptrs_constellation
    ):
        """modacc_fetch_pusch_ptrs_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHPTRSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchPUSCHPTRSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            pusch_ptrs_constellation, "pusch_ptrs_constellation", "complex64"
        )
        if len(pusch_ptrs_constellation) != response.actual_array_size // 2:
            pusch_ptrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pusch_ptrs_constellation, dtype=numpy.float32)
        pusch_ptrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_rms_evm_per_slot_mean_trace(
        self, selector_string, timeout, rms_evm_per_slot_mean
    ):
        """modacc_fetch_rms_evm_per_slot_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSEVMPerSlotMeanTrace,
            grpc_types.ModAccFetchRMSEVMPerSlotMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(rms_evm_per_slot_mean, "rms_evm_per_slot_mean", "float32")
        if len(rms_evm_per_slot_mean) != response.actual_array_size:
            rms_evm_per_slot_mean.resize((response.actual_array_size,), refcheck=False)
        rms_evm_per_slot_mean.flat[:] = response.rms_evm_per_slot_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSEVMPerSubcarrierMeanTrace,
            grpc_types.ModAccFetchRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            rms_evm_per_subcarrier_mean, "rms_evm_per_subcarrier_mean", "float32"
        )
        if len(rms_evm_per_subcarrier_mean) != response.actual_array_size:
            rms_evm_per_subcarrier_mean.resize((response.actual_array_size,), refcheck=False)
        rms_evm_per_subcarrier_mean.flat[:] = response.rms_evm_per_subcarrier_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_per_symbol_mean
    ):
        """modacc_fetch_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSEVMPerSymbolMeanTrace,
            grpc_types.ModAccFetchRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(rms_evm_per_symbol_mean, "rms_evm_per_symbol_mean", "float32")
        if len(rms_evm_per_symbol_mean) != response.actual_array_size:
            rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        rms_evm_per_symbol_mean.flat[:] = response.rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_rms_evm_high_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_high_per_symbol_mean
    ):
        """modacc_fetch_rms_evm_high_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSEVMHighPerSymbolMeanTrace,
            grpc_types.ModAccFetchRMSEVMHighPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            rms_evm_high_per_symbol_mean, "rms_evm_high_per_symbol_mean", "float32"
        )
        if len(rms_evm_high_per_symbol_mean) != response.actual_array_size:
            rms_evm_high_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        rms_evm_high_per_symbol_mean.flat[:] = response.rms_evm_high_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_peak_evm_high_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_high_per_symbol_maximum
    ):
        """modacc_fetch_peak_evm_high_per_symbol_maximum_trace."""
        response = self._invoke(
            self._client.ModAccFetchPeakEVMHighPerSymbolMaximumTrace,
            grpc_types.ModAccFetchPeakEVMHighPerSymbolMaximumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            peak_evm_high_per_symbol_maximum, "peak_evm_high_per_symbol_maximum", "float32"
        )
        if len(peak_evm_high_per_symbol_maximum) != response.actual_array_size:
            peak_evm_high_per_symbol_maximum.resize((response.actual_array_size,), refcheck=False)
        peak_evm_high_per_symbol_maximum.flat[:] = response.peak_evm_high_per_symbol_maximum
        return response.x0, response.dx, response.status

    def modacc_fetch_rms_evm_low_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_low_per_symbol_mean
    ):
        """modacc_fetch_rms_evm_low_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSEVMLowPerSymbolMeanTrace,
            grpc_types.ModAccFetchRMSEVMLowPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            rms_evm_low_per_symbol_mean, "rms_evm_low_per_symbol_mean", "float32"
        )
        if len(rms_evm_low_per_symbol_mean) != response.actual_array_size:
            rms_evm_low_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        rms_evm_low_per_symbol_mean.flat[:] = response.rms_evm_low_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_peak_evm_low_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_low_per_symbol_maximum
    ):
        """modacc_fetch_peak_evm_low_per_symbol_maximum_trace."""
        response = self._invoke(
            self._client.ModAccFetchPeakEVMLowPerSymbolMaximumTrace,
            grpc_types.ModAccFetchPeakEVMLowPerSymbolMaximumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            peak_evm_low_per_symbol_maximum, "peak_evm_low_per_symbol_maximum", "float32"
        )
        if len(peak_evm_low_per_symbol_maximum) != response.actual_array_size:
            peak_evm_low_per_symbol_maximum.resize((response.actual_array_size,), refcheck=False)
        peak_evm_low_per_symbol_maximum.flat[:] = response.peak_evm_low_per_symbol_maximum
        return response.x0, response.dx, response.status

    def modacc_fetch_transient_period_locations_trace(
        self, selector_string, timeout, transient_period_locations
    ):
        """modacc_fetch_transient_period_locations_trace."""
        response = self._invoke(
            self._client.ModAccFetchTransientPeriodLocationsTrace,
            grpc_types.ModAccFetchTransientPeriodLocationsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            transient_period_locations, "transient_period_locations", "float32"
        )
        if len(transient_period_locations) != response.actual_array_size:
            transient_period_locations.resize((response.actual_array_size,), refcheck=False)
        transient_period_locations.flat[:] = response.transient_period_locations
        return response.x0, response.dx, response.status

    def modacc_fetch_pusch_phase_offset_trace(self, selector_string, timeout, pusch_phase_offset):
        """modacc_fetch_pusch_phase_offset_trace."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHPhaseOffsetTrace,
            grpc_types.ModAccFetchPUSCHPhaseOffsetTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(pusch_phase_offset, "pusch_phase_offset", "float32")
        if len(pusch_phase_offset) != response.actual_array_size:
            pusch_phase_offset.resize((response.actual_array_size,), refcheck=False)
        pusch_phase_offset.flat[:] = response.pusch_phase_offset
        return response.x0, response.dx, response.status

    def modacc_fetch_frequency_error_per_slot_maximum_trace(
        self, selector_string, timeout, frequency_error_per_slot_maximum
    ):
        """modacc_fetch_frequency_error_per_slot_maximum_trace."""
        response = self._invoke(
            self._client.ModAccFetchFrequencyErrorPerSlotMaximumTrace,
            grpc_types.ModAccFetchFrequencyErrorPerSlotMaximumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            frequency_error_per_slot_maximum, "frequency_error_per_slot_maximum", "float32"
        )
        if len(frequency_error_per_slot_maximum) != response.actual_array_size:
            frequency_error_per_slot_maximum.resize((response.actual_array_size,), refcheck=False)
        frequency_error_per_slot_maximum.flat[:] = response.frequency_error_per_slot_maximum
        return response.x0, response.dx, response.status

    def modacc_fetch_spectral_flatness_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        """modacc_fetch_spectral_flatness_trace."""
        response = self._invoke(
            self._client.ModAccFetchSpectralFlatnessTrace,
            grpc_types.ModAccFetchSpectralFlatnessTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectral_flatness, "spectral_flatness", "float32")
        if len(spectral_flatness) != response.actual_array_size:
            spectral_flatness.resize((response.actual_array_size,), refcheck=False)
        spectral_flatness.flat[:] = response.spectral_flatness
        _helper.validate_numpy_array(
            spectral_flatness_lower_mask, "spectral_flatness_lower_mask", "float32"
        )
        if len(spectral_flatness_lower_mask) != response.actual_array_size:
            spectral_flatness_lower_mask.resize((response.actual_array_size,), refcheck=False)
        spectral_flatness_lower_mask.flat[:] = response.spectral_flatness_lower_mask
        _helper.validate_numpy_array(
            spectral_flatness_upper_mask, "spectral_flatness_upper_mask", "float32"
        )
        if len(spectral_flatness_upper_mask) != response.actual_array_size:
            spectral_flatness_upper_mask.resize((response.actual_array_size,), refcheck=False)
        spectral_flatness_upper_mask.flat[:] = response.spectral_flatness_upper_mask
        return response.x0, response.dx, response.status

    def modacc_fetch_sss_constellation_trace(self, selector_string, timeout, sss_constellation):
        """modacc_fetch_sss_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchSSSConstellationTraceInterleavedIQ,
            grpc_types.ModAccFetchSSSConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(sss_constellation, "sss_constellation", "complex64")
        if len(sss_constellation) != response.actual_array_size // 2:
            sss_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.sss_constellation, dtype=numpy.float32)
        sss_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_sss_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, sss_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_sss_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace,
            grpc_types.ModAccFetchSSSRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            sss_rms_evm_per_subcarrier_mean, "sss_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(sss_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            sss_rms_evm_per_subcarrier_mean.resize((response.actual_array_size,), refcheck=False)
        sss_rms_evm_per_subcarrier_mean.flat[:] = response.sss_rms_evm_per_subcarrier_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_sss_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, sss_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_sss_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchSSSRMSEVMPerSymbolMeanTrace,
            grpc_types.ModAccFetchSSSRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            sss_rms_evm_per_symbol_mean, "sss_rms_evm_per_symbol_mean", "float32"
        )
        if len(sss_rms_evm_per_symbol_mean) != response.actual_array_size:
            sss_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        sss_rms_evm_per_symbol_mean.flat[:] = response.sss_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def modacc_fetch_subblock_in_band_emission_trace(
        self,
        selector_string,
        timeout,
        subblock_in_band_emission,
        subblock_in_band_emission_mask,
        subblock_in_band_emission_rb_indices,
    ):
        """modacc_fetch_subblock_in_band_emission_trace."""
        response = self._invoke(
            self._client.ModAccFetchSubblockInBandEmissionTrace,
            grpc_types.ModAccFetchSubblockInBandEmissionTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            subblock_in_band_emission, "subblock_in_band_emission", "float64"
        )
        if len(subblock_in_band_emission) != response.actual_array_size:
            subblock_in_band_emission.resize((response.actual_array_size,), refcheck=False)
        subblock_in_band_emission.flat[:] = response.subblock_in_band_emission
        _helper.validate_numpy_array(
            subblock_in_band_emission_mask, "subblock_in_band_emission_mask", "float64"
        )
        if len(subblock_in_band_emission_mask) != response.actual_array_size:
            subblock_in_band_emission_mask.resize((response.actual_array_size,), refcheck=False)
        subblock_in_band_emission_mask.flat[:] = response.subblock_in_band_emission_mask
        _helper.validate_numpy_array(
            subblock_in_band_emission_rb_indices, "subblock_in_band_emission_rb_indices", "float64"
        )
        if len(subblock_in_band_emission_rb_indices) != response.actual_array_size:
            subblock_in_band_emission_rb_indices.resize(
                (response.actual_array_size,), refcheck=False
            )
        subblock_in_band_emission_rb_indices.flat[:] = response.subblock_in_band_emission_rb_indices
        return response.status

    def modacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
    ):
        """modacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchIQGainImbalancePerSubcarrierMeanTrace,
            grpc_types.ModAccFetchIQGainImbalancePerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            iq_gain_imbalance_per_subcarrier_mean,
            "iq_gain_imbalance_per_subcarrier_mean",
            "float32",
        )
        if len(iq_gain_imbalance_per_subcarrier_mean) != response.actual_array_size:
            iq_gain_imbalance_per_subcarrier_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        iq_gain_imbalance_per_subcarrier_mean.flat[:] = (
            response.iq_gain_imbalance_per_subcarrier_mean
        )
        return response.x0, response.dx, response.status

    def modacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
    ):
        """modacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace,
            grpc_types.ModAccFetchIQQuadratureErrorPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            iq_quadrature_error_per_subcarrier_mean,
            "iq_quadrature_error_per_subcarrier_mean",
            "float32",
        )
        if len(iq_quadrature_error_per_subcarrier_mean) != response.actual_array_size:
            iq_quadrature_error_per_subcarrier_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        iq_quadrature_error_per_subcarrier_mean.flat[:] = (
            response.iq_quadrature_error_per_subcarrier_mean
        )
        return response.x0, response.dx, response.status

    def acp_fetch_absolute_powers_trace(
        self, selector_string, timeout, trace_index, absolute_powers_trace
    ):
        """acp_fetch_absolute_powers_trace."""
        response = self._invoke(
            self._client.ACPFetchAbsolutePowersTrace,
            grpc_types.ACPFetchAbsolutePowersTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, trace_index=trace_index),  # type: ignore
        )
        _helper.validate_numpy_array(absolute_powers_trace, "absolute_powers_trace", "float32")
        if len(absolute_powers_trace) != response.actual_array_size:
            absolute_powers_trace.resize((response.actual_array_size,), refcheck=False)
        absolute_powers_trace.flat[:] = response.absolute_powers_trace
        return response.x0, response.dx, response.status

    def acp_fetch_measurement_array(self, selector_string, timeout):
        """acp_fetch_measurement_array."""
        response = self._invoke(
            self._client.ACPFetchComponentCarrierMeasurementArray,
            grpc_types.ACPFetchComponentCarrierMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power[:], response.relative_power[:], response.status

    def acp_fetch_offset_measurement_array(self, selector_string, timeout):
        """acp_fetch_offset_measurement_array."""
        response = self._invoke(
            self._client.ACPFetchOffsetMeasurementArray,
            grpc_types.ACPFetchOffsetMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.lower_relative_power[:],
            response.upper_relative_power[:],
            response.lower_absolute_power[:],
            response.upper_absolute_power[:],
            response.status,
        )

    def acp_fetch_relative_powers_trace(
        self, selector_string, timeout, trace_index, relative_powers_trace
    ):
        """acp_fetch_relative_powers_trace."""
        response = self._invoke(
            self._client.ACPFetchRelativePowersTrace,
            grpc_types.ACPFetchRelativePowersTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, trace_index=trace_index),  # type: ignore
        )
        _helper.validate_numpy_array(relative_powers_trace, "relative_powers_trace", "float32")
        if len(relative_powers_trace) != response.actual_array_size:
            relative_powers_trace.resize((response.actual_array_size,), refcheck=False)
        relative_powers_trace.flat[:] = response.relative_powers_trace
        return response.x0, response.dx, response.status

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

    def pvt_fetch_measurement_array(self, selector_string, timeout):
        """pvt_fetch_measurement_array."""
        response = self._invoke(
            self._client.PVTFetchMeasurementArray,
            grpc_types.PVTFetchMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            [enums.PvtMeasurementStatus(value) for value in response.measurement_status],
            response.absolute_off_power_before[:],
            response.absolute_off_power_after[:],
            response.absolute_on_power[:],
            response.burst_width[:],
            response.status,
        )

    def pvt_fetch_signal_power_trace(self, selector_string, timeout, signal_power, absolute_limit):
        """pvt_fetch_signal_power_trace."""
        response = self._invoke(
            self._client.PVTFetchSignalPowerTrace,
            grpc_types.PVTFetchSignalPowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(signal_power, "signal_power", "float32")
        if len(signal_power) != response.actual_array_size:
            signal_power.resize((response.actual_array_size,), refcheck=False)
        signal_power.flat[:] = response.signal_power
        _helper.validate_numpy_array(absolute_limit, "absolute_limit", "float32")
        if len(absolute_limit) != response.actual_array_size:
            absolute_limit.resize((response.actual_array_size,), refcheck=False)
        absolute_limit.flat[:] = response.absolute_limit
        return response.x0, response.dx, response.status

    def pvt_fetch_windowed_signal_power_trace(
        self, selector_string, timeout, windowed_signal_power
    ):
        """pvt_fetch_windowed_signal_power_trace."""
        response = self._invoke(
            self._client.PVTFetchWindowedSignalPowerTrace,
            grpc_types.PVTFetchWindowedSignalPowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(windowed_signal_power, "windowed_signal_power", "float32")
        if len(windowed_signal_power) != response.actual_array_size:
            windowed_signal_power.resize((response.actual_array_size,), refcheck=False)
        windowed_signal_power.flat[:] = response.windowed_signal_power
        return response.x0, response.dx, response.status

    def obw_fetch_spectrum(self, selector_string, timeout, spectrum):
        """obw_fetch_spectrum."""
        response = self._invoke(
            self._client.OBWFetchSpectrum,
            grpc_types.OBWFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def sem_fetch_measurement_array(self, selector_string, timeout):
        """sem_fetch_measurement_array."""
        response = self._invoke(
            self._client.SEMFetchComponentCarrierMeasurementArray,
            grpc_types.SEMFetchComponentCarrierMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.absolute_power[:],
            response.peak_absolute_power[:],
            response.peak_frequency[:],
            response.relative_power[:],
            response.status,
        )

    def sem_fetch_lower_offset_margin_array(self, selector_string, timeout):
        """sem_fetch_lower_offset_margin_array."""
        response = self._invoke(
            self._client.SEMFetchLowerOffsetMarginArray,
            grpc_types.SEMFetchLowerOffsetMarginArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            [enums.SemLowerOffsetMeasurementStatus(value) for value in response.measurement_status],
            response.margin[:],
            response.margin_frequency[:],
            response.margin_absolute_power[:],
            response.margin_relative_power[:],
            response.status,
        )

    def sem_fetch_lower_offset_power_array(self, selector_string, timeout):
        """sem_fetch_lower_offset_power_array."""
        response = self._invoke(
            self._client.SEMFetchLowerOffsetPowerArray,
            grpc_types.SEMFetchLowerOffsetPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.total_absolute_power[:],
            response.total_relative_power[:],
            response.peak_absolute_power[:],
            response.peak_frequency[:],
            response.peak_relative_power[:],
            response.status,
        )

    def sem_fetch_spectrum(self, selector_string, timeout, spectrum, composite_mask):
        """sem_fetch_spectrum."""
        response = self._invoke(
            self._client.SEMFetchSpectrum,
            grpc_types.SEMFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        _helper.validate_numpy_array(composite_mask, "composite_mask", "float32")
        if len(composite_mask) != response.actual_array_size:
            composite_mask.resize((response.actual_array_size,), refcheck=False)
        composite_mask.flat[:] = response.composite_mask
        return response.x0, response.dx, response.status

    def sem_fetch_upper_offset_margin_array(self, selector_string, timeout):
        """sem_fetch_upper_offset_margin_array."""
        response = self._invoke(
            self._client.SEMFetchUpperOffsetMarginArray,
            grpc_types.SEMFetchUpperOffsetMarginArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            [enums.SemUpperOffsetMeasurementStatus(value) for value in response.measurement_status],
            response.margin[:],
            response.margin_frequency[:],
            response.margin_absolute_power[:],
            response.margin_relative_power[:],
            response.status,
        )

    def sem_fetch_upper_offset_power_array(self, selector_string, timeout):
        """sem_fetch_upper_offset_power_array."""
        response = self._invoke(
            self._client.SEMFetchUpperOffsetPowerArray,
            grpc_types.SEMFetchUpperOffsetPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.total_absolute_power[:],
            response.total_relative_power[:],
            response.peak_absolute_power[:],
            response.peak_frequency[:],
            response.peak_relative_power[:],
            response.status,
        )

    def chp_fetch_measurement_array(self, selector_string, timeout):
        """chp_fetch_measurement_array."""
        response = self._invoke(
            self._client.CHPFetchComponentCarrierMeasurementArray,
            grpc_types.CHPFetchComponentCarrierMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power[:], response.relative_power[:], response.status

    def chp_fetch_spectrum(self, selector_string, timeout, spectrum):
        """chp_fetch_spectrum."""
        response = self._invoke(
            self._client.CHPFetchSpectrum,
            grpc_types.CHPFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
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
        # signal_configuration = NRSignalConfiguration.get_nr_signal_configuration(self, new_signal_name)
        import nirfmxnr

        signal_configuration = nirfmxnr._NRSignalConfiguration.get_nr_signal_configuration(self._instr_session, new_signal_name, True)  # type: ignore
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

    def analyze_spectrum_1_waveform(self, selector_string, result_name, x0, dx, spectrum, reset):
        """analyze_spectrum_1_waveform."""
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        spectrum_proto = spectrum.flat
        response = self._invoke(
            self._client.AnalyzeSpectrum1Waveform,
            grpc_types.AnalyzeSpectrum1WaveformRequest(instrument=self._vi, selector_string=selector_string, result_name=result_name, x0=x0, dx=dx, spectrum=spectrum_proto, reset=reset),  # type: ignore
        )
        return response.status

    def analyze_n_waveforms_iq(self, selector_string, result_name, x0, dx, iq, reset):
        """analyze_n_waveforms_iq."""
        iq_proto = []
        iq_sizes = []
        for arr in iq:
            _helper.validate_numpy_array(arr, "iq", "complex64")
            iq_proto.extend([nidevice_grpc_types.NIComplexNumberF32(real=r, imaginary=i) for r, i in zip(arr.real, arr.imag)])  # type: ignore
            iq_sizes.append(arr.size)
        response = self._invoke(
            self._client.AnalyzeNWaveformsIQ,
            grpc_types.AnalyzeNWaveformsIQRequest(instrument=self._vi, selector_string=selector_string, result_name=result_name, x0=x0, dx=dx, iq=iq_proto, iq_sizes=iq_sizes, reset=reset),  # type: ignore
        )
        return response.status

    def analyze_n_waveforms_spectrum(self, selector_string, result_name, x0, dx, spectrum, reset):
        """analyze_n_waveforms_spectrum."""
        spectrum_proto = []
        spectrum_sizes = []
        for arr in spectrum:
            _helper.validate_numpy_array(arr, "spectrum", "float32")
            spectrum_proto.extend(arr.flat)
            spectrum_sizes.append(arr.size)
        response = self._invoke(
            self._client.AnalyzeNWaveformsSpectrum,
            grpc_types.AnalyzeNWaveformsSpectrumRequest(instrument=self._vi, selector_string=selector_string, result_name=result_name, x0=x0, dx=dx, spectrum=spectrum_proto, spectrum_sizes=spectrum_sizes, reset=reset),  # type: ignore
        )
        return response.status
