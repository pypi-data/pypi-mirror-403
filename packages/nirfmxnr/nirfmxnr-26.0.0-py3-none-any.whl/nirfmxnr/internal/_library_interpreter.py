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
import nirfmxnr.attributes as attributes
import nirfmxnr.enums as enums
import nirfmxnr.errors as errors
import nirfmxnr.internal._custom_types as _custom_types
import nirfmxnr.internal._helper as _helper
import nirfmxnr.internal._library_singleton as _library_singleton
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
        size_or_error_code = self._library.RFmxNR_GetErrorString(
            self._vi, error_code_ctype, 0, None
        )
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxNR_GetErrorString(
                self._vi, error_code_ctype, size_or_error_code, error_string_ctype
            )
        return error_string_ctype.value.decode(self._encoding)

    def get_error(self) -> tuple[int, Any]:
        """Returns the error code and error message."""
        error_code_ctype = ctypes.c_int32()
        error_string_ctype = ctypes.create_string_buffer(0)
        size_or_error_code = self._library.RFmxNR_GetError(self._vi, error_code_ctype, 0, None)
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_code_ctype = ctypes.c_int32(error_code_ctype.value)
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxNR_GetError(
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
        error_code = self._library.RFmxNR_ResetAttribute(
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
                local_personality.value == nirfmxinstr.Personalities.NR.value
            )
        elif self._signal_obj is not None:
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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int8()
        error_code = self._library.RFmxNR_GetAttributeI8(
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
        error_code = self._library.RFmxNR_SetAttributeI8(
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
        error_code = self._library.RFmxNR_GetAttributeI8Array(
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
        error_code = self._library.RFmxNR_GetAttributeI8Array(
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
        error_code = self._library.RFmxNR_SetAttributeI8Array(
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
        error_code = self._library.RFmxNR_GetAttributeI16(
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
        error_code = self._library.RFmxNR_SetAttributeI16(
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
        error_code = self._library.RFmxNR_GetAttributeI32(
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
        error_code = self._library.RFmxNR_SetAttributeI32(
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
        error_code = self._library.RFmxNR_GetAttributeI32Array(
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
        error_code = self._library.RFmxNR_GetAttributeI32Array(
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
        error_code = self._library.RFmxNR_SetAttributeI32Array(
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
        error_code = self._library.RFmxNR_GetAttributeI64(
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
        error_code = self._library.RFmxNR_SetAttributeI64(
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
        error_code = self._library.RFmxNR_GetAttributeI64Array(
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
        error_code = self._library.RFmxNR_GetAttributeI64Array(
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
        error_code = self._library.RFmxNR_SetAttributeI64Array(
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
        error_code = self._library.RFmxNR_GetAttributeU8(
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
        error_code = self._library.RFmxNR_SetAttributeU8(
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
        error_code = self._library.RFmxNR_GetAttributeU8Array(
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
        error_code = self._library.RFmxNR_GetAttributeU8Array(
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
        error_code = self._library.RFmxNR_SetAttributeU8Array(
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
        error_code = self._library.RFmxNR_GetAttributeU16(
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
        error_code = self._library.RFmxNR_SetAttributeU16(
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
        error_code = self._library.RFmxNR_GetAttributeU32(
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
        error_code = self._library.RFmxNR_SetAttributeU32(
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
        error_code = self._library.RFmxNR_GetAttributeU32Array(
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
        error_code = self._library.RFmxNR_GetAttributeU32Array(
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
        error_code = self._library.RFmxNR_SetAttributeU32Array(
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
        error_code = self._library.RFmxNR_GetAttributeU64Array(
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
        error_code = self._library.RFmxNR_GetAttributeU64Array(
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
        error_code = self._library.RFmxNR_SetAttributeU64Array(
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
        error_code = self._library.RFmxNR_GetAttributeF32(
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
        error_code = self._library.RFmxNR_SetAttributeF32(
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
        error_code = self._library.RFmxNR_GetAttributeF32Array(
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
        error_code = self._library.RFmxNR_GetAttributeF32Array(
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
        error_code = self._library.RFmxNR_SetAttributeF32Array(
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
        error_code = self._library.RFmxNR_GetAttributeF64(
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
        error_code = self._library.RFmxNR_SetAttributeF64(
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
        error_code = self._library.RFmxNR_GetAttributeF64Array(
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
        error_code = self._library.RFmxNR_GetAttributeF64Array(
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
        error_code = self._library.RFmxNR_SetAttributeF64Array(
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
        error_code = self._library.RFmxNR_GetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxNR_GetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxNR_SetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxNR_GetAttributeNIComplexDoubleArray(
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
        error_code = self._library.RFmxNR_GetAttributeNIComplexDoubleArray(
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
        error_code = self._library.RFmxNR_SetAttributeNIComplexDoubleArray(
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
        size_or_error_code = self._library.RFmxNR_GetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, array_size_ctype, attr_val_ctype
        )
        if size_or_error_code < 0:
            errors.handle_error(
                self, size_or_error_code, ignore_warnings=True, is_error_handling=False
            )
            return None, size_or_error_code
        array_size_ctype = ctypes.c_int32(size_or_error_code)
        attr_val_ctype = (ctypes.c_char * array_size_ctype.value)()
        error_code = self._library.RFmxNR_GetAttributeString(
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
        error_code = self._library.RFmxNR_SetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_reference_waveform(self, selector_string, x0, dx, reference_waveform):
        """modacc_configure_reference_waveform."""
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
        error_code = self._library.RFmxNR_ModAccCfgReferenceWaveform(
            vi_ctype,
            selector_string_ctype,
            x0_ctype,
            dx_ctype,
            reference_waveform_ctype,
            array_size_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_auto_level(self, selector_string, timeout):
        """modacc_auto_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxNR_ModAccAutoLevel(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_validate_calibration_data(self, selector_string):
        """modacc_validate_calibration_data."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        calibration_data_valid_ctype = ctypes.c_int32()
        error_code = self._library.RFmxNR_ModAccValidateCalibrationData(
            vi_ctype, selector_string_ctype, calibration_data_valid_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.ModAccCalibrationDataValid(calibration_data_valid_ctype.value), error_code

    def modacc_clear_noise_calibration_database(self):
        """modacc_clear_noise_calibration_database."""
        vi_ctype = ctypes.c_uint32(self._vi)
        error_code = self._library.RFmxNR_ModAccClearNoiseCalibrationDatabase(vi_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_validate_noise_calibration_data(self, selector_string):
        """acp_validate_noise_calibration_data."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_calibration_data_valid_ctype = ctypes.c_int32()
        error_code = self._library.RFmxNR_ACPValidateNoiseCalibrationData(
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
        error_code = self._library.RFmxNR_CHPValidateNoiseCalibrationData(
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
        error_code = self._library.RFmxNR_AbortMeasurements(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_level(self, selector_string, measurement_interval):
        """auto_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_interval_ctype = ctypes.c_double(measurement_interval)
        reference_level_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_AutoLevel(
            vi_ctype, selector_string_ctype, measurement_interval_ctype, reference_level_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return reference_level_ctype.value, error_code

    def check_measurement_status(self, selector_string):
        """check_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        is_done_ctype = ctypes.c_int32()
        error_code = self._library.RFmxNR_CheckMeasurementStatus(
            vi_ctype, selector_string_ctype, is_done_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return bool(is_done_ctype.value), error_code

    def clear_all_named_results(self, selector_string):
        """clear_all_named_results."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxNR_ClearAllNamedResults(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def clear_named_result(self, selector_string):
        """clear_named_result."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxNR_ClearNamedResult(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def clear_noise_calibration_database(self, selector_string):
        """clear_noise_calibration_database."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxNR_ClearNoiseCalibrationDatabase(
            vi_ctype, selector_string_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def commit(self, selector_string):
        """commit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxNR_Commit(vi_ctype, selector_string_ctype)
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
        error_code = self._library.RFmxNR_CfgDigitalEdgeTrigger(
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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        iq_power_edge_trigger_source_ctype = ctypes.create_string_buffer(
            iq_power_edge_trigger_source.encode(self._encoding)
        )
        iq_power_edge_trigger_slope_ctype = ctypes.c_int32(iq_power_edge_trigger_slope)
        iq_power_edge_trigger_level_ctype = ctypes.c_double(iq_power_edge_trigger_level)
        trigger_delay_ctype = ctypes.c_double(trigger_delay)
        trigger_minimum_quiet_time_mode_ctype = ctypes.c_int32(trigger_minimum_quiet_time_mode)
        trigger_minimum_quiet_time_duration_ctype = ctypes.c_double(
            trigger_minimum_quiet_time_duration
        )
        iq_power_edge_trigger_level_type_ctype = ctypes.c_int32(iq_power_edge_trigger_level_type)
        enable_trigger_ctype = ctypes.c_int32(enable_trigger)
        error_code = self._library.RFmxNR_CfgIQPowerEdgeTrigger(
            vi_ctype,
            selector_string_ctype,
            iq_power_edge_trigger_source_ctype,
            iq_power_edge_trigger_slope_ctype,
            iq_power_edge_trigger_level_ctype,
            trigger_delay_ctype,
            trigger_minimum_quiet_time_mode_ctype,
            trigger_minimum_quiet_time_duration_ctype,
            iq_power_edge_trigger_level_type_ctype,
            enable_trigger_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_selected_ports_multiple(self, selector_string, selected_ports):
        """configure_selected_ports_multiple."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        selected_ports_ctype = ctypes.create_string_buffer(selected_ports.encode(self._encoding))
        error_code = self._library.RFmxNR_CfgSelectedPortsMultiple(
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
        error_code = self._library.RFmxNR_CfgSoftwareEdgeTrigger(
            vi_ctype, selector_string_ctype, trigger_delay_ctype, enable_trigger_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def create_list(self, list_name):
        """create_list."""
        vi_ctype = ctypes.c_uint32(self._vi)
        list_name_ctype = ctypes.create_string_buffer(list_name.encode(self._encoding))
        error_code = self._library.RFmxNR_CreateList(vi_ctype, list_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def create_list_step(self, selector_string):
        """create_list_step."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        created_step_index_ctype = ctypes.c_int32()
        error_code = self._library.RFmxNR_CreateListStep(
            vi_ctype, selector_string_ctype, created_step_index_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return created_step_index_ctype.value, error_code

    def create_signal_configuration(self, signal_name):
        """create_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(signal_name.encode(self._encoding))
        error_code = self._library.RFmxNR_CreateSignalConfiguration(vi_ctype, signal_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def delete_list(self, list_name):
        """delete_list."""
        vi_ctype = ctypes.c_uint32(self._vi)
        list_name_ctype = ctypes.create_string_buffer(list_name.encode(self._encoding))
        error_code = self._library.RFmxNR_DeleteList(vi_ctype, list_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def disable_trigger(self, selector_string):
        """disable_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxNR_DisableTrigger(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def initiate(self, selector_string, result_name):
        """initiate."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        error_code = self._library.RFmxNR_Initiate(
            vi_ctype, selector_string_ctype, result_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def reset_to_default(self, selector_string):
        """reset_to_default."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxNR_ResetToDefault(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def select_measurements(self, selector_string, measurements, enable_all_traces):
        """select_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurements_ctype = ctypes.c_uint32(measurements)
        enable_all_traces_ctype = ctypes.c_int32(enable_all_traces)
        error_code = self._library.RFmxNR_SelectMeasurements(
            vi_ctype, selector_string_ctype, measurements_ctype, enable_all_traces_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def wait_for_measurement_complete(self, selector_string, timeout):
        """wait_for_measurement_complete."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxNR_WaitForMeasurementComplete(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def load_from_generation_configuration_file(
        self, selector_string, file_path, configuration_index
    ):
        """load_from_generation_configuration_file."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        file_path_ctype = ctypes.create_string_buffer(file_path.encode(self._encoding))
        configuration_index_ctype = ctypes.c_int32(configuration_index)
        error_code = self._library.RFmxNR_LoadFromGenerationConfigurationFile(
            vi_ctype, selector_string_ctype, file_path_ctype, configuration_index_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_measurement_mode(self, selector_string, measurement_mode):
        """modacc_configure_measurement_mode."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_mode_ctype = ctypes.c_int32(measurement_mode)
        error_code = self._library.RFmxNR_ModAccCfgMeasurementMode(
            vi_ctype, selector_string_ctype, measurement_mode_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_noise_compensation_enabled(
        self, selector_string, noise_compensation_enabled
    ):
        """modacc_configure_noise_compensation_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_compensation_enabled_ctype = ctypes.c_int32(noise_compensation_enabled)
        error_code = self._library.RFmxNR_ModAccCfgNoiseCompensationEnabled(
            vi_ctype, selector_string_ctype, noise_compensation_enabled_ctype
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
        error_code = self._library.RFmxNR_ACPCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_measurement_method(self, selector_string, measurement_method):
        """acp_configure_measurement_method."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_method_ctype = ctypes.c_int32(measurement_method)
        error_code = self._library.RFmxNR_ACPCfgMeasurementMethod(
            vi_ctype, selector_string_ctype, measurement_method_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        """acp_configure_noise_compensation_enabled."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        noise_compensation_enabled_ctype = ctypes.c_int32(noise_compensation_enabled)
        error_code = self._library.RFmxNR_ACPCfgNoiseCompensationEnabled(
            vi_ctype, selector_string_ctype, noise_compensation_enabled_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_endc_offsets(self, selector_string, number_of_endc_offsets):
        """acp_configure_number_of_endc_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_endc_offsets_ctype = ctypes.c_int32(number_of_endc_offsets)
        error_code = self._library.RFmxNR_ACPCfgNumberOfENDCOffsets(
            vi_ctype, selector_string_ctype, number_of_endc_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_eutra_offsets(self, selector_string, number_of_eutra_offsets):
        """acp_configure_number_of_eutra_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_eutra_offsets_ctype = ctypes.c_int32(number_of_eutra_offsets)
        error_code = self._library.RFmxNR_ACPCfgNumberOfEUTRAOffsets(
            vi_ctype, selector_string_ctype, number_of_eutra_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_nr_offsets(self, selector_string, number_of_nr_offsets):
        """acp_configure_number_of_nr_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_nr_offsets_ctype = ctypes.c_int32(number_of_nr_offsets)
        error_code = self._library.RFmxNR_ACPCfgNumberOfNROffsets(
            vi_ctype, selector_string_ctype, number_of_nr_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_utra_offsets(self, selector_string, number_of_utra_offsets):
        """acp_configure_number_of_utra_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_utra_offsets_ctype = ctypes.c_int32(number_of_utra_offsets)
        error_code = self._library.RFmxNR_ACPCfgNumberOfUTRAOffsets(
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
        error_code = self._library.RFmxNR_ACPCfgRBWFilter(
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
        error_code = self._library.RFmxNR_ACPCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_power_units(self, selector_string, power_units):
        """acp_configure_power_units."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        power_units_ctype = ctypes.c_int32(power_units)
        error_code = self._library.RFmxNR_ACPCfgPowerUnits(
            vi_ctype, selector_string_ctype, power_units_ctype
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
        error_code = self._library.RFmxNR_PVTCfgAveraging(
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
        error_code = self._library.RFmxNR_PVTCfgMeasurementMethod(
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
        error_code = self._library.RFmxNR_PVTCfgOFFPowerExclusionPeriods(
            vi_ctype,
            selector_string_ctype,
            off_power_exclusion_before_ctype,
            off_power_exclusion_after_ctype,
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
        error_code = self._library.RFmxNR_OBWCfgAveraging(
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
        error_code = self._library.RFmxNR_OBWCfgRBWFilter(
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
        error_code = self._library.RFmxNR_OBWCfgSweepTime(
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
        error_code = self._library.RFmxNR_SEMCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_rated_output_power_array(
        self, selector_string, component_carrier_rated_output_power
    ):
        """sem_configure_rated_output_power_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_rated_output_power_ctype = _get_ctypes_pointer_for_buffer(
            value=component_carrier_rated_output_power, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(component_carrier_rated_output_power)
            if component_carrier_rated_output_power is not None
            else 0
        )
        error_code = self._library.RFmxNR_SEMCfgComponentCarrierRatedOutputPowerArray(
            vi_ctype,
            selector_string_ctype,
            component_carrier_rated_output_power_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_rated_output_power(
        self, selector_string, component_carrier_rated_output_power
    ):
        """sem_configure_rated_output_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        component_carrier_rated_output_power_ctype = ctypes.c_double(
            component_carrier_rated_output_power
        )
        error_code = self._library.RFmxNR_SEMCfgComponentCarrierRatedOutputPower(
            vi_ctype, selector_string_ctype, component_carrier_rated_output_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """sem_configure_number_of_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_offsets_ctype = ctypes.c_int32(number_of_offsets)
        error_code = self._library.RFmxNR_SEMCfgNumberOfOffsets(
            vi_ctype, selector_string_ctype, number_of_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_absolute_limit_array(
        self, selector_string, absolute_limit_start, absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        absolute_limit_start_ctype = _get_ctypes_pointer_for_buffer(
            value=absolute_limit_start, library_type=ctypes.c_double
        )
        absolute_limit_stop_ctype = _get_ctypes_pointer_for_buffer(
            value=absolute_limit_stop, library_type=ctypes.c_double
        )
        number_of_elements_ctype = ctypes.c_int32(
            _helper.validate_array_parameter_sizes_are_equal(
                ["absolute_limit_start", "absolute_limit_stop"],
                absolute_limit_start,
                absolute_limit_stop,
            )
        )
        error_code = self._library.RFmxNR_SEMCfgOffsetAbsoluteLimitArray(
            vi_ctype,
            selector_string_ctype,
            absolute_limit_start_ctype,
            absolute_limit_stop_ctype,
            number_of_elements_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_absolute_limit(
        self, selector_string, absolute_limit_start, absolute_limit_stop
    ):
        """sem_configure_offset_absolute_limit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        absolute_limit_start_ctype = ctypes.c_double(absolute_limit_start)
        absolute_limit_stop_ctype = ctypes.c_double(absolute_limit_stop)
        error_code = self._library.RFmxNR_SEMCfgOffsetAbsoluteLimit(
            vi_ctype, selector_string_ctype, absolute_limit_start_ctype, absolute_limit_stop_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_bandwidth_integral_array(self, selector_string, bandwidth_integral):
        """sem_configure_offset_bandwidth_integral_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        bandwidth_integral_ctype = _get_ctypes_pointer_for_buffer(
            value=bandwidth_integral, library_type=ctypes.c_int32
        )
        number_of_elements_ctype = ctypes.c_int32(
            len(bandwidth_integral) if bandwidth_integral is not None else 0
        )
        error_code = self._library.RFmxNR_SEMCfgOffsetBandwidthIntegralArray(
            vi_ctype, selector_string_ctype, bandwidth_integral_ctype, number_of_elements_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_bandwidth_integral(self, selector_string, bandwidth_integral):
        """sem_configure_offset_bandwidth_integral."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        bandwidth_integral_ctype = ctypes.c_int32(bandwidth_integral)
        error_code = self._library.RFmxNR_SEMCfgOffsetBandwidthIntegral(
            vi_ctype, selector_string_ctype, bandwidth_integral_ctype
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
        error_code = self._library.RFmxNR_SEMCfgOffsetFrequencyArray(
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
        error_code = self._library.RFmxNR_SEMCfgOffsetFrequency(
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
        error_code = self._library.RFmxNR_SEMCfgOffsetLimitFailMaskArray(
            vi_ctype, selector_string_ctype, limit_fail_mask_ctype, number_of_elements_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_offset_limit_fail_mask(self, selector_string, limit_fail_mask):
        """sem_configure_offset_limit_fail_mask."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        limit_fail_mask_ctype = ctypes.c_int32(limit_fail_mask)
        error_code = self._library.RFmxNR_SEMCfgOffsetLimitFailMask(
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
        error_code = self._library.RFmxNR_SEMCfgOffsetRBWFilterArray(
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
        error_code = self._library.RFmxNR_SEMCfgOffsetRBWFilter(
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
        error_code = self._library.RFmxNR_SEMCfgOffsetRelativeLimitArray(
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
        error_code = self._library.RFmxNR_SEMCfgOffsetRelativeLimit(
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
        error_code = self._library.RFmxNR_SEMCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def sem_configure_uplink_mask_type(self, selector_string, uplink_mask_type):
        """sem_configure_uplink_mask_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        uplink_mask_type_ctype = ctypes.c_int32(uplink_mask_type)
        error_code = self._library.RFmxNR_SEMCfgUplinkMaskType(
            vi_ctype, selector_string_ctype, uplink_mask_type_ctype
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
        error_code = self._library.RFmxNR_CHPCfgAveraging(
            vi_ctype,
            selector_string_ctype,
            averaging_enabled_ctype,
            averaging_count_ctype,
            averaging_type_ctype,
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
        error_code = self._library.RFmxNR_CHPCfgRBWFilter(
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
        error_code = self._library.RFmxNR_CHPCfgSweepTime(
            vi_ctype, selector_string_ctype, sweep_time_auto_ctype, sweep_time_interval_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_external_attenuation(self, selector_string, external_attenuation):
        """configure_external_attenuation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        external_attenuation_ctype = ctypes.c_double(external_attenuation)
        error_code = self._library.RFmxNR_CfgExternalAttenuation(
            vi_ctype, selector_string_ctype, external_attenuation_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency(self, selector_string, center_frequency):
        """configure_frequency."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        center_frequency_ctype = ctypes.c_double(center_frequency)
        error_code = self._library.RFmxNR_CfgFrequency(
            vi_ctype, selector_string_ctype, center_frequency_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_gnodeb_category(self, selector_string, gnodeb_category):
        """configure_gnodeb_category."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        gnodeb_category_ctype = ctypes.c_int32(gnodeb_category)
        error_code = self._library.RFmxNR_CfggNodeBCategory(
            vi_ctype, selector_string_ctype, gnodeb_category_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_reference_level(self, selector_string, reference_level):
        """configure_reference_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        reference_level_ctype = ctypes.c_double(reference_level)
        error_code = self._library.RFmxNR_CfgReferenceLevel(
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
        error_code = self._library.RFmxNR_CfgRF(
            vi_ctype,
            selector_string_ctype,
            center_frequency_ctype,
            reference_level_ctype,
            external_attenuation_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_composite_evm(self, selector_string, timeout):
        """modacc_fetch_composite_evm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        composite_rms_evm_mean_ctype = ctypes.c_double()
        composite_peak_evm_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_ModAccFetchCompositeEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            composite_rms_evm_mean_ctype,
            composite_peak_evm_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            composite_rms_evm_mean_ctype.value,
            composite_peak_evm_maximum_ctype.value,
            error_code,
        )

    def modacc_fetch_frequency_error_mean(self, selector_string, timeout):
        """modacc_fetch_frequency_error_mean."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        frequency_error_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_ModAccFetchFrequencyErrorMean(
            vi_ctype, selector_string_ctype, timeout_ctype, frequency_error_mean_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return frequency_error_mean_ctype.value, error_code

    def acp_fetch_measurement(self, selector_string, timeout):
        """acp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_power_ctype = ctypes.c_double()
        relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_ACPFetchComponentCarrierMeasurement(
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
        error_code = self._library.RFmxNR_ACPFetchOffsetMeasurement(
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

    def acp_fetch_total_aggregated_power(self, selector_string, timeout):
        """acp_fetch_total_aggregated_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        total_aggregated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_ACPFetchTotalAggregatedPower(
            vi_ctype, selector_string_ctype, timeout_ctype, total_aggregated_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return total_aggregated_power_ctype.value, error_code

    def acp_fetch_subblock_measurement(self, selector_string, timeout):
        """acp_fetch_subblock_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_power_ctype = ctypes.c_double()
        integration_bandwidth_ctype = ctypes.c_double()
        frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_ACPFetchSubblockMeasurement(
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

    def txp_fetch_measurement(self, selector_string, timeout):
        """txp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        average_power_mean_ctype = ctypes.c_double()
        peak_power_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_TXPFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_power_mean_ctype,
            peak_power_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return average_power_mean_ctype.value, peak_power_maximum_ctype.value, error_code

    def pvt_fetch_measurement(self, selector_string, timeout):
        """pvt_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        absolute_off_power_before_ctype = ctypes.c_double()
        absolute_off_power_after_ctype = ctypes.c_double()
        absolute_on_power_ctype = ctypes.c_double()
        burst_width_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_PVTFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            absolute_off_power_before_ctype,
            absolute_off_power_after_ctype,
            absolute_on_power_ctype,
            burst_width_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            enums.PvtMeasurementStatus(measurement_status_ctype.value),
            absolute_off_power_before_ctype.value,
            absolute_off_power_after_ctype.value,
            absolute_on_power_ctype.value,
            burst_width_ctype.value,
            error_code,
        )

    def obw_fetch_measurement(self, selector_string, timeout):
        """obw_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        occupied_bandwidth_ctype = ctypes.c_double()
        absolute_power_ctype = ctypes.c_double()
        start_frequency_ctype = ctypes.c_double()
        stop_frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_OBWFetchMeasurement(
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
        absolute_power_ctype = ctypes.c_double()
        peak_absolute_power_ctype = ctypes.c_double()
        peak_frequency_ctype = ctypes.c_double()
        relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_SEMFetchComponentCarrierMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            peak_absolute_power_ctype,
            peak_frequency_ctype,
            relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_power_ctype.value,
            peak_absolute_power_ctype.value,
            peak_frequency_ctype.value,
            relative_power_ctype.value,
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
        error_code = self._library.RFmxNR_SEMFetchLowerOffsetMargin(
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
        error_code = self._library.RFmxNR_SEMFetchLowerOffsetPower(
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
        error_code = self._library.RFmxNR_SEMFetchMeasurementStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, measurement_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.SemMeasurementStatus(measurement_status_ctype.value), error_code

    def sem_fetch_total_aggregated_power(self, selector_string, timeout):
        """sem_fetch_total_aggregated_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        total_aggregated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_SEMFetchTotalAggregatedPower(
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
        error_code = self._library.RFmxNR_SEMFetchUpperOffsetMargin(
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
        error_code = self._library.RFmxNR_SEMFetchUpperOffsetPower(
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

    def sem_fetch_subblock_measurement(self, selector_string, timeout):
        """sem_fetch_subblock_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_power_ctype = ctypes.c_double()
        integration_bandwidth_ctype = ctypes.c_double()
        frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_SEMFetchSubblockMeasurement(
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

    def chp_fetch_measurement(self, selector_string, timeout):
        """chp_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        absolute_power_ctype = ctypes.c_double()
        relative_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_CHPFetchComponentCarrierMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            relative_power_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return absolute_power_ctype.value, relative_power_ctype.value, error_code

    def chp_fetch_subblock_power(self, selector_string, timeout):
        """chp_fetch_subblock_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        subblock_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_CHPFetchSubblockPower(
            vi_ctype, selector_string_ctype, timeout_ctype, subblock_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return subblock_power_ctype.value, error_code

    def chp_fetch_total_aggregated_power(self, selector_string, timeout):
        """chp_fetch_total_aggregated_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        total_aggregated_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxNR_CHPFetchTotalAggregatedPower(
            vi_ctype, selector_string_ctype, timeout_ctype, total_aggregated_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return total_aggregated_power_ctype.value, error_code

    def modacc_fetch_in_band_emission_trace(
        self, selector_string, timeout, in_band_emission, in_band_emission_mask
    ):
        """modacc_fetch_in_band_emission_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchInBandEmissionTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchInBandEmissionTrace(
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

    def modacc_fetch_pbch_data_constellation_trace(
        self, selector_string, timeout, pbch_data_constellation
    ):
        """modacc_fetch_pbch_data_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDataConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pbch_data_constellation, "pbch_data_constellation", "complex64"
        )
        if len(pbch_data_constellation) != actual_array_size_ctype.value:
            pbch_data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pbch_data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_data_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDataConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pbch_data_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pbch_data_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pbch_data_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_pbch_data_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace(
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
            pbch_data_rms_evm_per_subcarrier_mean,
            "pbch_data_rms_evm_per_subcarrier_mean",
            "float32",
        )
        if len(pbch_data_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            pbch_data_rms_evm_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        pbch_data_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_data_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pbch_data_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pbch_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pbch_data_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_pbch_data_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace(
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
            pbch_data_rms_evm_per_symbol_mean, "pbch_data_rms_evm_per_symbol_mean", "float32"
        )
        if len(pbch_data_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            pbch_data_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        pbch_data_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_data_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDataRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pbch_data_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pbch_dmrs_constellation_trace(
        self, selector_string, timeout, pbch_dmrs_constellation
    ):
        """modacc_fetch_pbch_dmrs_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pbch_dmrs_constellation, "pbch_dmrs_constellation", "complex64"
        )
        if len(pbch_dmrs_constellation) != actual_array_size_ctype.value:
            pbch_dmrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pbch_dmrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_dmrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDMRSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pbch_dmrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pbch_dmrs_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pbch_dmrs_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_pbch_dmrs_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace(
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
            pbch_dmrs_rms_evm_per_subcarrier_mean,
            "pbch_dmrs_rms_evm_per_subcarrier_mean",
            "float32",
        )
        if len(pbch_dmrs_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            pbch_dmrs_rms_evm_per_subcarrier_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        pbch_dmrs_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_dmrs_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pbch_dmrs_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pbch_dmrs_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pbch_dmrs_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_pbch_dmrs_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace(
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
            pbch_dmrs_rms_evm_per_symbol_mean, "pbch_dmrs_rms_evm_per_symbol_mean", "float32"
        )
        if len(pbch_dmrs_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            pbch_dmrs_rms_evm_per_symbol_mean.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        pbch_dmrs_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=pbch_dmrs_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPBCHDMRSRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pbch_dmrs_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pdsch8_psk_constellation_trace(
        self, selector_string, timeout, psk8_constellation
    ):
        """modacc_fetch_pdsch8_psk_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(psk8_constellation, "psk8_constellation", "complex64")
        if len(psk8_constellation) != actual_array_size_ctype.value:
            psk8_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        psk8_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=psk8_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPDSCH8PSKConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            psk8_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch1024_qam_constellation_trace(
        self, selector_string, timeout, qam1024_constellation
    ):
        """modacc_fetch_pdsch1024_qam_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchPDSCH1024QAMConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam1024_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch16_qam_constellation_trace(
        self, selector_string, timeout, qam16_constellation
    ):
        """modacc_fetch_pdsch16_qam_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchPDSCH16QAMConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam16_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch256_qam_constellation_trace(
        self, selector_string, timeout, qam256_constellation
    ):
        """modacc_fetch_pdsch256_qam_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchPDSCH256QAMConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam256_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch64_qam_constellation_trace(
        self, selector_string, timeout, qam64_constellation
    ):
        """modacc_fetch_pdsch64_qam_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchPDSCH64QAMConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qam64_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_data_constellation_trace(
        self, selector_string, timeout, pdsch_data_constellation
    ):
        """modacc_fetch_pdsch_data_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHDataConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pdsch_data_constellation, "pdsch_data_constellation", "complex64"
        )
        if len(pdsch_data_constellation) != actual_array_size_ctype.value:
            pdsch_data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pdsch_data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pdsch_data_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHDataConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pdsch_data_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_demodulated_bits(self, selector_string, timeout, bits):
        """modacc_fetch_pdsch_demodulated_bits."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHDemodulatedBits(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(bits, "bits", "int8")
        if len(bits) != actual_array_size_ctype.value:
            bits.resize((actual_array_size_ctype.value,), refcheck=False)
        bits_ctype = _get_ctypes_pointer_for_buffer(value=bits, library_type=ctypes.c_int8)

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHDemodulatedBits(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_dmrs_constellation_trace(
        self, selector_string, timeout, pdsch_dmrs_constellation
    ):
        """modacc_fetch_pdsch_dmrs_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pdsch_dmrs_constellation, "pdsch_dmrs_constellation", "complex64"
        )
        if len(pdsch_dmrs_constellation) != actual_array_size_ctype.value:
            pdsch_dmrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pdsch_dmrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pdsch_dmrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHDMRSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pdsch_dmrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_ptrs_constellation_trace(
        self, selector_string, timeout, pdsch_ptrs_constellation
    ):
        """modacc_fetch_pdsch_ptrs_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pdsch_ptrs_constellation, "pdsch_ptrs_constellation", "complex64"
        )
        if len(pdsch_ptrs_constellation) != actual_array_size_ctype.value:
            pdsch_ptrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pdsch_ptrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pdsch_ptrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHPTRSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pdsch_ptrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pdsch_qpsk_constellation_trace(
        self, selector_string, timeout, qpsk_constellation
    ):
        """modacc_fetch_pdsch_qpsk_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchPDSCHQPSKConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            qpsk_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_peak_evm_per_slot_maximum_trace(
        self, selector_string, timeout, peak_evm_per_slot_maximum
    ):
        """modacc_fetch_peak_evm_per_slot_maximum_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace(
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
            peak_evm_per_slot_maximum, "peak_evm_per_slot_maximum", "float32"
        )
        if len(peak_evm_per_slot_maximum) != actual_array_size_ctype.value:
            peak_evm_per_slot_maximum.resize((actual_array_size_ctype.value,), refcheck=False)
        peak_evm_per_slot_maximum_ctype = _get_ctypes_pointer_for_buffer(
            value=peak_evm_per_slot_maximum, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMPerSlotMaximumTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            peak_evm_per_slot_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_peak_evm_per_subcarrier_maximum_trace(
        self, selector_string, timeout, peak_evm_per_subcarrier_maximum
    ):
        """modacc_fetch_peak_evm_per_subcarrier_maximum_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace(
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
            peak_evm_per_subcarrier_maximum, "peak_evm_per_subcarrier_maximum", "float32"
        )
        if len(peak_evm_per_subcarrier_maximum) != actual_array_size_ctype.value:
            peak_evm_per_subcarrier_maximum.resize((actual_array_size_ctype.value,), refcheck=False)
        peak_evm_per_subcarrier_maximum_ctype = _get_ctypes_pointer_for_buffer(
            value=peak_evm_per_subcarrier_maximum, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMPerSubcarrierMaximumTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            peak_evm_per_subcarrier_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_peak_evm_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_per_symbol_maximum
    ):
        """modacc_fetch_peak_evm_per_symbol_maximum_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace(
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
            peak_evm_per_symbol_maximum, "peak_evm_per_symbol_maximum", "float32"
        )
        if len(peak_evm_per_symbol_maximum) != actual_array_size_ctype.value:
            peak_evm_per_symbol_maximum.resize((actual_array_size_ctype.value,), refcheck=False)
        peak_evm_per_symbol_maximum_ctype = _get_ctypes_pointer_for_buffer(
            value=peak_evm_per_symbol_maximum, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMPerSymbolMaximumTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            peak_evm_per_symbol_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pss_constellation_trace(self, selector_string, timeout, pss_constellation):
        """modacc_fetch_pss_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPSSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(pss_constellation, "pss_constellation", "complex64")
        if len(pss_constellation) != actual_array_size_ctype.value:
            pss_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pss_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pss_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPSSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pss_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pss_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, pss_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_pss_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace(
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
            pss_rms_evm_per_subcarrier_mean, "pss_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(pss_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            pss_rms_evm_per_subcarrier_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        pss_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=pss_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPSSRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pss_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pss_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, pss_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_pss_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace(
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
            pss_rms_evm_per_symbol_mean, "pss_rms_evm_per_symbol_mean", "float32"
        )
        if len(pss_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            pss_rms_evm_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        pss_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=pss_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPSSRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pss_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pusch_data_constellation_trace(
        self, selector_string, timeout, pusch_data_constellation
    ):
        """modacc_fetch_pusch_data_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHDataConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pusch_data_constellation, "pusch_data_constellation", "complex64"
        )
        if len(pusch_data_constellation) != actual_array_size_ctype.value:
            pusch_data_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pusch_data_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pusch_data_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHDataConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pusch_data_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pusch_demodulated_bits(self, selector_string, timeout, bits):
        """modacc_fetch_pusch_demodulated_bits."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHDemodulatedBits(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(bits, "bits", "int8")
        if len(bits) != actual_array_size_ctype.value:
            bits.resize((actual_array_size_ctype.value,), refcheck=False)
        bits_ctype = _get_ctypes_pointer_for_buffer(value=bits, library_type=ctypes.c_int8)

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHDemodulatedBits(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pusch_dmrs_constellation_trace(
        self, selector_string, timeout, pusch_dmrs_constellation
    ):
        """modacc_fetch_pusch_dmrs_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pusch_dmrs_constellation, "pusch_dmrs_constellation", "complex64"
        )
        if len(pusch_dmrs_constellation) != actual_array_size_ctype.value:
            pusch_dmrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pusch_dmrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pusch_dmrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHDMRSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pusch_dmrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_pusch_ptrs_constellation_trace(
        self, selector_string, timeout, pusch_ptrs_constellation
    ):
        """modacc_fetch_pusch_ptrs_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(
            pusch_ptrs_constellation, "pusch_ptrs_constellation", "complex64"
        )
        if len(pusch_ptrs_constellation) != actual_array_size_ctype.value:
            pusch_ptrs_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        pusch_ptrs_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=pusch_ptrs_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHPTRSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            pusch_ptrs_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_rms_evm_per_slot_mean_trace(
        self, selector_string, timeout, rms_evm_per_slot_mean
    ):
        """modacc_fetch_rms_evm_per_slot_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace(
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
        _helper.validate_numpy_array(rms_evm_per_slot_mean, "rms_evm_per_slot_mean", "float32")
        if len(rms_evm_per_slot_mean) != actual_array_size_ctype.value:
            rms_evm_per_slot_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_per_slot_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_per_slot_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMPerSlotMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_per_slot_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace(
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
            rms_evm_per_subcarrier_mean, "rms_evm_per_subcarrier_mean", "float32"
        )
        if len(rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            rms_evm_per_subcarrier_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_per_symbol_mean
    ):
        """modacc_fetch_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace(
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
        _helper.validate_numpy_array(rms_evm_per_symbol_mean, "rms_evm_per_symbol_mean", "float32")
        if len(rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            rms_evm_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_rms_evm_high_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_high_per_symbol_mean
    ):
        """modacc_fetch_rms_evm_high_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace(
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
            rms_evm_high_per_symbol_mean, "rms_evm_high_per_symbol_mean", "float32"
        )
        if len(rms_evm_high_per_symbol_mean) != actual_array_size_ctype.value:
            rms_evm_high_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_high_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_high_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMHighPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_high_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_peak_evm_high_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_high_per_symbol_maximum
    ):
        """modacc_fetch_peak_evm_high_per_symbol_maximum_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace(
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
            peak_evm_high_per_symbol_maximum, "peak_evm_high_per_symbol_maximum", "float32"
        )
        if len(peak_evm_high_per_symbol_maximum) != actual_array_size_ctype.value:
            peak_evm_high_per_symbol_maximum.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        peak_evm_high_per_symbol_maximum_ctype = _get_ctypes_pointer_for_buffer(
            value=peak_evm_high_per_symbol_maximum, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMHighPerSymbolMaximumTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            peak_evm_high_per_symbol_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_rms_evm_low_per_symbol_mean_trace(
        self, selector_string, timeout, rms_evm_low_per_symbol_mean
    ):
        """modacc_fetch_rms_evm_low_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace(
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
            rms_evm_low_per_symbol_mean, "rms_evm_low_per_symbol_mean", "float32"
        )
        if len(rms_evm_low_per_symbol_mean) != actual_array_size_ctype.value:
            rms_evm_low_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        rms_evm_low_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=rms_evm_low_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchRMSEVMLowPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            rms_evm_low_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_peak_evm_low_per_symbol_maximum_trace(
        self, selector_string, timeout, peak_evm_low_per_symbol_maximum
    ):
        """modacc_fetch_peak_evm_low_per_symbol_maximum_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace(
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
            peak_evm_low_per_symbol_maximum, "peak_evm_low_per_symbol_maximum", "float32"
        )
        if len(peak_evm_low_per_symbol_maximum) != actual_array_size_ctype.value:
            peak_evm_low_per_symbol_maximum.resize((actual_array_size_ctype.value,), refcheck=False)
        peak_evm_low_per_symbol_maximum_ctype = _get_ctypes_pointer_for_buffer(
            value=peak_evm_low_per_symbol_maximum, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPeakEVMLowPerSymbolMaximumTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            peak_evm_low_per_symbol_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_transient_period_locations_trace(
        self, selector_string, timeout, transient_period_locations
    ):
        """modacc_fetch_transient_period_locations_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchTransientPeriodLocationsTrace(
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
            transient_period_locations, "transient_period_locations", "float32"
        )
        if len(transient_period_locations) != actual_array_size_ctype.value:
            transient_period_locations.resize((actual_array_size_ctype.value,), refcheck=False)
        transient_period_locations_ctype = _get_ctypes_pointer_for_buffer(
            value=transient_period_locations, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchTransientPeriodLocationsTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            transient_period_locations_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_pusch_phase_offset_trace(self, selector_string, timeout, pusch_phase_offset):
        """modacc_fetch_pusch_phase_offset_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace(
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
        _helper.validate_numpy_array(pusch_phase_offset, "pusch_phase_offset", "float32")
        if len(pusch_phase_offset) != actual_array_size_ctype.value:
            pusch_phase_offset.resize((actual_array_size_ctype.value,), refcheck=False)
        pusch_phase_offset_ctype = _get_ctypes_pointer_for_buffer(
            value=pusch_phase_offset, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchPUSCHPhaseOffsetTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            pusch_phase_offset_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_frequency_error_per_slot_maximum_trace(
        self, selector_string, timeout, frequency_error_per_slot_maximum
    ):
        """modacc_fetch_frequency_error_per_slot_maximum_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace(
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
            frequency_error_per_slot_maximum, "frequency_error_per_slot_maximum", "float32"
        )
        if len(frequency_error_per_slot_maximum) != actual_array_size_ctype.value:
            frequency_error_per_slot_maximum.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        frequency_error_per_slot_maximum_ctype = _get_ctypes_pointer_for_buffer(
            value=frequency_error_per_slot_maximum, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchFrequencyErrorPerSlotMaximumTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            frequency_error_per_slot_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

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
        error_code = self._library.RFmxNR_ModAccFetchSpectralFlatnessTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchSpectralFlatnessTrace(
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
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_sss_constellation_trace(self, selector_string, timeout, sss_constellation):
        """modacc_fetch_sss_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchSSSConstellationTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        _helper.validate_numpy_array(sss_constellation, "sss_constellation", "complex64")
        if len(sss_constellation) != actual_array_size_ctype.value:
            sss_constellation.resize((actual_array_size_ctype.value,), refcheck=False)
        sss_constellation_ctype = _get_ctypes_pointer_for_buffer(
            value=sss_constellation, library_type=_custom_types.ComplexSingle
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchSSSConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            sss_constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_sss_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, sss_rms_evm_per_subcarrier_mean
    ):
        """modacc_fetch_sss_rms_evm_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace(
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
            sss_rms_evm_per_subcarrier_mean, "sss_rms_evm_per_subcarrier_mean", "float32"
        )
        if len(sss_rms_evm_per_subcarrier_mean) != actual_array_size_ctype.value:
            sss_rms_evm_per_subcarrier_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        sss_rms_evm_per_subcarrier_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=sss_rms_evm_per_subcarrier_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchSSSRMSEVMPerSubcarrierMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            sss_rms_evm_per_subcarrier_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_sss_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, sss_rms_evm_per_symbol_mean
    ):
        """modacc_fetch_sss_rms_evm_per_symbol_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace(
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
            sss_rms_evm_per_symbol_mean, "sss_rms_evm_per_symbol_mean", "float32"
        )
        if len(sss_rms_evm_per_symbol_mean) != actual_array_size_ctype.value:
            sss_rms_evm_per_symbol_mean.resize((actual_array_size_ctype.value,), refcheck=False)
        sss_rms_evm_per_symbol_mean_ctype = _get_ctypes_pointer_for_buffer(
            value=sss_rms_evm_per_symbol_mean, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchSSSRMSEVMPerSymbolMeanTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            sss_rms_evm_per_symbol_mean_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_subblock_in_band_emission_trace(
        self,
        selector_string,
        timeout,
        subblock_in_band_emission,
        subblock_in_band_emission_mask,
        subblock_in_band_emission_rb_indices,
    ):
        """modacc_fetch_subblock_in_band_emission_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchSubblockInBandEmissionTrace(
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

        _helper.validate_numpy_array(
            subblock_in_band_emission, "subblock_in_band_emission", "float64"
        )
        if len(subblock_in_band_emission) != actual_array_size_ctype.value:
            subblock_in_band_emission.resize((actual_array_size_ctype.value,), refcheck=False)
        subblock_in_band_emission_ctype = _get_ctypes_pointer_for_buffer(
            value=subblock_in_band_emission, library_type=ctypes.c_double
        )
        _helper.validate_numpy_array(
            subblock_in_band_emission_mask, "subblock_in_band_emission_mask", "float64"
        )
        if len(subblock_in_band_emission_mask) != actual_array_size_ctype.value:
            subblock_in_band_emission_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        subblock_in_band_emission_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=subblock_in_band_emission_mask, library_type=ctypes.c_double
        )
        _helper.validate_numpy_array(
            subblock_in_band_emission_rb_indices, "subblock_in_band_emission_rb_indices", "float64"
        )
        if len(subblock_in_band_emission_rb_indices) != actual_array_size_ctype.value:
            subblock_in_band_emission_rb_indices.resize(
                (actual_array_size_ctype.value,), refcheck=False
            )
        subblock_in_band_emission_rb_indices_ctype = _get_ctypes_pointer_for_buffer(
            value=subblock_in_band_emission_rb_indices, library_type=ctypes.c_double
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_ModAccFetchSubblockInBandEmissionTrace(
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
        return error_code

    def modacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
    ):
        """modacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchIQGainImbalancePerSubcarrierMeanTrace(
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

    def modacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
    ):
        """modacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace(
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
        error_code = self._library.RFmxNR_ModAccFetchIQQuadratureErrorPerSubcarrierMeanTrace(
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
        error_code = self._library.RFmxNR_ACPFetchAbsolutePowersTrace(
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
        error_code = self._library.RFmxNR_ACPFetchAbsolutePowersTrace(
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
        error_code = self._library.RFmxNR_ACPFetchComponentCarrierMeasurementArray(
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
        error_code = self._library.RFmxNR_ACPFetchComponentCarrierMeasurementArray(
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
        error_code = self._library.RFmxNR_ACPFetchOffsetMeasurementArray(
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
        error_code = self._library.RFmxNR_ACPFetchOffsetMeasurementArray(
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
        error_code = self._library.RFmxNR_ACPFetchRelativePowersTrace(
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
        error_code = self._library.RFmxNR_ACPFetchRelativePowersTrace(
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
        error_code = self._library.RFmxNR_ACPFetchSpectrum(
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
        error_code = self._library.RFmxNR_ACPFetchSpectrum(
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

    def txp_fetch_power_trace(self, selector_string, timeout, power):
        """txp_fetch_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_TXPFetchPowerTrace(
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
        error_code = self._library.RFmxNR_TXPFetchPowerTrace(
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

    def pvt_fetch_measurement_array(self, selector_string, timeout):
        """pvt_fetch_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_PVTFetchMeasurementArray(
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
        absolute_off_power_before_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        absolute_off_power_after_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        absolute_on_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        burst_width_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_PVTFetchMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            measurement_status_ctype,
            absolute_off_power_before_ctype,
            absolute_off_power_after_ctype,
            absolute_on_power_ctype,
            burst_width_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            [enums.PvtMeasurementStatus(value) for value in measurement_status_ctype],
            absolute_off_power_before_ctype[:],
            absolute_off_power_after_ctype[:],
            absolute_on_power_ctype[:],
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
        error_code = self._library.RFmxNR_PVTFetchSignalPowerTrace(
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
        error_code = self._library.RFmxNR_PVTFetchSignalPowerTrace(
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

    def pvt_fetch_windowed_signal_power_trace(
        self, selector_string, timeout, windowed_signal_power
    ):
        """pvt_fetch_windowed_signal_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_PVTFetchWindowedSignalPowerTrace(
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
        _helper.validate_numpy_array(windowed_signal_power, "windowed_signal_power", "float32")
        if len(windowed_signal_power) != actual_array_size_ctype.value:
            windowed_signal_power.resize((actual_array_size_ctype.value,), refcheck=False)
        windowed_signal_power_ctype = _get_ctypes_pointer_for_buffer(
            value=windowed_signal_power, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_PVTFetchWindowedSignalPowerTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            windowed_signal_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def obw_fetch_spectrum(self, selector_string, timeout, spectrum):
        """obw_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_OBWFetchSpectrum(
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
        error_code = self._library.RFmxNR_OBWFetchSpectrum(
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
        error_code = self._library.RFmxNR_SEMFetchComponentCarrierMeasurementArray(
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

        absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        peak_frequency_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxNR_SEMFetchComponentCarrierMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            absolute_power_ctype,
            peak_absolute_power_ctype,
            peak_frequency_ctype,
            relative_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            absolute_power_ctype[:],
            peak_absolute_power_ctype[:],
            peak_frequency_ctype[:],
            relative_power_ctype[:],
            error_code,
        )

    def sem_fetch_lower_offset_margin_array(self, selector_string, timeout):
        """sem_fetch_lower_offset_margin_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_SEMFetchLowerOffsetMarginArray(
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
        error_code = self._library.RFmxNR_SEMFetchLowerOffsetMarginArray(
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
        error_code = self._library.RFmxNR_SEMFetchLowerOffsetPowerArray(
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
        error_code = self._library.RFmxNR_SEMFetchLowerOffsetPowerArray(
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
        error_code = self._library.RFmxNR_SEMFetchSpectrum(
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
        error_code = self._library.RFmxNR_SEMFetchSpectrum(
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
        error_code = self._library.RFmxNR_SEMFetchUpperOffsetMarginArray(
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
        error_code = self._library.RFmxNR_SEMFetchUpperOffsetMarginArray(
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
        error_code = self._library.RFmxNR_SEMFetchUpperOffsetPowerArray(
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
        error_code = self._library.RFmxNR_SEMFetchUpperOffsetPowerArray(
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

    def chp_fetch_measurement_array(self, selector_string, timeout):
        """chp_fetch_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxNR_CHPFetchComponentCarrierMeasurementArray(
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
        error_code = self._library.RFmxNR_CHPFetchComponentCarrierMeasurementArray(
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
        error_code = self._library.RFmxNR_CHPFetchSpectrum(
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
        error_code = self._library.RFmxNR_CHPFetchSpectrum(
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

    def clone_signal_configuration(self, old_signal_name, new_signal_name):
        """clone_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        old_signal_name_ctype = ctypes.create_string_buffer(old_signal_name.encode(self._encoding))
        new_signal_name_ctype = ctypes.create_string_buffer(new_signal_name.encode(self._encoding))
        error_code = self._library.RFmxNR_CloneSignalConfiguration(
            vi_ctype, old_signal_name_ctype, new_signal_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        import nirfmxnr

        signal_configuration = (
            nirfmxnr._NRSignalConfiguration.get_nr_signal_configuration(  # type: ignore
                self._instr_session, new_signal_name, True
            )
        )
        return signal_configuration, error_code

    def send_software_edge_trigger(self):
        """send_software_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        error_code = self._library.RFmxNR_SendSoftwareEdgeTrigger(vi_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def delete_signal_configuration(self, ignore_driver_error):
        """delete_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(
            self._signal_obj.signal_configuration_name.encode(self._encoding)
        )
        error_code = self._library.RFmxNR_DeleteSignalConfiguration(vi_ctype, signal_name_ctype)
        if not ignore_driver_error:
            errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_all_named_result_names(self, selector_string):
        """get_all_named_result_names."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        actual_result_names_size_ctype = ctypes.c_int32(0)
        default_result_exists_ctype = ctypes.c_int32()

        # call library function to get the size of array
        error_code = self._library.RFmxNR_GetAllNamedResultNames(
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
        error_code = self._library.RFmxNR_GetAllNamedResultNames(
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
        error_code = self._library.RFmxNR_AnalyzeIQ1Waveform(
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
        error_code = self._library.RFmxNR_AnalyzeSpectrum1Waveform(
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
        error_code = self._library.RFmxNR_AnalyzeNWaveformsIQ(
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
        error_code = self._library.RFmxNR_AnalyzeNWaveformsSpectrum(
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
