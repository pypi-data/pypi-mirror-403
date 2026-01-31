"""Provides methods to configure the DsssModAcc measurement."""

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


class DsssModAccConfiguration(object):
    """Provides methods to configure the DsssModAcc measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the DsssModAcc measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable the DSSSModAcc measurement, which is a measurement of the modulation accuracy on signals
        conforming to the DSSS PHY defined in section 15 and the High Rate DSSS PHY defined in section 16 of *IEEE Standard
        802.11-2016*.

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
                Specifies whether to enable the DSSSModAcc measurement, which is a measurement of the modulation accuracy on signals
                conforming to the DSSS PHY defined in section 15 and the High Rate DSSS PHY defined in section 16 of *IEEE Standard
                802.11-2016*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable the DSSSModAcc measurement, which is a measurement of the modulation accuracy on signals
        conforming to the DSSS PHY defined in section 15 and the High Rate DSSS PHY defined in section 16 of *IEEE Standard
        802.11-2016*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable the DSSSModAcc measurement, which is a measurement of the modulation accuracy on signals
                conforming to the DSSS PHY defined in section 15 and the High Rate DSSS PHY defined in section 16 of *IEEE Standard
                802.11-2016*.

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
                attributes.AttributeID.DSSSMODACC_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_acquisition_length_mode(self, selector_string):
        r"""Gets whether the measurement automatically computes the acquisition length of the waveform based on DSSSModAcc
        attributes.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | Uses the acquisition length specified by the DSSSModAcc Acquisition Length attribute.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | Computes the acquisition length based on the DSSSModAcc Meas Offset attribute                                            |
        |              | and the DSSSModAcc Max Meas Length attribute.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccAcquisitionLengthMode):
                Specifies whether the measurement automatically computes the acquisition length of the waveform based on DSSSModAcc
                attributes.

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
                attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE.value,
            )
            attr_val = enums.DsssModAccAcquisitionLengthMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_acquisition_length_mode(self, selector_string, value):
        r"""Sets whether the measurement automatically computes the acquisition length of the waveform based on DSSSModAcc
        attributes.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Manual (0)   | Uses the acquisition length specified by the DSSSModAcc Acquisition Length attribute.                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | Computes the acquisition length based on the DSSSModAcc Meas Offset attribute                                            |
        |              | and the DSSSModAcc Max Meas Length attribute.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccAcquisitionLengthMode, int):
                Specifies whether the measurement automatically computes the acquisition length of the waveform based on DSSSModAcc
                attributes.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccAcquisitionLengthMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_acquisition_length(self, selector_string):
        r"""Gets the length of the waveform to be acquired for the DSSSModAcc measurement when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
        expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 millisecond.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the length of the waveform to be acquired for the DSSSModAcc measurement when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
                expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_acquisition_length(self, selector_string, value):
        r"""Sets the length of the waveform to be acquired for the DSSSModAcc measurement when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
        expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 millisecond.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the length of the waveform to be acquired for the DSSSModAcc measurement when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
                expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_offset(self, selector_string):
        r"""Gets the number of data chips to be ignored from the start of the data field for the EVM computation. This value
        is expressed in chips.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of data chips to be ignored from the start of the data field for the EVM computation. This value
                is expressed in chips.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_MEASUREMENT_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_offset(self, selector_string, value):
        r"""Sets the number of data chips to be ignored from the start of the data field for the EVM computation. This value
        is expressed in chips.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of data chips to be ignored from the start of the data field for the EVM computation. This value
                is expressed in chips.

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
                attributes.AttributeID.DSSSMODACC_MEASUREMENT_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_maximum_measurement_length(self, selector_string):
        r"""Gets the maximum number of data chips that the measurement uses to compute EVM. This value is expressed in chips.

        If you set this attribute to -1, all chips in the signal are used for measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1000.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the maximum number of data chips that the measurement uses to compute EVM. This value is expressed in chips.

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
                attributes.AttributeID.DSSSMODACC_MAXIMUM_MEASUREMENT_LENGTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_maximum_measurement_length(self, selector_string, value):
        r"""Sets the maximum number of data chips that the measurement uses to compute EVM. This value is expressed in chips.

        If you set this attribute to -1, all chips in the signal are used for measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1000.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of data chips that the measurement uses to compute EVM. This value is expressed in chips.

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
                attributes.AttributeID.DSSSMODACC_MAXIMUM_MEASUREMENT_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pulse_shaping_filter_type(self, selector_string):
        r"""Gets the type of pulse shaping filter used at the transmitter. This attribute is ignored when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rectangular**.

        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                                              |
        +========================+==========================================================================================================================+
        | Rectangular (0)        | Specifies that the transmitter uses a rectangular pulse shaping filter. The measurement uses an impulse response as the  |
        |                        | matched filter.                                                                                                          |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Raised Cosine (1)      | Specifies that the transmitter uses a raised cosine pulse shaping filter. The measurement uses an impulse response as    |
        |                        | the matched filter.                                                                                                      |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Root Raised Cosine (2) | Specifies that the transmitter uses a root raised cosine pulse shaping filter. The measurement uses a root raised        |
        |                        | cosine filter as the matched filter.                                                                                     |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Gaussian (3)           | Specifies that the transmitter uses a Gaussian filter. The measurement uses a Gaussian as the matched filter.            |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccPulseShapingFilterType):
                Specifies the type of pulse shaping filter used at the transmitter. This attribute is ignored when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.

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
                attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE.value,
            )
            attr_val = enums.DsssModAccPulseShapingFilterType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pulse_shaping_filter_type(self, selector_string, value):
        r"""Sets the type of pulse shaping filter used at the transmitter. This attribute is ignored when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rectangular**.

        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                                              |
        +========================+==========================================================================================================================+
        | Rectangular (0)        | Specifies that the transmitter uses a rectangular pulse shaping filter. The measurement uses an impulse response as the  |
        |                        | matched filter.                                                                                                          |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Raised Cosine (1)      | Specifies that the transmitter uses a raised cosine pulse shaping filter. The measurement uses an impulse response as    |
        |                        | the matched filter.                                                                                                      |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Root Raised Cosine (2) | Specifies that the transmitter uses a root raised cosine pulse shaping filter. The measurement uses a root raised        |
        |                        | cosine filter as the matched filter.                                                                                     |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Gaussian (3)           | Specifies that the transmitter uses a Gaussian filter. The measurement uses a Gaussian as the matched filter.            |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccPulseShapingFilterType, int):
                Specifies the type of pulse shaping filter used at the transmitter. This attribute is ignored when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccPulseShapingFilterType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_pulse_shaping_filter_parameter(self, selector_string):
        r"""Gets the value of the filter roll-off when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE` attribute to **Raised Cosine** or
        **Root Raised Cosine**. This attribute is ignored if you set the Pulse Shaping Filter Type attribute to
        **Rectangular**.

        This attribute is ignored when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the value of the filter roll-off when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE` attribute to **Raised Cosine** or
                **Root Raised Cosine**. This attribute is ignored if you set the Pulse Shaping Filter Type attribute to
                **Rectangular**.

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
                attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_PARAMETER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_pulse_shaping_filter_parameter(self, selector_string, value):
        r"""Sets the value of the filter roll-off when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE` attribute to **Raised Cosine** or
        **Root Raised Cosine**. This attribute is ignored if you set the Pulse Shaping Filter Type attribute to
        **Rectangular**.

        This attribute is ignored when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the value of the filter roll-off when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE` attribute to **Raised Cosine** or
                **Root Raised Cosine**. This attribute is ignored if you set the Pulse Shaping Filter Type attribute to
                **Rectangular**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_PARAMETER.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_equalization_enabled(self, selector_string):
        r"""Gets whether to enable equalization. The *IEEE Standard 802.11-2016* does not allow equalization for computing
        EVM. If you enable equalization, the measurement does not support I/Q impairment estimation.

        Equalization is not supported for signals with data rates of 22 Mbps and 33 Mbps. Do not set this attribute to
        **True** when performing demodulation measurements on signals with data rates of 22 Mbps and 33 Mbps.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------+
        | Name (Value) | Description            |
        +==============+========================+
        | False (0)    | Disables equalization. |
        +--------------+------------------------+
        | True (1)     | Enables equalization.  |
        +--------------+------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccEqualizationEnabled):
                Specifies whether to enable equalization. The *IEEE Standard 802.11-2016* does not allow equalization for computing
                EVM. If you enable equalization, the measurement does not support I/Q impairment estimation.

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
                attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED.value,
            )
            attr_val = enums.DsssModAccEqualizationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_equalization_enabled(self, selector_string, value):
        r"""Sets whether to enable equalization. The *IEEE Standard 802.11-2016* does not allow equalization for computing
        EVM. If you enable equalization, the measurement does not support I/Q impairment estimation.

        Equalization is not supported for signals with data rates of 22 Mbps and 33 Mbps. Do not set this attribute to
        **True** when performing demodulation measurements on signals with data rates of 22 Mbps and 33 Mbps.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------+
        | Name (Value) | Description            |
        +==============+========================+
        | False (0)    | Disables equalization. |
        +--------------+------------------------+
        | True (1)     | Enables equalization.  |
        +--------------+------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccEqualizationEnabled, int):
                Specifies whether to enable equalization. The *IEEE Standard 802.11-2016* does not allow equalization for computing
                EVM. If you enable equalization, the measurement does not support I/Q impairment estimation.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccEqualizationEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_burst_start_detection_enabled(self, selector_string):
        r"""Gets whether the measurement detects the rising edge of a burst in the acquired waveform.

        The detected rising edge of the burst is used for the measurement. If you are using an I/Q power edge trigger
        or a digital edge trigger to trigger approximately and consistently at the start of a burst, set this attribute to
        **False**. If you are unable to reliably trigger at the start of a burst, set this attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                |
        +==============+============================================================================================+
        | False (0)    | Disables detection of a rising edge of the burst in the acquired waveform for measurement. |
        +--------------+--------------------------------------------------------------------------------------------+
        | True (1)     | Enables detection of a rising edge of the burst in the acquired waveform for measurement.  |
        +--------------+--------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccBurstStartDetectionEnabled):
                Specifies whether the measurement detects the rising edge of a burst in the acquired waveform.

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
                attributes.AttributeID.DSSSMODACC_BURST_START_DETECTION_ENABLED.value,
            )
            attr_val = enums.DsssModAccBurstStartDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_burst_start_detection_enabled(self, selector_string, value):
        r"""Sets whether the measurement detects the rising edge of a burst in the acquired waveform.

        The detected rising edge of the burst is used for the measurement. If you are using an I/Q power edge trigger
        or a digital edge trigger to trigger approximately and consistently at the start of a burst, set this attribute to
        **False**. If you are unable to reliably trigger at the start of a burst, set this attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                |
        +==============+============================================================================================+
        | False (0)    | Disables detection of a rising edge of the burst in the acquired waveform for measurement. |
        +--------------+--------------------------------------------------------------------------------------------+
        | True (1)     | Enables detection of a rising edge of the burst in the acquired waveform for measurement.  |
        +--------------+--------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccBurstStartDetectionEnabled, int):
                Specifies whether the measurement detects the rising edge of a burst in the acquired waveform.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value if type(value) is enums.DsssModAccBurstStartDetectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_BURST_START_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_unit(self, selector_string):
        r"""Gets the unit for the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **percentage**.

        +----------------+------------------------------------------+
        | Name (Value)   | Description                              |
        +================+==========================================+
        | Percentage (0) | Returns the EVM results as a percentage. |
        +----------------+------------------------------------------+
        | dB (1)         | Returns the EVM results in dB.           |
        +----------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccEvmUnit):
                Specifies the unit for the EVM results.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_EVM_UNIT.value
            )
            attr_val = enums.DsssModAccEvmUnit(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_unit(self, selector_string, value):
        r"""Sets the unit for the EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **percentage**.

        +----------------+------------------------------------------+
        | Name (Value)   | Description                              |
        +================+==========================================+
        | Percentage (0) | Returns the EVM results as a percentage. |
        +----------------+------------------------------------------+
        | dB (1)         | Returns the EVM results in dB.           |
        +----------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccEvmUnit, int):
                Specifies the unit for the EVM results.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccEvmUnit else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_EVM_UNIT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_measurement_enabled(self, selector_string):
        r"""Gets whether power measurement is performed. This measurement computes power of various fields in the PPDU.

        Additionally, this measurement computes power over the custom gates that you can configure using the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_NUMBER_OF_CUSTOM_GATES`, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_START_TIME` and the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_STOP_TIME` attributes.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------+
        | Name (Value) | Description                 |
        +==============+=============================+
        | False (0)    | Disables power measurement. |
        +--------------+-----------------------------+
        | True (1)     | Enables power measurement.  |
        +--------------+-----------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccPowerMeasurementEnabled):
                Specifies whether power measurement is performed. This measurement computes power of various fields in the PPDU.

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
                attributes.AttributeID.DSSSMODACC_POWER_MEASUREMENT_ENABLED.value,
            )
            attr_val = enums.DsssModAccPowerMeasurementEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_measurement_enabled(self, selector_string, value):
        r"""Sets whether power measurement is performed. This measurement computes power of various fields in the PPDU.

        Additionally, this measurement computes power over the custom gates that you can configure using the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_NUMBER_OF_CUSTOM_GATES`, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_START_TIME` and the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_STOP_TIME` attributes.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------+
        | Name (Value) | Description                 |
        +==============+=============================+
        | False (0)    | Disables power measurement. |
        +--------------+-----------------------------+
        | True (1)     | Enables power measurement.  |
        +--------------+-----------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccPowerMeasurementEnabled, int):
                Specifies whether power measurement is performed. This measurement computes power of various fields in the PPDU.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccPowerMeasurementEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_POWER_MEASUREMENT_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_number_of_custom_gates(self, selector_string):
        r"""Gets the number of custom gates used for power measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of custom gates used for power measurement.

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
                attributes.AttributeID.DSSSMODACC_POWER_NUMBER_OF_CUSTOM_GATES.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_number_of_custom_gates(self, selector_string, value):
        r"""Sets the number of custom gates used for power measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of custom gates used for power measurement.

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
                attributes.AttributeID.DSSSMODACC_POWER_NUMBER_OF_CUSTOM_GATES.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_custom_gate_start_time(self, selector_string):
        r"""Gets the start time of the custom power gate. This value is expressed in seconds.

        Use "gate<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        A value of 0 indicates that the start time is the start of the PPDU. The default value is 0 seconds.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the start time of the custom power gate. This value is expressed in seconds.

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
                attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_START_TIME.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_custom_gate_start_time(self, selector_string, value):
        r"""Sets the start time of the custom power gate. This value is expressed in seconds.

        Use "gate<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        A value of 0 indicates that the start time is the start of the PPDU. The default value is 0 seconds.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the start time of the custom power gate. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_START_TIME.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_custom_gate_stop_time(self, selector_string):
        r"""Gets the stop time for the custom power gate. This value is expressed in seconds.

        Use "gate<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 10 microseconds.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the stop time for the custom power gate. This value is expressed in seconds.

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
                attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_STOP_TIME.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_custom_gate_stop_time(self, selector_string, value):
        r"""Sets the stop time for the custom power gate. This value is expressed in seconds.

        Use "gate<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 10 microseconds.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the stop time for the custom power gate. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.set_attribute_f64(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_STOP_TIME.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency_error_correction_enabled(self, selector_string):
        r"""Gets whether to enable frequency error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------+
        | Name (Value) | Description                          |
        +==============+======================================+
        | False (0)    | Disables frequency error correction. |
        +--------------+--------------------------------------+
        | True (1)     | Enables frequency error correction.  |
        +--------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccFrequencyErrorCorrectionEnabled):
                Specifies whether to enable frequency error correction.

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
                attributes.AttributeID.DSSSMODACC_FREQUENCY_ERROR_CORRECTION_ENABLED.value,
            )
            attr_val = enums.DsssModAccFrequencyErrorCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency_error_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable frequency error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------+
        | Name (Value) | Description                          |
        +==============+======================================+
        | False (0)    | Disables frequency error correction. |
        +--------------+--------------------------------------+
        | True (1)     | Enables frequency error correction.  |
        +--------------+--------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccFrequencyErrorCorrectionEnabled, int):
                Specifies whether to enable frequency error correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.DsssModAccFrequencyErrorCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_FREQUENCY_ERROR_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_chip_clock_error_correction_enabled(self, selector_string):
        r"""Gets whether to enable chip clock error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | False (0)    | Disables the chip clock error correction. |
        +--------------+-------------------------------------------+
        | True (1)     | Enables the chip clock error correction.  |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccChipClockErrorCorrectionEnabled):
                Specifies whether to enable chip clock error correction.

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
                attributes.AttributeID.DSSSMODACC_CHIP_CLOCK_ERROR_CORRECTION_ENABLED.value,
            )
            attr_val = enums.DsssModAccChipClockErrorCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_chip_clock_error_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable chip clock error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | False (0)    | Disables the chip clock error correction. |
        +--------------+-------------------------------------------+
        | True (1)     | Enables the chip clock error correction.  |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccChipClockErrorCorrectionEnabled, int):
                Specifies whether to enable chip clock error correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.DsssModAccChipClockErrorCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_CHIP_CLOCK_ERROR_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_origin_offset_correction_enabled(self, selector_string):
        r"""Gets whether to enable I/Q origin offset correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | False (0)    | Disables the I/Q origin offset correction. |
        +--------------+--------------------------------------------+
        | True (1)     | Enables the I/Q origin offset correction.  |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccIQOriginOffsetCorrectionEnabled):
                Specifies whether to enable I/Q origin offset correction.

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
                attributes.AttributeID.DSSSMODACC_IQ_ORIGIN_OFFSET_CORRECTION_ENABLED.value,
            )
            attr_val = enums.DsssModAccIQOriginOffsetCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_origin_offset_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable I/Q origin offset correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | False (0)    | Disables the I/Q origin offset correction. |
        +--------------+--------------------------------------------+
        | True (1)     | Enables the I/Q origin offset correction.  |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccIQOriginOffsetCorrectionEnabled, int):
                Specifies whether to enable I/Q origin offset correction.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = (
                value.value
                if type(value) is enums.DsssModAccIQOriginOffsetCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_IQ_ORIGIN_OFFSET_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_spectrum_inverted(self, selector_string):
        r"""Gets whether the spectrum of the measured signal is inverted.

        The inversion occurs when the I and the Q components of the baseband complex signal are swapped.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                     |
        +==============+=================================================================================================================+
        | False (0)    | The spectrum of the measured signal is not inverted.                                                            |
        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components. |
        +--------------+-----------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccSpectrumInverted):
                Specifies whether the spectrum of the measured signal is inverted.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_SPECTRUM_INVERTED.value
            )
            attr_val = enums.DsssModAccSpectrumInverted(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spectrum_inverted(self, selector_string, value):
        r"""Sets whether the spectrum of the measured signal is inverted.

        The inversion occurs when the I and the Q components of the baseband complex signal are swapped.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                     |
        +==============+=================================================================================================================+
        | False (0)    | The spectrum of the measured signal is not inverted.                                                            |
        +--------------+-----------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components. |
        +--------------+-----------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccSpectrumInverted, int):
                Specifies whether the spectrum of the measured signal is inverted.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccSpectrumInverted else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_SPECTRUM_INVERTED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_data_decoding_enabled(self, selector_string):
        r"""Gets whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).

        .. note::
           Set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_MAXIMUM_MEASUREMENT_LENGTH` attribute to -1 to decode
           all chips. Data decoding is not supported if the data rate is 33 Mbps.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------+
        | Name (Value) | Description             |
        +==============+=========================+
        | False (0)    | Disables data decoding. |
        +--------------+-------------------------+
        | True (1)     | Enables data decoding.  |
        +--------------+-------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccDataDecodingEnabled):
                Specifies whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).

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
                attributes.AttributeID.DSSSMODACC_DATA_DECODING_ENABLED.value,
            )
            attr_val = enums.DsssModAccDataDecodingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_data_decoding_enabled(self, selector_string, value):
        r"""Sets whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).

        .. note::
           Set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_MAXIMUM_MEASUREMENT_LENGTH` attribute to -1 to decode
           all chips. Data decoding is not supported if the data rate is 33 Mbps.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------+
        | Name (Value) | Description             |
        +==============+=========================+
        | False (0)    | Disables data decoding. |
        +--------------+-------------------------+
        | True (1)     | Enables data decoding.  |
        +--------------+-------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccDataDecodingEnabled, int):
                Specifies whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccDataDecodingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_DATA_DECODING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for DSSSModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Performs measurement on a single acquisition.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Measurement uses the DSSSModAcc Averaging Count attribute for the number of acquisitions using which the results are     |
        |              | averaged.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DsssModAccAveragingEnabled):
                Specifies whether to enable averaging for DSSSModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED.value
            )
            attr_val = enums.DsssModAccAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for DSSSModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Performs measurement on a single acquisition.                                                                            |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Measurement uses the DSSSModAcc Averaging Count attribute for the number of acquisitions using which the results are     |
        |              | averaged.                                                                                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DsssModAccAveragingEnabled, int):
                Specifies whether to enable averaging for DSSSModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.DsssModAccAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.DSSSMODACC_AVERAGING_COUNT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable all the traces computed by DSSSModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (bool):
                Specifies whether to enable all the traces computed by DSSSModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.DSSSMODACC_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable all the traces computed by DSSSModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable all the traces computed by DSSSModAcc measurement.

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
                attributes.AttributeID.DSSSMODACC_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for DSSSModAcc measurement.

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
                Specifies the maximum number of threads used for parallelism for DSSSModAcc measurement.

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
                attributes.AttributeID.DSSSMODACC_NUMBER_OF_ANALYSIS_THREADS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for DSSSModAcc measurement.

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
                Specifies the maximum number of threads used for parallelism for DSSSModAcc measurement.

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
                attributes.AttributeID.DSSSMODACC_NUMBER_OF_ANALYSIS_THREADS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_acquisition_length(
        self, selector_string, acquisition_length_mode, acquisition_length
    ):
        r"""Configures the **Acquisition Length** parameter and the **Acquisition Length Mode** parameter of the acquired waveform
        for the measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            acquisition_length_mode (enums.DsssModAccAcquisitionLengthMode, int):
                This parameter specifies whether the measurement automatically computes the acquisition length of the waveform based on
                DSSSModAcc attributes. The default value is **Auto**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | Manual (0)   | Uses the acquisition length specified by the Acquisition Length parameter.                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Auto (1)     | Computes the acquisition length based on the DSSSModAcc Meas Offset attribute and the DSSSModAcc Max Meas Length         |
                |              | attribute.                                                                                                               |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            acquisition_length (float):
                This parameter specifies the length of the waveform to be acquired for the DSSSModAcc measurement when you set the
                **Acquisition Length Mode** parameter to **Manual**. This value is expressed in seconds. The default value is 0.001.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            acquisition_length_mode = (
                acquisition_length_mode.value
                if type(acquisition_length_mode) is enums.DsssModAccAcquisitionLengthMode
                else acquisition_length_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.dsssmodacc_configure_acquisition_length(
                updated_selector_string, acquisition_length_mode, acquisition_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_averaging(self, selector_string, averaging_enabled, averaging_count):
        r"""Configures averaging for the measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            averaging_enabled (enums.DsssModAccAveragingEnabled, int):
                This parameter specifies whether to enable averaging for DSSSModAcc measurements. The default value is **False**.

                +--------------+-----------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                           |
                +==============+=======================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                 |
                +--------------+-----------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses the Averaging Count parameter as the number of acquisitions over which the results are averaged. |
                +--------------+-----------------------------------------------------------------------------------------------------------------------+

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
                if type(averaging_enabled) is enums.DsssModAccAveragingEnabled
                else averaging_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.dsssmodacc_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_evm_unit(self, selector_string, evm_unit):
        r"""Configures EVM unit for the measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            evm_unit (enums.DsssModAccEvmUnit, int):
                This parameter specifies the unit for the EVM results. The default value is **Percentage**.

                +----------------+-------------------------------------------+
                | Name (Value)   | Description                               |
                +================+===========================================+
                | dB (0)         | EVM results are returned in dB.           |
                +----------------+-------------------------------------------+
                | Percentage (1) | EVM results are returned as a percentage. |
                +----------------+-------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            evm_unit = evm_unit.value if type(evm_unit) is enums.DsssModAccEvmUnit else evm_unit
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.dsssmodacc_configure_evm_unit(
                updated_selector_string, evm_unit
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_length(
        self, selector_string, measurement_offset, maximum_measurement_length
    ):
        r"""Configures the measurement offset and the maximum measurement length for the DSSSModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_offset (int):
                This parameter specifies the number of data chips to be ignored from the start of the data field for the EVM
                computation. This value is expressed in chips. The default value is 0.

            maximum_measurement_length (int):
                This parameter specifies the maximum number of data chips that the measurement uses to compute EVM. This value is
                expressed in chips. The default value is 1000.

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
            error_code = self._interpreter.dsssmodacc_configure_measurement_length(
                updated_selector_string, measurement_offset, maximum_measurement_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_power_measurement_custom_gate_array(self, selector_string, start_time, stop_time):
        r"""Configures the custom gate start and stop times for power measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            start_time (float):
                This parameter specifies the array of start time of the custom power gates. This value is expressed in seconds. A value
                of 0 indicates that the start time is the start of the PPDU. The default value is an empty array.

            stop_time (float):
                This parameter specifies the array of stop time of the custom power gates. This value is expressed in seconds. The
                default value is an empty array.

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
            error_code = self._interpreter.dsssmodacc_configure_power_measurement_custom_gate_array(
                updated_selector_string, start_time, stop_time
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_power_measurement_enabled(self, selector_string, power_measurement_enabled):
        r"""Configures whether power measurement is enabled for the DSSSModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            power_measurement_enabled (enums.DsssModAccPowerMeasurementEnabled, int):
                This parameter specifies if power measurement is performed. This parameter computes power of various fields in the
                PPDU. Additionally, this measurement computes power over the custom gates that you can configure using the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_NUMBER_OF_CUSTOM_GATES`, the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_START_TIME` and the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_POWER_CUSTOM_GATE_STOP_TIME` attributes. The default value is
                **False**.

                +--------------+-----------------------------+
                | Name (Value) | Description                 |
                +==============+=============================+
                | False (0)    | Disables power measurement. |
                +--------------+-----------------------------+
                | True (1)     | Enables power measurement.  |
                +--------------+-----------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            power_measurement_enabled = (
                power_measurement_enabled.value
                if type(power_measurement_enabled) is enums.DsssModAccPowerMeasurementEnabled
                else power_measurement_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.dsssmodacc_configure_power_measurement_enabled(
                updated_selector_string, power_measurement_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_power_measurement_number_of_custom_gates(
        self, selector_string, number_of_custom_gates
    ):
        r"""Configures the number of custom gates for power measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            number_of_custom_gates (int):
                This parameter specifies the number of custom gates used for power measurement. The default value is 0.

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
            error_code = (
                self._interpreter.dsssmodacc_configure_power_measurement_number_of_custom_gates(
                    updated_selector_string, number_of_custom_gates
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
