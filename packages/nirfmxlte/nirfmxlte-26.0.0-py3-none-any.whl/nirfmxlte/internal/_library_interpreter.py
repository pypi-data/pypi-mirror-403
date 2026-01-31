"""Library C<->Python interpreter.

This class is responsible for interpreting the Library's C API. It is responsible for:
* Converting ctypes to native Python types.
* Dealing with string encoding.
* Allocating memory.
* Converting errors returned by Library into Python exceptions.
"""

import array
import ctypes
import math
from typing import Any

import nirfmxinstr
import nirfmxlte.attributes as attributes
import nirfmxlte.enums as enums
import nirfmxlte.errors as errors
import nirfmxlte.internal._custom_types as _custom_types
import nirfmxlte.internal._helper as _helper
import nirfmxlte.internal._library_singleton as _library_singleton
import numpy


# Helper functions for creating ctypes needed for calling into the driver DLL
def _get_ctypes_pointer_for_buffer(
    value: Any = None, library_type: Any = None, size: Any = None
) -> Any:
    if isinstance(value, array.array):
        assert library_type is not None, "library_type is required for array.array"
        addr, _ = value.buffer_info()
        return ctypes.cast(addr, ctypes.POINTER(library_type))
    elif str(type(value)).find("'numpy.ndarray'") != -1:
        import numpy

        if "complex" in str(value.dtype):
            complex_dtype = numpy.dtype(library_type)
            structured_array = value.view(complex_dtype)
            return structured_array.ctypes.data_as(ctypes.POINTER(library_type))
        else:
            return numpy.ctypeslib.as_ctypes(value)
    elif isinstance(value, bytes):
        return ctypes.cast(value, ctypes.POINTER(library_type))  # type: ignore
    elif isinstance(value, list):
        assert library_type is not None, "library_type is required for list"
        return (library_type * len(value))(*value)
    else:
        if library_type is not None and size is not None:
            return (library_type * size)()
        else:
            return None


def _convert_to_array(value: Any, array_type: Any) -> Any:
    if value is not None:
        if isinstance(value, array.array):
            value_array = value
        else:
            value_array = array.array(array_type, value)
    else:
        value_array = None

    return value_array


