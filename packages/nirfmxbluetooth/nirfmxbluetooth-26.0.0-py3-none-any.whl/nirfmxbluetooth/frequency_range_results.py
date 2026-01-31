"""Provides methods to fetch and read the FrequencyRange measurement results."""

import functools

import nirfmxbluetooth.attributes as attributes
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


class FrequencyRangeResults(object):
    """Provides methods to fetch and read the FrequencyRange measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the FrequencyRange measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_high_frequency(self, selector_string):
        r"""Gets the highest frequency above the center frequency at which the transmit power drops below -30 dBm measured in a
        100 kHz bandwidth. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the highest frequency above the center frequency at which the transmit power drops below -30 dBm measured in a
                100 kHz bandwidth. This value is expressed in Hz.

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
                attributes.AttributeID.FREQUENCY_RANGE_RESULTS_HIGH_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_low_frequency(self, selector_string):
        r"""Gets the lowest frequency below the center frequency at which the transmit power drops below -30 dBm measured in a
        100 kHz bandwidth. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the lowest frequency below the center frequency at which the transmit power drops below -30 dBm measured in a
                100 kHz bandwidth. This value is expressed in Hz.

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
                attributes.AttributeID.FREQUENCY_RANGE_RESULTS_LOW_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_measurement(self, selector_string, timeout):
        r"""Fetches the FrequencyRange measurement results.

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
            Tuple (high_frequency, low_frequency, error_code):

            high_frequency (float):
                This parameter returns the highest frequency above the center frequency at which the transmit power drops below -30 dBm
                measured in a 100 kHz bandwidth. This value is expressed in Hz.

            low_frequency (float):
                This parameter returns the lowest frequency below the center frequency at which the transmit power drops below -30 dBm
                measured in a 100 kHz bandwidth. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            high_frequency, low_frequency, error_code = (
                self._interpreter.frequency_range_fetch_measurement(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return high_frequency, low_frequency, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum):
        r"""Fetches the FrequencyRange spectrum trace.

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
            x0, dx, error_code = self._interpreter.frequency_range_fetch_spectrum(
                updated_selector_string, timeout, spectrum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
