"""Provides methods to fetch and read the PowerRamp measurement results."""

import functools

import nirfmxbluetooth.attributes as attributes
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


class PowerRampResults(object):
    """Provides methods to fetch and read the PowerRamp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the PowerRamp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_rise_time_mean(self, selector_string):
        r"""Rise Time returns the rise time of the acquired signal that is the amount of time taken for the power envelope to rise
        from a level of 10 percent to 90 percent. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**, this parameter
        returns the mean of the rise time computed for each averaging count. This value is expressed in seconds.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Rise Time returns the rise time of the acquired signal that is the amount of time taken for the power envelope to rise
                from a level of 10 percent to 90 percent. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the rise time computed for each averaging count. This value is expressed in seconds.

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
                attributes.AttributeID.POWERRAMP_RESULTS_RISE_TIME_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_fall_time_mean(self, selector_string):
        r"""Fall Time returns the fall time of the acquired signal that is the amount of time taken for the power envelope to fall
        from a level of 90 percent to 10 percent.  When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**,this parameter
        returns the mean of the fall time computed for each averaging countt. This value is expressed in seconds.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Fall Time returns the fall time of the acquired signal that is the amount of time taken for the power envelope to fall
                from a level of 90 percent to 10 percent.  When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**,this parameter
                returns the mean of the fall time computed for each averaging countt. This value is expressed in seconds.

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
                attributes.AttributeID.POWERRAMP_RESULTS_FALL_TIME_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_40db_fall_time_mean(self, selector_string):
        r"""40dB Fall Time returns the fall time of the acquired signal at which transmit power drops 40 dB below average power.
        When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**,
        this parameter returns the mean of the 40dB fall time computed for each averaging count. This value is expressed in
        seconds.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                40dB Fall Time returns the fall time of the acquired signal at which transmit power drops 40 dB below average power.
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**,
                this parameter returns the mean of the 40dB fall time computed for each averaging count. This value is expressed in
                seconds.

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
                attributes.AttributeID.POWERRAMP_RESULTS_40DB_FALL_TIME_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code
