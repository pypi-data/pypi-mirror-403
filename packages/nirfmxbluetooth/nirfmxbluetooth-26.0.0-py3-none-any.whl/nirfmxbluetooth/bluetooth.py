"""Defines a root class which is used to identify and control Bluetooth signal configuration."""

import functools
import math

import nirfmxbluetooth.acp as acp
import nirfmxbluetooth.attributes as attributes
import nirfmxbluetooth.enums as enums
import nirfmxbluetooth.errors as errors
import nirfmxbluetooth.frequency_range as frequency_range
import nirfmxbluetooth.internal._helper as _helper
import nirfmxbluetooth.modacc as modacc
import nirfmxbluetooth.modspectrum as modspectrum
import nirfmxbluetooth.powerramp as powerramp
import nirfmxbluetooth.twenty_db_bandwidth as twenty_db_bandwidth
import nirfmxbluetooth.txp as txp
import nirfmxinstr
from nirfmxbluetooth.internal._helper import SignalConfiguration
from nirfmxbluetooth.internal._library_interpreter import LibraryInterpreter


class _BluetoothSignalConfiguration:
    """Contains static methods to create and delete Bluetooth signal."""

    @staticmethod
    def get_bluetooth_signal_configuration(instr_session, signal_name="", cloning=False):
        updated_signal_name = signal_name
        if signal_name:
            updated_signal_name = _helper.validate_and_remove_signal_qualifier(
                signal_name, "signal_name"
            )
            _helper.validate_signal_not_empty(updated_signal_name, "signal_name")
        return _BluetoothSignalConfiguration.init(instr_session, updated_signal_name, cloning)  # type: ignore

    @staticmethod
    def init(instr_session, signal_name, cloning):
        with instr_session._signal_lock:
            if signal_name.lower() == Bluetooth._default_signal_name_user_visible.lower():
                signal_name = Bluetooth._default_signal_name

            existing_signal = instr_session._signal_manager.find_signal_configuration(
                Bluetooth._signal_configuration_type, signal_name
            )
            if existing_signal is None:
                signal_configuration = Bluetooth(instr_session, signal_name, cloning)  # type: ignore
                instr_session._signal_manager.add_signal_configuration(signal_configuration)
            else:
                signal_configuration = existing_signal
                # Checking if signal exists in C layer
                if signal_configuration._interpreter.check_if_current_signal_exists() is False:
                    if not signal_configuration.signal_configuration_name.lower():
                        instr_session._interpreter.create_default_signal_configuration(
                            Bluetooth._default_signal_name_user_visible,
                            int(math.log(nirfmxinstr.Personalities.BT.value, 2.0)) + 1,
                        )
                    else:
                        signal_configuration._interpreter.create_signal_configuration(signal_name)

            return signal_configuration

    @staticmethod
    def remove_signal_configuration(instr_session, signal_configuration):
        with instr_session._signal_lock:
            instr_session._signal_manager.remove_signal_configuration(signal_configuration)


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        signal = xs[0]  # parameter 0 is 'self' which is the signal object
        if signal.is_disposed:
            raise Exception("Cannot access a disposed Bluetooth signal configuration")
        return f(*xs, **kws)

    return aux


