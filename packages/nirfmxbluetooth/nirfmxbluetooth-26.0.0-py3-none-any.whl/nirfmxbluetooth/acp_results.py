"""Provides methods to fetch and read the Acp measurement results."""

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


class AcpResults(object):
    """Provides methods to fetch and read the Acp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Acp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_status(self, selector_string):
        r"""Indicates the overall measurement status based on the measurement limits specified by the standard when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.

        The standard defines two masks, mask with exception and mask without exception. Mask with exception is more
        stringent than mask without exception.

        The mask with exception limits are as follows:

        +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
        | PHY | Data Rate (bps) | Offset 0                                                   | Offset 1                      | Offset 2                      | Offset 3                      | Offset 4                      | Offset (greater than or equal to 5) |
        +=====+=================+============================================================+===============================+===============================+===============================+===============================+=====================================+
        | BR  | NA              | NA                                                         | less than or equal to -20 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm       |
        +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
        | EDR | NA              | less than or equal to (Reference Channel Power (dBm) - 26) | less than or equal to -20 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm | less than or equal to -40 dBm       |
        +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
        | LE  | 1 Mbps          | NA                                                         | less than or equal to -20 dBm | less than or equal to -30 dBm | less than or equal to -30 dBm | less than or equal to -30 dBm | less than or equal to -30 dBm       |
        +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+
        | LE  | 2 Mbps          | NA                                                         | NA                            | NA                            | less than or equal to -20 dBm | less than or equal to -20 dBm | less than or equal to -30 dBm       |
        +-----+-----------------+------------------------------------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------+-------------------------------------+

        The mask without exception limits for all packet type are as follows:

        +-----+-----------------+-------------------------------+-------------------------------------+
        | PHY | Data Rate (bps) | Offset (2) to Offset (4)      | Offset (greater than or equal to 5) |
        +=====+=================+===============================+=====================================+
        | BR  | NA              | less than or equal to -20 dBm | less than or equal to -20 dBm       |
        +-----+-----------------+-------------------------------+-------------------------------------+
        | EDR | NA              | less than or equal to -20 dBm | less than or equal to -20 dBm       |
        +-----+-----------------+-------------------------------+-------------------------------------+
        | LE  | 1 Mbps          | less than or equal to -20 dBm | less than or equal to -20 dBm       |
        +-----+-----------------+-------------------------------+-------------------------------------+
        | LE  | 2 Mbps          | NA                            | less than or equal to -20 dBm       |
        +-----+-----------------+-------------------------------+-------------------------------------+

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)        | Description                                                                                                              |
        +=====================+==========================================================================================================================+
        | Not Applicable (-1) | This attribute returns Not Applicable when you set the ACP Offset Channel Mode attribute to Symmetric.                   |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Fail (0)            | This attribute returns Fail if more than 3 offsets from offset 3 onwards fail the mask with exception or any offset      |
        |                     | channel fails the mask without exception.                                                                                |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Pass (1)            | This attribute returns Pass if all offsets except up to a maximum of 3 from offset 3 onwards do not fail the mask with   |
        |                     | exception and all offset channels do not fail the mask without exception.                                                |
        +---------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.AcpResultsMeasurementStatus):
                Indicates the overall measurement status based on the measurement limits specified by the standard when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.ACP_RESULTS_MEASUREMENT_STATUS.value
            )
            attr_val = enums.AcpResultsMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_reference_channel_power(self, selector_string):
        r"""Gets the measured power of the reference channel. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the measured power of the reference channel. This value is expressed in dBm.

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
                attributes.AttributeID.ACP_RESULTS_REFERENCE_CHANNEL_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_absolute_power(self, selector_string):
        r"""Gets the absolute power measured in the lower offset channel. This value is expressed in dBm.

        Use "offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the absolute power measured in the lower offset channel. This value is expressed in dBm.

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
                attributes.AttributeID.ACP_RESULTS_LOWER_OFFSET_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_relative_power(self, selector_string):
        r"""Gets the relative power in the lower offset channel measured with respect to the reference channel power. This value
        is expressed in dB.

        Use "offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the relative power in the lower offset channel measured with respect to the reference channel power. This value
                is expressed in dB.

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
                attributes.AttributeID.ACP_RESULTS_LOWER_OFFSET_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin(self, selector_string):
        r"""Gets the margin from the limit specified by the mask with exception for lower offsets. This value is expressed in
        dB. Margin is defined as the difference between the offset absolute power and mask with exception. This result is valid
        only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
        **In-band**. This attribute returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

        Use "offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the margin from the limit specified by the mask with exception for lower offsets. This value is expressed in
                dB. Margin is defined as the difference between the offset absolute power and mask with exception. This result is valid
                only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
                **In-band**. This attribute returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

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
                attributes.AttributeID.ACP_RESULTS_LOWER_OFFSET_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_absolute_power(self, selector_string):
        r"""Gets the absolute power measured in the upper offset channel. This value is expressed in dBm.

        Use "offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the absolute power measured in the upper offset channel. This value is expressed in dBm.

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
                attributes.AttributeID.ACP_RESULTS_UPPER_OFFSET_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_relative_power(self, selector_string):
        r"""Gets the relative power in the upper offset channel measured with respect to the reference channel power. This value
        is expressed in dB.

        Use "offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the relative power in the upper offset channel measured with respect to the reference channel power. This value
                is expressed in dB.

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
                attributes.AttributeID.ACP_RESULTS_UPPER_OFFSET_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin(self, selector_string):
        r"""Gets the margin from the limit specified by the mask with exception for upper offsets. This value is expressed in
        dB. Margin is defined as the difference between the offset absolute power and mask with exception. This result is valid
        only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
        **In-band**. This attribute returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

        Use "offset<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the margin from the limit specified by the mask with exception for upper offsets. This value is expressed in
                dB. Margin is defined as the difference between the offset absolute power and mask with exception. This result is valid
                only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to
                **In-band**. This attribute returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

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
                attributes.AttributeID.ACP_RESULTS_UPPER_OFFSET_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_absolute_power_trace(self, selector_string, timeout, absolute_power):
        r"""Fetches the absolute power trace for ACP measurement.

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

            absolute_power (numpy.float32):
                This parameter returns the power measured in the carrier and offset channels. This value is expressed in Hz.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.acp_fetch_absolute_power_trace(
                updated_selector_string, timeout, absolute_power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_mask_trace(
        self, selector_string, timeout, limit_with_exception_mask, limit_without_exception_mask
    ):
        r"""Fetches the limit with exception mask and limit without exception mask traces for ACP measurement. This method returns
        a valid trace only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute
        to **In-band**.

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

            limit_with_exception_mask (numpy.float32):
                This parameter returns the limit with exception mask used for the measurement. This value is expressed in dBm.

            limit_without_exception_mask (numpy.float32):
                This parameter returns the limit with exception mask used for the measurement. This value is expressed in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency, which is the center frequency of the lowest offset. This value is expressed
                in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.acp_fetch_mask_trace(
                updated_selector_string,
                timeout,
                limit_with_exception_mask,
                limit_without_exception_mask,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_measurement_status(self, selector_string, timeout):
        r"""Fetches the overall ACP measurement status based on the measurement limits as defined by the standard if you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-Band**. This method is not
        valid if you set the ACP Offset Channel Mode attribute to **Symmetric**.

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
            Tuple (measurement_status, error_code):

            measurement_status (enums.AcpResultsMeasurementStatus):
                This parameter returns the overall measurement status based on the measurement limits specified by the standard when
                you set the ACP Offset Channel Mode attribute to **In-Band**. Refer to
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_RESULTS_MEASUREMENT_STATUS` attribute for more information about
                measurement status.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            measurement_status, error_code = self._interpreter.acp_fetch_measurement_status(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return measurement_status, error_code

    @_raise_if_disposed
    def fetch_offset_measurement_array(self, selector_string, timeout):
        r"""Fetches the array of absolute powers, relative powers and margins measured in the offset channels.

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
            Tuple (lower_absolute_power, upper_absolute_power, lower_relative_power, upper_relative_power, lower_margin, upper_margin, error_code):

            lower_absolute_power (float):
                This parameter returns the array of absolute power measured in the lower offset channel. This value is expressed in
                dBm.

            upper_absolute_power (float):
                This parameter returns the array of absolute power measured in the upper offset channel. This value is expressed in
                dBm.

            lower_relative_power (float):
                This parameter returns the array of relative power in the lower offset channel measured with respect to the reference
                channel power. This value is expressed in dB.

            upper_relative_power (float):
                This parameter returns array of the relative power in the upper offset channel measured with respect to the reference
                channel power. This value is expressed in dB.

            lower_margin (float):
                This parameter returns the array of margin from the limit specified by the mask with Exception for lower offset
                channel. This value is expressed in dB. Margin is defined as the difference between the Offset Absolute Power and Mask
                with Exception. This parameter is valid only if you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE` attribute to **In-band**. This parameter
                returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

            upper_margin (float):
                This parameter returns the array of the margin from the limit specified by the mask with Exception for upper offset
                channel. This value is expressed in dB. Margin is defined as the difference between the offset absolute power and mask
                with exception. This parameter is valid only if you set the ACP Offset Channel Mode attribute to **In-band**. This
                parameter returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            (
                lower_absolute_power,
                upper_absolute_power,
                lower_relative_power,
                upper_relative_power,
                lower_margin,
                upper_margin,
                error_code,
            ) = self._interpreter.acp_fetch_offset_measurement_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            lower_absolute_power,
            upper_absolute_power,
            lower_relative_power,
            upper_relative_power,
            lower_margin,
            upper_margin,
            error_code,
        )

    @_raise_if_disposed
    def fetch_offset_measurement(self, selector_string, timeout):
        r"""Fetches the absolute powers, relative powers and margins measured in the offset channel.

        Use "offset<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of offset
                number, and the result name.

                Example:

                "offset0"

                "result::r1/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (lower_absolute_power, upper_absolute_power, lower_relative_power, upper_relative_power, lower_margin, upper_margin, error_code):

            lower_absolute_power (float):
                This parameter returns the absolute power measured in the lower offset channel. This value is expressed in dBm.

            upper_absolute_power (float):
                This parameter returns the absolute power measured in the upper offset channel. This value is expressed in dBm.

            lower_relative_power (float):
                This parameter returns the relative power in the lower offset channel measured with respect to the reference channel
                power. This value is expressed in dB.

            upper_relative_power (float):
                This parameter returns the relative power in the upper offset channel measured with respect to the reference channel
                power. This value is expressed in dB.

            lower_margin (float):
                This parameter returns the margin from the limit specified by the mask with exception for lower offsets. This value is
                expressed in dB. Margin is defined as the difference between the offset absolute power and mask with exception. This
                parameter is valid only if you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.ACP_OFFSET_CHANNEL_MODE`
                attribute to **In-band**. This parameter returns NaN if you set the ACP Offset Channel Mode attribute to **Symmetric**.

            upper_margin (float):
                This parameter returns the margin from the limit specified by the mask with exception for upper offsets. This value is
                expressed in dB. Margin is defined as the difference between the offset absolute power and mask with exception. This
                parameter is valid only if you set the ACP Offset Channel Mode attribute to **In-band**. This parameter returns NaN if
                you set the ACP Offset Channel Mode attribute to **Symmetric**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            (
                lower_absolute_power,
                upper_absolute_power,
                lower_relative_power,
                upper_relative_power,
                lower_margin,
                upper_margin,
                error_code,
            ) = self._interpreter.acp_fetch_offset_measurement(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            lower_absolute_power,
            upper_absolute_power,
            lower_relative_power,
            upper_relative_power,
            lower_margin,
            upper_margin,
            error_code,
        )

    @_raise_if_disposed
    def fetch_reference_channel_power(self, selector_string, timeout):
        r"""Returns the measured power of the reference channel.

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
            Tuple (reference_channel_power, error_code):

            reference_channel_power (float):
                This parameter returns the measured power of the reference channel. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            reference_channel_power, error_code = (
                self._interpreter.acp_fetch_reference_channel_power(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return reference_channel_power, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum):
        r"""Fetches the spectrum used for ACP measurement.

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

            spectrum (numpy.float32):
                This parameter returns the averaged power measured at each frequency bin. This value is expressed in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.acp_fetch_spectrum(
                updated_selector_string, timeout, spectrum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
