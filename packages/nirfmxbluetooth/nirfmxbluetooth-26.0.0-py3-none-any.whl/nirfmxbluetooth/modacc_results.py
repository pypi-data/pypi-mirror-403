"""Provides methods to fetch and read the ModAcc measurement results."""

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


class ModAccResults(object):
    """Provides methods to fetch and read the ModAcc measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the ModAcc measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_df1avg_mean(self, selector_string):
        r"""Gets the df1avg value computed on the signal.  When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the df1avg results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df1avg value computed on the signal.  When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the df1avg results computed for each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF1AVG_MEAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_df1avg_maximum(self, selector_string):
        r"""Gets the df1avg value computed on the signal. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
        maximum of the df1avg results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df1avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                maximum of the df1avg results computed for each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF1AVG_MAXIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_df1avg_minimum(self, selector_string):
        r"""Gets the df1avg value computed on the signal. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
        minimum of the df1avg results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df1avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                minimum of the df1avg results computed for each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF1AVG_MINIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_df1max_maximum(self, selector_string):
        r"""Gets the peak df1max value computed on the signal. The measurement computes df1max deviation values on a packet and
        reports the peak value. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
        attribute to **True**, it returns the maximum of the peak df1max results computed for each averaging count. This value
        is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak df1max value computed on the signal. The measurement computes df1max deviation values on a packet and
                reports the peak value. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
                attribute to **True**, it returns the maximum of the peak df1max results computed for each averaging count. This value
                is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_PEAK_DF1MAX_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_minimum_df1max_minimum(self, selector_string):
        r"""Gets the minimum df1max value computed on the signal. The measurement computes df1max deviation values on a packet
        and reports the minimum value. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
        minimum of the Min df1max results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the minimum df1max value computed on the signal. The measurement computes df1max deviation values on a packet
                and reports the minimum value. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                minimum of the Min df1max results computed for each averaging count. This value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_MINIMUM_DF1MAX_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_percentage_of_symbols_above_df1max_threshold(self, selector_string):
        r"""Gets the percentage of symbols with df1max values that are greater than the df1max threshold defined by the
        standard. This result is valid only for the LE packet with a data rate of 125 Kbps. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it computes this
        result using the df1max values from all averaging counts. This value expressed as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the percentage of symbols with df1max values that are greater than the df1max threshold defined by the
                standard. This result is valid only for the LE packet with a data rate of 125 Kbps. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it computes this
                result using the df1max values from all averaging counts. This value expressed as a percentage.

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
                attributes.AttributeID.MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_ABOVE_DF1MAX_THRESHOLD.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_df2avg_mean(self, selector_string):
        r"""Gets the df2avg value computed on the signal. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the df2avg results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df2avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the df2avg results computed for each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF2AVG_MEAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_df2avg_maximum(self, selector_string):
        r"""Gets the df2avg value computed on the signal. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
        maximum of the df2avg results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df2avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                maximum of the df2avg results computed for each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF2AVG_MAXIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_df2avg_minimum(self, selector_string):
        r"""Gets the df2avg value computed on the signal. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
        minimum of the df2avg results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df2avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                minimum of the df2avg results computed for each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF2AVG_MINIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_df2max_maximum(self, selector_string):
        r"""Gets the peak df2max value computed on the signal. The measurement computes df2max deviation values on a packet and
        reports the peak value. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
        attribute to **True**, it returns the maximum of the peak df2max results computed for each averaging count. This value
        is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak df2max value computed on the signal. The measurement computes df2max deviation values on a packet and
                reports the peak value. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
                attribute to **True**, it returns the maximum of the peak df2max results computed for each averaging count. This value
                is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_PEAK_DF2MAX_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_minimum_df2max_minimum(self, selector_string):
        r"""Gets the minimum df2max value computed on the signal. The measurement computes df2max deviation values on a packet
        and reports the minimum value. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
        minimum of the Min df2max results computed for each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the minimum df2max value computed on the signal. The measurement computes df2max deviation values on a packet
                and reports the minimum value. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                minimum of the Min df2max results computed for each averaging count. This value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_MINIMUM_DF2MAX_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_percentage_of_symbols_above_df2max_threshold(self, selector_string):
        r"""Gets the percentage of symbols with df2max values that are greater than the df2max threshold defined by the
        standard. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
        **True**, it computes this result using the df2max values from all averaging counts. This value is expressed as a
        percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the percentage of symbols with df2max values that are greater than the df2max threshold defined by the
                standard. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
                **True**, it computes this result using the df2max values from all averaging counts. This value is expressed as a
                percentage.

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
                attributes.AttributeID.MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_ABOVE_DF2MAX_THRESHOLD.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_df3avg_mean(self, selector_string):
        r"""Gets the df3avg value computed on the signal. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the df3avg results computed for each averaging count. This value is expressed in Hz. This result is valid only for
        LE-CS packet with data rate 2 Mbps and when bandwidth bit period product is set to 2.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the df3avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the df3avg results computed for each averaging count. This value is expressed in Hz. This result is valid only for
                LE-CS packet with data rate 2 Mbps and when bandwidth bit period product is set to 2.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_DF3AVG_MEAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_percentage_of_symbols_above_df4avg_threshold(self, selector_string):
        r"""Gets the percentage of symbols with df4avg values that are greater than the df4avg threshold defined by the
        standard. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
        **True**, it computes this result using the df4avg values from all averaging counts. This value is expressed as a
        percentage. This result is valid only for LE-CS packet with data rate 2 Mbps and when bandwidth bit period product is
        set to 2.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `df1 and df2
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/df1-and-df2.html>`_ concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the percentage of symbols with df4avg values that are greater than the df4avg threshold defined by the
                standard. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
                **True**, it computes this result using the df4avg values from all averaging counts. This value is expressed as a
                percentage. This result is valid only for LE-CS packet with data rate 2 Mbps and when bandwidth bit period product is
                set to 2.

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
                attributes.AttributeID.MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_ABOVE_DF4AVG_THRESHOLD.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_br_initial_frequency_error_maximum(self, selector_string):
        r"""Gets the initial frequency error value computed on the preamble portion of the BR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute initial frequency error values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the initial frequency error value computed on the preamble portion of the BR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute initial frequency error values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_BR_INITIAL_FREQUENCY_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_br_peak_frequency_drift_maximum(self, selector_string):
        r"""Gets the peak frequency drift value computed on the BR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute peak frequency drift values computed for each averaging count. This value
        is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak frequency drift value computed on the BR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute peak frequency drift values computed for each averaging count. This value
                is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_BR_PEAK_FREQUENCY_DRIFT_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_br_peak_frequency_drift_rate_maximum(self, selector_string):
        r"""Gets the peak frequency drift rate value computed on the BR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute peak frequency drift rate values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak frequency drift rate value computed on the BR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute peak frequency drift rate values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_BR_PEAK_FREQUENCY_DRIFT_RATE_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_edr_header_frequency_error_wi_maximum(self, selector_string):
        r"""Gets the frequency error value computed on the header of the EDR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute header frequency error values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency error value computed on the header of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute header frequency error values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_EDR_HEADER_FREQUENCY_ERROR_WI_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_edr_peak_frequency_error_wi_plus_w0_maximum(self, selector_string):
        r"""Gets the peak frequency error value computed on the EDR portion of the EDR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute peak frequency error values computed for each averaging count. This value
        is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak frequency error value computed on the EDR portion of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute peak frequency error values computed for each averaging count. This value
                is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_EDR_PEAK_FREQUENCY_ERROR_WI_PLUS_W0_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_edr_peak_frequency_error_w0_maximum(self, selector_string):
        r"""Gets the peak frequency error value computed on the EDR portion of the EDR packet, relative to the header frequency
        error. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
        **True**, it returns the value corresponding to the maximum absolute of the peak frequency error values computed for
        each averaging count. This value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak frequency error value computed on the EDR portion of the EDR packet, relative to the header frequency
                error. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
                **True**, it returns the value corresponding to the maximum absolute of the peak frequency error values computed for
                each averaging count. This value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_EDR_PEAK_FREQUENCY_ERROR_W0_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_initial_frequency_error_maximum(self, selector_string):
        r"""Gets the initial frequency error value computed on the preamble portion of the LE or LE-CS packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
        corresponding to the maximum of the absolute initial frequency error values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the initial frequency error value computed on the preamble portion of the LE or LE-CS packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
                corresponding to the maximum of the absolute initial frequency error values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_LE_INITIAL_FREQUENCY_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_peak_frequency_error_maximum(self, selector_string):
        r"""When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Disabled**,
        it returns the peak frequency error value computed on the preamble and payload portion of the LE or LE-CS packet. When
        you set the Direction Finding Mode attribute to **Angle of Arrival**, it returns the peak frequency error value
        computed on the Constant tone extension field of the LE packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of absolute the peak frequency error values computed for each averaging count. This value
        is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Disabled**,
                it returns the peak frequency error value computed on the preamble and payload portion of the LE or LE-CS packet. When
                you set the Direction Finding Mode attribute to **Angle of Arrival**, it returns the peak frequency error value
                computed on the Constant tone extension field of the LE packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of absolute the peak frequency error values computed for each averaging count. This value
                is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_LE_PEAK_FREQUENCY_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_initial_frequency_drift_maximum(self, selector_string):
        r"""Gets the initial frequency drift value computed on the LE packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute initial frequency drift values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the initial frequency drift value computed on the LE packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute initial frequency drift values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_LE_INITIAL_FREQUENCY_DRIFT_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_peak_frequency_drift_maximum(self, selector_string):
        r"""Gets the peak frequency drift value computed on the LE packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute peak frequency drift values computed for each averaging count. This value
        is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak frequency drift value computed on the LE packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute peak frequency drift values computed for each averaging count. This value
                is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_LE_PEAK_FREQUENCY_DRIFT_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_peak_frequency_drift_rate_maximum(self, selector_string):
        r"""Gets the peak frequency drift rate value computed on the LE packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
        corresponding to the maximum of the absolute peak frequency drift rate values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak frequency drift rate value computed on the LE packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of the absolute peak frequency drift rate values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_LE_PEAK_FREQUENCY_DRIFT_RATE_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_preamble_frequency_error_w0_maximum(self, selector_string):
        r"""Gets the frequency error value computed on the preamble portion of the LE-HDT packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
        corresponding to the maximum of the absolute preamble frequency error values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency error value computed on the preamble portion of the LE-HDT packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
                corresponding to the maximum of the absolute preamble frequency error values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_PREAMBLE_FREQUENCY_ERROR_W0_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_payload_frequency_error_w1_maximum(self, selector_string):
        r"""Gets the frequency error value computed on the payload portion of the LE-HDT packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
        corresponding to the maximum of the absolute payload frequency error values computed for each averaging count. This
        value is expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency error value computed on the payload portion of the LE-HDT packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
                corresponding to the maximum of the absolute payload frequency error values computed for each averaging count. This
                value is expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_PAYLOAD_FREQUENCY_ERROR_W1_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_frequency_error_w0_plus_w1_maximum(self, selector_string):
        r"""Gets the total frequency error  for the LE-HDT packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
        corresponding to the maximum of the absolute frequency error values computed for each averaging count. This value is
        expressed in Hz.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the `Frequency Error Measurement
        <https://www.ni.com/docs/en-US/bundle/rfmx-for-bluetooth-test/page/frequency-error-measurement-basic-rate.html>`_
        concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the total frequency error  for the LE-HDT packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
                corresponding to the maximum of the absolute frequency error values computed for each averaging count. This value is
                expressed in Hz.

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
                attributes.AttributeID.MODACC_RESULTS_FREQUENCY_ERROR_W0_PLUS_W1_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_rms_devm_maximum(self, selector_string):
        r"""Gets the peak of the RMS differential EVM (DEVM) values computed on each 50us block of the EDR portion of the EDR
        packet. When you set :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,
        it returns the maximum of the peak RMS differential EVM (DEVM) values computed for each averaging count. This value is
        expressed as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the EDR Differential EVM concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak of the RMS differential EVM (DEVM) values computed on each 50us block of the EDR portion of the EDR
                packet. When you set :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,
                it returns the maximum of the peak RMS differential EVM (DEVM) values computed for each averaging count. This value is
                expressed as a percentage.

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
                attributes.AttributeID.MODACC_RESULTS_PEAK_RMS_DEVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rms_devm_mean(self, selector_string):
        r"""Gets the RMS differential EVM (DEVM) value computed on the EDR portion of the EDR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the RMS differential EVM (DEVM) values computed for each averaging count. This value is expressed as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.
        Refer to the EDR Differential EVM concept topic for more details.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS differential EVM (DEVM) value computed on the EDR portion of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the RMS differential EVM (DEVM) values computed for each averaging count. This value is expressed as a percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_RMS_DEVM_MEAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_devm_maximum(self, selector_string):
        r"""Gets the peak of the differential EVM (DEVM) values computed on symbols in the EDR portion of the EDR packet. When
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
        returns the maximum of the peak symbol differential EVM (DEVM) values computed for each averaging count. This value is
        expressed as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak of the differential EVM (DEVM) values computed on symbols in the EDR portion of the EDR packet. When
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
                returns the maximum of the peak symbol differential EVM (DEVM) values computed for each averaging count. This value is
                expressed as a percentage.

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
                attributes.AttributeID.MODACC_RESULTS_PEAK_DEVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_99_percent_devm(self, selector_string):
        r"""Gets the 99th percentile of the differential EVM (DEVM) values computed on symbols of the EDR portion of all
        measured EDR packets. This value is expressed as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the 99th percentile of the differential EVM (DEVM) values computed on symbols of the EDR portion of all
                measured EDR packets. This value is expressed as a percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.MODACC_RESULTS_99_PERCENT_DEVM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_percentage_of_symbols_below_99_percent_devm_limit(self, selector_string):
        r"""Gets the percentage of symbols in the EDR portion of all the measured EDR packets with differential EVM (DEVM) less
        than or equal to 99% DEVM threshold as defined in section 4.5.11 of the *Bluetooth Test Specification RF.TS.p33.*. When
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
        computes this result using the symbol DEVM values from all averaging counts. This value is expressed as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the percentage of symbols in the EDR portion of all the measured EDR packets with differential EVM (DEVM) less
                than or equal to 99% DEVM threshold as defined in section 4.5.11 of the *Bluetooth Test Specification RF.TS.p33.*. When
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
                computes this result using the symbol DEVM values from all averaging counts. This value is expressed as a percentage.

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
                attributes.AttributeID.MODACC_RESULTS_PERCENTAGE_OF_SYMBOLS_BELOW_99_PERCENT_DEVM_LIMIT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_average_rms_magnitude_error_mean(self, selector_string):
        r"""Gets the average of the RMS magnitude error values computed on each 50 us block of EDR portion of the EDR packet.
        When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
        returns the mean of the average RMS magnitude error values computed for each averaging count. This value is expressed
        as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average of the RMS magnitude error values computed on each 50 us block of EDR portion of the EDR packet.
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
                returns the mean of the average RMS magnitude error values computed for each averaging count. This value is expressed
                as a percentage.

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
                attributes.AttributeID.MODACC_RESULTS_AVERAGE_RMS_MAGNITUDE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_rms_magnitude_error_maximum(self, selector_string):
        r"""Gets the peak of the RMS magnitude error values computed on each 50 us block of EDR portion of the EDR packet. When
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,  it
        returns the maximum of the peak RMS Magnitude error values computed for each averaging count. This value is expressed
        as a percentage.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak of the RMS magnitude error values computed on each 50 us block of EDR portion of the EDR packet. When
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,  it
                returns the maximum of the peak RMS Magnitude error values computed for each averaging count. This value is expressed
                as a percentage.

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
                attributes.AttributeID.MODACC_RESULTS_PEAK_RMS_MAGNITUDE_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_average_rms_phase_error_mean(self, selector_string):
        r"""Return the average of the RMS phase error values computed on each 50 us block of EDR portion of the EDR packet. When
        you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
        returns the mean of the average RMS phase error values computed for each averaging count. This value is expressed in
        degrees.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Return the average of the RMS phase error values computed on each 50 us block of EDR portion of the EDR packet. When
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
                returns the mean of the average RMS phase error values computed for each averaging count. This value is expressed in
                degrees.

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
                attributes.AttributeID.MODACC_RESULTS_AVERAGE_RMS_PHASE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_rms_phase_error_maximum(self, selector_string):
        r"""Return the peak of the RMS phase error values computed on each 50 us block of EDR portion of the EDR packet. When you
        set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns
        the maximum of the peak RMS phase error values computed for each averaging count. This value is expressed in degrees.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Return the peak of the RMS phase error values computed on each 50 us block of EDR portion of the EDR packet. When you
                set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns
                the maximum of the peak RMS phase error values computed for each averaging count. This value is expressed in degrees.

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
                attributes.AttributeID.MODACC_RESULTS_PEAK_RMS_PHASE_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_preamble_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM value computed on the preamble portion of the LE-HDT packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid only for
        LE-HDT packet.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM value computed on the preamble portion of the LE-HDT packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid only for
                LE-HDT packet.

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
                attributes.AttributeID.MODACC_RESULTS_PREAMBLE_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_control_header_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM value computed on the control header portion of the LE-HDT packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid only for
        LE-HDT packet.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM value computed on the control header portion of the LE-HDT packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid only for
                LE-HDT packet.

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
                attributes.AttributeID.MODACC_RESULTS_CONTROL_HEADER_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_payload_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM value computed on the payload portion including the payload header of the LE-HDT packet. When you
        set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns
        the mean of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid
        only for LE-HDT packet.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM value computed on the payload portion including the payload header of the LE-HDT packet. When you
                set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns
                the mean of the RMS EVM values computed for each averaging count. This value is expressed in dB. This result is valid
                only for LE-HDT packet.

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
                attributes.AttributeID.MODACC_RESULTS_PAYLOAD_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_origin_offset_mean(self, selector_string):
        r"""Gets the I/Q origin offset estimated over the EDR portion of the EDR packets and preamble portion of the LE-HDT
        packets. This value is expressed in dB. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the I/Q origin offset values computed for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q origin offset estimated over the EDR portion of the EDR packets and preamble portion of the LE-HDT
                packets. This value is expressed in dB. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the I/Q origin offset values computed for each averaging count.

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
                attributes.AttributeID.MODACC_RESULTS_IQ_ORIGIN_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_mean(self, selector_string):
        r"""Gets the IQ gain imbalance estimated over preamble portion of the LE-HDT packets. This value is expressed in dB.
        When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
        returns the mean of the IQ gain imbalance values computed for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the IQ gain imbalance estimated over preamble portion of the LE-HDT packets. This value is expressed in dB.
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
                returns the mean of the IQ gain imbalance values computed for each averaging count.

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
                attributes.AttributeID.MODACC_RESULTS_IQ_GAIN_IMBALANCE_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_quadrature_error_mean(self, selector_string):
        r"""Gets the quadrature error estimated over preamble portion of the LE-HDT packets. This value is expressed in degree.
        When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
        returns the mean of the quadrature error values computed for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the quadrature error estimated over preamble portion of the LE-HDT packets. This value is expressed in degree.
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it
                returns the mean of the quadrature error values computed for each averaging count.

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
                attributes.AttributeID.MODACC_RESULTS_QUADRATURE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_clock_drift_mean(self, selector_string):
        r"""Gets the clock drift estimated over the LE-CS packet. This value is expressed in ppm. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the clock drift values computed for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the clock drift estimated over the LE-CS packet. This value is expressed in ppm. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the clock drift values computed for each averaging count.

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
                attributes.AttributeID.MODACC_RESULTS_CLOCK_DRIFT_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_preamble_start_time_mean(self, selector_string):
        r"""Gets the start time of the preamble of LE-CS packet. This value is expressed in seconds. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
        of the preamble start time values computed for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the start time of the preamble of LE-CS packet. This value is expressed in seconds. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the preamble start time values computed for each averaging count.

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
                attributes.AttributeID.MODACC_RESULTS_PREAMBLE_START_TIME_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_fractional_time_offset_mean(self, selector_string):
        r"""Gets the fractional time offset value computed on the sounding sequence portion of the LE CS Packet. This value is
        expressed in seconds. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
        attribute to **True**, it returns the mean of the fractional time offset values for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the fractional time offset value computed on the sounding sequence portion of the LE CS Packet. This value is
                expressed in seconds. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED`
                attribute to **True**, it returns the mean of the fractional time offset values for each averaging count.

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
                attributes.AttributeID.MODACC_RESULTS_FRACTIONAL_TIME_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_constellation_trace(self, selector_string, timeout, constellation):
        r"""Fetches the demodulated symbols from the enhanced data rate (EDR) portion of the EDR packet. This method is valid only
        for EDR packets.

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

            constellation (numpy.complex64):
                This parameter returns the array of demodulated symbols from over the EDR portion of the EDR packet.

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
            error_code = self._interpreter.modacc_fetch_constellation_trace(
                updated_selector_string, timeout, constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_cs_detrended_phase_trace(self, selector_string, timeout, cs_detrended_phase):
        r"""Fetches the zero-mean Detrended Phase (deg) versus time trace. This method is valid only for low energy CS (LE-CS)
        packets.

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

            cs_detrended_phase (numpy.float32):
                This parameter returns the array of phase values computed for each samples within CS Tone. This value is expressed in
                degrees.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start time. The value is expressed in seconds.

            dx (float):
                This parameter returns the sample duration. The value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_cs_detrended_phase_trace(
                updated_selector_string, timeout, cs_detrended_phase
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_cs_tone_trace(self, selector_string, timeout, cs_tone_amplitude, cs_tone_phase):
        r"""Fetches the CS Tone Amplitude (dBm) versus time and CS Tone Phase (deg) versus time traces. This method is valid only
        for low energy CS (LE-CS) packets.

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

            cs_tone_amplitude (numpy.float32):
                This parameter returns the array of amplitude values computed for each samples within CS Tone. The values are expressed
                in dBm.

            cs_tone_phase (numpy.float32):
                This parameter returns the array of amplitude values computed for each samples within CS Tone. The values are expressed
                in dBm.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start time. The value is expressed in seconds.

            dx (float):
                This parameter returns the sample duration. The value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_cs_tone_trace(
                updated_selector_string, timeout, cs_tone_amplitude, cs_tone_phase
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_demodulated_bit_trace(self, selector_string, timeout):
        r"""Fetches the ModAcc demodulated bit trace.

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
            Tuple (demodulated_bits, error_code):

            demodulated_bits (int):
                This parameter returns an array of demodulated bits of the packet.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            demodulated_bits, error_code = self._interpreter.modacc_fetch_demodulated_bit_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return demodulated_bits, error_code

    @_raise_if_disposed
    def fetch_devm_per_symbol_trace(self, selector_string, timeout):
        r"""Fetches the DEVM values for symbols from the enhanced data rate (EDR) portion of the EDR packet. This method is valid
        only for EDR packets.

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
            Tuple (devm_per_symbol, error_code):

            devm_per_symbol (float):
                This parameter returns the array of DEVM values computed over the symbols in the EDR portion of EDR packet. This value
                is expressed in percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            devm_per_symbol, error_code = self._interpreter.modacc_fetch_devm_per_symbol_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return devm_per_symbol, error_code

    @_raise_if_disposed
    def fetch_evm_per_symbol_trace(self, selector_string, timeout):
        r"""Fetches the EVM values for symbols from the payload portion including the payload header of the LE-HDT packet. This
        method is valid only for LE-HDT packet.

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
            Tuple (evm_per_symbol, error_code):

            evm_per_symbol (float):
                This parameter returns the EVM values for symbols from the payload portion including the payload header of the LE-HDT
                packet. The values are expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            evm_per_symbol, error_code = self._interpreter.modacc_fetch_evm_per_symbol_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return evm_per_symbol, error_code

    @_raise_if_disposed
    def fetch_devm(self, selector_string, timeout):
        r"""Fetches ModAcc differential EVM (DEVM) measurement results. These results are valid only for enhanced data rate (EDR)
        packets.

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
            Tuple (peak_rms_devm_maximum, peak_devm_maximum, ninetynine_percent_devm, error_code):

            peak_rms_devm_maximum (float):
                This parameter returns the peak of the RMS DEVM values computed on each 50us block of the EDR portion of the EDR
                packet. When you set :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**,
                it returns the maximum of the peak RMS DEVM values computed for each averaging count. This value is expressed in
                percentage.

            peak_devm_maximum (float):
                This parameter returns the peak of the DEVM values computed on symbols in the EDR portion of the EDR packet. When you
                set the ModAcc Averaging Enabled attribute to **True**, it returns the maximum of the peak symbol DEVM values computed
                for each averaging count. This value is expressed in percentage.

            ninetynine_percent_devm (float):
                This parameter returns the 99th percentile of the DEVM values computed on symbols of the EDR portion of all measured
                EDR packets. This value is expressed in percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            peak_rms_devm_maximum, peak_devm_maximum, ninetynine_percent_devm, error_code = (
                self._interpreter.modacc_fetch_devm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return peak_rms_devm_maximum, peak_devm_maximum, ninetynine_percent_devm, error_code

    @_raise_if_disposed
    def fetch_devm_magnitude_error(self, selector_string, timeout):
        r"""Fetches ModAcc RMS magnitude error results. These results are valid only for enhanced data rate (EDR) packets.

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
            Tuple (average_rms_magnitude_error_mean, peak_rms_magnitude_error_maximum, error_code):

            average_rms_magnitude_error_mean (float):
                This parameter returns the average of the RMS magnitude error values computed on each 50 us block of EDR portion of the
                EDR packet. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
                **True**, it returns the mean of the average RMS magnitude error values computed for each averaging count. This value
                is expressed as a percentage.

            peak_rms_magnitude_error_maximum (float):
                This parameter returns the peak of the RMS magnitude error values computed on each 50 us block of EDR portion of the
                EDR packet. When you set the ModAcc Averaging Enabled attribute to **True**, it returns the maximum of the peak RMS
                magnitude error values computed for each averaging count. This value is expressed as a percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            average_rms_magnitude_error_mean, peak_rms_magnitude_error_maximum, error_code = (
                self._interpreter.modacc_fetch_devm_magnitude_error(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return average_rms_magnitude_error_mean, peak_rms_magnitude_error_maximum, error_code

    @_raise_if_disposed
    def fetch_devm_phase_error(self, selector_string, timeout):
        r"""Fetches ModAcc RMS phase error results. These results are valid only for enhanced data rate (EDR) packets.

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
            Tuple (average_rms_phase_error_mean, peak_rms_phase_error_maximum, error_code):

            average_rms_phase_error_mean (float):
                This parameter returns the average of the RMS phase error values computed on each 50 us block of EDR portion of the EDR
                packet. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to
                **True**, it returns the mean of the average RMS phase error values computed for each averaging count. This value is
                expressed in degrees.

            peak_rms_phase_error_maximum (float):
                This parameter returns the peak of the RMS phase error values computed on each 50 us block of EDR portion of the EDR
                packet. When you set the ModAcc Averaging Enabled attribute to **True**, it returns the maximum of the peak RMS phase
                error values computed for each averaging count. This value is expressed in degrees.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            average_rms_phase_error_mean, peak_rms_phase_error_maximum, error_code = (
                self._interpreter.modacc_fetch_devm_phase_error(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return average_rms_phase_error_mean, peak_rms_phase_error_maximum, error_code

    @_raise_if_disposed
    def fetch_df1(self, selector_string, timeout):
        r"""Fetches the ModAcc df1 measurement results. These results are valid only for basic rate (BR) and low energy (LE)
        packets.

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
            Tuple (df1avg_maximum, df1avg_minimum, error_code):

            df1avg_maximum (float):
                This parameter returns the df1avg value computed on the signal. This value is expressed in Hz. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                maximum of the df1avg results computed for each averaging count.

            df1avg_minimum (float):
                This parameter returns the df1avg value computed on the signal. This value is expressed in Hz. When you set the ModAcc
                Averaging Enabled attribute to **True**, it returns the minimum of the df1avg results computed for each averaging
                count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            df1avg_maximum, df1avg_minimum, error_code = self._interpreter.modacc_fetch_df1(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return df1avg_maximum, df1avg_minimum, error_code

    @_raise_if_disposed
    def fetch_df1max_trace(self, selector_string, timeout):
        r"""Fetches the df1max versus the time trace. This method is applicable only for basic rate (BR) and low energy (LE)
        packets.

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
            Tuple (time, df1max, error_code):

            time (float):
                This parameter returns the array of time instances at which the df1max values are computed. This value is expressed in
                seconds.

            df1max (float):
                This parameter returns the array of df1max values computed over the packet at each time instance. This value is
                expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            time, df1max, error_code = self._interpreter.modacc_fetch_df1max_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return time, df1max, error_code

    @_raise_if_disposed
    def fetch_df2(self, selector_string, timeout):
        r"""Fetches the ModAcc df2 measurement results. These results are valid only for basic rate (BR) and low energy (LE)
        packets.

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
            Tuple (df2avg_minimum, percentage_of_symbols_above_df2max_threshold, error_code):

            df2avg_minimum (float):
                This parameter returns the df2avg value computed on the signal. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the
                minimum of the df2avg results computed for each averaging count. This value is expressed in Hz.

            percentage_of_symbols_above_df2max_threshold (float):
                This parameter returns the percentage of symbols with df2max values that are greater than the df2max threshold defined
                by the standard. When you set the ModAcc Averaging Enabled attribute to **True**, it computes this result using the
                df2max values from all averaging counts. This value is expressed as a percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            df2avg_minimum, percentage_of_symbols_above_df2max_threshold, error_code = (
                self._interpreter.modacc_fetch_df2(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return df2avg_minimum, percentage_of_symbols_above_df2max_threshold, error_code

    @_raise_if_disposed
    def fetch_df2max_trace(self, selector_string, timeout):
        r"""Fetches the df2max versus the time trace. This method is valid only for basic rate (BR) and low energy (LE) packets.

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
            Tuple (time, df2max, error_code):

            time (float):
                This parameter returns the array of time instances at which the df2max values are computed. This value is expressed in
                seconds.

            df2max (float):
                This parameter returns the array of df2max values computed over the packet at each time instance. This value is
                expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            time, df2max, error_code = self._interpreter.modacc_fetch_df2max_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return time, df2max, error_code

    @_raise_if_disposed
    def fetch_df4avg_trace(self, selector_string, timeout):
        r"""Fetches the df4avg versus the time trace. This method is valid only for LE-CS Packets.

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
            Tuple (time, df4avg, error_code):

            time (float):
                This parameter returns the array of time instances at which the df4avg values are computed. This value is expressed in
                seconds.

            df4avg (float):
                This parameterreturns the array of df4avg values computed over the packet at each time instance. This value is
                expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            time, df4avg, error_code = self._interpreter.modacc_fetch_df4avg_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return time, df4avg, error_code

    @_raise_if_disposed
    def fetch_frequency_error_br(self, selector_string, timeout):
        r"""Fetches the ModAcc frequency error trace for basic rate (BR) packets.

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
            Tuple (initial_frequency_error_maximum, peak_frequency_drift_maximum, peak_frequency_drift_rate_maximum, error_code):

            initial_frequency_error_maximum (float):
                This parameter returns the initial frequency error value computed on the preamble of the BR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns a value
                corresponding to the maximum of absolute initial frequency error values computed for each averaging count. This value
                is expressed in Hz.

            peak_frequency_drift_maximum (float):
                This parameter returns the peak frequency drift value computed on the BR packet. When you set the ModAcc Averaging
                Enabled attribute to **True**, it returns the value corresponding to the maximum of absolute peak frequency drift
                values computed for each averaging count. This value is expressed in Hz.

            peak_frequency_drift_rate_maximum (float):
                This parameter returns the peak frequency drift rate value computed on the BR packet. When you set the ModAcc Averaging
                Enabled attribute to **True**, it returns the value corresponding to the maximum of absolute peak frequency drift rate
                values computed for each averaging count. This value is expressed in Hz.

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
                initial_frequency_error_maximum,
                peak_frequency_drift_maximum,
                peak_frequency_drift_rate_maximum,
                error_code,
            ) = self._interpreter.modacc_fetch_frequency_error_br(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            initial_frequency_error_maximum,
            peak_frequency_drift_maximum,
            peak_frequency_drift_rate_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_frequency_error_edr(self, selector_string, timeout):
        r"""Fetches ModAcc frequency error measurement results for enhanced data rate (EDR) packets.

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
            Tuple (header_frequency_error_wi_maximum, peak_frequency_error_wi_plus_w0_maximum, peak_frequency_error_w0_maximum, error_code):

            header_frequency_error_wi_maximum (float):
                This parameter returns the frequency error value computed on the header of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, it returns the value
                corresponding to the maximum of absolute header frequency error values computed for each averaging count. This value is
                expressed in Hz.

            peak_frequency_error_wi_plus_w0_maximum (float):
                This parameter returns the peak frequency error value computed on the EDR portion of the EDR packet. When you set the
                ModAcc Averaging Enabled attribute to **True**, it returns the value corresponding to the maximum of absolute peak
                frequency error values computed for each averaging count. This value is expressed in Hz.

            peak_frequency_error_w0_maximum (float):
                This parameter returns the peak frequency error value computed on the EDR portion of the EDR packet, relative to the
                header frequency error. When you set the ModAcc Averaging Enabled attribute to **True**, it returns the value
                corresponding to the maximum of absolute peak frequency error values computed for each averaging count. This value is
                expressed in Hz.

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
                header_frequency_error_wi_maximum,
                peak_frequency_error_wi_plus_w0_maximum,
                peak_frequency_error_w0_maximum,
                error_code,
            ) = self._interpreter.modacc_fetch_frequency_error_edr(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            header_frequency_error_wi_maximum,
            peak_frequency_error_wi_plus_w0_maximum,
            peak_frequency_error_w0_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_frequency_error_le(self, selector_string, timeout):
        r"""Fetches ModAcc frequency error measurement results for low energy (LE) or low energy - channel sounding (LE-CS)
        packets.

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
            Tuple (peak_frequency_error_maximum, initial_frequency_drift_maximum, peak_frequency_drift_maximum, peak_frequency_drift_rate_maximum, error_code):

            peak_frequency_error_maximum (float):
                This parameter when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to
                **Disabled**, it returns the peak frequency error value computed on the preamble and payload portion of the LE packet.
                When you set the Direction Finding Mode attribute to **Angle of Arrival**, it returns the peak frequency error value
                computed on the Constant tone extension field of the LE packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.MODACC_AVERAGING_ENABLED` attribute to **True**, , it returns the
                value corresponding to the maximum of absolute peak frequency error values computed for each averaging count. This
                value is expressed in Hz.

            initial_frequency_drift_maximum (float):
                This parameter returns the initial frequency drift value computed on the LE packet. When you set the ModAcc Averaging
                Enabled attribute to **True**, it returns the value corresponding to the maximum of absolute initial frequency drift
                values computed for each averaging count. This value is expressed in Hz.

            peak_frequency_drift_maximum (float):
                This parameter returns the peak frequency drift value computed on the LE packet. When you set the ModAcc Averaging
                Enabled attribute to **True**, it returns the value corresponding to the maximum of absolute peak frequency drift
                values computed for each averaging count. This value is expressed in Hz.

            peak_frequency_drift_rate_maximum (float):
                This parameter returns the peak frequency drift rate value computed on the LE packet. When you set the ModAcc Averaging
                Enabled attribute to **True**, it returns the value corresponding to the maximum of absolute peak frequency drift rate
                values computed for each averaging count. This value is expressed in Hz.

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
                peak_frequency_error_maximum,
                initial_frequency_drift_maximum,
                peak_frequency_drift_maximum,
                peak_frequency_drift_rate_maximum,
                error_code,
            ) = self._interpreter.modacc_fetch_frequency_error_le(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            peak_frequency_error_maximum,
            initial_frequency_drift_maximum,
            peak_frequency_drift_maximum,
            peak_frequency_drift_rate_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_frequency_error_trace_br(self, selector_string, timeout):
        r"""Fetches the ModAcc frequency error trace for basic rate (BR) packets.

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
            Tuple (time, frequency_error, error_code):

            time (float):
                This parameter returns an array of time instances corresponding to the start of the bit blocks at which the frequency
                error values are computed. This value is expressed in seconds.

            frequency_error (float):
                This parameter returns an array of frequency errors computed over the packet. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            time, frequency_error, error_code = (
                self._interpreter.modacc_fetch_frequency_error_trace_br(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return time, frequency_error, error_code

    @_raise_if_disposed
    def fetch_frequency_error_trace_le(self, selector_string, timeout):
        r"""Fetches the ModAcc frequency error trace for low energy (LE) or low energy - channel sounding (LE-CS) packets.

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
            Tuple (time, frequency_error, error_code):

            time (float):
                This parameter returns an array of time instances corresponding to the start of the bit blocks at which the frequency
                error values are computed. This value is expressed in seconds.

            frequency_error (float):
                This parameter returns the array of frequency errors computed over the packet. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            time, frequency_error, error_code = (
                self._interpreter.modacc_fetch_frequency_error_trace_le(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return time, frequency_error, error_code

    @_raise_if_disposed
    def fetch_frequency_error_wi_plus_w0_trace_edr(self, selector_string, timeout):
        r"""Fetches the ModAcc frequency error trace for enhanced data rate (EDR) packets.

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
            Tuple (time, frequency_error_wi_plus_w0, error_code):

            time (float):
                This parameter returns an array of time instances corresponding to the start of the 50us blocks of the EDR portion of
                EDR packet at which the frequency error values are computed. This value is expressed in seconds.

            frequency_error_wi_plus_w0 (float):
                This parameter returns the array of frequency errors wi+w0 computed over the packet. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            time, frequency_error_wi_plus_w0, error_code = (
                self._interpreter.modacc_fetch_frequency_error_wi_plus_w0_trace_edr(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return time, frequency_error_wi_plus_w0, error_code

    @_raise_if_disposed
    def fetch_frequency_trace(self, selector_string, timeout, frequency):
        r"""Fetches the frequency versus time trace. This trace is valid for basic rate (BR), low energy (LE) and low energy -
        channel sounding (LE-CS) packets.

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

            frequency (numpy.float32):
                This parameter returns the frequency at each time instance. This value is expressed in Hz.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start time. This value is expressed in seconds.

            dx (float):
                This parameter returns the sample duration. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.modacc_fetch_frequency_trace(
                updated_selector_string, timeout, frequency
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_rms_devm_trace(self, selector_string, timeout):
        r"""Fetches the RMS DEVM values from each 50us block of EDR portion of EDR packet. This method is valid only for enhanced
        data rate (EDR) packets.

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
            Tuple (rms_devm, error_code):

            rms_devm (float):
                This parameter returns the array of RMS DEVM values computed on each 50us block of the EDR portion of the EDR packet.
                This value is expressed in percentage.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            rms_devm, error_code = self._interpreter.modacc_fetch_rms_devm_trace(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return rms_devm, error_code