class LibraryInterpreter(object):
    """Library C<->Python interpreter.

    This class is responsible for interpreting the Library's C API. It is responsible for:
    * Converting ctypes to native Python types.
    * Dealing with string encoding.
    * Allocating memory.
    * Converting errors returned by Library into Python exceptions.
    """

    _cls_encoding = "windows-1251"
    _cls_library = _library_singleton.get()

    def __init__(self, encoding, session=None, signal_obj=None):
        """Initializes the LibraryInterpreter."""
        self._encoding = encoding
        self._library = _library_singleton.get()
        self._signal_obj = signal_obj
        self._instr_session = session
        # Initialize _vi to 0 for now.
        # Session will directly update it once the driver runtime init function has been called and
        # we have a valid session handle.
        self.set_session_handle()

    def set_session_handle(self, value: Any = 0) -> None:
        """Sets the session handle."""
        self._vi = value

    def get_session_handle(self) -> Any:
        """Returns the session handle."""
        return self._vi

    def get_error_string(self, error_code: int) -> Any:
        """Returns the error message."""
        error_code_ctype = ctypes.c_int32(error_code)
        error_string_ctype = ctypes.create_string_buffer(0)
        size_or_error_code = self._library.RFmxLTE_GetErrorString(
            self._vi, error_code_ctype, 0, None
        )
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxLTE_GetErrorString(
                self._vi, error_code_ctype, size_or_error_code, error_string_ctype
            )
        return error_string_ctype.value.decode(self._encoding)

    def get_error(self) -> tuple[int, Any]:
        """Returns the error code and error message."""
        error_code_ctype = ctypes.c_int32()
        error_string_ctype = ctypes.create_string_buffer(0)
        size_or_error_code = self._library.RFmxLTE_GetError(self._vi, error_code_ctype, 0, None)
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_code_ctype = ctypes.c_int32(error_code_ctype.value)
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxLTE_GetError(
                self._vi, error_code_ctype, size_or_error_code, error_string_ctype
            )
        return error_code_ctype.value, error_string_ctype.value.decode(self._encoding)

    def get_error_description(self, error_code: Any) -> Any:
        """Returns the error description."""
        try:
            returned_error_code, error_string = self.get_error()
            if returned_error_code == error_code:
                return error_string
        except errors.Error:
            pass

        try:
            """
            It is expected for get_error to raise when the session is invalid
            Use get_error_string instead. It doesn't require a session.
            """
            error_string = self.get_error_string(error_code)
            return error_string
        except errors.Error:
            pass
        return "Failed to retrieve error description."

    def reset_attribute(self, selector_string, attribute_id):
        """reset_attribute."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_int32(attribute_id)
        error_code = self._library.RFmxLTE_ResetAttribute(
            vi_ctype, selector_string_ctype, attribute_id_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def check_if_current_signal_exists(self):
        """check_if_current_signal_exists."""
        return_value = False
        if self._signal_obj is not None and not self._signal_obj.signal_configuration_name:
            signal_configuration_exists, local_personality, _ = (
                self._signal_obj._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._signal_obj._default_signal_name_user_visible
                )
            )
            return_value = signal_configuration_exists and (
                local_personality.value == nirfmxinstr.Personalities.LTE.value
            )
        elif self._signal_obj is not None:
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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int8()
        error_code = self._library.RFmxLTE_GetAttributeI8(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_i8(self, selector_string, attribute_id, attr_val):
        """set_attribute_i8."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int8(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeI8(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_i8_array(self, selector_string, attribute_id):
        """get_attribute_i8_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeI8Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.int8)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_int8
        )
        error_code = self._library.RFmxLTE_GetAttributeI8Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_i8_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i8_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="i")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_int8
        )
        error_code = self._library.RFmxLTE_SetAttributeI8Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_i16(self, selector_string, attribute_id):
        """get_attribute_i16."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int16()
        error_code = self._library.RFmxLTE_GetAttributeI16(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_i16(self, selector_string, attribute_id, attr_val):
        """set_attribute_i16."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int16(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeI16(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_i32(self, selector_string, attribute_id):
        """get_attribute_i32."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeI32(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_i32(self, selector_string, attribute_id, attr_val):
        """set_attribute_i32."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int32(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeI32(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_i32_array(self, selector_string, attribute_id):
        """get_attribute_i32_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeI32Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.int32)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_int32
        )
        error_code = self._library.RFmxLTE_GetAttributeI32Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_i32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i32_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="i")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_int32
        )
        error_code = self._library.RFmxLTE_SetAttributeI32Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_i64(self, selector_string, attribute_id):
        """get_attribute_i64."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int64()
        error_code = self._library.RFmxLTE_GetAttributeI64(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_i64(self, selector_string, attribute_id, attr_val):
        """set_attribute_i64."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int64(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeI64(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_i64_array(self, selector_string, attribute_id):
        """get_attribute_i64_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeI64Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.int64)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_int64
        )
        error_code = self._library.RFmxLTE_GetAttributeI64Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_i64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_i64_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="i")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_int64
        )
        error_code = self._library.RFmxLTE_SetAttributeI64Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_u8(self, selector_string, attribute_id):
        """get_attribute_u8."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_uint8()
        error_code = self._library.RFmxLTE_GetAttributeU8(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_u8(self, selector_string, attribute_id, attr_val):
        """set_attribute_u8."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_uint8(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeU8(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_u8_array(self, selector_string, attribute_id):
        """get_attribute_u8_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeU8Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.uint8)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_uint8
        )
        error_code = self._library.RFmxLTE_GetAttributeU8Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_u8_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u8_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="i")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_uint8
        )
        error_code = self._library.RFmxLTE_SetAttributeU8Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_u16(self, selector_string, attribute_id):
        """get_attribute_u16."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_uint16()
        error_code = self._library.RFmxLTE_GetAttributeU16(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_u16(self, selector_string, attribute_id, attr_val):
        """set_attribute_u16."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_uint16(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeU16(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_u32(self, selector_string, attribute_id):
        """get_attribute_u32."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_uint32()
        error_code = self._library.RFmxLTE_GetAttributeU32(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_u32(self, selector_string, attribute_id, attr_val):
        """set_attribute_u32."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_uint32(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeU32(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_u32_array(self, selector_string, attribute_id):
        """get_attribute_u32_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeU32Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.uint32)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_uint32
        )
        error_code = self._library.RFmxLTE_GetAttributeU32Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_u32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u32_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="i")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_uint32
        )
        error_code = self._library.RFmxLTE_SetAttributeU32Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_u64_array(self, selector_string, attribute_id):
        """get_attribute_u64_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeU64Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.uint64)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_uint64
        )
        error_code = self._library.RFmxLTE_GetAttributeU64Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_u64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_u64_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="i")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_uint64
        )
        error_code = self._library.RFmxLTE_SetAttributeU64Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_f32(self, selector_string, attribute_id):
        """get_attribute_f32."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_float()
        error_code = self._library.RFmxLTE_GetAttributeF32(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_f32(self, selector_string, attribute_id, attr_val):
        """set_attribute_f32."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_float(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeF32(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_f32_array(self, selector_string, attribute_id):
        """get_attribute_f32_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeF32Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.float32)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_float
        )
        error_code = self._library.RFmxLTE_GetAttributeF32Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_f32_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_f32_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="f")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_float
        )
        error_code = self._library.RFmxLTE_SetAttributeF32Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_f64(self, selector_string, attribute_id):
        """get_attribute_f64."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_GetAttributeF64(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            None if attr_val_ctype is None else (ctypes.pointer(attr_val_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value, error_code

    def set_attribute_f64(self, selector_string, attribute_id, attr_val):
        """set_attribute_f64."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_double(attr_val)
        error_code = self._library.RFmxLTE_SetAttributeF64(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_f64_array(self, selector_string, attribute_id):
        """get_attribute_f64_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeF64Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.float64)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_double
        )
        error_code = self._library.RFmxLTE_GetAttributeF64Array(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_f64_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_f64_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="d")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_double
        )
        error_code = self._library.RFmxLTE_SetAttributeF64Array(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_nicomplexsingle_array(self, selector_string, attribute_id):
        """get_attribute_nicomplexsingle_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeNIComplexSingleArray(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.complex64)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_float
        )
        error_code = self._library.RFmxLTE_GetAttributeNIComplexSingleArray(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_nicomplexsingle_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_nicomplexsingle_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_float
        )
        error_code = self._library.RFmxLTE_SetAttributeNIComplexSingleArray(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_nicomplexdouble_array(self, selector_string, attribute_id):
        """get_attribute_nicomplexdouble_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = None
        array_size_ctype = ctypes.c_int32()
        actual_array_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_GetAttributeNIComplexDoubleArray(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            array_size_ctype,
            None if actual_array_size_ctype is None else (ctypes.pointer(actual_array_size_ctype)),
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        attr_val_array = numpy.empty(actual_array_size_ctype.value, dtype=numpy.complex128)
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_double
        )
        error_code = self._library.RFmxLTE_GetAttributeNIComplexDoubleArray(
            vi_ctype,
            selector_string_ctype,
            attribute_id_ctype,
            attr_val_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_array, error_code

    def set_attribute_nicomplexdouble_array(self, selector_string, attribute_id, attr_val):
        """set_attribute_nicomplexdouble_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_array = _convert_to_array(value=attr_val, array_type="")
        attr_val_ctype = _get_ctypes_pointer_for_buffer(
            value=attr_val_array, library_type=ctypes.c_double
        )
        error_code = self._library.RFmxLTE_SetAttributeNIComplexDoubleArray(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype, len(attr_val)
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_attribute_string(self, selector_string, attribute_id):
        """get_attribute_string."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        array_size_ctype = ctypes.c_int32(0)
        attr_val_ctype = None
        size_or_error_code = self._library.RFmxLTE_GetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, array_size_ctype, attr_val_ctype
        )
        if size_or_error_code < 0:
            errors.handle_error(
                self, size_or_error_code, ignore_warnings=True, is_error_handling=False
            )
            return None, size_or_error_code
        array_size_ctype = ctypes.c_int32(size_or_error_code)
        attr_val_ctype = (ctypes.c_char * array_size_ctype.value)()
        error_code = self._library.RFmxLTE_GetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, array_size_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return attr_val_ctype.value.decode(self._encoding), error_code

    def set_attribute_string(self, selector_string, attribute_id, attr_val):
        """set_attribute_string."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.create_string_buffer(attr_val.encode(self._encoding))
        error_code = self._library.RFmxLTE_SetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_validate_noise_calibration_data(self, selector_string):
        """acp_validate_noise_calibration_data."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_calibration_data_valid_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_ACPValidateNoiseCalibrationData(
            vi_ctype, selector_string_ctype, noise_calibration_data_valid_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.AcpNoiseCalibrationDataValid(noise_calibration_data_valid_ctype.value),
            error_code,
        )

    def chp_validate_noise_calibration_data(self, selector_string):
        """chp_validate_noise_calibration_data."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_calibration_data_valid_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_CHPValidateNoiseCalibrationData(
            vi_ctype, selector_string_ctype, noise_calibration_data_valid_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.ChpNoiseCalibrationDataValid(noise_calibration_data_valid_ctype.value),
            error_code,
        )

    def abort_measurements(self, selector_string):
        """abort_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_AbortMeasurements(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_level(self, selector_string, measurement_interval):
        """auto_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_interval_ctype = ctypes.c_double(measurement_interval)
        reference_level_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_AutoLevel(
            vi_ctype, selector_string_ctype, measurement_interval_ctype, reference_level_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return reference_level_ctype.value, error_code

    def check_measurement_status(self, selector_string):
        """check_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        is_done_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_CheckMeasurementStatus(
            vi_ctype, selector_string_ctype, is_done_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return bool(is_done_ctype.value), error_code

    def clear_all_named_results(self, selector_string):
        """clear_all_named_results."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_ClearAllNamedResults(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def clear_named_result(self, selector_string):
        """clear_named_result."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_ClearNamedResult(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def commit(self, selector_string):
        """commit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_Commit(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_digital_edge_trigger(
        self, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        """configure_digital_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        digital_edge_source_ctype = ctypes.create_string_buffer(
            digital_edge_source.encode(self._encoding)
        )
        digital_edge_ctype = ctypes.c_int32(digital_edge)
        trigger_delay_ctype = ctypes.c_double(trigger_delay)
        enable_trigger_ctype = ctypes.c_int32(enable_trigger)
        error_code = self._library.RFmxLTE_CfgDigitalEdgeTrigger(
            vi_ctype,
            selector_string_ctype,
            digital_edge_source_ctype,
            digital_edge_ctype,
            trigger_delay_ctype,
            enable_trigger_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency_earfcn(self, selector_string, link_direction, band, earfcn):
        """configure_frequency_earfcn."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        link_direction_ctype = ctypes.c_int32(link_direction)
        band_ctype = ctypes.c_int32(band)
        earfcn_ctype = ctypes.c_int32(earfcn)
        error_code = self._library.RFmxLTE_CfgFrequencyEARFCN(
            vi_ctype, selector_string_ctype, link_direction_ctype, band_ctype, earfcn_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        iq_power_edge_source_ctype = ctypes.create_string_buffer(
            iq_power_edge_source.encode(self._encoding)
        )
        iq_power_edge_slope_ctype = ctypes.c_int32(iq_power_edge_slope)
        iq_power_edge_level_ctype = ctypes.c_double(iq_power_edge_level)
        trigger_delay_ctype = ctypes.c_double(trigger_delay)
        trigger_min_quiet_time_mode_ctype = ctypes.c_int32(trigger_min_quiet_time_mode)
        trigger_min_quiet_time_duration_ctype = ctypes.c_double(trigger_min_quiet_time_duration)
        iq_power_edge_level_type_ctype = ctypes.c_int32(iq_power_edge_level_type)
        enable_trigger_ctype = ctypes.c_int32(enable_trigger)
        error_code = self._library.RFmxLTE_CfgIQPowerEdgeTrigger(
            vi_ctype,
            selector_string_ctype,
            iq_power_edge_source_ctype,
            iq_power_edge_slope_ctype,
            iq_power_edge_level_ctype,
            trigger_delay_ctype,
            trigger_min_quiet_time_mode_ctype,
            trigger_min_quiet_time_duration_ctype,
            iq_power_edge_level_type_ctype,
            enable_trigger_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        """configure_software_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        trigger_delay_ctype = ctypes.c_double(trigger_delay)
        enable_trigger_ctype = ctypes.c_int32(enable_trigger)
        error_code = self._library.RFmxLTE_CfgSoftwareEdgeTrigger(
            vi_ctype, selector_string_ctype, trigger_delay_ctype, enable_trigger_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def create_list_step(self, selector_string):
        """create_list_step."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        created_step_index_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_CreateListStep(
            vi_ctype, selector_string_ctype, created_step_index_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return created_step_index_ctype.value, error_code

    def create_list(self, list_name):
        """create_list."""
        vi_ctype = ctypes.c_uint32(self._vi)
        list_name_ctype = ctypes.create_string_buffer(list_name.encode(self._encoding))
        error_code = self._library.RFmxLTE_CreateList(vi_ctype, list_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def create_signal_configuration(self, signal_name):
        """create_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(signal_name.encode(self._encoding))
        error_code = self._library.RFmxLTE_CreateSignalConfiguration(vi_ctype, signal_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def delete_list(self, list_name):
        """delete_list."""
        vi_ctype = ctypes.c_uint32(self._vi)
        list_name_ctype = ctypes.create_string_buffer(list_name.encode(self._encoding))
        error_code = self._library.RFmxLTE_DeleteList(vi_ctype, list_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def disable_trigger(self, selector_string):
        """disable_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_DisableTrigger(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def initiate(self, selector_string, result_name):
        """initiate."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        error_code = self._library.RFmxLTE_Initiate(
            vi_ctype, selector_string_ctype, result_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def reset_to_default(self, selector_string):
        """reset_to_default."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_ResetToDefault(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def select_measurements(self, selector_string, measurements, enable_all_traces):
        """select_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurements_ctype = ctypes.c_uint32(measurements)
        enable_all_traces_ctype = ctypes.c_int32(enable_all_traces)
        error_code = self._library.RFmxLTE_SelectMeasurements(
            vi_ctype, selector_string_ctype, measurements_ctype, enable_all_traces_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def wait_for_measurement_complete(self, selector_string, timeout):
        """wait_for_measurement_complete."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxLTE_WaitForMeasurementComplete(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """acp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        averaging_type_ctype = ctypes.c_int32(averaging_type)
        error_code = self._library.RFmxLTE_ACPCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_configurable_number_of_offsets_enabled(
        self, selector_string, configurable_number_of_offsets_enabled
    ):
        """acp_configure_configurable_number_of_offsets_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        configurable_number_of_offsets_enabled_ctype = ctypes.c_int32(
            configurable_number_of_offsets_enabled
        )
        error_code = self._library.RFmxLTE_ACPCfgConfigurableNumberOfOffsetsEnabled(
            vi_ctype, selector_string_ctype, configurable_number_of_offsets_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_measurement_method(self, selector_string, measurement_method):
        """acp_configure_measurement_method."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_method_ctype = ctypes.c_int32(measurement_method)
        error_code = self._library.RFmxLTE_ACPCfgMeasurementMethod(
            vi_ctype, selector_string_ctype, measurement_method_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        """acp_configure_noise_compensation_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_compensation_enabled_ctype = ctypes.c_int32(noise_compensation_enabled)
        error_code = self._library.RFmxLTE_ACPCfgNoiseCompensationEnabled(
            vi_ctype, selector_string_ctype, noise_compensation_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_eutra_offsets(self, selector_string, number_of_eutra_offsets):
        """acp_configure_number_of_eutra_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_eutra_offsets_ctype = ctypes.c_int32(number_of_eutra_offsets)
        error_code = self._library.RFmxLTE_ACPCfgNumberOfEUTRAOffsets(
            vi_ctype, selector_string_ctype, number_of_eutra_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_gsm_offsets(self, selector_string, number_of_gsm_offsets):
        """acp_configure_number_of_gsm_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_gsm_offsets_ctype = ctypes.c_int32(number_of_gsm_offsets)
        error_code = self._library.RFmxLTE_ACPCfgNumberOfGSMOffsets(
            vi_ctype, selector_string_ctype, number_of_gsm_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_utra_offsets(self, selector_string, number_of_utra_offsets):
        """acp_configure_number_of_utra_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_utra_offsets_ctype = ctypes.c_int32(number_of_utra_offsets)
        error_code = self._library.RFmxLTE_ACPCfgNumberOfUTRAOffsets(
            vi_ctype, selector_string_ctype, number_of_utra_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """acp_configure_rbw_filter."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        rbw_auto_ctype = ctypes.c_int32(rbw_auto)
        rbw_ctype = ctypes.c_double(rbw)
        rbw_filter_type_ctype = ctypes.c_int32(rbw_filter_type)
        error_code = self._library.RFmxLTE_ACPCfgRBWFilter(
            vi_ctype, selector_string_ctype, rbw_auto_ctype, rbw_ctype, rbw_filter_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """acp_configure_sweep_time."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        sweep_time_auto_ctype = ctypes.c_int32(sweep_time_auto)
        sweep_time_interval_ctype = ctypes.c_double(sweep_time_interval)
        error_code = self._library.RFmxLTE_ACPCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_utra_and_eutra_offsets(
        self, selector_string, number_of_utra_offsets, number_of_eutra_offsets
    ):
        """acp_configure_utra_and_eutra_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_utra_offsets_ctype = ctypes.c_int32(number_of_utra_offsets)
        number_of_eutra_offsets_ctype = ctypes.c_int32(number_of_eutra_offsets)
        error_code = self._library.RFmxLTE_ACPCfgUTRAAndEUTRAOffsets(
            vi_ctype,
            selector_string_ctype,
            number_of_utra_offsets_ctype,
            number_of_eutra_offsets_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_power_units(self, selector_string, power_units):
        """acp_configure_power_units."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        power_units_ctype = ctypes.c_int32(power_units)
        error_code = self._library.RFmxLTE_ACPCfgPowerUnits(
            vi_ctype, selector_string_ctype, power_units_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def chp_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """chp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        averaging_type_ctype = ctypes.c_int32(averaging_type)
        error_code = self._library.RFmxLTE_CHPCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def chp_configure_integration_bandwidth_type(self, selector_string, integration_bandwidth_type):
        """chp_configure_integration_bandwidth_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        integration_bandwidth_type_ctype = ctypes.c_int32(integration_bandwidth_type)
        error_code = self._library.RFmxLTE_CHPCfgIntegrationBandwidthType(
            vi_ctype, selector_string_ctype, integration_bandwidth_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def chp_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """chp_configure_rbw_filter."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        rbw_auto_ctype = ctypes.c_int32(rbw_auto)
        rbw_ctype = ctypes.c_double(rbw)
        rbw_filter_type_ctype = ctypes.c_int32(rbw_filter_type)
        error_code = self._library.RFmxLTE_CHPCfgRBWFilter(
            vi_ctype, selector_string_ctype, rbw_auto_ctype, rbw_ctype, rbw_filter_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def chp_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """chp_configure_sweep_time."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        sweep_time_auto_ctype = ctypes.c_int32(sweep_time_auto)
        sweep_time_interval_ctype = ctypes.c_double(sweep_time_interval)
        error_code = self._library.RFmxLTE_CHPCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """modacc_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxLTE_ModAccCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_common_clock_source_enabled(
        self, selector_string, common_clock_source_enabled
    ):
        """modacc_configure_common_clock_source_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        common_clock_source_enabled_ctype = ctypes.c_int32(common_clock_source_enabled)
        error_code = self._library.RFmxLTE_ModAccCfgCommonClockSourceEnabled(
            vi_ctype, selector_string_ctype, common_clock_source_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_evm_unit(self, selector_string, evm_unit):
        """modacc_configure_evm_unit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        evm_unit_ctype = ctypes.c_int32(evm_unit)
        error_code = self._library.RFmxLTE_ModAccCfgEVMUnit(
            vi_ctype, selector_string_ctype, evm_unit_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_fft_window_offset(self, selector_string, fft_window_offset):
        """modacc_configure_fft_window_offset."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        fft_window_offset_ctype = ctypes.c_double(fft_window_offset)
        error_code = self._library.RFmxLTE_ModAccCfgFFTWindowOffset(
            vi_ctype, selector_string_ctype, fft_window_offset_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_fft_window_position(
        self, selector_string, fft_window_type, fft_window_offset, fft_window_length
    ):
        """modacc_configure_fft_window_position."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        fft_window_type_ctype = ctypes.c_int32(fft_window_type)
        fft_window_offset_ctype = ctypes.c_double(fft_window_offset)
        fft_window_length_ctype = ctypes.c_double(fft_window_length)
        error_code = self._library.RFmxLTE_ModAccCfgFFTWindowPosition(
            vi_ctype,
            selector_string_ctype,
            fft_window_type_ctype,
            fft_window_offset_ctype,
            fft_window_length_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_in_band_emission_mask_type(
        self, selector_string, in_band_emission_mask_type
    ):
        """modacc_configure_in_band_emission_mask_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        in_band_emission_mask_type_ctype = ctypes.c_int32(in_band_emission_mask_type)
        error_code = self._library.RFmxLTE_ModAccCfgInBandEmissionMaskType(
            vi_ctype, selector_string_ctype, in_band_emission_mask_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_synchronization_mode_and_interval(
        self, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        """modacc_configure_synchronization_mode_and_interval."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        synchronization_mode_ctype = ctypes.c_int32(synchronization_mode)
        measurement_offset_ctype = ctypes.c_int32(measurement_offset)
        measurement_length_ctype = ctypes.c_int32(measurement_length)
        error_code = self._library.RFmxLTE_ModAccCfgSynchronizationModeAndInterval(
            vi_ctype,
            selector_string_ctype,
            synchronization_mode_ctype,
            measurement_offset_ctype,
            measurement_length_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def obw_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """obw_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        averaging_type_ctype = ctypes.c_int32(averaging_type)
        error_code = self._library.RFmxLTE_OBWCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def obw_configure_rbw_filter(self, selector_string, rbw_auto, rbw, rbw_filter_type):
        """obw_configure_rbw_filter."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        rbw_auto_ctype = ctypes.c_int32(rbw_auto)
        rbw_ctype = ctypes.c_double(rbw)
        rbw_filter_type_ctype = ctypes.c_int32(rbw_filter_type)
        error_code = self._library.RFmxLTE_OBWCfgRBWFilter(
            vi_ctype, selector_string_ctype, rbw_auto_ctype, rbw_ctype, rbw_filter_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def obw_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """obw_configure_sweep_time."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        sweep_time_auto_ctype = ctypes.c_int32(sweep_time_auto)
        sweep_time_interval_ctype = ctypes.c_double(sweep_time_interval)
        error_code = self._library.RFmxLTE_OBWCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """sem_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        averaging_type_ctype = ctypes.c_int32(averaging_type)
        error_code = self._library.RFmxLTE_SEMCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_maximum_output_power_array(
        self, selector_string, component_carrier_maximum_output_power
    ):
        """sem_configure_maximum_output_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_maximum_output_power_ctype = _get_ctypes_pointer_for_buffer(
            value=component_carrier_maximum_output_power, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(component_carrier_maximum_output_power)
            if component_carrier_maximum_output_power is not None
            else 0
        )
        error_code = self._library.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPowerArray(
            vi_ctype,
            selector_string_ctype,
            component_carrier_maximum_output_power_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_maximum_output_power(
        self, selector_string, component_carrier_maximum_output_power
    ):
        """sem_configure_maximum_output_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_maximum_output_power_ctype = ctypes.c_double(
            component_carrier_maximum_output_power
        )
        error_code = self._library.RFmxLTE_SEMCfgComponentCarrierMaximumOutputPower(
            vi_ctype, selector_string_ctype, component_carrier_maximum_output_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_downlink_mask(
        self, selector_string, downlink_mask_type, delta_f_maximum, aggregated_maximum_power
    ):
        """sem_configure_downlink_mask."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        downlink_mask_type_ctype = ctypes.c_int32(downlink_mask_type)
        delta_f_maximum_ctype = ctypes.c_double(delta_f_maximum)
        aggregated_maximum_power_ctype = ctypes.c_double(aggregated_maximum_power)
        error_code = self._library.RFmxLTE_SEMCfgDownlinkMask(
            vi_ctype,
            selector_string_ctype,
            downlink_mask_type_ctype,
            delta_f_maximum_ctype,
            aggregated_maximum_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """sem_configure_number_of_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_offsets_ctype = ctypes.c_int32(number_of_offsets)
        error_code = self._library.RFmxLTE_SEMCfgNumberOfOffsets(
            vi_ctype, selector_string_ctype, number_of_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_absolute_limit_array(
        self, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_absolute_limit_start_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_absolute_limit_start, library_type=ctypes.c_double
        )
        offset_absolute_limit_stop_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_absolute_limit_stop, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["offset_absolute_limit_start", "offset_absolute_limit_stop"],
                offset_absolute_limit_start,
                offset_absolute_limit_stop,
            )
        )
        error_code = self._library.RFmxLTE_SEMCfgOffsetAbsoluteLimitArray(
            vi_ctype,
            selector_string_ctype,
            offset_absolute_limit_start_ctype,
            offset_absolute_limit_stop_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_absolute_limit(
        self, selector_string, offset_absolute_limit_start, offset_absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_absolute_limit_start_ctype = ctypes.c_double(offset_absolute_limit_start)
        offset_absolute_limit_stop_ctype = ctypes.c_double(offset_absolute_limit_stop)
        error_code = self._library.RFmxLTE_SEMCfgOffsetAbsoluteLimit(
            vi_ctype,
            selector_string_ctype,
            offset_absolute_limit_start_ctype,
            offset_absolute_limit_stop_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_bandwidth_integral_array(
        self, selector_string, offset_bandwidth_integral
    ):
        """sem_configure_offset_bandwidth_integral_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_bandwidth_integral_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_bandwidth_integral, library_type=ctypes.c_int32
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(offset_bandwidth_integral) if offset_bandwidth_integral is not None else 0
        )
        error_code = self._library.RFmxLTE_SEMCfgOffsetBandwidthIntegralArray(
            vi_ctype,
            selector_string_ctype,
            offset_bandwidth_integral_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_bandwidth_integral(self, selector_string, offset_bandwidth_integral):
        """sem_configure_offset_bandwidth_integral."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_bandwidth_integral_ctype = ctypes.c_int32(offset_bandwidth_integral)
        error_code = self._library.RFmxLTE_SEMCfgOffsetBandwidthIntegral(
            vi_ctype, selector_string_ctype, offset_bandwidth_integral_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_frequency_array(
        self, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        """sem_configure_offset_frequency_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_start_frequency_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_start_frequency, library_type=ctypes.c_double
        )
        offset_stop_frequency_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_stop_frequency, library_type=ctypes.c_double
        )
        offset_sideband_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_sideband, library_type=ctypes.c_int32
        )
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["offset_start_frequency", "offset_stop_frequency", "offset_sideband"],
                offset_start_frequency,
                offset_stop_frequency,
                offset_sideband,
            )
        )
        error_code = self._library.RFmxLTE_SEMCfgOffsetFrequencyArray(
            vi_ctype,
            selector_string_ctype,
            offset_start_frequency_ctype,
            offset_stop_frequency_ctype,
            offset_sideband_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_frequency(
        self, selector_string, offset_start_frequency, offset_stop_frequency, offset_sideband
    ):
        """sem_configure_offset_frequency."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_start_frequency_ctype = ctypes.c_double(offset_start_frequency)
        offset_stop_frequency_ctype = ctypes.c_double(offset_stop_frequency)
        offset_sideband_ctype = ctypes.c_int32(offset_sideband)
        error_code = self._library.RFmxLTE_SEMCfgOffsetFrequency(
            vi_ctype,
            selector_string_ctype,
            offset_start_frequency_ctype,
            offset_stop_frequency_ctype,
            offset_sideband_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_limit_fail_mask_array(self, selector_string, limit_fail_mask):
        """sem_configure_offset_limit_fail_mask_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        limit_fail_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=limit_fail_mask, library_type=ctypes.c_int32
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(limit_fail_mask) if limit_fail_mask is not None else 0
        )
        error_code = self._library.RFmxLTE_SEMCfgOffsetLimitFailMaskArray(
            vi_ctype, selector_string_ctype, limit_fail_mask_ctype, number_of_elements_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_limit_fail_mask(self, selector_string, limit_fail_mask):
        """sem_configure_offset_limit_fail_mask."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        limit_fail_mask_ctype = ctypes.c_int32(limit_fail_mask)
        error_code = self._library.RFmxLTE_SEMCfgOffsetLimitFailMask(
            vi_ctype, selector_string_ctype, limit_fail_mask_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_rbw_filter_array(
        self, selector_string, offset_rbw, offset_rbw_filter_type
    ):
        """sem_configure_offset_rbw_filter_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_rbw_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_rbw, library_type=ctypes.c_double
        )
        offset_rbw_filter_type_ctype = _get_ctypes_pointer_for_buffer(
            value=offset_rbw_filter_type, library_type=ctypes.c_int32
        )
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["offset_rbw", "offset_rbw_filter_type"], offset_rbw, offset_rbw_filter_type
            )
        )
        error_code = self._library.RFmxLTE_SEMCfgOffsetRBWFilterArray(
            vi_ctype,
            selector_string_ctype,
            offset_rbw_ctype,
            offset_rbw_filter_type_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_rbw_filter(self, selector_string, offset_rbw, offset_rbw_filter_type):
        """sem_configure_offset_rbw_filter."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_rbw_ctype = ctypes.c_double(offset_rbw)
        offset_rbw_filter_type_ctype = ctypes.c_int32(offset_rbw_filter_type)
        error_code = self._library.RFmxLTE_SEMCfgOffsetRBWFilter(
            vi_ctype, selector_string_ctype, offset_rbw_ctype, offset_rbw_filter_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_relative_limit_array(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        relative_limit_start_ctype = _get_ctypes_pointer_for_buffer(
            value=relative_limit_start, library_type=ctypes.c_double
        )
        relative_limit_stop_ctype = _get_ctypes_pointer_for_buffer(
            value=relative_limit_stop, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["relative_limit_start", "relative_limit_stop"],
                relative_limit_start,
                relative_limit_stop,
            )
        )
        error_code = self._library.RFmxLTE_SEMCfgOffsetRelativeLimitArray(
            vi_ctype,
            selector_string_ctype,
            relative_limit_start_ctype,
            relative_limit_stop_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_relative_limit(
        self, selector_string, relative_limit_start, relative_limit_stop
    ):
        """sem_configure_offset_relative_limit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        relative_limit_start_ctype = ctypes.c_double(relative_limit_start)
        relative_limit_stop_ctype = ctypes.c_double(relative_limit_stop)
        error_code = self._library.RFmxLTE_SEMCfgOffsetRelativeLimit(
            vi_ctype, selector_string_ctype, relative_limit_start_ctype, relative_limit_stop_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """sem_configure_sweep_time."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        sweep_time_auto_ctype = ctypes.c_int32(sweep_time_auto)
        sweep_time_interval_ctype = ctypes.c_double(sweep_time_interval)
        error_code = self._library.RFmxLTE_SEMCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_uplink_mask_type(self, selector_string, uplink_mask_type):
        """sem_configure_uplink_mask_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        uplink_mask_type_ctype = ctypes.c_int32(uplink_mask_type)
        error_code = self._library.RFmxLTE_SEMCfgUplinkMaskType(
            vi_ctype, selector_string_ctype, uplink_mask_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def pvt_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count, averaging_type
    ):
        """pvt_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        averaging_type_ctype = ctypes.c_int32(averaging_type)
        error_code = self._library.RFmxLTE_PVTCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def pvt_configure_measurement_method(self, selector_string, measurement_method):
        """pvt_configure_measurement_method."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_method_ctype = ctypes.c_int32(measurement_method)
        error_code = self._library.RFmxLTE_PVTCfgMeasurementMethod(
            vi_ctype, selector_string_ctype, measurement_method_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def pvt_configure_off_power_exclusion_periods(
        self, selector_string, off_power_exclusion_before, off_power_exclusion_after
    ):
        """pvt_configure_off_power_exclusion_periods."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        off_power_exclusion_before_ctype = ctypes.c_double(off_power_exclusion_before)
        off_power_exclusion_after_ctype = ctypes.c_double(off_power_exclusion_after)
        error_code = self._library.RFmxLTE_PVTCfgOFFPowerExclusionPeriods(
            vi_ctype,
            selector_string_ctype,
            off_power_exclusion_before_ctype,
            off_power_exclusion_after_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def slotphase_configure_synchronization_mode_and_interval(
        self, selector_string, synchronization_mode, measurement_offset, measurement_length
    ):
        """slotphase_configure_synchronization_mode_and_interval."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        synchronization_mode_ctype = ctypes.c_int32(synchronization_mode)
        measurement_offset_ctype = ctypes.c_int32(measurement_offset)
        measurement_length_ctype = ctypes.c_int32(measurement_length)
        error_code = self._library.RFmxLTE_SlotPhaseCfgSynchronizationModeAndInterval(
            vi_ctype,
            selector_string_ctype,
            synchronization_mode_ctype,
            measurement_offset_ctype,
            measurement_length_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def slotpower_configure_measurement_interval(
        self, selector_string, measurement_offset, measurement_length
    ):
        """slotpower_configure_measurement_interval."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_offset_ctype = ctypes.c_int32(measurement_offset)
        measurement_length_ctype = ctypes.c_int32(measurement_length)
        error_code = self._library.RFmxLTE_SlotPowerCfgMeasurementInterval(
            vi_ctype, selector_string_ctype, measurement_offset_ctype, measurement_length_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """txp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxLTE_TXPCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_measurement_offset_and_interval(
        self, selector_string, measurement_offset, measurement_interval
    ):
        """txp_configure_measurement_offset_and_interval."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_offset_ctype = ctypes.c_double(measurement_offset)
        measurement_interval_ctype = ctypes.c_double(measurement_interval)
        error_code = self._library.RFmxLTE_TXPCfgMeasurementOffsetAndInterval(
            vi_ctype, selector_string_ctype, measurement_offset_ctype, measurement_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_auto_dmrs_detection_enabled(self, selector_string, auto_dmrs_detection_enabled):
        """configure_auto_dmrs_detection_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        auto_dmrs_detection_enabled_ctype = ctypes.c_int32(auto_dmrs_detection_enabled)
        error_code = self._library.RFmxLTE_CfgAutoDMRSDetectionEnabled(
            vi_ctype, selector_string_ctype, auto_dmrs_detection_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_auto_npusch_channel_detection_enabled(
        self, selector_string, auto_npusch_channel_detection_enabled
    ):
        """configure_auto_npusch_channel_detection_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        auto_npusch_channel_detection_enabled_ctype = ctypes.c_int32(
            auto_npusch_channel_detection_enabled
        )
        error_code = self._library.RFmxLTE_CfgAutoNPUSCHChannelDetectionEnabled(
            vi_ctype, selector_string_ctype, auto_npusch_channel_detection_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_auto_resource_block_detection_enabled(
        self, selector_string, auto_resource_block_detection_enabled
    ):
        """configure_auto_resource_block_detection_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        auto_resource_block_detection_enabled_ctype = ctypes.c_int32(
            auto_resource_block_detection_enabled
        )
        error_code = self._library.RFmxLTE_CfgAutoResourceBlockDetectionEnabled(
            vi_ctype, selector_string_ctype, auto_resource_block_detection_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_band(self, selector_string, band):
        """configure_band."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        band_ctype = ctypes.c_int32(band)
        error_code = self._library.RFmxLTE_CfgBand(vi_ctype, selector_string_ctype, band_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_cell_specific_ratio(self, selector_string, cell_specific_ratio):
        """configure_cell_specific_ratio."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        cell_specific_ratio_ctype = ctypes.c_int32(cell_specific_ratio)
        error_code = self._library.RFmxLTE_CfgCellSpecificRatio(
            vi_ctype, selector_string_ctype, cell_specific_ratio_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_array(
        self, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        """configure_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_bandwidth_ctype = _get_ctypes_pointer_for_buffer(
            value=component_carrier_bandwidth, library_type=ctypes.c_double
        )
        component_carrier_frequency_ctype = _get_ctypes_pointer_for_buffer(
            value=component_carrier_frequency, library_type=ctypes.c_double
        )
        cell_id_ctype = _get_ctypes_pointer_for_buffer(value=cell_id, library_type=ctypes.c_int32)
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["component_carrier_bandwidth", "component_carrier_frequency", "cell_id"],
                component_carrier_bandwidth,
                component_carrier_frequency,
                cell_id,
            )
        )
        error_code = self._library.RFmxLTE_CfgComponentCarrierArray(
            vi_ctype,
            selector_string_ctype,
            component_carrier_bandwidth_ctype,
            component_carrier_frequency_ctype,
            cell_id_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_spacing(
        self, selector_string, component_carrier_spacing_type, component_carrier_at_center_frequency
    ):
        """configure_spacing."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_spacing_type_ctype = ctypes.c_int32(component_carrier_spacing_type)
        component_carrier_at_center_frequency_ctype = ctypes.c_int32(
            component_carrier_at_center_frequency
        )
        error_code = self._library.RFmxLTE_CfgComponentCarrierSpacing(
            vi_ctype,
            selector_string_ctype,
            component_carrier_spacing_type_ctype,
            component_carrier_at_center_frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure(
        self, selector_string, component_carrier_bandwidth, component_carrier_frequency, cell_id
    ):
        """configure."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_bandwidth_ctype = ctypes.c_double(component_carrier_bandwidth)
        component_carrier_frequency_ctype = ctypes.c_double(component_carrier_frequency)
        cell_id_ctype = ctypes.c_int32(cell_id)
        error_code = self._library.RFmxLTE_CfgComponentCarrier(
            vi_ctype,
            selector_string_ctype,
            component_carrier_bandwidth_ctype,
            component_carrier_frequency_ctype,
            cell_id_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_auto_cell_id_detection_enabled(
        self, selector_string, auto_cell_id_detection_enabled
    ):
        """configure_downlink_auto_cell_id_detection_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        auto_cell_id_detection_enabled_ctype = ctypes.c_int32(auto_cell_id_detection_enabled)
        error_code = self._library.RFmxLTE_CfgDownlinkAutoCellIDDetectionEnabled(
            vi_ctype, selector_string_ctype, auto_cell_id_detection_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_channel_configuration_mode(
        self, selector_string, channel_configuration_mode
    ):
        """configure_downlink_channel_configuration_mode."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        channel_configuration_mode_ctype = ctypes.c_int32(channel_configuration_mode)
        error_code = self._library.RFmxLTE_CfgDownlinkChannelConfigurationMode(
            vi_ctype, selector_string_ctype, channel_configuration_mode_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_number_of_subframes(self, selector_string, number_of_subframes):
        """configure_downlink_number_of_subframes."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_subframes_ctype = ctypes.c_int32(number_of_subframes)
        error_code = self._library.RFmxLTE_CfgDownlinkNumberOfSubframes(
            vi_ctype, selector_string_ctype, number_of_subframes_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_synchronization_signal(self, selector_string, pss_power, sss_power):
        """configure_downlink_synchronization_signal."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        pss_power_ctype = ctypes.c_double(pss_power)
        sss_power_ctype = ctypes.c_double(sss_power)
        error_code = self._library.RFmxLTE_CfgDownlinkSynchronizationSignal(
            vi_ctype, selector_string_ctype, pss_power_ctype, sss_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_test_model_array(self, selector_string, downlink_test_model):
        """configure_downlink_test_model_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        downlink_test_model_ctype = _get_ctypes_pointer_for_buffer(
            value=downlink_test_model, library_type=ctypes.c_int32
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(downlink_test_model) if downlink_test_model is not None else 0
        )
        error_code = self._library.RFmxLTE_CfgDownlinkTestModelArray(
            vi_ctype, selector_string_ctype, downlink_test_model_ctype, number_of_elements_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_test_model(self, selector_string, downlink_test_model):
        """configure_downlink_test_model."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        downlink_test_model_ctype = ctypes.c_int32(downlink_test_model)
        error_code = self._library.RFmxLTE_CfgDownlinkTestModel(
            vi_ctype, selector_string_ctype, downlink_test_model_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_duplex_scheme(
        self, selector_string, duplex_scheme, uplink_downlink_configuration
    ):
        """configure_duplex_scheme."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        duplex_scheme_ctype = ctypes.c_int32(duplex_scheme)
        uplink_downlink_configuration_ctype = ctypes.c_int32(uplink_downlink_configuration)
        error_code = self._library.RFmxLTE_CfgDuplexScheme(
            vi_ctype,
            selector_string_ctype,
            duplex_scheme_ctype,
            uplink_downlink_configuration_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_emtc_analysis_enabled(self, selector_string, emtc_analysis_enabled):
        """configure_emtc_analysis_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        emtc_analysis_enabled_ctype = ctypes.c_int32(emtc_analysis_enabled)
        error_code = self._library.RFmxLTE_CfgEMTCAnalysisEnabled(
            vi_ctype, selector_string_ctype, emtc_analysis_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_enodeb_category(self, selector_string, enodeb_category):
        """configure_enodeb_category."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        enodeb_category_ctype = ctypes.c_int32(enodeb_category)
        error_code = self._library.RFmxLTE_CfgeNodeBCategory(
            vi_ctype, selector_string_ctype, enodeb_category_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_external_attenuation(self, selector_string, external_attenuation):
        """configure_external_attenuation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        external_attenuation_ctype = ctypes.c_double(external_attenuation)
        error_code = self._library.RFmxLTE_CfgExternalAttenuation(
            vi_ctype, selector_string_ctype, external_attenuation_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency(self, selector_string, center_frequency):
        """configure_frequency."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        center_frequency_ctype = ctypes.c_double(center_frequency)
        error_code = self._library.RFmxLTE_CfgFrequency(
            vi_ctype, selector_string_ctype, center_frequency_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_link_direction(self, selector_string, link_direction):
        """configure_link_direction."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        link_direction_ctype = ctypes.c_int32(link_direction)
        error_code = self._library.RFmxLTE_CfgLinkDirection(
            vi_ctype, selector_string_ctype, link_direction_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_nb_iot_component_carrier(
        self, selector_string, n_cell_id, uplink_subcarrier_spacing
    ):
        """configure_nb_iot_component_carrier."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        n_cell_id_ctype = ctypes.c_int32(n_cell_id)
        uplink_subcarrier_spacing_ctype = ctypes.c_int32(uplink_subcarrier_spacing)
        error_code = self._library.RFmxLTE_CfgNBIoTComponentCarrier(
            vi_ctype, selector_string_ctype, n_cell_id_ctype, uplink_subcarrier_spacing_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        npusch_dmrs_base_sequence_mode_ctype = ctypes.c_int32(npusch_dmrs_base_sequence_mode)
        npusch_dmrs_base_sequence_index_ctype = ctypes.c_int32(npusch_dmrs_base_sequence_index)
        npusch_dmrs_cyclic_shift_ctype = ctypes.c_int32(npusch_dmrs_cyclic_shift)
        npusch_dmrs_group_hopping_enabled_ctype = ctypes.c_int32(npusch_dmrs_group_hopping_enabled)
        npusch_dmrs_delta_ss_ctype = ctypes.c_int32(npusch_dmrs_delta_ss)
        error_code = self._library.RFmxLTE_CfgNPUSCHDMRS(
            vi_ctype,
            selector_string_ctype,
            npusch_dmrs_base_sequence_mode_ctype,
            npusch_dmrs_base_sequence_index_ctype,
            npusch_dmrs_cyclic_shift_ctype,
            npusch_dmrs_group_hopping_enabled_ctype,
            npusch_dmrs_delta_ss_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_npusch_format(self, selector_string, format):
        """configure_npusch_format."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        format_ctype = ctypes.c_int32(format)
        error_code = self._library.RFmxLTE_CfgNPUSCHFormat(
            vi_ctype, selector_string_ctype, format_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_npusch_starting_slot(self, selector_string, starting_slot):
        """configure_npusch_starting_slot."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        starting_slot_ctype = ctypes.c_int32(starting_slot)
        error_code = self._library.RFmxLTE_CfgNPUSCHStartingSlot(
            vi_ctype, selector_string_ctype, starting_slot_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_npusch_tones(
        self, selector_string, tone_offset, number_of_tones, modulation_type
    ):
        """configure_npusch_tones."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        tone_offset_ctype = ctypes.c_int32(tone_offset)
        number_of_tones_ctype = ctypes.c_int32(number_of_tones)
        modulation_type_ctype = ctypes.c_int32(modulation_type)
        error_code = self._library.RFmxLTE_CfgNPUSCHTones(
            vi_ctype,
            selector_string_ctype,
            tone_offset_ctype,
            number_of_tones_ctype,
            modulation_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_number_of_component_carriers(self, selector_string, number_of_component_carriers):
        """configure_number_of_component_carriers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_component_carriers_ctype = ctypes.c_int32(number_of_component_carriers)
        error_code = self._library.RFmxLTE_CfgNumberOfComponentCarriers(
            vi_ctype, selector_string_ctype, number_of_component_carriers_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_number_of_dut_antennas(self, selector_string, number_of_dut_antennas):
        """configure_number_of_dut_antennas."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_dut_antennas_ctype = ctypes.c_int32(number_of_dut_antennas)
        error_code = self._library.RFmxLTE_CfgNumberOfDUTAntennas(
            vi_ctype, selector_string_ctype, number_of_dut_antennas_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_number_of_pdsch_channels(self, selector_string, number_of_pdsch_channels):
        """configure_number_of_pdsch_channels."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_pdsch_channels_ctype = ctypes.c_int32(number_of_pdsch_channels)
        error_code = self._library.RFmxLTE_CfgNumberOfPDSCHChannels(
            vi_ctype, selector_string_ctype, number_of_pdsch_channels_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_number_of_pusch_resource_block_clusters(
        self, selector_string, number_of_resource_block_clusters
    ):
        """configure_number_of_pusch_resource_block_clusters."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_resource_block_clusters_ctype = ctypes.c_int32(number_of_resource_block_clusters)
        error_code = self._library.RFmxLTE_CfgNumberOfPUSCHResourceBlockClusters(
            vi_ctype, selector_string_ctype, number_of_resource_block_clusters_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_number_of_subblocks(self, selector_string, number_of_subblocks):
        """configure_number_of_subblocks."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_subblocks_ctype = ctypes.c_int32(number_of_subblocks)
        error_code = self._library.RFmxLTE_CfgNumberOfSubblocks(
            vi_ctype, selector_string_ctype, number_of_subblocks_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pbch(self, selector_string, pbch_power):
        """configure_pbch."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        pbch_power_ctype = ctypes.c_double(pbch_power)
        error_code = self._library.RFmxLTE_CfgPBCH(
            vi_ctype, selector_string_ctype, pbch_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pcfich(self, selector_string, cfi, power):
        """configure_pcfich."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        cfi_ctype = ctypes.c_int32(cfi)
        power_ctype = ctypes.c_double(power)
        error_code = self._library.RFmxLTE_CfgPCFICH(
            vi_ctype, selector_string_ctype, cfi_ctype, power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pdcch(self, selector_string, pdcch_power):
        """configure_pdcch."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        pdcch_power_ctype = ctypes.c_double(pdcch_power)
        error_code = self._library.RFmxLTE_CfgPDCCH(
            vi_ctype, selector_string_ctype, pdcch_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pdsch(
        self, selector_string, cw0_modulation_type, resource_block_allocation, power
    ):
        """configure_pdsch."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        cw0_modulation_type_ctype = ctypes.c_int32(cw0_modulation_type)
        resource_block_allocation_ctype = ctypes.create_string_buffer(
            resource_block_allocation.encode(self._encoding)
        )
        power_ctype = ctypes.c_double(power)
        error_code = self._library.RFmxLTE_CfgPDSCH(
            vi_ctype,
            selector_string_ctype,
            cw0_modulation_type_ctype,
            resource_block_allocation_ctype,
            power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_phich(self, selector_string, resource, duration, power):
        """configure_phich."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        resource_ctype = ctypes.c_int32(resource)
        duration_ctype = ctypes.c_int32(duration)
        power_ctype = ctypes.c_double(power)
        error_code = self._library.RFmxLTE_CfgPHICH(
            vi_ctype, selector_string_ctype, resource_ctype, duration_ctype, power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pssch_modulation_type(self, selector_string, modulation_type):
        """configure_pssch_modulation_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        modulation_type_ctype = ctypes.c_int32(modulation_type)
        error_code = self._library.RFmxLTE_CfgPSSCHModulationType(
            vi_ctype, selector_string_ctype, modulation_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pssch_resource_blocks(
        self, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        """configure_pssch_resource_blocks."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        resource_block_offset_ctype = ctypes.c_int32(resource_block_offset)
        number_of_resource_blocks_ctype = ctypes.c_int32(number_of_resource_blocks)
        error_code = self._library.RFmxLTE_CfgPSSCHResourceBlocks(
            vi_ctype,
            selector_string_ctype,
            resource_block_offset_ctype,
            number_of_resource_blocks_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pusch_modulation_type(self, selector_string, modulation_type):
        """configure_pusch_modulation_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        modulation_type_ctype = ctypes.c_int32(modulation_type)
        error_code = self._library.RFmxLTE_CfgPUSCHModulationType(
            vi_ctype, selector_string_ctype, modulation_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_pusch_resource_blocks(
        self, selector_string, resource_block_offset, number_of_resource_blocks
    ):
        """configure_pusch_resource_blocks."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        resource_block_offset_ctype = ctypes.c_int32(resource_block_offset)
        number_of_resource_blocks_ctype = ctypes.c_int32(number_of_resource_blocks)
        error_code = self._library.RFmxLTE_CfgPUSCHResourceBlocks(
            vi_ctype,
            selector_string_ctype,
            resource_block_offset_ctype,
            number_of_resource_blocks_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_reference_level(self, selector_string, reference_level):
        """configure_reference_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        reference_level_ctype = ctypes.c_double(reference_level)
        error_code = self._library.RFmxLTE_CfgReferenceLevel(
            vi_ctype, selector_string_ctype, reference_level_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_rf(
        self, selector_string, center_frequency, reference_level, external_attenuation
    ):
        """configure_rf."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        center_frequency_ctype = ctypes.c_double(center_frequency)
        reference_level_ctype = ctypes.c_double(reference_level)
        external_attenuation_ctype = ctypes.c_double(external_attenuation)
        error_code = self._library.RFmxLTE_CfgRF(
            vi_ctype,
            selector_string_ctype,
            center_frequency_ctype,
            reference_level_ctype,
            external_attenuation_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_transmit_antenna_to_analyze(self, selector_string, transmit_antenna_to_analyze):
        """configure_transmit_antenna_to_analyze."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        transmit_antenna_to_analyze_ctype = ctypes.c_int32(transmit_antenna_to_analyze)
        error_code = self._library.RFmxLTE_CfgTransmitAntennaToAnalyze(
            vi_ctype, selector_string_ctype, transmit_antenna_to_analyze_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_fetch_measurement(self, selector_string, timeout):
        """acp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_power_ctype = ctypes.c_double()
        relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ACPFetchComponentCarrierMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_power_ctype.value, relative_power_ctype.value, error_code

    def acp_fetch_offset_measurement(self, selector_string, timeout):
        """acp_fetch_offset_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        lower_relative_power_ctype = ctypes.c_double()
        upper_relative_power_ctype = ctypes.c_double()
        lower_absolute_power_ctype = ctypes.c_double()
        upper_absolute_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ACPFetchOffsetMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            lower_relative_power_ctype,
            upper_relative_power_ctype,
            lower_absolute_power_ctype,
            upper_absolute_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            lower_relative_power_ctype.value,
            upper_relative_power_ctype.value,
            lower_absolute_power_ctype.value,
            upper_absolute_power_ctype.value,
            error_code,
        )

    def acp_fetch_subblock_measurement(self, selector_string, timeout):
        """acp_fetch_subblock_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_power_ctype = ctypes.c_double()
        integration_bandwidth_ctype = ctypes.c_double()
        frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ACPFetchSubblockMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subblock_power_ctype,
            integration_bandwidth_ctype,
            frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            subblock_power_ctype.value,
            integration_bandwidth_ctype.value,
            frequency_ctype.value,
            error_code,
        )

    def acp_fetch_total_aggregated_power(self, selector_string, timeout):
        """acp_fetch_total_aggregated_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        total_aggregated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ACPFetchTotalAggregatedPower(
            vi_ctype, selector_string_ctype, timeout_ctype, total_aggregated_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return total_aggregated_power_ctype.value, error_code

    def chp_fetch_measurement(self, selector_string, timeout):
        """chp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_power_ctype = ctypes.c_double()
        relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_CHPFetchComponentCarrierMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_power_ctype.value, relative_power_ctype.value, error_code

    def chp_fetch_subblock_measurement(self, selector_string, timeout):
        """chp_fetch_subblock_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_power_ctype = ctypes.c_double()
        integration_bandwidth_ctype = ctypes.c_double()
        frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_CHPFetchSubblockMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subblock_power_ctype,
            integration_bandwidth_ctype,
            frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            subblock_power_ctype.value,
            integration_bandwidth_ctype.value,
            frequency_ctype.value,
            error_code,
        )

    def chp_fetch_total_aggregated_power(self, selector_string, timeout):
        """chp_fetch_total_aggregated_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        total_aggregated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_CHPFetchTotalAggregatedPower(
            vi_ctype, selector_string_ctype, timeout_ctype, total_aggregated_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return total_aggregated_power_ctype.value, error_code

    def modacc_fetch_composite_evm(self, selector_string, timeout):
        """modacc_fetch_composite_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_composite_evm_ctype = ctypes.c_double()
        maximum_peak_composite_evm_ctype = ctypes.c_double()
        mean_frequency_error_ctype = ctypes.c_double()
        peak_composite_evm_symbol_index_ctype = ctypes.c_int32()
        peak_composite_evm_subcarrier_index_ctype = ctypes.c_int32()
        peak_composite_evm_slot_index_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_ModAccFetchCompositeEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_composite_evm_ctype,
            maximum_peak_composite_evm_ctype,
            mean_frequency_error_ctype,
            peak_composite_evm_symbol_index_ctype,
            peak_composite_evm_subcarrier_index_ctype,
            peak_composite_evm_slot_index_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_rms_composite_evm_ctype.value,
            maximum_peak_composite_evm_ctype.value,
            mean_frequency_error_ctype.value,
            peak_composite_evm_symbol_index_ctype.value,
            peak_composite_evm_subcarrier_index_ctype.value,
            peak_composite_evm_slot_index_ctype.value,
            error_code,
        )

    def modacc_fetch_composite_magnitude_and_phase_error(self, selector_string, timeout):
        """modacc_fetch_composite_magnitude_and_phase_error."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_composite_magnitude_error_ctype = ctypes.c_double()
        maximum_peak_composite_magnitude_error_ctype = ctypes.c_double()
        mean_rms_composite_phase_error_ctype = ctypes.c_double()
        maximum_peak_composite_phase_error_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseError(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_composite_magnitude_error_ctype,
            maximum_peak_composite_magnitude_error_ctype,
            mean_rms_composite_phase_error_ctype,
            maximum_peak_composite_phase_error_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_rms_composite_magnitude_error_ctype.value,
            maximum_peak_composite_magnitude_error_ctype.value,
            mean_rms_composite_phase_error_ctype.value,
            maximum_peak_composite_phase_error_ctype.value,
            error_code,
        )

    def modacc_fetch_csrs_evm(self, selector_string, timeout):
        """modacc_fetch_csrs_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_csrs_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchCSRSEVM(
            vi_ctype, selector_string_ctype, timeout_ctype, mean_rms_csrs_evm_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_csrs_evm_ctype.value, error_code

    def modacc_fetch_downlink_detected_cell_id(self, selector_string, timeout):
        """modacc_fetch_downlink_detected_cell_id."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        detected_cell_id_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkDetectedCellID(
            vi_ctype, selector_string_ctype, timeout_ctype, detected_cell_id_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return detected_cell_id_ctype.value, error_code

    def modacc_fetch_downlink_transmit_power(self, selector_string, timeout):
        """modacc_fetch_downlink_transmit_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rs_transmit_power_ctype = ctypes.c_double()
        ofdm_symbol_transmit_power_ctype = ctypes.c_double()
        reserved_1_ctype = ctypes.c_double()
        reserved_2_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkTransmitPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rs_transmit_power_ctype,
            ofdm_symbol_transmit_power_ctype,
            reserved_1_ctype,
            reserved_2_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rs_transmit_power_ctype.value,
            ofdm_symbol_transmit_power_ctype.value,
            reserved_1_ctype.value,
            reserved_2_ctype.value,
            error_code,
        )

    def modacc_fetch_in_band_emission_margin(self, selector_string, timeout):
        """modacc_fetch_in_band_emission_margin."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        in_band_emission_margin_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchInBandEmissionMargin(
            vi_ctype, selector_string_ctype, timeout_ctype, in_band_emission_margin_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return in_band_emission_margin_ctype.value, error_code

    def modacc_fetch_iq_impairments(self, selector_string, timeout):
        """modacc_fetch_iq_impairments."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_iq_origin_offset_ctype = ctypes.c_double()
        mean_iq_gain_imbalance_ctype = ctypes.c_double()
        mean_iq_quadrature_error_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchIQImpairments(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_iq_origin_offset_ctype,
            mean_iq_gain_imbalance_ctype,
            mean_iq_quadrature_error_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_iq_origin_offset_ctype.value,
            mean_iq_gain_imbalance_ctype.value,
            mean_iq_quadrature_error_ctype.value,
            error_code,
        )

    def modacc_fetch_npusch_data_evm(self, selector_string, timeout):
        """modacc_fetch_npusch_data_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        npusch_mean_rms_data_evm_ctype = ctypes.c_double()
        npusch_maximum_peak_data_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchNPUSCHDataEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            npusch_mean_rms_data_evm_ctype,
            npusch_maximum_peak_data_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            npusch_mean_rms_data_evm_ctype.value,
            npusch_maximum_peak_data_evm_ctype.value,
            error_code,
        )

    def modacc_fetch_npusch_dmrs_evm(self, selector_string, timeout):
        """modacc_fetch_npusch_dmrs_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        npusch_mean_rms_dmrs_evm_ctype = ctypes.c_double()
        npusch_maximum_peak_dmrs_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchNPUSCHDMRSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            npusch_mean_rms_dmrs_evm_ctype,
            npusch_maximum_peak_dmrs_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            npusch_mean_rms_dmrs_evm_ctype.value,
            npusch_maximum_peak_dmrs_evm_ctype.value,
            error_code,
        )

    def modacc_fetch_npusch_symbol_power(self, selector_string, timeout):
        """modacc_fetch_npusch_symbol_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        npusch_mean_data_power_ctype = ctypes.c_double()
        npusch_mean_dmrs_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchNPUSCHSymbolPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            npusch_mean_data_power_ctype,
            npusch_mean_dmrs_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return npusch_mean_data_power_ctype.value, npusch_mean_dmrs_power_ctype.value, error_code

    def modacc_fetch_pdsc_1024_qam_evm(self, selector_string, timeout):
        """modacc_fetch_pdsc_1024_qam_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_1024qam_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH1024QAMEVM(
            vi_ctype, selector_string_ctype, timeout_ctype, mean_rms_1024qam_evm_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_1024qam_evm_ctype.value, error_code

    def modacc_fetch_pdsch_evm(self, selector_string, timeout):
        """modacc_fetch_pdsch_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_evm_ctype = ctypes.c_double()
        mean_rms_qpsk_evm_ctype = ctypes.c_double()
        mean_rms_16qam_evm_ctype = ctypes.c_double()
        mean_rms_64qam_evm_ctype = ctypes.c_double()
        mean_rms_256qam_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPDSCHEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_evm_ctype,
            mean_rms_qpsk_evm_ctype,
            mean_rms_16qam_evm_ctype,
            mean_rms_64qam_evm_ctype,
            mean_rms_256qam_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_rms_evm_ctype.value,
            mean_rms_qpsk_evm_ctype.value,
            mean_rms_16qam_evm_ctype.value,
            mean_rms_64qam_evm_ctype.value,
            mean_rms_256qam_evm_ctype.value,
            error_code,
        )

    def modacc_fetch_pssch_data_evm(self, selector_string, timeout):
        """modacc_fetch_pssch_data_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pssch_mean_rms_data_evm_ctype = ctypes.c_double()
        pssch_maximum_peak_data_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHDataEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pssch_mean_rms_data_evm_ctype,
            pssch_maximum_peak_data_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            pssch_mean_rms_data_evm_ctype.value,
            pssch_maximum_peak_data_evm_ctype.value,
            error_code,
        )

    def modacc_fetch_pssch_dmrs_evm(self, selector_string, timeout):
        """modacc_fetch_pssch_dmrs_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pssch_mean_rms_dmrs_evm_ctype = ctypes.c_double()
        pssch_maximum_peak_dmrs_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHDMRSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pssch_mean_rms_dmrs_evm_ctype,
            pssch_maximum_peak_dmrs_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            pssch_mean_rms_dmrs_evm_ctype.value,
            pssch_maximum_peak_dmrs_evm_ctype.value,
            error_code,
        )

    def modacc_fetch_pssch_symbol_power(self, selector_string, timeout):
        """modacc_fetch_pssch_symbol_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pssch_mean_data_power_ctype = ctypes.c_double()
        pssch_mean_dmrs_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHSymbolPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pssch_mean_data_power_ctype,
            pssch_mean_dmrs_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pssch_mean_data_power_ctype.value, pssch_mean_dmrs_power_ctype.value, error_code

    def modacc_fetch_pusch_data_evm(self, selector_string, timeout):
        """modacc_fetch_pusch_data_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_data_evm_ctype = ctypes.c_double()
        maximum_peak_data_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDataEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_data_evm_ctype,
            maximum_peak_data_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_data_evm_ctype.value, maximum_peak_data_evm_ctype.value, error_code

    def modacc_fetch_pusch_dmrs_evm(self, selector_string, timeout):
        """modacc_fetch_pusch_dmrs_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_dmrs_evm_ctype = ctypes.c_double()
        maximum_peak_dmrs_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDMRSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_dmrs_evm_ctype,
            maximum_peak_dmrs_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_dmrs_evm_ctype.value, maximum_peak_dmrs_evm_ctype.value, error_code

    def modacc_fetch_pusch_symbol_power(self, selector_string, timeout):
        """modacc_fetch_pusch_symbol_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pusch_mean_data_power_ctype = ctypes.c_double()
        pusch_mean_dmrs_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHSymbolPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pusch_mean_data_power_ctype,
            pusch_mean_dmrs_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pusch_mean_data_power_ctype.value, pusch_mean_dmrs_power_ctype.value, error_code

    def modacc_fetch_spectral_flatness(self, selector_string, timeout):
        """modacc_fetch_spectral_flatness."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        range1_maximum_to_range1_minimum_ctype = ctypes.c_double()
        range2_maximum_to_range2_minimum_ctype = ctypes.c_double()
        range1_maximum_to_range2_minimum_ctype = ctypes.c_double()
        range2_maximum_to_range1_minimum_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchSpectralFlatness(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            range1_maximum_to_range1_minimum_ctype,
            range2_maximum_to_range2_minimum_ctype,
            range1_maximum_to_range2_minimum_ctype,
            range2_maximum_to_range1_minimum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            range1_maximum_to_range1_minimum_ctype.value,
            range2_maximum_to_range2_minimum_ctype.value,
            range1_maximum_to_range2_minimum_ctype.value,
            range2_maximum_to_range1_minimum_ctype.value,
            error_code,
        )

    def modacc_fetch_srs_evm(self, selector_string, timeout):
        """modacc_fetch_srs_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_srs_evm_ctype = ctypes.c_double()
        mean_srs_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchSRSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_srs_evm_ctype,
            mean_srs_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_srs_evm_ctype.value, mean_srs_power_ctype.value, error_code

    def modacc_fetch_subblock_in_band_emission_margin(self, selector_string, timeout):
        """modacc_fetch_subblock_in_band_emission_margin."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_in_band_emission_margin_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchSubblockInBandEmissionMargin(
            vi_ctype, selector_string_ctype, timeout_ctype, subblock_in_band_emission_margin_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return subblock_in_band_emission_margin_ctype.value, error_code

    def modacc_fetch_subblock_iq_impairments(self, selector_string, timeout):
        """modacc_fetch_subblock_iq_impairments."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_mean_iq_origin_offset_ctype = ctypes.c_double()
        subblock_mean_iq_gain_imbalance_ctype = ctypes.c_double()
        subblock_mean_iq_quadrature_error_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchSubblockIQImpairments(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subblock_mean_iq_origin_offset_ctype,
            subblock_mean_iq_gain_imbalance_ctype,
            subblock_mean_iq_quadrature_error_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            subblock_mean_iq_origin_offset_ctype.value,
            subblock_mean_iq_gain_imbalance_ctype.value,
            subblock_mean_iq_quadrature_error_ctype.value,
            error_code,
        )

    def modacc_fetch_synchronization_signal_evm(self, selector_string, timeout):
        """modacc_fetch_synchronization_signal_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mean_rms_pss_evm_ctype = ctypes.c_double()
        mean_rms_sss_evm_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_ModAccFetchSynchronizationSignalEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_pss_evm_ctype,
            mean_rms_sss_evm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_pss_evm_ctype.value, mean_rms_sss_evm_ctype.value, error_code

    def obw_fetch_measurement(self, selector_string, timeout):
        """obw_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        occupied_bandwidth_ctype = ctypes.c_double()
        absolute_power_ctype = ctypes.c_double()
        start_frequency_ctype = ctypes.c_double()
        stop_frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_OBWFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            occupied_bandwidth_ctype,
            absolute_power_ctype,
            start_frequency_ctype,
            stop_frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            occupied_bandwidth_ctype.value,
            absolute_power_ctype.value,
            start_frequency_ctype.value,
            stop_frequency_ctype.value,
            error_code,
        )

    def sem_fetch_measurement(self, selector_string, timeout):
        """sem_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_integrated_power_ctype = ctypes.c_double()
        relative_integrated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchComponentCarrierMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_integrated_power_ctype,
            relative_integrated_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_integrated_power_ctype.value,
            relative_integrated_power_ctype.value,
            error_code,
        )

    def sem_fetch_lower_offset_margin(self, selector_string, timeout):
        """sem_fetch_lower_offset_margin."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        margin_ctype = ctypes.c_double()
        margin_frequency_ctype = ctypes.c_double()
        margin_absolute_power_ctype = ctypes.c_double()
        margin_relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchLowerOffsetMargin(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            margin_ctype,
            margin_frequency_ctype,
            margin_absolute_power_ctype,
            margin_relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.SemLowerOffsetMeasurementStatus(measurement_status_ctype.value),
            margin_ctype.value,
            margin_frequency_ctype.value,
            margin_absolute_power_ctype.value,
            margin_relative_power_ctype.value,
            error_code,
        )

    def sem_fetch_lower_offset_power(self, selector_string, timeout):
        """sem_fetch_lower_offset_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_integrated_power_ctype = ctypes.c_double()
        relative_integrated_power_ctype = ctypes.c_double()
        absolute_peak_power_ctype = ctypes.c_double()
        peak_frequency_ctype = ctypes.c_double()
        relative_peak_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchLowerOffsetPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_integrated_power_ctype,
            relative_integrated_power_ctype,
            absolute_peak_power_ctype,
            peak_frequency_ctype,
            relative_peak_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_integrated_power_ctype.value,
            relative_integrated_power_ctype.value,
            absolute_peak_power_ctype.value,
            peak_frequency_ctype.value,
            relative_peak_power_ctype.value,
            error_code,
        )

    def sem_fetch_measurement_status(self, selector_string, timeout):
        """sem_fetch_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxLTE_SEMFetchMeasurementStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, measurement_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.SemMeasurementStatus(measurement_status_ctype.value), error_code

    def sem_fetch_subblock_measurement(self, selector_string, timeout):
        """sem_fetch_subblock_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_power_ctype = ctypes.c_double()
        integration_bandwidth_ctype = ctypes.c_double()
        frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchSubblockMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subblock_power_ctype,
            integration_bandwidth_ctype,
            frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            subblock_power_ctype.value,
            integration_bandwidth_ctype.value,
            frequency_ctype.value,
            error_code,
        )

    def sem_fetch_total_aggregated_power(self, selector_string, timeout):
        """sem_fetch_total_aggregated_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        total_aggregated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchTotalAggregatedPower(
            vi_ctype, selector_string_ctype, timeout_ctype, total_aggregated_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return total_aggregated_power_ctype.value, error_code

    def sem_fetch_upper_offset_margin(self, selector_string, timeout):
        """sem_fetch_upper_offset_margin."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        margin_ctype = ctypes.c_double()
        margin_frequency_ctype = ctypes.c_double()
        margin_absolute_power_ctype = ctypes.c_double()
        margin_relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchUpperOffsetMargin(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            margin_ctype,
            margin_frequency_ctype,
            margin_absolute_power_ctype,
            margin_relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.SemUpperOffsetMeasurementStatus(measurement_status_ctype.value),
            margin_ctype.value,
            margin_frequency_ctype.value,
            margin_absolute_power_ctype.value,
            margin_relative_power_ctype.value,
            error_code,
        )

    def sem_fetch_upper_offset_power(self, selector_string, timeout):
        """sem_fetch_upper_offset_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_integrated_power_ctype = ctypes.c_double()
        relative_integrated_power_ctype = ctypes.c_double()
        absolute_peak_power_ctype = ctypes.c_double()
        peak_frequency_ctype = ctypes.c_double()
        relative_peak_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SEMFetchUpperOffsetPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_integrated_power_ctype,
            relative_integrated_power_ctype,
            absolute_peak_power_ctype,
            peak_frequency_ctype,
            relative_peak_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_integrated_power_ctype.value,
            relative_integrated_power_ctype.value,
            absolute_peak_power_ctype.value,
            peak_frequency_ctype.value,
            relative_peak_power_ctype.value,
            error_code,
        )

    def pvt_fetch_measurement(self, selector_string, timeout):
        """pvt_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        mean_absolute_off_power_before_ctype = ctypes.c_double()
        mean_absolute_off_power_after_ctype = ctypes.c_double()
        mean_absolute_on_power_ctype = ctypes.c_double()
        burst_width_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_PVTFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            mean_absolute_off_power_before_ctype,
            mean_absolute_off_power_after_ctype,
            mean_absolute_on_power_ctype,
            burst_width_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.PvtMeasurementStatus(measurement_status_ctype.value),
            mean_absolute_off_power_before_ctype.value,
            mean_absolute_off_power_after_ctype.value,
            mean_absolute_on_power_ctype.value,
            burst_width_ctype.value,
            error_code,
        )

    def slotphase_fetch_maximum_phase_discontinuity(self, selector_string, timeout):
        """slotphase_fetch_maximum_phase_discontinuity."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        maximum_phase_discontinuity_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuity(
            vi_ctype, selector_string_ctype, timeout_ctype, maximum_phase_discontinuity_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return maximum_phase_discontinuity_ctype.value, error_code

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        average_power_mean_ctype = ctypes.c_double()
        peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxLTE_TXPFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_power_mean_ctype,
            peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return average_power_mean_ctype.value, peak_power_maximum_ctype.value, error_code

    def acp_fetch_absolute_powers_trace(
        self, selector_string, timeout, trace_index, absolute_powers_trace
    ):
        """acp_fetch_absolute_powers_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        trace_index_ctype = ctypes.c_int32(trace_index)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ACPFetchAbsolutePowersTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            trace_index_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(absolute_powers_trace, "absolute_powers_trace", "float32")
        if len(absolute_powers_trace) != actual_array_size_ctype.value:
            absolute_powers_trace.resize((actual_array_size_ctype.value,), refcheck=False)
        absolute_powers_trace_ctype = _get_ctypes_pointer_for_buffer(
            value=absolute_powers_trace, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ACPFetchAbsolutePowersTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            trace_index_ctype,
            x0_ctype,
            dx_ctype,
            absolute_powers_trace_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def acp_fetch_measurement_array(self, selector_string, timeout):
        """acp_fetch_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ACPFetchComponentCarrierMeasurementArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ACPFetchComponentCarrierMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_power_ctype[:], relative_power_ctype[:], error_code

    def acp_fetch_offset_measurement_array(self, selector_string, timeout):
        """acp_fetch_offset_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ACPFetchOffsetMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        lower_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        upper_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        lower_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        upper_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ACPFetchOffsetMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            lower_relative_power_ctype,
            upper_relative_power_ctype,
            lower_absolute_power_ctype,
            upper_absolute_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            lower_relative_power_ctype[:],
            upper_relative_power_ctype[:],
            lower_absolute_power_ctype[:],
            upper_absolute_power_ctype[:],
            error_code,
        )

    def acp_fetch_relative_powers_trace(
        self, selector_string, timeout, trace_index, relative_powers_trace
    ):
        """acp_fetch_relative_powers_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        trace_index_ctype = ctypes.c_int32(trace_index)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ACPFetchRelativePowersTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            trace_index_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(relative_powers_trace, "relative_powers_trace", "float32")
        if len(relative_powers_trace) != actual_array_size_ctype.value:
            relative_powers_trace.resize((actual_array_size_ctype.value,), refcheck=False)
        relative_powers_trace_ctype = _get_ctypes_pointer_for_buffer(
            value=relative_powers_trace, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ACPFetchRelativePowersTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            trace_index_ctype,
            x0_ctype,
            dx_ctype,
            relative_powers_trace_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def acp_fetch_spectrum(self, selector_string, timeout, spectrum):
        """acp_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ACPFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != actual_array_size_ctype.value:
            spectrum.resize((actual_array_size_ctype.value,), refcheck=False)
        spectrum_ctype = _get_ctypes_pointer_for_buffer(value=spectrum, library_type=ctypes.c_float)

        # call library function again to get array
        error_code = self._library.RFmxLTE_ACPFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            spectrum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def chp_fetch_measurement_array(self, selector_string, timeout):
        """chp_fetch_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_CHPFetchComponentCarrierMeasurementArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_CHPFetchComponentCarrierMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_power_ctype[:], relative_power_ctype[:], error_code

    def chp_fetch_spectrum(self, selector_string, timeout, spectrum):
        """chp_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_CHPFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != actual_array_size_ctype.value:
            spectrum.resize((actual_array_size_ctype.value,), refcheck=False)
        spectrum_ctype = _get_ctypes_pointer_for_buffer(value=spectrum, library_type=ctypes.c_float)

        # call library function again to get array
        error_code = self._library.RFmxLTE_CHPFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            spectrum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_composite_evm_array(self, selector_string, timeout):
        """modacc_fetch_composite_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchCompositeEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_composite_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        maximum_peak_composite_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_frequency_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_composite_evm_symbol_index_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )
        peak_composite_evm_subcarrier_index_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )
        peak_composite_evm_slot_index_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchCompositeEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_composite_evm_ctype,
            maximum_peak_composite_evm_ctype,
            mean_frequency_error_ctype,
            peak_composite_evm_symbol_index_ctype,
            peak_composite_evm_subcarrier_index_ctype,
            peak_composite_evm_slot_index_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_rms_composite_evm_ctype[:],
            maximum_peak_composite_evm_ctype[:],
            mean_frequency_error_ctype[:],
            peak_composite_evm_symbol_index_ctype[:],
            peak_composite_evm_subcarrier_index_ctype[:],
            peak_composite_evm_slot_index_ctype[:],
            error_code,
        )

    def modacc_fetch_composite_magnitude_and_phase_error_array(self, selector_string, timeout):
        """modacc_fetch_composite_magnitude_and_phase_error_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_composite_magnitude_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        maximum_peak_composite_magnitude_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_rms_composite_phase_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        maximum_peak_composite_phase_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchCompositeMagnitudeAndPhaseErrorArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_composite_magnitude_error_ctype,
            maximum_peak_composite_magnitude_error_ctype,
            mean_rms_composite_phase_error_ctype,
            maximum_peak_composite_phase_error_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_rms_composite_magnitude_error_ctype[:],
            maximum_peak_composite_magnitude_error_ctype[:],
            mean_rms_composite_phase_error_ctype[:],
            maximum_peak_composite_phase_error_ctype[:],
            error_code,
        )

    def modacc_fetch_csrs_constellation(self, selector_string, timeout, csrs_constellation):
        """modacc_fetch_csrs_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchCSRSConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(csrs_constellation, "csrs_constellation", "complex64")
        if len(csrs_constellation) != actual_array_size_ctype.value:
            csrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        csrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=csrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchCSRSConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            csrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_csrs_evm_array(self, selector_string, timeout):
        """modacc_fetch_csrs_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchCSRSEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_csrs_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchCSRSEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_csrs_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_csrs_evm_ctype[:], error_code

    def modacc_fetch_downlink_detected_cell_id_array(self, selector_string, timeout):
        """modacc_fetch_downlink_detected_cell_id_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        detected_cell_id_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkDetectedCellIDArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            detected_cell_id_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return detected_cell_id_ctype[:], error_code

    def modacc_fetch_downlink_pbch_constellation(
        self, selector_string, timeout, pbch_constellation
    ):
        """modacc_fetch_downlink_pbch_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPBCHConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(pbch_constellation, "pbch_constellation", "complex64")
        if len(pbch_constellation) != actual_array_size_ctype.value:
            pbch_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pbch_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPBCHConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pbch_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_downlink_pcfich_constellation(
        self, selector_string, timeout, pcfich_constellation
    ):
        """modacc_fetch_downlink_pcfich_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(pcfich_constellation, "pcfich_constellation", "complex64")
        if len(pcfich_constellation) != actual_array_size_ctype.value:
            pcfich_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pcfich_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pcfich_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPCFICHConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pcfich_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_downlink_pdcch_constellation(
        self, selector_string, timeout, pdcch_constellation
    ):
        """modacc_fetch_downlink_pdcch_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(pdcch_constellation, "pdcch_constellation", "complex64")
        if len(pdcch_constellation) != actual_array_size_ctype.value:
            pdcch_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pdcch_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pdcch_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPDCCHConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pdcch_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_downlink_phich_constellation(
        self, selector_string, timeout, phich_constellation
    ):
        """modacc_fetch_downlink_phich_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPHICHConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(phich_constellation, "phich_constellation", "complex64")
        if len(phich_constellation) != actual_array_size_ctype.value:
            phich_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        phich_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=phich_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkPHICHConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            phich_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_downlink_transmit_power_array(self, selector_string, timeout):
        """modacc_fetch_downlink_transmit_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        rs_transmit_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        ofdm_symbol_transmit_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        reserved_1_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        reserved_2_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchDownlinkTransmitPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rs_transmit_power_ctype,
            ofdm_symbol_transmit_power_ctype,
            reserved_1_ctype,
            reserved_2_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rs_transmit_power_ctype[:],
            ofdm_symbol_transmit_power_ctype[:],
            reserved_1_ctype[:],
            reserved_2_ctype[:],
            error_code,
        )

    def modacc_fetch_evm_per_slot_trace(self, selector_string, timeout, rms_evm_per_slot):
        """modacc_fetch_evm_per_slot_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchEVMPerSlotTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(rms_evm_per_slot, "rms_evm_per_slot", "float32")
        if len(rms_evm_per_slot) != actual_array_size_ctype.value:
            rms_evm_per_slot.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_per_slot_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_per_slot, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchEVMPerSlotTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_per_slot_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_evm_per_subcarrier_trace(
        self, selector_string, timeout, mean_rms_evm_per_subcarrier
    ):
        """modacc_fetch_evm_per_subcarrier_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            mean_rms_evm_per_subcarrier, "mean_rms_evm_per_subcarrier", "float32"
        )
        if len(mean_rms_evm_per_subcarrier) != actual_array_size_ctype.value:
            mean_rms_evm_per_subcarrier.resize((actual_array_size_ctype.value,), refcheck=False)
        mean_rms_evm_per_subcarrier_ctype = _get_ctypes_pointer_for_buffer(
            value=mean_rms_evm_per_subcarrier, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            mean_rms_evm_per_subcarrier_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_evm_per_symbol_trace(self, selector_string, timeout, rms_evm_per_symbol):
        """modacc_fetch_evm_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(rms_evm_per_symbol, "rms_evm_per_symbol", "float32")
        if len(rms_evm_per_symbol) != actual_array_size_ctype.value:
            rms_evm_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_evm_high_per_symbol_trace(self, selector_string, timeout, evm_high_per_symbol):
        """modacc_fetch_evm_high_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(evm_high_per_symbol, "evm_high_per_symbol", "float32")
        if len(evm_high_per_symbol) != actual_array_size_ctype.value:
            evm_high_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        evm_high_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=evm_high_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchEVMHighPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            evm_high_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_maximum_evm_high_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_high_per_symbol
    ):
        """modacc_fetch_maximum_evm_high_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            maximum_evm_high_per_symbol, "maximum_evm_high_per_symbol", "float32"
        )
        if len(maximum_evm_high_per_symbol) != actual_array_size_ctype.value:
            maximum_evm_high_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        maximum_evm_high_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_evm_high_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMHighPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_evm_high_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_evm_low_per_symbol_trace(self, selector_string, timeout, evm_low_per_symbol):
        """modacc_fetch_evm_low_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(evm_low_per_symbol, "evm_low_per_symbol", "float32")
        if len(evm_low_per_symbol) != actual_array_size_ctype.value:
            evm_low_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        evm_low_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=evm_low_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchEVMLowPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            evm_low_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_maximum_evm_low_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_low_per_symbol
    ):
        """modacc_fetch_maximum_evm_low_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            maximum_evm_low_per_symbol, "maximum_evm_low_per_symbol", "float32"
        )
        if len(maximum_evm_low_per_symbol) != actual_array_size_ctype.value:
            maximum_evm_low_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        maximum_evm_low_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_evm_low_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMLowPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_evm_low_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_in_band_emission_margin_array(self, selector_string, timeout):
        """modacc_fetch_in_band_emission_margin_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchInBandEmissionMarginArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        in_band_emission_margin_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchInBandEmissionMarginArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            in_band_emission_margin_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return in_band_emission_margin_ctype[:], error_code

    def modacc_fetch_in_band_emission_trace(
        self, selector_string, timeout, in_band_emission, in_band_emission_mask
    ):
        """modacc_fetch_in_band_emission_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchInBandEmissionTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(in_band_emission, "in_band_emission", "float32")
        if len(in_band_emission) != actual_array_size_ctype.value:
            in_band_emission.resize((actual_array_size_ctype.value,), refcheck=False)
        in_band_emission_ctype = _get_ctypes_pointer_for_buffer(
            value=in_band_emission, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(in_band_emission_mask, "in_band_emission_mask", "float32")
        if len(in_band_emission_mask) != actual_array_size_ctype.value:
            in_band_emission_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        in_band_emission_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=in_band_emission_mask, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchInBandEmissionTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            in_band_emission_ctype,
            in_band_emission_mask_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_iq_impairments_array(self, selector_string, timeout):
        """modacc_fetch_iq_impairments_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchIQImpairmentsArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_iq_origin_offset_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_iq_gain_imbalance_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_iq_quadrature_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchIQImpairmentsArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_iq_origin_offset_ctype,
            mean_iq_gain_imbalance_ctype,
            mean_iq_quadrature_error_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_iq_origin_offset_ctype[:],
            mean_iq_gain_imbalance_ctype[:],
            mean_iq_quadrature_error_ctype[:],
            error_code,
        )

    def modacc_fetch_maximum_evm_per_slot_trace(
        self, selector_string, timeout, maximum_evm_per_slot
    ):
        """modacc_fetch_maximum_evm_per_slot_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(maximum_evm_per_slot, "maximum_evm_per_slot", "float32")
        if len(maximum_evm_per_slot) != actual_array_size_ctype.value:
            maximum_evm_per_slot.resize((actual_array_size_ctype.value,), refcheck=False)
        maximum_evm_per_slot_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_evm_per_slot, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMPerSlotTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_evm_per_slot_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_maximum_evm_per_subcarrier_trace(
        self, selector_string, timeout, maximum_evm_per_subcarrier
    ):
        """modacc_fetch_maximum_evm_per_subcarrier_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            maximum_evm_per_subcarrier, "maximum_evm_per_subcarrier", "float32"
        )
        if len(maximum_evm_per_subcarrier) != actual_array_size_ctype.value:
            maximum_evm_per_subcarrier.resize((actual_array_size_ctype.value,), refcheck=False)
        maximum_evm_per_subcarrier_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_evm_per_subcarrier, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_evm_per_subcarrier_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_maximum_evm_per_symbol_trace(
        self, selector_string, timeout, maximum_evm_per_symbol
    ):
        """modacc_fetch_maximum_evm_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(maximum_evm_per_symbol, "maximum_evm_per_symbol", "float32")
        if len(maximum_evm_per_symbol) != actual_array_size_ctype.value:
            maximum_evm_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        maximum_evm_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_evm_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_evm_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_maximum_magnitude_error_per_symbol_trace(
        self, selector_string, timeout, maximum_magnitude_error_per_symbol
    ):
        """modacc_fetch_maximum_magnitude_error_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            maximum_magnitude_error_per_symbol, "maximum_magnitude_error_per_symbol", "float32"
        )
        if len(maximum_magnitude_error_per_symbol) != actual_array_size_ctype.value:
            maximum_magnitude_error_per_symbol.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        maximum_magnitude_error_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_magnitude_error_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumMagnitudeErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_magnitude_error_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_maximum_phase_error_per_symbol_trace(
        self, selector_string, timeout, maximum_phase_error_per_symbol
    ):
        """modacc_fetch_maximum_phase_error_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            maximum_phase_error_per_symbol, "maximum_phase_error_per_symbol", "float32"
        )
        if len(maximum_phase_error_per_symbol) != actual_array_size_ctype.value:
            maximum_phase_error_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        maximum_phase_error_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_phase_error_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumPhaseErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_phase_error_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pdsch_1024_qam_constellation(
        self, selector_string, timeout, qam1024_constellation
    ):
        """modacc_fetch_pdsch_1024_qam_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(qam1024_constellation, "qam1024_constellation", "complex64")
        if len(qam1024_constellation) != actual_array_size_ctype.value:
            qam1024_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        qam1024_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=qam1024_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH1024QAMConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam1024_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_1024_qam_evm_array(self, selector_string, timeout):
        """modacc_fetch_pdsch_1024_qam_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_1024qam_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH1024QAMEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_1024qam_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_1024qam_evm_ctype[:], error_code

    def modacc_fetch_pdsch_16_qam_constellation(
        self, selector_string, timeout, qam16_constellation
    ):
        """modacc_fetch_pdsch_16_qam_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH16QAMConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(qam16_constellation, "qam16_constellation", "complex64")
        if len(qam16_constellation) != actual_array_size_ctype.value:
            qam16_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        qam16_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=qam16_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH16QAMConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam16_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_256_qam_constellation(
        self, selector_string, timeout, qam256_constellation
    ):
        """modacc_fetch_pdsch_256_qam_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH256QAMConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(qam256_constellation, "qam256_constellation", "complex64")
        if len(qam256_constellation) != actual_array_size_ctype.value:
            qam256_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        qam256_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=qam256_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH256QAMConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam256_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_64_qam_constellation(
        self, selector_string, timeout, qam64_constellation
    ):
        """modacc_fetch_pdsch_64_qam_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH64QAMConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(qam64_constellation, "qam64_constellation", "complex64")
        if len(qam64_constellation) != actual_array_size_ctype.value:
            qam64_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        qam64_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=qam64_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCH64QAMConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam64_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_evm_array(self, selector_string, timeout):
        """modacc_fetch_pdsch_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCHEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_rms_qpsk_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_rms_16qam_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_rms_64qam_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_rms_256qam_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCHEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_evm_ctype,
            mean_rms_qpsk_evm_ctype,
            mean_rms_16qam_evm_ctype,
            mean_rms_64qam_evm_ctype,
            mean_rms_256qam_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            mean_rms_evm_ctype[:],
            mean_rms_qpsk_evm_ctype[:],
            mean_rms_16qam_evm_ctype[:],
            mean_rms_64qam_evm_ctype[:],
            mean_rms_256qam_evm_ctype[:],
            error_code,
        )

    def modacc_fetch_pdsch_qpsk_constellation(self, selector_string, timeout, qpsk_constellation):
        """modacc_fetch_pdsch_qpsk_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCHQPSKConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(qpsk_constellation, "qpsk_constellation", "complex64")
        if len(qpsk_constellation) != actual_array_size_ctype.value:
            qpsk_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        qpsk_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=qpsk_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPDSCHQPSKConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qpsk_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pssch_data_evm_array(self, selector_string, timeout):
        """modacc_fetch_pssch_data_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHDataEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        pssch_mean_rms_data_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        pssch_maximum_peak_data_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHDataEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pssch_mean_rms_data_evm_ctype,
            pssch_maximum_peak_data_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pssch_mean_rms_data_evm_ctype[:], pssch_maximum_peak_data_evm_ctype[:], error_code

    def modacc_fetch_pssch_dmrs_evm_array(self, selector_string, timeout):
        """modacc_fetch_pssch_dmrs_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        pssch_mean_rms_dmrs_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        pssch_maximum_peak_dmrs_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHDMRSEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pssch_mean_rms_dmrs_evm_ctype,
            pssch_maximum_peak_dmrs_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pssch_mean_rms_dmrs_evm_ctype[:], pssch_maximum_peak_dmrs_evm_ctype[:], error_code

    def modacc_fetch_pssch_symbol_power_array(self, selector_string, timeout):
        """modacc_fetch_pssch_symbol_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        pssch_mean_data_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        pssch_mean_dmrs_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHSymbolPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pssch_mean_data_power_ctype,
            pssch_mean_dmrs_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pssch_mean_data_power_ctype[:], pssch_mean_dmrs_power_ctype[:], error_code

    def modacc_fetch_pusch_data_evm_array(self, selector_string, timeout):
        """modacc_fetch_pusch_data_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDataEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_data_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        maximum_peak_data_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDataEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_data_evm_ctype,
            maximum_peak_data_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_data_evm_ctype[:], maximum_peak_data_evm_ctype[:], error_code

    def modacc_fetch_pusch_demodulated_bits(self, selector_string, timeout):
        """modacc_fetch_pusch_demodulated_bits."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDemodulatedBits(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int8, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDemodulatedBits(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return bits_ctype[:], error_code

    def modacc_fetch_pusch_dmrs_evm_array(self, selector_string, timeout):
        """modacc_fetch_pusch_dmrs_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_dmrs_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        maximum_peak_dmrs_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHDMRSEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_dmrs_evm_ctype,
            maximum_peak_dmrs_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_dmrs_evm_ctype[:], maximum_peak_dmrs_evm_ctype[:], error_code

    def modacc_fetch_pusch_symbol_power_array(self, selector_string, timeout):
        """modacc_fetch_pusch_symbol_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        pusch_mean_data_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        pusch_mean_dmrs_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHSymbolPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pusch_mean_data_power_ctype,
            pusch_mean_dmrs_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pusch_mean_data_power_ctype[:], pusch_mean_dmrs_power_ctype[:], error_code

    def modacc_fetch_rms_magnitude_error_per_symbol_trace(
        self, selector_string, timeout, rms_magnitude_error_per_symbol
    ):
        """modacc_fetch_rms_magnitude_error_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            rms_magnitude_error_per_symbol, "rms_magnitude_error_per_symbol", "float32"
        )
        if len(rms_magnitude_error_per_symbol) != actual_array_size_ctype.value:
            rms_magnitude_error_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_magnitude_error_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_magnitude_error_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchRMSMagnitudeErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_magnitude_error_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_rms_phase_error_per_symbol_trace(
        self, selector_string, timeout, rms_phase_error_per_symbol
    ):
        """modacc_fetch_rms_phase_error_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            rms_phase_error_per_symbol, "rms_phase_error_per_symbol", "float32"
        )
        if len(rms_phase_error_per_symbol) != actual_array_size_ctype.value:
            rms_phase_error_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_phase_error_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_phase_error_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchRMSPhaseErrorPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_phase_error_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_spectral_flatness_array(self, selector_string, timeout):
        """modacc_fetch_spectral_flatness_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSpectralFlatnessArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        range1_maximum_to_range1_minimum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        range2_maximum_to_range2_minimum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        range1_maximum_to_range2_minimum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        range2_maximum_to_range1_minimum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSpectralFlatnessArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            range1_maximum_to_range1_minimum_ctype,
            range2_maximum_to_range2_minimum_ctype,
            range1_maximum_to_range2_minimum_ctype,
            range2_maximum_to_range1_minimum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            range1_maximum_to_range1_minimum_ctype[:],
            range2_maximum_to_range2_minimum_ctype[:],
            range1_maximum_to_range2_minimum_ctype[:],
            range2_maximum_to_range1_minimum_ctype[:],
            error_code,
        )

    def modacc_fetch_srs_constellation(self, selector_string, timeout, srs_constellation):
        """modacc_fetch_srs_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSRSConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(srs_constellation, "srs_constellation", "complex64")
        if len(srs_constellation) != actual_array_size_ctype.value:
            srs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        srs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=srs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSRSConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            srs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_srs_evm_array(self, selector_string, timeout):
        """modacc_fetch_srs_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSRSEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_srs_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_srs_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSRSEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_srs_evm_ctype,
            mean_srs_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_srs_evm_ctype[:], mean_srs_power_ctype[:], error_code

    def modacc_fetch_subblock_in_band_emission_trace(self, selector_string, timeout):
        """modacc_fetch_subblock_in_band_emission_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        subblock_in_band_emission_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        subblock_in_band_emission_mask_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        subblock_in_band_emission_rb_indices_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSubblockInBandEmissionTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subblock_in_band_emission_ctype,
            subblock_in_band_emission_mask_ctype,
            subblock_in_band_emission_rb_indices_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            subblock_in_band_emission_ctype[:],
            subblock_in_band_emission_mask_ctype[:],
            subblock_in_band_emission_rb_indices_ctype[:],
            error_code,
        )

    def modacc_fetch_synchronization_signal_constellation(
        self, selector_string, timeout, sss_constellation, pss_constellation
    ):
        """modacc_fetch_synchronization_signal_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSynchronizationSignalConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(sss_constellation, "sss_constellation", "complex64")
        if len(sss_constellation) != actual_array_size_ctype.value:
            sss_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        sss_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=sss_constellation, library_type=_custom_types.ComplexSingle
        )
        _helper.validate_numpy_array(pss_constellation, "pss_constellation", "complex64")
        if len(pss_constellation) != actual_array_size_ctype.value:
            pss_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pss_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pss_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSynchronizationSignalConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            sss_constellation_ctype,
            pss_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_synchronization_signal_evm_array(self, selector_string, timeout):
        """modacc_fetch_synchronization_signal_evm_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        mean_rms_pss_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_rms_sss_evm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSynchronizationSignalEVMArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            mean_rms_pss_evm_ctype,
            mean_rms_sss_evm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mean_rms_pss_evm_ctype[:], mean_rms_sss_evm_ctype[:], error_code

    def modacc_fetch_maximum_frequency_error_per_slot_trace(
        self, selector_string, timeout, maximum_frequency_error_per_slot
    ):
        """modacc_fetch_maximum_frequency_error_per_slot_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            maximum_frequency_error_per_slot, "maximum_frequency_error_per_slot", "float32"
        )
        if len(maximum_frequency_error_per_slot) != actual_array_size_ctype.value:
            maximum_frequency_error_per_slot.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        maximum_frequency_error_per_slot_ctype = _get_ctypes_pointer_for_buffer(
            value=maximum_frequency_error_per_slot, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchMaximumFrequencyErrorPerSlotTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            maximum_frequency_error_per_slot_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_npdsch_qpsk_constellation(self, selector_string, timeout, qpsk_constellation):
        """modacc_fetch_npdsch_qpsk_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(qpsk_constellation, "qpsk_constellation", "complex64")
        if len(qpsk_constellation) != actual_array_size_ctype.value:
            qpsk_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        qpsk_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=qpsk_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchNPDSCHQPSKConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qpsk_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_nrs_constellation(self, selector_string, timeout, nrs_constellation):
        """modacc_fetch_nrs_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchNRSConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(nrs_constellation, "nrs_constellation", "complex64")
        if len(nrs_constellation) != actual_array_size_ctype.value:
            nrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        nrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=nrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchNRSConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            nrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def obw_fetch_spectrum(self, selector_string, timeout, spectrum):
        """obw_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_OBWFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != actual_array_size_ctype.value:
            spectrum.resize((actual_array_size_ctype.value,), refcheck=False)
        spectrum_ctype = _get_ctypes_pointer_for_buffer(value=spectrum, library_type=ctypes.c_float)

        # call library function again to get array
        error_code = self._library.RFmxLTE_OBWFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            spectrum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def sem_fetch_measurement_array(self, selector_string, timeout):
        """sem_fetch_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SEMFetchComponentCarrierMeasurementArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        absolute_integrated_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_integrated_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SEMFetchComponentCarrierMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_integrated_power_ctype,
            relative_integrated_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_integrated_power_ctype[:], relative_integrated_power_ctype[:], error_code

    def sem_fetch_lower_offset_margin_array(self, selector_string, timeout):
        """sem_fetch_lower_offset_margin_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SEMFetchLowerOffsetMarginArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        measurement_status_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )
        margin_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        margin_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        margin_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        margin_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SEMFetchLowerOffsetMarginArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            margin_ctype,
            margin_frequency_ctype,
            margin_absolute_power_ctype,
            margin_relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            [enums.SemLowerOffsetMeasurementStatus(value) for value in measurement_status_ctype],
            margin_ctype[:],
            margin_frequency_ctype[:],
            margin_absolute_power_ctype[:],
            margin_relative_power_ctype[:],
            error_code,
        )

    def sem_fetch_lower_offset_power_array(self, selector_string, timeout):
        """sem_fetch_lower_offset_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SEMFetchLowerOffsetPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        absolute_integrated_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_integrated_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        absolute_peak_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_peak_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SEMFetchLowerOffsetPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_integrated_power_ctype,
            relative_integrated_power_ctype,
            absolute_peak_power_ctype,
            peak_frequency_ctype,
            relative_peak_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_integrated_power_ctype[:],
            relative_integrated_power_ctype[:],
            absolute_peak_power_ctype[:],
            peak_frequency_ctype[:],
            relative_peak_power_ctype[:],
            error_code,
        )

    def sem_fetch_spectrum(self, selector_string, timeout, spectrum, composite_mask):
        """sem_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SEMFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        if len(spectrum) != actual_array_size_ctype.value:
            spectrum.resize((actual_array_size_ctype.value,), refcheck=False)
        spectrum_ctype = _get_ctypes_pointer_for_buffer(value=spectrum, library_type=ctypes.c_float)
        _helper.validate_numpy_array(composite_mask, "composite_mask", "float32")
        if len(composite_mask) != actual_array_size_ctype.value:
            composite_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        composite_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=composite_mask, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SEMFetchSpectrum(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            spectrum_ctype,
            composite_mask_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def sem_fetch_upper_offset_margin_array(self, selector_string, timeout):
        """sem_fetch_upper_offset_margin_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SEMFetchUpperOffsetMarginArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        measurement_status_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )
        margin_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        margin_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        margin_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        margin_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SEMFetchUpperOffsetMarginArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            margin_ctype,
            margin_frequency_ctype,
            margin_absolute_power_ctype,
            margin_relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            [enums.SemUpperOffsetMeasurementStatus(value) for value in measurement_status_ctype],
            margin_ctype[:],
            margin_frequency_ctype[:],
            margin_absolute_power_ctype[:],
            margin_relative_power_ctype[:],
            error_code,
        )

    def sem_fetch_upper_offset_power_array(self, selector_string, timeout):
        """sem_fetch_upper_offset_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SEMFetchUpperOffsetPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        absolute_integrated_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_integrated_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        absolute_peak_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_peak_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SEMFetchUpperOffsetPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_integrated_power_ctype,
            relative_integrated_power_ctype,
            absolute_peak_power_ctype,
            peak_frequency_ctype,
            relative_peak_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_integrated_power_ctype[:],
            relative_integrated_power_ctype[:],
            absolute_peak_power_ctype[:],
            peak_frequency_ctype[:],
            relative_peak_power_ctype[:],
            error_code,
        )

    def pvt_fetch_measurement_array(self, selector_string, timeout):
        """pvt_fetch_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_PVTFetchMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        measurement_status_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )
        mean_absolute_off_power_before_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_absolute_off_power_after_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        mean_absolute_on_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        burst_width_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_PVTFetchMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            mean_absolute_off_power_before_ctype,
            mean_absolute_off_power_after_ctype,
            mean_absolute_on_power_ctype,
            burst_width_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            [enums.PvtMeasurementStatus(value) for value in measurement_status_ctype],
            mean_absolute_off_power_before_ctype[:],
            mean_absolute_off_power_after_ctype[:],
            mean_absolute_on_power_ctype[:],
            burst_width_ctype[:],
            error_code,
        )

    def pvt_fetch_signal_power_trace(self, selector_string, timeout, signal_power, absolute_limit):
        """pvt_fetch_signal_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_PVTFetchSignalPowerTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(signal_power, "signal_power", "float32")
        if len(signal_power) != actual_array_size_ctype.value:
            signal_power.resize((actual_array_size_ctype.value,), refcheck=False)
        signal_power_ctype = _get_ctypes_pointer_for_buffer(
            value=signal_power, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(absolute_limit, "absolute_limit", "float32")
        if len(absolute_limit) != actual_array_size_ctype.value:
            absolute_limit.resize((actual_array_size_ctype.value,), refcheck=False)
        absolute_limit_ctype = _get_ctypes_pointer_for_buffer(
            value=absolute_limit, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_PVTFetchSignalPowerTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            signal_power_ctype,
            absolute_limit_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def slotphase_fetch_maximum_phase_discontinuity_array(self, selector_string, timeout):
        """slotphase_fetch_maximum_phase_discontinuity_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        maximum_phase_discontinuity_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SlotPhaseFetchMaximumPhaseDiscontinuityArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            maximum_phase_discontinuity_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return maximum_phase_discontinuity_ctype[:], error_code

    def slotphase_fetch_phase_discontinuities(self, selector_string, timeout):
        """slotphase_fetch_phase_discontinuities."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        slot_phase_discontinuity_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SlotPhaseFetchPhaseDiscontinuities(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            slot_phase_discontinuity_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return slot_phase_discontinuity_ctype[:], error_code

    def slotphase_fetch_sample_phase_error_linear_fit_trace(
        self, selector_string, timeout, sample_phase_error_linear_fit
    ):
        """slotphase_fetch_sample_phase_error_linear_fit_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(
            sample_phase_error_linear_fit, "sample_phase_error_linear_fit", "float32"
        )
        if len(sample_phase_error_linear_fit) != actual_array_size_ctype.value:
            sample_phase_error_linear_fit.resize((actual_array_size_ctype.value,), refcheck=False)
        sample_phase_error_linear_fit_ctype = _get_ctypes_pointer_for_buffer(
            value=sample_phase_error_linear_fit, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SlotPhaseFetchSamplePhaseErrorLinearFitTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            sample_phase_error_linear_fit_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def slotphase_fetch_sample_phase_error(self, selector_string, timeout, sample_phase_error):
        """slotphase_fetch_sample_phase_error."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SlotPhaseFetchSamplePhaseError(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(sample_phase_error, "sample_phase_error", "float32")
        if len(sample_phase_error) != actual_array_size_ctype.value:
            sample_phase_error.resize((actual_array_size_ctype.value,), refcheck=False)
        sample_phase_error_ctype = _get_ctypes_pointer_for_buffer(
            value=sample_phase_error, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SlotPhaseFetchSamplePhaseError(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            sample_phase_error_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def slotpower_fetch_powers(self, selector_string, timeout):
        """slotpower_fetch_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_SlotPowerFetchPowers(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        subframe_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        subframe_power_delta_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_SlotPowerFetchPowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subframe_power_ctype,
            subframe_power_delta_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return subframe_power_ctype[:], subframe_power_delta_ctype[:], error_code

    def txp_fetch_power_trace(self, selector_string, timeout, power):
        """txp_fetch_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_TXPFetchPowerTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(power, "power", "float32")
        if len(power) != actual_array_size_ctype.value:
            power.resize((actual_array_size_ctype.value,), refcheck=False)
        power_ctype = _get_ctypes_pointer_for_buffer(value=power, library_type=ctypes.c_float)

        # call library function again to get array
        error_code = self._library.RFmxLTE_TXPFetchPowerTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        old_signal_name_ctype = ctypes.create_string_buffer(old_signal_name.encode(self._encoding))
        new_signal_name_ctype = ctypes.create_string_buffer(new_signal_name.encode(self._encoding))
        error_code = self._library.RFmxLTE_CloneSignalConfiguration(
            vi_ctype, old_signal_name_ctype, new_signal_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        import nirfmxlte

        signal_configuration = (
            nirfmxlte._LteSignalConfiguration.get_lte_signal_configuration(  # type: ignore
                self._instr_session, new_signal_name, True
            )
        )
        return signal_configuration, error_code

    def delete_signal_configuration(self, ignore_driver_error):
        """delete_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(
            self._signal_obj.signal_configuration_name.encode(self._encoding)
        )
        error_code = self._library.RFmxLTE_DeleteSignalConfiguration(vi_ctype, signal_name_ctype)
        if not ignore_driver_error:
            errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def send_software_edge_trigger(self):
        """send_software_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        error_code = self._library.RFmxLTE_SendSoftwareEdgeTrigger(vi_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_all_named_result_names(self, selector_string):
        """get_all_named_result_names."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        actual_result_names_size_ctype = ctypes.c_int32(0)
        default_result_exists_ctype = ctypes.c_int32()

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_GetAllNamedResultNames(
            vi_ctype,
            selector_string_ctype,
            None,
            0,
            actual_result_names_size_ctype,
            default_result_exists_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        result_names_ctype = (ctypes.c_char * actual_result_names_size_ctype.value)()

        # call library function again to get array
        error_code = self._library.RFmxLTE_GetAllNamedResultNames(
            vi_ctype,
            selector_string_ctype,
            result_names_ctype,
            actual_result_names_size_ctype,
            None,
            default_result_exists_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        return (
            _helper.split_string_by_comma(result_names_ctype.value.decode(self._encoding)),
            default_result_exists_ctype.value,
            error_code,
        )

    def clear_noise_calibration_database(self, selector_string):
        """clear_noise_calibration_database."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxLTE_ClearNoiseCalibrationDatabase(
            vi_ctype, selector_string_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def analyze_iq_1_waveform(self, selector_string, result_name, x0, dx, iq, reset):
        """analyze_iq_1_waveform."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        x0_ctype = ctypes.c_double(x0)
        dx_ctype = ctypes.c_double(dx)
        _helper.validate_numpy_array(iq, "iq", "complex64")
        iq_ctype = _get_ctypes_pointer_for_buffer(
            value=iq, library_type=_custom_types.ComplexSingle
        )
        array_size_ctype = ctypes.c_int32(len(iq) if iq is not None else 0)
        reset_ctype = ctypes.c_int32(reset)
        reserved_ctype = ctypes.c_int64(0)
        error_code = self._library.RFmxLTE_AnalyzeIQ1Waveform(
            vi_ctype,
            selector_string_ctype,
            result_name_ctype,
            x0_ctype,
            dx_ctype,
            iq_ctype,
            array_size_ctype,
            reset_ctype,
            reserved_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def analyze_spectrum_1_waveform(self, selector_string, result_name, x0, dx, spectrum, reset):
        """analyze_spectrum_1_waveform."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        x0_ctype = ctypes.c_double(x0)
        dx_ctype = ctypes.c_double(dx)
        _helper.validate_numpy_array(spectrum, "spectrum", "float32")
        spectrum_ctype = _get_ctypes_pointer_for_buffer(value=spectrum, library_type=ctypes.c_float)
        array_size_ctype = ctypes.c_int32(len(spectrum) if spectrum is not None else 0)
        reset_ctype = ctypes.c_int32(reset)
        reserved_ctype = ctypes.c_int64(0)
        error_code = self._library.RFmxLTE_AnalyzeSpectrum1Waveform(
            vi_ctype,
            selector_string_ctype,
            result_name_ctype,
            x0_ctype,
            dx_ctype,
            spectrum_ctype,
            array_size_ctype,
            reset_ctype,
            reserved_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_downlink_auto_channel_detection(
        self,
        selector_string,
        auto_pdsch_channel_detection_enabled,
        auto_control_channel_power_detection_enabled,
        auto_pcfich_cfi_detection_enabled,
    ):
        """configure_downlink_auto_channel_detection."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        auto_pdsch_channel_detection_enabled_ctype = ctypes.c_int32(
            auto_pdsch_channel_detection_enabled
        )
        auto_control_channel_power_detection_enabled_ctype = ctypes.c_int32(
            auto_control_channel_power_detection_enabled
        )
        auto_pcfich_cfi_detection_enabled_ctype = ctypes.c_int32(auto_pcfich_cfi_detection_enabled)
        reserved_ctype = ctypes.c_int32(0)
        error_code = self._library.RFmxLTE_CfgDownlinkAutoChannelDetection(
            vi_ctype,
            selector_string_ctype,
            auto_pdsch_channel_detection_enabled_ctype,
            auto_control_channel_power_detection_enabled_ctype,
            auto_pcfich_cfi_detection_enabled_ctype,
            reserved_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pusch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        """modacc_fetch_pusch_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        data_actual_array_size_ctype = ctypes.c_int32(0)
        dmrs_actual_array_size_ctype = ctypes.c_int32(0)
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            0,
            data_actual_array_size_ctype,
            None,
            0,
            dmrs_actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != data_actual_array_size_ctype.value:
            data_constellation.resize((data_actual_array_size_ctype.value,), refcheck=False)
        data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=data_constellation, library_type=_custom_types.ComplexSingle
        )
        _helper.validate_numpy_array(dmrs_constellation, "dmrs_constellation", "complex64")
        if len(dmrs_constellation) != dmrs_actual_array_size_ctype.value:
            dmrs_constellation.resize((dmrs_actual_array_size_ctype.value,), refcheck=False)
        dmrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=dmrs_constellation, library_type=_custom_types.ComplexSingle
        )
        error_code = self._library.RFmxLTE_ModAccFetchPUSCHConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            data_constellation_ctype,
            data_actual_array_size_ctype.value,
            data_actual_array_size_ctype,
            dmrs_constellation_ctype,
            dmrs_actual_array_size_ctype.value,
            dmrs_actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_npusch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        """modacc_fetch_npusch_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        data_actual_array_size_ctype = ctypes.c_int32(0)
        dmrs_actual_array_size_ctype = ctypes.c_int32(0)
        error_code = self._library.RFmxLTE_ModAccFetchNPUSCHConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            0,
            data_actual_array_size_ctype,
            None,
            0,
            dmrs_actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != data_actual_array_size_ctype.value:
            data_constellation.resize((data_actual_array_size_ctype.value,), refcheck=False)
        data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=data_constellation, library_type=_custom_types.ComplexSingle
        )
        _helper.validate_numpy_array(dmrs_constellation, "dmrs_constellation", "complex64")
        if len(dmrs_constellation) != dmrs_actual_array_size_ctype.value:
            dmrs_constellation.resize((dmrs_actual_array_size_ctype.value,), refcheck=False)
        dmrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=dmrs_constellation, library_type=_custom_types.ComplexSingle
        )
        error_code = self._library.RFmxLTE_ModAccFetchNPUSCHConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            data_constellation_ctype,
            data_actual_array_size_ctype.value,
            data_actual_array_size_ctype,
            dmrs_constellation_ctype,
            dmrs_actual_array_size_ctype.value,
            dmrs_actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_nb_synchronization_signal_constellation(
        self, selector_string, timeout, nsss_constellation, npss_constellation
    ):
        """modacc_fetch_nb_synchronization_signal_constellation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(nsss_constellation, "nsss_constellation", "complex64")
        if len(nsss_constellation) != actual_array_size_ctype.value:
            nsss_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        nsss_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=nsss_constellation, library_type=_custom_types.ComplexSingle
        )
        _helper.validate_numpy_array(npss_constellation, "npss_constellation", "complex64")
        if len(npss_constellation) != actual_array_size_ctype.value:
            npss_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        npss_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=npss_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchNBSynchronizationSignalConstellation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            nsss_constellation_ctype,
            npss_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_spectral_flatness_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        """modacc_fetch_spectral_flatness_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchSpectralFlatnessTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            None,
            None,
            None,
            None,
            None,
            0,
            actual_array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(spectral_flatness, "spectral_flatness", "float32")
        if len(spectral_flatness) != actual_array_size_ctype.value:
            spectral_flatness.resize((actual_array_size_ctype.value,), refcheck=False)
        spectral_flatness_ctype = _get_ctypes_pointer_for_buffer(
            value=spectral_flatness, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(
            spectral_flatness_lower_mask, "spectral_flatness_lower_mask", "float32"
        )
        if len(spectral_flatness_lower_mask) != actual_array_size_ctype.value:
            spectral_flatness_lower_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        spectral_flatness_lower_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=spectral_flatness_lower_mask, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(
            spectral_flatness_upper_mask, "spectral_flatness_upper_mask", "float32"
        )
        if len(spectral_flatness_upper_mask) != actual_array_size_ctype.value:
            spectral_flatness_upper_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        spectral_flatness_upper_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=spectral_flatness_upper_mask, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchSpectralFlatnessTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            spectral_flatness_ctype,
            spectral_flatness_lower_mask_ctype,
            spectral_flatness_upper_mask_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return float(x0_ctype.value), float(dx_ctype.value), error_code

    def modacc_fetch_pssch_constellation_trace(
        self, selector_string, timeout, data_constellation, dmrs_constellation
    ):
        """modacc_fetch_pssch_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != actual_array_size_ctype.value:
            data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=data_constellation, library_type=_custom_types.ComplexSingle
        )
        _helper.validate_numpy_array(dmrs_constellation, "dmrs_constellation", "complex64")
        if len(dmrs_constellation) != actual_array_size_ctype.value:
            dmrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        dmrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=dmrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxLTE_ModAccFetchPSSCHConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            data_constellation_ctype,
            dmrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code
