"""attributes.py - Contains the ID of all attributes belongs to the module."""

from enum import Enum


class AttributeID(Enum):
    """This enum class contains the ID of all attributes belongs to the module."""

    SELECTED_PORTS = 10489853
    r"""Specifies the instrument port to be configured to acquire a signal. Use
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
    """

    CENTER_FREQUENCY = 10485761
    r"""Specifies the expected carrier frequency of the RF signal that needs to be acquired. This value is expressed in Hz. The
    signal analyzer tunes to this frequency.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    On a MIMO session, use "segment<*n*>" along with a named or default signal instance as the selector string to configure
    or read this attribute. Refer to the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
    syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    REFERENCE_LEVEL = 10485762
    r"""Specifies the reference level which represents the maximum expected power of the RF input signal. This value is
    expressed in dBm for RF devices and V\ :sub:`pk-pk`\ for baseband devices.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
    port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
    syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    EXTERNAL_ATTENUATION = 10485763
    r"""Specifies the attenuation of a switch (or cable) connected to the RF IN connector of the signal analyzer. This value is
    expressed in dB. For more information about attenuation, refer to the Attenuation and Signal Levels topic for your
    device in the *NI RF Vector Signal Analyzers Help*.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    On a MIMO session, use port::<deviceName>/<channelNumber> as a selector string to configure or read this attribute per
    port. If you do not specify port string, this attribute is configured for all ports. Refer to the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information about the string
    syntax for named signals.
    
    The default value is 0.
    """

    REFERENCE_LEVEL_HEADROOM = 10489852
    r"""Specifies the margin RFmx adds to the :py:attr:`~nirfmxwlan.attributes.AttributeID.REFERENCE_LEVEL` attribute. The
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
    """

    TRIGGER_TYPE = 10485764
    r"""Specifies the trigger type.
    
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
    """

    DIGITAL_EDGE_TRIGGER_SOURCE = 10485765
    r"""Specifies the source terminal for the digital edge trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **Digital Edge**.
    
    On a MIMO session, this attribute configures the digital edge trigger on the master port. By default, the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
    considered as the master port.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    DIGITAL_EDGE_TRIGGER_EDGE = 10485766
    r"""Specifies the active edge for the trigger. This attribute is used only when you set the
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
    """

    IQ_POWER_EDGE_TRIGGER_SOURCE = 10485767
    r"""Specifies the channel from which the device monitors the trigger. This attribute is used only when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    On a MIMO session, this attribute configures the IQ Power edge trigger on the master port. By default, the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SELECTED_PORTS` attribute is configured to "segment0/chain0" and is
    considered as the master port.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL = 10485768
    r"""Specifies the power level at which the device triggers. This value is expressed in dB when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE` attribute to **Relative** and in dBm
    when you set the IQ Power Edge Level Type attribute to **Absolute**.
    
    The device asserts the trigger when the signal exceeds the level specified by the value of this attribute,
    taking into consideration the specified slope. This attribute is used only when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_TYPE` attribute to **IQ Power Edge**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    IQ_POWER_EDGE_TRIGGER_LEVEL_TYPE = 10489855
    r"""Specifies the reference for the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_LEVEL` attribute.
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
    """

    IQ_POWER_EDGE_TRIGGER_SLOPE = 10485769
    r"""Specifies whether the device asserts the trigger when the signal power is rising or falling.
    
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
    """

    TRIGGER_DELAY = 10485770
    r"""Specifies the trigger delay time. This value is expressed in seconds.
    
    If the delay is negative, the measurement acquires pre-trigger samples. If the delay is positive, the
    measurement acquires post-trigger samples.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is RFmxWLAN measurement dependent.
    """

    TRIGGER_MINIMUM_QUIET_TIME_MODE = 10485771
    r"""Specifies whether the measurement computes the minimum quiet time used for triggering.
    
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
    """

    TRIGGER_MINIMUM_QUIET_TIME_DURATION = 10485772
    r"""Specifies the time duration for which the signal must be quiet before the signal analyzer arms the I/Q power edge
    trigger. This value is expressed in seconds.
    
    If you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.IQ_POWER_EDGE_TRIGGER_SLOPE` attribute to **Rising
    Slope**, the signal is quiet below the trigger level.  If you set the IQ Power Edge Slope attribute to **Falling
    Slope**, the signal is quiet above the trigger level.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value of this attribute is hardware dependent.
    """

    TRIGGER_GATE_ENABLED = 10485802
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
    """

    TRIGGER_GATE_LENGTH = 10485803
    r"""Specifies the maximum duration of time for each record used for computing the spectrum when you are performing an SEM
    measurement and when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TRIGGER_GATE_ENABLED` attribute to
    **True**.
    
    If the measurement interval required to perform the measurement exceeds the gate length, the measurement
    acquires as many additional records as necessary to honor the required measurement interval. This value is expressed in
    seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 millisecond.
    """

    STANDARD = 10485773
    r"""Specifies the signal under analysis as defined in *IEEE Standard 802.11*.
    
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
    """

    CHANNEL_BANDWIDTH = 10485774
    r"""Specifies the channel spacing as defined under section 3.1 of *IEEE Standard 802.11-2016 (pp. 130)*. This value is
    specified in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **20M**.
    """

    NUMBER_OF_FREQUENCY_SEGMENTS = 10485775
    r"""Specifies the number of frequency segments for 802.11ac and 802.11ax signals.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    
    Valid values are 1 and 2.
    """

    NUMBER_OF_RECEIVE_CHAINS = 10485776
    r"""Specifies the number of receive chains for OFDM standards.
    
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
    """

    OFDM_FREQUENCY_SEGMENT_INDEX = 10485780
    r"""Specifies the frequency segment index to be analyzed in an 80+80 MHz 802.11ax signal. You must set this attribute to
    either of the valid values when you want to analyze one of the two segments.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    
    The valid values are 0 and 1.
    """

    OFDM_TRANSMIT_POWER_CLASS = 10485781
    r"""Specifies the STA transmit power classification as defined in annexure D.2.2 of *IEEE Standard 802.11-2016*, if you set
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
    """

    OFDM_FREQUENCY_BAND = 10485782
    r"""Specifies the ISM frequency band. The SEM measurement uses this information to select an appropriate mask as defined in
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
    """

    OFDM_AUTO_PPDU_TYPE_DETECTION_ENABLED = 10485799
    r"""Specifies whether to enable auto detection of the PPDU type when performing the OFDMModAcc measurement.
    
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
    """

    OFDM_PPDU_TYPE = 10485783
    r"""Specifies the PPDU type when you set the
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
    """

    OFDM_HEADER_DECODING_ENABLED = 10485800
    r"""Specifies whether to enable the decoding of the header fields in the PPDU.
    
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
    """

    OFDM_SIG_COMPRESSION_ENABLED = 10485818
    r"""Specifies whether to enable SIG compression. This attribute is applicable only for 802.11be MU PPDU and 802.11bn MU
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
    """

    OFDM_NUMBER_OF_USERS = 10485784
    r"""Specifies the number of users in a multi-user (MU) PPDU.
    
    This attribute is ignored unless you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OFDM_MCS_INDEX = 10485785
    r"""Specifies the modulation and coding scheme (MCS) index or the data rate when you set the
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
    """

    OFDM_SCRAMBLER_SEED = 10485821
    r"""Specifies the scrambler seed for combined signal demodulation.  This is applicable only if
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.
    
    The default value is 93.
    """

    OFDM_FEC_CODING_TYPE = 10485810
    r"""Specifies the type of forward error correction (FEC) coding used.
    
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
    """

    OFDM_RU_SIZE = 10485786
    r"""Specifies the size of the resource unit (RU) or the multiple resource unit (MRU) in terms of number of subcarriers for
    802.11ax, 802.11be, and 802.11bn signals.
    
    You must always configure this attribute for 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU. For
    802.11ax Extended Range SU, MU, 802.11be MU and 802.11bn MU PPDUs, you must configure this attribute if the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
    802.11ax MU PPDU, 802.11ax TB PPDU, 802.11be MU PPDU, 802.11be TB PPDU, 802.11bn MU PPDU, and 802.11bn TB PPDU.
    
    The default value is **26**.
    """

    OFDM_RU_OFFSET_MRU_INDEX = 10485787
    r"""Specifies the location of RU  or MRU for a user. If an RU is configured, the RU Offset is in terms of the index of a
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
    """

    OFDM_RU_TYPE = 10485823
    r"""Specifies whether contiguous subcarriers form the resource unit (rRU) or non-contiguous subcarriers form the resource
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
    """

    OFDM_DISTRIBUTION_BANDWIDTH = 10485824
    r"""Specifies the bandwidth across which RU subcarriers are distributed, when you set
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_TYPE` attribute to  **dRU**.
    
    This attribute is only applicable for 802.11bn TB PPDU signals. You must configure this attribute if
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` is set to **False**.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is **20M**.
    """

    OFDM_GUARD_INTERVAL_TYPE = 10485788
    r"""Specifies the size of the guard interval of OFDM symbols.
    
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
    """

    OFDM_LTF_SIZE = 10485789
    r"""Specifies the LTF symbol size. This attribute is applicable only for 802.11ax, 802.11be, and 802.11bn signals.
    
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
    """

    OFDM_PRE_FEC_PADDING_FACTOR = 10485811
    r"""Specifies the pre-FEC padding factor used in 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU for decoding PLCP
    service data unit (PSDU) bits.
    
    The valid values are 1 to 4, inclusive.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OFDM_LDPC_EXTRA_SYMBOL_SEGMENT = 10485812
    r"""Specifies the presence of an extra OFDM symbol segment for LDPC in the 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn
    TB PPDU.
    
    This value is used for decoding PLCP service data unit (PSDU) bits. The valid values are 0 and 1.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    OFDM_PE_DISAMBIGUITY = 10485809
    r"""Specifies the packet extension disambiguity information.
    
    This attribute is applicable only for 802.11ax TB PPDU, 802.11be TB PPDU and 802.11bn TB PPDU.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    OFDM_STBC_ENABLED = 10485813
    r"""Specifies whether space-time block coding is enabled. This attribute is applicable only for 802.11ax TB PPDU.
    
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
    """

    OFDM_NUMBER_OF_SPACE_TIME_STREAMS = 10485790
    r"""Specifies the number of space time streams.
    
    This attribute is applicable when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **False** for 802.11n,
    802.11ac, 802.11ax, and 802.11be standards or when PPDU Type is TB for 802.11ax, 802.11be, or 802.11bn standards.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is 1.
    """

    OFDM_SPACE_TIME_STREAM_OFFSET = 10485791
    r"""Specifies the space time stream offset.
    
    This attribute is applicable only to 802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute for
    802.11ax TB PPDU, 802.11be TB PPDU, and 802.11bn TB PPDU.
    
    The default value is 0.
    """

    OFDM_NUMBER_OF_HE_SIG_B_SYMBOLS = 10485792
    r"""Specifies the number of HE-SIG-B symbols.
    
    This attribute is applicable only to 802.11ax MU PPDU signals. You must configure this attribute if the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OFDM_NUMBER_OF_SIG_SYMBOLS = 10485819
    r"""Specifies the number of SIG symbols. This attribute is applicable for 802.11be and 802.11bn MU PPDU signals.
    
    You must configure this attribute if the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OFDM_DCM_ENABLED = 10485793
    r"""Specifies whether the dual carrier modulation (DCM) is applied to the data field of the 802.11ax TB PPDU signals.
    
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
    """

    OFDM_2xLDPC_ENABLED = 10485825
    r"""Specifies whether to enable 2xLDPC for 802.11bn MU PPDU and 802.11bn TB PPDU signals.
    
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
    """

    OFDM_IM_PILOTS_ENABLED = 10485826
    r"""Specifies whether inteference mitigating pilots are present in 802.11bn MU PPDU signals.
    
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
    """

    OFDM_UNEQUAL_MODULATION_ENABLED = 10485827
    r"""Specifies whether to enable unequal modulation in different spatial streams for 802.11bn MU PPDU signals.
    
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
    """

    OFDM_UNEQUAL_MODULATION_PATTERN_INDEX = 10485828
    r"""Specifies the unequal modulation pattern for the user. Valid values are between 0 and number of space time streams-1.
    
    This attribute is applicable only to 802.11bn MU PPDU signals. You must configure this attribute if the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute is set to **False**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    OFDM_NUMBER_OF_LTF_SYMBOLS = 10485794
    r"""Specifies the number of HE-LTF, EHT-LTF, or UHR-LTF symbols in the 802.11ax TB PPDU, 802.11be or 802.11bn TB PPDU,
    respectively.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The valid values are 1, 2, 4, 6, and 8. The default value is 1.
    """

    OFDM_MU_MIMO_LTF_MODE_ENABLED = 10485801
    r"""Specifies whether the LTF sequence corresponding to each space-time stream is masked by a distinct orthogonal code.
    
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
    """

    OFDM_PREAMBLE_PUNCTURING_ENABLED = 10485807
    r"""Specifies whether the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU signal is preamble punctured.
    
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
    """

    OFDM_PREAMBLE_PUNCTURING_BITMAP = 10485808
    r"""Specifies the punctured 20 MHz sub-channels in the 802.11ax MU PPDU, the 802.11be MU PPDU or the 802.11bn MU PPDU
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
    """

    OFDM_AUTO_PHASE_ROTATION_DETECTION_ENABLED = 10485820
    r"""Specifies whether to enable auto detection of phase rotation coefficients.
    
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
    """

    OFDM_PHASE_ROTATION_COEFFICIENT_1 = 10485815
    r"""Specifies the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.
    
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
    """

    OFDM_PHASE_ROTATION_COEFFICIENT_2 = 10485816
    r"""Specifies the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.
    
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
    """

    OFDM_PHASE_ROTATION_COEFFICIENT_3 = 10485817
    r"""Specifies the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.
    
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
    """

    AUTO_DETECT_SIGNAL_DETECTED_STANDARD = 10485777
    r"""Returns the standard detected by the :py:meth:`auto_detect_signal` method.
    
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
    """

    AUTO_DETECT_SIGNAL_DETECTED_CHANNEL_BANDWIDTH = 10485778
    r"""Returns the channel bandwidth detected by the :py:meth:`auto_detect_signal`. The value is expressed in Hz.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    AUTO_DETECT_SIGNAL_DETECTED_BURST_LENGTH = 10485779
    r"""Returns the duration of the packet detected by the :py:meth:`auto_detect_signal` method. The value is expressed in
    seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    """

    DSSSMODACC_MEASUREMENT_ENABLED = 10498058
    r"""Specifies whether to enable the DSSSModAcc measurement, which is a measurement of the modulation accuracy on signals
    conforming to the DSSS PHY defined in section 15 and the High Rate DSSS PHY defined in section 16 of *IEEE Standard
    802.11-2016*.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    DSSSMODACC_ACQUISITION_LENGTH_MODE = 10498059
    r"""Specifies whether the measurement automatically computes the acquisition length of the waveform based on DSSSModAcc
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
    """

    DSSSMODACC_ACQUISITION_LENGTH = 10498060
    r"""Specifies the length of the waveform to be acquired for the DSSSModAcc measurement when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
    expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 millisecond.
    """

    DSSSMODACC_MEASUREMENT_OFFSET = 10498061
    r"""Specifies the number of data chips to be ignored from the start of the data field for the EVM computation. This value
    is expressed in chips.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    DSSSMODACC_MAXIMUM_MEASUREMENT_LENGTH = 10498062
    r"""Specifies the maximum number of data chips that the measurement uses to compute EVM. This value is expressed in chips.
    
    If you set this attribute to -1, all chips in the signal are used for measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1000.
    """

    DSSSMODACC_PULSE_SHAPING_FILTER_TYPE = 10498063
    r"""Specifies the type of pulse shaping filter used at the transmitter. This attribute is ignored when you set the
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
    """

    DSSSMODACC_PULSE_SHAPING_FILTER_PARAMETER = 10498064
    r"""Specifies the value of the filter roll-off when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_PULSE_SHAPING_FILTER_TYPE` attribute to **Raised Cosine** or
    **Root Raised Cosine**. This attribute is ignored if you set the Pulse Shaping Filter Type attribute to
    **Rectangular**.
    
    This attribute is ignored when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_EQUALIZATION_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.5.
    """

    DSSSMODACC_EQUALIZATION_ENABLED = 10498065
    r"""Specifies whether to enable equalization. The *IEEE Standard 802.11-2016* does not allow equalization for computing
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
    """

    DSSSMODACC_BURST_START_DETECTION_ENABLED = 10498170
    r"""Specifies whether the measurement detects the rising edge of a burst in the acquired waveform.
    
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
    """

    DSSSMODACC_EVM_UNIT = 10498066
    r"""Specifies the unit for the EVM results.
    
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
    """

    DSSSMODACC_POWER_MEASUREMENT_ENABLED = 10498067
    r"""Specifies whether power measurement is performed. This measurement computes power of various fields in the PPDU.
    
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
    """

    DSSSMODACC_POWER_NUMBER_OF_CUSTOM_GATES = 10498068
    r"""Specifies the number of custom gates used for power measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    DSSSMODACC_POWER_CUSTOM_GATE_START_TIME = 10498069
    r"""Specifies the start time of the custom power gate. This value is expressed in seconds.
    
    Use "gate<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    A value of 0 indicates that the start time is the start of the PPDU. The default value is 0 seconds.
    """

    DSSSMODACC_POWER_CUSTOM_GATE_STOP_TIME = 10498070
    r"""Specifies the stop time for the custom power gate. This value is expressed in seconds.
    
    Use "gate<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 10 microseconds.
    """

    DSSSMODACC_FREQUENCY_ERROR_CORRECTION_ENABLED = 10498092
    r"""Specifies whether to enable frequency error correction.
    
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
    """

    DSSSMODACC_CHIP_CLOCK_ERROR_CORRECTION_ENABLED = 10498093
    r"""Specifies whether to enable chip clock error correction.
    
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
    """

    DSSSMODACC_IQ_ORIGIN_OFFSET_CORRECTION_ENABLED = 10498094
    r"""Specifies whether to enable I/Q origin offset correction.
    
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
    """

    DSSSMODACC_SPECTRUM_INVERTED = 10498171
    r"""Specifies whether the spectrum of the measured signal is inverted.
    
    The inversion occurs when the I and the Q components of the baseband complex signal are swapped.
    
    The default value is **False**.
    
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                     |
    +==============+=================================================================================================================+
    | False (0)    | The spectrum of the measured signal is not inverted.                                                            |
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measured signal is inverted and the measurement corrects the signal by swapping the I and the Q components. |
    +--------------+-----------------------------------------------------------------------------------------------------------------+
    """

    DSSSMODACC_DATA_DECODING_ENABLED = 10498172
    r"""Specifies whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).
    
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
    """

    DSSSMODACC_AVERAGING_ENABLED = 10498095
    r"""Specifies whether to enable averaging for DSSSModAcc measurement.
    
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
    """

    DSSSMODACC_AVERAGING_COUNT = 10498096
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    DSSSMODACC_ALL_TRACES_ENABLED = 10498097
    r"""Specifies whether to enable all the traces computed by DSSSModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    """

    DSSSMODACC_NUMBER_OF_ANALYSIS_THREADS = 10498161
    r"""Specifies the maximum number of threads used for parallelism for DSSSModAcc measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    DSSSMODACC_RESULTS_RMS_EVM_MEAN = 10498098
    r"""Returns the RMS EVM of the burst. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the RMS EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PEAK_EVM_802_11_2016_MEAN = 10498108
    r"""Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.
    
    This measurement is performed in accordance with section 16.3.7.9 of *IEEE Standard 802.11-2016*.
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the peak EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PEAK_EVM_802_11_2016_MAXIMUM = 10498109
    r"""Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.
    
    This measurement is performed in accordance with section 16.3.7.9 of *IEEE Standard 802.11-2016*.
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum value of the peak EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PEAK_EVM_802_11_2007_MEAN = 10498101
    r"""Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.
    
    This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11-2007*.
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the peak EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PEAK_EVM_802_11_2007_MAXIMUM = 10498102
    r"""Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.
    
    This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11-2007*.
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum value of the peak EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PEAK_EVM_802_11_1999_MEAN = 10498099
    r"""Returns the peak EVM of the burst. This value is expressed as a percentage or in dB.
    
    This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11b-1999*.
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute is set to
    **True**, this result returns the mean of the peak EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PEAK_EVM_802_11_1999_MAXIMUM = 10498100
    r"""Returns the peak EVM of the burst. This value is expressed as percentage or in dB.
    
    This measurement is performed in accordance with section 18.4.7.8 of *IEEE Standard 802.11b-1999*.
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum of the peak EVM computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_NUMBER_OF_CHIPS_USED = 10498125
    r"""Returns the number of chips used for the DSSSModAcc measurement.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_FREQUENCY_ERROR_MEAN = 10498126
    r"""Returns the carrier frequency error of the transmitter. This value is expressed in Hz.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the carrier frequency error computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_CHIP_CLOCK_ERROR_MEAN = 10498130
    r"""Returns the chip clock error of the transmitter. This value is expressed in parts per million (ppm).
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the chip clock error computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_IQ_GAIN_IMBALANCE_MEAN = 10498131
    r"""Returns the I/Q gain imbalance. This value is expressed in dB.
    
    I/Q gain imbalance is the ratio of the mean amplitude of the in-phase (I) signal to the mean amplitude of the
    quadrature-phase (Q) signal. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result returns
    the mean of the I/Q gain imbalance computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_IQ_QUADRATURE_ERROR_MEAN = 10498135
    r"""Returns the I/Q quadrature error. This value is expressed in degrees.
    
    Quadrature error is the deviation in angle from 90 degrees between the in-phase (I) and quadrature-phase (Q)
    signals. When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the I/Q quadrature error computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_IQ_ORIGIN_OFFSET_MEAN = 10498139
    r"""Returns the I/Q origin offset. This value is expressed in dB.
    
    I/Q origin offset is the ratio of the mean value of the signal to the RMS value of the signal. When you set
    this :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to **True**, this result
    returns the mean of the I/Q origin offset computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_RMS_MAGNITUDE_ERROR_MEAN = 10498146
    r"""Returns the RMS magnitude error of the received constellation, which is the RMS level of the one minus the magnitude
    error of the received constellation symbols. This value is expressed as a percentage.
    
    When you set this :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the RMS magnitude error computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_RMS_PHASE_ERROR_MEAN = 10498147
    r"""Returns the RMS phase error of the received constellation, which is the RMS level of difference between the ideal and
    the actual values of the phase of the received constellation symbols. This value is expressed in degrees.
    
    When you set this :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the RMS phase error computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PREAMBLE_AVERAGE_POWER_MEAN = 10498162
    r"""Returns the average power of the preamble field of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the average preamble field power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PREAMBLE_PEAK_POWER_MAXIMUM = 10498163
    r"""Returns the peak power of the preamble field of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum of the peak preamble field power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_HEADER_AVERAGE_POWER_MEAN = 10498164
    r"""Returns the average power of the header field of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the average header field power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_HEADER_PEAK_POWER_MAXIMUM = 10498165
    r"""Returns the peak power of the header field of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum value of the peak header field power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_DATA_AVERAGE_POWER_MEAN = 10498166
    r"""Returns the average power of the data field of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the average data field power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_DATA_PEAK_POWER_MAXIMUM = 10498167
    r"""Returns the peak power of the data field of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum value of the peak data field power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PPDU_AVERAGE_POWER_MEAN = 10498168
    r"""Returns the average power of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean of the average PPDU power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PPDU_PEAK_POWER_MAXIMUM = 10498169
    r"""Returns the peak power of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum value of the peak PPDU power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_CUSTOM_GATE_AVERAGE_POWER_MEAN = 10498110
    r"""Returns the average power of the custom gate. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the mean value of the average custom gate power computed for each averaging count.
    
    Use "gate<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read the result.
    """

    DSSSMODACC_RESULTS_CUSTOM_GATE_PEAK_POWER_MAXIMUM = 10498111
    r"""Returns the peak power of the custom gate. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.DSSSMODACC_AVERAGING_ENABLED` attribute to
    **True**, this result returns the maximum value of the peak custom gate power computed for each averaging count.
    
    Use "gate<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to query the result.
    """

    DSSSMODACC_RESULTS_DATA_MODULATION_FORMAT = 10498152
    r"""Returns the data modulation format results of the analyzed waveform.
    
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
    """

    DSSSMODACC_RESULTS_PAYLOAD_LENGTH = 10498153
    r"""Returns the payload length of the acquired burst. This value is expressed in bytes.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_PREAMBLE_TYPE = 10498154
    r"""Returns the detected preamble type of the acquired burst.
    
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
    """

    DSSSMODACC_RESULTS_LOCKED_CLOCKS_BIT = 10498156
    r"""Returns the value of the locked clocks bit in the Long PHY SERVICE field.
    
    A value of 1 indicates that the transmit frequency and the symbol clock are derived from the same oscillator. A
    value of 0 indicates that the transmit frequency and the symbol clock are derived from independent oscillators.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    DSSSMODACC_RESULTS_HEADER_CRC_STATUS = 10498157
    r"""Returns whether the header cyclic redundancy check (CRC) is successfully passed, as defined in section 16.2.3.7 of
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
    """

    DSSSMODACC_RESULTS_PSDU_CRC_STATUS = 10498158
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
    """

    OFDMMODACC_MEASUREMENT_ENABLED = 10502144
    r"""Specifies whether to enable OFDMModAcc measurement for OFDM based standards.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    OFDMMODACC_AVERAGING_ENABLED = 10502146
    r"""Specifies whether to enable averaging for OFDMModAcc measurements.
    
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
    """

    OFDMMODACC_AVERAGING_COUNT = 10502147
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    OFDMMODACC_AVERAGING_TYPE = 10502316
    r"""Specifies the averaging type for the OFDMModAcc measurement.
    
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
    """

    OFDMMODACC_VECTOR_AVERAGING_TIME_ALIGNMENT_ENABLED = 10502317
    r"""Specifies whether to enable time alignment for the acquired I/Q data across multiple acquisitions.
    
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
    """

    OFDMMODACC_VECTOR_AVERAGING_PHASE_ALIGNMENT_ENABLED = 10502318
    r"""Specifies whether to enable phase alignment for the acquired I/Q data across multiple acquisitions.
    
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
    """

    OFDMMODACC_MEASUREMENT_MODE = 10502246
    r"""Specifies whether the measurement calibrates the noise floor of analyzer or performs the ModAcc measurement.
    
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
    """

    OFDMMODACC_EVM_REFERENCE_DATA_SYMBOLS_MODE = 10502291
    r"""Specifies whether to use an acquired waveform or a reference waveform to create reference data symbols (ideal
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
    """

    OFDMMODACC_EVM_UNIT = 10502152
    r"""Specifies the unit for EVM results.
    
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
    """

    OFDMMODACC_ACQUISITION_LENGTH_MODE = 10502153
    r"""Specifies whether the measurement automatically computes the acquisition length of the waveform based on other
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
    """

    OFDMMODACC_ACQUISITION_LENGTH = 10502154
    r"""Specifies the length of the waveform to be acquired for the OFDMModAcc measurement, when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_ACQUISITION_LENGTH_MODE` attribute to **Manual**. This value is
    expressed in seconds.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 millisecond.
    """

    OFDMMODACC_MEASUREMENT_OFFSET = 10502155
    r"""Specifies the number of data symbols to be ignored from the start of the data field for EVM computation. This value is
    expressed in symbols.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    OFDMMODACC_MAXIMUM_MEASUREMENT_LENGTH = 10502156
    r"""Specifies the maximum number of OFDM symbols that the measurement uses to compute EVM. This value is expressed in
    symbols.
    
    If the number of available data symbols (*n*) is greater than the value that you specify (*m*), the measurement
    ignores (*n*-*m*) symbols from the end of the data field. If you set this attribute to -1, all symbols in the data
    field are used to compute the EVM.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 16.
    """

    OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED = 10502346
    r"""Specifies whether to enable demodulation of the signal that is formed by combining signals from multiple transmitter
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
    """

    OFDMMODACC_REFERENCE_DATA_CONSTELLATION_IDENTIFIER = 10502347
    r"""Identifies the reference files used for combined signal demodulation. The value of this attribute must be same as the
    value of the Reference Data Identifier string specified while creating the reference files. This is applicable only if
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.
    
    The default value is "" (empty string).
    """

    OFDMMODACC_BURST_START_DETECTION_ENABLED = 10502277
    r"""Specifies whether the measurement detects a rising edge of a burst in the acquired waveform.
    
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
    """

    OFDMMODACC_FREQUENCY_ERROR_ESTIMATION_METHOD = 10502270
    r"""Specifies the PPDU fields that the measurement uses to estimate the carrier frequency error in the acquired signal.
    
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
    """

    OFDMMODACC_COMMON_CLOCK_SOURCE_ENABLED = 10502157
    r"""Specifies whether the transmitter uses the same reference clock signal for generating the RF carrier and the symbol
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
    """

    OFDMMODACC_COMMON_PILOT_ERROR_SCALING_REFERENCE = 10502353
    r"""Specifies whether common pilot error is computed relative to only  LTF  or scaling by average CPE.
    
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
    """

    OFDMMODACC_AMPLITUDE_TRACKING_ENABLED = 10502158
    r"""Specifies whether to enable pilot-based mean amplitude tracking per OFDM data symbol.
    
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
    """

    OFDMMODACC_PHASE_TRACKING_ENABLED = 10502159
    r"""Specifies whether to enable pilot-based common phase error correction per OFDM data symbol.
    
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
    """

    OFDMMODACC_SYMBOL_CLOCK_ERROR_CORRECTION_ENABLED = 10502160
    r"""Specifies whether to enable symbol clock error correction.
    
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
    """

    OFDMMODACC_SPECTRUM_INVERTED = 10502266
    r"""Specifies whether the spectrum of the measured signal is inverted. The inversion happens when the I and the Q
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
    """

    OFDMMODACC_CHANNEL_ESTIMATION_TYPE = 10502161
    r"""Specifies the fields in the PPDU used to estimate the channel frequency response.
    
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
    """

    OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE = 10502250
    r"""Specifies the interpolation type and/or smoothing type used on the channel estimates.
    
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
    """

    OFDMMODACC_CHANNEL_ESTIMATION_SMOOTHING_LENGTH = 10502251
    r"""Specifies the length of the triangular-weighted moving window across subcarriers that is used for averaging the channel
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
    """

    OFDMMODACC_CHANNEL_ESTIMATION_RELATIVE_DELAY_SPREAD = 10502327
    r"""Specifies the expected channel delay spread relative to the OFDM symbol length.
    
    The entire symbol length is considered as 1 and the value of this attribute is specified as a fraction of 1.
    This attribute is used only when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_CHANNEL_ESTIMATION_INTERPOLATION_TYPE` attribute to **Wiener
    Filter**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.125. Valid values are from 0 to 0.25, inclusive.
    """

    OFDMMODACC_CHANNEL_ESTIMATION_LTF_AVERAGING_ENABLED = 10502368
    r"""Specifies whether to average multiple Long Training Field (LTF) symbols to improve channel estimation. This attribute
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
    """

    OFDMMODACC_CHANNEL_ESTIMATION_L_LTF_ENABLED = 10502279
    r"""Specifies whether to use the legacy channel estimation field for combining with the reference channel frequency
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
    """

    OFDMMODACC_POWER_MEASUREMENT_ENABLED = 10502167
    r"""Specifies whether power measurements are performed.
    
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
    """

    OFDMMODACC_POWER_NUMBER_OF_CUSTOM_GATES = 10502168
    r"""Specifies the number of custom gates for power measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    OFDMMODACC_POWER_CUSTOM_GATE_START_TIME = 10502169
    r"""Specifies the start time of the custom power gate. This value is expressed in seconds.
    
    A value of 0 indicates that the start time is the start of the PPDU.
    
    Use "gate<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure or read this attribute.
    
    The default value is 0.
    """

    OFDMMODACC_POWER_CUSTOM_GATE_STOP_TIME = 10502170
    r"""Specifies the stop time of the custom power gate, and must be greater than the corresponding
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_POWER_CUSTOM_GATE_START_TIME` attribute. This value is
    expressed in seconds.
    
    Use "gate<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is 10 microseconds.
    """

    OFDMMODACC_CHANNEL_MATRIX_POWER_ENABLED = 10502285
    r"""Specifies whether the channel frequency response matrix power measurements are enabled. This enables cross-power
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
    """

    OFDMMODACC_IQ_IMPAIRMENTS_ESTIMATION_ENABLED = 10502267
    r"""Specifies whether to enable the estimation of I/Q gain imbalance, I/Q quadrature error, and I/Q timing skew
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
    """

    OFDMMODACC_IQ_IMPAIRMENTS_MODEL = 10502171
    r"""Specifies the I/Q impairments model used by the measurement for estimating I/Q impairments.
    
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
    """

    OFDMMODACC_IQ_GAIN_IMBALANCE_CORRECTION_ENABLED = 10502172
    r"""Specifies whether to enable I/Q gain imbalance correction.
    
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
    """

    OFDMMODACC_IQ_QUADRATURE_ERROR_CORRECTION_ENABLED = 10502173
    r"""Specifies whether to enable I/Q quadrature error correction.
    
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
    """

    OFDMMODACC_IQ_TIMING_SKEW_CORRECTION_ENABLED = 10502174
    r"""Specifies whether to enable I/Q timing skew correction.
    
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
    """

    OFDMMODACC_IQ_IMPAIRMENTS_PER_SUBCARRIER_ENABLED = 10502271
    r"""Specifies whether to estimate I/Q impairments independently for each subcarrier.
    
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
    """

    OFDMMODACC_UNUSED_TONE_ERROR_MASK_REFERENCE = 10502252
    r"""Specifies the reference used to create the unused tone error mask for the 802.11ax, 802.11be or 802.11bn TB PPDU
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
    """

    OFDMMODACC_DATA_DECODING_ENABLED = 10502283
    r"""Specifies whether to decode data bits and check for the validity of the cyclic redundancy check (CRC).
    
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
    """

    OFDMMODACC_NOISE_COMPENSATION_ENABLED = 10502247
    r"""Specifies whether the contribution of the instrument noise is compensated for EVM computation.
    
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
    """

    OFDMMODACC_NOISE_COMPENSATION_INPUT_POWER_CHECK_ENABLED = 10502248
    r"""Specifies whether the measurement checks if any high power signal is present at the RFIn port of the instrument while
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
    """

    OFDMMODACC_NOISE_COMPENSATION_REFERENCE_LEVEL_COERCION_LIMIT = 10502249
    r"""Specifies the reference level coercion limit for noise compensation. This value is expressed in dB.
    
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
    """

    OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED = 10502268
    r"""Specifies whether to optimize the analyzer's dynamic range for the EVM measurement.
    
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
    """

    OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_MARGIN = 10502269
    r"""Specifies the margin above the reference level you specify when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_OPTIMIZE_DYNAMIC_RANGE_FOR_EVM_ENABLED` attribute to **True**.
    This value is expressed in dB.
    
    When the property's value 0, the dynamic range is optimized. When you set a positive value to the attribute,
    the dynamic range reduces from the optimized dynamic range. You can use this attribute to avoid ADC and onboard signal
    processing (OSP) overflows.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 0.
    """

    OFDMMODACC_AUTO_LEVEL_ALLOW_OVERFLOW = 10502321
    r"""Specifies whether the :py:meth:`auto_level` method should search for the optimum reference levels while allowing ADC
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
    """

    OFDMMODACC_ALL_TRACES_ENABLED = 10502149
    r"""Specifies whether to enable all the traces computed by the OFDMModAcc measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    OFDMMODACC_NUMBER_OF_ANALYSIS_THREADS = 10502148
    r"""Specifies the maximum number of threads used for parallelism for the OFDMModAcc measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    OFDMMODACC_RESULTS_COMPOSITE_RMS_EVM_MEAN = 10502254
    r"""Returns the RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_COMPOSITE_DATA_RMS_EVM_MEAN = 10502255
    r"""Returns the RMS EVM of data-subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of data RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_COMPOSITE_PILOT_RMS_EVM_MEAN = 10502256
    r"""Returns the RMS EVM of pilot-subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute is set to
    **True**, this attribute returns the mean of pilot RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_STREAM_RMS_EVM_MEAN = 10502260
    r"""Returns the stream RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of stream RMS EVM results computed for each averaging count.
    
    Use "segment<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_STREAM_RMS_EVM_MAXIMUM = 10502294
    r"""
    """

    OFDMMODACC_RESULTS_STREAM_RMS_EVM_MINIMUM = 10502295
    r"""
    """

    OFDMMODACC_RESULTS_STREAM_DATA_RMS_EVM_MEAN = 10502261
    r"""Returns the stream RMS EVM of data subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of data stream RMS EVM results computed for each averaging count.
    
    Use "segment<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_STREAM_PILOT_RMS_EVM_MEAN = 10502262
    r"""Returns the stream RMS EVM of pilot subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of pilot stream RMS EVM results computed for each averaging count.
    
    Use "segment<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MEAN = 10502257
    r"""Returns the chain RMS EVM of all subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of chain RMS EVM results computed for each averaging count.
    
    Use "segment<*n*>/chain<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MAXIMUM = 10502296
    r"""
    """

    OFDMMODACC_RESULTS_CHAIN_RMS_EVM_MINIMUM = 10502297
    r"""
    """

    OFDMMODACC_RESULTS_CHAIN_DATA_RMS_EVM_MEAN = 10502258
    r"""Returns the chain RMS EVM of data subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of data chain RMS EVM results computed for each averaging count.
    
    Use "segment<*n*>/chain<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_CHAIN_PILOT_RMS_EVM_MEAN = 10502259
    r"""Returns the chain RMS EVM of pilot subcarriers in all OFDM symbols. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of pilot chain RMS EVM results computed for each averaging count.
    
    Use "segment<*n*>/chain<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_USER_STREAM_RMS_EVM_MEAN = 10502263
    r"""Returns the RMS EVM of all subcarriers in all OFDM symbols for the specified user. This value is expressed as a
    percentage or in dB.
    
    This result is applicable for MU PPDU. When you set
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of RMS EVM results for the specified user that is computed for each averaging count.
    
    Use "user<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_USER_STREAM_RMS_EVM_MAXIMUM = 10502298
    r"""
    """

    OFDMMODACC_RESULTS_USER_STREAM_RMS_EVM_MINIMUM = 10502299
    r"""
    """

    OFDMMODACC_RESULTS_USER_STREAM_DATA_RMS_EVM_MEAN = 10502264
    r"""Returns the RMS EVM of data-subcarriers in all OFDM symbols for the specified user. This value is expressed as a
    percentage or in dB.
    
    This result is applicable for MU PPDU. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of data RMS EVM results for the specified user that is computed for each averaging count.
    
    Use "user<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_USER_STREAM_PILOT_RMS_EVM_MEAN = 10502265
    r"""Returns the RMS EVM of pilot-subcarriers in all OFDM symbols for the specified user. This value is expressed as a
    percentage or in dB.
    
    This result is applicable for MU PPDU. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of pilot RMS EVM results for the specified user that is computed for each averaging count.
    
    Use "user<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_L_SIG_RMS_EVM_MEAN = 10502331
    r"""Returns the RMS EVM of subcarriers in the L-SIG symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_SIG_RMS_EVM_MEAN = 10502332
    r"""Returns the RMS EVM of subcarriers in the SIG symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_SIG_B_RMS_EVM_MEAN = 10502333
    r"""Returns the RMS EVM of subcarriers in the SIG-B symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_U_SIG_RMS_EVM_MEAN = 10502334
    r"""Returns the RMS EVM of subcarriers in the U-SIG symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_EHT_SIG_RMS_EVM_MEAN = 10502335
    r"""Returns the RMS EVM of subcarriers in the EHT-SIG symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_UHR_SIG_RMS_EVM_MEAN = 10502354
    r"""Returns the RMS EVM of subcarriers in the UHR-SIG symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_ELR_SIG_RMS_EVM_MEAN = 10502356
    r"""Returns the RMS EVM of subcarriers in the ELR-SIG symbol. This value is expressed as a percentage or in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of RMS EVM results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_L_STF_AVERAGE_POWER_MEAN = 10502202
    r"""Returns the average power of the L-STF or STF field. This value is expressed in dBm.
    
    This result is not applicable for 802.11n greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the L-STF or STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_L_STF_PEAK_POWER_MAXIMUM = 10502203
    r"""Returns the peak power of the L-STF or STF field. This value is expressed in dBm.
    
    This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the L-STF or STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_L_LTF_AVERAGE_POWER_MEAN = 10502204
    r"""Returns the average power of the L-LTF or LTF field. This value is expressed in dBm.
    
    This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the L-LTF or LTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_L_LTF_PEAK_POWER_MAXIMUM = 10502205
    r"""Returns the peak power of the L-LTF or LTF field. This value is expressed in dBm.
    
    This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the L-LTF or LTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_L_SIG_AVERAGE_POWER_MEAN = 10502206
    r"""Returns the average power of the L-SIG or SIGNAL field. This value is expressed in dBm.
    
    This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the L-SIG or SIGNAL field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_L_SIG_PEAK_POWER_MAXIMUM = 10502207
    r"""Returns the peak power of the L-SIG or SIGNAL field. This value is expressed in dBm.
    
    This result is not applicable for 802.11n Greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the L-SIG or SIGNAL field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_RL_SIG_AVERAGE_POWER_MEAN = 10502208
    r"""Returns the average power of the RL-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax and 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the RL-SIG field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_RL_SIG_PEAK_POWER_MAXIMUM = 10502209
    r"""Returns the peak power of the RL-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax and 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the RL-SIG field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_SIG_AVERAGE_POWER_MEAN = 10502210
    r"""Returns the average power of the HT-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HT-SIG field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_SIG_PEAK_POWER_MAXIMUM = 10502211
    r"""Returns the peak power of the HT-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HT-SIG field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_SIG_A_AVERAGE_POWER_MEAN = 10502212
    r"""Returns the average power of the VHT-SIG-A field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the VHT-SIG-A field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_SIG_A_PEAK_POWER_MAXIMUM = 10502213
    r"""Returns the peak power of the VHT-SIG-A field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the VHT-SIG-A field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_SIG_A_AVERAGE_POWER_MEAN = 10502214
    r"""Returns the average power of the HE-SIG-A field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HE-SIG-A field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_SIG_A_PEAK_POWER_MAXIMUM = 10502215
    r"""Returns the peak power of the HE-SIG-A field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HE-SIG-A field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_U_SIG_AVERAGE_POWER_MEAN = 10502336
    r"""Returns the average power of the U-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the U-SIG field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_U_SIG_PEAK_POWER_MAXIMUM = 10502337
    r"""Returns the peak power of the U-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the U-SIG field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_ELR_MARK_AVERAGE_POWER_MEAN = 10502366
    r"""Returns the average power of the ELR-MARK field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the ELR-MARK field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_ELR_MARK_PEAK_POWER_MAXIMUM = 10502367
    r"""Returns the peak power of the ELR-MARK field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the ELR-MARK field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_SIG_B_AVERAGE_POWER_MEAN = 10502216
    r"""Returns the average power of the VHT-SIG-B field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the VHT-SIG-B field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_SIG_B_PEAK_POWER_MAXIMUM = 10502217
    r"""Returns the peak power of the VHT-SIG-B field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the VHT-SIG-B field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_SIG_B_AVERAGE_POWER_MEAN = 10502218
    r"""Returns the average power of the HE-SIG-B field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HE-SIG-B field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_SIG_B_PEAK_POWER_MAXIMUM = 10502219
    r"""Returns the peak power of the HE-SIG-B field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HE-SIG-B field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_EHT_SIG_AVERAGE_POWER_MEAN = 10502338
    r"""Returns the average power of the EHT-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the EHT-SIG field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_EHT_SIG_PEAK_POWER_MAXIMUM = 10502339
    r"""Returns the peak power of the EHT-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the EHT-SIG field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_UHR_SIG_AVERAGE_POWER_MEAN = 10502362
    r"""Returns the average power of the UHR-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the UHR-SIG field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_UHR_SIG_PEAK_POWER_MAXIMUM = 10502363
    r"""Returns the peak power of the UHR-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the UHR-SIG field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_ELR_SIG_AVERAGE_POWER_MEAN = 10502364
    r"""Returns the average power of the ELR-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the ELR-SIG field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_ELR_SIG_PEAK_POWER_MAXIMUM = 10502365
    r"""Returns the peak power of the ELR-SIG field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the ELR-SIG field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_STF_AVERAGE_POWER_MEAN = 10502220
    r"""Returns the average power of the HT-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HT-STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_STF_PEAK_POWER_MAXIMUM = 10502221
    r"""Returns the peak power of the HT-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HT-STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_GF_STF_AVERAGE_POWER_MEAN = 10502222
    r"""Returns the average power of the HT-GF-STF. This value is expressed in dBm.
    
    This result is applicable only to 802.11n greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HT-GF-STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_GF_STF_PEAK_POWER_MAXIMUM = 10502223
    r"""Returns the peak power of the HT-GF-STF. This value is expressed in dBm.
    
    This result is applicable only to 802.11n greenfield PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HT-GF-STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_STF_AVERAGE_POWER_MEAN = 10502224
    r"""Returns the average power of the VHT-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the VHT-STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_STF_PEAK_POWER_MAXIMUM = 10502225
    r"""Returns the peak power of the VHT-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the VHT-STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_STF_AVERAGE_POWER_MEAN = 10502226
    r"""Returns the average power of the HE-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HE-STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_STF_PEAK_POWER_MAXIMUM = 10502227
    r"""Returns the peak power of the HE-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HE-STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_EHT_STF_AVERAGE_POWER_MEAN = 10502340
    r"""Returns the average power of the EHT-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the EHT-STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_EHT_STF_PEAK_POWER_MAXIMUM = 10502341
    r"""Returns the peak power of the EHT-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the EHT-STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_UHR_STF_AVERAGE_POWER_MEAN = 10502358
    r"""Returns the average power of the UHR-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the UHR-STF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_UHR_STF_PEAK_POWER_MAXIMUM = 10502359
    r"""Returns the peak power of the UHR-STF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the UHR-STF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_DLTF_AVERAGE_POWER_MEAN = 10502228
    r"""Returns the average power of the HT-DLTF. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HT-DLTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_DLTF_PEAK_POWER_MAXIMUM = 10502229
    r"""Returns the peak power of the HT-DLTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HT-DLTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_ELTF_AVERAGE_POWER_MEAN = 10502230
    r"""Returns the average power of the HT-ELTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HT-ELTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HT_ELTF_PEAK_POWER_MAXIMUM = 10502231
    r"""Returns the peak power of the HT-ELTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11n signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HT-ELTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_LTF_AVERAGE_POWER_MEAN = 10502232
    r"""Returns the average power of the VHT-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the VHT-LTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_VHT_LTF_PEAK_POWER_MAXIMUM = 10502233
    r"""Returns the peak power of the VHT-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ac signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the VHT-LTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_LTF_AVERAGE_POWER_MEAN = 10502234
    r"""Returns the average power of the HE-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the HE-LTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_HE_LTF_PEAK_POWER_MAXIMUM = 10502235
    r"""Returns the peak power of the HE-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the HE-LTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_EHT_LTF_AVERAGE_POWER_MEAN = 10502342
    r"""Returns the average power of the EHT-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the EHT-LTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_EHT_LTF_PEAK_POWER_MAXIMUM = 10502343
    r"""Returns the peak power of the EHT-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the EHT-LTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_UHR_LTF_AVERAGE_POWER_MEAN = 10502360
    r"""Returns the average power of the UHR-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the UHR-LTF average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_UHR_LTF_PEAK_POWER_MAXIMUM = 10502361
    r"""Returns the peak power of the UHR-LTF field. This value is expressed in dBm.
    
    This result is applicable only to 802.11bn signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the UHR-LTF peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_DATA_AVERAGE_POWER_MEAN = 10502236
    r"""Returns the average power of the data field. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the data field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_DATA_PEAK_POWER_MAXIMUM = 10502237
    r"""Returns the peak power of the data field. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the maximum of the data field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_PE_AVERAGE_POWER_MEAN = 10502238
    r"""Returns the average power of the packet extension field. This value is expressed in dBm.
    
    This result is applicable for 802.11ax and 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the packet extension field average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_PE_PEAK_POWER_MAXIMUM = 10502239
    r"""Returns the peak power of the packet extension field. This value is expressed in dBm.
    
    This result is applicable only to 802.11ax and 802.11be signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the maximum of the PE  field peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_PPDU_AVERAGE_POWER_MEAN = 10502240
    r"""Returns the average power of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the PPDU average power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_PPDU_PEAK_POWER_MAXIMUM = 10502241
    r"""Returns the peak power of the PPDU. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the maximum of the PPDU peak power results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_POWER_CUSTOM_GATE_AVERAGE_POWER_MEAN = 10502242
    r"""Returns the average power of the custom gate. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the custom gate average power results computed for each averaging count.
    
    Use "gate<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_POWER_CUSTOM_GATE_PEAK_POWER_MAXIMUM = 10502243
    r"""Returns the peak power of the custom gate. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the maximum of the custom gate peak power results computed for each averaging count.
    
    Use "gate<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_CROSS_POWER_MEAN = 10502286
    r"""Returns the cross power. The cross power for chain *x* is the power contribution from streams other than stream *x* in
    the chain. This value is expressed in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the cross power results computed for each averaging count.
    
    Use "segment<*n*>/chain<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_USER_POWER_MEAN = 10502287
    r"""Returns the user power. User power is the frequency domain power measured over subcarriers occupied by a given user.
    This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the user power results computed for each averaging count.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_USER_POWER_MAXIMUM = 10502300
    r"""
    """

    OFDMMODACC_RESULTS_USER_POWER_MINIMUM = 10502301
    r"""
    """

    OFDMMODACC_RESULTS_STREAM_POWER_MEAN = 10502348
    r"""Returns average stream power across iterations for combined signal demodulation. This is applicable only if
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_COMBINED_SIGNAL_DEMODULATION_ENABLED` is set to **True**.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of stream power results computed for each averaging count.
    
    Use "segment<*n*>/stream<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN = 10502179
    r"""Returns the spectral flatness margin, which is the minimum of the upper and lower spectral flatness margins. This value
    is expressed in dB.
    
    The upper spectral flatness margin is the minimum difference between the upper mask and the spectral flatness
    across subcarriers. The lower spectral flatness margin is the minimum difference between the spectral flatness and the
    lower mask across subcarriers. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, the spectral flatness
    is computed using the mean of the channel frequency response magnitude computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_MAXIMUM = 10502302
    r"""
    """

    OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_MINIMUM = 10502303
    r"""
    """

    OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN_SUBCARRIER_INDEX = 10502180
    r"""Returns the subcarrier index corresponding to the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_SPECTRAL_FLATNESS_MARGIN` result.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN = 10502181
    r"""Returns the unused tone error margin, which is the minimum difference between the unused tone error mask and the unused
    tone error across 26-tone RUs. This value is expressed in dB.
    
    This result is applicable only to 802.11ax, 802.11be and 802.11bn TB PPDU signals. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, the measurement
    computes the mean of the unused tone error over each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN_RU_INDEX = 10502182
    r"""Returns the 26-tone RU index corresponding to the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_RESULTS_UNUSED_TONE_ERROR_MARGIN`  result.
    
    This result is applicable for 802.11ax, 802.11be and 802.11bn TB PPDU signals.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_BURST_START_TIME_MEAN = 10502320
    r"""Returns the absolute time corresponding to the detected start of the analyzed burst. The start time is computed with
    respect to the initial time value of the acquired waveform. This value is expressed in seconds.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**,
    this attribute returns the mean of the burst start time computed for each averaging count.
    
    Use "segment<*n*>/chain<*k*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_NUMBER_OF_SYMBOLS_USED = 10502166
    r"""Returns the number of OFDM symbols used by the measurement.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_NOISE_COMPENSATION_APPLIED = 10502183
    r"""Returns whether the noise compensation is applied.
    
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
    """

    OFDMMODACC_RESULTS_FREQUENCY_ERROR_MEAN = 10502184
    r"""Returns the carrier frequency error of the transmitter. This value is expressed in Hz.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the carrier frequency error results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_FREQUENCY_ERROR_MAXIMUM = 10502304
    r"""
    """

    OFDMMODACC_RESULTS_FREQUENCY_ERROR_MINIMUM = 10502305
    r"""
    """

    OFDMMODACC_RESULTS_FREQUENCY_ERROR_CCDF_10_PERCENT = 10502185
    r"""Returns the 10% point of Complementary Cumulative Distribution Function (CCDF) of the absolute frequency error. This
    value is expressed in Hz.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, the CCDF is computed over each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_SYMBOL_CLOCK_ERROR_MEAN = 10502186
    r"""Returns the symbol clock error of the transmitter.
    
    Symbol clock error is the difference between the symbol clocks at the digital-to-analog converter (DAC) of the
    transmitting device under test (DUT) and the digitizer of the instrument. This value is expressed in parts per million
    (ppm).
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the symbol clock error results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_SYMBOL_CLOCK_ERROR_MAXIMUM = 10502306
    r"""
    """

    OFDMMODACC_RESULTS_SYMBOL_CLOCK_ERROR_MINIMUM = 10502307
    r"""
    """

    OFDMMODACC_RESULTS_RELATIVE_IQ_ORIGIN_OFFSET_MEAN = 10502187
    r"""Returns the relative I/Q origin offset, which is the ratio of the power of the DC subcarrier to the total power of all
    the subcarriers. This value is expressed in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the relative I/Q origin offset computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_RELATIVE_IQ_ORIGIN_OFFSET_MAXIMUM = 10502308
    r"""
    """

    OFDMMODACC_RESULTS_RELATIVE_IQ_ORIGIN_OFFSET_MINIMUM = 10502309
    r"""
    """

    OFDMMODACC_RESULTS_ABSOLUTE_IQ_ORIGIN_OFFSET_MEAN = 10502188
    r"""Returns the absolute I/Q origin offset, which is the power of the DC subcarrier. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the absolute I/Q origin offset computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_IQ_GAIN_IMBALANCE_MEAN = 10502189
    r"""Returns the I/Q gain imbalance, which is the ratio of the RMS amplitude of the in-phase (I) component of the signal to
    the RMS amplitude of the quadrature-phase (Q) component of the signal. This value is expressed in dB.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the I/Q gain imbalance results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_IQ_GAIN_IMBALANCE_MAXIMUM = 10502310
    r"""
    """

    OFDMMODACC_RESULTS_IQ_GAIN_IMBALANCE_MINIMUM = 10502311
    r"""
    """

    OFDMMODACC_RESULTS_IQ_QUADRATURE_ERROR_MEAN = 10502190
    r"""Returns the I/Q quadrature error, which is a measure of deviation of the phase difference between the quadrature-phase
    (Q) and the in-phase (I) component of the signal from 90 degrees. This value is expressed in degrees.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the I/Q quadrature error results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_IQ_QUADRATURE_ERROR_MAXIMUM = 10502312
    r"""
    """

    OFDMMODACC_RESULTS_IQ_QUADRATURE_ERROR_MINIMUM = 10502313
    r"""
    """

    OFDMMODACC_RESULTS_IQ_TIMING_SKEW_MEAN = 10502191
    r"""Returns the I/Q timing skew, which is the difference between the group delay of the in-phase (I) and quadrature (Q)
    components of the signal. This value is expressed in seconds.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the I/Q timing skew computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_RMS_COMMON_PHASE_ERROR_MEAN = 10502192
    r"""Returns the RMS common phase error.
    
    Common phase error for an OFDM symbol is the average phase deviation of the pilot-subcarriers from their ideal
    phase. RMS Common Phase Error is the RMS of common phase error of all OFDM symbols. When you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the RMS common phase error computed for each averaging count.
    
    Refer to `Common Pilot Error <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/common-pilot-error.html>`_ for more
    information.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_RMS_COMMON_PILOT_ERROR_MEAN = 10502253
    r"""Returns the RMS common pilot error. This value is expressed as a percentage.
    
    Common pilot error for an OFDM symbol is the correlation of the received pilot subcarrier QAM symbols with
    their ideal values. RMS Common Pilot Error is the RMS of 1 minus common pilot error for all OFDM symbols. When you set
    the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDMMODACC_AVERAGING_ENABLED` attribute to **True**, this attribute
    returns the mean of the RMS common pilot error computed for each averaging count.
    
    Refer to `Common Pilot Error <www.ni.com/docs/en-US/bundle/rfmx-wlan/page/common-pilot-error.html>`_ for more
    information.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_PPDU_TYPE = 10502193
    r"""Returns the PPDU type of the measured signal.
    
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
    """

    OFDMMODACC_RESULTS_MCS_INDEX = 10502194
    r"""Returns the MCS index or the data rate of the measured signal.
    
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
    """

    OFDMMODACC_RESULTS_AGGREGATION = 10502345
    r"""Returns the value of the Aggregation field as decoded from the high-throughput signal (HT-SIG) field of 802.11n signal.
    """

    OFDMMODACC_RESULTS_FEC_CODING_TYPE = 10502314
    r"""Returns the FEC coding type for a specified user.
    
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
    """

    OFDMMODACC_RESULTS_RU_SIZE = 10502195
    r"""Returns the RU or the MRU size.
    
    This result is applicable for 802.11ax MU, extended range SU, and TB PPDU signals, 802.11be MU and TB PPDU
    signals, and 802.11bn MU and TB PPDU signals. For 802.11ax MU PPDU signals, this value is decoded from the HE-SIG-B
    field. For 802.11ax extended range SU PPDU signals, this value is decoded from the HE-SIG-A field. For 802.11be MU PPDU
    signals, this value is decoded from the EHT-SIG field. For 802.11bn MU PPDU signals, this value is decoded from the
    UHR-SIG field. For 802.11ax, 802.11be or 802.11bn TB PPDU signals, this attribute returns the same value as the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_SIZE` attribute.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_RU_OFFSET_MRU_INDEX = 10502196
    r"""Returns the location of RU or MRU for a user. If an RU is detected, the RU Offset is in terms of the index of a 26-tone
    RU, assuming the entire bandwidth is composed of 26-tone RUs. If an MRU is detected, the MRU Index is as defined in the
    Table 36-8 to Table 36-15 of *IEEE P802.11be/D7.0*.
    
    This result is applicable for 802.11ax MU and TB PPDU signals, and 802.11be MU and TB PPDU signals. For
    802.11ax MU PPDU signals, this value is decoded from the HE-SIG-B field. For 802.11be MU PPDU signals, this value is
    decoded from the EHT-SIG field. For 802.11ax or 802.11be TB PPDU signals, this attribute returns the same value as the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_RU_OFFSET_MRU_INDEX` attribute.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_RU_TYPE = 10502369
    r"""Returns the type of RU for a user.
    
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
    """

    OFDMMODACC_RESULTS_DISTRIBUTION_BANDWIDTH = 10502370
    r"""Returns the bandwidth across which RU Subcarriers are distributed for a user.
    
    This result is applicable for 802.11bn TB PPDU signals when RU Type is dRU. For 802.11bn TB PPDU signals, this
    attribute returns the same value as the :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_DISTRIBUTION_BANDWIDTH`
    attribute.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_NUMBER_OF_USERS = 10502197
    r"""Returns the number of users.
    
    For 802.11ac MU PPDU signals, this value is decoded from the VHT-SIG-A field. For 802.11ax MU PPDU signals,
    this value is derived from the HE-SIG-B field. For 802.11be MU PPDU signals, this value is decoded from the EHT-SIG
    field. For 802.11bn MU PPDU signals, this value is decoded from the UHR-SIG field.
    
    For all other PPDUs, this attribute returns 1.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_NUMBER_OF_HE_SIG_B_SYMBOLS = 10502198
    r"""Returns the number of HE-SIG-B symbols.
    
    This result is applicable only to 802.11ax MU PPDU signals, and is decoded from the HE-SIG-A field.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_NUMBER_OF_SIG_SYMBOLS = 10502375
    r"""
    """

    OFDMMODACC_RESULTS_GUARD_INTERVAL_TYPE = 10502199
    r"""Returns the size of the guard interval of OFDM symbols.
    
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
    """

    OFDMMODACC_RESULTS_LTF_SIZE = 10502200
    r"""Returns the HE-LTF size, EHT-LTF or UHR-LTF size when you set the
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
    """

    OFDMMODACC_RESULTS_NUMBER_OF_SPACE_TIME_STREAMS = 10502201
    r"""Returns the number of space time streams.
    
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
    """

    OFDMMODACC_RESULTS_SPACE_TIME_STREAM_OFFSET = 10502288
    r"""Returns the space time stream offset. This attribute is applicable only to 802.11ac, 802.11ax, 802.11be, and 802.11bn
    signals.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    OFDMMODACC_RESULTS_DCM_ENABLED = 10502315
    r"""Returns whether DCM is enabled for a specified user.
    
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
    """

    OFDMMODACC_RESULTS_2xLDPC_ENABLED = 10502371
    r"""Returns whether 2xLDPC is enabled for a specified user.
    
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
    """

    OFDMMODACC_RESULTS_IM_PILOTS_ENABLED = 10502372
    r"""Returns whether interference mitigating pilots are present.
    
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
    """

    OFDMMODACC_RESULTS_UNEQUAL_MODULATION_ENABLED = 10502373
    r"""Returns whether unequal modulation is enabled for a specified user.
    
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
    """

    OFDMMODACC_RESULTS_UNEQUAL_MODULATION_PATTERN_INDEX = 10502374
    r"""Returns unequal modulation pattern for a specified user.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for 802.11bn MU PPDU
    signals.
    """

    OFDMMODACC_RESULTS_L_SIG_PARITY_CHECK_STATUS = 10502280
    r"""Returns whether the parity check has passed either for the SIGNAL field of the 802.11a/g waveform or for the L-SIG
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
    """

    OFDMMODACC_RESULTS_SIG_CRC_STATUS = 10502281
    r"""Returns whether the cyclic redundancy check (CRC) has passed either for the HT-SIG field of the 802.11n waveform, for
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
    """

    OFDMMODACC_RESULTS_SIG_B_CRC_STATUS = 10502282
    r"""Returns whether the cyclic redundancy check (CRC) has passed for the HE-SIG-B field of the 802.11ax MU PPDU waveform.
    
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
    """

    OFDMMODACC_RESULTS_U_SIG_CRC_STATUS = 10502289
    r"""Returns whether the cyclic redundancy check (CRC) has passed for the U-SIG field of the 802.11be or the 802.11bn
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
    """

    OFDMMODACC_RESULTS_EHT_SIG_CRC_STATUS = 10502290
    r"""Returns whether the cyclic redundancy check (CRC) has passed for the EHT-SIG field of the 802.11be waveform.
    
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
    """

    OFDMMODACC_RESULTS_UHR_SIG_CRC_STATUS = 10502355
    r"""Returns whether the cyclic redundancy check (CRC) has passed for the UHR-SIG field of the 802.11bn waveform.
    
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
    """

    OFDMMODACC_RESULTS_ELR_SIG_CRC_STATUS = 10502357
    r"""Returns whether the cyclic redundancy check (CRC) has passed for the ELR-SIG field of the 802.11bn waveform.
    
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
    """

    OFDMMODACC_RESULTS_PSDU_CRC_STATUS = 10502284
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
    """

    OFDMMODACC_RESULTS_SCRAMBLER_SEED = 10502344
    r"""Returns the detected initial state of the scrambler, which is used to scramble the data bits in the device under test
    (DUT). RFmx uses the same seed to descramble the received bit-sequence.
    
    Use "user<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result for MU PPDU signals.
    """

    OFDMMODACC_RESULTS_PE_DURATION = 10502293
    r"""Returns the duration of the packet extension field for the 802.11ax, 802.11be and 802.11bn signals. This value is
    expressed in seconds.
    
    This result is applicable only when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.OFDM_HEADER_DECODING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    OFDMMODACC_RESULTS_PHASE_ROTATION_COEFFICIENT_1 = 10502328
    r"""Specifies the phase rotation coefficient 1 as defined in *IEEE Standard P802.11be/D7.0*.
    
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
    """

    OFDMMODACC_RESULTS_PHASE_ROTATION_COEFFICIENT_2 = 10502329
    r"""Specifies the phase rotation coefficient 2 as defined in *IEEE Standard P802.11be/D7.0*.
    
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
    """

    OFDMMODACC_RESULTS_PHASE_ROTATION_COEFFICIENT_3 = 10502330
    r"""Specifies the phase rotation coefficient 3 as defined in *IEEE Standard P802.11be/D7.0*.
    
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
    """

    SEM_MEASUREMENT_ENABLED = 10506240
    r"""Specifies whether to enable the spectral emission mask (SEM) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SEM_MASK_TYPE = 10506242
    r"""Specifies whether the mask used for the SEM measurement is defined either as per the standard or as specified by you.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **Standard**.
    
    +--------------+----------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                            |
    +==============+========================================================================================+
    | Standard (0) | Mask limits are configured as per the specified standard, channel bandwidth, and band. |
    +--------------+----------------------------------------------------------------------------------------+
    | Custom (1)   | The measurement uses the mask limits that you specify.                                 |
    +--------------+----------------------------------------------------------------------------------------+
    """

    SEM_CARRIER_INTEGRATION_BANDWIDTH = 10506245
    r"""Returns the integration bandwidth of the carrier as per the standard and channel bandwidth. This value is expressed in
    Hz.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is 18 M.
    """

    SEM_NUMBER_OF_OFFSETS = 10506246
    r"""Specifies the number of offset segments for the SEM measurement when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_MASK_TYPE` attribute to **Custom**.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is 1.
    """

    SEM_OFFSET_START_FREQUENCY = 10506247
    r"""Specifies the start frequency of the offset segment relative to the carrier frequency. This value is expressed in Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is 9 MHz.
    """

    SEM_OFFSET_STOP_FREQUENCY = 10506248
    r"""Specifies the stop frequency of the offset segment relative to carrier frequency. This value is expressed in Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is 11 MHz.
    """

    SEM_OFFSET_SIDEBAND = 10506249
    r"""Specifies whether the offset segment is present on one side or on both sides of the carrier.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is **Both**.
    
    +--------------+-----------------------------------------------------------------+
    | Name (Value) | Description                                                     |
    +==============+=================================================================+
    | Neg (0)      | Configures a lower offset segment to the left of the carrier.   |
    +--------------+-----------------------------------------------------------------+
    | Pos (1)      | Configures an upper offset segment to the right of the carrier. |
    +--------------+-----------------------------------------------------------------+
    | Both (2)     | Configures both negative and positive offset segments.          |
    +--------------+-----------------------------------------------------------------+
    """

    SEM_OFFSET_RELATIVE_LIMIT_START = 10506250
    r"""Specifies the relative power limit corresponding to the start of the offset segment. This value is expressed in dB.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is 0.
    """

    SEM_OFFSET_RELATIVE_LIMIT_STOP = 10506251
    r"""Specifies the relative power limit corresponding to the end of the offset segment. This value is expressed in dB.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to configure this attribute.
    
    The default value is -20.
    """

    SEM_SPAN_AUTO = 10506252
    r"""Specifies whether the frequency range of the spectrum used for SEM measurement is computed automatically by the
    measurement or is configured by you.
    
    This attribute is applicable when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_MASK_TYPE`
    attribute to **Standard**.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+--------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                |
    +==============+============================================================================================+
    | False (0)    | The span you configure is used as the frequency range for the SEM measurement.             |
    +--------------+--------------------------------------------------------------------------------------------+
    | True (1)     | The span is automatically computed based on the configured standard and channel bandwidth. |
    +--------------+--------------------------------------------------------------------------------------------+
    """

    SEM_SPAN = 10506253
    r"""Specifies the frequency range of the spectrum used for the SEM measurement. This value is expressed in Hz.
    
    This attribute is applicable only when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_SPAN_AUTO`
    attribute to **False** and the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_MASK_TYPE` attribute to **Standard**.
    
    You do not need to use a selector string to read this attribute for the default signal instance. Refer to the
    `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals.
    
    The default value is 66 MHz.
    """

    SEM_SWEEP_TIME_AUTO = 10506257
    r"""Specifies whether the sweep time for the SEM measurement is computed automatically or is configured by you.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+----------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                              |
    +==============+==========================================================================================================+
    | False (0)    | The measurement uses the sweep time that you specify in the SEM Sweep Time attribute.                    |
    +--------------+----------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement automatically calculates the sweep time based on the standard and bandwidth you specify. |
    +--------------+----------------------------------------------------------------------------------------------------------+
    """

    SEM_SWEEP_TIME_INTERVAL = 10506258
    r"""Specifies the sweep time for the SEM measurement. This value is expressed in seconds.
    
    This attribute is ignored when you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_SWEEP_TIME_AUTO`
    attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 millisecond.
    """

    SEM_AVERAGING_ENABLED = 10506259
    r"""Specifies whether to enable averaging for the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The SEM measurement uses the SEM Averaging Count attribute as the number of acquisitions over which the SEM measurement  |
    |              | is averaged.                                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_AVERAGING_COUNT = 10506260
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    SEM_AVERAGING_TYPE = 10506261
    r"""Specifies the averaging type for averaging multiple spectrum acquisitions. The averaged spectrum is used for SEM
    measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **RMS**.
    
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                 |
    +==============+=============================================================================================================+
    | RMS (0)      | The power spectrum is linearly averaged. RMS averaging reduces signal fluctuations but not the noise floor. |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Log (1)      | The power spectrum is averaged in a logarithmic scale.                                                      |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Scalar (2)   | The square root of the power spectrum is averaged.                                                          |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Max (3)      | The peak power in the spectrum is retained from one acquisition to the next at each frequency bin.          |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    | Min (4)      | The least power in the spectrum is retained from one acquisition to the next at each frequency bin.         |
    +--------------+-------------------------------------------------------------------------------------------------------------+
    """

    SEM_AMPLITUDE_CORRECTION_TYPE = 10506262
    r"""Specifies whether the amplitude of the frequency bins, used in the measurement, is corrected for external attenuation
    at the RF center frequency, or at the individual frequency bins. Use the
    :py:meth:`nirfmxinstr.session.Session.configure_external_attenuation_table` method to configure the external
    attenuation table.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **RF Center Frequency**.
    
    +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value)               | Description                                                                                                              |
    +============================+==========================================================================================================================+
    | RF Center Frequency (0)    | All the frequency bins in the spectrum are compensated with a single external attenuation value that corresponds to the  |
    |                            | RF center frequency.                                                                                                     |
    +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
    | Spectrum Frequency Bin (1) | An individual frequency bin in the spectrum is compensated with the external attenuation value corresponding to that     |
    |                            | frequency.                                                                                                               |
    +----------------------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    SEM_ALL_TRACES_ENABLED = 10506263
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the SEM measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    SEM_NUMBER_OF_ANALYSIS_THREADS = 10506264
    r"""Specifies the maximum number of threads used for parallelism for SEM measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    SEM_RESULTS_MEASUREMENT_STATUS = 10506267
    r"""Returns the overall measurement status, indicating whether the spectrum exceeds the SEM measurement mask limits in any
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
    """

    SEM_RESULTS_CARRIER_ABSOLUTE_INTEGRATED_POWER = 10506268
    r"""Returns the average power of the carrier channel over the bandwidth indicated by the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
    dBm.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    SEM_RESULTS_CARRIER_ABSOLUTE_PEAK_POWER = 10506270
    r"""Returns the peak power in the carrier channel over the bandwidth indicated by the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_CARRIER_INTEGRATION_BANDWIDTH` attribute. This value is expressed in
    dBm. SEM mask level is determined by this result.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    SEM_RESULTS_CARRIER_PEAK_FREQUENCY = 10506271
    r"""Returns the frequency at which the peak power occurs in the carrier channel. This value is expressed in Hz.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    SEM_RESULTS_LOWER_OFFSET_MEASUREMENT_STATUS = 10506273
    r"""Returns the lower offset segment measurement status indicating whether the spectrum exceeds the SEM measurement mask
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
    """

    SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_INTEGRATED_POWER = 10506274
    r"""Returns the average power of the lower (negative) offset channel over the bandwidth obtained by the start and stop
    frequencies of the offset channel. This value is expressed in dBm.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_RELATIVE_INTEGRATED_POWER = 10506275
    r"""Returns the average power of the lower (negative) offset segment relative to the peak power of the carrier channel.
    This value is expressed in dB.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_ABSOLUTE_PEAK_POWER = 10506276
    r"""Returns the peak power measured in the lower (negative) offset segment. This value is expressed in dBm.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_RELATIVE_PEAK_POWER = 10506277
    r"""Returns the peak power of the lower (negative) offset segment relative to the peak power of the carrier channel. This
    value is expressed in dB.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_PEAK_FREQUENCY = 10506278
    r"""Returns the frequency at which the peak power occurs in the lower (negative) offset channel. This value is expressed in
    Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN = 10506279
    r"""Returns the margin from the SEM measurement mask for the lower (negative) offset. This value is expressed in dB.
    
    Margin is computed as
    
    Margin(dB) = Max(Spectrum[] - Mask[])
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_ABSOLUTE_POWER = 10506280
    r"""Returns the power level of the spectrum corresponding to the result of the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in
    dBm.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_RELATIVE_POWER = 10506281
    r"""Returns the power level of the spectrum corresponding to the result of the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in dB.
    
    The power level is returned relative to the peak power of the carrier channel.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_LOWER_OFFSET_MARGIN_FREQUENCY = 10506282
    r"""Returns the frequency of the spectrum corresponding to the result of the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_LOWER_OFFSET_MARGIN` attribute. This value is expressed in Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MEASUREMENT_STATUS = 10506283
    r"""Returns the upper offset (positive) segment measurement status indicating if the spectrum exceeds the SEM measurement
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
    """

    SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_INTEGRATED_POWER = 10506284
    r"""Returns the average power of the offset (positive) offset channel over the bandwidth determined by the start and stop
    frequencies of the offset channel. This value is expressed in dBm.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_RELATIVE_INTEGRATED_POWER = 10506285
    r"""Returns the average power of the offset (positive) offset segment relative to the peak power of the carrier channel.
    This value is expressed in dB.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_ABSOLUTE_PEAK_POWER = 10506286
    r"""Returns the peak power of the offset (positive) offset segment. This value is expressed in dBm.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_RELATIVE_PEAK_POWER = 10506287
    r"""Returns the peak power of the offset (positive) segment relative to the peak power of the carrier channel. This value
    is expressed in dB.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_PEAK_FREQUENCY = 10506288
    r"""Returns the frequency at which the peak power occurs in the offset (positive) channel. This value is expressed in Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN = 10506289
    r"""Returns the margin from the SEM measurement mask for the offset (positive). This value is expressed in dB.
    
    Margin is computed as
    
    Margin(dB) = Max(Spectrum[] - Mask[])
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_ABSOLUTE_POWER = 10506290
    r"""Returns the power level of the spectrum corresponding to the result of the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in
    dBm.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_RELATIVE_POWER = 10506291
    r"""Returns the power level of the spectrum corresponding to the result of the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in dB.
    
    The power level is returned relative to the peak power of the carrier channel.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    SEM_RESULTS_UPPER_OFFSET_MARGIN_FREQUENCY = 10506292
    r"""Returns the frequency of the spectrum corresponding to the result of the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.SEM_RESULTS_UPPER_OFFSET_MARGIN` attribute. This value is expressed in Hz.
    
    Use "offset<*n*>" as the `Selector String
    <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ to read this result.
    """

    TXP_MEASUREMENT_ENABLED = 10489856
    r"""Specifies whether to enable the transmit power (TXP) measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TXP_MAXIMUM_MEASUREMENT_INTERVAL = 10489858
    r"""Specifies the maximum measurement interval. This value is expressed in seconds.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TXP_BURST_DETECTION_ENABLED` attribute to
    **True**, the measurement interval used is equal to the smaller of the duration of the WLAN packet under analysis or
    the value you set for this attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 millisecond.
    """

    TXP_BURST_DETECTION_ENABLED = 10489859
    r"""Specifies whether the measurement detects the start and the end of a WLAN packet automatically.
    
    When you set this attribute to **True**, the measurement interval used is equal to the smaller of the duration
    of the WLAN packet under analysis or the value you set for the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.TXP_MAXIMUM_MEASUREMENT_INTERVAL` attribute.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **True**.
    
    +--------------+---------------------------+
    | Name (Value) | Description               |
    +==============+===========================+
    | False (0)    | Disables burst detection. |
    +--------------+---------------------------+
    | True (1)     | Enables burst detection.  |
    +--------------+---------------------------+
    """

    TXP_AVERAGING_ENABLED = 10489860
    r"""Specifies whether to enable averaging for the TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The TXP measurement uses the TXP Averaging Count attribute as the number of acquisitions over which the TXP measurement  |
    |              | is averaged.                                                                                                             |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    TXP_AVERAGING_COUNT = 10489861
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    TXP_ALL_TRACES_ENABLED = 10489862
    r"""Specifies whether to enable the traces to be stored and retrieved after performing the TXP measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    TXP_NUMBER_OF_ANALYSIS_THREADS = 10489863
    r"""Specifies the maximum number of threads used for parallelism for TXP measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    TXP_RESULTS_AVERAGE_POWER_MEAN = 10489865
    r"""Returns the average power of the acquired signal. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**,
    this attribute returns the mean of the average power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    TXP_RESULTS_AVERAGE_POWER_MAXIMUM = 10489877
    r"""
    """

    TXP_RESULTS_AVERAGE_POWER_MINIMUM = 10489878
    r"""
    """

    TXP_RESULTS_PEAK_POWER_MEAN = 10489879
    r"""
    """

    TXP_RESULTS_PEAK_POWER_MAXIMUM = 10489873
    r"""Returns the peak power of the acquired signal. This value is expressed in dBm.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.TXP_AVERAGING_ENABLED` attribute to **True**,
    this attribute returns the maximum value of the peak power computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    TXP_RESULTS_PEAK_POWER_MINIMUM = 10489880
    r"""
    """

    POWERRAMP_MEASUREMENT_ENABLED = 10493962
    r"""Specifies whether to enable PowerRamp measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    POWERRAMP_ACQUISITION_LENGTH = 10493964
    r"""Specifies the duration of the signal to be acquired for the PowerRamp measurement. This value is expressed in seconds.
    
    You must set this to a value that is greater than or equal to the duration of the PPDU under analysis, so that
    the acquired signal contains both rising and falling power ramp transitions.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1 millisecond.
    """

    POWERRAMP_AVERAGING_ENABLED = 10493972
    r"""Specifies if averaging is enabled for PowerRamp measurements.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is **False**.
    
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | Name (Value) | Description                                                                                                              |
    +==============+==========================================================================================================================+
    | False (0)    | The measurement is performed on a single acquisition.                                                                    |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    | True (1)     | The measurement uses the PowerRamp Averaging Count attribute as the number of acquisitions using which the results are   |
    |              | averaged.                                                                                                                |
    +--------------+--------------------------------------------------------------------------------------------------------------------------+
    """

    POWERRAMP_AVERAGING_COUNT = 10493973
    r"""Specifies the number of acquisitions used for averaging when you set the
    :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED`
    attribute to **True**.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """

    POWERRAMP_ALL_TRACES_ENABLED = 10493974
    r"""Specifies whether to enable all the traces computed by the PowerRamp measurement.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is FALSE.
    """

    POWERRAMP_NUMBER_OF_ANALYSIS_THREADS = 10493975
    r"""Specifies the maximum number of threads used for parallelism for PowerRamp measurement.
    
    The number of threads can range from 1 to the number of physical cores. The number of threads you set may not
    be used in calculations. The actual number of threads used depends on the problem size, system resources, data
    availability, and other considerations.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    """

    POWERRAMP_RESULTS_RISE_TIME_MEAN = 10493976
    r"""Returns the power-ramp rise time of the burst. This value is expressed in seconds.
    
    This measurement is performed in accordance with section 16.3.7.7 of *IEEE Standard 802.11-2016*.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the rise time results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    POWERRAMP_RESULTS_FALL_TIME_MEAN = 10493977
    r"""Returns the power-ramp fall time of the burst. This value is expressed in seconds.
    
    This measurement is performed in accordance with section 16.3.7.7 of *IEEE Standard 802.11-2016*.
    
    When you set the :py:attr:`~nirfmxwlan.attributes.AttributeID.POWERRAMP_AVERAGING_ENABLED` attribute to
    **True**, this attribute returns the mean of the fall time results computed for each averaging count.
    
    You do not need to use a selector string to read this result for default signal and result instance. Refer to
    the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for information
    about the string syntax for named signals and results.
    """

    AUTO_LEVEL_INITIAL_REFERENCE_LEVEL = 10485796
    r"""Specifies the initial reference level which the :py:meth:`auto_level` method uses to estimate the peak power of the
    input signal. This value is expressed in dBm.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 30.
    """

    SAMPLE_CLOCK_RATE_FACTOR = 10485814
    r"""Specifies the factor by which the sample clock rate is multiplied at the transmitter to generate a signal compressed in
    the frequency domain and expanded in the time domain.
    
    For example, a 40 MHz signal can be compressed to 20 MHz in the frequency domain if the sample clock rate is
    reduced to half at the transmitter. In this case, you must set this attribute to 0.5 to demodulate the signal.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 1.
    
    The valid values are 0.001 to 1, inclusive.
    """

    LIMITED_CONFIGURATION_CHANGE = 10485797
    r"""Specifies the set of attributes that are considered by RFmx in the locked signal configuration state.
    
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
    """

    RESULT_FETCH_TIMEOUT = 10534912
    r"""Specifies the time, in seconds, to wait before results are available in the RFmxWLAN Attribute. Set this value to a
    time longer than expected for fetching the measurement. A value of -1 specifies that the RFmxWLAN Attribute waits until
    the measurement is complete.
    
    You do not need to use a selector string to configure or read this attribute for the default signal instance.
    Refer to the `Selector String <https://www.ni.com/docs/en-US/bundle/rfmx/page/selector-strings-net.html>`_ topic for
    information about the string syntax for named signals.
    
    The default value is 10.
    """
