"""Provides methods to fetch and read the OfdmModAcc measurement results."""

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


class OfdmModAccResults(object):
    """Provides methods to fetch and read the OfdmModAcc measurement results."""

    def __init__(self, signal_obj):
        """Provides methods to fetch and read the OfdmModAcc measurement results."""
        self._signal_obj = signal_obj
        self._session_function_lock = signal_obj._session_function_lock
        self._interpreter = signal_obj._interpreter

    @_raise_if_disposed
    def get_composite_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_COMPOSITE_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_data_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of data-subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of data RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of data-subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_COMPOSITE_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_composite_pilot_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of pilot-subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute is set to
        **True**, this attribute returns the mean of pilot RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of pilot-subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_COMPOSITE_PILOT_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_stream_rms_evm_mean(self, selector_string):
        r"""Gets the stream RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of stream RMS EVM results computed for each averaging count.

        Use "segment<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the stream RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_STREAM_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_stream_rms_evm_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_STREAM_RMS_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_stream_rms_evm_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_STREAM_RMS_EVM_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_stream_data_rms_evm_mean(self, selector_string):
        r"""Gets the stream RMS EVM of data subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of data stream RMS EVM results computed for each averaging count.

        Use "segment<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the stream RMS EVM of data subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_STREAM_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_stream_pilot_rms_evm_mean(self, selector_string):
        r"""Gets the stream RMS EVM of pilot subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of pilot stream RMS EVM results computed for each averaging count.

        Use "segment<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the stream RMS EVM of pilot subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_STREAM_PILOT_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_chain_rms_evm_mean(self, selector_string):
        r"""Gets the chain RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of chain RMS EVM results computed for each averaging count.

        Use "segment<*n*>/chain<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the chain RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_chain_rms_evm_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_chain_rms_evm_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_chain_data_rms_evm_mean(self, selector_string):
        r"""Gets the chain RMS EVM of data subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of data chain RMS EVM results computed for each averaging count.

        Use "segment<*n*>/chain<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the chain RMS EVM of data subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_CHAIN_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_chain_pilot_rms_evm_mean(self, selector_string):
        r"""Gets the chain RMS EVM of pilot subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of pilot chain RMS EVM results computed for each averaging count.

        Use "segment<*n*>/chain<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the chain RMS EVM of pilot subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_CHAIN_PILOT_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_stream_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of all subcarriers in all OFDM symbols for the specified user. This value is expressed as a
        percentage or in dB.

        This result is applicable for MU PPDU. When you set
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of RMS EVM results for the specified user that is computed for each averaging count.

        Use "user<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of all subcarriers in all OFDM symbols for the specified user. This value is expressed as a
                percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_STREAM_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_stream_rms_evm_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_STREAM_RMS_EVM_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_stream_rms_evm_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_STREAM_RMS_EVM_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_stream_data_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of data-subcarriers in all OFDM symbols for the specified user. This value is expressed as a
        percentage or in dB.

        This result is applicable for MU PPDU. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of data RMS EVM results for the specified user that is computed for each averaging count.

        Use "user<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of data-subcarriers in all OFDM symbols for the specified user. This value is expressed as a
                percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_STREAM_DATA_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_stream_pilot_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of pilot-subcarriers in all OFDM symbols for the specified user. This value is expressed as a
        percentage or in dB.

        This result is applicable for MU PPDU. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of pilot RMS EVM results for the specified user that is computed for each averaging count.

        Use "user<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of pilot-subcarriers in all OFDM symbols for the specified user. This value is expressed as a
                percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_STREAM_PILOT_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_sig_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the L-SIG symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the L-SIG symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_L_SIG_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sig_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the SIG symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the SIG symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SIG_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sig_b_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the SIG-B symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the SIG-B symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SIG_B_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_u_sig_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the U-SIG symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the U-SIG symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_U_SIG_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_sig_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the EHT-SIG symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the EHT-SIG symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_EHT_SIG_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_sig_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the UHR-SIG symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the UHR-SIG symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_UHR_SIG_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_elr_sig_rms_evm_mean(self, selector_string):
        r"""Gets the RMS EVM of subcarriers in the ELR-SIG symbol. This value is expressed as a percentage or in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS EVM of subcarriers in the ELR-SIG symbol. This value is expressed as a percentage or in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_ELR_SIG_RMS_EVM_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the L-STF or STF field. This value is expressed in dBm.

        This result is not applicable for 802.11n greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the L-STF or STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the L-STF or STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_L_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the L-STF or STF field. This value is expressed in dBm.

        This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the L-STF or STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the L-STF or STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_L_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_ltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the L-LTF or LTF field. This value is expressed in dBm.

        This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the L-LTF or LTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the L-LTF or LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_L_LTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_ltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the L-LTF or LTF field. This value is expressed in dBm.

        This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the L-LTF or LTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the L-LTF or LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_L_LTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the L-SIG or SIGNAL field. This value is expressed in dBm.

        This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the L-SIG or SIGNAL field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the L-SIG or SIGNAL field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_L_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the L-SIG or SIGNAL field. This value is expressed in dBm.

        This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the L-SIG or SIGNAL field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the L-SIG or SIGNAL field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_L_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rl_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the RL-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11ax and 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the RL-SIG field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the RL-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_RL_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rl_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the RL-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11ax and 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the RL-SIG field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the RL-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_RL_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the HT-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HT-SIG field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HT-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HT-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HT-SIG field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HT-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_sig_a_average_power_mean(self, selector_string):
        r"""Gets the average power of the VHT-SIG-A field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the VHT-SIG-A field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the VHT-SIG-A field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_SIG_A_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_sig_a_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the VHT-SIG-A field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the VHT-SIG-A field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the VHT-SIG-A field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_SIG_A_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_sig_a_average_power_mean(self, selector_string):
        r"""Gets the average power of the HE-SIG-A field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HE-SIG-A field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HE-SIG-A field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_SIG_A_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_sig_a_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HE-SIG-A field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HE-SIG-A field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HE-SIG-A field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_SIG_A_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_u_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the U-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the U-SIG field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the U-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_U_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_u_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the U-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the U-SIG field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the U-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_U_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_elr_mark_average_power_mean(self, selector_string):
        r"""Gets the average power of the ELR-MARK field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the ELR-MARK field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the ELR-MARK field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_ELR_MARK_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_elr_mark_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the ELR-MARK field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the ELR-MARK field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the ELR-MARK field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_ELR_MARK_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_sig_b_average_power_mean(self, selector_string):
        r"""Gets the average power of the VHT-SIG-B field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the VHT-SIG-B field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the VHT-SIG-B field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_SIG_B_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_sig_b_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the VHT-SIG-B field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the VHT-SIG-B field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the VHT-SIG-B field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_SIG_B_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_sig_b_average_power_mean(self, selector_string):
        r"""Gets the average power of the HE-SIG-B field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HE-SIG-B field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HE-SIG-B field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_SIG_B_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_sig_b_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HE-SIG-B field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HE-SIG-B field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HE-SIG-B field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_SIG_B_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the EHT-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the EHT-SIG field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the EHT-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_EHT_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the EHT-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the EHT-SIG field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the EHT-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_EHT_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the UHR-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the UHR-SIG field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the UHR-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_UHR_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the UHR-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the UHR-SIG field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the UHR-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_UHR_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_elr_sig_average_power_mean(self, selector_string):
        r"""Gets the average power of the ELR-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the ELR-SIG field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the ELR-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_ELR_SIG_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_elr_sig_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the ELR-SIG field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the ELR-SIG field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the ELR-SIG field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_ELR_SIG_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the HT-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HT-STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HT-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HT-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HT-STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HT-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_htgf_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the HT-GF-STF. This value is expressed in dBm.

        This result is applicable only to 802.11n greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HT-GF-STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HT-GF-STF. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_GF_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_htgf_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HT-GF-STF. This value is expressed in dBm.

        This result is applicable only to 802.11n greenfield PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HT-GF-STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HT-GF-STF. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_GF_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the VHT-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the VHT-STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the VHT-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the VHT-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the VHT-STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the VHT-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the HE-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HE-STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HE-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HE-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HE-STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HE-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the EHT-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the EHT-STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the EHT-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_EHT_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the EHT-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the EHT-STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the EHT-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_EHT_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_stf_average_power_mean(self, selector_string):
        r"""Gets the average power of the UHR-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the UHR-STF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the UHR-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_UHR_STF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_stf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the UHR-STF field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the UHR-STF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the UHR-STF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_UHR_STF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_dltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the HT-DLTF. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HT-DLTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HT-DLTF. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_DLTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_dltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HT-DLTF field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HT-DLTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HT-DLTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_DLTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_eltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the HT-ELTF field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HT-ELTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HT-ELTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_ELTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ht_eltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HT-ELTF field. This value is expressed in dBm.

        This result is applicable only to 802.11n signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HT-ELTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HT-ELTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HT_ELTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_ltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the VHT-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the VHT-LTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the VHT-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_LTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_vht_ltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the VHT-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11ac signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the VHT-LTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the VHT-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_VHT_LTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_ltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the HE-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the HE-LTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the HE-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_LTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_he_ltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the HE-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11ax signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the HE-LTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the HE-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_HE_LTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_ltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the EHT-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the EHT-LTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the EHT-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_EHT_LTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_ltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the EHT-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the EHT-LTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the EHT-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_EHT_LTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_ltf_average_power_mean(self, selector_string):
        r"""Gets the average power of the UHR-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the UHR-LTF average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the UHR-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_UHR_LTF_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_ltf_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the UHR-LTF field. This value is expressed in dBm.

        This result is applicable only to 802.11bn signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the UHR-LTF peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the UHR-LTF field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_UHR_LTF_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_data_average_power_mean(self, selector_string):
        r"""Gets the average power of the data field. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the data field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the data field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_DATA_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_data_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the data field. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the maximum of the data field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the data field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_DATA_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pe_average_power_mean(self, selector_string):
        r"""Gets the average power of the packet extension field. This value is expressed in dBm.

        This result is applicable for 802.11ax and 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the packet extension field average power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the average power of the packet extension field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_PE_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pe_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the packet extension field. This value is expressed in dBm.

        This result is applicable only to 802.11ax and 802.11be signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the maximum of the PE  field peak power results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the peak power of the packet extension field. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_PE_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ppdu_average_power_mean(self, selector_string):
        r"""Gets the average power of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the PPDU average power results computed for each averaging count.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_PPDU_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ppdu_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the PPDU. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the maximum of the PPDU peak power results computed for each averaging count.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_PPDU_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_custom_gate_average_power_mean(self, selector_string):
        r"""Gets the average power of the custom gate. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the custom gate average power results computed for each averaging count.

        Use "gate<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_CUSTOM_GATE_AVERAGE_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_custom_gate_peak_power_maximum(self, selector_string):
        r"""Gets the peak power of the custom gate. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the maximum of the custom gate peak power results computed for each averaging count.

        Use "gate<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_POWER_CUSTOM_GATE_PEAK_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_cross_power_mean(self, selector_string):
        r"""Gets the cross power. The cross power for chain *x* is the power contribution from streams other than stream *x* in
        the chain. This value is expressed in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the cross power results computed for each averaging count.

        Use "segment<*n*>/chain<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the cross power. The cross power for chain *x* is the power contribution from streams other than stream *x* in
                the chain. This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_CROSS_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_power_mean(self, selector_string):
        r"""Gets the user power. User power is the frequency domain power measured over subcarriers occupied by a given user.
        This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the user power results computed for each averaging count.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the user power. User power is the frequency domain power measured over subcarriers occupied by a given user.
                This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_power_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_POWER_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_user_power_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_USER_POWER_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_stream_power_mean(self, selector_string):
        r"""Gets average stream power across iterations for combined signal demodulation. This is applicable only if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of stream power results computed for each averaging count.

        Use "segment<*n*>/stream<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns average stream power across iterations for combined signal demodulation. This is applicable only if
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_STREAM_POWER_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_margin(self, selector_string):
        r"""Gets the spectral flatness margin, which is the minimum of the upper and lower spectral flatness margins. This value
        is expressed in dB.

        The upper spectral flatness margin is the minimum difference between the upper mask and the spectral flatness
        across subcarriers. The lower spectral flatness margin is the minimum difference between the spectral flatness and the
        lower mask across subcarriers. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, the spectral flatness
        is computed using the mean of the channel frequency response magnitude computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the spectral flatness margin, which is the minimum of the upper and lower spectral flatness margins. This value
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
                attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_margin_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_margin_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_spectral_flatness_margin_subcarrier_index(self, selector_string):
        r"""Gets the subcarrier index corresponding to the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN` result.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the subcarrier index corresponding to the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN` result.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_SUBCARRIER_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_unused_tone_error_margin(self, selector_string):
        r"""Gets the unused tone error margin, which is the minimum difference between the unused tone error mask and the unused
        tone error across 26-tone RUs. This value is expressed in dB.

        This result is applicable only to 802.11ax, 802.11be and 802.11bn TB PPDU signals. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, the measurement
        computes the mean of the unused tone error over each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the unused tone error margin, which is the minimum difference between the unused tone error mask and the unused
                tone error across 26-tone RUs. This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_unused_tone_error_margin_ru_index(self, selector_string):
        r"""Gets the 26-tone RU index corresponding to the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN`  result.

        This result is applicable for 802.11ax, 802.11be and 802.11bn TB PPDU signals.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the 26-tone RU index corresponding to the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN`  result.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN_RU_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_burst_start_time_mean(self, selector_string):
        r"""Gets the absolute time corresponding to the detected start of the analyzed burst. The start time is computed with
        respect to the initial time value of the acquired waveform. This value is expressed in seconds.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**,
        this attribute returns the mean of the burst start time computed for each averaging count.

        Use "segment<*n*>/chain<*k*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the absolute time corresponding to the detected start of the analyzed burst. The start time is computed with
                respect to the initial time value of the acquired waveform. This value is expressed in seconds.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_BURST_START_TIME_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_symbols_used(self, selector_string):
        r"""Gets the number of OFDM symbols used by the measurement.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the number of OFDM symbols used by the measurement.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_NUMBER_OF_SYMBOLS_USED.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_noise_compensation_applied(self, selector_string):
        r"""Gets whether the noise compensation is applied.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+------------------------------------+
        | Name (Value) | Description                        |
        +==============+====================================+
        | False (0)    | Noise compensation is not applied. |
        +--------------+------------------------------------+
        | True (1)     | Noise compensation is applied.     |
        +--------------+------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccNoiseCompensationApplied):
                Returns whether the noise compensation is applied.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_NOISE_COMPENSATION_APPLIED.value,
            )
            attr_val = enums.OfdmModAccNoiseCompensationApplied(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_frequency_error_mean(self, selector_string):
        r"""Gets the carrier frequency error of the transmitter. This value is expressed in Hz.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the carrier frequency error results computed for each averaging count.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_FREQUENCY_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_frequency_error_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_FREQUENCY_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_frequency_error_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_FREQUENCY_ERROR_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_frequency_error_ccdf_10_percent(self, selector_string):
        r"""Gets the 10% point of Complementary Cumulative Distribution Function (CCDF) of the absolute frequency error. This
        value is expressed in Hz.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, the CCDF is computed over each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the 10% point of Complementary Cumulative Distribution Function (CCDF) of the absolute frequency error. This
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
                attributes.AttributeID.OFDMMODACC_RESULTS_FREQUENCY_ERROR_CCDF_10_PERCENT.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_symbol_clock_error_mean(self, selector_string):
        r"""Gets the symbol clock error of the transmitter.

        Symbol clock error is the difference between the symbol clocks at the digital-to-analog converter (DAC) of the
        transmitting device under test (DUT) and the digitizer of the instrument. This value is expressed in parts per million
        (ppm).

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the symbol clock error results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the symbol clock error of the transmitter.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SYMBOL_CLOCK_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_symbol_clock_error_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_SYMBOL_CLOCK_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_symbol_clock_error_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_SYMBOL_CLOCK_ERROR_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_relative_iq_origin_offset_mean(self, selector_string):
        r"""Gets the relative I/Q origin offset, which is the ratio of the power of the DC subcarrier to the total power of all
        the subcarriers. This value is expressed in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the relative I/Q origin offset computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the relative I/Q origin offset, which is the ratio of the power of the DC subcarrier to the total power of all
                the subcarriers. This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_RELATIVE_IQ_ORIGIN_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_relative_iq_origin_offset_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_RELATIVE_IQ_ORIGIN_OFFSET_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_relative_iq_origin_offset_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_RELATIVE_IQ_ORIGIN_OFFSET_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_absolute_iq_origin_offset_mean(self, selector_string):
        r"""Gets the absolute I/Q origin offset, which is the power of the DC subcarrier. This value is expressed in dBm.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the absolute I/Q origin offset computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the absolute I/Q origin offset, which is the power of the DC subcarrier. This value is expressed in dBm.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_ABSOLUTE_IQ_ORIGIN_OFFSET_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_mean(self, selector_string):
        r"""Gets the I/Q gain imbalance, which is the ratio of the RMS amplitude of the in-phase (I) component of the signal to
        the RMS amplitude of the quadrature-phase (Q) component of the signal. This value is expressed in dB.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the I/Q gain imbalance results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q gain imbalance, which is the ratio of the RMS amplitude of the in-phase (I) component of the signal to
                the RMS amplitude of the quadrature-phase (Q) component of the signal. This value is expressed in dB.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_GAIN_IMBALANCE_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_GAIN_IMBALANCE_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_gain_imbalance_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_GAIN_IMBALANCE_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_mean(self, selector_string):
        r"""Gets the I/Q quadrature error, which is a measure of deviation of the phase difference between the quadrature-phase
        (Q) and the in-phase (I) component of the signal from 90 degrees. This value is expressed in degrees.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the I/Q quadrature error results computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q quadrature error, which is a measure of deviation of the phase difference between the quadrature-phase
                (Q) and the in-phase (I) component of the signal from 90 degrees. This value is expressed in degrees.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_QUADRATURE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_maximum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_QUADRATURE_ERROR_MAXIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_quadrature_error_minimum(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_QUADRATURE_ERROR_MINIMUM.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_iq_timing_skew_mean(self, selector_string):
        r"""Gets the I/Q timing skew, which is the difference between the group delay of the in-phase (I) and quadrature (Q)
        components of the signal. This value is expressed in seconds.

        When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
        **True**, this attribute returns the mean of the I/Q timing skew computed for each averaging count.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the I/Q timing skew, which is the difference between the group delay of the in-phase (I) and quadrature (Q)
                components of the signal. This value is expressed in seconds.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_IQ_TIMING_SKEW_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rms_common_phase_error_mean(self, selector_string):
        r"""Gets the RMS common phase error.

        Common phase error for an OFDM symbol is the average phase deviation of the pilot-subcarriers from their ideal
        phase. RMS Common Phase Error is the RMS of common phase error of all OFDM symbols. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the RMS common phase error computed for each averaging count.

        Refer to `Common Pilot Error <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/common-pilot-error.html>`_ for more
        information.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS common phase error.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_RMS_COMMON_PHASE_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_rms_common_pilot_error_mean(self, selector_string):
        r"""Gets the RMS common pilot error. This value is expressed as a percentage.

        Common pilot error for an OFDM symbol is the correlation of the received pilot subcarrier QAM symbols with
        their ideal values. RMS Common Pilot Error is the RMS of 1 minus common pilot error for all OFDM symbols. When you set
        the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
        returns the mean of the RMS common pilot error computed for each averaging count.

        Refer to `Common Pilot Error <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/common-pilot-error.html>`_ for more
        information.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the RMS common pilot error. This value is expressed as a percentage.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_RMS_COMMON_PILOT_ERROR_MEAN.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ppdu_type(self, selector_string):
        r"""Gets the PPDU type of the measured signal.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)          | Description                                                                                                              |
        +=======================+==========================================================================================================================+
        | Non-HT (0)            | Indicates an 802.11a, 802.11j, or 802.11p PPDU, or 802.11n, 802.11ac, or 802.11ax PPDU operating in the Non-HT mode.     |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Mixed (1)             | Indicates the HT-mixed PPDU (802.11n).                                                                                   |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Greenfield (2)        | Applicable HT-Greenfield PPDU (802.11n).                                                                                 |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | SU (3)                | Indicates the VHT SU PPDU if you set the Standard attribute to 802.11ac or the HE SU PPDU if you set the Standard        |
        |                       | attribute to 802.11ax.                                                                                                   |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | MU (4)                | Indicates the VHT MU PPDU if you set the Standard attribute to 802.11ac, the HE MU PPDU if you set the Standard          |
        |                       | attribute to 802.11ax, the EHT MU PPDU if you set the Standard attribute to 802.11be, or the UHR MU PPDU if you set the  |
        |                       | Standard attribute to 802.11bn.                                                                                          |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Extended Range SU (5) | Indicates the HE Extended Range SU PPDU (802.11ax).                                                                      |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Trigger-based (6)     | Indicates the HE TB PPDU if you set the Standard attribute to 802.11ax, the EHT TB PPDU if you set the Standard          |
        |                       | attribute to 802.11be, or the UHR TB PPDU if you set the Standard attribute to 802.11bn.                                 |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | ELR (7)               | Indicates the UHR Enhanced Long Range PPDU (802.11bn).                                                                   |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmPpduType):
                Returns the PPDU type of the measured signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_PPDU_TYPE.value
            )
            attr_val = enums.OfdmPpduType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_mcs_index(self, selector_string):
        r"""Gets the MCS index or the data rate of the measured signal.

        The MCS index or data rate for various standard signals are decoded as follows:

        +----------------------------------------+----------------------------------------------------+
        | Standard                               | Field                                              |
        +========================================+====================================================+
        | 802.11a, 802.11j, 802.11p              | The data rate is decoded from the SIGNAL field.    |
        +----------------------------------------+----------------------------------------------------+
        | 802.11n                                | The MCS index is decoded from the HT-SIG field.    |
        +----------------------------------------+----------------------------------------------------+
        | 802.11ac SU                            | The MCS index is decoded from the VHT-SIG-A field. |
        +----------------------------------------+----------------------------------------------------+
        | 802.11ac MU                            | The MCS index is decoded from the VHT-SIG-B field. |
        +----------------------------------------+----------------------------------------------------+
        | 802.11ax SU and Extended Range SU PPDU | The MCS index is decoded from the HE-SIG-A field.  |
        +----------------------------------------+----------------------------------------------------+
        | 802.11ax MU PPDU                       | The MCS index is decoded from the HE-SIG-B field.  |
        +----------------------------------------+----------------------------------------------------+
        | 802.11be MU PPDU                       | The MCS index is decoded from the EHT-SIG field.   |
        +----------------------------------------+----------------------------------------------------+
        | 802.11bn MU PPDU                       | The MCS index is decoded from the UHR-SIG field.   |
        +----------------------------------------+----------------------------------------------------+
        | 802.11bn ELR PPDU                      | The MCS index is decoded from the ELR-SIG field.   |
        +----------------------------------------+----------------------------------------------------+

        For 802.11a, 802.11j, and 802.11p signals, the following MCS indices corresponds to their data rates:

        +-----+----------------------------------------------------------------------------------------------------+
        | MCS | Data Rate                                                                                          |
        +=====+====================================================================================================+
        | 0   | 1.5 Mbps, 3 Mbps, and 6 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.    |
        +-----+----------------------------------------------------------------------------------------------------+
        | 1   | 2.25 Mbps, 4.5 Mbps, and 9 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively. |
        +-----+----------------------------------------------------------------------------------------------------+
        | 2   | 3 Mbps, 6 Mbps, and 12 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.     |
        +-----+----------------------------------------------------------------------------------------------------+
        | 3   | 4.5 Mbps, 9 Mbps, and 18 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.   |
        +-----+----------------------------------------------------------------------------------------------------+
        | 4   | 6 Mbps, 12 Mbps, and 24 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.    |
        +-----+----------------------------------------------------------------------------------------------------+
        | 5   | 9 Mbps, 18 Mbps, and 36 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.    |
        +-----+----------------------------------------------------------------------------------------------------+
        | 6   | 12 Mbps, 24 Mbps, and 48 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.   |
        +-----+----------------------------------------------------------------------------------------------------+
        | 7   | 13.5 Mbps, 27 Mbps, and 54 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively. |
        +-----+----------------------------------------------------------------------------------------------------+

        For 802.11ax, 802.11be or 802.11bn TB PPDU signals, this attribute returns the same value as the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_MCS_INDEX` attribute.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for MU PPDU signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the MCS index or the data rate of the measured signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_MCS_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_aggregation(self, selector_string):
        r"""Gets the value of the Aggregation field as decoded from the high-throughput signal (HT-SIG) field of 802.11n signal.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the value of the Aggregation field as decoded from the high-throughput signal (HT-SIG) field of 802.11n signal.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_AGGREGATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_fec_coding_type(self, selector_string):
        r"""Gets the FEC coding type for a specified user.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for MU and TB PPDU
        signals.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | BCC (0)      | Indicates that the FEC coding type is BCC.  |
        +--------------+---------------------------------------------+
        | LDPC (1)     | Indicates that the FEC coding type is LDPC. |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccFecCodingType):
                Returns the FEC coding type for a specified user.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_FEC_CODING_TYPE.value,
            )
            attr_val = enums.OfdmModAccFecCodingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ru_size(self, selector_string):
        r"""Gets the RU or the MRU size.

        This result is applicable for 802.11ax MU, extended range SU, and TB PPDU signals, 802.11be MU and TB PPDU
        signals, and 802.11bn MU and TB PPDU signals. For 802.11ax MU PPDU signals, this value is decoded from the HE-SIG-B
        field. For 802.11ax extended range SU PPDU signals, this value is decoded from the HE-SIG-A field. For 802.11be MU PPDU
        signals, this value is decoded from the EHT-SIG field. For 802.11bn MU PPDU signals, this value is decoded from the
        UHR-SIG field. For 802.11ax, 802.11be or 802.11bn TB PPDU signals, this attribute returns the same value as the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_SIZE` attribute.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the RU or the MRU size.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_RU_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ru_offset_mru_index(self, selector_string):
        r"""Gets the location of RU or MRU for a user. If an RU is detected, the RU Offset is in terms of the index of a 26-tone
        RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is detected, the MRU Index is as defined in the
        Table 36-8 to Table 36-15 of *IEEE P802.11be/D7.0*.

        This result is applicable for 802.11ax MU and TB PPDU signals, and 802.11be MU and TB PPDU signals. For
        802.11ax MU PPDU signals, this value is decoded from the HE-SIG-B field. For 802.11be MU PPDU signals, this value is
        decoded from the EHT-SIG field. For 802.11ax or 802.11be TB PPDU signals, this attribute returns the same value as the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_OFFSET_MRU_INDEX` attribute.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the location of RU or MRU for a user. If an RU is detected, the RU Offset is in terms of the index of a 26-tone
                RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is detected, the MRU Index is as defined in the
                Table 36-8 to Table 36-15 of *IEEE P802.11be/D7.0*.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_RU_OFFSET_MRU_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ru_type(self, selector_string):
        r"""Gets the type of RU for a user.

        This result is applicable for 802.11bn TB PPDU signals. For 802.11bn TB PPDU signals, this attribute returns
        the same value as the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE` attribute.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        +--------------+---------------------+
        | Name (Value) | Description         |
        +==============+=====================+
        | rRU (0)      | The RU type is rRU. |
        +--------------+---------------------+
        | dRU (1)      | The RU type is dRU. |
        +--------------+---------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccRUType):
                Returns the type of RU for a user.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_RU_TYPE.value
            )
            attr_val = enums.OfdmModAccRUType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_distribution_bandwidth(self, selector_string):
        r"""Gets the bandwidth across which RU Subcarriers are distributed for a user.

        This result is applicable for 802.11bn TB PPDU signals when RU Type is dRU. For 802.11bn TB PPDU signals, this
        attribute returns the same value as the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_DISTRIBUTION_BANDWIDTH`
        attribute.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the bandwidth across which RU Subcarriers are distributed for a user.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_DISTRIBUTION_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_users(self, selector_string):
        r"""Gets the number of users.

        For 802.11ac MU PPDU signals, this value is decoded from the VHT-SIG-A field. For 802.11ax MU PPDU signals,
        this value is derived from the HE-SIG-B field. For 802.11be MU PPDU signals, this value is decoded from the EHT-SIG
        field. For 802.11bn MU PPDU signals, this value is decoded from the UHR-SIG field.

        For all other PPDUs, this attribute returns 1.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the number of users.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_NUMBER_OF_USERS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_he_sig_b_symbols(self, selector_string):
        r"""Gets the number of HE-SIG-B symbols.

        This result is applicable only to 802.11ax MU PPDU signals, and is decoded from the HE-SIG-A field.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the number of HE-SIG-B symbols.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_NUMBER_OF_HE_SIG_B_SYMBOLS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_sig_symbols(self, selector_string):
        r"""

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):


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
                attributes.AttributeID.OFDMMODACC_RESULTS_NUMBER_OF_SIG_SYMBOLS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_guard_interval_type(self, selector_string):
        r"""Gets the size of the guard interval of OFDM symbols.

        This result is always **1/4** for 802.11a, 802.11j, and 802.11p signals. The value is decoded for various
        standards as follows:

        +-----------+----------------------------------------------------------+
        | Standards | Fields                                                   |
        +===========+==========================================================+
        | 802.11n   | The guard interval type is decoded from HT-SIG field.    |
        +-----------+----------------------------------------------------------+
        | 802.11ac  | The guard interval type is decoded from VHT-SIG-A field. |
        +-----------+----------------------------------------------------------+
        | 802.11ax  | The guard interval type is decoded from HE-SIG-A field.  |
        +-----------+----------------------------------------------------------+
        | 802.11be  | The guard interval type is decoded from EHT-SIG field.   |
        +-----------+----------------------------------------------------------+
        | 802.11bn  | The guard interval type is decoded from UHR-SIG field.   |
        +-----------+----------------------------------------------------------+

        For 802.11ax, 802.11be, or 802.11bn TB PPDU signals, the attribute returns the same value as the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_GUARD_INTERVAL_TYPE` attribute.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | 1/4 (0)      | The Guard interval is 1/4th of the IFFT duration.  |
        +--------------+----------------------------------------------------+
        | 1/8 (1)      | The Guard interval is 1/8th of the IFFT duration.  |
        +--------------+----------------------------------------------------+
        | 1/16 (2)     | The Guard interval is 1/16th of the IFFT duration. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmGuardIntervalType):
                Returns the size of the guard interval of OFDM symbols.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_GUARD_INTERVAL_TYPE.value,
            )
            attr_val = enums.OfdmGuardIntervalType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_ltf_size(self, selector_string):
        r"""Gets the HE-LTF size, EHT-LTF or UHR-LTF size when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to **802.11ax**, **802.11be**, or **802.11bn**,
        respectively.

        This result is applicable only to 802.11ax, 802.11be and 802.11bn signals. This value is decoded from the
        HE-SIG-A field when you set the Standard attribute to **802.11ax**, from the EHT-SIG field when you set the Standard
        attribute to **802.11be**, and from the UHR-SIG field when you set the Standard attribute to **802.11bn**.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +---------------------+------------------------------------------------------------------+
        | Name (Value)        | Description                                                      |
        +=====================+==================================================================+
        | Not Applicable (-1) | Indicates that the LTF Size is invalid for the current waveform. |
        +---------------------+------------------------------------------------------------------+
        | 4x (0)              | Indicates that the LTF Size is 4x.                               |
        +---------------------+------------------------------------------------------------------+
        | 2x (1)              | Indicates that the LTF Size is 2x.                               |
        +---------------------+------------------------------------------------------------------+
        | 1x (2)              | Indicates that the LTF Size is 1x.                               |
        +---------------------+------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmLtfSize):
                Returns the HE-LTF size, EHT-LTF or UHR-LTF size when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to **802.11ax**, **802.11be**, or **802.11bn**,
                respectively.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_LTF_SIZE.value
            )
            attr_val = enums.OfdmLtfSize(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_number_of_space_time_streams(self, selector_string):
        r"""Gets the number of space time streams.

        The value is decoded for various standards as follows:

        +----------+----------------------------------------------------------------------------------------------------------------+
        | Standard | Derivation                                                                                                     |
        +==========+================================================================================================================+
        | 802.11n  | Derived from the MCS field and STBC field of the HT-SIG.                                                       |
        +----------+----------------------------------------------------------------------------------------------------------------+
        | 802.11ac | Derived from the NSTS field of the VHT-SIG-A.                                                                  |
        +----------+----------------------------------------------------------------------------------------------------------------+
        | 802.11ax | Derived from the HE-SIG-A for HE SU PPDU and HE Extended Range PPDU. Derived from the HE-SIG-B for HE MU PPDU. |
        +----------+----------------------------------------------------------------------------------------------------------------+
        | 802.11be | Derived from the EHT-SIG for EHT MU PPDU.                                                                      |
        +----------+----------------------------------------------------------------------------------------------------------------+
        | 802.11bn | Derived from the UHR-SIG for UHR MU PPDU.                                                                      |
        +----------+----------------------------------------------------------------------------------------------------------------+

        For all other configurations, the attribute returns the value of 1.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the number of space time streams.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_NUMBER_OF_SPACE_TIME_STREAMS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_space_time_stream_offset(self, selector_string):
        r"""Gets the space time stream offset. This attribute is applicable only to 802.11ac, 802.11ax, 802.11be, and 802.11bn
        signals.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the space time stream offset. This attribute is applicable only to 802.11ac, 802.11ax, 802.11be, and 802.11bn
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
                attributes.AttributeID.OFDMMODACC_RESULTS_SPACE_TIME_STREAM_OFFSET.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_dcm_enabled(self, selector_string):
        r"""Gets whether DCM is enabled for a specified user.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for 802.11ax MU and TB
        PPDU signals.

        +--------------+--------------------------------------------------------+
        | Name (Value) | Description                                            |
        +==============+========================================================+
        | False (0)    | Indicates that DCM is disabled for the specified user. |
        +--------------+--------------------------------------------------------+
        | True (1)     | Indicates that DCM is enabled for the specified user.  |
        +--------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccDcmEnabled):
                Returns whether DCM is enabled for a specified user.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_DCM_ENABLED.value
            )
            attr_val = enums.OfdmModAccDcmEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_2xldpc_enabled(self, selector_string):
        r"""Gets whether 2xLDPC is enabled for a specified user.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for 802.11bn MU and TB
        PPDU signals.

        +--------------+-----------------------------------------------------------+
        | Name (Value) | Description                                               |
        +==============+===========================================================+
        | False (0)    | Indicates that 2xLDPC is disabled for the specified user. |
        +--------------+-----------------------------------------------------------+
        | True (1)     | Indicates that 2xLDPC is enabled for the specified user.  |
        +--------------+-----------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAcc2xLdpcEnabled):
                Returns whether 2xLDPC is enabled for a specified user.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_2xLDPC_ENABLED.value,
            )
            attr_val = enums.OfdmModAcc2xLdpcEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_im_pilots_enabled(self, selector_string):
        r"""Gets whether interference mitigating pilots are present.

        This result is applicable only to 802.11bn MU PPDU signals.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | False (0)    | Indicates that interference mitigating pilots are absent.  |
        +--------------+------------------------------------------------------------+
        | True (1)     | Indicates that interference mitigating pilots are present. |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccIMPilotsEnabled):
                Returns whether interference mitigating pilots are present.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_IM_PILOTS_ENABLED.value,
            )
            attr_val = enums.OfdmModAccIMPilotsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_unequal_modulation_enabled(self, selector_string):
        r"""Gets whether unequal modulation is enabled for a specified user.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for 802.11bn MU PPDU
        signals.

        +--------------+-----------------------------------------------------------------------+
        | Name (Value) | Description                                                           |
        +==============+=======================================================================+
        | False (0)    | Indicates that unequal modulation is disabled for the specified user. |
        +--------------+-----------------------------------------------------------------------+
        | True (1)     | Indicates that unequal modulation is enabled for the specified user.  |
        +--------------+-----------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccUnequalModulationEnabled):
                Returns whether unequal modulation is enabled for a specified user.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_UNEQUAL_MODULATION_ENABLED.value,
            )
            attr_val = enums.OfdmModAccUnequalModulationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_unequal_modulation_pattern_index(self, selector_string):
        r"""Gets unequal modulation pattern for a specified user.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for 802.11bn MU PPDU
        signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns unequal modulation pattern for a specified user.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_UNEQUAL_MODULATION_PATTERN_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_l_sig_parity_check_status(self, selector_string):
        r"""Gets whether the parity check has passed either for the SIGNAL field of the 802.11a/g waveform or for the L-SIG
        field of the 802.11n/802.11ac/802.11ax/802.11be/802.11bn waveforms.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +---------------------+--------------------------------------------------------------------+
        | Name (Value)        | Description                                                        |
        +=====================+====================================================================+
        | Not Applicable (-1) | Returns that the parity check is invalid for the current waveform. |
        +---------------------+--------------------------------------------------------------------+
        | Fail (0)            | Returns that the parity check failed.                              |
        +---------------------+--------------------------------------------------------------------+
        | Pass (1)            | Returns that the parity check passed.                              |
        +---------------------+--------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccLSigParityCheckStatus):
                Returns whether the parity check has passed either for the SIGNAL field of the 802.11a/g waveform or for the L-SIG
                field of the 802.11n/802.11ac/802.11ax/802.11be/802.11bn waveforms.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_L_SIG_PARITY_CHECK_STATUS.value,
            )
            attr_val = enums.OfdmModAccLSigParityCheckStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sig_crc_status(self, selector_string):
        r"""Gets whether the cyclic redundancy check (CRC) has passed either for the HT-SIG field of the 802.11n waveform, for
        the VHT-SIG-A field of the 802.11ac waveform, or for the HE-SIG-A field of the 802.11ax waveform.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +---------------------+---------------------------------------------------------------+
        | Name (Value)        | Description                                                   |
        +=====================+===============================================================+
        | Not Applicable (-1) | Returns that the SIG CRC is invalid for the current waveform. |
        +---------------------+---------------------------------------------------------------+
        | Fail (0)            | Returns that the SIG CRC failed.                              |
        +---------------------+---------------------------------------------------------------+
        | Pass (1)            | Returns that the SIG CRC passed.                              |
        +---------------------+---------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccSigCrcStatus):
                Returns whether the cyclic redundancy check (CRC) has passed either for the HT-SIG field of the 802.11n waveform, for
                the VHT-SIG-A field of the 802.11ac waveform, or for the HE-SIG-A field of the 802.11ax waveform.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SIG_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccSigCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_sig_b_crc_status(self, selector_string):
        r"""Gets whether the cyclic redundancy check (CRC) has passed for the HE-SIG-B field of the 802.11ax MU PPDU waveform.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +---------------------+------------------------------------------------------------------+
        | Name (Value)        | Description                                                      |
        +=====================+==================================================================+
        | Not Applicable (-1) | Returns that the SIG-B CRC                                       |
        |                     | is invalid for the current waveform.                             |
        +---------------------+------------------------------------------------------------------+
        | Fail (0)            | Returns that the SIG-B CRC failed.                               |
        +---------------------+------------------------------------------------------------------+
        | Pass (1)            | Returns that the SIG-B CRC passed.                               |
        +---------------------+------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccSigBCrcStatus):
                Returns whether the cyclic redundancy check (CRC) has passed for the HE-SIG-B field of the 802.11ax MU PPDU waveform.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SIG_B_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccSigBCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_u_sig_crc_status(self, selector_string):
        r"""Gets whether the cyclic redundancy check (CRC) has passed for the U-SIG field of the 802.11be or the 802.11bn
        waveform.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +---------------------+-----------------------------------------------------------------+
        | Name (Value)        | Description                                                     |
        +=====================+=================================================================+
        | Not Applicable (-1) | Returns that the U-SIG CRC is invalid for the current waveform. |
        +---------------------+-----------------------------------------------------------------+
        | Fail (0)            | Returns that the U-SIG CRC failed.                              |
        +---------------------+-----------------------------------------------------------------+
        | Pass (1)            | Returns that the U-SIG CRC passed.                              |
        +---------------------+-----------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccUSigCrcStatus):
                Returns whether the cyclic redundancy check (CRC) has passed for the U-SIG field of the 802.11be or the 802.11bn
                waveform.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_U_SIG_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccUSigCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_eht_sig_crc_status(self, selector_string):
        r"""Gets whether the cyclic redundancy check (CRC) has passed for the EHT-SIG field of the 802.11be waveform.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +---------------------+-------------------------------------------------------------------+
        | Name (Value)        | Description                                                       |
        +=====================+===================================================================+
        | Not Applicable (-1) | Returns that the EHT-SIG CRC is invalid for the current waveform. |
        +---------------------+-------------------------------------------------------------------+
        | Fail (0)            | Returns that the EHT-SIG CRC failed.                              |
        +---------------------+-------------------------------------------------------------------+
        | Pass (1)            | Returns that the EHT-SIG CRC passed.                              |
        +---------------------+-------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccEhtSigCrcStatus):
                Returns whether the cyclic redundancy check (CRC) has passed for the EHT-SIG field of the 802.11be waveform.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_EHT_SIG_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccEhtSigCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_uhr_sig_crc_status(self, selector_string):
        r"""Gets whether the cyclic redundancy check (CRC) has passed for the UHR-SIG field of the 802.11bn waveform.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +---------------------+-------------------------------------------------------------------+
        | Name (Value)        | Description                                                       |
        +=====================+===================================================================+
        | Not Applicable (-1) | Returns that the UHR-SIG CRC is invalid for the current waveform. |
        +---------------------+-------------------------------------------------------------------+
        | Fail (0)            | Returns that the UHR-SIG CRC failed.                              |
        +---------------------+-------------------------------------------------------------------+
        | Pass (1)            | Returns that the UHR-SIG CRC passed.                              |
        +---------------------+-------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccUhrSigCrcStatus):
                Returns whether the cyclic redundancy check (CRC) has passed for the UHR-SIG field of the 802.11bn waveform.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_UHR_SIG_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccUhrSigCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_elr_sig_crc_status(self, selector_string):
        r"""Gets whether the cyclic redundancy check (CRC) has passed for the ELR-SIG field of the 802.11bn waveform.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        +---------------------+-------------------------------------------------------------------+
        | Name (Value)        | Description                                                       |
        +=====================+===================================================================+
        | Not Applicable (-1) | Returns that the ELR-SIG CRC is invalid for the current waveform. |
        +---------------------+-------------------------------------------------------------------+
        | Fail (0)            | Returns that the ELR-SIG CRC failed.                              |
        +---------------------+-------------------------------------------------------------------+
        | Pass (1)            | Returns that the ELR-SIG CRC passed.                              |
        +---------------------+-------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccElrSigCrcStatus):
                Returns whether the cyclic redundancy check (CRC) has passed for the ELR-SIG field of the 802.11bn waveform.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_ELR_SIG_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccElrSigCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_psdu_crc_status(self, selector_string):
        r"""Indicates whether the cyclic redundancy check (CRC) of the received decoded PLCP service data unit (PSDU) has passed.

        The measurement calculates the CRC over the decoded bits, excluding the last 32 bits of each MAC Protocol Data
        Unit (MPDU). The measurement first compares this value with the CRC value in the received payload, which is represented
        by the last 32 bits of the MPDU and then aggregates the values.

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

            attr_val (enums.OfdmModAccPsduCrcStatus):
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
                attributes.AttributeID.OFDMMODACC_RESULTS_PSDU_CRC_STATUS.value,
            )
            attr_val = enums.OfdmModAccPsduCrcStatus(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_scrambler_seed(self, selector_string):
        r"""Gets the detected initial state of the scrambler, which is used to scramble the data bits in the device under test
        (DUT). RFmx uses the same seed to descramble the received bit-sequence.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for MU PPDU signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Returns the detected initial state of the scrambler, which is used to scramble the data bits in the device under test
                (DUT). RFmx uses the same seed to descramble the received bit-sequence.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_SCRAMBLER_SEED.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_pe_duration(self, selector_string):
        r"""Gets the duration of the packet extension field for the 802.11ax, 802.11be and 802.11bn signals. This value is
        expressed in seconds.

        This result is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **True**.

        You do not need to use a selector string to read this result for default signal and result instance. Refer to
        the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals and results.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the duration of the packet extension field for the 802.11ax, 802.11be and 802.11bn signals. This value is
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
                updated_selector_string, attributes.AttributeID.OFDMMODACC_RESULTS_PE_DURATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_phase_rotation_coefficient_1(self, selector_string):
        r"""Gets the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute returns detected value when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | +1 (0)       | Specifies that phase rotation coefficient 1 is +1. |
        +--------------+----------------------------------------------------+
        | -1 (1)       | Specifies that phase rotation coefficient 1 is –1. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccPhaseRotationCoefficient1):
                Specifies the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_PHASE_ROTATION_COEFFICIENT_1.value,
            )
            attr_val = enums.OfdmModAccPhaseRotationCoefficient1(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_phase_rotation_coefficient_2(self, selector_string):
        r"""Gets the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute returns detected value when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | +1 (0)       | Specifies that phase rotation coefficient 2 is +1. |
        +--------------+----------------------------------------------------+
        | -1 (1)       | Specifies that phase rotation coefficient 2 is –1. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccPhaseRotationCoefficient2):
                Specifies the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_PHASE_ROTATION_COEFFICIENT_2.value,
            )
            attr_val = enums.OfdmModAccPhaseRotationCoefficient2(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_phase_rotation_coefficient_3(self, selector_string):
        r"""Gets the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute returns detected value when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **True**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | +1 (0)       | Specifies that phase rotation coefficient 3 is +1. |
        +--------------+----------------------------------------------------+
        | -1 (1)       | Specifies that phase rotation coefficient 3 is –1. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmModAccPhaseRotationCoefficient3):
                Specifies the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.

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
                attributes.AttributeID.OFDMMODACC_RESULTS_PHASE_ROTATION_COEFFICIENT_3.value,
            )
            attr_val = enums.OfdmModAccPhaseRotationCoefficient3(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def fetch_chain_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_data_rms_evm_per_symbol_mean
    ):
        r"""Fetches the chain data-subcarriers RMS EVM per symbol trace. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the chain data RMS EVM per symbol computed for each averaging count.

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

            chain_data_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array of chain data-subcarriers RMS EVM of each OFDM symbol. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_chain_data_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, chain_data_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_chain_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_pilot_rms_evm_per_symbol_mean
    ):
        r"""Fetches the chain pilot-subcarriers RMS EVM per symbol trace. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the chain pilot RMS EVM per symbol computed for each averaging count.

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

            chain_pilot_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array of chain pilot-subcarriers RMS EVM of each OFDM symbol. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_chain_pilot_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, chain_pilot_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_chain_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, chain_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the chain RMS EVM per subcarrier trace. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the chain RMS EVM per subcarrier computed for each averaging count.

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

            chain_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns an array of chain RMS EVM of each subcarrier. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_chain_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, chain_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_chain_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, chain_rms_evm_per_symbol_mean
    ):
        r"""Fetches the chain RMS EVM per symbol trace. When you set the When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the chain RMS EVM per symbol computed for each averaging count.

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

            chain_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns an array of chain RMS EVM of OFDM symbol. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_chain_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, chain_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_chain_rms_evm(self, selector_string, timeout):
        r"""Fetches the chain RMS EVM results.

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
            Tuple (chain_rms_evm_mean, chain_data_rms_evm_mean, chain_pilot_rms_evm_mean, error_code):

            chain_rms_evm_mean (float):
                This parameter returns the chain RMS EVM of all subcarriers in all OFDM symbols. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of chain RMS EVM results computed for each averaging count. This value is expressed as a percentage or
                in dB.

            chain_data_rms_evm_mean (float):
                This parameter returns the chain RMS EVM of data subcarriers in all OFDM symbols. When you set the OFDMModAcc Averaging
                Enabled attribute to **True**, this parameter returns the mean of data chain RMS EVM results computed for each
                averaging count. This value is expressed as a percentage or in dB.

            chain_pilot_rms_evm_mean (float):
                This parameter returns the chain RMS EVM of pilot subcarriers in all OFDM symbols. When you set the OFDMModAcc
                Averaging Enabled attribute to **True**, this parameter returns the mean of pilot chain RMS EVM results computed for
                each averaging count. This value is expressed as a percentage or in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            chain_rms_evm_mean, chain_data_rms_evm_mean, chain_pilot_rms_evm_mean, error_code = (
                self._interpreter.ofdmmodacc_fetch_chain_rms_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return chain_rms_evm_mean, chain_data_rms_evm_mean, chain_pilot_rms_evm_mean, error_code

    @_raise_if_disposed
    def fetch_channel_frequency_response_mean_trace(
        self,
        selector_string,
        timeout,
        channel_frequency_response_mean_magnitude,
        channel_frequency_response_mean_phase,
    ):
        r"""Fetches the channel frequency response trace. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the channel frequency response trace computed for each averaging count.

        Use "segment<*n*>/chain<*k*>/stream<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and stream number.

                Example:

                "segment0/chain0/stream0"

                "result::r1/segment0/chain0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            channel_frequency_response_mean_magnitude (numpy.float32):
                This parameter returns an array of magnitudes of the channel frequency response for each subcarrier. This value is
                expressed in dB.

            channel_frequency_response_mean_phase (numpy.float32):
                This parameter returns an array of magnitudes of the channel frequency response for each subcarrier. This value is
                expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_channel_frequency_response_mean_trace(
                    updated_selector_string,
                    timeout,
                    channel_frequency_response_mean_magnitude,
                    channel_frequency_response_mean_phase,
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_group_delay_mean_trace(self, selector_string, timeout, group_delay_mean):
        r"""Fetches the group delay trace. Group delay is computed from the channel frequency response. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the group delay trace computed for each averaging count.

        Use "segment<*n*>/chain<*k*>/stream<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and stream number.

                Example:

                "segment0/chain0/stream0"

                "result::r1/segment0/chain0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            group_delay_mean (numpy.float32):
                This parameter returns an array of group delay responses. This value is expressed in seconds.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.ofdmmodacc_fetch_group_delay_mean_trace(
                updated_selector_string, timeout, group_delay_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_common_pilot_error_trace(
        self, selector_string, timeout, common_pilot_error_magnitude, common_pilot_error_phase
    ):
        r"""Fetches the common pilot error magnitude and phase traces.

        Use "segment<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and segment number.

                Example:

                "segment0"

                "result::r1/segment0"

                You can use the :py:meth:`build_segment_string` method  to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            common_pilot_error_magnitude (numpy.float32):
                This parameter returns an array of magnitude of the common pilot error for each OFDM symbol.

            common_pilot_error_phase (numpy.float32):
                This parameter returns an array of magnitude of the common pilot error for each OFDM symbol.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.ofdmmodacc_fetch_common_pilot_error_trace(
                updated_selector_string,
                timeout,
                common_pilot_error_magnitude,
                common_pilot_error_phase,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_composite_rms_evm(self, selector_string, timeout):
        r"""Fetches the composite RMS EVM results.

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
            Tuple (composite_rms_evm_mean, composite_data_rms_evm_mean, composite_pilot_rms_evm_mean, error_code):

            composite_rms_evm_mean (float):
                This parameter returns the RMS EVM of all subcarriers in all OFDM symbols. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
                **True**, this parameter returns the mean of the composite RMS EVM results computed for each averaging count.

            composite_data_rms_evm_mean (float):
                This parameter returns the RMS EVM of data-subcarriers in all OFDM symbols. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. When you set the OFDMModAcc Averaging Enabled attribute to **True**, this parameter returns the mean of
                the composite data RMS EVM results computed for each averaging count.

            composite_pilot_rms_evm_mean (float):
                This parameter returns the RMS EVM of pilot-subcarriers in all OFDM symbols. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. When you set the OFDMModAcc Averaging Enabled attribute to **True**, this parameter returns the mean of
                the composite pilot RMS EVM results computed for each averaging count.

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
                composite_rms_evm_mean,
                composite_data_rms_evm_mean,
                composite_pilot_rms_evm_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_composite_rms_evm(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            composite_rms_evm_mean,
            composite_data_rms_evm_mean,
            composite_pilot_rms_evm_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_cross_power(self, selector_string, timeout):
        r"""Fetches the cross power.

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
            Tuple (cross_power_mean, error_code):

            cross_power_mean (float):
                This parameter returns the cross power. The cross power for chain *x* is the power contribution from streams other than
                stream *x* in the chain. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED`
                attribute to **True**, this parameter returns the mean of the cross power results computed for each averaging count.
                This value is expressed in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            cross_power_mean, error_code = self._interpreter.ofdmmodacc_fetch_cross_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return cross_power_mean, error_code

    @_raise_if_disposed
    def fetch_custom_gate_powers_array(self, selector_string, timeout):
        r"""Fetches the average and peak power of the custom gates.

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
            Tuple (average_power_mean, peak_power_maximum, error_code):

            average_power_mean (float):
                This parameter returns an array of average powers of the custom gates. This value is expressed in dBm. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns an array of the mean of the average custom gate power results computed for each averaging count.

            peak_power_maximum (float):
                This parameter returns an array of peak powers of the custom gates. This value is expressed in dBm. When you set the
                OFDMModAcc Averaging Enabled attribute to **True**, this parameter returns an array of the maximum of the peak custom
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
                self._interpreter.ofdmmodacc_fetch_custom_gate_powers_array(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return average_power_mean, peak_power_maximum, error_code

    @_raise_if_disposed
    def fetch_data_average_power(self, selector_string, timeout):
        r"""Fetches the average power of the data  field.

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
            Tuple (data_average_power_mean, error_code):

            data_average_power_mean (float):
                This parameter returns the average power of the data field. This value is expressed in dBm. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the data average power results computed for each averaging count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            data_average_power_mean, error_code = (
                self._interpreter.ofdmmodacc_fetch_data_average_power(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return data_average_power_mean, error_code

    @_raise_if_disposed
    def fetch_data_constellation_trace(self, selector_string, timeout, data_constellation):
        r"""Fetches the constellation trace for the data-subcarriers.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            data_constellation (numpy.complex64):
                This parameter returns the demodulated QAM symbols from all the data-subcarriers in all the OFDM symbols.

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
            error_code = self._interpreter.ofdmmodacc_fetch_data_constellation_trace(
                updated_selector_string, timeout, data_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_reference_data_constellation_trace(
        self, selector_string, timeout, reference_data_constellation
    ):
        r"""Fetches the reference constellation trace for the data-subcarriers.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            reference_data_constellation (numpy.complex64):
                This parameter returns the reference QAM symbols for all the data-subcarriers in all the OFDM symbols.

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
            error_code = self._interpreter.ofdmmodacc_fetch_reference_data_constellation_trace(
                updated_selector_string, timeout, reference_data_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_data_peak_power(self, selector_string, timeout):
        r"""Fetches the peak power of the data field.

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
            Tuple (data_peak_power_maximum, error_code):

            data_peak_power_maximum (float):
                This parameter returns the peak power of the data field. This value is expressed in dBm. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns an array of the maximum of the data peak power results computed for each averaging count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            data_peak_power_maximum, error_code = (
                self._interpreter.ofdmmodacc_fetch_data_peak_power(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return data_peak_power_maximum, error_code

    @_raise_if_disposed
    def fetch_decoded_l_sig_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded L-SIG bits trace.

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
            Tuple (decoded_l_sig_bits, error_code):

            decoded_l_sig_bits (int):
                This parameter returns the array of bits in the SIGNAL field of the 802.11a/g waveform or the L-SIG field of the
                802.11n/802.11ac/802.11ax/802.11be/802.11bn waveforms.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_l_sig_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_l_sig_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_l_sig_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_psdu_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded PLCP service data unit (PSDU) bits.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and user number.

                Example:

                "user0"

                "result::r1/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

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
                self._interpreter.ofdmmodacc_fetch_decoded_psdu_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_psdu_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_service_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded Service bits.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and user number.

                Example:

                "user0"

                "result::r1/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (decoded_service_bits, error_code):

            decoded_service_bits (int):
                This parameter returns an array of Service bits obtained after demodulation and decoding.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_service_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_service_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_service_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_sig_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded SIG bits.

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
            Tuple (decoded_sig_bits, error_code):

            decoded_sig_bits (int):
                This parameter returns an array of bits in the HT-SIG field of the 802.11n waveform, the VHT-SIG-A field of the
                802.11ac waveform, or the HE-SIG-A field of the 802.11ax waveform.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_sig_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_sig_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_sig_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_sig_b_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded SIG-B bits.

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
            Tuple (decoded_sig_b_bits, error_code):

            decoded_sig_b_bits (int):
                This parameter returns an array of bits in the VHT-SIG-B field of the 802.11ac waveform or the HE-SIG-B field of the
                802.11ax waveform.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_sig_b_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_sig_b_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_sig_b_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_u_sig_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded U-SIG bits trace.

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
            Tuple (decoded_u_sig_bits, error_code):

            decoded_u_sig_bits (int):
                This parameter returns the array of bits in the U-SIG field of the 802.11be/802.11bn waveform for all 80 MHz subblocks.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_u_sig_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_u_sig_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_u_sig_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_eht_sig_bits_trace(self, selector_string, timeout):
        r"""Fetches the decoded EHT-SIG bits trace.

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
            Tuple (decoded_eht_sig_bits, error_code):

            decoded_eht_sig_bits (int):
                This parameter returns the array of bits in the EHT-SIG field of the 802.11be waveform for all 80 MHz subblocks.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_eht_sig_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_eht_sig_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_eht_sig_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_uhr_sig_bits_trace(self, selector_string, timeout):
        r"""

        Args:
            selector_string (string):
            timeout (float):
        Returns:
            Tuple (decoded_uhr_sig_bits, error_code):

            decoded_uhr_sig_bits (int):
            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_uhr_sig_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_uhr_sig_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_uhr_sig_bits, error_code

    @_raise_if_disposed
    def fetch_decoded_elr_sig_bits_trace(self, selector_string, timeout):
        r"""

        Args:
            selector_string (string):
            timeout (float):
        Returns:
            Tuple (decoded_elr_sig_bits, error_code):

            decoded_elr_sig_bits (int):
            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            decoded_elr_sig_bits, error_code = (
                self._interpreter.ofdmmodacc_fetch_decoded_elr_sig_bits_trace(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return decoded_elr_sig_bits, error_code

    @_raise_if_disposed
    def fetch_evm_subcarrier_indices(self, selector_string, timeout):
        r"""Fetches the array of subcarrier indices for which the EVM results are computed.

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
            Tuple (subcarrier_indices, error_code):

            subcarrier_indices (int):
                This parameter returns an array of subcarrier indices for which the EVM results are computed.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            subcarrier_indices, error_code = (
                self._interpreter.ofdmmodacc_fetch_evm_subcarrier_indices(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return subcarrier_indices, error_code

    @_raise_if_disposed
    def fetch_frequency_error_ccdf_10_percent(self, selector_string, timeout):
        r"""Fetches the 10% point of the complementary cumulative distribution function (CCDF) of frequency error across the number
        of iterations.

        Use "segment<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and segment number.

                Example:

                "segment0"

                "result::r1/segment0"

                You can use the :py:meth:`build_segment_string` method  to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (frequency_error_ccdf_10_percent, error_code):

            frequency_error_ccdf_10_percent (float):
                This parameter returns the 10% point of the CCDF of absolute frequency error. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, the CCDF is computed
                over each averaging count. This value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            frequency_error_ccdf_10_percent, error_code = (
                self._interpreter.ofdmmodacc_fetch_frequency_error_ccdf_10_percent(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return frequency_error_ccdf_10_percent, error_code

    @_raise_if_disposed
    def fetch_frequency_error_mean(self, selector_string, timeout):
        r"""Fetches the carrier frequency error of the transmitter.

        Use "segment<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and segment number.

                Example:

                "segment0"

                "result::r1/segment0"

                You can use the :py:meth:`build_segment_string` method  to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (frequency_error_mean, error_code):

            frequency_error_mean (float):
                This parameter returns the carrier frequency error of the transmitter. This value is expressed in Hz. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
                returns the mean of the carrier frequency error results computed for each averaging count.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            frequency_error_mean, error_code = (
                self._interpreter.ofdmmodacc_fetch_frequency_error_mean(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return frequency_error_mean, error_code

    @_raise_if_disposed
    def fetch_guard_interval_type(self, selector_string, timeout):
        r"""Fetches the guard interval type.

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
            Tuple (guard_interval_type, error_code):

            guard_interval_type (enums.OfdmGuardIntervalType):
                This parameter returns the size of the guard interval of OFDM symbols.

                +--------------+--------------------------------------------------------------+
                | Name (Value) | Description                                                  |
                +==============+==============================================================+
                | 1/4 (0)      | Indicates the guard interval is 1/4th of the IFFT duration.  |
                +--------------+--------------------------------------------------------------+
                | 1/8 (1)      | Indicates the guard interval is 1/8th of the IFFT duration.  |
                +--------------+--------------------------------------------------------------+
                | 1/16 (2)     | Indicates the guard interval is 1/16th of the IFFT duration. |
                +--------------+--------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            guard_interval_type, error_code = (
                self._interpreter.ofdmmodacc_fetch_guard_interval_type(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return guard_interval_type, error_code

    @_raise_if_disposed
    def fetch_ltf_size(self, selector_string, timeout):
        r"""Fetches the HE-LTF or EHT-LTF size for 802.11ax or 802.11be, respectively.

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
            Tuple (ltf_size, error_code):

            ltf_size (enums.OfdmLtfSize):
                This parameter returns the HE-LTF or EHT-LTF size. This result is applicable only to 802.11ax and 802.11be signals.

                +---------------------+-----------------------------------+
                | Name (Value)        | Description                       |
                +=====================+===================================+
                | Not Applicable (-1) | Result is not applicable.         |
                +---------------------+-----------------------------------+
                | 4x (0)              | The HE-LTF or EHT-LTF size is 4x. |
                +---------------------+-----------------------------------+
                | 2x (1)              | The HE-LTF or EHT-LTF size is 2x. |
                +---------------------+-----------------------------------+
                | 1x (2)              | The HE-LTF or EHT-LTF size is 1x. |
                +---------------------+-----------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            ltf_size, error_code = self._interpreter.ofdmmodacc_fetch_ltf_size(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return ltf_size, error_code

    @_raise_if_disposed
    def fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
    ):
        r"""Fetches the I/Q gain imbalance per subcarrier trace. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the I/Q gain imbalance computed for each averaging count.

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

            iq_gain_imbalance_per_subcarrier_mean (numpy.float32):
                This parameter returns an array of I/Q gain imbalance for each subcarrier. This value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_iq_gain_imbalance_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, iq_gain_imbalance_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_iq_impairments(self, selector_string, timeout):
        r"""Fetches the I/Q Impairment results for the OFDMModAcc measurement.

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
            Tuple (relative_iq_origin_offset_mean, iq_gain_imbalance_mean, iq_quadrature_error_mean, absolute_iq_origin_offset_mean, iq_timing_skew_mean, error_code):

            relative_iq_origin_offset_mean (float):
                This parameter returns the relative I/Q origin offset, which is the ratio of the power of the DC subcarrier to the
                total power of all the subcarriers. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
                returns the mean of the relative I/Q origin offset computed for each averaging count. This value is expressed in dB.

            iq_gain_imbalance_mean (float):
                This parameter returns the I/Q gain imbalance, which is the ratio of the RMS amplitude of the in-phase (I) component of
                the signal to the RMS amplitude of the quadrature-phase (Q) component of the signal. When you set the OFDMModAcc
                Averaging Enabled attribute to **True**, this attribute returns the mean of the I/Q gain imbalance computed for each
                averaging count. This value is expressed in dB.

            iq_quadrature_error_mean (float):
                This parameter returns the I/Q quadrature error, which is a measure of deviation of the phase difference between the
                quadrature-phase (Q) and the in-phase (I) component of the signal from 90 degrees. When you set the OFDMModAcc
                Averaging Enabled attribute to **True**, this attribute returns the I/Q quadrature error computed for each averaging
                count. This value is expressed in degrees.

            absolute_iq_origin_offset_mean (float):
                This parameter returns the absolute I/Q origin offset, which is the power of the DC subcarrier. When you set the
                OFDMModAcc Averaging Enabled attribute to **True**, this attribute returns the mean of the absolute I/Q origin offset
                computed for each averaging count. This value is expressed in dBm.

            iq_timing_skew_mean (float):
                This parameter returns the I/Q timing skew, which is the difference between the group delay of the in-phase (I) and
                quadrature (Q) components of the signal. When you set the OFDMModAcc Averaging Enabled attribute to **True**, this
                attribute returns the mean of the I/Q timing skew computed for each averaging count. This value is expressed in
                seconds.

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
                relative_iq_origin_offset_mean,
                iq_gain_imbalance_mean,
                iq_quadrature_error_mean,
                absolute_iq_origin_offset_mean,
                iq_timing_skew_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_iq_impairments(updated_selector_string, timeout)
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            relative_iq_origin_offset_mean,
            iq_gain_imbalance_mean,
            iq_quadrature_error_mean,
            absolute_iq_origin_offset_mean,
            iq_timing_skew_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_iq_quadrature_error_per_subcarrier_mean_trace(
        self, selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
    ):
        r"""Fetches the I/Q quadrature error per subcarrier trace. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the I/Q quadrature error computed for each averaging count.

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

            iq_quadrature_error_per_subcarrier_mean (numpy.float32):
                This parameter returns an array of I/Q quadrature errors for each subcarrier. This value is expressed in degrees.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_iq_quadrature_error_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, iq_quadrature_error_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_l_sig_parity_check_status(self, selector_string, timeout):
        r"""Fetches the L-SIG parity check status.

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
            Tuple (l_sig_parity_check_status, error_code):

            l_sig_parity_check_status (enums.OfdmModAccLSigParityCheckStatus):
                This parameter returns whether the parity check has passed either for the SIGNAL field of the 802.11a/g waveform or for
                the L-SIG field of the 802.11n/802.11ac/802.11ax/802.11be/802.11bn waveforms.

                +---------------------+--------------------------------------------------------------------+
                | Name (Value)        | Description                                                        |
                +=====================+====================================================================+
                | Not Applicable (-1) | Returns that the parity check is invalid for the current waveform. |
                +---------------------+--------------------------------------------------------------------+
                | Fail (0)            | Returns that the parity check failed.                              |
                +---------------------+--------------------------------------------------------------------+
                | Pass (1)            | Returns that the parity check passed.                              |
                +---------------------+--------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            l_sig_parity_check_status, error_code = (
                self._interpreter.ofdmmodacc_fetch_l_sig_parity_check_status(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return l_sig_parity_check_status, error_code

    @_raise_if_disposed
    def fetch_mcs_index(self, selector_string, timeout):
        r"""Fetches the MCS index.

        Use "user<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and user number.

                Example:

                "user0"

                "result::r1/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (mcs_index, error_code):

            mcs_index (int):
                This parameter returns the MCS index or the data rate. The MCS index or data rate for various standard signals are
                decoded as follows:

                +----------------------------------------+----------------------------------------------------+
                | Standard                               | Field                                              |
                +========================================+====================================================+
                | 802.11a, 802.11j, 802.11p              | The data rate is decoded from the SIGNAL field.    |
                +----------------------------------------+----------------------------------------------------+
                | 802.11n                                | The MCS index is decoded from the HT-SIG field.    |
                +----------------------------------------+----------------------------------------------------+
                | 802.11ac                               | The MCS index is decoded from the VHT-SIG-A field. |
                +----------------------------------------+----------------------------------------------------+
                | 802.11ax SU and Extended Range SU PPDU | The MCS index is decoded from the HE-SIG-A field.  |
                +----------------------------------------+----------------------------------------------------+
                | 802.11ax MU PPDU                       | The MCS index is decoded from the HE-SIG-B field.  |
                +----------------------------------------+----------------------------------------------------+
                | 802.11be MU PPDU                       | The MCS index is decoded from the EHT-SIG field.   |
                +----------------------------------------+----------------------------------------------------+
                | 802.11bn MU PPDU                       | The MCS index is decoded from the UHR-SIG field.   |
                +----------------------------------------+----------------------------------------------------+
                | 802.11bn ELR PPDU                      | The MCS index is decoded from the ELR-SIG field.   |
                +----------------------------------------+----------------------------------------------------+

                For 802.11a, 802.11j, and 802.11p signals, the following MCS indices corresponds to their data rates:

                +-----+----------------------------------------------------------------------------------------------------+
                | MCS | Data Rate                                                                                          |
                +=====+====================================================================================================+
                | 0   | 1.5 Mbps, 3 Mbps, and 6 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.    |
                +-----+----------------------------------------------------------------------------------------------------+
                | 1   | 2.25 Mbps, 4.5 Mbps, and 9 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively. |
                +-----+----------------------------------------------------------------------------------------------------+
                | 2   | 3 Mbps, 6 Mbps, and 12 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.     |
                +-----+----------------------------------------------------------------------------------------------------+
                | 3   | 4.5 Mbps, 9 Mbps, and 18 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.   |
                +-----+----------------------------------------------------------------------------------------------------+
                | 4   | 6 Mbps, 12 Mbps, and 24 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.    |
                +-----+----------------------------------------------------------------------------------------------------+
                | 5   | 9 Mbps, 18 Mbps, and 36 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.    |
                +-----+----------------------------------------------------------------------------------------------------+
                | 6   | 12 Mbps, 24 Mbps, and 48 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively.   |
                +-----+----------------------------------------------------------------------------------------------------+
                | 7   | 13.5 Mbps, 27 Mbps, and 54 Mbps for channel bandwidths of 5 MHz, 10 MHz, and 20 MHz, respectively. |
                +-----+----------------------------------------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            mcs_index, error_code = self._interpreter.ofdmmodacc_fetch_mcs_index(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return mcs_index, error_code

    @_raise_if_disposed
    def fetch_number_of_he_sig_b_symbols(self, selector_string, timeout):
        r"""Fetches the number of HE-SIG-B symbols.

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
            Tuple (number_of_he_sig_b_symbols, error_code):

            number_of_he_sig_b_symbols (int):
                This parameter returns the number of HE-SIG-B symbols. This result is applicable for 802.11ax MU PPDU signals, and is
                decoded from the HE-SIG-A field.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            number_of_he_sig_b_symbols, error_code = (
                self._interpreter.ofdmmodacc_fetch_number_of_he_sig_b_symbols(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return number_of_he_sig_b_symbols, error_code

    @_raise_if_disposed
    def fetch_number_of_space_time_streams(self, selector_string, timeout):
        r"""Fetches the number of space time streams.

        Use "user<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and user number.

                Example:

                "user0"

                "result::r1/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (number_of_space_time_streams, error_code):

            number_of_space_time_streams (int):
                This parameter returns the number of space time streams.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            number_of_space_time_streams, error_code = (
                self._interpreter.ofdmmodacc_fetch_number_of_space_time_streams(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return number_of_space_time_streams, error_code

    @_raise_if_disposed
    def fetch_number_of_symbols_used(self, selector_string, timeout):
        r"""Fetches the number of OFDM symbols used for EVM measurement.

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
            Tuple (number_of_symbols_used, error_code):

            number_of_symbols_used (int):
                This parameter returns the number of OFDM symbols used by the measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            number_of_symbols_used, error_code = (
                self._interpreter.ofdmmodacc_fetch_number_of_symbols_used(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return number_of_symbols_used, error_code

    @_raise_if_disposed
    def fetch_number_of_users(self, selector_string, timeout):
        r"""Fetches the number of users.

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
            Tuple (number_of_users, error_code):

            number_of_users (int):
                This parameter returns the number of users which is derived for the following standards.

                +----------+---------------------------------------------+
                | Standard | Derivation                                  |
                +==========+=============================================+
                | 802.11ac | Derived from the VHT-SIG-A for VHT MU PPDU. |
                +----------+---------------------------------------------+
                | 802.11ax | Derived from the HE-SIG-B for HE MU PPDU.   |
                +----------+---------------------------------------------+
                | 802.11be | Derived from the EHT-SIG for EHT MU PPDU.   |
                +----------+---------------------------------------------+
                | 802.11bn | Derived from the UHR-SIG for UHR MU PPDU.   |
                +----------+---------------------------------------------+

                For all other PPDUs, this attribute returns 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            number_of_users, error_code = self._interpreter.ofdmmodacc_fetch_number_of_users(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return number_of_users, error_code

    @_raise_if_disposed
    def fetch_pe_average_power(self, selector_string, timeout):
        r"""Fetches the average power of the packet extension field.

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
            Tuple (pe_average_power_mean, error_code):

            pe_average_power_mean (float):
                This parameter returns the average power of the packet extension field. This parameter is applicable for 802.11ax
                signals. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
                **True**, this parameter returns the mean of the packet extension field average power results computed for each
                averaging count. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pe_average_power_mean, error_code = self._interpreter.ofdmmodacc_fetch_pe_average_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pe_average_power_mean, error_code

    @_raise_if_disposed
    def fetch_pe_peak_power(self, selector_string, timeout):
        r"""Fetches the peak power of the packet extension field.

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
            Tuple (pe_peak_power_maximum, error_code):

            pe_peak_power_maximum (float):
                This parameter returns the peak power of the packet extension field. This parameter is applicable for 802.11ax signals.
                When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this
                parameter returns the maximum of the PE field peak power results computed for each averaging count. This value is
                expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pe_peak_power_maximum, error_code = self._interpreter.ofdmmodacc_fetch_pe_peak_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pe_peak_power_maximum, error_code

    @_raise_if_disposed
    def fetch_pilot_constellation_trace(self, selector_string, timeout, pilot_constellation):
        r"""Fetches the constellation trace for the pilot-subcarriers.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            pilot_constellation (numpy.complex64):
                This parameter returns the demodulated QAM symbols from all the pilot-subcarriers in all OFDM symbols.

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
            error_code = self._interpreter.ofdmmodacc_fetch_pilot_constellation_trace(
                updated_selector_string, timeout, pilot_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_ppdu_average_power(self, selector_string, timeout):
        r"""Fetches the average power of the PPDU.

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
            Tuple (ppdu_average_power_mean, error_code):

            ppdu_average_power_mean (float):
                This parameter returns the average power of the PPDU. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the PPDU average power results computed for each averaging count. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            ppdu_average_power_mean, error_code = (
                self._interpreter.ofdmmodacc_fetch_ppdu_average_power(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return ppdu_average_power_mean, error_code

    @_raise_if_disposed
    def fetch_ppdu_peak_power(self, selector_string, timeout):
        r"""Fetches the peak power of the PPDU.

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
            Tuple (ppdu_peak_power_maximum, error_code):

            ppdu_peak_power_maximum (float):
                This parameter returns the peak power of the PPDU. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the maximum of the PPDU peak power results computed for each averaging count. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            ppdu_peak_power_maximum, error_code = (
                self._interpreter.ofdmmodacc_fetch_ppdu_peak_power(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return ppdu_peak_power_maximum, error_code

    @_raise_if_disposed
    def fetch_ppdu_type(self, selector_string, timeout):
        r"""Fetches the PPDU type.

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
            Tuple (ppdu_type, error_code):

            ppdu_type (enums.OfdmPpduType):
                This parameter returns the PPDU type.

                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value)          | Description                                                                                                              |
                +=======================+==========================================================================================================================+
                | Non-HT (0)            | Applicable to 802.11a, 802.11j, and 802.11p signals or for 802.11n, 802.11ac, and 802.11ax signals that operate in the   |
                |                       | Non-HT mode.                                                                                                             |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Mixed (1)             | Applicable to 802.11n mixed PPDU signals.                                                                                |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Greenfield (2)        | Applicable to 802.11n greenfield PPDU signals.                                                                           |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | SU (3)                | Applicable to 802.11ac and 802.11ax SU PPDU signals.                                                                     |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | MU (4)                | Applicable to 802.11ax, 802.11be, and 802.11bn MU PPDU signals.                                                          |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Extended Range SU (5) | Applicable to 802.11ax extended range SU PPDU signals.                                                                   |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | Trigger-based (6)     | Applicable to 802.11ax, 802.11be, and 802.11bn TB PPDU signals.                                                          |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
                | ELR (7)               | Applicable to 802.11bn ELR PPDU signals.                                                                                 |
                +-----------------------+--------------------------------------------------------------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            ppdu_type, error_code = self._interpreter.ofdmmodacc_fetch_ppdu_type(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return ppdu_type, error_code

    @_raise_if_disposed
    def fetch_preamble_average_powers_802_11ac(self, selector_string, timeout):
        r"""Fetches the average power of the 802.11ac specific preamble fields.

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
            Tuple (vht_sig_a_average_power_mean, vht_stf_average_power_mean, vht_ltf_average_power_mean, vht_sig_b_average_power_mean, error_code):

            vht_sig_a_average_power_mean (float):
                This parameter returns the average power of the VHT-SIG-A field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the VHT-SIG-A field average power results computed for each averaging count. This value is
                expressed in dBm.

            vht_stf_average_power_mean (float):
                This parameter returns the average power of the VHT-STF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this paramter returns the mean of the VHT-STF average power results computed for each averaging count.
                This value is expressed in dBm.

            vht_ltf_average_power_mean (float):
                This parameter returns the average power of the VHT-LTF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this paramter returns the mean of the VHT-LTF average power results computed for each averaging count.
                This value is expressed in dBm.

            vht_sig_b_average_power_mean (float):
                This parameter returns the average power of the VHT-SIG-B field. When you set the OFDMModAcc Averaging Enabled
                attribute to **True**, this parameter returns the mean of the VHT-SIG-B field average power results computed for each
                averaging count. This value is expressed in dBm.

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
                vht_sig_a_average_power_mean,
                vht_stf_average_power_mean,
                vht_ltf_average_power_mean,
                vht_sig_b_average_power_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_average_powers_802_11ac(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            vht_sig_a_average_power_mean,
            vht_stf_average_power_mean,
            vht_ltf_average_power_mean,
            vht_sig_b_average_power_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_average_powers_802_11ax(self, selector_string, timeout):
        r"""Fetches the average power of the 802.11ax specific preamble fields.

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
            Tuple (rl_sig_average_power_mean, he_sig_a_average_power_mean, he_sig_b_average_power_mean, he_stf_average_power_mean, he_ltf_average_power_mean, error_code):

            rl_sig_average_power_mean (float):
                This parameter returns the average power of the RL-SIG field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the RL-SIG field average power results computed for each averaging count. This value is expressed
                in dBm.

            he_sig_a_average_power_mean (float):
                This parameter returns the average power of the HE-SIG-A field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the HE-SIG-A field average power results computed for each averaging
                count. This value is expressed in dBm.

            he_sig_b_average_power_mean (float):
                This parameter returns the average power of the HE-SIG-B field. When you set the OFDMModAcc Averaging Enabled
                attribute to **True**, this parameter returns the mean of the HE-SIG-B field average power results computed for each
                averaging count. This value is expressed in dBm.

            he_stf_average_power_mean (float):
                This parameter returns the average power of the HE-STF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the HE-STF average power results computed for each averaging count.
                This value is expressed in dBm.

            he_ltf_average_power_mean (float):
                This parameter returns the average power of the HE-LTF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the HE-LTF average power results computed for each averaging count.
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
                rl_sig_average_power_mean,
                he_sig_a_average_power_mean,
                he_sig_b_average_power_mean,
                he_stf_average_power_mean,
                he_ltf_average_power_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_average_powers_802_11ax(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            rl_sig_average_power_mean,
            he_sig_a_average_power_mean,
            he_sig_b_average_power_mean,
            he_stf_average_power_mean,
            he_ltf_average_power_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_average_powers_802_11be(self, selector_string, timeout):
        r"""Fetches the average power of the 802.11be specific preamble fields.

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
            Tuple (rl_sig_average_power_mean, u_sig_average_power_mean, eht_sig_average_power_mean, eht_stf_average_power_mean, eht_ltf_average_power_mean, error_code):

            rl_sig_average_power_mean (float):
                This parameter returns the average power of the RL-SIG field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the RL-SIG field average power results computed for each averaging count. This value is expressed
                in dBm.

            u_sig_average_power_mean (float):
                This parameter returns the average power of the U-SIG field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this paramter returns the mean of the U-SIG average power results computed for each averaging count. This
                value is expressed in dBm.

            eht_sig_average_power_mean (float):
                This parameter returns the average power of the EHT-SIG field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the EHT-SIG average power results computed for each averaging count.
                This value is expressed in dBm.

            eht_stf_average_power_mean (float):
                This parameter returns the average power of the EHT-STF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the EHT-STF average power results computed for each averaging count.
                This value is expressed in dBm.

            eht_ltf_average_power_mean (float):
                This parameter returns the average power of the EHT-LTF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the EHT-LTF average power results computed for each averaging count.
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
                rl_sig_average_power_mean,
                u_sig_average_power_mean,
                eht_sig_average_power_mean,
                eht_stf_average_power_mean,
                eht_ltf_average_power_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_average_powers_802_11be(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            rl_sig_average_power_mean,
            u_sig_average_power_mean,
            eht_sig_average_power_mean,
            eht_stf_average_power_mean,
            eht_ltf_average_power_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_average_powers_802_11n(self, selector_string, timeout):
        r"""Fetches the average power of the 802.11n specific preamble fields.

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
            Tuple (ht_sig_average_power_mean, ht_stf_average_power_mean, ht_dltf_average_power_mean, ht_eltf_average_power_mean, error_code):

            ht_sig_average_power_mean (float):
                This parameter returns the average power of the HT-SIG field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the HT-SIG field average power results computed for each averaging
                count. This value is expressed in dBm.

            ht_stf_average_power_mean (float):
                This parameter returns the average power of the HT-STF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the HT-STF average power results computed for each averaging count.
                This value is expressed in dBm.

            ht_dltf_average_power_mean (float):
                This parameter returns the average power of the HT-DLTF. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the mean of the HT-DLTF average power results computed for each averaging count. This
                value is expressed in dBm.

            ht_eltf_average_power_mean (float):
                This parameter returns the average power of the HT-ELTF field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the mean of the HT-ELTF average power results computed for each averaging count.
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
                ht_sig_average_power_mean,
                ht_stf_average_power_mean,
                ht_dltf_average_power_mean,
                ht_eltf_average_power_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_average_powers_802_11n(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            ht_sig_average_power_mean,
            ht_stf_average_power_mean,
            ht_dltf_average_power_mean,
            ht_eltf_average_power_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_average_powers_common(self, selector_string, timeout):
        r"""Fetches the average power of the preamble fields.

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
            Tuple (l_stf_average_power_mean, l_ltf_average_power_mean, l_sig_average_power_mean, error_code):

            l_stf_average_power_mean (float):
                This parameter returns the average power of the L-STF or STF field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the L-STF or STF average power results computed for each averaging count. This value is expressed
                in dBm.

            l_ltf_average_power_mean (float):
                This parameter returns the average power of the L-LTF or LTF field. When you set the OFDMModAcc Averaging Enabled
                attribute to **True**, this parameter returns the mean of the L-LTF or LTF average power results computed for each
                averaging count. This value is expressed in dBm.

            l_sig_average_power_mean (float):
                This parameter returns the average power of the L-SIG or SIGNAL field. When you set the OFDMModAcc Averaging Enabled
                attribute to **True**, this parameter returns the mean of the L-SIG or SIGNAL field average power results computed for
                each averaging count. This value is expressed in dBm.

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
                l_stf_average_power_mean,
                l_ltf_average_power_mean,
                l_sig_average_power_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_average_powers_common(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            l_stf_average_power_mean,
            l_ltf_average_power_mean,
            l_sig_average_power_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_frequency_error_trace(
        self, selector_string, timeout, preamble_frequency_error
    ):
        r"""Fetches the preamble frequency error trace for signals containing an OFDM payload. Preamble frequency error computes
        the variations, across time, of the frequency error over initial 16us which comprises of the short training field (STF)
        and long training field (LTF) symbols.

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

            preamble_frequency_error (numpy.float32):
                This parameter returns the preamble frequency error at every sampling time. This value is expressed in Hz.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start time in seconds.

            dx (float):
                This parameter returns the time increment value. This value is the reciprocal of OFDM ModAcc processing rate.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.ofdmmodacc_fetch_preamble_frequency_error_trace(
                updated_selector_string, timeout, preamble_frequency_error
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_preamble_peak_powers_802_11ac(self, selector_string, timeout):
        r"""Fetches the peak power of the 802.11ac specific preamble fields.

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
            Tuple (vht_sig_a_peak_power_maximum, vht_stf_peak_power_maximum, vht_ltf_peak_power_maximum, vht_sig_b_peak_power_maximum, error_code):

            vht_sig_a_peak_power_maximum (float):
                This parameter returns the peak power of the VHT-SIG-A field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
                returns the maximum of the VHT-SIG-A field peak power results computed for each averaging count. This value is
                expressed in dBm.

            vht_stf_peak_power_maximum (float):
                This parameter returns the peak power of the VHT-STF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the VHT-STF peak power results computed for each averaging count. This
                value is expressed in dBm.

            vht_ltf_peak_power_maximum (float):
                This parameter returns the peak power of the VHT-LTF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the VHT-LTF peak power results computed for each averaging count. This
                value is expressed in dBm.

            vht_sig_b_peak_power_maximum (float):
                This parameter returns the peak power of the VHT-SIG-B field. When you set the OFDMModAcc Averaging Enabled attribute
                to **True**, this parameter returns the maximum of the VHT-SIG-B field peak power results computed for each averaging
                count. This value is expressed in dBm.

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
                vht_sig_a_peak_power_maximum,
                vht_stf_peak_power_maximum,
                vht_ltf_peak_power_maximum,
                vht_sig_b_peak_power_maximum,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_peak_powers_802_11ac(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            vht_sig_a_peak_power_maximum,
            vht_stf_peak_power_maximum,
            vht_ltf_peak_power_maximum,
            vht_sig_b_peak_power_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_peak_powers_802_11ax(self, selector_string, timeout):
        r"""Fetches the peak power of the 802.11ax specific preamble fields.

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
            Tuple (rl_sig_peak_power_maximum, he_sig_a_peak_power_maximum, he_sig_b_peak_power_maximum, he_stf_peak_power_maximum, he_ltf_peak_power_maximum, error_code):

            rl_sig_peak_power_maximum (float):
                This parameter returns the peak power of the RL-SIG field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the maximum of the RL-SIG field peak power results computed for each averaging count. This value is expressed
                in dBm.

            he_sig_a_peak_power_maximum (float):
                This parameter returns the peak power of the HE-SIG-A field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HE-SIG-A field peak power results computed for each averaging
                count. This value is expressed in dBm.

            he_sig_b_peak_power_maximum (float):
                This parameter returns the peak power of the HE-SIG-B field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HE-SIG-B field peak power results computed for each averaging
                count. This value is expressed in dBm.

            he_stf_peak_power_maximum (float):
                This parameter returns the peak power of the HE-STF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HE-STF peak power results computed for each averaging count. This
                value is expressed in dBm.

            he_ltf_peak_power_maximum (float):
                This parameter returns the peak power of the HE-LTF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HE-LTF peak power results computed for each averaging count. This
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
                rl_sig_peak_power_maximum,
                he_sig_a_peak_power_maximum,
                he_sig_b_peak_power_maximum,
                he_stf_peak_power_maximum,
                he_ltf_peak_power_maximum,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_peak_powers_802_11ax(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            rl_sig_peak_power_maximum,
            he_sig_a_peak_power_maximum,
            he_sig_b_peak_power_maximum,
            he_stf_peak_power_maximum,
            he_ltf_peak_power_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_peak_powers_802_11be(self, selector_string, timeout):
        r"""Fetches the peak power of the 802.11be specific preamble fields.

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
            Tuple (rl_sig_peak_power_maximum, u_sig_peak_power_maximum, eht_sig_peak_power_maximum, eht_stf_peak_power_maximum, eht_ltf_peak_power_maximum, error_code):

            rl_sig_peak_power_maximum (float):
                This parameter returns the peak power of the RL-SIG field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the maximum of the RL-SIG field peak power results computed for each averaging count. This value is expressed
                in dBm.

            u_sig_peak_power_maximum (float):
                This parameter returns the peak power of the U-SIG field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the U-SIG peak power results computed for each averaging count. This
                value is expressed in dBm.

            eht_sig_peak_power_maximum (float):
                This parameter returns the peak power of the EHT-SIG field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the EHT-SIG peak power results computed for each averaging count. This
                value is expressed in dBm.

            eht_stf_peak_power_maximum (float):
                This parameter returns the peak power of the EHT-STF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the EHT-STF peak power results computed for each averaging count. This
                value is expressed in dBm.

            eht_ltf_peak_power_maximum (float):
                This parameter returns the peak power of the EHT-LTF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the EHT-LTF peak power results computed for each averaging count. This
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
                rl_sig_peak_power_maximum,
                u_sig_peak_power_maximum,
                eht_sig_peak_power_maximum,
                eht_stf_peak_power_maximum,
                eht_ltf_peak_power_maximum,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_peak_powers_802_11be(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            rl_sig_peak_power_maximum,
            u_sig_peak_power_maximum,
            eht_sig_peak_power_maximum,
            eht_stf_peak_power_maximum,
            eht_ltf_peak_power_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_peak_powers_802_11n(self, selector_string, timeout):
        r"""Fetches the peak power of the 802.11n specific preamble fields.

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
            Tuple (ht_sig_peak_power_maximum, ht_stf_peak_power_maximum, ht_dltf_peak_power_maximum, ht_eltf_peak_power_maximum, error_code):

            ht_sig_peak_power_maximum (float):
                This parameter returns the peak power of the HT-SIG field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the maximum of the HT-SIG field peak power results computed for each averaging count. This value is expressed
                in dBm.

            ht_stf_peak_power_maximum (float):
                This parameter returns the peak power of the HT-STF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HT-STF peak power results computed for each averaging count. This
                value is expressed in dBm.

            ht_dltf_peak_power_maximum (float):
                This parameter returns the peak power of the HT-DLTF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HT-DLTF peak power results computed for each averaging count. This
                value is expressed in dBm.

            ht_eltf_peak_power_maximum (float):
                This parameter returns the peak power of the HT-ELTF field. When you set the OFDMModAcc Averaging Enabled attribute to
                **True**, this parameter returns the maximum of the HT-ELTF peak power results computed for each averaging count. This
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
                ht_sig_peak_power_maximum,
                ht_stf_peak_power_maximum,
                ht_dltf_peak_power_maximum,
                ht_eltf_peak_power_maximum,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_peak_powers_802_11n(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            ht_sig_peak_power_maximum,
            ht_stf_peak_power_maximum,
            ht_dltf_peak_power_maximum,
            ht_eltf_peak_power_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_preamble_peak_powers_common(self, selector_string, timeout):
        r"""Fetches the peak power of the preamble fields.

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
            Tuple (l_stf_peak_power_maximum, l_ltf_peak_power_maximum, l_sig_peak_power_maximum, error_code):

            l_stf_peak_power_maximum (float):
                This parameter returns the peak power of the L-STF or STF field. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the maximum of the L-STF or STF peak power results computed for each averaging count. This value is expressed
                in dBm.

            l_ltf_peak_power_maximum (float):
                This parameter returns the peak power of the L-LTF or LTF field. When you set the OFDMModAcc Averaging Enabled
                attribute to **True**, this parameter returns the maximum of the L-LTF or LTF peak power results computed for each
                averaging count. This value is expressed in dBm.

            l_sig_peak_power_maximum (float):
                This parameter returns the peak power of the L-SIG or SIGNAL field. When you set the OFDMModAcc Averaging Enabled
                attribute to **True**, this parameter returns the maximum of the L-SIG or SIGNAL field peak power results computed for
                each averaging count. This value is expressed in dBm.

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
                l_stf_peak_power_maximum,
                l_ltf_peak_power_maximum,
                l_sig_peak_power_maximum,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_preamble_peak_powers_common(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            l_stf_peak_power_maximum,
            l_ltf_peak_power_maximum,
            l_sig_peak_power_maximum,
            error_code,
        )

    @_raise_if_disposed
    def fetch_psdu_crc_status(self, selector_string, timeout):
        r"""Fetches the PLCP service data unit (PSDU) CRC status.

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
            Tuple (psdu_crc_status, error_code):

            psdu_crc_status (enums.OfdmModAccPsduCrcStatus):
                This parameter returns the PSDU CRC status.

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
            psdu_crc_status, error_code = self._interpreter.ofdmmodacc_fetch_psdu_crc_status(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return psdu_crc_status, error_code

    @_raise_if_disposed
    def fetch_pe_duration(self, selector_string, timeout):
        r"""Fetches the duration of the packet extension field.

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
            Tuple (pe_duration, error_code):

            pe_duration (float):
                This parameter returns the duration of the packet extension field for the 802.11ax and 802.11be signals. This parameter
                is applicable only when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED`
                attribute to **True**. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            pe_duration, error_code = self._interpreter.ofdmmodacc_fetch_pe_duration(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return pe_duration, error_code

    @_raise_if_disposed
    def fetch_ru_offset_and_size(self, selector_string, timeout):
        r"""Fetches the RU offset and the RU size of the specified user.

        Use "user<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and user number.

                Example:

                "user0"

                "result::r1/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (ru_offset, ru_size, error_code):

            ru_offset (int):
                This parameter returns the location of RU for the specified user in terms of the index of a 26-tone RU, assuming the
                entire bandwidth is composed of 26-tone RUs.

            ru_size (int):
                This parameter returns the RU size for the specified user.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            ru_offset, ru_size, error_code = self._interpreter.ofdmmodacc_fetch_ru_offset_and_size(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return ru_offset, ru_size, error_code

    @_raise_if_disposed
    def fetch_sig_crc_status(self, selector_string, timeout):
        r"""Fetches the SIG CRC Status.

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
            Tuple (sig_crc_status, error_code):

            sig_crc_status (enums.OfdmModAccSigCrcStatus):
                This parameter returns whether the cyclic redundancy check (CRC) has passed either for the HT-SIG field of the 802.11n
                waveform, for the VHT-SIG-A field of the 802.11ac waveform, or for the HE-SIG-A field of the 802.11ax waveform.

                +---------------------+---------------------------------------------------------------+
                | Name (Value)        | Description                                                   |
                +=====================+===============================================================+
                | Not Applicable (-1) | Returns that the SIG CRC is invalid for the current waveform. |
                +---------------------+---------------------------------------------------------------+
                | Fail (0)            | Returns that the SIG CRC failed.                              |
                +---------------------+---------------------------------------------------------------+
                | Pass (1)            | Returns that the SIG CRC passed.                              |
                +---------------------+---------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            sig_crc_status, error_code = self._interpreter.ofdmmodacc_fetch_sig_crc_status(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return sig_crc_status, error_code

    @_raise_if_disposed
    def fetch_sig_b_crc_status(self, selector_string, timeout):
        r"""Fetches the SIG-B CRC Status.

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
            Tuple (sig_b_crc_status, error_code):

            sig_b_crc_status (enums.OfdmModAccSigBCrcStatus):
                This parameter returns whether the cyclic redundancy check (CRC) has passed for the HE-SIG-B field of the 802.11ax MU
                PPDU waveform.

                +---------------------+------------------------------------------------------------------+
                | Name (Value)        | Description                                                      |
                +=====================+==================================================================+
                | Not Applicable (-1) | Returns that the SIG-B CRC                                       |
                |                     | is invalid for the current waveform.                             |
                +---------------------+------------------------------------------------------------------+
                | Fail (0)            | Returns that the SIG-B CRC failed.                               |
                +---------------------+------------------------------------------------------------------+
                | Pass (1)            | Returns that the SIG-B CRC passed.                               |
                +---------------------+------------------------------------------------------------------+

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            sig_b_crc_status, error_code = self._interpreter.ofdmmodacc_fetch_sig_b_crc_status(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return sig_b_crc_status, error_code

    @_raise_if_disposed
    def fetch_spectral_flatness_mean_trace(
        self,
        selector_string,
        timeout,
        spectral_flatness_mean,
        spectral_flatness_lower_mask,
        spectral_flatness_upper_mask,
    ):
        r"""Fetches the spectral flatness trace, and the lower and upper spectral flatness mask traces. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the spectral flatness trace computed on the mean of the channel estimates computed for each averaging count.

        Use "segment<*n*>/chain<*k*>/stream<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and stream number.

                Example:

                "segment0/chain0/stream0"

                "result::r1/segment0/chain0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            spectral_flatness_mean (numpy.float32):
                This parameter returns an array of spectral flatness for each subcarrier. This value is expressed in dB.

            spectral_flatness_lower_mask (numpy.float32):
                This parameter returns an array of spectral flatness for each subcarrier. This value is expressed in dB.

            spectral_flatness_upper_mask (numpy.float32):
                This parameter returns an array of spectral flatness for each subcarrier. This value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.ofdmmodacc_fetch_spectral_flatness_mean_trace(
                updated_selector_string,
                timeout,
                spectral_flatness_mean,
                spectral_flatness_lower_mask,
                spectral_flatness_upper_mask,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_spectral_flatness(self, selector_string, timeout):
        r"""Fetches the spectral flatness margin results.

        Use "segment<*n*>/chain<*k*>/stream<*l*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, chain number, and stream number.

                Example:

                "segment0/chain0/stream0"

                "result::r1/segment0/chain0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (spectral_flatness_margin, spectral_flatness_margin_subcarrier_index, error_code):

            spectral_flatness_margin (float):
                This parameter returns the spectral flatness margin, which is the minimum of the upper and lower spectral flatness
                margins. The upper spectral flatness margin is the minimum difference between the upper mask and the spectral flatness
                across subcarriers. The lower spectral flatness margin is the minimum difference between the spectral flatness and the
                lower mask across subcarriers. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, the spectral flatness
                is computed using the mean of the channel frequency response magnitude computed for each averaging count. This value is
                expressed in dB.

            spectral_flatness_margin_subcarrier_index (int):
                This parameter returns the subcarrier index corresponding to the **Spectral Flatness Margin** parameter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            spectral_flatness_margin, spectral_flatness_margin_subcarrier_index, error_code = (
                self._interpreter.ofdmmodacc_fetch_spectral_flatness(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return spectral_flatness_margin, spectral_flatness_margin_subcarrier_index, error_code

    @_raise_if_disposed
    def fetch_stream_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_data_rms_evm_per_symbol_mean
    ):
        r"""Fetches the stream data subcarriers RMS EVM per symbol trace.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            stream_data_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns the stream data subcarriers RMS EVM of each OFDM symbol. This value is expressed as a percentage
                or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_stream_data_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, stream_data_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_stream_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_pilot_rms_evm_per_symbol_mean
    ):
        r"""Fetches the stream pilot subcarriers RMS EVM per symbol trace.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            stream_pilot_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns the stream pilot subcarriers RMS EVM of each OFDM symbol. This value is expressed as a
                percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_stream_pilot_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, stream_pilot_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_stream_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, stream_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the stream RMS EVM per subcarrier trace.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            stream_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns the stream RMS EVM for each subcarrier. This value is expressed as a percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_stream_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, stream_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_stream_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, stream_rms_evm_per_symbol_mean
    ):
        r"""Fetches the stream RMS EVM per symbol trace.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            stream_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns the stream RMS EVM of each OFDM symbol. This value is expressed as a percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_stream_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, stream_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_stream_rms_evm(self, selector_string, timeout):
        r"""Fetches the stream RMS EVM results.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (stream_rms_evm_mean, stream_data_rms_evm_mean, stream_pilot_rms_evm_mean, error_code):

            stream_rms_evm_mean (float):
                This parameter returns the stream RMS EVM of all subcarriers in all OFDM symbols. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of stream RMS EVM results computed for each averaging count. This value is expressed as a percentage
                or in dB.

            stream_data_rms_evm_mean (float):
                This parameter returns the stream RMS EVM of data subcarriers in all OFDM symbols. When you set the OFDMModAcc
                Averaging Enabled attribute to **True**, this parameter returns the mean of data stream RMS EVM results computed for
                each averaging count. This value is expressed as a percentage or in dB.

            stream_pilot_rms_evm_mean (float):
                This parameter returns the stream RMS EVM of pilot subcarriers in all OFDM symbols. When you set the OFDMModAcc
                Averaging Enabled attribute to **True**, this parameter returns the mean of pilot stream RMS EVM results computed for
                each averaging count. This value is expressed as a percentage or in dB.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            stream_rms_evm_mean, stream_data_rms_evm_mean, stream_pilot_rms_evm_mean, error_code = (
                self._interpreter.ofdmmodacc_fetch_stream_rms_evm(updated_selector_string, timeout)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return stream_rms_evm_mean, stream_data_rms_evm_mean, stream_pilot_rms_evm_mean, error_code

    @_raise_if_disposed
    def fetch_subcarrier_chain_evm_per_symbol_trace(
        self, selector_string, timeout, subcarrier_index, subcarrier_chain_evm_per_symbol
    ):
        r"""Fetches the chain EVM per symbol trace for a subcarrier. For unoccupied subcarriers, the trace value is NaN.

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

            subcarrier_index (int):
                This parameter specifies the subcarrier index for which the trace is fetched. The default value is 0.

            subcarrier_chain_evm_per_symbol (numpy.float32):
                This parameter returns an array of chain EVM of each OFDM symbol for the specified subcarrier index. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_subcarrier_chain_evm_per_symbol_trace(
                    updated_selector_string,
                    timeout,
                    subcarrier_index,
                    subcarrier_chain_evm_per_symbol,
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_subcarrier_stream_evm_per_symbol_trace(
        self, selector_string, timeout, subcarrier_index, subcarrier_stream_evm_per_symbol
    ):
        r"""Fetches the stream EVM per symbol trace for a subcarrier.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            subcarrier_index (int):
                This parameter specifies the subcarrier index for which to fetch the trace. The default value is 0.

            subcarrier_stream_evm_per_symbol (numpy.float32):
                This parameter returns the stream EVM of each OFDM symbol for the specified subcarrier index. This value is expressed
                as a percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_subcarrier_stream_evm_per_symbol_trace(
                    updated_selector_string,
                    timeout,
                    subcarrier_index,
                    subcarrier_stream_evm_per_symbol,
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_symbol_chain_evm_per_subcarrier_trace(
        self, selector_string, timeout, symbol_index, symbol_chain_evm_per_subcarrier
    ):
        r"""Fetches the chain EVM per subcarrier trace for a symbol. For symbol indices outside the measurement interval, the trace
        value is NaN.

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

            symbol_index (int):
                This parameter specifies the symbol index for which to fetch the trace. The default value is 0.

            symbol_chain_evm_per_subcarrier (numpy.float32):
                This parameter returns an array of chain EVM for each subcarrier for the specified symbol index. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_symbol_chain_evm_per_subcarrier_trace(
                    updated_selector_string, timeout, symbol_index, symbol_chain_evm_per_subcarrier
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_symbol_clock_error_mean(self, selector_string, timeout):
        r"""Fetches the symbol clock error of the transmitter.

        Use "segment<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and segment number.

                Example:

                "segment0"

                "result::r1/segment0"

                You can use the :py:meth:`build_segment_string` method  to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (symbol_clock_error_mean, error_code):

            symbol_clock_error_mean (float):
                This parameter returns the symbol clock error of the transmitter. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this parameter
                returns the mean of the symbol clock error results computed for each averaging count. This value is expressed in parts
                per million (ppm).

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            symbol_clock_error_mean, error_code = (
                self._interpreter.ofdmmodacc_fetch_symbol_clock_error_mean(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return symbol_clock_error_mean, error_code

    @_raise_if_disposed
    def fetch_symbol_stream_evm_per_subcarrier_trace(
        self, selector_string, timeout, symbol_index, symbol_stream_evm_per_subcarrier
    ):
        r"""Fetches the stream EVM per subcarrier trace for a symbol.

        Use "segment<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, segment number, and stream number.

                Example:

                "segment0/stream0"

                "result::r1/segment0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            symbol_index (int):
                This parameter specifies the symbol index for which to fetch the trace. The default value is 0.

            symbol_stream_evm_per_subcarrier (numpy.float32):
                This parameter returns the stream EVM for each subcarrier for the specified symbol index. This value is expressed as a
                percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_symbol_stream_evm_per_subcarrier_trace(
                    updated_selector_string, timeout, symbol_index, symbol_stream_evm_per_subcarrier
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_unused_tone_error_margin_per_ru(
        self, selector_string, timeout, unused_tone_error_margin_per_ru
    ):
        r"""Fetches the unused tone error margin result per RU.

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

            unused_tone_error_margin_per_ru (numpy.float64):
                This parameter returns an array of unused tone error margin per RU, which is the difference between the unused tone
                error mask and the unused tone error for each RU. This value is expressed in dB.

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
            error_code = self._interpreter.ofdmmodacc_fetch_unused_tone_error_margin_per_ru(
                updated_selector_string, timeout, unused_tone_error_margin_per_ru
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_unused_tone_error_mean_trace(
        self, selector_string, timeout, unused_tone_error, unused_tone_error_mask
    ):
        r"""Fetches the unused tone error trace and the unused tone error mask trace.  When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the unused tone error computed for each averaging count.

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

            unused_tone_error (numpy.float32):
                This parameter returns an array of unused tone error for each RU. This value is expressed in dB.

            unused_tone_error_mask (numpy.float32):
                This parameter returns an array of unused tone error for each RU. This value is expressed in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting RU index. This value is always 0.

            dx (float):
                This parameter returns the RU increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = self._interpreter.ofdmmodacc_fetch_unused_tone_error_mean_trace(
                updated_selector_string, timeout, unused_tone_error, unused_tone_error_mask
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_unused_tone_error(self, selector_string, timeout):
        r"""Fetches the unused tone error margin results.

        Refer to `Unused Tone Error Mx <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/unused-tone-error-mx.html>`_ for
        more information.

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
            Tuple (unused_tone_error_margin, unused_tone_error_margin_ru_index, error_code):

            unused_tone_error_margin (float):
                This parameter returns the unused tone error margin, which is the minimum difference between the unused tone error mask
                and the unused tone error across 26-tone RUs. This value is expressed in dB.

            unused_tone_error_margin_ru_index (int):
                This parameter returns the 26-tone RU index corresponding to the **Unused Tone Error Margin** parameter.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            unused_tone_error_margin, unused_tone_error_margin_ru_index, error_code = (
                self._interpreter.ofdmmodacc_fetch_unused_tone_error(
                    updated_selector_string, timeout
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return unused_tone_error_margin, unused_tone_error_margin_ru_index, error_code

    @_raise_if_disposed
    def fetch_user_data_constellation_trace(
        self, selector_string, timeout, user_data_constellation
    ):
        r"""Fetches the constellation trace for the data-subcarriers of each user.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            user_data_constellation (numpy.complex64):
                This parameter returns the demodulated QAM symbols from all the data-subcarriers in all of the OFDM symbols for each
                user.

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
            error_code = self._interpreter.ofdmmodacc_fetch_user_data_constellation_trace(
                updated_selector_string, timeout, user_data_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_user_pilot_constellation_trace(
        self, selector_string, timeout, user_pilot_constellation
    ):
        r"""Fetches the constellation trace for the pilot-subcarriers of each user.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            user_pilot_constellation (numpy.complex64):
                This parameter returns the demodulated QAM symbols from all the pilot-subcarriers in all of the OFDM symbols for each
                user.

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
            error_code = self._interpreter.ofdmmodacc_fetch_user_pilot_constellation_trace(
                updated_selector_string, timeout, user_pilot_constellation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def fetch_user_power(self, selector_string, timeout):
        r"""Fetches the user power.

        Use "user<*n*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and user number.

                Example:

                "user0"

                "result::r1/user0"

                You can use the :py:meth:`build_user_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (user_power_mean, error_code):

            user_power_mean (float):
                This parameter returns the user power. User power is the frequency domain power measured over subcarriers occupied by a
                given user. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
                **True**, this parameter returns the mean of the user power results computed for each averaging count. This value is
                expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            user_power_mean, error_code = self._interpreter.ofdmmodacc_fetch_user_power(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return user_power_mean, error_code

    @_raise_if_disposed
    def fetch_user_stream_data_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_data_rms_evm_per_symbol_mean
    ):
        r"""Fetches the stream data-subcarriers RMS EVM per symbol trace for each user. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the user stream data RMS EVM per symbol computed for each averaging count.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            user_stream_data_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns the stream data subcarriers RMS EVM of each OFDM symbol for each user. This value is expressed
                as a percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_user_stream_data_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, user_stream_data_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_user_stream_pilot_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_pilot_rms_evm_per_symbol_mean
    ):
        r"""Fetches the stream pilot-subcarriers RMS EVM per symbol trace for each user.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            user_stream_pilot_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns the stream pilot subcarriers RMS EVM of each OFDM symbol for each user. This value is expressed
                as a percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_user_stream_pilot_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, user_stream_pilot_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_user_stream_rms_evm_per_subcarrier_mean_trace(
        self, selector_string, timeout, user_stream_rms_evm_per_subcarrier_mean
    ):
        r"""Fetches the stream RMS EVM per subcarrier trace for each user. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the user stream RMS EVM per subcarrier computed for each averaging count.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            user_stream_rms_evm_per_subcarrier_mean (numpy.float32):
                This parameter returns the user stream RMS EVM for each  subcarrier. This value is expressed as a percentage or in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting subcarrier index.

            dx (float):
                This parameter returns the subcarrier increment value. This value is always 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_user_stream_rms_evm_per_subcarrier_mean_trace(
                    updated_selector_string, timeout, user_stream_rms_evm_per_subcarrier_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_user_stream_rms_evm_per_symbol_mean_trace(
        self, selector_string, timeout, user_stream_rms_evm_per_symbol_mean
    ):
        r"""Fetches the stream RMS EVM per symbol trace for each user. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the user stream RMS EVM per symbol computed for each averaging count.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            user_stream_rms_evm_per_symbol_mean (numpy.float32):
                This parameter returns the stream RMS EVM of each OFDM symbol for each user. This value is expressed as a percentage or
                in dB.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the starting OFDM symbol index corresponding to the value of
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_MEASUREMENT_OFFSET` attribute.

            dx (float):
                This parameter returns the OFDM symbol increment value. This value is always equal to 1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self._signal_obj
            )
            x0, dx, error_code = (
                self._interpreter.ofdmmodacc_fetch_user_stream_rms_evm_per_symbol_mean_trace(
                    updated_selector_string, timeout, user_stream_rms_evm_per_symbol_mean
                )
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code

    @_raise_if_disposed
    def fetch_user_stream_rms_evm(self, selector_string, timeout):
        r"""Fetches the stream RMS EVM results for the specified user.

        Use "user<*n*>/stream<*k*>" as the selector string to read results from this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, user number, and stream number.

                Example:

                "user0/stream0"

                "result::r1/user0/stream0"

                You can use the :py:meth:`build_stream_string` method to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            Tuple (user_stream_rms_evm_mean, user_stream_data_rms_evm_mean, user_stream_pilot_rms_evm_mean, error_code):

            user_stream_rms_evm_mean (float):
                This parameter returns the RMS EVM of all subcarriers in all OFDM symbols for the specified user. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
                **True**, this parameter returns the mean of the user stream RMS EVM computed for each averaging count.

            user_stream_data_rms_evm_mean (float):
                This parameter returns the RMS EVM of data-subcarriers in all OFDM symbols for the specified user. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. When you set the OFDMModAcc Averaging Enabled attribute to **True**, this parameter returns the mean of
                the user stream data RMS EVM computed for each averaging count.

            user_stream_pilot_rms_evm_mean (float):
                This parameter returns the RMS EVM of pilot-subcarriers in all OFDM symbols for the specified user. When you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_EVM_UNIT` attribute to **Percentage**, the measurement returns
                this result as a percentage. When you set the OFDMModAcc EVM Unit attribute to **dB**, the measurement returns this
                result in dB. When you set the OFDMModAcc Averaging Enabled attribute to **True**, this parameter returns the mean of
                the user stream pilot RMS EVM computed for each averaging count.

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
                user_stream_rms_evm_mean,
                user_stream_data_rms_evm_mean,
                user_stream_pilot_rms_evm_mean,
                error_code,
            ) = self._interpreter.ofdmmodacc_fetch_user_stream_rms_evm(
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return (
            user_stream_rms_evm_mean,
            user_stream_data_rms_evm_mean,
            user_stream_pilot_rms_evm_mean,
            error_code,
        )

    @_raise_if_disposed
    def fetch_phase_noise_psd_mean_trace(self, selector_string, timeout, phase_noise_psd_mean):
        r"""Fetches the phase noise power spectral density (PSD) trace for signals containing an OFDM payload.

        Phase noise estimates are derived from the common pilot error estimates. When you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this method returns
        the mean of the phase noise PSD computed for each averaging count.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name, and segment number.

                Example:

                "segment0"

                "result::r1/segment0"

                You can use the :py:meth:`build_segment_string` method  to build the selector string.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

            phase_noise_psd_mean (numpy.float32):
                This parameter returns an array of the mean of phase noise PSD. This value is expressed in dBc/Hz.

        Returns:
            Tuple (x0, dx, error_code):

            x0 (float):
                This parameter returns the start frequency of the phase noise PSD mean trace. This value is expressed in Hz.

            dx (float):
                This parameter returns the frequency intervals between data points in the phase noise PSD mean trace. This value is
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
            x0, dx, error_code = self._interpreter.ofdmmodacc_fetch_phase_noise_psd_mean_trace(
                updated_selector_string, timeout, phase_noise_psd_mean
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return x0, dx, error_code
