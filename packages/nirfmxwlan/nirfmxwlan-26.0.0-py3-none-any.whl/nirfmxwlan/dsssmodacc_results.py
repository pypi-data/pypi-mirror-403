"""Provides methods to fetch and read the DsssModAcc measurement results."""

import functools

import nirfmxwlan.attributes as attributes
import nirfmxwlan.enums as enums
import nirfmxwlan.errors as errors
import nirfmxwlan.internal._helper as _helper


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        meas_obj = xs[0]  # parameter 0 is 'self' which is the measurement object
        if meas_obj._signal_obj.is_disposed:
            raise Exception("Cannot access a disposed Wlan signal configuration")
        return f(*xs, **kws)

    return aux


class DsssModAccResults(object):
    """Provides methods to fetch and read the DsssModAcc measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the DsssModAcc measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of the burst. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the RMS EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of the burst. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_evm_802_11_2016_mean(self, selector_string):
        r"""Gets the peak EVM of the burst. This value is expressed as a percentage or in dB.

        This measurement is performed in accordance with section 16.3.7.9 of *IEEE Standard 802.11-2016*.
        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the peak EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PEAK_EVM_802_11_2016_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_evm_802_11_2016_maximum(self, selector_string):
        r"""Gets the peak EVM of the burst. This value is expressed as a percentage or in dB.

        This measurement is performed in accordance with section 16.3.7.9 of *IEEE Standard 802.11-2016*.
        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum value of the peak EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PEAK_EVM_802_11_2016_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_evm_802_11_2007_mean(self, selector_string):
        r"""Gets the peak EVM of the burst. This value is expressed as a percentage or in dB.

        This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11-2007*.
        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the peak EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PEAK_EVM_802_11_2007_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_evm_802_11_2007_maximum(self, selector_string):
        r"""Gets the peak EVM of the burst. This value is expressed as a percentage or in dB.

        This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11-2007*.
        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum value of the peak EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PEAK_EVM_802_11_2007_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_evm_802_11_1999_mean(self, selector_string):
        r"""Gets the peak EVM of the burst. This value is expressed as a percentage or in dB.

        This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11b-1999*.
        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute is set to
        **True**, this result returns the mean of the peak EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PEAK_EVM_802_11_1999_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_peak_evm_802_11_1999_maximum(self, selector_string):
        r"""Gets the peak EVM of the burst. This value is expressed as percentage or in dB.

        This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11b-1999*.
        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum of the peak EVM computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak EVM of the burst. This value is expressed as percentage or in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PEAK_EVM_802_11_1999_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_chips_used(self, selector_string):
        r"""Gets the number of chips used for the DSSSModAcc measurement.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the number of chips used for the DSSSModAcc measurement.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_NUMBER_OF_CHIPS_USED.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_frequency_error_mean(self, selector_string):
        r"""Gets the carrier frequency error of the transmitter. This value is expressed in Hz.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the carrier frequency error computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the carrier frequency error of the transmitter. This value is expressed in Hz.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_FREQUENCY_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_chip_clock_error_mean(self, selector_string):
        r"""Gets the chip clock error of the transmitter. This value is expressed in parts per million (ppm).

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the chip clock error computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the chip clock error of the transmitter. This value is expressed in parts per million (ppm).

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
                attributes.AttributeID.DSSSMODACC_RESULTS_CHIP_CLOCK_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_mean(self, selector_string):
        r"""Gets the I/Q gain imbalance. This value is expressed in dB.

        I/Q gain imbalance is the ratio of the mean amplitude of the in-phase (I) signal to the mean amplitude of the
        quadrature-phase (Q) signal. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
        the mean of the I/Q gain imbalance computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q gain imbalance. This value is expressed in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_IQ_GAIN_IMBALANCE_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_mean(self, selector_string):
        r"""Gets the I/Q quadrature error. This value is expressed in degrees.

        Quadrature error is the deviation in angle from 90 degrees between the in-phase (I) and quadrature-phase (Q)
        signals. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the I/Q quadrature error computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q quadrature error. This value is expressed in degrees.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_IQ_QUADRATURE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_origin_offset_mean(self, selector_string):
        r"""Gets the I/Q origin offset. This value is expressed in dB.

        I/Q origin offset is the ratio of the mean value of the signal to the RMS value of the signal. When you set
        this :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result
        returns the mean of the I/Q origin offset computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q origin offset. This value is expressed in dB.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_IQ_ORIGIN_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rms_magnitude_error_mean(self, selector_string):
        r"""Gets the RMS magnitude error of the received constellation, which is the RMS level of the one minus the magnitude
        error of the received constellation symbols. This value is expressed as a percentage.

        When you set this :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the RMS magnitude error computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS magnitude error of the received constellation, which is the RMS level of the one minus the magnitude
                error of the received constellation symbols. This value is expressed as a percentage.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_RMS_MAGNITUDE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rms_phase_error_mean(self, selector_string):
        r"""Gets the RMS phase error of the received constellation, which is the RMS level of difference between the ideal and
        the actual values of the phase of the received constellation symbols. This value is expressed in degrees.

        When you set this :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the RMS phase error computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS phase error of the received constellation, which is the RMS level of difference between the ideal and
                the actual values of the phase of the received constellation symbols. This value is expressed in degrees.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_RMS_PHASE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_preamble_average_power_mean(self, selector_string):
        r"""Gets the average power of the preamble field of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the average preamble field power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the preamble field of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PREAMBLE_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_preamble_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the preamble field of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum of the peak preamble field power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the preamble field of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PREAMBLE_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_header_average_power_mean(self, selector_string):
        r"""Gets the average power of the header field of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the average header field power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the header field of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_HEADER_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_header_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the header field of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum value of the peak header field power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the header field of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_HEADER_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_data_average_power_mean(self, selector_string):
        r"""Gets the average power of the data field of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the average data field power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the data field of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_DATA_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_data_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the data field of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum value of the peak data field power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the data field of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_DATA_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ppdu_average_power_mean(self, selector_string):
        r"""Gets the average power of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean of the average PPDU power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PPDU_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ppdu_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum value of the peak PPDU power computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the PPDU. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PPDU_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_custom_gate_average_power_mean(self, selector_string):
        r"""Gets the average power of the custom gate. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the mean value of the average custom gate power computed for each averaging count.

        Use "gate<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read the result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the custom gate. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_CUSTOM_GATE_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_custom_gate_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the custom gate. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
        **True**, this result returns the maximum value of the peak custom gate power computed for each averaging count.

        Use "gate<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to query the result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the custom gate. This value is expressed in dBm.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_CUSTOM_GATE_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_data_modulation_format(self, selector_string):
        r"""Gets the data modulation format results of the analyzed waveform.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +-------------------+-----------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                 |
        +===================+=============================================================================+
        | DSSS 1 Mbps (0)   | Indicates that the modulation format is DSSS and the data rate is 1 Mbps.   |
        +-------------------+-----------------------------------------------------------------------------+
        | DSSS 2 Mbps (1)   | Indicates that the modulation format is DSSS and the data rate is 2 Mbps.   |
        +-------------------+-----------------------------------------------------------------------------+
        | CCK 5.5 Mbps (2)  | Indicates that the modulation format is CCK and the data rate is 5.5 Mbps.  |
        +-------------------+-----------------------------------------------------------------------------+
        | CCK 11 Mbps (3)   | Indicates that the modulation format is CCK and the data rate is 11 Mbps.   |
        +-------------------+-----------------------------------------------------------------------------+
        | PBCC 5.5 Mbps (4) | Indicates that the modulation format is PBCC and the data rate is 5.5 Mbps. |
        +-------------------+-----------------------------------------------------------------------------+
        | PBCC 11 Mbps (5)  | Indicates that the modulation format is PBCC and the data rate is 11 Mbps.  |
        +-------------------+-----------------------------------------------------------------------------+
        | PBCC 22 Mbps (6)  | Indicates that the modulation format is PBCC and the data rate is 22 Mbps.  |
        +-------------------+-----------------------------------------------------------------------------+
        | PBCC 33 Mbps (7)  | Indicates that the modulation format is PBCC and the data rate is 33 Mbps.  |
        +-------------------+-----------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccDataModulationFormat):
                Returns the data modulation format results of the analyzed waveform.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_DATA_MODULATION_FORMAT.value,
            )
            attr_val = enums.DsssModAccDataModulationFormat(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_payload_length(self, selector_string):
        r"""Gets the payload length of the acquired burst. This value is expressed in bytes.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the payload length of the acquired burst. This value is expressed in bytes.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PAYLOAD_LENGTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_preamble_type(self, selector_string):
        r"""Gets the detected preamble type of the acquired burst.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+--------------------------------------------------------------+
        | Name (Value) | Description                                                  |
        +==============+==============================================================+
        | Long (0)     | Indicates that the PPDU has a long PHY preamble and header.  |
        +--------------+--------------------------------------------------------------+
        | Short (1)    | Indicates that the PPDU has a short PHY preamble and header. |
        +--------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccPreambleType):
                Returns the detected preamble type of the acquired burst.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PREAMBLE_TYPE.value,
            )
            attr_val = enums.DsssModAccPreambleType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_locked_clocks_bit(self, selector_string):
        r"""Gets the value of the locked clocks bit in the Long PHY SERVICE field.

        A value of 1 indicates that the transmit frequency and the symbol clock are derived from the same oscillator. A
        value of 0 indicates that the transmit frequency and the symbol clock are derived from independent oscillators.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the value of the locked clocks bit in the Long PHY SERVICE field.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_LOCKED_CLOCKS_BIT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_header_crc_status(self, selector_string):
        r"""Gets whether the header cyclic redundancy check (CRC) is successfully passed, as defined in section 16.2.3.7 of
        *IEEE Standard 802.11 2016*.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | Fail (0)     | Returns that the header CRC failed. |
        +--------------+-------------------------------------+
        | Pass (1)     | Returns that the header CRC passed. |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccPayloadHeaderCrcStatus):
                Returns whether the header cyclic redundancy check (CRC) is successfully passed, as defined in section 16.2.3.7 of
                *IEEE Standard 802.11 2016*.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_HEADER_CRC_STATUS.value,
            )
            attr_val = enums.DsssModAccPayloadHeaderCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_psdu_crc_status(self, selector_string):
        r"""Indicates whether the cyclic redundancy check (CRC) of the received decoded PLCP service data unit (PSDU) has passed.

        The measurement calculates the CRC over the decoded bits, excluding the last 32 bits. The measurement then
        compares this value with the CRC value in the received payload, which is represented by the last 32 bits of the PSDU.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+-------------------------------------+
        | Name (Value) | Description                         |
        +==============+=====================================+
        | Fail (0)     | Indicates that the PSDU CRC failed. |
        +--------------+-------------------------------------+
        | Pass (1)     | Indicates that the PSDU CRC passed. |
        +--------------+-------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccPsduCrcStatus):
                Indicates whether the cyclic redundancy check (CRC) of the received decoded PLCP service data unit (PSDU) has passed.

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
                attributes.AttributeID.DSSSMODACC_RESULTS_PSDU_CRC_STATUS.value,
            )
            attr_val = enums.DsssModAccPsduCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_average_powers(self, selector_string, timeout):
        r"""Fetches the average power of various fields in the PPDU.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (preamble_average_power_mean, header_average_power_mean, data_average_power_mean, ppdu_average_power_mean, error_code):

            preamble_average_power_mean (float):
                This parameter returns the average power of the preamble field of the PPDU. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
                the mean of the average preamble field power computed for each averaging count. This value is expressed in dBm.

            header_average_power_mean (float):
                This parameter returns the average power of the header field of the PPDU. When you set the DSSSModAcc Averaging Enabled
                attribute to **True**, this result returns the mean of the average header field power computed for each averaging
                count. This value is expressed in dBm.

            data_average_power_mean (float):
                This parameter returns the average power of the data field of the PPDU. When you set the DSSSModAcc Averaging Enabled
                attribute to **True**, this attribute returns the mean of the data field average power results computed for each
                averaging count. This value is expressed in dBm.

            ppdu_average_power_mean (float):
                This parameter returns the average power of the PPDU. When you set the DSSSModAcc Averaging Enabled attribute to
                **True**, this parameter returns the mean of the average PPDU power results computed for each averaging count. This
                value is expressed in dBm.

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
                preamble_average_power_mean,
                header_average_power_mean,
                data_average_power_mean,
                ppdu_average_power_mean,
                error_code,
            ) = self._interpreter.dsssmodacc_fetch_average_powers(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            preamble_average_power_mean,
            header_average_power_mean,
            data_average_power_mean,
            ppdu_average_power_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_constellation_trace(self, selector_string, timeout, constellation):
        r"""Fetches the constellation trace for the data field.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            constellation (numpy.complex64):
                This parameter returns the constellation of the received symbols.

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
            error_code = self._interpreter.dsssmodacc_fetch_constellation_trace(
                updated_selector_string, timeout, constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_custom_gate_powers_array(self, selector_string, timeout):
        r"""Fetches the average and peak power of custom gates.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (average_power_mean, peak_power_maximum, error_code):

            average_power_mean (float):
                This parameter returns an array of average powers of the custom gates. This value is expressed in dBm. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns an array of the mean of the average custom gate power results computed for each averaging count.

            peak_power_maximum (float):
                This parameter returns an array of peak powers of the custom gates. This value is expressed in dBm. When you set the
                DSSSModAcc Averaging Enabled attribute to **True**, this parameter returns an array of the maximum of the peak custom
                gate power results computed for each averaging count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            average_power_mean, peak_power_maximum, error_code = (
                self._interpreter.dsssmodacc_fetch_custom_gate_powers_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return average_power_mean, peak_power_maximum, error_code

    @_raise_if_disposed
    def fetch_decoded_header_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded Header bits.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (decoded_header_bits, error_code):

            decoded_header_bits (int):
                This parameter returns an array of bits in the Header field.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_header_bits, error_code = (
                self._interpreter.dsssmodacc_fetch_decoded_header_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_header_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_psdu_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded PLCP service data unit (PSDU) bits.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (decoded_psdu_bits, error_code):

            decoded_psdu_bits (int):
                This parameter returns an array of PSDU bits obtained after demodulation and decoding.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_psdu_bits, error_code = (
                self._interpreter.dsssmodacc_fetch_decoded_psdu_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_psdu_bits, error_code

    @_raise_if_disposed
    def fetch_evm_per_chip_mean_trace(self, selector_string, timeout, evm_per_chip_mean):
        r"""Fetches the EVM per chip in the data field. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the EVM per chip computed for each averaging count.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            evm_per_chip_mean (numpy.float32):
                This parameter returns an array of EVM per chip. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the DSSSModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the index of the first chip.

            dx (float):
                This parameter returns the trace increment interval in number of chips. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.dsssmodacc_fetch_evm_per_chip_mean_trace(
                updated_selector_string, timeout, evm_per_chip_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_evm(self, selector_string, timeout):
        r"""Fetches the EVM results for the DSSSModAcc measurement.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (rms_evm_mean, peak_evm_80211_2016_maximum, peak_evm_80211_2007_maximum, peak_evm_80211_1999_maximum, frequency_error_mean, chip_clock_error_mean, number_of_chips_used, error_code):

            rms_evm_mean (float):
                This parameter returns the RMS EVM results of the burst. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
                the mean of the RMS EVM computed for each averaging count. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the DSSSModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

            peak_evm_80211_2016_maximum (float):
                This parameter returns the peak EVM results of the burst. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the DSSSModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. This measurement is performed in accordance with section 16.3.7.9 of *IEEE Standard 802.11-2016*. When
                you set the DSSSModAcc Averaging Enabled attribute to **True**, this result returns the maximum of the peak EVM
                computed for each averaging count.

            peak_evm_80211_2007_maximum (float):
                This parameter returns the peak EVM results of the burst. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the DSSSModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11-2007*. When
                you set the DSSSModAcc Averaging Enabled attribute to **True**, this result returns the maximum of the peak EVM
                computed for each averaging count.

            peak_evm_80211_1999_maximum (float):
                This parameter returns the peak EVM results of the burst. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the DSSSModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11b-1999*. When
                you set the DSSSModAcc Averaging Enabled attribute to **True**, this result returns the maximum of the peak EVM
                computed for each averaging count.

            frequency_error_mean (float):
                This parameter returns the carrier frequency error of the transmitter. This value is expressed in Hz. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
                the mean of the carrier frequency error results computed for each averaging count.

            chip_clock_error_mean (float):
                This parameter returns the chip clock error result of the transmitter. This value is expressed in parts per million
                (ppm). When you set the DSSSModAcc Averaging Enabled attribute to **True**, this result returns the mean of the chip
                clock error computed for each averaging count.

            number_of_chips_used (int):
                This parameter returns the number of chips used for the DSSSModAcc measurement.

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
                rms_evm_mean,
                peak_evm_80211_2016_maximum,
                peak_evm_80211_2007_maximum,
                peak_evm_80211_1999_maximum,
                frequency_error_mean,
                chip_clock_error_mean,
                number_of_chips_used,
                error_code,
            ) = self._interpreter.dsssmodacc_fetch_evm(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            rms_evm_mean,
            peak_evm_80211_2016_maximum,
            peak_evm_80211_2007_maximum,
            peak_evm_80211_1999_maximum,
            frequency_error_mean,
            chip_clock_error_mean,
            number_of_chips_used,
            error_code,
        )

    @_raise_if_disposed
    def fetch_iq_impairments(self, selector_string, timeout):
        r"""Fetches the I/Q Impairment results for the DSSSModAcc measurement.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (iq_origin_offset_mean, iq_gain_imbalance_mean, iq_quadrature_error_mean, error_code):

            iq_origin_offset_mean (float):
                This parameter returns the I/Q origin offset. This value is expressed in dB. I/Q origin offset is the ratio of the mean
                value of the signal to the RMS value of the signal. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the I/Q origin offset results computed for each averaging count.

            iq_gain_imbalance_mean (float):
                This parameter returns the I/Q gain imbalance results. This value is expressed in dB. I/Q gain imbalance is the ratio
                of the mean amplitude of the in-phase (I) signal to the mean amplitude of the quadrature-phase (Q) signal. When you set
                the DSSSModAcc Averaging Enabled attribute to **True**, this parameter returns the mean of the I/Q gain imbalance
                results computed for each averaging count.

            iq_quadrature_error_mean (float):
                This parameter returns the I/Q quadrature error. This value is expressed in degrees. Quadrature error is the deviation
                in angle from 90 degrees between the in-phase (I) and quadrature-phase (Q) signals. When the DSSSModAcc Averaging
                Enabled attribute is set to **True**, this parameter returns the mean of the I/Q quadrature error results computed for
                each averaging count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            iq_origin_offset_mean, iq_gain_imbalance_mean, iq_quadrature_error_mean, error_code = (
                self._interpreter.dsssmodacc_fetch_iq_impairments(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return iq_origin_offset_mean, iq_gain_imbalance_mean, iq_quadrature_error_mean, error_code

    @_raise_if_disposed
    def fetch_peak_powers(self, selector_string, timeout):
        r"""Fetches the peak power of various fields in the PPDU.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (preamble_peak_power_maximum, header_peak_power_maximum, data_peak_power_maximum, ppdu_peak_power_maximum, error_code):

            preamble_peak_power_maximum (float):
                This parameter returns the peak power of the preamble field of the PPDU. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
                the maximum of the peak preamble field power results computed for each averaging count. This value is expressed in dBm.

            header_peak_power_maximum (float):
                This parameter returns the peak power of the header field of the PPDU. When you set the DSSSModAcc Averaging Enabled
                attribute to **True**, this result returns the maximum of the peak header field power results computed for each
                averaging count. This value is expressed in dBm.

            data_peak_power_maximum (float):
                This parameter returns the peak power of the data field of the PPDU. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
                the maximum of the peak data field power results computed for each averaging count. This value is expressed in dBm.

            ppdu_peak_power_maximum (float):
                This parameter returns the peak power of the PPDU. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the maximum of the peak PPDU power results computed for each averaging count. This value is expressed in dBm.

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
                preamble_peak_power_maximum,
                header_peak_power_maximum,
                data_peak_power_maximum,
                ppdu_peak_power_maximum,
                error_code,
            ) = self._interpreter.dsssmodacc_fetch_peak_powers(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            preamble_peak_power_maximum,
            header_peak_power_maximum,
            data_peak_power_maximum,
            ppdu_peak_power_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_ppdu_information(self, selector_string, timeout):
        r"""Fetches the PPDU information.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (data_modulation_format, payload_length, preamble_type, locked_clocks_bit, header_crc_status, psdu_crc_status, error_code):

            data_modulation_format (enums.DsssModAccDataModulationFormat):
                This parameter returns the data modulation format results of the analyzed waveform.

                +-------------------+-----------------------------------------------------------------------------+
                | Name (Value)      | Description                                                                 |
                +===================+=============================================================================+
                | DSSS 1 Mbps (0)   | Indicates that the modulation format is DSSS and the data rate is 1 Mbps.   |
                +-------------------+-----------------------------------------------------------------------------+
                | DSSS 2 Mbps (1)   | Indicates that the modulation format is DSSS and the data rate is 2 Mbps.   |
                +-------------------+-----------------------------------------------------------------------------+
                | CCK 5.5 Mbps (2)  | Indicates that the modulation format is CCK and the data rate is 5.5 Mbps.  |
                +-------------------+-----------------------------------------------------------------------------+
                | CCK 11 Mbps (3)   | Indicates that the modulation format is CCK and the data rate is 11 Mbps.   |
                +-------------------+-----------------------------------------------------------------------------+
                | PBCC 5.5 Mbps (4) | Indicates that the modulation format is PBCC and the data rate is 5.5 Mbps. |
                +-------------------+-----------------------------------------------------------------------------+
                | PBCC 11 Mbps (5)  | Indicates that the modulation format is PBCC and the data rate is 11 Mbps.  |
                +-------------------+-----------------------------------------------------------------------------+
                | PBCC 22 Mbps (6)  | Indicates that the modulation format is PBCC and the data rate is 22 Mbps.  |
                +-------------------+-----------------------------------------------------------------------------+
                | PBCC 33 Mbps (7)  | Indicates that the modulation format is PBCC and the data rate is 33 Mbps.  |
                +-------------------+-----------------------------------------------------------------------------+

            payload_length (int):
                This parameter returns the payload length of the acquired burst. This value is expressed in bytes.

            preamble_type (enums.DsssModAccPreambleType):
                This parameter returns the detected preamble type.

                +--------------+--------------------------------------------------------------+
                | Name (Value) | Description                                                  |
                +==============+==============================================================+
                | Long (0)     | Indicates that the PPDU has a long PHY preamble and header.  |
                +--------------+--------------------------------------------------------------+
                | Short (1)    | Indicates that the PPDU has a short PHY preamble and header. |
                +--------------+--------------------------------------------------------------+

            locked_clocks_bit (int):
                This parameter returns the value of the locked clocks bit in the Long PHY SERVICE field. A value of 1 indicates that
                the transmit frequency and the symbol clock are derived from the same oscillator. A value of 0 indicates that the
                transmit frequency and the symbol clock are derived from independent oscillators.

            header_crc_status (enums.DsssModAccPayloadHeaderCrcStatus):
                This parameter returns whether the header CRC is successfully passed, as defined under section 16.2.3.7 of *IEEE
                Standard 802.11 2016*.

                +--------------+---------------------------------------+
                | Name (Value) | Description                           |
                +==============+=======================================+
                | Fail (0)     | Indicates that the header CRC failed. |
                +--------------+---------------------------------------+
                | Pass (1)     | Indicates that the header CRC passed. |
                +--------------+---------------------------------------+

            psdu_crc_status (enums.DsssModAccPsduCrcStatus):
                This parameter returns whether the PLCP service data unit (PSDU) cyclic redundancy check (CRC) has successfully passed.

                +--------------+-------------------------------------+
                | Name (Value) | Description                         |
                +==============+=====================================+
                | Fail (0)     | Indicates that the PSDU CRC failed. |
                +--------------+-------------------------------------+
                | Pass (1)     | Indicates that the PSDU CRC passed. |
                +--------------+-------------------------------------+

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
                data_modulation_format,
                payload_length,
                preamble_type,
                locked_clocks_bit,
                header_crc_status,
                psdu_crc_status,
                error_code,
            ) = self._interpreter.dsssmodacc_fetch_ppdu_information(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            data_modulation_format,
            payload_length,
            preamble_type,
            locked_clocks_bit,
            header_crc_status,
            psdu_crc_status,
            error_code,
        )
