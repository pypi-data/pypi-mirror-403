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
import nirfmxwlan.attributes as attributes
import nirfmxwlan.enums as enums
import nirfmxwlan.errors as errors
import nirfmxwlan.internal._custom_types as _custom_types
import nirfmxwlan.internal._helper as _helper
import nirfmxwlan.internal._library_singleton as _library_singleton
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
        size_or_error_code = self._library.RFmxWLAN_GetErrorString(
            self._vi, error_code_ctype, 0, None
        )
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxWLAN_GetErrorString(
                self._vi, error_code_ctype, size_or_error_code, error_string_ctype
            )
        return error_string_ctype.value.decode(self._encoding)

    def get_error(self) -> tuple[int, Any]:
        """Returns the error code and error message."""
        error_code_ctype = ctypes.c_int32()
        error_string_ctype = ctypes.create_string_buffer(0)
        size_or_error_code = self._library.RFmxWLAN_GetError(self._vi, error_code_ctype, 0, None)
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_code_ctype = ctypes.c_int32(error_code_ctype.value)
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxWLAN_GetError(
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
        error_code = self._library.RFmxWLAN_ResetAttribute(
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
                local_personality.value == nirfmxinstr.Personalities.WLAN.value
            )
        elif self._signal_obj is not None:
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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int8()
        error_code = self._library.RFmxWLAN_GetAttributeI8(
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
        error_code = self._library.RFmxWLAN_SetAttributeI8(
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
        error_code = self._library.RFmxWLAN_GetAttributeI8Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeI8Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeI8Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeI16(
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
        error_code = self._library.RFmxWLAN_SetAttributeI16(
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
        error_code = self._library.RFmxWLAN_GetAttributeI32(
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
        error_code = self._library.RFmxWLAN_SetAttributeI32(
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
        error_code = self._library.RFmxWLAN_GetAttributeI32Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeI32Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeI32Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeI64(
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
        error_code = self._library.RFmxWLAN_SetAttributeI64(
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
        error_code = self._library.RFmxWLAN_GetAttributeI64Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeI64Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeI64Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeU8(
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
        error_code = self._library.RFmxWLAN_SetAttributeU8(
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
        error_code = self._library.RFmxWLAN_GetAttributeU8Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeU8Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeU8Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeU16(
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
        error_code = self._library.RFmxWLAN_SetAttributeU16(
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
        error_code = self._library.RFmxWLAN_GetAttributeU32(
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
        error_code = self._library.RFmxWLAN_SetAttributeU32(
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
        error_code = self._library.RFmxWLAN_GetAttributeU32Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeU32Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeU32Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeU64Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeU64Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeU64Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeF32(
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
        error_code = self._library.RFmxWLAN_SetAttributeF32(
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
        error_code = self._library.RFmxWLAN_GetAttributeF32Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeF32Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeF32Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeF64(
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
        error_code = self._library.RFmxWLAN_SetAttributeF64(
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
        error_code = self._library.RFmxWLAN_GetAttributeF64Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeF64Array(
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
        error_code = self._library.RFmxWLAN_SetAttributeF64Array(
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
        error_code = self._library.RFmxWLAN_GetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxWLAN_GetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxWLAN_SetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxWLAN_GetAttributeNIComplexDoubleArray(
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
        error_code = self._library.RFmxWLAN_GetAttributeNIComplexDoubleArray(
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
        error_code = self._library.RFmxWLAN_SetAttributeNIComplexDoubleArray(
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
        size_or_error_code = self._library.RFmxWLAN_GetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, array_size_ctype, attr_val_ctype
        )
        if size_or_error_code < 0:
            errors.handle_error(
                self, size_or_error_code, ignore_warnings=True, is_error_handling=False
            )
            return None, size_or_error_code
        array_size_ctype = ctypes.c_int32(size_or_error_code)
        attr_val_ctype = (ctypes.c_char * array_size_ctype.value)()
        error_code = self._library.RFmxWLAN_GetAttributeString(
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
        error_code = self._library.RFmxWLAN_SetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_1_reference_waveform(
        self, selector_string, x0, dx, reference_waveform
    ):
        """ofdmmodacc_configure_1_reference_waveform."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        x0_ctype = ctypes.c_double(x0)
        dx_ctype = ctypes.c_double(dx)
        _helper.validate_numpy_array(reference_waveform, "reference_waveform", "complex64")
        reference_waveform_ctype = _get_ctypes_pointer_for_buffer(
            value=reference_waveform, library_type=_custom_types.ComplexSingle
        )
        array_size_ctype = ctypes.c_int32(
            len(reference_waveform) if reference_waveform is not None else 0
        )
        error_code = self._library.RFmxWLAN_OFDMModAccCfg1ReferenceWaveform(
            vi_ctype,
            selector_string_ctype,
            x0_ctype,
            dx_ctype,
            reference_waveform_ctype,
            array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_auto_level(self, selector_string, timeout):
        """ofdmmodacc_auto_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxWLAN_OFDMModAccAutoLevel(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_validate_calibration_data(self, selector_string):
        """ofdmmodacc_validate_calibration_data."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        calibration_data_valid_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccValidateCalibrationData(
            vi_ctype, selector_string_ctype, calibration_data_valid_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmModAccCalibrationDataValid(calibration_data_valid_ctype.value), error_code

    def abort_measurements(self, selector_string):
        """abort_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_AbortMeasurements(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_detect_signal(self, selector_string, timeout):
        """auto_detect_signal."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxWLAN_AutoDetectSignal(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_level(self, selector_string, measurement_interval):
        """auto_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_interval_ctype = ctypes.c_double(measurement_interval)
        error_code = self._library.RFmxWLAN_AutoLevel(
            vi_ctype, selector_string_ctype, measurement_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def check_measurement_status(self, selector_string):
        """check_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        is_done_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_CheckMeasurementStatus(
            vi_ctype, selector_string_ctype, is_done_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return bool(is_done_ctype.value), error_code

    def clear_all_named_results(self, selector_string):
        """clear_all_named_results."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_ClearAllNamedResults(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def clear_named_result(self, selector_string):
        """clear_named_result."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_ClearNamedResult(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def commit(self, selector_string):
        """commit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_Commit(vi_ctype, selector_string_ctype)
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
        error_code = self._library.RFmxWLAN_CfgDigitalEdgeTrigger(
            vi_ctype,
            selector_string_ctype,
            digital_edge_source_ctype,
            digital_edge_ctype,
            trigger_delay_ctype,
            enable_trigger_ctype,
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
        error_code = self._library.RFmxWLAN_CfgIQPowerEdgeTrigger(
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

    def configure_selected_ports_multiple(self, selector_string, selected_ports):
        """configure_selected_ports_multiple."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        selected_ports_ctype = ctypes.create_string_buffer(selected_ports.encode(self._encoding))
        error_code = self._library.RFmxWLAN_CfgSelectedPortsMultiple(
            vi_ctype, selector_string_ctype, selected_ports_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        """configure_software_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        trigger_delay_ctype = ctypes.c_double(trigger_delay)
        enable_trigger_ctype = ctypes.c_int32(enable_trigger)
        error_code = self._library.RFmxWLAN_CfgSoftwareEdgeTrigger(
            vi_ctype, selector_string_ctype, trigger_delay_ctype, enable_trigger_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def create_signal_configuration(self, signal_name):
        """create_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(signal_name.encode(self._encoding))
        error_code = self._library.RFmxWLAN_CreateSignalConfiguration(vi_ctype, signal_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def disable_trigger(self, selector_string):
        """disable_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_DisableTrigger(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def initiate(self, selector_string, result_name):
        """initiate."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        error_code = self._library.RFmxWLAN_Initiate(
            vi_ctype, selector_string_ctype, result_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def reset_to_default(self, selector_string):
        """reset_to_default."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_ResetToDefault(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def select_measurements(self, selector_string, measurements, enable_all_traces):
        """select_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurements_ctype = ctypes.c_uint32(measurements)
        enable_all_traces_ctype = ctypes.c_int32(enable_all_traces)
        error_code = self._library.RFmxWLAN_SelectMeasurements(
            vi_ctype, selector_string_ctype, measurements_ctype, enable_all_traces_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def wait_for_measurement_complete(self, selector_string, timeout):
        """wait_for_measurement_complete."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxWLAN_WaitForMeasurementComplete(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_detect_signal_analysis_only(self, selector_string, x0, dx, iq):
        """auto_detect_signal_analysis_only."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        x0_ctype = ctypes.c_double(x0)
        dx_ctype = ctypes.c_double(dx)
        _helper.validate_numpy_array(iq, "iq", "complex64")
        iq_ctype = _get_ctypes_pointer_for_buffer(
            value=iq, library_type=_custom_types.ComplexSingle
        )
        array_size_ctype = ctypes.c_int32(len(iq) if iq is not None else 0)
        error_code = self._library.RFmxWLAN_AutoDetectSignalAnalysisOnly(
            vi_ctype, selector_string_ctype, x0_ctype, dx_ctype, iq_ctype, array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """txp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxWLAN_TXPCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_burst_detection_enabled(self, selector_string, burst_detection_enabled):
        """txp_configure_burst_detection_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        burst_detection_enabled_ctype = ctypes.c_int32(burst_detection_enabled)
        error_code = self._library.RFmxWLAN_TXPCfgBurstDetectionEnabled(
            vi_ctype, selector_string_ctype, burst_detection_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_maximum_measurement_interval(
        self, selector_string, maximum_measurement_interval
    ):
        """txp_configure_maximum_measurement_interval."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        maximum_measurement_interval_ctype = ctypes.c_double(maximum_measurement_interval)
        error_code = self._library.RFmxWLAN_TXPCfgMaximumMeasurementInterval(
            vi_ctype, selector_string_ctype, maximum_measurement_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_acquisition_length(
        self, selector_string, acquisition_length_mode, acquisition_length
    ):
        """dsssmodacc_configure_acquisition_length."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        acquisition_length_mode_ctype = ctypes.c_int32(acquisition_length_mode)
        acquisition_length_ctype = ctypes.c_double(acquisition_length)
        error_code = self._library.RFmxWLAN_DSSSModAccCfgAcquisitionLength(
            vi_ctype, selector_string_ctype, acquisition_length_mode_ctype, acquisition_length_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """dsssmodacc_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxWLAN_DSSSModAccCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_evm_unit(self, selector_string, evm_unit):
        """dsssmodacc_configure_evm_unit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        evm_unit_ctype = ctypes.c_int32(evm_unit)
        error_code = self._library.RFmxWLAN_DSSSModAccCfgEVMUnit(
            vi_ctype, selector_string_ctype, evm_unit_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_measurement_length(
        self, selector_string, measurement_offset, maximum_measurement_length
    ):
        """dsssmodacc_configure_measurement_length."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_offset_ctype = ctypes.c_int32(measurement_offset)
        maximum_measurement_length_ctype = ctypes.c_int32(maximum_measurement_length)
        error_code = self._library.RFmxWLAN_DSSSModAccCfgMeasurementLength(
            vi_ctype,
            selector_string_ctype,
            measurement_offset_ctype,
            maximum_measurement_length_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_power_measurement_custom_gate_array(
        self, selector_string, start_time, stop_time
    ):
        """dsssmodacc_configure_power_measurement_custom_gate_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        start_time_ctype = _get_ctypes_pointer_for_buffer(
            value=start_time, library_type=ctypes.c_double
        )
        stop_time_ctype = _get_ctypes_pointer_for_buffer(
            value=stop_time, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["start_time", "stop_time"], start_time, stop_time
            )
        )
        error_code = self._library.RFmxWLAN_DSSSModAccCfgPowerMeasurementCustomGateArray(
            vi_ctype,
            selector_string_ctype,
            start_time_ctype,
            stop_time_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_power_measurement_enabled(
        self, selector_string, power_measurement_enabled
    ):
        """dsssmodacc_configure_power_measurement_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        power_measurement_enabled_ctype = ctypes.c_int32(power_measurement_enabled)
        error_code = self._library.RFmxWLAN_DSSSModAccCfgPowerMeasurementEnabled(
            vi_ctype, selector_string_ctype, power_measurement_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_configure_power_measurement_number_of_custom_gates(
        self, selector_string, number_of_custom_gates
    ):
        """dsssmodacc_configure_power_measurement_number_of_custom_gates."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_custom_gates_ctype = ctypes.c_int32(number_of_custom_gates)
        error_code = self._library.RFmxWLAN_DSSSModAccCfgPowerMeasurementNumberOfCustomGates(
            vi_ctype, selector_string_ctype, number_of_custom_gates_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def powerramp_configure_acquisition_length(self, selector_string, acquisition_length):
        """powerramp_configure_acquisition_length."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        acquisition_length_ctype = ctypes.c_double(acquisition_length)
        error_code = self._library.RFmxWLAN_PowerRampCfgAcquisitionLength(
            vi_ctype, selector_string_ctype, acquisition_length_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def powerramp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """powerramp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxWLAN_PowerRampCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_acquisition_length(
        self, selector_string, acquisition_length_mode, acquisition_length
    ):
        """ofdmmodacc_configure_acquisition_length."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        acquisition_length_mode_ctype = ctypes.c_int32(acquisition_length_mode)
        acquisition_length_ctype = ctypes.c_double(acquisition_length)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgAcquisitionLength(
            vi_ctype, selector_string_ctype, acquisition_length_mode_ctype, acquisition_length_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_amplitude_tracking_enabled(
        self, selector_string, amplitude_tracking_enabled
    ):
        """ofdmmodacc_configure_amplitude_tracking_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        amplitude_tracking_enabled_ctype = ctypes.c_int32(amplitude_tracking_enabled)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgAmplitudeTrackingEnabled(
            vi_ctype, selector_string_ctype, amplitude_tracking_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """ofdmmodacc_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_channel_estimation_type(
        self, selector_string, channel_estimation_type
    ):
        """ofdmmodacc_configure_channel_estimation_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        channel_estimation_type_ctype = ctypes.c_int32(channel_estimation_type)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgChannelEstimationType(
            vi_ctype, selector_string_ctype, channel_estimation_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_common_clock_source_enabled(
        self, selector_string, common_clock_source_enabled
    ):
        """ofdmmodacc_configure_common_clock_source_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        common_clock_source_enabled_ctype = ctypes.c_int32(common_clock_source_enabled)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgCommonClockSourceEnabled(
            vi_ctype, selector_string_ctype, common_clock_source_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_evm_unit(self, selector_string, evm_unit):
        """ofdmmodacc_configure_evm_unit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        evm_unit_ctype = ctypes.c_int32(evm_unit)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgEVMUnit(
            vi_ctype, selector_string_ctype, evm_unit_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_frequency_error_estimation_method(
        self, selector_string, frequency_error_estimation_method
    ):
        """ofdmmodacc_configure_frequency_error_estimation_method."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        frequency_error_estimation_method_ctype = ctypes.c_int32(frequency_error_estimation_method)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgFrequencyErrorEstimationMethod(
            vi_ctype, selector_string_ctype, frequency_error_estimation_method_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_measurement_length(
        self, selector_string, measurement_offset, maximum_measurement_length
    ):
        """ofdmmodacc_configure_measurement_length."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_offset_ctype = ctypes.c_int32(measurement_offset)
        maximum_measurement_length_ctype = ctypes.c_int32(maximum_measurement_length)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgMeasurementLength(
            vi_ctype,
            selector_string_ctype,
            measurement_offset_ctype,
            maximum_measurement_length_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_measurement_mode(self, selector_string, measurement_mode):
        """ofdmmodacc_configure_measurement_mode."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_mode_ctype = ctypes.c_int32(measurement_mode)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgMeasurementMode(
            vi_ctype, selector_string_ctype, measurement_mode_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_noise_compensation_enabled(
        self, selector_string, noise_compensation_enabled
    ):
        """ofdmmodacc_configure_noise_compensation_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_compensation_enabled_ctype = ctypes.c_int32(noise_compensation_enabled)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgNoiseCompensationEnabled(
            vi_ctype, selector_string_ctype, noise_compensation_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_optimize_dynamic_range_for_evm(
        self,
        selector_string,
        optimize_dynamic_range_for_evm_enabled,
        optimize_dynamic_range_for_evm_margin,
    ):
        """ofdmmodacc_configure_optimize_dynamic_range_for_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        optimize_dynamic_range_for_evm_enabled_ctype = ctypes.c_int32(
            optimize_dynamic_range_for_evm_enabled
        )
        optimize_dynamic_range_for_evm_margin_ctype = ctypes.c_double(
            optimize_dynamic_range_for_evm_margin
        )
        error_code = self._library.RFmxWLAN_OFDMModAccCfgOptimizeDynamicRangeForEVM(
            vi_ctype,
            selector_string_ctype,
            optimize_dynamic_range_for_evm_enabled_ctype,
            optimize_dynamic_range_for_evm_margin_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_phase_tracking_enabled(self, selector_string, phase_tracking_enabled):
        """ofdmmodacc_configure_phase_tracking_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        phase_tracking_enabled_ctype = ctypes.c_int32(phase_tracking_enabled)
        error_code = self._library.RFmxWLAN_OFDMModAccCfgPhaseTrackingEnabled(
            vi_ctype, selector_string_ctype, phase_tracking_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_symbol_clock_error_correction_enabled(
        self, selector_string, symbol_clock_error_correction_enabled
    ):
        """ofdmmodacc_configure_symbol_clock_error_correction_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        symbol_clock_error_correction_enabled_ctype = ctypes.c_int32(
            symbol_clock_error_correction_enabled
        )
        error_code = self._library.RFmxWLAN_OFDMModAccCfgSymbolClockErrorCorrectionEnabled(
            vi_ctype, selector_string_ctype, symbol_clock_error_correction_enabled_ctype
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
        error_code = self._library.RFmxWLAN_SEMCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_mask_type(self, selector_string, mask_type):
        """sem_configure_mask_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        mask_type_ctype = ctypes.c_int32(mask_type)
        error_code = self._library.RFmxWLAN_SEMCfgMaskType(
            vi_ctype, selector_string_ctype, mask_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """sem_configure_number_of_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_offsets_ctype = ctypes.c_int32(number_of_offsets)
        error_code = self._library.RFmxWLAN_SEMCfgNumberOfOffsets(
            vi_ctype, selector_string_ctype, number_of_offsets_ctype
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
        error_code = self._library.RFmxWLAN_SEMCfgOffsetFrequencyArray(
            vi_ctype,
            selector_string_ctype,
            offset_start_frequency_ctype,
            offset_stop_frequency_ctype,
            offset_sideband_ctype,
            number_of_elements_ctype,
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
        error_code = self._library.RFmxWLAN_SEMCfgOffsetRelativeLimitArray(
            vi_ctype,
            selector_string_ctype,
            relative_limit_start_ctype,
            relative_limit_stop_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_span(self, selector_string, span_auto, span):
        """sem_configure_span."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        span_auto_ctype = ctypes.c_int32(span_auto)
        span_ctype = ctypes.c_double(span)
        error_code = self._library.RFmxWLAN_SEMCfgSpan(
            vi_ctype, selector_string_ctype, span_auto_ctype, span_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_sweep_time(self, selector_string, sweep_time_auto, sweep_time_interval):
        """sem_configure_sweep_time."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        sweep_time_auto_ctype = ctypes.c_int32(sweep_time_auto)
        sweep_time_interval_ctype = ctypes.c_double(sweep_time_interval)
        error_code = self._library.RFmxWLAN_SEMCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_channel_bandwidth(self, selector_string, channel_bandwidth):
        """configure_channel_bandwidth."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        channel_bandwidth_ctype = ctypes.c_double(channel_bandwidth)
        error_code = self._library.RFmxWLAN_CfgChannelBandwidth(
            vi_ctype, selector_string_ctype, channel_bandwidth_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_external_attenuation(self, selector_string, external_attenuation):
        """configure_external_attenuation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        external_attenuation_ctype = ctypes.c_double(external_attenuation)
        error_code = self._library.RFmxWLAN_CfgExternalAttenuation(
            vi_ctype, selector_string_ctype, external_attenuation_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency_array(self, selector_string, center_frequency):
        """configure_frequency_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        center_frequency_ctype = _get_ctypes_pointer_for_buffer(
            value=center_frequency, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(center_frequency) if center_frequency is not None else 0
        )
        error_code = self._library.RFmxWLAN_CfgFrequencyArray(
            vi_ctype, selector_string_ctype, center_frequency_ctype, number_of_elements_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency(self, selector_string, center_frequency):
        """configure_frequency."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        center_frequency_ctype = ctypes.c_double(center_frequency)
        error_code = self._library.RFmxWLAN_CfgFrequency(
            vi_ctype, selector_string_ctype, center_frequency_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_number_of_frequency_segments_and_receive_chains(
        self, selector_string, number_of_frequency_segments, number_of_receive_chains
    ):
        """configure_number_of_frequency_segments_and_receive_chains."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_frequency_segments_ctype = ctypes.c_int32(number_of_frequency_segments)
        number_of_receive_chains_ctype = ctypes.c_int32(number_of_receive_chains)
        error_code = self._library.RFmxWLAN_CfgNumberOfFrequencySegmentsAndReceiveChains(
            vi_ctype,
            selector_string_ctype,
            number_of_frequency_segments_ctype,
            number_of_receive_chains_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_reference_level(self, selector_string, reference_level):
        """configure_reference_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        reference_level_ctype = ctypes.c_double(reference_level)
        error_code = self._library.RFmxWLAN_CfgReferenceLevel(
            vi_ctype, selector_string_ctype, reference_level_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_standard(self, selector_string, standard):
        """configure_standard."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        standard_ctype = ctypes.c_int32(standard)
        error_code = self._library.RFmxWLAN_CfgStandard(
            vi_ctype, selector_string_ctype, standard_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        average_power_mean_ctype = ctypes.c_double()
        peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_TXPFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_power_mean_ctype,
            peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return average_power_mean_ctype.value, peak_power_maximum_ctype.value, error_code

    def dsssmodacc_fetch_average_powers(self, selector_string, timeout):
        """dsssmodacc_fetch_average_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        preamble_average_power_mean_ctype = ctypes.c_double()
        header_average_power_mean_ctype = ctypes.c_double()
        data_average_power_mean_ctype = ctypes.c_double()
        ppdu_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_DSSSModAccFetchAveragePowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            preamble_average_power_mean_ctype,
            header_average_power_mean_ctype,
            data_average_power_mean_ctype,
            ppdu_average_power_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            preamble_average_power_mean_ctype.value,
            header_average_power_mean_ctype.value,
            data_average_power_mean_ctype.value,
            ppdu_average_power_mean_ctype.value,
            error_code,
        )

    def dsssmodacc_fetch_evm(self, selector_string, timeout):
        """dsssmodacc_fetch_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rms_evm_mean_ctype = ctypes.c_double()
        peak_evm_80211_2016_maximum_ctype = ctypes.c_double()
        peak_evm_80211_2007_maximum_ctype = ctypes.c_double()
        peak_evm_80211_1999_maximum_ctype = ctypes.c_double()
        frequency_error_mean_ctype = ctypes.c_double()
        chip_clock_error_mean_ctype = ctypes.c_double()
        number_of_chips_used_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_DSSSModAccFetchEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rms_evm_mean_ctype,
            peak_evm_80211_2016_maximum_ctype,
            peak_evm_80211_2007_maximum_ctype,
            peak_evm_80211_1999_maximum_ctype,
            frequency_error_mean_ctype,
            chip_clock_error_mean_ctype,
            number_of_chips_used_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rms_evm_mean_ctype.value,
            peak_evm_80211_2016_maximum_ctype.value,
            peak_evm_80211_2007_maximum_ctype.value,
            peak_evm_80211_1999_maximum_ctype.value,
            frequency_error_mean_ctype.value,
            chip_clock_error_mean_ctype.value,
            number_of_chips_used_ctype.value,
            error_code,
        )

    def dsssmodacc_fetch_iq_impairments(self, selector_string, timeout):
        """dsssmodacc_fetch_iq_impairments."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        iq_origin_offset_mean_ctype = ctypes.c_double()
        iq_gain_imbalance_mean_ctype = ctypes.c_double()
        iq_quadrature_error_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_DSSSModAccFetchIQImpairments(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            iq_origin_offset_mean_ctype,
            iq_gain_imbalance_mean_ctype,
            iq_quadrature_error_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            iq_origin_offset_mean_ctype.value,
            iq_gain_imbalance_mean_ctype.value,
            iq_quadrature_error_mean_ctype.value,
            error_code,
        )

    def dsssmodacc_fetch_peak_powers(self, selector_string, timeout):
        """dsssmodacc_fetch_peak_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        preamble_peak_power_maximum_ctype = ctypes.c_double()
        header_peak_power_maximum_ctype = ctypes.c_double()
        data_peak_power_maximum_ctype = ctypes.c_double()
        ppdu_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_DSSSModAccFetchPeakPowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            preamble_peak_power_maximum_ctype,
            header_peak_power_maximum_ctype,
            data_peak_power_maximum_ctype,
            ppdu_peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            preamble_peak_power_maximum_ctype.value,
            header_peak_power_maximum_ctype.value,
            data_peak_power_maximum_ctype.value,
            ppdu_peak_power_maximum_ctype.value,
            error_code,
        )

    def dsssmodacc_fetch_ppdu_information(self, selector_string, timeout):
        """dsssmodacc_fetch_ppdu_information."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        data_modulation_format_ctype = ctypes.c_int32()
        payload_length_ctype = ctypes.c_int32()
        preamble_type_ctype = ctypes.c_int32()
        locked_clocks_bit_ctype = ctypes.c_int32()
        header_crc_status_ctype = ctypes.c_int32()
        psdu_crc_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_DSSSModAccFetchPPDUInformation(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            data_modulation_format_ctype,
            payload_length_ctype,
            preamble_type_ctype,
            locked_clocks_bit_ctype,
            header_crc_status_ctype,
            psdu_crc_status_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.DsssModAccDataModulationFormat(data_modulation_format_ctype.value),
            payload_length_ctype.value,
            enums.DsssModAccPreambleType(preamble_type_ctype.value),
            locked_clocks_bit_ctype.value,
            enums.DsssModAccPayloadHeaderCrcStatus(header_crc_status_ctype.value),
            enums.DsssModAccPsduCrcStatus(psdu_crc_status_ctype.value),
            error_code,
        )

    def powerramp_fetch_measurement(self, selector_string, timeout):
        """powerramp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rise_time_mean_ctype = ctypes.c_double()
        fall_time_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_PowerRampFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rise_time_mean_ctype,
            fall_time_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return rise_time_mean_ctype.value, fall_time_mean_ctype.value, error_code

    def ofdmmodacc_fetch_chain_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_chain_rms_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        chain_rms_evm_mean_ctype = ctypes.c_double()
        chain_data_rms_evm_mean_ctype = ctypes.c_double()
        chain_pilot_rms_evm_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainRMSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            chain_rms_evm_mean_ctype,
            chain_data_rms_evm_mean_ctype,
            chain_pilot_rms_evm_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            chain_rms_evm_mean_ctype.value,
            chain_data_rms_evm_mean_ctype.value,
            chain_pilot_rms_evm_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_composite_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_composite_rms_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        composite_rms_evm_mean_ctype = ctypes.c_double()
        composite_data_rms_evm_mean_ctype = ctypes.c_double()
        composite_pilot_rms_evm_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchCompositeRMSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            composite_rms_evm_mean_ctype,
            composite_data_rms_evm_mean_ctype,
            composite_pilot_rms_evm_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            composite_rms_evm_mean_ctype.value,
            composite_data_rms_evm_mean_ctype.value,
            composite_pilot_rms_evm_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_cross_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_cross_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        cross_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchCrossPower(
            vi_ctype, selector_string_ctype, timeout_ctype, cross_power_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return cross_power_mean_ctype.value, error_code

    def ofdmmodacc_fetch_data_average_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_data_average_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        data_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDataAveragePower(
            vi_ctype, selector_string_ctype, timeout_ctype, data_average_power_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return data_average_power_mean_ctype.value, error_code

    def ofdmmodacc_fetch_data_peak_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_data_peak_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        data_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDataPeakPower(
            vi_ctype, selector_string_ctype, timeout_ctype, data_peak_power_maximum_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return data_peak_power_maximum_ctype.value, error_code

    def ofdmmodacc_fetch_frequency_error_ccdf_10_percent(self, selector_string, timeout):
        """ofdmmodacc_fetch_frequency_error_ccdf_10_percent."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        frequency_error_ccdf_10_percent_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchFrequencyErrorCCDF10Percent(
            vi_ctype, selector_string_ctype, timeout_ctype, frequency_error_ccdf_10_percent_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return frequency_error_ccdf_10_percent_ctype.value, error_code

    def ofdmmodacc_fetch_frequency_error_mean(self, selector_string, timeout):
        """ofdmmodacc_fetch_frequency_error_mean."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        frequency_error_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchFrequencyErrorMean(
            vi_ctype, selector_string_ctype, timeout_ctype, frequency_error_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return frequency_error_mean_ctype.value, error_code

    def ofdmmodacc_fetch_guard_interval_type(self, selector_string, timeout):
        """ofdmmodacc_fetch_guard_interval_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        guard_interval_type_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchGuardIntervalType(
            vi_ctype, selector_string_ctype, timeout_ctype, guard_interval_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmGuardIntervalType(guard_interval_type_ctype.value), error_code

    def ofdmmodacc_fetch_ltf_size(self, selector_string, timeout):
        """ofdmmodacc_fetch_ltf_size."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ltf_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchLTFSize(
            vi_ctype, selector_string_ctype, timeout_ctype, ltf_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmLtfSize(ltf_size_ctype.value), error_code

    def ofdmmodacc_fetch_iq_impairments(self, selector_string, timeout):
        """ofdmmodacc_fetch_iq_impairments."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        relative_iq_origin_offset_mean_ctype = ctypes.c_double()
        iq_gain_imbalance_mean_ctype = ctypes.c_double()
        iq_quadrature_error_mean_ctype = ctypes.c_double()
        absolute_iq_origin_offset_mean_ctype = ctypes.c_double()
        iq_timing_skew_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchIQImpairments(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            relative_iq_origin_offset_mean_ctype,
            iq_gain_imbalance_mean_ctype,
            iq_quadrature_error_mean_ctype,
            absolute_iq_origin_offset_mean_ctype,
            iq_timing_skew_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            relative_iq_origin_offset_mean_ctype.value,
            iq_gain_imbalance_mean_ctype.value,
            iq_quadrature_error_mean_ctype.value,
            absolute_iq_origin_offset_mean_ctype.value,
            iq_timing_skew_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_l_sig_parity_check_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_l_sig_parity_check_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        l_sig_parity_check_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchLSIGParityCheckStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, l_sig_parity_check_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.OfdmModAccLSigParityCheckStatus(l_sig_parity_check_status_ctype.value),
            error_code,
        )

    def ofdmmodacc_fetch_mcs_index(self, selector_string, timeout):
        """ofdmmodacc_fetch_mcs_index."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        mcs_index_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchMCSIndex(
            vi_ctype, selector_string_ctype, timeout_ctype, mcs_index_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return mcs_index_ctype.value, error_code

    def ofdmmodacc_fetch_number_of_he_sig_b_symbols(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_he_sig_b_symbols."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        number_of_he_sig_b_symbols_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchNumberOfHESIGBSymbols(
            vi_ctype, selector_string_ctype, timeout_ctype, number_of_he_sig_b_symbols_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return number_of_he_sig_b_symbols_ctype.value, error_code

    def ofdmmodacc_fetch_number_of_space_time_streams(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_space_time_streams."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        number_of_space_time_streams_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchNumberOfSpaceTimeStreams(
            vi_ctype, selector_string_ctype, timeout_ctype, number_of_space_time_streams_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return number_of_space_time_streams_ctype.value, error_code

    def ofdmmodacc_fetch_number_of_symbols_used(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_symbols_used."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        number_of_symbols_used_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchNumberofSymbolsUsed(
            vi_ctype, selector_string_ctype, timeout_ctype, number_of_symbols_used_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return number_of_symbols_used_ctype.value, error_code

    def ofdmmodacc_fetch_number_of_users(self, selector_string, timeout):
        """ofdmmodacc_fetch_number_of_users."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        number_of_users_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchNumberOfUsers(
            vi_ctype, selector_string_ctype, timeout_ctype, number_of_users_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return number_of_users_ctype.value, error_code

    def ofdmmodacc_fetch_pe_average_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_pe_average_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pe_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPEAveragePower(
            vi_ctype, selector_string_ctype, timeout_ctype, pe_average_power_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pe_average_power_mean_ctype.value, error_code

    def ofdmmodacc_fetch_pe_peak_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_pe_peak_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pe_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPEPeakPower(
            vi_ctype, selector_string_ctype, timeout_ctype, pe_peak_power_maximum_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pe_peak_power_maximum_ctype.value, error_code

    def ofdmmodacc_fetch_ppdu_average_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_ppdu_average_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ppdu_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPPDUAveragePower(
            vi_ctype, selector_string_ctype, timeout_ctype, ppdu_average_power_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return ppdu_average_power_mean_ctype.value, error_code

    def ofdmmodacc_fetch_ppdu_peak_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_ppdu_peak_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ppdu_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPPDUPeakPower(
            vi_ctype, selector_string_ctype, timeout_ctype, ppdu_peak_power_maximum_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return ppdu_peak_power_maximum_ctype.value, error_code

    def ofdmmodacc_fetch_ppdu_type(self, selector_string, timeout):
        """ofdmmodacc_fetch_ppdu_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ppdu_type_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPPDUType(
            vi_ctype, selector_string_ctype, timeout_ctype, ppdu_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmPpduType(ppdu_type_ctype.value), error_code

    def ofdmmodacc_fetch_preamble_average_powers_802_11ac(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11ac."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        vht_sig_a_average_power_mean_ctype = ctypes.c_double()
        vht_stf_average_power_mean_ctype = ctypes.c_double()
        vht_ltf_average_power_mean_ctype = ctypes.c_double()
        vht_sig_b_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ac(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            vht_sig_a_average_power_mean_ctype,
            vht_stf_average_power_mean_ctype,
            vht_ltf_average_power_mean_ctype,
            vht_sig_b_average_power_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            vht_sig_a_average_power_mean_ctype.value,
            vht_stf_average_power_mean_ctype.value,
            vht_ltf_average_power_mean_ctype.value,
            vht_sig_b_average_power_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_average_powers_802_11ax(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11ax."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rl_sig_average_power_mean_ctype = ctypes.c_double()
        he_sig_a_average_power_mean_ctype = ctypes.c_double()
        he_sig_b_average_power_mean_ctype = ctypes.c_double()
        he_stf_average_power_mean_ctype = ctypes.c_double()
        he_ltf_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11ax(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rl_sig_average_power_mean_ctype,
            he_sig_a_average_power_mean_ctype,
            he_sig_b_average_power_mean_ctype,
            he_stf_average_power_mean_ctype,
            he_ltf_average_power_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rl_sig_average_power_mean_ctype.value,
            he_sig_a_average_power_mean_ctype.value,
            he_sig_b_average_power_mean_ctype.value,
            he_stf_average_power_mean_ctype.value,
            he_ltf_average_power_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_average_powers_802_11be(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11be."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rl_sig_average_power_mean_ctype = ctypes.c_double()
        u_sig_average_power_mean_ctype = ctypes.c_double()
        eht_sig_average_power_mean_ctype = ctypes.c_double()
        eht_stf_average_power_mean_ctype = ctypes.c_double()
        eht_ltf_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11be(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rl_sig_average_power_mean_ctype,
            u_sig_average_power_mean_ctype,
            eht_sig_average_power_mean_ctype,
            eht_stf_average_power_mean_ctype,
            eht_ltf_average_power_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rl_sig_average_power_mean_ctype.value,
            u_sig_average_power_mean_ctype.value,
            eht_sig_average_power_mean_ctype.value,
            eht_stf_average_power_mean_ctype.value,
            eht_ltf_average_power_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_average_powers_802_11n(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_802_11n."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ht_sig_average_power_mean_ctype = ctypes.c_double()
        ht_stf_average_power_mean_ctype = ctypes.c_double()
        ht_dltf_average_power_mean_ctype = ctypes.c_double()
        ht_eltf_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleAveragePowers802_11n(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            ht_sig_average_power_mean_ctype,
            ht_stf_average_power_mean_ctype,
            ht_dltf_average_power_mean_ctype,
            ht_eltf_average_power_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            ht_sig_average_power_mean_ctype.value,
            ht_stf_average_power_mean_ctype.value,
            ht_dltf_average_power_mean_ctype.value,
            ht_eltf_average_power_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_average_powers_common(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_average_powers_common."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        l_stf_average_power_mean_ctype = ctypes.c_double()
        l_ltf_average_power_mean_ctype = ctypes.c_double()
        l_sig_average_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleAveragePowersCommon(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            l_stf_average_power_mean_ctype,
            l_ltf_average_power_mean_ctype,
            l_sig_average_power_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            l_stf_average_power_mean_ctype.value,
            l_ltf_average_power_mean_ctype.value,
            l_sig_average_power_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11ac(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11ac."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        vht_sig_a_peak_power_maximum_ctype = ctypes.c_double()
        vht_stf_peak_power_maximum_ctype = ctypes.c_double()
        vht_ltf_peak_power_maximum_ctype = ctypes.c_double()
        vht_sig_b_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ac(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            vht_sig_a_peak_power_maximum_ctype,
            vht_stf_peak_power_maximum_ctype,
            vht_ltf_peak_power_maximum_ctype,
            vht_sig_b_peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            vht_sig_a_peak_power_maximum_ctype.value,
            vht_stf_peak_power_maximum_ctype.value,
            vht_ltf_peak_power_maximum_ctype.value,
            vht_sig_b_peak_power_maximum_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11ax(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11ax."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rl_sig_peak_power_maximum_ctype = ctypes.c_double()
        he_sig_a_peak_power_maximum_ctype = ctypes.c_double()
        he_sig_b_peak_power_maximum_ctype = ctypes.c_double()
        he_stf_peak_power_maximum_ctype = ctypes.c_double()
        he_ltf_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11ax(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rl_sig_peak_power_maximum_ctype,
            he_sig_a_peak_power_maximum_ctype,
            he_sig_b_peak_power_maximum_ctype,
            he_stf_peak_power_maximum_ctype,
            he_ltf_peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rl_sig_peak_power_maximum_ctype.value,
            he_sig_a_peak_power_maximum_ctype.value,
            he_sig_b_peak_power_maximum_ctype.value,
            he_stf_peak_power_maximum_ctype.value,
            he_ltf_peak_power_maximum_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11be(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11be."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        rl_sig_peak_power_maximum_ctype = ctypes.c_double()
        u_sig_peak_power_maximum_ctype = ctypes.c_double()
        eht_sig_peak_power_maximum_ctype = ctypes.c_double()
        eht_stf_peak_power_maximum_ctype = ctypes.c_double()
        eht_ltf_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11be(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rl_sig_peak_power_maximum_ctype,
            u_sig_peak_power_maximum_ctype,
            eht_sig_peak_power_maximum_ctype,
            eht_stf_peak_power_maximum_ctype,
            eht_ltf_peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            rl_sig_peak_power_maximum_ctype.value,
            u_sig_peak_power_maximum_ctype.value,
            eht_sig_peak_power_maximum_ctype.value,
            eht_stf_peak_power_maximum_ctype.value,
            eht_ltf_peak_power_maximum_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_802_11n(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_802_11n."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ht_sig_peak_power_maximum_ctype = ctypes.c_double()
        ht_stf_peak_power_maximum_ctype = ctypes.c_double()
        ht_dltf_peak_power_maximum_ctype = ctypes.c_double()
        ht_eltf_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreamblePeakPowers802_11n(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            ht_sig_peak_power_maximum_ctype,
            ht_stf_peak_power_maximum_ctype,
            ht_dltf_peak_power_maximum_ctype,
            ht_eltf_peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            ht_sig_peak_power_maximum_ctype.value,
            ht_stf_peak_power_maximum_ctype.value,
            ht_dltf_peak_power_maximum_ctype.value,
            ht_eltf_peak_power_maximum_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_preamble_peak_powers_common(self, selector_string, timeout):
        """ofdmmodacc_fetch_preamble_peak_powers_common."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        l_stf_peak_power_maximum_ctype = ctypes.c_double()
        l_ltf_peak_power_maximum_ctype = ctypes.c_double()
        l_sig_peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreamblePeakPowersCommon(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            l_stf_peak_power_maximum_ctype,
            l_ltf_peak_power_maximum_ctype,
            l_sig_peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            l_stf_peak_power_maximum_ctype.value,
            l_ltf_peak_power_maximum_ctype.value,
            l_sig_peak_power_maximum_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_psdu_crc_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_psdu_crc_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        psdu_crc_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPSDUCRCStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, psdu_crc_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmModAccPsduCrcStatus(psdu_crc_status_ctype.value), error_code

    def ofdmmodacc_fetch_pe_duration(self, selector_string, timeout):
        """ofdmmodacc_fetch_pe_duration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        pe_duration_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPEDuration(
            vi_ctype, selector_string_ctype, timeout_ctype, pe_duration_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return pe_duration_ctype.value, error_code

    def ofdmmodacc_fetch_ru_offset_and_size(self, selector_string, timeout):
        """ofdmmodacc_fetch_ru_offset_and_size."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        ru_offset_ctype = ctypes.c_int32()
        ru_size_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchRUOffsetAndSize(
            vi_ctype, selector_string_ctype, timeout_ctype, ru_offset_ctype, ru_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return ru_offset_ctype.value, ru_size_ctype.value, error_code

    def ofdmmodacc_fetch_sig_crc_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_sig_crc_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        sig_crc_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSIGCRCStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, sig_crc_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmModAccSigCrcStatus(sig_crc_status_ctype.value), error_code

    def ofdmmodacc_fetch_sig_b_crc_status(self, selector_string, timeout):
        """ofdmmodacc_fetch_sig_b_crc_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        sig_b_crc_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSIGBCRCStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, sig_b_crc_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.OfdmModAccSigBCrcStatus(sig_b_crc_status_ctype.value), error_code

    def ofdmmodacc_fetch_spectral_flatness(self, selector_string, timeout):
        """ofdmmodacc_fetch_spectral_flatness."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        spectral_flatness_margin_ctype = ctypes.c_double()
        spectral_flatness_margin_subcarrier_index_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSpectralFlatness(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            spectral_flatness_margin_ctype,
            spectral_flatness_margin_subcarrier_index_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            spectral_flatness_margin_ctype.value,
            spectral_flatness_margin_subcarrier_index_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_stream_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_stream_rms_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        stream_rms_evm_mean_ctype = ctypes.c_double()
        stream_data_rms_evm_mean_ctype = ctypes.c_double()
        stream_pilot_rms_evm_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamRMSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            stream_rms_evm_mean_ctype,
            stream_data_rms_evm_mean_ctype,
            stream_pilot_rms_evm_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            stream_rms_evm_mean_ctype.value,
            stream_data_rms_evm_mean_ctype.value,
            stream_pilot_rms_evm_mean_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_symbol_clock_error_mean(self, selector_string, timeout):
        """ofdmmodacc_fetch_symbol_clock_error_mean."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        symbol_clock_error_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSymbolClockErrorMean(
            vi_ctype, selector_string_ctype, timeout_ctype, symbol_clock_error_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return symbol_clock_error_mean_ctype.value, error_code

    def ofdmmodacc_fetch_unused_tone_error(self, selector_string, timeout):
        """ofdmmodacc_fetch_unused_tone_error."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        unused_tone_error_margin_ctype = ctypes.c_double()
        unused_tone_error_margin_ru_index_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUnusedToneError(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            unused_tone_error_margin_ctype,
            unused_tone_error_margin_ru_index_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            unused_tone_error_margin_ctype.value,
            unused_tone_error_margin_ru_index_ctype.value,
            error_code,
        )

    def ofdmmodacc_fetch_user_power(self, selector_string, timeout):
        """ofdmmodacc_fetch_user_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        user_power_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserPower(
            vi_ctype, selector_string_ctype, timeout_ctype, user_power_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return user_power_mean_ctype.value, error_code

    def ofdmmodacc_fetch_user_stream_rms_evm(self, selector_string, timeout):
        """ofdmmodacc_fetch_user_stream_rms_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        user_stream_rms_evm_mean_ctype = ctypes.c_double()
        user_stream_data_rms_evm_mean_ctype = ctypes.c_double()
        user_stream_pilot_rms_evm_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            user_stream_rms_evm_mean_ctype,
            user_stream_data_rms_evm_mean_ctype,
            user_stream_pilot_rms_evm_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            user_stream_rms_evm_mean_ctype.value,
            user_stream_data_rms_evm_mean_ctype.value,
            user_stream_pilot_rms_evm_mean_ctype.value,
            error_code,
        )

    def sem_fetch_carrier_measurement(self, selector_string, timeout):
        """sem_fetch_carrier_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_power_ctype = ctypes.c_double()
        relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_SEMFetchCarrierMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_power_ctype.value, relative_power_ctype.value, error_code

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
        error_code = self._library.RFmxWLAN_SEMFetchLowerOffsetMargin(
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
        total_absolute_power_ctype = ctypes.c_double()
        total_relative_power_ctype = ctypes.c_double()
        peak_absolute_power_ctype = ctypes.c_double()
        peak_frequency_ctype = ctypes.c_double()
        peak_relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_SEMFetchLowerOffsetPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            total_absolute_power_ctype,
            total_relative_power_ctype,
            peak_absolute_power_ctype,
            peak_frequency_ctype,
            peak_relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            total_absolute_power_ctype.value,
            total_relative_power_ctype.value,
            peak_absolute_power_ctype.value,
            peak_frequency_ctype.value,
            peak_relative_power_ctype.value,
            error_code,
        )

    def sem_fetch_measurement_status(self, selector_string, timeout):
        """sem_fetch_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxWLAN_SEMFetchMeasurementStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, measurement_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.SemMeasurementStatus(measurement_status_ctype.value), error_code

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
        error_code = self._library.RFmxWLAN_SEMFetchUpperOffsetMargin(
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
        total_absolute_power_ctype = ctypes.c_double()
        total_relative_power_ctype = ctypes.c_double()
        peak_absolute_power_ctype = ctypes.c_double()
        peak_frequency_ctype = ctypes.c_double()
        peak_relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxWLAN_SEMFetchUpperOffsetPower(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            total_absolute_power_ctype,
            total_relative_power_ctype,
            peak_absolute_power_ctype,
            peak_frequency_ctype,
            peak_relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            total_absolute_power_ctype.value,
            total_relative_power_ctype.value,
            peak_absolute_power_ctype.value,
            peak_frequency_ctype.value,
            peak_relative_power_ctype.value,
            error_code,
        )

    def txp_fetch_power_trace(self, selector_string, timeout, power):
        """txp_fetch_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_TXPFetchPowerTrace(
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
        error_code = self._library.RFmxWLAN_TXPFetchPowerTrace(
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

    def dsssmodacc_fetch_constellation_trace(self, selector_string, timeout, constellation):
        """dsssmodacc_fetch_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(constellation, "constellation", "complex64")
        if len(constellation) != actual_array_size_ctype.value:
            constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def dsssmodacc_fetch_custom_gate_powers_array(self, selector_string, timeout):
        """dsssmodacc_fetch_custom_gate_powers_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        average_power_mean_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_power_maximum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchCustomGatePowersArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_power_mean_ctype,
            peak_power_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return average_power_mean_ctype[:], peak_power_maximum_ctype[:], error_code

    def dsssmodacc_fetch_decoded_header_bits_trace(self, selector_string, timeout):
        """dsssmodacc_fetch_decoded_header_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_header_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchDecodedHeaderBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_header_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_header_bits_ctype[:], error_code

    def dsssmodacc_fetch_decoded_psdu_bits_trace(self, selector_string, timeout):
        """dsssmodacc_fetch_decoded_psdu_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_psdu_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchDecodedPSDUBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_psdu_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_psdu_bits_ctype[:], error_code

    def dsssmodacc_fetch_evm_per_chip_mean_trace(self, selector_string, timeout, evm_per_chip_mean):
        """dsssmodacc_fetch_evm_per_chip_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace(
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
        _helper.validate_numpy_array(evm_per_chip_mean, "evm_per_chip_mean", "float32")
        if len(evm_per_chip_mean) != actual_array_size_ctype.value:
            evm_per_chip_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        evm_per_chip_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=evm_per_chip_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_DSSSModAccFetchEVMPerChipMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            evm_per_chip_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def powerramp_fetch_fall_trace(
        self, selector_string, timeout, raw_waveform, processed_waveform, threshold, power_reference
    ):
        """powerramp_fetch_fall_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_PowerRampFetchFallTrace(
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

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(raw_waveform, "raw_waveform", "float32")
        if len(raw_waveform) != actual_array_size_ctype.value:
            raw_waveform.resize((actual_array_size_ctype.value,), refcheck=False)
        raw_waveform_ctype = _get_ctypes_pointer_for_buffer(
            value=raw_waveform, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(processed_waveform, "processed_waveform", "float32")
        if len(processed_waveform) != actual_array_size_ctype.value:
            processed_waveform.resize((actual_array_size_ctype.value,), refcheck=False)
        processed_waveform_ctype = _get_ctypes_pointer_for_buffer(
            value=processed_waveform, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(threshold, "threshold", "float32")
        if len(threshold) != actual_array_size_ctype.value:
            threshold.resize((actual_array_size_ctype.value,), refcheck=False)
        threshold_ctype = _get_ctypes_pointer_for_buffer(
            value=threshold, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(power_reference, "power_reference", "float32")
        if len(power_reference) != actual_array_size_ctype.value:
            power_reference.resize((actual_array_size_ctype.value,), refcheck=False)
        power_reference_ctype = _get_ctypes_pointer_for_buffer(
            value=power_reference, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_PowerRampFetchFallTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            raw_waveform_ctype,
            processed_waveform_ctype,
            threshold_ctype,
            power_reference_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def powerramp_fetch_rise_trace(
        self, selector_string, timeout, raw_waveform, processed_waveform, threshold, power_reference
    ):
        """powerramp_fetch_rise_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_PowerRampFetchRiseTrace(
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

        x0_ctype = ctypes.c_double()
        dx_ctype = ctypes.c_double()
        _helper.validate_numpy_array(raw_waveform, "raw_waveform", "float32")
        if len(raw_waveform) != actual_array_size_ctype.value:
            raw_waveform.resize((actual_array_size_ctype.value,), refcheck=False)
        raw_waveform_ctype = _get_ctypes_pointer_for_buffer(
            value=raw_waveform, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(processed_waveform, "processed_waveform", "float32")
        if len(processed_waveform) != actual_array_size_ctype.value:
            processed_waveform.resize((actual_array_size_ctype.value,), refcheck=False)
        processed_waveform_ctype = _get_ctypes_pointer_for_buffer(
            value=processed_waveform, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(threshold, "threshold", "float32")
        if len(threshold) != actual_array_size_ctype.value:
            threshold.resize((actual_array_size_ctype.value,), refcheck=False)
        threshold_ctype = _get_ctypes_pointer_for_buffer(
            value=threshold, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(power_reference, "power_reference", "float32")
        if len(power_reference) != actual_array_size_ctype.value:
            power_reference.resize((actual_array_size_ctype.value,), refcheck=False)
        power_reference_ctype = _get_ctypes_pointer_for_buffer(
            value=power_reference, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_PowerRampFetchRiseTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            raw_waveform_ctype,
            processed_waveform_ctype,
            threshold_ctype,
            power_reference_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_chain_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_data_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_chain_data_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace(
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
            chain_data_rms_evm_per_symbol_mean, "chain_data_rms_evm_per_symbol_mean", "float32"
        )
        if len(chain_data_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            chain_data_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        chain_data_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=chain_data_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainDataRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            chain_data_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_chain_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_pilot_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_chain_pilot_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace(
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
            chain_pilot_rms_evm_per_symbol_mean, "chain_pilot_rms_evm_per_symbol_mean", "float32"
        )
        if len(chain_pilot_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            chain_pilot_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        chain_pilot_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=chain_pilot_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainPilotRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            chain_pilot_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_chain_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, chain_rms_evm_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_chain_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace(
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
            chain_rms_evm_per_subcarrier_mean, "chain_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(chain_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            chain_rms_evm_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        chain_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=chain_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            chain_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_chain_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_chain_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace(
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
            chain_rms_evm_per_symbol_mean, "chain_rms_evm_per_symbol_mean", "float32"
        )
        if len(chain_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            chain_rms_evm_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        chain_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=chain_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChainRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            chain_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_channel_frequency_response_mean_trace(
        self,
        selector_string,
        timeout,
        channel_frequency_response_mean_magnitude,
        channel_frequency_response_mean_phase,
    ):
        """ofdmmodacc_fetch_channel_frequency_response_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace(
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
        _helper.validate_numpy_array(
            channel_frequency_response_mean_magnitude,
            "channel_frequency_response_mean_magnitude",
            "float32",
        )
        if len(channel_frequency_response_mean_magnitude) != actual_array_size_ctype.value:
            channel_frequency_response_mean_magnitude.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        channel_frequency_response_mean_magnitude_ctype = _get_ctypes_pointer_for_buffer(
            value=channel_frequency_response_mean_magnitude, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(
            channel_frequency_response_mean_phase,
            "channel_frequency_response_mean_phase",
            "float32",
        )
        if len(channel_frequency_response_mean_phase) != actual_array_size_ctype.value:
            channel_frequency_response_mean_phase.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        channel_frequency_response_mean_phase_ctype = _get_ctypes_pointer_for_buffer(
            value=channel_frequency_response_mean_phase, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchChannelFrequencyResponseMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            channel_frequency_response_mean_magnitude_ctype,
            channel_frequency_response_mean_phase_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_group_delay_mean_trace(self, selector_string, timeout, group_delay_mean):
        """ofdmmodacc_fetch_group_delay_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace(
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
        _helper.validate_numpy_array(group_delay_mean, "group_delay_mean", "float32")
        if len(group_delay_mean) != actual_array_size_ctype.value:
            group_delay_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        group_delay_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=group_delay_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchGroupDelayMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            group_delay_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_common_pilot_error_trace(
        self, selector_string, timeout, common_pilot_error_magnitude, common_pilot_error_phase
    ):
        """ofdmmodacc_fetch_common_pilot_error_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace(
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
        _helper.validate_numpy_array(
            common_pilot_error_magnitude, "common_pilot_error_magnitude", "float32"
        )
        if len(common_pilot_error_magnitude) != actual_array_size_ctype.value:
            common_pilot_error_magnitude.resize((actual_array_size_ctype.value,), refcheck=False)
        common_pilot_error_magnitude_ctype = _get_ctypes_pointer_for_buffer(
            value=common_pilot_error_magnitude, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(
            common_pilot_error_phase, "common_pilot_error_phase", "float32"
        )
        if len(common_pilot_error_phase) != actual_array_size_ctype.value:
            common_pilot_error_phase.resize((actual_array_size_ctype.value,), refcheck=False)
        common_pilot_error_phase_ctype = _get_ctypes_pointer_for_buffer(
            value=common_pilot_error_phase, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchCommonPilotErrorTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            common_pilot_error_magnitude_ctype,
            common_pilot_error_phase_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_custom_gate_powers_array(self, selector_string, timeout):
        """ofdmmodacc_fetch_custom_gate_powers_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        average_power_mean_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_power_maximum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchCustomGatePowersArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_power_mean_ctype,
            peak_power_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return average_power_mean_ctype[:], peak_power_maximum_ctype[:], error_code

    def ofdmmodacc_fetch_data_constellation_trace(
        self, selector_string, timeout, data_constellation
    ):
        """ofdmmodacc_fetch_data_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDataConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(data_constellation, "data_constellation", "complex64")
        if len(data_constellation) != actual_array_size_ctype.value:
            data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=data_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDataConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            data_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_fetch_reference_data_constellation_trace(
        self, selector_string, timeout, reference_data_constellation
    ):
        """ofdmmodacc_fetch_reference_data_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            reference_data_constellation, "reference_data_constellation", "complex64"
        )
        if len(reference_data_constellation) != actual_array_size_ctype.value:
            reference_data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        reference_data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=reference_data_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchReferenceDataConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            reference_data_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_fetch_decoded_l_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_l_sig_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_l_sig_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedLSIGBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_l_sig_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_l_sig_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_psdu_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_psdu_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_psdu_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedPSDUBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_psdu_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_psdu_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_service_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_service_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_service_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedServiceBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_service_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_service_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_sig_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_sig_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedSIGBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_sig_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_sig_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_sig_b_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_sig_b_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_sig_b_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedSIGBBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_sig_b_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_sig_b_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_u_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_u_sig_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_u_sig_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedUSIGBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_u_sig_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_u_sig_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_eht_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_eht_sig_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_eht_sig_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedEHTSIGBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_eht_sig_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_eht_sig_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_uhr_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_uhr_sig_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_uhr_sig_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedUHRSIGBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_uhr_sig_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_uhr_sig_bits_ctype[:], error_code

    def ofdmmodacc_fetch_decoded_elr_sig_bits_trace(self, selector_string, timeout):
        """ofdmmodacc_fetch_decoded_elr_sig_bits_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        decoded_elr_sig_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchDecodedELRSIGBitsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            decoded_elr_sig_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return decoded_elr_sig_bits_ctype[:], error_code

    def ofdmmodacc_fetch_evm_subcarrier_indices(self, selector_string, timeout):
        """ofdmmodacc_fetch_evm_subcarrier_indices."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        subcarrier_indices_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int32, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchEVMSubcarrierIndices(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subcarrier_indices_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return subcarrier_indices_ctype[:], error_code

    def ofdmmodacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace(
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
            iq_gain_imbalance_per_subcarrier_mean,
            "iq_gain_imbalance_per_subcarrier_mean",
            "float32",
        )
        if len(iq_gain_imbalance_per_subcarrier_mean) != actual_array_size_ctype.value:
            iq_gain_imbalance_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        iq_gain_imbalance_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=iq_gain_imbalance_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchIQGainImbalancePerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            iq_gain_imbalance_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace(
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
            iq_quadrature_error_per_subcarrier_mean,
            "iq_quadrature_error_per_subcarrier_mean",
            "float32",
        )
        if len(iq_quadrature_error_per_subcarrier_mean) != actual_array_size_ctype.value:
            iq_quadrature_error_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        iq_quadrature_error_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=iq_quadrature_error_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            iq_quadrature_error_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_pilot_constellation_trace(
        self, selector_string, timeout, pilot_constellation
    ):
        """ofdmmodacc_fetch_pilot_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(pilot_constellation, "pilot_constellation", "complex64")
        if len(pilot_constellation) != actual_array_size_ctype.value:
            pilot_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pilot_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pilot_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPilotConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pilot_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_fetch_preamble_frequency_error_trace(
        self, selector_string, timeout, preamble_frequency_error
    ):
        """ofdmmodacc_fetch_preamble_frequency_error_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace(
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
            preamble_frequency_error, "preamble_frequency_error", "float32"
        )
        if len(preamble_frequency_error) != actual_array_size_ctype.value:
            preamble_frequency_error.resize((actual_array_size_ctype.value,), refcheck=False)
        preamble_frequency_error_ctype = _get_ctypes_pointer_for_buffer(
            value=preamble_frequency_error, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPreambleFrequencyErrorTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            preamble_frequency_error_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_spectral_flatness_mean_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness_mean,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        """ofdmmodacc_fetch_spectral_flatness_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace(
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
        _helper.validate_numpy_array(spectral_flatness_mean, "spectral_flatness_mean", "float32")
        if len(spectral_flatness_mean) != actual_array_size_ctype.value:
            spectral_flatness_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        spectral_flatness_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=spectral_flatness_mean, library_type=ctypes.c_float
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
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSpectralFlatnessMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            spectral_flatness_mean_ctype,
            spectral_flatness_lower_mask_ctype,
            spectral_flatness_upper_mask_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_stream_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_data_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_stream_data_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace(
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
            stream_data_rms_evm_per_symbol_mean, "stream_data_rms_evm_per_symbol_mean", "float32"
        )
        if len(stream_data_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            stream_data_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        stream_data_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=stream_data_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamDataRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            stream_data_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_stream_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_pilot_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_stream_pilot_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace(
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
            stream_pilot_rms_evm_per_symbol_mean, "stream_pilot_rms_evm_per_symbol_mean", "float32"
        )
        if len(stream_pilot_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            stream_pilot_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        stream_pilot_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=stream_pilot_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamPilotRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            stream_pilot_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_stream_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, stream_rms_evm_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_stream_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace(
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
            stream_rms_evm_per_subcarrier_mean, "stream_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(stream_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            stream_rms_evm_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        stream_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=stream_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            stream_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_stream_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_stream_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace(
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
            stream_rms_evm_per_symbol_mean, "stream_rms_evm_per_symbol_mean", "float32"
        )
        if len(stream_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            stream_rms_evm_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        stream_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=stream_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchStreamRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            stream_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_subcarrier_chain_evm_per_symbol_trace(
        self, selector_string, timeout, subcarrier_index, subcarrier_chain_evm_per_symbol
    ):
        """ofdmmodacc_fetch_subcarrier_chain_evm_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subcarrier_index_ctype = ctypes.c_int32(subcarrier_index)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subcarrier_index_ctype,
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
            subcarrier_chain_evm_per_symbol, "subcarrier_chain_evm_per_symbol", "float32"
        )
        if len(subcarrier_chain_evm_per_symbol) != actual_array_size_ctype.value:
            subcarrier_chain_evm_per_symbol.resize((actual_array_size_ctype.value,), refcheck=False)
        subcarrier_chain_evm_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=subcarrier_chain_evm_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSubcarrierChainEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subcarrier_index_ctype,
            x0_ctype,
            dx_ctype,
            subcarrier_chain_evm_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_subcarrier_stream_evm_per_symbol_trace(
        self, selector_string, timeout, subcarrier_index, subcarrier_stream_evm_per_symbol
    ):
        """ofdmmodacc_fetch_subcarrier_stream_evm_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subcarrier_index_ctype = ctypes.c_int32(subcarrier_index)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subcarrier_index_ctype,
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
            subcarrier_stream_evm_per_symbol, "subcarrier_stream_evm_per_symbol", "float32"
        )
        if len(subcarrier_stream_evm_per_symbol) != actual_array_size_ctype.value:
            subcarrier_stream_evm_per_symbol.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        subcarrier_stream_evm_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            value=subcarrier_stream_evm_per_symbol, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSubcarrierStreamEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            subcarrier_index_ctype,
            x0_ctype,
            dx_ctype,
            subcarrier_stream_evm_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_symbol_chain_evm_per_subcarrier_trace(
        self, selector_string, timeout, symbol_index, symbol_chain_evm_per_subcarrier
    ):
        """ofdmmodacc_fetch_symbol_chain_evm_per_subcarrier_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        symbol_index_ctype = ctypes.c_int32(symbol_index)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            symbol_index_ctype,
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
            symbol_chain_evm_per_subcarrier, "symbol_chain_evm_per_subcarrier", "float32"
        )
        if len(symbol_chain_evm_per_subcarrier) != actual_array_size_ctype.value:
            symbol_chain_evm_per_subcarrier.resize((actual_array_size_ctype.value,), refcheck=False)
        symbol_chain_evm_per_subcarrier_ctype = _get_ctypes_pointer_for_buffer(
            value=symbol_chain_evm_per_subcarrier, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSymbolChainEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            symbol_index_ctype,
            x0_ctype,
            dx_ctype,
            symbol_chain_evm_per_subcarrier_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_symbol_stream_evm_per_subcarrier_trace(
        self, selector_string, timeout, symbol_index, symbol_stream_evm_per_subcarrier
    ):
        """ofdmmodacc_fetch_symbol_stream_evm_per_subcarrier_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        symbol_index_ctype = ctypes.c_int32(symbol_index)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            symbol_index_ctype,
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
            symbol_stream_evm_per_subcarrier, "symbol_stream_evm_per_subcarrier", "float32"
        )
        if len(symbol_stream_evm_per_subcarrier) != actual_array_size_ctype.value:
            symbol_stream_evm_per_subcarrier.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        symbol_stream_evm_per_subcarrier_ctype = _get_ctypes_pointer_for_buffer(
            value=symbol_stream_evm_per_subcarrier, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchSymbolStreamEVMPerSubcarrierTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            symbol_index_ctype,
            x0_ctype,
            dx_ctype,
            symbol_stream_evm_per_subcarrier_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_unused_tone_error_margin_per_ru(
        self, selector_string, timeout, unused_tone_error_margin_per_ru
    ):
        """ofdmmodacc_fetch_unused_tone_error_margin_per_ru."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            unused_tone_error_margin_per_ru, "unused_tone_error_margin_per_ru", "float64"
        )
        if len(unused_tone_error_margin_per_ru) != actual_array_size_ctype.value:
            unused_tone_error_margin_per_ru.resize((actual_array_size_ctype.value,), refcheck=False)
        unused_tone_error_margin_per_ru_ctype = _get_ctypes_pointer_for_buffer(
            value=unused_tone_error_margin_per_ru, library_type=ctypes.c_double
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMarginPerRU(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            unused_tone_error_margin_per_ru_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_fetch_unused_tone_error_mean_trace(
        self, selector_string, timeout, unused_tone_error, unused_tone_error_mask
    ):
        """ofdmmodacc_fetch_unused_tone_error_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace(
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
        _helper.validate_numpy_array(unused_tone_error, "unused_tone_error", "float32")
        if len(unused_tone_error) != actual_array_size_ctype.value:
            unused_tone_error.resize((actual_array_size_ctype.value,), refcheck=False)
        unused_tone_error_ctype = _get_ctypes_pointer_for_buffer(
            value=unused_tone_error, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(unused_tone_error_mask, "unused_tone_error_mask", "float32")
        if len(unused_tone_error_mask) != actual_array_size_ctype.value:
            unused_tone_error_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        unused_tone_error_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=unused_tone_error_mask, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUnusedToneErrorMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            unused_tone_error_ctype,
            unused_tone_error_mask_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_user_data_constellation_trace(
        self, selector_string, timeout, user_data_constellation
    ):
        """ofdmmodacc_fetch_user_data_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            user_data_constellation, "user_data_constellation", "complex64"
        )
        if len(user_data_constellation) != actual_array_size_ctype.value:
            user_data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        user_data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=user_data_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserDataConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            user_data_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_fetch_user_pilot_constellation_trace(
        self, selector_string, timeout, user_pilot_constellation
    ):
        """ofdmmodacc_fetch_user_pilot_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            user_pilot_constellation, "user_pilot_constellation", "complex64"
        )
        if len(user_pilot_constellation) != actual_array_size_ctype.value:
            user_pilot_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        user_pilot_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=user_pilot_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserPilotConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            user_pilot_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_fetch_user_stream_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_data_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_user_stream_data_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace(
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
            user_stream_data_rms_evm_per_symbol_mean,
            "user_stream_data_rms_evm_per_symbol_mean",
            "float32",
        )
        if len(user_stream_data_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            user_stream_data_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        user_stream_data_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=user_stream_data_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamDataRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            user_stream_data_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_user_stream_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_pilot_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_user_stream_pilot_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace(
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
            user_stream_pilot_rms_evm_per_symbol_mean,
            "user_stream_pilot_rms_evm_per_symbol_mean",
            "float32",
        )
        if len(user_stream_pilot_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            user_stream_pilot_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        user_stream_pilot_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=user_stream_pilot_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamPilotRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            user_stream_pilot_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_user_stream_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, user_stream_rms_evm_per_subcarrier_mean
    ):
        """ofdmmodacc_fetch_user_stream_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace(
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
            user_stream_rms_evm_per_subcarrier_mean,
            "user_stream_rms_evm_per_subcarrier_mean",
            "float32",
        )
        if len(user_stream_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            user_stream_rms_evm_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        user_stream_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=user_stream_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            user_stream_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_user_stream_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_rms_evm_per_symbol_mean
    ):
        """ofdmmodacc_fetch_user_stream_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace(
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
            user_stream_rms_evm_per_symbol_mean, "user_stream_rms_evm_per_symbol_mean", "float32"
        )
        if len(user_stream_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            user_stream_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        user_stream_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=user_stream_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchUserStreamRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            user_stream_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def ofdmmodacc_fetch_phase_noise_psd_mean_trace(
        self, selector_string, timeout, phase_noise_psd_mean
    ):
        """ofdmmodacc_fetch_phase_noise_psd_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace(
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
        _helper.validate_numpy_array(phase_noise_psd_mean, "phase_noise_psd_mean", "float32")
        if len(phase_noise_psd_mean) != actual_array_size_ctype.value:
            phase_noise_psd_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        phase_noise_psd_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=phase_noise_psd_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_OFDMModAccFetchPhaseNoisePSDMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            phase_noise_psd_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def sem_fetch_lower_offset_margin_array(self, selector_string, timeout):
        """sem_fetch_lower_offset_margin_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_SEMFetchLowerOffsetMarginArray(
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
        error_code = self._library.RFmxWLAN_SEMFetchLowerOffsetMarginArray(
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
        error_code = self._library.RFmxWLAN_SEMFetchLowerOffsetPowerArray(
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

        total_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        total_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_SEMFetchLowerOffsetPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            total_absolute_power_ctype,
            total_relative_power_ctype,
            peak_absolute_power_ctype,
            peak_frequency_ctype,
            peak_relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            total_absolute_power_ctype[:],
            total_relative_power_ctype[:],
            peak_absolute_power_ctype[:],
            peak_frequency_ctype[:],
            peak_relative_power_ctype[:],
            error_code,
        )

    def sem_fetch_spectrum(self, selector_string, timeout, spectrum, composite_mask):
        """sem_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_SEMFetchSpectrum(
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
        error_code = self._library.RFmxWLAN_SEMFetchSpectrum(
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
        error_code = self._library.RFmxWLAN_SEMFetchUpperOffsetMarginArray(
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
        error_code = self._library.RFmxWLAN_SEMFetchUpperOffsetMarginArray(
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
        error_code = self._library.RFmxWLAN_SEMFetchUpperOffsetPowerArray(
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

        total_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        total_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxWLAN_SEMFetchUpperOffsetPowerArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            total_absolute_power_ctype,
            total_relative_power_ctype,
            peak_absolute_power_ctype,
            peak_frequency_ctype,
            peak_relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            total_absolute_power_ctype[:],
            total_relative_power_ctype[:],
            peak_absolute_power_ctype[:],
            peak_frequency_ctype[:],
            peak_relative_power_ctype[:],
            error_code,
        )

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        old_signal_name_ctype = ctypes.create_string_buffer(old_signal_name.encode(self._encoding))
        new_signal_name_ctype = ctypes.create_string_buffer(new_signal_name.encode(self._encoding))
        error_code = self._library.RFmxWLAN_CloneSignalConfiguration(
            vi_ctype, old_signal_name_ctype, new_signal_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        import nirfmxwlan

        signal_configuration = (
            nirfmxwlan._WlanSignalConfiguration.get_wlan_signal_configuration(  # type: ignore
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
        error_code = self._library.RFmxWLAN_DeleteSignalConfiguration(vi_ctype, signal_name_ctype)
        if not ignore_driver_error:
            errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def send_software_edge_trigger(self):
        """send_software_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        error_code = self._library.RFmxWLAN_SendSoftwareEdgeTrigger(vi_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_all_named_result_names(self, selector_string):
        """get_all_named_result_names."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        actual_result_names_size_ctype = ctypes.c_int32(0)
        default_result_exists_ctype = ctypes.c_int32()

        # call library function to get the size of array
        error_code = self._library.RFmxWLAN_GetAllNamedResultNames(
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
        error_code = self._library.RFmxWLAN_GetAllNamedResultNames(
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

    def ofdmmodacc_clear_noise_calibration_database(self, selector_string):
        """clear_noise_calibration_database."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxWLAN_OFDMModAccClearNoiseCalibrationDatabase(
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
        error_code = self._library.RFmxWLAN_AnalyzeIQ1Waveform(
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
        error_code = self._library.RFmxWLAN_AnalyzeSpectrum1Waveform(
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

    def analyze_n_waveforms_iq(self, selector_string, result_name, x0, dx, iq, reset):
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        x0_ctype = _get_ctypes_pointer_for_buffer(value=x0, library_type=ctypes.c_double)
        dx_ctype = _get_ctypes_pointer_for_buffer(value=dx, library_type=ctypes.c_double)
        iq_size = []
        for arr in iq:
            _helper.validate_numpy_array(arr, "iq", "complex64")
            iq_size.append(len(arr))
        iq_array = numpy.concatenate(iq)
        iq_ctype = _get_ctypes_pointer_for_buffer(
            value=iq_array, library_type=_custom_types.ComplexSingle
        )
        iq_size_ctype = _get_ctypes_pointer_for_buffer(value=iq_size, library_type=ctypes.c_int32)
        array_size_ctype = ctypes.c_int32(len(iq))
        reset_ctype = ctypes.c_int32(reset)
        error_code = self._library.RFmxWLAN_AnalyzeNWaveformsIQ(
            vi_ctype,
            selector_string_ctype,
            result_name_ctype,
            x0_ctype,
            dx_ctype,
            iq_ctype,
            iq_size_ctype,
            array_size_ctype,
            reset_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def analyze_n_waveforms_spectrum(self, selector_string, result_name, x0, dx, spectrum, reset):
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        x0_ctype = _get_ctypes_pointer_for_buffer(value=x0, library_type=ctypes.c_double)
        dx_ctype = _get_ctypes_pointer_for_buffer(value=dx, library_type=ctypes.c_double)
        spectrum_size = []
        for arr in spectrum:
            _helper.validate_numpy_array(arr, "spectrum", "float32")
            spectrum_size.append(len(arr))
        spectrum_array = numpy.concatenate(spectrum)
        spectrum_ctype = _get_ctypes_pointer_for_buffer(
            value=spectrum_array, library_type=ctypes.c_float
        )
        x0_ctype = _get_ctypes_pointer_for_buffer(value=x0, library_type=ctypes.c_double)
        dx_ctype = _get_ctypes_pointer_for_buffer(value=dx, library_type=ctypes.c_double)
        spectrum_size = []
        for arr in spectrum:
            _helper.validate_numpy_array(arr, "spectrum", "float32")
            spectrum_size.append(len(arr))
        spectrum_array = numpy.concatenate(spectrum)
        spectrum_ctype = _get_ctypes_pointer_for_buffer(
            value=spectrum_array, library_type=ctypes.c_float
        )
        spectrum_size_ctype = _get_ctypes_pointer_for_buffer(
            value=spectrum_size, library_type=ctypes.c_int32
        )
        array_size_ctype = ctypes.c_int32(len(spectrum))
        reset_ctype = ctypes.c_int32(reset)
        error_code = self._library.RFmxWLAN_AnalyzeNWaveformsSpectrum(
            vi_ctype,
            selector_string_ctype,
            result_name_ctype,
            x0_ctype,
            dx_ctype,
            spectrum_ctype,
            spectrum_size_ctype,
            array_size_ctype,
            reset_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def ofdmmodacc_configure_n_reference_waveforms(
        self, selector_string, x0, dx, reference_waveform
    ):
        """ofdmmodacc_configure_n_reference_waveforms."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        x0_ctype = _get_ctypes_pointer_for_buffer(value=x0, library_type=ctypes.c_double)
        dx_ctype = _get_ctypes_pointer_for_buffer(value=dx, library_type=ctypes.c_double)
        reference_waveform_size = []
        for arr in reference_waveform:
            _helper.validate_numpy_array(arr, "reference_waveform", "complex64")
            reference_waveform_size.append(len(arr))
        reference_waveform_array = numpy.concatenate(reference_waveform)
        reference_waveform_ctype = _get_ctypes_pointer_for_buffer(
            value=reference_waveform_array, library_type=_custom_types.ComplexSingle
        )
        reference_waveform_size_ctype = _get_ctypes_pointer_for_buffer(
            value=reference_waveform_size, library_type=ctypes.c_int32
        )
        array_size_ctype = ctypes.c_int32(len(reference_waveform))
        error_code = self._library.RFmxWLAN_OFDMModAccCfgNReferenceWaveforms(
            vi_ctype,
            selector_string_ctype,
            x0_ctype,
            dx_ctype,
            reference_waveform_ctype,
            reference_waveform_size_ctype,
            array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return 0
