"""Provides methods to configure the ModAcc measurement."""

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


class ModAccConfiguration(object):
    """Provides methods to configure the ModAcc measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the ModAcc measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the ModAcc measurements. You can use this attribute to determine the modulation quality of
        the bluetooth transmitter.

        You can perform the following sub-measurements when ModAcc measurement is enabled:
        <ul><li>
        DEVM, on EDR packets</li>
        <li>
        df1, on BR and LE packets</li>
        <li>
        df2, on BR and LE packets</li>
        <li>
        Frequency Error, on BR, EDR, LE and LE-CS packets</li></ul>

        The listed sub-measurements are enabled or disabled based on the value of the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_BIT_PATTERN` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable the ModAcc measurements. You can use this attribute to determine the modulation quality of
                the bluetooth transmitter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the ModAcc measurements. You can use this attribute to determine the modulation quality of
        the bluetooth transmitter.

        You can perform the following sub-measurements when ModAcc measurement is enabled:
        <ul><li>
        DEVM, on EDR packets</li>
        <li>
        df1, on BR and LE packets</li>
        <li>
        df2, on BR and LE packets</li>
        <li>
        Frequency Error, on BR, EDR, LE and LE-CS packets</li></ul>

        The listed sub-measurements are enabled or disabled based on the value of the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PAYLOAD_BIT_PATTERN` attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the ModAcc measurements. You can use this attribute to determine the modulation quality of
                the bluetooth transmitter.

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
                attributes.AttributeID.MODACC_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_burst_synchronization_type(self, selector_string):
        r"""Gets the type of synchronization used for detecting the start of packet in ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Preamble**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Preamble (1)  | Specifies that the measurement uses the preamble field to detect the start of the packet.                                |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
        |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.         |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccBurstSynchronizationType):
                Specifies the type of synchronization used for detecting the start of packet in ModAcc measurement.

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
                attributes.AttributeID.MODACC_BURST_SYNCHRONIZATION_TYPE.value,
            )
            attr_val = enums.ModAccBurstSynchronizationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_burst_synchronization_type(self, selector_string, value):
        r"""Sets the type of synchronization used for detecting the start of packet in ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Preamble**.

        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                              |
        +===============+==========================================================================================================================+
        | None (0)      | Specifies that the measurement does not perform synchronization to detect the start of the packet.                       |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Preamble (1)  | Specifies that the measurement uses the preamble field to detect the start of the packet.                                |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+
        | Sync Word (2) | Specifies that the measurement uses sync word for the BR/EDR packets and access address for the LE/LE-CS packets to      |
        |               | detect the start of the packet. For BR /EDR packets, the sync word is derived from the BD Address LAP attribute.         |
        +---------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccBurstSynchronizationType, int):
                Specifies the type of synchronization used for detecting the start of packet in ModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccBurstSynchronizationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_BURST_SYNCHRONIZATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_origin_offset_correction_enabled(self, selector_string):
        r"""Gets whether to enable the I/Q origin offset correction for EDR and LE-HDT packets. If you set this attribute to
        **True**, the DEVM and EVM results are computed after correcting for the I/Q origin offset.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Disables the I/Q origin offset correction for EDR and LE-HDT packets. |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Enables the I/Q origin offset correction for EDR and LE-HDT packets.  |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQOriginOffsetCorrectionEnabled):
                Specifies whether to enable the I/Q origin offset correction for EDR and LE-HDT packets. If you set this attribute to
                **True**, the DEVM and EVM results are computed after correcting for the I/Q origin offset.

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
                attributes.AttributeID.MODACC_IQ_ORIGIN_OFFSET_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQOriginOffsetCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_origin_offset_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable the I/Q origin offset correction for EDR and LE-HDT packets. If you set this attribute to
        **True**, the DEVM and EVM results are computed after correcting for the I/Q origin offset.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Disables the I/Q origin offset correction for EDR and LE-HDT packets. |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Enables the I/Q origin offset correction for EDR and LE-HDT packets.  |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQOriginOffsetCorrectionEnabled, int):
                Specifies whether to enable the I/Q origin offset correction for EDR and LE-HDT packets. If you set this attribute to
                **True**, the DEVM and EVM results are computed after correcting for the I/Q origin offset.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.ModAccIQOriginOffsetCorrectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_ORIGIN_OFFSET_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_mismatch_correction_enabled(self, selector_string):
        r"""Gets whether to enable the IQ mismatch correction for LE- HDT packet. If you set this attribute to **True**, the
        EVM results are computed after correcting for the IQ gain imbalance and quadrature error .

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | Disables the IQ mismatch correction for LE-HDT packets. |
        +--------------+---------------------------------------------------------+
        | True (1)     | Enables the IQ mismatch correction for LE-HDT packets.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccIQMismatchCorrectionEnabled):
                Specifies whether to enable the IQ mismatch correction for LE- HDT packet. If you set this attribute to **True**, the
                EVM results are computed after correcting for the IQ gain imbalance and quadrature error .

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
                attributes.AttributeID.MODACC_IQ_MISMATCH_CORRECTION_ENABLED.value,
            )
            attr_val = enums.ModAccIQMismatchCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_mismatch_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable the IQ mismatch correction for LE- HDT packet. If you set this attribute to **True**, the
        EVM results are computed after correcting for the IQ gain imbalance and quadrature error .

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | Disables the IQ mismatch correction for LE-HDT packets. |
        +--------------+---------------------------------------------------------+
        | True (1)     | Enables the IQ mismatch correction for LE-HDT packets.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccIQMismatchCorrectionEnabled, int):
                Specifies whether to enable the IQ mismatch correction for LE- HDT packet. If you set this attribute to **True**, the
                EVM results are computed after correcting for the IQ gain imbalance and quadrature error .

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccIQMismatchCorrectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_IQ_MISMATCH_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency_tracking_enabled(self, selector_string):
        r"""Gets whether to enable frequency tracking for LE- HDT packet. If you set this attribute to **True**, the Control
        Header EVM, Payload EVM, Payload Frequency Error w1 and Frequency Error w0+w1 results are computed after frequency
        tracking.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------+
        | Name (Value) | Description                                         |
        +==============+=====================================================+
        | False (0)    | Disables the frequency tracking for LE-HDT packets. |
        +--------------+-----------------------------------------------------+
        | True (1)     | Enables the frequency tracking for LE-HDT packets.  |
        +--------------+-----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccFrequencyTrackingEnabled):
                Specifies whether to enable frequency tracking for LE- HDT packet. If you set this attribute to **True**, the Control
                Header EVM, Payload EVM, Payload Frequency Error w1 and Frequency Error w0+w1 results are computed after frequency
                tracking.

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
                attributes.AttributeID.MODACC_FREQUENCY_TRACKING_ENABLED.value,
            )
            attr_val = enums.ModAccFrequencyTrackingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency_tracking_enabled(self, selector_string, value):
        r"""Sets whether to enable frequency tracking for LE- HDT packet. If you set this attribute to **True**, the Control
        Header EVM, Payload EVM, Payload Frequency Error w1 and Frequency Error w0+w1 results are computed after frequency
        tracking.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------+
        | Name (Value) | Description                                         |
        +==============+=====================================================+
        | False (0)    | Disables the frequency tracking for LE-HDT packets. |
        +--------------+-----------------------------------------------------+
        | True (1)     | Enables the frequency tracking for LE-HDT packets.  |
        +--------------+-----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccFrequencyTrackingEnabled, int):
                Specifies whether to enable frequency tracking for LE- HDT packet. If you set this attribute to **True**, the Control
                Header EVM, Payload EVM, Payload Frequency Error w1 and Frequency Error w0+w1 results are computed after frequency
                tracking.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccFrequencyTrackingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_FREQUENCY_TRACKING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the ModAcc measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the ModAcc Averaging Count attribute as the number of acquisitions over which the ModAcc            |
        |              | measurement is averaged.                                                                                                 |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.ModAccAveragingEnabled):
                Specifies whether to enable averaging for the ModAcc measurements.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_ENABLED.value
            )
            attr_val = enums.ModAccAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the ModAcc measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the ModAcc Averaging Count attribute as the number of acquisitions over which the ModAcc            |
        |              | measurement is averaged.                                                                                                 |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.ModAccAveragingEnabled, int):
                Specifies whether to enable averaging for the ModAcc measurements.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.ModAccAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.MODACC_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**.

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
                updated_selector_string, attributes.AttributeID.MODACC_AVERAGING_COUNT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable all the traces computed by ModAcc measurements.

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
                Specifies whether to enable all the traces computed by ModAcc measurements.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.MODACC_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable all the traces computed by ModAcc measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable all the traces computed by ModAcc measurements.

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
                attributes.AttributeID.MODACC_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
        range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
        number of threads used depends on the problem size, system resources, data availability, and other considerations.

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
                Specifies the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
                range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
                number of threads used depends on the problem size, system resources, data availability, and other considerations.

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
                attributes.AttributeID.MODACC_NUMBER_OF_ANALYSIS_THREADS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
        range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
        number of threads used depends on the problem size, system resources, data availability, and other considerations.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of threads used for parallelism for the ModAcc measurement. The number of threads can
                range from 1 to the number of physical cores. The number of threads you set may not be used in calculations. The actual
                number of threads used depends on the problem size, system resources, data availability, and other considerations.

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
                attributes.AttributeID.MODACC_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        r"""Configures averaging for the ModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.ModAccAveragingEnabled, int):
                This parameter specifies whether to enable averaging for the ModAcc measurement. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses the Averaging Count parameter as the number of acquisitions over which the ModAcc measurement is    |
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
                if type(averaging_enabled) is enums.ModAccAveragingEnabled
                else averaging_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_burst_synchronization_type(self, selector_string, burst_synchronization_type):
        r"""Configures the burst synchronization type for ModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            burst_synchronization_type (enums.ModAccBurstSynchronizationType, int):
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
                if type(burst_synchronization_type) is enums.ModAccBurstSynchronizationType
                else burst_synchronization_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.modacc_configure_burst_synchronization_type(
                updated_selector_string, burst_synchronization_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
