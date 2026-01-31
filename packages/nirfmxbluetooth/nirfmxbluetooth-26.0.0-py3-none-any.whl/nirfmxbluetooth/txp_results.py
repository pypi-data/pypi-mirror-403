"""Provides methods to fetch and read the Txp measurement results."""

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


class TxpResults(object):
    """Provides methods to fetch and read the Txp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Txp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_average_power_mean(self, selector_string):
        r"""Gets the average power computed over the measurement interval. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
        packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
        average power is calculated from beginning of the payload portion. This value is expressed in dBm. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
        the average power results computed for each averaging count.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power computed over the measurement interval. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
                packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
                average power is calculated from beginning of the payload portion. This value is expressed in dBm. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
                the average power results computed for each averaging count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.TXP_RESULTS_AVERAGE_POWER_MEAN.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_average_power_maximum(self, selector_string):
        r"""Gets the average power computed over the measurement interval. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
        packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
        average power is calculated from beginning of the payload portion. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
        of the average power results computed for each averaging count. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power computed over the measurement interval. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
                packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
                average power is calculated from beginning of the payload portion. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
                of the average power results computed for each averaging count. This value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_AVERAGE_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_average_power_minimum(self, selector_string):
        r"""Gets the average power computed over the measurement interval. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
        packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
        average power is calculated from beginning of the payload portion. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the minimum
        of the average power results computed for each averaging count. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power computed over the measurement interval. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
                packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
                average power is calculated from beginning of the payload portion. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the minimum
                of the average power results computed for each averaging count. This value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_AVERAGE_POWER_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_power_maximum(self, selector_string):
        r"""Gets the peak power computed over the measurement interval. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
        packets, it will exclude guard period and all the switching slots for the peak power computation. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
        of the peak power results computed for each averaging count. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power computed over the measurement interval. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
                packets, it will exclude guard period and all the switching slots for the peak power computation. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
                of the peak power results computed for each averaging count. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.TXP_RESULTS_PEAK_POWER_MAXIMUM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_to_average_power_ratio_maximum(self, selector_string):
        r"""Gets the peak to average power ratio computed over the measurement interval. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
        packets, it will exclude guard period and all the switching slots for the peak to average power ratio computation. For
        LE-HDT, PAPR is calculated using peak power calculated over active portion of burst and average power calculated from
        beginning of the payload portion. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
        of the peak to average power ratio results computed for each averaging count. This value is expressed in dB.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak to average power ratio computed over the measurement interval. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
                packets, it will exclude guard period and all the switching slots for the peak to average power ratio computation. For
                LE-HDT, PAPR is calculated using peak power calculated over active portion of burst and average power calculated from
                beginning of the payload portion. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the maximum
                of the peak to average power ratio results computed for each averaging count. This value is expressed in dB.

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
                attributes.AttributeID.TXP_RESULTS_PEAK_TO_AVERAGE_POWER_RATIO_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_edr_gfsk_average_power_mean(self, selector_string):
        r"""Gets the average power of the GFSK portion of the EDR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
        the GFSK average power results computed for each averaging count. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the GFSK portion of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
                the GFSK average power results computed for each averaging count. This value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_EDR_GFSK_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_edr_dpsk_average_power_mean(self, selector_string):
        r"""Gets the average power of the DPSK portion of the EDR packet. When you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
        the DPSK average power results computed for each averaging count. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the DPSK portion of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
                the DPSK average power results computed for each averaging count. This value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_EDR_DPSK_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_edr_dpsk_gfsk_average_power_ratio_mean(self, selector_string):
        r"""Gets the ratio of the average power of the DPSK portion to the average power of the GFSK portion of the EDR packet.
        When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
        returns the mean of the DPSK GFSK average power ratio results computed for each averaging count. This value is
        expressed in dB.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the ratio of the average power of the DPSK portion to the average power of the GFSK portion of the EDR packet.
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
                returns the mean of the DPSK GFSK average power ratio results computed for each averaging count. This value is
                expressed in dB.

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
                attributes.AttributeID.TXP_RESULTS_EDR_DPSK_GFSK_AVERAGE_POWER_RATIO_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_cte_reference_period_average_power_mean(self, selector_string):
        r"""Gets the average power computed over the reference period in the CTE portion of the LE packet. This result is
        applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to
        **Angle of Departure**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED`
        attribute to **True**, it returns the mean of the CTE reference period average power results computed for each
        averaging count. This value is expressed in dBm.

        You do not need to use a selector string to read this result for the default signal and result instance. Refer
        to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power computed over the reference period in the CTE portion of the LE packet. This result is
                applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to
                **Angle of Departure**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED`
                attribute to **True**, it returns the mean of the CTE reference period average power results computed for each
                averaging count. This value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_LE_CTE_REFERENCE_PERIOD_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_cte_reference_period_peak_absolute_power_deviation_maximum(self, selector_string):
        r"""Gets the peak absolute power deviation computed over the reference period in the CTE portion of the LE packet. The
        peak absolute power deviation is the  deviation of peak power with respect to the average power in the reference
        period. This result is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**. When you
        set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the
        maximum of the CTE reference period absolute power deviation results computed for each averaging count. This value is
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
                Returns the peak absolute power deviation computed over the reference period in the CTE portion of the LE packet. The
                peak absolute power deviation is the  deviation of peak power with respect to the average power in the reference
                period. This result is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**. When you
                set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the
                maximum of the CTE reference period absolute power deviation results computed for each averaging count. This value is
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
                attributes.AttributeID.TXP_RESULTS_LE_CTE_REFERENCE_PERIOD_PEAK_ABSOLUTE_POWER_DEVIATION_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_cte_transmit_slot_average_power_mean(self, selector_string):
        r"""Gets the average power computed over each transmit slot in CTE portion of the LE packet. This result is applicable
        only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of
        Departure**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to
        **True**, it returns the mean of the CTE transmit slot average power results computed for each averaging count. This
        value is expressed in dBm.

        Use "slot<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power computed over each transmit slot in CTE portion of the LE packet. This result is applicable
                only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of
                Departure**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to
                **True**, it returns the mean of the CTE transmit slot average power results computed for each averaging count. This
                value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_LE_CTE_TRANSMIT_SLOT_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_cte_transmit_slot_peak_absolute_power_deviation_maximum(self, selector_string):
        r"""Gets the peak absolute power deviation computed over each transmit slot in the CTE portion of the LE packet. The
        peak absolute power deviation is the deviation of peak power in each transmit slot with respect to the average power in
        that transmit slot. This result is applicable only when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**. When you
        set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the
        maximum of the CTE transmit slot absolute power deviation results computed for each averaging count. This value is
        expressed as a percentage.

        Use "slot<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak absolute power deviation computed over each transmit slot in the CTE portion of the LE packet. The
                peak absolute power deviation is the deviation of peak power in each transmit slot with respect to the average power in
                that transmit slot. This result is applicable only when you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**. When you
                set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the
                maximum of the CTE transmit slot absolute power deviation results computed for each averaging count. This value is
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
                attributes.AttributeID.TXP_RESULTS_LE_CTE_TRANSMIT_SLOT_PEAK_ABSOLUTE_POWER_DEVIATION_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_le_cs_phase_measurement_period_average_power_mean(self, selector_string):
        r"""Gets the average power computed over each antenna path during phase measurement period of the LE-CS packet. This
        result is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to
        **LE-CS** and the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any
        value other than **SYNC**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED`
        attribute to **True**, it returns the mean of the phase measurement period average power results computed for each
        averaging count. This value is expressed in dBm.

        Use "slot<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power computed over each antenna path during phase measurement period of the LE-CS packet. This
                result is applicable only when you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.PACKET_TYPE` attribute to
                **LE-CS** and the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.CHANNEL_SOUNDING_PACKET_FORMAT` attribute to any
                value other than **SYNC**. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED`
                attribute to **True**, it returns the mean of the phase measurement period average power results computed for each
                averaging count. This value is expressed in dBm.

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
                attributes.AttributeID.TXP_RESULTS_LE_CS_PHASE_MEASUREMENT_PERIOD_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_edr_powers(self, selector_string, timeout):
        r"""Fetches TXP measurement results for enhanced data rate (EDR) packets.

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
            Tuple (edr_gfsk_average_power_mean, edr_dpsk_average_power_mean, edr_dpsk_gfsk_average_power_ratio_mean, error_code):

            edr_gfsk_average_power_mean (float):
                This parameter returns the average power of the GFSK portion of the EDR packet. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
                the GFSK average power results computed for each averaging count. This value is expressed in dBm.

            edr_dpsk_average_power_mean (float):
                This parameter returns the average power of the DPSK portion of the EDR packet. When you set the TXP Averaging Enabled
                attribute to **True**, it returns the mean of the DPSK average power results computed for each averaging count. This
                value is expressed in dBm.

            edr_dpsk_gfsk_average_power_ratio_mean (float):
                This parameter returns the ratio of the average power of the DPSK portion to the average power of the GFSK portion of
                the EDR packet. When you set the TXP Averaging Enabled attribute to **True**, it returns the mean of the DPSK GFSK
                average power ratio results computed for each averaging count. This value is expressed in dB.

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
                edr_gfsk_average_power_mean,
                edr_dpsk_average_power_mean,
                edr_dpsk_gfsk_average_power_ratio_mean,
                error_code,
            ) = self._interpreter.txp_fetch_edr_powers(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            edr_gfsk_average_power_mean,
            edr_dpsk_average_power_mean,
            edr_dpsk_gfsk_average_power_ratio_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_le_cte_reference_period_powers(self, selector_string, timeout):
        r"""Fetches the transmit power (TXP) measurement results over the reference period of the constant tone extension (CTE)
        portion for low energy (LE) packets when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**.

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
            Tuple (reference_period_average_power_mean, reference_period_peak_absolute_power_deviation_maximum, error_code):

            reference_period_average_power_mean (float):
                This parameter returns the average power computed over the reference period in the CTE portion of the LE packet. When
                you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns
                the mean of the CTE reference period average power results computed for each averaging count. This value is expressed
                in dBm.

            reference_period_peak_absolute_power_deviation_maximum (float):
                This parameter returns the peak absolute power deviation computed over the reference period in the CTE portion of the
                LE packet. The peak absolute power deviation is the  deviation of peak power with respect to the average power in the
                reference period. When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute
                to **True**, it returns the maximum of the CTE reference period absolute power deviation results computed for each
                averaging count. This value is expressed as a percentage.

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
                reference_period_average_power_mean,
                reference_period_peak_absolute_power_deviation_maximum,
                error_code,
            ) = self._interpreter.txp_fetch_le_cte_reference_period_powers(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            reference_period_average_power_mean,
            reference_period_peak_absolute_power_deviation_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_le_cte_transmit_slot_powers_array(self, selector_string, timeout):
        r"""Fetches an array of transmit power (TXP) measurement results over all the transmit slots of constant tone extension
        (CTE) portion for low energy (LE) packets when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**.

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
            Tuple (transmit_slot_average_power_mean, transmit_slot_peak_absolute_power_deviation_maximum, error_code):

            transmit_slot_average_power_mean (float):
                This parameter returns an array of average powers computed over every transmit slot in CTE portion of the LE packet.
                When you set the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it
                returns an array of mean of the CTE transmit slot average power results computed for each averaging count. This value
                is expressed in dBm.

            transmit_slot_peak_absolute_power_deviation_maximum (float):
                This parameter returns an array of peak absolute power deviations computed over every transmit slot in CTE portion of
                the LE packet. The peak absolute power deviation is the  deviation of peak power in each transmit slot with respect to
                the average power in that transmit slot. When you set the **TXPï¿½Averagingï¿½Enabled** attribute to **True**, it
                returns an array of maximum of the CTE transmit slot absolute power deviation results computed for each averaging
                count. This value is expressed as a percentage.

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
                transmit_slot_average_power_mean,
                transmit_slot_peak_absolute_power_deviation_maximum,
                error_code,
            ) = self._interpreter.txp_fetch_le_cte_transmit_slot_powers_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            transmit_slot_average_power_mean,
            transmit_slot_peak_absolute_power_deviation_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_le_cte_transmit_slot_powers(self, selector_string, timeout):
        r"""Fetches the transmit power (TXP) measurement results over each transmit slot of the constant tone extension (CTE)
        portion for low energy (LE) packets when you set the
        :py:attr:`~nirfmxbluetooth.attributes.AttributeID.DIRECTION_FINDING_MODE` attribute to **Angle of Departure**.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and slot number.

                Example:

                "slot0"

                "result::r1/slot0"

                You can use the :py:meth:`build_slot_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. This value is expressed in seconds. Set
                this value to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the
                method waits until the measurement is complete. The default value is 10.

        Returns:
            Tuple (transmit_slot_average_power_mean, transmit_slot_peak_absolute_power_deviation_maximum, error_code):

            transmit_slot_average_power_mean (float):
                This parameter returns the average power computed over each transmit slot in CTE portion of the LE packet. When you set
                the :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean
                of the CTE transmit slot average power results computed for each averaging count. This value is expressed in dBm.

            transmit_slot_peak_absolute_power_deviation_maximum (float):
                This parameter returns the peak absolute power deviation computed over each transmit slot in the CTE portion of the LE
                packet. The peak absolute power deviation is the deviation of peak power in each transmit slot with respect to the
                average power in that transmit slot.  When you set the **TXPï¿½Averagingï¿½Enabled** attribute to **True**, it returns
                the maximum of the CTE transmit slot absolute power deviation results computed for each averaging count. This value is
                expressed as a percentage.

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
                transmit_slot_average_power_mean,
                transmit_slot_peak_absolute_power_deviation_maximum,
                error_code,
            ) = self._interpreter.txp_fetch_le_cte_transmit_slot_powers(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            transmit_slot_average_power_mean,
            transmit_slot_peak_absolute_power_deviation_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_power_trace(self, selector_string, timeout, power):
        r"""Fetches the power versus time trace.

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

            power (numpy.float32):
                This parameter returns the averaged power at each time instance. This value is expressed in dBm.

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
            x0, dx, error_code = self._interpreter.txp_fetch_power_trace(
                updated_selector_string, timeout, power
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_powers(self, selector_string, timeout):
        r"""Fetches TXP measurement results. These results are valid for all packets.

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
            Tuple (average_power_mean, average_power_maximum, average_power_minimum, peak_to_average_power_ratio_maximum, error_code):

            average_power_mean (float):
                This parameter returns the average power computed over the measurement interval. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **Angle of Departure** for LE
                packets, it will exclude guard period and all the switching slots for the average power computation. For LE-HDT,
                average power is calculated from beginning of the payload portion. When you set the
                :py:attr:`~nirfmxbluetooth.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**, it returns the mean of
                the average power results computed for each averaging count. This value is expressed in dBm.

            average_power_maximum (float):
                This parameter returns the average power computed over the measurement interval. When you set the Direction Finding
                Mode attribute to **Angle of Departure** for LE packets, it will exclude guard period and all the switching slots for
                the average power computation. For LE-HDT, average power is calculated from beginning of the payload portion. When you
                set the TXP Averaging Enabled attribute to **True**, it returns the maximum of the average power results computed for
                each averaging count. This value is expressed in dBm.

            average_power_minimum (float):
                This parameter returns the average power computed over the measurement interval. When you set the Direction Finding
                Mode attribute to **Angle of Departure** for LE packets, it will exclude guard period and all the switching slots for
                the average power computation. For LE-HDT, average power is calculated from beginning of the payload portion. When you
                set the TXP Averaging Enabled attribute to **True**, it returns the minimum of the average power results computed for
                each averaging count. This value is expressed in dBm.

            peak_to_average_power_ratio_maximum (float):
                This parameter returns the peak to average power ratio computed over the measurement interval. When you set the
                Direction Finding Mode attribute to **Angle of Departure** for LE packets, it will exclude guard period and all the
                switching slots for the peak to average power ratio computation. For LE-HDT, PAPR is calculated using peak power
                calculated over active portion of burst and average power calculated from beginning of the payload portion. When you
                set the TXP Averaging Enabled attribute to **True**, it returns the maximum of the peak to average power ratio results
                computed for each averaging count. This value is expressed in dB.

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
                average_power_mean,
                average_power_maximum,
                average_power_minimum,
                peak_to_average_power_ratio_maximum,
                error_code,
            ) = self._interpreter.txp_fetch_powers(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            average_power_mean,
            average_power_maximum,
            average_power_minimum,
            peak_to_average_power_ratio_maximum,
            error_code,
        )
