"""Provides methods to fetch and read the Sem measurement results."""

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


class SemResults(object):
    """Provides methods to fetch and read the Sem measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the Sem measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_status(self, selector_string):
        r"""Gets the overall measurement status, indicating whether the spectrum exceeds the SEM measurement mask limits in any
        of the offset segments.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+-----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                   |
        +==============+===============================================================================================+
        | Fail (0)     | The spectrum exceeds the SEM measurement mask limits for at least one of the offset segments. |
        +--------------+-----------------------------------------------------------------------------------------------+
        | Pass (1)     | The spectrum does not exceed the SEM measurement mask limits for any offset segment.          |
        +--------------+-----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemMeasurementStatus):
                Returns the overall measurement status, indicating whether the spectrum exceeds the SEM measurement mask limits in any
                of the offset segments.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.SEM_RESULTS_MEASUREMENT_STATUS.value
            )
            attr_val = enums.SemMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_carrier_absolute_integrated_power(self, selector_string):
        r"""Gets the average power of the carrier channel over the bandwidth indicated by the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
        dBm.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the carrier channel over the bandwidth indicated by the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
                dBm.

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
                attributes.AttributeID.SEM_RESULTS_CARRIER_ABSOLUTE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_carrier_absolute_peak_power(self, selector_string):
        r"""Gets the peak power in the carrier channel over the bandwidth indicated by the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
        dBm. SEM mask level is determined by this result.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power in the carrier channel over the bandwidth indicated by the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
                dBm. SEM mask level is determined by this result.

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
                attributes.AttributeID.SEM_RESULTS_CARRIER_ABSOLUTE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_carrier_peak_frequency(self, selector_string):
        r"""Gets the frequency at which the peak power occurs in the carrier channel. This value is expressed in Hz.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the peak power occurs in the carrier channel. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_CARRIER_PEAK_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_measurement_status(self, selector_string):
        r"""Gets the lower offset segment measurement status indicating whether the spectrum exceeds the SEM measurement mask
        limits in the lower offset segment.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | Fail (0)     | Indicates that the measurement has failed. |
        +--------------+--------------------------------------------+
        | Pass (1)     | Indicates that the measurement has passed. |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemLowerOffsetMeasurementStatus):
                Returns the lower offset segment measurement status indicating whether the spectrum exceeds the SEM measurement mask
                limits in the lower offset segment.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MEASUREMENT_STATUS.value,
            )
            attr_val = enums.SemLowerOffsetMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_absolute_integrated_power(self, selector_string):
        r"""Gets the average power of the lower (negative) offset channel over the bandwidth obtained by the start and stop
        frequencies of the offset channel. This value is expressed in dBm.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the lower (negative) offset channel over the bandwidth obtained by the start and stop
                frequencies of the offset channel. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_relative_integrated_power(self, selector_string):
        r"""Gets the average power of the lower (negative) offset segment relative to the peak power of the carrier channel.
        This value is expressed in dB.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the lower (negative) offset segment relative to the peak power of the carrier channel.
                This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_RELATIVE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_absolute_peak_power(self, selector_string):
        r"""Gets the peak power measured in the lower (negative) offset segment. This value is expressed in dBm.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power measured in the lower (negative) offset segment. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_relative_peak_power(self, selector_string):
        r"""Gets the peak power of the lower (negative) offset segment relative to the peak power of the carrier channel. This
        value is expressed in dB.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the lower (negative) offset segment relative to the peak power of the carrier channel. This
                value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_RELATIVE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_peak_frequency(self, selector_string):
        r"""Gets the frequency at which the peak power occurs in the lower (negative) offset channel. This value is expressed in
        Hz.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the peak power occurs in the lower (negative) offset channel. This value is expressed in
                Hz.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_PEAK_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin(self, selector_string):
        r"""Gets the margin from the SEM measurement mask for the lower (negative) offset. This value is expressed in dB.

        Margin is computed as

        Margin(dB) = Max(Spectrum[] - Mask[])

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the margin from the SEM measurement mask for the lower (negative) offset. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin_absolute_power(self, selector_string):
        r"""Gets the power level of the spectrum corresponding to the result of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in
        dBm.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power level of the spectrum corresponding to the result of the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in
                dBm.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin_relative_power(self, selector_string):
        r"""Gets the power level of the spectrum corresponding to the result of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in dB.

        The power level is returned relative to the peak power of the carrier channel.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power level of the spectrum corresponding to the result of the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_lower_offset_margin_frequency(self, selector_string):
        r"""Gets the frequency of the spectrum corresponding to the result of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in Hz.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency of the spectrum corresponding to the result of the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_measurement_status(self, selector_string):
        r"""Gets the upper offset (positive) segment measurement status indicating if the spectrum exceeds the SEM measurement
        mask limits in the upper offset segment.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        +--------------+------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                    |
        +==============+================================================================================================+
        | Fail (0)     | The spectrum exceeds the SEM measurement mask and limits for the upper offset segment.         |
        +--------------+------------------------------------------------------------------------------------------------+
        | Pass (1)     | The spectrum does not exceed the SEM measurement mask and limits for the upper offset segment. |
        +--------------+------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.SemUpperOffsetMeasurementStatus):
                Returns the upper offset (positive) segment measurement status indicating if the spectrum exceeds the SEM measurement
                mask limits in the upper offset segment.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MEASUREMENT_STATUS.value,
            )
            attr_val = enums.SemUpperOffsetMeasurementStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_absolute_integrated_power(self, selector_string):
        r"""Gets the average power of the offset (positive) offset channel over the bandwidth determined by the start and stop
        frequencies of the offset channel. This value is expressed in dBm.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the offset (positive) offset channel over the bandwidth determined by the start and stop
                frequencies of the offset channel. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_relative_integrated_power(self, selector_string):
        r"""Gets the average power of the offset (positive) offset segment relative to the peak power of the carrier channel.
        This value is expressed in dB.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the offset (positive) offset segment relative to the peak power of the carrier channel.
                This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_RELATIVE_INTEGRATED_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_absolute_peak_power(self, selector_string):
        r"""Gets the peak power of the offset (positive) offset segment. This value is expressed in dBm.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the offset (positive) offset segment. This value is expressed in dBm.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_relative_peak_power(self, selector_string):
        r"""Gets the peak power of the offset (positive) segment relative to the peak power of the carrier channel. This value
        is expressed in dB.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the offset (positive) segment relative to the peak power of the carrier channel. This value
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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_RELATIVE_PEAK_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_peak_frequency(self, selector_string):
        r"""Gets the frequency at which the peak power occurs in the offset (positive) channel. This value is expressed in Hz.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency at which the peak power occurs in the offset (positive) channel. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_PEAK_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin(self, selector_string):
        r"""Gets the margin from the SEM measurement mask for the offset (positive). This value is expressed in dB.

        Margin is computed as

        Margin(dB) = Max(Spectrum[] - Mask[])

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the margin from the SEM measurement mask for the offset (positive). This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin_absolute_power(self, selector_string):
        r"""Gets the power level of the spectrum corresponding to the result of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in
        dBm.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power level of the spectrum corresponding to the result of the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in
                dBm.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN_ABSOLUTE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin_relative_power(self, selector_string):
        r"""Gets the power level of the spectrum corresponding to the result of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in dB.

        The power level is returned relative to the peak power of the carrier channel.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the power level of the spectrum corresponding to the result of the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in dB.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN_RELATIVE_POWER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_upper_offset_margin_frequency(self, selector_string):
        r"""Gets the frequency of the spectrum corresponding to the result of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in Hz.

        Use "offset<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the frequency of the spectrum corresponding to the result of the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in Hz.

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
                attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN_FREQUENCY.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_carrier_measurement(self, selector_string, timeout):
        r"""Returns the absolute and relative carrier power measurements. The relative power is relative to the peak power of the
        carrier.

        Use "segment<*n*>/chain<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and chain number.

                Example:

                "segment0/chain0"

                "result::r1/segment0/chain0"

                You can use the :py:meth:`build_chain_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (absolute_power, relative_power, error_code):

            absolute_power (float):
                This parameter returns the average power of the carrier channel over the bandwidth indicated by the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
                dBm.

            relative_power (float):
                This parameter returns the average power of the carrier channel, relative to the peak power of the carrier channel,
                over the bandwidth indicated by the SEM Carrier IBW attribute. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            absolute_power, relative_power, error_code = (
                self._interpreter.sem_fetch_carrier_measurement(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return absolute_power, relative_power, error_code

    @_raise_if_disposed
    def fetch_lower_offset_margin_array(self, selector_string, timeout):
        r"""Returns an array of measurement status, margins, margin-frequencies, and absolute and relative powers corresponding to
        the margin-frequencies for lower offset segments.  The relative powers are relative to the peak power in the carrier.

        Use "segment<*n*>/chain<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and chain number.

                Example:

                "segment0/chain0"

                "result::r1/segment0/chain0"

                You can use the :py:meth:`build_chain_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemLowerOffsetMeasurementStatus):
                This parameter returns an array of lower (negative) offset segment measurement status, indicating whether the spectrum
                exceeds the SEM measurement mask limits in the lower offset segments.

                +--------------+--------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                |
                +==============+============================================================================================+
                | Fail (0)     | The spectrum exceeds the SEM measurement mask limits the lower offset segment.             |
                +--------------+--------------------------------------------------------------------------------------------+
                | Pass (1)     | The spectrum does not exceed the SEM measurement mask limits for the lower offset segment. |
                +--------------+--------------------------------------------------------------------------------------------+

            margin (float):
                This parameter returns an array of margins from the SEM measurement mask for the lower offset. This value is expressed
                in dB. Margin is defined as the maximum difference between the spectrum and the mask.

            margin_frequency (float):
                This parameter returns an array of frequencies corresponding to the margins for the lower (negative) offsets. This
                value is expressed in dB.

            margin_absolute_power (float):
                This parameter returns an array of absolute powers corresponding to the margins for the lower offsets. This value is
                expressed in dBm.

            margin_relative_power (float):
                This parameter returns an array of relative powers corresponding to the margins for the lower offsets. The relative
                powers are relative to the peak power of the carrier channel. This value is expressed in dB.

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
                measurement_status,
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_margin_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_lower_offset_margin(self, selector_string, timeout):
        r"""Returns the measurement status, margin, margin-frequency, and absolute and relative power corresponding to the
        margin-frequency for lower offset segment. The relative power is relative to the peak power in the carrier.

        Use "segment<*n*>/chain<*k*>/offset<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and offset number.

                Example:

                "segment0/chain0/offset0"

                "result::r1/segment0/chain0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemLowerOffsetMeasurementStatus):
                This parameter returns the lower offset (negative) segment measurement status, indicating whether the spectrum exceeds
                the SEM measurement mask limits in the lower offset segment.

                +--------------+--------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                |
                +==============+============================================================================================+
                | Fail (0)     | The spectrum exceeds the SEM measurement mask limits the lower offset segment.             |
                +--------------+--------------------------------------------------------------------------------------------+
                | Pass (1)     | The spectrum does not exceed the SEM measurement mask limits for the lower offset segment. |
                +--------------+--------------------------------------------------------------------------------------------+

            margin (float):
                This parameter returns the margin from the SEM measurement mask for the lower offset. This value is expressed in dB.
                Margin is defined as the maximum difference between the spectrum and the mask.

            margin_frequency (float):
                This parameter returns the frequency corresponding to the margin for the lower offset. This value is expressed in Hz.

            margin_absolute_power (float):
                This parameter returns the absolute power corresponding to the margin for the lower offset. This value is expressed in
                dBm.

            margin_relative_power (float):
                This parameter returns the relative power corresponding to the margin for the lower offset. The relative power is
                relative to the peak power of the carrier channel. This value is expressed in dB.

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
                measurement_status,
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_margin(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_lower_offset_power_array(self, selector_string, timeout):
        r"""Returns an array of total absolute and relative powers, peak absolute and relative powers and frequencies corresponding
        to the peak absolute powers of lower offset segments. The relative powers are relative to peak power of the carrier.

        Use "segment<*n*>/chain<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and chain number.

                Example:

                "segment0/chain0"

                "result::r1/segment0/chain0"

                You can use the :py:meth:`build_chain_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (total_absolute_power, total_relative_power, peak_absolute_power, peak_frequency, peak_relative_power, error_code):

            total_absolute_power (float):
                This parameter returns an array of average powers of the lower offsets over the bandwidth determined by the offset
                start and stop frequencies. This value is expressed in dBm.

            total_relative_power (float):
                This parameter returns an array of average powers of the lower offsets relative to the peak power of the carrier
                channel. This value is expressed in dB.

            peak_absolute_power (float):
                This parameter returns an array of peak powers of the lower offsets. This value is expressed in dBm.

            peak_frequency (float):
                This parameter returns an array of frequencies at which the peak power occurs in the lower offsets. This value is
                expressed in Hz.

            peak_relative_power (float):
                This parameter returns an array of peak powers of the lower offsets, relative to the peak power of the carrier channel.
                This value is expressed in dBm.

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
                total_absolute_power,
                total_relative_power,
                peak_absolute_power,
                peak_frequency,
                peak_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_power_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_lower_offset_power(self, selector_string, timeout):
        r"""Returns the total absolute and relative powers, peak absolute and relative powers and frequency at peak absolute power
        of lower offset segment. The relative power is relative to the peak power of the carrier.

        Use "segment<*n*>/chain<*k*>/offset<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and offset number.

                Example:

                "segment0/chain0/offset0"

                "result::r1/segment0/chain0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (total_absolute_power, total_relative_power, peak_absolute_power, peak_frequency, peak_relative_power, error_code):

            total_absolute_power (float):
                This parameter returns the average power of the lower offset over the bandwidth determined by the offset start and stop
                frequencies. This value is expressed in dBm.

            total_relative_power (float):
                This parameter returns the average power of the lower offset relative to the peak power of the carrier channel. This
                value is expressed in dB.

            peak_absolute_power (float):
                This parameter returns the peak power of the lower offset. This value is expressed in dBm.

            peak_frequency (float):
                This parameter returns the frequency at which the peak power occurs in the lower offset. This value is expressed in Hz.

            peak_relative_power (float):
                This parameter returns the peak power of the lower offset, relative to the peak power of the carrier channel. This
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
                total_absolute_power,
                total_relative_power,
                peak_absolute_power,
                peak_frequency,
                peak_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_lower_offset_power(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_measurement_status(self, selector_string, timeout):
        r"""Fetches the overall measurement status.

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
            Tuple (measurement_status, error_code):

            measurement_status (enums.SemMeasurementStatus):
                This parameter returns the overall measurement status indicating whether the spectrum exceeds the SEM measurement mask
                limits in any of the offset segments.

                +--------------+-----------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                   |
                +==============+===============================================================================================+
                | Fail (0)     | The spectrum exceeds the SEM measurement mask limits for at least one of the offset segments. |
                +--------------+-----------------------------------------------------------------------------------------------+
                | Pass (1)     | The spectrum does not exceed the SEM measurement mask limits for any offset segment.          |
                +--------------+-----------------------------------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            measurement_status, error_code = self._interpreter.sem_fetch_measurement_status(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return measurement_status, error_code

    @_raise_if_disposed
    def fetch_spectrum(self, selector_string, timeout, spectrum, composite_mask):
        r"""Fetches the spectrum and mask traces.

        Use "segment<*n*>/chain<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and chain number.

                Example:

                "segment0/chain0"

                "result::r1/segment0/chain0"

                You can use the :py:meth:`build_chain_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            spectrum (numpy.float32):
                This parameter returns an array of power measured at each frequency bin. This value is expressed in dBm.

            composite_mask (numpy.float32):
                This parameter returns an array of power measured at each frequency bin. This value is expressed in dBm.

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
            x0, dx, error_code = self._interpreter.sem_fetch_spectrum(
                updated_selector_string, timeout, spectrum, composite_mask
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_upper_offset_margin_array(self, selector_string, timeout):
        r"""Returns an array of measurement status, margins, margin frequencies, absolute and relative powers corresponding to the
        margin-frequencies for upper offset segments. The relative powers are relative to the peak power in the carrier.

        Use "segment<*n*>/chain<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and chain number.

                Example:

                "segment0/chain0"

                "result::r1/segment0/chain0"

                You can use the :py:meth:`build_chain_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemUpperOffsetMeasurementStatus):
                This parameter returns an array of upper offset (positive) segment measurement status, indicating whether the spectrum
                exceeds the SEM measurement mask limits in the upper offset segments.

                +--------------+--------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                |
                +==============+============================================================================================+
                | Fail (0)     | The spectrum exceeds the SEM measurement mask limits the upper offset segment.             |
                +--------------+--------------------------------------------------------------------------------------------+
                | Pass (1)     | The spectrum does not exceed the SEM measurement mask limits for the upper offset segment. |
                +--------------+--------------------------------------------------------------------------------------------+

            margin (float):
                This parameter returns an array of margins from the SEM measurement mask for the upper offset. This value is expressed
                in dB. Margin is defined as the maximum difference between the spectrum and the mask.

            margin_frequency (float):
                This parameter returns an array of frequencies corresponding to the margins for the upper offsets. This value is
                expressed in Hz.

            margin_absolute_power (float):
                This parameter returns an array of absolute powers corresponding to the margins for the upper (positive) offsets. This
                value is expressed in dBm.

            margin_relative_power (float):
                This parameter returns an array of relative powers corresponding to the margins for the upper (positive) offsets. The
                relative powers are relative to the peak power of the carrier channel. This value is expressed in dB.

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
                measurement_status,
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_margin_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_upper_offset_margin(self, selector_string, timeout):
        r"""Returns the measurement status, margin, margin-frequency, absolute and relative power corresponding to the
        margin-frequency for upper offset segment. The relative power is relative to the peak power in the carrier.

        Use "segment<*n*>/chain<*k*>/offset<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and offset number.

                Example:

                "segment0/chain0/offset0"

                "result::r1/segment0/chain0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (measurement_status, margin, margin_frequency, margin_absolute_power, margin_relative_power, error_code):

            measurement_status (enums.SemUpperOffsetMeasurementStatus):
                This parameter returns the upper (positive) offset segment measurement status, indicating whether the spectrum exceeds
                the SEM measurement mask limits in the upper offset segment.

                +--------------+--------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                |
                +==============+============================================================================================+
                | Fail (0)     | The spectrum exceeds the SEM measurement mask limits the upper offset segment.             |
                +--------------+--------------------------------------------------------------------------------------------+
                | Pass (1)     | The spectrum does not exceed the SEM measurement mask limits for the upper offset segment. |
                +--------------+--------------------------------------------------------------------------------------------+

            margin (float):
                This parameter returns the margin from the SEM measurement mask for the upper offset. Margin is defined as the maximum
                difference between the spectrum and the mask. This value is expressed in dB.

            margin_frequency (float):
                This parameter returns the frequency corresponding to the margin for the upper offset. This value is expressed in Hz.

            margin_absolute_power (float):
                This parameter returns the power level of the spectrum, corresponding to the SEM Results Upper Offset Margin result.
                This value is expressed in dBm.

            margin_relative_power (float):
                This parameter returns the power level of the spectrum, corresponding to the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` result. The power level is returned
                relative to the peak power of the carrier channel. This value is expressed in dB.

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
                measurement_status,
                margin,
                margin_frequency,
                margin_absolute_power,
                margin_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_margin(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            measurement_status,
            margin,
            margin_frequency,
            margin_absolute_power,
            margin_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_upper_offset_power_array(self, selector_string, timeout):
        r"""Fetches an array of total absolute and relative powers, peak absolute and relative powers, and frequencies
        corresponding to the peak absolute powers of upper offset segments. The relative powers are relative to peak power of
        the carrier.

        Use "segment<*n*>/chain<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and chain number.

                Example:

                "segment0/chain0"

                "result::r1/segment0/chain0"

                You can use the :py:meth:`build_chain_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (total_absolute_power, total_relative_power, peak_absolute_power, peak_frequency, peak_relative_power, error_code):

            total_absolute_power (float):
                This parameter returns an array of average powers of the upper offsets over the bandwidth determined by the offset
                start and stop frequencies. This value is expressed in dBm.

            total_relative_power (float):
                This parameter returns an array of average powers of the upper offsets relative to the peak power of the carrier
                channel. This value is expressed in dB.

            peak_absolute_power (float):
                This parameter returns an array of peak powers of the upper offsets. This value is expressed in dBm.

            peak_frequency (float):
                This parameter returns an array of frequencies at which the peak power occurs in the upper offsets. This value is
                expressed in Hz.

            peak_relative_power (float):
                This parameter returns an array of peak powers of the upper offsets, relative to the peak power of the carrier channel.
                This value is expressed in dBm.

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
                total_absolute_power,
                total_relative_power,
                peak_absolute_power,
                peak_frequency,
                peak_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_power_array(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
            error_code,
        )

    @_raise_if_disposed
    def fetch_upper_offset_power(self, selector_string, timeout):
        r"""Returns the total absolute and relative powers, peak absolute and relative powers and frequency at peak absolute power
        of upper offset segment. The relative power is relative to the peak power of the carrier.

        Use "segment<*n*>/chain<*k*>/offset<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and offset number.

                Example:

                "segment0/chain0/offset0"

                "result::r1/segment0/chain0/offset0"

                You can use the :py:meth:`build_offset_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (total_absolute_power, total_relative_power, peak_absolute_power, peak_frequency, peak_relative_power, error_code):

            total_absolute_power (float):
                This parameter returns the  average power of the upper (positive) offset over the bandwidth determined by the offset
                start and stop frequencies. This value is expressed in dBm.

            total_relative_power (float):
                This parameter returns the average power of the upper offset relative to the peak power of the carrier channel. This
                value is expressed in dB.

            peak_absolute_power (float):
                This parameter returns the peak power of the upper offset. This value is expressed in dBm.

            peak_frequency (float):
                This parameter returns the frequency at which the peak power occurs in the upper offset. This value is expressed in Hz.

            peak_relative_power (float):
                This parameter returns the peak power of the upper offset, relative to the peak power of the carrier channel. This
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
                total_absolute_power,
                total_relative_power,
                peak_absolute_power,
                peak_frequency,
                peak_relative_power,
                error_code,
            ) = self._interpreter.sem_fetch_upper_offset_power(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            total_absolute_power,
            total_relative_power,
            peak_absolute_power,
            peak_frequency,
            peak_relative_power,
            error_code,
        )
