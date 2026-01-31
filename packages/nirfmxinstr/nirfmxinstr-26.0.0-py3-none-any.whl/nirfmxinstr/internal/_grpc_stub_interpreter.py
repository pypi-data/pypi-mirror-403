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
import hightime
import nirfmxinstr.enums as enums
import nirfmxinstr.errors as errors
import nirfmxinstr.internal._custom_types as _custom_types
import nirfmxinstr.internal._helper as _helper
import nirfmxinstr.internal.nidevice_pb2 as nidevice_grpc_types
import nirfmxinstr.internal.nirfmxinstr_pb2 as grpc_types
import nirfmxinstr.internal.nirfmxinstr_pb2_grpc as nirfmxinstr_grpc
import nirfmxinstr.internal.nirfmxinstr_restricted_pb2 as restricted_grpc_types
import nirfmxinstr.internal.nirfmxinstr_restricted_pb2_grpc as nirfmxinstr_restricted_grpc
import nirfmxinstr.internal.session_pb2 as session_grpc_types


class GrpcStubInterpreter(object):
    """Interpreter for interacting with a gRPC Stub class"""

    def __init__(self, grpc_options, session=None, signal_obj=None):
        self._grpc_options = grpc_options
        self._signal_obj = signal_obj
        self._instr_session = session
        self._client = nirfmxinstr_grpc.NiRFmxInstrStub(grpc_options.grpc_channel)  # type: ignore
        self._restricted_client = nirfmxinstr_restricted_grpc.NiRFmxInstrRestrictedStub(grpc_options.grpc_channel)  # type: ignore
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
            raise errors.RFmxError(error_code, error_message)  # type: ignore

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

    def get_attribute_i8(self, selector_string, attribute_id):
        """get_attribute_i8."""
        response = self._invoke(
            self._client.GetAttributeI8,
            grpc_types.GetAttributeI8Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i8(self, selector_string, attribute_id, attr_val):
        """set_attribute_i8."""
        response = self._invoke(
            self._client.SetAttributeI8,
            grpc_types.SetAttributeI8Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i8_array(self, selector_string, attribute_id):
        """get_attribute_i8_array."""
        response = self._invoke(
            self._client.GetAttributeI8Array,
            grpc_types.GetAttributeI8ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i8_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i8_array."""
        response = self._invoke(
            self._client.SetAttributeI8Array,
            grpc_types.SetAttributeI8ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i16(self, selector_string, attribute_id):
        """get_attribute_i16."""
        response = self._invoke(
            self._client.GetAttributeI16,
            grpc_types.GetAttributeI16Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i16(self, selector_string, attribute_id, attr_val):
        """set_attribute_i16."""
        response = self._invoke(
            self._client.SetAttributeI16,
            grpc_types.SetAttributeI16Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i32(self, selector_string, attribute_id):
        """get_attribute_i32."""
        response = self._invoke(
            self._client.GetAttributeI32,
            grpc_types.GetAttributeI32Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val_raw, response.status

    def set_attribute_i32(self, selector_string, attribute_id, attr_val):
        """set_attribute_i32."""
        response = self._invoke(
            self._client.SetAttributeI32,
            grpc_types.SetAttributeI32Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val_raw=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i32_array(self, selector_string, attribute_id):
        """get_attribute_i32_array."""
        response = self._invoke(
            self._client.GetAttributeI32Array,
            grpc_types.GetAttributeI32ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i32_array."""
        response = self._invoke(
            self._client.SetAttributeI32Array,
            grpc_types.SetAttributeI32ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i64(self, selector_string, attribute_id):
        """get_attribute_i64."""
        response = self._invoke(
            self._client.GetAttributeI64,
            grpc_types.GetAttributeI64Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i64(self, selector_string, attribute_id, attr_val):
        """set_attribute_i64."""
        response = self._invoke(
            self._client.SetAttributeI64,
            grpc_types.SetAttributeI64Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_i64_array(self, selector_string, attribute_id):
        """get_attribute_i64_array."""
        response = self._invoke(
            self._client.GetAttributeI64Array,
            grpc_types.GetAttributeI64ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_i64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i64_array."""
        response = self._invoke(
            self._client.SetAttributeI64Array,
            grpc_types.SetAttributeI64ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u8(self, selector_string, attribute_id):
        """get_attribute_u8."""
        response = self._invoke(
            self._client.GetAttributeU8,
            grpc_types.GetAttributeU8Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u8(self, selector_string, attribute_id, attr_val):
        """set_attribute_u8."""
        response = self._invoke(
            self._client.SetAttributeU8,
            grpc_types.SetAttributeU8Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u8_array(self, selector_string, attribute_id):
        """get_attribute_u8_array."""
        response = self._invoke(
            self._client.GetAttributeU8Array,
            grpc_types.GetAttributeU8ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u8_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u8_array."""
        response = self._invoke(
            self._client.SetAttributeU8Array,
            grpc_types.SetAttributeU8ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u16(self, selector_string, attribute_id):
        """get_attribute_u16."""
        response = self._invoke(
            self._client.GetAttributeU16,
            grpc_types.GetAttributeU16Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u16(self, selector_string, attribute_id, attr_val):
        """set_attribute_u16."""
        response = self._invoke(
            self._client.SetAttributeU16,
            grpc_types.SetAttributeU16Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u32(self, selector_string, attribute_id):
        """get_attribute_u32."""
        response = self._invoke(
            self._client.GetAttributeU32,
            grpc_types.GetAttributeU32Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u32(self, selector_string, attribute_id, attr_val):
        """set_attribute_u32."""
        response = self._invoke(
            self._client.SetAttributeU32,
            grpc_types.SetAttributeU32Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u32_array(self, selector_string, attribute_id):
        """get_attribute_u32_array."""
        response = self._invoke(
            self._client.GetAttributeU32Array,
            grpc_types.GetAttributeU32ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u32_array."""
        response = self._invoke(
            self._client.SetAttributeU32Array,
            grpc_types.SetAttributeU32ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_u64_array(self, selector_string, attribute_id):
        """get_attribute_u64_array."""
        response = self._invoke(
            self._client.GetAttributeU64Array,
            grpc_types.GetAttributeU64ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_u64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u64_array."""
        response = self._invoke(
            self._client.SetAttributeU64Array,
            grpc_types.SetAttributeU64ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f32(self, selector_string, attribute_id):
        """get_attribute_f32."""
        response = self._invoke(
            self._client.GetAttributeF32,
            grpc_types.GetAttributeF32Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f32(self, selector_string, attribute_id, attr_val):
        """set_attribute_f32."""
        response = self._invoke(
            self._client.SetAttributeF32,
            grpc_types.SetAttributeF32Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f32_array(self, selector_string, attribute_id):
        """get_attribute_f32_array."""
        response = self._invoke(
            self._client.GetAttributeF32Array,
            grpc_types.GetAttributeF32ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_f32_array."""
        response = self._invoke(
            self._client.SetAttributeF32Array,
            grpc_types.SetAttributeF32ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f64(self, selector_string, attribute_id):
        """get_attribute_f64."""
        response = self._invoke(
            self._client.GetAttributeF64,
            grpc_types.GetAttributeF64Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f64(self, selector_string, attribute_id, attr_val):
        """set_attribute_f64."""
        response = self._invoke(
            self._client.SetAttributeF64,
            grpc_types.SetAttributeF64Request(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_f64_array(self, selector_string, attribute_id):
        """get_attribute_f64_array."""
        response = self._invoke(
            self._client.GetAttributeF64Array,
            grpc_types.GetAttributeF64ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_f64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_f64_array."""
        response = self._invoke(
            self._client.SetAttributeF64Array,
            grpc_types.SetAttributeF64ArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_nicomplexsingle_array(self, selector_string, attribute_id):
        """get_attribute_nicomplexsingle_array."""
        response = self._invoke(
            self._client.GetAttributeNIComplexSingleArray,
            grpc_types.GetAttributeNIComplexSingleArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_nicomplexsingle_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_nicomplexsingle_array."""
        response = self._invoke(
            self._client.SetAttributeNIComplexSingleArray,
            grpc_types.SetAttributeNIComplexSingleArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_nicomplexdouble_array(self, selector_string, attribute_id):
        """get_attribute_nicomplexdouble_array."""
        response = self._invoke(
            self._client.GetAttributeNIComplexDoubleArray,
            grpc_types.GetAttributeNIComplexDoubleArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_nicomplexdouble_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_nicomplexdouble_array."""
        response = self._invoke(
            self._client.SetAttributeNIComplexDoubleArray,
            grpc_types.SetAttributeNIComplexDoubleArrayRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val=attr_val),  # type: ignore
        )
        return response.status

    def get_attribute_string(self, selector_string, attribute_id):
        """get_attribute_string."""
        response = self._invoke(
            self._client.GetAttributeString,
            grpc_types.GetAttributeStringRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.attr_val, response.status

    def set_attribute_string(self, selector_string, attribute_id, attr_val):
        """set_attribute_string."""
        response = self._invoke(
            self._client.SetAttributeString,
            grpc_types.SetAttributeStringRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id, attr_val_raw=attr_val),  # type: ignore
        )
        return response.status

    def check_acquisition_status(self):
        """check_acquisition_status."""
        response = self._invoke(
            self._client.CheckAcquisitionStatus,
            grpc_types.CheckAcquisitionStatusRequest(instrument=self._vi),  # type: ignore
        )
        return bool(response.acquisition_done), response.status

    def configure_external_attenuation_table(
        self, selector_string, table_name, frequency, external_attenuation
    ):
        """configure_external_attenuation_table."""
        _helper.validate_numpy_array(frequency, "frequency", "float64")
        frequency_proto = frequency.flat

        _helper.validate_numpy_array(external_attenuation, "external_attenuation", "float64")
        external_attenuation_proto = external_attenuation.flat

        response = self._invoke(
            self._client.CfgExternalAttenuationTable,
            grpc_types.CfgExternalAttenuationTableRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name, frequency=frequency_proto, external_attenuation=external_attenuation_proto),  # type: ignore
        )
        return response.status

    def select_active_external_attenuation_table(self, selector_string, table_name):
        """select_active_external_attenuation_table."""
        response = self._invoke(
            self._client.SelectActiveExternalAttenuationTable,
            grpc_types.SelectActiveExternalAttenuationTableRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name),  # type: ignore
        )
        return response.status

    def delete_external_attenuation_table(self, selector_string, table_name):
        """delete_external_attenuation_table."""
        response = self._invoke(
            self._client.DeleteExternalAttenuationTable,
            grpc_types.DeleteExternalAttenuationTableRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name),  # type: ignore
        )
        return response.status

    def delete_all_external_attenuation_tables(self, selector_string):
        """delete_all_external_attenuation_tables."""
        response = self._invoke(
            self._client.DeleteAllExternalAttenuationTables,
            grpc_types.DeleteAllExternalAttenuationTablesRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def enable_calibration_plane(self, selector_string):
        """enable_calibration_plane."""
        response = self._invoke(
            self._client.EnableCalibrationPlane,
            grpc_types.EnableCalibrationPlaneRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def disable_calibration_plane(self, selector_string):
        """disable_calibration_plane."""
        response = self._invoke(
            self._client.DisableCalibrationPlane,
            grpc_types.DisableCalibrationPlaneRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.status

    def check_if_signal_exists(self, signal_name):
        """check_if_signal_exists."""
        response = self._invoke(
            self._client.CheckIfSignalConfigurationExists,
            grpc_types.CheckIfSignalConfigurationExistsRequest(instrument=self._vi, signal_name=signal_name),  # type: ignore
        )
        return (
            bool(response.signal_configuration_exists),
            enums.Personalities(response.personality),
            response.status,
        )

    def load_s_parameter_external_attenuation_table_from_s2p_file(
        self, selector_string, table_name, s2p_file_path, s_parameter_orientation
    ):
        """load_s_parameter_external_attenuation_table_from_s2p_file."""
        response = self._invoke(
            self._client.LoadSParameterExternalAttenuationTableFromS2PFile,
            grpc_types.LoadSParameterExternalAttenuationTableFromS2PFileRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name, s2p_file_path=s2p_file_path, s_parameter_orientation_raw=s_parameter_orientation),  # type: ignore
        )
        return response.status

    def configure_external_attenuation_interpolation_nearest(self, selector_string, table_name):
        """configure_external_attenuation_interpolation_nearest."""
        response = self._invoke(
            self._client.CfgExternalAttenuationInterpolationNearest,
            grpc_types.CfgExternalAttenuationInterpolationNearestRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name),  # type: ignore
        )
        return response.status

    def configure_external_attenuation_interpolation_linear(
        self, selector_string, table_name, format
    ):
        """configure_external_attenuation_interpolation_linear."""
        response = self._invoke(
            self._client.CfgExternalAttenuationInterpolationLinear,
            grpc_types.CfgExternalAttenuationInterpolationLinearRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name, format_raw=format),  # type: ignore
        )
        return response.status

    def configure_external_attenuation_interpolation_spline(self, selector_string, table_name):
        """configure_external_attenuation_interpolation_spline."""
        response = self._invoke(
            self._client.CfgExternalAttenuationInterpolationSpline,
            grpc_types.CfgExternalAttenuationInterpolationSplineRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name),  # type: ignore
        )
        return response.status

    def configure_s_parameter_external_attenuation_type(self, selector_string, s_parameter_type):
        """configure_s_parameter_external_attenuation_type."""
        response = self._invoke(
            self._client.CfgSParameterExternalAttenuationType,
            grpc_types.CfgSParameterExternalAttenuationTypeRequest(instrument=self._vi, selector_string=selector_string, s_parameter_type_raw=s_parameter_type),  # type: ignore
        )
        return response.status

    def send_software_edge_start_trigger(self):
        """send_software_edge_start_trigger."""
        response = self._invoke(
            self._client.SendSoftwareEdgeStartTrigger,
            grpc_types.SendSoftwareEdgeStartTriggerRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def send_software_edge_advance_trigger(self):
        """send_software_edge_advance_trigger."""
        response = self._invoke(
            self._client.SendSoftwareEdgeAdvanceTrigger,
            grpc_types.SendSoftwareEdgeAdvanceTriggerRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def configure_frequency_reference(
        self, selector_string, frequency_reference_source, frequency_reference_frequency
    ):
        """configure_frequency_reference."""
        response = self._invoke(
            self._client.CfgFrequencyReference,
            grpc_types.CfgFrequencyReferenceRequest(instrument=self._vi, channel_name=selector_string, frequency_reference_source_raw=frequency_reference_source, frequency_reference_frequency=frequency_reference_frequency),  # type: ignore
        )
        return response.status

    def configure_mechanical_attenuation(
        self, selector_string, mechanical_attenuation_auto, mechanical_attenuation_value
    ):
        """configure_mechanical_attenuation."""
        response = self._invoke(
            self._client.CfgMechanicalAttenuation,
            grpc_types.CfgMechanicalAttenuationRequest(instrument=self._vi, channel_name=selector_string, mechanical_attenuation_auto_raw=mechanical_attenuation_auto, mechanical_attenuation_value=mechanical_attenuation_value),  # type: ignore
        )
        return response.status

    def configure_rf_attenuation(self, selector_string, rf_attenuation_auto, rf_attenuation_value):
        """configure_rf_attenuation."""
        response = self._invoke(
            self._client.CfgRFAttenuation,
            grpc_types.CfgRFAttenuationRequest(instrument=self._vi, channel_name=selector_string, rf_attenuation_auto_raw=rf_attenuation_auto, rf_attenuation_value=rf_attenuation_value),  # type: ignore
        )
        return response.status

    def wait_for_acquisition_complete(self, timeout):
        """wait_for_acquisition_complete."""
        response = self._invoke(
            self._client.WaitForAcquisitionComplete,
            grpc_types.WaitForAcquisitionCompleteRequest(instrument=self._vi, timeout=timeout),  # type: ignore
        )
        return response.status

    def reset_to_default(self):
        """reset_to_default."""
        response = self._invoke(
            self._client.ResetToDefault,
            grpc_types.ResetToDefaultRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def reset_driver(self):
        """reset_driver."""
        response = self._invoke(
            self._client.ResetDriver,
            grpc_types.ResetDriverRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def save_all_configurations(self, file_path):
        """save_all_configurations."""
        response = self._invoke(
            self._client.SaveAllConfigurations,
            grpc_types.SaveAllConfigurationsRequest(instrument=self._vi, file_path=file_path),  # type: ignore
        )
        return response.status

    def reset_entire_session(self):
        """reset_entire_session."""
        response = self._invoke(
            self._client.ResetEntireSession,
            grpc_types.ResetEntireSessionRequest(instrument=self._vi),  # type: ignore
        )
        return response.status

    def export_signal(self, export_signal_source, export_signal_output_terminal):
        """export_signal."""
        response = self._invoke(
            self._client.ExportSignal,
            grpc_types.ExportSignalRequest(instrument=self._vi, export_signal_source_raw=export_signal_source, export_signal_output_terminal_raw=export_signal_output_terminal),  # type: ignore
        )
        return response.status

    def self_calibrate(self, selector_string, steps_to_omit):
        """self_calibrate."""
        response = self._invoke(
            self._client.SelfCalibrate,
            grpc_types.SelfCalibrateRequest(instrument=self._vi, selector_string=selector_string, steps_to_omit_raw=steps_to_omit),  # type: ignore
        )
        return response.status

    def self_calibrate_range(
        self,
        selector_string,
        steps_to_omit,
        minimum_frequency,
        maximum_frequency,
        minimum_reference_level,
        maximum_reference_level,
    ):
        """self_calibrate_range."""
        response = self._invoke(
            self._client.SelfCalibrateRange,
            grpc_types.SelfCalibrateRangeRequest(instrument=self._vi, selector_string=selector_string, steps_to_omit_raw=steps_to_omit, minimum_frequency=minimum_frequency, maximum_frequency=maximum_frequency, minimum_reference_level=minimum_reference_level, maximum_reference_level=maximum_reference_level),  # type: ignore
        )
        return response.status

    def load_configurations(self, file_path):
        """load_configurations."""
        response = self._invoke(
            self._client.LoadConfigurations,
            grpc_types.LoadConfigurationsRequest(instrument=self._vi, file_path=file_path),  # type: ignore
        )
        return response.status

    def is_self_calibrate_valid(self, selector_string):
        """is_self_calibrate_valid."""
        response = self._invoke(
            self._client.IsSelfCalibrateValid,
            grpc_types.IsSelfCalibrateValidRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return (
            response.self_calibrate_valid,
            enums.SelfCalibrateSteps(response.valid_steps),
            response.status,
        )

    def reset_attribute(self, selector_string, attribute_id):
        """reset_attribute."""
        response = self._invoke(
            self._client.ResetAttribute,
            grpc_types.ResetAttributeRequest(instrument=self._vi, channel_name=selector_string, attribute_id=attribute_id),  # type: ignore
        )
        return response.status

    def get_s_parameter_external_attenuation_type(self, selector_string):
        """get_s_parameter_external_attenuation_type."""
        response = self._invoke(
            self._client.GetSParameterExternalAttenuationType,
            grpc_types.GetSParameterExternalAttenuationTypeRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return enums.SParameterType(response.s_parameter_type), response.status

    def get_external_attenuation_table_actual_value(self, selector_string):
        """get_external_attenuation_table_actual_value."""
        response = self._invoke(
            self._client.GetExternalAttenuationTableActualValue,
            grpc_types.GetExternalAttenuationTableActualValueRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return response.external_attenuation, response.status

    def get_self_calibrate_last_temperature(self, selector_string, self_calibrate_step):
        """get_self_calibrate_last_temperature."""
        response = self._invoke(
            self._client.GetSelfCalibrateLastTemperature,
            grpc_types.GetSelfCalibrateLastTemperatureRequest(instrument=self._vi, selector_string=selector_string, self_calibrate_step_raw=self_calibrate_step),  # type: ignore
        )
        return response.temperature, response.status

    def get_available_ports(self, selector_string):
        """get_available_ports."""
        response = self._invoke(
            self._client.GetAvailablePorts,
            grpc_types.GetAvailablePortsRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return _helper.split_string_by_comma(response.available_ports), response.status

    def get_available_paths(self, selector_string):
        """get_available_paths."""
        response = self._invoke(
            self._client.GetAvailablePaths,
            grpc_types.GetAvailablePathsRequest(instrument=self._vi, selector_string=selector_string),  # type: ignore
        )
        return _helper.split_string_by_comma(response.available_paths), response.status

    @staticmethod
    def get_session_unique_identifier(resource_name, option_string):
        response = GrpcStubInterpreter._invoke(
            GrpcStubInterpreter._restricted_client.GetSessionUniqueIdentifier,
            restricted_grpc_types.GetSessionUniqueIdentifierRequest(resource_name=resource_name, option_string=option_string),  # type: ignore
        )
        return response.session_unique_identifier, response.status

    def initialize(self, session_name, resource_name, option_string, initialization_behavior):
        response = self._invoke(
            self._client.Initialize,
            grpc_types.InitializeRequest(session_name=session_name, resource_name=resource_name, option_string=option_string, initialization_behavior=initialization_behavior),  # type: ignore
        )
        return response.instrument, response.is_new_session, response.status

    def create_default_signal_configuration(self, signal_name, personality_id):
        response = self._invoke(
            self._restricted_client.CreateDefaultSignalConfiguration,
            restricted_grpc_types.CreateDefaultSignalConfigurationRequest(instrument=self._vi, signal_name=signal_name, personality_id=personality_id),  # type: ignore
        )
        return response.status

    def close(self, force_destroy):
        response = self._invoke(
            self._client.Close,
            grpc_types.CloseRequest(instrument=self._vi, force_destroy=force_destroy),  # type: ignore
        )
        return response.status

    def configure_s_parameter_external_attenuation_table(
        self, selector_string, table_name, frequency, s_parameters, s_parameter_orientation
    ):
        _helper.validate_numpy_array(frequency, "frequency", "float64")
        _helper.validate_numpy_array(s_parameters, "s_parameters", "complex128")
        if s_parameters.shape[0] == s_parameters.shape[1]:
            number_of_ports_proto = s_parameters.shape[1]
        else:
            raise ValueError("sParameters Dimension Mismatch")
        frequency_proto = frequency.flat
        s_parameters_proto = s_parameters.ravel().view(numpy.float64)
        response = self._invoke(
            self._client.CfgSParameterExternalAttenuationTableInterleavedIQ,
            grpc_types.CfgSParameterExternalAttenuationTableInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, table_name=table_name, frequency=frequency_proto, s_parameters=s_parameters_proto, number_of_ports=number_of_ports_proto, s_parameter_orientation=s_parameter_orientation),  # type: ignore
        )
        return response.status

    def get_signal_configuration_names(self, selector_string, personality_filter):
        response = self._invoke(
            self._client.GetSignalConfigurationNames,
            grpc_types.GetSignalConfigurationNamesRequest(instrument=self._vi, selector_string=selector_string, personality_filter=personality_filter),  # type: ignore
        )
        return (
            _helper.split_string_by_comma(response.signal_names),
            response.personality,
            response.status,
        )

    def fetch_raw_iq_data(self, selector_string, timeout, records_to_fetch, samples_to_read, data):
        response = self._invoke(
            self._client.FetchRawIQDataInterleavedIQ,
            grpc_types.FetchRawIQDataInterleavedIQRequest(instrument=self._vi, selector_string=selector_string, timeout=timeout, records_to_fetch=records_to_fetch, samples_to_read=samples_to_read),  # type: ignore
        )
        _helper.validate_numpy_array(data, "data", "complex64")
        if len(data) != response.actual_array_size:
            data.resize((response.actual_array_size,), refcheck=False)
        flat = numpy.array(response.data, dtype=numpy.float32)
        data = flat.view(numpy.complex64)
        return response.x0, response.dx, response.status

    def get_self_calibrate_last_date_and_time(self, selector_string, self_calibrate_step):
        response = self._invoke(
            self._client.GetSelfCalibrateLastDateAndTime,
            grpc_types.GetSelfCalibrateLastDateAndTimeRequest(instrument=self._vi, selector_string=selector_string, self_calibrate_step_raw=self_calibrate_step),  # type: ignore
        )
        from datetime import datetime

        date_time = response.timestamp.ToDatetime()
        return (
            hightime.datetime(
                date_time.year, date_time.month, date_time.day, date_time.hour, date_time.minute
            ),
            response.status,
        )
