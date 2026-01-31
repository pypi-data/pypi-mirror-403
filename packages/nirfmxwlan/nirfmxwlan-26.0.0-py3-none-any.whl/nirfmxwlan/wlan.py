"""Defines a root class which is used to identify and control Wlan signal configuration."""

import functools
import math

import nirfmxinstr
import nirfmxwlan.attributes as attributes
import nirfmxwlan.dsssmodacc as dsssmodacc
import nirfmxwlan.enums as enums
import nirfmxwlan.errors as errors
import nirfmxwlan.internal._helper as _helper
import nirfmxwlan.ofdmmodacc as ofdmmodacc
import nirfmxwlan.powerramp as powerramp
import nirfmxwlan.sem as sem
import nirfmxwlan.txp as txp
from nirfmxwlan.internal._helper import SignalConfiguration
from nirfmxwlan.internal._library_interpreter import LibraryInterpreter


class _WlanSignalConfiguration:
    """Contains static methods to create and delete Wlan signal."""

    @staticmethod
    def get_wlan_signal_configuration(instr_session, signal_name="", cloning=False):
        updated_signal_name = signal_name
        if signal_name:
            updated_signal_name = _helper.validate_and_remove_signal_qualifier(
                signal_name, "signal_name"
            )
            _helper.validate_signal_not_empty(updated_signal_name, "signal_name")
        return _WlanSignalConfiguration.init(instr_session, updated_signal_name, cloning)  # type: ignore

    @staticmethod
    def init(instr_session, signal_name, cloning):
        with instr_session._signal_lock:
            if signal_name.lower() == Wlan._default_signal_name_user_visible.lower():
                signal_name = Wlan._default_signal_name

            existing_signal = instr_session._signal_manager.find_signal_configuration(
                Wlan._signal_configuration_type, signal_name
            )
            if existing_signal is None:
                signal_configuration = Wlan(instr_session, signal_name, cloning)  # type: ignore
                instr_session._signal_manager.add_signal_configuration(signal_configuration)
            else:
                signal_configuration = existing_signal
                # Checking if signal exists in C layer
                if signal_configuration._interpreter.check_if_current_signal_exists() is False:
                    if not signal_configuration.signal_configuration_name.lower():
                        instr_session._interpreter.create_default_signal_configuration(
                            Wlan._default_signal_name_user_visible,
                            int(math.log(nirfmxinstr.Personalities.WLAN.value, 2.0)) + 1,
                        )
                    else:
                        signal_configuration._interpreter.create_signal_configuration(signal_name)

            return signal_configuration

    @staticmethod
    def remove_signal_configuration(instr_session, signal_configuration):
        with instr_session._signal_lock:
            instr_session._signal_manager.remove_signal_configuration(signal_configuration)


def _raise_if_disposed(f):
    """From https://stackoverflow.com/questions/5929107/decorators-with-parameters."""

    @functools.wraps(f)
    def aux(*xs, **kws):
        signal = xs[0]  # parameter 0 is 'self' which is the signal object
        if signal.is_disposed:
            raise Exception("Cannot access a disposed Wlan signal configuration")
        return f(*xs, **kws)

    return aux