class _BluetoothBase(SignalConfiguration):
    """Defines a base class for Bluetooth."""

    _default_signal_name = ""
    _default_signal_name_user_visible = "default@BT"
    _signal_configuration_type = "<'nirfmxbluetooth.bluetooth.Bluetooth'>"

    def __init__(self, session, signal_name="", cloning=False):
        self.is_disposed = False
        self._rfmxinstrsession = session
        self._rfmxinstrsession_interpreter = session._interpreter
        self.signal_configuration_name = signal_name
        self.signal_configuration_type = type(self)  # type: ignore
        self._signal_configuration_mode = "Signal"
        if session._is_remote_session:
            import nirfmxbluetooth.internal._grpc_stub_interpreter as _grpc_stub_interpreter

            interpreter = _grpc_stub_interpreter.GrpcStubInterpreter(session._grpc_options, session, self)  # type: ignore
        else:
            interpreter = LibraryInterpreter("windows-1251", session, self)  # type: ignore

        self._interpreter = interpreter
        self._interpreter.set_session_handle(self._rfmxinstrsession_interpreter._vi)  # type: ignore
        self._session_function_lock = _helper.SessionFunctionLock()

        # Measurements object
        self.txp = txp.Txp(self)  # type: ignore
        self.modacc = modacc.ModAcc(self)  # type: ignore
        self.twenty_db_bandwidth = twenty_db_bandwidth.TwentydBBandwidth(self)  # type: ignore
        self.frequency_range = frequency_range.FrequencyRange(self)  # type: ignore
        self.acp = acp.Acp(self)  # type: ignore
        self.powerramp = powerramp.PowerRamp(self)  # type: ignore
        self.modspectrum = modspectrum.ModSpectrum(self)  # type: ignore

        if not signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._default_signal_name_user_visible
                )
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.BT.value):
                self._rfmxinstrsession_interpreter.create_default_signal_configuration(
                    self._default_signal_name_user_visible,
                    int(math.log(nirfmxinstr.Personalities.BT.value, 2.0)) + 1,
                )
        elif signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(signal_name)
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.BT.value):
                self._interpreter.create_signal_configuration(signal_name)  # type: ignore

    def __enter__(self):
        """Enters the context of the Bluetooth signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the Bluetooth signal configuration."""
        self.dispose()  # type: ignore
        pass

    def dispose(self):
        r"""Deletes the signal configuration if it is not the default signal configuration
        and clears any trace of the current signal configuration, if any.

        .. note::
            You can call this function safely more than once, even if the signal is already deleted.
        """
        if not self.is_disposed:
            if self.signal_configuration_name == self._default_signal_name:
                self.is_disposed = True
                return
            else:
                _ = self._delete_signal_configuration(True)  # type: ignore
                self.is_disposed = True

    @_raise_if_disposed
    def delete_signal_configuration(self):
        r"""Deletes the current instance of a signal.

        Returns:
            error_code:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        error_code = self._delete_signal_configuration(False)  # type: ignore
        return error_code

    def _delete_signal_configuration(self, ignore_driver_error):
        error_code = 0
        try:
            if not self.is_disposed:
                self._session_function_lock.enter_write_lock()
                error_code = self._interpreter.delete_signal_configuration(ignore_driver_error)  # type: ignore
                _BluetoothSignalConfiguration.remove_signal_configuration(self._rfmxinstrsession, self)  # type: ignore
                self.is_disposed = True
        finally:
            self._session_function_lock.exit_write_lock()

        return error_code

    @_raise_if_disposed
    def get_warning(self):
        r"""Retrieves and then clears the warning information for the session.

        Returns:
            Tuple (warning_code, warning_message):

            warning_code (int):
                Contains the latest warning code.

            warning_message (string):
                Contains the latest warning description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            warning_code, warning_message = self._interpreter.get_error()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return warning_code, warning_message

    @_raise_if_disposed
    def get_error_string(self, error_code):
        r"""Gets the description of a driver error code.

        Args:
            error_code (int):
                Specifies an error or warning code.

        Returns:
            string:
                Contains the error description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_message = self._interpreter.get_error_string(error_code)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_message

    @_raise_if_disposed
    def reset_attribute(self, selector_string, attribute_id):
        r"""Resets the attribute to its default value.

        Args:
            selector_string (string):
                Specifies the selector string for the property being reset.

            attribute_id (PropertyId):
                Specifies an attribute identifier.

        Returns:
            int:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attribute_id = (
                attribute_id.value if type(attribute_id) is attributes.AttributeID else attribute_id
            )
            error_code = self._interpreter.reset_attribute(  # type: ignore
                updated_selector_string, attribute_id
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_selected_ports(self, selector_string):
        r"""Gets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_selected_ports(self, selector_string, value):
        r"""Sets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_center_frequency(self, selector_string):
        r"""Gets the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
        signal analyzer tunes to this frequency.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is hardware dependent. The default value for the devices PXIe-5645/5820 is 0 Hz. The default
        value for devices PXIe-5644/5646/5840/5663/5663E/5665/5668R is 2.402 GHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
                signal analyzer tunes to this frequency.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_center_frequency(self, selector_string, value):
        r"""Sets the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
        signal analyzer tunes to this frequency.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is hardware dependent. The default value for the devices PXIe-5645/5820 is 0 Hz. The default
        value for devices PXIe-5644/5646/5840/5663/5663E/5665/5668R is 2.402 GHz.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
                signal analyzer tunes to this frequency.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level(self, selector_string):
        r"""Gets the reference level that represents the maximum expected power of the RF input signal. This value is
        expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the reference level that represents the maximum expected power of the RF input signal. This value is
                expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level(self, selector_string, value):
        r"""Sets the reference level that represents the maximum expected power of the RF input signal. This value is
        expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the reference level that represents the maximum expected power of the RF input signal. This value is
                expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_external_attenuation(self, selector_string):
        r"""Gets the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        For more information about attenuation, refer to the *Attenuation and Signal Levels* topic for your device in
        the *NI RF Vector Signal Analyzers Help*.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_external_attenuation(self, selector_string, value):
        r"""Sets the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        For more information about attenuation, refer to the *Attenuation and Signal Levels* topic for your device in
        the *NI RF Vector Signal Analyzers Help*.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level_headroom(self, selector_string):
        r"""Gets the margin RFmx adds to the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
        margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668R, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
                margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level_headroom(self, selector_string, value):
        r"""Sets the margin RFmx adds to the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
        margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668R, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
                margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_type(self, selector_string):
        r"""Gets the type of trigger to be used for signal acquisition.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **IQ Power Edge**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No reference trigger is used for signal acquisition.                                                                     |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | A digital-edge trigger is used for signal acquisition. The source of the digital edge is specified using the Digital     |
        |                   | Edge Source attribute.                                                                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | An I/Q power-edge trigger is used for signal acquisition, which is configured using the IQ Power Edge Slope attribute.   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | A software trigger is used for signal acquisition.                                                                       |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerType):
                Specifies the type of trigger to be used for signal acquisition.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value
            )
            attr_val = enums.TriggerType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_type(self, selector_string, value):
        r"""Sets the type of trigger to be used for signal acquisition.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **IQ Power Edge**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No reference trigger is used for signal acquisition.                                                                     |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | A digital-edge trigger is used for signal acquisition. The source of the digital edge is specified using the Digital     |
        |                   | Edge Source attribute.                                                                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | An I/Q power-edge trigger is used for signal acquisition, which is configured using the IQ Power Edge Slope attribute.   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | A software trigger is used for signal acquisition.                                                                       |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerType, int):
                Specifies the type of trigger to be used for signal acquisition.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_source(self, selector_string):
        r"""Gets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_source(self, selector_string, value):
        r"""Sets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_edge(self, selector_string):
        r"""Gets the active edge for the trigger. This attribute is valid only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DigitalEdgeTriggerEdge):
                Specifies the active edge for the trigger. This attribute is valid only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value
            )
            attr_val = enums.DigitalEdgeTriggerEdge(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_edge(self, selector_string, value):
        r"""Sets the active edge for the trigger. This attribute is valid only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DigitalEdgeTriggerEdge, int):
                Specifies the active edge for the trigger. This attribute is valid only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DigitalEdgeTriggerEdge else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_source(self, selector_string):
        r"""Gets the channel from which the device monitors the trigger. This attribute is valid only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the channel from which the device monitors the trigger. This attribute is valid only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_source(self, selector_string, value):
        r"""Sets the channel from which the device monitors the trigger. This attribute is valid only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the channel from which the device monitors the trigger. This attribute is valid only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level(self, selector_string):
        r"""Gets the power level at which the device triggers. The device asserts the trigger when the signal exceeds the
        level specified by the value of this parameter, taking into consideration the specified slope.

        This value is expressed in dB when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in
        dBm when you set the IQ Power Edge Level Type attribute to **Absolute**. This attribute is valid only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power level at which the device triggers. The device asserts the trigger when the signal exceeds the
                level specified by the value of this parameter, taking into consideration the specified slope.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level(self, selector_string, value):
        r"""Sets the power level at which the device triggers. The device asserts the trigger when the signal exceeds the
        level specified by the value of this parameter, taking into consideration the specified slope.

        This value is expressed in dB when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in
        dBm when you set the IQ Power Edge Level Type attribute to **Absolute**. This attribute is valid only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power level at which the device triggers. The device asserts the trigger when the signal exceeds the
                level specified by the value of this parameter, taking into consideration the specified slope.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level_type(self, selector_string):
        r"""Gets the reference for the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL`
        attribute. The IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerLevelType):
                Specifies the reference for the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL`
                attribute. The IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
            )
            attr_val = enums.IQPowerEdgeTriggerLevelType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level_type(self, selector_string, value):
        r"""Sets the reference for the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL`
        attribute. The IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerLevelType, int):
                Specifies the reference for the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL`
                attribute. The IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerLevelType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_slope(self, selector_string):
        r"""Gets whether the device asserts the trigger when the signal power is rising or when it is falling. The device
        asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
        used only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power
        Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerSlope):
                Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
                used only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power
                Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value
            )
            attr_val = enums.IQPowerEdgeTriggerSlope(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_slope(self, selector_string, value):
        r"""Sets whether the device asserts the trigger when the signal power is rising or when it is falling. The device
        asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
        used only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power
        Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerSlope, int):
                Specifies whether the device asserts the trigger when the signal power is rising or when it is falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
                used only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power
                Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerSlope else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_delay(self, selector_string):
        r"""Gets the trigger delay time. This value is expressed in seconds.

        If the delay is negative, the measurement acquires pretrigger samples. If the delay is positive, the
        measurement acquires posttrigger samples.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the trigger delay time. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_delay(self, selector_string, value):
        r"""Sets the trigger delay time. This value is expressed in seconds.

        If the delay is negative, the measurement acquires pretrigger samples. If the delay is positive, the
        measurement acquires posttrigger samples.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the trigger delay time. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_mode(self, selector_string):
        r"""Gets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                 |
        +==============+=============================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
        +--------------+---------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
        +--------------+---------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerMinimumQuietTimeMode):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
            )
            attr_val = enums.TriggerMinimumQuietTimeMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_mode(self, selector_string, value):
        r"""Sets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+---------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                 |
        +==============+=============================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time attribute. |
        +--------------+---------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                        |
        +--------------+---------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerMinimumQuietTimeMode, int):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerMinimumQuietTimeMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_duration(self, selector_string):
        r"""Gets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds.

        If you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to
        **Rising Slope**, the signal is quiet below the trigger level. If you set the IQ Power Edge Slope attribute to
        **Falling Slope**, the signal is quiet above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_duration(self, selector_string, value):
        r"""Sets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds.

        If you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to
        **Rising Slope**, the signal is quiet below the trigger level. If you set the IQ Power Edge Slope attribute to
        **Falling Slope**, the signal is quiet above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_packet_type(self, selector_string):
        r"""Gets the type of the Bluetooth packet to be measured.

        In this document, packet type is sometimes referred to by the Bluetooth physical layer (PHY) it belongs to.
        Supported Bluetooth physical layers are basic rate (BR), enhanced data rate (EDR), low energy (LE) and low energy -
        channel sounding (LE-CS).
        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **DH1**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | DH1 (0)      | Specifies that the packet type is DH1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.2, Part B,      |
        |              | Volume 2 of the Bluetooth Core Specification v6.0 for more information about this packet.                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DH3 (1)      | Specifies that the packet type is DH3. The packet belongs to BR PHY. Refer to section 6.5.4.4, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DH5 (2)      | Specifies that the packet type is DH5. The packet belongs to BR PHY. Refer to section 6.5.4.6, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DM1 (3)      | Specifies that the packet type is DM1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.1, Part B,      |
        |              | Volume 2 of the Bluetooth Core Specification v6.0 for more information about this packet.                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DM3 (4)      | Specifies that the packet type is DM3. The packet belongs to BR PHY. Refer to section 6.5.4.3, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DM5 (5)      | Specifies that the packet type is DM5. The packet belongs to BR PHY. Refer to section 6.5.4.5, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-DH1 (6)    | Specifies that the packet type is 2-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.8, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-DH3 (7)    | Specifies that the packet type is 2-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.9, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-DH5 (8)    | Specifies that the packet type is 2-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.10, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-DH1 (9)    | Specifies that the packet type is 3-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.11, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-DH3 (10)   | Specifies that the packet type is 3-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.12, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-DH5 (11)   | Specifies that the packet type is 3-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.13, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-EV3 (12)   | Specifies that the packet type is 2-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.4, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-EV5 (13)   | Specifies that the packet type is 2-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.5, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-EV3 (14)   | Specifies that the packet type is 3-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.6, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-EV5 (15)   | Specifies that the packet type is 3-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.7, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | LE (16)      | Specifies that the packet type is LE. The packet belongs to LE PHY. Refer to sections 2.1 and 2.2, Part B, Volume 6 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | LE-CS (17)   | Specifies that the packet type is LE-CS. The packet belongs to LE-CS PHY. Refer to Section 2, Part H, Volume 6 of the    |
        |              | Bluetooth Specification v6.0 for more information about this packet                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | LE-HDT (18)  | Specifies that the packet type is LE-HDT. The packet belongs to LE-HDT PHY.                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PacketType):
                Specifies the type of the Bluetooth packet to be measured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PACKET_TYPE.value
            )
            attr_val = enums.PacketType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_packet_type(self, selector_string, value):
        r"""Sets the type of the Bluetooth packet to be measured.

        In this document, packet type is sometimes referred to by the Bluetooth physical layer (PHY) it belongs to.
        Supported Bluetooth physical layers are basic rate (BR), enhanced data rate (EDR), low energy (LE) and low energy -
        channel sounding (LE-CS).
        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **DH1**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | DH1 (0)      | Specifies that the packet type is DH1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.2, Part B,      |
        |              | Volume 2 of the Bluetooth Core Specification v6.0 for more information about this packet.                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DH3 (1)      | Specifies that the packet type is DH3. The packet belongs to BR PHY. Refer to section 6.5.4.4, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DH5 (2)      | Specifies that the packet type is DH5. The packet belongs to BR PHY. Refer to section 6.5.4.6, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DM1 (3)      | Specifies that the packet type is DM1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.1, Part B,      |
        |              | Volume 2 of the Bluetooth Core Specification v6.0 for more information about this packet.                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DM3 (4)      | Specifies that the packet type is DM3. The packet belongs to BR PHY. Refer to section 6.5.4.3, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | DM5 (5)      | Specifies that the packet type is DM5. The packet belongs to BR PHY. Refer to section 6.5.4.5, Part B, Volume 2 of the   |
        |              | Bluetooth Core Specification v6.0 for more information about this packet.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-DH1 (6)    | Specifies that the packet type is 2-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.8, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-DH3 (7)    | Specifies that the packet type is 2-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.9, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-DH5 (8)    | Specifies that the packet type is 2-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.10, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-DH1 (9)    | Specifies that the packet type is 3-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.11, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-DH3 (10)   | Specifies that the packet type is 3-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.12, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-DH5 (11)   | Specifies that the packet type is 3-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.13, Part B, Volume 2 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-EV3 (12)   | Specifies that the packet type is 2-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.4, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 2-EV5 (13)   | Specifies that the packet type is 2-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.5, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-EV3 (14)   | Specifies that the packet type is 3-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.6, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | 3-EV5 (15)   | Specifies that the packet type is 3-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.7, Part B, Volume 2 of    |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | LE (16)      | Specifies that the packet type is LE. The packet belongs to LE PHY. Refer to sections 2.1 and 2.2, Part B, Volume 6 of   |
        |              | the Bluetooth Core Specification v6.0 for more information about this packet.                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | LE-CS (17)   | Specifies that the packet type is LE-CS. The packet belongs to LE-CS PHY. Refer to Section 2, Part H, Volume 6 of the    |
        |              | Bluetooth Specification v6.0 for more information about this packet                                                      |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | LE-HDT (18)  | Specifies that the packet type is LE-HDT. The packet belongs to LE-HDT PHY.                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PacketType, int):
                Specifies the type of the Bluetooth packet to be measured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.PacketType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PACKET_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_data_rate(self, selector_string):
        r"""Gets the data rate of the LE, LE-CS or LE-HDT packet transmitted by the device under test (DUT). This value is
        expressed in bps. This attribute is applicable only to LE, LE-CS or LE-HDT packet type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **1M**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the data rate of the LE, LE-CS or LE-HDT packet transmitted by the device under test (DUT). This value is
                expressed in bps. This attribute is applicable only to LE, LE-CS or LE-HDT packet type.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DATA_RATE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_data_rate(self, selector_string, value):
        r"""Sets the data rate of the LE, LE-CS or LE-HDT packet transmitted by the device under test (DUT). This value is
        expressed in bps. This attribute is applicable only to LE, LE-CS or LE-HDT packet type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **1M**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the data rate of the LE, LE-CS or LE-HDT packet transmitted by the device under test (DUT). This value is
                expressed in bps. This attribute is applicable only to LE, LE-CS or LE-HDT packet type.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DATA_RATE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bandwidth_bit_period_product(self, selector_string):
        r"""Gets the bandwidth bit period product of GFSK modulation for LE-CS packet type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the bandwidth bit period product of GFSK modulation for LE-CS packet type.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.BANDWIDTH_BIT_PERIOD_PRODUCT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bandwidth_bit_period_product(self, selector_string, value):
        r"""Sets the bandwidth bit period product of GFSK modulation for LE-CS packet type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the bandwidth bit period product of GFSK modulation for LE-CS packet type.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.BANDWIDTH_BIT_PERIOD_PRODUCT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_bd_address_lap(self, selector_string):
        r"""Gets the 24-bit lower address part (LAP) of the bluetooth device address (BD_ADDR).

        This value is used to generate the sync word if you set the burst synchronization type attribute in TXP, ACP,
        or ModAcc measurements to **Sync Word**. This attribute is applicable only to BR and EDR packet types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the 24-bit lower address part (LAP) of the bluetooth device address (BD_ADDR).

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.BD_ADDRESS_LAP.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_bd_address_lap(self, selector_string, value):
        r"""Sets the 24-bit lower address part (LAP) of the bluetooth device address (BD_ADDR).

        This value is used to generate the sync word if you set the burst synchronization type attribute in TXP, ACP,
        or ModAcc measurements to **Sync Word**. This attribute is applicable only to BR and EDR packet types.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the 24-bit lower address part (LAP) of the bluetooth device address (BD_ADDR).

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.BD_ADDRESS_LAP.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_access_address(self, selector_string):
        r"""Gets the 32-bit LE access address.

        This value is used to synchronize to the start of the packet if you set the burst synchronization type
        attribute in TXP, ACP, or ModAcc measurements to **Sync Word** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE** or **LE-CS**.
        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0x71764129 as specified by the bluetooth standard.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the 32-bit LE access address.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.ACCESS_ADDRESS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_access_address(self, selector_string, value):
        r"""Sets the 32-bit LE access address.

        This value is used to synchronize to the start of the packet if you set the burst synchronization type
        attribute in TXP, ACP, or ModAcc measurements to **Sync Word** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE** or **LE-CS**.
        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0x71764129 as specified by the bluetooth standard.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the 32-bit LE access address.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.ACCESS_ADDRESS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_payload_bit_pattern(self, selector_string):
        r"""Gets the bit pattern present in the payload of the packet. This value is used to determine the set of ModAcc
        measurements to be performed.

        The following table shows the measurements applicable for different Payload Bit Pattern:

        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | Bluetooth PHY | Data Rate | Standard                                                                           | 11110000                                                                                                     | 10101010                   |
        +===============+===========+====================================================================================+==============================================================================================================+============================+
        | BR            | NA        | Error                                                                              | df1                                                                                                          | df2 and BR frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | EDR           | NA        | DEVM (The measurement considers PN9 as payload pattern)                            | Error                                                                                                        | Error                      |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 1 Mbps    | Error                                                                              | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 2 Mbps    | Error                                                                              | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 125 kbps  | df1 and LE frequency error (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 500 kbps  | df2 and LE frequency error (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE-CS         | 1 Mbps    | Error                                                                              | df1                                                                                                          | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE-CS         | 2 Mbps    | Error                                                                              | df1                                                                                                          | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Standard Defined**.

        +----------------------+-------------------------------------------------------------+
        | Name (Value)         | Description                                                 |
        +======================+=============================================================+
        | Standard Defined (0) | Specifies that the payload bit pattern is Standard Defined. |
        +----------------------+-------------------------------------------------------------+
        | 11110000 (1)         | Specifies that the payload bit pattern is 11110000.         |
        +----------------------+-------------------------------------------------------------+
        | 10101010 (2)         | Specifies that the payload bit pattern is 10101010.         |
        +----------------------+-------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PayloadBitPattern):
                Specifies the bit pattern present in the payload of the packet. This value is used to determine the set of ModAcc
                measurements to be performed.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PAYLOAD_BIT_PATTERN.value
            )
            attr_val = enums.PayloadBitPattern(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_payload_bit_pattern(self, selector_string, value):
        r"""Sets the bit pattern present in the payload of the packet. This value is used to determine the set of ModAcc
        measurements to be performed.

        The following table shows the measurements applicable for different Payload Bit Pattern:

        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | Bluetooth PHY | Data Rate | Standard                                                                           | 11110000                                                                                                     | 10101010                   |
        +===============+===========+====================================================================================+==============================================================================================================+============================+
        | BR            | NA        | Error                                                                              | df1                                                                                                          | df2 and BR frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | EDR           | NA        | DEVM (The measurement considers PN9 as payload pattern)                            | Error                                                                                                        | Error                      |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 1 Mbps    | Error                                                                              | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 2 Mbps    | Error                                                                              | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 125 kbps  | df1 and LE frequency error (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE            | 500 kbps  | df2 and LE frequency error (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE-CS         | 1 Mbps    | Error                                                                              | df1                                                                                                          | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
        | LE-CS         | 2 Mbps    | Error                                                                              | df1                                                                                                          | df2 and LE frequency error |
        +---------------+-----------+------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Standard Defined**.

        +----------------------+-------------------------------------------------------------+
        | Name (Value)         | Description                                                 |
        +======================+=============================================================+
        | Standard Defined (0) | Specifies that the payload bit pattern is Standard Defined. |
        +----------------------+-------------------------------------------------------------+
        | 11110000 (1)         | Specifies that the payload bit pattern is 11110000.         |
        +----------------------+-------------------------------------------------------------+
        | 10101010 (2)         | Specifies that the payload bit pattern is 10101010.         |
        +----------------------+-------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PayloadBitPattern, int):
                Specifies the bit pattern present in the payload of the packet. This value is used to determine the set of ModAcc
                measurements to be performed.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.PayloadBitPattern else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PAYLOAD_BIT_PATTERN.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_payload_length_mode(self, selector_string):
        r"""Gets the payload length mode of the signal to be measured. The payload length mode and
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH` attributes decide the length of the payload to be
        used for measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | Enables the value specified by the Payload Length attribute. The acquisition and measurement durations will be decided   |
        |              | based on this value.                                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | Enables the standard defined maximum payload length for BR, EDR, LE and LE-CS packet, and the maximum payload zone       |
        |              | length for LE-HDT packet. If this attribute is set to Auto, the maximum standard defined payload length or payload zone  |
        |              | length for the selected Packet Type is chosen. The maximum payload length a device under test (DUT) can generate varies  |
        |              | from 37 to 255 bytes for LE packet, and the maximum payload zone length varies from 514 to 33020 bytes for LE-HDT        |
        |              | packet. When you set the payload length mode to Auto, RFmx chooses 37 bytes for LE packet and 514 bytes for LE-HDT       |
        |              | packet.                                                                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.PayloadLengthMode):
                Specifies the payload length mode of the signal to be measured. The payload length mode and
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH` attributes decide the length of the payload to be
                used for measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PAYLOAD_LENGTH_MODE.value
            )
            attr_val = enums.PayloadLengthMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_payload_length_mode(self, selector_string, value):
        r"""Sets the payload length mode of the signal to be measured. The payload length mode and
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH` attributes decide the length of the payload to be
        used for measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | Enables the value specified by the Payload Length attribute. The acquisition and measurement durations will be decided   |
        |              | based on this value.                                                                                                     |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | Enables the standard defined maximum payload length for BR, EDR, LE and LE-CS packet, and the maximum payload zone       |
        |              | length for LE-HDT packet. If this attribute is set to Auto, the maximum standard defined payload length or payload zone  |
        |              | length for the selected Packet Type is chosen. The maximum payload length a device under test (DUT) can generate varies  |
        |              | from 37 to 255 bytes for LE packet, and the maximum payload zone length varies from 514 to 33020 bytes for LE-HDT        |
        |              | packet. When you set the payload length mode to Auto, RFmx chooses 37 bytes for LE packet and 514 bytes for LE-HDT       |
        |              | packet.                                                                                                                  |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.PayloadLengthMode, int):
                Specifies the payload length mode of the signal to be measured. The payload length mode and
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH` attributes decide the length of the payload to be
                used for measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.PayloadLengthMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PAYLOAD_LENGTH_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_payload_length(self, selector_string):
        r"""Gets the payload length of BR, EDR, LE and LE-CS packet, and the payload zone length of LE-HDT packet, in bytes.
        This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH_MODE` attribute to **Manual**. This attribute returns
        the payload length or payload zone length used for measurement if you set the Payload Length Mode attribute to
        **Auto**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the payload length of BR, EDR, LE and LE-CS packet, and the payload zone length of LE-HDT packet, in bytes.
                This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH_MODE` attribute to **Manual**. This attribute returns
                the payload length or payload zone length used for measurement if you set the Payload Length Mode attribute to
                **Auto**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PAYLOAD_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_payload_length(self, selector_string, value):
        r"""Sets the payload length of BR, EDR, LE and LE-CS packet, and the payload zone length of LE-HDT packet, in bytes.
        This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH_MODE` attribute to **Manual**. This attribute returns
        the payload length or payload zone length used for measurement if you set the Payload Length Mode attribute to
        **Auto**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the payload length of BR, EDR, LE and LE-CS packet, and the payload zone length of LE-HDT packet, in bytes.
                This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_LENGTH_MODE` attribute to **Manual**. This attribute returns
                the payload length or payload zone length used for measurement if you set the Payload Length Mode attribute to
                **Auto**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.PAYLOAD_LENGTH.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_direction_finding_mode(self, selector_string):
        r"""Gets the mode of direction finding.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +------------------------+----------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                            |
        +========================+========================================================================================+
        | Disabled (0)           | Specifies that the LE packet does not have fields required for direction finding.      |
        +------------------------+----------------------------------------------------------------------------------------+
        | Angle of Arrival (1)   | Specifies that the LE packets uses the Angle of Arrival method of direction finding.   |
        +------------------------+----------------------------------------------------------------------------------------+
        | Angle of Departure (2) | Specifies that the LE packets uses the Angle of Departure method of direction finding. |
        +------------------------+----------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DirectionFindingMode):
                Specifies the mode of direction finding.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIRECTION_FINDING_MODE.value
            )
            attr_val = enums.DirectionFindingMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_direction_finding_mode(self, selector_string, value):
        r"""Sets the mode of direction finding.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +------------------------+----------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                            |
        +========================+========================================================================================+
        | Disabled (0)           | Specifies that the LE packet does not have fields required for direction finding.      |
        +------------------------+----------------------------------------------------------------------------------------+
        | Angle of Arrival (1)   | Specifies that the LE packets uses the Angle of Arrival method of direction finding.   |
        +------------------------+----------------------------------------------------------------------------------------+
        | Angle of Departure (2) | Specifies that the LE packets uses the Angle of Departure method of direction finding. |
        +------------------------+----------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DirectionFindingMode, int):
                Specifies the mode of direction finding.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DirectionFindingMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIRECTION_FINDING_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_cte_length(self, selector_string):
        r"""Gets the length of the constant tone extension (CTE) field in the generated signal. This value is expressed in
        seconds. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to either **Angle of Arrival** or
        **Angle of Departure**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 160 microseconds.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the length of the constant tone extension (CTE) field in the generated signal. This value is expressed in
                seconds. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to either **Angle of Arrival** or
                **Angle of Departure**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CTE_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_cte_length(self, selector_string, value):
        r"""Sets the length of the constant tone extension (CTE) field in the generated signal. This value is expressed in
        seconds. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to either **Angle of Arrival** or
        **Angle of Departure**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 160 microseconds.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the length of the constant tone extension (CTE) field in the generated signal. This value is expressed in
                seconds. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to either **Angle of Arrival** or
                **Angle of Departure**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CTE_LENGTH.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_cte_slot_duration(self, selector_string):
        r"""Gets the length of the switching slots and transmit slots in the constant tone extension field in the generated
        signal. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Arrival** or **Angle
        of Departure**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1u.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the length of the switching slots and transmit slots in the constant tone extension field in the generated
                signal. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Arrival** or **Angle
                of Departure**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CTE_SLOT_DURATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_cte_slot_duration(self, selector_string, value):
        r"""Sets the length of the switching slots and transmit slots in the constant tone extension field in the generated
        signal. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Arrival** or **Angle
        of Departure**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1u.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the length of the switching slots and transmit slots in the constant tone extension field in the generated
                signal. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Arrival** or **Angle
                of Departure**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CTE_SLOT_DURATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_cte_number_of_transmit_slots(self, selector_string):
        r"""Gets the number of transmit slots in the constant time extension portion of the generated LE packet. This attribute
        is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute
        to **Angle of Arrival** or **Angle of Departure**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the number of transmit slots in the constant time extension portion of the generated LE packet. This attribute
                is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute
                to **Angle of Arrival** or **Angle of Departure**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.CTE_NUMBER_OF_TRANSMIT_SLOTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_channel_sounding_packet_format(self, selector_string):
        r"""Gets the format of the Channel Sounding packet depending on the position and presence of SYNC and CS Tone fields.
        This attribute is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE`
        attribute to **LE-CS**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **SYNC**.

        +-------------------------+-----------------------------------------------------------------------------+
        | Name (Value)            | Description                                                                 |
        +=========================+=============================================================================+
        | SYNC (0)                | Specifies that the LE-CS packet contains only SYNC portion.                 |
        +-------------------------+-----------------------------------------------------------------------------+
        | CS Tone (1)             | Specifies that the LE-CS packet contains only CS Tone.                      |
        +-------------------------+-----------------------------------------------------------------------------+
        | CS Tone after SYNC (2)  | Specifies that the CS Tone portion is at the end of the LE-CS packet.       |
        +-------------------------+-----------------------------------------------------------------------------+
        | CS Tone before SYNC (3) | Specifies that the CS Tone portion is at the beginning of the LE-CS packet. |
        +-------------------------+-----------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChannelSoundingPacketFormat):
                Specifies the format of the Channel Sounding packet depending on the position and presence of SYNC and CS Tone fields.
                This attribute is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE`
                attribute to **LE-CS**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT.value
            )
            attr_val = enums.ChannelSoundingPacketFormat(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_sounding_packet_format(self, selector_string, value):
        r"""Sets the format of the Channel Sounding packet depending on the position and presence of SYNC and CS Tone fields.
        This attribute is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE`
        attribute to **LE-CS**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **SYNC**.

        +-------------------------+-----------------------------------------------------------------------------+
        | Name (Value)            | Description                                                                 |
        +=========================+=============================================================================+
        | SYNC (0)                | Specifies that the LE-CS packet contains only SYNC portion.                 |
        +-------------------------+-----------------------------------------------------------------------------+
        | CS Tone (1)             | Specifies that the LE-CS packet contains only CS Tone.                      |
        +-------------------------+-----------------------------------------------------------------------------+
        | CS Tone after SYNC (2)  | Specifies that the CS Tone portion is at the end of the LE-CS packet.       |
        +-------------------------+-----------------------------------------------------------------------------+
        | CS Tone before SYNC (3) | Specifies that the CS Tone portion is at the beginning of the LE-CS packet. |
        +-------------------------+-----------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChannelSoundingPacketFormat, int):
                Specifies the format of the Channel Sounding packet depending on the position and presence of SYNC and CS Tone fields.
                This attribute is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE`
                attribute to **LE-CS**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.ChannelSoundingPacketFormat else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_sounding_sync_sequence(self, selector_string):
        r"""Gets the type of sequence present in the SYNC portion after trailer bits. This attribute is applicable only when
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **CS Tone**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **None**.

        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                            |
        +==============================+========================================================================================================+
        | None (0)                     | Specifies that there is no optional sequence at the end of the SYNC portion of the LE-CS packet.       |
        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Sounding Sequence 32-bit (1) | Specifies that there is a 32-bit sounding sequence at the end of the SYNC portion of the LE-CS packet. |
        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Sounding Sequence 96-bit (2) | Specifies that there is a 96-bit sounding sequence at the end of the SYNC portion of the LE-CS packet. |
        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Payload Pattern (3)          | Specifies that the payload bit pattern is present at the end of the SYNC portion of the LE-CS packet.  |
        +------------------------------+--------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChannelSoundingSyncSequence):
                Specifies the type of sequence present in the SYNC portion after trailer bits. This attribute is applicable only when
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **CS Tone**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_SOUNDING_SYNC_SEQUENCE.value
            )
            attr_val = enums.ChannelSoundingSyncSequence(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_sounding_sync_sequence(self, selector_string, value):
        r"""Sets the type of sequence present in the SYNC portion after trailer bits. This attribute is applicable only when
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **CS Tone**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **None**.

        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Name (Value)                 | Description                                                                                            |
        +==============================+========================================================================================================+
        | None (0)                     | Specifies that there is no optional sequence at the end of the SYNC portion of the LE-CS packet.       |
        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Sounding Sequence 32-bit (1) | Specifies that there is a 32-bit sounding sequence at the end of the SYNC portion of the LE-CS packet. |
        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Sounding Sequence 96-bit (2) | Specifies that there is a 96-bit sounding sequence at the end of the SYNC portion of the LE-CS packet. |
        +------------------------------+--------------------------------------------------------------------------------------------------------+
        | Payload Pattern (3)          | Specifies that the payload bit pattern is present at the end of the SYNC portion of the LE-CS packet.  |
        +------------------------------+--------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChannelSoundingSyncSequence, int):
                Specifies the type of sequence present in the SYNC portion after trailer bits. This attribute is applicable only when
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **CS Tone**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.ChannelSoundingSyncSequence else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_SYNC_SEQUENCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_sounding_phase_measurement_period(self, selector_string):
        r"""Gets the Channel Sounding Phase Measurement Period for the LE-CS packet. This attribute is applicable only when
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **10 us**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the Channel Sounding Phase Measurement Period for the LE-CS packet. This attribute is applicable only when
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_PHASE_MEASUREMENT_PERIOD.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_sounding_phase_measurement_period(self, selector_string, value):
        r"""Sets the Channel Sounding Phase Measurement Period for the LE-CS packet. This attribute is applicable only when
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **10 us**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the Channel Sounding Phase Measurement Period for the LE-CS packet. This attribute is applicable only when
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_PHASE_MEASUREMENT_PERIOD.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_sounding_tone_extension_slot(self, selector_string):
        r"""Gets whether the tone extension slot transmission is enabled after CS Tone. This attribute is applicable only when
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +--------------+------------------------------------------------------------------------+
        | Name (Value) | Description                                                            |
        +==============+========================================================================+
        | Disabled (0) | Specifies that there is no transmission in the CS Tone extension slot. |
        +--------------+------------------------------------------------------------------------+
        | Enabled (1)  | Specifies that there is transmission in the CS Tone extension slot.    |
        +--------------+------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ChannelSoundingToneExtensionSlot):
                Specifies whether the tone extension slot transmission is enabled after CS Tone. This attribute is applicable only when
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_TONE_EXTENSION_SLOT.value,
            )
            attr_val = enums.ChannelSoundingToneExtensionSlot(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_sounding_tone_extension_slot(self, selector_string, value):
        r"""Sets whether the tone extension slot transmission is enabled after CS Tone. This attribute is applicable only when
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Disabled**.

        +--------------+------------------------------------------------------------------------+
        | Name (Value) | Description                                                            |
        +==============+========================================================================+
        | Disabled (0) | Specifies that there is no transmission in the CS Tone extension slot. |
        +--------------+------------------------------------------------------------------------+
        | Enabled (1)  | Specifies that there is transmission in the CS Tone extension slot.    |
        +--------------+------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ChannelSoundingToneExtensionSlot, int):
                Specifies whether the tone extension slot transmission is enabled after CS Tone. This attribute is applicable only when
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.ChannelSoundingToneExtensionSlot else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_TONE_EXTENSION_SLOT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_sounding_number_of_antenna_path(self, selector_string):
        r"""Gets the number of antenna paths for the generated LE-CS packet. This attribute is applicable only when you set
        the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of antenna paths for the generated LE-CS packet. This attribute is applicable only when you set
                the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_NUMBER_OF_ANTENNA_PATH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_sounding_number_of_antenna_path(self, selector_string, value):
        r"""Sets the number of antenna paths for the generated LE-CS packet. This attribute is applicable only when you set
        the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **1**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of antenna paths for the generated LE-CS packet. This attribute is applicable only when you set
                the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_NUMBER_OF_ANTENNA_PATH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_sounding_antenna_switch_time(self, selector_string):
        r"""Gets the Channel Sounding Antenna Switch Time for the LE-CS packet. This attribute is applicable only when you set
        the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **0 us**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the Channel Sounding Antenna Switch Time for the LE-CS packet. This attribute is applicable only when you set
                the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_ANTENNA_SWITCH_TIME.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_sounding_antenna_switch_time(self, selector_string, value):
        r"""Sets the Channel Sounding Antenna Switch Time for the LE-CS packet. This attribute is applicable only when you set
        the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
        **SYNC**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **0 us**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the Channel Sounding Antenna Switch Time for the LE-CS packet. This attribute is applicable only when you set
                the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-CS** and the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any value other than
                **SYNC**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.CHANNEL_SOUNDING_ANTENNA_SWITCH_TIME.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_zadoff_chu_index(self, selector_string):
        r"""Gets Zadoff-Chu Index for the Long Training Sequence in the preamble. Input to the Zadoff-Chu Index attribute must
        be in the range of [1 - 16]. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **7**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies Zadoff-Chu Index for the Long Training Sequence in the preamble. Input to the Zadoff-Chu Index attribute must
                be in the range of [1 - 16]. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.ZADOFF_CHU_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_zadoff_chu_index(self, selector_string, value):
        r"""Sets Zadoff-Chu Index for the Long Training Sequence in the preamble. Input to the Zadoff-Chu Index attribute must
        be in the range of [1 - 16]. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **7**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies Zadoff-Chu Index for the Long Training Sequence in the preamble. Input to the Zadoff-Chu Index attribute must
                be in the range of [1 - 16]. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.ZADOFF_CHU_INDEX.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_high_data_throughput_packet_format(self, selector_string):
        r"""Gets the Higher Data Throughput (HDT) packet format. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Format0**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Short Format (0) | Specifies that the HDT packet format is Short Format. This packet consists of preamble and control header field.         |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Format0 (1)      | Specifies that the HDT packet format is Format0. This packet consists of preamble, control header, PDU header and        |
        |                  | payload field. The maximum payload length is 510 bytes.                                                                  |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Format1 (2)      | Specifies that the HDT packet format is Format1. This packet format is similar to the Format0 but its payload zone       |
        |                  | consists of multiple blocks and the maximum payload length per payload is 8191 bytes.                                    |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.HighDataThroughputPacketFormat):
                Specifies the Higher Data Throughput (HDT) packet format. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.HIGH_DATA_THROUGHPUT_PACKET_FORMAT.value,
            )
            attr_val = enums.HighDataThroughputPacketFormat(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_high_data_throughput_packet_format(self, selector_string, value):
        r"""Sets the Higher Data Throughput (HDT) packet format. This attribute is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Format0**.

        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)     | Description                                                                                                              |
        +==================+==========================================================================================================================+
        | Short Format (0) | Specifies that the HDT packet format is Short Format. This packet consists of preamble and control header field.         |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Format0 (1)      | Specifies that the HDT packet format is Format0. This packet consists of preamble, control header, PDU header and        |
        |                  | payload field. The maximum payload length is 510 bytes.                                                                  |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Format1 (2)      | Specifies that the HDT packet format is Format1. This packet format is similar to the Format0 but its payload zone       |
        |                  | consists of multiple blocks and the maximum payload length per payload is 8191 bytes.                                    |
        +------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.HighDataThroughputPacketFormat, int):
                Specifies the Higher Data Throughput (HDT) packet format. This attribute is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to **LE-HDT**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.HighDataThroughputPacketFormat else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.HIGH_DATA_THROUGHPUT_PACKET_FORMAT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_vhdt_mode_enabled(self, selector_string):
        r"""+--------------+-------------+
        | Name (Value) | Description |
        +==============+=============+
        | False (0)    |             |
        +--------------+-------------+
        | True (1)     |             |
        +--------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.VhdtModeEnabled):
                +--------------+-------------+
                | Name (Value) | Description |
                +==============+=============+
                | False (0)    |             |
                +--------------+-------------+
                | True (1)     |             |
                +--------------+-------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.VHDT_MODE_ENABLED.value
            )
            attr_val = enums.VhdtModeEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_vhdt_mode_enabled(self, selector_string, value):
        r"""+--------------+-------------+
        | Name (Value) | Description |
        +==============+=============+
        | False (0)    |             |
        +--------------+-------------+
        | True (1)     |             |
        +--------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.VhdtModeEnabled, int):
                +--------------+-------------+
                | Name (Value) | Description |
                +==============+=============+
                | False (0)    |             |
                +--------------+-------------+
                | True (1)     |             |
                +--------------+-------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.VhdtModeEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.VHDT_MODE_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_block_repetition_sequences(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):


            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.NUMBER_OF_BLOCK_REPETITION_SEQUENCES.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_block_repetition_sequences(self, selector_string, value):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):


        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.NUMBER_OF_BLOCK_REPETITION_SEQUENCES.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_number(self, selector_string):
        r"""Gets the RF channel number of the signal generated by the device under test (DUT), as defined in the bluetooth
        specification. This attribute is applicable when you enable the ACP measurement and when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the RF channel number of the signal generated by the device under test (DUT), as defined in the bluetooth
                specification. This attribute is applicable when you enable the ACP measurement and when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_NUMBER.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_number(self, selector_string, value):
        r"""Sets the RF channel number of the signal generated by the device under test (DUT), as defined in the bluetooth
        specification. This attribute is applicable when you enable the ACP measurement and when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the RF channel number of the signal generated by the device under test (DUT), as defined in the bluetooth
                specification. This attribute is applicable when you enable the ACP measurement and when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_NUMBER.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_detected_packet_type(self, selector_string):
        r"""Gets the packet type detected by the RFmxBluetooth Auto Detect Signal method. This attribute can be queried only after
        calling the RFmxBluetooth Auto Detect Signal method.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is **Unknown**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the packet type detected by the RFmxBluetooth Auto Detect Signal method. This attribute can be queried only after
                calling the RFmxBluetooth Auto Detect Signal method.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DETECTED_PACKET_TYPE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_detected_data_rate(self, selector_string):
        r"""Gets the data rate detected by the RFmxBluetooth Auto Detect Signal method. This attribute returns a valid data rate only
        if the Detected Packet Type attribute returns LE. This attribute can be queried only after calling the RFmxBluetooth Auto
        Detect Signal method.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is **Not Applicable**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the data rate detected by the RFmxBluetooth Auto Detect Signal method. This attribute returns a valid data rate only
                if the Detected Packet Type attribute returns LE. This attribute can be queried only after calling the RFmxBluetooth Auto
                Detect Signal method.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DETECTED_DATA_RATE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_detected_payload_length(self, selector_string):
        r"""Gets the payload length detected by the RFmxBluetooth Auto Detect Signal method. This attribute can be queried only after
        calling the RFmxBluetooth Auto Detect Signal method.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is -1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the payload length detected by the RFmxBluetooth Auto Detect Signal method. This attribute can be queried only after
                calling the RFmxBluetooth Auto Detect Signal method.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DETECTED_PAYLOAD_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_limited_configuration_change(self, selector_string):
        r"""Gets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies and/or
        power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
        value other than Disabled, the RFmx driver will use an optimized code path and skip some checks. Because RFmx skips
        some checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in
        the `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to precompute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFInstr or personality attributes while
        testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        Selector String topic for information about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration and RFmxInstr configuration are locked after the first Commit or Initiate of the named signal       |
        |                                        | configuration. Any configuration change thereafter either in RFmxInstr attributes or personality attributes will not be  |
        |                                        | considered by subsequent RFmx Commits or Initiates of this signal.                                                       |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency, external attenuation, and RFInstr configuration, is locked after      |
        |                                        | first Commit or Initiate of the named signal configuration. Thereafter, only the Center Frequency and External           |
        |                                        | Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of this signal.         |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level and RFInstr configuration, is locked after first Commit or          |
        |                                        | Initiate of the named signal configuration. Thereafter only the Reference Level attribute value change will be           |
        |                                        | considered by subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ     |
        |                                        | Power Edge Trigger, NI recommends that you set the IQ Power Edge Level Type to Relative so that the trigger level is     |
        |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
        |                                        | Property topic for more details about the limitations of using this mode.                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, external attenuation, and RFInstr configuration, is  |
        |                                        | locked after first Commit or Initiate of the named signal configuration. Thereafter only Center Frequency, Reference     |
        |                                        | Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of  |
        |                                        | this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power      |
        |                                        | Edge                                                                                                                     |
        |                                        | Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to   |
        |                                        | the Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this  |
        |                                        | mode.                                                                                                                    |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr    |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type to Relative so that the trigger level is automatically       |
        |                                        | adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic  |
        |                                        | for more details about the limitations of using this mode.                                                               |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LimitedConfigurationChange):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value
            )
            attr_val = enums.LimitedConfigurationChange(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_limited_configuration_change(self, selector_string, value):
        r"""Sets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies and/or
        power levels repeatedly, enabling this attribute can help achieve faster measurements. When you set this attribute to a
        value other than Disabled, the RFmx driver will use an optimized code path and skip some checks. Because RFmx skips
        some checks when you use this attribute, you need to be aware of the limitations of this feature, which are listed in
        the `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to precompute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFInstr or personality attributes while
        testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        Selector String topic for information about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration and RFmxInstr configuration are locked after the first Commit or Initiate of the named signal       |
        |                                        | configuration. Any configuration change thereafter either in RFmxInstr attributes or personality attributes will not be  |
        |                                        | considered by subsequent RFmx Commits or Initiates of this signal.                                                       |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency, external attenuation, and RFInstr configuration, is locked after      |
        |                                        | first Commit or Initiate of the named signal configuration. Thereafter, only the Center Frequency and External           |
        |                                        | Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of this signal.         |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level and RFInstr configuration, is locked after first Commit or          |
        |                                        | Initiate of the named signal configuration. Thereafter only the Reference Level attribute value change will be           |
        |                                        | considered by subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ     |
        |                                        | Power Edge Trigger, NI recommends that you set the IQ Power Edge Level Type to Relative so that the trigger level is     |
        |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
        |                                        | Property topic for more details about the limitations of using this mode.                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, external attenuation, and RFInstr configuration, is  |
        |                                        | locked after first Commit or Initiate of the named signal configuration. Thereafter only Center Frequency, Reference     |
        |                                        | Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of  |
        |                                        | this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power      |
        |                                        | Edge                                                                                                                     |
        |                                        | Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to   |
        |                                        | the Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this  |
        |                                        | mode.                                                                                                                    |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr    |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type to Relative so that the trigger level is automatically       |
        |                                        | adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic  |
        |                                        | for more details about the limitations of using this mode.                                                               |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LimitedConfigurationChange, int):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.LimitedConfigurationChange else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_level_initial_reference_level(self, selector_string):
        r"""Gets the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
        input signal. This value is expressed in dBm.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
                input signal. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_level_initial_reference_level(self, selector_string, value):
        r"""Sets the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
        input signal. This value is expressed in dBm.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
                input signal. This value is expressed in dBm.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_result_fetch_timeout(self, selector_string):
        r"""Gets the time, in seconds, to wait before results are available in the RFmxBluetooth Attribute. Set this value to a time
        longer than expected for fetching the measurement. A value of -1 specifies that the RFmxBluetooth Attribute waits until the
        measurement is complete.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time, in seconds, to wait before results are available in the RFmxBluetooth Attribute. Set this value to a time
                longer than expected for fetching the measurement. A value of -1 specifies that the RFmxBluetooth Attribute waits until the
                measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_result_fetch_timeout(self, selector_string, value):
        r"""Sets the time, in seconds, to wait before results are available in the RFmxBluetooth Attribute. Set this value to a time
        longer than expected for fetching the measurement. A value of -1 specifies that the RFmxBluetooth Attribute waits until the
        measurement is complete.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time, in seconds, to wait before results are available in the RFmxBluetooth Attribute. Set this value to a time
                longer than expected for fetching the measurement. A value of -1 specifies that the RFmxBluetooth Attribute waits until the
                measurement is complete.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def abort_measurements(self, selector_string):
        r"""Stops acquisition and measurements associated with signal instance that you specify in the **Selector String**
        parameter, which were previously initiated by the :py:meth:`initiate` or measurement read methods. Calling this method
        is optional, unless you want to stop a measurement before it is complete. This method executes even if there is an
        incoming error.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.abort_measurements(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_detect_signal(self, selector_string, timeout):
        r"""Detects the Bluetooth packet and returns the detected packet type, data rate, and payload length.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.auto_detect_signal(  # type: ignore
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_level(self, selector_string, measurement_interval):
        r"""Examines the input signal to calculate the peak power level and sets it as the value of the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.REFERENCE_LEVEL` attribute. Use this method to help calculate an
        approximate setting for the reference level.

        The RFmxBluetooth Auto Level method does the following:
        #. Resets the mixer level, mixer level offset and IF output power offset.

        #. Sets the starting reference level to the maximum reference level supported by the device based on the current RF attenuation, mechanical attenuation and preamp enabled settings.

        #. Iterates to adjust the reference level based on the input signal peak power.

        #. Uses immediate triggering and restores the trigger settings back to user setting after completing execution.

        You can also specify the starting reference level using the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL` attribute.
        When using NI 5663, 5665, or 5668R devices, NI recommends that you set an appropriate value for mechanical
        attenuation before calling the RFmxBluetooth Auto Level method. Setting an appropriate value for mechanical attenuation
        reduces the number of times the attenuator settings are changed by this method, thus reducing wear and tear, and
        maximizing the life time of the attenuator.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_interval (float):
                This parameter specifies the acquisition length. Use this value to compute the number of samples to acquire from the
                signal analyzer. This value is expressed in seconds. The default value is 10 ms.

                Auto Level method does not use any trigger for acquisition. It ignores the user-configured trigger attributes.
                NI recommends that you set a sufficiently high measurement interval to ensure that the acquired waveform is at least as
                long as one period of the signal.

        Returns:
            Tuple (reference_level, error_code):

            reference_level (float):
                This parameter returns the estimated peak power level of the input signal. This value is expressed in dBm for RF
                devices and V\ :sub:`pk-pk`\ for baseband devices.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            reference_level, error_code = self._interpreter.auto_level(  # type: ignore
                updated_selector_string, measurement_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return reference_level, error_code

    @_raise_if_disposed
    def check_measurement_status(self, selector_string):
        r"""Checks the status of the measurement. Use this method to check for any errors that may occur during measurement or to
        check whether the measurement is complete and results are available.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name.

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            Tuple (is_done, error_code):

            is_done (bool):
                This parameter indicates whether the measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            is_done, error_code = self._interpreter.check_measurement_status(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return is_done, error_code

    @_raise_if_disposed
    def clear_all_named_results(self, selector_string):
        r"""Clears all results for the signal that you specify in the **Selector String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_all_named_results(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def clear_named_result(self, selector_string):
        r"""Clears a result instance specified by the result name in the **Selector String** parameter.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name.

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_named_result(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def commit(self, selector_string):
        r"""Commits settings to the hardware. Calling this method is optional. RFmxBluetooth commits settings to the hardware when you
        call the :py:meth:`initiate` method or any of the measurement Read methods.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.commit(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_channel_number(self, selector_string, channel_number):
        r"""Configures the RF channel number of the signal generated by the device under test (DUT), as defined in the Bluetooth
        specification.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            channel_number (int):
                This parameter specifies the RF channel number of the signal generated by the device under test (DUT), as defined in
                the Bluetooth specification. This parameter is applicable when you enable the ACP measurement and when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**. The default value
                is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_channel_number(  # type: ignore
                updated_selector_string, channel_number
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_data_rate(self, selector_string, data_rate):
        r"""Configures the data rate of low energy (LE) or low energy - channel sounding (LE-CS) packets to be measured.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            data_rate (int):
                This parameter specifies the data rate of the LE packet transmitted by the device under test (DUT). This value is
                expressed in bps. This parameter is applicable only to the LE/LE-CS packet types. The default value is **1M**.

                +----------------+----------------------------+
                | Name (Value)   | Description                |
                +================+============================+
                | 125K (125000)  | The date rate is 125 Kbps. |
                +----------------+----------------------------+
                | 500K (500000)  | The date rate is 500 Kbps. |
                +----------------+----------------------------+
                | 1M (1000000)   | The date rate is 1 Mbps.   |
                +----------------+----------------------------+
                | 2M (2000000)   | The date rate is 2 Mbps.   |
                +----------------+----------------------------+
                | 3M (3000000)   | The date rate is 3 Mbps.   |
                +----------------+----------------------------+
                | 4M (4000000)   | The date rate is 4 Mbps.   |
                +----------------+----------------------------+
                | 6M (6000000)   | The date rate is 6 Mbps.   |
                +----------------+----------------------------+
                | 7.5M (7500000) | The date rate is 7.5 Mbps. |
                +----------------+----------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_data_rate(  # type: ignore
                updated_selector_string, data_rate
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_digital_edge_trigger(
        self, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        r"""Configures the device to wait for a digital edge trigger and then marks a reference point within the record.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            digital_edge_source (string):
                This parameter specifies the source terminal for the digital edge trigger. The default of this attribute is hardware
                dependent.

                +---------------------------+-----------------------------------------------------------+
                | Name (Value)              | Description                                               |
                +===========================+===========================================================+
                | PFI0 (PFI0)               | The trigger is received on PFI 0.                         |
                +---------------------------+-----------------------------------------------------------+
                | PFI1 (PFI1)               | The trigger is received on PFI 1.                         |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig0 (PXI_Trig0)     | The trigger is received on PXI trigger line 0.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig1 (PXI_Trig1)     | The trigger is received on PXI trigger line 1.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig2 (PXI_Trig2)     | The trigger is received on PXI trigger line 2.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig3 (PXI_Trig3)     | The trigger is received on PXI trigger line 3.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig4 (PXI_Trig4)     | The trigger is received on PXI trigger line 4.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig5 (PXI_Trig5)     | The trigger is received on PXI trigger line 5.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig6 (PXI_Trig6)     | The trigger is received on PXI trigger line 6.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig7 (PXI_Trig7)     | The trigger is received on PXI trigger line 7.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_STAR (PXI_STAR)       | The trigger is received on the PXI star trigger line.     |
                +---------------------------+-----------------------------------------------------------+
                | PXIe_DStarB (PXIe_DStarB) | The trigger is received on the PXIe DStar B trigger line. |
                +---------------------------+-----------------------------------------------------------+
                | TimerEvent (TimerEvent)   | The trigger is received from the timer event.             |
                +---------------------------+-----------------------------------------------------------+

            digital_edge (enums.DigitalEdgeTriggerEdge, int):
                This parameter specifies the trigger edge to detect. The default value is **Rising Edge**.

                +------------------+--------------------------------------------------------+
                | Name (Value)     | Description                                            |
                +==================+========================================================+
                | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
                +------------------+--------------------------------------------------------+
                | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
                +------------------+--------------------------------------------------------+

            trigger_delay (float):
                This parameter specifies the trigger delay time, in seconds. The default value is 0.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(digital_edge_source, "digital_edge_source")
            digital_edge = (
                digital_edge.value
                if type(digital_edge) is enums.DigitalEdgeTriggerEdge
                else digital_edge
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_digital_edge_trigger(  # type: ignore
                updated_selector_string,
                digital_edge_source,
                digital_edge,
                trigger_delay,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_external_attenuation(self, selector_string, external_attenuation):
        r"""Configures the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal
                analyzer. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your device in
                the* NI RF Vector Signal Analyzers Help*. The value is expressed in dB. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_external_attenuation(  # type: ignore
                updated_selector_string, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency_channel_number(self, selector_string, standard, channel_number):
        r"""Configures the expected carrier frequency of the RF signal to be acquired using **Channel Number** and
        **Standard** parameters.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            standard (enums.Standard, int):
                This parameter specifies the signal to which the Bluetooth physical layer belongs. The default value is **BR/EDR**.

                +--------------+---------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                           |
                +==============+=======================================================================================+
                | BR/EDR (0)   | Specifies that the signal belongs to Basic Rate (BR) or Enhanced Data Rate (EDR) PHY. |
                +--------------+---------------------------------------------------------------------------------------+
                | LE (1)       | Specifies that the signal belongs to Low Energy (LE) PHY.                             |
                +--------------+---------------------------------------------------------------------------------------+
                | LE-CS (2)    | Specifies that the signal belongs to Low Energy - Channel Sounding (LE-CS) PHY.       |
                +--------------+---------------------------------------------------------------------------------------+

            channel_number (int):
                This parameter specifies the RF channel number of the signal generated by the device under test (DUT), as defined in
                the Bluetooth specification. This parameter is applicable when you enable the ACP measurement and when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**. The default value
                is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            standard = standard.value if type(standard) is enums.Standard else standard
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency_channel_number(  # type: ignore
                updated_selector_string, standard, channel_number
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency(self, selector_string, center_frequency):
        r"""Configures the expected carrier frequency of the RF signal to acquire. The signal analyzer tunes to this frequency.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            center_frequency (float):
                This parameter Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is
                expressed in Hz. The signal analyzer tunes to this frequency. The default value of this parameter is hardware
                dependent. The default value for the devices PXIe-5645/5820 is 0 Hz. The default value for devices
                PXIe-5644/5646/5840/5663/5663E/5665/5668 is 2.402 GHz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency(  # type: ignore
                updated_selector_string, center_frequency
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
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
        r"""Configures the device to wait for the complex power of the I/Q data to cross the specified threshold and then marks a
        reference point within the record.

        To trigger on bursty signals, specify a minimum quiet time, which ensures that the trigger does not occur in
        the middle of the burst signal. The quiet time must be set to a value smaller than the time between bursts, but large
        enough to ignore power changes within a burst.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            iq_power_edge_source (string):
                This parameter specifies the channel from which the device monitors the trigger. The default of this attribute is
                hardware dependent.

            iq_power_edge_slope (enums.IQPowerEdgeTriggerSlope, int):
                This parameter specifies whether the device asserts the trigger when the signal power is rising or when it is falling.
                The device asserts the trigger when the signal power exceeds the specified level with the slope you specify. The
                default value is **Rising Slope**.

                +-------------------+-------------------------------------------------------+
                | Name (Value)      | Description                                           |
                +===================+=======================================================+
                | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
                +-------------------+-------------------------------------------------------+
                | Falling Slope (1) | The trigger asserts when the signal power is falling. |
                +-------------------+-------------------------------------------------------+

            iq_power_edge_level (float):
                This parameter specifies the power level at which the device triggers. This value is expressed in dB when you set the
                **IQ Power Edge Level Type** parameter to **Relative**; and is expressed in dBm when you set the **IQ Power Edge Level
                Type** parameter to **Absolute**. The device asserts the trigger when the signal exceeds the level specified by the
                value of this parameter, taking into consideration the specified slope. The default of this attribute is hardware
                dependent.

            trigger_delay (float):
                This parameter specifies the trigger delay time, in seconds. The default value is 0.

            trigger_min_quiet_time_mode (enums.TriggerMinimumQuietTimeMode, int):
                This parameter specifies whether the measurement computes the minimum quiet time used for triggering. The default value
                is **Auto**.

                +--------------+------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                              |
                +==============+==========================================================================================+
                | Manual (0)   | The minimum quiet time used for triggering is the value of the Min Quiet Time parameter. |
                +--------------+------------------------------------------------------------------------------------------+
                | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                     |
                +--------------+------------------------------------------------------------------------------------------+

            trigger_min_quiet_time_duration (float):
                This parameter specifies the duration, in seconds, for which the signal must be quiet before the signal analyzer arms
                the I/Q Power Edge trigger. If you set the **IQ Power Edge Slope** parameter to **Rising Slope**, the signal is quiet
                when it is below the trigger level. If you set the **IQ Power Edge Slope** parameter to **Falling Slope**, the signal
                is quiet when it is above the trigger level. The default of this attribute is hardware dependent.

            iq_power_edge_level_type (enums.IQPowerEdgeTriggerLevelType, int):
                This parameter specifies the reference for the ** IQ Power Edge Level** parameter. The default value is **Relative**.

                +--------------+-----------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                   |
                +==============+===============================================================================================+
                | Relative (0) | The                                                                                           |
                |              | IQ Power Edge Level parameter is relative to the value of the Reference Level attribute.      |
                +--------------+-----------------------------------------------------------------------------------------------+
                | Absolute (1) | The                                                                                           |
                |              | IQ Power Edge Level parameter specifies the absolute power.                                   |
                +--------------+-----------------------------------------------------------------------------------------------+

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(iq_power_edge_source, "iq_power_edge_source")
            iq_power_edge_slope = (
                iq_power_edge_slope.value
                if type(iq_power_edge_slope) is enums.IQPowerEdgeTriggerSlope
                else iq_power_edge_slope
            )
            trigger_min_quiet_time_mode = (
                trigger_min_quiet_time_mode.value
                if type(trigger_min_quiet_time_mode) is enums.TriggerMinimumQuietTimeMode
                else trigger_min_quiet_time_mode
            )
            iq_power_edge_level_type = (
                iq_power_edge_level_type.value
                if type(iq_power_edge_level_type) is enums.IQPowerEdgeTriggerLevelType
                else iq_power_edge_level_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_iq_power_edge_trigger(  # type: ignore
                updated_selector_string,
                iq_power_edge_source,
                iq_power_edge_slope,
                iq_power_edge_level,
                trigger_delay,
                trigger_min_quiet_time_mode,
                trigger_min_quiet_time_duration,
                iq_power_edge_level_type,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_le_direction_finding(
        self, selector_string, direction_finding_mode, cte_length, cte_slot_duration
    ):
        r"""Configures the mode of direction finding, length of the constant tone extension field, and the duration of the
        switching slot in the generated signal.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            direction_finding_mode (enums.DirectionFindingMode, int):
                This parameter specifies the mode of direction finding. The default value is **Disabled**.

                +------------------------+-----------------------------------------------------------------------------------+
                | Name (Value)           | Description                                                                       |
                +========================+===================================================================================+
                | Disabled (0)           | Specifies that the LE packet does not have fields required for direction finding. |
                +------------------------+-----------------------------------------------------------------------------------+
                | Angle of Arrival (1)   | Specifies the LE packets uses the Angle of Arrival method of direction finding.   |
                +------------------------+-----------------------------------------------------------------------------------+
                | Angle of Departure (2) | Specifies the LE packets uses the angle of departure method of direction finding. |
                +------------------------+-----------------------------------------------------------------------------------+

            cte_length (float):
                This parameter specifies the length of the constant tone extension field in the generated signal. This value is
                expressed in seconds. This parameter is applicable only when you set the **Direction Finding Mode** parameter to either
                **Angle of Arrival** or **Angle of Departure**. The default value is 160 microseconds.

            cte_slot_duration (float):
                This parameter specifies the length of the switching slots and transmit slots in the constant tone extension field in
                the generated signal. This attribute is applicable only when you set the **Direction Finding Mode** parameter to
                **Angle of Arrival** or **Angle of Departure** The default value is 1u.

                +---------------+-------------------------------------------------------------------------------+
                | Name (Value)  | Description                                                                   |
                +===============+===============================================================================+
                | 1u (0.000001) | Specifies that the length of the transmit slot and sampling slot is 0.000001. |
                +---------------+-------------------------------------------------------------------------------+
                | 2u (0.000002) | Specifies that the length of the transmit slot and sampling slot is 0.000002. |
                +---------------+-------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            direction_finding_mode = (
                direction_finding_mode.value
                if type(direction_finding_mode) is enums.DirectionFindingMode
                else direction_finding_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_le_direction_finding(  # type: ignore
                updated_selector_string, direction_finding_mode, cte_length, cte_slot_duration
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_packet_type(self, selector_string, packet_type):
        r"""Configures the type of Bluetooth packet to be measured.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            packet_type (enums.PacketType, int):
                This parameter specifies the type of Bluetooth packet to be measured. In this document, packet type is sometimes
                referred to by the Bluetooth physical layer (PHY) it belongs to. Supported Bluetooth physical layers are basic rate
                (BR), enhanced data rate (EDR), low energy (LE) and low energy - channel sounding (LE-CS).

                The default value is **DH1**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | DH1 (0)      | Specifies that the packet type is DH1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.2, Part B,      |
                |              | Volume 2 of the Bluetooth Core Specification v5.1 for more information about this packet.                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | DH3 (1)      | Specifies that the packet type is DH3. The packet belongs to BR PHY. Refer to section 6.5.4.4, Part B, Volume 2 of the   |
                |              | Bluetooth Core Specification v5.1 for more information about this packet.                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | DH5 (2)      | Specifies that the packet type is DH5. The packet belongs to BR PHY. Refer to section 6.5.4.6, Part B, Volume 2 of the   |
                |              | Bluetooth Core Specification v5.1 for more information about this packet.                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | DM1 (3)      | Specifies that the packet type is DM1. The packet belongs to BR PHY. Refer to sections 6.5.1.5 and 6.5.4.1, Part B,      |
                |              | Volume 2 of the Bluetooth Core Specification v5.1 for more information about this packet.                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | DM3 (4)      | Specifies that the packet type is DM3. The packet belongs to BR PHY. Refer to section 6.5.4.3, Part B, Volume 2 of the   |
                |              | Bluetooth Core Specification v5.1 for more information about this packet.                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | DM5 (5)      | Specifies that the packet type is DM5. The packet belongs to BR PHY. Refer to section 6.5.4.5, Part B, Volume 2 of the   |
                |              | Bluetooth Core Specification v5.1 for more information about this packet.                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 2-DH1 (6)    | Specifies that the packet type is 2-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.8, Part B, Volume 2 of    |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 2-DH3 (7)    | Specifies that the packet type is 2-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.9, Part B, Volume 2 of    |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 2-DH5 (8)    | Specifies that the packet type is 2-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.10, Part B, Volume 2 of   |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3-DH1 (9)    | Specifies that the packet type is 3-DH1. The packet belongs to EDR PHY. Refer to section 6.5.4.11, Part B, Volume 2 of   |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3-DH3 (10)   | Specifies that the packet type is 3-DH3. The packet belongs to EDR PHY. Refer to section 6.5.4.12, Part B, Volume 2 of   |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3-DH5 (11)   | Specifies that the packet type is 3-DH5. The packet belongs to EDR PHY. Refer to section 6.5.4.13, Part B, Volume 2 of   |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 2-EV3 (12)   | Specifies that the packet type is 2-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.4, Part B, Volume 2 of    |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 2-EV5 (13)   | Specifies that the packet type is 2-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.5, Part B, Volume 2 of    |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3-EV3 (14)   | Specifies that the packet type is 3-EV3. The packet belongs to EDR PHY. Refer to section 6.5.3.6, Part B, Volume 2 of    |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 3-EV5 (15)   | Specifies that the packet type is 3-EV5. The packet belongs to EDR PHY. Refer to section 6.5.3.7, Part B, Volume 2 of    |
                |              | the Bluetooth Core Specification v5.1 for more information about this packet.                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | LE (16)      | Specifies that the packet belongs to LE PHY. Refer to sections 2.1 and 2.2, Part B, Volume 6 of the Bluetooth Core       |
                |              | Specification v5.1 for more information about this packet.                                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | LE-CS (17)   | Specifies that the packet type is LE-CS. The packet belongs to LE-CS PHY.                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | LE-HDT (18)  | Specifies that the packet type is LE-HDT. The packet belongs to LE-HDT PHY.                                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            packet_type = (
                packet_type.value if type(packet_type) is enums.PacketType else packet_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_packet_type(  # type: ignore
                updated_selector_string, packet_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_payload_bit_pattern(self, selector_string, payload_bit_pattern):
        r"""Configures the bit pattern present in the payload of the packet.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            payload_bit_pattern (enums.PayloadBitPattern, int):
                This parameter specifies the bit pattern present in the payload of the packet. This value is used to determine the set
                of ModAcc measurements to be performed.

                The following table shows the measurements applicable for different payload bit patterns:

                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
                | Bluetooth PHY | Data Rate | Standard                                                                            | 11110000                                                                                                     | 10101010                   |
                +===============+===========+=====================================================================================+==============================================================================================================+============================+
                | BR            | NA        | Error                                                                               | df1                                                                                                          | df2 and BR frequency error |
                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
                | EDR           | NA        | DEVM (The measurement considers PN9 as payload pattern)                             | Error                                                                                                        | Error                      |
                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
                | LE            | 1 Mbps    | Error                                                                               | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
                | LE            | 2 Mbps    | Error                                                                               | df1 and LE frequency errors on the constant tone extension (CTE) field within the direction finding packets. | df2 and LE frequency error |
                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
                | LE            | 125 kbps  | df1 and LE frequency errors (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+
                | LE            | 500 kbps  | df2 and LE frequency errors (The measurement considers 11111111 as payload pattern) | Error                                                                                                        | Error                      |
                +---------------+-----------+-------------------------------------------------------------------------------------+--------------------------------------------------------------------------------------------------------------+----------------------------+

                The default value is **Standard Defined**.

                +----------------------+-------------------------------------------------------------+
                | Name (Value)         | Description                                                 |
                +======================+=============================================================+
                | Standard Defined (0) | Specifies that the payload bit pattern is Standard Defined. |
                +----------------------+-------------------------------------------------------------+
                | 11110000 (1)         | Specifies that the payload bit pattern is 11110000.         |
                +----------------------+-------------------------------------------------------------+
                | 10101010 (2)         | Specifies that the payload bit pattern is 10101010.         |
                +----------------------+-------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            payload_bit_pattern = (
                payload_bit_pattern.value
                if type(payload_bit_pattern) is enums.PayloadBitPattern
                else payload_bit_pattern
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_payload_bit_pattern(  # type: ignore
                updated_selector_string, payload_bit_pattern
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_payload_length(self, selector_string, payload_length_mode, payload_length):
        r"""Configures the **Payload Length Mode** and **Payload Length** parameters that decide the length of the payload to be
        used for the measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            payload_length_mode (enums.PayloadLengthMode, int):
                This parameter specifies the payload length mode of the signal to be measured. The **Payload Length Mode** and
                **Payload Length** parameters decide the length of the payload to be used for measurement. The default value is
                **Auto**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | Manual (0)   | Enables the value specified by the Payload Length parameter. The acquisition and measurement durations will be decided   |
                |              | based on this value.                                                                                                     |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Auto (1)     | Enables the standard defined maximum payload length for BR, EDR, LE and LE-CS packet, and the maximum payload zone       |
                |              | length for LE-HDT packet. If this parameter is set to Auto, the maximum standard defined payload length or payload zone  |
                |              | length for the selected packet type is chosen. The maximum payload length a device under test (DUT) can generate varies  |
                |              | from 37 to 255 bytes for LE packet, and the maximum payload zone length varies from 514 to 33020 bytes for LE-HDT        |
                |              | packet. When you set the payload length mode to Auto, RFmx chooses 37 bytes for LE packet and 514 bytes for LE-HDT       |
                |              | packet.                                                                                                                  |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            payload_length (int):
                This parameter specifies the payload length of BR, EDR, LE and LE-CS packet, and the payload zone length of LE-HDT
                packet, in bytes. The parameter is applicable only when you set the **Payload Length Mode** parameter to **Manual**.
                This parameter returns the payload length or payload zone length used for measurement if you set the Payload Length
                Mode parameter to **Auto**. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            payload_length_mode = (
                payload_length_mode.value
                if type(payload_length_mode) is enums.PayloadLengthMode
                else payload_length_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_payload_length(  # type: ignore
                updated_selector_string, payload_length_mode, payload_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_reference_level(self, selector_string, reference_level):
        r"""Configures the reference level which represents the maximum expected power of an RF input signal.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of an RF input signal. This
                value is expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices. The default of this parameter is
                hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_reference_level(  # type: ignore
                updated_selector_string, reference_level
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_rf(
        self, selector_string, center_frequency, reference_level, external_attenuation
    ):
        r"""Configures the RF attributes of the signal specified by the selector string.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            center_frequency (float):
                This parameter specifies the expected carrier frequency of the RF signal to acquire. The signal analyzer tunes to this
                frequency. The value is expressed in Hz. The default of this attribute is hardware dependent.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of an RF input signal. This
                value is expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices. The default of this parameter is
                hardware dependent.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal
                analyzer. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your device in
                the* NI RF Vector Signal Analyzers Help*. The value is expressed in dB. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_rf(  # type: ignore
                updated_selector_string, center_frequency, reference_level, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        r"""Configures the device to wait for a software trigger and then marks a reference point within the record.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            trigger_delay (float):
                This parameter specifies the trigger delay time, in seconds. The default value is 0.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_software_edge_trigger(  # type: ignore
                updated_selector_string, trigger_delay, int(enable_trigger)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def disable_trigger(self, selector_string):
        r"""Configures the device to not wait for a trigger to mark a reference point within a record. This method defines the
        signal triggering as immediate.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.disable_trigger(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def initiate(self, selector_string, result_name):
        r"""Initiates all enabled measurements. Call this method after configuring the signal and measurement. This method
        asynchronously launches measurements in the background and immediately returns to the caller program. You can fetch
        measurement results using the Fetch methods or result attributes in the attribute node. To get the status of
        measurements, use the :py:meth:`wait_for_measurement_complete` method or :py:meth:`check_measurement_status` method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.initiate(  # type: ignore
                updated_selector_string, result_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def reset_to_default(self, selector_string):
        r"""Resets a signal to the default values.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.reset_to_default(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def select_measurements(self, selector_string, measurements, enable_all_traces):
        r"""Enables all the measurements that you specify in the **Measurements** parameter and disables all other measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurements (enums.MeasurementTypes, int):
                This parameter specifies the measurement to perform. You can specify one or more of the following measurements. The
                default is an empty array.

                +--------------------+-------------------------------------+
                | Name (Value)       | Description                         |
                +====================+=====================================+
                | TXP (0)            | Enables TXP measurement.            |
                +--------------------+-------------------------------------+
                | ModAcc (1)         | Enables ModAcc measurement.         |
                +--------------------+-------------------------------------+
                | 20dB Bandwidth (2) | Enables 20dB Bandwidth measurement. |
                +--------------------+-------------------------------------+
                | FrequencyRange (3) | Enables FrequencyRange measurement. |
                +--------------------+-------------------------------------+
                | ACP (4)            | Enables ACP measurement.            |
                +--------------------+-------------------------------------+

            enable_all_traces (bool):
                This parameter specifies whether to enable all traces for the selected measurement. The default value is FALSE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurements = (
                measurements.value if type(measurements) is enums.MeasurementTypes else measurements
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.select_measurements(  # type: ignore
                updated_selector_string, measurements, int(enable_all_traces)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def wait_for_measurement_complete(self, selector_string, timeout):
        r"""Waits for the specified number for seconds for all the measurements to complete.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of the
                result name.

                Example:

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.wait_for_measurement_complete(  # type: ignore
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @staticmethod
    def build_result_string(result_name):
        r"""Creates selector string for use with configuration or fetch.

        Args:
            result_name (string):
                Specifies the result name for building the selector string.
                This input accepts the result name with or without the "result::" prefix.
                Example: "", "result::r1", "r1".

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(result_name, "result_name")
        return _helper.build_result_string(result_name)

    @staticmethod
    def build_offset_string(selector_string, offset_number):
        r"""Creates the offset string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            offset_number (int):
                This parameter specifies the offset number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_offset_string(selector_string, offset_number)  # type: ignore

    @staticmethod
    def build_slot_string(selector_string, slot_number):
        r"""Creates the slot string for use with the TXP configuration or fetch attributes and methods.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            slot_number (int):
                This parameter specifies the slot number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_slot_string(selector_string, slot_number)  # type: ignore

    @_raise_if_disposed
    def clone_signal_configuration(self, new_signal_name):
        r"""Creates a new instance of a signal by copying all the properties from an existing signal instance.

        Args:
            new_signal_name (string):
                This parameter specifies the name of the new signal. This parameter accepts the signal name with or without the \"signal::\" prefix.

                Example:

                \"signal::NewSigName\"

                \"NewSigName\"

        Returns:
            Tuple (cloned_signal, error_code):

            cloned_signal (Bluetooth):
                Contains a new Bluetooth signal instance.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(new_signal_name, "new_signal_name")
            updated_new_signal_name = _helper.validate_and_remove_signal_qualifier(
                new_signal_name, self
            )
            cloned_signal, error_code = self._interpreter.clone_signal_configuration(self.signal_configuration_name, updated_new_signal_name)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return cloned_signal, error_code

    @_raise_if_disposed
    def send_software_edge_trigger(self):
        r"""Sends a trigger to the device when you use the RFmxBluetooth Configure Trigger function to choose a software version of a trigger and the device is waiting for the trigger to be sent. You can also use this function to override a hardware trigger.

        This function returns an error in the following situations:

        - You configure an invalid trigger.

        - You have not previously called the initiate function.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_code = self._interpreter.send_software_edge_trigger()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_named_result_names(self, selector_string):
        r"""Returns all the named result names of the signal that you specify in the Selector String parameter.

        Args:
            selector_string (string):
                Pass an empty string. The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (result_names, default_result_exists, error_code):

            result_names (string):
                Returns an array of result names.

            default_result_exists (bool):
                Indicates whether the default result exists.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            result_names, default_result_exists, error_code = self._interpreter.get_all_named_result_names(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return result_names, default_result_exists, error_code

    @_raise_if_disposed
    def analyze_iq_1_waveform(self, selector_string, result_name, x0, dx, iq, reset):
        r"""Performs the enabled measurements on the  I/Q complex waveform  that you specify in the **IQ** parameter. Call this
        method after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch
        methods or result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **IQ** or **IQ or Spectral**.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq (numpy.complex64):
                This parameter specifies an array of complex-valued time domain data. The real and imaginary parts of this complex data
                array correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_iq_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, iq, int(reset)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code


class Bluetooth(_BluetoothBase):
    """Defines a root class which is used to identify and control Bluetooth signal configuration."""

    def __init__(self, session, signal_name="", cloning=False):
        """Initializes a Bluetooth signal configuration."""
        super(Bluetooth, self).__init__(
            session=session,
            signal_name=signal_name,
            cloning=cloning,
        )  # type: ignore

    def __enter__(self):
        """Enters the context of the Bluetooth signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the Bluetooth signal configuration."""
        self.dispose()  # type: ignore
        pass
