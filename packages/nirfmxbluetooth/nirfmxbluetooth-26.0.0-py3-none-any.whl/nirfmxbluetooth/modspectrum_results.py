"""Provides methods to fetch and read the ModSpectrum measurement results."""

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


class ModSpectrumResults(object):
    """Provides methods to fetch and read the ModSpectrum measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the ModSpectrum measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_bandwidth(self, selector_string):
        r"""Gets the 6 dB bandwidth of the received signal. It is computed as the difference between
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_RESULTS_HIGH_FREQUENCY`  and
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_RESULTS_LOW_FREQUENCY` . This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the 6 dB bandwidth of the received signal. It is computed as the difference between
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_RESULTS_HIGH_FREQUENCY`  and
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODSPECTRUM_RESULTS_LOW_FREQUENCY` . This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODSPECTRUM_RESULTS_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_high_frequency(self, selector_string):
        r"""Gets the highest frequency above the center frequency at which the transmit power drops 6dB below the peak power.
        This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the highest frequency above the center frequency at which the transmit power drops 6dB below the peak power.
                This value is expressed in Hz.

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
                attributes.AttributeID.MODSPECTRUM_RESULTS_HIGH_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_low_frequency(self, selector_string):
        r"""Gets the lowest frequency below the center frequency at which the transmit power drops 6 dB below the peak power.
        This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the lowest frequency below the center frequency at which the transmit power drops 6 dB below the peak power.
                This value is expressed in Hz.

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
                attributes.AttributeID.MODSPECTRUM_RESULTS_LOW_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum):
        r"""Fetches the ModSpectrum spectrum trace.

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

            spectrum (numpy.float32):
                This parameterReturns the averaged power measured at each frequency bin. This value is expressed in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameterReturns the start frequency. This value is expressed in Hz.

            dx (float):
                This parameterReturns the frequency bin spacing. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modspectrum_fetch_spectrum(
                updated_selector_string, timeout, spectrum
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
