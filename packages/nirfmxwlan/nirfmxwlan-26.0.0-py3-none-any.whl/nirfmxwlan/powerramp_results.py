"""Provides methods to fetch and read the PowerRamp measurement results."""

import functools

import nirfmxwlan.attributes as attributes
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


class PowerRampResults(object):
    """Provides methods to fetch and read the PowerRamp measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the PowerRamp measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_rise_time_mean(self, selector_string):
        r"""Gets the power-ramp rise time of the burst. This value is expressed in seconds.

        This measurement is performed in accordance with section 16.3.7.7 of *IEEE Standard 802.11-2016*.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the rise time results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power-ramp rise time of the burst. This value is expressed in seconds.

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
        r"""Gets the power-ramp fall time of the burst. This value is expressed in seconds.

        This measurement is performed in accordance with section 16.3.7.7 of *IEEE Standard 802.11-2016*.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the fall time results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power-ramp fall time of the burst. This value is expressed in seconds.

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
    def fetch_fall_trace(
        self, selector_string, timeout, raw_waveform, processed_waveform, threshold, power_reference
    ):
        r"""Returns the raw, processed, thresholding and power reference waveforms at the end of a burst.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            raw_waveform (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

            processed_waveform (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

            threshold (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

            power_reference (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the trace start time. This value is expressed in seconds.

            dx (float):
                This parameter returns the sampling interval. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.powerramp_fetch_fall_trace(
                updated_selector_string,
                timeout,
                raw_waveform,
                processed_waveform,
                threshold,
                power_reference,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_measurement(self, selector_string, timeout):
        r"""Returns the PowerRamp rise time and fall time.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (rise_time_mean, fall_time_mean, error_code):

            rise_time_mean (float):
                This parameter returns the rise time of the acquired signal that is the amount of time taken for the power envelope to
                rise from a level of 10 percent to 90 percent. This value is expressed in seconds. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to **True**, this parameter returns
                the mean of the rise time computed for each averaging count. This value is expressed in seconds.

            fall_time_mean (float):
                This parameter returns the fall time of the acquired signal that is the amount of time taken for the power envelope to
                fall from a level of 90 percent to 10 percent. This value is expressed in seconds. When you set the PowerRamp Averaging
                Enabled attribute to **True**, this parameter returns the mean of the fall time computed for each averaging count. This
                value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            rise_time_mean, fall_time_mean, error_code = (
                self._interpreter.powerramp_fetch_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return rise_time_mean, fall_time_mean, error_code

    @_raise_if_disposed
    def fetch_rise_trace(
        self, selector_string, timeout, raw_waveform, processed_waveform, threshold, power_reference
    ):
        r"""Returns the raw, processed, threshold and power-reference traces at the beginning of a burst.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            raw_waveform (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

            processed_waveform (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

            threshold (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

            power_reference (numpy.float32):
                This parameter returns an array of measured signal power. This value is expressed as a percentage.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the trace start time. This value is expressed in seconds.

            dx (float):
                This parameter returns the sampling interval. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.powerramp_fetch_rise_trace(
                updated_selector_string,
                timeout,
                raw_waveform,
                processed_waveform,
                threshold,
                power_reference,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
