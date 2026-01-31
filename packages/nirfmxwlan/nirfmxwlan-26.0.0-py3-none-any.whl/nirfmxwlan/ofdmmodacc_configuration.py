"""Provides methods to configure the OfdmModAcc measurement."""

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


class OfdmModAccConfiguration(object):
    """Provides methods to configure the OfdmModAcc measurement."""

    def __init__(self, signal_obj):
        """Provides methods to configure the OfdmModAcc measurement."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_measurement_enabled(self, selector_string):
        r"""Gets whether to enable OFDMModAcc measurement for OFDM based standards.

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
                Specifies whether to enable OFDMModAcc measurement for OFDM based standards.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_MEASUREMENT_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_enabled(self, selector_string, value):
        r"""Sets whether to enable OFDMModAcc measurement for OFDM based standards.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable OFDMModAcc measurement for OFDM based standards.

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
                attributes.AttributeID.OFDMMODACC_MEASUREMENT_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_enabled(self, selector_string):
        r"""Gets whether to enable averaging for OFDMModAcc measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the value of the OFDMModAcc Averaging Count attribute as the number of acquisitions over which the  |
        |              | results are computed according to the OFDMModAcc Averaging Type attribute.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccAveragingEnabled):
                Specifies whether to enable averaging for OFDMModAcc measurements.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED.value
            )
            attr_val = enums.OfdmModAccAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_enabled(self, selector_string, value):
        r"""Sets whether to enable averaging for OFDMModAcc measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | The measurement is performed on a single acquisition.                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | The measurement uses the value of the OFDMModAcc Averaging Count attribute as the number of acquisitions over which the  |
        |              | results are computed according to the OFDMModAcc Averaging Type attribute.                                               |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccAveragingEnabled, int):
                Specifies whether to enable averaging for OFDMModAcc measurements.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccAveragingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_count(self, selector_string):
        r"""Gets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**.

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
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_count(self, selector_string, value):
        r"""Sets the number of acquisitions used for averaging when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of acquisitions used for averaging when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**.

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
                attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_averaging_type(self, selector_string):
        r"""Gets the averaging type for the OFDMModAcc measurement.

        This attribute is considered only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True** and when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT` attribute is to a value greater than 1.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RMS**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | RMS (0)      | The OFDMModAcc measurement is performed on I/Q data acquired in each averaging count. The scalar results and traces are  |
        |              | linearly averaged over the averaging count.                                                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Vector (5)   | The acquired I/Q data is averaged across averaging count after aligning the data in time and phase using the OFDMModAcc  |
        |              | Vector Averaging Time Alignment Enabled and OFDMModAcc Vector Averaging Phase Alignment Enabled properties,              |
        |              | respectively. The averaged I/Q data is used for the measurement. Refer to the Vector Averaging concept topic for more    |
        |              | information. You must ensure that the frequency reference is locked between the generator and the analyzer.              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccAveragingType):
                Specifies the averaging type for the OFDMModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE.value
            )
            attr_val = enums.OfdmModAccAveragingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_averaging_type(self, selector_string, value):
        r"""Sets the averaging type for the OFDMModAcc measurement.

        This attribute is considered only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True** and when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT` attribute is to a value greater than 1.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **RMS**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | RMS (0)      | The OFDMModAcc measurement is performed on I/Q data acquired in each averaging count. The scalar results and traces are  |
        |              | linearly averaged over the averaging count.                                                                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Vector (5)   | The acquired I/Q data is averaged across averaging count after aligning the data in time and phase using the OFDMModAcc  |
        |              | Vector Averaging Time Alignment Enabled and OFDMModAcc Vector Averaging Phase Alignment Enabled properties,              |
        |              | respectively. The averaged I/Q data is used for the measurement. Refer to the Vector Averaging concept topic for more    |
        |              | information. You must ensure that the frequency reference is locked between the generator and the analyzer.              |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccAveragingType, int):
                Specifies the averaging type for the OFDMModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccAveragingType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_vector_averaging_time_alignment_enabled(self, selector_string):
        r"""Gets whether to enable time alignment for the acquired I/Q data across multiple acquisitions.

        This attribute is considered only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT` attribute to a value greater than 1, and when
        you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE` attribute to **Vector**. You can
        set this attribute to **False** when there is no time offset between the acquired I/Q data of all averaging counts.
        Refer to the `OFDMModAcc Vector Averaging
        <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/ofdmmodacc-vector-averaging.html>`_ concept topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                     |
        +==============+=================================================================================+
        | False (0)    | Disables time alignment for the acquired I/Q data across multiple acquisitions. |
        +--------------+---------------------------------------------------------------------------------+
        | True (1)     | Enables time alignment for the acquired I/Q data across multiple acquisitions.  |
        +--------------+---------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccVectorAveragingTimeAlignmentEnabled):
                Specifies whether to enable time alignment for the acquired I/Q data across multiple acquisitions.

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
                attributes.AttributeID.OFDMMODACC_VECTOR_AVERAGING_TIME_ALIGNMENT_ENABLED.value,
            )
            attr_val = enums.OfdmModAccVectorAveragingTimeAlignmentEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_vector_averaging_time_alignment_enabled(self, selector_string, value):
        r"""Sets whether to enable time alignment for the acquired I/Q data across multiple acquisitions.

        This attribute is considered only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT` attribute to a value greater than 1, and when
        you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE` attribute to **Vector**. You can
        set this attribute to **False** when there is no time offset between the acquired I/Q data of all averaging counts.
        Refer to the `OFDMModAcc Vector Averaging
        <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/ofdmmodacc-vector-averaging.html>`_ concept topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                     |
        +==============+=================================================================================+
        | False (0)    | Disables time alignment for the acquired I/Q data across multiple acquisitions. |
        +--------------+---------------------------------------------------------------------------------+
        | True (1)     | Enables time alignment for the acquired I/Q data across multiple acquisitions.  |
        +--------------+---------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccVectorAveragingTimeAlignmentEnabled, int):
                Specifies whether to enable time alignment for the acquired I/Q data across multiple acquisitions.

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
                if type(value) is enums.OfdmModAccVectorAveragingTimeAlignmentEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_VECTOR_AVERAGING_TIME_ALIGNMENT_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_vector_averaging_phase_alignment_enabled(self, selector_string):
        r"""Gets whether to enable phase alignment for the acquired I/Q data across multiple acquisitions.

        This attribute is considered only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT` attribute to a value greater than 1, and when
        you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE` attribute to **Vector**. You can
        set this attribute to **False** when there is no phase offset between the acquired I/Q data of all averaging counts.
        Refer to the `OFDMModAcc Vector Averaging
        <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/ofdmmodacc-vector-averaging.html>`_ concept topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | Disables phase alignment for the acquired I/Q data across multiple acquisitions. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | Enables phase alignment for the acquired I/Q data across multiple acquisitions.  |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccVectorAveragingPhaseAlignmentEnabled):
                Specifies whether to enable phase alignment for the acquired I/Q data across multiple acquisitions.

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
                attributes.AttributeID.OFDMMODACC_VECTOR_AVERAGING_PHASE_ALIGNMENT_ENABLED.value,
            )
            attr_val = enums.OfdmModAccVectorAveragingPhaseAlignmentEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_vector_averaging_phase_alignment_enabled(self, selector_string, value):
        r"""Sets whether to enable phase alignment for the acquired I/Q data across multiple acquisitions.

        This attribute is considered only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_COUNT` attribute to a value greater than 1, and when
        you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_TYPE` attribute to **Vector**. You can
        set this attribute to **False** when there is no phase offset between the acquired I/Q data of all averaging counts.
        Refer to the `OFDMModAcc Vector Averaging
        <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/ofdmmodacc-vector-averaging.html>`_ concept topic for more information.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | Disables phase alignment for the acquired I/Q data across multiple acquisitions. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | Enables phase alignment for the acquired I/Q data across multiple acquisitions.  |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccVectorAveragingPhaseAlignmentEnabled, int):
                Specifies whether to enable phase alignment for the acquired I/Q data across multiple acquisitions.

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
                if type(value) is enums.OfdmModAccVectorAveragingPhaseAlignmentEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_VECTOR_AVERAGING_PHASE_ALIGNMENT_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_mode(self, selector_string):
        r"""Gets whether the measurement calibrates the noise floor of analyzer or performs the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                                                              |
        +===========================+==========================================================================================================================+
        | Measure (0)               | The OFDMModAcc measurement is performed on the acquired signal.                                                          |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | The OFDMModAcc measurement measures the noise floor of the instrument across the frequency range of interest determined  |
        |                           | by the carrier frequency and channel bandwidth. In this mode, the measurement expects that the signal generator to be    |
        |                           | turned off and checks whether no signal power is detected at the RF In port of the analyzer beyond a certain threshold.  |
        |                           | All scalar results and traces are invalid in this mode. Even if the instrument noise floor is previously calibrated,     |
        |                           | the measurement performs all the required acquisitions and overwrites any pre-existing noise floor calibration data.     |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccMeasurementMode):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the ModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_MEASUREMENT_MODE.value
            )
            attr_val = enums.OfdmModAccMeasurementMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_mode(self, selector_string, value):
        r"""Sets whether the measurement calibrates the noise floor of analyzer or performs the ModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Measure**.

        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)              | Description                                                                                                              |
        +===========================+==========================================================================================================================+
        | Measure (0)               | The OFDMModAcc measurement is performed on the acquired signal.                                                          |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Calibrate Noise Floor (1) | The OFDMModAcc measurement measures the noise floor of the instrument across the frequency range of interest determined  |
        |                           | by the carrier frequency and channel bandwidth. In this mode, the measurement expects that the signal generator to be    |
        |                           | turned off and checks whether no signal power is detected at the RF In port of the analyzer beyond a certain threshold.  |
        |                           | All scalar results and traces are invalid in this mode. Even if the instrument noise floor is previously calibrated,     |
        |                           | the measurement performs all the required acquisitions and overwrites any pre-existing noise floor calibration data.     |
        +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccMeasurementMode, int):
                Specifies whether the measurement calibrates the noise floor of analyzer or performs the ModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccMeasurementMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_MEASUREMENT_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_reference_data_symbols_mode(self, selector_string):
        r"""Gets whether to use an acquired waveform or a reference waveform to create reference data symbols (ideal
        constellation points) for an EVM computation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Acquired Waveform**.

        +------------------------+-----------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                             |
        +========================+=========================================================================================+
        | Acquired Waveform (0)  | Reference data symbols for an EVM computation are created using the acquired waveform.  |
        +------------------------+-----------------------------------------------------------------------------------------+
        | Reference Waveform (1) | Reference data symbols for an EVM computation are created using the reference waveform. |
        +------------------------+-----------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccEvmReferenceDataSymbolsMode):
                Specifies whether to use an acquired waveform or a reference waveform to create reference data symbols (ideal
                constellation points) for an EVM computation.

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
                attributes.AttributeID.OFDMMODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE.value,
            )
            attr_val = enums.OfdmModAccEvmReferenceDataSymbolsMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_reference_data_symbols_mode(self, selector_string, value):
        r"""Sets whether to use an acquired waveform or a reference waveform to create reference data symbols (ideal
        constellation points) for an EVM computation.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Acquired Waveform**.

        +------------------------+-----------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                             |
        +========================+=========================================================================================+
        | Acquired Waveform (0)  | Reference data symbols for an EVM computation are created using the acquired waveform.  |
        +------------------------+-----------------------------------------------------------------------------------------+
        | Reference Waveform (1) | Reference data symbols for an EVM computation are created using the reference waveform. |
        +------------------------+-----------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccEvmReferenceDataSymbolsMode, int):
                Specifies whether to use an acquired waveform or a reference waveform to create reference data symbols (ideal
                constellation points) for an EVM computation.

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
                value.value if type(value) is enums.OfdmModAccEvmReferenceDataSymbolsMode else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_evm_unit(self, selector_string):
        r"""Gets the unit for EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **dB**.

        +----------------+-----------------------------------------------+
        | Name (Value)   | Description                                   |
        +================+===============================================+
        | Percentage (0) | The EVM results are returned as a percentage. |
        +----------------+-----------------------------------------------+
        | dB (1)         | The EVM results are returned in dB.           |
        +----------------+-----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccEvmUnit):
                Specifies the unit for EVM results.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_EVM_UNIT.value
            )
            attr_val = enums.OfdmModAccEvmUnit(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_evm_unit(self, selector_string, value):
        r"""Sets the unit for EVM results.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **dB**.

        +----------------+-----------------------------------------------+
        | Name (Value)   | Description                                   |
        +================+===============================================+
        | Percentage (0) | The EVM results are returned as a percentage. |
        +----------------+-----------------------------------------------+
        | dB (1)         | The EVM results are returned in dB.           |
        +----------------+-----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccEvmUnit, int):
                Specifies the unit for EVM results.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccEvmUnit else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_EVM_UNIT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_acquisition_length_mode(self, selector_string):
        r"""Gets whether the measurement automatically computes the acquisition length of the waveform based on other
        OFDMModAcc attributes.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                        |
        +==============+====================================================================================================================+
        | Manual (0)   | Uses the acquisition length specified by the OFDMModAcc Acquisition Length attribute.                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | Computes the acquisition length based on the OFDMModAcc Meas Offset and the OFDMModAcc Max Meas Length attributes. |
        +--------------+--------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccAcquisitionLengthMode):
                Specifies whether the measurement automatically computes the acquisition length of the waveform based on other
                OFDMModAcc attributes.

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
                attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE.value,
            )
            attr_val = enums.OfdmModAccAcquisitionLengthMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_acquisition_length_mode(self, selector_string, value):
        r"""Sets whether the measurement automatically computes the acquisition length of the waveform based on other
        OFDMModAcc attributes.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                        |
        +==============+====================================================================================================================+
        | Manual (0)   | Uses the acquisition length specified by the OFDMModAcc Acquisition Length attribute.                              |
        +--------------+--------------------------------------------------------------------------------------------------------------------+
        | Auto (1)     | Computes the acquisition length based on the OFDMModAcc Meas Offset and the OFDMModAcc Max Meas Length attributes. |
        +--------------+--------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccAcquisitionLengthMode, int):
                Specifies whether the measurement automatically computes the acquisition length of the waveform based on other
                OFDMModAcc attributes.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccAcquisitionLengthMode else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_acquisition_length(self, selector_string):
        r"""Gets the length of the waveform to be acquired for the OFDMModAcc measurement, when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
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
                Specifies the length of the waveform to be acquired for the OFDMModAcc measurement, when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
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
                updated_selector_string, attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_acquisition_length(self, selector_string, value):
        r"""Sets the length of the waveform to be acquired for the OFDMModAcc measurement, when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
        expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 millisecond.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the length of the waveform to be acquired for the OFDMModAcc measurement, when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
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
                attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_measurement_offset(self, selector_string):
        r"""Gets the number of data symbols to be ignored from the start of the data field for EVM computation. This value is
        expressed in symbols.

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
                Specifies the number of data symbols to be ignored from the start of the data field for EVM computation. This value is
                expressed in symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_measurement_offset(self, selector_string, value):
        r"""Sets the number of data symbols to be ignored from the start of the data field for EVM computation. This value is
        expressed in symbols.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of data symbols to be ignored from the start of the data field for EVM computation. This value is
                expressed in symbols.

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
                attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_maximum_measurement_length(self, selector_string):
        r"""Gets the maximum number of OFDM symbols that the measurement uses to compute EVM. This value is expressed in
        symbols.

        If the number of available data symbols (*n*) is greater than the value that you specify (*m*), the measurement
        ignores (*n*-*m*) symbols from the end of the data field. If you set this attribute to -1, all symbols in the data
        field are used to compute the EVM.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 16.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the maximum number of OFDM symbols that the measurement uses to compute EVM. This value is expressed in
                symbols.

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
                attributes.AttributeID.OFDMMODACC_MAXIMUM_MEASUREMENT_LENGTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_maximum_measurement_length(self, selector_string, value):
        r"""Sets the maximum number of OFDM symbols that the measurement uses to compute EVM. This value is expressed in
        symbols.

        If the number of available data symbols (*n*) is greater than the value that you specify (*m*), the measurement
        ignores (*n*-*m*) symbols from the end of the data field. If you set this attribute to -1, all symbols in the data
        field are used to compute the EVM.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 16.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the maximum number of OFDM symbols that the measurement uses to compute EVM. This value is expressed in
                symbols.

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
                attributes.AttributeID.OFDMMODACC_MAXIMUM_MEASUREMENT_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_combined_signal_demodulation_enabled(self, selector_string):
        r"""Gets whether to enable demodulation of the signal that is formed by combining signals from multiple transmitter
        chains.

        This attribute can be set to True only if you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD`
        attribute to **802.11n**, **802.11ac**, **802.11ax** or **802.11be**.

        The default value is **False**.

        +--------------+-------------------------------------------------+
        | Name (Value) | Description                                     |
        +==============+=================================================+
        | False (0)    | Disables combined signal demodulation analysis. |
        +--------------+-------------------------------------------------+
        | True (1)     | Enables combined signal demodulation analysis.  |
        +--------------+-------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccCombinedSignalDemodulationEnabled):
                Specifies whether to enable demodulation of the signal that is formed by combining signals from multiple transmitter
                chains.

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
                attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccCombinedSignalDemodulationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_combined_signal_demodulation_enabled(self, selector_string, value):
        r"""Sets whether to enable demodulation of the signal that is formed by combining signals from multiple transmitter
        chains.

        This attribute can be set to True only if you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD`
        attribute to **802.11n**, **802.11ac**, **802.11ax** or **802.11be**.

        The default value is **False**.

        +--------------+-------------------------------------------------+
        | Name (Value) | Description                                     |
        +==============+=================================================+
        | False (0)    | Disables combined signal demodulation analysis. |
        +--------------+-------------------------------------------------+
        | True (1)     | Enables combined signal demodulation analysis.  |
        +--------------+-------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccCombinedSignalDemodulationEnabled, int):
                Specifies whether to enable demodulation of the signal that is formed by combining signals from multiple transmitter
                chains.

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
                if type(value) is enums.OfdmModAccCombinedSignalDemodulationEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_data_constellation_identifier(self, selector_string):
        r"""Identifies the reference files used for combined signal demodulation. The value of this attribute must be same as the
        value of the Reference Data Identifier string specified while creating the reference files. This is applicable only if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        The default value is "" (empty string).

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Identifies the reference files used for combined signal demodulation. The value of this attribute must be same as the
                value of the Reference Data Identifier string specified while creating the reference files. This is applicable only if
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_string(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_REFERENCE_DATA_CONSTELLATION_IDENTIFIER.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_data_constellation_identifier(self, selector_string, value):
        r"""Identifies the reference files used for combined signal demodulation. The value of this attribute must be same as the
        value of the Reference Data Identifier string specified while creating the reference files. This is applicable only if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        The default value is "" (empty string).

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Identifies the reference files used for combined signal demodulation. The value of this attribute must be same as the
                value of the Reference Data Identifier string specified while creating the reference files. This is applicable only if
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_REFERENCE_DATA_CONSTELLATION_IDENTIFIER.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_burst_start_detection_enabled(self, selector_string):
        r"""Gets whether the measurement detects a rising edge of a burst in the acquired waveform.

        If you are using an I/Q power edge trigger or digital edge trigger to trigger approximately and consistently at
        the start of a burst, set this attribute to **False**. If you are unable to reliably trigger at the start of a burst,
        set this attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Disables detecting a rising edge of a burst in the acquired waveform. |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Enables detecting a rising edge of a burst in the acquired waveform.  |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccBurstStartDetectionEnabled):
                Specifies whether the measurement detects a rising edge of a burst in the acquired waveform.

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
                attributes.AttributeID.OFDMMODACC_BURST_START_DETECTION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccBurstStartDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_burst_start_detection_enabled(self, selector_string, value):
        r"""Sets whether the measurement detects a rising edge of a burst in the acquired waveform.

        If you are using an I/Q power edge trigger or digital edge trigger to trigger approximately and consistently at
        the start of a burst, set this attribute to **False**. If you are unable to reliably trigger at the start of a burst,
        set this attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Disables detecting a rising edge of a burst in the acquired waveform. |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Enables detecting a rising edge of a burst in the acquired waveform.  |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccBurstStartDetectionEnabled, int):
                Specifies whether the measurement detects a rising edge of a burst in the acquired waveform.

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
                value.value if type(value) is enums.OfdmModAccBurstStartDetectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_BURST_START_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_frequency_error_estimation_method(self, selector_string):
        r"""Gets the PPDU fields that the measurement uses to estimate the carrier frequency error in the acquired signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Preamble and Pilots**.

        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                  | Description                                                                                                      |
        +===============================+==================================================================================================================+
        | Disabled (0)                  | Carrier frequency error is not computed and the corresponding result is returned as NaN.                         |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Initial Preamble (1)          | Initial short and long training fields in the PPDU are used.                                                     |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Preamble (2)                  | Initial short and long training fields along with the SIGnal fields are used.                                    |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Preamble and Pilots (3)       | The initial short and long training fields, SIGnal fields, and the pilot subcarriers in the DATA field are used. |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Preamble, Pilots and Data (4) | The initial short and long training fields, SIGnal fields, and all the subcarriers in the DATA field are used.   |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccFrequencyErrorEstimationMethod):
                Specifies the PPDU fields that the measurement uses to estimate the carrier frequency error in the acquired signal.

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
                attributes.AttributeID.OFDMMODACC_FREQUENCY_ERROR_ESTIMATION_METHOD.value,
            )
            attr_val = enums.OfdmModAccFrequencyErrorEstimationMethod(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_frequency_error_estimation_method(self, selector_string, value):
        r"""Sets the PPDU fields that the measurement uses to estimate the carrier frequency error in the acquired signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Preamble and Pilots**.

        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                  | Description                                                                                                      |
        +===============================+==================================================================================================================+
        | Disabled (0)                  | Carrier frequency error is not computed and the corresponding result is returned as NaN.                         |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Initial Preamble (1)          | Initial short and long training fields in the PPDU are used.                                                     |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Preamble (2)                  | Initial short and long training fields along with the SIGnal fields are used.                                    |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Preamble and Pilots (3)       | The initial short and long training fields, SIGnal fields, and the pilot subcarriers in the DATA field are used. |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+
        | Preamble, Pilots and Data (4) | The initial short and long training fields, SIGnal fields, and all the subcarriers in the DATA field are used.   |
        +-------------------------------+------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccFrequencyErrorEstimationMethod, int):
                Specifies the PPDU fields that the measurement uses to estimate the carrier frequency error in the acquired signal.

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
                if type(value) is enums.OfdmModAccFrequencyErrorEstimationMethod
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_FREQUENCY_ERROR_ESTIMATION_METHOD.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_common_clock_source_enabled(self, selector_string):
        r"""Gets whether the transmitter uses the same reference clock signal for generating the RF carrier and the symbol
        clock.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Specifies that the transmitter does not use a common reference clock. The OFDMModAcc measurement computes the symbol     |
        |              | clock error and carrier frequency error independently.                                                                   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Specifies that the transmitter uses a common reference clock. The OFDMModAcc measurement derives the symbol clock error  |
        |              | from the configured center frequency and carrier frequency error.                                                        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccCommonClockSourceEnabled):
                Specifies whether the transmitter uses the same reference clock signal for generating the RF carrier and the symbol
                clock.

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
                attributes.AttributeID.OFDMMODACC_COMMON_CLOCK_SOURCE_ENABLED.value,
            )
            attr_val = enums.OfdmModAccCommonClockSourceEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_common_clock_source_enabled(self, selector_string, value):
        r"""Sets whether the transmitter uses the same reference clock signal for generating the RF carrier and the symbol
        clock.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Specifies that the transmitter does not use a common reference clock. The OFDMModAcc measurement computes the symbol     |
        |              | clock error and carrier frequency error independently.                                                                   |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Specifies that the transmitter uses a common reference clock. The OFDMModAcc measurement derives the symbol clock error  |
        |              | from the configured center frequency and carrier frequency error.                                                        |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccCommonClockSourceEnabled, int):
                Specifies whether the transmitter uses the same reference clock signal for generating the RF carrier and the symbol
                clock.

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
                value.value if type(value) is enums.OfdmModAccCommonClockSourceEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_COMMON_CLOCK_SOURCE_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_common_pilot_error_scaling_reference(self, selector_string):
        r"""Gets whether common pilot error is computed relative to only  LTF  or scaling by average CPE.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Average CPE**.

        +-----------------+---------------------------------------------------------------------------------------------------------+
        | Name (Value)    | Description                                                                                             |
        +=================+=========================================================================================================+
        | None (0)        | Specifies that Common Pilot Error is computed relative to only LTF and no scaling is performed.         |
        +-----------------+---------------------------------------------------------------------------------------------------------+
        | Average CPE (1) | Specifies that Common Pilot Error is computed relative to LTF and scaling by average CPE                |
        |                 | is performed.                                                                                           |
        +-----------------+---------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccCommonPilotErrorScalingReference):
                Specifies whether common pilot error is computed relative to only  LTF  or scaling by average CPE.

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
                attributes.AttributeID.OFDMMODACC_COMMON_PILOT_ERROR_SCALING_REFERENCE.value,
            )
            attr_val = enums.OfdmModAccCommonPilotErrorScalingReference(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_common_pilot_error_scaling_reference(self, selector_string, value):
        r"""Sets whether common pilot error is computed relative to only  LTF  or scaling by average CPE.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Average CPE**.

        +-----------------+---------------------------------------------------------------------------------------------------------+
        | Name (Value)    | Description                                                                                             |
        +=================+=========================================================================================================+
        | None (0)        | Specifies that Common Pilot Error is computed relative to only LTF and no scaling is performed.         |
        +-----------------+---------------------------------------------------------------------------------------------------------+
        | Average CPE (1) | Specifies that Common Pilot Error is computed relative to LTF and scaling by average CPE                |
        |                 | is performed.                                                                                           |
        +-----------------+---------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccCommonPilotErrorScalingReference, int):
                Specifies whether common pilot error is computed relative to only  LTF  or scaling by average CPE.

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
                if type(value) is enums.OfdmModAccCommonPilotErrorScalingReference
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_COMMON_PILOT_ERROR_SCALING_REFERENCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_amplitude_tracking_enabled(self, selector_string):
        r"""Gets whether to enable pilot-based mean amplitude tracking per OFDM data symbol.

        Amplitude tracking is useful if the mean amplitude of the OFDM symbols in a PPDU varies over time. However,
        enabling tracking may degrade EVM because of attempts to track random amplitude distortions caused by additive noise
        and other distortions.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------+
        | Name (Value) | Description                     |
        +==============+=================================+
        | False (0)    | Amplitude tracking is disabled. |
        +--------------+---------------------------------+
        | True (1)     | Amplitude tracking is enabled.  |
        +--------------+---------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccAmplitudeTrackingEnabled):
                Specifies whether to enable pilot-based mean amplitude tracking per OFDM data symbol.

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
                attributes.AttributeID.OFDMMODACC_AMPLITUDE_TRACKING_ENABLED.value,
            )
            attr_val = enums.OfdmModAccAmplitudeTrackingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_amplitude_tracking_enabled(self, selector_string, value):
        r"""Sets whether to enable pilot-based mean amplitude tracking per OFDM data symbol.

        Amplitude tracking is useful if the mean amplitude of the OFDM symbols in a PPDU varies over time. However,
        enabling tracking may degrade EVM because of attempts to track random amplitude distortions caused by additive noise
        and other distortions.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------+
        | Name (Value) | Description                     |
        +==============+=================================+
        | False (0)    | Amplitude tracking is disabled. |
        +--------------+---------------------------------+
        | True (1)     | Amplitude tracking is enabled.  |
        +--------------+---------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccAmplitudeTrackingEnabled, int):
                Specifies whether to enable pilot-based mean amplitude tracking per OFDM data symbol.

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
                value.value if type(value) is enums.OfdmModAccAmplitudeTrackingEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_AMPLITUDE_TRACKING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_phase_tracking_enabled(self, selector_string):
        r"""Gets whether to enable pilot-based common phase error correction per OFDM data symbol.

        Phase tracking is useful for tracking the phase variation over the modulation symbol caused by the residual
        frequency offset and phase noise.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-----------------------------+
        | Name (Value) | Description                 |
        +==============+=============================+
        | False (0)    | Phase tracking is disabled. |
        +--------------+-----------------------------+
        | True (1)     | Phase tracking is enabled.  |
        +--------------+-----------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccPhaseTrackingEnabled):
                Specifies whether to enable pilot-based common phase error correction per OFDM data symbol.

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
                attributes.AttributeID.OFDMMODACC_PHASE_TRACKING_ENABLED.value,
            )
            attr_val = enums.OfdmModAccPhaseTrackingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_phase_tracking_enabled(self, selector_string, value):
        r"""Sets whether to enable pilot-based common phase error correction per OFDM data symbol.

        Phase tracking is useful for tracking the phase variation over the modulation symbol caused by the residual
        frequency offset and phase noise.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-----------------------------+
        | Name (Value) | Description                 |
        +==============+=============================+
        | False (0)    | Phase tracking is disabled. |
        +--------------+-----------------------------+
        | True (1)     | Phase tracking is enabled.  |
        +--------------+-----------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccPhaseTrackingEnabled, int):
                Specifies whether to enable pilot-based common phase error correction per OFDM data symbol.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccPhaseTrackingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_PHASE_TRACKING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_symbol_clock_error_correction_enabled(self, selector_string):
        r"""Gets whether to enable symbol clock error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | False (0)    | Symbol clock error correction is disabled. |
        +--------------+--------------------------------------------+
        | True (1)     | Symbol clock error correction is enabled.  |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccSymbolClockErrorCorrectionEnabled):
                Specifies whether to enable symbol clock error correction.

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
                attributes.AttributeID.OFDMMODACC_SYMBOL_CLOCK_ERROR_CORRECTION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccSymbolClockErrorCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_symbol_clock_error_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable symbol clock error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | False (0)    | Symbol clock error correction is disabled. |
        +--------------+--------------------------------------------+
        | True (1)     | Symbol clock error correction is enabled.  |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccSymbolClockErrorCorrectionEnabled, int):
                Specifies whether to enable symbol clock error correction.

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
                if type(value) is enums.OfdmModAccSymbolClockErrorCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_SYMBOL_CLOCK_ERROR_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_spectrum_inverted(self, selector_string):
        r"""Gets whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
        components of the baseband complex signal are swapped.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

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

            attr_val (enums.OfdmModAccSpectrumInverted):
                Specifies whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
                components of the baseband complex signal are swapped.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_SPECTRUM_INVERTED.value
            )
            attr_val = enums.OfdmModAccSpectrumInverted(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_spectrum_inverted(self, selector_string, value):
        r"""Sets whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
        components of the baseband complex signal are swapped.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

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

            value (enums.OfdmModAccSpectrumInverted, int):
                Specifies whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
                components of the baseband complex signal are swapped.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccSpectrumInverted else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_SPECTRUM_INVERTED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_type(self, selector_string):
        r"""Gets the fields in the PPDU used to estimate the channel frequency response.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference**.

        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                                              |
        +========================+==========================================================================================================================+
        | Reference (0)          | The channel is estimated using long training fields (LTFs) in the preamble and the most recently received midamble, if   |
        |                        | present.                                                                                                                 |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference and Data (1) | The channel is estimated using long training fields (LTFs) in the preamble, the midamble (if present), and the data      |
        |                        | field.                                                                                                                   |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccChannelEstimationType):
                Specifies the fields in the PPDU used to estimate the channel frequency response.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_TYPE.value,
            )
            attr_val = enums.OfdmModAccChannelEstimationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_type(self, selector_string, value):
        r"""Sets the fields in the PPDU used to estimate the channel frequency response.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Reference**.

        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)           | Description                                                                                                              |
        +========================+==========================================================================================================================+
        | Reference (0)          | The channel is estimated using long training fields (LTFs) in the preamble and the most recently received midamble, if   |
        |                        | present.                                                                                                                 |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference and Data (1) | The channel is estimated using long training fields (LTFs) in the preamble, the midamble (if present), and the data      |
        |                        | field.                                                                                                                   |
        +------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccChannelEstimationType, int):
                Specifies the fields in the PPDU used to estimate the channel frequency response.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccChannelEstimationType else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_interpolation_type(self, selector_string):
        r"""Gets the interpolation type and/or smoothing type used on the channel estimates.

        The interpolation is applied only for 802.11ax, 802.11be, and 802.11bn signals when the LTF Size is 2x and 1x.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Linear**.

        +--------------------------+----------------------------------------------------------------------------------------------------------+
        | Name (Value)             | Description                                                                                              |
        +==========================+==========================================================================================================+
        | Linear (0)               | Linear interpolation is performed on reference channel estimates across subcarriers.                     |
        +--------------------------+----------------------------------------------------------------------------------------------------------+
        | Triangular Smoothing (1) | Channel estimates are smoothed using a triangular weighted moving average window across subcarriers.     |
        +--------------------------+----------------------------------------------------------------------------------------------------------+
        | Wiener Filter (2)        | Wiener filter is used for interpolation and smoothing on reference channel estimates across subcarriers. |
        +--------------------------+----------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccChannelEstimationInterpolationType):
                Specifies the interpolation type and/or smoothing type used on the channel estimates.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE.value,
            )
            attr_val = enums.OfdmModAccChannelEstimationInterpolationType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_interpolation_type(self, selector_string, value):
        r"""Sets the interpolation type and/or smoothing type used on the channel estimates.

        The interpolation is applied only for 802.11ax, 802.11be, and 802.11bn signals when the LTF Size is 2x and 1x.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Linear**.

        +--------------------------+----------------------------------------------------------------------------------------------------------+
        | Name (Value)             | Description                                                                                              |
        +==========================+==========================================================================================================+
        | Linear (0)               | Linear interpolation is performed on reference channel estimates across subcarriers.                     |
        +--------------------------+----------------------------------------------------------------------------------------------------------+
        | Triangular Smoothing (1) | Channel estimates are smoothed using a triangular weighted moving average window across subcarriers.     |
        +--------------------------+----------------------------------------------------------------------------------------------------------+
        | Wiener Filter (2)        | Wiener filter is used for interpolation and smoothing on reference channel estimates across subcarriers. |
        +--------------------------+----------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccChannelEstimationInterpolationType, int):
                Specifies the interpolation type and/or smoothing type used on the channel estimates.

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
                if type(value) is enums.OfdmModAccChannelEstimationInterpolationType
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_smoothing_length(self, selector_string):
        r"""Gets the length of the triangular-weighted moving window across subcarriers that is used for averaging the channel
        estimate.

        This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE`
        attribute to **Triangular Smoothing**. The window is always symmetrical about the subcarrier. The length of the window
        is reduced at the edges in order to keep it symmetrical. For a window length of *L*, the weights generated are 1, 2, 3,
        ..., (*L*+1)/2, ..., 3, 2, 1. For a fully occupied channel bandwidth, valid values are all odd numbers between 1 and
        half the number of subcarriers in the bandwidth, inclusive. For 802.11ax MU and TB PPDU signals,  802.11be MU and TB
        PPDU signals, and 802.11bn MU and TB PPDU signals, the valid values are all odd numbers between 1 and the size of the
        smallest RU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 5.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the length of the triangular-weighted moving window across subcarriers that is used for averaging the channel
                estimate.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_SMOOTHING_LENGTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_smoothing_length(self, selector_string, value):
        r"""Sets the length of the triangular-weighted moving window across subcarriers that is used for averaging the channel
        estimate.

        This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE`
        attribute to **Triangular Smoothing**. The window is always symmetrical about the subcarrier. The length of the window
        is reduced at the edges in order to keep it symmetrical. For a window length of *L*, the weights generated are 1, 2, 3,
        ..., (*L*+1)/2, ..., 3, 2, 1. For a fully occupied channel bandwidth, valid values are all odd numbers between 1 and
        half the number of subcarriers in the bandwidth, inclusive. For 802.11ax MU and TB PPDU signals,  802.11be MU and TB
        PPDU signals, and 802.11bn MU and TB PPDU signals, the valid values are all odd numbers between 1 and the size of the
        smallest RU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the length of the triangular-weighted moving window across subcarriers that is used for averaging the channel
                estimate.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_SMOOTHING_LENGTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_relative_delay_spread(self, selector_string):
        r"""Gets the expected channel delay spread relative to the OFDM symbol length.

        The entire symbol length is considered as 1 and the value of this attribute is specified as a fraction of 1.
        This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE` attribute to **Wiener
        Filter**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.125. Valid values are from 0 to 0.25, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the expected channel delay spread relative to the OFDM symbol length.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_RELATIVE_DELAY_SPREAD.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_relative_delay_spread(self, selector_string, value):
        r"""Sets the expected channel delay spread relative to the OFDM symbol length.

        The entire symbol length is considered as 1 and the value of this attribute is specified as a fraction of 1.
        This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE` attribute to **Wiener
        Filter**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.125. Valid values are from 0 to 0.25, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the expected channel delay spread relative to the OFDM symbol length.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_RELATIVE_DELAY_SPREAD.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_ltf_averaging_enabled(self, selector_string):
        r"""Gets whether to average multiple Long Training Field (LTF) symbols to improve channel estimation. This attribute
        is only applicable for 11ax, 11be and 11bn standards.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | False (0)    | Channel estimation with LTF averaging is disabled. |
        +--------------+----------------------------------------------------+
        | True (1)     | Channel estimation with LTF averaging is enabled.  |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccChannelEstimationLtfAveragingEnabled):
                Specifies whether to average multiple Long Training Field (LTF) symbols to improve channel estimation. This attribute
                is only applicable for 11ax, 11be and 11bn standards.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_LTF_AVERAGING_ENABLED.value,
            )
            attr_val = enums.OfdmModAccChannelEstimationLtfAveragingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_ltf_averaging_enabled(self, selector_string, value):
        r"""Sets whether to average multiple Long Training Field (LTF) symbols to improve channel estimation. This attribute
        is only applicable for 11ax, 11be and 11bn standards.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | False (0)    | Channel estimation with LTF averaging is disabled. |
        +--------------+----------------------------------------------------+
        | True (1)     | Channel estimation with LTF averaging is enabled.  |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccChannelEstimationLtfAveragingEnabled, int):
                Specifies whether to average multiple Long Training Field (LTF) symbols to improve channel estimation. This attribute
                is only applicable for 11ax, 11be and 11bn standards.

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
                if type(value) is enums.OfdmModAccChannelEstimationLtfAveragingEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_LTF_AVERAGING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_estimation_l_ltf_enabled(self, selector_string):
        r"""Gets whether to use the legacy channel estimation field for combining with the reference channel frequency
        response.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------+
        | Name (Value) | Description                              |
        +==============+==========================================+
        | False (0)    | Channel estimation on L-LTF is disabled. |
        +--------------+------------------------------------------+
        | True (1)     | Channel estimation on L-LTF is enabled.  |
        +--------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccChannelEstimationLLtfEnabled):
                Specifies whether to use the legacy channel estimation field for combining with the reference channel frequency
                response.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_L_LTF_ENABLED.value,
            )
            attr_val = enums.OfdmModAccChannelEstimationLLtfEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_estimation_l_ltf_enabled(self, selector_string, value):
        r"""Sets whether to use the legacy channel estimation field for combining with the reference channel frequency
        response.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------+
        | Name (Value) | Description                              |
        +==============+==========================================+
        | False (0)    | Channel estimation on L-LTF is disabled. |
        +--------------+------------------------------------------+
        | True (1)     | Channel estimation on L-LTF is enabled.  |
        +--------------+------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccChannelEstimationLLtfEnabled, int):
                Specifies whether to use the legacy channel estimation field for combining with the reference channel frequency
                response.

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
                if type(value) is enums.OfdmModAccChannelEstimationLLtfEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_L_LTF_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_measurement_enabled(self, selector_string):
        r"""Gets whether power measurements are performed.

        The measurement computes power of the various fields in the PPDU.  Additionally, the measurement also computes
        power over the custom gates that you configure using
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_NUMBER_OF_CUSTOM_GATES`,
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` and
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_STOP_TIME` attributes.

        Refer to `ModAcc Power Measurement
        <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/modacc-power-measurement.html>`_ for more information about power
        measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------+
        | Name (Value) | Description                      |
        +==============+==================================+
        | False (0)    | Power measurements are disabled. |
        +--------------+----------------------------------+
        | True (1)     | Power measurements are enabled.  |
        +--------------+----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccPowerMeasurementEnabled):
                Specifies whether power measurements are performed.

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
                attributes.AttributeID.OFDMMODACC_POWER_MEASUREMENT_ENABLED.value,
            )
            attr_val = enums.OfdmModAccPowerMeasurementEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_measurement_enabled(self, selector_string, value):
        r"""Sets whether power measurements are performed.

        The measurement computes power of the various fields in the PPDU.  Additionally, the measurement also computes
        power over the custom gates that you configure using
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_NUMBER_OF_CUSTOM_GATES`,
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` and
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_STOP_TIME` attributes.

        Refer to `ModAcc Power Measurement
        <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/modacc-power-measurement.html>`_ for more information about power
        measurements.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------+
        | Name (Value) | Description                      |
        +==============+==================================+
        | False (0)    | Power measurements are disabled. |
        +--------------+----------------------------------+
        | True (1)     | Power measurements are enabled.  |
        +--------------+----------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccPowerMeasurementEnabled, int):
                Specifies whether power measurements are performed.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccPowerMeasurementEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_POWER_MEASUREMENT_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_number_of_custom_gates(self, selector_string):
        r"""Gets the number of custom gates for power measurement.

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
                Specifies the number of custom gates for power measurement.

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
                attributes.AttributeID.OFDMMODACC_POWER_NUMBER_OF_CUSTOM_GATES.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_number_of_custom_gates(self, selector_string, value):
        r"""Sets the number of custom gates for power measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of custom gates for power measurement.

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
                attributes.AttributeID.OFDMMODACC_POWER_NUMBER_OF_CUSTOM_GATES.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_custom_gate_start_time(self, selector_string):
        r"""Gets the start time of the custom power gate. This value is expressed in seconds.

        A value of 0 indicates that the start time is the start of the PPDU.

        Use "gate<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

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
                attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_custom_gate_start_time(self, selector_string, value):
        r"""Sets the start time of the custom power gate. This value is expressed in seconds.

        A value of 0 indicates that the start time is the start of the PPDU.

        Use "gate<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is 0.

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
                attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_power_custom_gate_stop_time(self, selector_string):
        r"""Gets the stop time of the custom power gate, and must be greater than the corresponding
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` attribute. This value is
        expressed in seconds.

        Use "gate<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.

        The default value is 10 microseconds.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the stop time of the custom power gate, and must be greater than the corresponding
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` attribute. This value is
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
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_STOP_TIME.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_power_custom_gate_stop_time(self, selector_string, value):
        r"""Sets the stop time of the custom power gate, and must be greater than the corresponding
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` attribute. This value is
        expressed in seconds.

        Use "gate<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.

        The default value is 10 microseconds.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the stop time of the custom power gate, and must be greater than the corresponding
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` attribute. This value is
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
                attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_STOP_TIME.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_matrix_power_enabled(self, selector_string):
        r"""Gets whether the channel frequency response matrix power measurements are enabled. This enables cross-power
        measurements for MIMO signals and user-power measurements for MU signals.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------+
        | Name (Value) | Description                                                        |
        +==============+====================================================================+
        | False (0)    | Channel frequency response matrix power measurements are disabled. |
        +--------------+--------------------------------------------------------------------+
        | True (1)     | Channel frequency response matrix power measurements are enabled.  |
        +--------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccChannelMatrixPowerEnabled):
                Specifies whether the channel frequency response matrix power measurements are enabled. This enables cross-power
                measurements for MIMO signals and user-power measurements for MU signals.

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
                attributes.AttributeID.OFDMMODACC_CHANNEL_MATRIX_POWER_ENABLED.value,
            )
            attr_val = enums.OfdmModAccChannelMatrixPowerEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_matrix_power_enabled(self, selector_string, value):
        r"""Sets whether the channel frequency response matrix power measurements are enabled. This enables cross-power
        measurements for MIMO signals and user-power measurements for MU signals.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------------------------------+
        | Name (Value) | Description                                                        |
        +==============+====================================================================+
        | False (0)    | Channel frequency response matrix power measurements are disabled. |
        +--------------+--------------------------------------------------------------------+
        | True (1)     | Channel frequency response matrix power measurements are enabled.  |
        +--------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccChannelMatrixPowerEnabled, int):
                Specifies whether the channel frequency response matrix power measurements are enabled. This enables cross-power
                measurements for MIMO signals and user-power measurements for MU signals.

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
                value.value if type(value) is enums.OfdmModAccChannelMatrixPowerEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_CHANNEL_MATRIX_POWER_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_impairments_estimation_enabled(self, selector_string):
        r"""Gets whether to enable the estimation of I/Q gain imbalance, I/Q quadrature error, and I/Q timing skew
        impairments.

        Refer to `IQ Impairments <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/iq-impairments.html>`_ for more
        information about impairments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | False (0)    | I/Q impairments estimation is disabled. |
        +--------------+-----------------------------------------+
        | True (1)     | I/Q impairments estimation is enabled.  |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIQImpairmentsEstimationEnabled):
                Specifies whether to enable the estimation of I/Q gain imbalance, I/Q quadrature error, and I/Q timing skew
                impairments.

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
                attributes.AttributeID.OFDMMODACC_IQ_IMPAIRMENTS_ESTIMATION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccIQImpairmentsEstimationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_impairments_estimation_enabled(self, selector_string, value):
        r"""Sets whether to enable the estimation of I/Q gain imbalance, I/Q quadrature error, and I/Q timing skew
        impairments.

        Refer to `IQ Impairments <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/iq-impairments.html>`_ for more
        information about impairments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | False (0)    | I/Q impairments estimation is disabled. |
        +--------------+-----------------------------------------+
        | True (1)     | I/Q impairments estimation is enabled.  |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccIQImpairmentsEstimationEnabled, int):
                Specifies whether to enable the estimation of I/Q gain imbalance, I/Q quadrature error, and I/Q timing skew
                impairments.

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
                if type(value) is enums.OfdmModAccIQImpairmentsEstimationEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_IQ_IMPAIRMENTS_ESTIMATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_impairments_model(self, selector_string):
        r"""Gets the I/Q impairments model used by the measurement for estimating I/Q impairments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **TX**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | TX (0)       | The measurement assumes that the I/Q impairments are introduced by a transmit DUT. |
        +--------------+------------------------------------------------------------------------------------+
        | RX (1)       | The measurement assumes that the I/Q impairments are introduced by a receive DUT.  |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIQImpairmentsModel):
                Specifies the I/Q impairments model used by the measurement for estimating I/Q impairments.

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
                attributes.AttributeID.OFDMMODACC_IQ_IMPAIRMENTS_MODEL.value,
            )
            attr_val = enums.OfdmModAccIQImpairmentsModel(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_impairments_model(self, selector_string, value):
        r"""Sets the I/Q impairments model used by the measurement for estimating I/Q impairments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **TX**.

        +--------------+------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                        |
        +==============+====================================================================================+
        | TX (0)       | The measurement assumes that the I/Q impairments are introduced by a transmit DUT. |
        +--------------+------------------------------------------------------------------------------------+
        | RX (1)       | The measurement assumes that the I/Q impairments are introduced by a receive DUT.  |
        +--------------+------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccIQImpairmentsModel, int):
                Specifies the I/Q impairments model used by the measurement for estimating I/Q impairments.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccIQImpairmentsModel else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_IQ_IMPAIRMENTS_MODEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_correction_enabled(self, selector_string):
        r"""Gets whether to enable I/Q gain imbalance correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | False (0)    | I/Q gain imbalance correction is disabled. |
        +--------------+--------------------------------------------+
        | True (1)     | I/Q gain imbalance correction is enabled.  |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIQGainImbalanceCorrectionEnabled):
                Specifies whether to enable I/Q gain imbalance correction.

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
                attributes.AttributeID.OFDMMODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccIQGainImbalanceCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_gain_imbalance_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable I/Q gain imbalance correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+--------------------------------------------+
        | Name (Value) | Description                                |
        +==============+============================================+
        | False (0)    | I/Q gain imbalance correction is disabled. |
        +--------------+--------------------------------------------+
        | True (1)     | I/Q gain imbalance correction is enabled.  |
        +--------------+--------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccIQGainImbalanceCorrectionEnabled, int):
                Specifies whether to enable I/Q gain imbalance correction.

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
                if type(value) is enums.OfdmModAccIQGainImbalanceCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_correction_enabled(self, selector_string):
        r"""Gets whether to enable I/Q quadrature error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | I/Q quadrature error correction is disabled. |
        +--------------+----------------------------------------------+
        | True (1)     | I/Q quadrature error correction is enabled.  |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIQQuadratureErrorCorrectionEnabled):
                Specifies whether to enable I/Q quadrature error correction.

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
                attributes.AttributeID.OFDMMODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccIQQuadratureErrorCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_quadrature_error_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable I/Q quadrature error correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | I/Q quadrature error correction is disabled. |
        +--------------+----------------------------------------------+
        | True (1)     | I/Q quadrature error correction is enabled.  |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccIQQuadratureErrorCorrectionEnabled, int):
                Specifies whether to enable I/Q quadrature error correction.

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
                if type(value) is enums.OfdmModAccIQQuadratureErrorCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_timing_skew_correction_enabled(self, selector_string):
        r"""Gets whether to enable I/Q timing skew correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | False (0)    | I/Q timing skew correction is disabled. |
        +--------------+-----------------------------------------+
        | True (1)     | I/Q timing skew correction is enabled.  |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIQTimingSkewCorrectionEnabled):
                Specifies whether to enable I/Q timing skew correction.

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
                attributes.AttributeID.OFDMMODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccIQTimingSkewCorrectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_timing_skew_correction_enabled(self, selector_string, value):
        r"""Sets whether to enable I/Q timing skew correction.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------+
        | Name (Value) | Description                             |
        +==============+=========================================+
        | False (0)    | I/Q timing skew correction is disabled. |
        +--------------+-----------------------------------------+
        | True (1)     | I/Q timing skew correction is enabled.  |
        +--------------+-----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccIQTimingSkewCorrectionEnabled, int):
                Specifies whether to enable I/Q timing skew correction.

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
                if type(value) is enums.OfdmModAccIQTimingSkewCorrectionEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_impairments_per_subcarrier_enabled(self, selector_string):
        r"""Gets whether to estimate I/Q impairments independently for each subcarrier.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------+
        | Name (Value) | Description                                                                |
        +==============+============================================================================+
        | False (0)    | Independent estimation of I/Q impairments for each subcarrier is disabled. |
        +--------------+----------------------------------------------------------------------------+
        | True (1)     | Independent estimation of I/Q impairments for each subcarrier is enabled.  |
        +--------------+----------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIQImpairmentsPerSubcarrierEnabled):
                Specifies whether to estimate I/Q impairments independently for each subcarrier.

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
                attributes.AttributeID.OFDMMODACC_IQ_IMPAIRMENTS_PER_SUBCARRIER_ENABLED.value,
            )
            attr_val = enums.OfdmModAccIQImpairmentsPerSubcarrierEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_impairments_per_subcarrier_enabled(self, selector_string, value):
        r"""Sets whether to estimate I/Q impairments independently for each subcarrier.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------+
        | Name (Value) | Description                                                                |
        +==============+============================================================================+
        | False (0)    | Independent estimation of I/Q impairments for each subcarrier is disabled. |
        +--------------+----------------------------------------------------------------------------+
        | True (1)     | Independent estimation of I/Q impairments for each subcarrier is enabled.  |
        +--------------+----------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccIQImpairmentsPerSubcarrierEnabled, int):
                Specifies whether to estimate I/Q impairments independently for each subcarrier.

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
                if type(value) is enums.OfdmModAccIQImpairmentsPerSubcarrierEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_IQ_IMPAIRMENTS_PER_SUBCARRIER_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_unused_tone_error_mask_reference(self, selector_string):
        r"""Gets the reference used to create the unused tone error mask for the 802.11ax, 802.11be or 802.11bn TB PPDU
        signals.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Limit1**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Limit1 (0)   | Applies the mask corresponding to the case when the transmit power of the DUT is less than or equal to the maximum       |
        |              | power of MCS7.                                                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Limit2 (1)   | Applies the mask corresponding to the case when the transmit power of the DUT is more than the maximum power of MCS7.    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccUnusedToneErrorMaskReference):
                Specifies the reference used to create the unused tone error mask for the 802.11ax, 802.11be or 802.11bn TB PPDU
                signals.

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
                attributes.AttributeID.OFDMMODACC_UNUSED_TONE_ERROR_MASK_REFERENCE.value,
            )
            attr_val = enums.OfdmModAccUnusedToneErrorMaskReference(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_unused_tone_error_mask_reference(self, selector_string, value):
        r"""Sets the reference used to create the unused tone error mask for the 802.11ax, 802.11be or 802.11bn TB PPDU
        signals.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Limit1**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | Limit1 (0)   | Applies the mask corresponding to the case when the transmit power of the DUT is less than or equal to the maximum       |
        |              | power of MCS7.                                                                                                           |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Limit2 (1)   | Applies the mask corresponding to the case when the transmit power of the DUT is more than the maximum power of MCS7.    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccUnusedToneErrorMaskReference, int):
                Specifies the reference used to create the unused tone error mask for the 802.11ax, 802.11be or 802.11bn TB PPDU
                signals.

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
                if type(value) is enums.OfdmModAccUnusedToneErrorMaskReference
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_UNUSED_TONE_ERROR_MASK_REFERENCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_data_decoding_enabled(self, selector_string):
        r"""Gets whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).

        This further enables the check for the validity of SIG-B cyclic redundancy check (CRC) of the 802.11ac PPDU.

        .. note::
           Set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MAXIMUM_MEASUREMENT_LENGTH` attribute to -1 to decode
           all symbols.

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

            attr_val (enums.OfdmModAccDataDecodingEnabled):
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
                attributes.AttributeID.OFDMMODACC_DATA_DECODING_ENABLED.value,
            )
            attr_val = enums.OfdmModAccDataDecodingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_data_decoding_enabled(self, selector_string, value):
        r"""Sets whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).

        This further enables the check for the validity of SIG-B cyclic redundancy check (CRC) of the 802.11ac PPDU.

        .. note::
           Set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MAXIMUM_MEASUREMENT_LENGTH` attribute to -1 to decode
           all symbols.

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

            value (enums.OfdmModAccDataDecodingEnabled, int):
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
            value = value.value if type(value) is enums.OfdmModAccDataDecodingEnabled else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_DATA_DECODING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_enabled(self, selector_string):
        r"""Gets whether the contribution of the instrument noise is compensated for EVM computation.

        You must measure the noise floor before applying the noise compensation. The instrument noise floor is measured
        for the RF path used by the OFDMModAcc measurement and cached for future use.

        **Supported devices: **PXIe-5830/5831/5832/5646/5840/5841/5842/5860.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | Disables instrument noise compensation for EVM results. |
        +--------------+---------------------------------------------------------+
        | True (1)     | Enables instrument noise compensation for EVM results.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccNoiseCompensationEnabled):
                Specifies whether the contribution of the instrument noise is compensated for EVM computation.

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
                attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccNoiseCompensationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_enabled(self, selector_string, value):
        r"""Sets whether the contribution of the instrument noise is compensated for EVM computation.

        You must measure the noise floor before applying the noise compensation. The instrument noise floor is measured
        for the RF path used by the OFDMModAcc measurement and cached for future use.

        **Supported devices: **PXIe-5830/5831/5832/5646/5840/5841/5842/5860.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+---------------------------------------------------------+
        | Name (Value) | Description                                             |
        +==============+=========================================================+
        | False (0)    | Disables instrument noise compensation for EVM results. |
        +--------------+---------------------------------------------------------+
        | True (1)     | Enables instrument noise compensation for EVM results.  |
        +--------------+---------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccNoiseCompensationEnabled, int):
                Specifies whether the contribution of the instrument noise is compensated for EVM computation.

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
                value.value if type(value) is enums.OfdmModAccNoiseCompensationEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_input_power_check_enabled(self, selector_string):
        r"""Gets whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
        performing noise floor calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | Disables the input power check at the RFIn port of the signal analyzer. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | Enables the input power check at the RFIn port of the signal analyzer.  |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccNoiseCompensationInputPowerCheckEnabled):
                Specifies whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
                performing noise floor calibration.

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
                attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_INPUT_POWER_CHECK_ENABLED.value,
            )
            attr_val = enums.OfdmModAccNoiseCompensationInputPowerCheckEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_input_power_check_enabled(self, selector_string, value):
        r"""Sets whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
        performing noise floor calibration.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+-------------------------------------------------------------------------+
        | Name (Value) | Description                                                             |
        +==============+=========================================================================+
        | False (0)    | Disables the input power check at the RFIn port of the signal analyzer. |
        +--------------+-------------------------------------------------------------------------+
        | True (1)     | Enables the input power check at the RFIn port of the signal analyzer.  |
        +--------------+-------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccNoiseCompensationInputPowerCheckEnabled, int):
                Specifies whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
                performing noise floor calibration.

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
                if type(value) is enums.OfdmModAccNoiseCompensationInputPowerCheckEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_INPUT_POWER_CHECK_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_noise_compensation_reference_level_coercion_limit(self, selector_string):
        r"""Gets the reference level coercion limit for noise compensation. This value is expressed in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_ENABLED` attribute
        to **True** and the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_MODE` attribute to **Measure**,
        the measurement attempts to read the noise floor calibration data corresponding to the configured reference level. If
        the noise floor calibration data corresponding to the configured reference level in the calibration database is not
        found, then the measurement attempts to read noise floor calibration data from the calibration database for any
        reference level in the range of the configured reference level plus or minus the coercion limit you set for this
        attribute.

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
                Specifies the reference level coercion limit for noise compensation. This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_REFERENCE_LEVEL_COERCION_LIMIT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_noise_compensation_reference_level_coercion_limit(self, selector_string, value):
        r"""Sets the reference level coercion limit for noise compensation. This value is expressed in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_ENABLED` attribute
        to **True** and the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_MODE` attribute to **Measure**,
        the measurement attempts to read the noise floor calibration data corresponding to the configured reference level. If
        the noise floor calibration data corresponding to the configured reference level in the calibration database is not
        found, then the measurement attempts to read noise floor calibration data from the calibration database for any
        reference level in the range of the configured reference level plus or minus the coercion limit you set for this
        attribute.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.5.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the reference level coercion limit for noise compensation. This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_REFERENCE_LEVEL_COERCION_LIMIT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_optimize_dynamic_range_for_evm_enabled(self, selector_string):
        r"""Gets whether to optimize the analyzer's dynamic range for the EVM measurement.

        This attribute computes optimum attenuation settings for the analyzer based on the reference level you specify
        while still avoiding ADC or onboard signal processing (OSP) overflow. When you specify the reference level and you
        notice an overflow error, you can increase the reference level or specify a margin above the reference level by
        configuring the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_MARGIN`
        attribute.

        **Supported devices: **PXIe-5646/5840/5841/5842/5860.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------------------+
        | Name (Value) | Description                                                            |
        +==============+========================================================================+
        | False (0)    | Specifies that the dynamic range is not optimized for EVM measurement. |
        +--------------+------------------------------------------------------------------------+
        | True (1)     | Specifies that the dynamic range is optimized for EVM measurement.     |
        +--------------+------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccOptimizeDynamicRangeForEvmEnabled):
                Specifies whether to optimize the analyzer's dynamic range for the EVM measurement.

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
                attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED.value,
            )
            attr_val = enums.OfdmModAccOptimizeDynamicRangeForEvmEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_optimize_dynamic_range_for_evm_enabled(self, selector_string, value):
        r"""Sets whether to optimize the analyzer's dynamic range for the EVM measurement.

        This attribute computes optimum attenuation settings for the analyzer based on the reference level you specify
        while still avoiding ADC or onboard signal processing (OSP) overflow. When you specify the reference level and you
        notice an overflow error, you can increase the reference level or specify a margin above the reference level by
        configuring the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_MARGIN`
        attribute.

        **Supported devices: **PXIe-5646/5840/5841/5842/5860.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------------------+
        | Name (Value) | Description                                                            |
        +==============+========================================================================+
        | False (0)    | Specifies that the dynamic range is not optimized for EVM measurement. |
        +--------------+------------------------------------------------------------------------+
        | True (1)     | Specifies that the dynamic range is optimized for EVM measurement.     |
        +--------------+------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccOptimizeDynamicRangeForEvmEnabled, int):
                Specifies whether to optimize the analyzer's dynamic range for the EVM measurement.

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
                if type(value) is enums.OfdmModAccOptimizeDynamicRangeForEvmEnabled
                else value
            )
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_optimize_dynamic_range_for_evm_margin(self, selector_string):
        r"""Gets the margin above the reference level you specify when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED` attribute to **True**.
        This value is expressed in dB.

        When the property's value 0, the dynamic range is optimized. When you set a positive value to the attribute,
        the dynamic range reduces from the optimized dynamic range. You can use this attribute to avoid ADC and onboard signal
        processing (OSP) overflows.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the margin above the reference level you specify when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED` attribute to **True**.
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
                attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_optimize_dynamic_range_for_evm_margin(self, selector_string, value):
        r"""Sets the margin above the reference level you specify when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED` attribute to **True**.
        This value is expressed in dB.

        When the property's value 0, the dynamic range is optimized. When you set a positive value to the attribute,
        the dynamic range reduces from the optimized dynamic range. You can use this attribute to avoid ADC and onboard signal
        processing (OSP) overflows.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the margin above the reference level you specify when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED` attribute to **True**.
                This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_MARGIN.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_auto_level_allow_overflow(self, selector_string):
        r"""Gets whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
        overflow.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | Disables searching for the optimum reference levels while allowing ADC overflow. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | Enables searching for the optimum reference levels while allowing ADC overflow.  |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccAutoLevelAllowOverflow):
                Specifies whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
                overflow.

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
                attributes.AttributeID.OFDMMODACC_AUTO_LEVEL_ALLOW_OVERFLOW.value,
            )
            attr_val = enums.OfdmModAccAutoLevelAllowOverflow(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_level_allow_overflow(self, selector_string, value):
        r"""Sets whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
        overflow.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                      |
        +==============+==================================================================================+
        | False (0)    | Disables searching for the optimum reference levels while allowing ADC overflow. |
        +--------------+----------------------------------------------------------------------------------+
        | True (1)     | Enables searching for the optimum reference levels while allowing ADC overflow.  |
        +--------------+----------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmModAccAutoLevelAllowOverflow, int):
                Specifies whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
                overflow.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            value = value.value if type(value) is enums.OfdmModAccAutoLevelAllowOverflow else value
            error_code = self._interpreter.set_attribute_i32(
                updated_selector_string,
                attributes.AttributeID.OFDMMODACC_AUTO_LEVEL_ALLOW_OVERFLOW.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_traces_enabled(self, selector_string):
        r"""Gets whether to enable all the traces computed by the OFDMModAcc measurement.

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
                Specifies whether to enable all the traces computed by the OFDMModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_ALL_TRACES_ENABLED.value
            )
            attr_val = bool(attr_val)
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_all_traces_enabled(self, selector_string, value):
        r"""Sets whether to enable all the traces computed by the OFDMModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is FALSE.

        Args:
            selector_string (string):
                Pass an empty string.

            value (bool):
                Specifies whether to enable all the traces computed by the OFDMModAcc measurement.

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
                attributes.AttributeID.OFDMMODACC_ALL_TRACES_ENABLED.value,
                int(value),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_analysis_threads(self, selector_string):
        r"""Gets the maximum number of threads used for parallelism for the OFDMModAcc measurement.

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
                Specifies the maximum number of threads used for parallelism for the OFDMModAcc measurement.

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
                attributes.AttributeID.OFDMMODACC_NUMBER_OF_ANALYSIS_THREADS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_analysis_threads(self, selector_string, value):
        r"""Sets the maximum number of threads used for parallelism for the OFDMModAcc measurement.

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
                Specifies the maximum number of threads used for parallelism for the OFDMModAcc measurement.

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
                attributes.AttributeID.OFDMMODACC_NUMBER_OF_ANALYSIS_THREADS.value,
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

            acquisition_length_mode (enums.OfdmModAccAcquisitionLengthMode, int):
                This parameter specifies whether the measurement automatically computes the acquisition length of the waveform based on
                other OFDMModAcc attributes. The default value is **Auto**.

                +--------------+--------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                        |
                +==============+====================================================================================================================+
                | Manual (0)   | Uses the acquisition length specified by the OFDMModAcc Acquisition Length attribute.                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------+
                | Auto (1)     | Computes the acquisition length based on the OFDMModAcc Meas Offset and the OFDMModAcc Max Meas Length attributes. |
                +--------------+--------------------------------------------------------------------------------------------------------------------+

            acquisition_length (float):
                This parameter specifies the length of the waveform to be acquired for the OFDMModAcc measurement when you set the
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
                if type(acquisition_length_mode) is enums.OfdmModAccAcquisitionLengthMode
                else acquisition_length_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_acquisition_length(
                updated_selector_string, acquisition_length_mode, acquisition_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_amplitude_tracking_enabled(self, selector_string, amplitude_tracking_enabled):
        r"""Configures whether to enable pilot-based mean amplitude tracking per OFDM data symbol.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            amplitude_tracking_enabled (enums.OfdmModAccAmplitudeTrackingEnabled, int):
                This parameter specifies whether to enable pilot-based mean amplitude tracking per OFDM data symbol. Amplitude tracking
                is useful if the mean amplitude of the OFDM symbols in a PPDU varies over time. However, enabling tracking may degrade
                EVM because of attempts to track random amplitude distortions caused by additive noise and other distortions. The
                default value is **False**.

                +--------------+---------------------------------+
                | Name (Value) | Description                     |
                +==============+=================================+
                | False (0)    | Amplitude tracking is disabled. |
                +--------------+---------------------------------+
                | True (1)     | Amplitude tracking is enabled.  |
                +--------------+---------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            amplitude_tracking_enabled = (
                amplitude_tracking_enabled.value
                if type(amplitude_tracking_enabled) is enums.OfdmModAccAmplitudeTrackingEnabled
                else amplitude_tracking_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_amplitude_tracking_enabled(
                updated_selector_string, amplitude_tracking_enabled
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

            averaging_enabled (enums.OfdmModAccAveragingEnabled, int):
                This parameter specifies whether to enable averaging for OFDMModAcc measurements. The default value is **False**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | The measurement is performed on a single acquisition.                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | The measurement uses the value of the Averaging Count parameter as the number of acquisitions over which the results     |
                |              | are averaged.                                                                                                            |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

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
                if type(averaging_enabled) is enums.OfdmModAccAveragingEnabled
                else averaging_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_averaging(
                updated_selector_string, averaging_enabled, averaging_count
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_channel_estimation_type(self, selector_string, channel_estimation_type):
        r"""Configures the fields in the PPDU used to estimate the channel frequency response.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            channel_estimation_type (enums.OfdmModAccChannelEstimationType, int):
                This parameter specifies the fields in the PPDU used to estimate the channel frequency response. The default value is
                **Reference**.

                +------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)           | Description                                                                                                              |
                +========================+==========================================================================================================================+
                | Reference (0)          | The channel is estimated using long training fields (LTFs) in the preamble and the most recently received midamble, if   |
                |                        | present.                                                                                                                 |
                +------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Reference and Data (1) | The channel is estimated using long training fields (LTFs) in the preamble, the midamble (if present), and the data      |
                |                        | field.                                                                                                                   |
                +------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            channel_estimation_type = (
                channel_estimation_type.value
                if type(channel_estimation_type) is enums.OfdmModAccChannelEstimationType
                else channel_estimation_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_channel_estimation_type(
                updated_selector_string, channel_estimation_type
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_common_clock_source_enabled(self, selector_string, common_clock_source_enabled):
        r"""Configures whether the transmitter uses the same reference clock signal for generating the RF carrier and for the
        symbol clock.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            common_clock_source_enabled (enums.OfdmModAccCommonClockSourceEnabled, int):
                This parameter specifies if the transmitter uses the same reference clock signal for generating the RF carrier and the
                symbol clock. The default value is **True**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Specifies that the transmitter does not use a common reference clock. The OFDMModAcc measurement computes the symbol     |
                |              | clock error and carrier frequency error independently.                                                                   |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Specifies that the transmitter uses a common reference clock. The OFDMModAcc measurement derives the symbol clock error  |
                |              | from the configured center frequency and carrier frequency error.                                                        |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            common_clock_source_enabled = (
                common_clock_source_enabled.value
                if type(common_clock_source_enabled) is enums.OfdmModAccCommonClockSourceEnabled
                else common_clock_source_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_common_clock_source_enabled(
                updated_selector_string, common_clock_source_enabled
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

            evm_unit (enums.OfdmModAccEvmUnit, int):
                This parameter specifies the unit for the EVM results. The default value is **dB**.

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
            evm_unit = evm_unit.value if type(evm_unit) is enums.OfdmModAccEvmUnit else evm_unit
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_evm_unit(
                updated_selector_string, evm_unit
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency_error_estimation_method(
        self, selector_string, frequency_error_estimation_method
    ):
        r"""Configures the frequency error estimation method for the OFDMModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            frequency_error_estimation_method (enums.OfdmModAccFrequencyErrorEstimationMethod, int):
                This parameter specifies the PPDU fields that the measurement uses to estimate the carrier frequency error in the
                acquired signal. The default value is **Preamble and Pilots**.

                +-------------------------------+------------------------------------------------------------------------------------------------------------------+
                | Name (Value)                  | Description                                                                                                      |
                +===============================+==================================================================================================================+
                | Disabled (0)                  | Carrier frequency error is not computed and the corresponding result is returned as NaN.                         |
                +-------------------------------+------------------------------------------------------------------------------------------------------------------+
                | Initial Preamble (1)          | Initial short and long training fields in the PPDU are used.                                                     |
                +-------------------------------+------------------------------------------------------------------------------------------------------------------+
                | Preamble (2)                  | Initial short and long training fields along with the SIGnal fields are used.                                    |
                +-------------------------------+------------------------------------------------------------------------------------------------------------------+
                | Preamble and Pilots (3)       | The initial short and long training fields, SIGnal fields, and the pilot subcarriers in the DATA field are used. |
                +-------------------------------+------------------------------------------------------------------------------------------------------------------+
                | Preamble, Pilots and Data (4) | The initial short and long training fields, SIGnal fields, and all the subcarriers in the DATA field are used.   |
                +-------------------------------+------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            frequency_error_estimation_method = (
                frequency_error_estimation_method.value
                if type(frequency_error_estimation_method)
                is enums.OfdmModAccFrequencyErrorEstimationMethod
                else frequency_error_estimation_method
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_frequency_error_estimation_method(
                updated_selector_string, frequency_error_estimation_method
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_length(
        self, selector_string, measurement_offset, maximum_measurement_length
    ):
        r"""Configures the measurement offset and maximum measurement length for the OFDMModAcc EVM measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_offset (int):
                This parameter specifies the number of data OFDM symbols to be ignored from the start of the data field for EVM
                computation. The default value is 0.

            maximum_measurement_length (int):
                This parameter specifies the maximum number of data OFDM symbols that the measurement uses to compute EVM. The default
                value is 16. If the number of available data symbols (*n*) is greater than the value that you specify (*m*), the
                measurement ignores (*n*-*m*) symbols from the end of the data field. If you set this parameter to -1, all symbols in
                the data field are used to compute the EVM.

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
            error_code = self._interpreter.ofdmmodacc_configure_measurement_length(
                updated_selector_string, measurement_offset, maximum_measurement_length
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_measurement_mode(self, selector_string, measurement_mode):
        r"""Configures the measurement mode for the OFDMModAcc measurement.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_mode (enums.OfdmModAccMeasurementMode, int):
                This parameter specifies whether the measurement should calibrate the noise floor of the analyzer or perform the
                OFDMModAcc measurement. The default value is **Measure**.

                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)              | Description                                                                                                              |
                +===========================+==========================================================================================================================+
                | Measure (0)               | The OFDMModAcc measurement is performed on the acquired signal.                                                          |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Calibrate Noise Floor (1) | The OFDMModAcc measurement measures the noise floor of the instrument across the frequency range of interest determined  |
                |                           | by the carrier frequency and channel bandwidth. In this mode, the measurement expects that the signal generator to be    |
                |                           | turned off and checks whether no signal power is detected at the RF In port of the analyzer beyond a certain threshold.  |
                |                           | All scalar results and traces are invalid in this mode. Even if the instrument noise floor is previously calibrated,     |
                |                           | the measurement performs all the required acquisitions and overwrites any pre-existing noise floor calibration data.     |
                +---------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurement_mode = (
                measurement_mode.value
                if type(measurement_mode) is enums.OfdmModAccMeasurementMode
                else measurement_mode
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_measurement_mode(
                updated_selector_string, measurement_mode
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_1_reference_waveform(self, selector_string, x0, dx, reference_waveform):
        r"""Configures the reference waveform for a SISO measurement when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE` attribute to **Reference
        Waveform**.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            x0 (float):
                This parameter specifies the starting time of the reference waveform. This value is expressed in seconds.

            dx (float):
                This parameter specifies the sampling interval of the reference waveform. This value is expressed in seconds.

            reference_waveform (numpy.complex64):
                This parameter specifies an array of waveform samples of the reference waveform.

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
            error_code = self._interpreter.ofdmmodacc_configure_1_reference_waveform(
                updated_selector_string, x0, dx, reference_waveform
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_noise_compensation_enabled(self, selector_string, noise_compensation_enabled):
        r"""Configures whether to enable EVM noise compensation for the OFDMModAcc measurement.

        **Supported devices: **PXIe-5830/5831/5832/5646/5840/5841/5842/5860.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            noise_compensation_enabled (enums.OfdmModAccNoiseCompensationEnabled, int):
                This parameter specifies whether the contribution of the instrument noise is compensated for EVM computation. The
                default value is **False**.

                +--------------+---------------------------------------------------------+
                | Name (Value) | Description                                             |
                +==============+=========================================================+
                | False (0)    | Disables instrument noise compensation for EVM results. |
                +--------------+---------------------------------------------------------+
                | True (1)     | Enables instrument noise compensation for EVM results.  |
                +--------------+---------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            noise_compensation_enabled = (
                noise_compensation_enabled.value
                if type(noise_compensation_enabled) is enums.OfdmModAccNoiseCompensationEnabled
                else noise_compensation_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_noise_compensation_enabled(
                updated_selector_string, noise_compensation_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_optimize_dynamic_range_for_evm(
        self,
        selector_string,
        optimize_dynamic_range_for_evm_enabled,
        optimize_dynamic_range_for_evm_margin,
    ):
        r"""Specifies whether to optimize analyzer's dynamic range for the EVM measurement.

        **Supported devices: **PXIe-5646/5840/5841/5842/5860.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            optimize_dynamic_range_for_evm_enabled (enums.OfdmModAccOptimizeDynamicRangeForEvmEnabled, int):
                This parameter specifies whether to optimize the analyzer's dynamic range for the EVM measurement. This parameter
                computes optimum attenuation settings for the analyzer based on the reference level you specify while still avoiding
                ADC or onboard signal processing (OSP) overflow. When you specify the reference level and you notice an overflow error,
                you can increase the reference level or specify a margin above the reference level by configuring the **Optimize
                Dynamic Range for EVM Margin** parameter. The default value is **False**.

                +--------------+------------------------------------------------------------------------+
                | Name (Value) | Description                                                            |
                +==============+========================================================================+
                | False (0)    | Specifies that the dynamic range is not optimized for EVM measurement. |
                +--------------+------------------------------------------------------------------------+
                | True (1)     | Specifies that the dynamic range is optimized for EVM measurement.     |
                +--------------+------------------------------------------------------------------------+

            optimize_dynamic_range_for_evm_margin ():
                This parameter specifies the margin above the reference level you specify when you set the **Optimize Dynamic Range for
                EVM Enabled** parameter to **True**. This value is expressed in dB. When the parameter's value is 0, the dynamic range
                is optimized. When you set a positive value to the parameter, the dynamic range reduces from the optimized dynamic
                range. You can use this parameter to avoid ADC and onboard signal processing (OSP) overflows. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            optimize_dynamic_range_for_evm_enabled = (
                optimize_dynamic_range_for_evm_enabled.value
                if type(optimize_dynamic_range_for_evm_enabled)
                is enums.OfdmModAccOptimizeDynamicRangeForEvmEnabled
                else optimize_dynamic_range_for_evm_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_optimize_dynamic_range_for_evm(
                updated_selector_string,
                optimize_dynamic_range_for_evm_enabled,
                optimize_dynamic_range_for_evm_margin,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_phase_tracking_enabled(self, selector_string, phase_tracking_enabled):
        r"""Configures whether to enable pilot-based common phase error correction per OFDM data symbol.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            phase_tracking_enabled (enums.OfdmModAccPhaseTrackingEnabled, int):
                This parameter specifies whether to enable pilot-based common phase error correction per OFDM data symbol. Phase
                tracking is useful for tracking the phase variation over the modulation symbol caused by the residual frequency offset
                and phase noise. The default value is **True**.

                +--------------+-----------------------------+
                | Name (Value) | Description                 |
                +==============+=============================+
                | False (0)    | Phase tracking is disabled. |
                +--------------+-----------------------------+
                | True (1)     | Phase tracking is enabled.  |
                +--------------+-----------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            phase_tracking_enabled = (
                phase_tracking_enabled.value
                if type(phase_tracking_enabled) is enums.OfdmModAccPhaseTrackingEnabled
                else phase_tracking_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = self._interpreter.ofdmmodacc_configure_phase_tracking_enabled(
                updated_selector_string, phase_tracking_enabled
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_symbol_clock_error_correction_enabled(
        self, selector_string, symbol_clock_error_correction_enabled
    ):
        r"""Configures whether to enable symbol clock error correction.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            symbol_clock_error_correction_enabled (enums.OfdmModAccSymbolClockErrorCorrectionEnabled, int):
                This parameter specifies whether to enable symbol clock error correction. The default value is **True**.

                +--------------+--------------------------------------------+
                | Name (Value) | Description                                |
                +==============+============================================+
                | False (0)    | Symbol clock error correction is disabled. |
                +--------------+--------------------------------------------+
                | True (1)     | Symbol clock error correction is enabled.  |
                +--------------+--------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            symbol_clock_error_correction_enabled = (
                symbol_clock_error_correction_enabled.value
                if type(symbol_clock_error_correction_enabled)
                is enums.OfdmModAccSymbolClockErrorCorrectionEnabled
                else symbol_clock_error_correction_enabled
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            error_code = (
                self._interpreter.ofdmmodacc_configure_symbol_clock_error_correction_enabled(
                    updated_selector_string, symbol_clock_error_correction_enabled
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_level(self, selector_string, timeout):
        r"""Performs the user-configured ModAcc measurement on all initialized devices at multiple reference levels relative to the
        user-configured :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute and configures the reference
        level corresponding to the lowest :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MEAN`
        result on each device.

        This method only measures at the reference levels that do not result in an ADC or OSP overflow when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AUTO_LEVEL_ALLOW_OVERFLOW` attribute to **False**. If you set
        the OFDMModAcc Auto Level Allow Overflow attribute to **True**, this method measures at a few reference levels beyond
        the overflow.

        After calling this method, you need to perform the ModAcc measurement.

        .. note::
           Calling this method will also set the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL_HEADROOM` attribute
           to 0.

        This method expects:

        - A valid OFDMModAcc measurement configuration

        - Reference Level attribute set to peak power of the signal

        - Repetitive signals at the analyzer's input along with trigger settings that measure the same portion of the waveform every time the measurement is performed

        - No other measurements are running in parallel

        Auto level needs to be performed again if the input signal or RFmx configuration changes.

        For repeatable results, you must make sure that the OFDMModAcc measurement is repeatable.

        This method measures EVM at reference levels starting at an integer at least 1 dB above the value you configure
        for the Reference Level attribute, extending upto 12 dB lower when you set the OFDMModAcc Auto Level Allow Overflow
        attribute to **False**, and up to 17 dB lower when you set the OFDMModAcc Auto Level Allow Overflow attribute to
        **True** with a step size of 0.5 dB.

        When you use this method with the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_NOISE_COMPENSATION_ENABLED` attribute set to **True**, you need
        to make sure that valid noise calibration data is available for the above measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            timeout (float):
                This parameter specifies the timeout for fetching the EVM results. This value is expressed in seconds. Set this value
                to an appropriate time, longer than expected for fetching the measurement. A value of -1 specifies that the method
                waits until the measurement is complete. The default value is 10.

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
            error_code = self._interpreter.ofdmmodacc_auto_level(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def validate_calibration_data(self, selector_string):
        r"""Indicates whether calibration data is valid for the configuration specified by the signal name in the **Selector
        string** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (calibration_data_valid, error_code):

            calibration_data_valid (enums.OfdmModAccCalibrationDataValid):
                This parameter returns whether the calibration data is valid.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | False (0)    | Returns false if the calibration data is not present for the specified configuration or if the difference between the    |
                |              | current device temperature and the calibration temperature exceeds the [-5 °C, 5 °C] range.                              |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | True (1)     | Returns true if the calibration data is present for the configuration specified by the signal name in the Selector       |
                |              | string parameter.                                                                                                        |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            calibration_data_valid, error_code = (
                self._interpreter.ofdmmodacc_validate_calibration_data(updated_selector_string)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return calibration_data_valid, error_code

    @_raise_if_disposed
    def configure_n_reference_waveforms(self, selector_string, x0, dx, reference_waveform):
        r"""Configures the reference waveform array for a MIMO measurement when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.EVM_REFERENCE_DATA_SYMBOLS_MODE` attribute to **Reference Waveform**.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            x0 (float):
                This parameter specifies the starting time of the reference waveform. This value is expressed in seconds.

            dx (float):
                This parameter specifies the sampling interval of the reference waveform. This value is expressed in seconds.

            reference_waveform (numpy.complex64):
                This parameter specifies an array of waveform samples of the reference waveform.

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
            error_code = self._interpreter.ofdmmodacc_configure_n_reference_waveforms(
                updated_selector_string, x0, dx, reference_waveform
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code
