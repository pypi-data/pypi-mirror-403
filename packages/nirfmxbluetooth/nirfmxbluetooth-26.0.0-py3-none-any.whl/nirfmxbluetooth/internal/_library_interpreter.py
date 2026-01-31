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

import nirfmxbluetooth.attributes as attributes
import nirfmxbluetooth.enums as enums
import nirfmxbluetooth.errors as errors
import nirfmxbluetooth.internal._custom_types as _custom_types
import nirfmxbluetooth.internal._helper as _helper
import nirfmxbluetooth.internal._library_singleton as _library_singleton
import nirfmxinstr
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
        size_or_error_code = self._library.RFmxBT_GetErrorString(
            self._vi, error_code_ctype, 0, None
        )
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxBT_GetErrorString(
                self._vi, error_code_ctype, size_or_error_code, error_string_ctype
            )
        return error_string_ctype.value.decode(self._encoding)

    def get_error(self) -> tuple[int, Any]:
        """Returns the error code and error message."""
        error_code_ctype = ctypes.c_int32()
        error_string_ctype = ctypes.create_string_buffer(0)
        size_or_error_code = self._library.RFmxBT_GetError(self._vi, error_code_ctype, 0, None)
        if size_or_error_code > 0 and error_code_ctype.value != 0:
            error_code_ctype = ctypes.c_int32(error_code_ctype.value)
            error_string_ctype = ctypes.create_string_buffer(size_or_error_code)
            self._library.RFmxBT_GetError(
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
        error_code = self._library.RFmxBT_ResetAttribute(
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
                local_personality.value == nirfmxinstr.Personalities.BT.value
            )
        elif self._signal_obj is not None:
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
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        attribute_id_ctype = ctypes.c_uint32(attribute_id)
        attr_val_ctype = ctypes.c_int8()
        error_code = self._library.RFmxBT_GetAttributeI8(
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
        error_code = self._library.RFmxBT_SetAttributeI8(
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
        error_code = self._library.RFmxBT_GetAttributeI8Array(
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
        error_code = self._library.RFmxBT_GetAttributeI8Array(
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
        error_code = self._library.RFmxBT_SetAttributeI8Array(
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
        error_code = self._library.RFmxBT_GetAttributeI16(
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
        error_code = self._library.RFmxBT_SetAttributeI16(
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
        error_code = self._library.RFmxBT_GetAttributeI32(
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
        error_code = self._library.RFmxBT_SetAttributeI32(
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
        error_code = self._library.RFmxBT_GetAttributeI32Array(
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
        error_code = self._library.RFmxBT_GetAttributeI32Array(
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
        error_code = self._library.RFmxBT_SetAttributeI32Array(
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
        error_code = self._library.RFmxBT_GetAttributeI64(
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
        error_code = self._library.RFmxBT_SetAttributeI64(
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
        error_code = self._library.RFmxBT_GetAttributeI64Array(
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
        error_code = self._library.RFmxBT_GetAttributeI64Array(
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
        error_code = self._library.RFmxBT_SetAttributeI64Array(
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
        error_code = self._library.RFmxBT_GetAttributeU8(
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
        error_code = self._library.RFmxBT_SetAttributeU8(
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
        error_code = self._library.RFmxBT_GetAttributeU8Array(
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
        error_code = self._library.RFmxBT_GetAttributeU8Array(
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
        error_code = self._library.RFmxBT_SetAttributeU8Array(
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
        error_code = self._library.RFmxBT_GetAttributeU16(
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
        error_code = self._library.RFmxBT_SetAttributeU16(
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
        error_code = self._library.RFmxBT_GetAttributeU32(
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
        error_code = self._library.RFmxBT_SetAttributeU32(
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
        error_code = self._library.RFmxBT_GetAttributeU32Array(
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
        error_code = self._library.RFmxBT_GetAttributeU32Array(
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
        error_code = self._library.RFmxBT_SetAttributeU32Array(
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
        error_code = self._library.RFmxBT_GetAttributeU64Array(
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
        error_code = self._library.RFmxBT_GetAttributeU64Array(
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
        error_code = self._library.RFmxBT_SetAttributeU64Array(
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
        error_code = self._library.RFmxBT_GetAttributeF32(
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
        error_code = self._library.RFmxBT_SetAttributeF32(
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
        error_code = self._library.RFmxBT_GetAttributeF32Array(
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
        error_code = self._library.RFmxBT_GetAttributeF32Array(
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
        error_code = self._library.RFmxBT_SetAttributeF32Array(
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
        error_code = self._library.RFmxBT_GetAttributeF64(
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
        error_code = self._library.RFmxBT_SetAttributeF64(
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
        error_code = self._library.RFmxBT_GetAttributeF64Array(
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
        error_code = self._library.RFmxBT_GetAttributeF64Array(
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
        error_code = self._library.RFmxBT_SetAttributeF64Array(
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
        error_code = self._library.RFmxBT_GetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxBT_GetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxBT_SetAttributeNIComplexSingleArray(
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
        error_code = self._library.RFmxBT_GetAttributeNIComplexDoubleArray(
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
        error_code = self._library.RFmxBT_GetAttributeNIComplexDoubleArray(
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
        error_code = self._library.RFmxBT_SetAttributeNIComplexDoubleArray(
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
        size_or_error_code = self._library.RFmxBT_GetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, array_size_ctype, attr_val_ctype
        )
        if size_or_error_code < 0:
            errors.handle_error(
                self, size_or_error_code, ignore_warnings=True, is_error_handling=False
            )
            return None, size_or_error_code
        array_size_ctype = ctypes.c_int32(size_or_error_code)
        attr_val_ctype = (ctypes.c_char * array_size_ctype.value)()
        error_code = self._library.RFmxBT_GetAttributeString(
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
        error_code = self._library.RFmxBT_SetAttributeString(
            vi_ctype, selector_string_ctype, attribute_id_ctype, attr_val_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def abort_measurements(self, selector_string):
        """abort_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxBT_AbortMeasurements(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_detect_signal(self, selector_string, timeout):
        """auto_detect_signal."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxBT_AutoDetectSignal(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def auto_level(self, selector_string, measurement_interval):
        """auto_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurement_interval_ctype = ctypes.c_double(measurement_interval)
        reference_level_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_AutoLevel(
            vi_ctype, selector_string_ctype, measurement_interval_ctype, reference_level_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return reference_level_ctype.value, error_code

    def check_measurement_status(self, selector_string):
        """check_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        is_done_ctype = ctypes.c_int32()
        error_code = self._library.RFmxBT_CheckMeasurementStatus(
            vi_ctype, selector_string_ctype, is_done_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return bool(is_done_ctype.value), error_code

    def clear_all_named_results(self, selector_string):
        """clear_all_named_results."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxBT_ClearAllNamedResults(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def clear_named_result(self, selector_string):
        """clear_named_result."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxBT_ClearNamedResult(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def commit(self, selector_string):
        """commit."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxBT_Commit(vi_ctype, selector_string_ctype)
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
        error_code = self._library.RFmxBT_CfgDigitalEdgeTrigger(
            vi_ctype,
            selector_string_ctype,
            digital_edge_source_ctype,
            digital_edge_ctype,
            trigger_delay_ctype,
            enable_trigger_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency_channel_number(self, selector_string, standard, channel_number):
        """configure_frequency_channel_number."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        standard_ctype = ctypes.c_int32(standard)
        channel_number_ctype = ctypes.c_int32(channel_number)
        error_code = self._library.RFmxBT_CfgFrequencyChannelNumber(
            vi_ctype, selector_string_ctype, standard_ctype, channel_number_ctype
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
        error_code = self._library.RFmxBT_CfgIQPowerEdgeTrigger(
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
        error_code = self._library.RFmxBT_CfgSoftwareEdgeTrigger(
            vi_ctype, selector_string_ctype, trigger_delay_ctype, enable_trigger_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def create_signal_configuration(self, signal_name):
        """create_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(signal_name.encode(self._encoding))
        error_code = self._library.RFmxBT_CreateSignalConfiguration(vi_ctype, signal_name_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def disable_trigger(self, selector_string):
        """disable_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxBT_DisableTrigger(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def initiate(self, selector_string, result_name):
        """initiate."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        result_name_ctype = ctypes.create_string_buffer(result_name.encode(self._encoding))
        error_code = self._library.RFmxBT_Initiate(
            vi_ctype, selector_string_ctype, result_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def reset_to_default(self, selector_string):
        """reset_to_default."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        error_code = self._library.RFmxBT_ResetToDefault(vi_ctype, selector_string_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def select_measurements(self, selector_string, measurements, enable_all_traces):
        """select_measurements."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        measurements_ctype = ctypes.c_uint32(measurements)
        enable_all_traces_ctype = ctypes.c_int32(enable_all_traces)
        error_code = self._library.RFmxBT_SelectMeasurements(
            vi_ctype, selector_string_ctype, measurements_ctype, enable_all_traces_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def wait_for_measurement_complete(self, selector_string, timeout):
        """wait_for_measurement_complete."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        error_code = self._library.RFmxBT_WaitForMeasurementComplete(
            vi_ctype, selector_string_ctype, timeout_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """txp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_TXPCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_configure_burst_synchronization_type(self, selector_string, burst_synchronization_type):
        """txp_configure_burst_synchronization_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        burst_synchronization_type_ctype = ctypes.c_int32(burst_synchronization_type)
        error_code = self._library.RFmxBT_TXPCfgBurstSynchronizationType(
            vi_ctype, selector_string_ctype, burst_synchronization_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """modacc_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_ModAccCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_configure_burst_synchronization_type(
        self, selector_string, burst_synchronization_type
    ):
        """modacc_configure_burst_synchronization_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        burst_synchronization_type_ctype = ctypes.c_int32(burst_synchronization_type)
        error_code = self._library.RFmxBT_ModAccCfgBurstSynchronizationType(
            vi_ctype, selector_string_ctype, burst_synchronization_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def twenty_db_bandwidth_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count
    ):
        """twenty_db_bandwidth_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_20dBBandwidthCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def frequency_range_configure_averaging(
        self, selector_string, averaging_enabled, averaging_count
    ):
        """frequency_range_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_FrequencyRangeCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def frequency_range_configure_span(self, selector_string, span):
        """frequency_range_configure_span."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        span_ctype = ctypes.c_double(span)
        error_code = self._library.RFmxBT_FrequencyRangeCfgSpan(
            vi_ctype, selector_string_ctype, span_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """acp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_ACPCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_burst_synchronization_type(self, selector_string, burst_synchronization_type):
        """acp_configure_burst_synchronization_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        burst_synchronization_type_ctype = ctypes.c_int32(burst_synchronization_type)
        error_code = self._library.RFmxBT_ACPCfgBurstSynchronizationType(
            vi_ctype, selector_string_ctype, burst_synchronization_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_number_of_offsets(self, selector_string, number_of_offsets):
        """acp_configure_number_of_offsets."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        number_of_offsets_ctype = ctypes.c_int32(number_of_offsets)
        error_code = self._library.RFmxBT_ACPCfgNumberOfOffsets(
            vi_ctype, selector_string_ctype, number_of_offsets_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def acp_configure_offset_channel_mode(self, selector_string, offset_channel_mode):
        """acp_configure_offset_channel_mode."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        offset_channel_mode_ctype = ctypes.c_int32(offset_channel_mode)
        error_code = self._library.RFmxBT_ACPCfgOffsetChannelMode(
            vi_ctype, selector_string_ctype, offset_channel_mode_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def powerramp_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """powerramp_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_PowerRampCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def powerramp_configure_burst_synchronization_type(
        self, selector_string, burst_synchronization_type
    ):
        """powerramp_configure_burst_synchronization_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        burst_synchronization_type_ctype = ctypes.c_int32(burst_synchronization_type)
        error_code = self._library.RFmxBT_PowerRampCfgBurstSynchronizationType(
            vi_ctype, selector_string_ctype, burst_synchronization_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modspectrum_configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        """modspectrum_configure_averaging."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        averaging_enabled_ctype = ctypes.c_int32(averaging_enabled)
        averaging_count_ctype = ctypes.c_int32(averaging_count)
        error_code = self._library.RFmxBT_ModSpectrumCfgAveraging(
            vi_ctype, selector_string_ctype, averaging_enabled_ctype, averaging_count_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modspectrum_configure_burst_synchronization_type(
        self, selector_string, burst_synchronization_type
    ):
        """modspectrum_configure_burst_synchronization_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        burst_synchronization_type_ctype = ctypes.c_int32(burst_synchronization_type)
        error_code = self._library.RFmxBT_ModSpectrumCfgBurstSynchronizationType(
            vi_ctype, selector_string_ctype, burst_synchronization_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_channel_number(self, selector_string, channel_number):
        """configure_channel_number."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        channel_number_ctype = ctypes.c_int32(channel_number)
        error_code = self._library.RFmxBT_CfgChannelNumber(
            vi_ctype, selector_string_ctype, channel_number_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_data_rate(self, selector_string, data_rate):
        """configure_data_rate."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        data_rate_ctype = ctypes.c_int32(data_rate)
        error_code = self._library.RFmxBT_CfgDataRate(
            vi_ctype, selector_string_ctype, data_rate_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_external_attenuation(self, selector_string, external_attenuation):
        """configure_external_attenuation."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        external_attenuation_ctype = ctypes.c_double(external_attenuation)
        error_code = self._library.RFmxBT_CfgExternalAttenuation(
            vi_ctype, selector_string_ctype, external_attenuation_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_frequency(self, selector_string, center_frequency):
        """configure_frequency."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        center_frequency_ctype = ctypes.c_double(center_frequency)
        error_code = self._library.RFmxBT_CfgFrequency(
            vi_ctype, selector_string_ctype, center_frequency_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_le_direction_finding(
        self, selector_string, direction_finding_mode, cte_length, cte_slot_duration
    ):
        """configure_le_direction_finding."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        direction_finding_mode_ctype = ctypes.c_int32(direction_finding_mode)
        cte_length_ctype = ctypes.c_double(cte_length)
        cte_slot_duration_ctype = ctypes.c_double(cte_slot_duration)
        error_code = self._library.RFmxBT_CfgLEDirectionFinding(
            vi_ctype,
            selector_string_ctype,
            direction_finding_mode_ctype,
            cte_length_ctype,
            cte_slot_duration_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_packet_type(self, selector_string, packet_type):
        """configure_packet_type."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        packet_type_ctype = ctypes.c_int32(packet_type)
        error_code = self._library.RFmxBT_CfgPacketType(
            vi_ctype, selector_string_ctype, packet_type_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_payload_bit_pattern(self, selector_string, payload_bit_pattern):
        """configure_payload_bit_pattern."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        payload_bit_pattern_ctype = ctypes.c_int32(payload_bit_pattern)
        error_code = self._library.RFmxBT_CfgPayloadBitPattern(
            vi_ctype, selector_string_ctype, payload_bit_pattern_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_payload_length(self, selector_string, payload_length_mode, payload_length):
        """configure_payload_length."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        payload_length_mode_ctype = ctypes.c_int32(payload_length_mode)
        payload_length_ctype = ctypes.c_int32(payload_length)
        error_code = self._library.RFmxBT_CfgPayloadLength(
            vi_ctype, selector_string_ctype, payload_length_mode_ctype, payload_length_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def configure_reference_level(self, selector_string, reference_level):
        """configure_reference_level."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        reference_level_ctype = ctypes.c_double(reference_level)
        error_code = self._library.RFmxBT_CfgReferenceLevel(
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
        error_code = self._library.RFmxBT_CfgRF(
            vi_ctype,
            selector_string_ctype,
            center_frequency_ctype,
            reference_level_ctype,
            external_attenuation_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def txp_fetch_edr_powers(self, selector_string, timeout):
        """txp_fetch_edr_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        edr_gfsk_average_power_mean_ctype = ctypes.c_double()
        edr_dpsk_average_power_mean_ctype = ctypes.c_double()
        edr_dpsk_gfsk_average_power_ratio_mean_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_TXPFetchEDRPowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            edr_gfsk_average_power_mean_ctype,
            edr_dpsk_average_power_mean_ctype,
            edr_dpsk_gfsk_average_power_ratio_mean_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            edr_gfsk_average_power_mean_ctype.value,
            edr_dpsk_average_power_mean_ctype.value,
            edr_dpsk_gfsk_average_power_ratio_mean_ctype.value,
            error_code,
        )

    def txp_fetch_le_cte_reference_period_powers(self, selector_string, timeout):
        """txp_fetch_le_cte_reference_period_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        reference_period_average_power_mean_ctype = ctypes.c_double()
        reference_period_peak_absolute_power_deviation_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_TXPFetchLECTEReferencePeriodPowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            reference_period_average_power_mean_ctype,
            reference_period_peak_absolute_power_deviation_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            reference_period_average_power_mean_ctype.value,
            reference_period_peak_absolute_power_deviation_maximum_ctype.value,
            error_code,
        )

    def txp_fetch_le_cte_transmit_slot_powers(self, selector_string, timeout):
        """txp_fetch_le_cte_transmit_slot_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        transmit_slot_average_power_mean_ctype = ctypes.c_double()
        transmit_slot_peak_absolute_power_deviation_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_TXPFetchLECTETransmitSlotPowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            transmit_slot_average_power_mean_ctype,
            transmit_slot_peak_absolute_power_deviation_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            transmit_slot_average_power_mean_ctype.value,
            transmit_slot_peak_absolute_power_deviation_maximum_ctype.value,
            error_code,
        )

    def txp_fetch_powers(self, selector_string, timeout):
        """txp_fetch_powers."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        average_power_mean_ctype = ctypes.c_double()
        average_power_maximum_ctype = ctypes.c_double()
        average_power_minimum_ctype = ctypes.c_double()
        peak_to_average_power_ratio_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_TXPFetchPowers(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_power_mean_ctype,
            average_power_maximum_ctype,
            average_power_minimum_ctype,
            peak_to_average_power_ratio_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            average_power_mean_ctype.value,
            average_power_maximum_ctype.value,
            average_power_minimum_ctype.value,
            peak_to_average_power_ratio_maximum_ctype.value,
            error_code,
        )

    def modacc_fetch_devm(self, selector_string, timeout):
        """modacc_fetch_devm."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        peak_rms_devm_maximum_ctype = ctypes.c_double()
        peak_devm_maximum_ctype = ctypes.c_double()
        ninetynine_percent_devm_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchDEVM(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            peak_rms_devm_maximum_ctype,
            peak_devm_maximum_ctype,
            ninetynine_percent_devm_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            peak_rms_devm_maximum_ctype.value,
            peak_devm_maximum_ctype.value,
            ninetynine_percent_devm_ctype.value,
            error_code,
        )

    def modacc_fetch_devm_magnitude_error(self, selector_string, timeout):
        """modacc_fetch_devm_magnitude_error."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        average_rms_magnitude_error_mean_ctype = ctypes.c_double()
        peak_rms_magnitude_error_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchDEVMMagnitudeError(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_rms_magnitude_error_mean_ctype,
            peak_rms_magnitude_error_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            average_rms_magnitude_error_mean_ctype.value,
            peak_rms_magnitude_error_maximum_ctype.value,
            error_code,
        )

    def modacc_fetch_devm_phase_error(self, selector_string, timeout):
        """modacc_fetch_devm_phase_error."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        average_rms_phase_error_mean_ctype = ctypes.c_double()
        peak_rms_phase_error_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchDEVMPhaseError(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            average_rms_phase_error_mean_ctype,
            peak_rms_phase_error_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            average_rms_phase_error_mean_ctype.value,
            peak_rms_phase_error_maximum_ctype.value,
            error_code,
        )

    def modacc_fetch_df1(self, selector_string, timeout):
        """modacc_fetch_df1."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        df1avg_maximum_ctype = ctypes.c_double()
        df1avg_minimum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchDf1(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            df1avg_maximum_ctype,
            df1avg_minimum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return df1avg_maximum_ctype.value, df1avg_minimum_ctype.value, error_code

    def modacc_fetch_df2(self, selector_string, timeout):
        """modacc_fetch_df2."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        df2avg_minimum_ctype = ctypes.c_double()
        percentage_of_symbols_above_df2max_threshold_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchDf2(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            df2avg_minimum_ctype,
            percentage_of_symbols_above_df2max_threshold_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            df2avg_minimum_ctype.value,
            percentage_of_symbols_above_df2max_threshold_ctype.value,
            error_code,
        )

    def modacc_fetch_frequency_error_br(self, selector_string, timeout):
        """modacc_fetch_frequency_error_br."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        initial_frequency_error_maximum_ctype = ctypes.c_double()
        peak_frequency_drift_maximum_ctype = ctypes.c_double()
        peak_frequency_drift_rate_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorBR(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            initial_frequency_error_maximum_ctype,
            peak_frequency_drift_maximum_ctype,
            peak_frequency_drift_rate_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            initial_frequency_error_maximum_ctype.value,
            peak_frequency_drift_maximum_ctype.value,
            peak_frequency_drift_rate_maximum_ctype.value,
            error_code,
        )

    def modacc_fetch_frequency_error_edr(self, selector_string, timeout):
        """modacc_fetch_frequency_error_edr."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        header_frequency_error_wi_maximum_ctype = ctypes.c_double()
        peak_frequency_error_wi_plus_w0_maximum_ctype = ctypes.c_double()
        peak_frequency_error_w0_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorEDR(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            header_frequency_error_wi_maximum_ctype,
            peak_frequency_error_wi_plus_w0_maximum_ctype,
            peak_frequency_error_w0_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            header_frequency_error_wi_maximum_ctype.value,
            peak_frequency_error_wi_plus_w0_maximum_ctype.value,
            peak_frequency_error_w0_maximum_ctype.value,
            error_code,
        )

    def modacc_fetch_frequency_error_le(self, selector_string, timeout):
        """modacc_fetch_frequency_error_le."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        peak_frequency_error_maximum_ctype = ctypes.c_double()
        initial_frequency_drift_maximum_ctype = ctypes.c_double()
        peak_frequency_drift_maximum_ctype = ctypes.c_double()
        peak_frequency_drift_rate_maximum_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorLE(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            peak_frequency_error_maximum_ctype,
            initial_frequency_drift_maximum_ctype,
            peak_frequency_drift_maximum_ctype,
            peak_frequency_drift_rate_maximum_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            peak_frequency_error_maximum_ctype.value,
            initial_frequency_drift_maximum_ctype.value,
            peak_frequency_drift_maximum_ctype.value,
            peak_frequency_drift_rate_maximum_ctype.value,
            error_code,
        )

    def twenty_db_bandwidth_fetch_measurement(self, selector_string, timeout):
        """twenty_db_bandwidth_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        peak_power_ctype = ctypes.c_double()
        bandwidth_ctype = ctypes.c_double()
        high_frequency_ctype = ctypes.c_double()
        low_frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_20dBBandwidthFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            peak_power_ctype,
            bandwidth_ctype,
            high_frequency_ctype,
            low_frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            peak_power_ctype.value,
            bandwidth_ctype.value,
            high_frequency_ctype.value,
            low_frequency_ctype.value,
            error_code,
        )

    def frequency_range_fetch_measurement(self, selector_string, timeout):
        """frequency_range_fetch_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        high_frequency_ctype = ctypes.c_double()
        low_frequency_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_FrequencyRangeFetchMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            high_frequency_ctype,
            low_frequency_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return high_frequency_ctype.value, low_frequency_ctype.value, error_code

    def acp_fetch_measurement_status(self, selector_string, timeout):
        """acp_fetch_measurement_status."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        measurement_status_ctype = ctypes.c_int32()
        error_code = self._library.RFmxBT_ACPFetchMeasurementStatus(
            vi_ctype, selector_string_ctype, timeout_ctype, measurement_status_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return enums.AcpResultsMeasurementStatus(measurement_status_ctype.value), error_code

    def acp_fetch_offset_measurement(self, selector_string, timeout):
        """acp_fetch_offset_measurement."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        lower_absolute_power_ctype = ctypes.c_double()
        upper_absolute_power_ctype = ctypes.c_double()
        lower_relative_power_ctype = ctypes.c_double()
        upper_relative_power_ctype = ctypes.c_double()
        lower_margin_ctype = ctypes.c_double()
        upper_margin_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ACPFetchOffsetMeasurement(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            lower_absolute_power_ctype,
            upper_absolute_power_ctype,
            lower_relative_power_ctype,
            upper_relative_power_ctype,
            lower_margin_ctype,
            upper_margin_ctype,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            lower_absolute_power_ctype.value,
            upper_absolute_power_ctype.value,
            lower_relative_power_ctype.value,
            upper_relative_power_ctype.value,
            lower_margin_ctype.value,
            upper_margin_ctype.value,
            error_code,
        )

    def acp_fetch_reference_channel_power(self, selector_string, timeout):
        """acp_fetch_reference_channel_power."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        reference_channel_power_ctype = ctypes.c_double()
        error_code = self._library.RFmxBT_ACPFetchReferenceChannelPower(
            vi_ctype, selector_string_ctype, timeout_ctype, reference_channel_power_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return reference_channel_power_ctype.value, error_code

    def txp_fetch_le_cte_transmit_slot_powers_array(self, selector_string, timeout):
        """txp_fetch_le_cte_transmit_slot_powers_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_TXPFetchLECTETransmitSlotPowersArray(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        transmit_slot_average_power_mean_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        transmit_slot_peak_absolute_power_deviation_maximum_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_TXPFetchLECTETransmitSlotPowersArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            transmit_slot_average_power_mean_ctype,
            transmit_slot_peak_absolute_power_deviation_maximum_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            transmit_slot_average_power_mean_ctype[:],
            transmit_slot_peak_absolute_power_deviation_maximum_ctype[:],
            error_code,
        )

    def txp_fetch_power_trace(self, selector_string, timeout, power):
        """txp_fetch_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_TXPFetchPowerTrace(
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
        error_code = self._library.RFmxBT_TXPFetchPowerTrace(
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

    def modacc_fetch_constellation_trace(self, selector_string, timeout, constellation):
        """modacc_fetch_constellation_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchConstellationTrace(
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
        error_code = self._library.RFmxBT_ModAccFetchConstellationTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            constellation_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def modacc_fetch_cs_detrended_phase_trace(self, selector_string, timeout, cs_detrended_phase):
        """modacc_fetch_cs_detrended_phase_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchCSDetrendedPhaseTrace(
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
        _helper.validate_numpy_array(cs_detrended_phase, "cs_detrended_phase", "float32")
        if len(cs_detrended_phase) != actual_array_size_ctype.value:
            cs_detrended_phase.resize((actual_array_size_ctype.value,), refcheck=False)
        cs_detrended_phase_ctype = _get_ctypes_pointer_for_buffer(
            value=cs_detrended_phase, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchCSDetrendedPhaseTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            cs_detrended_phase_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_cs_tone_trace(
        self, selector_string, timeout, cs_tone_amplitude, cs_tone_phase
    ):
        """modacc_fetch_cs_tone_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchCSToneTrace(
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
        _helper.validate_numpy_array(cs_tone_amplitude, "cs_tone_amplitude", "float32")
        if len(cs_tone_amplitude) != actual_array_size_ctype.value:
            cs_tone_amplitude.resize((actual_array_size_ctype.value,), refcheck=False)
        cs_tone_amplitude_ctype = _get_ctypes_pointer_for_buffer(
            value=cs_tone_amplitude, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(cs_tone_phase, "cs_tone_phase", "float32")
        if len(cs_tone_phase) != actual_array_size_ctype.value:
            cs_tone_phase.resize((actual_array_size_ctype.value,), refcheck=False)
        cs_tone_phase_ctype = _get_ctypes_pointer_for_buffer(
            value=cs_tone_phase, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchCSToneTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            cs_tone_amplitude_ctype,
            cs_tone_phase_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_demodulated_bit_trace(self, selector_string, timeout):
        """modacc_fetch_demodulated_bit_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchDemodulatedBitTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        demodulated_bits_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_int8, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchDemodulatedBitTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            demodulated_bits_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return demodulated_bits_ctype[:], error_code

    def modacc_fetch_devm_per_symbol_trace(self, selector_string, timeout):
        """modacc_fetch_devm_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchDEVMPerSymbolTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        devm_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchDEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            devm_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return devm_per_symbol_ctype[:], error_code

    def modacc_fetch_evm_per_symbol_trace(self, selector_string, timeout):
        """modacc_fetch_evm_per_symbol_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchEVMPerSymbolTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        evm_per_symbol_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchEVMPerSymbolTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            evm_per_symbol_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return evm_per_symbol_ctype[:], error_code

    def modacc_fetch_df1max_trace(self, selector_string, timeout):
        """modacc_fetch_df1max_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchDf1maxTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        time_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )
        df1max_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchDf1maxTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            time_ctype,
            df1max_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return time_ctype[:], df1max_ctype[:], error_code

    def modacc_fetch_df2max_trace(self, selector_string, timeout):
        """modacc_fetch_df2max_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchDf2maxTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        time_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )
        df2max_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchDf2maxTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            time_ctype,
            df2max_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return time_ctype[:], df2max_ctype[:], error_code

    def modacc_fetch_df4avg_trace(self, selector_string, timeout):
        """modacc_fetch_df4avg_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchDf4avgTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        time_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )
        df4avg_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchDf4avgTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            time_ctype,
            df4avg_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return time_ctype[:], df4avg_ctype[:], error_code

    def modacc_fetch_frequency_error_trace_br(self, selector_string, timeout):
        """modacc_fetch_frequency_error_trace_br."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorTraceBR(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        time_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )
        frequency_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorTraceBR(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            time_ctype,
            frequency_error_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return time_ctype[:], frequency_error_ctype[:], error_code

    def modacc_fetch_frequency_error_trace_le(self, selector_string, timeout):
        """modacc_fetch_frequency_error_trace_le."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorTraceLE(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        time_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )
        frequency_error_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorTraceLE(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            time_ctype,
            frequency_error_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return time_ctype[:], frequency_error_ctype[:], error_code

    def modacc_fetch_frequency_error_wi_plus_w0_trace_edr(self, selector_string, timeout):
        """modacc_fetch_frequency_error_wi_plus_w0_trace_edr."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR(
            vi_ctype, selector_string_ctype, timeout_ctype, None, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        time_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )
        frequency_error_wi_plus_w0_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyErrorWiPlusW0TraceEDR(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            time_ctype,
            frequency_error_wi_plus_w0_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return time_ctype[:], frequency_error_wi_plus_w0_ctype[:], error_code

    def modacc_fetch_frequency_trace(self, selector_string, timeout, frequency):
        """modacc_fetch_frequency_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyTrace(
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
        _helper.validate_numpy_array(frequency, "frequency", "float32")
        if len(frequency) != actual_array_size_ctype.value:
            frequency.resize((actual_array_size_ctype.value,), refcheck=False)
        frequency_ctype = _get_ctypes_pointer_for_buffer(
            value=frequency, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchFrequencyTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            frequency_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def modacc_fetch_rms_devm_trace(self, selector_string, timeout):
        """modacc_fetch_rms_devm_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModAccFetchRMSDEVMTrace(
            vi_ctype, selector_string_ctype, timeout_ctype, None, 0, actual_array_size_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)

        rms_devm_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_float, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ModAccFetchRMSDEVMTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            rms_devm_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return rms_devm_ctype[:], error_code

    def twenty_db_bandwidth_fetch_spectrum(self, selector_string, timeout, spectrum):
        """twenty_db_bandwidth_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_20dBBandwidthFetchSpectrum(
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
        error_code = self._library.RFmxBT_20dBBandwidthFetchSpectrum(
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

    def frequency_range_fetch_spectrum(self, selector_string, timeout, spectrum):
        """frequency_range_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_FrequencyRangeFetchSpectrum(
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
        error_code = self._library.RFmxBT_FrequencyRangeFetchSpectrum(
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

    def acp_fetch_absolute_power_trace(self, selector_string, timeout, absolute_power):
        """acp_fetch_absolute_power_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ACPFetchAbsolutePowerTrace(
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
        _helper.validate_numpy_array(absolute_power, "absolute_power", "float32")
        if len(absolute_power) != actual_array_size_ctype.value:
            absolute_power.resize((actual_array_size_ctype.value,), refcheck=False)
        absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            value=absolute_power, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ACPFetchAbsolutePowerTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            absolute_power_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def acp_fetch_mask_trace(
        self, selector_string, timeout, limit_with_exception_mask, limit_without_exception_mask
    ):
        """acp_fetch_mask_trace."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ACPFetchMaskTrace(
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
            limit_with_exception_mask, "limit_with_exception_mask", "float32"
        )
        if len(limit_with_exception_mask) != actual_array_size_ctype.value:
            limit_with_exception_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        limit_with_exception_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=limit_with_exception_mask, library_type=ctypes.c_float
        )
        _helper.validate_numpy_array(
            limit_without_exception_mask, "limit_without_exception_mask", "float32"
        )
        if len(limit_without_exception_mask) != actual_array_size_ctype.value:
            limit_without_exception_mask.resize((actual_array_size_ctype.value,), refcheck=False)
        limit_without_exception_mask_ctype = _get_ctypes_pointer_for_buffer(
            value=limit_without_exception_mask, library_type=ctypes.c_float
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ACPFetchMaskTrace(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            x0_ctype,
            dx_ctype,
            limit_with_exception_mask_ctype,
            limit_without_exception_mask_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return x0_ctype.value, dx_ctype.value, error_code

    def acp_fetch_offset_measurement_array(self, selector_string, timeout):
        """acp_fetch_offset_measurement_array."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ACPFetchOffsetMeasurementArray(
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

        lower_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        upper_absolute_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        lower_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        upper_relative_power_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        lower_margin_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )
        upper_margin_ctype = _get_ctypes_pointer_for_buffer(
            library_type=ctypes.c_double, size=actual_array_size_ctype.value
        )

        # call library function again to get array
        error_code = self._library.RFmxBT_ACPFetchOffsetMeasurementArray(
            vi_ctype,
            selector_string_ctype,
            timeout_ctype,
            lower_absolute_power_ctype,
            upper_absolute_power_ctype,
            lower_relative_power_ctype,
            upper_relative_power_ctype,
            lower_margin_ctype,
            upper_margin_ctype,
            actual_array_size_ctype,
            None,
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return (
            lower_absolute_power_ctype[:],
            upper_absolute_power_ctype[:],
            lower_relative_power_ctype[:],
            upper_relative_power_ctype[:],
            lower_margin_ctype[:],
            upper_margin_ctype[:],
            error_code,
        )

    def acp_fetch_spectrum(self, selector_string, timeout, spectrum):
        """acp_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ACPFetchSpectrum(
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
        error_code = self._library.RFmxBT_ACPFetchSpectrum(
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

    def modspectrum_fetch_spectrum(self, selector_string, timeout, spectrum):
        """modspectrum_fetch_spectrum."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        timeout_ctype = ctypes.c_double(timeout)
        actual_array_size_ctype = ctypes.c_int32(0)

        # call library function to get the size of array
        error_code = self._library.RFmxBT_ModSpectrumFetchSpectrum(
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
        error_code = self._library.RFmxBT_ModSpectrumFetchSpectrum(
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
        error_code = self._library.RFmxBT_CloneSignalConfiguration(
            vi_ctype, old_signal_name_ctype, new_signal_name_ctype
        )
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        import nirfmxbluetooth

        signal_configuration = nirfmxbluetooth._BluetoothSignalConfiguration.get_bluetooth_signal_configuration(self._instr_session, new_signal_name, True)  # type: ignore
        return signal_configuration, error_code

    def delete_signal_configuration(self, ignore_driver_error):
        """delete_signal_configuration."""
        vi_ctype = ctypes.c_uint32(self._vi)
        signal_name_ctype = ctypes.create_string_buffer(
            self._signal_obj.signal_configuration_name.encode(self._encoding)
        )
        error_code = self._library.RFmxBT_DeleteSignalConfiguration(vi_ctype, signal_name_ctype)
        if not ignore_driver_error:
            errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def send_software_edge_trigger(self):
        """send_software_edge_trigger."""
        vi_ctype = ctypes.c_uint32(self._vi)
        error_code = self._library.RFmxBT_SendSoftwareEdgeTrigger(vi_ctype)
        errors.handle_error(self, error_code, ignore_warnings=True, is_error_handling=False)
        return error_code

    def get_all_named_result_names(self, selector_string):
        """get_all_named_result_names."""
        vi_ctype = ctypes.c_uint32(self._vi)
        selector_string_ctype = ctypes.create_string_buffer(selector_string.encode(self._encoding))
        actual_result_names_size_ctype = ctypes.c_int32(0)
        default_result_exists_ctype = ctypes.c_int32()

        # call library function to get the size of array
        error_code = self._library.RFmxBT_GetAllNamedResultNames(
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
        error_code = self._library.RFmxBT_GetAllNamedResultNames(
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
        error_code = self._library.RFmxBT_AnalyzeIQ1Waveform(
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
