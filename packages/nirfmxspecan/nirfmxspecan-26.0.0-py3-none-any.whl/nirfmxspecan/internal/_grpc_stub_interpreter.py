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
import nirfmxspecan.enums as enums
import nirfmxspecan.errors as errors
import nirfmxspecan.internal._custom_types as _custom_types
import nirfmxspecan.internal._helper as _helper
import nirfmxspecan.internal.nidevice_pb2 as nidevice_grpc_types
import nirfmxspecan.internal.nirfmxspecan_pb2 as grpc_types
import nirfmxspecan.internal.nirfmxspecan_pb2_grpc as nirfmxspecan_grpc
import nirfmxspecan.internal.nirfmxspecan_restricted_pb2 as restricted_grpc_types
import nirfmxspecan.internal.nirfmxspecan_restricted_pb2_grpc as nirfmxspecan_restricted_grpc
import nirfmxspecan.internal.session_pb2 as session_grpc_types


class GrpcStubInterpreter(object):
    """Interpreter for interacting with a gRPC Stub class"""

    def __init__(self, grpc_options, session=None, signal_obj=None):
        self._grpc_options = grpc_options
        self._signal_obj = signal_obj
        self._instr_session = session
        self._client = nirfmxspecan_grpc.NiRFmxSpecAnStub(grpc_options.grpc_channel)  # type: ignore
        self._restricted_client = nirfmxspecan_restricted_grpc.NiRFmxSpecAnRestrictedStub(grpc_options.grpc_channel)  # type: ignore
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
                local_personality.value == nirfmxinstr.Personalities.SPECAN.value
            )
        else:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj.signal_configuration_name
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.SPECAN.value
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

    def nf_clear_calibration_database(self, calibration_setup_id):
        """nf_clear_calibration_database."""
        response = self._invoke(
            self._client.NFClearCalibrationDatabase,
            grpc_types.NFClearCalibrationDatabaseRequest(instrument=self._vi, calibration_setup_id=calibration_setup_id),  # type: ignore
        )
        return response.status

    def nf_configure_frequency_list_start_stop_points(
        self, selector_string, start_frequency, stop_frequency, number_of_points
    ):
        """nf_configure_frequency_list_start_stop_points."""
        response = self._invoke(
            self._client.NFCfgFrequencyListStartStopPoints,
            grpc_types.NFCfgFrequencyListStartStopPointsRequest(instrument=self._vi, selector_string=selector_string, start_frequency=start_frequency, stop_frequency=stop_frequency, number_of_points=number_of_points),  # type: ignore
        )
        return response.status

    def nf_configure_frequency_list_start_stop_step(
        self, selector_string, start_frequency, stop_frequency, step_size
    ):
        """nf_configure_frequency_list_start_stop_step."""
        response = self._invoke(
            self._client.NFCfgFrequencyListStartStopStep,
            grpc_types.NFCfgFrequencyListStartStopStepRequest(instrument=self._vi, selector_string=selector_string, start_frequency=start_frequency, stop_frequency=stop_frequency, step_size=step_size),  # type: ignore
        )
        return response.status

    def nf_recommend_reference_level(self, selector_string, dut_max_gain, dut_max_noise_figure):
        """nf_recommend_reference_level."""
        response = self._invoke(
            self._client.NFRecommendReferenceLevel,
            grpc_types.NFRecommendReferenceLevelRequest(instrument=self._vi, selector_string=selector_string, dut_max_gain=dut_max_gain, dut_max_noise_figure=dut_max_noise_figure),  # type: ignore
        )
        return response.reference_level, response.status

    def nf_validate_calibration_data(self, selector_string):
        """nf_validate_calibration_data."""
        response = self._invoke(
            self._client.NFValidateCalibrationData,
            grpc_types.NFValidateCalibrationDataRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return enums.NFCalibrationDataValid(response.calibration_data_valid), response.status

    def nf_load_dut_input_loss_from_s2p(
        self,
        selector_string,
        dut_input_loss_compensation_enabled,
        dut_input_loss_s2p_file_path,
        dut_input_loss_s_parameter_orientation,
        dut_input_loss_temperature,
    ):
        """nf_load_dut_input_loss_from_s2p."""
        response = self._invoke(
            self._client.NFLoadDUTInputLossFromS2p,
            grpc_types.NFLoadDUTInputLossFromS2pRequest(instrument=self._vi, selector_string=selector_string, dut_input_loss_compensation_enabled_raw=dut_input_loss_compensation_enabled, dut_input_loss_s2p_file_path=dut_input_loss_s2p_file_path, dut_input_loss_s_parameter_orientation_raw=dut_input_loss_s_parameter_orientation, dut_input_loss_temperature=dut_input_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_load_dut_output_loss_from_s2p(
        self,
        selector_string,
        dut_output_loss_compensation_enabled,
        dut_output_loss_s2p_file_path,
        dut_output_loss_s_parameter_orientation,
        dut_output_loss_temperature,
    ):
        """nf_load_dut_output_loss_from_s2p."""
        response = self._invoke(
            self._client.NFLoadDUTOutputLossFromS2p,
            grpc_types.NFLoadDUTOutputLossFromS2pRequest(instrument=self._vi, selector_string=selector_string, dut_output_loss_compensation_enabled_raw=dut_output_loss_compensation_enabled, dut_output_loss_s2p_file_path=dut_output_loss_s2p_file_path, dut_output_loss_s_parameter_orientation_raw=dut_output_loss_s_parameter_orientation, dut_output_loss_temperature=dut_output_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_load_calibration_loss_from_s2p(
        self,
        selector_string,
        calibration_loss_compensation_enabled,
        calibration_loss_s2p_file_path,
        calibration_loss_s_parameter_orientation,
        calibration_loss_temperature,
    ):
        """nf_load_calibration_loss_from_s2p."""
        response = self._invoke(
            self._client.NFLoadCalibrationLossFromS2p,
            grpc_types.NFLoadCalibrationLossFromS2pRequest(instrument=self._vi, selector_string=selector_string, calibration_loss_compensation_enabled_raw=calibration_loss_compensation_enabled, calibration_loss_s2p_file_path=calibration_loss_s2p_file_path, calibration_loss_s_parameter_orientation_raw=calibration_loss_s_parameter_orientation, calibration_loss_temperature=calibration_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_load_cold_source_dut_s_parameter_from_s2p(
        self, selector_string, dut_s_parameters_s2p_file_path, dut_s_parameter_orientation
    ):
        """nf_load_cold_source_dut_s_parameter_from_s2p."""
        response = self._invoke(
            self._client.NFLoadColdSourceDUTSParametersFromS2p,
            grpc_types.NFLoadColdSourceDUTSParametersFromS2pRequest(instrument=self._vi, selector_string=selector_string, dut_s_parameters_s2p_file_path=dut_s_parameters_s2p_file_path, dut_s_parameter_orientation_raw=dut_s_parameter_orientation),  # type: ignore
        )
        return response.status

    def nf_load_y_factor_noise_source_loss_from_s2p(
        self,
        selector_string,
        noise_source_loss_compensation_enabled,
        noise_source_loss_s2p_file_path,
        noise_source_loss_s_parameter_orientation,
        noise_source_loss_temperature,
    ):
        """nf_load_y_factor_noise_source_loss_from_s2p."""
        response = self._invoke(
            self._client.NFLoadYFactorNoiseSourceLossFromS2p,
            grpc_types.NFLoadYFactorNoiseSourceLossFromS2pRequest(instrument=self._vi, selector_string=selector_string, noise_source_loss_compensation_enabled_raw=noise_source_loss_compensation_enabled, noise_source_loss_s2p_file_path=noise_source_loss_s2p_file_path, noise_source_loss_s_parameter_orientation_raw=noise_source_loss_s_parameter_orientation, noise_source_loss_temperature=noise_source_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_load_cold_source_input_termination_from_s1p(
        self, selector_string, termination_s1p_file_path, termination_temperature
    ):
        """nf_load_cold_source_input_termination_from_s1p."""
        response = self._invoke(
            self._client.NFLoadColdSourceInputTerminationFromS1p,
            grpc_types.NFLoadColdSourceInputTerminationFromS1pRequest(instrument=self._vi, selector_string=selector_string, termination_s1p_file_path=termination_s1p_file_path, termination_temperature=termination_temperature),  # type: ignore
        )
        return response.status

    def nf_load_external_preamp_gain_from_s2p(
        self,
        selector_string,
        external_preamp_present,
        external_preamp_gain_s2p_file_path,
        external_preamp_gain_s_parameter_orientation,
    ):
        """nf_load_external_preamp_gain_from_s2p."""
        response = self._invoke(
            self._client.NFLoadExternalPreampGainFromS2p,
            grpc_types.NFLoadExternalPreampGainFromS2pRequest(instrument=self._vi, selector_string=selector_string, external_preamp_present_raw=external_preamp_present, external_preamp_gain_s2p_file_path=external_preamp_gain_s2p_file_path, external_preamp_gain_s_parameter_orientation_raw=external_preamp_gain_s_parameter_orientation),  # type: ignore
        )
        return response.status

    def spectrum_configure_frequency_start_stop(
        self, selector_string, start_frequency, stop_frequency
    ):
        """spectrum_configure_frequency_start_stop."""
        response = self._invoke(
            self._client.SpectrumCfgFrequencyStartStop,
            grpc_types.SpectrumCfgFrequencyStartStopRequest(instrument=self._vi, selector_string=selector_string, start_frequency=start_frequency, stop_frequency=stop_frequency),  # type: ignore
        )
        return response.status

    def spectrum_validate_noise_calibration_data(self, selector_string):
        """spectrum_validate_noise_calibration_data."""
        response = self._invoke(
            self._client.SpectrumValidateNoiseCalibrationData,
            grpc_types.SpectrumValidateNoiseCalibrationDataRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return (
            enums.SpectrumNoiseCalibrationDataValid(response.noise_calibration_data_valid),
            response.status,
        )

    def ampm_configure_reference_waveform(
        self, selector_string, x0, dx, reference_waveform, idle_duration_present, signal_type
    ):
        """ampm_configure_reference_waveform."""
        _helper.validate_numpy_array(reference_waveform, "reference_waveform", "complex64")
        reference_waveform_proto = reference_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.AMPMCfgReferenceWaveformInterleavedIQ,
            grpc_types.AMPMCfgReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, reference_waveform=reference_waveform_proto, idle_duration_present_raw=idle_duration_present, signal_type_raw=signal_type),  # type: ignore
        )
        return response.status

    def dpd_configure_user_dpd_polynomial(self, selector_string, dpd_polynomial):
        """dpd_configure_user_dpd_polynomial."""
        _helper.validate_numpy_array(dpd_polynomial, "dpd_polynomial", "complex64")
        dpd_polynomial_proto = dpd_polynomial.view(numpy.float32)
        response = self._invoke(
            self._client.DPDCfgApplyDPDUserDPDPolynomialInterleavedIQ,
            grpc_types.DPDCfgApplyDPDUserDPDPolynomialInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, dpd_polynomial=dpd_polynomial_proto),  # type: ignore
        )
        return response.status

    def dpd_configure_user_lookup_table(self, selector_string, lut_input_powers, lut_complex_gains):
        """dpd_configure_user_lookup_table."""
        _helper.validate_numpy_array(lut_complex_gains, "lut_complex_gains", "complex64")
        lut_complex_gains_proto = lut_complex_gains.view(numpy.float32)
        response = self._invoke(
            self._client.DPDCfgApplyDPDUserLookupTableInterleavedIQ,
            grpc_types.DPDCfgApplyDPDUserLookupTableInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, lut_input_powers=lut_input_powers, lut_complex_gains=lut_complex_gains_proto),  # type: ignore
        )
        return response.status

    def dpd_configure_previous_dpd_polynomial(self, selector_string, previous_dpd_polynomial):
        """dpd_configure_previous_dpd_polynomial."""
        _helper.validate_numpy_array(
            previous_dpd_polynomial, "previous_dpd_polynomial", "complex64"
        )
        previous_dpd_polynomial_proto = previous_dpd_polynomial.view(numpy.float32)
        response = self._invoke(
            self._client.DPDCfgPreviousDPDPolynomialInterleavedIQ,
            grpc_types.DPDCfgPreviousDPDPolynomialInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, previous_dpd_polynomial=previous_dpd_polynomial_proto),  # type: ignore
        )
        return response.status

    def dpd_configure_reference_waveform(
        self, selector_string, x0, dx, reference_waveform, idle_duration_present, signal_type
    ):
        """dpd_configure_reference_waveform."""
        _helper.validate_numpy_array(reference_waveform, "reference_waveform", "complex64")
        reference_waveform_proto = reference_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.DPDCfgReferenceWaveformInterleavedIQ,
            grpc_types.DPDCfgReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, reference_waveform=reference_waveform_proto, idle_duration_present_raw=idle_duration_present, signal_type_raw=signal_type),  # type: ignore
        )
        return response.status

    def dpd_configure_extract_model_target_waveform(self, selector_string, x0, dx, target_waveform):
        """dpd_configure_extract_model_target_waveform."""
        _helper.validate_numpy_array(target_waveform, "target_waveform", "complex64")
        target_waveform_proto = target_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.DPDCfgExtractModelTargetWaveformInterleavedIQ,
            grpc_types.DPDCfgExtractModelTargetWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, target_waveform=target_waveform_proto),  # type: ignore
        )
        return response.status

    def acp_configure_carrier_and_offsets(
        self, selector_string, integration_bandwidth, number_of_offsets, channel_spacing
    ):
        """acp_configure_carrier_and_offsets."""
        response = self._invoke(
            self._client.ACPCfgCarrierAndOffsets,
            grpc_types.ACPCfgCarrierAndOffsetsRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth=integration_bandwidth, number_of_offsets=number_of_offsets, channel_spacing=channel_spacing),  # type: ignore
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

    def marker_configure_number_of_markers(self, selector_string, number_of_markers):
        """marker_configure_number_of_markers."""
        response = self._invoke(
            self._client.MarkerCfgNumberOfMarkers,
            grpc_types.MarkerCfgNumberOfMarkersRequest(instrument=self._vi, selector_string=selector_string, number_of_markers=number_of_markers),  # type: ignore
        )
        return response.status

    def marker_configure_peak_excursion(
        self, selector_string, peak_excursion_enabled, peak_excursion
    ):
        """marker_configure_peak_excursion."""
        response = self._invoke(
            self._client.MarkerCfgPeakExcursion,
            grpc_types.MarkerCfgPeakExcursionRequest(instrument=self._vi, selector_string=selector_string, peak_excursion_enabled_raw=peak_excursion_enabled, peak_excursion=peak_excursion),  # type: ignore
        )
        return response.status

    def marker_configure_reference_marker(self, selector_string, reference_marker):
        """marker_configure_reference_marker."""
        response = self._invoke(
            self._client.MarkerCfgReferenceMarker,
            grpc_types.MarkerCfgReferenceMarkerRequest(instrument=self._vi, selector_string=selector_string, reference_marker=reference_marker),  # type: ignore
        )
        return response.status

    def marker_configure_threshold(self, selector_string, threshold_enabled, threshold):
        """marker_configure_threshold."""
        response = self._invoke(
            self._client.MarkerCfgThreshold,
            grpc_types.MarkerCfgThresholdRequest(instrument=self._vi, selector_string=selector_string, threshold_enabled_raw=threshold_enabled, threshold=threshold),  # type: ignore
        )
        return response.status

    def marker_configure_trace(self, selector_string, trace):
        """marker_configure_trace."""
        response = self._invoke(
            self._client.MarkerCfgTrace,
            grpc_types.MarkerCfgTraceRequest(instrument=self._vi, selector_string=selector_string, trace_raw=trace),  # type: ignore
        )
        return response.status

    def marker_configure_type(self, selector_string, marker_type):
        """marker_configure_type."""
        response = self._invoke(
            self._client.MarkerCfgType,
            grpc_types.MarkerCfgTypeRequest(instrument=self._vi, selector_string=selector_string, marker_type_raw=marker_type),  # type: ignore
        )
        return response.status

    def marker_configure_x_location(self, selector_string, marker_x_location):
        """marker_configure_x_location."""
        response = self._invoke(
            self._client.MarkerCfgXLocation,
            grpc_types.MarkerCfgXLocationRequest(instrument=self._vi, selector_string=selector_string, marker_x_location=marker_x_location),  # type: ignore
        )
        return response.status

    def marker_configure_y_location(self, selector_string, marker_y_location):
        """marker_configure_y_location."""
        response = self._invoke(
            self._client.MarkerCfgYLocation,
            grpc_types.MarkerCfgYLocationRequest(instrument=self._vi, selector_string=selector_string, marker_y_location=marker_y_location),  # type: ignore
        )
        return response.status

    def marker_configure_function_type(self, selector_string, function_type):
        """marker_configure_function_type."""
        response = self._invoke(
            self._client.MarkerCfgFunctionType,
            grpc_types.MarkerCfgFunctionTypeRequest(instrument=self._vi, selector_string=selector_string, function_type_raw=function_type),  # type: ignore
        )
        return response.status

    def marker_configure_band_span(self, selector_string, span):
        """marker_configure_band_span."""
        response = self._invoke(
            self._client.MarkerCfgBandSpan,
            grpc_types.MarkerCfgBandSpanRequest(instrument=self._vi, selector_string=selector_string, span=span),  # type: ignore
        )
        return response.status

    def pavt_configure_segment_start_time_step(
        self, selector_string, number_of_segments, segment0_start_time, segment_interval
    ):
        """pavt_configure_segment_start_time_step."""
        response = self._invoke(
            self._client.PAVTCfgSegmentStartTimeStep,
            grpc_types.PAVTCfgSegmentStartTimeStepRequest(instrument=self._vi, selector_string=selector_string, number_of_segments=number_of_segments, segment0_start_time=segment0_start_time, segment_interval=segment_interval),  # type: ignore
        )
        return response.status

    def idpd_configure_reference_waveform(
        self, selector_string, x0, dx, reference_waveform, idle_duration_present, signal_type
    ):
        """idpd_configure_reference_waveform."""
        _helper.validate_numpy_array(reference_waveform, "reference_waveform", "complex64")
        reference_waveform_proto = reference_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.IDPDCfgReferenceWaveformInterleavedIQ,
            grpc_types.IDPDCfgReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, reference_waveform=reference_waveform_proto, idle_duration_present_raw=idle_duration_present, signal_type_raw=signal_type),  # type: ignore
        )
        return response.status

    def idpd_configure_predistorted_waveform(
        self, selector_string, x0, dx, predistorted_waveform, target_gain
    ):
        """idpd_configure_predistorted_waveform."""
        _helper.validate_numpy_array(predistorted_waveform, "predistorted_waveform", "complex64")
        predistorted_waveform_proto = predistorted_waveform.view(numpy.float32)
        response = self._invoke(
            self._client.IDPDCfgPredistortedWaveformInterleavedIQ,
            grpc_types.IDPDCfgPredistortedWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, predistorted_waveform=predistorted_waveform_proto, target_gain=target_gain),  # type: ignore
        )
        return response.status

    def idpd_configure_equalizer_coefficients(
        self, selector_string, x0, dx, equalizer_coefficients
    ):
        """idpd_configure_equalizer_coefficients."""
        _helper.validate_numpy_array(equalizer_coefficients, "equalizer_coefficients", "complex64")
        equalizer_coefficients_proto = equalizer_coefficients.view(numpy.float32)
        response = self._invoke(
            self._client.IDPDCfgEqualizerCoefficientsInterleavedIQ,
            grpc_types.IDPDCfgEqualizerCoefficientsInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0=x0, dx=dx, equalizer_coefficients=equalizer_coefficients_proto),  # type: ignore
        )
        return response.status

    def abort_measurements(self, selector_string):
        """abort_measurements."""
        response = self._invoke(
            self._client.AbortMeasurements,
            grpc_types.AbortMeasurementsRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def auto_level(self, selector_string, bandwidth, measurement_interval):
        """auto_level."""
        response = self._invoke(
            self._client.AutoLevel,
            grpc_types.AutoLevelRequest(instrument=self._vi, selector_string=selector_string, bandwidth=bandwidth, measurement_interval=measurement_interval),  # type: ignore
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

    def configure_iq_power_edge_trigger(
        self,
        selector_string,
        iq_power_edge_trigger_source,
        iq_power_edge_trigger_level,
        iq_power_edge_slope,
        trigger_delay,
        minimum_quiet_time_mode,
        minimum_quiet_time_duration,
        enable_trigger,
    ):
        """configure_iq_power_edge_trigger."""
        response = self._invoke(
            self._client.CfgIQPowerEdgeTrigger,
            grpc_types.CfgIQPowerEdgeTriggerRequest(instrument=self._vi, selector_string=selector_string, iq_power_edge_source=iq_power_edge_trigger_source, iq_power_edge_level=iq_power_edge_trigger_level, iq_power_edge_slope_raw=iq_power_edge_slope, trigger_delay=trigger_delay, trigger_min_quiet_time_mode=minimum_quiet_time_mode, trigger_min_quiet_time_duration=minimum_quiet_time_duration, enable_trigger=enable_trigger),  # type: ignore
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

    def im_configure_auto_intermods_setup(
        self, selector_string, auto_intermods_setup_enabled, maximum_intermod_order
    ):
        """im_configure_auto_intermods_setup."""
        response = self._invoke(
            self._client.IMCfgAutoIntermodsSetup,
            grpc_types.IMCfgAutoIntermodsSetupRequest(instrument=self._vi, selector_string=selector_string, auto_intermods_setup_enabled_raw=auto_intermods_setup_enabled, maximum_intermod_order=maximum_intermod_order),  # type: ignore
        )
        return response.status

    def im_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """im_configure_averaging."""
        response = self._invoke(
            self._client.IMCfgAveraging,
            grpc_types.IMCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def im_configure_fft(self, selector_string, fft_window, fft_padding):
        """im_configure_fft."""
        response = self._invoke(
            self._client.IMCfgFFT,
            grpc_types.IMCfgFFTRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window, fft_padding=fft_padding),  # type: ignore
        )
        return response.status

    def im_configure_frequency_definition(self, selector_string, frequency_definition):
        """im_configure_frequency_definition."""
        response = self._invoke(
            self._client.IMCfgFrequencyDefinition,
            grpc_types.IMCfgFrequencyDefinitionRequest(instrument=self._vi, selector_string=selector_string, frequency_definition_raw=frequency_definition),  # type: ignore
        )
        return response.status

    def im_configure_fundamental_tones(
        self, selector_string, lower_tone_frequency, upper_tone_frequency
    ):
        """im_configure_fundamental_tones."""
        response = self._invoke(
            self._client.IMCfgFundamentalTones,
            grpc_types.IMCfgFundamentalTonesRequest(instrument=self._vi, selector_string=selector_string, lower_tone_frequency=lower_tone_frequency, upper_tone_frequency=upper_tone_frequency),  # type: ignore
        )
        return response.status

    def im_configure_intermod_array(
        self,
        selector_string,
        intermod_order,
        lower_intermod_frequency,
        upper_intermod_frequency,
        intermod_side,
        intermod_enabled,
    ):
        """im_configure_intermod_array."""
        response = self._invoke(
            self._client.IMCfgIntermodArray,
            grpc_types.IMCfgIntermodArrayRequest(instrument=self._vi, selector_string=selector_string, intermod_order=intermod_order, lower_intermod_frequency=lower_intermod_frequency, upper_intermod_frequency=upper_intermod_frequency, intermod_side=intermod_side, intermod_enabled=intermod_enabled),  # type: ignore
        )
        return response.status

    def im_configure_intermod(
        self,
        selector_string,
        intermod_order,
        lower_intermod_frequency,
        upper_intermod_frequency,
        intermod_side,
        intermod_enabled,
    ):
        """im_configure_intermod."""
        response = self._invoke(
            self._client.IMCfgIntermod,
            grpc_types.IMCfgIntermodRequest(instrument=self._vi, selector_string=selector_string, intermod_order=intermod_order, lower_intermod_frequency=lower_intermod_frequency, upper_intermod_frequency=upper_intermod_frequency, intermod_side_raw=intermod_side, intermod_enabled_raw=intermod_enabled),  # type: ignore
        )
        return response.status

    def im_configure_measurement_method(self, selector_string, measurement_method):
        """im_configure_measurement_method."""
        response = self._invoke(
            self._client.IMCfgMeasurementMethod,
            grpc_types.IMCfgMeasurementMethodRequest(instrument=self._vi, selector_string=selector_string, measurement_method_raw=measurement_method),  # type: ignore
        )
        return response.status

    def im_configure_number_of_intermods(self, selector_string, number_of_intermods):
        """im_configure_number_of_intermods."""
        response = self._invoke(
            self._client.IMCfgNumberOfIntermods,
            grpc_types.IMCfgNumberOfIntermodsRequest(instrument=self._vi, selector_string=selector_string, number_of_intermods=number_of_intermods),  # type: ignore
        )
        return response.status

    def im_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """im_configure_rbw_filter."""
        response = self._invoke(
            self._client.IMCfgRBWFilter,
            grpc_types.IMCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def im_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """im_configure_sweep_time."""
        response = self._invoke(
            self._client.IMCfgSweepTime,
            grpc_types.IMCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def nf_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """nf_configure_averaging."""
        response = self._invoke(
            self._client.NFCfgAveraging,
            grpc_types.NFCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def nf_configure_calibration_loss(
        self,
        selector_string,
        calibration_loss_compensation_enabled,
        calibration_loss_frequency,
        calibration_loss,
        calibration_loss_temperature,
    ):
        """nf_configure_calibration_loss."""
        response = self._invoke(
            self._client.NFCfgCalibrationLoss,
            grpc_types.NFCfgCalibrationLossRequest(instrument=self._vi, selector_string=selector_string, calibration_loss_compensation_enabled_raw=calibration_loss_compensation_enabled, calibration_loss_frequency=calibration_loss_frequency, calibration_loss=calibration_loss, calibration_loss_temperature=calibration_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_configure_cold_source_dut_s_parameters(
        self, selector_string, dut_s_parameters_frequency, dut_s21, dut_s12, dut_s11, dut_s22
    ):
        """nf_configure_cold_source_dut_s_parameters."""
        response = self._invoke(
            self._client.NFCfgColdSourceDUTSParameters,
            grpc_types.NFCfgColdSourceDUTSParametersRequest(instrument=self._vi, selector_string=selector_string, dut_s_parameters_frequency=dut_s_parameters_frequency, dut_s21=dut_s21, dut_s12=dut_s12, dut_s11=dut_s11, dut_s22=dut_s22),  # type: ignore
        )
        return response.status

    def nf_configure_cold_source_input_termination(
        self, selector_string, termination_vswr, termination_vswr_frequency, termination_temperature
    ):
        """nf_configure_cold_source_input_termination."""
        response = self._invoke(
            self._client.NFCfgColdSourceInputTermination,
            grpc_types.NFCfgColdSourceInputTerminationRequest(instrument=self._vi, selector_string=selector_string, termination_vswr=termination_vswr, termination_vswr_frequency=termination_vswr_frequency, termination_temperature=termination_temperature),  # type: ignore
        )
        return response.status

    def nf_configure_cold_source_mode(self, selector_string, cold_source_mode):
        """nf_configure_cold_source_mode."""
        response = self._invoke(
            self._client.NFCfgColdSourceMode,
            grpc_types.NFCfgColdSourceModeRequest(instrument=self._vi, selector_string=selector_string, cold_source_mode_raw=cold_source_mode),  # type: ignore
        )
        return response.status

    def nf_configure_dut_input_loss(
        self,
        selector_string,
        dut_input_loss_compensation_enabled,
        dut_input_loss_frequency,
        dut_input_loss,
        dut_input_loss_temperature,
    ):
        """nf_configure_dut_input_loss."""
        response = self._invoke(
            self._client.NFCfgDUTInputLoss,
            grpc_types.NFCfgDUTInputLossRequest(instrument=self._vi, selector_string=selector_string, dut_input_loss_compensation_enabled_raw=dut_input_loss_compensation_enabled, dut_input_loss_frequency=dut_input_loss_frequency, dut_input_loss=dut_input_loss, dut_input_loss_temperature=dut_input_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_configure_dut_output_loss(
        self,
        selector_string,
        dut_output_loss_compensation_enabled,
        dut_output_loss_frequency,
        dut_output_loss,
        dut_output_loss_temperature,
    ):
        """nf_configure_dut_output_loss."""
        response = self._invoke(
            self._client.NFCfgDUTOutputLoss,
            grpc_types.NFCfgDUTOutputLossRequest(instrument=self._vi, selector_string=selector_string, dut_output_loss_compensation_enabled_raw=dut_output_loss_compensation_enabled, dut_output_loss_frequency=dut_output_loss_frequency, dut_output_loss=dut_output_loss, dut_output_loss_temperature=dut_output_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_configure_frequency_list(self, selector_string, frequency_list):
        """nf_configure_frequency_list."""
        response = self._invoke(
            self._client.NFCfgFrequencyList,
            grpc_types.NFCfgFrequencyListRequest(instrument=self._vi, selector_string=selector_string, frequency_list=frequency_list),  # type: ignore
        )
        return response.status

    def nf_configure_measurement_bandwidth(self, selector_string, measurement_bandwidth):
        """nf_configure_measurement_bandwidth."""
        response = self._invoke(
            self._client.NFCfgMeasurementBandwidth,
            grpc_types.NFCfgMeasurementBandwidthRequest(instrument=self._vi, selector_string=selector_string, measurement_bandwidth=measurement_bandwidth),  # type: ignore
        )
        return response.status

    def nf_configure_measurement_interval(self, selector_string, measurement_interval):
        """nf_configure_measurement_interval."""
        response = self._invoke(
            self._client.NFCfgMeasurementInterval,
            grpc_types.NFCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def nf_configure_measurement_method(self, selector_string, measurement_method):
        """nf_configure_measurement_method."""
        response = self._invoke(
            self._client.NFCfgMeasurementMethod,
            grpc_types.NFCfgMeasurementMethodRequest(instrument=self._vi, selector_string=selector_string, measurement_method_raw=measurement_method),  # type: ignore
        )
        return response.status

    def nf_configure_y_factor_mode(self, selector_string, y_factor_mode):
        """nf_configure_y_factor_mode."""
        response = self._invoke(
            self._client.NFCfgYFactorMode,
            grpc_types.NFCfgYFactorModeRequest(instrument=self._vi, selector_string=selector_string, y_factor_mode_raw=y_factor_mode),  # type: ignore
        )
        return response.status

    def nf_configure_y_factor_noise_source_enr(
        self, selector_string, enr_frequency, enr, cold_temperature, off_temperature
    ):
        """nf_configure_y_factor_noise_source_enr."""
        response = self._invoke(
            self._client.NFCfgYFactorNoiseSourceENR,
            grpc_types.NFCfgYFactorNoiseSourceENRRequest(instrument=self._vi, selector_string=selector_string, enr_frequency=enr_frequency, enr=enr, cold_temperature=cold_temperature, off_temperature=off_temperature),  # type: ignore
        )
        return response.status

    def nf_configure_y_factor_noise_source_loss(
        self,
        selector_string,
        noise_source_loss_compensation_enabled,
        noise_source_loss_frequency,
        noise_source_loss,
        noise_source_loss_temperature,
    ):
        """nf_configure_y_factor_noise_source_loss."""
        response = self._invoke(
            self._client.NFCfgYFactorNoiseSourceLoss,
            grpc_types.NFCfgYFactorNoiseSourceLossRequest(instrument=self._vi, selector_string=selector_string, noise_source_loss_compensation_enabled_raw=noise_source_loss_compensation_enabled, noise_source_loss_frequency=noise_source_loss_frequency, noise_source_loss=noise_source_loss, noise_source_loss_temperature=noise_source_loss_temperature),  # type: ignore
        )
        return response.status

    def nf_configure_y_factor_noise_source_settling_time(self, selector_string, settling_time):
        """nf_configure_y_factor_noise_source_settling_time."""
        response = self._invoke(
            self._client.NFCfgYFactorNoiseSourceSettlingTime,
            grpc_types.NFCfgYFactorNoiseSourceSettlingTimeRequest(instrument=self._vi, selector_string=selector_string, settling_time=settling_time),  # type: ignore
        )
        return response.status

    def fcnt_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """fcnt_configure_averaging."""
        response = self._invoke(
            self._client.FCntCfgAveraging,
            grpc_types.FCntCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def fcnt_configure_measurement_interval(self, selector_string, measurement_interval):
        """fcnt_configure_measurement_interval."""
        response = self._invoke(
            self._client.FCntCfgMeasurementInterval,
            grpc_types.FCntCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def fcnt_configure_rbw_filter(self, selector_string, rbw, rbw_filter_type, rrc_alpha):
        """fcnt_configure_rbw_filter."""
        response = self._invoke(
            self._client.FCntCfgRBWFilter,
            grpc_types.FCntCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw=rbw, rbw_filter_type_raw=rbw_filter_type, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def fcnt_configure_threshold(
        self, selector_string, threshold_enabled, threshold_level, threshold_type
    ):
        """fcnt_configure_threshold."""
        response = self._invoke(
            self._client.FCntCfgThreshold,
            grpc_types.FCntCfgThresholdRequest(instrument=self._vi, selector_string=selector_string, threshold_enabled_raw=threshold_enabled, threshold_level=threshold_level, threshold_type_raw=threshold_type),  # type: ignore
        )
        return response.status

    def spectrum_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """spectrum_configure_averaging."""
        response = self._invoke(
            self._client.SpectrumCfgAveraging,
            grpc_types.SpectrumCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def spectrum_configure_detector(self, selector_string, detector_type, detector_points):
        """spectrum_configure_detector."""
        response = self._invoke(
            self._client.SpectrumCfgDetector,
            grpc_types.SpectrumCfgDetectorRequest(instrument=self._vi, selector_string=selector_string, detector_type_raw=detector_type, detector_points=detector_points),  # type: ignore
        )
        return response.status

    def spectrum_configure_fft(self, selector_string, fft_window, fft_padding):
        """spectrum_configure_fft."""
        response = self._invoke(
            self._client.SpectrumCfgFFT,
            grpc_types.SpectrumCfgFFTRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window, fft_padding=fft_padding),  # type: ignore
        )
        return response.status

    def spectrum_configure_noise_compensation_enabled(
        self, selector_string, noise_compensation_enabled
    ):
        """spectrum_configure_noise_compensation_enabled."""
        response = self._invoke(
            self._client.SpectrumCfgNoiseCompensationEnabled,
            grpc_types.SpectrumCfgNoiseCompensationEnabledRequest(instrument=self._vi, selector_string=selector_string, noise_compensation_enabled_raw=noise_compensation_enabled),  # type: ignore
        )
        return response.status

    def spectrum_configure_power_units(self, selector_string, spectrum_power_units):
        """spectrum_configure_power_units."""
        response = self._invoke(
            self._client.SpectrumCfgPowerUnits,
            grpc_types.SpectrumCfgPowerUnitsRequest(instrument=self._vi, selector_string=selector_string, spectrum_power_units_raw=spectrum_power_units),  # type: ignore
        )
        return response.status

    def spectrum_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """spectrum_configure_rbw_filter."""
        response = self._invoke(
            self._client.SpectrumCfgRBWFilter,
            grpc_types.SpectrumCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def spectrum_configure_span(self, selector_string, span):
        """spectrum_configure_span."""
        response = self._invoke(
            self._client.SpectrumCfgSpan,
            grpc_types.SpectrumCfgSpanRequest(instrument=self._vi, selector_string=selector_string, span=span),  # type: ignore
        )
        return response.status

    def spectrum_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """spectrum_configure_sweep_time."""
        response = self._invoke(
            self._client.SpectrumCfgSweepTime,
            grpc_types.SpectrumCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def spectrum_configure_vbw_filter(self, selector_string, vbw_auto, vbw, vbw_to_rbw_ratio):
        """spectrum_configure_vbw_filter."""
        response = self._invoke(
            self._client.SpectrumCfgVBWFilter,
            grpc_types.SpectrumCfgVBWFilterRequest(instrument=self._vi, selector_string=selector_string, vbw_auto_raw=vbw_auto, vbw=vbw, vbw_to_rbw_ratio=vbw_to_rbw_ratio),  # type: ignore
        )
        return response.status

    def spectrum_configure_measurement_method(self, selector_string, measurement_method):
        """spectrum_configure_measurement_method."""
        response = self._invoke(
            self._client.SpectrumCfgMeasurementMethod,
            grpc_types.SpectrumCfgMeasurementMethodRequest(instrument=self._vi, selector_string=selector_string, measurement_method_raw=measurement_method),  # type: ignore
        )
        return response.status

    def spur_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """spur_configure_averaging."""
        response = self._invoke(
            self._client.SpurCfgAveraging,
            grpc_types.SpurCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def spur_configure_fft_window_type(self, selector_string, fft_window):
        """spur_configure_fft_window_type."""
        response = self._invoke(
            self._client.SpurCfgFFTWindowType,
            grpc_types.SpurCfgFFTWindowTypeRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window),  # type: ignore
        )
        return response.status

    def spur_configure_number_of_ranges(self, selector_string, number_of_ranges):
        """spur_configure_number_of_ranges."""
        response = self._invoke(
            self._client.SpurCfgNumberOfRanges,
            grpc_types.SpurCfgNumberOfRangesRequest(instrument=self._vi, selector_string=selector_string, number_of_ranges=number_of_ranges),  # type: ignore
        )
        return response.status

    def spur_configure_range_absolute_limit_array(
        self, selector_string, absolute_limit_mode, absolute_limit_start, absolute_limit_stop
    ):
        """spur_configure_range_absolute_limit_array."""
        response = self._invoke(
            self._client.SpurCfgRangeAbsoluteLimitArray,
            grpc_types.SpurCfgRangeAbsoluteLimitArrayRequest(instrument=self._vi, selector_string=selector_string, absolute_limit_mode=absolute_limit_mode, absolute_limit_start=absolute_limit_start, absolute_limit_stop=absolute_limit_stop),  # type: ignore
        )
        return response.status

    def spur_configure_range_absolute_limit(
        self, selector_string, absolute_limit_mode, absolute_limit_start, absolute_limit_stop
    ):
        """spur_configure_range_absolute_limit."""
        response = self._invoke(
            self._client.SpurCfgRangeAbsoluteLimit,
            grpc_types.SpurCfgRangeAbsoluteLimitRequest(instrument=self._vi, selector_string=selector_string, absolute_limit_mode_raw=absolute_limit_mode, absolute_limit_start=absolute_limit_start, absolute_limit_stop=absolute_limit_stop),  # type: ignore
        )
        return response.status

    def spur_configure_range_detector_array(self, selector_string, detector_type, detector_points):
        """spur_configure_range_detector_array."""
        response = self._invoke(
            self._client.SpurCfgRangeDetectorArray,
            grpc_types.SpurCfgRangeDetectorArrayRequest(instrument=self._vi, selector_string=selector_string, detector_type=detector_type, detector_points=detector_points),  # type: ignore
        )
        return response.status

    def spur_configure_range_detector(self, selector_string, detector_type, detector_points):
        """spur_configure_range_detector."""
        response = self._invoke(
            self._client.SpurCfgRangeDetector,
            grpc_types.SpurCfgRangeDetectorRequest(instrument=self._vi, selector_string=selector_string, detector_type_raw=detector_type, detector_points=detector_points),  # type: ignore
        )
        return response.status

    def spur_configure_range_frequency_array(
        self, selector_string, start_frequency, stop_frequency, range_enabled
    ):
        """spur_configure_range_frequency_array."""
        response = self._invoke(
            self._client.SpurCfgRangeFrequencyArray,
            grpc_types.SpurCfgRangeFrequencyArrayRequest(instrument=self._vi, selector_string=selector_string, start_frequency=start_frequency, stop_frequency=stop_frequency, range_enabled=range_enabled),  # type: ignore
        )
        return response.status

    def spur_configure_range_frequency(
        self, selector_string, start_frequency, stop_frequency, range_enabled
    ):
        """spur_configure_range_frequency."""
        response = self._invoke(
            self._client.SpurCfgRangeFrequency,
            grpc_types.SpurCfgRangeFrequencyRequest(instrument=self._vi, selector_string=selector_string, start_frequency=start_frequency, stop_frequency=stop_frequency, range_enabled_raw=range_enabled),  # type: ignore
        )
        return response.status

    def spur_configure_range_number_of_spurs_to_report_array(
        self, selector_string, number_of_spurs_to_report
    ):
        """spur_configure_range_number_of_spurs_to_report_array."""
        response = self._invoke(
            self._client.SpurCfgRangeNumberOfSpursToReportArray,
            grpc_types.SpurCfgRangeNumberOfSpursToReportArrayRequest(instrument=self._vi, selector_string=selector_string, number_of_spurs_to_report=number_of_spurs_to_report),  # type: ignore
        )
        return response.status

    def spur_configure_range_number_of_spurs_to_report(
        self, selector_string, number_of_spurs_to_report
    ):
        """spur_configure_range_number_of_spurs_to_report."""
        response = self._invoke(
            self._client.SpurCfgRangeNumberOfSpursToReport,
            grpc_types.SpurCfgRangeNumberOfSpursToReportRequest(instrument=self._vi, selector_string=selector_string, number_of_spurs_to_report=number_of_spurs_to_report),  # type: ignore
        )
        return response.status

    def spur_configure_range_peak_criteria_array(self, selector_string, threshold, excursion):
        """spur_configure_range_peak_criteria_array."""
        response = self._invoke(
            self._client.SpurCfgRangePeakCriteriaArray,
            grpc_types.SpurCfgRangePeakCriteriaArrayRequest(instrument=self._vi, selector_string=selector_string, threshold=threshold, excursion=excursion),  # type: ignore
        )
        return response.status

    def spur_configure_range_peak_criteria(self, selector_string, threshold, excursion):
        """spur_configure_range_peak_criteria."""
        response = self._invoke(
            self._client.SpurCfgRangePeakCriteria,
            grpc_types.SpurCfgRangePeakCriteriaRequest(instrument=self._vi, selector_string=selector_string, threshold=threshold, excursion=excursion),  # type: ignore
        )
        return response.status

    def spur_configure_range_rbw_array(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """spur_configure_range_rbw_array."""
        response = self._invoke(
            self._client.SpurCfgRangeRBWArray,
            grpc_types.SpurCfgRangeRBWArrayRequest(instrument=self._vi, selector_string=selector_string, rbw_auto=rbw_auto, rbw=rbw, rbw_filter_type=rbw_filter_type),  # type: ignore
        )
        return response.status

    def spur_configure_range_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """spur_configure_range_rbw_filter."""
        response = self._invoke(
            self._client.SpurCfgRangeRBWFilter,
            grpc_types.SpurCfgRangeRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def spur_configure_range_relative_attenuation_array(
        self, selector_string, relative_attenuation
    ):
        """spur_configure_range_relative_attenuation_array."""
        response = self._invoke(
            self._client.SpurCfgRangeRelativeAttenuationArray,
            grpc_types.SpurCfgRangeRelativeAttenuationArrayRequest(instrument=self._vi, selector_string=selector_string, relative_attenuation=relative_attenuation),  # type: ignore
        )
        return response.status

    def spur_configure_range_relative_attenuation(self, selector_string, relative_attenuation):
        """spur_configure_range_relative_attenuation."""
        response = self._invoke(
            self._client.SpurCfgRangeRelativeAttenuation,
            grpc_types.SpurCfgRangeRelativeAttenuationRequest(instrument=self._vi, selector_string=selector_string, relative_attenuation=relative_attenuation),  # type: ignore
        )
        return response.status

    def spur_configure_range_sweep_time_array(
        self, selector_string, sweep_time_auto, sweep_time_interval
    ):
        """spur_configure_range_sweep_time_array."""
        response = self._invoke(
            self._client.SpurCfgRangeSweepTimeArray,
            grpc_types.SpurCfgRangeSweepTimeArrayRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def spur_configure_range_sweep_time(
        self, selector_string, sweep_time_auto, sweep_time_interval
    ):
        """spur_configure_range_sweep_time."""
        response = self._invoke(
            self._client.SpurCfgRangeSweepTime,
            grpc_types.SpurCfgRangeSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def spur_configure_range_vbw_filter_array(
        self, selector_string, vbw_auto, vbw, vbw_to_rbw_ratio
    ):
        """spur_configure_range_vbw_filter_array."""
        response = self._invoke(
            self._client.SpurCfgRangeVBWFilterArray,
            grpc_types.SpurCfgRangeVBWFilterArrayRequest(instrument=self._vi, selector_string=selector_string, vbw_auto=vbw_auto, vbw=vbw, vbw_to_rbw_ratio=vbw_to_rbw_ratio),  # type: ignore
        )
        return response.status

    def spur_configure_range_vbw_filter(self, selector_string, vbw_auto, vbw, vbw_to_rbw_ratio):
        """spur_configure_range_vbw_filter."""
        response = self._invoke(
            self._client.SpurCfgRangeVBWFilter,
            grpc_types.SpurCfgRangeVBWFilterRequest(instrument=self._vi, selector_string=selector_string, vbw_auto_raw=vbw_auto, vbw=vbw, vbw_to_rbw_ratio=vbw_to_rbw_ratio),  # type: ignore
        )
        return response.status

    def spur_configure_trace_range_index(self, selector_string, trace_range_index):
        """spur_configure_trace_range_index."""
        response = self._invoke(
            self._client.SpurCfgTraceRangeIndex,
            grpc_types.SpurCfgTraceRangeIndexRequest(instrument=self._vi, selector_string=selector_string, trace_range_index=trace_range_index),  # type: ignore
        )
        return response.status

    def ampm_configure_am_to_am_curve_fit(
        self, selector_string, am_to_am_curve_fit_order, am_to_am_curve_fit_type
    ):
        """ampm_configure_am_to_am_curve_fit."""
        response = self._invoke(
            self._client.AMPMCfgAMToAMCurveFit,
            grpc_types.AMPMCfgAMToAMCurveFitRequest(instrument=self._vi, selector_string=selector_string, am_to_am_curve_fit_order=am_to_am_curve_fit_order, am_to_am_curve_fit_type_raw=am_to_am_curve_fit_type),  # type: ignore
        )
        return response.status

    def ampm_configure_am_to_pm_curve_fit(
        self, selector_string, am_to_pm_curve_fit_order, am_to_pm_curve_fit_type
    ):
        """ampm_configure_am_to_pm_curve_fit."""
        response = self._invoke(
            self._client.AMPMCfgAMToPMCurveFit,
            grpc_types.AMPMCfgAMToPMCurveFitRequest(instrument=self._vi, selector_string=selector_string, am_to_pm_curve_fit_order=am_to_pm_curve_fit_order, am_to_pm_curve_fit_type_raw=am_to_pm_curve_fit_type),  # type: ignore
        )
        return response.status

    def ampm_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """ampm_configure_averaging."""
        response = self._invoke(
            self._client.AMPMCfgAveraging,
            grpc_types.AMPMCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def ampm_configure_compression_points(
        self, selector_string, compression_point_enabled, compression_level
    ):
        """ampm_configure_compression_points."""
        response = self._invoke(
            self._client.AMPMCfgCompressionPoints,
            grpc_types.AMPMCfgCompressionPointsRequest(instrument=self._vi, selector_string=selector_string, compression_point_enabled_raw=compression_point_enabled, compression_level=compression_level),  # type: ignore
        )
        return response.status

    def ampm_configure_dut_average_input_power(self, selector_string, dut_average_input_power):
        """ampm_configure_dut_average_input_power."""
        response = self._invoke(
            self._client.AMPMCfgDUTAverageInputPower,
            grpc_types.AMPMCfgDUTAverageInputPowerRequest(instrument=self._vi, selector_string=selector_string, dut_average_input_power=dut_average_input_power),  # type: ignore
        )
        return response.status

    def ampm_configure_measurement_interval(self, selector_string, measurement_interval):
        """ampm_configure_measurement_interval."""
        response = self._invoke(
            self._client.AMPMCfgMeasurementInterval,
            grpc_types.AMPMCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def ampm_configure_measurement_sample_rate(
        self, selector_string, sample_rate_mode, sample_rate
    ):
        """ampm_configure_measurement_sample_rate."""
        response = self._invoke(
            self._client.AMPMCfgMeasurementSampleRate,
            grpc_types.AMPMCfgMeasurementSampleRateRequest(instrument=self._vi, selector_string=selector_string, sample_rate_mode_raw=sample_rate_mode, sample_rate=sample_rate),  # type: ignore
        )
        return response.status

    def ampm_configure_reference_power_type(self, selector_string, reference_power_type):
        """ampm_configure_reference_power_type."""
        response = self._invoke(
            self._client.AMPMCfgReferencePowerType,
            grpc_types.AMPMCfgReferencePowerTypeRequest(instrument=self._vi, selector_string=selector_string, reference_power_type_raw=reference_power_type),  # type: ignore
        )
        return response.status

    def ampm_configure_synchronization_method(self, selector_string, synchronization_method):
        """ampm_configure_synchronization_method."""
        response = self._invoke(
            self._client.AMPMCfgSynchronizationMethod,
            grpc_types.AMPMCfgSynchronizationMethodRequest(instrument=self._vi, selector_string=selector_string, synchronization_method_raw=synchronization_method),  # type: ignore
        )
        return response.status

    def ampm_configure_threshold(
        self, selector_string, threshold_enabled, threshold_level, threshold_type
    ):
        """ampm_configure_threshold."""
        response = self._invoke(
            self._client.AMPMCfgThreshold,
            grpc_types.AMPMCfgThresholdRequest(instrument=self._vi, selector_string=selector_string, threshold_enabled_raw=threshold_enabled, threshold_level=threshold_level, threshold_type_raw=threshold_type),  # type: ignore
        )
        return response.status

    def dpd_configure_configuration_input(self, selector_string, configuration_input):
        """dpd_configure_configuration_input."""
        response = self._invoke(
            self._client.DPDCfgApplyDPDConfigurationInput,
            grpc_types.DPDCfgApplyDPDConfigurationInputRequest(instrument=self._vi, selector_string=selector_string, configuration_input_raw=configuration_input),  # type: ignore
        )
        return response.status

    def dpd_configure_lookup_table_correction_type(self, selector_string, lut_correction_type):
        """dpd_configure_lookup_table_correction_type."""
        response = self._invoke(
            self._client.DPDCfgApplyDPDLookupTableCorrectionType,
            grpc_types.DPDCfgApplyDPDLookupTableCorrectionTypeRequest(instrument=self._vi, selector_string=selector_string, lut_correction_type_raw=lut_correction_type),  # type: ignore
        )
        return response.status

    def dpd_configure_memory_model_correction_type(
        self, selector_string, memory_model_correction_type
    ):
        """dpd_configure_memory_model_correction_type."""
        response = self._invoke(
            self._client.DPDCfgApplyDPDMemoryModelCorrectionType,
            grpc_types.DPDCfgApplyDPDMemoryModelCorrectionTypeRequest(instrument=self._vi, selector_string=selector_string, memory_model_correction_type_raw=memory_model_correction_type),  # type: ignore
        )
        return response.status

    def dpd_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """dpd_configure_averaging."""
        response = self._invoke(
            self._client.DPDCfgAveraging,
            grpc_types.DPDCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count),  # type: ignore
        )
        return response.status

    def dpd_configure_dpd_model(self, selector_string, dpd_model):
        """dpd_configure_dpd_model."""
        response = self._invoke(
            self._client.DPDCfgDPDModel,
            grpc_types.DPDCfgDPDModelRequest(instrument=self._vi, selector_string=selector_string, dpd_model_raw=dpd_model),  # type: ignore
        )
        return response.status

    def dpd_configure_dut_average_input_power(self, selector_string, dut_average_input_power):
        """dpd_configure_dut_average_input_power."""
        response = self._invoke(
            self._client.DPDCfgDUTAverageInputPower,
            grpc_types.DPDCfgDUTAverageInputPowerRequest(instrument=self._vi, selector_string=selector_string, dut_average_input_power=dut_average_input_power),  # type: ignore
        )
        return response.status

    def dpd_configure_generalized_memory_polynomial_cross_terms(
        self,
        selector_string,
        memory_polynomial_lead_order,
        memory_polynomial_lag_order,
        memory_polynomial_lead_memory_depth,
        memory_polynomial_lag_memory_depth,
        memory_polynomial_maximum_lead,
        memory_polynomial_maximum_lag,
    ):
        """dpd_configure_generalized_memory_polynomial_cross_terms."""
        response = self._invoke(
            self._client.DPDCfgGeneralizedMemoryPolynomialCrossTerms,
            grpc_types.DPDCfgGeneralizedMemoryPolynomialCrossTermsRequest(instrument=self._vi, selector_string=selector_string, memory_polynomial_lead_order=memory_polynomial_lead_order, memory_polynomial_lag_order=memory_polynomial_lag_order, memory_polynomial_lead_memory_depth=memory_polynomial_lead_memory_depth, memory_polynomial_lag_memory_depth=memory_polynomial_lag_memory_depth, memory_polynomial_maximum_lead=memory_polynomial_maximum_lead, memory_polynomial_maximum_lag=memory_polynomial_maximum_lag),  # type: ignore
        )
        return response.status

    def dpd_configure_iterative_dpd_enabled(self, selector_string, iterative_dpd_enabled):
        """dpd_configure_iterative_dpd_enabled."""
        response = self._invoke(
            self._client.DPDCfgIterativeDPDEnabled,
            grpc_types.DPDCfgIterativeDPDEnabledRequest(instrument=self._vi, selector_string=selector_string, iterative_dpd_enabled_raw=iterative_dpd_enabled),  # type: ignore
        )
        return response.status

    def dpd_configure_lookup_table_am_to_am_curve_fit(
        self, selector_string, am_to_am_curve_fit_order, am_to_am_curve_fit_type
    ):
        """dpd_configure_lookup_table_am_to_am_curve_fit."""
        response = self._invoke(
            self._client.DPDCfgLookupTableAMToAMCurveFit,
            grpc_types.DPDCfgLookupTableAMToAMCurveFitRequest(instrument=self._vi, selector_string=selector_string, am_to_am_curve_fit_order=am_to_am_curve_fit_order, am_to_am_curve_fit_type_raw=am_to_am_curve_fit_type),  # type: ignore
        )
        return response.status

    def dpd_configure_lookup_table_am_to_pm_curve_fit(
        self, selector_string, am_to_pm_curve_fit_order, am_to_pm_curve_fit_type
    ):
        """dpd_configure_lookup_table_am_to_pm_curve_fit."""
        response = self._invoke(
            self._client.DPDCfgLookupTableAMToPMCurveFit,
            grpc_types.DPDCfgLookupTableAMToPMCurveFitRequest(instrument=self._vi, selector_string=selector_string, am_to_pm_curve_fit_order=am_to_pm_curve_fit_order, am_to_pm_curve_fit_type_raw=am_to_pm_curve_fit_type),  # type: ignore
        )
        return response.status

    def dpd_configure_lookup_table_step_size(self, selector_string, step_size):
        """dpd_configure_lookup_table_step_size."""
        response = self._invoke(
            self._client.DPDCfgLookupTableStepSize,
            grpc_types.DPDCfgLookupTableStepSizeRequest(instrument=self._vi, selector_string=selector_string, step_size=step_size),  # type: ignore
        )
        return response.status

    def dpd_configure_lookup_table_threshold(
        self, selector_string, threshold_enabled, threshold_level, threshold_type
    ):
        """dpd_configure_lookup_table_threshold."""
        response = self._invoke(
            self._client.DPDCfgLookupTableThreshold,
            grpc_types.DPDCfgLookupTableThresholdRequest(instrument=self._vi, selector_string=selector_string, threshold_enabled_raw=threshold_enabled, threshold_level=threshold_level, threshold_type_raw=threshold_type),  # type: ignore
        )
        return response.status

    def dpd_configure_lookup_table_type(self, selector_string, lookup_table_type):
        """dpd_configure_lookup_table_type."""
        response = self._invoke(
            self._client.DPDCfgLookupTableType,
            grpc_types.DPDCfgLookupTableTypeRequest(instrument=self._vi, selector_string=selector_string, lookup_table_type_raw=lookup_table_type),  # type: ignore
        )
        return response.status

    def dpd_configure_measurement_interval(self, selector_string, measurement_interval):
        """dpd_configure_measurement_interval."""
        response = self._invoke(
            self._client.DPDCfgMeasurementInterval,
            grpc_types.DPDCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def dpd_configure_measurement_sample_rate(self, selector_string, sample_rate_mode, sample_rate):
        """dpd_configure_measurement_sample_rate."""
        response = self._invoke(
            self._client.DPDCfgMeasurementSampleRate,
            grpc_types.DPDCfgMeasurementSampleRateRequest(instrument=self._vi, selector_string=selector_string, sample_rate_mode_raw=sample_rate_mode, sample_rate=sample_rate),  # type: ignore
        )
        return response.status

    def dpd_configure_memory_polynomial(
        self, selector_string, memory_polynomial_order, memory_polynomial_memory_depth
    ):
        """dpd_configure_memory_polynomial."""
        response = self._invoke(
            self._client.DPDCfgMemoryPolynomial,
            grpc_types.DPDCfgMemoryPolynomialRequest(instrument=self._vi, selector_string=selector_string, memory_polynomial_order=memory_polynomial_order, memory_polynomial_memory_depth=memory_polynomial_memory_depth),  # type: ignore
        )
        return response.status

    def dpd_configure_synchronization_method(self, selector_string, synchronization_method):
        """dpd_configure_synchronization_method."""
        response = self._invoke(
            self._client.DPDCfgSynchronizationMethod,
            grpc_types.DPDCfgSynchronizationMethodRequest(instrument=self._vi, selector_string=selector_string, synchronization_method_raw=synchronization_method),  # type: ignore
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

    def acp_configure_carrier_integration_bandwidth(self, selector_string, integration_bandwidth):
        """acp_configure_carrier_integration_bandwidth."""
        response = self._invoke(
            self._client.ACPCfgCarrierIntegrationBandwidth,
            grpc_types.ACPCfgCarrierIntegrationBandwidthRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth=integration_bandwidth),  # type: ignore
        )
        return response.status

    def acp_configure_carrier_mode(self, selector_string, carrier_mode):
        """acp_configure_carrier_mode."""
        response = self._invoke(
            self._client.ACPCfgCarrierMode,
            grpc_types.ACPCfgCarrierModeRequest(instrument=self._vi, selector_string=selector_string, carrier_mode_raw=carrier_mode),  # type: ignore
        )
        return response.status

    def acp_configure_carrier_frequency(self, selector_string, carrier_frequency):
        """acp_configure_carrier_frequency."""
        response = self._invoke(
            self._client.ACPCfgCarrierFrequency,
            grpc_types.ACPCfgCarrierFrequencyRequest(instrument=self._vi, selector_string=selector_string, carrier_frequency=carrier_frequency),  # type: ignore
        )
        return response.status

    def acp_configure_carrier_rrc_filter(self, selector_string, rrc_filter_enabled, rrc_alpha):
        """acp_configure_carrier_rrc_filter."""
        response = self._invoke(
            self._client.ACPCfgCarrierRRCFilter,
            grpc_types.ACPCfgCarrierRRCFilterRequest(instrument=self._vi, selector_string=selector_string, rrc_filter_enabled_raw=rrc_filter_enabled, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def acp_configure_fft(self, selector_string, fft_window, fft_padding):
        """acp_configure_fft."""
        response = self._invoke(
            self._client.ACPCfgFFT,
            grpc_types.ACPCfgFFTRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window, fft_padding=fft_padding),  # type: ignore
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

    def acp_configure_number_of_carriers(self, selector_string, number_of_carriers):
        """acp_configure_number_of_carriers."""
        response = self._invoke(
            self._client.ACPCfgNumberOfCarriers,
            grpc_types.ACPCfgNumberOfCarriersRequest(instrument=self._vi, selector_string=selector_string, number_of_carriers=number_of_carriers),  # type: ignore
        )
        return response.status

    def acp_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """acp_configure_number_of_offsets."""
        response = self._invoke(
            self._client.ACPCfgNumberOfOffsets,
            grpc_types.ACPCfgNumberOfOffsetsRequest(instrument=self._vi, selector_string=selector_string, number_of_offsets=number_of_offsets),  # type: ignore
        )
        return response.status

    def acp_configure_offset_array(
        self, selector_string, offset_frequency, offset_sideband, offset_enabled
    ):
        """acp_configure_offset_array."""
        response = self._invoke(
            self._client.ACPCfgOffsetArray,
            grpc_types.ACPCfgOffsetArrayRequest(instrument=self._vi, selector_string=selector_string, offset_frequency=offset_frequency, offset_sideband=offset_sideband, offset_enabled=offset_enabled),  # type: ignore
        )
        return response.status

    def acp_configure_offset_frequency_definition(
        self, selector_string, offset_frequency_definition
    ):
        """acp_configure_offset_frequency_definition."""
        response = self._invoke(
            self._client.ACPCfgOffsetFrequencyDefinition,
            grpc_types.ACPCfgOffsetFrequencyDefinitionRequest(instrument=self._vi, selector_string=selector_string, offset_frequency_definition_raw=offset_frequency_definition),  # type: ignore
        )
        return response.status

    def acp_configure_offset_integration_bandwidth_array(
        self, selector_string, integration_bandwidth
    ):
        """acp_configure_offset_integration_bandwidth_array."""
        response = self._invoke(
            self._client.ACPCfgOffsetIntegrationBandwidthArray,
            grpc_types.ACPCfgOffsetIntegrationBandwidthArrayRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth=integration_bandwidth),  # type: ignore
        )
        return response.status

    def acp_configure_offset_integration_bandwidth(self, selector_string, integration_bandwidth):
        """acp_configure_offset_integration_bandwidth."""
        response = self._invoke(
            self._client.ACPCfgOffsetIntegrationBandwidth,
            grpc_types.ACPCfgOffsetIntegrationBandwidthRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth=integration_bandwidth),  # type: ignore
        )
        return response.status

    def acp_configure_offset_power_reference_array(
        self, selector_string, offset_power_reference_carrier, offset_power_reference_specific
    ):
        """acp_configure_offset_power_reference_array."""
        response = self._invoke(
            self._client.ACPCfgOffsetPowerReferenceArray,
            grpc_types.ACPCfgOffsetPowerReferenceArrayRequest(instrument=self._vi, selector_string=selector_string, offset_power_reference_carrier=offset_power_reference_carrier, offset_power_reference_specific=offset_power_reference_specific),  # type: ignore
        )
        return response.status

    def acp_configure_offset_power_reference(
        self, selector_string, offset_reference_carrier, offset_reference_specific
    ):
        """acp_configure_offset_power_reference."""
        response = self._invoke(
            self._client.ACPCfgOffsetPowerReference,
            grpc_types.ACPCfgOffsetPowerReferenceRequest(instrument=self._vi, selector_string=selector_string, offset_reference_carrier_raw=offset_reference_carrier, offset_reference_specific=offset_reference_specific),  # type: ignore
        )
        return response.status

    def acp_configure_offset_relative_attenuation_array(
        self, selector_string, relative_attenuation
    ):
        """acp_configure_offset_relative_attenuation_array."""
        response = self._invoke(
            self._client.ACPCfgOffsetRelativeAttenuationArray,
            grpc_types.ACPCfgOffsetRelativeAttenuationArrayRequest(instrument=self._vi, selector_string=selector_string, relative_attenuation=relative_attenuation),  # type: ignore
        )
        return response.status

    def acp_configure_offset_relative_attenuation(self, selector_string, relative_attenuation):
        """acp_configure_offset_relative_attenuation."""
        response = self._invoke(
            self._client.ACPCfgOffsetRelativeAttenuation,
            grpc_types.ACPCfgOffsetRelativeAttenuationRequest(instrument=self._vi, selector_string=selector_string, relative_attenuation=relative_attenuation),  # type: ignore
        )
        return response.status

    def acp_configure_offset_rrc_filter_array(self, selector_string, rrc_filter_enabled, rrc_alpha):
        """acp_configure_offset_rrc_filter_array."""
        response = self._invoke(
            self._client.ACPCfgOffsetRRCFilterArray,
            grpc_types.ACPCfgOffsetRRCFilterArrayRequest(instrument=self._vi, selector_string=selector_string, rrc_filter_enabled=rrc_filter_enabled, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def acp_configure_offset_rrc_filter(self, selector_string, rrc_filter_enabled, rrc_alpha):
        """acp_configure_offset_rrc_filter."""
        response = self._invoke(
            self._client.ACPCfgOffsetRRCFilter,
            grpc_types.ACPCfgOffsetRRCFilterRequest(instrument=self._vi, selector_string=selector_string, rrc_filter_enabled_raw=rrc_filter_enabled, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def acp_configure_offset(
        self, selector_string, offset_frequency, offset_sideband, offset_enabled
    ):
        """acp_configure_offset."""
        response = self._invoke(
            self._client.ACPCfgOffset,
            grpc_types.ACPCfgOffsetRequest(instrument=self._vi, selector_string=selector_string, offset_frequency=offset_frequency, offset_sideband_raw=offset_sideband, offset_enabled_raw=offset_enabled),  # type: ignore
        )
        return response.status

    def acp_configure_power_units(self, selector_string, power_units):
        """acp_configure_power_units."""
        response = self._invoke(
            self._client.ACPCfgPowerUnits,
            grpc_types.ACPCfgPowerUnitsRequest(instrument=self._vi, selector_string=selector_string, power_units_raw=power_units),  # type: ignore
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

    def acp_configure_detector(self, selector_string, detector_type, detector_points):
        """acp_configure_detector."""
        response = self._invoke(
            self._client.ACPCfgDetector,
            grpc_types.ACPCfgDetectorRequest(instrument=self._vi, selector_string=selector_string, detector_type_raw=detector_type, detector_points=detector_points),  # type: ignore
        )
        return response.status

    def ccdf_configure_measurement_interval(self, selector_string, measurement_interval):
        """ccdf_configure_measurement_interval."""
        response = self._invoke(
            self._client.CCDFCfgMeasurementInterval,
            grpc_types.CCDFCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def ccdf_configure_number_of_records(self, selector_string, number_of_records):
        """ccdf_configure_number_of_records."""
        response = self._invoke(
            self._client.CCDFCfgNumberOfRecords,
            grpc_types.CCDFCfgNumberOfRecordsRequest(instrument=self._vi, selector_string=selector_string, number_of_records=number_of_records),  # type: ignore
        )
        return response.status

    def ccdf_configure_rbw_filter(self, selector_string, rbw, rbw_filter_type, rrc_alpha):
        """ccdf_configure_rbw_filter."""
        response = self._invoke(
            self._client.CCDFCfgRBWFilter,
            grpc_types.CCDFCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw=rbw, rbw_filter_type_raw=rbw_filter_type, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def ccdf_configure_threshold(
        self, selector_string, threshold_enabled, threshold_level, threshold_type
    ):
        """ccdf_configure_threshold."""
        response = self._invoke(
            self._client.CCDFCfgThreshold,
            grpc_types.CCDFCfgThresholdRequest(instrument=self._vi, selector_string=selector_string, threshold_enabled_raw=threshold_enabled, threshold_level=threshold_level, threshold_type_raw=threshold_type),  # type: ignore
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

    def chp_configure_carrier_offset(self, selector_string, carrier_frequency):
        """chp_configure_carrier_offset."""
        response = self._invoke(
            self._client.CHPCfgCarrierOffset,
            grpc_types.CHPCfgCarrierOffsetRequest(instrument=self._vi, selector_string=selector_string, carrier_frequency=carrier_frequency),  # type: ignore
        )
        return response.status

    def chp_configure_fft(self, selector_string, fft_window, fft_padding):
        """chp_configure_fft."""
        response = self._invoke(
            self._client.CHPCfgFFT,
            grpc_types.CHPCfgFFTRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window, fft_padding=fft_padding),  # type: ignore
        )
        return response.status

    def chp_configure_integration_bandwidth(self, selector_string, integration_bandwidth):
        """chp_configure_integration_bandwidth."""
        response = self._invoke(
            self._client.CHPCfgIntegrationBandwidth,
            grpc_types.CHPCfgIntegrationBandwidthRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth=integration_bandwidth),  # type: ignore
        )
        return response.status

    def chp_configure_number_of_carriers(self, selector_string, number_of_carriers):
        """chp_configure_number_of_carriers."""
        response = self._invoke(
            self._client.CHPCfgNumberOfCarriers,
            grpc_types.CHPCfgNumberOfCarriersRequest(instrument=self._vi, selector_string=selector_string, number_of_carriers=number_of_carriers),  # type: ignore
        )
        return response.status

    def chp_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """chp_configure_rbw_filter."""
        response = self._invoke(
            self._client.CHPCfgRBWFilter,
            grpc_types.CHPCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def chp_configure_rrc_filter(self, selector_string, rrc_filter_enabled, rrc_alpha):
        """chp_configure_rrc_filter."""
        response = self._invoke(
            self._client.CHPCfgRRCFilter,
            grpc_types.CHPCfgRRCFilterRequest(instrument=self._vi, selector_string=selector_string, rrc_filter_enabled_raw=rrc_filter_enabled, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def chp_configure_span(self, selector_string, span):
        """chp_configure_span."""
        response = self._invoke(
            self._client.CHPCfgSpan,
            grpc_types.CHPCfgSpanRequest(instrument=self._vi, selector_string=selector_string, span=span),  # type: ignore
        )
        return response.status

    def chp_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """chp_configure_sweep_time."""
        response = self._invoke(
            self._client.CHPCfgSweepTime,
            grpc_types.CHPCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def chp_configure_detector(self, selector_string, detector_type, detector_points):
        """chp_configure_detector."""
        response = self._invoke(
            self._client.CHPCfgDetector,
            grpc_types.CHPCfgDetectorRequest(instrument=self._vi, selector_string=selector_string, detector_type_raw=detector_type, detector_points=detector_points),  # type: ignore
        )
        return response.status

    def harm_configure_auto_harmonics(self, selector_string, auto_harmonics_setup_enabled):
        """harm_configure_auto_harmonics."""
        response = self._invoke(
            self._client.HarmCfgAutoHarmonics,
            grpc_types.HarmCfgAutoHarmonicsRequest(instrument=self._vi, selector_string=selector_string, auto_harmonics_setup_enabled_raw=auto_harmonics_setup_enabled),  # type: ignore
        )
        return response.status

    def harm_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """harm_configure_averaging."""
        response = self._invoke(
            self._client.HarmCfgAveraging,
            grpc_types.HarmCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def harm_configure_fundamental_measurement_interval(
        self, selector_string, measurement_interval
    ):
        """harm_configure_fundamental_measurement_interval."""
        response = self._invoke(
            self._client.HarmCfgFundamentalMeasurementInterval,
            grpc_types.HarmCfgFundamentalMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def harm_configure_fundamental_rbw(self, selector_string, rbw, rbw_filter_type, rrc_alpha):
        """harm_configure_fundamental_rbw."""
        response = self._invoke(
            self._client.HarmCfgFundamentalRBW,
            grpc_types.HarmCfgFundamentalRBWRequest(instrument=self._vi, selector_string=selector_string, rbw=rbw, rbw_filter_type_raw=rbw_filter_type, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def harm_configure_harmonic_array(
        self,
        selector_string,
        harmonic_order,
        harmonic_bandwidth,
        harmonic_enabled,
        harmonic_measurement_interval,
    ):
        """harm_configure_harmonic_array."""
        response = self._invoke(
            self._client.HarmCfgHarmonicArray,
            grpc_types.HarmCfgHarmonicArrayRequest(instrument=self._vi, selector_string=selector_string, harmonic_order=harmonic_order, harmonic_bandwidth=harmonic_bandwidth, harmonic_enabled=harmonic_enabled, harmonic_measurement_interval=harmonic_measurement_interval),  # type: ignore
        )
        return response.status

    def harm_configure_harmonic(
        self,
        selector_string,
        harmonic_order,
        harmonic_bandwidth,
        harmonic_enabled,
        harmonic_measurement_interval,
    ):
        """harm_configure_harmonic."""
        response = self._invoke(
            self._client.HarmCfgHarmonic,
            grpc_types.HarmCfgHarmonicRequest(instrument=self._vi, selector_string=selector_string, harmonic_order=harmonic_order, harmonic_bandwidth=harmonic_bandwidth, harmonic_enabled_raw=harmonic_enabled, harmonic_measurement_interval=harmonic_measurement_interval),  # type: ignore
        )
        return response.status

    def harm_configure_number_of_harmonics(self, selector_string, number_of_harmonics):
        """harm_configure_number_of_harmonics."""
        response = self._invoke(
            self._client.HarmCfgNumberOfHarmonics,
            grpc_types.HarmCfgNumberOfHarmonicsRequest(instrument=self._vi, selector_string=selector_string, number_of_harmonics=number_of_harmonics),  # type: ignore
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

    def sem_configure_carrier_channel_bandwidth(self, selector_string, carrier_channel_bandwidth):
        """sem_configure_carrier_channel_bandwidth."""
        response = self._invoke(
            self._client.SEMCfgCarrierChannelBandwidth,
            grpc_types.SEMCfgCarrierChannelBandwidthRequest(instrument=self._vi, selector_string=selector_string, carrier_channel_bandwidth=carrier_channel_bandwidth),  # type: ignore
        )
        return response.status

    def sem_configure_carrier_enabled(self, selector_string, carrier_enabled):
        """sem_configure_carrier_enabled."""
        response = self._invoke(
            self._client.SEMCfgCarrierEnabled,
            grpc_types.SEMCfgCarrierEnabledRequest(instrument=self._vi, selector_string=selector_string, carrier_enabled_raw=carrier_enabled),  # type: ignore
        )
        return response.status

    def sem_configure_carrier_integration_bandwidth(self, selector_string, integration_bandwidth):
        """sem_configure_carrier_integration_bandwidth."""
        response = self._invoke(
            self._client.SEMCfgCarrierIntegrationBandwidth,
            grpc_types.SEMCfgCarrierIntegrationBandwidthRequest(instrument=self._vi, selector_string=selector_string, integration_bandwidth=integration_bandwidth),  # type: ignore
        )
        return response.status

    def sem_configure_carrier_frequency(self, selector_string, carrier_frequency):
        """sem_configure_carrier_frequency."""
        response = self._invoke(
            self._client.SEMCfgCarrierFrequency,
            grpc_types.SEMCfgCarrierFrequencyRequest(instrument=self._vi, selector_string=selector_string, carrier_frequency=carrier_frequency),  # type: ignore
        )
        return response.status

    def sem_configure_carrier_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """sem_configure_carrier_rbw_filter."""
        response = self._invoke(
            self._client.SEMCfgCarrierRBWFilter,
            grpc_types.SEMCfgCarrierRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def sem_configure_carrier_rrc_filter(self, selector_string, rrc_filter_enabled, rrc_alpha):
        """sem_configure_carrier_rrc_filter."""
        response = self._invoke(
            self._client.SEMCfgCarrierRRCFilter,
            grpc_types.SEMCfgCarrierRRCFilterRequest(instrument=self._vi, selector_string=selector_string, rrc_filter_enabled_raw=rrc_filter_enabled, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def sem_configure_fft(self, selector_string, fft_window, fft_padding):
        """sem_configure_fft."""
        response = self._invoke(
            self._client.SEMCfgFFT,
            grpc_types.SEMCfgFFTRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window, fft_padding=fft_padding),  # type: ignore
        )
        return response.status

    def sem_configure_number_of_carriers(self, selector_string, number_of_carriers):
        """sem_configure_number_of_carriers."""
        response = self._invoke(
            self._client.SEMCfgNumberOfCarriers,
            grpc_types.SEMCfgNumberOfCarriersRequest(instrument=self._vi, selector_string=selector_string, number_of_carriers=number_of_carriers),  # type: ignore
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
        self, selector_string, absolute_limit_mode, absolute_limit_start, absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetAbsoluteLimitArray,
            grpc_types.SEMCfgOffsetAbsoluteLimitArrayRequest(instrument=self._vi, selector_string=selector_string, absolute_limit_mode=absolute_limit_mode, absolute_limit_start=absolute_limit_start, absolute_limit_stop=absolute_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_absolute_limit(
        self, selector_string, absolute_limit_mode, absolute_limit_start, absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit."""
        response = self._invoke(
            self._client.SEMCfgOffsetAbsoluteLimit,
            grpc_types.SEMCfgOffsetAbsoluteLimitRequest(instrument=self._vi, selector_string=selector_string, absolute_limit_mode_raw=absolute_limit_mode, absolute_limit_start=absolute_limit_start, absolute_limit_stop=absolute_limit_stop),  # type: ignore
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
        self,
        selector_string,
        offset_start_frequency,
        offset_stop_frequency,
        offset_enabled,
        offset_sideband,
    ):
        """sem_configure_offset_frequency_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetFrequencyArray,
            grpc_types.SEMCfgOffsetFrequencyArrayRequest(instrument=self._vi, selector_string=selector_string, offset_start_frequency=offset_start_frequency, offset_stop_frequency=offset_stop_frequency, offset_enabled=offset_enabled, offset_sideband=offset_sideband),  # type: ignore
        )
        return response.status

    def sem_configure_offset_frequency_definition(
        self, selector_string, offset_frequency_definition
    ):
        """sem_configure_offset_frequency_definition."""
        response = self._invoke(
            self._client.SEMCfgOffsetFrequencyDefinition,
            grpc_types.SEMCfgOffsetFrequencyDefinitionRequest(instrument=self._vi, selector_string=selector_string, offset_frequency_definition_raw=offset_frequency_definition),  # type: ignore
        )
        return response.status

    def sem_configure_offset_frequency(
        self,
        selector_string,
        offset_start_frequency,
        offset_stop_frequency,
        offset_enabled,
        offset_sideband,
    ):
        """sem_configure_offset_frequency."""
        response = self._invoke(
            self._client.SEMCfgOffsetFrequency,
            grpc_types.SEMCfgOffsetFrequencyRequest(instrument=self._vi, selector_string=selector_string, offset_start_frequency=offset_start_frequency, offset_stop_frequency=offset_stop_frequency, offset_enabled_raw=offset_enabled, offset_sideband_raw=offset_sideband),  # type: ignore
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
        self, selector_string, rbw_auto, rbw, rbw_filter_type
    ):
        """sem_configure_offset_rbw_filter_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetRBWFilterArray,
            grpc_types.SEMCfgOffsetRBWFilterArrayRequest(instrument=self._vi, selector_string=selector_string, rbw_auto=rbw_auto, rbw=rbw, rbw_filter_type=rbw_filter_type),  # type: ignore
        )
        return response.status

    def sem_configure_offset_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """sem_configure_offset_rbw_filter."""
        response = self._invoke(
            self._client.SEMCfgOffsetRBWFilter,
            grpc_types.SEMCfgOffsetRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def sem_configure_offset_relative_attenuation_array(
        self, selector_string, relative_attenuation
    ):
        """sem_configure_offset_relative_attenuation_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeAttenuationArray,
            grpc_types.SEMCfgOffsetRelativeAttenuationArrayRequest(instrument=self._vi, selector_string=selector_string, relative_attenuation=relative_attenuation),  # type: ignore
        )
        return response.status

    def sem_configure_offset_relative_attenuation(self, selector_string, relative_attenuation):
        """sem_configure_offset_relative_attenuation."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeAttenuation,
            grpc_types.SEMCfgOffsetRelativeAttenuationRequest(instrument=self._vi, selector_string=selector_string, relative_attenuation=relative_attenuation),  # type: ignore
        )
        return response.status

    def sem_configure_offset_relative_limit_array(
        self, selector_string, relative_limit_mode, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit_array."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeLimitArray,
            grpc_types.SEMCfgOffsetRelativeLimitArrayRequest(instrument=self._vi, selector_string=selector_string, relative_limit_mode=relative_limit_mode, relative_limit_start=relative_limit_start, relative_limit_stop=relative_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_offset_relative_limit(
        self, selector_string, relative_limit_mode, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit."""
        response = self._invoke(
            self._client.SEMCfgOffsetRelativeLimit,
            grpc_types.SEMCfgOffsetRelativeLimitRequest(instrument=self._vi, selector_string=selector_string, relative_limit_mode_raw=relative_limit_mode, relative_limit_start=relative_limit_start, relative_limit_stop=relative_limit_stop),  # type: ignore
        )
        return response.status

    def sem_configure_power_units(self, selector_string, power_units):
        """sem_configure_power_units."""
        response = self._invoke(
            self._client.SEMCfgPowerUnits,
            grpc_types.SEMCfgPowerUnitsRequest(instrument=self._vi, selector_string=selector_string, power_units_raw=power_units),  # type: ignore
        )
        return response.status

    def sem_configure_reference_type(self, selector_string, reference_type):
        """sem_configure_reference_type."""
        response = self._invoke(
            self._client.SEMCfgReferenceType,
            grpc_types.SEMCfgReferenceTypeRequest(instrument=self._vi, selector_string=selector_string, reference_type_raw=reference_type),  # type: ignore
        )
        return response.status

    def sem_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """sem_configure_sweep_time."""
        response = self._invoke(
            self._client.SEMCfgSweepTime,
            grpc_types.SEMCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
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

    def obw_configure_bandwidth_percentage(self, selector_string, bandwidth_percentage):
        """obw_configure_bandwidth_percentage."""
        response = self._invoke(
            self._client.OBWCfgBandwidthPercentage,
            grpc_types.OBWCfgBandwidthPercentageRequest(instrument=self._vi, selector_string=selector_string, bandwidth_percentage=bandwidth_percentage),  # type: ignore
        )
        return response.status

    def obw_configure_fft(self, selector_string, fft_window, fft_padding):
        """obw_configure_fft."""
        response = self._invoke(
            self._client.OBWCfgFFT,
            grpc_types.OBWCfgFFTRequest(instrument=self._vi, selector_string=selector_string, fft_window_raw=fft_window, fft_padding=fft_padding),  # type: ignore
        )
        return response.status

    def obw_configure_power_units(self, selector_string, power_units):
        """obw_configure_power_units."""
        response = self._invoke(
            self._client.OBWCfgPowerUnits,
            grpc_types.OBWCfgPowerUnitsRequest(instrument=self._vi, selector_string=selector_string, power_units_raw=power_units),  # type: ignore
        )
        return response.status

    def obw_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """obw_configure_rbw_filter."""
        response = self._invoke(
            self._client.OBWCfgRBWFilter,
            grpc_types.OBWCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw_auto_raw=rbw_auto, rbw=rbw, rbw_filter_type_raw=rbw_filter_type),  # type: ignore
        )
        return response.status

    def obw_configure_span(self, selector_string, span):
        """obw_configure_span."""
        response = self._invoke(
            self._client.OBWCfgSpan,
            grpc_types.OBWCfgSpanRequest(instrument=self._vi, selector_string=selector_string, span=span),  # type: ignore
        )
        return response.status

    def obw_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """obw_configure_sweep_time."""
        response = self._invoke(
            self._client.OBWCfgSweepTime,
            grpc_types.OBWCfgSweepTimeRequest(instrument=self._vi, selector_string=selector_string, sweep_time_auto_raw=sweep_time_auto, sweep_time_interval=sweep_time_interval),  # type: ignore
        )
        return response.status

    def txp_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """txp_configure_averaging."""
        response = self._invoke(
            self._client.TXPCfgAveraging,
            grpc_types.TXPCfgAveragingRequest(instrument=self._vi, selector_string=selector_string, averaging_enabled_raw=averaging_enabled, averaging_count=averaging_count, averaging_type_raw=averaging_type),  # type: ignore
        )
        return response.status

    def txp_configure_measurement_interval(self, selector_string, measurement_interval):
        """txp_configure_measurement_interval."""
        response = self._invoke(
            self._client.TXPCfgMeasurementInterval,
            grpc_types.TXPCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_interval=measurement_interval),  # type: ignore
        )
        return response.status

    def txp_configure_rbw_filter(self, selector_string, rbw, rbw_filter_type, rrc_alpha):
        """txp_configure_rbw_filter."""
        response = self._invoke(
            self._client.TXPCfgRBWFilter,
            grpc_types.TXPCfgRBWFilterRequest(instrument=self._vi, selector_string=selector_string, rbw=rbw, rbw_filter_type_raw=rbw_filter_type, rrc_alpha=rrc_alpha),  # type: ignore
        )
        return response.status

    def txp_configure_threshold(
        self, selector_string, threshold_enabled, threshold_level, threshold_type
    ):
        """txp_configure_threshold."""
        response = self._invoke(
            self._client.TXPCfgThreshold,
            grpc_types.TXPCfgThresholdRequest(instrument=self._vi, selector_string=selector_string, threshold_enabled_raw=threshold_enabled, threshold_level=threshold_level, threshold_type_raw=threshold_type),  # type: ignore
        )
        return response.status

    def txp_configure_vbw_filter(self, selector_string, vbw_auto, vbw, vbw_to_rbw_ratio):
        """txp_configure_vbw_filter."""
        response = self._invoke(
            self._client.TXPCfgVBWFilter,
            grpc_types.TXPCfgVBWFilterRequest(instrument=self._vi, selector_string=selector_string, vbw_auto_raw=vbw_auto, vbw=vbw, vbw_to_rbw_ratio=vbw_to_rbw_ratio),  # type: ignore
        )
        return response.status

    def iq_configure_acquisition(
        self, selector_string, sample_rate, number_of_records, acquisition_time, pretrigger_time
    ):
        """iq_configure_acquisition."""
        response = self._invoke(
            self._client.IQCfgAcquisition,
            grpc_types.IQCfgAcquisitionRequest(instrument=self._vi, selector_string=selector_string, sample_rate=sample_rate, number_of_records=number_of_records, acquisition_time=acquisition_time, pretrigger_time=pretrigger_time),  # type: ignore
        )
        return response.status

    def iq_configure_bandwidth(self, selector_string, bandwidth_auto, bandwidth):
        """iq_configure_bandwidth."""
        response = self._invoke(
            self._client.IQCfgBandwidth,
            grpc_types.IQCfgBandwidthRequest(instrument=self._vi, selector_string=selector_string, bandwidth_auto_raw=bandwidth_auto, bandwidth=bandwidth),  # type: ignore
        )
        return response.status

    def phase_noise_configure_auto_range(
        self, selector_string, start_frequency, stop_frequency, rbw_percentage
    ):
        """phase_noise_configure_auto_range."""
        response = self._invoke(
            self._client.PhaseNoiseCfgAutoRange,
            grpc_types.PhaseNoiseCfgAutoRangeRequest(instrument=self._vi, selector_string=selector_string, start_frequency=start_frequency, stop_frequency=stop_frequency, rbw_percentage=rbw_percentage),  # type: ignore
        )
        return response.status

    def phase_noise_configure_averaging_multiplier(self, selector_string, averaging_multiplier):
        """phase_noise_configure_averaging_multiplier."""
        response = self._invoke(
            self._client.PhaseNoiseCfgAveragingMultiplier,
            grpc_types.PhaseNoiseCfgAveragingMultiplierRequest(instrument=self._vi, selector_string=selector_string, averaging_multiplier=averaging_multiplier),  # type: ignore
        )
        return response.status

    def phase_noise_configure_cancellation(
        self,
        selector_string,
        cancellation_enabled,
        cancellation_threshold,
        frequency,
        reference_phase_noise,
    ):
        """phase_noise_configure_cancellation."""
        response = self._invoke(
            self._client.PhaseNoiseCfgCancellation,
            grpc_types.PhaseNoiseCfgCancellationRequest(instrument=self._vi, selector_string=selector_string, cancellation_enabled_raw=cancellation_enabled, cancellation_threshold=cancellation_threshold, frequency=frequency, reference_phase_noise=reference_phase_noise),  # type: ignore
        )
        return response.status

    def phase_noise_configure_integrated_noise(
        self,
        selector_string,
        integrated_noise_range_definition,
        integrated_noise_start_frequency,
        integrated_noise_stop_frequency,
    ):
        """phase_noise_configure_integrated_noise."""
        response = self._invoke(
            self._client.PhaseNoiseCfgIntegratedNoise,
            grpc_types.PhaseNoiseCfgIntegratedNoiseRequest(instrument=self._vi, selector_string=selector_string, integrated_noise_range_definition_raw=integrated_noise_range_definition, integrated_noise_start_frequency=integrated_noise_start_frequency, integrated_noise_stop_frequency=integrated_noise_stop_frequency),  # type: ignore
        )
        return response.status

    def phase_noise_configure_number_of_ranges(self, selector_string, number_of_ranges):
        """phase_noise_configure_number_of_ranges."""
        response = self._invoke(
            self._client.PhaseNoiseCfgNumberOfRanges,
            grpc_types.PhaseNoiseCfgNumberOfRangesRequest(instrument=self._vi, selector_string=selector_string, number_of_ranges=number_of_ranges),  # type: ignore
        )
        return response.status

    def phase_noise_configure_range_array(
        self,
        selector_string,
        range_start_frequency,
        range_stop_frequency,
        range_rbw_percentage,
        range_averaging_count,
    ):
        """phase_noise_configure_range_array."""
        response = self._invoke(
            self._client.PhaseNoiseCfgRangeArray,
            grpc_types.PhaseNoiseCfgRangeArrayRequest(instrument=self._vi, selector_string=selector_string, range_start_frequency=range_start_frequency, range_stop_frequency=range_stop_frequency, range_rbw_percentage=range_rbw_percentage, range_averaging_count=range_averaging_count),  # type: ignore
        )
        return response.status

    def phase_noise_configure_range_definition(self, selector_string, range_definition):
        """phase_noise_configure_range_definition."""
        response = self._invoke(
            self._client.PhaseNoiseCfgRangeDefinition,
            grpc_types.PhaseNoiseCfgRangeDefinitionRequest(instrument=self._vi, selector_string=selector_string, range_definition_raw=range_definition),  # type: ignore
        )
        return response.status

    def phase_noise_configure_smoothing(
        self, selector_string, smoothing_type, smoothing_percentage
    ):
        """phase_noise_configure_smoothing."""
        response = self._invoke(
            self._client.PhaseNoiseCfgSmoothing,
            grpc_types.PhaseNoiseCfgSmoothingRequest(instrument=self._vi, selector_string=selector_string, smoothing_type_raw=smoothing_type, smoothing_percentage=smoothing_percentage),  # type: ignore
        )
        return response.status

    def phase_noise_configure_spot_noise_frequency_list(self, selector_string, frequency_list):
        """phase_noise_configure_spot_noise_frequency_list."""
        response = self._invoke(
            self._client.PhaseNoiseCfgSpotNoiseFrequencyList,
            grpc_types.PhaseNoiseCfgSpotNoiseFrequencyListRequest(instrument=self._vi, selector_string=selector_string, frequency_list=frequency_list),  # type: ignore
        )
        return response.status

    def phase_noise_configure_spur_removal(
        self, selector_string, spur_removal_enabled, peak_excursion
    ):
        """phase_noise_configure_spur_removal."""
        response = self._invoke(
            self._client.PhaseNoiseCfgSpurRemoval,
            grpc_types.PhaseNoiseCfgSpurRemovalRequest(instrument=self._vi, selector_string=selector_string, spur_removal_enabled_raw=spur_removal_enabled, peak_excursion=peak_excursion),  # type: ignore
        )
        return response.status

    def pavt_configure_measurement_bandwidth(self, selector_string, measurement_bandwidth):
        """pavt_configure_measurement_bandwidth."""
        response = self._invoke(
            self._client.PAVTCfgMeasurementBandwidth,
            grpc_types.PAVTCfgMeasurementBandwidthRequest(instrument=self._vi, selector_string=selector_string, measurement_bandwidth=measurement_bandwidth),  # type: ignore
        )
        return response.status

    def pavt_configure_measurement_interval_mode(self, selector_string, measurement_interval_mode):
        """pavt_configure_measurement_interval_mode."""
        response = self._invoke(
            self._client.PAVTCfgMeasurementIntervalMode,
            grpc_types.PAVTCfgMeasurementIntervalModeRequest(instrument=self._vi, selector_string=selector_string, measurement_interval_mode_raw=measurement_interval_mode),  # type: ignore
        )
        return response.status

    def pavt_configure_measurement_interval(
        self, selector_string, measurement_offset, measurement_length
    ):
        """pavt_configure_measurement_interval."""
        response = self._invoke(
            self._client.PAVTCfgMeasurementInterval,
            grpc_types.PAVTCfgMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, measurement_offset=measurement_offset, measurement_length=measurement_length),  # type: ignore
        )
        return response.status

    def pavt_configure_measurement_location_type(self, selector_string, measurement_location_type):
        """pavt_configure_measurement_location_type."""
        response = self._invoke(
            self._client.PAVTCfgMeasurementLocationType,
            grpc_types.PAVTCfgMeasurementLocationTypeRequest(instrument=self._vi, selector_string=selector_string, measurement_location_type_raw=measurement_location_type),  # type: ignore
        )
        return response.status

    def pavt_configure_number_of_segments(self, selector_string, number_of_segments):
        """pavt_configure_number_of_segments."""
        response = self._invoke(
            self._client.PAVTCfgNumberOfSegments,
            grpc_types.PAVTCfgNumberOfSegmentsRequest(instrument=self._vi, selector_string=selector_string, number_of_segments=number_of_segments),  # type: ignore
        )
        return response.status

    def pavt_configure_segment_measurement_interval_array(
        self, selector_string, segment_measurement_offset, segment_measurement_length
    ):
        """pavt_configure_segment_measurement_interval_array."""
        response = self._invoke(
            self._client.PAVTCfgSegmentMeasurementIntervalArray,
            grpc_types.PAVTCfgSegmentMeasurementIntervalArrayRequest(instrument=self._vi, selector_string=selector_string, segment_measurement_offset=segment_measurement_offset, segment_measurement_length=segment_measurement_length),  # type: ignore
        )
        return response.status

    def pavt_configure_segment_measurement_interval(
        self, selector_string, segment_measurement_offset, segment_measurement_length
    ):
        """pavt_configure_segment_measurement_interval."""
        response = self._invoke(
            self._client.PAVTCfgSegmentMeasurementInterval,
            grpc_types.PAVTCfgSegmentMeasurementIntervalRequest(instrument=self._vi, selector_string=selector_string, segment_measurement_offset=segment_measurement_offset, segment_measurement_length=segment_measurement_length),  # type: ignore
        )
        return response.status

    def pavt_configure_segment_start_time_list(self, selector_string, segment_start_time):
        """pavt_configure_segment_start_time_list."""
        response = self._invoke(
            self._client.PAVTCfgSegmentStartTimeList,
            grpc_types.PAVTCfgSegmentStartTimeListRequest(instrument=self._vi, selector_string=selector_string, segment_start_time=segment_start_time),  # type: ignore
        )
        return response.status

    def pavt_configure_segment_type_array(self, selector_string, segment_type):
        """pavt_configure_segment_type_array."""
        response = self._invoke(
            self._client.PAVTCfgSegmentTypeArray,
            grpc_types.PAVTCfgSegmentTypeArrayRequest(instrument=self._vi, selector_string=selector_string, segment_type=segment_type),  # type: ignore
        )
        return response.status

    def pavt_configure_segment_type(self, selector_string, segment_type):
        """pavt_configure_segment_type."""
        response = self._invoke(
            self._client.PAVTCfgSegmentType,
            grpc_types.PAVTCfgSegmentTypeRequest(instrument=self._vi, selector_string=selector_string, segment_type_raw=segment_type),  # type: ignore
        )
        return response.status

    def power_list_configure_rbw_filter_array(
        self, selector_string, rbw, rbw_filter_type, rrc_alpha
    ):
        """power_list_configure_rbw_filter_array."""
        response = self._invoke(
            self._client.PowerListCfgRBWFilterArray,
            grpc_types.PowerListCfgRBWFilterArrayRequest(instrument=self._vi, selector_string=selector_string, rbw=rbw, rbw_filter_type=rbw_filter_type, rrc_alpha=rrc_alpha),  # type: ignore
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

    def im_fetch_fundamental_measurement(self, selector_string, timeout):
        """im_fetch_fundamental_measurement."""
        response = self._invoke(
            self._client.IMFetchFundamentalMeasurement,
            grpc_types.IMFetchFundamentalMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.lower_tone_power, response.upper_tone_power, response.status

    def im_fetch_intercept_power(self, selector_string, timeout):
        """im_fetch_intercept_power."""
        response = self._invoke(
            self._client.IMFetchInterceptPower,
            grpc_types.IMFetchInterceptPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.intermod_order,
            response.worst_case_output_intercept_power,
            response.lower_output_intercept_power,
            response.upper_output_intercept_power,
            response.status,
        )

    def im_fetch_intermod_measurement(self, selector_string, timeout):
        """im_fetch_intermod_measurement."""
        response = self._invoke(
            self._client.IMFetchIntermodMeasurement,
            grpc_types.IMFetchIntermodMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.intermod_order,
            response.lower_intermod_power,
            response.upper_intermod_power,
            response.status,
        )

    def fcnt_fetch_allan_deviation(self, selector_string, timeout):
        """fcnt_fetch_allan_deviation."""
        response = self._invoke(
            self._client.FCntFetchAllanDeviation,
            grpc_types.FCntFetchAllanDeviationRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.allan_deviation, response.status

    def fcnt_fetch_measurement(self, selector_string, timeout):
        """fcnt_fetch_measurement."""
        response = self._invoke(
            self._client.FCntFetchMeasurement,
            grpc_types.FCntFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_relative_frequency,
            response.average_absolute_frequency,
            response.mean_phase,
            response.status,
        )

    def fcnt_read(self, selector_string, timeout):
        """fcnt_read."""
        response = self._invoke(
            self._client.FCntRead,
            grpc_types.FCntReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_relative_frequency,
            response.average_absolute_frequency,
            response.mean_phase,
            response.status,
        )

    def spectrum_fetch_measurement(self, selector_string, timeout):
        """spectrum_fetch_measurement."""
        response = self._invoke(
            self._client.SpectrumFetchMeasurement,
            grpc_types.SpectrumFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.peak_amplitude,
            response.peak_frequency,
            response.frequency_resolution,
            response.status,
        )

    def spur_fetch_measurement_status(self, selector_string, timeout):
        """spur_fetch_measurement_status."""
        response = self._invoke(
            self._client.SpurFetchMeasurementStatus,
            grpc_types.SpurFetchMeasurementStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return enums.SpurMeasurementStatus(response.measurement_status), response.status

    def spur_fetch_range_status(self, selector_string, timeout):
        """spur_fetch_range_status."""
        response = self._invoke(
            self._client.SpurFetchRangeStatus,
            grpc_types.SpurFetchRangeStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.SpurRangeStatus(response.range_status),
            response.detected_spurs,
            response.status,
        )

    def spur_fetch_spur_measurement(self, selector_string, timeout):
        """spur_fetch_spur_measurement."""
        response = self._invoke(
            self._client.SpurFetchSpurMeasurement,
            grpc_types.SpurFetchSpurMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.spur_frequency,
            response.spur_amplitude,
            response.spur_margin,
            response.spur_absolute_limit,
            response.status,
        )

    def ampm_fetch_curve_fit_residual(self, selector_string, timeout):
        """ampm_fetch_curve_fit_residual."""
        response = self._invoke(
            self._client.AMPMFetchCurveFitResidual,
            grpc_types.AMPMFetchCurveFitResidualRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.am_to_am_residual, response.am_to_pm_residual, response.status

    def ampm_fetch_dut_characteristics(self, selector_string, timeout):
        """ampm_fetch_dut_characteristics."""
        response = self._invoke(
            self._client.AMPMFetchDUTCharacteristics,
            grpc_types.AMPMFetchDUTCharacteristicsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_linear_gain,
            response.one_db_compression_point,
            response.mean_rms_evm,
            response.status,
        )

    def ampm_fetch_error(self, selector_string, timeout):
        """ampm_fetch_error."""
        response = self._invoke(
            self._client.AMPMFetchError,
            grpc_types.AMPMFetchErrorRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.gain_error_range,
            response.phase_error_range,
            response.mean_phase_error,
            response.status,
        )

    def dpd_fetch_pre_cfr_papr(self, selector_string, timeout):
        """dpd_fetch_pre_cfr_papr."""
        response = self._invoke(
            self._client.DPDFetchApplyDPDPreCFRPAPR,
            grpc_types.DPDFetchApplyDPDPreCFRPAPRRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.pre_cfr_papr, response.status

    def dpd_fetch_average_gain(self, selector_string, timeout):
        """dpd_fetch_average_gain."""
        response = self._invoke(
            self._client.DPDFetchAverageGain,
            grpc_types.DPDFetchAverageGainRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.average_gain, response.status

    def dpd_fetch_nmse(self, selector_string, timeout):
        """dpd_fetch_nmse."""
        response = self._invoke(
            self._client.DPDFetchNMSE,
            grpc_types.DPDFetchNMSERequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.nmse, response.status

    def acp_fetch_carrier_measurement(self, selector_string, timeout):
        """acp_fetch_carrier_measurement."""
        response = self._invoke(
            self._client.ACPFetchCarrierMeasurement,
            grpc_types.ACPFetchCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.absolute_power,
            response.total_relative_power,
            response.carrier_offset,
            response.integration_bandwidth,
            response.status,
        )

    def acp_fetch_frequency_resolution(self, selector_string, timeout):
        """acp_fetch_frequency_resolution."""
        response = self._invoke(
            self._client.ACPFetchFrequencyResolution,
            grpc_types.ACPFetchFrequencyResolutionRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency_resolution, response.status

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

    def acp_fetch_total_carrier_power(self, selector_string, timeout):
        """acp_fetch_total_carrier_power."""
        response = self._invoke(
            self._client.ACPFetchTotalCarrierPower,
            grpc_types.ACPFetchTotalCarrierPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_carrier_power, response.status

    def acp_read(self, selector_string, timeout):
        """acp_read."""
        response = self._invoke(
            self._client.ACPRead,
            grpc_types.ACPReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.carrier_absolute_power,
            response.offset_ch0_lower_relative_power,
            response.offset_ch0_upper_relative_power,
            response.offset_ch1_lower_relative_power,
            response.offset_ch1_upper_relative_power,
            response.status,
        )

    def ccdf_fetch_basic_power_probabilities(self, selector_string, timeout):
        """ccdf_fetch_basic_power_probabilities."""
        response = self._invoke(
            self._client.CCDFFetchBasicPowerProbabilities,
            grpc_types.CCDFFetchBasicPowerProbabilitiesRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.ten_percent_power,
            response.one_percent_power,
            response.one_tenth_percent_power,
            response.one_hundredth_percent_power,
            response.one_thousandth_percent_power,
            response.one_ten_thousandth_percent_power,
            response.status,
        )

    def ccdf_fetch_power(self, selector_string, timeout):
        """ccdf_fetch_power."""
        response = self._invoke(
            self._client.CCDFFetchPower,
            grpc_types.CCDFFetchPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_power,
            response.mean_power_percentile,
            response.peak_power,
            response.measured_samples_count,
            response.status,
        )

    def ccdf_read(self, selector_string, timeout):
        """ccdf_read."""
        response = self._invoke(
            self._client.CCDFRead,
            grpc_types.CCDFReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_power,
            response.mean_power_percentile,
            response.peak_power,
            response.measured_samples_count,
            response.status,
        )

    def chp_fetch_total_carrier_power(self, selector_string, timeout):
        """chp_fetch_total_carrier_power."""
        response = self._invoke(
            self._client.CHPFetchTotalCarrierPower,
            grpc_types.CHPFetchTotalCarrierPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_carrier_power, response.status

    def chp_read(self, selector_string, timeout):
        """chp_read."""
        response = self._invoke(
            self._client.CHPRead,
            grpc_types.CHPReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power, response.psd, response.status

    def harm_fetch_harmonic_measurement(self, selector_string, timeout):
        """harm_fetch_harmonic_measurement."""
        response = self._invoke(
            self._client.HarmFetchHarmonicMeasurement,
            grpc_types.HarmFetchHarmonicMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_relative_power,
            response.average_absolute_power,
            response.rbw,
            response.frequency,
            response.status,
        )

    def harm_fetch_total_harmonic_distortion(self, selector_string, timeout):
        """harm_fetch_total_harmonic_distortion."""
        response = self._invoke(
            self._client.HarmFetchTHD,
            grpc_types.HarmFetchTHDRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.total_harmonic_distortion,
            response.average_fundamental_power,
            response.fundamental_frequency,
            response.status,
        )

    def harm_read(self, selector_string, timeout):
        """harm_read."""
        response = self._invoke(
            self._client.HarmRead,
            grpc_types.HarmReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.total_harmonic_distortion,
            response.average_fundamental_power,
            response.status,
        )

    def marker_fetch_xy(self, selector_string):
        """marker_fetch_xy."""
        response = self._invoke(
            self._client.MarkerFetchXY,
            grpc_types.MarkerFetchXYRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.marker_x_location, response.marker_y_location, response.status

    def marker_next_peak(self, selector_string, next_peak):
        """marker_next_peak."""
        response = self._invoke(
            self._client.MarkerNextPeak,
            grpc_types.MarkerNextPeakRequest(instrument=self._vi, selector_string=selector_string, next_peak_raw=next_peak),  # type: ignore
        )
        return bool(response.next_peak_found), response.status

    def marker_peak_search(self, selector_string):
        """marker_peak_search."""
        response = self._invoke(
            self._client.MarkerPeakSearch,
            grpc_types.MarkerPeakSearchRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.number_of_peaks, response.status

    def marker_fetch_function_value(self, selector_string):
        """marker_fetch_function_value."""
        response = self._invoke(
            self._client.MarkerFetchFunctionValue,
            grpc_types.MarkerFetchFunctionValueRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.function_value, response.status

    def sem_fetch_carrier_measurement(self, selector_string, timeout):
        """sem_fetch_carrier_measurement."""
        response = self._invoke(
            self._client.SEMFetchCarrierMeasurement,
            grpc_types.SEMFetchCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.absolute_power,
            response.peak_absolute_power,
            response.peak_frequency,
            response.total_relative_power,
            response.status,
        )

    def sem_fetch_composite_measurement_status(self, selector_string, timeout):
        """sem_fetch_composite_measurement_status."""
        response = self._invoke(
            self._client.SEMFetchCompositeMeasurementStatus,
            grpc_types.SEMFetchCompositeMeasurementStatusRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            enums.SemCompositeMeasurementStatus(response.composite_measurement_status),
            response.status,
        )

    def sem_fetch_frequency_resolution(self, selector_string, timeout):
        """sem_fetch_frequency_resolution."""
        response = self._invoke(
            self._client.SEMFetchFrequencyResolution,
            grpc_types.SEMFetchFrequencyResolutionRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency_resolution, response.status

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

    def sem_fetch_total_carrier_power(self, selector_string, timeout):
        """sem_fetch_total_carrier_power."""
        response = self._invoke(
            self._client.SEMFetchTotalCarrierPower,
            grpc_types.SEMFetchTotalCarrierPowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.total_carrier_power, response.status

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

    def obw_fetch_measurement(self, selector_string, timeout):
        """obw_fetch_measurement."""
        response = self._invoke(
            self._client.OBWFetchMeasurement,
            grpc_types.OBWFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.occupied_bandwidth,
            response.average_power,
            response.frequency_resolution,
            response.start_frequency,
            response.stop_frequency,
            response.status,
        )

    def obw_read(self, selector_string, timeout):
        """obw_read."""
        response = self._invoke(
            self._client.OBWRead,
            grpc_types.OBWReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.occupied_bandwidth,
            response.average_power,
            response.frequency_resolution,
            response.start_frequency,
            response.stop_frequency,
            response.status,
        )

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        response = self._invoke(
            self._client.TXPFetchMeasurement,
            grpc_types.TXPFetchMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_mean_power,
            response.peak_to_average_ratio,
            response.maximum_power,
            response.minimum_power,
            response.status,
        )

    def txp_read(self, selector_string, timeout):
        """txp_read."""
        response = self._invoke(
            self._client.TXPRead,
            grpc_types.TXPReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_mean_power,
            response.peak_to_average_ratio,
            response.maximum_power,
            response.minimum_power,
            response.status,
        )

    def iq_get_records_done(self, selector_string):
        """iq_get_records_done."""
        response = self._invoke(
            self._client.IQGetRecordsDone,
            grpc_types.IQGetRecordsDoneRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.records_done, response.status

    def phase_noise_fetch_carrier_measurement(self, selector_string, timeout):
        """phase_noise_fetch_carrier_measurement."""
        response = self._invoke(
            self._client.PhaseNoiseFetchCarrierMeasurement,
            grpc_types.PhaseNoiseFetchCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.carrier_frequency, response.carrier_power, response.status

    def pavt_fetch_phase_and_amplitude(self, selector_string, timeout):
        """pavt_fetch_phase_and_amplitude."""
        response = self._invoke(
            self._client.PAVTFetchPhaseAndAmplitude,
            grpc_types.PAVTFetchPhaseAndAmplitudeRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_relative_phase,
            response.mean_relative_amplitude,
            response.mean_absolute_phase,
            response.mean_absolute_amplitude,
            response.status,
        )

    def chp_fetch_carrier_measurement(self, selector_string, timeout):
        """chp_fetch_carrier_measurement."""
        response = self._invoke(
            self._client.CHPFetchCarrierMeasurement,
            grpc_types.CHPFetchCarrierMeasurementRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.absolute_power, response.psd, response.relative_power, response.status

    def im_fetch_intercept_power_array(self, selector_string, timeout):
        """im_fetch_intercept_power_array."""
        response = self._invoke(
            self._client.IMFetchInterceptPowerArray,
            grpc_types.IMFetchInterceptPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.intermod_order[:],
            response.worst_case_output_intercept_power[:],
            response.lower_output_intercept_power[:],
            response.upper_output_intercept_power[:],
            response.status,
        )

    def im_fetch_intermod_measurement_array(self, selector_string, timeout):
        """im_fetch_intermod_measurement_array."""
        response = self._invoke(
            self._client.IMFetchIntermodMeasurementArray,
            grpc_types.IMFetchIntermodMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.intermod_order[:],
            response.lower_intermod_power[:],
            response.upper_intermod_power[:],
            response.status,
        )

    def im_fetch_spectrum(self, selector_string, timeout, spectrum_index, spectrum):
        """im_fetch_spectrum."""
        response = self._invoke(
            self._client.IMFetchSpectrum,
            grpc_types.IMFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, spectrum_index=spectrum_index),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def nf_fetch_analyzer_noise_figure(self, selector_string, timeout):
        """nf_fetch_analyzer_noise_figure."""
        response = self._invoke(
            self._client.NFFetchAnalyzerNoiseFigure,
            grpc_types.NFFetchAnalyzerNoiseFigureRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.analyzer_noise_figure[:], response.status

    def nf_fetch_cold_source_power(self, selector_string, timeout):
        """nf_fetch_cold_source_power."""
        response = self._invoke(
            self._client.NFFetchColdSourcePower,
            grpc_types.NFFetchColdSourcePowerRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.cold_source_power[:], response.status

    def nf_fetch_dut_noise_figure_and_gain(self, selector_string, timeout):
        """nf_fetch_dut_noise_figure_and_gain."""
        response = self._invoke(
            self._client.NFFetchDUTNoiseFigureAndGain,
            grpc_types.NFFetchDUTNoiseFigureAndGainRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.dut_noise_figure[:],
            response.dut_noise_temperature[:],
            response.dut_gain[:],
            response.status,
        )

    def nf_fetch_y_factor_powers(self, selector_string, timeout):
        """nf_fetch_y_factor_powers."""
        response = self._invoke(
            self._client.NFFetchYFactorPowers,
            grpc_types.NFFetchYFactorPowersRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.hot_power[:], response.cold_power[:], response.status

    def nf_fetch_y_factors(self, selector_string, timeout):
        """nf_fetch_y_factors."""
        response = self._invoke(
            self._client.NFFetchYFactors,
            grpc_types.NFFetchYFactorsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.measurement_y_factor[:], response.calibration_y_factor[:], response.status

    def fcnt_fetch_frequency_trace(self, selector_string, timeout, frequency_trace):
        """fcnt_fetch_frequency_trace."""
        response = self._invoke(
            self._client.FCntFetchFrequencyTrace,
            grpc_types.FCntFetchFrequencyTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(frequency_trace, "frequency_trace", "float32")
        if len(frequency_trace) != response.actual_array_size:
            frequency_trace.resize((response.actual_array_size,), refcheck=False)
        frequency_trace.flat[:] = response.frequency_trace
        return response.x0, response.dx, response.status

    def fcnt_fetch_phase_trace(self, selector_string, timeout, phase_trace):
        """fcnt_fetch_phase_trace."""
        response = self._invoke(
            self._client.FCntFetchPhaseTrace,
            grpc_types.FCntFetchPhaseTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(phase_trace, "phase_trace", "float32")
        if len(phase_trace) != response.actual_array_size:
            phase_trace.resize((response.actual_array_size,), refcheck=False)
        phase_trace.flat[:] = response.phase_trace
        return response.x0, response.dx, response.status

    def fcnt_fetch_power_trace(self, selector_string, timeout, power_trace):
        """fcnt_fetch_power_trace."""
        response = self._invoke(
            self._client.FCntFetchPowerTrace,
            grpc_types.FCntFetchPowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(power_trace, "power_trace", "float32")
        if len(power_trace) != response.actual_array_size:
            power_trace.resize((response.actual_array_size,), refcheck=False)
        power_trace.flat[:] = response.power_trace
        return response.x0, response.dx, response.status

    def spectrum_fetch_power_trace(self, selector_string, timeout, power):
        """spectrum_fetch_power_trace."""
        response = self._invoke(
            self._client.SpectrumFetchPowerTrace,
            grpc_types.SpectrumFetchPowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(power, "power", "float32")
        if len(power) != response.actual_array_size:
            power.resize((response.actual_array_size,), refcheck=False)
        power.flat[:] = response.power
        return response.x0, response.dx, response.status

    def spectrum_fetch_spectrum(self, selector_string, timeout, spectrum):
        """spectrum_fetch_spectrum."""
        response = self._invoke(
            self._client.SpectrumFetchSpectrum,
            grpc_types.SpectrumFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def spectrum_read(self, selector_string, timeout, spectrum):
        """spectrum_read."""
        response = self._invoke(
            self._client.SpectrumRead,
            grpc_types.SpectrumReadRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
        return response.x0, response.dx, response.status

    def spur_fetch_all_spurs(self, selector_string, timeout):
        """spur_fetch_all_spurs."""
        response = self._invoke(
            self._client.SpurFetchAllSpurs,
            grpc_types.SpurFetchAllSpursRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.spur_frequency[:],
            response.spur_amplitude[:],
            response.spur_margin[:],
            response.spur_absolute_limit[:],
            response.spur_range_index[:],
            response.status,
        )

    def spur_fetch_range_absolute_limit_trace(self, selector_string, timeout, absolute_limit):
        """spur_fetch_range_absolute_limit_trace."""
        response = self._invoke(
            self._client.SpurFetchRangeAbsoluteLimitTrace,
            grpc_types.SpurFetchRangeAbsoluteLimitTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(absolute_limit, "absolute_limit", "float32")
        if len(absolute_limit) != response.actual_array_size:
            absolute_limit.resize((response.actual_array_size,), refcheck=False)
        absolute_limit.flat[:] = response.absolute_limit
        return response.x0, response.dx, response.status

    def spur_fetch_range_spectrum_trace(self, selector_string, timeout, range_spectrum):
        """spur_fetch_range_spectrum_trace."""
        response = self._invoke(
            self._client.SpurFetchRangeSpectrumTrace,
            grpc_types.SpurFetchRangeSpectrumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(range_spectrum, "range_spectrum", "float32")
        if len(range_spectrum) != response.actual_array_size:
            range_spectrum.resize((response.actual_array_size,), refcheck=False)
        range_spectrum.flat[:] = response.range_spectrum
        return response.x0, response.dx, response.status

    def spur_fetch_range_status_array(self, selector_string, timeout):
        """spur_fetch_range_status_array."""
        response = self._invoke(
            self._client.SpurFetchRangeStatusArray,
            grpc_types.SpurFetchRangeStatusArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            [enums.SpurRangeStatus(value) for value in response.range_status],
            response.number_of_detected_spurs[:],
            response.status,
        )

    def spur_fetch_spur_measurement_array(self, selector_string, timeout):
        """spur_fetch_spur_measurement_array."""
        response = self._invoke(
            self._client.SpurFetchSpurMeasurementArray,
            grpc_types.SpurFetchSpurMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.spur_frequency[:],
            response.spur_amplitude[:],
            response.spur_absolute_limit[:],
            response.spur_margin[:],
            response.status,
        )

    def ampm_fetch_am_to_am_trace(self, selector_string, timeout):
        """ampm_fetch_am_to_am_trace."""
        response = self._invoke(
            self._client.AMPMFetchAMToAMTrace,
            grpc_types.AMPMFetchAMToAMTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.reference_powers[:],
            response.measured_am_to_am[:],
            response.curve_fit_am_to_am[:],
            response.status,
        )

    def ampm_fetch_am_to_pm_trace(self, selector_string, timeout):
        """ampm_fetch_am_to_pm_trace."""
        response = self._invoke(
            self._client.AMPMFetchAMToPMTrace,
            grpc_types.AMPMFetchAMToPMTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.reference_powers[:],
            response.measured_am_to_pm[:],
            response.curve_fit_am_to_pm[:],
            response.status,
        )

    def ampm_fetch_compression_points(self, selector_string, timeout):
        """ampm_fetch_compression_points."""
        response = self._invoke(
            self._client.AMPMFetchCompressionPoints,
            grpc_types.AMPMFetchCompressionPointsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.input_compression_point[:],
            response.output_compression_point[:],
            response.status,
        )

    def ampm_fetch_curve_fit_coefficients(self, selector_string, timeout):
        """ampm_fetch_curve_fit_coefficients."""
        response = self._invoke(
            self._client.AMPMFetchCurveFitCoefficients,
            grpc_types.AMPMFetchCurveFitCoefficientsRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.am_to_am_coefficients[:], response.am_to_pm_coefficients[:], response.status

    def ampm_fetch_processed_mean_acquired_waveform(
        self, selector_string, timeout, processed_mean_acquired_waveform
    ):
        """ampm_fetch_processed_mean_acquired_waveform."""
        response = self._invoke(
            self._client.AMPMFetchProcessedMeanAcquiredWaveformInterleavedIQ,
            grpc_types.AMPMFetchProcessedMeanAcquiredWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            processed_mean_acquired_waveform, "processed_mean_acquired_waveform", "complex64"
        )
        if len(processed_mean_acquired_waveform) != response.actual_array_size // 2:
            processed_mean_acquired_waveform.resize(
                (response.actual_array_size // 2,), refcheck=False
            )
        flat = numpy.array(response.processed_mean_acquired_waveform, dtype=numpy.float32)
        processed_mean_acquired_waveform[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def ampm_fetch_processed_reference_waveform(
        self, selector_string, timeout, processed_reference_waveform
    ):
        """ampm_fetch_processed_reference_waveform."""
        response = self._invoke(
            self._client.AMPMFetchProcessedReferenceWaveformInterleavedIQ,
            grpc_types.AMPMFetchProcessedReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            processed_reference_waveform, "processed_reference_waveform", "complex64"
        )
        if len(processed_reference_waveform) != response.actual_array_size // 2:
            processed_reference_waveform.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.processed_reference_waveform, dtype=numpy.float32)
        processed_reference_waveform[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def ampm_fetch_relative_phase_trace(self, selector_string, timeout, relative_phase):
        """ampm_fetch_relative_phase_trace."""
        response = self._invoke(
            self._client.AMPMFetchRelativePhaseTrace,
            grpc_types.AMPMFetchRelativePhaseTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(relative_phase, "relative_phase", "float32")
        if len(relative_phase) != response.actual_array_size:
            relative_phase.resize((response.actual_array_size,), refcheck=False)
        relative_phase.flat[:] = response.relative_phase
        return response.x0, response.dx, response.status

    def ampm_fetch_relative_power_trace(self, selector_string, timeout, relative_power):
        """ampm_fetch_relative_power_trace."""
        response = self._invoke(
            self._client.AMPMFetchRelativePowerTrace,
            grpc_types.AMPMFetchRelativePowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(relative_power, "relative_power", "float32")
        if len(relative_power) != response.actual_array_size:
            relative_power.resize((response.actual_array_size,), refcheck=False)
        relative_power.flat[:] = response.relative_power
        return response.x0, response.dx, response.status

    def dpd_fetch_dpd_polynomial(self, selector_string, timeout, dpd_polynomial):
        """dpd_fetch_dpd_polynomial."""
        response = self._invoke(
            self._client.DPDFetchDPDPolynomialInterleavedIQ,
            grpc_types.DPDFetchDPDPolynomialInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(dpd_polynomial, "dpd_polynomial", "complex64")
        if len(dpd_polynomial) != response.actual_array_size // 2:
            dpd_polynomial.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.dpd_polynomial, dtype=numpy.float32)
        dpd_polynomial[:] = flat.view(numpy.complex64)
        return response.status

    def dpd_fetch_dvr_model(self, selector_string, timeout, dvr_model):
        """dpd_fetch_dvr_model."""
        response = self._invoke(
            self._client.DPDFetchDVRModelInterleavedIQ,
            grpc_types.DPDFetchDVRModelInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(dvr_model, "dvr_model", "complex64")
        if len(dvr_model) != response.actual_array_size // 2:
            dvr_model.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.dvr_model, dtype=numpy.float32)
        dvr_model[:] = flat.view(numpy.complex64)
        return response.status

    def dpd_fetch_lookup_table(self, selector_string, timeout, complex_gains):
        """dpd_fetch_lookup_table."""
        response = self._invoke(
            self._client.DPDFetchLookupTableInterleavedIQ,
            grpc_types.DPDFetchLookupTableInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(complex_gains, "complex_gains", "complex64")
        if len(complex_gains) != response.actual_array_size // 2:
            complex_gains.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.complex_gains, dtype=numpy.float32)
        complex_gains[:] = flat.view(numpy.complex64)
        return response.input_powers[:], response.status

    def dpd_fetch_processed_mean_acquired_waveform(
        self, selector_string, timeout, processed_mean_acquired_waveform
    ):
        """dpd_fetch_processed_mean_acquired_waveform."""
        response = self._invoke(
            self._client.DPDFetchProcessedMeanAcquiredWaveformInterleavedIQ,
            grpc_types.DPDFetchProcessedMeanAcquiredWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            processed_mean_acquired_waveform, "processed_mean_acquired_waveform", "complex64"
        )
        if len(processed_mean_acquired_waveform) != response.actual_array_size // 2:
            processed_mean_acquired_waveform.resize(
                (response.actual_array_size // 2,), refcheck=False
            )
        flat = numpy.array(response.processed_mean_acquired_waveform, dtype=numpy.float32)
        processed_mean_acquired_waveform[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def dpd_fetch_processed_reference_waveform(
        self, selector_string, timeout, processed_reference_waveform
    ):
        """dpd_fetch_processed_reference_waveform."""
        response = self._invoke(
            self._client.DPDFetchProcessedReferenceWaveformInterleavedIQ,
            grpc_types.DPDFetchProcessedReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            processed_reference_waveform, "processed_reference_waveform", "complex64"
        )
        if len(processed_reference_waveform) != response.actual_array_size // 2:
            processed_reference_waveform.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.processed_reference_waveform, dtype=numpy.float32)
        processed_reference_waveform[:] = flat.view(numpy.complex64)
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

    def ccdf_fetch_gaussian_probabilities_trace(
        self, selector_string, timeout, gaussian_probabilities
    ):
        """ccdf_fetch_gaussian_probabilities_trace."""
        response = self._invoke(
            self._client.CCDFFetchGaussianProbabilitiesTrace,
            grpc_types.CCDFFetchGaussianProbabilitiesTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(gaussian_probabilities, "gaussian_probabilities", "float32")
        if len(gaussian_probabilities) != response.actual_array_size:
            gaussian_probabilities.resize((response.actual_array_size,), refcheck=False)
        gaussian_probabilities.flat[:] = response.gaussian_probabilities
        return response.x0, response.dx, response.status

    def ccdf_fetch_probabilities_trace(self, selector_string, timeout, probabilities):
        """ccdf_fetch_probabilities_trace."""
        response = self._invoke(
            self._client.CCDFFetchProbabilitiesTrace,
            grpc_types.CCDFFetchProbabilitiesTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(probabilities, "probabilities", "float32")
        if len(probabilities) != response.actual_array_size:
            probabilities.resize((response.actual_array_size,), refcheck=False)
        probabilities.flat[:] = response.probabilities
        return response.x0, response.dx, response.status

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

    def harm_fetch_harmonic_power_trace(self, selector_string, timeout, power):
        """harm_fetch_harmonic_power_trace."""
        response = self._invoke(
            self._client.HarmFetchHarmonicPowerTrace,
            grpc_types.HarmFetchHarmonicPowerTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(power, "power", "float32")
        if len(power) != response.actual_array_size:
            power.resize((response.actual_array_size,), refcheck=False)
        power.flat[:] = response.power
        return response.x0, response.dx, response.status

    def harm_fetch_harmonic_measurement_array(self, selector_string, timeout):
        """harm_fetch_harmonic_measurement_array."""
        response = self._invoke(
            self._client.HarmFetchHarmonicMeasurementArray,
            grpc_types.HarmFetchHarmonicMeasurementArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.average_relative_power[:],
            response.average_absolute_power[:],
            response.rbw[:],
            response.frequency[:],
            response.status,
        )

    def sem_fetch_absolute_mask_trace(self, selector_string, timeout, absolute_mask):
        """sem_fetch_absolute_mask_trace."""
        response = self._invoke(
            self._client.SEMFetchAbsoluteMaskTrace,
            grpc_types.SEMFetchAbsoluteMaskTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(absolute_mask, "absolute_mask", "float32")
        if len(absolute_mask) != response.actual_array_size:
            absolute_mask.resize((response.actual_array_size,), refcheck=False)
        absolute_mask.flat[:] = response.absolute_mask
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

    def sem_fetch_relative_mask_trace(self, selector_string, timeout, relative_mask):
        """sem_fetch_relative_mask_trace."""
        response = self._invoke(
            self._client.SEMFetchRelativeMaskTrace,
            grpc_types.SEMFetchRelativeMaskTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(relative_mask, "relative_mask", "float32")
        if len(relative_mask) != response.actual_array_size:
            relative_mask.resize((response.actual_array_size,), refcheck=False)
        relative_mask.flat[:] = response.relative_mask
        return response.x0, response.dx, response.status

    def sem_fetch_spectrum(self, selector_string, timeout, spectrum):
        """sem_fetch_spectrum."""
        response = self._invoke(
            self._client.SEMFetchSpectrum,
            grpc_types.SEMFetchSpectrumRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != response.actual_array_size:
            spectrum.resize((response.actual_array_size,), refcheck=False)
        spectrum.flat[:] = response.spectrum
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

    def obw_fetch_spectrum_trace(self, selector_string, timeout, spectrum):
        """obw_fetch_spectrum_trace."""
        response = self._invoke(
            self._client.OBWFetchSpectrumTrace,
            grpc_types.OBWFetchSpectrumTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
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

    def iq_fetch_data(self, selector_string, timeout, record_to_fetch, samples_to_read, data):
        """iq_fetch_data."""
        response = self._invoke(
            self._client.IQFetchDataInterleavedIQ,
            grpc_types.IQFetchDataInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, record_to_fetch=record_to_fetch, samples_to_read=samples_to_read),  # type: ignore
        )
        _helper.validate_numpy_array(data, "data", "complex64")
        if len(data) != response.actual_array_size // 2:
            data.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.data, dtype=numpy.float32)
        data[:] = flat.view(numpy.complex64)
        return response.t0, response.dt, response.status

    def phase_noise_fetch_integrated_noise(self, selector_string, timeout):
        """phase_noise_fetch_integrated_noise."""
        response = self._invoke(
            self._client.PhaseNoiseFetchIntegratedNoise,
            grpc_types.PhaseNoiseFetchIntegratedNoiseRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.integrated_phase_noise[:],
            response.residual_pm_in_radian[:],
            response.residual_pm_in_degree[:],
            response.residual_fm[:],
            response.jitter[:],
            response.status,
        )

    def phase_noise_fetch_measured_log_plot_trace(self, selector_string, timeout):
        """phase_noise_fetch_measured_log_plot_trace."""
        response = self._invoke(
            self._client.PhaseNoiseFetchMeasuredLogPlotTrace,
            grpc_types.PhaseNoiseFetchMeasuredLogPlotTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency[:], response.measured_phase_noise[:], response.status

    def phase_noise_fetch_smoothed_log_plot_trace(self, selector_string, timeout):
        """phase_noise_fetch_smoothed_log_plot_trace."""
        response = self._invoke(
            self._client.PhaseNoiseFetchSmoothedLogPlotTrace,
            grpc_types.PhaseNoiseFetchSmoothedLogPlotTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.frequency[:], response.smoothed_phase_noise[:], response.status

    def phase_noise_fetch_spot_noise(self, selector_string, timeout):
        """phase_noise_fetch_spot_noise."""
        response = self._invoke(
            self._client.PhaseNoiseFetchSpotNoise,
            grpc_types.PhaseNoiseFetchSpotNoiseRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.spot_phase_noise[:], response.status

    def pavt_fetch_amplitude_trace(self, selector_string, timeout, trace_index, amplitude):
        """pavt_fetch_amplitude_trace."""
        response = self._invoke(
            self._client.PAVTFetchAmplitudeTrace,
            grpc_types.PAVTFetchAmplitudeTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, trace_index=trace_index),  # type: ignore
        )
        _helper.validate_numpy_array(amplitude, "amplitude", "float32")
        if len(amplitude) != response.actual_array_size:
            amplitude.resize((response.actual_array_size,), refcheck=False)
        amplitude.flat[:] = response.amplitude
        return response.x0, response.dx, response.status

    def pavt_fetch_phase_and_amplitude_array(self, selector_string, timeout):
        """pavt_fetch_phase_and_amplitude_array."""
        response = self._invoke(
            self._client.PAVTFetchPhaseAndAmplitudeArray,
            grpc_types.PAVTFetchPhaseAndAmplitudeArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return (
            response.mean_relative_phase[:],
            response.mean_relative_amplitude[:],
            response.mean_absolute_phase[:],
            response.mean_absolute_amplitude[:],
            response.status,
        )

    def pavt_fetch_phase_trace(self, selector_string, timeout, trace_index, phase):
        """pavt_fetch_phase_trace."""
        response = self._invoke(
            self._client.PAVTFetchPhaseTrace,
            grpc_types.PAVTFetchPhaseTraceRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, trace_index=trace_index),  # type: ignore
        )
        _helper.validate_numpy_array(phase, "phase", "float32")
        if len(phase) != response.actual_array_size:
            phase.resize((response.actual_array_size,), refcheck=False)
        phase.flat[:] = response.phase
        return response.x0, response.dx, response.status

    def idpd_fetch_processed_mean_acquired_waveform(
        self, selector_string, timeout, processed_mean_acquired_waveform
    ):
        """idpd_fetch_processed_mean_acquired_waveform."""
        response = self._invoke(
            self._client.IDPDFetchProcessedMeanAcquiredWaveformInterleavedIQ,
            grpc_types.IDPDFetchProcessedMeanAcquiredWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            processed_mean_acquired_waveform, "processed_mean_acquired_waveform", "complex64"
        )
        if len(processed_mean_acquired_waveform) != response.actual_array_size // 2:
            processed_mean_acquired_waveform.resize(
                (response.actual_array_size // 2,), refcheck=False
            )
        flat = numpy.array(response.processed_mean_acquired_waveform, dtype=numpy.float32)
        processed_mean_acquired_waveform[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def idpd_fetch_processed_reference_waveform(
        self, selector_string, timeout, processed_reference_waveform
    ):
        """idpd_fetch_processed_reference_waveform."""
        response = self._invoke(
            self._client.IDPDFetchProcessedReferenceWaveformInterleavedIQ,
            grpc_types.IDPDFetchProcessedReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(
            processed_reference_waveform, "processed_reference_waveform", "complex64"
        )
        if len(processed_reference_waveform) != response.actual_array_size // 2:
            processed_reference_waveform.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.processed_reference_waveform, dtype=numpy.float32)
        processed_reference_waveform[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def idpd_fetch_predistorted_waveform(self, selector_string, timeout, predistorted_waveform):
        """idpd_fetch_predistorted_waveform."""
        response = self._invoke(
            self._client.IDPDFetchPredistortedWaveformInterleavedIQ,
            grpc_types.IDPDFetchPredistortedWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(predistorted_waveform, "predistorted_waveform", "complex64")
        if len(predistorted_waveform) != response.actual_array_size // 2:
            predistorted_waveform.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.predistorted_waveform, dtype=numpy.float32)
        predistorted_waveform[:] = flat.view(numpy.complex64)
        return (
            response.x0,
            response.dx,
            response.papr,
            response.power_offset,
            response.gain,
            response.status,
        )

    def idpd_fetch_equalizer_coefficients(self, selector_string, timeout, equalizer_coefficients):
        """idpd_fetch_equalizer_coefficients."""
        response = self._invoke(
            self._client.IDPDFetchEqualizerCoefficientsInterleavedIQ,
            grpc_types.IDPDFetchEqualizerCoefficientsInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        _helper.validate_numpy_array(equalizer_coefficients, "equalizer_coefficients", "complex64")
        if len(equalizer_coefficients) != response.actual_array_size // 2:
            equalizer_coefficients.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.equalizer_coefficients, dtype=numpy.float32)
        equalizer_coefficients[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def idpd_get_equalizer_reference_waveform(self, selector_string, equalizer_reference_waveform):
        """idpd_get_equalizer_reference_waveform."""
        response = self._invoke(
            self._client.IDPDGetEqualizerReferenceWaveformInterleavedIQ,
            grpc_types.IDPDGetEqualizerReferenceWaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        _helper.validate_numpy_array(
            equalizer_reference_waveform, "equalizer_reference_waveform", "complex64"
        )
        if len(equalizer_reference_waveform) != response.actual_array_size // 2:
            equalizer_reference_waveform.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.equalizer_reference_waveform, dtype=numpy.float32)
        equalizer_reference_waveform[:] = flat.view(numpy.complex64)
        return response.x0, response.dx, response.papr, response.status

    def power_list_fetch_mean_absolute_power_array(self, selector_string, timeout):
        """power_list_fetch_mean_absolute_power_array."""
        response = self._invoke(
            self._client.PowerListFetchMeanAbsolutePowerArray,
            grpc_types.PowerListFetchMeanAbsolutePowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.mean_absolute_power[:], response.status

    def power_list_fetch_maximum_power_array(self, selector_string, timeout):
        """power_list_fetch_maximum_power_array."""
        response = self._invoke(
            self._client.PowerListFetchMaximumPowerArray,
            grpc_types.PowerListFetchMaximumPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.maximum_power[:], response.status

    def power_list_fetch_minimum_power_array(self, selector_string, timeout):
        """power_list_fetch_minimum_power_array."""
        response = self._invoke(
            self._client.PowerListFetchMinimumPowerArray,
            grpc_types.PowerListFetchMinimumPowerArrayRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout),  # type: ignore
        )
        return response.minimum_power[:], response.status

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        response = self._invoke(
            self._client.CloneSignalConfiguration,
            grpc_types.CloneSignalConfigurationRequest(instrument=self._vi, old_signal_name=old_signal_name, new_signal_name=new_signal_name),  # type: ignore
        )
        # signal_configuration = SpecAnSignalConfiguration.get_specan_signal_configuration(self, new_signal_name)
        import nirfmxspecan

        signal_configuration = nirfmxspecan._SpecAnSignalConfiguration.get_specan_signal_configuration(self._instr_session, new_signal_name, True)  # type: ignore
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

    def dpd_apply_digital_predistortion(
        self,
        selector_string,
        x0_in,
        dx_in,
        waveform_in,
        idle_duration_present,
        measurement_timeout,
        waveform_out,
    ):
        """dpd_apply_digital_predistortion."""
        _helper.validate_numpy_array(waveform_in, "waveform_in", "complex64")
        waveform_in_proto = waveform_in.view(numpy.float32)
        response = self._invoke(
            self._client.DPDApplyDigitalPredistortionInterleavedIQ,
            grpc_types.DPDApplyDigitalPredistortionInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0_in=x0_in, dx_in=dx_in, waveform_in=waveform_in_proto, idle_duration_present_raw=idle_duration_present, measurement_timeout=measurement_timeout),  # type: ignore
        )
        _helper.validate_numpy_array(waveform_out, "waveform_out", "complex64")
        if len(waveform_out) != response.actual_array_size // 2:
            waveform_out.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.waveform_out, dtype=numpy.float32)
        waveform_out = flat.view(numpy.complex64)
        return (
            response.x0_out,
            response.dx_out,
            response.papr,
            response.power_offset,
            response.status,
        )

    def dpd_apply_pre_dpd_signal_conditioning(
        self, selector_string, x0_in, dx_in, waveform_in, idle_duration_present, waveform_out
    ):
        """dpd_apply_pre_dpd_signal_conditioning."""
        _helper.validate_numpy_array(waveform_in, "waveform_in", "complex64")
        waveform_in_proto = waveform_in.view(numpy.float32)
        response = self._invoke(
            self._client.DPDApplyPreDPDSignalConditioningInterleavedIQ,
            grpc_types.DPDApplyPreDPDSignalConditioningInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, x0_in=x0_in, dx_in=dx_in, waveform_in=waveform_in_proto, idle_duration_present_raw=idle_duration_present),  # type: ignore
        )
        _helper.validate_numpy_array(waveform_out, "waveform_out", "complex64")
        if len(waveform_out) != response.actual_array_size // 2:
            waveform_out.resize((response.actual_array_size // 2,), refcheck=False)
        flat = numpy.array(response.waveform_out, dtype=numpy.float32)
        waveform_out = flat.view(numpy.complex64)
        return response.x0_out, response.dx_out, response.papr, response.status

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
        iq_proto = iq.view(numpy.float32)
        response = self._invoke(
            self._client.AnalyzeIQ1WaveformInterleavedIQ,
            grpc_types.AnalyzeIQ1WaveformInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, result_name=result_name, x0=x0, dx=dx, iq=iq_proto, reset=reset),  # type: ignore
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
