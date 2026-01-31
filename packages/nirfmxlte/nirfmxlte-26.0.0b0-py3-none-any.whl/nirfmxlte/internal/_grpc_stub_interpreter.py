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
import nirfmxlte.enums as enums
import nirfmxlte.errors as errors
import nirfmxlte.internal._custom_types as _custom_types
import nirfmxlte.internal._helper as _helper
import nirfmxlte.internal.nidevice_pb2 as nidevice_grpc_types
import nirfmxlte.internal.nirfmxlte_pb2 as grpc_types
import nirfmxlte.internal.nirfmxlte_pb2_grpc as nirfmxlte_grpc
import nirfmxlte.internal.session_pb2 as session_grpc_types


class GrpcStubInterpreter(object):
    """Interpreter for interacting with a gRPC Stub class"""

    def __init__(self, grpc_options, session=None, signal_obj=None):
        self._grpc_options = grpc_options
        self._signal_obj = signal_obj
        self._instr_session = session
        self._client = nirfmxlte_grpc.NiRFmxLTEStub(grpc_options.grpc_channel)  # type: ignore
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
                local_personality.value == nirfmxinstr.Personalities.LTE.value
            )
        else:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj.signal_configuration_name
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.LTE.value
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

    def configure_frequency_earfcn(self, selector_string, link_direction, band, earfcn):
        """configure_frequency_earfcn."""
        response = self._invoke(
            self._client.CfgFrequencyEARFCN,
            grpc_types.CfgFrequencyEARFCNRequest(instrument=self._vi, selector_string=selector_string, link_direction_raw=link_direction, band=band, earfcn=earfcn),  # type: ignore
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

    def create_list_step(self, selector_string):
        """create_list_step."""
        response = self._invoke(
            self._client.CreateListStep,
            grpc_types.CreateListStepRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.created_step_index, response.status

    def create_list(self, list_name):
        """create_list."""
        response = self._invoke(
            self._client.CreateList,
            grpc_types.CreateListRequest(instrument=self._vi, list_name=list_name),  # type: ignore
        )
        return response.status

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

    def acp_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """acp_configure_averaging."""
        response = self._invoke(
            self._client.ACPCfgAveraging,
            grpc_types.ACPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def acp_configure_configurable_number_of_offsets_enabled(
        self, selector_string, configurable_number_of_offsets_enabled
    ):
        """acp_configure_configurable_number_of_offsets_enabled."""
        response = self._invoke(
            self._client.ACPCfgConfigurableNumberOfOffsetsEnabled,
            grpc_types.ACPCfgConfigurableNumberOfOffsetsEnabledRequest(instrument=self._vi, selector_string=selector_string, configurable_number_of_offsets_enabled_raw=configurable_number_of_offsets_enabled),  # type: ignore
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

    def acp_configure_number_of_eutra_offsets(self, selector_string, number_of_eutra_offsets):
        """acp_configure_number_of_eutra_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfEUTRAOffsets,
            grpc_types.ACPCfgNumberOfEUTRAOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_eutra_offsets=number_of_eutra_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_gsm_offsets(self, selector_string, number_of_gsm_offsets):
        """acp_configure_number_of_gsm_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfGSMOffsets,
            grpc_types.ACPCfgNumberOfGSMOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_gsm_offsets=number_of_gsm_offsets),  # type: ignore
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

    def acp_configure_utra_and_eutra_offsets(
        self, selector_string, number_of_utra_offsets, number_of_eutra_offsets
    ):
        """acp_configure_utra_and_eutra_offsets."""
        response = self._invoke(
            self._client.ACPCfgUTRAAndEUTRAOffsets,
            grpc_types.ACPCfgUTRAAndEUTRAOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_utra_offsets=number_of_utra_offsets, number_of_eutra_offsets=number_of_eutra_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_power_units(self, selector_string, power_units):
        """acp_configure_power_units."""
        response = self._invoke(
            self._client.ACPCfgPowerUnits,
            grpc_types.ACPCfgPowerUnitsRequest(instrument=self._vi, selector_string=selector_string, power_units_raw=power_units),  # type: ignore
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

    def chp_configure_integration_bandwidth_type(self, selector_string, integration_bandwidth_type):
        """chp_configure_integration_bandwidth_type."""
        response = self._invoke(
            self._client.CHPCfgIntegrationBandwidthType,
            grpc_types.CHPCfgIntegrationBandwidthTypeRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth_type_raw=integration_bandwidth_type),  # type: ignore
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

    def modacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """modacc_configure_averaging."""
        response = self._invoke(
            self._client.ModAccCfgAveraging,
            grpc_types.ModAccCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def modacc_configure_common_clock_source_enabled(
        self, selector_string, common_clock_source_enabled
    ):
        """modacc_configure_common_clock_source_enabled."""
        response = self._invoke(
            self._client.ModAccCfgCommonClockSourceEnabled,
            grpc_types.ModAccCfgCommonClockSourceEnabledRequest(instrument=self._vi, selector_string=selector_string, common_clock_source_enabled_raw=common_clock_source_enabled),  # type: ignore
        )
        return response.status

    def modacc_configure_evm_unit(self, selector_string, evm_unit):
        """modacc_configure_evm_unit."""
        response = self._invoke(
            self._client.ModAccCfgEVMUnit,
            grpc_types.ModAccCfgEVMUnitRequest(instrument=self._vi, selector_string=selector_string, evm_unit_raw=evm_unit),  # type: ignore
        )
        return response.status

    def modacc_configure_fft_window_offset(self, selector_string, fft_window_offset):
        """modacc_configure_fft_window_offset."""
        response = self._invoke(
            self._client.ModAccCfgFFTWindowOffset,
            grpc_types.ModAccCfgFFTWindowOffsetRequest(instrument=self._vi, selector_string=selector_string, fft_window_offset=fft_window_offset),  # type: ignore
        )
        return response.status

    def modacc_configure_fft_window_position(
        self, selector_string, fft_window_type, fft_window_offset, fft_window_length
    ):
        """modacc_configure_fft_window_position."""
        response = self._invoke(
            self._client.ModAccCfgFFTWindowPosition,
            grpc_types.ModAccCfgFFTWindowPositionRequest(instrument=self._vi, selector_string=selector_string, fft_window_type_raw=fft_window_type, fft_window_offset=fft_window_offset, fft_window_length=fft_window_length),  # type: ignore
        )
        return response.status

    def modacc_configure_in_band_emission_mask_type(
        self, selector_string, in_band_emission_mask_type
    ):
        """modacc_configure_in_band_emission_mask_type."""
        response = self._invoke(
            self._client.ModAccCfgInBandEmissionMaskType,
            grpc_types.ModAccCfgInBandEmissionMaskTypeRequest(instrument=self._vi, selector_string=selector_string, in_band_emission_mask_type_raw=in_band_emission_mask_type),  # type: ignore
        )
        return response.status

    def modacc_configure_synchronization_mode_and_interval(
        self, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        """modacc_configure_synchronization_mode_and_interval."""
        response = self._invoke(
            self._client.ModAccCfgSynchronizationModeAndInterval,
            grpc_types.ModAccCfgSynchronizationModeAndIntervalRequest(instrument=self._vi, selector_string=selector_string, synchronization_mode_raw=synchronization_mode, measurement_offset=measurement_offset, measurement_length=measurement_length),  # type: ignore
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

    def sem_configure_maximum_output_power_array(
        self, selector_string, component_carrier_maximum_output_power
    ):
        """sem_configure_maximum_output_power_array."""
        response = self._invoke(
            self._client.SEMCfgComponentCarrierMaximumOutputPowerArray,
            grpc_types.SEMCfgComponentCarrierMaximumOutputPowerArrayRequest(instrument=self._vi, selector_string=selector_string, component_carrier_maximum_output_power=component_carrier_maximum_output_power),  # type: ignore
        )
        return response.status

    def sem_configure_maximum_output_power(
        self, selector_string, component_carrier_maximum_output_power
    ):
        """sem_configure_maximum_output_power."""
        response = self._invoke(
            self._client.SEMCfgComponentCarrierMaximumOutputPower,
            grpc_types.SEMCfgComponentCarrierMaximumOutputPowerRequest(instrument=self._vi, selector_string=selector_string, component_carrier_maximum_output_power=component_carrier_maximum_output_power),  # type: ignore
        )
        return response.status

    def sem_configure_downlink_mask(
        self, selector_string, downlink_mask_type, delta_f_maximum, aggregated_maximum_power
    ):
        """sem_configure_downlink_mask."""
        response = self._invoke(
            self._client.SEMCfgDownlinkMask,
            grpc_types.SEMCfgDownlinkMaskRequest(instrument=self._vi, selector_string=selector_string, downlink_mask_type_raw=downlink_mask_type, delta_f_maximum=delta_f_maximum, aggregated_maximum_power=aggregated_maximum_power),  # type: ignore
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
        self, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetAbsoluteLimitArray,
            grpc_types.SEMCfgOffsetAbsoluteLimitArrayRequest(instrument=self._vi, selector_string=selector_string, offset_absolute_limit_start=offset_absolute_limit_start, offset_absolute_limit_stop=offset_absolute_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_absolute_limit(
        self, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit."""
        response = self._invoke(
            self._client.SEMCfgOffsetAbsoluteLimit,
            grpc_types.SEMCfgOffsetAbsoluteLimitRequest(instrument=self._vi, selector_string=selector_string, offset_absolute_limit_start=offset_absolute_limit_start, offset_absolute_limit_stop=offset_absolute_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_bandwidth_integral_array(
        self, selector_string, offset_bandwidth_integral
    ):
        """sem_configure_offset_bandwidth_integral_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetBandwidthIntegralArray,
            grpc_types.SEMCfgOffsetBandwidthIntegralArrayRequest(instrument=self._vi, selector_string=selector_string, offset_bandwidth_integral=offset_bandwidth_integral),  # type: ignore
        )
        return response.status

    def sem_configure_offset_bandwidth_integral(self, selector_string, offset_bandwidth_integral):
        """sem_configure_offset_bandwidth_integral."""
        response = self._invoke(
            self._client.SEMCfgOffsetBandwidthIntegral,
            grpc_types.SEMCfgOffsetBandwidthIntegralRequest(instrument=self._vi, selector_string=selector_string, offset_bandwidth_integral=offset_bandwidth_integral),  # type: ignore
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

    def slotphase_configure_synchronization_mode_and_interval(
        self, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        """slotphase_configure_synchronization_mode_and_interval."""
        response = self._invoke(
            self._client.SlotPhaseCfgSynchronizationModeAndInterval,
            grpc_types.SlotPhaseCfgSynchronizationModeAndIntervalRequest(instrument=self._vi, selector_string=selector_string, synchronization_mode_raw=synchronization_mode, measurement_offset=measurement_offset, measurement_length=measurement_length),  # type: ignore
        )
        return response.status

    def slotpower_configure_measurement_interval(
        self, selector_string, measurement_offset, measurement_length
    ):
        """slotpower_configure_measurement_interval."""
        response = self._invoke(
            self._client.SlotPowerCfgMeasurementInterval,
            grpc_types.SlotPowerCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_offset=measurement_offset, measurement_length=measurement_length),  # type: ignore
        )
        return response.status

    def txp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """txp_configure_averaging."""
        response = self._invoke(
            self._client.TXPCfgAveraging,
            grpc_types.TXPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def txp_configure_measurement_offset_and_interval(
        self, selector_string, measurement_offset, measurement_interval
    ):
        """txp_configure_measurement_offset_and_interval."""
        response = self._invoke(
            self._client.TXPCfgMeasurementOffsetAndInterval,
            grpc_types.TXPCfgMeasurementOffsetAndIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_offset=measurement_offset, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def configure_auto_dmrs_detection_enabled(self, selector_string, auto_dmrs_detection_enabled):
        """configure_auto_dmrs_detection_enabled."""
        response = self._invoke(
            self._client.CfgAutoDMRSDetectionEnabled,
            grpc_types.CfgAutoDMRSDetectionEnabledRequest(instrument=self._vi, selector_string=selector_string, auto_dmrs_detection_enabled_raw=auto_dmrs_detection_enabled),  # type: ignore
        )
        return response.status

    def configure_auto_npusch_channel_detection_enabled(
        self, selector_string, auto_npusch_channel_detection_enabled
    ):
        """configure_auto_npusch_channel_detection_enabled."""
        response = self._invoke(
            self._client.CfgAutoNPUSCHChannelDetectionEnabled,
            grpc_types.CfgAutoNPUSCHChannelDetectionEnabledRequest(instrument=self._vi, selector_string=selector_string, auto_npusch_channel_detection_enabled_raw=auto_npusch_channel_detection_enabled),  # type: ignore
        )
        return response.status

    def configure_auto_resource_block_detection_enabled(
        self, selector_string, auto_resource_block_detection_enabled
    ):
        """configure_auto_resource_block_detection_enabled."""
        response = self._invoke(
            self._client.CfgAutoResourceBlockDetectionEnabled,
            grpc_types.CfgAutoResourceBlockDetectionEnabledRequest(instrument=self._vi, selector_string=selector_string, auto_resource_block_detection_enabled_raw=auto_resource_block_detection_enabled),  # type: ignore
        )
        return response.status

    def configure_band(self, selector_string, band):
        """configure_band."""
        response = self._invoke(
            self._client.CfgBand,
            grpc_types.CfgBandRequest(instrument=self._vi, selector_string=selector_string, band=band),  # type: ignore
        )
        return response.status

    def configure_cell_specific_ratio(self, selector_string, cell_specific_ratio):
        """configure_cell_specific_ratio."""
        response = self._invoke(
            self._client.CfgCellSpecificRatio,
            grpc_types.CfgCellSpecificRatioRequest(instrument=self._vi, selector_string=selector_string, cell_specific_ratio_raw=cell_specific_ratio),  # type: ignore
        )
        return response.status

    def configure_array(
        self, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        """configure_array."""
        response = self._invoke(
            self._client.CfgComponentCarrierArray,
            grpc_types.CfgComponentCarrierArrayRequest(instrument=self._vi, selector_string=selector_string, component_carrier_bandwidth=component_carrier_bandwidth, component_carrier_frequency=component_carrier_frequency, cell_id=cell_id),  # type: ignore
        )
        return response.status

    def configure_spacing(
        self, selector_string, component_carrier_spacing_type, component_carrier_at_center_frequency
    ):
        """configure_spacing."""
        response = self._invoke(
            self._client.CfgComponentCarrierSpacing,
            grpc_types.CfgComponentCarrierSpacingRequest(instrument=self._vi, selector_string=selector_string, component_carrier_spacing_type_raw=component_carrier_spacing_type, component_carrier_at_center_frequency=component_carrier_at_center_frequency),  # type: ignore
        )
        return response.status

    def configure(
        self, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        """configure."""
        response = self._invoke(
            self._client.CfgComponentCarrier,
            grpc_types.CfgComponentCarrierRequest(instrument=self._vi, selector_string=selector_string, component_carrier_bandwidth=component_carrier_bandwidth, component_carrier_frequency=component_carrier_frequency, cell_id=cell_id),  # type: ignore
        )
        return response.status

    def configure_downlink_auto_cell_id_detection_enabled(
        self, selector_string, auto_cell_id_detection_enabled
    ):
        """configure_downlink_auto_cell_id_detection_enabled."""
        response = self._invoke(
            self._client.CfgDownlinkAutoCellIDDetectionEnabled,
            grpc_types.CfgDownlinkAutoCellIDDetectionEnabledRequest(instrument=self._vi, selector_string=selector_string, auto_cell_id_detection_enabled_raw=auto_cell_id_detection_enabled),  # type: ignore
        )
        return response.status

    def configure_downlink_channel_configuration_mode(
        self, selector_string, channel_configuration_mode
    ):
        """configure_downlink_channel_configuration_mode."""
        response = self._invoke(
            self._client.CfgDownlinkChannelConfigurationMode,
            grpc_types.CfgDownlinkChannelConfigurationModeRequest(instrument=self._vi, selector_string=selector_string, channel_configuration_mode_raw=channel_configuration_mode),  # type: ignore
        )
        return response.status

    def configure_downlink_number_of_subframes(self, selector_string, number_of_subframes):
        """configure_downlink_number_of_subframes."""
        response = self._invoke(
            self._client.CfgDownlinkNumberOfSubframes,
            grpc_types.CfgDownlinkNumberOfSubframesRequest(instrument=self._vi, selector_string=selector_string, number_of_subframes=number_of_subframes),  # type: ignore
        )
        return response.status

    def configure_downlink_synchronization_signal(self, selector_string, pss_power, sss_power):
        """configure_downlink_synchronization_signal."""
        response = self._invoke(
            self._client.CfgDownlinkSynchronizationSignal,
            grpc_types.CfgDownlinkSynchronizationSignalRequest(instrument=self._vi, selector_string=selector_string, pss_power=pss_power, sss_power=sss_power),  # type: ignore
        )
        return response.status

    def configure_downlink_test_model_array(self, selector_string, downlink_test_model):
        """configure_downlink_test_model_array."""
        response = self._invoke(
            self._client.CfgDownlinkTestModelArray,
            grpc_types.CfgDownlinkTestModelArrayRequest(instrument=self._vi, selector_string=selector_string, downlink_test_model=downlink_test_model),  # type: ignore
        )
        return response.status

    def configure_downlink_test_model(self, selector_string, downlink_test_model):
        """configure_downlink_test_model."""
        response = self._invoke(
            self._client.CfgDownlinkTestModel,
            grpc_types.CfgDownlinkTestModelRequest(instrument=self._vi, selector_string=selector_string, downlink_test_model_raw=downlink_test_model),  # type: ignore
        )
        return response.status

    def configure_duplex_scheme(
        self, selector_string, duplex_scheme, uplink_downlink_configuration
    ):
        """configure_duplex_scheme."""
        response = self._invoke(
            self._client.CfgDuplexScheme,
            grpc_types.CfgDuplexSchemeRequest(instrument=self._vi, selector_string=selector_string, duplex_scheme_raw=duplex_scheme, uplink_downlink_configuration_raw=uplink_downlink_configuration),  # type: ignore
        )
        return response.status

    def configure_emtc_analysis_enabled(self, selector_string, emtc_analysis_enabled):
        """configure_emtc_analysis_enabled."""
        response = self._invoke(
            self._client.CfgEMTCAnalysisEnabled,
            grpc_types.CfgEMTCAnalysisEnabledRequest(instrument=self._vi, selector_string=selector_string, emtc_analysis_enabled_raw=emtc_analysis_enabled),  # type: ignore
        )
        return response.status

    def configure_enodeb_category(self, selector_string, enodeb_category):
        """configure_enodeb_category."""
        response = self._invoke(
            self._client.CfgeNodeBCategory,
            grpc_types.CfgeNodeBCategoryRequest(instrument=self._vi, selector_string=selector_string, enodeb_category_raw=enodeb_category),  # type: ignore
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

    def configure_link_direction(self, selector_string, link_direction):
        """configure_link_direction."""
        response = self._invoke(
            self._client.CfgLinkDirection,
            grpc_types.CfgLinkDirectionRequest(instrument=self._vi, selector_string=selector_string, link_direction_raw=link_direction),  # type: ignore
        )
        return response.status

    def configure_nb_iot_component_carrier(
        self, selector_string, n_cell_id, uplink_subcarrier_spacing
    ):
        """configure_nb_iot_component_carrier."""
        response = self._invoke(
            self._client.CfgNBIoTComponentCarrier,
            grpc_types.CfgNBIoTComponentCarrierRequest(instrument=self._vi, selector_string=selector_string, n_cell_id=n_cell_id, uplink_subcarrier_spacing_raw=uplink_subcarrier_spacing),  # type: ignore
        )
        return response.status

    def configure_npusch_dmrs(
        self,
        selector_string,
        npusch_dmrs_base_sequence_mode,
        npusch_dmrs_base_sequence_index,
        npusch_dmrs_cyclic_shift,
        npusch_dmrs_group_hopping_enabled,
        npusch_dmrs_delta_ss,
    ):
        """configure_npusch_dmrs."""
        response = self._invoke(
            self._client.CfgNPUSCHDMRS,
            grpc_types.CfgNPUSCHDMRSRequest(instrument=self._vi, selector_string=selector_string, npusch_dmrs_base_sequence_mode_raw=npusch_dmrs_base_sequence_mode, npusch_dmrs_base_sequence_index=npusch_dmrs_base_sequence_index, npusch_dmrs_cyclic_shift=npusch_dmrs_cyclic_shift, npusch_dmrs_group_hopping_enabled_raw=npusch_dmrs_group_hopping_enabled, npusch_dmrs_delta_ss=npusch_dmrs_delta_ss),  # type: ignore
        )
        return response.status

    def configure_npusch_format(self, selector_string, format):
        """configure_npusch_format."""
        response = self._invoke(
            self._client.CfgNPUSCHFormat,
            grpc_types.CfgNPUSCHFormatRequest(instrument=self._vi, selector_string=selector_string, format=format),  # type: ignore
        )
        return response.status

    def configure_npusch_starting_slot(self, selector_string, starting_slot):
        """configure_npusch_starting_slot."""
        response = self._invoke(
            self._client.CfgNPUSCHStartingSlot,
            grpc_types.CfgNPUSCHStartingSlotRequest(instrument=self._vi, selector_string=selector_string, starting_slot=starting_slot),  # type: ignore
        )
        return response.status

    def configure_npusch_tones(
        self, selector_string, tone_offset, number_of_tones, modulation_type
    ):
        """configure_npusch_tones."""
        response = self._invoke(
            self._client.CfgNPUSCHTones,
            grpc_types.CfgNPUSCHTonesRequest(instrument=self._vi, selector_string=selector_string, tone_offset=tone_offset, number_of_tones=number_of_tones, modulation_type_raw=modulation_type),  # type: ignore
        )
        return response.status

    def configure_number_of_component_carriers(self, selector_string, number_of_component_carriers):
        """configure_number_of_component_carriers."""
        response = self._invoke(
            self._client.CfgNumberOfComponentCarriers,
            grpc_types.CfgNumberOfComponentCarriersRequest(instrument=self._vi, selector_string=selector_string, number_of_component_carriers=number_of_component_carriers),  # type: ignore
        )
        return response.status

    def configure_number_of_dut_antennas(self, selector_string, number_of_dut_antennas):
        """configure_number_of_dut_antennas."""
        response = self._invoke(
            self._client.CfgNumberOfDUTAntennas,
            grpc_types.CfgNumberOfDUTAntennasRequest(instrument=self._vi, selector_string=selector_string, number_of_dut_antennas=number_of_dut_antennas),  # type: ignore
        )
        return response.status

    def configure_number_of_pdsch_channels(self, selector_string, number_of_pdsch_channels):
        """configure_number_of_pdsch_channels."""
        response = self._invoke(
            self._client.CfgNumberOfPDSCHChannels,
            grpc_types.CfgNumberOfPDSCHChannelsRequest(instrument=self._vi, selector_string=selector_string, number_of_pdsch_channels=number_of_pdsch_channels),  # type: ignore
        )
        return response.status

    def configure_number_of_pusch_resource_block_clusters(
        self, selector_string, number_of_resource_block_clusters
    ):
        """configure_number_of_pusch_resource_block_clusters."""
        response = self._invoke(
            self._client.CfgNumberOfPUSCHResourceBlockClusters,
            grpc_types.CfgNumberOfPUSCHResourceBlockClustersRequest(instrument=self._vi, selector_string=selector_string, number_of_resource_block_clusters=number_of_resource_block_clusters),  # type: ignore
        )
        return response.status

    def configure_number_of_subblocks(self, selector_string, number_of_subblocks):
        """configure_number_of_subblocks."""
        response = self._invoke(
            self._client.CfgNumberOfSubblocks,
            grpc_types.CfgNumberOfSubblocksRequest(instrument=self._vi, selector_string=selector_string, number_of_subblocks=number_of_subblocks),  # type: ignore
        )
        return response.status

    def configure_pbch(self, selector_string, pbch_power):
        """configure_pbch."""
        response = self._invoke(
            self._client.CfgPBCH,
            grpc_types.CfgPBCHRequest(instrument=self._vi, selector_string=selector_string, pbch_power=pbch_power),  # type: ignore
        )
        return response.status

    def configure_pcfich(self, selector_string, cfi, power):
        """configure_pcfich."""
        response = self._invoke(
            self._client.CfgPCFICH,
            grpc_types.CfgPCFICHRequest(instrument=self._vi, selector_string=selector_string, cfi=cfi, power=power),  # type: ignore
        )
        return response.status

    def configure_pdcch(self, selector_string, pdcch_power):
        """configure_pdcch."""
        response = self._invoke(
            self._client.CfgPDCCH,
            grpc_types.CfgPDCCHRequest(instrument=self._vi, selector_string=selector_string, pdcch_power=pdcch_power),  # type: ignore
        )
        return response.status

    def configure_pdsch(
        self, selector_string, cw0_modulation_type, resource_block_allocation, power
    ):
        """configure_pdsch."""
        response = self._invoke(
            self._client.CfgPDSCH,
            grpc_types.CfgPDSCHRequest(instrument=self._vi, selector_string=selector_string, cw0_modulation_type_raw=cw0_modulation_type, resource_block_allocation=resource_block_allocation, power=power),  # type: ignore
        )
        return response.status

    def configure_phich(self, selector_string, resource, duration, power):
        """configure_phich."""
        response = self._invoke(
            self._client.CfgPHICH,
            grpc_types.CfgPHICHRequest(instrument=self._vi, selector_string=selector_string, resource_raw=resource, duration_raw=duration, power=power),  # type: ignore
        )
        return response.status

    def configure_pssch_modulation_type(self, selector_string, modulation_type):
        """configure_pssch_modulation_type."""
        response = self._invoke(
            self._client.CfgPSSCHModulationType,
            grpc_types.CfgPSSCHModulationTypeRequest(instrument=self._vi, selector_string=selector_string, modulation_type_raw=modulation_type),  # type: ignore
        )
        return response.status

    def configure_pssch_resource_blocks(
        self, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        """configure_pssch_resource_blocks."""
        response = self._invoke(
            self._client.CfgPSSCHResourceBlocks,
            grpc_types.CfgPSSCHResourceBlocksRequest(instrument=self._vi, selector_string=selector_string, resource_block_offset=resource_block_offset, number_of_resource_blocks=number_of_resource_blocks),  # type: ignore
        )
        return response.status

    def configure_pusch_modulation_type(self, selector_string, modulation_type):
        """configure_pusch_modulation_type."""
        response = self._invoke(
            self._client.CfgPUSCHModulationType,
            grpc_types.CfgPUSCHModulationTypeRequest(instrument=self._vi, selector_string=selector_string, modulation_type_raw=modulation_type),  # type: ignore
        )
        return response.status

    def configure_pusch_resource_blocks(
        self, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        """configure_pusch_resource_blocks."""
        response = self._invoke(
            self._client.CfgPUSCHResourceBlocks,
            grpc_types.CfgPUSCHResourceBlocksRequest(instrument=self._vi, selector_string=selector_string, resource_block_offset=resource_block_offset, number_of_resource_blocks=number_of_resource_blocks),  # type: ignore
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

    def configure_transmit_antenna_to_analyze(self, selector_string, transmit_antenna_to_analyze):
        """configure_transmit_antenna_to_analyze."""
        response = self._invoke(
            self._client.CfgTransmitAntennaToAnalyze,
            grpc_types.CfgTransmitAntennaToAnalyzeRequest(instrument=self._vi, selector_string=selector_string, transmit_antenna_to_analyze=transmit_antenna_to_analyze),  # type: ignore
        )
        return response.status

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

    def acp_fetch_total_aggregated_power(self, selector_string, timeout):
        """acp_fetch_total_aggregated_power."""
        response = self._invoke(
            self._client.ACPFetchTotalAggregatedPower,
            grpc_types.ACPFetchTotalAggregatedPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_aggregated_power, response.status

    def chp_fetch_measurement(self, selector_string, timeout):
        """chp_fetch_measurement."""
        response = self._invoke(
            self._client.CHPFetchComponentCarrierMeasurement,
            grpc_types.CHPFetchComponentCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power, response.relative_power, response.status

    def chp_fetch_subblock_measurement(self, selector_string, timeout):
        """chp_fetch_subblock_measurement."""
        response = self._invoke(
            self._client.CHPFetchSubblockMeasurement,
            grpc_types.CHPFetchSubblockMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.subblock_power,
            response.integration_bandwidth,
            response.frequency,
            response.status,
        )

    def chp_fetch_total_aggregated_power(self, selector_string, timeout):
        """chp_fetch_total_aggregated_power."""
        response = self._invoke(
            self._client.CHPFetchTotalAggregatedPower,
            grpc_types.CHPFetchTotalAggregatedPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_aggregated_power, response.status

    def modacc_fetch_composite_evm(self, selector_string, timeout):
        """modacc_fetch_composite_evm."""
        response = self._invoke(
            self._client.ModAccFetchCompositeEVM,
            grpc_types.ModAccFetchCompositeEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_rms_composite_evm,
            response.maximum_peak_composite_evm,
            response.mean_frequency_error,
            response.peak_composite_evm_symbol_index,
            response.peak_composite_evm_subcarrier_index,
            response.peak_composite_evm_slot_index,
            response.status,
        )

    def modacc_fetch_composite_magnitude_and_phase_error(self, selector_string, timeout):
        """modacc_fetch_composite_magnitude_and_phase_error."""
        response = self._invoke(
            self._client.ModAccFetchCompositeMagnitudeAndPhaseError,
            grpc_types.ModAccFetchCompositeMagnitudeAndPhaseErrorRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_rms_composite_magnitude_error,
            response.maximum_peak_composite_magnitude_error,
            response.mean_rms_composite_phase_error,
            response.maximum_peak_composite_phase_error,
            response.status,
        )

    def modacc_fetch_csrs_evm(self, selector_string, timeout):
        """modacc_fetch_csrs_evm."""
        response = self._invoke(
            self._client.ModAccFetchCSRSEVM,
            grpc_types.ModAccFetchCSRSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_csrs_evm, response.status

    def modacc_fetch_downlink_detected_cell_id(self, selector_string, timeout):
        """modacc_fetch_downlink_detected_cell_id."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkDetectedCellID,
            grpc_types.ModAccFetchDownlinkDetectedCellIDRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.detected_cell_id, response.status

    def modacc_fetch_downlink_transmit_power(self, selector_string, timeout):
        """modacc_fetch_downlink_transmit_power."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkTransmitPower,
            grpc_types.ModAccFetchDownlinkTransmitPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rs_transmit_power,
            response.ofdm_symbol_transmit_power,
            response.reserved_1,
            response.reserved_2,
            response.status,
        )

    def modacc_fetch_in_band_emission_margin(self, selector_string, timeout):
        """modacc_fetch_in_band_emission_margin."""
        response = self._invoke(
            self._client.ModAccFetchInBandEmissionMargin,
            grpc_types.ModAccFetchInBandEmissionMarginRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.in_band_emission_margin, response.status

    def modacc_fetch_iq_impairments(self, selector_string, timeout):
        """modacc_fetch_iq_impairments."""
        response = self._invoke(
            self._client.ModAccFetchIQImpairments,
            grpc_types.ModAccFetchIQImpairmentsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_iq_origin_offset,
            response.mean_iq_gain_imbalance,
            response.mean_iq_quadrature_error,
            response.status,
        )

    def modacc_fetch_npusch_data_evm(self, selector_string, timeout):
        """modacc_fetch_npusch_data_evm."""
        response = self._invoke(
            self._client.ModAccFetchNPUSCHDataEVM,
            grpc_types.ModAccFetchNPUSCHDataEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.npusch_mean_rms_data_evm,
            response.npusch_maximum_peak_data_evm,
            response.status,
        )

    def modacc_fetch_npusch_dmrs_evm(self, selector_string, timeout):
        """modacc_fetch_npusch_dmrs_evm."""
        response = self._invoke(
            self._client.ModAccFetchNPUSCHDMRSEVM,
            grpc_types.ModAccFetchNPUSCHDMRSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.npusch_mean_rms_dmrs_evm,
            response.npusch_maximum_peak_dmrs_evm,
            response.status,
        )

    def modacc_fetch_npusch_symbol_power(self, selector_string, timeout):
        """modacc_fetch_npusch_symbol_power."""
        response = self._invoke(
            self._client.ModAccFetchNPUSCHSymbolPower,
            grpc_types.ModAccFetchNPUSCHSymbolPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.npusch_mean_data_power, response.npusch_mean_dmrs_power, response.status

    def modacc_fetch_pdsc_1024_qam_evm(self, selector_string, timeout):
        """modacc_fetch_pdsc_1024_qam_evm."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH1024QAMEVM,
            grpc_types.ModAccFetchPDSCH1024QAMEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_1024qam_evm, response.status

    def modacc_fetch_pdsch_evm(self, selector_string, timeout):
        """modacc_fetch_pdsch_evm."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHEVM,
            grpc_types.ModAccFetchPDSCHEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_rms_evm,
            response.mean_rms_qpsk_evm,
            response.mean_rms_16qam_evm,
            response.mean_rms_64qam_evm,
            response.mean_rms_256qam_evm,
            response.status,
        )

    def modacc_fetch_pssch_data_evm(self, selector_string, timeout):
        """modacc_fetch_pssch_data_evm."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHDataEVM,
            grpc_types.ModAccFetchPSSCHDataEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.pssch_mean_rms_data_evm,
            response.pssch_maximum_peak_data_evm,
            response.status,
        )

    def modacc_fetch_pssch_dmrs_evm(self, selector_string, timeout):
        """modacc_fetch_pssch_dmrs_evm."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHDMRSEVM,
            grpc_types.ModAccFetchPSSCHDMRSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.pssch_mean_rms_dmrs_evm,
            response.pssch_maximum_peak_dmrs_evm,
            response.status,
        )

    def modacc_fetch_pssch_symbol_power(self, selector_string, timeout):
        """modacc_fetch_pssch_symbol_power."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHSymbolPower,
            grpc_types.ModAccFetchPSSCHSymbolPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pssch_mean_data_power, response.pssch_mean_dmrs_power, response.status

    def modacc_fetch_pusch_data_evm(self, selector_string, timeout):
        """modacc_fetch_pusch_data_evm."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDataEVM,
            grpc_types.ModAccFetchPUSCHDataEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_data_evm, response.maximum_peak_data_evm, response.status

    def modacc_fetch_pusch_dmrs_evm(self, selector_string, timeout):
        """modacc_fetch_pusch_dmrs_evm."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDMRSEVM,
            grpc_types.ModAccFetchPUSCHDMRSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_dmrs_evm, response.maximum_peak_dmrs_evm, response.status

    def modacc_fetch_pusch_symbol_power(self, selector_string, timeout):
        """modacc_fetch_pusch_symbol_power."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHSymbolPower,
            grpc_types.ModAccFetchPUSCHSymbolPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pusch_mean_data_power, response.pusch_mean_dmrs_power, response.status

    def modacc_fetch_spectral_flatness(self, selector_string, timeout):
        """modacc_fetch_spectral_flatness."""
        response = self._invoke(
            self._client.ModAccFetchSpectralFlatness,
            grpc_types.ModAccFetchSpectralFlatnessRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.range1_maximum_to_range1_minimum,
            response.range2_maximum_to_range2_minimum,
            response.range1_maximum_to_range2_minimum,
            response.range2_maximum_to_range1_minimum,
            response.status,
        )

    def modacc_fetch_srs_evm(self, selector_string, timeout):
        """modacc_fetch_srs_evm."""
        response = self._invoke(
            self._client.ModAccFetchSRSEVM,
            grpc_types.ModAccFetchSRSEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_srs_evm, response.mean_srs_power, response.status

    def modacc_fetch_subblock_in_band_emission_margin(self, selector_string, timeout):
        """modacc_fetch_subblock_in_band_emission_margin."""
        response = self._invoke(
            self._client.ModAccFetchSubblockInBandEmissionMargin,
            grpc_types.ModAccFetchSubblockInBandEmissionMarginRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.subblock_in_band_emission_margin, response.status

    def modacc_fetch_subblock_iq_impairments(self, selector_string, timeout):
        """modacc_fetch_subblock_iq_impairments."""
        response = self._invoke(
            self._client.ModAccFetchSubblockIQImpairments,
            grpc_types.ModAccFetchSubblockIQImpairmentsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.subblock_mean_iq_origin_offset,
            response.subblock_mean_iq_gain_imbalance,
            response.subblock_mean_iq_quadrature_error,
            response.status,
        )

    def modacc_fetch_synchronization_signal_evm(self, selector_string, timeout):
        """modacc_fetch_synchronization_signal_evm."""
        response = self._invoke(
            self._client.ModAccFetchSynchronizationSignalEVM,
            grpc_types.ModAccFetchSynchronizationSignalEVMRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_pss_evm, response.mean_rms_sss_evm, response.status

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
            response.absolute_integrated_power,
            response.relative_integrated_power,
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
            response.absolute_integrated_power,
            response.relative_integrated_power,
            response.absolute_peak_power,
            response.peak_frequency,
            response.relative_peak_power,
            response.status,
        )

    def sem_fetch_measurement_status(self, selector_string, timeout):
        """sem_fetch_measurement_status."""
        response = self._invoke(
            self._client.SEMFetchMeasurementStatus,
            grpc_types.SEMFetchMeasurementStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.SemMeasurementStatus(response.measurement_status), response.status

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
            response.absolute_integrated_power,
            response.relative_integrated_power,
            response.absolute_peak_power,
            response.peak_frequency,
            response.relative_peak_power,
            response.status,
        )

    def pvt_fetch_measurement(self, selector_string, timeout):
        """pvt_fetch_measurement."""
        response = self._invoke(
            self._client.PVTFetchMeasurement,
            grpc_types.PVTFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.PvtMeasurementStatus(response.measurement_status),
            response.mean_absolute_off_power_before,
            response.mean_absolute_off_power_after,
            response.mean_absolute_on_power,
            response.burst_width,
            response.status,
        )

    def slotphase_fetch_maximum_phase_discontinuity(self, selector_string, timeout):
        """slotphase_fetch_maximum_phase_discontinuity."""
        response = self._invoke(
            self._client.SlotPhaseFetchMaximumPhaseDiscontinuity,
            grpc_types.SlotPhaseFetchMaximumPhaseDiscontinuityRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.maximum_phase_discontinuity, response.status

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        response = self._invoke(
            self._client.TXPFetchMeasurement,
            grpc_types.TXPFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.average_power_mean, response.peak_power_maximum, response.status

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

    def modacc_fetch_composite_evm_array(self, selector_string, timeout):
        """modacc_fetch_composite_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchCompositeEVMArray,
            grpc_types.ModAccFetchCompositeEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_rms_composite_evm[:],
            response.maximum_peak_composite_evm[:],
            response.mean_frequency_error[:],
            response.peak_composite_evm_symbol_index[:],
            response.peak_composite_evm_subcarrier_index[:],
            response.peak_composite_evm_slot_index[:],
            response.status,
        )

    def modacc_fetch_composite_magnitude_and_phase_error_array(self, selector_string, timeout):
        """modacc_fetch_composite_magnitude_and_phase_error_array."""
        response = self._invoke(
            self._client.ModAccFetchCompositeMagnitudeAndPhaseErrorArray,
            grpc_types.ModAccFetchCompositeMagnitudeAndPhaseErrorArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_rms_composite_magnitude_error[:],
            response.maximum_peak_composite_magnitude_error[:],
            response.mean_rms_composite_phase_error[:],
            response.maximum_peak_composite_phase_error[:],
            response.status,
        )

    def modacc_fetch_csrs_constellation(self, selector_string, timeout, csrs_constellation):
        """modacc_fetch_csrs_constellation."""
        response = self._invoke(
            self._client.ModAccFetchCSRSConstellationInterleavedIQ,
            grpc_types.ModAccFetchCSRSConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(csrs_constellation, "csrs_constellation", "complex64")
        if len(csrs_constellation) != response.actual_array_size // 2:
            csrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.csrs_constellation, dtype=numpy.float32)
        csrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_csrs_evm_array(self, selector_string, timeout):
        """modacc_fetch_csrs_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchCSRSEVMArray,
            grpc_types.ModAccFetchCSRSEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_csrs_evm[:], response.status

    def modacc_fetch_downlink_detected_cell_id_array(self, selector_string, timeout):
        """modacc_fetch_downlink_detected_cell_id_array."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkDetectedCellIDArray,
            grpc_types.ModAccFetchDownlinkDetectedCellIDArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.detected_cell_id[:], response.status

    def modacc_fetch_downlink_pbch_constellation(
        self, selector_string, timeout, pbch_constellation
    ):
        """modacc_fetch_downlink_pbch_constellation."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkPBCHConstellationInterleavedIQ,
            grpc_types.ModAccFetchDownlinkPBCHConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(pbch_constellation, "pbch_constellation", "complex64")
        if len(pbch_constellation) != response.actual_array_size // 2:
            pbch_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pbch_constellation, dtype=numpy.float32)
        pbch_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_downlink_pcfich_constellation(
        self, selector_string, timeout, pcfich_constellation
    ):
        """modacc_fetch_downlink_pcfich_constellation."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkPCFICHConstellationInterleavedIQ,
            grpc_types.ModAccFetchDownlinkPCFICHConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(pcfich_constellation, "pcfich_constellation", "complex64")
        if len(pcfich_constellation) != response.actual_array_size // 2:
            pcfich_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pcfich_constellation, dtype=numpy.float32)
        pcfich_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_downlink_pdcch_constellation(
        self, selector_string, timeout, pdcch_constellation
    ):
        """modacc_fetch_downlink_pdcch_constellation."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkPDCCHConstellationInterleavedIQ,
            grpc_types.ModAccFetchDownlinkPDCCHConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(pdcch_constellation, "pdcch_constellation", "complex64")
        if len(pdcch_constellation) != response.actual_array_size // 2:
            pdcch_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pdcch_constellation, dtype=numpy.float32)
        pdcch_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_downlink_phich_constellation(
        self, selector_string, timeout, phich_constellation
    ):
        """modacc_fetch_downlink_phich_constellation."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkPHICHConstellationInterleavedIQ,
            grpc_types.ModAccFetchDownlinkPHICHConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(phich_constellation, "phich_constellation", "complex64")
        if len(phich_constellation) != response.actual_array_size // 2:
            phich_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.phich_constellation, dtype=numpy.float32)
        phich_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_downlink_transmit_power_array(self, selector_string, timeout):
        """modacc_fetch_downlink_transmit_power_array."""
        response = self._invoke(
            self._client.ModAccFetchDownlinkTransmitPowerArray,
            grpc_types.ModAccFetchDownlinkTransmitPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.rs_transmit_power[:],
            response.ofdm_symbol_transmit_power[:],
            response.reserved_1[:],
            response.reserved_2[:],
            response.status,
        )

    def modacc_fetch_evm_per_slot_trace(self, selector_string, timeout, rms_evm_per_slot):
        """modacc_fetch_evm_per_slot_trace."""
        response = self._invoke(
            self._client.ModAccFetchEVMPerSlotTrace,
            grpc_types.ModAccFetchEVMPerSlotTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(rms_evm_per_slot, "rms_evm_per_slot", "float32")
        if len(rms_evm_per_slot) != response.actual_array_size:
            rms_evm_per_slot.resize((response.actual_array_size,), refcheck=False)
        rms_evm_per_slot.flat[:] = response.rms_evm_per_slot
        return response.x0, response.dx, response.status

    def modacc_fetch_evm_per_subcarrier_trace(
        self, selector_string, timeout, mean_rms_evm_per_subcarrier
    ):
        """modacc_fetch_evm_per_subcarrier_trace."""
        response = self._invoke(
            self._client.ModAccFetchEVMPerSubcarrierTrace,
            grpc_types.ModAccFetchEVMPerSubcarrierTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            mean_rms_evm_per_subcarrier, "mean_rms_evm_per_subcarrier", "float32"
        )
        if len(mean_rms_evm_per_subcarrier) != response.actual_array_size:
            mean_rms_evm_per_subcarrier.resize((response.actual_array_size,), refcheck=False)
        mean_rms_evm_per_subcarrier.flat[:] = response.mean_rms_evm_per_subcarrier
        return response.x0, response.dx, response.status

    def modacc_fetch_evm_per_symbol_trace(self, selector_string, timeout, rms_evm_per_symbol):
        """modacc_fetch_evm_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchEVMPerSymbolTrace,
            grpc_types.ModAccFetchEVMPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(rms_evm_per_symbol, "rms_evm_per_symbol", "float32")
        if len(rms_evm_per_symbol) != response.actual_array_size:
            rms_evm_per_symbol.resize((response.actual_array_size,), refcheck=False)
        rms_evm_per_symbol.flat[:] = response.rms_evm_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_evm_high_per_symbol_trace(self, selector_string, timeout, evm_high_per_symbol):
        """modacc_fetch_evm_high_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchEVMHighPerSymbolTrace,
            grpc_types.ModAccFetchEVMHighPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(evm_high_per_symbol, "evm_high_per_symbol", "float32")
        if len(evm_high_per_symbol) != response.actual_array_size:
            evm_high_per_symbol.resize((response.actual_array_size,), refcheck=False)
        evm_high_per_symbol.flat[:] = response.evm_high_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_maximum_evm_high_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_high_per_symbol
    ):
        """modacc_fetch_maximum_evm_high_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumEVMHighPerSymbolTrace,
            grpc_types.ModAccFetchMaximumEVMHighPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            maximum_evm_high_per_symbol, "maximum_evm_high_per_symbol", "float32"
        )
        if len(maximum_evm_high_per_symbol) != response.actual_array_size:
            maximum_evm_high_per_symbol.resize((response.actual_array_size,), refcheck=False)
        maximum_evm_high_per_symbol.flat[:] = response.maximum_evm_high_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_evm_low_per_symbol_trace(self, selector_string, timeout, evm_low_per_symbol):
        """modacc_fetch_evm_low_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchEVMLowPerSymbolTrace,
            grpc_types.ModAccFetchEVMLowPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(evm_low_per_symbol, "evm_low_per_symbol", "float32")
        if len(evm_low_per_symbol) != response.actual_array_size:
            evm_low_per_symbol.resize((response.actual_array_size,), refcheck=False)
        evm_low_per_symbol.flat[:] = response.evm_low_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_maximum_evm_low_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_low_per_symbol
    ):
        """modacc_fetch_maximum_evm_low_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumEVMLowPerSymbolTrace,
            grpc_types.ModAccFetchMaximumEVMLowPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            maximum_evm_low_per_symbol, "maximum_evm_low_per_symbol", "float32"
        )
        if len(maximum_evm_low_per_symbol) != response.actual_array_size:
            maximum_evm_low_per_symbol.resize((response.actual_array_size,), refcheck=False)
        maximum_evm_low_per_symbol.flat[:] = response.maximum_evm_low_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_in_band_emission_margin_array(self, selector_string, timeout):
        """modacc_fetch_in_band_emission_margin_array."""
        response = self._invoke(
            self._client.ModAccFetchInBandEmissionMarginArray,
            grpc_types.ModAccFetchInBandEmissionMarginArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.in_band_emission_margin[:], response.status

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

    def modacc_fetch_iq_impairments_array(self, selector_string, timeout):
        """modacc_fetch_iq_impairments_array."""
        response = self._invoke(
            self._client.ModAccFetchIQImpairmentsArray,
            grpc_types.ModAccFetchIQImpairmentsArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_iq_origin_offset[:],
            response.mean_iq_gain_imbalance[:],
            response.mean_iq_quadrature_error[:],
            response.status,
        )

    def modacc_fetch_maximum_evm_per_slot_trace(
        self, selector_string, timeout, maximum_evm_per_slot
    ):
        """modacc_fetch_maximum_evm_per_slot_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumEVMPerSlotTrace,
            grpc_types.ModAccFetchMaximumEVMPerSlotTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(maximum_evm_per_slot, "maximum_evm_per_slot", "float32")
        if len(maximum_evm_per_slot) != response.actual_array_size:
            maximum_evm_per_slot.resize((response.actual_array_size,), refcheck=False)
        maximum_evm_per_slot.flat[:] = response.maximum_evm_per_slot
        return response.x0, response.dx, response.status

    def modacc_fetch_maximum_evm_per_subcarrier_trace(
        self, selector_string, timeout, maximum_evm_per_subcarrier
    ):
        """modacc_fetch_maximum_evm_per_subcarrier_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumEVMPerSubcarrierTrace,
            grpc_types.ModAccFetchMaximumEVMPerSubcarrierTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            maximum_evm_per_subcarrier, "maximum_evm_per_subcarrier", "float32"
        )
        if len(maximum_evm_per_subcarrier) != response.actual_array_size:
            maximum_evm_per_subcarrier.resize((response.actual_array_size,), refcheck=False)
        maximum_evm_per_subcarrier.flat[:] = response.maximum_evm_per_subcarrier
        return response.x0, response.dx, response.status

    def modacc_fetch_maximum_evm_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_per_symbol
    ):
        """modacc_fetch_maximum_evm_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumEVMPerSymbolTrace,
            grpc_types.ModAccFetchMaximumEVMPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(maximum_evm_per_symbol, "maximum_evm_per_symbol", "float32")
        if len(maximum_evm_per_symbol) != response.actual_array_size:
            maximum_evm_per_symbol.resize((response.actual_array_size,), refcheck=False)
        maximum_evm_per_symbol.flat[:] = response.maximum_evm_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_maximum_magnitude_error_per_symbol_trace(
        self, selector_string, timeout, maximum_magnitude_error_per_symbol
    ):
        """modacc_fetch_maximum_magnitude_error_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumMagnitudeErrorPerSymbolTrace,
            grpc_types.ModAccFetchMaximumMagnitudeErrorPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            maximum_magnitude_error_per_symbol, "maximum_magnitude_error_per_symbol", "float32"
        )
        if len(maximum_magnitude_error_per_symbol) != response.actual_array_size:
            maximum_magnitude_error_per_symbol.resize((response.actual_array_size,), refcheck=False)
        maximum_magnitude_error_per_symbol.flat[:] = response.maximum_magnitude_error_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_maximum_phase_error_per_symbol_trace(
        self, selector_string, timeout, maximum_phase_error_per_symbol
    ):
        """modacc_fetch_maximum_phase_error_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumPhaseErrorPerSymbolTrace,
            grpc_types.ModAccFetchMaximumPhaseErrorPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            maximum_phase_error_per_symbol, "maximum_phase_error_per_symbol", "float32"
        )
        if len(maximum_phase_error_per_symbol) != response.actual_array_size:
            maximum_phase_error_per_symbol.resize((response.actual_array_size,), refcheck=False)
        maximum_phase_error_per_symbol.flat[:] = response.maximum_phase_error_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_pdsch_1024_qam_constellation(
        self, selector_string, timeout, qam1024_constellation
    ):
        """modacc_fetch_pdsch_1024_qam_constellation."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH1024QAMConstellationInterleavedIQ,
            grpc_types.ModAccFetchPDSCH1024QAMConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam1024_constellation, "qam1024_constellation", "complex64")
        if len(qam1024_constellation) != response.actual_array_size // 2:
            qam1024_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam1024_constellation, dtype=numpy.float32)
        qam1024_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_1024_qam_evm_array(self, selector_string, timeout):
        """modacc_fetch_pdsch_1024_qam_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH1024QAMEVMArray,
            grpc_types.ModAccFetchPDSCH1024QAMEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_1024qam_evm[:], response.status

    def modacc_fetch_pdsch_16_qam_constellation(
        self, selector_string, timeout, qam16_constellation
    ):
        """modacc_fetch_pdsch_16_qam_constellation."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH16QAMConstellationInterleavedIQ,
            grpc_types.ModAccFetchPDSCH16QAMConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam16_constellation, "qam16_constellation", "complex64")
        if len(qam16_constellation) != response.actual_array_size // 2:
            qam16_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam16_constellation, dtype=numpy.float32)
        qam16_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_256_qam_constellation(
        self, selector_string, timeout, qam256_constellation
    ):
        """modacc_fetch_pdsch_256_qam_constellation."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH256QAMConstellationInterleavedIQ,
            grpc_types.ModAccFetchPDSCH256QAMConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam256_constellation, "qam256_constellation", "complex64")
        if len(qam256_constellation) != response.actual_array_size // 2:
            qam256_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam256_constellation, dtype=numpy.float32)
        qam256_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_64_qam_constellation(
        self, selector_string, timeout, qam64_constellation
    ):
        """modacc_fetch_pdsch_64_qam_constellation."""
        response = self._invoke(
            self._client.ModAccFetchPDSCH64QAMConstellationInterleavedIQ,
            grpc_types.ModAccFetchPDSCH64QAMConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qam64_constellation, "qam64_constellation", "complex64")
        if len(qam64_constellation) != response.actual_array_size // 2:
            qam64_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qam64_constellation, dtype=numpy.float32)
        qam64_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pdsch_evm_array(self, selector_string, timeout):
        """modacc_fetch_pdsch_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHEVMArray,
            grpc_types.ModAccFetchPDSCHEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_rms_evm[:],
            response.mean_rms_qpsk_evm[:],
            response.mean_rms_16qam_evm[:],
            response.mean_rms_64qam_evm[:],
            response.mean_rms_256qam_evm[:],
            response.status,
        )

    def modacc_fetch_pdsch_qpsk_constellation(self, selector_string, timeout, qpsk_constellation):
        """modacc_fetch_pdsch_qpsk_constellation."""
        response = self._invoke(
            self._client.ModAccFetchPDSCHQPSKConstellationInterleavedIQ,
            grpc_types.ModAccFetchPDSCHQPSKConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qpsk_constellation, "qpsk_constellation", "complex64")
        if len(qpsk_constellation) != response.actual_array_size // 2:
            qpsk_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qpsk_constellation, dtype=numpy.float32)
        qpsk_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_pssch_data_evm_array(self, selector_string, timeout):
        """modacc_fetch_pssch_data_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHDataEVMArray,
            grpc_types.ModAccFetchPSSCHDataEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.pssch_mean_rms_data_evm[:],
            response.pssch_maximum_peak_data_evm[:],
            response.status,
        )

    def modacc_fetch_pssch_dmrs_evm_array(self, selector_string, timeout):
        """modacc_fetch_pssch_dmrs_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHDMRSEVMArray,
            grpc_types.ModAccFetchPSSCHDMRSEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.pssch_mean_rms_dmrs_evm[:],
            response.pssch_maximum_peak_dmrs_evm[:],
            response.status,
        )

    def modacc_fetch_pssch_symbol_power_array(self, selector_string, timeout):
        """modacc_fetch_pssch_symbol_power_array."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHSymbolPowerArray,
            grpc_types.ModAccFetchPSSCHSymbolPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pssch_mean_data_power[:], response.pssch_mean_dmrs_power[:], response.status

    def modacc_fetch_pusch_data_evm_array(self, selector_string, timeout):
        """modacc_fetch_pusch_data_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDataEVMArray,
            grpc_types.ModAccFetchPUSCHDataEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_data_evm[:], response.maximum_peak_data_evm[:], response.status

    def modacc_fetch_pusch_demodulated_bits(self, selector_string, timeout):
        """modacc_fetch_pusch_demodulated_bits."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDemodulatedBits,
            grpc_types.ModAccFetchPUSCHDemodulatedBitsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.bits[:], response.status

    def modacc_fetch_pusch_dmrs_evm_array(self, selector_string, timeout):
        """modacc_fetch_pusch_dmrs_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHDMRSEVMArray,
            grpc_types.ModAccFetchPUSCHDMRSEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_dmrs_evm[:], response.maximum_peak_dmrs_evm[:], response.status

    def modacc_fetch_pusch_symbol_power_array(self, selector_string, timeout):
        """modacc_fetch_pusch_symbol_power_array."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHSymbolPowerArray,
            grpc_types.ModAccFetchPUSCHSymbolPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pusch_mean_data_power[:], response.pusch_mean_dmrs_power[:], response.status

    def modacc_fetch_rms_magnitude_error_per_symbol_trace(
        self, selector_string, timeout, rms_magnitude_error_per_symbol
    ):
        """modacc_fetch_rms_magnitude_error_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSMagnitudeErrorPerSymbolTrace,
            grpc_types.ModAccFetchRMSMagnitudeErrorPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            rms_magnitude_error_per_symbol, "rms_magnitude_error_per_symbol", "float32"
        )
        if len(rms_magnitude_error_per_symbol) != response.actual_array_size:
            rms_magnitude_error_per_symbol.resize((response.actual_array_size,), refcheck=False)
        rms_magnitude_error_per_symbol.flat[:] = response.rms_magnitude_error_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_rms_phase_error_per_symbol_trace(
        self, selector_string, timeout, rms_phase_error_per_symbol
    ):
        """modacc_fetch_rms_phase_error_per_symbol_trace."""
        response = self._invoke(
            self._client.ModAccFetchRMSPhaseErrorPerSymbolTrace,
            grpc_types.ModAccFetchRMSPhaseErrorPerSymbolTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            rms_phase_error_per_symbol, "rms_phase_error_per_symbol", "float32"
        )
        if len(rms_phase_error_per_symbol) != response.actual_array_size:
            rms_phase_error_per_symbol.resize((response.actual_array_size,), refcheck=False)
        rms_phase_error_per_symbol.flat[:] = response.rms_phase_error_per_symbol
        return response.x0, response.dx, response.status

    def modacc_fetch_spectral_flatness_array(self, selector_string, timeout):
        """modacc_fetch_spectral_flatness_array."""
        response = self._invoke(
            self._client.ModAccFetchSpectralFlatnessArray,
            grpc_types.ModAccFetchSpectralFlatnessArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.range1_maximum_to_range1_minimum[:],
            response.range2_maximum_to_range2_minimum[:],
            response.range1_maximum_to_range2_minimum[:],
            response.range2_maximum_to_range1_minimum[:],
            response.status,
        )

    def modacc_fetch_srs_constellation(self, selector_string, timeout, srs_constellation):
        """modacc_fetch_srs_constellation."""
        response = self._invoke(
            self._client.ModAccFetchSRSConstellationInterleavedIQ,
            grpc_types.ModAccFetchSRSConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(srs_constellation, "srs_constellation", "complex64")
        if len(srs_constellation) != response.actual_array_size // 2:
            srs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.srs_constellation, dtype=numpy.float32)
        srs_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_srs_evm_array(self, selector_string, timeout):
        """modacc_fetch_srs_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchSRSEVMArray,
            grpc_types.ModAccFetchSRSEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_srs_evm[:], response.mean_srs_power[:], response.status

    def modacc_fetch_subblock_in_band_emission_trace(self, selector_string, timeout):
        """modacc_fetch_subblock_in_band_emission_trace."""
        response = self._invoke(
            self._client.ModAccFetchSubblockInBandEmissionTrace,
            grpc_types.ModAccFetchSubblockInBandEmissionTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.subblock_in_band_emission[:],
            response.subblock_in_band_emission_mask[:],
            response.subblock_in_band_emission_rb_indices[:],
            response.status,
        )

    def modacc_fetch_synchronization_signal_constellation(
        self, selector_string, timeout, sss_constellation, pss_constellation
    ):
        """modacc_fetch_synchronization_signal_constellation."""
        response = self._invoke(
            self._client.ModAccFetchSynchronizationSignalConstellationInterleavedIQ,
            grpc_types.ModAccFetchSynchronizationSignalConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(sss_constellation, "sss_constellation", "complex64")
        if len(sss_constellation) != response.actual_array_size // 2:
            sss_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.sss_constellation, dtype=numpy.float32)
        sss_constellation[:] = flat.view(numpy.complex64)
        _helper.validate_numpy_array(pss_constellation, "pss_constellation", "complex64")
        if len(pss_constellation) != response.actual_array_size // 2:
            pss_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.pss_constellation, dtype=numpy.float32)
        pss_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_synchronization_signal_evm_array(self, selector_string, timeout):
        """modacc_fetch_synchronization_signal_evm_array."""
        response = self._invoke(
            self._client.ModAccFetchSynchronizationSignalEVMArray,
            grpc_types.ModAccFetchSynchronizationSignalEVMArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_rms_pss_evm[:], response.mean_rms_sss_evm[:], response.status

    def modacc_fetch_maximum_frequency_error_per_slot_trace(
        self, selector_string, timeout, maximum_frequency_error_per_slot
    ):
        """modacc_fetch_maximum_frequency_error_per_slot_trace."""
        response = self._invoke(
            self._client.ModAccFetchMaximumFrequencyErrorPerSlotTrace,
            grpc_types.ModAccFetchMaximumFrequencyErrorPerSlotTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            maximum_frequency_error_per_slot, "maximum_frequency_error_per_slot", "float32"
        )
        if len(maximum_frequency_error_per_slot) != response.actual_array_size:
            maximum_frequency_error_per_slot.resize((response.actual_array_size,), refcheck=False)
        maximum_frequency_error_per_slot.flat[:] = response.maximum_frequency_error_per_slot
        return response.x0, response.dx, response.status

    def modacc_fetch_npdsch_qpsk_constellation(self, selector_string, timeout, qpsk_constellation):
        """modacc_fetch_npdsch_qpsk_constellation."""
        response = self._invoke(
            self._client.ModAccFetchNPDSCHQPSKConstellationInterleavedIQ,
            grpc_types.ModAccFetchNPDSCHQPSKConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(qpsk_constellation, "qpsk_constellation", "complex64")
        if len(qpsk_constellation) != response.actual_array_size // 2:
            qpsk_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.qpsk_constellation, dtype=numpy.float32)
        qpsk_constellation[:] = flat.view(numpy.complex64)
        return response.status

    def modacc_fetch_nrs_constellation(self, selector_string, timeout, nrs_constellation):
        """modacc_fetch_nrs_constellation."""
        response = self._invoke(
            self._client.ModAccFetchNRSConstellationInterleavedIQ,
            grpc_types.ModAccFetchNRSConstellationInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(nrs_constellation, "nrs_constellation", "complex64")
        if len(nrs_constellation) != response.actual_array_size // 2:
            nrs_constellation.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.nrs_constellation, dtype=numpy.float32)
        nrs_constellation[:] = flat.view(numpy.complex64)
        return response.status

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
            response.absolute_integrated_power[:],
            response.relative_integrated_power[:],
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
            response.absolute_integrated_power[:],
            response.relative_integrated_power[:],
            response.absolute_peak_power[:],
            response.peak_frequency[:],
            response.relative_peak_power[:],
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
            response.absolute_integrated_power[:],
            response.relative_integrated_power[:],
            response.absolute_peak_power[:],
            response.peak_frequency[:],
            response.relative_peak_power[:],
            response.status,
        )

    def pvt_fetch_measurement_array(self, selector_string, timeout):
        """pvt_fetch_measurement_array."""
        response = self._invoke(
            self._client.PVTFetchMeasurementArray,
            grpc_types.PVTFetchMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            [enums.PvtMeasurementStatus(value) for value in response.measurement_status],
            response.mean_absolute_off_power_before[:],
            response.mean_absolute_off_power_after[:],
            response.mean_absolute_on_power[:],
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

    def slotphase_fetch_maximum_phase_discontinuity_array(self, selector_string, timeout):
        """slotphase_fetch_maximum_phase_discontinuity_array."""
        response = self._invoke(
            self._client.SlotPhaseFetchMaximumPhaseDiscontinuityArray,
            grpc_types.SlotPhaseFetchMaximumPhaseDiscontinuityArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.maximum_phase_discontinuity[:], response.status

    def slotphase_fetch_phase_discontinuities(self, selector_string, timeout):
        """slotphase_fetch_phase_discontinuities."""
        response = self._invoke(
            self._client.SlotPhaseFetchPhaseDiscontinuities,
            grpc_types.SlotPhaseFetchPhaseDiscontinuitiesRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.slot_phase_discontinuity[:], response.status

    def slotphase_fetch_sample_phase_error_linear_fit_trace(
        self, selector_string, timeout, sample_phase_error_linear_fit
    ):
        """slotphase_fetch_sample_phase_error_linear_fit_trace."""
        response = self._invoke(
            self._client.SlotPhaseFetchSamplePhaseErrorLinearFitTrace,
            grpc_types.SlotPhaseFetchSamplePhaseErrorLinearFitTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            sample_phase_error_linear_fit, "sample_phase_error_linear_fit", "float32"
        )
        if len(sample_phase_error_linear_fit) != response.actual_array_size:
            sample_phase_error_linear_fit.resize((response.actual_array_size,), refcheck=False)
        sample_phase_error_linear_fit.flat[:] = response.sample_phase_error_linear_fit
        return response.x0, response.dx, response.status

    def slotphase_fetch_sample_phase_error(self, selector_string, timeout, sample_phase_error):
        """slotphase_fetch_sample_phase_error."""
        response = self._invoke(
            self._client.SlotPhaseFetchSamplePhaseError,
            grpc_types.SlotPhaseFetchSamplePhaseErrorRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(sample_phase_error, "sample_phase_error", "float32")
        if len(sample_phase_error) != response.actual_array_size:
            sample_phase_error.resize((response.actual_array_size,), refcheck=False)
        sample_phase_error.flat[:] = response.sample_phase_error
        return response.x0, response.dx, response.status

    def slotpower_fetch_powers(self, selector_string, timeout):
        """slotpower_fetch_powers."""
        response = self._invoke(
            self._client.SlotPowerFetchPowers,
            grpc_types.SlotPowerFetchPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.subframe_power[:], response.subframe_power_delta[:], response.status

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

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        response = self._invoke(
            self._client.CloneSignalConfiguration,
            grpc_types.CloneSignalConfigurationRequest(instrument=self._vi, old_signal_name=old_signal_name, new_signal_name=new_signal_name),  # type: ignore
        )
        # signal_configuration = LteSignalConfiguration.get_lte_signal_configuration(self, new_signal_name)
        import nirfmxlte

        signal_configuration = nirfmxlte._LteSignalConfiguration.get_lte_signal_configuration(self._instr_session, new_signal_name, True)  # type: ignore
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

    def clear_noise_calibration_database(self, selector_string):
        """clear_noise_calibration_database."""
        response = self._invoke(
            self._client.ClearNoiseCalibrationDatabase,
            grpc_types.ClearNoiseCalibrationDatabaseRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
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

    def configure_downlink_auto_channel_detection(
        self,
        selector_string,
        auto_pdsch_channel_detection_enabled,
        auto_control_channel_power_detection_enabled,
        auto_pcfich_cfi_detection_enabled,
    ):
        """configure_downlink_auto_channel_detection."""
        response = self._invoke(
            self._client.CfgDownlinkAutoChannelDetection,
            grpc_types.CfgDownlinkAutoChannelDetectionRequest(instrument=self._vi, selector_string=selector_string, auto_pdsch_channel_detection_enabled=auto_pdsch_channel_detection_enabled, auto_control_channel_power_detection_enabled=auto_control_channel_power_detection_enabled, auto_pcfich_cfi_detection_enabled=auto_pcfich_cfi_detection_enabled),  # type: ignore
        )
        return response.status

    def modacc_fetch_pusch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        """modacc_fetch_pusch_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPUSCHConstellationTrace,
            grpc_types.ModAccFetchPUSCHConstellationTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != response.data_constellation_actual_array_size:
            data_constellation.resize(
                (response.data_constellation_actual_array_size,), refcheck=False
            )
        data_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.data_constellation],
            dtype=numpy.complex64,
        )
        _helper.validate_numpy_array(dmrs_constellation, "dmrs_constellation", "complex64")
        if len(dmrs_constellation) != response.dmrs_constellation_actual_array_size:
            dmrs_constellation.resize(
                (response.dmrs_constellation_actual_array_size,), refcheck=False
            )
        dmrs_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.dmrs_constellation],
            dtype=numpy.complex64,
        )
        return response.status

    def modacc_fetch_npusch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        """modacc_fetch_npusch_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchNPUSCHConstellationTrace,
            grpc_types.ModAccFetchNPUSCHConstellationTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != response.data_constellation_actual_array_size:
            data_constellation.resize(
                (response.data_constellation_actual_array_size,), refcheck=False
            )
        data_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.data_constellation],
            dtype=numpy.complex64,
        )
        _helper.validate_numpy_array(dmrs_constellation, "dmrs_constellation", "complex64")
        if len(dmrs_constellation) != response.dmrs_constellation_actual_array_size:
            dmrs_constellation.resize(
                (response.dmrs_constellation_actual_array_size,), refcheck=False
            )
        dmrs_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.dmrs_constellation],
            dtype=numpy.complex64,
        )
        return response.status

    def modacc_fetch_nb_synchronization_signal_constellation(
        self, selector_string, timeout, nsss_constellation, npss_constellation
    ):
        """modacc_fetch_nb_synchronization_signal_constellation."""
        response = self._invoke(
            self._client.ModAccFetchNBSynchronizationSignalConstellation,
            grpc_types.ModAccFetchNBSynchronizationSignalConstellationRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(nsss_constellation, "nsss_constellation", "complex64")
        if len(nsss_constellation) != response.nsss_constellation_actual_array_size:
            nsss_constellation.resize(
                (response.nsss_constellation_actual_array_size,), refcheck=False
            )
        nsss_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.nsss_constellation],
            dtype=numpy.complex64,
        )
        _helper.validate_numpy_array(npss_constellation, "npss_constellation", "complex64")
        if len(npss_constellation) != response.npss_constellation_actual_array_size:
            npss_constellation.resize(
                (response.npss_constellation_actual_array_size,), refcheck=False
            )
        npss_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.npss_constellation],
            dtype=numpy.complex64,
        )
        return response.status

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

    def modacc_fetch_pssch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        """modacc_fetch_pssch_constellation_trace."""
        response = self._invoke(
            self._client.ModAccFetchPSSCHConstellationTrace,
            grpc_types.ModAccFetchPSSCHConstellationTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != response.data_constellation_actual_array_size:
            data_constellation.resize(
                (response.data_constellation_actual_array_size,), refcheck=False
            )
        data_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.data_constellation],
            dtype=numpy.complex64,
        )
        _helper.validate_numpy_array(dmrs_constellation, "dmrs_constellation", "complex64")
        if len(dmrs_constellation) != response.dmrs_constellation_actual_array_size:
            dmrs_constellation.resize(
                (response.dmrs_constellation_actual_array_size,), refcheck=False
            )
        dmrs_constellation[:] = numpy.array(
            [complex(c.real, c.imaginary) for c in response.dmrs_constellation],
            dtype=numpy.complex64,
        )
        return response.status