class _WlanBase(SignalConfiguration):
    """Defines a base class for Wlan."""

    _default_signal_name = ""
    _default_signal_name_user_visible = "default@WLAN"
    _signal_configuration_type = "<'nirfmxwlan.wlan.Wlan'>"

    def __init__(self, session, signal_name="", cloning=False):
        self.is_disposed = False
        self._rfmxinstrsession = session
        self._rfmxinstrsession_interpreter = session._interpreter
        self.signal_configuration_name = signal_name
        self.signal_configuration_type = type(self)  # type: ignore
        self._signal_configuration_mode = "Signal"
        if session._is_remote_session:
            import nirfmxwlan.internal._grpc_stub_interpreter as _grpc_stub_interpreter

            interpreter = _grpc_stub_interpreter.GrpcStubInterpreter(session._grpc_options, session, self)  # type: ignore
        else:
            interpreter = LibraryInterpreter("windows-1251", session, self)  # type: ignore

        self._interpreter = interpreter
        self._interpreter.set_session_handle(self._rfmxinstrsession_interpreter._vi)  # type: ignore
        self._session_function_lock = _helper.SessionFunctionLock()

        # Measurements object
        self.txp = txp.Txp(self)  # type: ignore
        self.dsssmodacc = dsssmodacc.DsssModAcc(self)  # type: ignore
        self.powerramp = powerramp.PowerRamp(self)  # type: ignore
        self.ofdmmodacc = ofdmmodacc.OfdmModAcc(self)  # type: ignore
        self.sem = sem.Sem(self)  # type: ignore

        if not signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(
                    self._default_signal_name_user_visible
                )
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.WLAN.value):
                self._rfmxinstrsession_interpreter.create_default_signal_configuration(
                    self._default_signal_name_user_visible,
                    int(math.log(nirfmxinstr.Personalities.WLAN.value, 2.0)) + 1,
                )
        elif signal_name and not cloning:
            signal_exists, personality, _ = (
                self._rfmxinstrsession_interpreter.check_if_signal_exists(signal_name)
            )
            if not (signal_exists and personality.value == nirfmxinstr.Personalities.WLAN.value):
                self._interpreter.create_signal_configuration(signal_name)  # type: ignore

    def __enter__(self):
        """Enters the context of the Wlan signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the Wlan signal configuration."""
        self.dispose()  # type: ignore
        pass

    def dispose(self):
        r"""Deletes the signal configuration if it is not the default signal configuration
        and clears any trace of the current signal configuration, if any.

        .. note::
            You can call this function safely more than once, even if the signal is already deleted.
        """
        if not self.is_disposed:
            if self.signal_configuration_name == self._default_signal_name:
                self.is_disposed = True
                return
            else:
                _ = self._delete_signal_configuration(True)  # type: ignore
                self.is_disposed = True

    @_raise_if_disposed
    def delete_signal_configuration(self):
        r"""Deletes the current instance of a signal.

        Returns:
            error_code:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        error_code = self._delete_signal_configuration(False)  # type: ignore
        return error_code

    def _delete_signal_configuration(self, ignore_driver_error):
        error_code = 0
        try:
            if not self.is_disposed:
                self._session_function_lock.enter_write_lock()
                error_code = self._interpreter.delete_signal_configuration(ignore_driver_error)  # type: ignore
                _WlanSignalConfiguration.remove_signal_configuration(self._rfmxinstrsession, self)  # type: ignore
                self.is_disposed = True
        finally:
            self._session_function_lock.exit_write_lock()

        return error_code

    @_raise_if_disposed
    def get_warning(self):
        r"""Retrieves and then clears the warning information for the session.

        Returns:
            Tuple (warning_code, warning_message):

            warning_code (int):
                Contains the latest warning code.

            warning_message (string):
                Contains the latest warning description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            warning_code, warning_message = self._interpreter.get_error()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return warning_code, warning_message

    @_raise_if_disposed
    def get_error_string(self, error_code):
        r"""Gets the description of a driver error code.

        Args:
            error_code (int):
                Specifies an error or warning code.

        Returns:
            string:
                Contains the error description.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_message = self._interpreter.get_error_string(error_code)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_message

    @_raise_if_disposed
    def reset_attribute(self, selector_string, attribute_id):
        r"""Resets the attribute to its default value.

        Args:
            selector_string (string):
                Specifies the selector string for the property being reset.

            attribute_id (PropertyId):
                Specifies an attribute identifier.

        Returns:
            int:
                Returns the status code of this method.
                The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attribute_id = (
                attribute_id.value if type(attribute_id) is attributes.AttributeID else attribute_id
            )
            error_code = self._interpreter.reset_attribute(  # type: ignore
                updated_selector_string, attribute_id
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_selected_ports(self, selector_string):
        r"""Gets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        On a MIMO session, this attribute specifies one of the initialized devices. Use
        "port::<deviceName>/<channelNumber>" as the format for the selected port. To perform a MIMO measurement, you must
        configure the selected ports attribute for the configured number of segments and chains.

        For PXIe-5830/5831/5832 devices on a MIMO session, the selected port includes the instrument port in the format
        "port::<deviceName>/<channelNumber>/<instrPort>".

        Example:

        port::myrfsa1/0/if1

        You can use the :py:meth:`build_port_string` method to build the selected port.

        Use "segment<m>/chain<n>" as the selector string to configure or read this attribute. You can use the
        :py:meth:`build_chain_string` method to build the selector string.

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_selected_ports(self, selector_string, value):
        r"""Sets the instrument port to be configured to acquire a signal. Use
        :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        On a MIMO session, this attribute specifies one of the initialized devices. Use
        "port::<deviceName>/<channelNumber>" as the format for the selected port. To perform a MIMO measurement, you must
        configure the selected ports attribute for the configured number of segments and chains.

        For PXIe-5830/5831/5832 devices on a MIMO session, the selected port includes the instrument port in the format
        "port::<deviceName>/<channelNumber>/<instrPort>".

        Example:

        port::myrfsa1/0/if1

        You can use the :py:meth:`build_port_string` method to build the selected port.

        Use "segment<m>/chain<n>" as the selector string to configure or read this attribute. You can use the
        :py:meth:`build_chain_string` method to build the selector string.

        **Default values**

        +---------------------+-------------------+
        | Name (value)        | Description       |
        +=====================+===================+
        | PXIe-5830/5831/5832 | if1               |
        +---------------------+-------------------+
        | Other devices       | "" (empty string) |
        +---------------------+-------------------+

        **Valid values**

        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (value)   | Description                                                                                                              |
        +================+==========================================================================================================================+
        | PXIe-5830      | if0, if1                                                                                                                 |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | PXIe-5831/5832 | if0, if1, rf<0-1>/port<x>, where 0-1 indicates one (0) or two (1) mmRH-5582 connections and x is the port number on the  |
        |                | mmRH-5582 front panel                                                                                                    |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+
        | Other devices  | "" (empty string)                                                                                                        |
        +----------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the instrument port to be configured to acquire a signal. Use
                :py:meth:`nirfmxinstr.session.Session.get_available_ports` method to get the valid port names.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.SELECTED_PORTS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_center_frequency(self, selector_string):
        r"""Gets the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
        signal analyzer tunes to this frequency.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use "segment<*n*>" along with a named or default signal instance as the selector string to configure
        or read this attribute. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
                signal analyzer tunes to this frequency.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_center_frequency(self, selector_string, value):
        r"""Sets the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
        signal analyzer tunes to this frequency.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use "segment<*n*>" along with a named or default signal instance as the selector string to configure
        or read this attribute. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
                signal analyzer tunes to this frequency.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CENTER_FREQUENCY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level(self, selector_string):
        r"""Gets the reference level which represents the maximum expected power of the RF input signal. This value is
        expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
                expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level(self, selector_string, value):
        r"""Sets the reference level which represents the maximum expected power of the RF input signal. This value is
        expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
                expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_external_attenuation(self, selector_string):
        r"""Gets the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
        device in the *NI RF Vector Signal Analyzers Help*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
                device in the *NI RF Vector Signal Analyzers Help*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_external_attenuation(self, selector_string, value):
        r"""Sets the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
        expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
        device in the *NI RF Vector Signal Analyzers Help*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
        port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
        syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
                expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
                device in the *NI RF Vector Signal Analyzers Help*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.EXTERNAL_ATTENUATION.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_reference_level_headroom(self, selector_string):
        r"""Gets the margin RFmx adds to the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
        margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
                margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_reference_level_headroom(self, selector_string, value):
        r"""Sets the margin RFmx adds to the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
        margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        RFmx configures the input gain to avoid clipping and associated overflow warnings provided the instantaneous
        power of the input signal remains within the Reference Level plus the Reference Level Headroom. If you know the input
        power of the signal precisely or previously included the margin in the Reference Level, you could improve the
        signal-to-noise ratio by reducing the Reference Level Headroom.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        **Supported devices: **PXIe-5668, PXIe-5830/5831/5832/5840/5841/5842/5860.

        **Default values**

        +------------------------------------+-------------+
        | Name (value)                       | Description |
        +====================================+=============+
        | PXIe-5668                          | 6 dB        |
        +------------------------------------+-------------+
        | PXIe-5830/5831/5832/5841/5842/5860 | 1 dB        |
        +------------------------------------+-------------+
        | PXIe-5840                          | 0 dB        |
        +------------------------------------+-------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the margin RFmx adds to the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
                margin avoids clipping and overflow warnings if the input signal exceeds the configured reference level.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.REFERENCE_LEVEL_HEADROOM.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_type(self, selector_string):
        r"""Gets the trigger type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **IQ Power Edge**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No reference trigger is configured.                                                                                      |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | The reference trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
        |                   | using the Digital Edge Source attribute.                                                                                 |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | The reference trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
        |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | The reference trigger is not asserted until a software trigger occurs.                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerType):
                Specifies the trigger type.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value
            )
            attr_val = enums.TriggerType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_type(self, selector_string, value):
        r"""Sets the trigger type.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **IQ Power Edge**.

        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)      | Description                                                                                                              |
        +===================+==========================================================================================================================+
        | None (0)          | No reference trigger is configured.                                                                                      |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Digital Edge (1)  | The reference trigger is not asserted until a digital edge is detected. The source of the digital edge is specified      |
        |                   | using the Digital Edge Source attribute.                                                                                 |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | IQ Power Edge (2) | The reference trigger is asserted when the signal changes past the level specified by the slope (rising or falling),     |
        |                   | which is configured using the IQ Power Edge Slope attribute.                                                             |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Software (3)      | The reference trigger is not asserted until a software trigger occurs.                                                   |
        +-------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerType, int):
                Specifies the trigger type.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_source(self, selector_string):
        r"""Gets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        On a MIMO session, this attribute configures the digital edge trigger on the master port. By default, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
        considered as the master port.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_source(self, selector_string, value):
        r"""Sets the source terminal for the digital edge trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        On a MIMO session, this attribute configures the digital edge trigger on the master port. By default, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
        considered as the master port.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_digital_edge_trigger_edge(self, selector_string):
        r"""Gets the active edge for the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.DigitalEdgeTriggerEdge):
                Specifies the active edge for the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value
            )
            attr_val = enums.DigitalEdgeTriggerEdge(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_digital_edge_trigger_edge(self, selector_string, value):
        r"""Sets the active edge for the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Edge**.

        +------------------+--------------------------------------------------------+
        | Name (Value)     | Description                                            |
        +==================+========================================================+
        | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
        +------------------+--------------------------------------------------------+
        | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
        +------------------+--------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.DigitalEdgeTriggerEdge, int):
                Specifies the active edge for the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.DigitalEdgeTriggerEdge else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.DIGITAL_EDGE_TRIGGER_EDGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_source(self, selector_string):
        r"""Gets the channel from which the device monitors the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        On a MIMO session, this attribute configures the IQ Power edge trigger on the master port. By default, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
        considered as the master port.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (string):
                Specifies the channel from which the device monitors the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_string(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_source(self, selector_string, value):
        r"""Sets the channel from which the device monitors the trigger. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        On a MIMO session, this attribute configures the IQ Power edge trigger on the master port. By default, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
        considered as the master port.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (string):
                Specifies the channel from which the device monitors the trigger. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            _helper.validate_not_none(value, "value")
            error_code = self._interpreter.set_attribute_string(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SOURCE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level(self, selector_string):
        r"""Gets the power level at which the device triggers. This value is expressed in dB when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm
        when you set the IQ Power Edge Level Type attribute to **Absolute**.

        The device asserts the trigger when the signal exceeds the level specified by the value of this attribute,
        taking into consideration the specified slope. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the power level at which the device triggers. This value is expressed in dB when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm
                when you set the IQ Power Edge Level Type attribute to **Absolute**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level(self, selector_string, value):
        r"""Sets the power level at which the device triggers. This value is expressed in dB when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm
        when you set the IQ Power Edge Level Type attribute to **Absolute**.

        The device asserts the trigger when the signal exceeds the level specified by the value of this attribute,
        taking into consideration the specified slope. This attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the power level at which the device triggers. This value is expressed in dB when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm
                when you set the IQ Power Edge Level Type attribute to **Absolute**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_level_type(self, selector_string):
        r"""Gets the reference for the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute.
        The IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerLevelType):
                Specifies the reference for the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute.
                The IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
            )
            attr_val = enums.IQPowerEdgeTriggerLevelType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_level_type(self, selector_string, value):
        r"""Sets the reference for the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute.
        The IQ Power Edge Level Type attribute is used only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Relative**.

        +--------------+----------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                  |
        +==============+==============================================================================================+
        | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
        +--------------+----------------------------------------------------------------------------------------------+
        | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
        +--------------+----------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerLevelType, int):
                Specifies the reference for the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute.
                The IQ Power Edge Level Type attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerLevelType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_iq_power_edge_trigger_slope(self, selector_string):
        r"""Gets whether the device asserts the trigger when the signal power is rising or falling.

        The device asserts the trigger when the signal power exceeds the specified level with the slope you specify.
        This attribute is used only when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE`  attribute to
        **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.IQPowerEdgeTriggerSlope):
                Specifies whether the device asserts the trigger when the signal power is rising or falling.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value
            )
            attr_val = enums.IQPowerEdgeTriggerSlope(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_iq_power_edge_trigger_slope(self, selector_string, value):
        r"""Sets whether the device asserts the trigger when the signal power is rising or falling.

        The device asserts the trigger when the signal power exceeds the specified level with the slope you specify.
        This attribute is used only when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE`  attribute to
        **IQ Power Edge**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Rising Slope**.

        +-------------------+-------------------------------------------------------+
        | Name (Value)      | Description                                           |
        +===================+=======================================================+
        | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
        +-------------------+-------------------------------------------------------+
        | Falling Slope (1) | The trigger asserts when the signal power is falling. |
        +-------------------+-------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.IQPowerEdgeTriggerSlope, int):
                Specifies whether the device asserts the trigger when the signal power is rising or falling.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.IQPowerEdgeTriggerSlope else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_delay(self, selector_string):
        r"""Gets the trigger delay time. This value is expressed in seconds.

        If the delay is negative, the measurement acquires pre-trigger samples. If the delay is positive, the
        measurement acquires post-trigger samples.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is RFmxWLAN measurement dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the trigger delay time. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_delay(self, selector_string, value):
        r"""Sets the trigger delay time. This value is expressed in seconds.

        If the delay is negative, the measurement acquires pre-trigger samples. If the delay is positive, the
        measurement acquires post-trigger samples.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is RFmxWLAN measurement dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the trigger delay time. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_DELAY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_mode(self, selector_string):
        r"""Gets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                          |
        +==============+======================================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time Duration attribute. |
        +--------------+------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                                 |
        +--------------+------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerMinimumQuietTimeMode):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
            )
            attr_val = enums.TriggerMinimumQuietTimeMode(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_mode(self, selector_string, value):
        r"""Sets whether the measurement computes the minimum quiet time used for triggering.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Auto**.

        +--------------+------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                          |
        +==============+======================================================================================================+
        | Manual (0)   | The minimum quiet time for triggering is the value of the Trigger Min Quiet Time Duration attribute. |
        +--------------+------------------------------------------------------------------------------------------------------+
        | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                                 |
        +--------------+------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerMinimumQuietTimeMode, int):
                Specifies whether the measurement computes the minimum quiet time used for triggering.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerMinimumQuietTimeMode else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_MODE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_minimum_quiet_time_duration(self, selector_string):
        r"""Gets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds.

        If you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising
        Slope**, the signal is quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling
        Slope**, the signal is quiet above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_minimum_quiet_time_duration(self, selector_string, value):
        r"""Sets the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
        trigger. This value is expressed in seconds.

        If you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising
        Slope**, the signal is quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling
        Slope**, the signal is quiet above the trigger level.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value of this attribute is hardware dependent.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
                trigger. This value is expressed in seconds.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.TRIGGER_MINIMUM_QUIET_TIME_DURATION.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_gate_enabled(self, selector_string):
        r"""Enables time-domain gating of the acquired signal for SEM measurement.

        If you set this attribute to **True** and the required measurement interval exceeds the value you set for the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_LENGTH` attribute, then the measurement restricts the
        acquisition duration of each record to Gate Length attribute and acquires as many additional records as necessary for
        the required measurement interval.
        If you want to ignore the idle duration between multiple PPDUs during an SEM measurement, you must set Gate
        Enabled to **True** and set Gate Length to a value less than or equal to the length of the PPDU under analysis. This
        value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | Gate for SEM measurements is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | Gate for SEM measurements is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.TriggerGateEnabled):
                Enables time-domain gating of the acquired signal for SEM measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_GATE_ENABLED.value
            )
            attr_val = enums.TriggerGateEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_gate_enabled(self, selector_string, value):
        r"""Enables time-domain gating of the acquired signal for SEM measurement.

        If you set this attribute to **True** and the required measurement interval exceeds the value you set for the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_LENGTH` attribute, then the measurement restricts the
        acquisition duration of each record to Gate Length attribute and acquires as many additional records as necessary for
        the required measurement interval.
        If you want to ignore the idle duration between multiple PPDUs during an SEM measurement, you must set Gate
        Enabled to **True** and set Gate Length to a value less than or equal to the length of the PPDU under analysis. This
        value is expressed in seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+----------------------------------------+
        | Name (Value) | Description                            |
        +==============+========================================+
        | False (0)    | Gate for SEM measurements is disabled. |
        +--------------+----------------------------------------+
        | True (1)     | Gate for SEM measurements is enabled.  |
        +--------------+----------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.TriggerGateEnabled, int):
                Enables time-domain gating of the acquired signal for SEM measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.TriggerGateEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_GATE_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_trigger_gate_length(self, selector_string):
        r"""Gets the maximum duration of time for each record used for computing the spectrum when you are performing an SEM
        measurement and when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_ENABLED` attribute to
        **True**.

        If the measurement interval required to perform the measurement exceeds the gate length, the measurement
        acquires as many additional records as necessary to honor the required measurement interval. This value is expressed in
        seconds.

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
                Specifies the maximum duration of time for each record used for computing the spectrum when you are performing an SEM
                measurement and when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_ENABLED` attribute to
                **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_GATE_LENGTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_trigger_gate_length(self, selector_string, value):
        r"""Sets the maximum duration of time for each record used for computing the spectrum when you are performing an SEM
        measurement and when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_ENABLED` attribute to
        **True**.

        If the measurement interval required to perform the measurement exceeds the gate length, the measurement
        acquires as many additional records as necessary to honor the required measurement interval. This value is expressed in
        seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1 millisecond.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the maximum duration of time for each record used for computing the spectrum when you are performing an SEM
                measurement and when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_ENABLED` attribute to
                **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.TRIGGER_GATE_LENGTH.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_standard(self, selector_string):
        r"""Gets the signal under analysis as defined in *IEEE Standard 802.11*.

        .. note::
           On a MIMO session, the supported standards are 802.11n, 802.11ac, 802.11ax, 802.11be, and 802.11bn.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **802.11a/g**.

        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                         |
        +===============+=====================================================================================================================+
        | 802.11a/g (0) | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11a-1999 and IEEE Standard 802.11g-2003. |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11b (1)   | Corresponds to the DSSS based PPDU formats as defined in IEEE Standard 802.11b-1999.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11j (2)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11j-2004.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11p (3)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11p-2010.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11n (4)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11n-2009.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11ac (5)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11ac-2013.                               |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11ax (6)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11ax/D8.0.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11be (7)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11be/D7.0.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11bn (8)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11bn/D1.2.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.Standard):
                Specifies the signal under analysis as defined in *IEEE Standard 802.11*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.STANDARD.value
            )
            attr_val = enums.Standard(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_standard(self, selector_string, value):
        r"""Sets the signal under analysis as defined in *IEEE Standard 802.11*.

        .. note::
           On a MIMO session, the supported standards are 802.11n, 802.11ac, 802.11ax, 802.11be, and 802.11bn.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **802.11a/g**.

        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                         |
        +===============+=====================================================================================================================+
        | 802.11a/g (0) | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11a-1999 and IEEE Standard 802.11g-2003. |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11b (1)   | Corresponds to the DSSS based PPDU formats as defined in IEEE Standard 802.11b-1999.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11j (2)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11j-2004.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11p (3)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11p-2010.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11n (4)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11n-2009.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11ac (5)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11ac-2013.                               |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11ax (6)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11ax/D8.0.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11be (7)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11be/D7.0.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11bn (8)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11bn/D1.2.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.Standard, int):
                Specifies the signal under analysis as defined in *IEEE Standard 802.11*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.Standard else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.STANDARD.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_channel_bandwidth(self, selector_string):
        r"""Gets the channel spacing as defined under section 3.1 of *IEEE Standard 802.11-2016 (pp. 130)*. This value is
        specified in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **20M**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the channel spacing as defined under section 3.1 of *IEEE Standard 802.11-2016 (pp. 130)*. This value is
                specified in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_channel_bandwidth(self, selector_string, value):
        r"""Sets the channel spacing as defined under section 3.1 of *IEEE Standard 802.11-2016 (pp. 130)*. This value is
        specified in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **20M**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the channel spacing as defined under section 3.1 of *IEEE Standard 802.11-2016 (pp. 130)*. This value is
                specified in Hz.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.CHANNEL_BANDWIDTH.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_frequency_segments(self, selector_string):
        r"""Gets the number of frequency segments for 802.11ac and 802.11ax signals.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Valid values are 1 and 2.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of frequency segments for 802.11ac and 802.11ax signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_FREQUENCY_SEGMENTS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_frequency_segments(self, selector_string, value):
        r"""Sets the number of frequency segments for 802.11ac and 802.11ax signals.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Valid values are 1 and 2.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of frequency segments for 802.11ac and 802.11ax signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.NUMBER_OF_FREQUENCY_SEGMENTS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_number_of_receive_chains(self, selector_string):
        r"""Gets the number of receive chains for OFDM standards.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        The valid values are as follows.

        +------------------------------+--------------------------+
        | Standard                     | Number of Receive Chains |
        +==============================+==========================+
        | 802.11a/g, 802.11j, 802.11p  | 1                        |
        +------------------------------+--------------------------+
        | 802.11n                      | 1–4                      |
        +------------------------------+--------------------------+
        | 802.11ac, 802.11ax, 802.11be | 1–8                      |
        +------------------------------+--------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of receive chains for OFDM standards.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.NUMBER_OF_RECEIVE_CHAINS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_number_of_receive_chains(self, selector_string, value):
        r"""Sets the number of receive chains for OFDM standards.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        The valid values are as follows.

        +------------------------------+--------------------------+
        | Standard                     | Number of Receive Chains |
        +==============================+==========================+
        | 802.11a/g, 802.11j, 802.11p  | 1                        |
        +------------------------------+--------------------------+
        | 802.11n                      | 1–4                      |
        +------------------------------+--------------------------+
        | 802.11ac, 802.11ax, 802.11be | 1–8                      |
        +------------------------------+--------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of receive chains for OFDM standards.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.NUMBER_OF_RECEIVE_CHAINS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_frequency_segment_index(self, selector_string):
        r"""Gets the frequency segment index to be analyzed in an 80+80 MHz 802.11ax signal. You must set this attribute to
        either of the valid values when you want to analyze one of the two segments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        The valid values are 0 and 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the frequency segment index to be analyzed in an 80+80 MHz 802.11ax signal. You must set this attribute to
                either of the valid values when you want to analyze one of the two segments.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_FREQUENCY_SEGMENT_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_frequency_segment_index(self, selector_string, value):
        r"""Sets the frequency segment index to be analyzed in an 80+80 MHz 802.11ax signal. You must set this attribute to
        either of the valid values when you want to analyze one of the two segments.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        The valid values are 0 and 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the frequency segment index to be analyzed in an 80+80 MHz 802.11ax signal. You must set this attribute to
                either of the valid values when you want to analyze one of the two segments.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_FREQUENCY_SEGMENT_INDEX.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_transmit_power_class(self, selector_string):
        r"""Gets the STA transmit power classification as defined in annexure D.2.2 of *IEEE Standard 802.11-2016*, if you set
        the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to **802.11p**.

        If you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_MASK_TYPE` attribute to **Standard**, the value
        of this attribute computes mask limits for the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **A**.

        +--------------+---------------------------------------+
        | Name (Value) | Description                           |
        +==============+=======================================+
        | A (0)        | Maximum STA Transmit Power is 1 mW.   |
        +--------------+---------------------------------------+
        | B (1)        | Maximum STA Transmit Power is 10 mW.  |
        +--------------+---------------------------------------+
        | C (2)        | Maximum STA Transmit Power is 100 mW. |
        +--------------+---------------------------------------+
        | D (3)        | Maximum STA Transmit Power is 760 mW. |
        +--------------+---------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmTransmitPowerClass):
                Specifies the STA transmit power classification as defined in annexure D.2.2 of *IEEE Standard 802.11-2016*, if you set
                the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to **802.11p**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_TRANSMIT_POWER_CLASS.value
            )
            attr_val = enums.OfdmTransmitPowerClass(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_transmit_power_class(self, selector_string, value):
        r"""Sets the STA transmit power classification as defined in annexure D.2.2 of *IEEE Standard 802.11-2016*, if you set
        the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to **802.11p**.

        If you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_MASK_TYPE` attribute to **Standard**, the value
        of this attribute computes mask limits for the SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **A**.

        +--------------+---------------------------------------+
        | Name (Value) | Description                           |
        +==============+=======================================+
        | A (0)        | Maximum STA Transmit Power is 1 mW.   |
        +--------------+---------------------------------------+
        | B (1)        | Maximum STA Transmit Power is 10 mW.  |
        +--------------+---------------------------------------+
        | C (2)        | Maximum STA Transmit Power is 100 mW. |
        +--------------+---------------------------------------+
        | D (3)        | Maximum STA Transmit Power is 760 mW. |
        +--------------+---------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmTransmitPowerClass, int):
                Specifies the STA transmit power classification as defined in annexure D.2.2 of *IEEE Standard 802.11-2016*, if you set
                the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` attribute to **802.11p**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmTransmitPowerClass else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_TRANSMIT_POWER_CLASS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_frequency_band(self, selector_string):
        r"""Gets the ISM frequency band. The SEM measurement uses this information to select an appropriate mask as defined in
        *IEEE Standard 802.11n - 2009* and *IEEE Standard P802.11be/D7.0*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **2.4 GHz**.

        +--------------+--------------------------------------------------------------+
        | Name (Value) | Description                                                  |
        +==============+==============================================================+
        | 2.4 GHz (0)  | Corresponds to the ISM band ranging from 2.4 GHz to 2.5 GHz. |
        +--------------+--------------------------------------------------------------+
        | 5 GHz (1)    | Corresponds to the 5 GHz band.                               |
        +--------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmFrequencyBand):
                Specifies the ISM frequency band. The SEM measurement uses this information to select an appropriate mask as defined in
                *IEEE Standard 802.11n - 2009* and *IEEE Standard P802.11be/D7.0*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_FREQUENCY_BAND.value
            )
            attr_val = enums.OfdmFrequencyBand(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_frequency_band(self, selector_string, value):
        r"""Sets the ISM frequency band. The SEM measurement uses this information to select an appropriate mask as defined in
        *IEEE Standard 802.11n - 2009* and *IEEE Standard P802.11be/D7.0*.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **2.4 GHz**.

        +--------------+--------------------------------------------------------------+
        | Name (Value) | Description                                                  |
        +==============+==============================================================+
        | 2.4 GHz (0)  | Corresponds to the ISM band ranging from 2.4 GHz to 2.5 GHz. |
        +--------------+--------------------------------------------------------------+
        | 5 GHz (1)    | Corresponds to the 5 GHz band.                               |
        +--------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmFrequencyBand, int):
                Specifies the ISM frequency band. The SEM measurement uses this information to select an appropriate mask as defined in
                *IEEE Standard 802.11n - 2009* and *IEEE Standard P802.11be/D7.0*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmFrequencyBand else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_FREQUENCY_BAND.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_auto_ppdu_type_detection_enabled(self, selector_string):
        r"""Gets whether to enable auto detection of the PPDU type when performing the OFDMModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | Auto detection of the PPDU type is disabled. |
        +--------------+----------------------------------------------+
        | True (1)     | Auto detection of the PPDU type is enabled.  |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmAutoPpduTypeDetectionEnabled):
                Specifies whether to enable auto detection of the PPDU type when performing the OFDMModAcc measurement.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED.value,
            )
            attr_val = enums.OfdmAutoPpduTypeDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_auto_ppdu_type_detection_enabled(self, selector_string, value):
        r"""Sets whether to enable auto detection of the PPDU type when performing the OFDMModAcc measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+----------------------------------------------+
        | Name (Value) | Description                                  |
        +==============+==============================================+
        | False (0)    | Auto detection of the PPDU type is disabled. |
        +--------------+----------------------------------------------+
        | True (1)     | Auto detection of the PPDU type is enabled.  |
        +--------------+----------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmAutoPpduTypeDetectionEnabled, int):
                Specifies whether to enable auto detection of the PPDU type when performing the OFDMModAcc measurement.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmAutoPpduTypeDetectionEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_ppdu_type(self, selector_string):
        r"""Gets the PPDU type when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED`
        attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Non-HT**.

        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)          | Description                                                                                                              |
        +=======================+==========================================================================================================================+
        | Non-HT (0)            | Specifies an 802.11a, 802.11j, or 802.11p PPDU type, or 802.11n, 802.11ac, or 802.11ax PPDU type when operating in the   |
        |                       | Non-HT mode.                                                                                                             |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Mixed (1)             | Specifies the HT-Mixed PPDU (802.11n) type.                                                                              |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Greenfield (2)        | Specifies the HT-Greenfield PPDU (802.11n) type.                                                                         |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | SU (3)                | Specifies the VHT SU PPDU type if you set the Standard attribute to 802.11ac or the HE SU PPDU type if you set the       |
        |                       | Standard attribute to 802.11ax.                                                                                          |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | MU (4)                | Specifies the VHT MU PPDU type if you set the Standard attribute to 802.11ac, the HE MU PPDU type if you set the         |
        |                       | Standard attribute to 802.11ax, or the EHT MU PPDU type if you set the Standard attribute to 802.11be.                   |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Extended Range SU (5) | Specifies the HE Extended Range SU PPDU (802.11ax) type.                                                                 |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Trigger-based (6)     | Specifies the HE TB PPDU if you set the Standard attribute to 802.11ax , the EHT TB PPDU if you set the Standard         |
        |                       | attribute to 802.11be or the UHR TB PPDU if you set the Standard attribute to 802.11bn .                                 |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | ELR (7)               |                                                                                                                          |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmPpduType):
                Specifies the PPDU type when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED`
                attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_PPDU_TYPE.value
            )
            attr_val = enums.OfdmPpduType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_ppdu_type(self, selector_string, value):
        r"""Sets the PPDU type when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED`
        attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **Non-HT**.

        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)          | Description                                                                                                              |
        +=======================+==========================================================================================================================+
        | Non-HT (0)            | Specifies an 802.11a, 802.11j, or 802.11p PPDU type, or 802.11n, 802.11ac, or 802.11ax PPDU type when operating in the   |
        |                       | Non-HT mode.                                                                                                             |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Mixed (1)             | Specifies the HT-Mixed PPDU (802.11n) type.                                                                              |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Greenfield (2)        | Specifies the HT-Greenfield PPDU (802.11n) type.                                                                         |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | SU (3)                | Specifies the VHT SU PPDU type if you set the Standard attribute to 802.11ac or the HE SU PPDU type if you set the       |
        |                       | Standard attribute to 802.11ax.                                                                                          |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | MU (4)                | Specifies the VHT MU PPDU type if you set the Standard attribute to 802.11ac, the HE MU PPDU type if you set the         |
        |                       | Standard attribute to 802.11ax, or the EHT MU PPDU type if you set the Standard attribute to 802.11be.                   |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Extended Range SU (5) | Specifies the HE Extended Range SU PPDU (802.11ax) type.                                                                 |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Trigger-based (6)     | Specifies the HE TB PPDU if you set the Standard attribute to 802.11ax , the EHT TB PPDU if you set the Standard         |
        |                       | attribute to 802.11be or the UHR TB PPDU if you set the Standard attribute to 802.11bn .                                 |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+
        | ELR (7)               |                                                                                                                          |
        +-----------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmPpduType, int):
                Specifies the PPDU type when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED`
                attribute to **False**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmPpduType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_PPDU_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_header_decoding_enabled(self, selector_string):
        r"""Gets whether to enable the decoding of the header fields in the PPDU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Header information is not read from the header fields in the PPDU. You must configure the following properties:          |
        |              | OFDM Num Users                                                                                                           |
        |              | OFDM MCS Index                                                                                                           |
        |              | OFDM RU Size                                                                                                             |
        |              | OFDM RU Offset/MRU Index                                                                                                 |
        |              | OFDM Guard Interval Type                                                                                                 |
        |              | OFDM LTF Size                                                                                                            |
        |              | OFDM Space Time Stream Offset                                                                                            |
        |              | OFDM Num HE-SIG-B Symbols                                                                                                |
        |              | OFDM PE Disambiguity                                                                                                     |
        |              | OFDM SIG Compression Enabled                                                                                             |
        |              | OFDM Num SIG Symbols                                                                                                     |
        |              | OFDM RU Type                                                                                                             |
        |              | OFDM DBW (Hz)                                                                                                            |
        |              | OFDM IM Pilots Enabled                                                                                                   |
        |              | OFDM Unequal Modulation Enabled                                                                                          |
        |              | OFDM Unequal Modulation Pattern Index                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Header information is obtained by decoding the header fields in the PPDU.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmHeaderDecodingEnabled):
                Specifies whether to enable the decoding of the header fields in the PPDU.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED.value
            )
            attr_val = enums.OfdmHeaderDecodingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_header_decoding_enabled(self, selector_string, value):
        r"""Sets whether to enable the decoding of the header fields in the PPDU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value) | Description                                                                                                              |
        +==============+==========================================================================================================================+
        | False (0)    | Header information is not read from the header fields in the PPDU. You must configure the following properties:          |
        |              | OFDM Num Users                                                                                                           |
        |              | OFDM MCS Index                                                                                                           |
        |              | OFDM RU Size                                                                                                             |
        |              | OFDM RU Offset/MRU Index                                                                                                 |
        |              | OFDM Guard Interval Type                                                                                                 |
        |              | OFDM LTF Size                                                                                                            |
        |              | OFDM Space Time Stream Offset                                                                                            |
        |              | OFDM Num HE-SIG-B Symbols                                                                                                |
        |              | OFDM PE Disambiguity                                                                                                     |
        |              | OFDM SIG Compression Enabled                                                                                             |
        |              | OFDM Num SIG Symbols                                                                                                     |
        |              | OFDM RU Type                                                                                                             |
        |              | OFDM DBW (Hz)                                                                                                            |
        |              | OFDM IM Pilots Enabled                                                                                                   |
        |              | OFDM Unequal Modulation Enabled                                                                                          |
        |              | OFDM Unequal Modulation Pattern Index                                                                                    |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+
        | True (1)     | Header information is obtained by decoding the header fields in the PPDU.                                                |
        +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmHeaderDecodingEnabled, int):
                Specifies whether to enable the decoding of the header fields in the PPDU.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmHeaderDecodingEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_sig_compression_enabled(self, selector_string):
        r"""Gets whether to enable SIG compression. This attribute is applicable only for 802.11be MU PPDU and 802.11bn MU
        PPDU signals.

        You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | Specifies that SIG compression is disabled. |
        +--------------+---------------------------------------------+
        | True (1)     | Specifies that SIG compression is enabled.  |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmSigCompressionEnabled):
                Specifies whether to enable SIG compression. This attribute is applicable only for 802.11be MU PPDU and 802.11bn MU
                PPDU signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_SIG_COMPRESSION_ENABLED.value
            )
            attr_val = enums.OfdmSigCompressionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_sig_compression_enabled(self, selector_string, value):
        r"""Sets whether to enable SIG compression. This attribute is applicable only for 802.11be MU PPDU and 802.11bn MU
        PPDU signals.

        You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+---------------------------------------------+
        | Name (Value) | Description                                 |
        +==============+=============================================+
        | False (0)    | Specifies that SIG compression is disabled. |
        +--------------+---------------------------------------------+
        | True (1)     | Specifies that SIG compression is enabled.  |
        +--------------+---------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmSigCompressionEnabled, int):
                Specifies whether to enable SIG compression. This attribute is applicable only for 802.11be MU PPDU and 802.11bn MU
                PPDU signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmSigCompressionEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_SIG_COMPRESSION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_number_of_users(self, selector_string):
        r"""Gets the number of users in a multi-user (MU) PPDU.

        This attribute is ignored unless you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.

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
                Specifies the number of users in a multi-user (MU) PPDU.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_NUMBER_OF_USERS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_number_of_users(self, selector_string, value):
        r"""Sets the number of users in a multi-user (MU) PPDU.

        This attribute is ignored unless you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of users in a multi-user (MU) PPDU.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_NUMBER_OF_USERS.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_mcs_index(self, selector_string):
        r"""Gets the modulation and coding scheme (MCS) index or the data rate when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.

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

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for MU
        PPDU and TB PPDU signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the modulation and coding scheme (MCS) index or the data rate when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_MCS_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_mcs_index(self, selector_string, value):
        r"""Sets the modulation and coding scheme (MCS) index or the data rate when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.

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

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for MU
        PPDU and TB PPDU signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the modulation and coding scheme (MCS) index or the data rate when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_MCS_INDEX.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_scrambler_seed(self, selector_string):
        r"""Gets the scrambler seed for combined signal demodulation.  This is applicable only if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        The default value is 93.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the scrambler seed for combined signal demodulation.  This is applicable only if
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_SCRAMBLER_SEED.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_scrambler_seed(self, selector_string, value):
        r"""Sets the scrambler seed for combined signal demodulation.  This is applicable only if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        The default value is 93.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the scrambler seed for combined signal demodulation.  This is applicable only if
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_SCRAMBLER_SEED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_fec_coding_type(self, selector_string):
        r"""Gets the type of forward error correction (FEC) coding used.

        The value of this attribute is used to decode PLCP service data unit (PSDU) bits. This attribute is applicable
        only to 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        The default value is **LDPC**.

        +--------------+--------------------------------------------------------------+
        | Name (Value) | Description                                                  |
        +==============+==============================================================+
        | BCC (0)      | The FEC coding type used is binary convolutional code (BCC). |
        +--------------+--------------------------------------------------------------+
        | LDPC (1)     | The FEC coding type used is low-density parity check (LDPC). |
        +--------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmFecCodingType):
                Specifies the type of forward error correction (FEC) coding used.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_FEC_CODING_TYPE.value
            )
            attr_val = enums.OfdmFecCodingType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_fec_coding_type(self, selector_string, value):
        r"""Sets the type of forward error correction (FEC) coding used.

        The value of this attribute is used to decode PLCP service data unit (PSDU) bits. This attribute is applicable
        only to 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        The default value is **LDPC**.

        +--------------+--------------------------------------------------------------+
        | Name (Value) | Description                                                  |
        +==============+==============================================================+
        | BCC (0)      | The FEC coding type used is binary convolutional code (BCC). |
        +--------------+--------------------------------------------------------------+
        | LDPC (1)     | The FEC coding type used is low-density parity check (LDPC). |
        +--------------+--------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmFecCodingType, int):
                Specifies the type of forward error correction (FEC) coding used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmFecCodingType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_FEC_CODING_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_ru_size(self, selector_string):
        r"""Gets the size of the resource unit (RU) or the multiple resource unit (MRU) in terms of number of subcarriers for
        802.11ax, 802.11be, and 802.11bn signals.

        You must always configure this attribute for 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU. For
        802.11ax Extended Range SU, MU, 802.11be MU and 802.11bn MU PPDUs, you must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax MU PPDU, 802.11ax TB PPDU, 802.11be MU PPDU, 802.11be TB PPDU, 802.11bn MU PPDU, and 802.11bn TB PPDU.

        The default value is **26**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the size of the resource unit (RU) or the multiple resource unit (MRU) in terms of number of subcarriers for
                802.11ax, 802.11be, and 802.11bn signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_RU_SIZE.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_ru_size(self, selector_string, value):
        r"""Sets the size of the resource unit (RU) or the multiple resource unit (MRU) in terms of number of subcarriers for
        802.11ax, 802.11be, and 802.11bn signals.

        You must always configure this attribute for 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU. For
        802.11ax Extended Range SU, MU, 802.11be MU and 802.11bn MU PPDUs, you must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax MU PPDU, 802.11ax TB PPDU, 802.11be MU PPDU, 802.11be TB PPDU, 802.11bn MU PPDU, and 802.11bn TB PPDU.

        The default value is **26**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the size of the resource unit (RU) or the multiple resource unit (MRU) in terms of number of subcarriers for
                802.11ax, 802.11be, and 802.11bn signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_RU_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_ru_offset_mru_index(self, selector_string):
        r"""Gets the location of RU  or MRU for a user. If an RU is configured, the RU Offset is in terms of the index of a
        26-tone RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is configured, the MRU Index is as
        defined in the Table 36-8 to Table 36-15 of
        *IEEE P802.11be/D7.0*. If a dRU is configured, the RU Offset represents dRU Index as defined in the Table 38-4
        to Table 38-6 and the Equation 38-1 of *IEEE P802.11bn/D1.2*.

        This attribute is applicable for 802.11ax MU and TB PPDU, 802.11be MU and TB PPDU, and 802.11bn MU and TB PPDU
        signals. For 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU you must always configure this attribute. For
        802.11ax MU PPDU, 802.11be MU PPDU and 802.11bn MU PPDU, you must configure this attribute if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax MU PPDU, 802.11ax TB PPDU, 802.11be MU PPDU,  802.11be TB PPDU,  802.11bn MU PPDU, and 802.11bn TB PPDU.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the location of RU  or MRU for a user. If an RU is configured, the RU Offset is in terms of the index of a
                26-tone RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is configured, the MRU Index is as
                defined in the Table 36-8 to Table 36-15 of
                *IEEE P802.11be/D7.0*. If a dRU is configured, the RU Offset represents dRU Index as defined in the Table 38-4
                to Table 38-6 and the Equation 38-1 of *IEEE P802.11bn/D1.2*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_RU_OFFSET_MRU_INDEX.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_ru_offset_mru_index(self, selector_string, value):
        r"""Sets the location of RU  or MRU for a user. If an RU is configured, the RU Offset is in terms of the index of a
        26-tone RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is configured, the MRU Index is as
        defined in the Table 36-8 to Table 36-15 of
        *IEEE P802.11be/D7.0*. If a dRU is configured, the RU Offset represents dRU Index as defined in the Table 38-4
        to Table 38-6 and the Equation 38-1 of *IEEE P802.11bn/D1.2*.

        This attribute is applicable for 802.11ax MU and TB PPDU, 802.11be MU and TB PPDU, and 802.11bn MU and TB PPDU
        signals. For 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU you must always configure this attribute. For
        802.11ax MU PPDU, 802.11be MU PPDU and 802.11bn MU PPDU, you must configure this attribute if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax MU PPDU, 802.11ax TB PPDU, 802.11be MU PPDU,  802.11be TB PPDU,  802.11bn MU PPDU, and 802.11bn TB PPDU.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the location of RU  or MRU for a user. If an RU is configured, the RU Offset is in terms of the index of a
                26-tone RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is configured, the MRU Index is as
                defined in the Table 36-8 to Table 36-15 of
                *IEEE P802.11be/D7.0*. If a dRU is configured, the RU Offset represents dRU Index as defined in the Table 38-4
                to Table 38-6 and the Equation 38-1 of *IEEE P802.11bn/D1.2*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_RU_OFFSET_MRU_INDEX.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_ru_type(self, selector_string):
        r"""Gets whether contiguous subcarriers form the resource unit (rRU) or non-contiguous subcarriers form the resource
        unit (dRU).

        This attribute is only applicable for 802.11bn TB PPDU signals. You must configure this attribute if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **rRU**.

        +--------------+---------------------------------------------------+
        | Name (Value) | Description                                       |
        +==============+===================================================+
        | rRU (0)      | Contiguous subcarriers are present in the RU.     |
        +--------------+---------------------------------------------------+
        | dRU (1)      | Non-contiguous subcarriers are present in the RU. |
        +--------------+---------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmRUType):
                Specifies whether contiguous subcarriers form the resource unit (rRU) or non-contiguous subcarriers form the resource
                unit (dRU).

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_RU_TYPE.value
            )
            attr_val = enums.OfdmRUType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_ru_type(self, selector_string, value):
        r"""Sets whether contiguous subcarriers form the resource unit (rRU) or non-contiguous subcarriers form the resource
        unit (dRU).

        This attribute is only applicable for 802.11bn TB PPDU signals. You must configure this attribute if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **rRU**.

        +--------------+---------------------------------------------------+
        | Name (Value) | Description                                       |
        +==============+===================================================+
        | rRU (0)      | Contiguous subcarriers are present in the RU.     |
        +--------------+---------------------------------------------------+
        | dRU (1)      | Non-contiguous subcarriers are present in the RU. |
        +--------------+---------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmRUType, int):
                Specifies whether contiguous subcarriers form the resource unit (rRU) or non-contiguous subcarriers form the resource
                unit (dRU).

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmRUType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_RU_TYPE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_distribution_bandwidth(self, selector_string):
        r"""Gets the bandwidth across which RU subcarriers are distributed, when you set
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE` attribute to  **dRU**.

        This attribute is only applicable for 802.11bn TB PPDU signals. You must configure this attribute if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **20M**.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the bandwidth across which RU subcarriers are distributed, when you set
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE` attribute to  **dRU**.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_DISTRIBUTION_BANDWIDTH.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_distribution_bandwidth(self, selector_string, value):
        r"""Sets the bandwidth across which RU subcarriers are distributed, when you set
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE` attribute to  **dRU**.

        This attribute is only applicable for 802.11bn TB PPDU signals. You must configure this attribute if
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **20M**.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the bandwidth across which RU subcarriers are distributed, when you set
                :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE` attribute to  **dRU**.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_DISTRIBUTION_BANDWIDTH.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_guard_interval_type(self, selector_string):
        r"""Gets the size of the guard interval of OFDM symbols.

        For 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU, you must always configure this attribute. For other
        signals, you must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The value of the attribute for different standards is given in the following table.

        +------------------------------+-------------------------------------------+
        | Standard                     | Guard Interval Length                     |
        +==============================+===========================================+
        | 802.11n                      | 1/4 - 0.8 us                              |
        |                              | 1/8 - 0.4 us                              |
        |                              | 1/16 - N.A                                |
        +------------------------------+-------------------------------------------+
        | 802.11ac                     | 1/4 - 0.8 us                              |
        |                              | 1/8 - 0.4 us                              |
        |                              | 1/16 - N.A                                |
        +------------------------------+-------------------------------------------+
        | 802.11ax, 802.11be, 802.11bn | 1/4 - 3.2 us                              |
        |                              | 1/8 - 1.6 us                              |
        |                              | 1/16 - 0.8 us                             |
        +------------------------------+-------------------------------------------+

        The default value is **1/4**.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | 1/4 (0)      | The guard interval is 1/4th of the IFFT duration.  |
        +--------------+----------------------------------------------------+
        | 1/8 (1)      | The guard interval is 1/8th of the IFFT duration.  |
        +--------------+----------------------------------------------------+
        | 1/16 (2)     | The guard interval is 1/16th of the IFFT duration. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmGuardIntervalType):
                Specifies the size of the guard interval of OFDM symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_GUARD_INTERVAL_TYPE.value
            )
            attr_val = enums.OfdmGuardIntervalType(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_guard_interval_type(self, selector_string, value):
        r"""Sets the size of the guard interval of OFDM symbols.

        For 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU, you must always configure this attribute. For other
        signals, you must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The value of the attribute for different standards is given in the following table.

        +------------------------------+-------------------------------------------+
        | Standard                     | Guard Interval Length                     |
        +==============================+===========================================+
        | 802.11n                      | 1/4 - 0.8 us                              |
        |                              | 1/8 - 0.4 us                              |
        |                              | 1/16 - N.A                                |
        +------------------------------+-------------------------------------------+
        | 802.11ac                     | 1/4 - 0.8 us                              |
        |                              | 1/8 - 0.4 us                              |
        |                              | 1/16 - N.A                                |
        +------------------------------+-------------------------------------------+
        | 802.11ax, 802.11be, 802.11bn | 1/4 - 3.2 us                              |
        |                              | 1/8 - 1.6 us                              |
        |                              | 1/16 - 0.8 us                             |
        +------------------------------+-------------------------------------------+

        The default value is **1/4**.

        +--------------+----------------------------------------------------+
        | Name (Value) | Description                                        |
        +==============+====================================================+
        | 1/4 (0)      | The guard interval is 1/4th of the IFFT duration.  |
        +--------------+----------------------------------------------------+
        | 1/8 (1)      | The guard interval is 1/8th of the IFFT duration.  |
        +--------------+----------------------------------------------------+
        | 1/16 (2)     | The guard interval is 1/16th of the IFFT duration. |
        +--------------+----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmGuardIntervalType, int):
                Specifies the size of the guard interval of OFDM symbols.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmGuardIntervalType else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_GUARD_INTERVAL_TYPE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_ltf_size(self, selector_string):
        r"""Gets the LTF symbol size. This attribute is applicable only for 802.11ax, 802.11be, and 802.11bn signals.

        For 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU, you must always configure this attribute. For
        other signals, you must configure this attribute only when the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The valid combinations of LTF size and guard interval type are given in the following table.

        +---------------------------------+-------------------------+------------------------------------+
        | PPDU Type Property Value        | LTF Size Property Value | Guard Interval Type Property Value |
        +=================================+=========================+====================================+
        | SU PPDU, Extended Range SU PPDU | 4x                      | 1/4                                |
        +---------------------------------+-------------------------+------------------------------------+
        | SU PPDU, Extended Range SU PPDU | 2x                      | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+
        | SU PPDU, Extended Range SU PPDU | 4x, 2x, 1x              | 1/16                               |
        +---------------------------------+-------------------------+------------------------------------+
        | MU PPDU                         | 4x                      | 1/4                                |
        +---------------------------------+-------------------------+------------------------------------+
        | MU PPDU                         | 2x                      | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+
        | MU PPDU                         | 4x, 2x                  | 1/16                               |
        +---------------------------------+-------------------------+------------------------------------+
        | TB PPDU                         | 4x                      | 1/4                                |
        +---------------------------------+-------------------------+------------------------------------+
        | TB PPDU                         | 2x, 1x                  | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+
        | ELR PPDU                        | 2x                      | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+

        The default value is **4x**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | 4x (0)       | Specifies that the LTF symbol size is 4x. |
        +--------------+-------------------------------------------+
        | 2x (1)       | Specifies that the LTF symbol size is 2x. |
        +--------------+-------------------------------------------+
        | 1x (2)       | Specifies that the LTF symbol size is 1x. |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmLtfSize):
                Specifies the LTF symbol size. This attribute is applicable only for 802.11ax, 802.11be, and 802.11bn signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_LTF_SIZE.value
            )
            attr_val = enums.OfdmLtfSize(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_ltf_size(self, selector_string, value):
        r"""Sets the LTF symbol size. This attribute is applicable only for 802.11ax, 802.11be, and 802.11bn signals.

        For 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU, you must always configure this attribute. For
        other signals, you must configure this attribute only when the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The valid combinations of LTF size and guard interval type are given in the following table.

        +---------------------------------+-------------------------+------------------------------------+
        | PPDU Type Property Value        | LTF Size Property Value | Guard Interval Type Property Value |
        +=================================+=========================+====================================+
        | SU PPDU, Extended Range SU PPDU | 4x                      | 1/4                                |
        +---------------------------------+-------------------------+------------------------------------+
        | SU PPDU, Extended Range SU PPDU | 2x                      | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+
        | SU PPDU, Extended Range SU PPDU | 4x, 2x, 1x              | 1/16                               |
        +---------------------------------+-------------------------+------------------------------------+
        | MU PPDU                         | 4x                      | 1/4                                |
        +---------------------------------+-------------------------+------------------------------------+
        | MU PPDU                         | 2x                      | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+
        | MU PPDU                         | 4x, 2x                  | 1/16                               |
        +---------------------------------+-------------------------+------------------------------------+
        | TB PPDU                         | 4x                      | 1/4                                |
        +---------------------------------+-------------------------+------------------------------------+
        | TB PPDU                         | 2x, 1x                  | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+
        | ELR PPDU                        | 2x                      | 1/8                                |
        +---------------------------------+-------------------------+------------------------------------+

        The default value is **4x**.

        +--------------+-------------------------------------------+
        | Name (Value) | Description                               |
        +==============+===========================================+
        | 4x (0)       | Specifies that the LTF symbol size is 4x. |
        +--------------+-------------------------------------------+
        | 2x (1)       | Specifies that the LTF symbol size is 2x. |
        +--------------+-------------------------------------------+
        | 1x (2)       | Specifies that the LTF symbol size is 1x. |
        +--------------+-------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmLtfSize, int):
                Specifies the LTF symbol size. This attribute is applicable only for 802.11ax, 802.11be, and 802.11bn signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmLtfSize else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_LTF_SIZE.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_pre_fec_padding_factor(self, selector_string):
        r"""Gets the pre-FEC padding factor used in 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU for decoding PLCP
        service data unit (PSDU) bits.

        The valid values are 1 to 4, inclusive.

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
                Specifies the pre-FEC padding factor used in 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU for decoding PLCP
                service data unit (PSDU) bits.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_PRE_FEC_PADDING_FACTOR.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_pre_fec_padding_factor(self, selector_string, value):
        r"""Sets the pre-FEC padding factor used in 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU for decoding PLCP
        service data unit (PSDU) bits.

        The valid values are 1 to 4, inclusive.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the pre-FEC padding factor used in 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU for decoding PLCP
                service data unit (PSDU) bits.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PRE_FEC_PADDING_FACTOR.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_ldpc_extra_symbol_segment(self, selector_string):
        r"""Gets the presence of an extra OFDM symbol segment for LDPC in the 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn
        TB PPDU.

        This value is used for decoding PLCP service data unit (PSDU) bits. The valid values are 0 and 1.

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
                Specifies the presence of an extra OFDM symbol segment for LDPC in the 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn
                TB PPDU.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_LDPC_EXTRA_SYMBOL_SEGMENT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_ldpc_extra_symbol_segment(self, selector_string, value):
        r"""Sets the presence of an extra OFDM symbol segment for LDPC in the 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn
        TB PPDU.

        This value is used for decoding PLCP service data unit (PSDU) bits. The valid values are 0 and 1.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the presence of an extra OFDM symbol segment for LDPC in the 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn
                TB PPDU.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_LDPC_EXTRA_SYMBOL_SEGMENT.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_pe_disambiguity(self, selector_string):
        r"""Gets the packet extension disambiguity information.

        This attribute is applicable only for 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU.

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
                Specifies the packet extension disambiguity information.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_PE_DISAMBIGUITY.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_pe_disambiguity(self, selector_string, value):
        r"""Sets the packet extension disambiguity information.

        This attribute is applicable only for 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the packet extension disambiguity information.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_PE_DISAMBIGUITY.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_stbc_enabled(self, selector_string):
        r"""Gets whether space-time block coding is enabled. This attribute is applicable only for 802.11ax TB PPDU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------+
        | Name (Value) | Description                                         |
        +==============+=====================================================+
        | False (0)    | Specifies that space-time block coding is disabled. |
        +--------------+-----------------------------------------------------+
        | True (1)     | Specifies that space-time block coding is enabled.  |
        +--------------+-----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmStbcEnabled):
                Specifies whether space-time block coding is enabled. This attribute is applicable only for 802.11ax TB PPDU.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_STBC_ENABLED.value
            )
            attr_val = enums.OfdmStbcEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_stbc_enabled(self, selector_string, value):
        r"""Sets whether space-time block coding is enabled. This attribute is applicable only for 802.11ax TB PPDU.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-----------------------------------------------------+
        | Name (Value) | Description                                         |
        +==============+=====================================================+
        | False (0)    | Specifies that space-time block coding is disabled. |
        +--------------+-----------------------------------------------------+
        | True (1)     | Specifies that space-time block coding is enabled.  |
        +--------------+-----------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmStbcEnabled, int):
                Specifies whether space-time block coding is enabled. This attribute is applicable only for 802.11ax TB PPDU.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmStbcEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_STBC_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_number_of_space_time_streams(self, selector_string):
        r"""Gets the number of space time streams.

        This attribute is applicable when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False** for 802.11n,
        802.11ac, 802.11ax, and 802.11be standards or when PPDU Type is TB for 802.11ax, 802.11be, or 802.11bn standards.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of space time streams.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_NUMBER_OF_SPACE_TIME_STREAMS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_number_of_space_time_streams(self, selector_string, value):
        r"""Sets the number of space time streams.

        This attribute is applicable when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False** for 802.11n,
        802.11ac, 802.11ax, and 802.11be standards or when PPDU Type is TB for 802.11ax, 802.11be, or 802.11bn standards.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of space time streams.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_NUMBER_OF_SPACE_TIME_STREAMS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_space_time_stream_offset(self, selector_string):
        r"""Gets the space time stream offset.

        This attribute is applicable only to 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the space time stream offset.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_SPACE_TIME_STREAM_OFFSET.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_space_time_stream_offset(self, selector_string, value):
        r"""Sets the space time stream offset.

        This attribute is applicable only to 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
        802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the space time stream offset.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_SPACE_TIME_STREAM_OFFSET.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_number_of_he_sig_b_symbols(self, selector_string):
        r"""Gets the number of HE-SIG-B symbols.

        This attribute is applicable only to 802.11ax MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

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
                Specifies the number of HE-SIG-B symbols.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_NUMBER_OF_HE_SIG_B_SYMBOLS.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_number_of_he_sig_b_symbols(self, selector_string, value):
        r"""Sets the number of HE-SIG-B symbols.

        This attribute is applicable only to 802.11ax MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of HE-SIG-B symbols.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_NUMBER_OF_HE_SIG_B_SYMBOLS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_number_of_sig_symbols(self, selector_string):
        r"""Gets the number of SIG symbols. This attribute is applicable for 802.11be and 802.11bn MU PPDU signals.

        You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

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
                Specifies the number of SIG symbols. This attribute is applicable for 802.11be and 802.11bn MU PPDU signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_NUMBER_OF_SIG_SYMBOLS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_number_of_sig_symbols(self, selector_string, value):
        r"""Sets the number of SIG symbols. This attribute is applicable for 802.11be and 802.11bn MU PPDU signals.

        You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of SIG symbols. This attribute is applicable for 802.11be and 802.11bn MU PPDU signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_NUMBER_OF_SIG_SYMBOLS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_dcm_enabled(self, selector_string):
        r"""Gets whether the dual carrier modulation (DCM) is applied to the data field of the 802.11ax TB PPDU signals.

        You can set this attribute to **True** only for MCS indices 0, 1, 3, or 4. This attribute is used to compute
        masks for unused tone error measurements.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | False (0)    | Specifies that DCM is not applied to the data field for 802.11ax signals. |
        +--------------+---------------------------------------------------------------------------+
        | True (1)     | Specifies that DCM is applied to the data field for 802.11ax signals.     |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmDcmEnabled):
                Specifies whether the dual carrier modulation (DCM) is applied to the data field of the 802.11ax TB PPDU signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_DCM_ENABLED.value
            )
            attr_val = enums.OfdmDcmEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_dcm_enabled(self, selector_string, value):
        r"""Sets whether the dual carrier modulation (DCM) is applied to the data field of the 802.11ax TB PPDU signals.

        You can set this attribute to **True** only for MCS indices 0, 1, 3, or 4. This attribute is used to compute
        masks for unused tone error measurements.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+---------------------------------------------------------------------------+
        | Name (Value) | Description                                                               |
        +==============+===========================================================================+
        | False (0)    | Specifies that DCM is not applied to the data field for 802.11ax signals. |
        +--------------+---------------------------------------------------------------------------+
        | True (1)     | Specifies that DCM is applied to the data field for 802.11ax signals.     |
        +--------------+---------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmDcmEnabled, int):
                Specifies whether the dual carrier modulation (DCM) is applied to the data field of the 802.11ax TB PPDU signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmDcmEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_DCM_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_2xldpc_enabled(self, selector_string):
        r"""Gets whether to enable 2xLDPC for 802.11bn MU PPDU and 802.11bn TB PPDU signals.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+------------------------------------+
        | Name (Value) | Description                        |
        +==============+====================================+
        | False (0)    | Specifies that 2xLDPC is disabled. |
        +--------------+------------------------------------+
        | True (1)     | Specifies that 2xLDPC is enabled.  |
        +--------------+------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.Ofdm2xLdpcEnabled):
                Specifies whether to enable 2xLDPC for 802.11bn MU PPDU and 802.11bn TB PPDU signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_2xLDPC_ENABLED.value
            )
            attr_val = enums.Ofdm2xLdpcEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_2xldpc_enabled(self, selector_string, value):
        r"""Sets whether to enable 2xLDPC for 802.11bn MU PPDU and 802.11bn TB PPDU signals.

        Use "user<*n*>" as the `Selector String
        <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.

        The default value is **False**.

        +--------------+------------------------------------+
        | Name (Value) | Description                        |
        +==============+====================================+
        | False (0)    | Specifies that 2xLDPC is disabled. |
        +--------------+------------------------------------+
        | True (1)     | Specifies that 2xLDPC is enabled.  |
        +--------------+------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.Ofdm2xLdpcEnabled, int):
                Specifies whether to enable 2xLDPC for 802.11bn MU PPDU and 802.11bn TB PPDU signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.Ofdm2xLdpcEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_2xLDPC_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_im_pilots_enabled(self, selector_string):
        r"""Gets whether inteference mitigating pilots are present in 802.11bn MU PPDU signals.

        This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | False (0)    | Specifies that Interference Mitigating Pilots are absent.  |
        +--------------+------------------------------------------------------------+
        | True (1)     | Specifies that Interference Mitigating Pilots are present. |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmIMPilotsEnabled):
                Specifies whether inteference mitigating pilots are present in 802.11bn MU PPDU signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_IM_PILOTS_ENABLED.value
            )
            attr_val = enums.OfdmIMPilotsEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_im_pilots_enabled(self, selector_string, value):
        r"""Sets whether inteference mitigating pilots are present in 802.11bn MU PPDU signals.

        This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | False (0)    | Specifies that Interference Mitigating Pilots are absent.  |
        +--------------+------------------------------------------------------------+
        | True (1)     | Specifies that Interference Mitigating Pilots are present. |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmIMPilotsEnabled, int):
                Specifies whether inteference mitigating pilots are present in 802.11bn MU PPDU signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmIMPilotsEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_IM_PILOTS_ENABLED.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_unequal_modulation_enabled(self, selector_string):
        r"""Gets whether to enable unequal modulation in different spatial streams for 802.11bn MU PPDU signals.

        This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------+
        | Name (Value) | Description                                    |
        +==============+================================================+
        | False (0)    | Specifies that Unequal Modulation is disabled. |
        +--------------+------------------------------------------------+
        | True (1)     | Specifies that Unequal Modulation is enabled.  |
        +--------------+------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmUnequalModulationEnabled):
                Specifies whether to enable unequal modulation in different spatial streams for 802.11bn MU PPDU signals.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_UNEQUAL_MODULATION_ENABLED.value,
            )
            attr_val = enums.OfdmUnequalModulationEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_unequal_modulation_enabled(self, selector_string, value):
        r"""Sets whether to enable unequal modulation in different spatial streams for 802.11bn MU PPDU signals.

        This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------+
        | Name (Value) | Description                                    |
        +==============+================================================+
        | False (0)    | Specifies that Unequal Modulation is disabled. |
        +--------------+------------------------------------------------+
        | True (1)     | Specifies that Unequal Modulation is enabled.  |
        +--------------+------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmUnequalModulationEnabled, int):
                Specifies whether to enable unequal modulation in different spatial streams for 802.11bn MU PPDU signals.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmUnequalModulationEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_UNEQUAL_MODULATION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_unequal_modulation_pattern_index(self, selector_string):
        r"""Gets the unequal modulation pattern for the user. Valid values are between 0 and number of space time streams-1.

        This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

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
                Specifies the unequal modulation pattern for the user. Valid values are between 0 and number of space time streams-1.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_UNEQUAL_MODULATION_PATTERN_INDEX.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_unequal_modulation_pattern_index(self, selector_string, value):
        r"""Sets the unequal modulation pattern for the user. Valid values are between 0 and number of space time streams-1.

        This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 0.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the unequal modulation pattern for the user. Valid values are between 0 and number of space time streams-1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_UNEQUAL_MODULATION_PATTERN_INDEX.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_number_of_ltf_symbols(self, selector_string):
        r"""Gets the number of HE-LTF, EHT-LTF, or UHR-LTF symbols in the 802.11ax TB PPDU, 802.11be or 802.11bn TB PPDU,
        respectively.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The valid values are 1, 2, 4, 6, and 8. The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the number of HE-LTF, EHT-LTF, or UHR-LTF symbols in the 802.11ax TB PPDU, 802.11be or 802.11bn TB PPDU,
                respectively.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_NUMBER_OF_LTF_SYMBOLS.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_number_of_ltf_symbols(self, selector_string, value):
        r"""Sets the number of HE-LTF, EHT-LTF, or UHR-LTF symbols in the 802.11ax TB PPDU, 802.11be or 802.11bn TB PPDU,
        respectively.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The valid values are 1, 2, 4, 6, and 8. The default value is 1.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the number of HE-LTF, EHT-LTF, or UHR-LTF symbols in the 802.11ax TB PPDU, 802.11be or 802.11bn TB PPDU,
                respectively.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_NUMBER_OF_LTF_SYMBOLS.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_mu_mimo_ltf_mode_enabled(self, selector_string):
        r"""Gets whether the LTF sequence corresponding to each space-time stream is masked by a distinct orthogonal code.

        This attribute is valid for 802.11ax TB PPDU only.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | False (0)    | Specifies that the LTF sequence uses single stream pilots. |
        +--------------+------------------------------------------------------------+
        | True (1)     | Specifies that the LTF sequence is HE masked.              |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmMUMimoLtfModeEnabled):
                Specifies whether the LTF sequence corresponding to each space-time stream is masked by a distinct orthogonal code.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.OFDM_MU_MIMO_LTF_MODE_ENABLED.value
            )
            attr_val = enums.OfdmMUMimoLtfModeEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_mu_mimo_ltf_mode_enabled(self, selector_string, value):
        r"""Sets whether the LTF sequence corresponding to each space-time stream is masked by a distinct orthogonal code.

        This attribute is valid for 802.11ax TB PPDU only.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+------------------------------------------------------------+
        | Name (Value) | Description                                                |
        +==============+============================================================+
        | False (0)    | Specifies that the LTF sequence uses single stream pilots. |
        +--------------+------------------------------------------------------------+
        | True (1)     | Specifies that the LTF sequence is HE masked.              |
        +--------------+------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmMUMimoLtfModeEnabled, int):
                Specifies whether the LTF sequence corresponding to each space-time stream is masked by a distinct orthogonal code.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmMUMimoLtfModeEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_MU_MIMO_LTF_MODE_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_preamble_puncturing_enabled(self, selector_string):
        r"""Gets whether the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU signal is preamble punctured.

        Preamble puncturing is valid only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.CHANNEL_BANDWIDTH` attribute to **80M**, **160M**, or **320M**. This
        attribute is used only for SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------------+
        | Name (Value) | Description                                     |
        +==============+=================================================+
        | False (0)    | Indicates that preamble puncturing is disabled. |
        +--------------+-------------------------------------------------+
        | True (1)     | Indicates that preamble puncturing is enabled.  |
        +--------------+-------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmPreamblePuncturingEnabled):
                Specifies whether the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU signal is preamble punctured.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PREAMBLE_PUNCTURING_ENABLED.value,
            )
            attr_val = enums.OfdmPreamblePuncturingEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_preamble_puncturing_enabled(self, selector_string, value):
        r"""Sets whether the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU signal is preamble punctured.

        Preamble puncturing is valid only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.CHANNEL_BANDWIDTH` attribute to **80M**, **160M**, or **320M**. This
        attribute is used only for SEM measurement.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **False**.

        +--------------+-------------------------------------------------+
        | Name (Value) | Description                                     |
        +==============+=================================================+
        | False (0)    | Indicates that preamble puncturing is disabled. |
        +--------------+-------------------------------------------------+
        | True (1)     | Indicates that preamble puncturing is enabled.  |
        +--------------+-------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmPreamblePuncturingEnabled, int):
                Specifies whether the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU signal is preamble punctured.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmPreamblePuncturingEnabled else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PREAMBLE_PUNCTURING_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_preamble_puncturing_bitmap(self, selector_string):
        r"""Gets the punctured 20 MHz sub-channels in the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU
        signal when preamble puncturing is enabled.

        The binary representation of the signed integer is interpreted as the bitmap, where a '0' bit indicates that
        the corresponding sub-channel is punctured. In the binary representation, the least significant bit (LSB) maps to the
        20 MHz sub-channel lower in frequency, and the most significant bit (MSB) maps to the 20 MHz sub-channel higher in
        frequency. For a 80+80 MHz PPDU, the LSB represents the lowest sub-channel in the lower frequency segment. The
        puncturing information for the 20 MHz sub-channels of a 80 MHz PPDU are encoded in the least significant four bits. The
        puncturing information for the 20 MHz sub-channels of a 80+80 MHz PPDU or a 160 MHz PPDU is encoded in the least
        significant eight bits. The puncturing information for the 20 MHz sub-channels of a 320 MHz PPDU is encoded in the
        least significant sixteen bits.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **0xFFF FFFF FFFF FFFF**, indicating that none of the eight 20 MHz sub-channels of a 160 MHz
        PPDU are punctured. The most significant 52 bits are reserved for future use.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (int):
                Specifies the punctured 20 MHz sub-channels in the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU
                signal when preamble puncturing is enabled.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PREAMBLE_PUNCTURING_BITMAP.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_preamble_puncturing_bitmap(self, selector_string, value):
        r"""Sets the punctured 20 MHz sub-channels in the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU
        signal when preamble puncturing is enabled.

        The binary representation of the signed integer is interpreted as the bitmap, where a '0' bit indicates that
        the corresponding sub-channel is punctured. In the binary representation, the least significant bit (LSB) maps to the
        20 MHz sub-channel lower in frequency, and the most significant bit (MSB) maps to the 20 MHz sub-channel higher in
        frequency. For a 80+80 MHz PPDU, the LSB represents the lowest sub-channel in the lower frequency segment. The
        puncturing information for the 20 MHz sub-channels of a 80 MHz PPDU are encoded in the least significant four bits. The
        puncturing information for the 20 MHz sub-channels of a 80+80 MHz PPDU or a 160 MHz PPDU is encoded in the least
        significant eight bits. The puncturing information for the 20 MHz sub-channels of a 320 MHz PPDU is encoded in the
        least significant sixteen bits.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **0xFFF FFFF FFFF FFFF**, indicating that none of the eight 20 MHz sub-channels of a 160 MHz
        PPDU are punctured. The most significant 52 bits are reserved for future use.

        Args:
            selector_string (string):
                Pass an empty string.

            value (int):
                Specifies the punctured 20 MHz sub-channels in the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU
                signal when preamble puncturing is enabled.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_i64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PREAMBLE_PUNCTURING_BITMAP.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_auto_phase_rotation_detection_enabled(self, selector_string):
        r"""Gets whether to enable auto detection of phase rotation coefficients.

        This attribute is applicable only when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD`
        attribute to **802.11be** or **802.11bn**  and the :py:attr:`~nirfmxwlan.attributes.AttributeID.CHANNEL_BANDWIDTH`
        attribute to **320M**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------+
        | Name (Value) | Description                                                              |
        +==============+==========================================================================+
        | False (0)    | Specifies that auto detection of phase rotation coefficient is disabled. |
        +--------------+--------------------------------------------------------------------------+
        | True (1)     | Specifies that auto detection of phase rotation coefficient is enabled.  |
        +--------------+--------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.OfdmAutoPhaseRotationDetectionEnabled):
                Specifies whether to enable auto detection of phase rotation coefficients.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED.value,
            )
            attr_val = enums.OfdmAutoPhaseRotationDetectionEnabled(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_auto_phase_rotation_detection_enabled(self, selector_string, value):
        r"""Sets whether to enable auto detection of phase rotation coefficients.

        This attribute is applicable only when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD`
        attribute to **802.11be** or **802.11bn**  and the :py:attr:`~nirfmxwlan.attributes.AttributeID.CHANNEL_BANDWIDTH`
        attribute to **320M**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **True**.

        +--------------+--------------------------------------------------------------------------+
        | Name (Value) | Description                                                              |
        +==============+==========================================================================+
        | False (0)    | Specifies that auto detection of phase rotation coefficient is disabled. |
        +--------------+--------------------------------------------------------------------------+
        | True (1)     | Specifies that auto detection of phase rotation coefficient is enabled.  |
        +--------------+--------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.OfdmAutoPhaseRotationDetectionEnabled, int):
                Specifies whether to enable auto detection of phase rotation coefficients.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = (
                value.value if type(value) is enums.OfdmAutoPhaseRotationDetectionEnabled else value
            )
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_phase_rotation_coefficient_1(self, selector_string):
        r"""Gets the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **+1**.

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

            attr_val (enums.OfdmPhaseRotationCoefficient1):
                Specifies the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PHASE_ROTATION_COEFFICIENT_1.value,
            )
            attr_val = enums.OfdmPhaseRotationCoefficient1(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_phase_rotation_coefficient_1(self, selector_string, value):
        r"""Sets the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **+1**.

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

            value (enums.OfdmPhaseRotationCoefficient1, int):
                Specifies the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmPhaseRotationCoefficient1 else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PHASE_ROTATION_COEFFICIENT_1.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_phase_rotation_coefficient_2(self, selector_string):
        r"""Gets the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **-1**.

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

            attr_val (enums.OfdmPhaseRotationCoefficient2):
                Specifies the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PHASE_ROTATION_COEFFICIENT_2.value,
            )
            attr_val = enums.OfdmPhaseRotationCoefficient2(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_phase_rotation_coefficient_2(self, selector_string, value):
        r"""Sets the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **-1**.

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

            value (enums.OfdmPhaseRotationCoefficient2, int):
                Specifies the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmPhaseRotationCoefficient2 else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PHASE_ROTATION_COEFFICIENT_2.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_ofdm_phase_rotation_coefficient_3(self, selector_string):
        r"""Gets the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **-1**.

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

            attr_val (enums.OfdmPhaseRotationCoefficient3):
                Specifies the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PHASE_ROTATION_COEFFICIENT_3.value,
            )
            attr_val = enums.OfdmPhaseRotationCoefficient3(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_ofdm_phase_rotation_coefficient_3(self, selector_string, value):
        r"""Sets the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.

        This attribute is applicable only when you set the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED` attribute to **False**.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is **-1**.

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

            value (enums.OfdmPhaseRotationCoefficient3, int):
                Specifies the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.OfdmPhaseRotationCoefficient3 else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.OFDM_PHASE_ROTATION_COEFFICIENT_3.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_detected_standard(self, selector_string):
        r"""Gets the standard detected by the :py:meth:`auto_detect_signal` method.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | Name (Value)  | Description                                                                                                         |
        +===============+=====================================================================================================================+
        | Unknown (-1)  | Indicates that the standard is not detected.                                                                        |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11a/g (0) | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11a 1999 and IEEE Standard 802.11g-2003. |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11b (1)   | Corresponds to the DSSS based PPDU formats as defined in IEEE Standard 802.11b 1999.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11j (2)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11j 2004.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11p (3)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11p 2010.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11n (4)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11n 2009.                                |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11ac (5)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11ac 2013.                               |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11ax (6)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11ax/D8.0.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11be (7)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11be/D7.0.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+
        | 802.11bn (8)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11bn/D1.2.                              |
        +---------------+---------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.Standard):
                Returns the standard detected by the :py:meth:`auto_detect_signal` method.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_STANDARD.value,
            )
            attr_val = enums.Standard(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_detected_channel_bandwidth(self, selector_string):
        r"""Gets the channel bandwidth detected by the :py:meth:`auto_detect_signal`. The value is expressed in Hz.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the channel bandwidth detected by the :py:meth:`auto_detect_signal`. The value is expressed in Hz.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_CHANNEL_BANDWIDTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_detected_burst_length(self, selector_string):
        r"""Gets the duration of the packet detected by the :py:meth:`auto_detect_signal` method. The value is expressed in
        seconds.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Returns the duration of the packet detected by the :py:meth:`auto_detect_signal` method. The value is expressed in
                seconds.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_BURST_LENGTH.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def get_auto_level_initial_reference_level(self, selector_string):
        r"""Gets the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
        input signal. This value is expressed in dBm.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
                input signal. This value is expressed in dBm.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL.value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_auto_level_initial_reference_level(self, selector_string, value):
        r"""Sets the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
        input signal. This value is expressed in dBm.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 30.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
                input signal. This value is expressed in dBm.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_sample_clock_rate_factor(self, selector_string):
        r"""Gets the factor by which the sample clock rate is multiplied at the transmitter to generate a signal compressed in
        the frequency domain and expanded in the time domain.

        For example, a 40 MHz signal can be compressed to 20 MHz in the frequency domain if the sample clock rate is
        reduced to half at the transmitter. In this case, you must set this attribute to 0.5 to demodulate the signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        The valid values are 0.001 to 1, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the factor by which the sample clock rate is multiplied at the transmitter to generate a signal compressed in
                the frequency domain and expanded in the time domain.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.SAMPLE_CLOCK_RATE_FACTOR.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_sample_clock_rate_factor(self, selector_string, value):
        r"""Sets the factor by which the sample clock rate is multiplied at the transmitter to generate a signal compressed in
        the frequency domain and expanded in the time domain.

        For example, a 40 MHz signal can be compressed to 20 MHz in the frequency domain if the sample clock rate is
        reduced to half at the transmitter. In this case, you must set this attribute to 0.5 to demodulate the signal.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 1.

        The valid values are 0.001 to 1, inclusive.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the factor by which the sample clock rate is multiplied at the transmitter to generate a signal compressed in
                the frequency domain and expanded in the time domain.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.SAMPLE_CLOCK_RATE_FACTOR.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_limited_configuration_change(self, selector_string):
        r"""Gets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies, and/or
        power levels repeatedly, you can enable this attribute to help achieve faster measurements. When you set this attribute
        to a value other than **Disabled**, the RFmx driver will use an optimized code path and skips some checks. Because RFmx
        skips some checks when you use this attribute, you need to be aware of the limitations of this feature, which are
        listed in the `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to precompute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFInstr or personality attributes while
        testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration and RFmxInstr configuration are locked after the first Commit or Initiate of the named signal       |
        |                                        | configuration. Any configuration change thereafter either in RFmxInstr attributes or personality attributes will not be  |
        |                                        | considered by subsequent RFmx Commits or Initiates of this signal.                                                       |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency, external attenuation, and RFInstr configuration, is locked after      |
        |                                        | first Commit or Initiate of the named signal configuration. Thereafter, only the Center Frequency and External           |
        |                                        | Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of this signal.         |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level and RFInstr configuration, is locked after first Commit or          |
        |                                        | Initiate of the named signal configuration. Thereafter only the Reference Level attribute value change will be           |
        |                                        | considered by subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ     |
        |                                        | Power Edge Trigger, NI recommends that you set the IQ Power Edge Level Type to Relative so that the trigger level is     |
        |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
        |                                        | Property topic for more details about the limitations of using this mode.                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, external attenuation, and RFInstr configuration, is  |
        |                                        | locked after first Commit or Initiate of the named signal configuration. Thereafter only Center Frequency, Reference     |
        |                                        | Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of  |
        |                                        | this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power      |
        |                                        | Edge                                                                                                                     |
        |                                        | Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to   |
        |                                        | the Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this  |
        |                                        | mode.                                                                                                                    |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr    |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type to Relative so that the trigger level is automatically       |
        |                                        | adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic  |
        |                                        | for more details about the limitations of using this mode.                                                               |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (enums.LimitedConfigurationChange):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_i32(  # type: ignore
                updated_selector_string, attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value
            )
            attr_val = enums.LimitedConfigurationChange(attr_val)
        except (KeyError, ValueError):
            raise errors.DriverTooNewError()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_limited_configuration_change(self, selector_string, value):
        r"""Sets the set of attributes that are considered by RFmx in the locked signal configuration state.

        If your test system performs the same measurement at different selected ports, multiple frequencies, and/or
        power levels repeatedly, you can enable this attribute to help achieve faster measurements. When you set this attribute
        to a value other than **Disabled**, the RFmx driver will use an optimized code path and skips some checks. Because RFmx
        skips some checks when you use this attribute, you need to be aware of the limitations of this feature, which are
        listed in the `Limitations of the Limited Configuration Change Property
        <https://www.ni.com/docs/en-US/bundle/rfmx-wcdma-prop/page/rfmxwcdmaprop/limitations.html>`_ topic.

        You can also use this attribute to lock a specific instrument configuration for a signal so that every time
        that you initiate the signal, RFmx applies the RFmxInstr attributes from a locked configuration.

        NI recommends you use this attribute in conjunction with named signal configurations. Create named signal
        configurations for each measurement configuration in your test program and set this attribute to a value other than
        **Disabled** for one or more of the named signal configurations. This allows RFmx to precompute the acquisition
        settings for your measurement configurations and re-use the precomputed settings each time you initiate the
        measurement. You do not need to use this attribute if you create named signals for all the measurement configurations
        in your test program during test sequence initialization and do not change any RFInstr or personality attributes while
        testing each device under test. RFmx automatically optimizes that use case.

        Specify the named signal configuration you are setting this attribute in the selector string input.  You do not
        need to use a selector string to configure or read this attribute for the default signal instance. Refer to the
        `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
        about the string syntax for named signals.

        The default value is **Disabled**.

        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Name (Value)                           | Description                                                                                                              |
        +========================================+==========================================================================================================================+
        | Disabled (0)                           | This is the normal mode of RFmx operation. All configuration changes in RFmxInstr attributes or in personality           |
        |                                        | attributes will be applied during RFmx Commit.                                                                           |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | No Change (1)                          | Signal configuration and RFmxInstr configuration are locked after the first Commit or Initiate of the named signal       |
        |                                        | configuration. Any configuration change thereafter either in RFmxInstr attributes or personality attributes will not be  |
        |                                        | considered by subsequent RFmx Commits or Initiates of this signal.                                                       |
        |                                        | Use No Change if you have created named signal configurations for all measurement configurations but are setting some    |
        |                                        | RFmxInstr attributes. Refer to the Limitations of the Limited Configuration Change Property topic for more details       |
        |                                        | about the limitations of using this mode.                                                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Frequency (2)                          | Signal configuration, other than center frequency, external attenuation, and RFInstr configuration, is locked after      |
        |                                        | first Commit or Initiate of the named signal configuration. Thereafter, only the Center Frequency and External           |
        |                                        | Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of this signal.         |
        |                                        | Refer to the Limitations of the Limited Configuration Change Property topic for more details about the limitations of    |
        |                                        | using this mode.                                                                                                         |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Reference Level (3)                    | Signal configuration, other than the reference level and RFInstr configuration, is locked after first Commit or          |
        |                                        | Initiate of the named signal configuration. Thereafter only the Reference Level attribute value change will be           |
        |                                        | considered by subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ     |
        |                                        | Power Edge Trigger, NI recommends that you set the IQ Power Edge Level Type to Relative so that the trigger level is     |
        |                                        | automatically adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change   |
        |                                        | Property topic for more details about the limitations of using this mode.                                                |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Freq and Ref Level (4)                 | Signal configuration, other than center frequency, reference level, external attenuation, and RFInstr configuration, is  |
        |                                        | locked after first Commit or Initiate of the named signal configuration. Thereafter only Center Frequency, Reference     |
        |                                        | Level, and External Attenuation attribute value changes will be considered by subsequent driver Commits or Initiates of  |
        |                                        | this signal. If you have configured this signal to use an IQ Power Edge Trigger, NI recommends you set the IQ Power      |
        |                                        | Edge                                                                                                                     |
        |                                        | Level Type to Relative so that the trigger level is automatically adjusted as you adjust the reference level. Refer to   |
        |                                        | the Limitations of the Limited Configuration Change Property topic for more details about the limitations of using this  |
        |                                        | mode.                                                                                                                    |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+
        | Selected Ports, Freq and Ref Level (5) | Signal configuration, other than selected ports, center frequency, reference level, external attenuation, and RFInstr    |
        |                                        | configuration, is locked after first Commit or Initiate of the named signal configuration. Thereafter only Selected      |
        |                                        | Ports, Center Frequency, Reference Level, and External Attenuation attribute value changes will be considered by         |
        |                                        | subsequent driver Commits or Initiates of this signal. If you have configured this signal to use an IQ Power Edge        |
        |                                        | Trigger, NI recommends you set the IQ Power Edge Level Type to Relative so that the trigger level is automatically       |
        |                                        | adjusted as you adjust the reference level. Refer to the Limitations of the Limited Configuration Change Property topic  |
        |                                        | for more details about the limitations of using this mode.                                                               |
        +----------------------------------------+--------------------------------------------------------------------------------------------------------------------------+

        Args:
            selector_string (string):
                Pass an empty string.

            value (enums.LimitedConfigurationChange, int):
                Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            value = value.value if type(value) is enums.LimitedConfigurationChange else value
            error_code = self._interpreter.set_attribute_i32(  # type: ignore
                updated_selector_string,
                attributes.AttributeID.LIMITED_CONFIGURATION_CHANGE.value,
                value,
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_result_fetch_timeout(self, selector_string):
        r"""Gets the time, in seconds, to wait before results are available in the RFmxWLAN Attribute. Set this value to a
        time longer than expected for fetching the measurement. A value of -1 specifies that the RFmxWLAN Attribute waits until
        the measurement is complete.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

        Returns:
            Tuple (attr_val, error_code):

            attr_val (float):
                Specifies the time, in seconds, to wait before results are available in the RFmxWLAN Attribute. Set this value to a
                time longer than expected for fetching the measurement. A value of -1 specifies that the RFmxWLAN Attribute waits until
                the measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            attr_val, error_code = self._interpreter.get_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return attr_val, error_code

    @_raise_if_disposed
    def set_result_fetch_timeout(self, selector_string, value):
        r"""Sets the time, in seconds, to wait before results are available in the RFmxWLAN Attribute. Set this value to a
        time longer than expected for fetching the measurement. A value of -1 specifies that the RFmxWLAN Attribute waits until
        the measurement is complete.

        You do not need to use a selector string to configure or read this attribute for the default signal instance.
        Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
        information about the string syntax for named signals.

        The default value is 10.

        Args:
            selector_string (string):
                Pass an empty string.

            value (float):
                Specifies the time, in seconds, to wait before results are available in the RFmxWLAN Attribute. Set this value to a
                time longer than expected for fetching the measurement. A value of -1 specifies that the RFmxWLAN Attribute waits until
                the measurement is complete.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.set_attribute_f64(  # type: ignore
                updated_selector_string, attributes.AttributeID.RESULT_FETCH_TIMEOUT.value, value
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def abort_measurements(self, selector_string):
        r"""Stops acquisition and measurements associated with signal instance that you specify in the  **Selector String**
        parameter, which were previously initiated by the :py:meth:`initiate` method or measurement read methods. Calling this
        method is optional, unless you want to stop a measurement before it is complete. This method executes even if there is
        an incoming error.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.abort_measurements(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_detect_signal(self, selector_string, timeout):
        r"""Automatically detects the standard, channel bandwidth, and burst length of the input signal, and writes the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_STANDARD`,
        :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_CHANNEL_BANDWIDTH`, and
        :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_BURST_LENGTH` attributes.

        You must configure the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute before calling
        this method. If the peak power level of the input is unknown, you can call the :py:meth:`auto_level` method to
        configure the Reference Level attribute after you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.STANDARD` and
        :py:attr:`~nirfmxwlan.attributes.AttributeID.CHANNEL_BANDWIDTH` attributes to values corresponding to maximum expected
        channel bandwidth.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            timeout (float):
                This parameter specifies the timeout for fetching the specified measurement. Set this value to an appropriate time,
                longer than expected for fetching the measurement. A value of -1 specifies that the method waits until the measurement
                is complete. This value is expressed in seconds. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.auto_detect_signal(  # type: ignore
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_level(self, selector_string, measurement_interval):
        r"""Examines the input signal to calculate the peak power level and sets it as the value of the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute. Use this method to help calculate an
        approximate setting for the reference level.

        The RFmxWLAN Auto Level method does the following:
        #. Resets the mixer level, mixer level offset and IF output power offset.

        #. Sets the starting reference level to the maximum reference level supported by the device based on the current RF attenuation, mechanical attenuation and preamp enabled settings.

        #. Iterates to adjust the reference level based on the input signal peak power.

        #. Uses immediate triggering and restores the trigger settings back to user setting after completing execution.

        You can also specify the starting reference level using the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_LEVEL_INITIAL_REFERENCE_LEVEL` attribute.
        When using NI-PXie 5663, NI-PXie 5665, or NI-PXie 5668R devices, NI recommends that you set an appropriate
        value for mechanical attenuation before calling the RFmxWLAN Auto Level method. Setting an appropriate value for
        mechanical attenuation reduces the number of times the attenuator settings are changed by this method, thus reducing
        wear and tear, and maximizing the life time of the attenuator.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurement_interval (float):
                This parameter specifies the acquisition length. Use this value to compute the number of samples to acquire from the
                signal analyzer. This value is expressed in seconds. The default value is 10 ms.

                Auto Level method does not use any trigger for acquisition. It ignores the user-configured trigger attributes.
                NI recommends that you set a sufficiently high measurement interval to ensure that the acquired waveform is at least as
                long as one period of the signal.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.auto_level(  # type: ignore
                updated_selector_string, measurement_interval
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def check_measurement_status(self, selector_string):
        r"""Checks the status of the measurement. Use this method to check for any errors that may occur during measurement or to
        check whether the measurement is complete and results are available.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of result
                name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            Tuple (is_done, error_code):

            is_done (bool):
                This parameter indicates whether the measurement is complete.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            is_done, error_code = self._interpreter.check_measurement_status(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return is_done, error_code

    @_raise_if_disposed
    def clear_all_named_results(self, selector_string):
        r"""Clears all results for the signal that you specify in the **Selector String** parameter.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_all_named_results(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def clear_named_result(self, selector_string):
        r"""Clears a result instance specified by the result name in the **Selector String** parameter.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the selector string.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.clear_named_result(  # type: ignore
                updated_selector_string
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def commit(self, selector_string):
        r"""Commits settings to the hardware. Calling this method is optional. RFmxWLAN commits settings to the hardware when you
        call the :py:meth:`initiate` method.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.commit(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_channel_bandwidth(self, selector_string, channel_bandwidth):
        r"""Configures the channel bandwidth.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            channel_bandwidth (float):
                This parameter specifies the channel spacing as defined in section 3.1 of *IEEE Standard 802.11-2016 (pp. 130)*. This
                value is expressed in Hz. The default value is **20M**.

                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                                              |
                +==============+==========================================================================================================================+
                | 5M (5e6)     | This bandwidth corresponds to IEEE Standard 802.11p.                                                                     |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 10M (10e6)   | This bandwidth corresponds to IEEE Standard 802.11j and IEEE Standard 802.11p.                                           |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 20M (20e6)   | This bandwidth corresponds to IEEE Standard 802.11a/g, IEEE Standard 802.11j, IEEE Standard 802.11p, IEEE Standard       |
                |              | 802.11n, IEEE Standard 802.11ac, IEEE Standard 802.11ax, IEEE Standard 802.11be, and IEEE Standard 802.11bn.             |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 40M (40e6)   | This bandwidth corresponds to IEEE Standard 802.11n, IEEE Standard 802.11ac, IEEE Standard 802.11ax, IEEE Standard       |
                |              | 802.11be, and IEEE Standard 802.11bn.                                                                                    |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 80M (80e6)   | This bandwidth corresponds to IEEE Standard 802.11ac, IEEE Standard 802.11ax, IEEE Standard 802.11be, and IEEE Standard  |
                |              | 802.11bn.                                                                                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 160M (160e6) | This bandwidth corresponds to IEEE Standard 802.11ac, IEEE Standard 802.11ax, IEEE Standard 802.11be, and IEEE Standard  |
                |              | 802.11bn.                                                                                                                |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+
                | 320M (320e6) | This bandwidth corresponds to IEEE Standard 802.11be, and IEEE Standard 802.11bn.                                        |
                +--------------+--------------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_channel_bandwidth(  # type: ignore
                updated_selector_string, channel_bandwidth
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_digital_edge_trigger(
        self, selector_string, digital_edge_source, digital_edge, trigger_delay, enable_trigger
    ):
        r"""Configures the device to wait for a digital edge trigger and then marks a reference point within the record.

        On a MIMO session, this method configures the digital edge trigger on the master port. By default, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
        considered as the master port.

        Spectral measurements are sometimes implemented with multiple acquisitions and therefore will require that
        digital triggers are sent for each acquisition. Multiple factors, including the desired span versus the realtime
        bandwidth of the hardware, affect the number of acquisitions. RFmx recommends repeating the generation until the
        measurement is completed in order to ensure that all the acquisitions are triggered.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            digital_edge_source (string):
                This parameter specifies the source terminal for the digital edge trigger. This parameter is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**. The default value of this
                attribute is hardware dependent.

                To make a specific MIMO port as the trigger master, you must use the port specifier format
                "port::<device_name>/<source_terminal>".

                Example:

                "port::myrfsa1/PFI0"

                +---------------------------+-----------------------------------------------------------+
                | Name (Value)              | Description                                               |
                +===========================+===========================================================+
                | PFI0 (PFI0)               | The trigger is received on PFI 0.                         |
                +---------------------------+-----------------------------------------------------------+
                | PFI1 (PFI1)               | The trigger is received on PFI 1.                         |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig0 (PXI_Trig0)     | The trigger is received on PXI trigger line 0.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig1 (PXI_Trig1)     | The trigger is received on PXI trigger line 1.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig2 (PXI_Trig2)     | The trigger is received on PXI trigger line 2.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig3 (PXI_Trig3)     | The trigger is received on PXI trigger line 3.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig4 (PXI_Trig4)     | The trigger is received on PXI trigger line 4.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig5 (PXI_Trig5)     | The trigger is received on PXI trigger line 5.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig6 (PXI_Trig6)     | The trigger is received on PXI trigger line 6.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_Trig7 (PXI_Trig7)     | The trigger is received on PXI trigger line 7.            |
                +---------------------------+-----------------------------------------------------------+
                | PXI_STAR (PXI_STAR)       | The trigger is received on the PXI star trigger line.     |
                +---------------------------+-----------------------------------------------------------+
                | PXIe_DStarB (PXIe_DStarB) | The trigger is received on the PXIe DStar B trigger line. |
                +---------------------------+-----------------------------------------------------------+
                | TimerEvent (TimerEvent)   | The trigger is received from the timer event.             |
                +---------------------------+-----------------------------------------------------------+

            digital_edge (enums.DigitalEdgeTriggerEdge, int):
                This parameter specifies the active edge for the trigger. This parameter is used only when you set the Trigger Type
                attribute to **Digital Edge**. The default value is **Rising Edge**.

                +------------------+--------------------------------------------------------+
                | Name (Value)     | Description                                            |
                +==================+========================================================+
                | Rising Edge (0)  | The trigger asserts on the rising edge of the signal.  |
                +------------------+--------------------------------------------------------+
                | Falling Edge (1) | The trigger asserts on the falling edge of the signal. |
                +------------------+--------------------------------------------------------+

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. The default value is 0. If the
                delay is negative, the measurement acquires pretrigger samples. If the delay is positive, the measurement acquires
                posttrigger samples.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(digital_edge_source, "digital_edge_source")
            digital_edge = (
                digital_edge.value
                if type(digital_edge) is enums.DigitalEdgeTriggerEdge
                else digital_edge
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_digital_edge_trigger(  # type: ignore
                updated_selector_string,
                digital_edge_source,
                digital_edge,
                trigger_delay,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_external_attenuation(self, selector_string, external_attenuation):
        r"""Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. On a MIMO
        session, use port::<deviceName>/<channelNumber> as a selector string to configure external attenuation for each port.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of port
                string. On a MIMO session, an empty string corresponds to all the initialized ports.

                Example:

                ""

                "port::myrfsa1/0"

                You can use the :py:meth:`build_result_string` method to build the selector string. On a MIMO session, you can
                use the :py:meth:`build_port_string` method to build the selector string.

            external_attenuation (float):
                This parameter specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal
                analyzer. This value is expressed in dB. For more information about attenuation, refer to the *Attenuation and Signal
                Levels*  topic for your device in the *NI RF Vector Signal Analyzers Help*. The default value is 0.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_external_attenuation(  # type: ignore
                updated_selector_string, external_attenuation
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency_array(self, selector_string, center_frequency):
        r"""Configures a list of expected carrier frequencies of the RF signal to acquire. The signal analyzers tune to these
        frequencies based on the value you configure for the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.NUMBER_OF_FREQUENCY_SEGMENTS` attribute.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            center_frequency (float):
                This parameter specifies the list of center frequencies to be configured for the given number of frequency segments.
                This value is expressed in Hz. The default value is hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency_array(  # type: ignore
                updated_selector_string, center_frequency
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_frequency(self, selector_string, center_frequency):
        r"""Configures the expected carrier frequency of the RF signal to acquire. The signal analyzer tunes to this frequency. On
        a MIMO session, use "segment<*n*>" as the selector string to configure this method.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of segment
                number.

                Example:

                "segment0"

                You can use the :py:meth:`build_chain_string` method to build the selector string. If number of segments is
                greater than 1, you can use the :py:meth:`build_segment_string` method to build the selector string.

            center_frequency (float):
                This parameter specifies the center frequency. This value is expressed in Hz. The default of this attribute is hardware
                dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_frequency(  # type: ignore
                updated_selector_string, center_frequency
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_iq_power_edge_trigger(
        self,
        selector_string,
        iq_power_edge_source,
        iq_power_edge_slope,
        iq_power_edge_level,
        trigger_delay,
        trigger_min_quiet_time_mode,
        trigger_min_quiet_time_duration,
        iq_power_edge_level_type,
        enable_trigger,
    ):
        r"""Configures the device to wait for the complex power of the I/Q data to cross the specified threshold and then marks a
        reference point within the record.

        On a MIMO session, this method configures the IQ Power edge trigger on the master port. By default, the
        :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
        considered as the master port.

        To trigger on bursty signals, specify a minimum quiet time, which ensures that the trigger does not occur in
        the middle of the burst signal. The quiet time must be set to a value smaller than the time between bursts, but large
        enough to ignore power changes within a burst.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            iq_power_edge_source (string):
                This parameter specifies the channel from which the device monitors the trigger. This parameter is used only when you
                set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**. The default value is
                hardware dependent.

                To make a specific MIMO port as the trigger master, use the port specifier format
                "port::<deviceName>/<source_terminal>".

                Example:

                port::myrfsa1/0

            iq_power_edge_slope (enums.IQPowerEdgeTriggerSlope, int):
                This parameter specifies whether the device asserts the trigger when the signal power is rising or falling. The device
                asserts the trigger when the signal power exceeds the specified level with the slope you specify. This attribute is
                used only when you set the Trigger Type attribute to **IQ Power Edge**. The default value is **Rising Slope**.

                +-------------------+-------------------------------------------------------+
                | Name (Value)      | Description                                           |
                +===================+=======================================================+
                | Rising Slope (0)  | The trigger asserts when the signal power is rising.  |
                +-------------------+-------------------------------------------------------+
                | Falling Slope (1) | The trigger asserts when the signal power is falling. |
                +-------------------+-------------------------------------------------------+

            iq_power_edge_level (float):
                This parameter specifies the power level at which the device triggers. This value is expressed in dB when you set the
                **IQ Power Edge Level Type** parameter to **Relative** and is expressed in dBm when you set the **IQ Power Edge Level
                Type** parameter to **Absolute**. The default value is hardware dependent.

                The device asserts the trigger when the signal exceeds the level specified by the value of this attribute,
                taking into consideration the specified slope. This attribute is used only when you set the
                :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. The default value is 0. If the
                delay is negative, the measurement acquires pretrigger samples. If the delay is positive, the measurement acquires
                posttrigger samples.

            trigger_min_quiet_time_mode (enums.TriggerMinimumQuietTimeMode, int):
                This parameter specifies whether the measurement computes the minimum quiet time used for triggering. The default value
                is **Auto**.

                +--------------+------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                              |
                +==============+==========================================================================================+
                | Manual (0)   | The minimum quiet time used for triggering is the value of the Min Quiet Time parameter. |
                +--------------+------------------------------------------------------------------------------------------+
                | Auto (1)     | The measurement computes the minimum quiet time used for triggering.                     |
                +--------------+------------------------------------------------------------------------------------------+

            trigger_min_quiet_time_duration (float):
                This parameter specifies the duration for which the signal must be quiet before the signal analyzer arms the I/Q Power
                Edge trigger. If you set the **IQ Power Edge Slope** parameter to **Rising Slope**, the signal is quiet when it is
                below the trigger level. If you set the **IQ Power Edge Slope** parameter to **Falling Slope**, the signal is quiet
                when it is above the trigger level. The default of this attribute is hardware dependent. This value is expressed in
                seconds.

            iq_power_edge_level_type (enums.IQPowerEdgeTriggerLevelType, int):
                This parameter specifies the reference for the **IQ Power Edge Level** parameter. The **IQ Power Edge Level** parameter
                is used only when you set the Trigger Type attribute to **IQ Power Edge**. The default value is **Relative**.

                +--------------+----------------------------------------------------------------------------------------------+
                | Name (Value) | Description                                                                                  |
                +==============+==============================================================================================+
                | Relative (0) | The IQ Power Edge Level attribute is relative to the value of the Reference Level attribute. |
                +--------------+----------------------------------------------------------------------------------------------+
                | Absolute (1) | The IQ Power Edge Level attribute specifies the absolute power.                              |
                +--------------+----------------------------------------------------------------------------------------------+

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(iq_power_edge_source, "iq_power_edge_source")
            iq_power_edge_slope = (
                iq_power_edge_slope.value
                if type(iq_power_edge_slope) is enums.IQPowerEdgeTriggerSlope
                else iq_power_edge_slope
            )
            trigger_min_quiet_time_mode = (
                trigger_min_quiet_time_mode.value
                if type(trigger_min_quiet_time_mode) is enums.TriggerMinimumQuietTimeMode
                else trigger_min_quiet_time_mode
            )
            iq_power_edge_level_type = (
                iq_power_edge_level_type.value
                if type(iq_power_edge_level_type) is enums.IQPowerEdgeTriggerLevelType
                else iq_power_edge_level_type
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_iq_power_edge_trigger(  # type: ignore
                updated_selector_string,
                iq_power_edge_source,
                iq_power_edge_slope,
                iq_power_edge_level,
                trigger_delay,
                trigger_min_quiet_time_mode,
                trigger_min_quiet_time_duration,
                iq_power_edge_level_type,
                int(enable_trigger),
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_number_of_frequency_segments_and_receive_chains(
        self, selector_string, number_of_frequency_segments, number_of_receive_chains
    ):
        r"""Configures the number of frequency segments and receive chains.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            number_of_frequency_segments (int):
                This parameter specifies the number of frequency segments. The default value is 1.

            number_of_receive_chains (int):
                This parameter specifies the number of receive chains. The default value is 1.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_number_of_frequency_segments_and_receive_chains(  # type: ignore
                updated_selector_string, number_of_frequency_segments, number_of_receive_chains
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_reference_level(self, selector_string, reference_level):
        r"""Configures the reference level, which represents the maximum expected power of an RF input signal. On a MIMO session,
        use "port::<deviceName>/<channelNumber>" as the selector string to configure reference level for each port.

        Args:
            selector_string (string):
                This parameter specifies a `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ comprising of port
                string. On a MIMO session, an empty string corresponds to all the initialized ports.

                Example:

                ""

                "port::myrfsa1/0"

                You can use the :py:meth:`build_result_string` method to build the selector string. On a MIMO session, you can
                use the :py:meth:`build_port_string` method to build the selector string.

            reference_level (float):
                This parameter specifies the reference level which represents the maximum expected power of the RF input signal. This
                value is expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices. The default value of this attribute
                is hardware dependent.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_reference_level(  # type: ignore
                updated_selector_string, reference_level
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_selected_ports_multiple(self, selector_string, selected_ports):
        r"""Configures the selected ports to each segment/chain based on the values you set in
        :py:attr:`~nirfmxwlan.attributes.AttributeID.NUMBER_OF_FREQUENCY_SEGMENTS` and
        :py:attr:`~nirfmxwlan.attributes.AttributeID.NUMBER_OF_RECEIVE_CHAINS` attributes.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            selected_ports (string):
                This parameter specifies the list of MIMO ports to be configured. Use "port::<deviceName>/<channelNumber>" as the
                format for the selected port.

                For PXIe-5830/5831/5832 devices on a MIMO session, the selected port includes the instrument port in the format
                "port::<deviceName>/<channelNumber>/<instrPort>".

                Example:

                port::myrfsa1/0/if1

                You can use the :py:meth:`build_port_string` method to build the selected port.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(selected_ports, "selected_ports")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_selected_ports_multiple(  # type: ignore
                updated_selector_string, selected_ports
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_software_edge_trigger(self, selector_string, trigger_delay, enable_trigger):
        r"""Configures the device to wait for a software trigger and then marks a reference point within the record.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            trigger_delay (float):
                This parameter specifies the trigger delay time. This value is expressed in seconds. The default value is 0. If the
                delay is negative, the measurement acquires pretrigger samples. If the delay is positive, the measurement acquires
                posttrigger samples.

            enable_trigger (bool):
                This parameter specifies whether to enable the trigger. The default value is TRUE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_software_edge_trigger(  # type: ignore
                updated_selector_string, trigger_delay, int(enable_trigger)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def configure_standard(self, selector_string, standard):
        r"""Configures the IEEE 802.11 standard for the signal under analysis.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            standard (enums.Standard, int):
                This parameter specifies the signal under analysis as defined under *IEEE Standard 802.11*. The default value is
                **802.11a/g**.

                .. note::
                   On a MIMO session, the supported standards are 802.11n, 802.11ac, 802.11ax, and 802.11be.

                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | Name (Value)  | Description                                                                                                         |
                +===============+=====================================================================================================================+
                | 802.11a/g (0) | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11a-1999 and IEEE Standard 802.11g-2003. |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11b (1)   | Corresponds to the DSSS based PPDU formats as defined in IEEE Standard 802.11b-1999.                                |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11j (2)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11j-2004.                                |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11p (3)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11p-2010.                                |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11n (4)   | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11n-2009.                                |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11ac (5)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard 802.11ac-2013.                               |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11ax (6)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11ax/D8.0.                              |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11be (7)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11be/D7.0.                              |
                +---------------+---------------------------------------------------------------------------------------------------------------------+
                | 802.11bn (8)  | Corresponds to the OFDM based PPDU formats as defined in IEEE Standard P802.11bn/D1.2.                              |
                +---------------+---------------------------------------------------------------------------------------------------------------------+

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            standard = standard.value if type(standard) is enums.Standard else standard
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.configure_standard(  # type: ignore
                updated_selector_string, standard
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def disable_trigger(self, selector_string):
        r"""Configures the device to not wait for a trigger to mark a reference point within a record. This method defines the
        signal triggering as immediate.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.disable_trigger(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def initiate(self, selector_string, result_name):
        r"""Initiates all enabled measurements. Call this method after configuring the signal and measurement. This method
        asynchronously launches measurements in the background and immediately returns to the caller program. You can fetch
        measurement results using the Fetch methods or result attributes in the attribute node. To get the status of
        measurements, use the :py:meth:`wait_for_measurement_complete` method or :py:meth:`check_measurement_status` method.

        Args:
            selector_string (string):
                This parameter specifies the signal name and result name. The result name can either be specified through this input or
                the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name** parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method  to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.initiate(  # type: ignore
                updated_selector_string, result_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def reset_to_default(self, selector_string):
        r"""Resets a signal to the default values.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.reset_to_default(updated_selector_string)  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def select_measurements(self, selector_string, measurements, enable_all_traces):
        r"""Enables all the measurements that you specify in the **Measurements** parameter and disables all other measurements.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            measurements (enums.MeasurementTypes, int):
                This parameter specifies the measurement to perform. You can specify one or more of the following measurements. The
                default is an empty array.

                +----------------+---------------------------------+
                | Name (Value)   | Description                     |
                +================+=================================+
                | TXP (0)        | Enables TXP measurement.        |
                +----------------+---------------------------------+
                | PowerRamp (1)  | Enables PowerRamp measurement.  |
                +----------------+---------------------------------+
                | DSSSModAcc (2) | Enables DSSSModAcc measurement. |
                +----------------+---------------------------------+
                | OFDMModAcc (3) | Enables OFDMModAcc measurement. |
                +----------------+---------------------------------+
                | SEM (4)        | Enables SEM measurement.        |
                +----------------+---------------------------------+

            enable_all_traces (bool):
                This parameter specifies whether to enable all traces for the selected measurement. The default value is FALSE.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            measurements = (
                measurements.value if type(measurements) is enums.MeasurementTypes else measurements
            )
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.select_measurements(  # type: ignore
                updated_selector_string, measurements, int(enable_all_traces)
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def wait_for_measurement_complete(self, selector_string, timeout):
        r"""Waits for the specified number for seconds for all the measurements to complete.

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
                This parameter specifies the time for which the method waits for the measurement to complete. This value is expressed
                in seconds. A value of -1 specifies that the method waits until the measurement is complete. The default value is 10.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.wait_for_measurement_complete(  # type: ignore
                updated_selector_string, timeout
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def auto_detect_signal_analysis_only(self, selector_string, x0, dx, iq):
        r"""Automatically detects the standard, channel bandwidth, and burst length on the I/Q complex waveform that you specify in
        **IQ** parameter, and writes the :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_STANDARD`,
        :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_CHANNEL_BANDWIDTH`, and
        :py:attr:`~nirfmxwlan.attributes.AttributeID.AUTO_DETECT_SIGNAL_DETECTED_BURST_LENGTH` attributes.

        Args:
            selector_string (string):
                Pass an empty string.
                The signal name that is passed when creating the signal configuration is used.

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq (numpy.complex64):
                This parameter specifies an array of complex-valued time domain data. The real and imaginary parts of this complex data
                array correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.auto_detect_signal_analysis_only(  # type: ignore
                updated_selector_string, x0, dx, iq
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @staticmethod
    def build_result_string(result_name):
        r"""Creates selector string for use with configuration or fetch.

        Args:
            result_name (string):
                Specifies the result name for building the selector string.
                This input accepts the result name with or without the "result::" prefix.
                Example: "", "result::r1", "r1".

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(result_name, "result_name")
        return _helper.build_result_string(result_name)

    @staticmethod
    def build_chain_string(selector_string, chain_number):
        r"""Creates a chain string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            chain_number (int):
                This parameter specifies the chain number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_chain_string(selector_string, chain_number)  # type: ignore

    @staticmethod
    def build_gate_string(selector_string, gate_number):
        r"""Creates the gate string to use as the selector string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            gate_number (int):
                This parameter specifies the gate number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_gate_string(selector_string, gate_number)  # type: ignore

    @staticmethod
    def build_offset_string(selector_string, offset_number):
        r"""Creates the offset string to use as the selector string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            offset_number (int):
                This parameter specifies the offset number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_offset_string(selector_string, offset_number)  # type: ignore

    @staticmethod
    def build_segment_string(selector_string, segment_number):
        r"""Creates a segment string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            segment_number (int):
                This parameter specifies the segment number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_segment_string(selector_string, segment_number)  # type: ignore

    @staticmethod
    def build_stream_string(selector_string, stream_number):
        r"""Creates the stream string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            stream_number (int):
                This parameter specifies the stream number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_stream_string(selector_string, stream_number)  # type: ignore

    @staticmethod
    def build_user_string(selector_string, user_number):
        r"""Creates the user string to use as the selector string.

        Args:
            selector_string (string):
                Specifies the result name for building the selector string.

            user_number (int):
                This parameter specifies the user number for building the selector string.

        Returns:
            string:
                Contains the selector string created by this method.
        """
        _helper.validate_not_none(selector_string, "selector_string")
        return _helper.build_user_string(selector_string, user_number)  # type: ignore

    @_raise_if_disposed
    def clone_signal_configuration(self, new_signal_name):
        r"""Creates a new instance of a signal by copying all the properties from an existing signal instance.

        Args:
            new_signal_name (string):
                This parameter specifies the name of the new signal. This parameter accepts the signal name with or without the \"signal::\" prefix.

                Example:

                \"signal::NewSigName\"

                \"NewSigName\"

        Returns:
            Tuple (cloned_signal, error_code):

            cloned_signal (wlan):
                Contains a new Wlan signal instance.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(new_signal_name, "new_signal_name")
            updated_new_signal_name = _helper.validate_and_remove_signal_qualifier(
                new_signal_name, self
            )
            cloned_signal, error_code = self._interpreter.clone_signal_configuration(  # type: ignore
                self.signal_configuration_name, updated_new_signal_name
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return cloned_signal, error_code

    @_raise_if_disposed
    def send_software_edge_trigger(self):
        r"""Sends a trigger to the device when you use the [RFmxWLAN Configure Trigger](RFmxWLAN_Configure_Trigger.html) function to choose a software version of a trigger and the device is waiting for the trigger to be sent. You can also use this function to override a hardware trigger.

        This function returns an error in the following situations:

        - You configure an invalid trigger.

        - You have not previously called the initiate function.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            error_code = self._interpreter.send_software_edge_trigger()  # type: ignore
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def get_all_named_result_names(self, selector_string):
        r"""Returns all the named result names of the signal that you specify in the Selector String parameter.

        Args:
            selector_string (string):
                Pass an empty string. The signal name that is passed when creating the signal configuration is used.

        Returns:
            Tuple (result_names, default_result_exists, error_code):

            result_names (string):
                Returns an array of result names.

            default_result_exists (bool):
                Indicates whether the default result exists.

            error_code (int):
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            result_names, default_result_exists, error_code = (
                self._interpreter.get_all_named_result_names(updated_selector_string)  # type: ignore
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return result_names, default_result_exists, error_code

    @_raise_if_disposed
    def analyze_iq_1_waveform(self, selector_string, result_name, x0, dx, iq, reset):
        r"""Performs the enabled measurements on the  I/Q complex waveform  that you specify in the **IQ** parameter. Call this
        method after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch
        methods or result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **IQ** or **IQ or Spectral**.
        When using the Analysis-Only mode in RFmxWLAN, the RFmx driver ignores the RFmx hardware settings such as reference level
        and attenuation. The only RF hardware settings that are not ignored are the center frequency and trigger type, since it is
        needed for spectral measurement traces as well as some measurements such as ModAcc, ACP, and SEM.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the result name. The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq (numpy.complex64):
                This parameter specifies an array of complex-valued time domain data. The real and imaginary parts of this complex data
                array correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_iq_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, iq, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_spectrum_1_waveform(self, selector_string, result_name, x0, dx, spectrum, reset):
        r"""Performs the enabled measurements on the spectrum that you specify in the **Spectrum** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **Spectral** or **IQ or Spectral**.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the result name.  The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start frequency of the spectrum. This value is expressed in Hz.

            dx (float):
                This parameter specifies the frequency interval between data points in the spectrum.

            spectrum (numpy.float32):
                This parameter specifies the data for a spectrum waveform.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_spectrum_1_waveform(  # type: ignore
                updated_selector_string, result_name, x0, dx, spectrum, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_n_waveforms_iq(self, selector_string, result_name, x0, dx, iq, reset):
        r"""Performs the enabled measurements on multiple I/Q complex waveforms that you specify in the **IQ** parameter. Call this
        method after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch
        methods or result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **IQ** or **IQ or Spectral**.
        When using the Analysis-Only mode in RFmxWLAN, the RFmx driver ignores the RFmx hardware settings such as reference level
        and attenuation. The only RF hardware settings that are not ignored are the center frequency and trigger type, since it is
        needed for spectral measurement traces as well as some measurements such as ModAcc, ACP, and SEM.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the result name. The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start time of the input **y** array. This value is expressed in seconds.

            dx (float):
                This parameter specifies the time interval between the samples in the input **y** array. This value is expressed in
                seconds. The reciprocal of **dx** indicates the I/Q rate of the input signal.

            iq ([numpy.complex64]):
                This parameter specifies an array of complex-valued time domain data arrays. The real and imaginary parts of this complex data
                correspond to the in-phase (I) and quadrature-phase (Q) data, respectively.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_n_waveforms_iq(  # type: ignore
                updated_selector_string, result_name, x0, dx, iq, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code

    @_raise_if_disposed
    def analyze_n_waveforms_spectrum(self, selector_string, result_name, x0, dx, spectrum, reset):
        r"""Performs the enabled measurements on multiple spectra that you specify in the **Spectrum** parameter. Call this method
        after you configure the signal and measurement attributes. You can fetch measurement results using the Fetch methods or
        result attributes in the attribute node.
        Use this method only if the :py:attr:`~nirfmxinstr.attribute.AttributeID.RECOMMENDED_ACQUISITION_TYPE` attribute value
        is either **Spectral** or **IQ or Spectral**.

        .. note::
           Query the Recommended Acquisition Type attribute from the RFmxInstr Attribute after calling the :py:meth:`commit`
           method.

        Args:
            selector_string (string):
                This parameter specifies the result name. The result name can either be specified through this input
                or the **Result Name** parameter. If you do
                not specify the result name in this parameter, either the result name specified by the **Result Name**  parameter  or
                the default result instance is used.

                Example:

                ""

                "result::r1"

                You can use the :py:meth:`build_result_string` method to build the `Selector String
                <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_.

            result_name (string):
                This parameter specifies the name to be associated with measurement results. Provide a unique name, such as "r1" to
                enable fetching of multiple measurement results and traces. This input accepts the result name with or without the
                "result::" prefix. The default value is "" (empty string), which refers to the default result instance.

                Example:

                ""

                "result::r1"

                "r1"

            x0 (float):
                This parameter specifies the start frequency of the spectrum. This value is expressed in Hz.

            dx (float):
                This parameter specifies the frequency interval between data points in the spectrum.

            spectrum ([numpy.float32]):
                This parameter specifies waveform arrays.

            reset (bool):
                This parameter resets measurement averaging. If you enable averaging, set this parameter to TRUE for the first record
                and FALSE for the subsequent records.

        Returns:
            int:
                Returns the status code of this method. The status code either indicates success or describes a warning condition.
        """
        try:
            self._session_function_lock.enter_read_lock()
            _helper.validate_not_none(selector_string, "selector_string")
            _helper.validate_not_none(result_name, "result_name")
            updated_selector_string = _helper.validate_and_update_selector_string(
                selector_string, self
            )
            error_code = self._interpreter.analyze_n_waveforms_spectrum(  # type: ignore
                updated_selector_string, result_name, x0, dx, spectrum, reset
            )
        finally:
            self._session_function_lock.exit_read_lock()

        return error_code


class Wlan(_WlanBase):
    """Defines a root class which is used to identify and control Wlan signal configuration."""

    def __init__(self, session, signal_name="", cloning=False):
        """Initializes a Wlan signal configuration."""
        super(Wlan, self).__init__(
            session=session,
            signal_name=signal_name,
            cloning=cloning,
        )  # type: ignore

    def __enter__(self):
        """Enters the context of the Wlan signal configuration."""
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        """Exits the context of the Wlan signal configuration."""
        self.dispose()  # type: ignore
        pass
