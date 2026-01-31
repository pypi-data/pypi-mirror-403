"""Provides methods to configure the TwentydBBandwidth measurement."""

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


class TwentydBBandwidthConfiguration(object):
    """Provides methods to configure the TwentydBBandwidth measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the TwentydBBandwidth measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the 20dBBandwidth measurement specified in section 4.5.5 of the *Bluetooth Test
        Specification RF.TS.p33*. The measurement uses a span of 3 MHz internally. This measurement is valid only for basic
        rate (BR) packets.

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
                Specifies whether to enable the 20dBBandwidth measurement specified in section 4.5.5 of the *Bluetooth Test
                Specification RF.TS.p33*. The measurement uses a span of 3 MHz internally. This measurement is valid only for basic
                rate (BR) packets.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_MEASUREMENT_ENABLED.value,
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the 20dBBandwidth measurement specified in section 4.5.5 of the *Bluetooth Test
        Specification RF.TS.p33*. The measurement uses a span of 3 MHz internally. This measurement is valid only for basic
        rate (BR) packets.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the 20dBBandwidth measurement specified in section 4.5.5 of the *Bluetooth Test
                Specification RF.TS.p33*. The measurement uses a span of 3 MHz internally. This measurement is valid only for basic
                rate (BR) packets.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for the 20dBBandwidth measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The 20dBBandwidth measurement uses the 20dBBandwidth Averaging Count attribute as the number of acquisitions over which  |
        |              | the 20dBBandwidth measurement is averaged.                                                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TwentydBBandwidthAveragingEnabled):
                Specifies whether to enable averaging for the 20dBBandwidth measurement.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED.value,
            )
            attr_val = enums.TwentydBBandwidthAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for the 20dBBandwidth measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The 20dBBandwidth measurement uses the 20dBBandwidth Averaging Count attribute as the number of acquisitions over which  |
        |              | the 20dBBandwidth measurement is averaged.                                                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TwentydBBandwidthAveragingEnabled, int):
                Specifies whether to enable averaging for the 20dBBandwidth measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.TwentydBBandwidthAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_COUNT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_AVERAGING_COUNT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable all the traces for the 20dBBandwidth measurement.

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
                Specifies whether to enable all the traces for the 20dBBandwidth measurement.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_ALL_TRACES_ENABLED.value,
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable all the traces for the 20dBBandwidth measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable all the traces for the 20dBBandwidth measurement.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the 20dB bandwidth measurement.

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
                Specifies the maximum number of threads used for parallelism for the 20dB bandwidth measurement.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_NUMBER_OF_ANALYSIS_THREADS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the 20dB bandwidth measurement.

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
                Specifies the maximum number of threads used for parallelism for the 20dB bandwidth measurement.

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
                attributes.AttributeID.TWENTY_DB_BANDWIDTH_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        r"""Configures averaging for the 20dBBandwidth measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.TwentydBBandwidthAveragingEnabled, int):
                This parameter specifies whether to enable averaging for 20dBBandwidth measurement. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses the Averaging Count parameter as the number of acquisitions over which the 20dBBandwidth            |
                |              | measurement is averaged.                                                                                                 |
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
                if type(averaging_enabled) is enums.TwentydBBandwidthAveragingEnabled
                else averaging_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.twenty_db_bandwidth_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
