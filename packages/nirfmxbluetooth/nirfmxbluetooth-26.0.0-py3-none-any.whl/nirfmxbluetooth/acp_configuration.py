"""Provides methods to configure the Acp measurement."""

import functools

import nirfmxbluetooth.attributes as attributes
import nirfmxbluetooth.enums as enums
import nirfmxbluetooth.errors as errors
import nirfmxbluetooth.internal._helper as _helper


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed Bluetooth signal configuration")
        return f(*xs, **kws)

    return aux


class AcpConfiguration(object):
    """Provides methods to configure the Acp measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the Acp measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the ACP measurement.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the ACP measurement.

        You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_channel_mode(self, selector_string):
        r"""Gets which offset channels are used for the measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Symmetric**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | Symmetric (0) | Specifies that the offset channels are symmetrically located around the reference channel. The number of offsets on      |
        |               | either side of the reference channel is specified by the ACP Num Offsets attribute. In symmetric mode, the               |
        |               | Center Frequency attribute specifies the frequency of the reference channel, expressed in Hz.                            |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | In-band (1)   | Specifies that the measurement is performed over all the channels as specified by the standard. For BR and EDR packets,  |
        |               | 79 channels starting from 2.402GHz to 2.48GHz are used for the measurement. For LE packets, 81 channels starting from    |
        |               | 2.401GHz to 2.481GHz are used for the measurement. In In-band mode, the Center Frequency attribute specifies the         |
        |               | frequency of acquisition which must be equal to 2.441GHz. Configure the Channel Number attribute to specify the          |
        |               | frequency of the reference channel.                                                                                      |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpOffsetChannelMode):
                Specifies which offset channels are used for the measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE.value
            )
            attr_val = enums.AcpOffsetChannelMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_offset_channel_mode(self, selector_string, value):
        r"""Sets which offset channels are used for the measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Symmetric**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | Symmetric (0) | Specifies that the offset channels are symmetrically located around the reference channel. The number of offsets on      |
        |               | either side of the reference channel is specified by the ACP Num Offsets attribute. In symmetric mode, the               |
        |               | Center Frequency attribute specifies the frequency of the reference channel, expressed in Hz.                            |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | In-band (1)   | Specifies that the measurement is performed over all the channels as specified by the standard. For BR and EDR packets,  |
        |               | 79 channels starting from 2.402GHz to 2.48GHz are used for the measurement. For LE packets, 81 channels starting from    |
        |               | 2.401GHz to 2.481GHz are used for the measurement. In In-band mode, the Center Frequency attribute specifies the         |
        |               | frequency of acquisition which must be equal to 2.441GHz. Configure the Channel Number attribute to specify the          |
        |               | frequency of the reference channel.                                                                                      |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpOffsetChannelMode, int):
                Specifies which offset channels are used for the measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpOffsetChannelMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_offsets(self, selector_string):
        r"""Gets the number of offset channels used on either side of the reference channel for the adjacent channel power
        (ACP) measurement when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute
        to **Symmetric**. This attribute also returns the actual number of offsets used in the ACP measurement when you set the
        ACP Offset Channel Mode attribute to **In-band**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 5. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of offset channels used on either side of the reference channel for the adjacent channel power
                (ACP) measurement when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute
                to **Symmetric**. This attribute also returns the actual number of offsets used in the ACP measurement when you set the
                ACP Offset Channel Mode attribute to **In-band**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_OFFSETS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_offsets(self, selector_string, value):
        r"""Sets the number of offset channels used on either side of the reference channel for the adjacent channel power
        (ACP) measurement when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute
        to **Symmetric**. This attribute also returns the actual number of offsets used in the ACP measurement when you set the
        ACP Offset Channel Mode attribute to **In-band**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 5. Valid values are 0 to 100, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of offset channels used on either side of the reference channel for the adjacent channel power
                (ACP) measurement when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute
                to **Symmetric**. This attribute also returns the actual number of offsets used in the ACP measurement when you set the
                ACP Offset Channel Mode attribute to **In-band**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_OFFSETS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_offset_frequency(self, selector_string):
        r"""Gets the frequency of the offset channel with respect to the reference channel frequency. This value is expressed in
        Hz.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 1 MHz.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency of the offset channel with respect to the reference channel frequency. This value is expressed in
                Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.ACP_OFFSET_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_reference_channel_bandwidth_mode(self, selector_string):
        r"""+--------------+-------------+
        | Name (Value) | Description |
        +==============+=============+
        | Auto (0)     |             |
        +--------------+-------------+
        | Manual (1)   |             |
        +--------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpReferenceChannelBandwidthMode):
                +--------------+-------------+
                | Name (Value) | Description |
                +==============+=============+
                | Auto (0)     |             |
                +--------------+-------------+
                | Manual (1)   |             |
                +--------------+-------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_REFERENCE_CHANNEL_BANDWIDTH_MODE.value,
            )
            attr_val = enums.AcpReferenceChannelBandwidthMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_channel_bandwidth_mode(self, selector_string, value):
        r"""+--------------+-------------+
        | Name (Value) | Description |
        +==============+=============+
        | Auto (0)     |             |
        +--------------+-------------+
        | Manual (1)   |             |
        +--------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpReferenceChannelBandwidthMode, int):
                +--------------+-------------+
                | Name (Value) | Description |
                +==============+=============+
                | Auto (0)     |             |
                +--------------+-------------+
                | Manual (1)   |             |
                +--------------+-------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpReferenceChannelBandwidthMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_REFERENCE_CHANNEL_BANDWIDTH_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_channel_bandwidth(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.ACP_REFERENCE_CHANNEL_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_channel_bandwidth(self, selector_string, value):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):


        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.ACP_REFERENCE_CHANNEL_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_burst_synchronization_type(self, selector_string):
        r"""Gets the type of synchronization used for detecting the start of the EDR packet in the adjacent channel power
        (ACP) measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Preamble**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Preamble (1)  | Specifies that the measurement uses the preamble field bits to detect the start of the packet.                           |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
        |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.         |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpBurstSynchronizationType):
                Specifies the type of synchronization used for detecting the start of the EDR packet in the adjacent channel power
                (ACP) measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_BURST_SYNCHRONIZATION_TYPE.value
            )
            attr_val = enums.AcpBurstSynchronizationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_burst_synchronization_type(self, selector_string, value):
        r"""Sets the type of synchronization used for detecting the start of the EDR packet in the adjacent channel power
        (ACP) measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Preamble**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Preamble (1)  | Specifies that the measurement uses the preamble field bits to detect the start of the packet.                           |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
        |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.         |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpBurstSynchronizationType, int):
                Specifies the type of synchronization used for detecting the start of the EDR packet in the adjacent channel power
                (ACP) measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpBurstSynchronizationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_BURST_SYNCHRONIZATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the ACP Averaging Count attribute as the number of acquisitions over which the ACP measurement is   |
        |              | averaged.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpAveragingEnabled):
                Specifies whether to enable averaging for the ACP measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_ENABLED.value
            )
            attr_val = enums.AcpAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the ACP measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the ACP Averaging Count attribute as the number of acquisitions over which the ACP measurement is   |
        |              | averaged.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.AcpAveragingEnabled, int):
                Specifies whether to enable averaging for the ACP measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.AcpAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

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
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_AVERAGING_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable all traces for the adjacent channel power (ACP) measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable all traces for the adjacent channel power (ACP) measurements.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable all traces for the adjacent channel power (ACP) measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable all traces for the adjacent channel power (ACP) measurements.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for adjacent channel power (ACP) measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size, system resources, data
        availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the maximum number of threads used for parallelism for adjacent channel power (ACP) measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for adjacent channel power (ACP) measurement.

        The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
        be used in calculations. The actual number of threads used depends on the problem size, system resources, data
        availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of threads used for parallelism for adjacent channel power (ACP) measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.ACP_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        r"""Configures averaging for the adjacent channel power (ACP) measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.AcpAveragingEnabled, int):
                This parameter specifies whether to enable averaging for the ACP measurement. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses the Averaging Count parameter as the number of acquisitions over which the ACP measurement is       |
                |              | averaged.                                                                                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            averaging_count (int):
                This parameter specifies the number of acquisitions used for averaging when you set the **Averaging Enabled** parameter
                to **True**. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            averaging_enabled = (
                averaging_enabled.value
                if type(averaging_enabled) is enums.AcpAveragingEnabled
                else averaging_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_burst_synchronization_type(self, selector_string, burst_synchronization_type):
        r"""Configures the type of synchronization used for detecting the start of the packet in the adjacent channel power (ACP)
        measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            burst_synchronization_type (enums.AcpBurstSynchronizationType, int):
                This parameter specifies the type of synchronization used for detecting the start of packet in the measurement. The
                default value is **Preamble**.

                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (value)  | Description                                                                                                              |
                +===============+==========================================================================================================================+
                | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | Preamble (1)  | Specifies that the measurement uses the preamble field bits to detect the start of the packet.                           |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
                |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the                                   |
                |               | :py:attr:`~nirfmxbluetooth.attributes.AttributeID.BD_ADDRESS_LAP` attribute.                                             |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            burst_synchronization_type = (
                burst_synchronization_type.value
                if type(burst_synchronization_type) is enums.AcpBurstSynchronizationType
                else burst_synchronization_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_burst_synchronization_type(
                updated_selector_string, burst_synchronization_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_offsets(self, selector_string, number_of_offsets):
        r"""Configures the number of offsets for the adjacent channel power (ACP) measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            number_of_offsets (int):
                This parameter specifies the number of offset channels used on either side of the reference channel for the ACP
                measurement when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
                **Symmetric**. This parameter returns the actual number of offsets used in the ACP measurement when you set the ACP
                Offset Channel Mode attribute to **In-band**. The default value is 5.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_number_of_offsets(
                updated_selector_string, number_of_offsets
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_offset_channel_mode(self, selector_string, offset_channel_mode):
        r"""Configures the offset channels used for the adjacent channel power (ACP) measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            offset_channel_mode (enums.AcpOffsetChannelMode, int):
                This parameter specifies which offset channels are used for the measurement. The default value is **Symmetric**.

                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)  | Description                                                                                                              |
                +===============+==========================================================================================================================+
                | Symmetric (0) | Specifies that the offset channels are symmetrically located around the reference channel. The number of offsets on      |
                |               | either side of the reference channel is specified by the ACP Num Offsets attribute. In symmetric mode, the Center        |
                |               | Frequency attribute specifies the frequency of the reference channel, expressed in Hz.                                   |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+
                | In-band (1)   | Specifies that the measurement is performed over all the channels as specified by the standard. For BR and EDR packets,  |
                |               | 79 channels starting from 2.402GHz to 2.48GHz are used for the measurement. For LE packets, 81 channels starting from    |
                |               | 2.401GHz to 2.481GHz are used for the measurement. In In-band mode, the Center Frequency attribute specifies the         |
                |               | frequency of acquisition which must be equal to 2.441GHz. Configure the Channel Number attribute to specify the          |
                |               | frequency of the reference channel.                                                                                      |
                +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            offset_channel_mode = (
                offset_channel_mode.value
                if type(offset_channel_mode) is enums.AcpOffsetChannelMode
                else offset_channel_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.acp_configure_offset_channel_mode(
                updated_selector_string, offset_channel_mode
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
