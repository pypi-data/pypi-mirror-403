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
import nirfmxwlan.enums as enums
import nirfmxwlan.errors as errors
import nirfmxwlan.internal._custom_types as _custom_types
import nirfmxwlan.internal._helper as _helper
import nirfmxwlan.internal.nidevice_pb2 as nidevice_grpc_types
import nirfmxwlan.internal.nirfmxwlan_pb2 as grpc_types
import nirfmxwlan.internal.nirfmxwlan_pb2_grpc as nirfmxwlan_grpc
import nirfmxwlan.internal.nirfmxwlan_restricted_pb2 as restricted_grpc_types
import nirfmxwlan.internal.nirfmxwlan_restricted_pb2_grpc as nirfmxwlan_restricted_grpc
import nirfmxwlan.internal.session_pb2 as session_grpc_types


class GrpcStubInterpreter(object):
    """Interpreter for interacting with a gRPC Stub class"""

    def __init__(self, grpc_options, session=None, signal_obj=None):
        self._grpc_options = grpc_options
        self._signal_obj = signal_obj
        self._instr_session = session
        self._client = nirfmxwlan_grpc.NiRFmxWLANStub(grpc_options.grpc_channel)  # type: ignore
        self._restricted_client = nirfmxwlan_restricted_grpc.NiRFmxWLANRestrictedStub(grpc_options.grpc_channel)  # type: ignore
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
                local_personality.value == nirfmxinstr.Personalities.WLAN.value
            )
        else:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj.signal_configuration_name
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.WLAN.value
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

    def ofdmmodacc_configure_1_reference_waveform(
        self, selector_string, x0, dx, reference_waveform
    ):
        """ofdmmodacc_configure_1_reference_waveform."""
        _helper.validate_numpy_array(reference_waveform, "reference_waveform", "complex64")
        reference_waveform_proto = reference_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.OFDMModAccCfg1ReferenceWaveformInterleavedIQ,
            grpc_types.OFDMModAccCfg1ReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, reference_waveform=reference_waveform_proto),  # type: ignore
        )
        return response.status

    def ofdmmodacc_auto_level(self, selector_string, timeout):
        """ofdmmodacc_auto_level."""
        response = self._invoke(
            self._client.OFDMModAccAutoLevel,
            grpc_types.OFDMModAccAutoLevelRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.status

    def ofdmmodacc_validate_calibration_data(self, selector_string):
        """ofdmmodacc_validate_calibration_data."""
        response = self._invoke(
            self._client.OFDMModAccValidateCalibrationData,
            grpc_types.OFDMModAccValidateCalibrationDataRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return (
            enums.OfdmModAccCalibrationDataValid(response.calibration_data_valid),
            response.status,
        )

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
        return response.status

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

    def auto_detect_signal_analysis_only(self, selector_string, x0, dx, iq):
        """auto_detect_signal_analysis_only."""
        _helper.validate_numpy_array(iq, "iq", "complex64")
        iq_proto = iq.view(numpy.float32)
        response = self._invoke(
            self._client.AutoDetectSignalAnalysisOnlyInterleavedIQ,
            grpc_types.AutoDetectSignalAnalysisOnlyInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, iq=iq_proto),  # type: ignore
        )
        return response.status

    def txp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """txp_configure_averaging."""
        response = self._invoke(
            self._client.TXPCfgAveraging,
            grpc_types.TXPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def txp_configure_burst_detection_enabled(self, selector_string, burst_detection_enabled):
        """txp_configure_burst_detection_enabled."""
        response = self._invoke(
            self._client.TXPCfgBurstDetectionEnabled,
            grpc_types.TXPCfgBurstDetectionEnabledRequest(instrument=self._vi, selector_string=selector_string, burst_detection_enabled_raw=burst_detection_enabled),  # type: ignore
        )
        return response.status

    def txp_configure_maximum_measurement_interval(
        self, selector_string, maximum_measurement_interval
    ):
        """txp_configure_maximum_measurement_interval."""
        response = self._invoke(
            self._client.TXPCfgMaximumMeasurementInterval,
            grpc_types.TXPCfgMaximumMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, maximum_measurement_interval=maximum_measurement_interval),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_acquisition_length(
        self, selector_string, acquisition_length_mode, acquisition_length
    ):
        """dsssmodacc_configure_acquisition_length."""
        response = self._invoke(
            self._client.DSSSModAccCfgAcquisitionLength,
            grpc_types.DSSSModAccCfgAcquisitionLengthRequest(instrument=self._vi, selector_string=selector_string, acquisition_length_mode_raw=acquisition_length_mode, acquisition_length=acquisition_length),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """dsssmodacc_configure_averaging."""
        response = self._invoke(
            self._client.DSSSModAccCfgAveraging,
            grpc_types.DSSSModAccCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_evm_unit(self, selector_string, evm_unit):
        """dsssmodacc_configure_evm_unit."""
        response = self._invoke(
            self._client.DSSSModAccCfgEVMUnit,
            grpc_types.DSSSModAccCfgEVMUnitRequest(instrument=self._vi, selector_string=selector_string, evm_unit_raw=evm_unit),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_measurement_length(
        self, selector_string, measurement_offset, maximum_measurement_length
    ):
        """dsssmodacc_configure_measurement_length."""
        response = self._invoke(
            self._client.DSSSModAccCfgMeasurementLength,
            grpc_types.DSSSModAccCfgMeasurementLengthRequest(instrument=self._vi, selector_string=selector_string, measurement_offset=measurement_offset, maximum_measurement_length=maximum_measurement_length),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_power_measurement_custom_gate_array(
        self, selector_string, start_time, stop_time
    ):
        """dsssmodacc_configure_power_measurement_custom_gate_array."""
        response = self._invoke(
            self._client.DSSSModAccCfgPowerMeasurementCustomGateArray,
            grpc_types.DSSSModAccCfgPowerMeasurementCustomGateArrayRequest(instrument=self._vi, selector_string=selector_string, start_time=start_time, stop_time=stop_time),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_power_measurement_enabled(
        self, selector_string, power_measurement_enabled
    ):
        """dsssmodacc_configure_power_measurement_enabled."""
        response = self._invoke(
            self._client.DSSSModAccCfgPowerMeasurementEnabled,
            grpc_types.DSSSModAccCfgPowerMeasurementEnabledRequest(instrument=self._vi, selector_string=selector_string, power_measurement_enabled_raw=power_measurement_enabled),  # type: ignore
        )
        return response.status

    def dsssmodacc_configure_power_measurement_number_of_custom_gates(
        self, selector_string, number_of_custom_gates
    ):
        """dsssmodacc_configure_power_measurement_number_of_custom_gates."""
        response = self._invoke(
            self._client.DSSSModAccCfgPowerMeasurementNumberOfCustomGates,
            grpc_types.DSSSModAccCfgPowerMeasurementNumberOfCustomGatesRequest(instrument=self._vi, selector_string=selector_string, number_of_custom_gates=number_of_custom_gates),  # type: ignore
        )
        return response.status

    def powerramp_configure_acquisition_length(self, selector_string, acquisition_length):
        """powerramp_configure_acquisition_length."""
        response = self._invoke(
            self._client.PowerRampCfgAcquisitionLength,
            grpc_types.PowerRampCfgAcquisitionLengthRequest(instrument=self._vi, selector_string=selector_string, acquisition_length=acquisition_length),  # type: ignore
        )
        return response.status

    def powerramp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """powerramp_configure_averaging."""
        response = self._invoke(
            self._client.PowerRampCfgAveraging,
            grpc_types.PowerRampCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_acquisition_length(
        self, selector_string, acquisition_length_mode, acquisition_length
    ):
        """ofdmmodacc_configure_acquisition_length."""
        response = self._invoke(
            self._client.OFDMModAccCfgAcquisitionLength,
            grpc_types.OFDMModAccCfgAcquisitionLengthRequest(instrument=self._vi, selector_string=selector_string, acquisition_length_mode_raw=acquisition_length_mode, acquisition_length=acquisition_length),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_amplitude_tracking_enabled(
        self, selector_string, amplitude_tracking_enabled
    ):
        """ofdmmodacc_configure_amplitude_tracking_enabled."""
        response = self._invoke(
            self._client.OFDMModAccCfgAmplitudeTrackingEnabled,
            grpc_types.OFDMModAccCfgAmplitudeTrackingEnabledRequest(instrument=self._vi, selector_string=selector_string, amplitude_tracking_enabled_raw=amplitude_tracking_enabled),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """ofdmmodacc_configure_averaging."""
        response = self._invoke(
            self._client.OFDMModAccCfgAveraging,
            grpc_types.OFDMModAccCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_channel_estimation_type(
        self, selector_string, channel_estimation_type
    ):
        """ofdmmodacc_configure_channel_estimation_type."""
        response = self._invoke(
            self._client.OFDMModAccCfgChannelEstimationType,
            grpc_types.OFDMModAccCfgChannelEstimationTypeRequest(instrument=self._vi, selector_string=selector_string, channel_estimation_type_raw=channel_estimation_type),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_common_clock_source_enabled(
        self, selector_string, common_clock_source_enabled
    ):
        """ofdmmodacc_configure_common_clock_source_enabled."""
        response = self._invoke(
            self._client.OFDMModAccCfgCommonClockSourceEnabled,
            grpc_types.OFDMModAccCfgCommonClockSourceEnabledRequest(instrument=self._vi, selector_string=selector_string, common_clock_source_enabled_raw=common_clock_source_enabled),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_evm_unit(self, selector_string, evm_unit):
        """ofdmmodacc_configure_evm_unit."""
        response = self._invoke(
            self._client.OFDMModAccCfgEVMUnit,
            grpc_types.OFDMModAccCfgEVMUnitRequest(instrument=self._vi, selector_string=selector_string, evm_unit_raw=evm_unit),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_frequency_error_estimation_method(
        self, selector_string, frequency_error_estimation_method
    ):
        """ofdmmodacc_configure_frequency_error_estimation_method."""
        response = self._invoke(
            self._client.OFDMModAccCfgFrequencyErrorEstimationMethod,
            grpc_types.OFDMModAccCfgFrequencyErrorEstimationMethodRequest(instrument=self._vi, selector_string=selector_string, frequency_error_estimation_method_raw=frequency_error_estimation_method),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_measurement_length(
        self, selector_string, measurement_offset, maximum_measurement_length
    ):
        """ofdmmodacc_configure_measurement_length."""
        response = self._invoke(
            self._client.OFDMModAccCfgMeasurementLength,
            grpc_types.OFDMModAccCfgMeasurementLengthRequest(instrument=self._vi, selector_string=selector_string, measurement_offset=measurement_offset, maximum_measurement_length=maximum_measurement_length),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_measurement_mode(self, selector_string, measurement_mode):
        """ofdmmodacc_configure_measurement_mode."""
        response = self._invoke(
            self._client.OFDMModAccCfgMeasurementMode,
            grpc_types.OFDMModAccCfgMeasurementModeRequest(instrument=self._vi, selector_string=selector_string, measurement_mode_raw=measurement_mode),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_noise_compensation_enabled(
        self, selector_string, noise_compensation_enabled
    ):
        """ofdmmodacc_configure_noise_compensation_enabled."""
        response = self._invoke(
            self._client.OFDMModAccCfgNoiseCompensationEnabled,
            grpc_types.OFDMModAccCfgNoiseCompensationEnabledRequest(instrument=self._vi, selector_string=selector_string, noise_compensation_enabled_raw=noise_compensation_enabled),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_optimize_dynamic_range_for_evm(
        self,
        selector_string,
        optimize_dynamic_range_for_evm_enabled,
        optimize_dynamic_range_for_evm_margin,
    ):
        """ofdmmodacc_configure_optimize_dynamic_range_for_evm."""
        response = self._invoke(
            self._client.OFDMModAccCfgOptimizeDynamicRangeForEVM,
            grpc_types.OFDMModAccCfgOptimizeDynamicRangeForEVMRequest(instrument=self._vi, selector_string=selector_string, optimize_dynamic_range_for_evm_enabled_raw=optimize_dynamic_range_for_evm_enabled, optimize_dynamic_range_for_evm_margin=optimize_dynamic_range_for_evm_margin),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_phase_tracking_enabled(self, selector_string, phase_tracking_enabled):
        """ofdmmodacc_configure_phase_tracking_enabled."""
        response = self._invoke(
            self._client.OFDMModAccCfgPhaseTrackingEnabled,
            grpc_types.OFDMModAccCfgPhaseTrackingEnabledRequest(instrument=self._vi, selector_string=selector_string, phase_tracking_enabled_raw=phase_tracking_enabled),  # type: ignore
        )
        return response.status

    def ofdmmodacc_configure_symbol_clock_error_correction_enabled(
        self, selector_string, symbol_clock_error_correction_enabled
    ):
        """ofdmmodacc_configure_symbol_clock_error_correction_enabled."""
        response = self._invoke(
            self._client.OFDMModAccCfgSymbolClockErrorCorrectionEnabled,
            grpc_types.OFDMModAccCfgSymbolClockErrorCorrectionEnabledRequest(instrument=self._vi, selector_string=selector_string, symbol_clock_error_correction_enabled_raw=symbol_clock_error_correction_enabled),  # type: ignore
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

    def sem_configure_mask_type(self, selector_string, mask_type):
        """sem_configure_mask_type."""
        response = self._invoke(
            self._client.SEMCfgMaskType,
            grpc_types.SEMCfgMaskTypeRequest(instrument=self._vi, selector_string=selector_string, mask_type_raw=mask_type),  # type: ignore
        )
        return response.status

    def sem_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """sem_configure_number_of_offsets."""
        response = self._invoke(
            self._client.SEMCfgNumberOfOffsets,
            grpc_types.SEMCfgNumberOfOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_offsets=number_of_offsets),  # type: ignore
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

    def sem_configure_offset_relative_limit_array(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeLimitArray,
            grpc_types.SEMCfgOffsetRelativeLimitArrayRequest(instrument=self._vi, selector_string=selector_string, relative_limit_start=relative_limit_start, relative_limit_stop=relative_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_span(self, selector_string, span_auto, span):
        """sem_configure_span."""
        response = self._invoke(
            self._client.SEMCfgSpan,
            grpc_types.SEMCfgSpanRequest(instrument=self._vi, selector_string=selector_string, span_auto_raw=span_auto, span=span),  # type: ignore
        )
        return response.status

    def sem_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """sem_configure_sweep_time."""
        response = self._invoke(
            self._client.SEMCfgSweepTime,
            grpc_types.SEMCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def configure_channel_bandwidth(self, selector_string, channel_bandwidth):
        """configure_channel_bandwidth."""
        response = self._invoke(
            self._client.CfgChannelBandwidth,
            grpc_types.CfgChannelBandwidthRequest(instrument=self._vi, selector_string=selector_string, channel_bandwidth=channel_bandwidth),  # type: ignore
        )
        return response.status

    def configure_external_attenuation(self, selector_string, external_attenuation):
        """configure_external_attenuation."""
        response = self._invoke(
            self._client.CfgExternalAttenuation,
            grpc_types.CfgExternalAttenuationRequest(instrument=self._vi, selector_string=selector_string, external_attenuation=external_attenuation),  # type: ignore
        )
        return response.status

    def configure_frequency_array(self, selector_string, center_frequency):
        """configure_frequency_array."""
        response = self._invoke(
            self._client.CfgFrequencyArray,
            grpc_types.CfgFrequencyArrayRequest(instrument=self._vi, selector_string=selector_string, center_frequency=center_frequency),  # type: ignore
        )
        return response.status

    def configure_frequency(self, selector_string, center_frequency):
        """configure_frequency."""
        response = self._invoke(
            self._client.CfgFrequency,
            grpc_types.CfgFrequencyRequest(instrument=self._vi, selector_string=selector_string, center_frequency=center_frequency),  # type: ignore
        )
        return response.status

    def configure_number_of_frequency_segments_and_receive_chains(
        self, selector_string, number_of_frequency_segments, number_of_receive_chains
    ):
        """configure_number_of_frequency_segments_and_receive_chains."""
        response = self._invoke(
            self._client.CfgNumberOfFrequencySegmentsAndReceiveChains,
            grpc_types.CfgNumberOfFrequencySegmentsAndReceiveChainsRequest(instrument=self._vi, selector_string=selector_string, number_of_frequency_segments=number_of_frequency_segments, number_of_receive_chains=number_of_receive_chains),  # type: ignore
        )
        return response.status

    def configure_reference_level(self, selector_string, reference_level):
        """configure_reference_level."""
        response = self._invoke(
            self._client.CfgReferenceLevel,
            grpc_types.CfgReferenceLevelRequest(instrument=self._vi, selector_string=selector_string, reference_level=reference_level),  # type: ignore
        )
        return response.status

    def configure_standard(self, selector_string, standard):
        """configure_standard."""
        response = self._invoke(
            self._client.CfgStandard,
            grpc_types.CfgStandardRequest(instrument=self._vi, selector_string=selector_string, standard_raw=standard),  # type: ignore
        )
        return response.status

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        response = self._invoke(
            self._client.TXPFetchMeasurement,
            grpc_types.TXPFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.average_power_mean, response.peak_power_maximum, response.status

    def dsssmodacc_fetch_average_powers(self, selector_string, timeout):
        """dsssmodacc_fetch_average_powers."""
        response = self._invoke(
            self._client.DSSSModAccFetchAveragePowers,
            grpc_types.DSSSModAccFetchAveragePowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.preamble_average_power_mean,
            response.header_average_power_mean,
            response.data_average_power_mean,
            response.ppdu_average_power_mean,
            response.status,
        )

    def dsssmodacc_fetch_evm(self, selector_string, timeout):
        """dsssmodacc_fetch_evm."""
        response = self._invoke(
            self._client.DSSSModAccFetchEVM,
            grpc_types.DSSSModAccFetchEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rms_evm_mean,
            response.peak_evm_80211_2016_maximum,
            response.peak_evm_80211_2007_maximum,
            response.peak_evm_80211_1999_maximum,
            response.frequency_error_mean,
            response.chip_clock_error_mean,
            response.number_of_chips_used,
            response.status,
        )

    def dsssmodacc_fetch_iq_impairments(self, selector_string, timeout):
        """dsssmodacc_fetch_iq_impairments."""
        response = self._invoke(
            self._client.DSSSModAccFetchIQImpairments,
            grpc_types.DSSSModAccFetchIQImpairmentsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.iq_origin_offset_mean,
            response.iq_gain_imbalance_mean,
            response.iq_quadrature_error_mean,
            response.status,
        )

    def dsssmodacc_fetch_peak_powers(self, selector_string, timeout):
        """dsssmodacc_fetch_peak_powers."""
        response = self._invoke(
            self._client.DSSSModAccFetchPeakPowers,
            grpc_types.DSSSModAccFetchPeakPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.preamble_peak_power_maximum,
            response.header_peak_power_maximum,
            response.data_peak_power_maximum,
            response.ppdu_peak_power_maximum,
            response.status,
        )

    def dsssmodacc_fetch_ppdu_information(self, selector_string, timeout):
        """dsssmodacc_fetch_ppdu_information."""
        response = self._invoke(
            self._client.DSSSModAccFetchPPDUInformation,
            grpc_types.DSSSModAccFetchPPDUInformationRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.DsssModAccDataModulationFormat(response.data_modulation_format),
            response.payload_length,
            enums.DsssModAccPreambleType(response.preamble_type),
            response.locked_clocks_bit,
            enums.DsssModAccPayloadHeaderCrcStatus(response.header_crc_status),
            enums.DsssModAccPsduCrcStatus(response.psdu_crc_status),
            response.status,
        )

    def powerramp_fetch_measurement(self, selector_string, timeout):
        """powerramp_fetch_measurement."""
        response = self._invoke(
            self._client.PowerRampFetchMeasurement,
            grpc_types.PowerRampFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.rise_time_mean, response.fall_time_mean, response.status

    def ofdmmodacc_fetch_chain_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_chain_rms_evm."""
        response = self._invoke(
            self._client.OFDMModAccFetchChainRMSEVM,
            grpc_types.OFDMModAccFetchChainRMSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.chain_rms_evm_mean,
            response.chain_data_rms_evm_mean,
            response.chain_pilot_rms_evm_mean,
            response.status,
        )

    def ofdmmodacc_fetch_composite_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_composite_rms_evm."""
        response = self._invoke(
            self._client.OFDMModAccFetchCompositeRMSEVM,
            grpc_types.OFDMModAccFetchCompositeRMSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.composite_rms_evm_mean,
            response.composite_data_rms_evm_mean,
            response.composite_pilot_rms_evm_mean,
            response.status,
        )

    def ofdmmodacc_fetch_cross_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_cross_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchCrossPower,
            grpc_types.OFDMModAccFetchCrossPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.cross_power_mean, response.status

    def ofdmmodacc_fetch_data_average_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_data_average_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchDataAveragePower,
            grpc_types.OFDMModAccFetchDataAveragePowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.data_average_power_mean, response.status

    def ofdmmodacc_fetch_data_peak_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_data_peak_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchDataPeakPower,
            grpc_types.OFDMModAccFetchDataPeakPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.data_peak_power_maximum, response.status

    def ofdmmodacc_fetch_frequency_error_ccdf_10_percent(self, selector_string, timeout):
        """ofdmmodacc_fetch_frequency_error_ccdf_10_percent."""
        response = self._invoke(
            self._client.OFDMModAccFetchFrequencyErrorCCDF10Percent,
            grpc_types.OFDMModAccFetchFrequencyErrorCCDF10PercentRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency_error_ccdf_10_percent, response.status

    def ofdmmodacc_fetch_frequency_error_mean(self, selector_string, timeout):
        """ofdmmodacc_fetch_frequency_error_mean."""
        response = self._invoke(
            self._client.OFDMModAccFetchFrequencyErrorMean,
            grpc_types.OFDMModAccFetchFrequencyErrorMeanRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency_error_mean, response.status

    def ofdmmodacc_fetch_guard_interval_type(self, selector_string, timeout):
        """ofdmmodacc_fetch_guard_interval_type."""
        response = self._invoke(
            self._client.OFDMModAccFetchGuardIntervalType,
            grpc_types.OFDMModAccFetchGuardIntervalTypeRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.OfdmGuardIntervalType(response.guard_interval_type), response.status

    def ofdmmodacc_fetch_ltf_size(self, selector_string, timeout):
        """ofdmmodacc_fetch_ltf_size."""
        response = self._invoke(
            self._client.OFDMModAccFetchLTFSize,
            grpc_types.OFDMModAccFetchLTFSizeRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.OfdmLtfSize(response.ltf_size), response.status

    def ofdmmodacc_fetch_iq_impairments(self, selector_string, timeout):
        """ofdmmodacc_fetch_iq_impairments."""
        response = self._invoke(
            self._client.OFDMModAccFetchIQImpairments,
            grpc_types.OFDMModAccFetchIQImpairmentsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.relative_iq_origin_offset_mean,
            response.iq_gain_imbalance_mean,
            response.iq_quadrature_error_mean,
            response.absolute_iq_origin_offset_mean,
            response.iq_timing_skew_mean,
            response.status,
        )

    def ofdmmodacc_fetch_l_sig_parity_check_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_l_sig_parity_check_status."""
        response = self._invoke(
            self._client.OFDMModAccFetchLSIGParityCheckStatus,
            grpc_types.OFDMModAccFetchLSIGParityCheckStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.OfdmModAccLSigParityCheckStatus(response.l_sig_parity_check_status),
            response.status,
        )

    def ofdmmodacc_fetch_mcs_index(self, selector_string, timeout):
        """ofdmmodacc_fetch_mcs_index."""
        response = self._invoke(
            self._client.OFDMModAccFetchMCSIndex,
            grpc_types.OFDMModAccFetchMCSIndexRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mcs_index, response.status

    def ofdmmodacc_fetch_number_of_he_sig_b_symbols(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_he_sig_b_symbols."""
        response = self._invoke(
            self._client.OFDMModAccFetchNumberOfHESIGBSymbols,
            grpc_types.OFDMModAccFetchNumberOfHESIGBSymbolsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.number_of_he_sig_b_symbols, response.status

    def ofdmmodacc_fetch_number_of_space_time_streams(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_space_time_streams."""
        response = self._invoke(
            self._client.OFDMModAccFetchNumberOfSpaceTimeStreams,
            grpc_types.OFDMModAccFetchNumberOfSpaceTimeStreamsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.number_of_space_time_streams, response.status

    def ofdmmodacc_fetch_number_of_symbols_used(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_symbols_used."""
        response = self._invoke(
            self._client.OFDMModAccFetchNumberofSymbolsUsed,
            grpc_types.OFDMModAccFetchNumberofSymbolsUsedRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.number_of_symbols_used, response.status

    def ofdmmodacc_fetch_number_of_users(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_users."""
        response = self._invoke(
            self._client.OFDMModAccFetchNumberOfUsers,
            grpc_types.OFDMModAccFetchNumberOfUsersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.number_of_users, response.status

    def ofdmmodacc_fetch_pe_average_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_pe_average_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchPEAveragePower,
            grpc_types.OFDMModAccFetchPEAveragePowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pe_average_power_mean, response.status

    def ofdmmodacc_fetch_pe_peak_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_pe_peak_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchPEPeakPower,
            grpc_types.OFDMModAccFetchPEPeakPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pe_peak_power_maximum, response.status

    def ofdmmodacc_fetch_ppdu_average_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_ppdu_average_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchPPDUAveragePower,
            grpc_types.OFDMModAccFetchPPDUAveragePowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.ppdu_average_power_mean, response.status

    def ofdmmodacc_fetch_ppdu_peak_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_ppdu_peak_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchPPDUPeakPower,
            grpc_types.OFDMModAccFetchPPDUPeakPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.ppdu_peak_power_maximum, response.status

    def ofdmmodacc_fetch_ppdu_type(self, selector_string, timeout):
        """ofdmmodacc_fetch_ppdu_type."""
        response = self._invoke(
            self._client.OFDMModAccFetchPPDUType,
            grpc_types.OFDMModAccFetchPPDUTypeRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.OfdmPpduType(response.ppdu_type), response.status

    def ofdmmodacc_fetch_preamble_average_powers_802_11ac(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11ac."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreambleAveragePowers80211ac,
            grpc_types.OFDMModAccFetchPreambleAveragePowers80211acRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.vht_sig_a_average_power_mean,
            response.vht_stf_average_power_mean,
            response.vht_ltf_average_power_mean,
            response.vht_sig_b_average_power_mean,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_average_powers_802_11ax(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11ax."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreambleAveragePowers80211ax,
            grpc_types.OFDMModAccFetchPreambleAveragePowers80211axRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rl_sig_average_power_mean,
            response.he_sig_a_average_power_mean,
            response.he_sig_b_average_power_mean,
            response.he_stf_average_power_mean,
            response.he_ltf_average_power_mean,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_average_powers_802_11be(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11be."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreambleAveragePowers80211be,
            grpc_types.OFDMModAccFetchPreambleAveragePowers80211beRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rl_sig_average_power_mean,
            response.u_sig_average_power_mean,
            response.eht_sig_average_power_mean,
            response.eht_stf_average_power_mean,
            response.eht_ltf_average_power_mean,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_average_powers_802_11n(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11n."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreambleAveragePowers80211n,
            grpc_types.OFDMModAccFetchPreambleAveragePowers80211nRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.ht_sig_average_power_mean,
            response.ht_stf_average_power_mean,
            response.ht_dltf_average_power_mean,
            response.ht_eltf_average_power_mean,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_average_powers_common(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_common."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreambleAveragePowersCommon,
            grpc_types.OFDMModAccFetchPreambleAveragePowersCommonRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.l_stf_average_power_mean,
            response.l_ltf_average_power_mean,
            response.l_sig_average_power_mean,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11ac(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11ac."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreamblePeakPowers80211ac,
            grpc_types.OFDMModAccFetchPreamblePeakPowers80211acRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.vht_sig_a_peak_power_maximum,
            response.vht_stf_peak_power_maximum,
            response.vht_ltf_peak_power_maximum,
            response.vht_sig_b_peak_power_maximum,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11ax(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11ax."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreamblePeakPowers80211ax,
            grpc_types.OFDMModAccFetchPreamblePeakPowers80211axRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rl_sig_peak_power_maximum,
            response.he_sig_a_peak_power_maximum,
            response.he_sig_b_peak_power_maximum,
            response.he_stf_peak_power_maximum,
            response.he_ltf_peak_power_maximum,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11be(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11be."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreamblePeakPowers80211be,
            grpc_types.OFDMModAccFetchPreamblePeakPowers80211beRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rl_sig_peak_power_maximum,
            response.u_sig_peak_power_maximum,
            response.eht_sig_peak_power_maximum,
            response.eht_stf_peak_power_maximum,
            response.eht_ltf_peak_power_maximum,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11n(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11n."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreamblePeakPowers80211n,
            grpc_types.OFDMModAccFetchPreamblePeakPowers80211nRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.ht_sig_peak_power_maximum,
            response.ht_stf_peak_power_maximum,
            response.ht_dltf_peak_power_maximum,
            response.ht_eltf_peak_power_maximum,
            response.status,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_common(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_common."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreamblePeakPowersCommon,
            grpc_types.OFDMModAccFetchPreamblePeakPowersCommonRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.l_stf_peak_power_maximum,
            response.l_ltf_peak_power_maximum,
            response.l_sig_peak_power_maximum,
            response.status,
        )

    def ofdmmodacc_fetch_psdu_crc_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_psdu_crc_status."""
        response = self._invoke(
            self._client.OFDMModAccFetchPSDUCRCStatus,
            grpc_types.OFDMModAccFetchPSDUCRCStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.OfdmModAccPsduCrcStatus(response.psdu_crc_status), response.status

    def ofdmmodacc_fetch_pe_duration(self, selector_string, timeout):
        """ofdmmodacc_fetch_pe_duration."""
        response = self._invoke(
            self._client.OFDMModAccFetchPEDuration,
            grpc_types.OFDMModAccFetchPEDurationRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pe_duration, response.status

    def ofdmmodacc_fetch_ru_offset_and_size(self, selector_string, timeout):
        """ofdmmodacc_fetch_ru_offset_and_size."""
        response = self._invoke(
            self._client.OFDMModAccFetchRUOffsetAndSize,
            grpc_types.OFDMModAccFetchRUOffsetAndSizeRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.ru_offset, response.ru_size, response.status

    def ofdmmodacc_fetch_sig_crc_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_sig_crc_status."""
        response = self._invoke(
            self._client.OFDMModAccFetchSIGCRCStatus,
            grpc_types.OFDMModAccFetchSIGCRCStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.OfdmModAccSigCrcStatus(response.sig_crc_status), response.status

    def ofdmmodacc_fetch_sig_b_crc_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_sig_b_crc_status."""
        response = self._invoke(
            self._client.OFDMModAccFetchSIGBCRCStatus,
            grpc_types.OFDMModAccFetchSIGBCRCStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.OfdmModAccSigBCrcStatus(response.sig_b_crc_status), response.status

    def ofdmmodacc_fetch_spectral_flatness(self, selector_string, timeout):
        """ofdmmodacc_fetch_spectral_flatness."""
        response = self._invoke(
            self._client.OFDMModAccFetchSpectralFlatness,
            grpc_types.OFDMModAccFetchSpectralFlatnessRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.spectral_flatness_margin,
            response.spectral_flatness_margin_subcarrier_index,
            response.status,
        )

    def ofdmmodacc_fetch_stream_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_stream_rms_evm."""
        response = self._invoke(
            self._client.OFDMModAccFetchStreamRMSEVM,
            grpc_types.OFDMModAccFetchStreamRMSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.stream_rms_evm_mean,
            response.stream_data_rms_evm_mean,
            response.stream_pilot_rms_evm_mean,
            response.status,
        )

    def ofdmmodacc_fetch_symbol_clock_error_mean(self, selector_string, timeout):
        """ofdmmodacc_fetch_symbol_clock_error_mean."""
        response = self._invoke(
            self._client.OFDMModAccFetchSymbolClockErrorMean,
            grpc_types.OFDMModAccFetchSymbolClockErrorMeanRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.symbol_clock_error_mean, response.status

    def ofdmmodacc_fetch_unused_tone_error(self, selector_string, timeout):
        """ofdmmodacc_fetch_unused_tone_error."""
        response = self._invoke(
            self._client.OFDMModAccFetchUnusedToneError,
            grpc_types.OFDMModAccFetchUnusedToneErrorRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.unused_tone_error_margin,
            response.unused_tone_error_margin_ru_index,
            response.status,
        )

    def ofdmmodacc_fetch_user_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_user_power."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserPower,
            grpc_types.OFDMModAccFetchUserPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.user_power_mean, response.status

    def ofdmmodacc_fetch_user_stream_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_user_stream_rms_evm."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserStreamRMSEVM,
            grpc_types.OFDMModAccFetchUserStreamRMSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.user_stream_rms_evm_mean,
            response.user_stream_data_rms_evm_mean,
            response.user_stream_pilot_rms_evm_mean,
            response.status,
        )

    def sem_fetch_carrier_measurement(self, selector_string, timeout):
        """sem_fetch_carrier_measurement."""
        response = self._invoke(
            self._client.SEMFetchCarrierMeasurement,
            grpc_types.SEMFetchCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power, response.relative_power, response.status

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

    def dsssmodacc_fetch_constellation_trace(self, selector_string, timeout, constellation):
        """dsssmodacc_fetch_constellation_trace."""
        response = self._invoke(
            self._client.DSSSModAccFetchConstellationTraceInterleavedIQ,
            grpc_types.DSSSModAccFetchConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(constellation, "constellation", "complex64")
        if len(constellation) != response.actual_array_size // 2:
            constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.constellation, dtype=numpy.float32)
        constellation[:] = flat.view(numpy.complex64)
        return response.status

    def dsssmodacc_fetch_custom_gate_powers_array(self, selector_string, timeout):
        """dsssmodacc_fetch_custom_gate_powers_array."""
        response = self._invoke(
            self._client.DSSSModAccFetchCustomGatePowersArray,
            grpc_types.DSSSModAccFetchCustomGatePowersArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.average_power_mean[:], response.peak_power_maximum[:], response.status

    def dsssmodacc_fetch_decoded_header_bits_trace(self, selector_string, timeout):
        """dsssmodacc_fetch_decoded_header_bits_trace."""
        response = self._invoke(
            self._client.DSSSModAccFetchDecodedHeaderBitsTrace,
            grpc_types.DSSSModAccFetchDecodedHeaderBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_header_bits[:], response.status

    def dsssmodacc_fetch_decoded_psdu_bits_trace(self, selector_string, timeout):
        """dsssmodacc_fetch_decoded_psdu_bits_trace."""
        response = self._invoke(
            self._client.DSSSModAccFetchDecodedPSDUBitsTrace,
            grpc_types.DSSSModAccFetchDecodedPSDUBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_psdu_bits[:], response.status

    def dsssmodacc_fetch_evm_per_chip_mean_trace(self, selector_string, timeout, evm_per_chip_mean):
        """dsssmodacc_fetch_evm_per_chip_mean_trace."""
        response = self._invoke(
            self._client.DSSSModAccFetchEVMPerChipMeanTrace,
            grpc_types.DSSSModAccFetchEVMPerChipMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(evm_per_chip_mean, "evm_per_chip_mean", "float32")
        if len(evm_per_chip_mean) != response.actual_array_size:
            evm_per_chip_mean.resize((response.actual_array_size,), refcheck=False)
        evm_per_chip_mean.flat[:] = response.evm_per_chip_mean
        return response.x0, response.dx, response.status

    def powerramp_fetch_fall_trace(
        self, selector_string, timeout, raw_waveform, processed_waveform, threshold, power_reference
    ):
        """powerramp_fetch_fall_trace."""
        response = self._invoke(
            self._client.PowerRampFetchFallTrace,
            grpc_types.PowerRampFetchFallTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(raw_waveform, "raw_waveform", "float32")
        if len(raw_waveform) != response.actual_array_size:
            raw_waveform.resize((response.actual_array_size,), refcheck=False)
        raw_waveform.flat[:] = response.raw_waveform
        _helper.validate_numpy_array(processed_waveform, "processed_waveform", "float32")
        if len(processed_waveform) != response.actual_array_size:
            processed_waveform.resize((response.actual_array_size,), refcheck=False)
        processed_waveform.flat[:] = response.processed_waveform
        _helper.validate_numpy_array(threshold, "threshold", "float32")
        if len(threshold) != response.actual_array_size:
            threshold.resize((response.actual_array_size,), refcheck=False)
        threshold.flat[:] = response.threshold
        _helper.validate_numpy_array(power_reference, "power_reference", "float32")
        if len(power_reference) != response.actual_array_size:
            power_reference.resize((response.actual_array_size,), refcheck=False)
        power_reference.flat[:] = response.power_reference
        return response.x0, response.dx, response.status

    def powerramp_fetch_rise_trace(
        self, selector_string, timeout, raw_waveform, processed_waveform, threshold, power_reference
    ):
        """powerramp_fetch_rise_trace."""
        response = self._invoke(
            self._client.PowerRampFetchRiseTrace,
            grpc_types.PowerRampFetchRiseTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(raw_waveform, "raw_waveform", "float32")
        if len(raw_waveform) != response.actual_array_size:
            raw_waveform.resize((response.actual_array_size,), refcheck=False)
        raw_waveform.flat[:] = response.raw_waveform
        _helper.validate_numpy_array(processed_waveform, "processed_waveform", "float32")
        if len(processed_waveform) != response.actual_array_size:
            processed_waveform.resize((response.actual_array_size,), refcheck=False)
        processed_waveform.flat[:] = response.processed_waveform
        _helper.validate_numpy_array(threshold, "threshold", "float32")
        if len(threshold) != response.actual_array_size:
            threshold.resize((response.actual_array_size,), refcheck=False)
        threshold.flat[:] = response.threshold
        _helper.validate_numpy_array(power_reference, "power_reference", "float32")
        if len(power_reference) != response.actual_array_size:
            power_reference.resize((response.actual_array_size,), refcheck=False)
        power_reference.flat[:] = response.power_reference
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_chain_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_data_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_chain_data_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            chain_data_rms_evm_per_symbol_mean, "chain_data_rms_evm_per_symbol_mean", "float32"
        )
        if len(chain_data_rms_evm_per_symbol_mean) != response.actual_array_size:
            chain_data_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        chain_data_rms_evm_per_symbol_mean.flat[:] = response.chain_data_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_chain_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_pilot_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_chain_pilot_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            chain_pilot_rms_evm_per_symbol_mean, "chain_pilot_rms_evm_per_symbol_mean", "float32"
        )
        if len(chain_pilot_rms_evm_per_symbol_mean) != response.actual_array_size:
            chain_pilot_rms_evm_per_symbol_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        chain_pilot_rms_evm_per_symbol_mean.flat[:] = response.chain_pilot_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_chain_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, chain_rms_evm_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_chain_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace,
            grpc_types.OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            chain_rms_evm_per_subcarrier_mean, "chain_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(chain_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            chain_rms_evm_per_subcarrier_mean.resize((response.actual_array_size,), refcheck=False)
        chain_rms_evm_per_subcarrier_mean.flat[:] = response.chain_rms_evm_per_subcarrier_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_chain_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_chain_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchChainRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            chain_rms_evm_per_symbol_mean, "chain_rms_evm_per_symbol_mean", "float32"
        )
        if len(chain_rms_evm_per_symbol_mean) != response.actual_array_size:
            chain_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        chain_rms_evm_per_symbol_mean.flat[:] = response.chain_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_channel_frequency_response_mean_trace(
        self,
        selector_string,
        timeout,
        channel_frequency_response_mean_magnitude,
        channel_frequency_response_mean_phase,
    ):
        """ofdmmodacc_fetch_channel_frequency_response_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchChannelFrequencyResponseMeanTrace,
            grpc_types.OFDMModAccFetchChannelFrequencyResponseMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            channel_frequency_response_mean_magnitude,
            "channel_frequency_response_mean_magnitude",
            "float32",
        )
        if len(channel_frequency_response_mean_magnitude) != response.actual_array_size:
            channel_frequency_response_mean_magnitude.resize(
                (response.actual_array_size,), refcheck=False
            )
        channel_frequency_response_mean_magnitude.flat[:] = (
            response.channel_frequency_response_mean_magnitude
        )
        _helper.validate_numpy_array(
            channel_frequency_response_mean_phase,
            "channel_frequency_response_mean_phase",
            "float32",
        )
        if len(channel_frequency_response_mean_phase) != response.actual_array_size:
            channel_frequency_response_mean_phase.resize(
                (response.actual_array_size,), refcheck=False
            )
        channel_frequency_response_mean_phase.flat[:] = (
            response.channel_frequency_response_mean_phase
        )
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_group_delay_mean_trace(self, selector_string, timeout, group_delay_mean):
        """ofdmmodacc_fetch_group_delay_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchGroupDelayMeanTrace,
            grpc_types.OFDMModAccFetchGroupDelayMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(group_delay_mean, "group_delay_mean", "float32")
        if len(group_delay_mean) != response.actual_array_size:
            group_delay_mean.resize((response.actual_array_size,), refcheck=False)
        group_delay_mean.flat[:] = response.group_delay_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_common_pilot_error_trace(
        self, selector_string, timeout, common_pilot_error_magnitude, common_pilot_error_phase
    ):
        """ofdmmodacc_fetch_common_pilot_error_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchCommonPilotErrorTrace,
            grpc_types.OFDMModAccFetchCommonPilotErrorTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            common_pilot_error_magnitude, "common_pilot_error_magnitude", "float32"
        )
        if len(common_pilot_error_magnitude) != response.actual_array_size:
            common_pilot_error_magnitude.resize((response.actual_array_size,), refcheck=False)
        common_pilot_error_magnitude.flat[:] = response.common_pilot_error_magnitude
        _helper.validate_numpy_array(
            common_pilot_error_phase, "common_pilot_error_phase", "float32"
        )
        if len(common_pilot_error_phase) != response.actual_array_size:
            common_pilot_error_phase.resize((response.actual_array_size,), refcheck=False)
        common_pilot_error_phase.flat[:] = response.common_pilot_error_phase
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_custom_gate_powers_array(self, selector_string, timeout):
        """ofdmmodacc_fetch_custom_gate_powers_array."""
        response = self._invoke(
            self._client.OFDMModAccFetchCustomGatePowersArray,
            grpc_types.OFDMModAccFetchCustomGatePowersArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.average_power_mean[:], response.peak_power_maximum[:], response.status

    def ofdmmodacc_fetch_data_constellation_trace(
        self, selector_string, timeout, data_constellation
    ):
        """ofdmmodacc_fetch_data_constellation_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDataConstellationTraceInterleavedIQ,
            grpc_types.OFDMModAccFetchDataConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != response.actual_array_size // 2:
            data_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.data_constellation, dtype=numpy.float32)
        data_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def ofdmmodacc_fetch_reference_data_constellation_trace(
        self, selector_string, timeout, reference_data_constellation
    ):
        """ofdmmodacc_fetch_reference_data_constellation_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchReferenceDataConstellationTraceInterleavedIQ,
            grpc_types.OFDMModAccFetchReferenceDataConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            reference_data_constellation, "reference_data_constellation", "complex64"
        )
        if len(reference_data_constellation) != response.actual_array_size // 2:
            reference_data_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.reference_data_constellation, dtype=numpy.float32)
        reference_data_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def ofdmmodacc_fetch_decoded_l_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_l_sig_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedLSIGBitsTrace,
            grpc_types.OFDMModAccFetchDecodedLSIGBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_l_sig_bits[:], response.status

    def ofdmmodacc_fetch_decoded_psdu_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_psdu_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedPSDUBitsTrace,
            grpc_types.OFDMModAccFetchDecodedPSDUBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_psdu_bits[:], response.status

    def ofdmmodacc_fetch_decoded_service_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_service_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedServiceBitsTrace,
            grpc_types.OFDMModAccFetchDecodedServiceBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_service_bits[:], response.status

    def ofdmmodacc_fetch_decoded_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_sig_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedSIGBitsTrace,
            grpc_types.OFDMModAccFetchDecodedSIGBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_sig_bits[:], response.status

    def ofdmmodacc_fetch_decoded_sig_b_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_sig_b_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedSIGBBitsTrace,
            grpc_types.OFDMModAccFetchDecodedSIGBBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_sig_b_bits[:], response.status

    def ofdmmodacc_fetch_decoded_u_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_u_sig_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedUSIGBitsTrace,
            grpc_types.OFDMModAccFetchDecodedUSIGBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_u_sig_bits[:], response.status

    def ofdmmodacc_fetch_decoded_eht_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_eht_sig_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedEHTSIGBitsTrace,
            grpc_types.OFDMModAccFetchDecodedEHTSIGBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_eht_sig_bits[:], response.status

    def ofdmmodacc_fetch_decoded_uhr_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_uhr_sig_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedUHRSIGBitsTrace,
            grpc_types.OFDMModAccFetchDecodedUHRSIGBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_uhr_sig_bits[:], response.status

    def ofdmmodacc_fetch_decoded_elr_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_elr_sig_bits_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchDecodedELRSIGBitsTrace,
            grpc_types.OFDMModAccFetchDecodedELRSIGBitsTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.decoded_elr_sig_bits[:], response.status

    def ofdmmodacc_fetch_evm_subcarrier_indices(self, selector_string, timeout):
        """ofdmmodacc_fetch_evm_subcarrier_indices."""
        response = self._invoke(
            self._client.OFDMModAccFetchEVMSubcarrierIndices,
            grpc_types.OFDMModAccFetchEVMSubcarrierIndicesRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.subcarrier_indices[:], response.status

    def ofdmmodacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace,
            grpc_types.OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
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

    def ofdmmodacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace,
            grpc_types.OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
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

    def ofdmmodacc_fetch_pilot_constellation_trace(
        self, selector_string, timeout, pilot_constellation
    ):
        """ofdmmodacc_fetch_pilot_constellation_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchPilotConstellationTraceInterleavedIQ,
            grpc_types.OFDMModAccFetchPilotConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(pilot_constellation, "pilot_constellation", "complex64")
        if len(pilot_constellation) != response.actual_array_size // 2:
            pilot_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pilot_constellation, dtype=numpy.float32)
        pilot_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def ofdmmodacc_fetch_preamble_frequency_error_trace(
        self, selector_string, timeout, preamble_frequency_error
    ):
        """ofdmmodacc_fetch_preamble_frequency_error_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchPreambleFrequencyErrorTrace,
            grpc_types.OFDMModAccFetchPreambleFrequencyErrorTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            preamble_frequency_error, "preamble_frequency_error", "float32"
        )
        if len(preamble_frequency_error) != response.actual_array_size:
            preamble_frequency_error.resize((response.actual_array_size,), refcheck=False)
        preamble_frequency_error.flat[:] = response.preamble_frequency_error
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_spectral_flatness_mean_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness_mean,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        """ofdmmodacc_fetch_spectral_flatness_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchSpectralFlatnessMeanTrace,
            grpc_types.OFDMModAccFetchSpectralFlatnessMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectral_flatness_mean, "spectral_flatness_mean", "float32")
        if len(spectral_flatness_mean) != response.actual_array_size:
            spectral_flatness_mean.resize((response.actual_array_size,), refcheck=False)
        spectral_flatness_mean.flat[:] = response.spectral_flatness_mean
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

    def ofdmmodacc_fetch_stream_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_data_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_stream_data_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            stream_data_rms_evm_per_symbol_mean, "stream_data_rms_evm_per_symbol_mean", "float32"
        )
        if len(stream_data_rms_evm_per_symbol_mean) != response.actual_array_size:
            stream_data_rms_evm_per_symbol_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        stream_data_rms_evm_per_symbol_mean.flat[:] = response.stream_data_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_stream_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_pilot_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_stream_pilot_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            stream_pilot_rms_evm_per_symbol_mean, "stream_pilot_rms_evm_per_symbol_mean", "float32"
        )
        if len(stream_pilot_rms_evm_per_symbol_mean) != response.actual_array_size:
            stream_pilot_rms_evm_per_symbol_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        stream_pilot_rms_evm_per_symbol_mean.flat[:] = response.stream_pilot_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_stream_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, stream_rms_evm_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_stream_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace,
            grpc_types.OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            stream_rms_evm_per_subcarrier_mean, "stream_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(stream_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            stream_rms_evm_per_subcarrier_mean.resize((response.actual_array_size,), refcheck=False)
        stream_rms_evm_per_subcarrier_mean.flat[:] = response.stream_rms_evm_per_subcarrier_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_stream_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_stream_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchStreamRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            stream_rms_evm_per_symbol_mean, "stream_rms_evm_per_symbol_mean", "float32"
        )
        if len(stream_rms_evm_per_symbol_mean) != response.actual_array_size:
            stream_rms_evm_per_symbol_mean.resize((response.actual_array_size,), refcheck=False)
        stream_rms_evm_per_symbol_mean.flat[:] = response.stream_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_subcarrier_chain_evm_per_symbol_trace(
        self, selector_string, timeout, subcarrier_index, subcarrier_chain_evm_per_symbol
    ):
        """ofdmmodacc_fetch_subcarrier_chain_evm_per_symbol_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace,
            grpc_types.OFDMModAccFetchSubcarrierChainEVMPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, subcarrier_index=subcarrier_index),  # type: ignore
        )
        _helper.validate_numpy_array(
            subcarrier_chain_evm_per_symbol, "subcarrier_chain_evm_per_symbol", "float32"
        )
        if len(subcarrier_chain_evm_per_symbol) != response.actual_array_size:
            subcarrier_chain_evm_per_symbol.resize((response.actual_array_size,), refcheck=False)
        subcarrier_chain_evm_per_symbol.flat[:] = response.subcarrier_chain_evm_per_symbol
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_subcarrier_stream_evm_per_symbol_trace(
        self, selector_string, timeout, subcarrier_index, subcarrier_stream_evm_per_symbol
    ):
        """ofdmmodacc_fetch_subcarrier_stream_evm_per_symbol_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace,
            grpc_types.OFDMModAccFetchSubcarrierStreamEVMPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, subcarrier_index=subcarrier_index),  # type: ignore
        )
        _helper.validate_numpy_array(
            subcarrier_stream_evm_per_symbol, "subcarrier_stream_evm_per_symbol", "float32"
        )
        if len(subcarrier_stream_evm_per_symbol) != response.actual_array_size:
            subcarrier_stream_evm_per_symbol.resize((response.actual_array_size,), refcheck=False)
        subcarrier_stream_evm_per_symbol.flat[:] = response.subcarrier_stream_evm_per_symbol
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_symbol_chain_evm_per_subcarrier_trace(
        self, selector_string, timeout, symbol_index, symbol_chain_evm_per_subcarrier
    ):
        """ofdmmodacc_fetch_symbol_chain_evm_per_subcarrier_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace,
            grpc_types.OFDMModAccFetchSymbolChainEVMPerSubcarrierTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, symbol_index=symbol_index),  # type: ignore
        )
        _helper.validate_numpy_array(
            symbol_chain_evm_per_subcarrier, "symbol_chain_evm_per_subcarrier", "float32"
        )
        if len(symbol_chain_evm_per_subcarrier) != response.actual_array_size:
            symbol_chain_evm_per_subcarrier.resize((response.actual_array_size,), refcheck=False)
        symbol_chain_evm_per_subcarrier.flat[:] = response.symbol_chain_evm_per_subcarrier
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_symbol_stream_evm_per_subcarrier_trace(
        self, selector_string, timeout, symbol_index, symbol_stream_evm_per_subcarrier
    ):
        """ofdmmodacc_fetch_symbol_stream_evm_per_subcarrier_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace,
            grpc_types.OFDMModAccFetchSymbolStreamEVMPerSubcarrierTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, symbol_index=symbol_index),  # type: ignore
        )
        _helper.validate_numpy_array(
            symbol_stream_evm_per_subcarrier, "symbol_stream_evm_per_subcarrier", "float32"
        )
        if len(symbol_stream_evm_per_subcarrier) != response.actual_array_size:
            symbol_stream_evm_per_subcarrier.resize((response.actual_array_size,), refcheck=False)
        symbol_stream_evm_per_subcarrier.flat[:] = response.symbol_stream_evm_per_subcarrier
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_unused_tone_error_margin_per_ru(
        self, selector_string, timeout, unused_tone_error_margin_per_ru
    ):
        """ofdmmodacc_fetch_unused_tone_error_margin_per_ru."""
        response = self._invoke(
            self._client.OFDMModAccFetchUnusedToneErrorMarginPerRU,
            grpc_types.OFDMModAccFetchUnusedToneErrorMarginPerRURequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            unused_tone_error_margin_per_ru, "unused_tone_error_margin_per_ru", "float64"
        )
        if len(unused_tone_error_margin_per_ru) != response.actual_array_size:
            unused_tone_error_margin_per_ru.resize((response.actual_array_size,), refcheck=False)
        unused_tone_error_margin_per_ru.flat[:] = response.unused_tone_error_margin_per_ru
        return response.status

    def ofdmmodacc_fetch_unused_tone_error_mean_trace(
        self, selector_string, timeout, unused_tone_error, unused_tone_error_mask
    ):
        """ofdmmodacc_fetch_unused_tone_error_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUnusedToneErrorMeanTrace,
            grpc_types.OFDMModAccFetchUnusedToneErrorMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(unused_tone_error, "unused_tone_error", "float32")
        if len(unused_tone_error) != response.actual_array_size:
            unused_tone_error.resize((response.actual_array_size,), refcheck=False)
        unused_tone_error.flat[:] = response.unused_tone_error
        _helper.validate_numpy_array(unused_tone_error_mask, "unused_tone_error_mask", "float32")
        if len(unused_tone_error_mask) != response.actual_array_size:
            unused_tone_error_mask.resize((response.actual_array_size,), refcheck=False)
        unused_tone_error_mask.flat[:] = response.unused_tone_error_mask
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_user_data_constellation_trace(
        self, selector_string, timeout, user_data_constellation
    ):
        """ofdmmodacc_fetch_user_data_constellation_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserDataConstellationTraceInterleavedIQ,
            grpc_types.OFDMModAccFetchUserDataConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            user_data_constellation, "user_data_constellation", "complex64"
        )
        if len(user_data_constellation) != response.actual_array_size // 2:
            user_data_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.user_data_constellation, dtype=numpy.float32)
        user_data_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def ofdmmodacc_fetch_user_pilot_constellation_trace(
        self, selector_string, timeout, user_pilot_constellation
    ):
        """ofdmmodacc_fetch_user_pilot_constellation_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserPilotConstellationTraceInterleavedIQ,
            grpc_types.OFDMModAccFetchUserPilotConstellationTraceInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            user_pilot_constellation, "user_pilot_constellation", "complex64"
        )
        if len(user_pilot_constellation) != response.actual_array_size // 2:
            user_pilot_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.user_pilot_constellation, dtype=numpy.float32)
        user_pilot_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def ofdmmodacc_fetch_user_stream_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_data_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_user_stream_data_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            user_stream_data_rms_evm_per_symbol_mean,
            "user_stream_data_rms_evm_per_symbol_mean",
            "float32",
        )
        if len(user_stream_data_rms_evm_per_symbol_mean) != response.actual_array_size:
            user_stream_data_rms_evm_per_symbol_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        user_stream_data_rms_evm_per_symbol_mean.flat[:] = (
            response.user_stream_data_rms_evm_per_symbol_mean
        )
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_user_stream_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_pilot_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_user_stream_pilot_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            user_stream_pilot_rms_evm_per_symbol_mean,
            "user_stream_pilot_rms_evm_per_symbol_mean",
            "float32",
        )
        if len(user_stream_pilot_rms_evm_per_symbol_mean) != response.actual_array_size:
            user_stream_pilot_rms_evm_per_symbol_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        user_stream_pilot_rms_evm_per_symbol_mean.flat[:] = (
            response.user_stream_pilot_rms_evm_per_symbol_mean
        )
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_user_stream_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, user_stream_rms_evm_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_user_stream_rms_evm_per_subcarrier_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace,
            grpc_types.OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            user_stream_rms_evm_per_subcarrier_mean,
            "user_stream_rms_evm_per_subcarrier_mean",
            "float32",
        )
        if len(user_stream_rms_evm_per_subcarrier_mean) != response.actual_array_size:
            user_stream_rms_evm_per_subcarrier_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        user_stream_rms_evm_per_subcarrier_mean.flat[:] = (
            response.user_stream_rms_evm_per_subcarrier_mean
        )
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_user_stream_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_user_stream_rms_evm_per_symbol_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace,
            grpc_types.OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            user_stream_rms_evm_per_symbol_mean, "user_stream_rms_evm_per_symbol_mean", "float32"
        )
        if len(user_stream_rms_evm_per_symbol_mean) != response.actual_array_size:
            user_stream_rms_evm_per_symbol_mean.resize(
                (response.actual_array_size,), refcheck=False
            )
        user_stream_rms_evm_per_symbol_mean.flat[:] = response.user_stream_rms_evm_per_symbol_mean
        return response.x0, response.dx, response.status

    def ofdmmodacc_fetch_phase_noise_psd_mean_trace(
        self, selector_string, timeout, phase_noise_psd_mean
    ):
        """ofdmmodacc_fetch_phase_noise_psd_mean_trace."""
        response = self._invoke(
            self._client.OFDMModAccFetchPhaseNoisePSDMeanTrace,
            grpc_types.OFDMModAccFetchPhaseNoisePSDMeanTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(phase_noise_psd_mean, "phase_noise_psd_mean", "float32")
        if len(phase_noise_psd_mean) != response.actual_array_size:
            phase_noise_psd_mean.resize((response.actual_array_size,), refcheck=False)
        phase_noise_psd_mean.flat[:] = response.phase_noise_psd_mean
        return response.x0, response.dx, response.status

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

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        response = self._invoke(
            self._client.CloneSignalConfiguration,
            grpc_types.CloneSignalConfigurationRequest(instrument=self._vi, old_signal_name=old_signal_name, new_signal_name=new_signal_name),  # type: ignore
        )
        # signal_configuration = WLANSignalConfiguration.get_wlan_signal_configuration(self, new_signal_name)
        import nirfmxwlan

        signal_configuration = nirfmxwlan._WlanSignalConfiguration.get_wlan_signal_configuration(self._instr_session, new_signal_name, True)  # type: ignore
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

    def ofdmmodacc_clear_noise_calibration_database(self, selector_string):
        """clear_noise_calibration_database."""
        response = self._invoke(
            self._client.OFDMModAccClearNoiseCalibrationDatabase,
            grpc_types.OFDMModAccClearNoiseCalibrationDatabaseRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

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

    def ofdmmodacc_configure_n_reference_waveforms(
        self, updated_selector_string, x0, dx, reference_waveform
    ):
        """ofdmmodacc_configure_n_reference_waveforms."""
        reference_waveform_proto = []
        reference_waveform_sizes = []
        for arr in reference_waveform:
            _helper.validate_numpy_array(arr, "reference_waveform", "complex64")
            reference_waveform_proto.extend([nidevice_grpc_types.NIComplexNumberF32(real=r, imaginary=i) for r, i in zip(arr.real, arr.imag)])  # type: ignore
            reference_waveform_sizes.append(arr.size)
        response = self._invoke(
            self._client.OFDMModAccCfgNReferenceWaveforms,
            grpc_types.OFDMModAccCfgNReferenceWaveformsRequest(instrument=self._vi, selector_string=updated_selector_string, x0=x0, dx=dx, reference_waveform=reference_waveform_proto, reference_waveform_sizes=reference_waveform_sizes),  # type: ignore
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
